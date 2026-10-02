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

    def test_sells_for_envelope_rides_in_edge_detail_and_is_validated(self):
        entities = copy.deepcopy(ENTITIES)
        entities[1]["sells_for"] = [{
            "slug": "core", "channel": "Ozon", "basis": "doc", "source_id": "s1", "products": ["propellers 8 in"],
            "status_history": [{"status": "listed", "as_of": "2026-07-06", "source_id": "s1"},
                               {"status": "announced", "as_of": "2026-06-01", "source_id": "s1"}],
            "role": "licensed_dealer", "asserted_by": "self", "credibility": "doc", "authorised": "n/a", "open": "Поставщик not established"}]
        graph = build_graph(entities, copy.deepcopy(PEOPLE))
        edge = next(e for e in graph["edges"] if e["type"] == "sells_for")
        # status is the latest dated state, whatever the order of the list
        self.assertEqual({"products": ["propellers 8 in"], "status": "listed", "role": "licensed_dealer", "asserted_by": "self",
                          "credibility": "doc", "authorised": "n/a", "open": "Поставщик not established"},
                         edge["detail"])
        self.assertEqual([], validate_graph(graph, entities, PEOPLE, SOURCES))
        # an edge with no envelope field carries no detail, and every other edge type never does
        self.assertTrue(all(e["detail"] is None for e in graph["edges"] if e is not edge))
        for key, value in (("status", "teleported"), ("role", "wizard"), ("asserted_by", "rumour"), ("authorised", "maybe"),
                           ("products", "propellers")):
            bad = copy.deepcopy(graph)
            next(e for e in bad["edges"] if e["type"] == "sells_for")["detail"][key] = value
            self.assertTrue(any("detail" in m for m in validate_graph(bad, entities, PEOPLE, SOURCES)), key)
        # the finer credibility may not contradict the coarse basis
        bad = copy.deepcopy(graph)
        next(e for e in bad["edges"] if e["type"] == "sells_for")["detail"]["credibility"] = "inferred"
        self.assertTrue(any("contradicts basis" in m for m in validate_graph(bad, entities, PEOPLE, SOURCES)))
        # detail on a non-sells_for edge is rejected
        bad = copy.deepcopy(graph)
        other = next(e for e in bad["edges"] if e["type"] != "sells_for")
        other["detail"] = {"status": "listed"}
        self.assertTrue(any("detail must be null" in m for m in validate_graph(bad, entities, PEOPLE, SOURCES)))

    def test_platform_partners_draw_graded_edges_by_kind(self):
        entities = copy.deepcopy(ENTITIES)
        entities[1]["platform_partners"] = [
            {"slug": "core", "kind": "bank", "basis": "doc", "source_id": "s1", "as_of": "2026-08-22"},
            {"slug": "core", "kind": "logistics", "basis": "press", "source_id": "s1", "as_of": "2026-08-22"},
            {"slug": "core", "kind": "wizard", "basis": "doc", "source_id": "s1", "as_of": "2026-08-22"}]
        graph = build_graph(entities, copy.deepcopy(PEOPLE))
        got = sorted((e["type"], e["label"], e["confidence"]) for e in graph["edges"] if e["type"] in ("banks_with", "ships_via", "acquiring_via"))
        # a malformed kind is dropped by the builder (check_registry reports it), never guessed into an edge
        self.assertEqual([("banks_with", "bank", "doc"), ("ships_via", "logistics", "press")], got)
        self.assertEqual([], validate_graph(graph, entities, PEOPLE, SOURCES))
        bad = copy.deepcopy(graph)
        next(e for e in bad["edges"] if e["type"] == "banks_with")["confidence"] = "rumour"
        self.assertTrue(any("banks_with" in m for m in validate_graph(bad, entities, PEOPLE, SOURCES)))

    def test_product_record_replaces_version_leaves_and_draws_storefronts(self):
        entities = copy.deepcopy(ENTITIES)
        entities[0]["products"] = [{"name_ru": "«Х» в.1", "source_id": "s1"}, {"name_ru": "«Х» в.2", "source_id": "s1"},
                                   {"name_ru": "«Другой»", "source_id": "s1"}]
        products = [{"slug": "x", "name_ru": "«Х»", "category": "detector", "maker": "core",
                     "versions": [{"slug": "x1", "name_ru": "«Х» в.1", "source_id": "s1"},
                                  {"slug": "x2", "name_ru": "«Х» в.2", "source_id": "s1"}],
                     "listings": [
                         {"channel": "WB", "seller": {"entity": "ordinary", "storefront": "Shop A"}, "basis": "doc",
                          "source_id": "s1", "as_of": "2026-01-01"},
                         {"channel": "WB", "seller": {"entity": "ordinary", "storefront": "Shop A"}, "basis": "doc",
                          "source_id": "s1", "as_of": "2026-03-01"},
                         {"channel": "Ozon", "seller": {"entity": None, "storefront": "Dealer B"}, "basis": "doc",
                          "source_id": "s1", "as_of": "2026-02-01"}]}]
        graph = build_graph(entities, copy.deepcopy(PEOPLE), None, None, products)
        labels = sorted(n["label"] for n in graph["nodes"] if n["kind"] == "product")
        # the two covered version leaves are gone; the record and the uncovered product remain
        self.assertEqual(["«Другой»", "«Х»"], labels)
        self.assertEqual(2, next(n["product_count"] for n in graph["nodes"] if n["id"] == "core"))
        store = {n["label"] for n in graph["nodes"] if n["kind"] == "storefront"}
        self.assertEqual({"Shop A", "Dealer B"}, store)
        lists = [e for e in graph["edges"] if e["type"] == "lists"]
        operated = [e for e in graph["edges"] if e["type"] == "operated_by"]
        # one lists edge per storefront and product (the latest listing), one operated_by only for a named entity
        self.assertEqual(2, len(lists))
        self.assertEqual(["2026-03-01"], sorted(e["as_of"] for e in lists if e["label"] == "WB"))
        self.assertEqual([("ordinary", "doc")], [(e["target"], e["confidence"]) for e in operated])
        self.assertEqual([], validate_graph(graph, entities, PEOPLE, SOURCES))
        bad = copy.deepcopy(graph)
        next(n for n in bad["nodes"] if n["id"] == "core")["product_count"] = 9
        self.assertTrue(any("product_count" in m for m in validate_graph(bad, entities, PEOPLE, SOURCES)))

    def test_candidate_identities_never_become_edges_or_nodes(self):
        entities = copy.deepcopy(ENTITIES)
        before = build_graph(copy.deepcopy(ENTITIES), copy.deepcopy(PEOPLE))
        entities[1]["candidate_identities"] = [{"name_ru": "ООО «Тезка»", "inn": "5445029638", "status": "unverified",
                                                "as_of": "2026-10-01", "source_id": "s1"}]
        after = build_graph(entities, copy.deepcopy(PEOPLE))
        self.assertEqual(before["edges"], after["edges"])
        self.assertEqual(len(before["nodes"]), len(after["nodes"]))

    def test_unlinked_sells_for_target_is_dropped_not_crashing(self):
        entities = copy.deepcopy(ENTITIES)
        entities[1]["sells_for"] = [{"slug": "does-not-exist", "channel": "Ozon", "basis": "doc"}]
        graph = build_graph(entities, copy.deepcopy(PEOPLE))
        self.assertFalse(any(e["type"] == "sells_for" for e in graph["edges"]))

    def test_programs_events_groups_become_nodes_and_graded_edges(self):
        entities = copy.deepcopy(ENTITIES)
        entities[1]["memberships"] = [{"program": "res", "role": "resident", "basis": "doc", "source_id": "s1", "as_of": "2026-01-02"}]
        entities[1]["participations"] = [{"event": "ev-1", "role": "exhibitor", "basis": "doc", "source_id": "s1", "as_of": "2026-01-02"}]
        programs = [
            {"slug": "res", "kind": "program", "subtype": "residency", "name_ru": "Residency",
             "operators": [{"slug": "core", "basis": "doc", "source_id": "s1"}]},
            {"slug": "ev", "kind": "event", "subtype": "event_series", "name_ru": "Series",
             "organisers": [{"slug": "core", "role": "co-organiser", "basis": "doc", "source_id": "s1"}]},
            {"slug": "ev-1", "kind": "event", "subtype": "event_edition", "name_ru": "Edition", "parent": "ev"},
            {"slug": "grp", "kind": "group", "subtype": "brand_cluster", "name_ru": "Group",
             "members": [{"slug": "ordinary", "role": "member", "basis": "inferred"}]},
        ]
        graph = build_graph(entities, copy.deepcopy(PEOPLE), None, programs)
        got = sorted((e["type"], e["source"], e["target"], e["confidence"]) for e in graph["edges"]
                     if e["type"] in {"operates", "organises", "resident_of", "participated_in", "part_of", "member_of"})
        self.assertEqual([("member_of", "ordinary", "group::grp", "inferred"),
                          ("operates", "core", "program::res", "doc"),
                          ("organises", "core", "event::ev", "doc"),
                          ("part_of", "event::ev-1", "event::ev", None),
                          ("participated_in", "ordinary", "event::ev-1", "doc"),
                          ("resident_of", "ordinary", "program::res", "doc")], got)
        self.assertEqual([], validate_graph(graph, entities, PEOPLE, SOURCES))

    def test_program_edges_reject_wrong_endpoints_and_missing_basis(self):
        entities = copy.deepcopy(ENTITIES)
        programs = [{"slug": "res", "kind": "program", "subtype": "residency", "name_ru": "Residency",
                     "operators": [{"slug": "core", "basis": "doc", "source_id": "s1"}]}]
        graph = build_graph(entities, copy.deepcopy(PEOPLE), None, programs)
        bad = copy.deepcopy(graph)
        edge = next(e for e in bad["edges"] if e["type"] == "operates")
        edge["source"], edge["target"] = edge["target"], edge["source"]
        self.assertTrue(any("invalid" in m and "operates" in m for m in validate_graph(bad, entities, PEOPLE, SOURCES)))
        bad = copy.deepcopy(graph)
        next(e for e in bad["edges"] if e["type"] == "operates")["confidence"] = None
        self.assertTrue(any("confidence" in m for m in validate_graph(bad, entities, PEOPLE, SOURCES)))
        bad = copy.deepcopy(graph)
        next(n for n in bad["nodes"] if n["kind"] == "program")["subtype"] = "event_series"
        self.assertTrue(any("subtype" in m for m in validate_graph(bad, entities, PEOPLE, SOURCES)))

    def test_quality_report_is_deterministic(self):
        first = report(self.graph, self.views, ENTITIES, PEOPLE)
        second = report(self.graph, self.views, ENTITIES, PEOPLE)
        self.assertEqual(first, second)
        self.assertIn("Live-registry parity: 2/2 entities; 1/1 people", first)


    def test_every_edge_is_graded_from_its_document(self):
        """B1: a register extract grades doc, a company's own post rep, no source open; a confidence wins."""
        from graph_contract import source_grade
        self.assertEqual(source_grade({"path": "data/sources/EGRUL_7802942873_20260907_x.pdf"}), "doc")
        self.assertEqual(source_grade({"path": "data/sources/ul-1247700190430-20260815.pdf"}), "doc")
        self.assertEqual(source_grade({"path": "data/sources/A40-211563-2022_20221109_Opredelenie.pdf"}), "doc")
        # a Telegram post the content scan typed "court" is still the party's own word
        self.assertEqual(source_grade({"path": "data/sources/TGPOST_20250101_x-1.txt", "type": "court"}), "rep")
        self.assertEqual(source_grade({"path": "data/sources/PRESS_20250101_x.html"}), "rep")
        self.assertEqual(source_grade(None), "open")
        for edge in self.graph["edges"]:
            self.assertIn(edge["grade"], {"doc", "rep", "open"})
            if not edge["source_id"] and not edge["confidence"]:
                self.assertEqual(edge["grade"], "open")


if __name__ == "__main__":
    unittest.main()
