#!/usr/bin/env python3
"""One-off (24.10.2026): combine the three posts that report both products to one recipient into one event each.

Posts 382, 397 and 448 of @nashapravdafond were two rows each (a «Булат» row and a «Капюшон» row). Each pair becomes the
«Булат» event with two items; the «Капюшон» item keeps its old id, so its chain view and its media records are unchanged.
Fields that differed between the two rows take the fuller value (the named carrier over "not stated"; the longer note).
    python3 scripts/archive/combine_double_product_events_20261024.py [--dry-run]
"""
import json
import sys
from pathlib import Path

PATH = Path(__file__).resolve().parent.parent.parent / "data" / "registry" / "deliveries.json"
PAIRS = [("bulat-d17", "kapyushon-d05"), ("bulat-d02", "kapyushon-d06"), ("bulat-d07", "kapyushon-d08")]


def main():
    events = json.loads(PATH.read_text(encoding="utf-8"))
    by = {e["id"]: e for e in events}
    drop = set()
    for a, b in PAIRS:
        x, y = by[a], by[b]
        assert (x["source_channel"], x["post_id"], x["recipient"], x["date"], x["donor"]) == \
               (y["source_channel"], y["post_id"], y["recipient"], y["date"], y["donor"]), (a, b)
        x["items"] = x["items"] + [dict(y["items"][0], id=b)]
        if x["carrier"] == "not stated":
            x["carrier"] = y["carrier"]
        if len(y.get("note") or "") > len(x.get("note") or ""):
            x["note"] = y["note"]
        for k in ("co_donors", "other_source_ids"):
            merged = list(x.get(k) or [])
            for v in y.get(k) or []:
                if v not in merged:
                    merged.append(v)
            if k in x or merged:
                x[k] = merged
        drop.add(b)
    out = [e for e in events if e["id"] not in drop]
    print(f"{len(events)} events -> {len(out)}")
    if "--dry-run" not in sys.argv:
        PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
