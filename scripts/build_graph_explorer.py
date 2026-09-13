#!/usr/bin/env python3
"""Render the local, evidence-first relationship-graph explorer.

The explorer is generated only from the validated canonical graph, its
deterministic derived views, and source metadata already in the registry. It
does not collect, infer, or add citations. Run after build_relationship_graph:

    python3 scripts/build_graph_explorer.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import jinja2

sys.path.insert(0, str(Path(__file__).resolve().parent))
from graph_contract import validate_graph, validate_views  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
REG = REPO / "data" / "registry"
TEMPLATES = REPO / "templates"
OUT = REPO / "docs" / "relationship-graph.html"


def load_json(name: str):
    return json.loads((REG / name).read_text(encoding="utf-8"))


def script_json(value) -> str:
    """Serialize safely for an inert application/json script element."""
    return (json.dumps(value, ensure_ascii=False, separators=(",", ":"))
            .replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026"))


def source_subset(graph: dict, sources: list[dict]) -> list[dict]:
    """Expose metadata only for source IDs directly cited by graph records."""
    cited_ids = {
        item["source_id"]
        for item in [*graph["edges"], *graph["nodes"]]
        if item.get("source_id")
    }
    fields = ("id", "type", "path", "url", "captured_date", "as_of")
    return [
        {field: source.get(field) for field in fields}
        for source in sources
        if source.get("id") in cited_ids
    ]


def build_context(graph: dict, views: dict, entities: list[dict],
                  people: list[dict], sources: list[dict]) -> dict:
    """Validate inputs and return the template's self-contained data context."""
    graph_errors = validate_graph(graph, entities, people, sources)
    errors = [*graph_errors]
    if not graph_errors:
        errors.extend(validate_views(graph, views))
    if errors:
        raise ValueError("\n".join(errors))
    return {
        "graph_json": script_json(graph),
        "views_json": script_json(views),
        "sources_json": script_json(source_subset(graph, sources)),
        "node_count": graph["node_count"],
        "edge_count": graph["edge_count"],
        "cited_count": sum(edge["source_id"] is not None for edge in graph["edges"]),
        "gap_count": sum(edge["source_id"] is None for edge in graph["edges"]),
    }


def render_explorer(context: dict) -> str:
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(TEMPLATES),
        autoescape=True,
    )
    return env.get_template("relationship_graph.html.jinja2").render(**context)


def main() -> int:
    graph = load_json("relationship_graph.json")
    views = load_json("relationship_graph_views.json")
    entities = load_json("entities.json")
    people = load_json("people.json")
    sources = load_json("sources.json")
    try:
        context = build_context(graph, views, entities, people, sources)
    except ValueError as ex:
        print(f"error: graph explorer inputs are invalid:\n{ex}", file=sys.stderr)
        return 1
    OUT.write_text(render_explorer(context), encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)} — {context['node_count']} nodes, "
          f"{context['edge_count']} edges; {context['cited_count']} cited and "
          f"{context['gap_count']} evidence-gap edges")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
