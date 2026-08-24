#!/usr/bin/env python3
"""Extract revenue/net-profit from the БФО (bo.nalog.gov.ru) xlsx filings
already on file in data/sources/, for every registry entity that has one.

Local file processing only (reads already-downloaded zips) — no network
calls, safe to run directly/repeatedly per CLAUDE.md's crawling-jobs policy.

БФО xlsx has 3 sheets: "Сведения об организации" (name/address/units),
"Бухгалтерский баланс", and "Отчет о финансовых результатах" (P&L) — the
"Отчет..." sheet's layout varies slightly between the simplified (0710096)
and full (0710002) forms, so this scans every row for cells matching the
line codes rather than assuming a fixed column, and reads the two adjacent
numeric-looking cells to the right as (this-year, prior-year).

Units: filings are almost always "Тыс. руб." (thousands of rubles) — this
script reads that from "Сведения об организации" and reports revenue/profit
in actual rubles (value * 1000) plus records `units_source` so a downstream
reader isn't guessing; a filing that reports full rubles keeps its own
declared scale. See memory: verify_bfo_units_against_known_figure.

Usage:
    python3 scripts/parse_bfo_financials.py                    # all entities with a БФО file on record
    python3 scripts/parse_bfo_financials.py --inn 7743451768    # one entity
    python3 scripts/parse_bfo_financials.py --out data/registry/_bfo_financials.json
"""
from __future__ import annotations

import argparse
import json
import re
import warnings
import zipfile
from pathlib import Path

import openpyxl

REPO = Path(__file__).resolve().parent.parent
ENTITIES = REPO / "data" / "registry" / "entities.json"
SOURCES = REPO / "data" / "registry" / "sources.json"

CODE_REVENUE = "2110"
CODE_NET_PROFIT = "2400"

NUM_RE = re.compile(r"^\(?-?[\d\s]+\)?$")


def to_number(cell) -> float | None:
    if cell is None:
        return None
    s = str(cell).strip()
    if s in ("-", "", "—"):
        return None
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()").replace(" ", "").replace("\xa0", "")
    if not s or not NUM_RE.match(s.replace(" ", "")):
        try:
            v = float(s)
        except ValueError:
            return None
    else:
        try:
            v = float(s)
        except ValueError:
            return None
    return -v if neg else v


def parse_one(path: Path) -> dict | None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            wb = openpyxl.load_workbook(path, data_only=True)
        except Exception as e:
            return {"error": str(e)}

    units = None
    for sn in wb.sheetnames:
        if "сведения" in sn.lower():
            for row in wb[sn].iter_rows(values_only=True):
                cells = [c for c in row if c is not None]
                if cells and "Единица измерения" in str(cells[0]):
                    units = str(cells[-1]).strip()
            break

    revenue = net_profit = None
    for sn in wb.sheetnames:
        if "финансовых результат" not in sn.lower():
            continue
        ws = wb[sn]
        for row in ws.iter_rows(values_only=True):
            cells = list(row)
            for i, c in enumerate(cells):
                if c is None:
                    continue
                code = str(c).strip()
                if code not in (CODE_REVENUE, CODE_NET_PROFIT):
                    continue
                # the value(s) live somewhere to the right of the code cell
                rest = [x for x in cells[i + 1:] if x is not None and str(x).strip() not in ("",)]
                nums = [to_number(x) for x in rest]
                nums = [n for n in nums if n is not None]
                val = nums[0] if nums else None
                if code == CODE_REVENUE:
                    revenue = val
                else:
                    net_profit = val
    return {"units": units, "revenue": revenue, "net_profit": net_profit}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--inn", default=None)
    ap.add_argument("--out", default="data/registry/_bfo_financials.json")
    args = ap.parse_args()

    entities = json.loads(ENTITIES.read_text(encoding="utf-8"))
    sources = json.loads(SOURCES.read_text(encoding="utf-8"))

    target_inns = {e["inn"] for e in entities if e.get("inn")}
    if args.inn:
        target_inns = {args.inn}

    bfo_sources = [s for s in sources if s.get("type") == "bfo" and any(i in target_inns for i in s.get("inns", []))]
    print(f"{len(bfo_sources)} БФО filings to parse across {len(target_inns)} target ИНН")

    slug_by_inn = {e["inn"]: e.get("slug") for e in entities if e.get("inn")}
    results: dict[str, list[dict]] = {}

    for i, src in enumerate(bfo_sources, 1):
        path = REPO / src["path"]
        # a filing's `inns` list can include related parties, not just the
        # filer itself — pick the one that's actually the target entity's own
        inn = next((i2 for i2 in src.get("inns", []) if i2 in target_inns), None)
        if inn is None:
            print(f"  [{i}/{len(bfo_sources)}] {src['id']}: no target ИНН in this source's inns list, skip")
            continue
        slug = slug_by_inn.get(inn, inn)
        fy = src.get("fiscal_year")

        # БФО zips hold one xlsx member
        try:
            with zipfile.ZipFile(path) as z:
                names = [n for n in z.namelist() if n.lower().endswith(".xlsx")]
                if not names:
                    print(f"  [{i}/{len(bfo_sources)}] {src['id']} {slug}: no xlsx member, skip")
                    continue
                tmp = Path("/tmp") / Path(names[0]).name
                tmp.write_bytes(z.read(names[0]))
        except Exception as e:
            print(f"  [{i}/{len(bfo_sources)}] {src['id']} {slug}: zip error {e}")
            continue

        parsed = parse_one(tmp)
        tmp.unlink(missing_ok=True)
        if not parsed or parsed.get("error"):
            print(f"  [{i}/{len(bfo_sources)}] {src['id']} {slug} FY{fy}: parse error {parsed.get('error') if parsed else '?'}")
            continue

        results.setdefault(slug, []).append({
            "fiscal_year": fy,
            "revenue": parsed["revenue"],
            "profit": parsed["net_profit"],
            "units": parsed["units"],
            "source_id": src["id"],
        })
        print(f"  [{i}/{len(bfo_sources)}] {src['id']} {slug} FY{fy}: revenue={parsed['revenue']} profit={parsed['net_profit']} ({parsed['units']})")

    out_path = REPO / args.out
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out_path} ({len(results)} entities)")


if __name__ == "__main__":
    main()
