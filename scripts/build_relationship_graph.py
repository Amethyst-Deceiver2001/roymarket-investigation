#!/usr/bin/env python3
"""Build evidence-preserving relationship and product graph artifacts.

The graph is a local, reproducible view of structured registry fields.  It
excludes `_merged_into` tombstones, keeps unresolved names as explicit stubs,
and never infers a source_id: `cited_only` contains only edges whose source is
already attached to the underlying structured record.

Writes:
  - data/registry/relationship_graph.json
  - data/registry/relationship_graph_views.json

The companion `graph_quality_report.py` reports the reproducible quality
baseline and `check_registry.py` enforces the generated-artifact contract.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from graph_contract import GRAPH_SCHEMA_VERSION

REPO = Path(__file__).resolve().parent.parent
REG = REPO / "data" / "registry"
ENTITIES = REG / "entities.json"
PEOPLE = REG / "people.json"
OUT = REG / "relationship_graph.json"
VIEWS_OUT = REG / "relationship_graph_views.json"

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
_MULTIROTOR_RE = re.compile(r"\b(?:multirotor|multicopter|quadcopter)\b|"
                            r"мультикоптер|квадрокоптер", re.IGNORECASE)
_VEHICLE_MOUNTED_RE = re.compile(
    r"\bvehicle[- ]mounted\b|на\s+(?:автомобильном|машинном)\s+(?:шасси|платформе)|"
    r"на\s+базе\s+автомобил", re.IGNORECASE)
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse_founder_entries(raw) -> list[dict]:
    """Normalize historical free-text/list founder shapes without editing data."""
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
            if len(name) >= 3:
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
    return _WS_RE.sub(" ", n).strip().lower()


def product_id(owner_slug: str, name: str, ordinal: int = 1) -> str:
    """Create a stable graph-only id; ordinal avoids duplicate product labels."""
    stem = re.sub(r"[^a-z0-9а-я]+", "-", normalize(name)).strip("-") or "unnamed"
    base = f"product::{owner_slug}::{stem}"
    return base if ordinal == 1 else f"{base}--{ordinal}"


def classify_product(name: str, description: str | None) -> dict:
    """Classify only direct wording; generic UAV/jammer terms remain unknown."""
    text = f"{name} {description or ''}"
    uav_platform = "multirotor" if _MULTIROTOR_RE.search(text) else "unknown"
    ew_installation = "vehicle-mounted" if _VEHICLE_MOUNTED_RE.search(text) else "unknown"
    return {
        "status": "classified" if (
            uav_platform != "unknown" or ew_installation != "unknown"
        ) else "unclassified",
        "uav_platform": uav_platform,
        "ew_installation": ew_installation,
    }


def _date_and_source(item: dict) -> tuple[str | None, str | None]:
    as_of, source_id = item.get("as_of"), item.get("source_id")
    return (as_of if isinstance(as_of, str) and _DATE_RE.fullmatch(as_of) else None,
            source_id if isinstance(source_id, str) else None)


def _director_temporal_status(entry: dict, current_name: str | None) -> str:
    """Only mark time states where the history entry itself is dated and cited."""
    as_of, source_id = _date_and_source(entry)
    if not as_of or not source_id:
        return "unknown"
    return "current" if normalize(entry.get("value", "")) == normalize(current_name or "") else "historical"


def build_graph(entities: list[dict], people: list[dict]) -> dict:
    """Return a deterministic full graph and evidence-first derived views."""
    entities = [e for e in entities if not e.get("_merged_into")]
    people = [p for p in people if not p.get("_merged_into")]
    entity_by_ogrn = {e.get("ogrn"): e["slug"] for e in entities if e.get("ogrn")}
    inn_to_entity_slug = {e.get("inn"): e["slug"] for e in entities if e.get("inn")}

    name_to_slug = {}
    for entity in entities:
        for name in (entity.get("name_ru"), entity.get("brand_ru")):
            if name:
                name_to_slug.setdefault(normalize(name), entity["slug"])
    for person in people:
        if person.get("fio_ru"):
            name_to_slug.setdefault(normalize(person["fio_ru"]), person["slug"])

    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    unresolved: dict[str, dict] = {}

    def add_node(node_id: str, **attrs) -> None:
        if node_id not in nodes:
            nodes[node_id] = {"id": node_id, **attrs}

    for entity in entities:
        add_node(
            entity["slug"], kind="entity",
            label=entity.get("name_ru") or entity.get("brand_ru") or entity["slug"],
            name_latin=entity.get("name_latin"), inn=entity.get("inn"),
            tier=entity.get("tier"), sanctioned=bool(entity.get("sanctions")),
            legal_form=entity.get("legal_form"),
        )
    for person in people:
        add_node(
            person["slug"], kind="person",
            label=person.get("fio_ru") or person["slug"],
            name_latin=person.get("name_latin"), sanctioned=bool(person.get("sanctions")),
        )

    def add_stub(raw_name: str, context: str) -> str:
        node_id = f"stub::{normalize(raw_name)}"
        add_node(node_id, kind="unresolved", label=raw_name)
        item = unresolved.setdefault(node_id, {"id": node_id, "raw_name": raw_name, "contexts": []})
        if context not in item["contexts"]:
            item["contexts"].append(context)
        return node_id

    def resolve_name(raw_name: str) -> str | None:
        return name_to_slug.get(normalize(raw_name))

    def add_edge(source, target, edge_type, label=None, source_id=None, as_of=None,
                 weight=1.0, temporal_status="unknown") -> None:
        if source in nodes and target in nodes:
            as_of = as_of if isinstance(as_of, str) and _DATE_RE.fullmatch(as_of) else None
            if temporal_status in {"current", "historical"} and (not as_of or not source_id):
                temporal_status = "unknown"
            edges.append({
                "source": source, "target": target, "type": edge_type,
                "label": label, "source_id": source_id, "as_of": as_of,
                "weight": weight, "temporal_status": temporal_status,
            })

    for entity in entities:
        slug = entity["slug"]
        for parent in entity.get("parents") or []:
            target = parent.get("slug")
            if target in nodes:
                add_edge(target, slug, "owns", f"{parent.get('share_percent', '?')}%",
                         parent.get("source_id"), weight=parent.get("share_percent") or 1.0)
        for subsidiary in entity.get("subsidiaries") or []:
            target = subsidiary.get("slug") or entity_by_ogrn.get(subsidiary.get("ogrn"))
            as_of, source_id = _date_and_source(subsidiary)
            temporal_status = "historical" if as_of and source_id else "unknown"
            add_edge(slug, target, "owns", subsidiary.get("role"), source_id, as_of,
                     temporal_status=temporal_status)
        for related in entity.get("related_entities") or []:
            add_edge(slug, related.get("slug"), "related", "related (ambiguous)",
                     related.get("source_id"))
        for founder in parse_founder_entries(entity.get("founders")):
            raw_name = founder["name"]
            target = resolve_name(raw_name)
            if target == slug:
                continue
            source = target or add_stub(raw_name, f"founder of {slug}")
            add_edge(source, slug, "founded",
                     f"{founder['share']}%" if founder.get("share") else None)
        for director in entity.get("director_history") or []:
            raw_name = director.get("value")
            if not raw_name or raw_name.startswith("—"):
                continue
            target = resolve_name(raw_name)
            if target == slug:
                continue
            source = target or add_stub(raw_name, f"director of {slug}")
            as_of, source_id = _date_and_source(director)
            add_edge(source, slug, "directs", source_id=source_id, as_of=as_of,
                     temporal_status=_director_temporal_status(director, entity.get("director")))
        if not entity.get("director_history") and entity.get("director"):
            raw_name = entity["director"]
            target = resolve_name(raw_name)
            if target != slug:
                source = target or add_stub(raw_name, f"director of {slug}")
                add_edge(source, slug, "directs")

        seen_product_ids: Counter[str] = Counter()
        for product in entity.get("products") or []:
            if isinstance(product, dict):
                name = product.get("name_ru")
                description, source_id = product.get("description"), product.get("source_id")
            elif isinstance(product, str):
                name, description, source_id = product, None, None
            else:
                continue
            if not name:
                continue
            base_id = product_id(slug, name)
            seen_product_ids[base_id] += 1
            node_id = product_id(slug, name, seen_product_ids[base_id])
            add_node(node_id, kind="product", label=name, owner_slug=slug,
                     source_id=source_id, classification=classify_product(name, description))
            add_edge(slug, node_id, "produces", source_id=source_id)

    for person in people:
        slug = person["slug"]
        for role in person.get("roles") or []:
            target = role.get("entity_slug")
            add_edge(slug, target, "role", role.get("title"), role.get("source_id"),
                     role.get("from"))
        for other in person.get("other_entities") or []:
            target = inn_to_entity_slug.get(other.get("inn"))
            add_edge(slug, target, "role", other.get("role"), other.get("source_id"),
                     other.get("as_of"))

    node_list = sorted(nodes.values(), key=lambda node: node["id"])
    edges.sort(key=lambda edge: (
        edge["source"], edge["target"], edge["type"], edge["as_of"] or "",
        edge["label"] or "", edge["source_id"] or "",
    ))
    degree = Counter()
    for edge in edges:
        degree[edge["source"]] += 1
        degree[edge["target"]] += 1
    for node in node_list:
        node["degree"] = degree[node["id"]]
    unresolved_list = sorted(unresolved.values(), key=lambda item: item["id"])

    graph = {
        "schema_version": GRAPH_SCHEMA_VERSION,
        "generated_from": "data/registry/entities.json + people.json",
        "node_count": len(node_list),
        "edge_count": len(edges),
        "unresolved_count": len(unresolved_list),
        "nodes": node_list,
        "edges": edges,
        "unresolved": unresolved_list,
    }
    return graph


def build_views(graph: dict) -> dict:
    """Build deterministic edge subsets without promoting uncited evidence."""
    nodes = {node["id"]: node for node in graph["nodes"]}
    edges = graph["edges"]

    def subgraph(selected: list[dict]) -> dict:
        ids = {edge["source"] for edge in selected} | {edge["target"] for edge in selected}
        return {
            "nodes": [nodes[node_id] for node_id in sorted(ids)],
            "edges": selected,
        }

    core_ids = {
        node["id"] for node in graph["nodes"]
        if node["kind"] == "entity" and node.get("tier") == "cbst-core"
    }
    core_edges = [
        edge for edge in edges
        if edge["source"] in core_ids or edge["target"] in core_ids
    ]
    return {
        "schema_version": GRAPH_SCHEMA_VERSION,
        "generated_from": "relationship_graph.json",
        "views": {
            "cited_only": subgraph([edge for edge in edges if edge["source_id"] is not None]),
            "current_only": subgraph([edge for edge in edges if edge["temporal_status"] == "current"]),
            "core_network": subgraph(core_edges),
            "evidence_gaps": subgraph([edge for edge in edges if edge["source_id"] is None]),
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", help="report the requested entity's one-hop graph after rebuilding canonical artifacts")
    args = ap.parse_args()
    entities = json.loads(ENTITIES.read_text(encoding="utf-8"))
    people = json.loads(PEOPLE.read_text(encoding="utf-8"))
    graph = build_graph(entities, people)
    views = build_views(graph)
    OUT.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    VIEWS_OUT.write_text(json.dumps(views, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    edge_types = Counter(edge["type"] for edge in graph["edges"])
    print(f"wrote {OUT.relative_to(REPO)} — {graph['node_count']} nodes, "
          f"{graph['edge_count']} edges, {graph['unresolved_count']} unresolved stubs")
    print(f"wrote {VIEWS_OUT.relative_to(REPO)} — edge types: {dict(sorted(edge_types.items()))}")
    if args.slug:
        incident = [edge for edge in graph["edges"]
                    if edge["source"] == args.slug or edge["target"] == args.slug]
        if not any(node["id"] == args.slug for node in graph["nodes"]):
            raise SystemExit(f"error: no live graph node with id {args.slug!r}")
        neighbours = {args.slug}
        for edge in incident:
            neighbours.update((edge["source"], edge["target"]))
        print(f"one-hop graph for {args.slug}: {len(neighbours)} nodes, {len(incident)} edges")


if __name__ == "__main__":
    main()
