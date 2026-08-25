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
across the whole roster (450+ ИНН between entities and people) is exactly
the "real work at scale" case that policy exists for.

Uses the `supplierTitle` search param reverse-engineered from a user-supplied
DevTools HAR capture 2026-08-25 — see the seeded memory
`zakupki_gov_ru_contract_search_api`. That param accepts a bare ИНН and
filters correctly; every other param name tried before it (`customerInn`,
`supplierInn`) either got silently ignored (returns the whole ~42M-record
registry) or free-text search gave false positives via morphological
stemming. As a guard against a future param regression doing the same
silent-ignore thing, this script treats an implausibly large hit count
(>200) as a FAILURE, not a finding, and does not save it as a lead.

Two-step workflow, matching scripts/tg_media_pull.py's candidates/fetch
split:

  scan            — one supplierTitle search per ИНН. Zero-hit ИНН are
                     logged to a local scan cache (data/registry/
                     _zakupki_scan_log.json, NOT under data/sources/ — it's
                     bookkeeping, not evidence) so a re-run skips them by
                     default. Any ИНН with 1-200 hits gets its raw search-
                     results page archived to data/sources/
                     ZAKUPKI_<inn>_<date>_supplier-search.html and printed
                     as a HIT for a human to triage (per this project's
                     standing rule that a scan's output is a triage list,
                     not a source, until someone reads the actual contract).

  fetch-contracts — given a regNumber list (read straight from the last
                     scan's archived HTML, or passed via --reg-numbers),
                     fetches each contract's full common-info.html card
                     live and archives it the same way the Цыганов
                     contracts were archived by hand. Also live network at
                     scale — same policy, hand to the user.

Usage:
  python3 scripts/zakupki_batch_pull.py scan --limit 10          # quick check
  python3 scripts/zakupki_batch_pull.py scan                     # full roster
  python3 scripts/zakupki_batch_pull.py scan --inn 504405055721  # one ИНН
  python3 scripts/zakupki_batch_pull.py scan --kind person       # people only
  python3 scripts/zakupki_batch_pull.py fetch-contracts --inn 504405055721
  python3 scripts/zakupki_batch_pull.py fetch-contracts --reg-numbers 1463204748024000101,1500300810225000152

After a scan with hits, or after fetch-contracts, refresh the pipeline:
  python3 scripts/scan_sources.py --out data/sources/MANIFEST.md
  python3 scripts/inventory_sources.py
  python3 scripts/extract_registry.py
  python3 scripts/check_registry.py
Then hand-verify each hit and wire confirmed contracts into
government_contracts[] via corrections.json, the same way the two Цыганов
contracts were added — a hit is a lead, not yet a citable fact.
"""
from __future__ import annotations

import argparse
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
# A real supplierTitle=<ИНН> hit is a handful of contracts at most. A count
# above this almost certainly means the filter param silently stopped
# working (see the customerInn/supplierInn trap in the module docstring) —
# treat it as a failure, not a finding.
MAX_PLAUSIBLE_HITS = 200

# TLS: zakupki.gov.ru serves a Russian government cert chain not in
# standard trust stores. curl needs -k; here we build an unverified context.
_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE


def http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, context=_SSL_CTX, timeout=30) as resp:
        return resp.read()


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
        "sortDirection": "false", "recordsPerPage": "_10",
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
    return sorted(set(re.findall(r'№\s*(\d{10,25})', html)))


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
        if not args.force and log.get(inn, {}).get("date") == today:
            skipped += 1
            continue

        try:
            html = http_get(search_url(inn)).decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError, OSError) as ex:
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

        reg_numbers = parse_reg_numbers(html) if count else []
        log[inn] = {"date": today, "kind": t["kind"], "slug": t["slug"], "name": t["name"],
                    "hit_count": count, "reg_numbers": reg_numbers}

        if count == 0:
            zero += 1
        else:
            hits += 1
            out_path = SOURCES / f"ZAKUPKI_{inn}_{today}_supplier-search.html"
            out_path.write_text(html, encoding="utf-8")
            print(f"  [{i}/{len(targets)}] HIT      {inn}  {t['name'][:40]}  — {count} contract(s): {', '.join(reg_numbers)}")

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


def cmd_fetch_contracts(args) -> int:
    reg_numbers: list[str] = []
    if args.reg_numbers:
        reg_numbers = [r.strip() for r in args.reg_numbers.split(",") if r.strip()]
    elif args.inn:
        log = load_scan_log()
        entry = log.get(args.inn)
        if not entry or not entry.get("reg_numbers"):
            print(f"no cached scan hits for ИНН {args.inn} — run `scan --inn {args.inn}` first", file=sys.stderr)
            return 1
        reg_numbers = entry["reg_numbers"]
    else:
        print("pass --inn (uses the cached scan log) or --reg-numbers", file=sys.stderr)
        return 1

    if len(reg_numbers) > 50:
        print(f"refusing: {len(reg_numbers)} contracts requested in one run — split into smaller batches", file=sys.stderr)
        return 1

    today = date.today().strftime("%Y%m%d")
    print(f"{len(reg_numbers)} contract card(s) to fetch")

    for i, reg in enumerate(reg_numbers, 1):
        url = f"{BASE}/epz/contract/contractCard/common-info.html?reestrNumber={reg}"
        try:
            html = http_get(url).decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError, OSError) as ex:
            print(f"  [{i}/{len(reg_numbers)}] FAILED  {reg}  ({ex})")
            time.sleep(DELAY_SECONDS)
            continue

        # supplier ИНН isn't known here without parsing — key the filename on
        # regNumber alone, a human/corrections.json pass assigns it to an entity.
        out_path = SOURCES / f"ZAKUPKI_contract_{reg}_{today}.html"
        out_path.write_text(html, encoding="utf-8")
        print(f"  [{i}/{len(reg_numbers)}] saved   {reg}  -> {out_path.relative_to(REPO)}")
        time.sleep(DELAY_SECONDS)

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
    ap_f.set_defaults(func=cmd_fetch_contracts)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
