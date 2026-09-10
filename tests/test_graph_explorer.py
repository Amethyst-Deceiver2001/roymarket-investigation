#!/usr/bin/env python3
"""Focused tests for the local relationship-graph explorer renderer."""
from __future__ import annotations

import copy
import re
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_graph_explorer import build_context, render_explorer, source_subset  # noqa: E402
from build_relationship_graph import build_graph, build_views  # noqa: E402


ENTITIES = [{
    "slug": "core",
    "name_ru": "Core entity",
    "tier": "cbst-core",
    "director": "Example Person",
    "director_history": [{
        "value": "Example Person", "as_of": "2026-01-02", "source_id": "s1",
    }],
    "founders": "Unresolved Founder (100%)",
    "products": [{
        "name_ru": "Generic UAV jammer", "description": "Generic jammer", "source_id": "s1",
    }],
}]
PEOPLE = [{"slug": "person", "fio_ru": "Example Person"}]
SOURCES = [
    {"id": "s1", "type": "EGRUL", "path": "data/sources/example.pdf",
     "url": "https://example.test/source", "captured_date": "2026-01-03", "as_of": "2026-01-02"},
    {"id": "s2", "type": "unused", "path": "data/sources/unused.pdf",
     "url": None, "captured_date": None, "as_of": None},
]


class GraphExplorerTests(unittest.TestCase):
    def setUp(self):
        self.graph = build_graph(copy.deepcopy(ENTITIES), copy.deepcopy(PEOPLE))
        self.views = build_views(self.graph)
        self.context = build_context(self.graph, self.views, ENTITIES, PEOPLE, SOURCES)

    def test_renderer_exposes_accessible_evidence_first_controls(self):
        html = render_explorer(self.context)
        for marker in (
            'href="#graph-table"', 'data-view="cited_only"', 'data-view="current_only"',
            'data-view="core_network"', 'data-view="evidence_gaps"', 'id="graph-search"',
            'id="graph-table"', 'id="detail-content"', 'id="map-list"',
            'type="application/json"', "Product labels are heuristics",
            "not a global layout", "Unresolved research lead",
        ):
            self.assertIn(marker, html)
        self.assertIn("https://example.test/source", html)
        self.assertNotIn("unused.pdf", html)

    def test_source_subset_only_includes_direct_graph_references(self):
        subset = source_subset(self.graph, SOURCES)
        self.assertEqual(["s1"], [source["id"] for source in subset])

    def test_renderer_refuses_invalid_canonical_graph(self):
        malformed = copy.deepcopy(self.graph)
        malformed["nodes"][0]["id"] = ""
        with self.assertRaises(ValueError):
            build_context(malformed, self.views, ENTITIES, PEOPLE, SOURCES)

    def test_dark_selected_controls_meet_wcag_aa_contrast(self):
        html = render_explorer(self.context)
        dark_theme = re.search(r":root\[data-theme=\"dark\"\] \{([^}]*)\}", html)
        self.assertIsNotNone(dark_theme)
        colors = dict(re.findall(r"--(accent(?:-ink)?):\s*(#[0-9a-f]{3,6})", dark_theme.group(1)))
        selected_rule = re.search(r'button\[aria-pressed="true"\] \{([^}]*)\}', html)
        self.assertIsNotNone(selected_rule)
        selected_color = re.search(r"(?:^|;)\s*color:([^;]+);", selected_rule.group(1))
        self.assertIsNotNone(selected_color)
        self.assertEqual("var(--accent-ink)", selected_color.group(1).strip())
        self.assertGreaterEqual(contrast_ratio(colors["accent"], colors["accent-ink"]), 4.5)


def contrast_ratio(first: str, second: str) -> float:
    def luminance(color: str) -> float:
        components = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
        adjusted = [
            component / 12.92 if component <= 0.04045
            else ((component + 0.055) / 1.055) ** 2.4
            for component in components
        ]
        return 0.2126 * adjusted[0] + 0.7152 * adjusted[1] + 0.0722 * adjusted[2]

    high, low = sorted((luminance(first), luminance(second)), reverse=True)
    return (high + 0.05) / (low + 0.05)


if __name__ == "__main__":
    unittest.main()
