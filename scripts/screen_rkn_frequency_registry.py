#!/usr/bin/env python3
"""Cross-check entity ИНН against RKN's Единый реестр частотных присвоений
(rkn.gov.ru/activity/connection/register/radio/, "Поиск по параметрам
разрешений" tab) — a real, live, unauthenticated POST search confirmed
working 2026-09-06.

**Reverse-engineering note**: an initial chrome-devtools UI test (filling
the ИНН field, clicking НАЙТИ) appeared to return "Записей не найдено" for
every ИНН tried, including a large national telecom operator — looking like
another JS-gated dead end. That was a devtools network-capture artifact,
not a real result: the tool's request list silently stopped reflecting new
POSTs after the first one in that session. A plain `curl` replication of
the exact same param set immediately returned real results (158,183 records
for Ростелеком by ИНН alone). Lesson repeated from the comms-license
registry: don't trust an apparent non-response without confirming via a
second, independent method (here: curl) that a request was actually sent.

The endpoint accepts a plain POST (urlencoded body is fine, no multipart
needed) with: act=search, page=<0-based, 20/page>, filter_select=none,
iDate_1=, iDate_2=, legName=<name or blank>, inn=<ИНН or blank>, ordNum=,
decType=, byDecisionParams=1. Searching by ИНН alone works.

A hit means the ИНН appears in the frequency-assignment registry with real
record(s) (record number, validity period, order number/date, status) — a
lead to verify and wire into an entity's licences[] via
corrections_entities.json, not an automatic fact. A large operator can
return thousands of records; this script only pulls page 0 (first 20) plus
the registry's own reported total count — for genuinely large hits, treat
the total count as a signal (this entity holds many frequency assignments)
rather than trying to enumerate every row.

This is a per-ИНН query loop against a live third-party service — per
CLAUDE.md's crawling-jobs policy, tested inline on a handful first, full-
roster sweep handed to the user to run themselves.

Usage:
    python3 scripts/screen_rkn_frequency_registry.py --slug ao-tsentr-telko
    python3 scripts/screen_rkn_frequency_registry.py --inn 7707049388
    python3 scripts/screen_rkn_frequency_registry.py
"""
from __future__ import annotations

import argparse
import html as html_module
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTITIES = REPO / "data" / "registry" / "entities.json"
OUT = REPO / "data" / "registry" / "_rkn_frequency_hits.json"

BASE_URL = "https://rkn.gov.ru/activity/connection/register/radio/"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36")
DELAY_SECONDS = 1.5

ROW_RE = re.compile(
    r"<tr class='clmn\d'\s*>\s*"
    r"<td>([^<]*)</td>\s*"
    r"<td class=\"t1\">([^<]*)</td>\s*"
    r"<td class=\"t1\">([^<]*)<br/?>(\d{10,12})</td>\s*"
    r"<td class=\"t1\">([^<]*)</td>\s*"
    r"<td class=\"t1\">([^<]*)</td>\s*"
    r"<td>([^<]*)</td>\s*"
    r"<td>([^<]*)</td>",
    re.DOTALL,
)
TOTAL_RE = re.compile(r"Всего:</b>\s*(\d+)")


def search(inn: str = "", leg_name: str = "", retries: int = 3) -> tuple[list[dict], int]:
    params = {
        "act": "search", "page": "0", "filter_select": "none",
        "iDate_1": "", "iDate_2": "", "legName": leg_name, "inn": inn,
        "ordNum": "", "decType": "", "byDecisionParams": "1",
    }
    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(BASE_URL, data=data, headers={
        "User-Agent": UA,
        "Content-Type": "application/x-www-form-urlencoded",
    })
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")
            break
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last_err = e
            if attempt < retries:
                time.sleep(5 * attempt)
    else:
        raise last_err
    try:
        page = json.loads(raw).get("modal", "")
    except json.JSONDecodeError:
        page = raw
    if "Записей не найдено" in page:
        return [], 0
    total_match = TOTAL_RE.search(page)
    total = int(total_match.group(1)) if total_match else 0
    records = []
    for m in ROW_RE.finditer(page):
        records.append({
            "record_number": html_module.unescape(m.group(1).strip()),
            "validity_period": html_module.unescape(m.group(2).strip()),
            "org_name": html_module.unescape(m.group(3).strip()),
            "inn": m.group(4),
            "suspended_date": html_module.unescape(m.group(5).strip()),
            "terminated_date": html_module.unescape(m.group(6).strip()),
            "order": html_module.unescape(m.group(7).strip()),
            "status": html_module.unescape(m.group(8).strip()),
        })
    return records, total


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inn", action="append", default=[])
    ap.add_argument("--slug", action="append", default=[])
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    entities = json.loads(ENTITIES.read_text(encoding="utf-8"))
    by_slug = {e["slug"]: e for e in entities}

    targets: list[tuple[str, str]] = []
    for inn in args.inn:
        targets.append((inn, next((e["slug"] for e in entities if e.get("inn") == inn), f"inn-{inn}")))
    for slug in args.slug:
        e = by_slug.get(slug)
        if e and e.get("inn"):
            targets.append((e["inn"], slug))
    if not targets:
        targets = [(e["inn"], e["slug"]) for e in entities if e.get("inn")]
        if args.limit:
            targets = targets[: args.limit]

    print(f"Checking {len(targets)} ИНН against {BASE_URL} ...")
    hits = []
    for i, (inn, slug) in enumerate(targets, 1):
        try:
            records, total = search(inn=inn)
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            print(f"  [{i}/{len(targets)}] {slug} ({inn}): ERROR {e}")
            continue
        if records:
            hits.append({"slug": slug, "inn": inn, "total": total, "records_page0": records})
            print(f"  [{i}/{len(targets)}] HIT {slug} ({inn}): {total} record(s) total, {len(records)} on page 0")
            OUT.write_text(json.dumps(hits, ensure_ascii=False, indent=2), encoding="utf-8")
        time.sleep(DELAY_SECONDS)

    print(f"\n{len(hits)} hit(s) out of {len(targets)} checked")
    OUT.write_text(json.dumps(hits, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
