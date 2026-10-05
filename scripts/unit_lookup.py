#!/usr/bin/env python3
"""Resolve a free-text unit name to a record in data/registry/military_units.json.

  python3 scripts/unit_lookup.py "237-му гвардейскому десантно-штурмовому полку"
  python3 scripts/unit_lookup.py --check        # duplicates and handover recipients
  python3 scripts/unit_lookup.py --check --strict

States: resolved (one record, the query gave a type or arm that fits), ambiguous (several
records, or a bare number: a number alone never picks a unit), unrecorded (none). A parent
named in the query narrows the candidates; a record with no parent on file stays a candidate.
Local, no network.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import unit_names as un  # noqa: E402

REG = Path(__file__).resolve().parent.parent / "data" / "registry"


def load_units() -> list[dict]:
    return json.loads((REG / "military_units.json").read_text(encoding="utf-8"))


def lookup(text: str, units: list[dict]) -> dict:
    q = un.parse(text)
    by_slug = {u["slug"]: u for u in units}
    if q["vch"] and q["number"] is None:
        hit = [u for u in units if any(n.get("form") == "vch" and q["vch"] in n.get("value", "") for n in u.get("names") or [])
               or q["vch"] in (u.get("slug") or "")]
        return _answer(hit, q, None, False)
    if q["number"] is None:
        return {"state": "unrecorded", "query": q, "candidates": [], "why": "no unit number in the text"}
    cands, unstated = [], []
    for u in units:
        if not any(un.match(q, f) for f in un.forms(u)):
            continue
        parents = un.parents_of(u, by_slug)
        if q["parent"]:
            if parents and not any(un.match(q["parent"], p) for p in parents):
                continue
            if not parents:
                unstated.append(u["slug"])
        cands.append(u)
    specific = bool(q["kind"] or q["arm"])
    return _answer(cands, q, "bare number" if not specific else None, bool(unstated), unstated)


def _answer(cands: list[dict], q: dict, bare: str | None, parent_unstated: bool, unstated=()) -> dict:
    slugs = [u["slug"] for u in cands]
    if not cands:
        return {"state": "unrecorded", "query": q, "candidates": [], "why": "no record matches number, type and arm"}
    if bare or len(cands) > 1:
        why = ("a bare number never picks a unit; the text gives no type or arm" if bare == "bare number"
               else "several records fit; a parent formation, type or arm in the text would decide")
        return {"state": "ambiguous", "query": q, "candidates": slugs, "why": why}
    return {"state": "resolved", "query": q, "candidates": slugs, "parent_unstated": parent_unstated and bool(unstated),
            "why": "one record fits number, type and arm" + ("; the text names a parent the record does not state" if unstated else "")}


def find_duplicates(units: list[dict]) -> list[tuple[str, str]]:
    """Pairs of records that read as one unit: same number, compatible type and arm, parents not different."""
    by_slug = {u["slug"]: u for u in units}
    out = []
    for i, a in enumerate(units):
        for b in units[i + 1:]:
            for fa in un.forms(a):
                if any(un.match(fa, fb) for fb in un.forms(b)):
                    pa, pb = un.parents_of(a, by_slug), un.parents_of(b, by_slug)
                    if pa and pb and not any(un.match(x, y) for x in pa for y in pb):
                        break
                    out.append((a["slug"], b["slug"]))
                    break
    return out


def recipient_tally(units: list[dict], handovers: list[dict]) -> dict:
    """How the handovers' free-text recipients resolve: resolved, ambiguous, unrecorded counts."""
    tally = {"resolved": 0, "ambiguous": 0, "unrecorded": 0}
    for h in handovers:
        if h.get("recipient_raw"):
            tally[lookup(h["recipient_raw"], units)["state"]] += 1
    return tally


def check(units: list[dict], strict: bool = False) -> int:
    by_slug = {u["slug"]: u for u in units}
    problems = 0
    print("Possible duplicate records (same number, compatible type and arm, parents not different):")
    dups = find_duplicates(units)
    for a, b in dups:
        print(f"  {a}  /  {b}")
    problems += len(dups)
    if not dups:
        print("  none")
    h_path = REG / "handovers.json"
    if h_path.exists():
        tally = {"resolved": 0, "ambiguous": 0, "unrecorded": 0}
        print("Handover recipients:")
        for h in json.loads(h_path.read_text(encoding="utf-8")):
            raw = h.get("recipient_raw")
            if not raw:
                continue
            r = lookup(raw, units)
            tally[r["state"]] += 1
            slug = h.get("recipient_unit_slug")
            if slug and slug not in by_slug:
                print(f"  {h['id']}: recipient_unit_slug {slug!r} is not a unit")
                problems += 1
            elif slug and r["state"] == "resolved" and r["candidates"] != [slug]:
                print(f"  {h['id']}: slug {slug} but the text {raw!r} resolves to {r['candidates']}")
                problems += 1
            elif slug and r["state"] == "ambiguous" and slug not in r["candidates"]:
                print(f"  {h['id']}: slug {slug} is not among the candidates {r['candidates']} for {raw!r}")
                problems += 1
            elif not slug and r["state"] == "resolved":
                print(f"  {h['id']}: no slug set, the text {raw!r} resolves to {r['candidates'][0]}")
        print("  " + ", ".join(f"{k} {v}" for k, v in tally.items()))
    print(f"{problems} problem(s)")
    return 1 if strict and problems else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("text", nargs="?")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--strict", action="store_true", help="with --check: exit 1 on any problem")
    a = ap.parse_args()
    units = load_units()
    if a.check:
        return check(units, a.strict)
    if not a.text:
        ap.error("give a unit name or --check")
    r = lookup(a.text, units)
    q = r["query"]
    print(f"{r['state']}: {', '.join(r['candidates']) or '-'}")
    print(f"  read as: number {q['number']}, type {q['kind']}, arm {q['arm']}, parent "
          f"{q['parent'] and (q['parent']['number'], q['parent']['kind'], q['parent']['arm'])}, в/ч {q['vch']}")
    print(f"  {r['why']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
