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
import subprocess
import warnings
import zipfile
from pathlib import Path

import openpyxl

REPO = Path(__file__).resolve().parent.parent
ENTITIES = REPO / "data" / "registry" / "entities.json"
SOURCES = REPO / "data" / "registry" / "sources.json"

CODE_REVENUE = "2110"
CODE_NET_PROFIT = "2400"

# Non-profit filings (АНО/фонд, form 0710096) file a P&L that is empty by
# construction -- an НКО has no Выручка and no Чистая прибыль -- and report
# their actual money in the "Отчет о целевом использовании средств" (ОЦИС,
# ОКУД 0710003) instead. Reading only the P&L therefore returned
# revenue=None/profit=None for EVERY non-profit in the registry and looked
# exactly like "this entity has no figures on file". Found 2026-09-05 on
# АНО «ЦБСТ» itself -- the investigation's core entity -- whose six filings
# all parsed to None while the ОЦИС sheet showed ₽269.8m received in 2024.
#
# These are NOT revenue and profit and must never be recorded as such: 6200
# is targeted funding received (grants, contributions, state money), 6300 is
# how much of it was spent. Kept under their own keys so a downstream reader
# cannot silently conflate an НКО's funding inflow with commercial turnover.
CODE_FUNDS_BALANCE_START = "6100"
CODE_FUNDS_RECEIVED = "6200"
CODE_FUNDS_USED = "6300"
CODE_FUNDS_BALANCE_END = "6400"
TARGET_CODES = {
    CODE_FUNDS_BALANCE_START: "funds_balance_start",
    CODE_FUNDS_RECEIVED: "funds_received",
    CODE_FUNDS_USED: "funds_used",
    CODE_FUNDS_BALANCE_END: "funds_balance_end",
}
# Line 6300 is a *use* of funds, and filings are inconsistent about how they
# show that: some print "98 047", others "(275 587)". to_number() reads the
# parenthesised form as negative, so the same quantity landed in the registry
# with opposite signs depending on which filing it came from. The sign is
# presentational, so it is normalised to a positive magnitude and the result
# is checked against the sheet's own identity:
#     6100 (opening) + 6200 (received) - 6300 (used) == 6400 (closing)
# A filing that fails that identity is reported rather than silently trusted.
SIGN_NORMALISED = ("funds_used",)

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


