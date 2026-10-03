#!/usr/bin/env python3
"""Tests for the reader-safe relationship neighbourhood explorer."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "exhibits"))

from build_neighbourhood import build_payload, neighbourhood, page, search  # noqa: E402


class NeighbourhoodTests(unittest.TestCase):
    def setUp(self):
        self.graph = {
            "schema_version": 12,
            "nodes": [
                {"id": "internal-root", "kind": "entity", "label": "ООО «Ёлка»",
                 "name_latin": "LLC Elka", "inn": "1234567890", "sanctioned": False},
                {"id": "internal-person", "kind": "person", "label": "Тестовый директор",
                 "name_latin": "Test Director", "sanctioned": True},
                {"id": "internal-unit", "kind": "military_unit", "label": "в/ч 12345"},
                {"id": "unconnected", "kind": "entity", "label": "Other entity"},
            ],
            "edges": [
                {"source": "internal-root", "target": "internal-person", "type": "directs",
                 "source_id": "s1234", "grade": "doc", "as_of": "2026-01-02",
                 "temporal_status": "current"},
                {"source": "internal-person", "target": "internal-unit", "type": "related",
                 "source_id": "missing-source", "grade": "open", "temporal_status": "unknown"},
            ],
        }
        self.sources = [{"id": "s1234", "title": "Registry extract", "public_url": "https://example.test/source"}]
        self.payload = build_payload(self.graph, self.sources)

    def test_search_matches_case_and_yo_and_identifier(self):
        self.assertEqual([0], search(self.payload, "елКа"))
        self.assertEqual([0], search(self.payload, "1234567890"))
        self.assertEqual([], search(self.payload, "ё"))

    def test_neighbourhood_is_undirected_and_depth_limited(self):
        distances, edges = neighbourhood(self.payload, 0, 1)
        self.assertEqual({0: 0, 1: 1}, distances)
        self.assertEqual(1, len(edges))
        distances, edges = neighbourhood(self.payload, 0, 2)
        self.assertEqual({0: 0, 1: 1, 2: 2}, distances)
        self.assertEqual(2, len(edges))
        self.assertEqual({}, neighbourhood(self.payload, 99, 1)[0])

    def test_reader_payload_omits_registry_and_source_ids(self):
        serialized = json.dumps(self.payload, ensure_ascii=False)
        self.assertNotIn("internal-root", serialized)
        self.assertNotIn("s1234", serialized)
        self.assertNotIn("missing-source", serialized)
        self.assertEqual("Registry extract", self.payload["edges"][0]["citation"]["title"])
        self.assertIsNone(self.payload["edges"][1]["citation"])

    def test_render_uses_reader_safe_names_and_source_descriptions(self):
        document = page(self.payload)
        self.assertIn("Registry extract", document)
        self.assertNotIn("s1234", document)
        self.assertNotIn("internal-root", document)
        self.assertIn("Not documented", document)
        self.assertIn("One step", document)
        self.assertIn("Two steps", document)


if __name__ == "__main__":
    unittest.main()
