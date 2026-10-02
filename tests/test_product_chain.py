#!/usr/bin/env python3
"""Regression fixtures for scripts/product_chain.py and the products.json record for «Булат».

    python3 tests/test_product_chain.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import product_chain as P  # noqa: E402

pr = {"slug": "x", "name_ru": "«Х»", "category": "detector", "maker": "m",
      "versions": [{"slug": "x1", "name_ru": "«Х» 1", "firmware": None, "source_id": "s1"}],
      "listings": [{"channel": "WB", "status": "listed", "as_of": "2026-01-01", "version": None, "source_id": None,
                    "basis": "doc", "asserted_by": "platform",
                    "seller": {"entity": None, "storefront": "Shop", "identity": "unresolved"}}],
      "deliveries": []}
text = "\n".join(P.chain_lines(pr, {"m": "ООО «М»"}))
# a listing with no source says so, an empty delivery list says none recorded, a null firmware says n/a
assert "NO SOURCE (placeholder)" in text and "none recorded" in text and "fw n/a" in text
assert "version not recorded" in text and "no registry entity" in text
dpr = dict(pr, deliveries=[{"date": "2026-02-02", "version": "x1", "qty": 3, "donor": "A", "carrier": "B", "recipient": "C",
                            "asserted_by": "self", "credibility": "single", "source_channel": "ch", "post_id": 7, "source_id": "s2"}])
assert "2026-02-02 x1 x3 A -> B -> C" in "\n".join(P.chain_lines(dpr, {}))
nver = dict(dpr, deliveries=[dict(dpr["deliveries"][0], version=None, co_donors=["E"], other_source_ids=["s3"])])
assert "version not stated x3 A+E" in "\n".join(P.chain_lines(nver, {})) and "[s2,s3]" in "\n".join(P.chain_lines(nver, {}))

# the real record: every listing without a source is one of the two WB brand-store listings
real = json.loads((ROOT / "data/registry/products.json").read_text(encoding="utf-8"))
bulat = next(p for p in real if p["slug"] == "bulat")
assert [l["id"] for l in bulat["listings"] if l["source_id"] is None] == ["bulat-wb-brand-v3", "bulat-wb-brand-v4"]
assert len(bulat["deliveries"]) == 17 and all(d["donor"] == "fond-nasha-pravda" for d in bulat["deliveries"])
assert all(d["credibility"] == "single" and d["version"] is None for d in bulat["deliveries"])
print("product_chain: all checks passed")
