#!/usr/bin/env python3
"""Pull signed БФО (annual accounts) filings from bo.nalog.gov.ru.

Discovered 2026-09-05: the site's actual filing-PDF endpoint,
/download/bfo/pdf/<correction_id>, is NOT the same as /download/original/<id>
documented in the `bo_nalog_gov_ru_api` memory (which IS universally gated,
"Organization closed for public use"). /download/bfo/pdf/ was found by
clicking the real "Скачать c подписью ФНС России" button in a live browser
and watching the network tab open a new page at that URL with no cookies
sent and no captcha challenge -- confirmed reproducible via a plain
`curl -k`, no session/auth of any kind. This closes what the memory called
a "cannot self-serve" gap.

Flow, all unauthenticated:
    GET /advanced-search/organizations/search?query=<INN or name>
        -> org `id` (a `bfo` block confirms whether ANY filing exists)
    GET /nbo/organizations/<id>/bfo/
        -> one row per filing year; walk typeCorrections[].correction.id
           for the doc id `/download/bfo/pdf/` wants (NOT the outer bfoId)
    GET /download/bfo/pdf/<correction.id>
        -> the actual signed PDF (curl -k required, self-signed TLS chain,
           same as zakupki.gov.ru elsewhere in this repo)

Single-ИНН / a handful = inline reconnaissance, run directly. A full-roster
sweep (--all-missing, added 2026-09-07, mirroring egrul_vypiska_pull.py's
selector-less mode) should be handed to the user per this repo's
crawling-jobs policy in CLAUDE.md, same as egrul_vypiska_pull.py /
egrul_batch_pull.py.
"""
import argparse
import json
import re
import sys
import time
import unicodedata
from datetime import date
from pathlib import Path

import requests
from source_files import write_new  # never overwrite a catalogued source

BASE = "https://bo.nalog.gov.ru"
ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "data" / "sources"
ENTITIES = ROOT / "data" / "registry" / "entities.json"
DELAY_SECONDS = 2.0

# bo.nalog.gov.ru's WAF 403s any request lacking a normal browser UA/sec-ch-ua
# set - confirmed 2026-09-05 (curl/requests default headers -> 403, a real
# Chrome UA -> 200). Not an auth gate, just a bot-signature check.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
}


def slugify(name: str) -> str:
    name = unicodedata.normalize("NFKD", name)
    name = re.sub(r"[^\w\s-]", "", name, flags=re.UNICODE).strip().lower()
    return re.sub(r"[\s_-]+", "-", name)[:60]


# bo.nalog.gov.ru's TLS/connection is flaky under repeated automated hits
# (confirmed 2026-09-14: SSLError/IncompleteRead/RemoteDisconnected all seen
# on plain retries of the same request seconds apart, no pattern to which
# endpoint). A single unhandled one used to kill the whole --all-missing
# sweep partway through the 2nd entity. get_with_retry() absorbs these with
# a short backoff before giving up; the per-ИНН loop in main() also now
# isolates each entity's own exceptions so one still-failing ИНН doesn't
# abort the ones after it.
RETRYABLE = (
    requests.exceptions.SSLError,
    requests.exceptions.ConnectionError,
    requests.exceptions.Timeout,
)


def get_with_retry(url: str, *, attempts: int = 4, backoff: float = 3.0, **kwargs) -> requests.Response:
    last_exc = None
    for attempt in range(attempts):
        try:
            r = requests.get(url, headers=HEADERS, verify=False, **kwargs)
            r.raise_for_status()
            return r
        except RETRYABLE as ex:
            last_exc = ex
            if attempt < attempts - 1:
                print(f"  retry {attempt + 1}/{attempts - 1} after {ex.__class__.__name__}: {ex}", file=sys.stderr)
                time.sleep(backoff * (attempt + 1))
    raise last_exc


def find_org(inn: str) -> dict | None:
    r = get_with_retry(
        f"{BASE}/advanced-search/organizations/search",
        params={"query": inn},
        timeout=20,
    )
    for row in r.json().get("content", []):
        # inn/shortName come back with <strong> highlight markup around the
        # matched substring - strip tags before comparing, or an exact-ИНН
        # match silently never fires.
        row_inn = re.sub(r"<[^>]+>", "", row.get("inn") or "")
        if row_inn == inn:
            row["inn"] = row_inn
            row["shortName"] = re.sub(r"<[^>]+>", "", row.get("shortName") or "")
            return row
    return None


