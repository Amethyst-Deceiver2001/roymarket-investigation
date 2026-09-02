#!/usr/bin/env python3
"""Cluster an entity/person's already-archived-but-unwired zakupki contract
cards by customer name, to surface recurring-relationship patterns without
requiring a human to read every card by hand.

Built 2026-08-30 generalizing the single biggest manual-recovery win of that
session: reading 83 previously-unwired (but already-fetched) contract cards
for ao-nii-stt by hand surfaced that 49 of them were the same customer (ФГКУ
«Войсковая часть 35533», identified via a separate OSINT source as an
FSB-linked institute) totaling ₽178.4m, plus another 18 with regional МВД
directorates totaling ₽22.35m — both patterns invisible in the registry
until that manual read. This script reproduces that read mechanically: for
any entity/person, diff scanned reg_numbers (from
data/registry/_zakupki_scan_log.json, via mine_zakupki.reg_numbers_for_inn)
against archived cards (data/sources/ZAKUPKI_contract_<reg>_*.html) against
already-wired reg_numbers (entities.json's government_contracts[]), parse
each remaining unwired card's customer/value/date via mine_zakupki's own
parse_contract_card_html, and group by normalized customer name.

Local file processing only — reads registry JSON + already-archived
data/sources/ files, no network calls — safe to run directly/repeatedly,
same category as mine_zakupki.py/zakupki_coverage.py/zakupki_signatory_diff.py.

Usage:
    python3 scripts/zakupki_customer_clusters.py --inn 6730046954
    python3 scripts/zakupki_customer_clusters.py --all [--min-count 3]
    python3 scripts/zakupki_customer_clusters.py --all --out report.md
"""
import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REGISTRY = REPO / "data" / "registry"
SOURCES = REPO / "data" / "sources"
sys.path.insert(0, str(REPO / "scripts"))
from mine_zakupki import parse_contract_card_html, reg_numbers_for_inn  # noqa: E402
from id_patterns import norm  # noqa: E402

RUB_CLEAN_RE = re.compile(r'[^\d,.\s]')
DATE_RE = re.compile(r'\d{2}\.\d{2}\.\d{4}')


def parse_rub(raw: str | None) -> float | None:
    """'45 500 000,00 ₽' -> 45500000.0. None on anything that doesn't
    reduce to a plain number (blank/cancelled-contract cards)."""
    if not raw:
        return None
    s = RUB_CLEAN_RE.sub("", raw).replace(" ", "").replace("\xa0", "")
    parts = s.rsplit(",", 1)
    s = ".".join(parts) if len(parts) == 2 else parts[0]
    try:
        return float(s)
    except ValueError:
        return None


def archived_contract_regs() -> set[str]:
    regs = set()
    for f in SOURCES.glob("ZAKUPKI_contract_*.html"):
        parts = f.stem.split("_")
        if len(parts) >= 3:
            regs.add(parts[2])
    return regs


def unwired_archived_regs(inn: str, wired: set[str]) -> set[str]:
    """scanned ∩ archived − already wired, for one supplier ИНН."""
    scanned = reg_numbers_for_inn(inn)
    if not scanned:
        return set()
    return (scanned & archived_contract_regs()) - wired


def card_summary(reg: str) -> dict | None:
    """Locate the archived ZAKUPKI_contract_<reg>_*.html and pull
    customer/value/date via mine_zakupki's own parse_contract_card_html —
    no re-parsing logic duplicated here."""
    matches = sorted(SOURCES.glob(f"ZAKUPKI_contract_{reg}_*.html"))
    if not matches:
        return None
    card = parse_contract_card_html(matches[0])
    if card is None:
        return None
    f = card["fields"]
    customer = f.get("Полное наименование заказчика") or f.get("Заказчик")
    value = parse_rub(f.get("Цена контракта"))
    date_field = (f.get("Дата заключения контракта")
                  or f.get("Дата размещения (по местному времени)") or "")
    date_m = DATE_RE.search(date_field)
    return {"reg": reg, "customer": customer, "value_rub": value,
            "date": date_m.group(0) if date_m else None}


def cluster_by_customer(cards: list[dict]) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = {}
    for c in cards:
        if not c.get("customer"):
            continue
        groups.setdefault(norm(c["customer"]), []).append(c)
    return groups


def report_for_target(inn: str, slug: str, wired: set[str], min_count: int) -> str:
    regs = unwired_archived_regs(inn, wired)
    cards = [c for c in (card_summary(r) for r in sorted(regs)) if c]
    groups = cluster_by_customer(cards)
    lines = [f"# Unwired-card customer clusters — {slug} ({inn}) — "
             f"{len(cards)} unwired archived card(s)\n"]

    recurring = {k: v for k, v in groups.items() if len(v) >= min_count}
    for key, recs in sorted(recurring.items(), key=lambda kv: -sum(r["value_rub"] or 0 for r in kv[1])):
        total = sum(r["value_rub"] or 0 for r in recs)
        dates = sorted(r["date"] for r in recs if r["date"])
        display = recs[0]["customer"]
        date_range = f", {dates[0]}–{dates[-1]}" if dates else ""
        lines.append(f"## RECURRING: {display} — {len(recs)} contracts, "
                      f"₽{total:,.0f} total{date_range}")
        lines.append(", ".join(r["reg"] for r in recs))
        lines.append("")

    other = {k: v for k, v in groups.items() if len(v) < min_count}
    if other:
        lines.append(f"## {sum(len(v) for v in other.values())} other unwired "
                      f"card(s), not recurring (<{min_count}x)\n")
    if not cards:
        lines.append("(no unwired archived cards for this ИНН)\n")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inn", help="cluster just this one ИНН")
    ap.add_argument("--all", action="store_true", help="every registry ИНН with an archived unwired card")
    ap.add_argument("--min-count", type=int, default=3,
                     help="minimum contract count to flag a customer as recurring (default 3)")
    ap.add_argument("--out")
    args = ap.parse_args()

    if not args.inn and not args.all:
        print("pass --inn <ИНН> or --all", file=sys.stderr)
        return 1

    entities = json.loads((REGISTRY / "entities.json").read_text(encoding="utf-8"))
    people = json.loads((REGISTRY / "people.json").read_text(encoding="utf-8"))

    targets = []
    for e in entities:
        if e.get("inn"):
            wired = {gc.get("reg_number") for gc in e.get("government_contracts", []) or []
                     if gc.get("reg_number")}
            targets.append((e["inn"], e.get("slug"), wired))
    for p in people:
        if p.get("inn_personal"):
            targets.append((p["inn_personal"], p.get("slug"), set()))

    if args.inn:
        targets = [t for t in targets if t[0] == args.inn]
        if not targets:
            print(f"ИНН {args.inn} not found in registry", file=sys.stderr)
            return 1

    reports = []
    for inn, slug, wired in targets:
        r = report_for_target(inn, slug, wired, args.min_count)
        if "no unwired archived cards" not in r:
            reports.append(r)

    output = "\n".join(reports) if reports else "(nothing to report)\n"
    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
        print(f"wrote {args.out} ({len(reports)} target(s) with unwired cards)")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
