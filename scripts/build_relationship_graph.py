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

from graph_contract import GRAPH_SCHEMA_VERSION, CBST_TIE_CONFIDENCE, build_view_projections

REPO = Path(__file__).resolve().parent.parent
REG = REPO / "data" / "registry"
ENTITIES = REG / "entities.json"
PEOPLE = REG / "people.json"
MILITARY_UNITS = REG / "military_units.json"
OUT = REG / "relationship_graph.json"
VIEWS_OUT = REG / "relationship_graph_views.json"

CBST_SLUG = "ano-tsbst-centre-for-unmanned-systems-technologies"

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
_SHARE_SUFFIX_RE = re.compile(r"\s*(\d+(?:[.,]\d+)?)\s*%\s*$")
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
                out.append({
                    "name": item["name"],
                    "share": item.get("share", item.get("share_pct")),
                })
            continue
        if not isinstance(item, str):
            continue
        for segment in _SPLIT_RE.split(item):
            segment = segment.strip().strip(",")
            if not segment:
                continue
            share_m = _SHARE_RE.search(segment)
            name = segment[: segment.find("(")].strip() if "(" in segment else segment
            name = _SHARE_SUFFIX_RE.sub("", name)
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


def customer_id(name: str) -> str:
    """Stable graph-only id for a government_contracts[].customer name."""
    stem = re.sub(r"[^a-z0-9а-я]+", "-", normalize(name)).strip("-") or "unnamed"
    return f"customer::{stem}"


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


# Offensive/defensive/dual-use classification for the hub glyph badges
# (hex-pattern glyph — see notes/hub_insignia_design_notes.md's "v5" entry
# for the design rationale). Distinct from classify_product() above: this
# is a coarser, entity-level read of the SAME products[] text, kept
# deliberately separate because it answers a different question (does
# this manufacturer's overall catalogue skew offensive/defensive/both)
# than classify_product()'s per-product platform/installation read. A
# presentation judgment for the graph's icon layer only, not a sourced
# registry field.
_OFFENSIVE_TERMS = [
    "камикадзе", "kamikaze", "ударный дрон", "ударн", "боеприпас",
    "боевая часть", "warhead", "боеголов", "снаряд", "авиабомб", "бомб",
    "штурмов",
]
_DEFENSIVE_TERMS = [
    "рэб", "радиоэлектронн", "подавлен", "антидрон", "anti-drone",
    "counter-drone", "counter-uav", "jam", "глушен", "детектор бпла",
    "обнаружен", "щит", "перехватчик", "антиспуфинг", "радиоподавлен",
]


def classify_variant(entity: dict) -> str | None:
    if entity.get("tier") not in ("manufacturer", "cbst-core"):
        return None
    chunks = []
    for prod in entity.get("products") or []:
        if isinstance(prod, dict):
            chunks.append(str(prod.get("name_ru") or ""))
            chunks.append(str(prod.get("description") or ""))
        elif isinstance(prod, str):
            chunks.append(prod)
    text = " ".join(chunks).lower()
    if not text.strip():
        return None
    off = any(term in text for term in _OFFENSIVE_TERMS)
    dfn = any(term in text for term in _DEFENSIVE_TERMS)
    if off and dfn:
        return "dual"
    if off:
        return "offensive"
    if dfn:
        return "defensive"
    return None


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


