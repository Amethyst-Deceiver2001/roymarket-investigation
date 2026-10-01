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
from check_registry import validate_generated_graph  # noqa: E402
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
        # The newest dated entry is the current holder (builder rule since 2026-09-29),
        # so a former founder needs a newer entry that no longer lists them.
        "founders_history": [
            {"value": "Former Founder (25%)", "as_of": "2025-01-02", "source_id": "s1"},
            {"value": "Unknown Founder (100%)", "as_of": "2026-01-02", "source_id": "s1"},
        ],
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
        former_founder = next(
            edge for edge in self.graph["edges"]
            if edge["source"] == "stub::former founder" and edge["target"] == "core"
        )
        self.assertEqual("historical", former_founder["temporal_status"])
        self.assertEqual("s1", former_founder["source_id"])
        self.assertEqual([], validate_graph(self.graph, ENTITIES, PEOPLE, SOURCES))
        self.assertEqual([], validate_views(self.graph, self.views))
        self.assertEqual(
            self.graph,
            build_graph(copy.deepcopy(ENTITIES), copy.deepcopy(PEOPLE)),
        )

    def test_held_off_entity_is_omitted_even_with_ownership_edges(self):
        entities = copy.deepcopy(ENTITIES)
        entities[1]["graph_tier"] = "held-off"  # "ordinary", owned 100% by the hub-connected "core"
        graph = build_graph(entities, copy.deepcopy(PEOPLE))
        ids = {node["id"] for node in graph["nodes"]}
        self.assertNotIn("ordinary", ids)
        self.assertIn("ordinary", graph["detached_ids"])
        self.assertTrue(all("ordinary" not in (e["source"], e["target"]) for e in graph["edges"]))
        self.assertEqual([], validate_graph(graph, entities, PEOPLE, SOURCES))

    def test_contract_with_graph_false_is_not_drawn(self):
        entities = copy.deepcopy(ENTITIES)
        entities[0]["government_contracts"] = [
            {"customer": "Министерство обороны Российской Федерации", "date": "2014-06-09",
             "value_rub": 10.0, "source_id": "s1"},
            {"customer": "Федеральное агентство воздушного транспорта", "date": "2014-06-10",
             "value_rub": 20.0, "source_id": "s1", "graph": False},
        ]
        graph = build_graph(entities, copy.deepcopy(PEOPLE))
        labels = {n["label"] for n in graph["nodes"] if n["kind"] == "government_customer"}
        self.assertEqual({"Министерство обороны Российской Федерации"}, labels)
        self.assertEqual(1, sum(1 for e in graph["edges"] if e["type"] == "procures"))

    def test_historical_founder_share_suffix_does_not_create_false_stub(self):
        entities = [{
            "slug": "company",
            "name_ru": "ООО «Company»",
            "tier": "manufacturer",
            "founders": [{"name": "Current Founder", "share_pct": 50}],
            "founders_history": [{
                "value": "Current Founder 50% (₽1 550 000)",
                "as_of": "2025-04-14",
                "source_id": "s1",
            }],
        }]
        people = [{"slug": "current-founder", "fio_ru": "Current Founder"}]

        graph = build_graph(entities, people)
        self.assertNotIn("stub::current founder 50%", {node["id"] for node in graph["nodes"]})
        self.assertTrue(any(
            edge["type"] == "founded"
            and edge["source"] == "current-founder"
            and edge["target"] == "company"
            and edge["label"] == "50%"
            for edge in graph["edges"]
        ))
        self.assertFalse(any(
            edge["type"] == "founded"
            and edge["source"] == "current-founder"
            and edge["target"] == "company"
            and edge["temporal_status"] == "historical"
            for edge in graph["edges"]
        ))

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
        bad_views["views"]["cited_only"]["edges"].pop()
        self.assertTrue(any("edge projection differs" in message
                            for message in validate_views(self.graph, bad_views)))

    def test_rebuild_rejects_substituted_valid_source(self):
        bad = copy.deepcopy(self.graph)
        edge = next(edge for edge in bad["edges"] if edge["source_id"] == "s1")
        edge["source_id"] = "s2"
        self.assertEqual([], validate_graph(bad, ENTITIES, PEOPLE, SOURCES))
        bad_views = build_views(bad)
        self.assertEqual([], validate_views(bad, bad_views))
        messages = validate_generated_graph(bad, bad_views, ENTITIES, PEOPLE, SOURCES)
        self.assertTrue(any("does not exactly match the deterministic rebuild" in message
                            for message in messages))

    def test_malformed_graph_returns_errors_without_view_traceback(self):
        malformed = {
            "schema_version": 2,
            "node_count": 1,
            "edge_count": 1,
            "unresolved_count": 0,
            "nodes": [{}],
            "edges": [{}],
            "unresolved": [],
        }
        self.assertTrue(any("cannot derive expected projections" in message
                            for message in validate_views(malformed, self.views)))
        messages = validate_generated_graph(
            malformed, self.views, ENTITIES, PEOPLE, SOURCES)
        self.assertTrue(any("nodes[0].kind" in message for message in messages))
        self.assertTrue(any("edges[0] endpoint" in message for message in messages))

    def test_sells_for_edge_carries_channel_and_basis_and_replaces_dealer_link(self):
        entities = copy.deepcopy(ENTITIES)
        entities[1]["sells_for"] = [{"slug": "core", "channel": "Ozon (test store)", "basis": "doc", "source_id": "s1"}]
        entities[0]["related_entities"] = [{"slug": "ordinary", "relationship_type": "dealer", "source_id": "s1"}]
        graph = build_graph(entities, copy.deepcopy(PEOPLE))
        sells = [e for e in graph["edges"] if e["type"] == "sells_for"]
        self.assertEqual([("ordinary", "core", "Ozon (test store)", "doc")],
                         [(e["source"], e["target"], e["label"], e["confidence"]) for e in sells])
        # the prose dealer link for the same pair (either direction) is not drawn a second time
        self.assertFalse(any(e["type"] == "related" and e["label"] == "dealer" for e in graph["edges"]))
        self.assertEqual([], validate_graph(graph, entities, PEOPLE, SOURCES))

    def test_sells_for_rejects_unknown_basis_and_person_endpoint(self):
        entities = copy.deepcopy(ENTITIES)
        entities[1]["sells_for"] = [{"slug": "core", "channel": "Ozon", "basis": "doc", "source_id": "s1"}]
        graph = build_graph(entities, copy.deepcopy(PEOPLE))
        bad = copy.deepcopy(graph)
        edge = next(e for e in bad["edges"] if e["type"] == "sells_for")
        edge["confidence"] = "rumour"
        self.assertTrue(any("sells_for" in m for m in validate_graph(bad, entities, PEOPLE, SOURCES)))
        bad = copy.deepcopy(graph)
        edge = next(e for e in bad["edges"] if e["type"] == "sells_for")
        edge["target"] = "alice"
        self.assertTrue(any("invalid entity->person endpoints" in m for m in validate_graph(bad, entities, PEOPLE, SOURCES)))

    def test_unlinked_sells_for_target_is_dropped_not_crashing(self):
        entities = copy.deepcopy(ENTITIES)
        entities[1]["sells_for"] = [{"slug": "does-not-exist", "channel": "Ozon", "basis": "doc"}]
        graph = build_graph(entities, copy.deepcopy(PEOPLE))
        self.assertFalse(any(e["type"] == "sells_for" for e in graph["edges"]))

    def test_quality_report_is_deterministic(self):
        first = report(self.graph, self.views, ENTITIES, PEOPLE)
        second = report(self.graph, self.views, ENTITIES, PEOPLE)
        self.assertEqual(first, second)
        self.assertIn("Live-registry parity: 2/2 entities; 1/1 people", first)


if __name__ == "__main__":
    unittest.main()
