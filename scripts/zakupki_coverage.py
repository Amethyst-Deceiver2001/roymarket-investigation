#!/usr/bin/env python3
"""One-command answer to "are we done with zakupki?" — collapses the five
ad-hoc cross-reference scripts written across the 2026-08-29 session (scan
log vs entities.json/people.json ИНН, hit_count vs archived contract cards,
archived contract cards vs government_contracts[] wiring, ZAKUPKI_ATTACH_
filename prefixes vs entities with fetch-documents run) into one repeatable,
cheap report.

Local file processing only — reads registry JSON + data/sources/ filenames,
no network calls — safe to run directly/repeatedly, same category as
mine_zakupki.py/scan_sources.py.

Usage:
    python3 scripts/zakupki_coverage.py                # full report
    python3 scripts/zakupki_coverage.py --gaps-only      # only rows needing action
"""
import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REGISTRY = REPO / "data" / "registry"
SOURCES = REPO / "data" / "sources"
sys.path.insert(0, str(REPO / "scripts"))  # for the lazy mine_zakupki import below


def load(name):
    path = REGISTRY / name
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def archived_contract_regs():
    regs = set()
    for f in SOURCES.glob("ZAKUPKI_contract_*.html"):
        parts = f.stem.split("_")
        if len(parts) >= 3:
            regs.add(parts[2])
    return regs


def archived_document_keys():
    """Keys ZAKUPKI_ATTACH_<key>_... files are named under — either an ИНН
    or a bare regNumber, depending on how fetch-documents was invoked."""
    keys = set()
    for f in SOURCES.glob("ZAKUPKI_ATTACH_*"):
        m = re.match(r"ZAKUPKI_ATTACH_([^_]+)_", f.name)
        if m:
            keys.add(m.group(1))
    return keys


# high_value (below) only ever looks at already-wired government_contracts[]
# — an entity with a large raw scan-log hit_count but ZERO wired contracts
# (e.g. gk-rostekh: 45 hits, 0 wired) can never trip it, which is exactly
# backwards: an entity nobody has read yet is the one most in need of a
# first pass, not one this tool should stay silent about. Found 2026-08-30
# auditing this script for a coverage-completeness plan.
HIT_COUNT_PRIORITY_THRESHOLD = 10  # calibrated against gk-rostekh's 45 hits,
                                   # with headroom below it
DEFENSE_KEYWORD_RE = re.compile(
    r'оборон|войсковая часть|\bв/ч ?\d|минобороны|росгвард|рособоронэкспорт|фсб|фсо',
    re.IGNORECASE,
)


def sample_customer_keywords(reg_numbers: set, archived_regs: set, sample_size: int = 5) -> bool:
    """Cheap keyword scan over up to sample_size already-archived-but-unwired
    contract cards — no fetch-documents pass, no full mine_zakupki run.
    mine_zakupki is imported lazily so entities that don't need this path
    (i.e. already have wired contracts) pay no bs4 import cost."""
    candidates = sorted(reg_numbers & archived_regs)[:sample_size]
    if not candidates:
        return False
    from mine_zakupki import parse_contract_card_html
    for reg in candidates:
        for f in SOURCES.glob(f"ZAKUPKI_contract_{reg}_*.html"):
            card = parse_contract_card_html(f)
            if card and DEFENSE_KEYWORD_RE.search(
                    card["fields"].get("Полное наименование заказчика", "")):
                return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gaps-only", action="store_true",
                     help="only print rows with unscanned/unfetched/unwired gaps")
    args = ap.parse_args()

    entities = load("entities.json")
    people = load("people.json")
    scan_log = load("_zakupki_scan_log.json")

    targets = []
    for e in entities:
        if e.get("inn"):
            targets.append({"inn": e["inn"], "slug": e.get("slug"), "kind": "entity",
                             "name": e.get("name_ru"), "gc": e.get("government_contracts", [])})
    for p in people:
        if p.get("inn_personal"):
            targets.append({"inn": p["inn_personal"], "slug": p.get("slug"), "kind": "person",
                             "name": p.get("fio_ru"), "gc": []})

    archived_regs = archived_contract_regs()
    doc_keys = archived_document_keys()

    print(f"{len(targets)} ИНН in registry (entities + people)\n")

    n_unscanned = n_partial_fetch = n_no_docs_high_value = n_no_docs_high_value_candidate = 0
    rows = []
    for t in targets:
        entry = scan_log.get(t["inn"])
        if not entry:
            rows.append((t, "UNSCANNED", None, None))
            n_unscanned += 1
            continue
        hit_count = entry.get("hit_count", 0)
        if hit_count == 0:
            if not args.gaps_only:
                rows.append((t, "zero-hit", 0, 0))
            continue
        reg_numbers = set(entry.get("reg_numbers", []))
        fetched = reg_numbers & archived_regs
        fetch_status = "FULL" if len(fetched) == len(reg_numbers) else "PARTIAL"
        if fetch_status == "PARTIAL":
            n_partial_fetch += 1
        wired_regs = {gc.get("reg_number") for gc in t["gc"] if gc.get("reg_number")}
        has_docs = bool(reg_numbers & doc_keys) or t["inn"] in doc_keys
        total_value = sum(gc.get("value_rub") or 0 for gc in t["gc"])
        high_value = total_value > 10_000_000 or any(
            "оборон" in (gc.get("customer") or "").lower() or "свo" in (gc.get("items") or "").lower()
            or "специальной военной операции" in (gc.get("items") or "").lower()
            for gc in t["gc"]
        )
        # Zero-wired blind spot: high_value above can never fire with an
        # empty wired_regs (nothing in t["gc"] to check keywords/value on) —
        # exactly the entities most needing a first read. Raw hit_count
        # magnitude or a cheap keyword scan over a few already-archived
        # unwired cards substitutes for the missing wired-contract signal.
        high_value_candidate = False
        if not wired_regs:
            high_value_candidate = (hit_count >= HIT_COUNT_PRIORITY_THRESHOLD
                                     or sample_customer_keywords(reg_numbers, archived_regs))
        if high_value and not has_docs:
            n_no_docs_high_value += 1
        elif high_value_candidate and not has_docs:
            n_no_docs_high_value_candidate += 1
        rows.append((t, f"{fetch_status} ({len(fetched)}/{len(reg_numbers)})",
                     hit_count, len(wired_regs), has_docs, high_value, high_value_candidate))

    for row in rows:
        t = row[0]
        if row[1] == "UNSCANNED":
            print(f"  UNSCANNED   {t['inn']:15} {t['kind']:8} {t['slug']}")
        elif row[1] == "zero-hit":
            print(f"  zero-hit    {t['inn']:15} {t['kind']:8} {t['slug']}")
        else:
            _, status, hit_count, wired_count, has_docs, high_value, high_value_candidate = row
            flag = ""
            if high_value and not has_docs:
                flag = "  <-- high-value, no fetch-documents yet"
            elif high_value_candidate and not has_docs:
                flag = "  <-- high-value CANDIDATE (0 wired, raw hit_count/keyword) — needs a first read"
            if not args.gaps_only or flag:
                print(f"  {status:16} hits={hit_count:<4} wired={wired_count:<3} "
                      f"docs={'Y' if has_docs else 'N'}  {t['inn']:15} {t['slug']}{flag}")

    print(f"\n--- summary ---")
    print(f"never scanned:                        {n_unscanned}")
    print(f"partial fetch-contracts:               {n_partial_fetch}")
    print(f"high-value, no documents:              {n_no_docs_high_value}")
    print(f"high-value candidate, no documents:    {n_no_docs_high_value_candidate}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
