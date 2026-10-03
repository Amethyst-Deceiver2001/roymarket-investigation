#!/usr/bin/env python3
"""Batch-search zakupki.gov.ru's contract registry for every ИНН already in
this investigation's registry (legal entities' `inn` + individuals'
`inn_personal`), to find government contracts like the ones confirmed for
ИП Цыганов (₽28.176m combined, «Булат»/«Покров» counter-UAV systems) that a
one-off manual check would otherwise never surface.

**This is a live network job against a third-party service — per
CLAUDE.md's crawling-jobs policy, run it yourself; it should not be run in
the background or executed directly by the assistant.** Tested inline on a
handful of ИНН first (ordinary reconnaissance), but a systematic pass
across the whole roster (186 ИНН as of 2026-08-25: 146 entity + 40
personal) is exactly the "real work at scale" case that policy exists for.

Uses the `supplierTitle` search param reverse-engineered from a user-supplied
DevTools HAR capture 2026-08-25 — see the seeded memory
`zakupki_gov_ru_contract_search_api`. That param accepts a bare ИНН and
filters correctly; every other param name tried before it (`customerInn`,
`supplierInn`) either got silently ignored (returns the whole ~42M-record
registry) or free-text search gave false positives via morphological
stemming. As a guard against that specific failure mode recurring, this
script treats an implausibly large hit count (>5000 — large state
defense-industry primes legitimately run into the hundreds, confirmed
against a real 160-contract ИНН, so the bar is set well above that) as a
FAILURE, not a finding, and does not save it as a lead.

Three-step workflow — `scan`/`fetch-contracts` match scripts/tg_media_pull.py's
candidates/fetch split; `fetch-documents` goes one level deeper into each
contract's actual attachments:

  scan            — one supplierTitle search per ИНН, paginated (50/page)
                     until every regNumber the hit count promises is
                     collected — a single page-1 fetch silently truncates a
                     160-contract ИНН to 10 (or worse, to the wrong dozen
                     "№" digit-strings on the page — the reg-number
                     extraction only matches an actual contract card's own
                     link now, not any 10-25-digit number near a "№"
                     anywhere on the page). Zero-hit ИНН are logged to a
                     local scan cache (data/registry/_zakupki_scan_log.json,
                     NOT under data/sources/ — it's bookkeeping, not
                     evidence) so a re-run skips them by default. Any ИНН
                     with hits gets its raw search-results page archived to
                     data/sources/ZAKUPKI_<inn>_<date>_supplier-search.html
                     and printed as a HIT for a human to triage (per this
                     project's standing rule that a scan's output is a
                     triage list, not a source, until someone reads the
                     actual contract).

  fetch-contracts — given a regNumber list (--inn reads the scan log,
                     --reg-numbers takes an explicit list, --all-hits pulls
                     every regNumber across every ИНН with hits), fetches
                     each contract's full common-info.html card live and
                     archives it the same way the Цыганов contracts were
                     archived by hand. Skips a regNumber whose card is
                     already archived. Capped at 50 contracts/invocation.

  fetch-documents — the full pull this module is named for: contract card
                     (reused if `fetch-contracts` already saved it) +
                     `contractInfoId` extraction + every attachment on the
                     card's "Вложения" tab — the signed contract PDF,
                     payment orders, delivery acts (УПД), sole-supplier
                     justification, etc. — downloaded from zakupki's
                     filestore with the real filename read off each
                     response's Content-Disposition header. Attachments can
                     be multi-megabyte PDFs; this is the slowest, heaviest
                     step in the chain. Capped at 50 contracts/invocation by
                     default (`--max-contracts` to raise it deliberately —
                     e.g. `--all-hits --max-contracts 424` for the full
                     2026-08-25 scan's total).

Usage:
  python3 scripts/zakupki_batch_pull.py scan --limit 10          # quick check
  python3 scripts/zakupki_batch_pull.py scan                     # full roster
  python3 scripts/zakupki_batch_pull.py scan --inn 504405055721  # one ИНН
  python3 scripts/zakupki_batch_pull.py scan --kind person       # people only
  python3 scripts/zakupki_batch_pull.py fetch-contracts --inn 504405055721
  python3 scripts/zakupki_batch_pull.py fetch-contracts --reg-numbers 1463204748024000101,1500300810225000152
  python3 scripts/zakupki_batch_pull.py fetch-documents --inn 504405055721
  python3 scripts/zakupki_batch_pull.py fetch-documents --all-hits --max-contracts 424   # everything found so far

After a scan with hits, or after fetch-contracts/fetch-documents, refresh
the pipeline:
  python3 scripts/scan_sources.py --out data/sources/MANIFEST.md
  python3 scripts/inventory_sources.py
  python3 scripts/extract_registry.py
  python3 scripts/check_registry.py
Then hand-verify each hit and wire confirmed contracts into
government_contracts[] via corrections.json, the same way the two Цыганов
contracts were added — a hit is a lead, not yet a citable fact. Many hits
here will belong to large, already-well-documented state defense primes
(Ростех, НИИ «Вектор», Технодинамика, ...) whose zakupki footprint is
enormous by nature, not evidence of a ЦБСТ/РОЙ.МАРКЕТ-specific finding —
triage for what's actually new before spending a `fetch-documents` pass on
it.
"""
from __future__ import annotations

