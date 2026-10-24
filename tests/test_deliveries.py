#!/usr/bin/env python3
"""Fixtures for scripts/deliveries.py and the merged data/registry/deliveries.json (24.10.2026).

The merge of handovers.json and products deliveries[] must keep every old reader's view: a product's deliveries
come back in the shape the pages read, ordered by id (the order the rows were added), one dict per product item.

No pytest dependency - plain assertions, run directly:
    python3 tests/test_deliveries.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import deliveries as dl  # noqa: E402

EVENTS = [
    {"id": "h0002", "date": "2025-02-01", "donor": "d", "co_donors": [], "carrier": "not stated", "recipient": "R2",
     "source_channel": "@c", "post_id": 2, "asserted_by": "self", "credibility": "single", "source_id": None,
     "items": [{"product": None, "version": None, "item": None, "note": "x"}], "text_ru": "t"},
    {"id": "p-d02", "date": "2025-01-05", "donor": "d", "co_donors": ["E"], "carrier": "C", "recipient": "R1",
     "recipient_en": "r1", "source_channel": "@c", "post_id": 1, "asserted_by": "self", "credibility": "single",
     "source_id": "s1", "note": "n", "items": [{"product": "p", "version": "p-v1", "item": "I", "note": None}]},
    {"id": "p-d01", "date": "2025-03-01", "donor": "d", "co_donors": [], "carrier": "C", "recipient": "R3",
     "source_channel": "@c", "post_id": 3, "asserted_by": "self", "credibility": "single", "source_id": "s2",
     "items": [{"product": "p", "version": None, "item": "J", "note": None},
               {"product": "q", "version": None, "item": "K", "note": None, "id": "q-d07"}]},
]

# a product sees only the events that name it, in id order, with the old field names and no event-only fields
got = dl.for_product(EVENTS, "p")
assert [d["id"] for d in got] == ["p-d01", "p-d02"], "ordered by id, not by date"
assert got[1] == {"id": "p-d02", "date": "2025-01-05", "donor": "d", "co_donors": ["E"], "carrier": "C", "recipient": "R1",
                  "recipient_en": "r1", "source_channel": "@c", "post_id": 1, "asserted_by": "self", "credibility": "single",
                  "source_id": "s1", "note": "n", "version": "p-v1", "item": "I"}
assert "text_ru" not in dl.for_product(EVENTS, "p")[0] and "items" not in got[0]
# one event naming two products shows on both, each with its own item
assert [d["item"] for d in dl.for_product(EVENTS, "q")] == ["K"] and dl.for_product(EVENTS, "nobody") == []
# a second product's item keeps the id its own row had, so its view and its media records are unchanged
assert [d["id"] for d in dl.for_product(EVENTS, "q")] == ["q-d07"] and [d["id"] for d in dl.for_product(EVENTS, "p")][0] == "p-d01"
prods = dl.attach([{"slug": "p"}, {"slug": "q"}], EVENTS)
assert [len(p["deliveries"]) for p in prods] == [2, 1]

# the real file: one record of every reported handover (24.10.2026: 65 events; 26 product items on 23 of them)
real = dl.load()
ids = [e["id"] for e in real]
assert len(ids) == len(set(ids)) >= 65
assert [e["date"] for e in real] == sorted(e["date"] for e in real), "the file is kept in date order"
assert all(e["items"] and e["recipient"] and e["donor"] for e in real)
named = [e for e in real if any(i["product"] for i in e["items"])]
assert len(named) >= 23 and all(e["source_id"] for e in named), "a product event rests on a catalogued source"
assert sum(1 for e in named for i in e["items"] if i["product"]) >= 26
two = [e for e in named if len({i["product"] for i in e["items"]}) == 2]
assert len(two) == 3 and all(e["items"][1].get("id") for e in two), "posts 382, 397, 448 carry both products"
prods = {p["slug"]: p for p in dl.load_products()}
assert len(prods["bulat"]["deliveries"]) >= 18 and len(prods["kapyushon"]["deliveries"]) >= 8
print("test_deliveries: ok")
