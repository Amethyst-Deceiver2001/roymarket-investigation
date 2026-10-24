#!/usr/bin/env python3
"""One-off (24.10.2026): merge handovers.json and products.json deliveries[] into data/registry/deliveries.json.

Kept for the record; run once. It refuses to write unless the merged file reproduces every product delivery exactly
as the old products.json held it (the compatibility view in scripts/deliveries.py) and every handover field.
    python3 scripts/archive/migrate_deliveries_20261024.py --dry-run
    python3 scripts/archive/migrate_deliveries_20261024.py
"""
import argparse
import copy
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import deliveries as dl  # noqa: E402

REG = REPO / "data" / "registry"


def dump(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    products = json.loads((REG / "products.json").read_text(encoding="utf-8"))
    handovers = json.loads((REG / "handovers.json").read_text(encoding="utf-8"))
    old_view = {p["slug"]: copy.deepcopy(p.get("deliveries") or []) for p in products}

    events = []
    for p in products:
        for d in p.get("deliveries") or []:
            e = {k: v for k, v in d.items() if k not in ("version", "item")}
            e["items"] = [{"product": p["slug"], "version": d["version"], "item": d.get("item"), "note": None}]
            events.append(e)
    for h in handovers:
        donors = h["donor_orgs"]
        e = {
            "id": h["id"], "date": h["date"], "donor": donors[0], "co_donors": donors[1:],
            "donor_people": h["donor_people"], "carrier": h["named_deliverer"] or "not stated",
            "named_deliverer": h["named_deliverer"],
            "recipient": h["recipient_raw"], "recipient_unit_slug": h["recipient_unit_slug"],
            "direction": h["location_direction"],
            "items": [{"product": None, "version": None, "item": it.get("item_type") or it.get("product_name_ru"),
                       "note": it.get("note")} for it in h["items"]],
            # the standing default for a donor's or maker's own report (CLAUDE.md, delivery rules)
            "asserted_by": "self", "credibility": "single", "register": h["evidence_register"],
            "source_channel": "@" + h["channel"], "post_id": h["msg_id"], "source_id": h["source_id"],
            "text_ru": h["text_ru"], "context_en": h["context_en"], "cost_rub_raw": h["cost_rub_raw"],
            "media": h["media"], "note": None,
        }
        events.append(e)
    # product events keep their old key order; give every event the same leading keys for a readable file
    lead = ("id", "date", "donor", "co_donors", "donor_people", "carrier", "named_deliverer", "recipient", "recipient_en",
            "recipient_unit_slug", "direction", "items", "asserted_by", "credibility", "register", "source_channel",
            "post_id", "source_id", "other_source_ids", "text_ru", "context_en", "cost_rub_raw", "media", "note")
    events = [{k: e[k] for k in lead if k in e} | {k: v for k, v in e.items() if k not in lead} for e in events]
    events.sort(key=lambda e: (e["date"], e["id"]))
    assert len({e["id"] for e in events}) == len(events), "duplicate event ids"

    # the merged file must give back every product delivery as it was, and every handover field
    rebuilt = {p["slug"]: dl.for_product(events, p["slug"]) for p in products}
    for slug, old in old_view.items():
        key = lambda d: d["id"]  # noqa: E731
        assert sorted(rebuilt[slug], key=key) == sorted(old, key=key), f"{slug}: deliveries differ after the merge"
    for h in handovers:
        e = next(x for x in events if x["id"] == h["id"])
        assert (e["donor"], e["recipient"], e["recipient_unit_slug"], e["date"], e["text_ru"]) == (
            h["donor_orgs"][0], h["recipient_raw"], h["recipient_unit_slug"], h["date"], h["text_ru"]), h["id"]
    print(f"{len(events)} events: {sum(1 for e in events if e['items'][0]['product'])} naming a product, "
          f"{sum(1 for e in events if not e['items'][0]['product'])} with no product named")
    if a.dry_run:
        return
    dump(REG / "deliveries.json", events)
    for p in products:
        p.pop("deliveries", None)
    dump(REG / "products.json", products)
    print("wrote deliveries.json; removed deliveries[] from products.json; delete handovers.json with git rm")


if __name__ == "__main__":
    main()