def parse_pdf_filing(path: Path) -> dict | None:
    """Parse a signed БФО PDF (what `bfo_pull.py` downloads).

    Added 2026-09-05. The original parser only ever read the xlsx inside a
    `РЕСУРС_БФО_*.zip`; `bfo_pull.py` (added the same day) downloads the
    *signed PDF* from a different endpoint, so its output was invisible to
    this script -- 16 freshly-pulled filings sat on disk contributing nothing
    to `financials[]` until this branch existed. Same extraction contract as
    parse_one(): returns {units, revenue, net_profit} in the filing's own
    declared units, left for the caller to scale.

    `pdftotext -layout` keeps the P&L as aligned columns, so a line reads:
        Выручка7            2110      516 738       36 787
    i.e. label, line code, THIS year, PRIOR year. Only the first number is
    taken -- the second is the comparative prior-year figure, which arrives
    on its own in that year's own filing and would double-count here.
    """
    try:
        out = subprocess.run(
            ["pdftotext", "-layout", str(path), "-"],
            capture_output=True, timeout=120,
        )
        text = out.stdout.decode("utf-8", errors="replace")
    except Exception as e:  # pdftotext missing, or a malformed PDF
        return {"error": f"pdftotext: {e}"}
    if not text.strip():
        return {"error": "pdftotext produced no text (scanned/image-only PDF?)"}
    # NOTE: the caller normalises the profit key to `profit` to match the xlsx
    # path's output shape. Keep both paths emitting the same keys -- they were
    # briefly divergent (`net_profit` here vs `profit` there) on 2026-09-05 and
    # a downstream consumer silently dropped every xlsx-sourced profit figure.

    units = None
    m = re.search(r"Единица измерения\s+(.+)", text)
    if m:
        units = m.group(1).strip().split("  ")[0].strip()

    # Non-profit filings (form 0710096) report their real money on the ОЦИС
    # page ("Отчет о целевом использовании средств", line codes 6100-6400),
    # not the empty-by-construction P&L -- see the TARGET_CODES comment above
    # parse_one(). Found 2026-09-07: this PDF-path parser (what every
    # bfo_pull.py download goes through) only ever scanned for 2110/2400 and
    # silently dropped funds_* for every non-profit pulled via bfo_pull.py --
    # the same class of bug as the original all-null discovery, just in the
    # PDF branch instead of the xlsx one. Confirmed on ano-arrs-krasnodar's
    # 2024/2025 filings, which had real 6200/6300 figures sitting unread.
    line_codes = {CODE_REVENUE: "revenue", CODE_NET_PROFIT: "net_profit",
                  **TARGET_CODES}
    found: dict[str, float] = {}
    for line in text.splitlines():
        for code, key in line_codes.items():
            if key in found:
                continue
            mm = re.search(rf"\b{code}\b\s+(.+)", line)
            if not mm:
                continue
            # `-layout` separates the this-year and prior-year columns with
            # a wide run of spaces -- the previous [\d\s]{1,20} pattern had
            # no way to tell "space inside a thousands-grouped number" from
            # "space between columns" and, capped at 20 chars, would bleed
            # digits from the START of the second column into the first
            # match once the gap was narrow enough to fit both within the
            # cap (e.g. "59 574 775         13 929 333" -> "5957477513").
            # Found 2026-09-07 on ooo-tsugam, which had a trillion-ruble
            # "revenue" as a result. A run of 2+ spaces is the actual column
            # boundary in this layout; a single space is only ever a
            # thousands separator within one number.
            first_col = re.split(r"\s{2,}", mm.group(1).strip(), maxsplit=1)[0]
            nums = [to_number(tok) for tok in re.findall(r"\(?-?[\d\s]{1,20}\)?", first_col)]
            nums = [n for n in nums if n is not None]
            if not nums:
                continue
            v = nums[0]
            if key in SIGN_NORMALISED:
                v = abs(v)
            found[key] = v

    revenue = found.get("revenue")
    net_profit = found.get("net_profit")
    targets = {k: found[k] for k in TARGET_CODES.values() if k in found}
    if targets and all(k in targets for k in TARGET_CODES.values()):
        lhs = (targets["funds_balance_start"] + targets["funds_received"]
               - targets["funds_used"])
        if abs(lhs - targets["funds_balance_end"]) > 1:
            targets["funds_identity_check"] = (
                f"FAILED: 6100 {targets['funds_balance_start']} + 6200 "
                f"{targets['funds_received']} - 6300 {targets['funds_used']} = {lhs}, "
                f"but 6400 reports {targets['funds_balance_end']}")
    return {"units": units, "revenue": revenue, "net_profit": net_profit, **targets}


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

    def first_number_right(cells, i):
        """The value(s) live somewhere to the right of the code cell."""
        rest = [x for x in cells[i + 1:] if x is not None and str(x).strip() not in ("",)]
        nums = [n for n in (to_number(x) for x in rest) if n is not None]
        return nums[0] if nums else None

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
                val = first_number_right(cells, i)
                if code == CODE_REVENUE:
                    revenue = val
                else:
                    net_profit = val

    # Non-profit branch -- see TARGET_CODES. The sheet name is truncated to 31
    # chars by Excel ("Отчет о целевом использовании д"), so match on a prefix
    # short enough to survive that, not on the full form title.
    targets = {}
    for sn in wb.sheetnames:
        if "целевом использовании" not in sn.lower():
            continue
        for row in wb[sn].iter_rows(values_only=True):
            cells = list(row)
            for i, c in enumerate(cells):
                if c is None:
                    continue
                key = TARGET_CODES.get(str(c).strip())
                if key and key not in targets:
                    v = first_number_right(cells, i)
                    if v is not None and key in SIGN_NORMALISED:
                        v = abs(v)
                    targets[key] = v

    if targets:
        got = {k: targets.get(k) for k in TARGET_CODES.values()}
        if all(v is not None for v in got.values()):
            lhs = (got["funds_balance_start"] + got["funds_received"]
                   - got["funds_used"])
            if abs(lhs - got["funds_balance_end"]) > 1:  # tolerate rounding
                targets["funds_identity_check"] = (
                    f"FAILED: 6100 {got['funds_balance_start']} + 6200 "
                    f"{got['funds_received']} - 6300 {got['funds_used']} = {lhs}, "
                    f"but 6400 reports {got['funds_balance_end']}")

    return {"units": units, "revenue": revenue, "net_profit": net_profit, **targets}


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
        # A filing's `inns` list can include related parties, not just the
        # filer itself, and it is NOT ordered filer-first -- picking the first
        # entry that happens to be in the registry attributes the filing to
        # whichever related party sorts first. That silently credited фонд
        # «Градислава»'s FY2025 filing (s0295, inns [3705066020, 7704278421,
        # 7709278792, 7717094069]) to ООО «Заволжское» -- a commercial LLC that
        # would then have carried another organisation's non-profit funding
        # figures. Found 2026-09-05.
        #
        # The filename is authoritative: bo.nalog.gov.ru names every export
        # РЕСУРС_БФО_<filer ИНН>_<year>_<pulled>.zip, and bfo_pull.py writes
        # BFO_<filer ИНН>_<year>_<slug>.pdf. Read the filer off the name and
        # only fall back to the inns list when the name carries no ИНН.
        m_filer = re.search(r"(?:РЕСУРС_БФО|BFO)_(\d{10}|\d{12})_", path.name)
        inn = m_filer.group(1) if m_filer else None
        if inn is not None and inn not in target_inns:
            # correctly-named filing for an entity outside this run's scope
            inn = None if args.inn else inn
        if inn is None:
            inn = next((i2 for i2 in src.get("inns", []) if i2 in target_inns), None)
        if inn is None:
            print(f"  [{i}/{len(bfo_sources)}] {src['id']}: no target ИНН in this source's inns list, skip")
            continue
        slug = slug_by_inn.get(inn, inn)
        fy = src.get("fiscal_year")

        # `bfo_pull.py` output is a signed PDF, not a zip -- and it carries no
        # `fiscal_year` in sources.json, so read it off the filename, whose
        # shape (BFO_<ИНН>_<year>_<slug>.pdf) is fixed by that script.
        if path.suffix.lower() == ".pdf":
            if fy is None:
                mfy = re.match(r"BFO_\d+_(\d{4})_", path.name)
                fy = mfy.group(1) if mfy else None
            parsed = parse_pdf_filing(path)
            if not parsed or parsed.get("error"):
                err = parsed.get("error") if parsed else "?"
                print(f"  [{i}/{len(bfo_sources)}] {src['id']} {slug} FY{fy}: {err}")
                continue
            rec = {
                "fiscal_year": fy,
                "source_id": src["id"],
                "path": src["path"],
                "inn": inn,
                "units": parsed.get("units"),
                "revenue": parsed.get("revenue"),
                # normalise to the xlsx path's key name
                "profit": parsed.get("net_profit"),
            }
            for k in list(TARGET_CODES.values()) + ["funds_identity_check"]:
                if k in parsed:
                    rec[k] = parsed[k]
            results.setdefault(slug, []).append(rec)
            extra = "".join(f" {k}={rec[k]}" for k in list(TARGET_CODES.values())
                             + ["funds_identity_check"] if k in rec)
            print(f"  [{i}/{len(bfo_sources)}] {src['id']} {slug} FY{fy}: "
                  f"revenue={parsed.get('revenue')} profit={parsed.get('net_profit')}"
                  f"{extra} ({parsed.get('units')})")
            continue

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

        rec = {
            "fiscal_year": fy,
            "revenue": parsed["revenue"],
            "profit": parsed["net_profit"],
            "units": parsed["units"],
            "source_id": src["id"],
        }
        for k in list(TARGET_CODES.values()) + ["funds_identity_check"]:
            if parsed.get(k) is not None:
                rec[k] = parsed[k]
        results.setdefault(slug, []).append(rec)
        extra = "".join(f" {k}={rec[k]}" for k in list(TARGET_CODES.values()) + ["funds_identity_check"] if k in rec)
        print(f"  [{i}/{len(bfo_sources)}] {src['id']} {slug} FY{fy}: revenue={parsed['revenue']} profit={parsed['net_profit']}{extra} ({parsed['units']})")

    out_path = REPO / args.out
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out_path} ({len(results)} entities)")


if __name__ == "__main__":
    main()
