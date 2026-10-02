#!/usr/bin/env python3
"""Machine-readable export of the registry: FollowTheMoney JSON lines and flat CSVs.

**Why.** Screening vendors, OpenSanctions and OCCRP Aleph load FollowTheMoney
(FtM) entities with no custom work; other researchers want CSV
(notes/presentation_review.md §5.2 H). The registry is the source; this writes
nothing back into it.

**Scope.** The nodes of `relationship_graph.json`: the entities and people the
network graph already admits. That leaves out `tier: adjacent` entities,
`held-off` entities, `reference` people, merged records and unresolved names.
State customers become FtM `PublicBody` entities.

**Filters (the parked public-site rules).** No researcher notes (`notes`, `why`,
`_corrected`, open questions), no screening fields, no home address, phone,
e-mail or social handles for people. A person's date and place of birth and
personal ИНН are included, since they make a sanctions match usable (PII policy
in CLAUDE.md); `--no-pii` drops them. Sanctions are not exported as FtM
`Sanction` entities: the official lists are the authority, and many registry
entries still rest on OpenSanctions itself. The CSV carries them as text.

**Mapping.** founded / owns → `Ownership` (percentage where the label gives
it); directs → `Directorship`; every other entity-to-entity or person link with
both ends exported (cbst_tie, role, related, sells_for, banks_with, procures)
→ `UnknownLink` with the edge type as `role` (a family tie → `Family`).
Products, storefronts, programmes and events stay in `ties.csv` only. Every
link carries its evidence grade and its source's plain-words title in
`description`, the source's public link in `sourceUrl` where one exists, and the
source id in `recordId`, so a citation can be traced back to this registry.

Local file processing, no network:
  python3 scripts/export_data.py                # writes exports/
  python3 scripts/export_data.py --no-pii --out /tmp/x
If the `followthemoney` package is installed (it needs ICU), every FtM entity
is validated against the official schema; otherwise the run says it skipped that.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REG = ROOT / "data" / "registry"
sys.path.insert(0, str(ROOT / "scripts"))
from display_helpers import display_name  # noqa: E402

PUBLISHER = "RoyMarket / ЦБСТ investigation registry"
GRADE_WORD = {"doc": "documented", "rep": "reported", "open": "not documented"}
ORG_FORMS = {"АНО", "Фонд", "Ассоциация", "Общественная организация", "Некоммерческое партнёрство"}
OWNERSHIP_EDGES = {"founded": "founder", "owns": "owner"}
LINK_EDGES = {"cbst_tie", "role", "related", "sells_for", "banks_with", "procures", "directs"}


def load(name):
    return json.loads((REG / name).read_text(encoding="utf-8"))


def iso(d) -> str | None:
    """DD.MM.YYYY or YYYY-MM-DD -> YYYY-MM-DD; anything else -> None."""
    if not d:
        return None
    m = re.match(r"^(\d{2})\.(\d{2})\.(\d{4})$", str(d))
    if m:
        return f"{m[3]}-{m[2]}-{m[1]}"
    return str(d) if re.match(r"^\d{4}(-\d{2}(-\d{2})?)?$", str(d)) else None


def fid(*parts) -> str:
    return "rm-" + hashlib.sha1("|".join(map(str, parts)).encode()).hexdigest()[:16]


def legal_name(e: dict) -> str:
    return (e.get("name_ru") or "").split(" | ")[0].strip()


def ent(schema: str, id_: str, **props) -> dict:
    clean = {}
    for k, v in props.items():
        vals = v if isinstance(v, list) else [v]
        vals = [str(x) for x in vals if x not in (None, "", [])]
        if vals:
            clean[k] = list(dict.fromkeys(vals))
    return {"id": id_, "schema": schema, "properties": clean}


def build(no_pii: bool = False):
    entities = {e["slug"]: e for e in load("entities.json") if not e.get("_merged_into")}
    people = {p["slug"]: p for p in load("people.json") if not p.get("_merged_into")}
    sources = {s["id"]: s for s in load("sources.json")}
    graph = load("relationship_graph.json")
    nodes = {n["id"]: n for n in graph["nodes"]}
    in_scope = {n["id"] for n in graph["nodes"] if n["kind"] in ("entity", "person", "government_customer")}
    ftm, ids = [], {}

    for nid in sorted(in_scope):
        n = nodes[nid]
        if n["kind"] == "entity" and nid in entities:
            e = entities[nid]
            names = display_name(e)
            schema = "Organization" if e.get("legal_form") in ORG_FORMS else "Company"
            web = e.get("web") or {}
            ids[nid] = f"rm-{nid}"
            ftm.append(ent(schema, ids[nid], name=legal_name(e), alias=[names["latin"], names["head"]],
                           innCode=e.get("inn"), ogrnCode=e.get("ogrn"), incorporationDate=iso(e.get("registered")),
                           address=e.get("address"), jurisdiction="ru", country="ru", legalForm=e.get("legal_form"),
                           okvedCode=e.get("okved_code"), classification=e.get("okved_label"),
                           website=[s.get("url") if isinstance(s, dict) else s for s in web.get("sites") or []],
                           publisher=PUBLISHER))
        elif n["kind"] == "person" and nid in people:
            p = people[nid]
            parts = (p.get("fio_ru") or "").split()
            first = dict(lastName=parts[0], firstName=parts[1], fatherName=parts[2]) if len(parts) == 3 else {}
            pii = {} if no_pii else dict(birthDate=iso(p.get("dob")), innCode=p.get("inn_personal"),
                                         birthPlace=p.get("birthplace"))
            ids[nid] = f"rm-{nid}"
            ftm.append(ent("Person", ids[nid], name=p.get("fio_ru"), alias=p.get("name_latin"),
                           publisher=PUBLISHER, **first, **pii))
        elif n["kind"] == "government_customer":
            ids[nid] = fid("customer", nid)
            ftm.append(ent("PublicBody", ids[nid], name=n.get("label"), country="ru", publisher=PUBLISHER))

    def provenance(x):
        s = sources.get(x.get("source_id")) or {}
        grade = GRADE_WORD.get(x.get("grade") or "open")
        desc = f"Evidence: {grade}" + (f"; source: {s['title']}" if s.get("title") else "; no source on file")
        return dict(description=desc, sourceUrl=s.get("public_url"), recordId=x.get("source_id"),
                    publisher=PUBLISHER, startDate=iso(x.get("as_of")))

    seen = set()
    for x in graph["edges"]:
        a, b, t = x["source"], x["target"], x["type"]
        if a not in ids or b not in ids:
            continue
        key = (a, t, b, x.get("label"), x.get("source_id"))
        if key in seen:
            continue
        seen.add(key)
        id_ = fid(*key)
        if t in OWNERSHIP_EDGES:
            pct = re.search(r"(\d+(?:[.,]\d+)?)\s*%", x.get("label") or "")
            ftm.append(ent("Ownership", id_, owner=ids[a], asset=ids[b],
                           percentage=pct[1].replace(",", ".") if pct else None,
                           role=OWNERSHIP_EDGES[t], **provenance(x)))
        elif t == "directs" and nodes[a]["kind"] == "person":
            ftm.append(ent("Directorship", id_, director=ids[a], organization=ids[b],
                           role=x.get("label") or "director", **provenance(x)))
        elif t == "family_tie":
            ftm.append(ent("Family", id_, person=ids[a], relative=ids[b], relationship=x.get("label"),
                           **{k: v for k, v in provenance(x).items() if k != "startDate"}))
        elif t in LINK_EDGES:
            role = t.replace("_", " ") + (f": {x['label']}" if x.get("label") else "")
            ftm.append(ent("UnknownLink", id_, subject=ids[a], object=ids[b], role=role[:500], **provenance(x)))
    return ftm, entities, people, sources, graph, in_scope, nodes


def validate(ftm: list[dict]) -> str:
    try:
        from followthemoney import model
    except ImportError:
        return "followthemoney not installed: schema validation skipped"
    for d in ftm:
        proxy = model.get_proxy(d, cleaned=False)
        for prop in d["properties"]:
            if prop not in proxy.schema.properties:
                raise ValueError(f"{d['id']}: {prop} not in {d['schema']}")
        # A value the library's own cleaning would drop (a malformed date, a bad code) is an error here.
        cleaned = model.get_proxy(d)
        for prop, vals in d["properties"].items():
            if len(cleaned.get(prop)) < len(vals):
                raise ValueError(f"{d['id']}: {prop} value(s) {vals} rejected by followthemoney")
        if proxy.schema.edge and not all(proxy.get(p) for p in (proxy.schema.edge_source, proxy.schema.edge_target)):
            raise ValueError(f"{d['id']}: link without both ends")
    return f"validated {len(ftm)} entities against followthemoney"


def write(out: Path, no_pii: bool) -> dict:
    ftm, entities, people, sources, graph, in_scope, nodes = build(no_pii)
    status = validate(ftm)
    (out / "csv").mkdir(parents=True, exist_ok=True)
    (out / "ftm").mkdir(parents=True, exist_ok=True)
    with (out / "ftm" / "roymarket.ftm.json").open("w", encoding="utf-8") as f:
        for d in ftm:
            f.write(json.dumps(d, ensure_ascii=False, sort_keys=True) + "\n")

    def rows(path, header, data):
        with (out / "csv" / path).open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(data)

    tie_grade = {x["source"]: x.get("grade") for x in graph["edges"] if x["type"] == "cbst_tie"}
    erows = []
    for slug in sorted(s for s in in_scope if s in entities):
        e = entities[slug]
        fin = sorted((f for f in e.get("financials") or [] if f.get("revenue") is not None), key=lambda f: str(f.get("year")))
        regimes = []
        for s in e.get("sanctions") or []:
            r = s.get("regime")
            regimes += r if isinstance(r, list) else [r] if r else []
        erows.append([slug, legal_name(e), display_name(e)["latin"], e.get("inn"), e.get("ogrn"), iso(e.get("registered")),
                      e.get("address"), e.get("okved_code"), e.get("tier"), GRADE_WORD.get(tie_grade.get(slug), ""),
                      fin[-1]["year"] if fin else "", fin[-1]["revenue"] if fin else "",
                      " | ".join(map(str, regimes))])
    rows("entities.csv", ["id", "name_ru", "name_latin", "inn", "ogrn", "registered", "address", "okved",
                          "tier", "cbst_tie_grade", "revenue_year", "revenue_rub",
                          "sanctions_as_recorded_verify_on_official_list"], erows)
    prows = []
    for slug in sorted(s for s in in_scope if s in people):
        p = people[slug]
        prows.append([slug, p.get("fio_ru"), p.get("name_latin"),
                      "" if no_pii else iso(p.get("dob")) or "", "" if no_pii else p.get("birthplace") or "",
                      "" if no_pii else p.get("inn_personal") or ""])
    rows("people.csv", ["id", "fio_ru", "name_latin", "birth_date", "birth_place", "inn_personal"], prows)
    trows = [[x["source"], nodes.get(x["source"], {}).get("label"), x["type"], x["target"],
              nodes.get(x["target"], {}).get("label"), x.get("label") or "", GRADE_WORD.get(x.get("grade") or "open"),
              x.get("as_of") or "", x.get("source_id") or ""] for x in graph["edges"]
             if x["source"] in nodes and x["target"] in nodes
             and nodes[x["source"]]["kind"] != "unresolved" and nodes[x["target"]]["kind"] != "unresolved"]
    rows("ties.csv", ["from_id", "from_name", "type", "to_id", "to_name", "label", "evidence", "as_of", "source_id"], trows)
    cited = {r[8] for r in trows if r[8]}
    srows = [[s["id"], s.get("title"), s.get("public_url") or "", s.get("as_of") or "", s.get("sha256") or ""]
             for sid, s in sorted(sources.items()) if sid in cited]
    rows("sources.csv", ["source_id", "title", "public_url", "as_of", "sha256"], srows)
    counts = {"ftm": len(ftm), "entities": len(erows), "people": len(prows), "ties": len(trows),
              "sources": len(srows), "validation": status}
    (out / "manifest.json").write_text(json.dumps(
        {"generated": date.today().isoformat(), "graph_schema": graph.get("schema_version"), "pii": not no_pii,
         **counts}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return counts


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(ROOT / "exports"))
    ap.add_argument("--no-pii", action="store_true", help="drop people's birth date, birth place and personal ИНН")
    args = ap.parse_args()
    counts = write(Path(args.out), args.no_pii)
    print(json.dumps(counts, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
