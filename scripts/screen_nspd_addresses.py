#!/usr/bin/env python3
"""Cross-check every entity's known address(es) against Rosreestr's НСПД
(nspd.gov.ru) geoportal search — see `scripts/nspd_lookup.py` for the
endpoint reverse-engineering notes and the WAF-reliability caveat.

For each entity, queries `address` plus every distinct value in
`address_history[]`, and writes back matched cadastral records (cadastral
number, building name, area, year built, purpose, ownership_type,
right_type, cost_value) to a scratch file for human review. This does NOT
resolve an address to an owning ИНН — Rosreestr's public output never
exposes owner/tenant identity (redacted since 2017) — it only corroborates
a registered address against a real, dated cadastral record: existence,
scale, declared use, construction year. Useful for the same class of
"letterbox address vs. real facility" contrast already used for Гагаринг's
own three addresses (see notes/gagaring_network_map.md).

**Reliability**: nspd.gov.ru's WAF has 403'd this sandbox's curl requests
in bursts even with a full browser-like header set, while never failing
from an actual chrome-devtools browser session on the same queries. This
script may show a run of ERRORs if the WAF is in a blocking mood — that is
a signal to retry later or fall back to chrome-devtools for the specific
addresses that failed, not proof the addresses have no records.

This is a per-entity query loop against a live third-party service — per
CLAUDE.md's crawling-jobs policy, tested inline on a handful first, full-
roster sweep handed to the user to run themselves.

Usage:
    python3 scripts/screen_nspd_addresses.py --slug ooo-gagaring
    python3 scripts/screen_nspd_addresses.py --inn 7736238480
    python3 scripts/screen_nspd_addresses.py
"""
from __future__ import annotations

import argparse
import json
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTITIES = REPO / "data" / "registry" / "entities.json"
OUT = REPO / "data" / "registry" / "_nspd_address_hits.json"

BASE_URL = "https://nspd.gov.ru/api/geoportal/v2/search/geoportal"
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36"),
    "Referer": "https://nspd.gov.ru/map",
    "Accept": "*/*",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
    "sec-ch-ua": '"Chromium";v="152", "Not?A_Brand";v="24", "Google Chrome";v="152"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
}
SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE
DELAY_SECONDS = 1.5


def search(query: str, retries: int = 3) -> list[dict]:
    params = {"query": query, "thematicSearchId": "1"}
    url = BASE_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=HEADERS)
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=20, context=SSL_CONTEXT) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            break
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last_err = e
            if attempt < retries:
                time.sleep(5 * attempt)
    else:
        raise last_err
    return data.get("data", {}).get("features", [])


def entity_addresses(entity: dict) -> list[str]:
    addrs = set()
    if entity.get("address"):
        addrs.add(entity["address"])
    for hist in entity.get("address_history", []) or []:
        if hist.get("value"):
            addrs.add(hist["value"])
    return sorted(addrs)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inn", action="append", default=[])
    ap.add_argument("--slug", action="append", default=[])
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    entities = json.loads(ENTITIES.read_text(encoding="utf-8"))
    by_slug = {e["slug"]: e for e in entities}
    by_inn = {e["inn"]: e for e in entities if e.get("inn")}

    targets: list[dict] = []
    for inn in args.inn:
        if inn in by_inn:
            targets.append(by_inn[inn])
    for slug in args.slug:
        if slug in by_slug:
            targets.append(by_slug[slug])
    if not targets:
        targets = [e for e in entities if e.get("address") or e.get("address_history")]
        if args.limit:
            targets = targets[: args.limit]

    print(f"Checking {len(targets)} entities against {BASE_URL} ...")
    hits = []
    for i, entity in enumerate(targets, 1):
        slug = entity["slug"]
        for addr in entity_addresses(entity):
            try:
                features = search(addr)
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                print(f"  [{i}/{len(targets)}] {slug} | {addr[:50]}: ERROR {e}")
                continue
            if features:
                records = []
                for f in features:
                    opts = f.get("properties", {}).get("options", {})
                    records.append({
                        "cad_num": opts.get("cad_num") or opts.get("cad_number"),
                        "readable_address": opts.get("readable_address"),
                        "building_name": opts.get("building_name") or opts.get("name"),
                        "area": opts.get("build_record_area") or opts.get("area"),
                        "year_built": opts.get("year_built"),
                        "purpose": opts.get("purpose"),
                        "ownership_type": opts.get("ownership_type"),
                        "right_type": opts.get("right_type"),
                        "cost_value": opts.get("cost_value"),
                        "status": opts.get("status"),
                    })
                hits.append({"slug": slug, "inn": entity.get("inn"), "queried_address": addr, "records": records})
                print(f"  [{i}/{len(targets)}] HIT {slug} | {addr[:50]}: {len(records)} record(s)")
                OUT.write_text(json.dumps(hits, ensure_ascii=False, indent=2), encoding="utf-8")
            time.sleep(DELAY_SECONDS)

    print(f"\n{len(hits)} address-hit(s) across {len(targets)} entities checked")
    OUT.write_text(json.dumps(hits, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
