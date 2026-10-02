#!/usr/bin/env python3
"""RETIRED 02.10.2026 with the public graph explorer (user); kept for reference, do not run.

Refresh the embedded graph data in docs/relationship-graph.html in place.

docs/relationship-graph.html (the live, hand-built D3 force-graph explorer)
is NOT otherwise generated -- every prior "refresh graph exhibit data"
commit hand-substituted a fresh copy of data/registry/relationship_graph.json
into its <script id="graph-data" type="application/json"> block. That data
shape is an exact match for relationship_graph.json's own top-level shape
(schema_version, generated_from, node_count, edge_count, unresolved_count,
nodes, edges, unresolved, detached_ids) -- confirmed by direct comparison
2026-09-21 -- so this script does the same substitution mechanically instead
of by hand, the same "generated, not hand-written" discipline every other
docs/ page already gets.

This does NOT rebuild relationship_graph.json itself -- run
build_relationship_graph.py first (as always, after any registry change
that could touch ownership/roles/products/cbst_tie). This script only
re-embeds whatever relationship_graph.json currently holds into the page
and reports the before/after counts, so a stale embed is visible rather
than silently trusted.

Replaces the old build_graph_explorer.py / templates/relationship_graph.html
.jinja2 pipeline, which rendered a completely different, superseded design
and had drifted out of sync with the live page since 2026-09-10 -- removed
2026-09-21 rather than left as a landmine in run_pipeline.py's local stage
list (it would have silently overwritten this page with the old design).

Local file processing only, no network. Run after build_relationship_graph.py:

    python3 scripts/build_relationship_graph.py
    python3 scripts/refresh_graph_page_data.py
    python3 scripts/check_tag_balance.py docs/relationship-graph.html
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
GRAPH_JSON = REPO / "data" / "registry" / "relationship_graph.json"
PAGE = REPO / "docs" / "relationship-graph.html"

BLOCK_RE = re.compile(
    r'(<script id="graph-data" type="application/json">)(.*?)(</script>)',
    re.S,
)


def script_json(value) -> str:
    """Serialize safely for an inert application/json script element --
    same escaping the old build_graph_explorer.py used, so a stray </script>
    or an HTML-special character inside a label/note can't break the page."""
    return (
        json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )


def main():
    graph = json.loads(GRAPH_JSON.read_text(encoding="utf-8"))
    html = PAGE.read_text(encoding="utf-8")

    m = BLOCK_RE.search(html)
    if not m:
        raise SystemExit(
            f'{PAGE}: no <script id="graph-data" type="application/json"> '
            f"block found -- page structure changed, update BLOCK_RE."
        )

    old_json_text = m.group(2)
    try:
        old = json.loads(old_json_text)
        old_summary = (old.get("node_count"), old.get("edge_count"), old.get("unresolved_count"))
    except json.JSONDecodeError:
        old_summary = ("?", "?", "?")

    new_text = script_json(graph)
    html = html[: m.start()] + m.group(1) + new_text + m.group(3) + html[m.end():]
    PAGE.write_text(html, encoding="utf-8")

    new_summary = (graph.get("node_count"), graph.get("edge_count"), graph.get("unresolved_count"))
    print(f"{PAGE}: graph-data refreshed")
    print(f"  before: {old_summary[0]} nodes, {old_summary[1]} edges, {old_summary[2]} unresolved")
    print(f"  after:  {new_summary[0]} nodes, {new_summary[1]} edges, {new_summary[2]} unresolved")
    if old_summary == new_summary:
        print("  (no change -- already current)")


if __name__ == "__main__":
    main()
