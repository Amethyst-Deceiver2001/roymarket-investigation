#!/usr/bin/env python3
"""Evidence packet for one ЦБСТ-tied company: everything the registry holds that a
sanctions desk or an NGO submitter needs, in one internal Markdown document.

**Why.** The sanctions-gap table (`scripts/sanctions_gap.py`) lists the ЦБСТ-tied
organisations that no Western list names by identifier. A row in a table is not
something a designating authority can act on. A packet is: identifiers, owners and
directors with dates, filed revenue, the documented tie to ЦБСТ, products, and a
numbered exhibit list that names every document in plain words
(notes/presentation_review.md §5.2 G).

**What it is not.** It is generated from `data/registry/*.json` only, so it is as
good as the registry and no better. Every packet is marked DRAFT until a person
has checked each line against the documents on its exhibit list. The "statement
of reasons" section strings registry facts together in the order an EU listing
uses; it does not choose a legal criterion or draw the conclusion, which is the
submitter's to write. Researcher notes (`why`, `_corrected`, `notes`) never go in.

Local file processing, no network:
  python3 exhibits/build_evidence_packet.py ooo-gagaring
  python3 exhibits/build_evidence_packet.py --top 5        # the five largest unlisted by filed revenue
  python3 exhibits/build_evidence_packet.py ooo-gagaring --external   # no internal source ids
Writes notes/packets/<slug>.md and refreshes notes/packets/README.md.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REG = ROOT / "data" / "registry"
sys.path.insert(0, str(ROOT / "scripts"))
from display_helpers import display_name, reader_grade, ru_date  # noqa: E402

OUT = ROOT / "notes" / "packets"
GAP_CSV = ROOT / "exhibits" / "sanctions_gap.csv"
GAP_AS_OF = "02.10.2026"   # date of the exhibits/ snapshot; pass --gap/--gap-as-of for a newer run
GRADE_WORD = {"doc": "Documented", "rep": "Reported", "open": "Not documented"}
REGIME_LABEL = {"eu": "EU", "us": "US (OFAC)", "uk": "UK", "ch": "Switzerland (SECO)", "ua": "Ukraine",
                "ca": "Canada", "au": "Australia", "jp": "Japan", "nz": "New Zealand"}
EDGE_WORDS = {"owns": "owns", "founded": "is a recorded participant of", "directs": "directs", "role": "role at",
              "cbst_tie": "tie to ЦБСТ", "related": "related to", "sells_for": "sells for",
              "procures": "buys from", "resident_of": "resident of", "participated_in": "took part in",
              "member_of": "member of", "produces": "makes"}


def load(name):
    return json.loads((REG / name).read_text(encoding="utf-8"))


def rub_m(x) -> str:
    if x in (None, ""):
        return "—"
    return ("−" if float(x) < 0 else "") + f"₽{abs(float(x)) / 1e6:,.1f}m"


def iso_or_ru(d) -> str:
    return ru_date(d) if d else "undated"


class Exhibits:
    """Numbers sources in order of first use: E1, E2, ..."""

    def __init__(self, sources: dict, external: bool):
        self.sources, self.external, self.order = sources, external, []

    def ref(self, sid) -> str:
        if not sid:
            return "[no source on file]"
        if sid not in self.sources:
            return f"[unresolved source {sid}]"
        if sid not in self.order:
            self.order.append(sid)
        return f"[E{self.order.index(sid) + 1}]"

    def table(self) -> list[str]:
        head = "| No. | Document | Public link | SHA-256 (first 16) |" + ("" if self.external else " Internal id |")
        rule = "|---|---|---|---|" + ("" if self.external else "---|")
        rows = [head, rule]
        for i, sid in enumerate(self.order, 1):
            s = self.sources[sid]
            link = s.get("public_url") or "none public; copy on file"
            row = f"| E{i} | {s.get('title') or '(untitled)'} | {link} | `{(s.get('sha256') or '')[:16]}` |"
            rows.append(row + ("" if self.external else f" {sid} |"))
        return rows


def gap_row(slug: str, path: Path) -> dict | None:
    if not path.exists():
        return None
    return next((r for r in csv.DictReader(path.open(encoding="utf-8")) if r["slug"] == slug), None)


def top_unlisted(path: Path, n: int) -> list[str]:
    rows = [r for r in csv.DictReader(path.open(encoding="utf-8"))
            if r["western_status"].startswith("no ID match on any") and r["revenue_basis"] == "filed"
            and not r["ua"]]
    rows.sort(key=lambda r: -float(r["revenue_rub_m"] or 0))
    return [r["slug"] for r in rows[:n]]


def tie_text(e: dict, x: dict) -> str:
    """The tie claim in full. The graph's edge label is cut at 120 characters for drawing; a packet prints the record's own claim."""
    label = x.get("label") or ""
    full = (e.get("cbst_tie") or {}).get("claim") or ""
    return full if full and label and full.startswith(label[:60]) else label


REGIME_WORD = {"eu": "EU", "us": "US", "uk": "UK", "ch": "Switz", "ua": "Ukraine", "ca": "Canada",
               "au": "Australia", "jp": "Japan", "nz": "New Zealand"}


def unchecked(e: dict, k: str) -> str:
    """What a regime row says when the weekly run has no status for it: not 'nothing' if the record holds a lead."""
    held = [s for s in e.get("sanctions") or []
            if REGIME_WORD[k].casefold() in " ".join(s.get("regime") if isinstance(s.get("regime"), list) else [str(s.get("regime") or "")]).casefold()]
    if held:
        return ("the registry holds an entry for this regime; read it before use, it may be an aggregator record "
                "not read against the list's own text (see the registry entries below)")
    return "nothing in the registry; not checked by the weekly run"


def build(slug: str, external: bool, gap_path: Path, gap_as_of: str) -> str:
    entities = {e["slug"]: e for e in load("entities.json")}
    people = {p["slug"]: p for p in load("people.json")}
    sources = {s["id"]: s for s in load("sources.json")}
    graph = load("relationship_graph.json")
    programs = {p["slug"]: p for p in load("programs.json")}
    products = load("products.json")
    products = products if isinstance(products, list) else products.get("products", [])
    nodes = {n["id"]: n for n in graph["nodes"]}
    e = entities[slug]
    X = Exhibits(sources, external)
    names = display_name(e)
    today = date.today().strftime("%d.%m.%Y")

    def label(node_id):
        if node_id in entities:
            return entities[node_id]["name_ru"].split(" | ")[0]
        if node_id in people:
            return people[node_id]["fio_ru"]
        n = nodes.get(node_id)
        return (n or {}).get("label") or node_id

    L = [f"# Evidence packet: {names['legal'] or names['head']}", "",
         f"**DRAFT, generated {today} from the project registry. Not checked against the documents.** "
         "Before this leaves the project, a person reads every exhibit below and confirms each line that cites it. "
         "Grades: Documented (a primary document shows it), Reported (a party's own word or the press), "
         "Not documented (no document on file).", ""]

    # 1. Identification
    L += ["## 1. Identification", "",
          f"- Registered name: {e['name_ru'].split(' | ')[0]}",
          f"- Latin form (as screening lists write it): {names['latin']}"]
    if names["legal"]:
        L.append(f"- Known to buyers as: {names['head']}")
    L += [f"- ИНН {e.get('inn') or '—'}, ОГРН {e.get('ogrn') or '—'}",
          f"- Registered: {e.get('registered') or '—'}"]
    hist = e.get("address_history") or []
    # The entry that carries the current address: an exact match, else the latest dated entry that extends or
    # is extended by it (a bare "г. Москва" is a prefix of the full address). Never a guess between unlike strings.
    cur = " ".join((e.get("address") or "").split()).casefold()
    match = None
    for h in sorted(hist, key=lambda h: h.get("as_of") or "", reverse=True):
        v = " ".join(str(h.get("value", "")).split()).casefold()
        if cur and v and (v == cur or v.startswith(cur) or cur.startswith(v)):
            match = h
            break
    if e.get("address"):
        L.append(f"- Registered address: {e['address']}"
                 + (f" (as of {iso_or_ru(match.get('as_of'))}) {X.ref(match.get('source_id'))}" if match
                    else " [no dated source on file]"))
    for h in hist:
        if h is not match:
            L.append(f"- Other address in the record: {h.get('value')} (as of {iso_or_ru(h.get('as_of'))}) "
                     f"{X.ref(h.get('source_id'))}")
    if e.get("okved_code"):
        L.append(f"- Declared main activity (ОКВЭД): {e['okved_code']} «{e.get('okved_label') or ''}»")
    for w in (e.get("web") or {}).get("sites") or []:
        L.append(f"- Website: {w.get('url') if isinstance(w, dict) else w}")
    for t in (e.get("web") or {}).get("telegram") or []:
        L.append(f"- Telegram: {(t.get('url') or t.get('handle')) if isinstance(t, dict) else t}")
    L.append("")

    # 2. Sanctions status
    g = gap_row(slug, gap_path)
    L += ["## 2. Sanctions status", ""]
    if g:
        L.append(f"Weekly identifier check of the official lists, run of {gap_as_of}. \"No ID match\" means no entry "
                 "on that list carries this ИНН or ОГРН; a list can still name the company without them, so search "
                 "each list by name before calling it unlisted.")
        L += ["", "| Regime | Status |", "|---|---|"]
        for k in ("eu", "us", "uk", "ch", "ua", "ca", "au", "jp", "nz"):
            L.append(f"| {REGIME_LABEL[k]} | {g.get(k) or unchecked(e, k)} |")
    else:
        L.append("Not in the sanctions-gap table.")
    for s in e.get("sanctions") or []:
        reg = s.get("regime")
        reg = ", ".join(reg) if isinstance(reg, list) else reg
        L.append(f"- Registry entry: {reg} {X.ref(s.get('source_id'))}")
    L.append("")

    # 3. Owners and directors
    L += ["## 3. Owners and directors", ""]
    fh = e.get("founders_history") or []
    if fh:
        L += ["| As of | Owner | Share | Personal ИНН | Source |", "|---|---|---|---|---|"]
        for h in fh:
            vals = h["value"] if isinstance(h["value"], list) else [h["value"]]
            for v in vals:
                v = v if isinstance(v, dict) else {"name": v}
                share = f"{v['share_percent']}%" if v.get("share_percent") is not None else "—"
                L.append(f"| {iso_or_ru(h.get('as_of'))} | {v.get('name')} | {share} | {v.get('inn_personal') or '—'} | "
                         f"{X.ref(h.get('source_id'))} |")
        L.append("")
    dh = e.get("director_history") or []
    if dh:
        L += ["| As of | General director | Source |", "|---|---|---|"]
        for h in dh:
            L.append(f"| {iso_or_ru(h.get('as_of'))} | {h['value']} | {X.ref(h.get('source_id'))} |")
        L.append("")
    principals = sorted({x["source"] for x in graph["edges"]
                         if x["target"] == slug and x["type"] in ("owns", "founded", "directs") and x["source"] in people})
    if principals:
        L.append("Identifying detail on file for the people above (field-level sources are not recorded for date "
                 "and place of birth; confirm each against a document before use):")
        L.append("")
        for p in (people[s] for s in principals):
            bits = [f"ДР {ru_date(p['dob'])}" if p.get("dob") else None,
                    f"born {p['birthplace']}" if p.get("birthplace") else None,
                    f"ИНН {p['inn_personal']}" if p.get("inn_personal") else None]
            L.append(f"- {p['fio_ru']}: " + ("; ".join(b for b in bits if b) or "no identifying detail on file"))
        L.append("")
    if not (fh or dh):
        L += ["No dated ownership or director record on file.", ""]

    # 4. Money and staff
    L += ["## 4. Filed accounts and staff", ""]
    fin = sorted(e.get("financials") or [], key=lambda f: str(f.get("year")))
    if fin:
        L += ["| Year | Revenue | Net profit | Source |", "|---|---|---|---|"]
        for f in fin:
            L.append(f"| {f.get('year')} | {rub_m(f.get('revenue'))} | {rub_m(f.get('profit'))} | {X.ref(f.get('source_id'))} |")
        L.append("")
        for f in fin:
            if f.get("note"):
                L.append(f"- FY{f.get('year')}: {re.sub(r' ?\(s\d{4}\)', '', f['note'])}")
        L.append("")
    for w in e.get("workforce_history") or []:
        L.append(f"- Staff {w.get('count')} as of {iso_or_ru(w.get('as_of'))} {X.ref(w.get('source_id'))}")
    if not fin:
        L.append("No filed accounts on file.")
    L.append("")

    # 5. Tie to ЦБСТ and other links
    edges = [x for x in graph["edges"] if slug in (x["source"], x["target"])]
    tie = [x for x in edges if x["type"] == "cbst_tie"]
    L += ["## 5. Tie to ЦБСТ", ""]
    for x in tie:
        L.append(f"- **{GRADE_WORD[x.get('grade') or 'open']}**: {tie_text(e, x)} {X.ref(x.get('source_id'))}")
    for m in e.get("memberships") or []:
        L.append(f"- Programme membership: {programs.get(m['program'], {}).get('name_ru', m['program'])} as {m.get('role')}, {iso_or_ru(m.get('as_of'))}, "
                 f"graded {GRADE_WORD[reader_grade(m.get('basis'))]} {X.ref(m.get('source_id'))}")
    for p in e.get("participations") or []:
        L.append(f"- Event: {programs.get(p['event'], {}).get('name_ru', p['event'])} as {p.get('role')}, {iso_or_ru(p.get('as_of'))} {X.ref(p.get('source_id'))}")
    if not tie:
        L.append("No ЦБСТ edge in the graph.")
    L.append("")
    other = [x for x in edges if x["type"] not in ("cbst_tie", "produces")
             and not (x["target"] == slug and x["source"] in people)]
    if other:
        L += ["Other links in the record:", "", "| Link | Grade | Source |", "|---|---|---|"]
        seen = set()
        for x in other:
            key = (x["source"], x["type"], x["target"], x.get("label"))
            if key in seen:
                continue
            seen.add(key)
            if x.get("label") == "name-collision-distinct":  # a namesake kept on file as a false lead is not a link
                L.append(f"| {label(x['source'])} and {label(x['target'])} are different parties with similar names; "
                         f"recorded so the collision is not mistaken for a link | Namesake, not a link | {X.ref(x.get('source_id'))} |")
                continue
            text = f"{label(x['source'])} {EDGE_WORDS.get(x['type'], x['type'])} {label(x['target'])}"
            if x.get("label"):
                text += f" ({x['label']})"
            L.append(f"| {text} | {GRADE_WORD[x.get('grade') or 'open']} | {X.ref(x.get('source_id'))} |")
        L.append("")

    # 6. Products, claims and use
    L += ["## 6. Products and what is said about their use", ""]
    for p in e.get("products") or []:
        L.append(f"- {p.get('name_ru')} {X.ref(p.get('source_id'))}")
    for pr in (p for p in products if p.get("maker") == slug or slug in (p.get("makers") or [])):
        dl = pr.get("deliveries") or []
        L.append(f"- Product record {pr.get('name_ru') or pr.get('slug')}: {len(dl)} recorded handovers, "
                 "all self-reported by donors unless marked otherwise")
        for d in dl:
            L.append(f"  - {iso_or_ru(d.get('date'))}: to «{d.get('recipient')}», reported by {d.get('source_channel')} "
                     f"{X.ref(d.get('source_id'))}")
    for t in e.get("trademarks") or []:
        L.append(f"- Trademark № {t.get('reg_number') or t.get('registration') or '?'} «{t.get('name') or ''}», "
                 f"holder {t.get('holder') or '?'}, registered {iso_or_ru(t.get('registered'))} {X.ref(t.get('source_id'))}")
    for t in e.get("patents") or []:
        L.append(f"- {t.get('type') or 'Patent'} № {t.get('reg_number') or '?'} «{t.get('title') or ''}», "
                 f"holder {t.get('holder') or '?'} {X.ref(t.get('source_id'))}")
    claims = (e.get("marketing_claims") or []) + (e.get("battlefield_evidence") or [])
    if claims:
        L += ["", "In the company's own words or the press (verbatim, Russian original first):", ""]
        for c in claims:
            if c.get("text_ru"):
                L.append(f"> «{c['text_ru']}»")
                L.append(f">")
                L.append(f"> Working translation: {c.get('text_en') or '(none)'} {X.ref(c.get('source_id'))}")
                L.append("")
    for s in e.get("state_programs") or []:
        nm = s.get("name_ru") or s.get("name") or s.get("name_en") or s.get("program") or "(unnamed)"
        L.append(f"- State programme or association: {nm}" + (f" ({s['role']})" if s.get("role") else "")
                 + f" {X.ref(s.get('source_id'))}")
    for c in e.get("government_contracts") or []:
        L.append(f"- State contract: {c.get('customer')}, {c.get('number') or ''}, {iso_or_ru(c.get('date'))}, "
                 f"{c.get('value') or ''} {X.ref(c.get('source_id'))}")
    L.append("")

    # 7. Draft statement of reasons
    L += ["## 7. Draft statement of reasons", "",
          "*Facts only, in the order an EU listing puts them. The submitter chooses the legal route (for example "
          "the asset-freeze criteria of Council Decision 2014/145/CFSP, or the military end-user list in Annex IV "
          "to Council Regulation (EU) No 833/2014) and writes the conclusion.*", ""]
    sor = [f"{names['latin']} ({e['name_ru'].split(' | ')[0]}; ИНН {e.get('inn')}; ОГРН {e.get('ogrn')}) "
           f"is a company registered in Russia{(' on ' + e['registered']) if e.get('registered') else ''}"
           f"{(', in ' + e['city']) if e.get('city') else ''}."]
    if dh:
        sor.append(f"Its general director is {dh[-1]['value']} {X.ref(dh[-1].get('source_id'))}.")
    if fh:
        last = fh[-1]["value"] if isinstance(fh[-1]["value"], list) else [fh[-1]["value"]]
        own = ", ".join(f"{v.get('name')} ({v['share_percent']}%)" if isinstance(v, dict) and v.get("share_percent") is not None
                        else (v.get("name") if isinstance(v, dict) else str(v)) for v in last)
        dmy = lambda d: '.'.join(reversed(str(d).split('-'))) if d and str(d)[:4].isdigit() and str(d).count('-') == 2 else str(d)
        def shares(row):
            v = row["value"] if isinstance(row["value"], list) else []
            return sorted((x.get("name"), x.get("share_percent")) for x in v if isinstance(x, dict) and x.get("share_percent") is not None)
        sor.append(f"Its owners, as of {dmy(fh[-1].get('as_of'))}, are {own} {X.ref(fh[-1].get('source_id'))}.")
        other = [r for r in fh[:-1] if shares(r) and shares(r) != shares(fh[-1])]
        if other and any(e2.get("text", "").startswith("Ownership conflict") for e2 in (e.get("open_questions") or [])):
            o = other[-1]
            sor.append(f"Another document gives different shares as of {dmy(o.get('as_of'))} {X.ref(o.get('source_id'))}; "
                       "the two are not reconciled (see the open questions).")
    if tie:
        t = tie[0]
        sor.append(f"Its tie to the Centre for Unmanned Systems and Technologies (АНО «ЦБСТ»): {tie_text(e, t)} "
                   f"{X.ref(t.get('source_id'))}.")
    if e.get("products"):
        sor.append("Its products include " + ", ".join(p["name_ru"] for p in e["products"][:6] if p.get("name_ru"))
                   + f" {X.ref(e['products'][0].get('source_id'))}.")
    if fin and fin[-1].get("revenue"):
        sor.append(f"Its filed revenue for {fin[-1]['year']} was {rub_m(fin[-1]['revenue'])} {X.ref(fin[-1].get('source_id'))}.")
    L += [" ".join(sor), "", "[Conclusion and criterion: for the submitter.]", ""]

    # 9. Exhibits
    L += ["## Exhibits", "",
          "Every document cited above. Telegram posts and web pages are archived and hashed; a document with no "
          "public link is a copy held by the project (register extracts and filed accounts can be re-pulled from "
          "the Federal Tax Service by ИНН)."
          + ("" if external else " The last column is the project's internal id: strip it before sending."), ""]
    L += X.table()

    # Appendix: the record's open questions are research notes, so they stay internal.
    oq = e.get("open_questions") or []
    if oq and not external:
        L += ["", "## Appendix (internal, drop before sending): open questions in the record", "",
              "Research notes as the registry holds them. Some may weaken a line above; read them before sign-off.", ""]
        for q in oq:
            text = q.get("text") if isinstance(q, dict) else str(q)
            sid = q.get("source_id") if isinstance(q, dict) else None
            L.append(f"- {text}" + (f" ({sid})" if sid else ""))
    return "\n".join(L) + "\n"


def write_index():
    rows = ["# Evidence packets", "",
            "Internal drafts generated by `exhibits/build_evidence_packet.py` from the registry. Each one is a DRAFT "
            "until someone has checked every line against its exhibits. Not for `docs/`.", "",
            "| Packet | ИНН |", "|---|---|"]
    entities = {e["slug"]: e for e in load("entities.json")}
    for p in sorted(OUT.glob("*.md")):
        if p.name == "README.md":
            continue
        e = entities.get(p.stem, {})
        rows.append(f"| [{e.get('name_ru', p.stem).split(' | ')[0]}]({p.name}) | {e.get('inn', '')} |")
    (OUT / "README.md").write_text("\n".join(rows) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slugs", nargs="*")
    ap.add_argument("--top", type=int, help="the N largest ЦБСТ-tied companies with no list match, by filed revenue")
    ap.add_argument("--external", action="store_true", help="omit internal source ids from the exhibit list")
    ap.add_argument("--gap", default=str(GAP_CSV), help="sanctions_gap.csv to read regime status from")
    ap.add_argument("--gap-as-of", default=GAP_AS_OF)
    args = ap.parse_args()
    slugs = list(args.slugs) + (top_unlisted(Path(args.gap), args.top) if args.top else [])
    if not slugs:
        ap.error("give a slug or --top N")
    OUT.mkdir(parents=True, exist_ok=True)
    for s in slugs:
        (OUT / f"{s}.md").write_text(build(s, args.external, Path(args.gap), args.gap_as_of), encoding="utf-8")
        print(f"wrote notes/packets/{s}.md")
    write_index()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
