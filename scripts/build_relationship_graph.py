#!/usr/bin/env python3
"""Build a relationship graph (nodes + edges) from data/registry/entities.json
and data/registry/people.json, for the network-relationship visualization
requested 2026-09-08 (the "bring us closer to Kontur.Focus Pro's
beneficial-ownership graph" gap — see notes/full_pipeline_catalogue.md).

This is pure local aggregation over already-verified registry data — no
network calls, no new claims. It does NOT invent relationships: every edge
comes from a structured field a human (or a screen_*.py script) already
populated, each of which already carries its own source_id per entity/
person record. The graph adds no sourcing of its own; a viewer clicking an
edge should go back to the underlying entity/person record for the
source_id, the same way the company-profile pages already do.

Edge sources (all pre-existing structured fields, nothing new mined here):
  - entities[].parents[]           entity --owns--> entity   (has slug+share)
  - entities[].subsidiaries[]      entity --owns--> entity   (has slug)
  - entities[].related_entities[]  entity --related(ambiguous)--> entity
  - entities[].founders[]          entity/person --founded--> entity
                                    (name-string only; resolved to a slug by
                                    normalized-name match against both
                                    registries — unresolved names are kept
                                    as unlinked label-only stub nodes so the
                                    graph doesn't silently drop them)
  - entities[].director / director_history[]   person --directs--> entity
                                    (name-string; resolved the same way)
  - people[].roles[]                person --role(title)--> entity
                                    (already carries entity_slug when known)
  - people[].other_entities[]       person --director/founder--> entity
                                    (already carries inn; resolved to slug)

Name resolution is fuzzy on purpose (legal-form prefixes/guillemets/case
stripped — see normalize()) because founders[]/director[] were extracted
from EGRUL free text, not authored with slugs. A resolution is logged as
"unresolved" (kept as a same-named stub node, not silently dropped) when no
registry match exists — this surfaces exactly the kind of gap
[[roymarket_fuzzy_dedup]] already found by hand, but automated for the
whole registry at once instead of one document at a time.

Usage:
    python3 scripts/build_relationship_graph.py
    python3 scripts/build_relationship_graph.py --slug ano-npts-ushkuynik  # ego-only subgraph, for spot-checking

Writes data/registry/relationship_graph.json. Local file processing only,
safe to run directly/repeatedly after any registry change.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTITIES = REPO / "data" / "registry" / "entities.json"
PEOPLE = REPO / "data" / "registry" / "people.json"
OUT = REPO / "data" / "registry" / "relationship_graph.json"

LEGAL_PREFIXES = [
    "ООО", "ОАО", "ЗАО", "ПАО", "АО", "АНО", "НКО", "НПЦ", "НПО", "КБ",
    "ФГУП", "ГУП", "МУП", "ИП", "ФОНД", "АССОЦИАЦИЯ", "СОЮЗ", "ОБЩЕСТВО",
]
_PREFIX_RE = re.compile(
    r"^\s*(?:" + "|".join(re.escape(p) for p in LEGAL_PREFIXES) + r")\.?\s+",
    re.IGNORECASE,
)
_QUOTE_RE = re.compile(r"[«»\"'“”‘’]")
_WS_RE = re.compile(r"\s+")
_SHARE_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*%")
_SPLIT_RE = re.compile(r",\s*(?![^(]*\))")


def parse_founder_entries(raw) -> list[dict]:
    """founders[] is shaped inconsistently across the registry — sometimes a
    list of {name, share} dicts, sometimes a single 'Name (25%), Name2 (75%)'
    string, sometimes a list of such strings (a pre-existing data-shape
    inconsistency, not introduced here — normalized on read rather than
    fixed in entities.json, which is out of scope for a graph-building pass).
    """
    if not raw:
        return []
    if isinstance(raw, str):
        raw = [raw]
    out = []
    for item in raw:
        if isinstance(item, dict):
            if item.get("name"):
                out.append({"name": item["name"], "share": item.get("share")})
            continue
        if not isinstance(item, str):
            continue
        for segment in _SPLIT_RE.split(item):
            segment = segment.strip().strip(",")
            if not segment:
                continue
            share_m = _SHARE_RE.search(segment)
            name = segment[: segment.find("(")].strip() if "(" in segment else segment
            name = name.strip(" .,")
            if len(name) < 3:
                continue
            out.append({"name": name, "share": share_m.group(1) if share_m else None})
    return out


def normalize(name: str) -> str:
    if not name:
        return ""
    n = _QUOTE_RE.sub("", name)
    prev = None
    while prev != n:
        prev = n
        n = _PREFIX_RE.sub("", n)
    n = _WS_RE.sub(" ", n).strip().lower()
    return n


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", default=None, help="limit output to this entity's ego-network")
    args = ap.parse_args()

    entities = json.loads(ENTITIES.read_text(encoding="utf-8"))
    people = json.loads(PEOPLE.read_text(encoding="utf-8"))

    inn_to_entity_slug = {e["inn"]: e["slug"] for e in entities if e.get("inn")}
    name_to_entity_slug = {}
    for e in entities:
        for nm in (e.get("name_ru"), e.get("brand_ru")):
            if nm:
                name_to_entity_slug.setdefault(normalize(nm), e["slug"])
    name_to_person_slug = {}
    inn_to_person_slug = {}
    for p in people:
        if p.get("fio_ru"):
            name_to_person_slug.setdefault(normalize(p["fio_ru"]), p["slug"])
        if p.get("inn_personal"):
            inn_to_person_slug[p["inn_personal"]] = p["slug"]

    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    unresolved: list[dict] = []

    def add_node(node_id, **attrs):
        if node_id not in nodes:
            nodes[node_id] = {"id": node_id, **attrs}
        else:
            nodes[node_id].update({k: v for k, v in attrs.items() if v is not None})

    for e in entities:
        add_node(
            e["slug"],
            kind="entity",
            label=e.get("name_ru") or e.get("brand_ru") or e["slug"],
            name_latin=e.get("name_latin"),
            inn=e.get("inn"),
            tier=e.get("tier"),
            sanctioned=bool(e.get("sanctions")),
            legal_form=e.get("legal_form"),
        )

    for p in people:
        add_node(
            p["slug"],
            kind="person",
            label=p.get("fio_ru") or p["slug"],
            name_latin=p.get("name_latin"),
            sanctioned=bool(p.get("sanctions")),
        )

    def resolve_name(raw_name: str) -> str | None:
        norm = normalize(raw_name)
        if norm in name_to_entity_slug:
            return name_to_entity_slug[norm]
        if norm in name_to_person_slug:
            return name_to_person_slug[norm]
        return None

    def add_edge(src, dst, etype, label=None, source_id=None, as_of=None, weight=1.0):
        edges.append({
            "source": src, "target": dst, "type": etype,
            "label": label, "source_id": source_id, "as_of": as_of, "weight": weight,
        })

    for e in entities:
        slug = e["slug"]

        for par in e.get("parents") or []:
            if par.get("slug"):
                add_edge(par["slug"], slug, "owns", f"{par.get('share_percent', '?')}%",
                          par.get("source_id"), None, par.get("share_percent") or 1.0)

        for sub in e.get("subsidiaries") or []:
            if sub.get("slug"):
                add_edge(slug, sub["slug"], "owns", sub.get("role"),
                          sub.get("source_id"), sub.get("as_of"))
            elif sub.get("ogrn"):
                match = next((x["slug"] for x in entities if x.get("ogrn") == sub["ogrn"]), None)
                if match:
                    add_edge(slug, match, "owns", sub.get("role"), sub.get("source_id"), sub.get("as_of"))

        for rel in e.get("related_entities") or []:
            if rel.get("slug"):
                add_edge(slug, rel["slug"], "related", "related (ambiguous)", rel.get("source_id"))

        for f in parse_founder_entries(e.get("founders")):
            nm = f.get("name")
            if not nm:
                continue
            target = resolve_name(nm)
            if target and target != slug:
                add_edge(target, slug, "founded", f"{f.get('share')}%" if f.get("share") else None)
            elif not target:
                stub_id = f"stub::{normalize(nm)}"
                add_node(stub_id, kind="unresolved", label=nm)
                add_edge(stub_id, slug, "founded")
                unresolved.append({"raw_name": nm, "context": f"founder of {slug}"})

        director_entries = e.get("director_history") or ([{"value": e["director"], "source_id": None, "as_of": None}]
                                                            if e.get("director") else [])
        seen_directors = set()
        for d in director_entries:
            nm = d.get("value")
            if not nm or nm in seen_directors or nm.startswith("—"):
                continue
            seen_directors.add(nm)
            target = resolve_name(nm)
            if target and target != slug:
                add_edge(target, slug, "directs", None, d.get("source_id"), d.get("as_of"))
            elif not target:
                stub_id = f"stub::{normalize(nm)}"
                add_node(stub_id, kind="unresolved", label=nm)
                add_edge(stub_id, slug, "directs", None, d.get("source_id"), d.get("as_of"))
                unresolved.append({"raw_name": nm, "context": f"director of {slug}"})

    for p in people:
        slug = p["slug"]
        for r in p.get("roles") or []:
            target = r.get("entity_slug")
            if target and target in nodes:
                add_edge(slug, target, "role", r.get("title"), r.get("source_id"), r.get("from"))

        for oe in p.get("other_entities") or []:
            target = oe.get("inn") and inn_to_entity_slug.get(oe["inn"])
            if target and target != slug:
                add_edge(slug, target, "role", oe.get("role"))

    if args.slug:
        keep = {args.slug}
        for ed in edges:
            if ed["source"] == args.slug or ed["target"] == args.slug:
                keep.add(ed["source"])
                keep.add(ed["target"])
        nodes = {k: v for k, v in nodes.items() if k in keep}
        edges = [ed for ed in edges if ed["source"] in keep and ed["target"] in keep]

    node_list = list(nodes.values())
    node_ids = {n["id"] for n in node_list}
    edges = [ed for ed in edges if ed["source"] in node_ids and ed["target"] in node_ids]

    degree: dict[str, int] = {}
    for ed in edges:
        degree[ed["source"]] = degree.get(ed["source"], 0) + 1
        degree[ed["target"]] = degree.get(ed["target"], 0) + 1
    for n in node_list:
        n["degree"] = degree.get(n["id"], 0)

    out = {
        "generated_from": "data/registry/entities.json + people.json",
        "node_count": len(node_list),
        "edge_count": len(edges),
        "unresolved_count": len(unresolved),
        "nodes": node_list,
        "edges": edges,
        "unresolved": unresolved,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)} — {len(node_list)} nodes, {len(edges)} edges, "
          f"{len(unresolved)} unresolved name(s) kept as stub nodes")
    edge_types: dict[str, int] = {}
    for ed in edges:
        edge_types[ed["type"]] = edge_types.get(ed["type"], 0) + 1
    print("edge types:", edge_types)


if __name__ == "__main__":
    main()
