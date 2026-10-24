#!/usr/bin/env python3
"""Print a product's chain from data/registry/products.json: maker, versions, who lists it where, what is recorded
as delivered. Local, no network. Every listing line says its basis and source, or says it has none.

    python3 scripts/product_chain.py bulat
    python3 scripts/product_chain.py            # list the products on file
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import deliveries as dl  # noqa: E402

REG = Path(__file__).resolve().parent.parent / "data" / "registry"


def chain_lines(pr: dict, names: dict) -> list:
    out = [f"{pr['name_ru']} ({pr['category']}) - maker {names.get(pr['maker'], pr['maker'])} [{pr['maker']}]"]
    out.append("versions: " + "; ".join(f"{v['name_ru']} fw {v['firmware'] or 'n/a'} [{v['source_id']}]" for v in pr.get("versions") or []))
    for a in pr.get("accessories") or []:
        out.append(f"accessory: {a['name_ru']} (pairs with {a['pairs_with']}) [{a['source_id']}]")
    for s in pr.get("shown_at") or []:
        out.append(f"shown at {s['event']} {s['as_of']} [{s['source_id']}]")
    out.append(f"listings ({len(pr.get('listings') or [])}):")
    for l in pr.get("listings") or []:
        who = l["seller"]["entity"] or "no registry entity"
        src = l["source_id"] or "NO SOURCE (placeholder)"
        out.append(f"  {l['as_of']} {l['status']:9} {l['channel']} | seller {l['seller']['storefront']} ({who}) "
                   f"| {l['basis']}, asserted by {l['asserted_by']} | version {l['version'] or 'not recorded'} | {src}")
    deliveries = pr.get("deliveries") or []
    out.append(f"deliveries ({len(deliveries)}):" + ("  none recorded" if not deliveries else ""))
    for d in deliveries:
        donors = "+".join([d["donor"]] + list(d.get("co_donors") or []))
        also = "".join(f",{x}" for x in d.get("other_source_ids") or [])
        out.append(f"  {d['date']} {d.get('version') or 'version not stated'} x{d.get('qty', '?')} {donors} -> {d['carrier']} -> "
                   f"{d['recipient']} | {d['asserted_by']}/{d['credibility']} | {d['source_channel']} {d['post_id']} [{d['source_id']}{also}]")
    for q in pr.get("open_questions") or []:
        out.append(f"open: {q}")
    return out


def main(argv):
    products = dl.load_products(REG / "products.json")
    if not argv:
        print("\n".join(f"{p['slug']}  {p['name_ru']}  (maker {p['maker']})" for p in products))
        return 0
    raw = json.loads((REG / "entities.json").read_text(encoding="utf-8"))
    ents = raw if isinstance(raw, list) else raw.get("entities", raw)
    names = {e["slug"]: e.get("name_ru") for e in ents}
    pr = next((p for p in products if p["slug"] == argv[0]), None)
    if not pr:
        print(f"no product {argv[0]!r}; on file: {[p['slug'] for p in products]}")
        return 2
    print("\n".join(chain_lines(pr, names)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