import argparse
import http.client
import json
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path
from source_files import write_new  # never overwrite a catalogued source

REPO = Path(__file__).resolve().parent.parent
ENTITIES = REPO / "data" / "registry" / "entities.json"
PEOPLE = REPO / "data" / "registry" / "people.json"
SOURCES = REPO / "data" / "sources"
SCAN_LOG = REPO / "data" / "registry" / "_zakupki_scan_log.json"

BASE = "https://zakupki.gov.ru"
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# Politeness delay between calls — a batch job against a shared government
# service, not a burst of one-off lookups. Slower on purpose.
DELAY_SECONDS = 3.0
# Large state defense-industry primes (e.g. АО «НИИ «Вектор»», ГК «Ростех»)
# legitimately have hundreds of contracts — confirmed against ИНН 7813491943
# (160 real, distinct cards). Only an outright-broken filter (the
# customerInn/supplierInn trap in the module docstring, which returns the
# whole ~42M-record registry) should trip this — treat that as a failure,
# not a finding.
MAX_PLAUSIBLE_HITS = 5000
PAGE_SIZE = 50

# TLS: zakupki.gov.ru serves a Russian government cert chain not in
# standard trust stores. curl needs -k; here we build an unverified context.
_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE


def http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, context=_SSL_CTX, timeout=30) as resp:
        return resp.read()


