#!/usr/bin/env python3
"""Citation worksheet: official list entries to replace OpenSanctions as the
source of each sanctions claim.

**Why.** 87 records (2026-10-02) carry `sanctions[]` entries whose only source
is an OpenSanctions compilation. The landing page and the chain views cite it
for the Sanctioned flag (Тримикс's "Switzerland, EU, US, Ukraine"). For
sanctions lobbying each regime should cite its own official entry. The weekly
watcher (`sanctions_watch.py`) already finds the EU, US, UK and Swiss entries
that carry a record's ИНН/ОГРН; this script lays them out per record, with each
entry's own id, names, programme or legal act, dates and links.

**It writes nothing into the registry.** Per the hard rule in CLAUDE.md, a
person reads each entry on the official list, archives it, and records it in
`sanctions[]` via `corrections_entities.json` / `corrections_people.json`.
Regimes the watcher does not read (Ukraine, Canada, Australia, Japan, New
Zealand) and entries with no identifier match are listed as manual look-ups.

Local file processing, no network:
  git show origin/watch/sanctions:sanctions_watch.json > /tmp/watch.json
  python3 scripts/sanctions_citations.py --watch /tmp/watch.json --md exhibits/sanctions_citations.md
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REG = ROOT / "data" / "registry"

LIST_LABEL = {"us": "US OFAC SDN", "eu": "EU consolidated list", "uk": "UK Sanctions List",
              "ch": "Swiss SECO list"}
# A public page per entry where the list offers one; otherwise the list itself.
ENTRY_URL = {"us": "https://sanctionssearch.ofac.treas.gov/Details.aspx?id={id}"}
CLAIM_KEYS = {
    "us": re.compile(r"\b(US|OFAC|SDN|EO 14024)\b", re.I),
    "eu": re.compile(r"\b(EU|European Union|Council (Implementing )?Regulation)\b", re.I),
    "ch": re.compile(r"\b(Switzerland|Swiss|SECO|CH)\b", re.I),
    "uk": re.compile(r"\b(UK|GB|United Kingdom|OFSI|FCDO)\b", re.I),
    "ua": re.compile(r"\b(Ukrain|UA-|NSDC|GUR|war-sanctions)", re.I),
    "other": re.compile(r"\b(Canada|CA-|Australia|AU-|Japan|JP-|New Zealand|NZ-|Monaco|Belgium|France)", re.I),
}


def is_opensanctions(src: dict) -> bool:
    return ("OpenSanctions" in (src.get("title") or "")
            or "OPENSANCTIONS" in (src.get("path") or "").upper())


def regime_text(rec: dict) -> str:
    out = []
    for s in rec.get("sanctions") or []:
        r = s.get("regime")
        out.extend(r if isinstance(r, list) else [r] if r else [])
    return " | ".join(map(str, out))


def build(watch: dict) -> list[dict]:
    sources = {s["id"]: s for s in json.loads((REG / "sources.json").read_text(encoding="utf-8"))}
    records = []
    for fname, kind, name_key in (("entities.json", "entity", "name_ru"), ("people.json", "person", "fio_ru")):
        for r in json.loads((REG / fname).read_text(encoding="utf-8")):
            if not r.get("_merged_into"):
                records.append((kind, r.get(name_key), r))
    hits: dict[str, list[dict]] = {}
    for h in watch.get("hits", []):
        hits.setdefault(h["slug"], []).append(h)
    scanned = {k for k, v in watch.get("lists", {}).items() if not v.get("error")}

    rows = []
    for kind, name, r in records:
        sanc = r.get("sanctions") or []
        os_only = bool(sanc) and all(is_opensanctions(sources.get(s.get("source_id"), {})) for s in sanc)
        if not os_only and r["slug"] not in hits:
            continue
        claims = regime_text(r)
        entries = []
        for h in sorted(hits.get(r["slug"], []), key=lambda x: (x["list"], str(x.get("entry_id")))):
            if any(e["list"] == h["list"] and e["entry_id"] == h.get("entry_id") for e in entries):
                continue
            url = ENTRY_URL.get(h["list"], "").format(id=h.get("entry_id")) or None
            entries.append({"list": h["list"], "entry_id": h.get("entry_id"),
                            "identifiers": sorted({x["identifier"] for x in hits[r["slug"]]
                                                   if x["list"] == h["list"]
                                                   and x.get("entry_id") == h.get("entry_id")}),
                            "names": h.get("list_names", []), "programs": h.get("programs", []),
                            "refs": h.get("refs", []), "dates": h.get("dates", []),
                            "urls": ([url] if url else []) + h.get("urls", [])})
        found = {e["list"] for e in entries}
        todo = []
        for lst in ("eu", "us", "uk", "ch"):
            if CLAIM_KEYS[lst].search(claims) and lst not in found:
                todo.append(f"{LIST_LABEL[lst]}: claimed, no identifier match"
                            + ("" if lst in scanned else " (list not read this week)")
                            + "; find the entry by name")
        if CLAIM_KEYS["ua"].search(claims):
            todo.append("Ukraine: claimed; find the NSDC register / decree entry or the GUR page")
        if CLAIM_KEYS["other"].search(claims):
            todo.append("Other regimes claimed (Canada, Australia, Japan, NZ…): not read by the "
                        "watcher; find each official entry")
        rows.append({"kind": kind, "slug": r["slug"], "name": name, "os_only": os_only,
                     "claims": claims, "entries": entries, "todo": todo})
    rows.sort(key=lambda x: (not x["os_only"], -len(x["entries"]), x["name"] or ""))
    return rows


def write_md(rows: list[dict], watch: dict, path: Path) -> None:
    lists = watch.get("lists", {})
    lines = ["# Sanctions citations worksheet", "",
             "Internal working file, generated by `scripts/sanctions_citations.py` from the sanctions watch "
             f"of {watch.get('as_of')}. Not a reader page and not a source: read each entry on the official "
             "list, archive it, then record it in the registry by hand.", ""]
    for k, v in lists.items():
        lines.append(f"- {LIST_LABEL.get(k, k)}: " + (f"failed ({v['error']})" if v.get("error") else
                     f"list dated {v.get('publish_date')}, SHA-256 `{(v.get('sha256') or '')[:16]}…`"))
    n_os = sum(1 for r in rows if r["os_only"])
    n_found = sum(1 for r in rows if r["os_only"] and r["entries"])
    lines += ["", f"{n_os} records rest only on OpenSanctions; for {n_found} of them the watcher found at "
              f"least one official entry by identifier. {len(rows) - n_os} more records have watcher hits "
              "and are listed for completeness.", ""]
    for r in rows:
        tag = "OpenSanctions-only" if r["os_only"] else "has other sources"
        lines += [f"## {r['name']} (`{r['slug']}`, {r['kind']}, {tag})", "",
                  f"Registry claims: {r['claims'] or '(no regime field)'}", ""]
        for e in r["entries"]:
            lines.append(f"- **{LIST_LABEL[e['list']]}**, entry `{e['entry_id']}`, matched on "
                         f"{', '.join(e['identifiers'])}")
            if e["names"]:
                lines.append(f"  - names on the entry: {'; '.join(e['names'][:4])}")
            if e["programs"] or e["refs"]:
                lines.append(f"  - programme / legal act: {'; '.join((e['programs'] + e['refs'])[:6])}")
            if e["dates"]:
                lines.append(f"  - dates on the entry: {'; '.join(e['dates'][:6])}")
            for u in e["urls"][:3]:
                lines.append(f"  - {u}")
        for t in r["todo"]:
            lines.append(f"- to look up: {t}")
        lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--watch", required=True, help="sanctions_watch.json from the watch/sanctions branch")
    ap.add_argument("--md", required=True, help="write the worksheet here")
    args = ap.parse_args()
    watch = json.loads(Path(args.watch).read_text(encoding="utf-8"))
    rows = build(watch)
    write_md(rows, watch, Path(args.md))
    n_os = sum(1 for r in rows if r["os_only"])
    print(f"{len(rows)} records; {n_os} OpenSanctions-only, "
          f"{sum(1 for r in rows if r['os_only'] and r['entries'])} of them with an official entry found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
