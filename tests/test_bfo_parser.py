#!/usr/bin/env python3
"""Regression fixtures for scripts/parse_bfo_financials.py's parse_one().

No pytest dependency — plain assertions, run directly:
    python3 tests/test_bfo_parser.py

Exists because of the 2026-09-05 non-profit gap: an АНО/фонд files form
0710096, whose «Отчет о финансовых результатах» sheet is empty by
construction (an НКО has no Выручка and no Чистая прибыль). The parser read
only that sheet, so every non-profit in the registry returned
revenue=None/profit=None — indistinguishable from "no filing on file". It hid
₽269.8m of FY2024 targeted funding for АНО «ЦБСТ», the investigation's core
entity, whose six filings sat in data/sources/ contributing nothing.

Two things this locks down, both of which were real defects:
  1. the ОЦИС sheet (ОКУД 0710003) is read at all, under funds_* keys that
     cannot be mistaken for revenue/profit;
  2. line 6300 «Использовано средств» is sign-normalised — filings print it
     both bare ("98 047") and parenthesised ("(275 587)"), and to_number()
     reads the parenthesised form as negative, so the same quantity was
     landing in the registry with opposite signs depending on the filing.

Run after any change to parse_one() or the TARGET_CODES/SIGN_NORMALISED
handling.
"""
import sys
from pathlib import Path

from openpyxl import Workbook

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from parse_bfo_financials import parse_one  # noqa: E402

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
FIXTURES_DIR.mkdir(exist_ok=True)


def build(path, rows_pl, rows_target, units="Тыс. руб."):
    """Write a minimal 0710096-shaped workbook.

    Sheet titles match what Excel actually produces: the ОЦИС sheet name is
    truncated to 31 characters, which is why the parser matches on a prefix
    rather than the full form title.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Сведения об организации"
    ws.append(["Единица измерения", units])
    pl = wb.create_sheet("Отчет о финансовых результатах")
    pl.append(["Пояснения", "Наименование показателя", "Код строки", "2024", "2023"])
    for r in rows_pl:
        pl.append(r)
    if rows_target is not None:
        tg = wb.create_sheet("Отчет о целевом использовании д")
        tg.append(["Пояснения", "Наименование показателя", "Код строки", "2024", "2023"])
        for r in rows_target:
            tg.append(r)
    wb.save(path)
    return path


# --- 1. non-profit, funds used printed BARE --------------------------------
# Modelled on АНО «ЦБСТ» FY2024 (s0384): empty P&L, real money in the ОЦИС.
p = build(
    FIXTURES_DIR / "bfo_nonprofit_bare.xlsx",
    rows_pl=[[None, "Выручка", "2110", "-", "-"],
             [None, "Чистая прибыль (убыток)", "2400", "-", "-"]],
    rows_target=[[None, "Остаток средств на начало отчетного года", "6100", "0", "-"],
                 [None, "Поступило средств", "6200", "269 835", "-"],
                 [None, "Использовано средств", "6300", "98 047", "-"],
                 [None, "Остаток средств на конец отчетного года", "6400", "171 788", "-"]],
)
got = parse_one(p)
assert got["units"] == "Тыс. руб.", got
assert got["revenue"] is None, got          # genuinely absent, not unread
assert got["net_profit"] is None, got
assert got["funds_received"] == 269835.0, got
assert got["funds_used"] == 98047.0, got
assert got["funds_balance_end"] == 171788.0, got
assert "funds_identity_check" not in got, got

# --- 2. same figures, funds used PARENTHESISED -----------------------------
# Modelled on АНО «ЦБСТ» FY2025 (s0387). Must yield the same positive
# magnitude as case 1's bare form, and still satisfy the balance identity.
p = build(
    FIXTURES_DIR / "bfo_nonprofit_parens.xlsx",
    rows_pl=[[None, "Выручка", "2110", "-", "-"]],
    rows_target=[[None, "Остаток средств на начало отчетного года", "6100", "171 788", "-"],
                 [None, "Поступило средств", "6200", "137 105", "-"],
                 [None, "Использовано средств", "6300", "(275 587)", "-"],
                 [None, "Остаток средств на конец отчетного года", "6400", "33 306", "-"]],
)
got = parse_one(p)
assert got["funds_used"] == 275587.0, f"sign not normalised: {got}"
assert got["funds_balance_start"] == 171788.0, got
assert "funds_identity_check" not in got, got

# --- 3. a broken filing must be REPORTED, not silently trusted -------------
p = build(
    FIXTURES_DIR / "bfo_nonprofit_broken.xlsx",
    rows_pl=[],
    rows_target=[[None, "Остаток средств на начало отчетного года", "6100", "0", "-"],
                 [None, "Поступило средств", "6200", "100", "-"],
                 [None, "Использовано средств", "6300", "10", "-"],
                 [None, "Остаток средств на конец отчетного года", "6400", "999", "-"]],
)
got = parse_one(p)
assert "FAILED" in got.get("funds_identity_check", ""), got

# --- 4. commercial filing still parses, and grows no funds_* keys ----------
p = build(
    FIXTURES_DIR / "bfo_commercial.xlsx",
    rows_pl=[[None, "Выручка", "2110", "21 328", "10 930"],
             [None, "Чистая прибыль (убыток)", "2400", "422", "660"]],
    rows_target=None,
)
got = parse_one(p)
assert got["revenue"] == 21328.0, got       # this year, not the prior-year column
assert got["net_profit"] == 422.0, got
assert not any(k.startswith("funds_") for k in got), got

print("all BFO parser fixtures pass")