def http_get_with_headers(url: str):
    """Returns (body_bytes, headers). `headers` stays an email.message.Message
    (not dict()-converted) so .get() is case-insensitive — the server sends
    "Content-disposition", not "Content-Disposition", and a plain dict()
    lookup on the wrong case silently returns the default instead of erroring,
    which is exactly how this bug hid on the first test run (every file
    saved as .bin)."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, context=_SSL_CTX, timeout=120) as resp:
        return resp.read(), resp.headers


def search_url(inn: str, page: int = 1) -> str:
    params = {
        "morphology": "on", "fz44": "on", "fz94": "on",
        "contractStageList_0": "on", "contractStageList_1": "on",
        "contractStageList_2": "on", "contractStageList_3": "on",
        "contractStageList": "0,1,2,3",
        "currencyCode": "ANY", "budgetLevelsIdNameHidden": "{}",
        "countryRegIdNameHidden": "{}",
        "supplierTitle": inn,
        "sortBy": "UPDATE_DATE", "pageNumber": str(page),
        "sortDirection": "false", "recordsPerPage": f"_{PAGE_SIZE}",
        "showLotsInfoHidden": "false",
    }
    return f"{BASE}/epz/contract/search/results.html?" + urllib.parse.urlencode(params)


def parse_hit_count(html: str) -> int | None:
    if "Поиск не дал результатов" in html:
        return 0
    m = re.search(r'>\s*([\d\s]+)\s*запис', html)
    if not m:
        return None
    return int(m.group(1).replace(" ", "").replace("\xa0", ""))


def parse_reg_numbers(html: str) -> list[str]:
    """Only real contract-card reg numbers — the href on each card's own
    "№ <regNumber>" link. A blanket regex over the page also picks up
    unrelated digit strings (ИКЗ codes, plan-position numbers, a linked
    notice's own regNumber in a different numbering scheme) that look the
    same shape but aren't a contract regNumber — confirmed by comparing
    against the visible hit_count, which this fixes from over- to exact."""
    return list(dict.fromkeys(re.findall(
        r'href="/epz/contract/contractCard/common-info\.html\?reestrNumber=(\d+)"', html)))


def fetch_all_reg_numbers(inn: str, hit_count: int) -> list[str]:
    """Paginate through supplierTitle=<inn> results until every reg number
    the hit count promises is collected (or a page returns nothing new).

    Network errors on page 2+ are swallowed, not raised — a transient
    connection reset here used to crash the whole scan batch (only page 1's
    fetch, in cmd_scan's own loop, was wrapped in a try/except); now it just
    stops paginating and returns whatever was collected so far, so one flaky
    page degrades to an incomplete-but-recoverable result instead of killing
    every ИНН still queued behind it."""
    all_regs: list[str] = []
    page = 1
    while len(all_regs) < hit_count:
        try:
            html = http_get(search_url(inn, page)).decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException) as ex:
            print(f"      (page {page} failed: {ex} — using {len(all_regs)}/{hit_count} collected so far)")
            break
        page_regs = parse_reg_numbers(html)
        if not page_regs:
            break
        new = [r for r in page_regs if r not in all_regs]
        all_regs.extend(new)
        if len(page_regs) < PAGE_SIZE:
            break
        page += 1
        time.sleep(DELAY_SECONDS)
    return all_regs


def load_targets(kind_filter: str | None) -> list[dict]:
    targets = []
    if kind_filter in (None, "entity"):
        for e in json.loads(ENTITIES.read_text(encoding="utf-8")):
            if e.get("inn"):
                targets.append({"inn": e["inn"], "slug": e["slug"],
                               "name": e.get("name_ru") or e["slug"], "kind": "entity"})
    if kind_filter in (None, "person"):
        for p in json.loads(PEOPLE.read_text(encoding="utf-8")):
            if p.get("inn_personal"):
                targets.append({"inn": p["inn_personal"], "slug": p["slug"],
                               "name": p.get("fio_ru") or p["slug"], "kind": "person"})
    # dedupe by ИНН, keep first
    seen, out = set(), []
    for t in targets:
        if t["inn"] not in seen:
            seen.add(t["inn"])
            out.append(t)
    return out


def load_scan_log() -> dict:
    if SCAN_LOG.exists():
        return json.loads(SCAN_LOG.read_text(encoding="utf-8"))
    return {}


def save_scan_log(log: dict) -> None:
    SCAN_LOG.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")


def cmd_scan(args) -> int:
    targets = load_targets(args.kind)
    if args.inn:
        targets = [t for t in targets if t["inn"] == args.inn]
        if not targets:
            print(f"ИНН {args.inn} not found in registry (entities.json/people.json)", file=sys.stderr)
            return 1
    if args.limit is not None:
        targets = targets[: args.limit]

    today = date.today().strftime("%Y%m%d")
    log = load_scan_log()

    print(f"{len(targets)} ИНН to scan (supplierTitle search, {DELAY_SECONDS}s delay between calls)")

    ok = hits = zero = failed = skipped = 0
    for i, t in enumerate(targets, 1):
        inn = t["inn"]
        if not args.force and inn in log:
            skipped += 1
            continue

        try:
            html = http_get(search_url(inn)).decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException) as ex:
            print(f"  [{i}/{len(targets)}] FAILED   {inn}  {t['name'][:40]}  ({ex})")
            failed += 1
            time.sleep(DELAY_SECONDS)
            continue

        count = parse_hit_count(html)
        if count is None:
            print(f"  [{i}/{len(targets)}] UNKNOWN  {inn}  {t['name'][:40]}  (couldn't parse result count — page shape may have changed)")
            failed += 1
            time.sleep(DELAY_SECONDS)
            continue

        if count > MAX_PLAUSIBLE_HITS:
            print(f"  [{i}/{len(targets)}] SUSPECT  {inn}  {t['name'][:40]}  ({count} hits — likely a broken filter, NOT saved as a lead)")
            failed += 1
            time.sleep(DELAY_SECONDS)
            continue

        if count:
            reg_numbers = parse_reg_numbers(html)
            if len(reg_numbers) < count:
                reg_numbers = fetch_all_reg_numbers(inn, count)
        else:
            reg_numbers = []
        incomplete = len(reg_numbers) < count
        log[inn] = {"date": today, "kind": t["kind"], "slug": t["slug"], "name": t["name"],
                    "hit_count": count, "reg_numbers": reg_numbers, "incomplete": incomplete}

        if count == 0:
            zero += 1
        else:
            hits += 1
            out_path = write_new(SOURCES / f"ZAKUPKI_{inn}_{today}_supplier-search.html", html)
            shown = ", ".join(reg_numbers[:5]) + (f", +{len(reg_numbers) - 5} more" if len(reg_numbers) > 5 else "")
            flag = "  [INCOMPLETE — pagination failed partway, re-run scan --force]" if incomplete else ""
            print(f"  [{i}/{len(targets)}] HIT      {inn}  {t['name'][:40]}  — {count} contract(s): {shown}{flag}")

        ok += 1
        if i % 25 == 0 or i == len(targets):
            save_scan_log(log)
            print(f"  ... [{i}/{len(targets)}] {ok} scanned, {hits} with hits, {zero} zero, {failed} failed, {skipped} skipped")

        time.sleep(DELAY_SECONDS)

    save_scan_log(log)
    print(f"\ndone: {ok} scanned, {hits} with hits, {zero} zero-hit, {failed} failed, {skipped} skipped (already scanned today)")
    if hits:
        print(f"\n{hits} ИНН with hits archived under data/sources/ZAKUPKI_*_supplier-search.html")
        print("Next: python3 scripts/zakupki_batch_pull.py fetch-contracts --inn <one of the hit ИНН>")
        print("      (or --reg-numbers <comma-separated regNumbers> to pull specific contracts directly)")
    return 0


def resolve_reg_numbers(args) -> list[tuple[str, str | None]]:
    """Returns [(regNumber, supplier_inn_or_None), ...]. supplier_inn is only
    known when the regNumber came from the scan log (a specific ИНН's
    cached hits); explicit --reg-numbers has no ИНН attached."""
    if getattr(args, "reg_numbers", None):
        return [(r.strip(), None) for r in args.reg_numbers.split(",") if r.strip()]

    log = load_scan_log()
    if getattr(args, "inn", None):
        entry = log.get(args.inn)
        if not entry or not entry.get("reg_numbers"):
            print(f"no cached scan hits for ИНН {args.inn} — run `scan --inn {args.inn}` first", file=sys.stderr)
            return []
        if entry.get("incomplete"):
            print(f"warning: {args.inn}'s scan is INCOMPLETE ({len(entry['reg_numbers'])}/{entry['hit_count']} — a page failed) — re-run `scan --inn {args.inn} --force` for the full set", file=sys.stderr)
        return [(r, args.inn) for r in entry["reg_numbers"]]

    if getattr(args, "all_hits", False):
        incomplete_inns = [inn for inn, entry in log.items() if entry.get("incomplete")]
        if incomplete_inns:
            print(f"warning: {len(incomplete_inns)} ИНН have INCOMPLETE scans (a page failed mid-pagination): {', '.join(incomplete_inns)} — re-run `scan --force` for those before trusting --all-hits as complete", file=sys.stderr)
        out = []
        for inn, entry in log.items():
            for r in entry.get("reg_numbers", []):
                out.append((r, inn))
        return out

    print("pass --inn, --reg-numbers, or --all-hits", file=sys.stderr)
    return []


def extract_contract_info_id(html: str) -> str | None:
    m = re.search(r"contractInfoId=(\d+)", html)
    return m.group(1) if m else None


def parse_attachments(html: str) -> list[dict]:
    """Each attachment on the document-info.html tab is a filestore link
    immediately preceded by its human-readable label text."""
    out = []
    for m in re.finditer(
        r'<a[^>]*href="(https://zakupki\.gov\.ru/44fz/filestore/[^"]+uid=([0-9A-F]+))"[^>]*>\s*([^<]*)',
        html,
    ):
        url, uid = m.group(1), m.group(2)
        label = re.sub(r"\s+", " ", m.group(3)).strip()
        out.append({"url": url, "uid": uid, "label": label or "vlozhenie"})
    return out


def slug_label(label: str) -> str:
    table = {"а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
            "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
            "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
            "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch",
            "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya"}
    out = []
    for ch in label.lower():
        out.append(table.get(ch, ch if ch.isalnum() else "-"))
    return re.sub(r"-+", "-", "".join(out)).strip("-")[:40] or "vlozhenie"


def cmd_fetch_contracts(args) -> int:
    pairs = resolve_reg_numbers(args)
    if not pairs:
        return 1
    reg_numbers = list(dict.fromkeys(r for r, _ in pairs))

    if len(reg_numbers) > args.max_contracts:
        print(f"refusing: {len(reg_numbers)} contracts requested, cap is --max-contracts {args.max_contracts} "
              f"— split into smaller batches or raise --max-contracts deliberately", file=sys.stderr)
        return 1

    today = date.today().strftime("%Y%m%d")
    print(f"{len(reg_numbers)} contract card(s) to fetch")

    for i, reg in enumerate(reg_numbers, 1):
        out_path = SOURCES / f"ZAKUPKI_contract_{reg}_{today}.html"
        if out_path.exists():
            print(f"  [{i}/{len(reg_numbers)}] cached  {reg}")
            continue
        url = f"{BASE}/epz/contract/contractCard/common-info.html?reestrNumber={reg}"
        try:
            html = http_get(url).decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException) as ex:
            print(f"  [{i}/{len(reg_numbers)}] FAILED  {reg}  ({ex})")
            time.sleep(DELAY_SECONDS)
            continue

        # supplier ИНН isn't known here without parsing — key the filename on
        # regNumber alone, a human/corrections.json pass assigns it to an entity.
        out_path = write_new(out_path, html)
        print(f"  [{i}/{len(reg_numbers)}] saved   {reg}  -> {out_path.relative_to(REPO)}")
        time.sleep(DELAY_SECONDS)

    print("\nRefresh the pipeline, then hand-verify and wire confirmed contracts")
    print("into government_contracts[] via corrections.json:")
    print("  python3 scripts/scan_sources.py --out data/sources/MANIFEST.md")
    print("  python3 scripts/inventory_sources.py")
    print("  python3 scripts/extract_registry.py")
    print("  python3 scripts/check_registry.py")
    return 0


def cmd_fetch_documents(args) -> int:
    """Full pull: contract card + every attached document (the signed
    contract PDF, payment orders, delivery acts, sole-supplier
    justification, etc.) for each regNumber. This is the deepest, slowest,
    most network-heavy step in the whole zakupki tool chain — expect
    multi-megabyte PDFs per contract and plan the delay/scale accordingly."""
    pairs = resolve_reg_numbers(args)
    if not pairs:
        return 1
    # dedupe regNumbers, keep first-seen supplier ИНН for filename purposes
    by_reg: dict[str, str | None] = {}
    for reg, inn in pairs:
        by_reg.setdefault(reg, inn)

    if len(by_reg) > args.max_contracts:
        print(f"refusing: {len(by_reg)} contracts requested, cap is --max-contracts {args.max_contracts} "
             f"(this pulls every attachment per contract too — raise the cap deliberately, don't default to it)", file=sys.stderr)
        return 1

    today = date.today().strftime("%Y%m%d")
    print(f"{len(by_reg)} contract(s) — fetching card + attachments for each")

    total_files = total_bytes = 0
    for i, (reg, inn) in enumerate(by_reg.items(), 1):
        key = inn or reg
        card_path = SOURCES / f"ZAKUPKI_contract_{reg}_{today}.html"
        if card_path.exists():
            html = card_path.read_text(encoding="utf-8")
        else:
            try:
                html = http_get(f"{BASE}/epz/contract/contractCard/common-info.html?reestrNumber={reg}").decode("utf-8", errors="replace")
            except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException) as ex:
                print(f"  [{i}/{len(by_reg)}] FAILED card  {reg}  ({ex})")
                time.sleep(DELAY_SECONDS)
                continue
            card_path = write_new(card_path, html)
            time.sleep(DELAY_SECONDS)

        contract_info_id = extract_contract_info_id(html)
        if not contract_info_id:
            print(f"  [{i}/{len(by_reg)}] {reg}  no contractInfoId found (page shape may have changed) — skipping attachments")
            continue

        doc_url = f"{BASE}/epz/contract/contractCard/document-info.html?reestrNumber={reg}&contractInfoId={contract_info_id}"
        try:
            doc_html = http_get(doc_url).decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException) as ex:
            print(f"  [{i}/{len(by_reg)}] FAILED docs  {reg}  ({ex})")
            time.sleep(DELAY_SECONDS)
            continue
        time.sleep(DELAY_SECONDS)

        attachments = parse_attachments(doc_html)
        if not attachments:
            print(f"  [{i}/{len(by_reg)}] {reg}  0 attachments found")
            continue

        print(f"  [{i}/{len(by_reg)}] {reg}  ({key})  {len(attachments)} attachment(s)")
        for j, att in enumerate(attachments, 1):
            slug = slug_label(att["label"])
            uid8 = att["uid"][:8].lower()
            # extension resolved from Content-Disposition below; placeholder first
            probe_path = list(SOURCES.glob(f"ZAKUPKI_ATTACH_{key}_{reg}_*_{uid8}.*"))
            if probe_path:
                print(f"      [{j}/{len(attachments)}] cached  {att['label'][:40]}")
                continue
            try:
                data, headers = http_get_with_headers(att["url"])
            except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException) as ex:
                print(f"      [{j}/{len(attachments)}] FAILED  {att['label'][:40]}  ({ex})")
                time.sleep(DELAY_SECONDS)
                continue

            disp = headers.get("Content-Disposition", "")
            m = re.search(r"filename\*=UTF-8''([^;]+)", disp) or re.search(r'filename="([^"]+)"', disp)
            ext = "bin"
            if m:
                fname = urllib.parse.unquote(m.group(1))
                if "." in fname:
                    ext = fname.rsplit(".", 1)[-1].lower()[:5]

            out_path = SOURCES / f"ZAKUPKI_ATTACH_{key}_{reg}_{slug}_{uid8}.{ext}"
            out_path = write_new(out_path, data)
            total_files += 1
            total_bytes += len(data)
            print(f"      [{j}/{len(attachments)}] saved   {att['label'][:40]}  ({len(data):,}B) -> {out_path.name}")
            time.sleep(DELAY_SECONDS)

    print(f"\ndone: {total_files} attachment(s) saved, {total_bytes/1e6:.1f} MB total")
    print("\nRefresh the pipeline, then hand-verify and wire confirmed contracts")
    print("into government_contracts[] via corrections.json:")
    print("  python3 scripts/scan_sources.py --out data/sources/MANIFEST.md")
    print("  python3 scripts/inventory_sources.py")
    print("  python3 scripts/extract_registry.py")
    print("  python3 scripts/check_registry.py")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    ap_s = sub.add_parser("scan", help="one supplierTitle search per ИНН in the registry")
    ap_s.add_argument("--limit", type=int, default=None)
    ap_s.add_argument("--inn", default=None, help="scan just this one ИНН")
    ap_s.add_argument("--kind", choices=["entity", "person"], default=None,
                      help="restrict to entities.json ИНН or people.json inn_personal (default: both)")
    ap_s.add_argument("--force", action="store_true", help="re-scan even if already scanned today")
    ap_s.set_defaults(func=cmd_scan)

    ap_f = sub.add_parser("fetch-contracts", help="pull full contract cards for known regNumbers")
    ap_f.add_argument("--inn", default=None, help="use this ИНН's cached scan-log hits")
    ap_f.add_argument("--reg-numbers", default=None, help="comma-separated regNumber list")
    ap_f.add_argument("--all-hits", action="store_true", help="every regNumber across every ИНН in the scan log")
    ap_f.add_argument("--max-contracts", type=int, default=50,
                      help="safety cap on contracts per invocation (default 50; raise deliberately, e.g. for a single --inn with 86 hits)")
    ap_f.set_defaults(func=cmd_fetch_contracts)

    ap_d = sub.add_parser("fetch-documents",
                          help="full pull: contract card + every attached document (contract PDF, payment orders, acts, ...)")
    ap_d.add_argument("--inn", default=None, help="use this ИНН's cached scan-log hits")
    ap_d.add_argument("--reg-numbers", default=None, help="comma-separated regNumber list")
    ap_d.add_argument("--all-hits", action="store_true", help="every regNumber across every ИНН in the scan log")
    ap_d.add_argument("--max-contracts", type=int, default=50,
                      help="safety cap on contracts per invocation (default 50; raise deliberately for --all-hits, e.g. 424)")
    ap_d.set_defaults(func=cmd_fetch_documents)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
