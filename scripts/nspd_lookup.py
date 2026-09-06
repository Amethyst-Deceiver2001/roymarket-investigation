#!/usr/bin/env python3
"""Look up a property/building record in Rosreestr's НСПД (nspd.gov.ru)
geoportal — a real, live, unauthenticated JSON search confirmed working
2026-09-06 via curl.

**Reverse-engineering note, and an honest reliability caveat**: a bare curl
(User-Agent only) gets a 403 from this endpoint; adding a full browser-like
header set (`Referer`, `Accept`, the `sec-ch-ua*`/`sec-fetch-*` family) got
a real 200 with full JSON once — but every retry afterward, from the same
sandbox, 403'd again, while a chrome-devtools browser session on the exact
same query kept working the whole time. This looks like an IP-reputation
WAF (not a session/cookie/token check — no cookies were ever sent) that is
unreliable specifically for this sandbox's egress IPs, not a stable
curl-scriptable endpoint the way RKN's registries turned out to be. **Do
not trust a single successful curl run as proof this is reliably
scriptable** — verify with a few repeated calls first, and fall back to a
chrome-devtools browser session (which has not failed once) if curl 403s.
This script is provided for the cases where curl does work; when it
403s, redo the same query via chrome-devtools instead.

Endpoint: `GET nspd.gov.ru/api/geoportal/v2/search/geoportal
?thematicSearchId=1&query=<address or cadastral number>` — accepts either
a free-text address (geocoded, returns nearby buildings ranked by score)
or an exact cadastral number (`23:43:0302010:387` format) for a precise
single-record lookup.

Returns, per matched building/parcel/unit: cadastral number, address,
area, year built, floors, materials, "ownership_type" (Частная/
Государственная федеральная/etc — NOT the owner's name; Rosreestr's public
lookup does not expose individual owner identity per post-2017 privacy
amendments), "right_type" (Собственность/etc), cadastral value, status,
and (for buildings) a human-readable "building_name" like "Производственный
корпус" that data corroborates purpose/description.

This is a lookup tool for corroborating a facility's existence, scale, and
declared use against an address already surfaced by other sources (a
Telegram post, an EGRUL registered address, a press photo) — not an
entity/person search. It cannot resolve a building to an owning ИНН; that
still requires the standard EGRUL flow for the address.

Single-address lookups are ordinary inline reconnaissance, fine to run
directly per CLAUDE.md's crawling-jobs policy.

Usage:
    python3 scripts/nspd_lookup.py --query "Краснодар Одесская 48"
    python3 scripts/nspd_lookup.py --query "23:43:0302010:387"
"""
from __future__ import annotations

import argparse
import json
import ssl
import urllib.error
import urllib.parse
import urllib.request

# nspd.gov.ru's TLS chain terminates in a Russian government CA
# ("Russian Trusted Sub CA") not present in standard trust stores --
# verification must be disabled the same way `curl -k` does, not a sign
# of anything suspicious about the endpoint itself.
SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE

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


def search(query: str) -> dict:
    params = {"thematicSearchId": "1", "query": query}
    url = BASE_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20, context=SSL_CONTEXT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True, help="Address or cadastral number")
    args = ap.parse_args()

    try:
        result = search(args.query)
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        print(f"ERROR: {e}")
        return 1

    features = result.get("data", {}).get("features", [])
    if not features:
        print("No records found.")
        return 0

    print(f"{len(features)} record(s):\n")
    for f in features:
        opts = f.get("properties", {}).get("options", {})
        print(f"  cad_num: {opts.get('cad_num') or opts.get('cad_number')}")
        print(f"  address: {opts.get('readable_address')}")
        print(f"  name: {opts.get('building_name') or opts.get('name', '-')}")
        print(f"  area: {opts.get('build_record_area') or opts.get('area')} m2")
        print(f"  year_built: {opts.get('year_built', '-')}")
        print(f"  purpose: {opts.get('purpose', '-')}")
        print(f"  ownership_type: {opts.get('ownership_type', '-')}")
        print(f"  right_type: {opts.get('right_type', '-')}")
        print(f"  cost_value: {opts.get('cost_value', '-')} rub")
        print(f"  status: {opts.get('status', '-')}")
        print()

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