def build_graph(entities: list[dict], people: list[dict],
                 military_units: list[dict] | None = None) -> dict:
    """Return a deterministic full graph and evidence-first derived views."""
    entities = [e for e in entities if not e.get("_merged_into")]
    people = [p for p in people if not p.get("_merged_into")]
    military_units = military_units or []
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
            legal_form=entity.get("legal_form"), variant=classify_variant(entity),
        )
    for person in people:
        add_node(
            person["slug"], kind="person",
            label=person.get("fio_ru") or person["slug"],
            name_latin=person.get("name_latin"), sanctioned=bool(person.get("sanctions")),
        )
    for unit in military_units:
        add_node(
            f"unit::{unit['slug']}", kind="military_unit",
            label=unit.get("name_ru") or unit["slug"],
            unit_type=unit.get("unit_type"), parent_grouping=unit.get("parent_grouping"),
            designation_confidence=unit.get("designation_confidence"),
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
                 weight=1.0, temporal_status="unknown", confidence=None) -> None:
        if source in nodes and target in nodes:
            as_of = as_of if isinstance(as_of, str) and _DATE_RE.fullmatch(as_of) else None
            if temporal_status in {"current", "historical"} and (not as_of or not source_id):
                temporal_status = "unknown"
            edges.append({
                "source": source, "target": target, "type": edge_type,
                "label": label, "source_id": source_id, "as_of": as_of,
                "weight": weight, "temporal_status": temporal_status,
                "confidence": confidence,
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
        current_founders = {
            normalize(founder["name"])
            for founder in parse_founder_entries(entity.get("founders"))
        }
        historical_founders = set()
        for entry in entity.get("founders_history") or []:
            if not isinstance(entry, dict):
                continue
            as_of, source_id = _date_and_source(entry)
            for founder in parse_founder_entries(entry.get("value")):
                raw_name = founder["name"]
                normalized_name = normalize(raw_name)
                if normalized_name in current_founders or normalized_name in historical_founders:
                    continue
                historical_founders.add(normalized_name)
                target = resolve_name(raw_name)
                if target == slug:
                    continue
                source = target or add_stub(raw_name, f"former founder of {slug}")
                add_edge(
                    source,
                    slug,
                    "founded",
                    f"former founder ({founder['share']}%)" if founder.get("share")
                    else "former founder",
                    source_id,
                    as_of,
                    temporal_status="historical" if as_of and source_id else "unknown",
                )
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

        for contract in entity.get("government_contracts") or []:
            customer_name = contract.get("customer")
            if not customer_name:
                continue
            cust_id = customer_id(customer_name)
            add_node(cust_id, kind="government_customer", label=customer_name)
            raw_date = contract.get("date")
            as_of = raw_date if isinstance(raw_date, str) and _DATE_RE.fullmatch(raw_date) else None
            source_id = contract.get("source_id") if isinstance(contract.get("source_id"), str) else None
            add_edge(cust_id, slug, "procures", contract.get("contract_number"),
                     source_id, as_of, weight=contract.get("value_rub") or 1.0)

        cbst_tie = entity.get("cbst_tie")
        if (isinstance(cbst_tie, dict) and cbst_tie.get("claim")
                and cbst_tie.get("confidence") in CBST_TIE_CONFIDENCE
                and slug != CBST_SLUG and CBST_SLUG in nodes):
            claim = cbst_tie["claim"]
            label = claim if len(claim) <= 120 else claim[:117] + "..."
            add_edge(slug, CBST_SLUG, "cbst_tie", label,
                     cbst_tie.get("source_id"), weight=1.0,
                     confidence=cbst_tie.get("confidence"))

        for evidence in entity.get("battlefield_evidence") or []:
            unit_slug = evidence.get("unit_slug")
            if not unit_slug:
                continue
            unit_node_id = f"unit::{unit_slug}"
            as_of, source_id = _date_and_source(evidence)
            add_edge(slug, unit_node_id, "confirmed_field_use", None, source_id, as_of)

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
    return {
        "schema_version": GRAPH_SCHEMA_VERSION,
        "generated_from": "relationship_graph.json",
        "views": build_view_projections(graph),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", help="report the requested entity's one-hop graph after rebuilding canonical artifacts")
    args = ap.parse_args()
    entities = json.loads(ENTITIES.read_text(encoding="utf-8"))
    people = json.loads(PEOPLE.read_text(encoding="utf-8"))
    military_units = json.loads(MILITARY_UNITS.read_text(encoding="utf-8")) if MILITARY_UNITS.exists() else []
    graph = build_graph(entities, people, military_units)
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
