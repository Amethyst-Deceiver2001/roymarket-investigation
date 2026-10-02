#!/usr/bin/env python3
"""Sanctions-gap table: every ЦБСТ-tied organisation, with one column per
sanctions regime, for sanctions desks and NGO submitters.

**Why.** The registry knows which organisations are tied to ЦБСТ and, in
free text, which lists name them. Nothing put the two side by side, so the
most useful output for sanctions lobbying, the tied companies that no Western
list names, had no page (notes/presentation_review.md §5.2 F).

**Columns.** EU, US, UK and CH come from the weekly sanctions watcher
(`sanctions_watch.py`, state on the `watch/sanctions` branch): `listed` with
the list's own entry id and programme when an entry carries the company's
ИНН/ОГРН; `no ID match` when the list was read that week and no entry carries
them. That is not proof of absence, since a list can name a company without
its ИНН. Each `no ID match` cell is checked against the registry's own
`sanctions[]` regime text: where the registry claims the listing anyway, the cell
says `registry: listed` so it is read, not counted as a gap. UA, CA, AU, JP and NZ
come from the registry's `sanctions[]` regime text only, with its source id.
Nothing here is a finding until the entry is read on the official list.

**Rows.** Organisations with a `cbst_tie` edge in relationship_graph.json,
with the edge's grade (doc / rep). `--all` adds every non-adjacent entity.

Local file processing, no network:
  git show origin/watch/sanctions:sanctions_watch.json > /tmp/watch.json
  python3 scripts/sanctions_gap.py --watch /tmp/watch.json \\
      --csv exhibits/sanctions_gap.csv --md exhibits/sanctions_gap.md
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REG = ROOT / "data" / "registry"

WATCHED = ["eu", "us", "uk", "ch"]
# Registry-only regimes: label -> pattern over sanctions[].regime strings.
REGISTRY_ONLY = {
    "ua": re.compile(r"\b(Ukrain|UA-|NSDC|GUR|war-sanctions)", re.I),
    "ca": re.compile(r"\b(Canada|CA-)", re.I),
    "au": re.compile(r"\b(Australia|AU-)", re.I),
    "jp": re.compile(r"\b(Japan|JP-)", re.I),
    "nz": re.compile(r"\b(New Zealand|NZ-)", re.I),
}
# Same keys as sanctions_watch.REGIME_KEYS, for the "registry claims it" check.
WATCHED_KEYS = {
    "us": re.compile(r"\b(US|OFAC|SDN|EO 14024)\b", re.I),
    "eu": re.compile(r"\b(EU|European Union|Council (Implementing )?Regulation)\b", re.I),
    "ch": re.compile(r"\b(Switzerland|Swiss|SECO|CH)\b", re.I),
    "uk": re.compile(r"\b(UK|GB|United Kingdom|OFSI|FCDO)\b", re.I),
}


def regimes(e: dict) -> list[tuple[str, str | None]]:
    """(regime string, source_id) pairs from the regime field only."""
    out = []
    for s in e.get("sanctions") or []:
        r = s.get("regime")
        for v in (r if isinstance(r, list) else [r] if r else []):
            out.append((str(v), s.get("source_id")))
    return out


def latest_revenue(e: dict, src_type: dict):
    """(rubles, year, basis): basis says whether the figure is a filed БФО or relayed by others."""
    rows = [f for f in e.get("financials") or [] if f.get("revenue")]
    if not rows:
        return None, None, ""
    f = max(rows, key=lambda x: str(x.get("year")))
    kind = src_type.get(f.get("source_id")) or ""
    basis = ("filed" if kind == "bfo" else
             "press-relayed" if "press" in (f.get("note") or "").lower() or kind == "press" else
             kind or "unknown")
    return float(f["revenue"]), str(f.get("year")), basis


def build(watch: dict | None, include_all: bool) -> tuple[list[dict], dict]:
    entities = [e for e in json.loads((REG / "entities.json").read_text(encoding="utf-8"))
                if not e.get("_merged_into")]
    graph = json.loads((REG / "relationship_graph.json").read_text(encoding="utf-8"))
    src_type = {s.get("id"): s.get("type") for s in
                json.loads((REG / "sources.json").read_text(encoding="utf-8"))}
    by_slug = {e["slug"]: e for e in entities}
    ties: dict[str, str] = {}
    for ed in graph["edges"]:
        if ed.get("type") != "cbst_tie":
            continue
        for end in (ed["source"], ed["target"]):
            if end in by_slug and "tsbst" not in end:
                ties[end] = ed.get("grade") or "?"
    slugs = sorted(by_slug) if include_all else sorted(ties)
    if include_all:
        slugs = [s for s in slugs if by_slug[s].get("tier") != "adjacent"]

    hits: dict[tuple[str, str], list[dict]] = {}
    scanned = {}
    if watch:
        scanned = {k: v for k, v in watch.get("lists", {}).items() if not v.get("error")}
        for h in watch.get("hits", []):
            hits.setdefault((h["slug"], h["list"]), []).append(h)

    rows = []
    for slug in slugs:
        e = by_slug[slug]
        rev, year, basis = latest_revenue(e, src_type)
        reg = regimes(e)
        reg_text = " | ".join(r for r, _ in reg)
        row = {
            "slug": slug,
            "name_ru": e.get("name_ru"),
            "inn": e.get("inn") or "",
            "ogrn": e.get("ogrn") or "",
            "tier": e.get("tier") or "",
            "cbst_tie": ties.get(slug, ""),
            "revenue_rub_m": round(rev / 1e6, 1) if rev else "",
            "revenue_year": year or "",
            "revenue_basis": basis,
            "state_contracts": len(e.get("government_contracts") or []),
        }
        for lst in WATCHED:
            if lst not in scanned:
                row[lst] = "not checked"
                continue
            hs = hits.get((slug, lst))
            if hs:
                ids = sorted({str(h.get("entry_id")) for h in hs})
                progs = sorted({p for h in hs for p in h.get("programs", [])})
                row[lst] = f"listed: entry {', '.join(ids)}" + (f" ({'; '.join(progs[:2])})" if progs else "")
            elif WATCHED_KEYS[lst].search(reg_text):
                row[lst] = "no ID match; registry: listed"
            else:
                row[lst] = "no ID match"
        for lst, pat in REGISTRY_ONLY.items():
            srcs = sorted({s or "no source" for r, s in reg if pat.search(r)})
            row[lst] = f"registry: listed [{', '.join(srcs)}]" if srcs else ""
        western = [row[l] for l in WATCHED]
        row["western_status"] = (
            "listed" if any(c.startswith("listed") for c in western) else
            "registry claims, no ID match" if any("registry: listed" in c for c in western) else
            "no ID match on any" if all(c == "no ID match" for c in western) else
            "not checked")
        rows.append(row)

    order = {"no ID match on any": 0, "registry claims, no ID match": 1, "not checked": 2, "listed": 3}
    rows.sort(key=lambda r: (order[r["western_status"]], -(r["revenue_rub_m"] or 0), r["slug"]))
    meta = {"lists": {k: {"publish_date": v.get("publish_date"), "sha256": v.get("sha256"),
                          "fetched": v.get("fetched")} for k, v in scanned.items()},
            "watch_as_of": (watch or {}).get("as_of"), "rows": len(rows)}
    return rows, meta


COLUMNS = ["slug", "name_ru", "inn", "ogrn", "tier", "cbst_tie", "revenue_rub_m", "revenue_year", "revenue_basis",
           "state_contracts", "western_status", *WATCHED, *REGISTRY_ONLY]


def write_md(rows: list[dict], meta: dict, path: Path) -> None:
    lines = ["# Sanctions gap: ЦБСТ-tied organisations by regime", "",
             "Internal working table, generated by `scripts/sanctions_gap.py`. Not a reader page.", ""]
    if meta["lists"]:
        lines.append(f"EU/US/UK/CH columns from the sanctions watch of {meta['watch_as_of']}:")
        for k, v in meta["lists"].items():
            lines.append(f"- {k.upper()}: list dated {v['publish_date']}, SHA-256 `{(v['sha256'] or '')[:16]}…`")
    else:
        lines.append("No sanctions-watch data given: EU/US/UK/CH read `not checked`.")
    lines += ["", "`no ID match` means no entry on that list carries the company's ИНН/ОГРН. A list can "
              "name a company without them, so read the list before calling it unlisted. UA, CA, AU, JP, NZ "
              "are the registry's own claims, with their source ids.", ""]
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["western_status"]] = counts.get(r["western_status"], 0) + 1
    lines += [f"{meta['rows']} organisations: " + ", ".join(f"{n} {k}" for k, n in counts.items()), ""]
    head = ["Organisation", "ИНН", "Tie", "Revenue ₽m (year)", "Contracts", "EU", "US", "UK", "CH", "UA"]
    lines += ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for r in rows:
        rev = (f"{r['revenue_rub_m']} ({r['revenue_year']}"
               + ("" if r["revenue_basis"] == "filed" else f", {r['revenue_basis']}") + ")"
               if r["revenue_rub_m"] != "" else "")
        cells = [f"{r['name_ru']} (`{r['slug']}`)", r["inn"], r["cbst_tie"], rev, str(r["state_contracts"]),
                 r["eu"], r["us"], r["uk"], r["ch"], r["ua"]]
        lines.append("| " + " | ".join(c.replace("|", "/") for c in cells) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--watch", help="sanctions_watch.json from the watch/sanctions branch")
    ap.add_argument("--csv", help="write the table as CSV")
    ap.add_argument("--md", help="write the table as Markdown")
    ap.add_argument("--all", action="store_true", help="every non-adjacent entity, not only ЦБСТ-tied")
    args = ap.parse_args()
    watch = json.loads(Path(args.watch).read_text(encoding="utf-8")) if args.watch else None
    rows, meta = build(watch, args.all)
    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
    if args.md:
        write_md(rows, meta, Path(args.md))
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["western_status"]] = counts.get(r["western_status"], 0) + 1
    print(f"{meta['rows']} rows; " + ", ".join(f"{k}: {n}" for k, n in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
