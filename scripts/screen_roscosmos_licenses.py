#!/usr/bin/env python3
"""Cross-check entity ИНН against Roscosmos's public space-activity license
registry (licenses.roscosmos.ru/api/public/licenses) — a real, live,
unauthenticated JSON API confirmed working 2026-09-06: one GET returns the
ENTIRE dataset (548 records as of that date, no pagination/ИНН param
needed). Requires a real User-Agent header (a bare curl with none gets a
403; any browser-like UA works).

This is a SINGLE bulk fetch of the whole registry, not a per-entity network
loop — like scan_sources.py/mine_leads.py, safe to run directly/repeatedly
regardless of roster size. Not covered by CLAUDE.md's crawling-jobs policy
(that policy targets scripted loops of many requests against a third
party, not one dataset download).

A hit means the ИНН appears in Roscosmos's registry with a real license
record (licenseNumber/status/workTypes/dateIssue/dateOrder) — this is a
lead to verify and wire into an entity's licences[] via
corrections_entities.json, not an automatic fact (same discipline as
screen_mchs_fire_licenses.py). Cross-check the license number against
whatever's already on file before wiring — this project already found one
case (ao-nii-vektor, 2026-09-06) where a Roscosmos hit and an EGRUL/other-
source hit were the SAME license cited two different ways.

Usage:
    python3 scripts/screen_roscosmos_licenses.py
    python3 scripts/screen_roscosmos_licenses.py --slug ao-nii-vektor
"""
from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTITIES = REPO / "data" / "registry" / "entities.json"
OUT = REPO / "data" / "registry" / "_roscosmos_license_hits.json"

API_URL = "https://licenses.roscosmos.ru/api/public/licenses"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def fetch_all_licenses() -> list[dict]:
    req = urllib.request.Request(API_URL, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", action="append", default=[])
    args = ap.parse_args()

    entities = json.loads(ENTITIES.read_text(encoding="utf-8"))
    targets = [e for e in entities if e.get("inn")]
    if args.slug:
        targets = [e for e in targets if e["slug"] in args.slug]

    print(f"Fetching full Roscosmos license dataset from {API_URL} ...")
    try:
        licenses = fetch_all_licenses()
    except (urllib.error.URLError, json.JSONDecodeError) as e:
        print(f"ERROR fetching dataset: {e}")
        return 1
    print(f"{len(licenses)} license records fetched; matching against {len(targets)} entity ИНН ...")

    by_inn: dict[str, list[dict]] = {}
    for lic in licenses:
        inn = (lic.get("inn") or "").strip()
        if inn:
            by_inn.setdefault(inn, []).append(lic)

    hits = []
    for e in targets:
        matches = by_inn.get(e["inn"])
        if matches:
            hits.append({"slug": e["slug"], "inn": e["inn"], "org_name": e.get("name_ru"), "licenses": matches})
            print(f"  HIT {e['slug']} ({e['inn']}): {len(matches)} license(s) — "
                  + ", ".join(m.get("licenseNumber", "?") for m in matches))

    print(f"\n{len(hits)} entity/entities with hit(s) out of {len(targets)} checked")
    OUT.write_text(json.dumps(hits, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
