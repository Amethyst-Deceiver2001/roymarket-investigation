#!/usr/bin/env python3
"""Shared schema contract for generated relationship-graph artifacts.

The graph is a derived view of the registry.  Its edges may be intentionally
uncited when the source registry field is an unresolved legacy assertion; the
contract preserves that distinction rather than inventing a source reference.
"""
from __future__ import annotations

import re
from collections import Counter

GRAPH_SCHEMA_VERSION = 4
NODE_KINDS = {"entity", "person", "product", "unresolved",
              "government_customer", "military_unit"}
EDGE_TYPES = {"owns", "related", "founded", "directs", "role", "produces",
              "procures", "confirmed_field_use", "cbst_tie"}
TEMPORAL_STATUSES = {"current", "historical", "unknown"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
UNIT_TYPES = {"army", "brigade", "regiment", "battalion", "detachment",
              "volunteer_detachment", "unit_designator", "grouping",
              "unspecified_role"}
UNIT_DESIGNATION_CONFIDENCE = {"named", "descriptive", "grouping"}

NODE_FIELDS = {
    "entity": {"id", "kind", "label", "name_latin", "inn", "tier",
               "sanctioned", "legal_form", "degree", "variant"},
    "person": {"id", "kind", "label", "name_latin", "sanctioned", "degree"},
    "product": {"id", "kind", "label", "owner_slug", "source_id",
                "classification", "degree"},
    "unresolved": {"id", "kind", "label", "degree"},
    "government_customer": {"id", "kind", "label", "degree"},
    "military_unit": {"id", "kind", "label", "unit_type", "parent_grouping",
                       "designation_confidence", "degree"},
}
EDGE_FIELDS = {
    "source", "target", "type", "label", "source_id", "as_of", "weight",
    "temporal_status", "confidence",
}
# Confidence vocabulary carried over verbatim from entities.json's own
# cbst_tie.confidence field (t-doc/t-open/press are positive-tie values;
# "none"/"not_established" mean no tie and are never emitted as edges).
CBST_TIE_CONFIDENCE = {"t-doc", "t-open", "press"}
PRODUCT_CLASSIFICATION_FIELDS = {
    "status", "uav_platform", "ew_installation",
}


def _error(errors: list[str], message: str) -> None:
    errors.append(f"graph: {message}")


def _is_date(value) -> bool:
    return isinstance(value, str) and bool(DATE_RE.fullmatch(value))


def validate_graph(
    graph: dict,
    entities: list[dict],
    people: list[dict],
    sources: list[dict],
) -> list[str]:
    """Return graph-contract failures without printing or mutating inputs."""
    errors: list[str] = []
    if not isinstance(graph, dict):
        return ["graph: top-level value must be an object"]
    if graph.get("schema_version") != GRAPH_SCHEMA_VERSION:
        _error(errors, f"schema_version must be {GRAPH_SCHEMA_VERSION}")

    nodes = graph.get("nodes")
    edges = graph.get("edges")
    unresolved = graph.get("unresolved")
    if not isinstance(nodes, list):
        _error(errors, "nodes must be a list")
        nodes = []
    if not isinstance(edges, list):
        _error(errors, "edges must be a list")
        edges = []
    if not isinstance(unresolved, list):
        _error(errors, "unresolved must be a list")
        unresolved = []

    for count_key, values in (("node_count", nodes), ("edge_count", edges),
                              ("unresolved_count", unresolved)):
        if graph.get(count_key) != len(values):
            _error(errors, f"{count_key} does not equal its array length")

    live_entities = {
        e["slug"] for e in entities
        if isinstance(e, dict) and e.get("slug") and not e.get("_merged_into")
    }
    live_people = {
        p["slug"] for p in people
        if isinstance(p, dict) and p.get("slug") and not p.get("_merged_into")
    }
    tombstone_entities = {
        e["slug"] for e in entities
        if isinstance(e, dict) and e.get("slug") and e.get("_merged_into")
    }
    tombstone_people = {
        p["slug"] for p in people
        if isinstance(p, dict) and p.get("slug") and p.get("_merged_into")
    }
    source_ids = {s.get("id") for s in sources if isinstance(s, dict) and s.get("id")}

    node_by_id: dict[str, dict] = {}
    for i, node in enumerate(nodes):
        where = f"nodes[{i}]"
        if not isinstance(node, dict):
            _error(errors, f"{where} must be an object")
            continue
        kind = node.get("kind")
        node_id = node.get("id")
        if kind not in NODE_KINDS:
            _error(errors, f"{where}.kind has invalid value {kind!r}")
            continue
        if set(node) - NODE_FIELDS[kind]:
            _error(errors, f"{where} has unsupported field(s) {sorted(set(node) - NODE_FIELDS[kind])}")
        if not isinstance(node_id, str) or not node_id:
            _error(errors, f"{where}.id must be a non-empty string")
            continue
        if node_id in node_by_id:
            _error(errors, f"duplicate node id {node_id!r}")
            continue
        node_by_id[node_id] = node
        if not isinstance(node.get("label"), str) or not node["label"]:
            _error(errors, f"{where}.label must be a non-empty string")
        if not isinstance(node.get("degree"), int) or node["degree"] < 0:
            _error(errors, f"{where}.degree must be a non-negative integer")
        if kind == "entity":
            if node_id not in live_entities:
                _error(errors, f"{where} entity id {node_id!r} is not a live entity")
            if not isinstance(node.get("sanctioned"), bool):
                _error(errors, f"{where}.sanctioned must be bool")
        elif kind == "person":
            if node_id not in live_people:
                _error(errors, f"{where} person id {node_id!r} is not a live person")
            if not isinstance(node.get("sanctioned"), bool):
                _error(errors, f"{where}.sanctioned must be bool")
        elif kind == "product":
            owner = node.get("owner_slug")
            if not node_id.startswith(f"product::{owner}::"):
                _error(errors, f"{where}.id must be namespaced to owner_slug")
            if owner not in live_entities:
                _error(errors, f"{where}.owner_slug {owner!r} is not a live entity")
            sid = node.get("source_id")
            if sid is not None and sid not in source_ids:
                _error(errors, f"{where}.source_id references unknown source {sid!r}")
            classification = node.get("classification")
            if not isinstance(classification, dict):
                _error(errors, f"{where}.classification must be an object")
            else:
                if set(classification) != PRODUCT_CLASSIFICATION_FIELDS:
                    _error(errors, f"{where}.classification has invalid field set")
                if classification.get("status") not in {"classified", "unclassified"}:
                    _error(errors, f"{where}.classification.status is invalid")
                if classification.get("uav_platform") not in {"multirotor", "unknown"}:
                    _error(errors, f"{where}.classification.uav_platform is invalid")
                if classification.get("ew_installation") not in {"vehicle-mounted", "unknown"}:
                    _error(errors, f"{where}.classification.ew_installation is invalid")
        elif kind == "government_customer":
            if not node_id.startswith("customer::"):
                _error(errors, f"{where} government_customer node id must start with 'customer::'")
        elif kind == "military_unit":
            if not node_id.startswith("unit::"):
                _error(errors, f"{where} military_unit node id must start with 'unit::'")
            if node.get("unit_type") not in UNIT_TYPES:
                _error(errors, f"{where}.unit_type has invalid value {node.get('unit_type')!r}")
            if node.get("designation_confidence") not in UNIT_DESIGNATION_CONFIDENCE:
                _error(errors, f"{where}.designation_confidence has invalid value "
                               f"{node.get('designation_confidence')!r}")
            pg = node.get("parent_grouping")
            if pg is not None and not isinstance(pg, str):
                _error(errors, f"{where}.parent_grouping must be a string or null")
        else:
            if not node_id.startswith("stub::"):
                _error(errors, f"{where} unresolved node id must start with 'stub::'")

    for tombstone in sorted(tombstone_entities | tombstone_people):
        if tombstone in node_by_id:
            _error(errors, f"tombstoned registry node {tombstone!r} is included")
    for missing in sorted((live_entities | live_people) - set(node_by_id)):
        _error(errors, f"live registry node {missing!r} is missing")

    observed_degree = Counter()
    for i, edge in enumerate(edges):
        where = f"edges[{i}]"
        if not isinstance(edge, dict):
            _error(errors, f"{where} must be an object")
            continue
        if set(edge) != EDGE_FIELDS:
            _error(errors, f"{where} has invalid field set")
        src, dst = edge.get("source"), edge.get("target")
        if src not in node_by_id or dst not in node_by_id:
            _error(errors, f"{where} endpoint must reference a graph node")
            continue
        observed_degree[src] += 1
        observed_degree[dst] += 1
        etype = edge.get("type")
        if etype not in EDGE_TYPES:
            _error(errors, f"{where}.type has invalid value {etype!r}")
        else:
            src_kind = node_by_id[src]["kind"]
            dst_kind = node_by_id[dst]["kind"]
            permitted = {
                "owns": ({"entity"}, {"entity"}),
                "related": ({"entity"}, {"entity"}),
                "founded": ({"entity", "person", "unresolved"}, {"entity"}),
                "directs": ({"entity", "person", "unresolved"}, {"entity"}),
                "role": ({"person"}, {"entity"}),
                "produces": ({"entity"}, {"product"}),
                "procures": ({"government_customer"}, {"entity"}),
                "confirmed_field_use": ({"entity", "product"}, {"military_unit"}),
                "cbst_tie": ({"entity"}, {"entity"}),
            }[etype]
            if src_kind not in permitted[0] or dst_kind not in permitted[1]:
                _error(errors, f"{where} has invalid {src_kind}->{dst_kind} endpoints for {etype}")
        sid = edge.get("source_id")
        if sid is not None and sid not in source_ids:
            _error(errors, f"{where}.source_id references unknown source {sid!r}")
        if edge.get("as_of") is not None and not _is_date(edge["as_of"]):
            _error(errors, f"{where}.as_of must be YYYY-MM-DD or null")
        if not isinstance(edge.get("weight"), (int, float)) or isinstance(edge.get("weight"), bool):
            _error(errors, f"{where}.weight must be numeric")
        confidence = edge.get("confidence")
        if etype == "cbst_tie":
            if confidence not in CBST_TIE_CONFIDENCE:
                _error(errors, f"{where}.confidence has invalid value {confidence!r} for cbst_tie")
        elif confidence is not None:
            _error(errors, f"{where}.confidence must be null for non-cbst_tie edge type {etype!r}")
        status = edge.get("temporal_status")
        if status not in TEMPORAL_STATUSES:
            _error(errors, f"{where}.temporal_status has invalid value {status!r}")
        elif status in {"current", "historical"}:
            if sid is None or not _is_date(edge.get("as_of")):
                _error(errors, f"{where} {status} status requires a cited YYYY-MM-DD as_of")

    for node_id, node in node_by_id.items():
        if node.get("degree") != observed_degree[node_id]:
            _error(errors, f"node {node_id!r} degree does not match its incident edges")

    unresolved_by_id: dict[str, dict] = {}
    for i, item in enumerate(unresolved):
        where = f"unresolved[{i}]"
        if not isinstance(item, dict) or set(item) != {"id", "raw_name", "contexts"}:
            _error(errors, f"{where} must contain exactly id, raw_name, contexts")
            continue
        node_id = item.get("id")
        if node_id in unresolved_by_id:
            _error(errors, f"duplicate unresolved stub {node_id!r}")
            continue
        unresolved_by_id[node_id] = item
        node = node_by_id.get(node_id)
        if not node or node.get("kind") != "unresolved":
            _error(errors, f"{where}.id does not identify an unresolved node")
            continue
        if item.get("raw_name") != node.get("label"):
            _error(errors, f"{where}.raw_name must match its node label")
        if not isinstance(item.get("contexts"), list) or not all(isinstance(x, str) for x in item["contexts"]):
            _error(errors, f"{where}.contexts must be a list of strings")
        if observed_degree[node_id] == 0:
            _error(errors, f"{where}.id has no incident edge")
    stub_ids = {node_id for node_id, node in node_by_id.items() if node.get("kind") == "unresolved"}
    if stub_ids != set(unresolved_by_id):
        _error(errors, "unresolved[] does not have one entry for every unresolved node")

    return errors


VIEW_NAMES = ("cited_only", "current_only", "core_network", "evidence_gaps")


def _projection_ready(graph: dict) -> bool:
    """Return whether projection code can safely read required graph members."""
    if not isinstance(graph, dict):
        return False
    nodes, edges = graph.get("nodes"), graph.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        return False
    return (
        all(isinstance(node, dict) and isinstance(node.get("id"), str)
            and isinstance(node.get("kind"), str) for node in nodes)
        and all(isinstance(edge, dict) and isinstance(edge.get("source"), str)
                and isinstance(edge.get("target"), str)
                and "source_id" in edge and "temporal_status" in edge
                for edge in edges)
    )


def build_view_projections(graph: dict) -> dict[str, dict]:
    """Derive every view directly from the canonical graph, deterministically."""
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
    return {
        "cited_only": subgraph([edge for edge in edges if edge["source_id"] is not None]),
        "current_only": subgraph([edge for edge in edges if edge["temporal_status"] == "current"]),
        "core_network": subgraph([
            edge for edge in edges
            if edge["source"] in core_ids or edge["target"] in core_ids
        ]),
        "evidence_gaps": subgraph([edge for edge in edges if edge["source_id"] is None]),
    }


def validate_views(graph: dict, views: dict) -> list[str]:
    """Require serialized views to exactly equal their canonical projections."""
    errors: list[str] = []
    if not isinstance(views, dict) or views.get("schema_version") != GRAPH_SCHEMA_VERSION:
        return ["graph views: schema_version must match the graph schema"]
    if set(views) != {"schema_version", "generated_from", "views"}:
        return ["graph views: top-level fields must be schema_version, generated_from, views"]
    if views.get("generated_from") != "relationship_graph.json":
        return ["graph views: generated_from must be relationship_graph.json"]
    if not _projection_ready(graph):
        return ["graph views: cannot derive expected projections because the "
                "canonical graph has malformed node or edge members"]
    view_map = views.get("views")
    if not isinstance(view_map, dict) or set(view_map) != set(VIEW_NAMES):
        return ["graph views: expected cited_only, current_only, core_network, evidence_gaps"]
    expected_views = build_view_projections(graph)

    for name in VIEW_NAMES:
        view = view_map[name]
        if not isinstance(view, dict) or not isinstance(view.get("nodes"), list) or not isinstance(view.get("edges"), list):
            errors.append(f"graph views: {name} must contain nodes and edges lists")
            continue
        expected = expected_views[name]
        if view["edges"] != expected["edges"]:
            actual_keys = Counter(json_key(edge) for edge in view["edges"] if isinstance(edge, dict))
            expected_keys = Counter(json_key(edge) for edge in expected["edges"])
            missing = sum((expected_keys - actual_keys).values())
            extra = sum((actual_keys - expected_keys).values())
            errors.append(
                f"graph views: {name} edge projection differs from its canonical "
                f"predicate ({missing} missing, {extra} extra or substituted; "
                "run scripts/build_relationship_graph.py)")
        if view["nodes"] != expected["nodes"]:
            actual_ids = Counter(
                node.get("id") for node in view["nodes"]
                if isinstance(node, dict) and node.get("id")
            )
            expected_ids = Counter(node["id"] for node in expected["nodes"])
            missing = sum((expected_ids - actual_ids).values())
            extra = sum((actual_ids - expected_ids).values())
            errors.append(
                f"graph views: {name} node projection differs from endpoints of "
                f"its canonical edges ({missing} missing, {extra} extra, or "
                "non-canonical node content/order; run scripts/build_relationship_graph.py)")
    return errors


def json_key(value: dict) -> str:
    """Canonical comparison key without importing a second graph dependency."""
    import json
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