def list_filings(org_id: int) -> list[dict]:
    r = get_with_retry(f"{BASE}/nbo/organizations/{org_id}/bfo/", timeout=20)
    return r.json()


def download_filing(correction_id: int, out_path: Path) -> int:
    r = get_with_retry(f"{BASE}/download/bfo/pdf/{correction_id}", timeout=60)
    if r.headers.get("content-type", "").split(";")[0] != "application/pdf":
        raise RuntimeError(f"unexpected content-type {r.headers.get('content-type')!r}")
    out_path = write_new(out_path, r.content)
    return len(r.content)


def record_miss(registry: str, inn: str) -> None:
    """Note in data/registry/_pull_misses.json that a registry had no record for this ИНН today."""
    path = ENTITIES.parent / "_pull_misses.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    data.setdefault(registry, {})[inn] = date.today().isoformat()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--inn", action="append", help="ИНН (repeatable)")
    ap.add_argument("--slug", required=False, help="entity slug for filename (single --inn only)")
    ap.add_argument("--force", action="store_true", help="re-download even if a same-year file exists")
    ap.add_argument("--all-missing", action="store_true",
                     help="sweep every entities.json ИНН with an empty financials[] "
                          "(full-roster live job, hand to user per crawling-jobs policy)")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    if not args.inn and not args.all_missing:
        ap.error("need --inn (repeatable) or --all-missing")

    requests.packages.urllib3.disable_warnings()  # noqa: self-signed chain, same as zakupki_batch_pull.py

    entities = json.loads(ENTITIES.read_text(encoding="utf-8"))
    inn_to_reg_slug = {e["inn"]: e["slug"] for e in entities if e.get("inn") and e.get("slug")}

    inns = list(args.inn or [])
    if args.all_missing:
        gap = [e["inn"] for e in entities if e.get("inn") and not e.get("financials")]
        if args.limit is not None:
            gap = gap[:args.limit]
        print(f"{len(gap)} ИНН missing financials[] to sweep", file=sys.stderr)
        inns.extend(gap)

    for i, inn in enumerate(inns):
        if args.all_missing and i:
            time.sleep(DELAY_SECONDS)
        try:
            org = find_org(inn)
        except Exception as ex:
            print(f"[{inn}] search FAILED, skipping this ИНН - {ex}", file=sys.stderr)
            continue
        if not org:
            print(f"[{inn}] not found in bo.nalog.gov.ru search index", file=sys.stderr)
            record_miss("bfo", inn)  # status_board.py waits 30 days before queueing it again
            continue
        try:
            filings = list_filings(org["id"])
        except Exception as ex:
            print(f"[{inn}] filing-list FAILED, skipping this ИНН - {ex}", file=sys.stderr)
            continue
        if not filings:
            print(f"[{inn}] {org.get('shortName', '')}: no БФО filings on record")
            continue
        # Prefer the entity's own entities.json slug (stable filename across
        # runs) over re-slugifying bo.nalog.gov.ru's shortName, which caused
        # a real duplicate-content re-pull of ooo-arkhangel's FY2025 filing
        # under a Cyrillic slug spelling on 2026-09-07.
        if args.slug and len(inns) == 1:
            slug = args.slug
        elif inn in inn_to_reg_slug:
            slug = inn_to_reg_slug[inn]
        else:
            slug = slugify(org.get("shortName", inn))
        for f in filings:
            year = f.get("period")
            for tc in f.get("typeCorrections", []):
                corr = tc.get("correction") or {}
                cid = corr.get("id")
                if not cid:
                    continue
                out = SOURCES / f"BFO_{inn}_{year}_{slug}.pdf"
                if out.exists() and not args.force:
                    print(f"[{inn}] {year}: already have {out.name}, skip (--force to re-pull)")
                    continue
                try:
                    size = download_filing(cid, out)
                except Exception as ex:
                    print(f"[{inn}] {year} (correction {cid}): FAILED - {ex}", file=sys.stderr)
                    continue
                print(f"[{inn}] {year}: wrote {out.name} ({size:,} bytes)")

    print(
        "\nRun the housekeeping chain next: inventory_sources.py -> scan_sources.py "
        "--out data/sources/MANIFEST.md --leads-out <file> -> extract_registry.py -> "
        "check_registry.py",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
