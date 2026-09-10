#!/usr/bin/env python3
"""Focused contract tests for the derived registry relationship graph."""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_relationship_graph import build_graph, build_views, classify_product  # noqa: E402
from graph_contract import validate_graph, validate_views  # noqa: E402
from graph_quality_report import report  # noqa: E402


SOURCES = [{"id": "s1"}, {"id": "s2"}]
ENTITIES = [
    {
        "slug": "core",
        "name_ru": "ООО «Core»",
        "tier": "cbst-core",
        "director": "Alice Example",
        "director_history": [{"value": "Alice Example", "as_of": "2026-01-02", "source_id": "s1"}],
        "founders": "Unknown Founder (100%)",
        "products": [
            {"name_ru": "Generic UAV jammer", "description": "UAV jammer", "source_id": "s2"},
            {"name_ru": "Explicit platform", "description": "multirotor vehicle-mounted jammer", "source_id": "s2"},
        ],
    },
    {
        "slug": "ordinary",
        "name_ru": "ООО «Ordinary»",
        "tier": "manufacturer",
        "parents": [{"slug": "core", "share_percent": 100, "source_id": "s1"}],
    },
    {
        "slug": "merged",
        "name_ru": "ООО «Merged»",
        "tier": "manufacturer",
        "_merged_into": "ordinary",
    },
]
PEOPLE = [
    {
        "slug": "alice",
        "fio_ru": "Alice Example",
        "roles": [{"entity_slug": "core", "title": "Director", "source_id": "s1"}],
    },
    {
        "slug": "merged-person",
        "fio_ru": "Merged Person",
        "_merged_into": "alice",
    },
]


class RelationshipGraphTests(unittest.TestCase):
    def setUp(self):
        self.graph = build_graph(copy.deepcopy(ENTITIES), copy.deepcopy(PEOPLE))
        self.views = build_views(self.graph)

    def test_generic_terms_remain_unclassified(self):
        generic = classify_product("Generic UAV jammer", "UAV jammer")
        self.assertEqual(
            generic,
            {"status": "unclassified", "uav_platform": "unknown", "ew_installation": "unknown"},
        )
        explicit = classify_product("Explicit platform", "multirotor vehicle-mounted jammer")
        self.assertEqual(explicit["status"], "classified")
        self.assertEqual(explicit["uav_platform"], "multirotor")
        self.assertEqual(explicit["ew_installation"], "vehicle-mounted")

    def test_build_excludes_tombstones_and_preserves_stub(self):
        ids = {node["id"] for node in self.graph["nodes"]}
        self.assertNotIn("merged", ids)
        self.assertNotIn("merged-person", ids)
        self.assertIn("stub::unknown founder", ids)
        self.assertEqual([], validate_graph(self.graph, ENTITIES, PEOPLE, SOURCES))
        self.assertEqual([], validate_views(self.graph, self.views))
        self.assertEqual(
            self.graph,
            build_graph(copy.deepcopy(ENTITIES), copy.deepcopy(PEOPLE)),
        )

    def test_validator_rejects_graph_contract_breaks(self):
        bad = copy.deepcopy(self.graph)
        bad["edges"][0]["source_id"] = "missing"
        bad["edges"][1]["type"] = "owns"
        bad["edges"][2]["temporal_status"] = "current"
        bad["edges"][2]["source_id"] = None
        bad["unresolved"] = []
        messages = validate_graph(bad, ENTITIES, PEOPLE, SOURCES)
        self.assertTrue(any("unknown source" in message for message in messages))
        self.assertTrue(any("invalid" in message and "endpoints" in message for message in messages))
        self.assertTrue(any("current status requires" in message for message in messages))
        self.assertTrue(any("unresolved[]" in message for message in messages))

    def test_validator_rejects_tombstone_and_bad_views(self):
        bad = copy.deepcopy(self.graph)
        bad["nodes"].append({
            "id": "merged", "kind": "entity", "label": "ООО «Merged»",
            "name_latin": None, "inn": None, "tier": "manufacturer",
            "sanctioned": False, "legal_form": None, "degree": 0,
        })
        bad["node_count"] += 1
        self.assertTrue(any("tombstoned registry node" in message
                            for message in validate_graph(bad, ENTITIES, PEOPLE, SOURCES)))
        bad_views = copy.deepcopy(self.views)
        bad_views["views"]["cited_only"]["edges"].append(
            next(edge for edge in self.graph["edges"] if edge["source_id"] is None)
        )
        self.assertTrue(any("uncited edge" in message for message in validate_views(self.graph, bad_views)))

    def test_quality_report_is_deterministic(self):
        first = report(self.graph, self.views, ENTITIES, PEOPLE)
        second = report(self.graph, self.views, ENTITIES, PEOPLE)
        self.assertEqual(first, second)
        self.assertIn("Live-registry parity: 2/2 entities; 1/1 people", first)


if __name__ == "__main__":
    unittest.main()
