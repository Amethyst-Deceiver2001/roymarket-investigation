#!/usr/bin/env python3
"""Cross-check entity ИНН against favt.gov.ru's aviation-works operator
registry (Реестр эксплуатантов, выполняющих авиационные работы) — a real,
live, unauthenticated page confirmed working 2026-09-06: a single GET
embeds the ENTIRE table (~424 rows as of that date) directly in the page's
static HTML as plain <tr> markup, no JS rendering/pagination/API needed.

This is a SINGLE bulk fetch of the whole registry, not a per-entity network
loop — like scan_sources.py/mine_leads.py, safe to run directly/repeatedly
regardless of roster size. Not covered by CLAUDE.md's crawling-jobs policy.

A hit means the entity's ИНН appears as a certificated operator (№ СЭ,
base airport, registered aircraft models+counts) — this is direct evidence
of *operating* aircraft (not just manufacturing/selling them), a
meaningfully different fact than a products[] listing. Wire confirmed hits
into an entity's licences[] (or a new dedicated field if the shape doesn't
fit) via corrections_entities.json, not automatically.

Usage:
    python3 scripts/screen_favt_aviation_operators.py
    python3 scripts/screen_favt_aviation_operators.py --slug ooo-aeromaks
"""
from __future__ import annotations

import argparse
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTITIES = REPO / "data" / "registry" / "entities.json"
OUT = REPO / "data" / "registry" / "_favt_aviation_operator_hits.json"

PAGE_URL = "https://favt.gov.ru/dejatelnost-letnaya-eksplutacia-reestry-ekspluatantov-aviacionnye-raboty/"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36")

INN_RE = re.compile(r"ИНН\s*(\d{10,12})")


def strip_tags(html: str) -> str:
    return re.sub(r"<[^>]+>", " ", html)


def parse_rows(html: str) -> list[dict]:
    rows = re.findall(r"<tr>(.*?)</tr>", html, re.DOTALL)
    records = []
    for row in rows:
        cells = re.findall(r"<td>(.*?)</td>", row, re.DOTALL)
        if len(cells) < 6:
            continue
        cert_status = strip_tags(cells[1]).split()
        full_name_cell = strip_tags(cells[3])
        m = INN_RE.search(full_name_cell)
        if not m:
            continue
        records.append({
            "cert_info": " ".join(strip_tags(cells[1]).split()),
            "short_name": " ".join(strip_tags(cells[2]).split()),
            "full_name": full_name_cell.split("ИНН")[0].strip(),
            "inn": m.group(1),
            "base_airport": " ".join(strip_tags(cells[4]).split()),
            "aircraft": " ".join(strip_tags(cells[5]).split()) if len(cells) > 5 else "",
        })
    return records


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", action="append", default=[])
    args = ap.parse_args()

    entities = json.loads(ENTITIES.read_text(encoding="utf-8"))
    targets = [e for e in entities if e.get("inn")]
    if args.slug:
        targets = [e for e in targets if e["slug"] in args.slug]

    print(f"Fetching favt.gov.ru aviation-works operator registry ...")
    req = urllib.request.Request(PAGE_URL, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except urllib.error.URLError as e:
        print(f"ERROR fetching page: {e}")
        return 1

    records = parse_rows(html)
    print(f"{len(records)} operator records parsed; matching against {len(targets)} entity ИНН ...")

    by_inn: dict[str, list[dict]] = {}
    for r in records:
        by_inn.setdefault(r["inn"], []).append(r)

    hits = []
    for e in targets:
        matches = by_inn.get(e["inn"])
        if matches:
            hits.append({"slug": e["slug"], "inn": e["inn"], "org_name": e.get("name_ru"), "records": matches})
            print(f"  HIT {e['slug']} ({e['inn']}): {matches[0]['cert_info']}")

    print(f"\n{len(hits)} entity/entities with hit(s) out of {len(targets)} checked")
    OUT.write_text(json.dumps(hits, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
