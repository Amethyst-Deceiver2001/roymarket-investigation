#!/usr/bin/env python3
"""Per-entity coverage matrix across every source/screening dimension.

**Why this exists.** On 2026-09-05 the same session claimed three times that
an entity was an uncovered gap ("ГК «Логос» has no ИНН", "ООО «Воздушный
трактат» is not in entities.json", "ООО «МЛ Констракшнс» not cross-checked")
when all three were already fully covered in `data/registry/`. Each claim came
from stale working memory rather than a read of the actual record. That is a
recurring, systematic failure mode -- an investigation this size cannot be held
in a head, and "have we checked X against Y?" must be a query, not a
recollection.

So: this script answers that question mechanically. It reads only
`data/registry/*.json` and reports, per entity, which of the ~20 coverage
dimensions are satisfied. Nothing here is a judgement call; every dimension is
a field-presence test whose rule is stated in DIMENSIONS below.

Local file processing over already-generated registry JSON -- no network calls,
safe to run directly/repeatedly (same class as `mine_leads.py`/`check_registry.py`).

Usage:
    python3 scripts/coverage_report.py                     # summary + gap queues
    python3 scripts/coverage_report.py --slug ooo-gagaring # one entity, verbose
    python3 scripts/coverage_report.py --top 25            # best-covered first
    python3 scripts/coverage_report.py --missing bfo       # work queue for one dimension
    python3 scripts/coverage_report.py --tier manufacturer --min-score 0
    python3 scripts/coverage_report.py --out report.md     # markdown table

**Read the gap queues as work queues, not as findings.** A missing dimension
means "not recorded", which is usually "not checked" but is sometimes "checked,
legitimately empty" -- a dormant shell really has no contracts, a 3-week-old
company really has no filed accounts. Where the distinction matters, the
`*_screened_at` timestamp dimensions separate the two: a null `screened_at` is
genuinely unchecked, whereas `screened_at` set with an empty `matches[]` is a
real, citable negative result. Prefer adding a screened_at-style timestamp to
any new check for exactly this reason.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REG = ROOT / "data" / "registry"


def load(name: str):
    return json.loads((REG / f"{name}.json").read_text(encoding="utf-8"))


def _nonempty(v) -> bool:
    """True if a field carries real content (not None/[]/{}/'')."""
    if v is None:
        return False
    if isinstance(v, (list, dict, str)):
        return len(v) > 0
    return True


# Each dimension: (key, group, label, predicate over the entity dict).
# Grouped so the summary can report "identity 8/8, screening 3/8" rather than
# one undifferentiated percentage -- the groups fail for different reasons and
# are closed by different tools.
DIMENSIONS: list[tuple[str, str, str, object]] = [
    # --- identity: who is this legal entity, per the primary registry ---
    ("inn",        "identity", "ИНН",              lambda e: _nonempty(e.get("inn"))),
    ("ogrn",       "identity", "ОГРН",             lambda e: _nonempty(e.get("ogrn"))),
    ("address",    "identity", "address",          lambda e: _nonempty(e.get("address"))),
    ("okved",      "identity", "ОКВЭД",            lambda e: _nonempty(e.get("okved_code"))),
    ("director",   "identity", "director",         lambda e: _nonempty(e.get("director"))),
    ("founders",   "identity", "founders",         lambda e: _nonempty(e.get("founders"))),
    ("capital",    "identity", "charter capital",  lambda e: _nonempty(e.get("charter_capital"))),
    ("registered", "identity", "reg. date",        lambda e: _nonempty(e.get("registered"))),
    # --- financial ---
    ("bfo",        "financial", "БФО financials",  lambda e: _nonempty(e.get("financials"))),
    # --- screening: every screen_*.py has a matching *_screened_at stamp ---
    ("opensanctions", "screening", "OpenSanctions", lambda e: _nonempty(e.get("opensanctions_screened_at"))),
    ("gur",           "screening", "GUR war-sanctions", lambda e: _nonempty(e.get("gur_screened_at"))),
    ("gur_components","screening", "GUR components",    lambda e: _nonempty(e.get("gur_components_screened_at"))),
    ("aleph",         "screening", "Aleph/OCCRP",       lambda e: _nonempty(e.get("aleph_screened_at"))),
    ("rk2035",        "screening", "rk2035 БАС reg.",   lambda e: _nonempty(e.get("rk2035_screened_at"))),
    ("rospatent",     "screening", "Rospatent (dir.)",  lambda e: _nonempty(e.get("rospatent_director_screened_at"))),
    ("wb",            "screening", "WB/marketplace",    lambda e: _nonempty(e.get("wb_screened_at"))),
    ("securing",      "screening", "ФНС обеспеч. меры", lambda e: _nonempty(e.get("securing_measures_checked_at"))),
    # --- activity / evidence: what the entity actually does ---
    ("products",   "activity", "products",          lambda e: _nonempty(e.get("products"))),
    ("zakupki",    "activity", "gov. contracts",    lambda e: _nonempty(e.get("government_contracts"))),
    ("ip",         "activity", "patents/TMs",       lambda e: _nonempty(e.get("patents")) or _nonempty(e.get("trademarks"))),
    ("web",        "activity", "web/social",        lambda e: any(_nonempty(v) for v in (e.get("web") or {}).values())),
    ("marketing",  "activity", "marketing claims",  lambda e: _nonempty(e.get("marketing_claims"))),
    ("battlefield","activity", "battlefield evid.", lambda e: _nonempty(e.get("battlefield_evidence"))),
    ("images",     "activity", "images",            lambda e: _nonempty(e.get("images"))),
    # --- analysis: the investigation's own conclusions, sourced ---
    ("cbst_tie",   "analysis", "ЦБСТ tie stated",   lambda e: _nonempty((e.get("cbst_tie") or {}).get("claim") if isinstance(e.get("cbst_tie"), dict) else e.get("cbst_tie"))),
    ("tier_basis", "analysis", "tier basis",        lambda e: _nonempty(e.get("tier_basis"))),
    ("sanctions",  "analysis", "sanctions checked", lambda e: _nonempty(e.get("sanctions"))),
]

GROUPS = ["identity", "financial", "screening", "activity", "analysis"]


def score(entity: dict) -> dict:
    """Return {dim_key: bool} plus per-group and total tallies."""
    hits = {key: bool(pred(entity)) for key, _grp, _lbl, pred in DIMENSIONS}
    by_group: dict[str, tuple[int, int]] = {}
    for grp in GROUPS:
        keys = [k for k, g, _l, _p in DIMENSIONS if g == grp]
        by_group[grp] = (sum(hits[k] for k in keys), len(keys))
    return {
        "hits": hits,
        "by_group": by_group,
        "total": sum(hits.values()),
        "max": len(DIMENSIONS),
    }


def entity_sources_map():
    """Map slug -> count of archived primary documents citing its ИНН.

    Reuses reverse_source_index so the definition of "a source cites this
    entity" stays in one place rather than being reimplemented here.
    """
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from reverse_source_index import build_index  # noqa: E402
    except Exception:
        return {}
    ent, _ppl, _refs = build_index(load("entities"), load("people"), load("sources"))
    return {k: len(set(v)) for k, v in ent.items()}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--slug", help="report one entity in full")
    ap.add_argument("--tier", help="restrict to one tier")
    ap.add_argument("--top", type=int, help="show N best-covered entities")
    ap.add_argument("--missing", help="list entities missing this dimension key (work queue)")
    ap.add_argument("--min-score", type=int, default=None, help="only entities at/above this total")
    ap.add_argument("--out", help="write a markdown table here")
    args = ap.parse_args()

    entities = load("entities")
    srcmap = entity_sources_map()

    if args.tier:
        entities = [e for e in entities if e.get("tier") == args.tier]

    scored = []
    for e in entities:
        s = score(e)
        s["slug"] = e["slug"]
        s["name"] = e.get("name_ru") or e["slug"]
        s["tier"] = e.get("tier")
        s["inn"] = e.get("inn")
        s["docs"] = srcmap.get(e["slug"], 0)
        scored.append(s)

    # --- single entity ---
    if args.slug:
        match = [s for s in scored if s["slug"] == args.slug]
        if not match:
            print(f"no entity with slug {args.slug!r}", file=sys.stderr)
            return 1
        s = match[0]
        print(f"{s['name']}  [{s['slug']}]  ИНН {s['inn'] or '—'}  tier={s['tier']}")
        print(f"coverage {s['total']}/{s['max']}   archived documents citing it: {s['docs']}\n")
        for grp in GROUPS:
            got, tot = s["by_group"][grp]
            print(f"  {grp:10s} {got}/{tot}")
            for key, g, label, _p in DIMENSIONS:
                if g != grp:
                    continue
                print(f"      {'YES' if s['hits'][key] else ' - '}  {label}")
        return 0

    # --- work queue for one dimension ---
    if args.missing:
        keys = {k for k, _g, _l, _p in DIMENSIONS}
        if args.missing not in keys:
            print(f"unknown dimension {args.missing!r}. known: {', '.join(sorted(keys))}", file=sys.stderr)
            return 1
        gaps = [s for s in scored if not s["hits"][args.missing]]
        gaps.sort(key=lambda s: (-s["total"], s["slug"]))
        label = next(l for k, _g, l, _p in DIMENSIONS if k == args.missing)
        print(f"{len(gaps)} entit{'y' if len(gaps)==1 else 'ies'} missing: {label}\n")
        for s in gaps:
            print(f"  {s['total']:2d}/{s['max']}  {s['inn'] or '(no ИНН)':<14s} {s['tier'] or '-':<13s} {s['name'][:60]}")
        return 0

    scored.sort(key=lambda s: (-s["total"], -s["docs"], s["slug"]))
    if args.min_score is not None:
        scored = [s for s in scored if s["total"] >= args.min_score]
    shown = scored[: args.top] if args.top else scored

    lines = []
    lines.append(f"# Entity coverage report ({len(scored)} entities)\n")
    hdr = "| # | Entity | ИНН | tier | total | " + " | ".join(GROUPS) + " | docs |"
    sep = "|---|---|---|---|---|" + "---|" * (len(GROUPS) + 1)
    lines.append(hdr)
    lines.append(sep)
    for i, s in enumerate(shown, 1):
        grp = " | ".join(f"{s['by_group'][g][0]}/{s['by_group'][g][1]}" for g in GROUPS)
        lines.append(
            f"| {i} | {s['name'][:52]} | {s['inn'] or '—'} | {s['tier'] or '—'} | "
            f"**{s['total']}/{s['max']}** | {grp} | {s['docs']} |"
        )

    # aggregate: which dimensions are weakest across the whole roster
    lines.append("\n## Dimension coverage across all listed entities\n")
    lines.append("| dimension | group | covered | % |")
    lines.append("|---|---|---|---|")
    for key, grp, label, _p in DIMENSIONS:
        n = sum(1 for s in scored if s["hits"][key])
        pct = (100 * n / len(scored)) if scored else 0
        lines.append(f"| {label} | {grp} | {n}/{len(scored)} | {pct:.0f}% |")

    text = "\n".join(lines)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
