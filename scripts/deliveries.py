"""The one record of reported handovers: data/registry/deliveries.json (merged 24.10.2026, user).

Before the merge there were two lists with no post in common: handovers.json (every handover post, one row per
recipient, no product named) and products.json deliveries[] (only «Булат» and «Капюшон», richer fields). Both are
now one list of events. An event is one post's report of one handover to one recipient; several channels reporting
the same handover would be one event with `other_source_ids`.

Event fields (all in the file; none is optional except where marked):
    id                     stable name, never renamed: media records point at it ('bulat-d05', 'h0025')
    date, donor, co_donors[], donor_people[], carrier, named_deliverer
    recipient              the wording of the post, Russian; recipient_en its gloss; recipient_kind "civilian" where the post names civilian recipients (absent: military); recipient_unit_slug a unit record or null;
                           direction (a front direction the post names) or null
    items[]                {product: product slug|null, version: version slug|null, item: text|null, note|null, id?}
                           a product slug here is what makes the event show on that product's chain view; an item `id`
                           is the name its product's view and its media records use for this handover (a post that
                           reports two products to one recipient is one event with two items, and the second item
                           keeps the id its own row had before they were combined)
    asserted_by, credibility, register ('institutional_announcement' | 'field_video')
    source_channel ('@name'), post_id, source_id (null until the post is catalogued), other_source_ids[]
    text_ru, context_en, cost_rub_raw, media[], note

Readers that want a product's handovers in the old shape call `load_products()`: each product record then carries
`deliveries`, built from the events whose items name it, with the field names the pages already use.
"""
import json
from pathlib import Path

REG = Path(__file__).resolve().parent.parent / "data" / "registry"
PATH = REG / "deliveries.json"

# the fields a product's chain view has always read from a delivery, copied from the event as they are
SHARED = ("id", "date", "donor", "co_donors", "carrier", "recipient", "recipient_en", "recipient_kind", "source_channel", "post_id",
          "asserted_by", "credibility", "source_id", "other_source_ids", "note")


def load(path: Path = PATH) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def for_product(events: list[dict], slug: str) -> list[dict]:
    """The events that name this product, one dict each in the shape products.json deliveries[] used."""
    out = []
    for e in events:
        for it in e.get("items") or []:
            if it.get("product") == slug:
                d = {k: e[k] for k in SHARED if k in e}
                if it.get("id"):
                    d["id"] = it["id"]
                d["version"] = it.get("version")
                d["item"] = it.get("item")
                out.append(d)
    # ids were given in the order the rows were added, which the pages' footnotes and printouts follow; the
    # events file itself is sorted by date
    return sorted(out, key=lambda d: d["id"])


def attach(products: list[dict], events: list[dict] | None = None) -> list[dict]:
    events = load() if events is None else events
    for p in products:
        p["deliveries"] = for_product(events, p["slug"])
    return products


def load_products(path: Path | None = None) -> list[dict]:
    """products.json with `deliveries` attached from deliveries.json (the old shape, built on load)."""
    path = path or REG / "products.json"
    raw = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    return attach(raw if isinstance(raw, list) else raw.get("products", []))
