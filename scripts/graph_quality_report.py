#!/usr/bin/env python3
"""Report a deterministic quality baseline for relationship-graph artifacts.

This is an evidence-quality report, not a claim generator.  "Cited" means an
edge carries a source_id from its originating structured field; an uncited edge
is reported as an evidence gap, not assigned a likely source from elsewhere in
the registry.

Usage:
    python3 scripts/graph_quality_report.py
    python3 scripts/graph_quality_report.py --out data/registry/relationship_graph_quality.md
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

from graph_contract import validate_graph, validate_views

REPO = Path(__file__).resolve().parent.parent
REG = REPO / "data" / "registry"


def load(name: str):
    return json.loads((REG / name).read_text(encoding="utf-8"))


def report(graph: dict, views: dict, entities: list[dict], people: list[dict]) -> str:
    """Render a stable Markdown report with only facts derivable from the graph."""
    node_kinds = Counter(node["kind"] for node in graph["nodes"])
    edge_types = Counter(edge["type"] for edge in graph["edges"])
    temporal = Counter(edge["temporal_status"] for edge in graph["edges"])
    cited = sum(edge["source_id"] is not None for edge in graph["edges"])
    live_entities = sum(not entity.get("_merged_into") for entity in entities)
    live_people = sum(not person.get("_merged_into") for person in people)
    raw = json.dumps(graph, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    graph_hash = hashlib.sha256(raw).hexdigest()

    lines = [
        "# Relationship graph quality baseline",
        "",
        "This report is deterministic local aggregation over `data/registry/`; "
        "it does not assert facts or fill missing citations.",
        "",
        f"- Graph schema: `{graph['schema_version']}`",
        f"- Canonical graph SHA-256: `{graph_hash}`",
        f"- Live-registry parity: {node_kinds['entity']}/{live_entities} entities; "
        f"{node_kinds['person']}/{live_people} people",
        f"- Cited edges: {cited}/{len(graph['edges'])}",
        f"- Directly uncited relation edges (evidence gaps): "
        f"{len(graph['edges']) - cited}/{len(graph['edges'])}",
        f"- Explicit unresolved stubs: {graph['unresolved_count']}",
        "",
        "## Nodes",
        "",
        "| Kind | Count |",
        "|---|---:|",
    ]
    lines.extend(f"| {kind} | {node_kinds[kind]} |" for kind in sorted(node_kinds))
    lines.extend(["", "## Edges", "", "| Type | Total | Cited | Uncited |", "|---|---:|---:|---:|"])
    for edge_type in sorted(edge_types):
        typed = [edge for edge in graph["edges"] if edge["type"] == edge_type]
        typed_cited = sum(edge["source_id"] is not None for edge in typed)
        lines.append(f"| {edge_type} | {len(typed)} | {typed_cited} | {len(typed) - typed_cited} |")
    lines.extend(["", "## Temporal semantics", "", "| State | Count |", "|---|---:|"])
    lines.extend(f"| {status} | {temporal[status]} |" for status in ("current", "historical", "unknown"))
    lines.extend([
        "",
        "Only directly cited, dated director/history facts can be labelled `current` "
        "or `historical`; all other relationship timing remains `unknown`.",
        "",
        "## Derived views",
        "",
        "| View | Nodes | Edges | Meaning |",
        "|---|---:|---:|---|",
    ])
    meanings = {
        "cited_only": "Edges with an originating source_id only",
        "current_only": "Explicitly cited and dated current historical-field edges only",
        "core_network": "One-hop edges incident to a cbst-core entity",
        "evidence_gaps": "Edges lacking an originating source_id; not evidence of absence",
    }
    for name in ("cited_only", "current_only", "core_network", "evidence_gaps"):
        view = views["views"][name]
        lines.append(f"| {name} | {len(view['nodes'])} | {len(view['edges'])} | {meanings[name]} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", help="write the Markdown report to this path")
    args = ap.parse_args()
    try:
        entities = load("entities.json")
        people = load("people.json")
        sources = load("sources.json")
        graph = load("relationship_graph.json")
        views = load("relationship_graph_views.json")
    except (OSError, json.JSONDecodeError) as ex:
        print(f"error: unable to load graph inputs: {ex}", file=sys.stderr)
        return 1

    errors = validate_graph(graph, entities, people, sources) + validate_views(graph, views)
    if errors:
        for error in errors:
            print(f"ERROR   {error}")
        return 1
    text = report(graph, views, entities, people)
    if args.out:
        destination = Path(args.out)
        destination.write_text(text, encoding="utf-8")
        print(f"wrote {destination}")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
