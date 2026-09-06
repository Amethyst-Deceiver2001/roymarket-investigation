#!/usr/bin/env python3
"""Cross-check entity ИНН against RKN's communications-license registry
(rkn.gov.ru/activity/connection/register/license/) — a real, live,
unauthenticated search confirmed working 2026-09-06 via curl, per-ИНН.

**Reverse-engineering note**: an earlier attempt this session (same day)
concluded this endpoint was JS/anti-bot-gated and unscriptable, because a
GET with only `act`/`org_name_full`/`org_inn`/`lic_num` silently returned
the untouched default page (identical byte count every time, no error).
That was wrong — the server requires the FULL param set the real form
submits, including `lic_status_id=0&service_id=0&region_id=0&
searchBtn=Найти` (URL-encoded as %D0%9D%D0%B0%D0%B9%D1%82%D0%B8); omitting
any of them makes it silently ignore the whole request rather than error.
Confirmed via a live chrome-devtools UI click (which produces this exact
URL) followed by a raw curl replication of it — no cookies, no browser,
no JS challenge involved. Lesson: a same-byte-count non-response from a
government search form can mean "malformed request silently ignored",
not "JS-gated" — try the exact param set a real click produces before
concluding a screener isn't possible.

A hit means the ИНН appears in RKN's registry with real license record(s)
(number, status, licensed activity) — a lead to verify and wire into an
entity's licences[] via corrections_entities.json, not an automatic fact.

This is a per-ИНН query loop against a live third-party service — per
CLAUDE.md's crawling-jobs policy, tested inline on a handful first (see
conversation), full-roster sweep handed to the user to run themselves.

Usage:
    python3 scripts/screen_rkn_comms_license.py --slug ao-nii-vektor
    python3 scripts/screen_rkn_comms_license.py --inn 7813491943
    python3 scripts/screen_rkn_comms_license.py
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
OUT = REPO / "data" / "registry" / "_rkn_comms_license_hits.json"

BASE_URL = "https://rkn.gov.ru/activity/connection/register/license/"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36")
DELAY_SECONDS = 1.5

ROW_RE = re.compile(
    r"<tr class='clmn\d'\s*>\s*"
    r"<td[^>]*><a href=\"[^\"]*\"[^>]*>([^<]+)</a>(.*?)</td>\s*"
    r"<td>([^<]*)<br/?>\s*ИНН\s*(\d{10,12})</td>\s*"
    r"<td>([^<]*)</td>",
    re.DOTALL,
)
STATUS_RE = re.compile(r"<small>([^<]*)</small>")


def search(inn: str, retries: int = 3) -> list[dict]:
    # rkn.gov.ru resets connections in short transient bursts under a
    # scripted loop (observed 2026-09-06: two ~20-request blocks reset
    # mid-sweep, then recovered on their own) -- a short backoff-and-retry
    # clears this reliably rather than needing a manual re-run.
    params = {
        "act": "search", "org_name_full": "", "org_inn": inn, "lic_num": "",
        "lic_status_id": "0", "service_id": "0", "region_id": "0", "searchBtn": "Найти",
    }
    url = BASE_URL + "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                page = resp.read().decode("utf-8", errors="ignore")
            break
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last_err = e
            if attempt < retries:
                time.sleep(5 * attempt)
    else:
        raise last_err
    if "не найдено" in page:
        return []
    records = []
    for m in ROW_RE.finditer(page):
        status_match = STATUS_RE.search(m.group(2))
        records.append({
            "license_number": html_module.unescape(m.group(1).strip()),
            "status": html_module.unescape(status_match.group(1).strip()) if status_match else "действующая",
            "org_name": html_module.unescape(m.group(3).strip()),
            "inn": m.group(4),
            "activity": html_module.unescape(m.group(5).strip()),
        })
    return records


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
            records = search(inn)
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            print(f"  [{i}/{len(targets)}] {slug} ({inn}): ERROR {e}")
            continue
        if records:
            hits.append({"slug": slug, "inn": inn, "records": records})
            print(f"  [{i}/{len(targets)}] HIT {slug} ({inn}): {len(records)} license(s)")
            OUT.write_text(json.dumps(hits, ensure_ascii=False, indent=2), encoding="utf-8")
        time.sleep(DELAY_SECONDS)

    print(f"\n{len(hits)} hit(s) out of {len(targets)} checked")
    OUT.write_text(json.dumps(hits, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
