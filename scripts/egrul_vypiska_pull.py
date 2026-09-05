#!/usr/bin/env python3
"""Pull the FULL signed ЕГРЮЛ/ЕГРИП выписка PDF from egrul.nalog.ru.

Sibling to `egrul_batch_pull.py`, which only ever fetched the lightweight
search-result JSON (name, ИНН, ОГРН, current director, region). This script
goes one step further and drives the site's own "Получить выписку" flow:

    POST /                        -> search token
    GET  /search-result/<token>   -> result rows, each carrying its own token
    GET  /vyp-request/<row-token> -> {"t": <doc-token>, "captchaRequired": bool}
    GET  /vyp-status/<doc-token>  -> {"status": "ready"}  (poll)
    GET  /vyp-download/<doc-token> -> the PDF bytes

**`captchaRequired` came back false on every entity tested 2026-09-05** — the
same no-captcha property that made the open lookup API usable (see the
`egrul_nalog_ru_open_api` memory) extends to the full extract. That is a
materially better source than the JSON lookup: the выписка carries the full
founder list with per-founder ИНН and share percentages, charter capital, the
complete ОКВЭД list, the registered address, and the dated ГРН record history
— i.e. everything `director_history`/`founders_history`/`charter_capital_history`
/`address_history` need, from a signed primary document rather than an
aggregator.

**Live network job.** Per CLAUDE.md's crawling-jobs policy: a handful of ИНН
(`--inn`, or a short `--slug` list) is ordinary inline reconnaissance and fine
to run directly; a full-roster sweep (no selector) must be handed to the user
as an exact command, never run in the background.

Output: `data/sources/EGRUL_<ИНН>_<YYYYMMDD>_<slug>.pdf`, matching the archiving
convention in CLAUDE.md. Skips an ИНН that already has today's file unless
`--force`. Afterwards run the usual housekeeping chain
(`inventory_sources.py` → `scan_sources.py` → `extract_registry.py` →
`check_registry.py`) so the new PDFs get real `sNNNN` source ids; `as_of` on
each new cache entry is the выписка's own formation date, which is the pull
date for this source type.
"""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "data" / "sources"
ENTITIES = ROOT / "data" / "registry" / "entities.json"

EGRUL_BASE = "https://egrul.nalog.ru"
USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36")
DELAY_SECONDS = 3.0
POLL_SECONDS = 1.5
POLL_MAX = 25


def slugify(name: str) -> str:
    s = re.sub(r"[^\w\s-]", "", name, flags=re.UNICODE).strip().lower()
    return re.sub(r"[\s_]+", "-", s)[:60] or "entity"


def http(url: str, data: bytes | None = None) -> bytes:
    req = urllib.request.Request(url, data=data, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def search_row(inn: str) -> dict | None:
    """Exact-ИНН search row, carrying the per-row token the выписка needs."""
    body = urllib.parse.urlencode({
        "vyp3CaptchaToken": "", "page": "", "query": inn,
        "region": "", "PreventChromeAutocomplete": "",
    }).encode()
    token = json.loads(http(EGRUL_BASE + "/", body))["t"]
    time.sleep(1.0)
    rows = json.loads(http(f"{EGRUL_BASE}/search-result/{token}")).get("rows", [])
    for row in rows:
        if row.get("i") == inn:
            return row
    return None


def download_vypiska(row: dict) -> bytes:
    """Drive the vyp-request → vyp-status → vyp-download flow for one row."""
    req = json.loads(http(f"{EGRUL_BASE}/vyp-request/{row['t']}"))
    if req.get("captchaRequired"):
        raise RuntimeError("captcha required — cannot proceed unattended")
    doc_token = req["t"]
    for _ in range(POLL_MAX):
        time.sleep(POLL_SECONDS)
        if json.loads(http(f"{EGRUL_BASE}/vyp-status/{doc_token}")).get("status") == "ready":
            break
    else:
        raise RuntimeError("выписка never reached status=ready")
    pdf = http(f"{EGRUL_BASE}/vyp-download/{doc_token}")
    if not pdf.startswith(b"%PDF-"):
        raise RuntimeError(f"response is not a PDF ({pdf[:40]!r})")
    return pdf


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--inn", action="append", default=[],
                    help="pull just this ИНН (repeatable); may be outside entities.json")
    ap.add_argument("--slug", action="append", default=[],
                    help="pull the entity with this slug (repeatable)")
    ap.add_argument("--tier", default=None, help="pull only entities with this tier")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--force", action="store_true",
                    help="re-pull even if today's file already exists")
    args = ap.parse_args()

    entities = json.loads(ENTITIES.read_text(encoding="utf-8"))
    by_inn = {e["inn"]: e for e in entities if e.get("inn")}
    today = date.today().strftime("%Y%m%d")

    targets: list[tuple[str, str, str]] = []          # (inn, slug, name)
    if args.inn or args.slug:
        for inn in args.inn:
            e = by_inn.get(inn)
            targets.append((inn,
                            (e or {}).get("slug") or f"inn-{inn}",
                            (e or {}).get("name_ru") or f"(not in registry) ИНН {inn}"))
        by_slug = {e.get("slug"): e for e in entities}
        for slug in args.slug:
            e = by_slug.get(slug)
            if not e or not e.get("inn"):
                print(f"  SKIP {slug}: not in entities.json, or has no ИНН")
                continue
            targets.append((e["inn"], slug, e.get("name_ru") or slug))
    else:
        pool = [e for e in entities if e.get("inn")]
        if args.tier:
            pool = [e for e in pool if e.get("tier") == args.tier]
        targets = [(e["inn"], e.get("slug") or slugify(e["name_ru"]),
                    e.get("name_ru") or "") for e in pool]
    if args.limit is not None:
        targets = targets[:args.limit]

    print(f"{len(targets)} выписка(s) to pull (formation date {today})")

    ok = failed = skipped = 0
    for i, (inn, slug, name) in enumerate(targets, 1):
        out_path = SOURCES / f"EGRUL_{inn}_{today}_{slug}.pdf"
        if out_path.exists() and not args.force:
            skipped += 1
            continue
        try:
            row = search_row(inn)
            if row is None:
                print(f"  [{i}/{len(targets)}] NO MATCH  {inn}  {name[:40]}")
                failed += 1
                time.sleep(DELAY_SECONDS)
                continue
            pdf = download_vypiska(row)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError,
                KeyError, RuntimeError) as ex:
            print(f"  [{i}/{len(targets)}] FAILED  {inn}  {name[:40]}  ({ex})")
            failed += 1
            time.sleep(DELAY_SECONDS)
            continue

        out_path.write_bytes(pdf)
        ok += 1
        print(f"  [{i}/{len(targets)}] ok  {inn}  {name[:40]}  "
              f"({len(pdf):,} bytes → {out_path.name})")
        time.sleep(DELAY_SECONDS)

    print(f"\ndone: {ok} pulled, {failed} failed/no-match, "
          f"{skipped} skipped (already had today's file)")
    if ok:
        print("\nNow refresh the pipeline:")
        print("    python3 scripts/inventory_sources.py")
        print("    python3 scripts/scan_sources.py --out data/sources/MANIFEST.md")
        print("    python3 scripts/extract_registry.py")
        print("    python3 scripts/check_registry.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
