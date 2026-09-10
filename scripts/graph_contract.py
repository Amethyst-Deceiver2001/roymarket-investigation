#!/usr/bin/env python3
"""Shared schema contract for generated relationship-graph artifacts.

The graph is a derived view of the registry.  Its edges may be intentionally
uncited when the source registry field is an unresolved legacy assertion; the
contract preserves that distinction rather than inventing a source reference.
"""
from __future__ import annotations

import re
from collections import Counter

GRAPH_SCHEMA_VERSION = 2
NODE_KINDS = {"entity", "person", "product", "unresolved"}
EDGE_TYPES = {"owns", "related", "founded", "directs", "role", "produces"}
TEMPORAL_STATUSES = {"current", "historical", "unknown"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

NODE_FIELDS = {
    "entity": {"id", "kind", "label", "name_latin", "inn", "tier",
               "sanctioned", "legal_form", "degree"},
    "person": {"id", "kind", "label", "name_latin", "sanctioned", "degree"},
    "product": {"id", "kind", "label", "owner_slug", "source_id",
                "classification", "degree"},
    "unresolved": {"id", "kind", "label", "degree"},
}
EDGE_FIELDS = {
    "source", "target", "type", "label", "source_id", "as_of", "weight",
    "temporal_status",
}
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


def validate_views(graph: dict, views: dict) -> list[str]:
    """Validate derived views are exact edge/node subsets of the full graph."""
    errors: list[str] = []
    if not isinstance(views, dict) or views.get("schema_version") != GRAPH_SCHEMA_VERSION:
        return ["graph views: schema_version must match the graph schema"]
    full_nodes = {node["id"]: node for node in graph.get("nodes", []) if isinstance(node, dict) and node.get("id")}
    full_edges = {
        json_key(edge) for edge in graph.get("edges", []) if isinstance(edge, dict)
    }
    view_map = views.get("views")
    expected = {"cited_only", "current_only", "core_network", "evidence_gaps"}
    if not isinstance(view_map, dict) or set(view_map) != expected:
        return ["graph views: expected cited_only, current_only, core_network, evidence_gaps"]

    for name, view in view_map.items():
        if not isinstance(view, dict) or not isinstance(view.get("nodes"), list) or not isinstance(view.get("edges"), list):
            errors.append(f"graph views: {name} must contain nodes and edges lists")
            continue
        ids = {node.get("id") for node in view["nodes"] if isinstance(node, dict)}
        if len(ids) != len(view["nodes"]) or not ids <= set(full_nodes):
            errors.append(f"graph views: {name} contains unknown or duplicate nodes")
        for edge in view["edges"]:
            if json_key(edge) not in full_edges:
                errors.append(f"graph views: {name} contains an edge absent from full graph")
            elif edge.get("source") not in ids or edge.get("target") not in ids:
                errors.append(f"graph views: {name} edge endpoint is absent from its nodes")
        if name == "cited_only" and any(edge.get("source_id") is None for edge in view["edges"]):
            errors.append("graph views: cited_only includes an uncited edge")
        if name == "current_only" and any(edge.get("temporal_status") != "current" for edge in view["edges"]):
            errors.append("graph views: current_only includes a non-current edge")
        if name == "evidence_gaps" and any(edge.get("source_id") is not None for edge in view["edges"]):
            errors.append("graph views: evidence_gaps includes a cited edge")
    return errors


def json_key(value: dict) -> str:
    """Canonical comparison key without importing a second graph dependency."""
    import json
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
