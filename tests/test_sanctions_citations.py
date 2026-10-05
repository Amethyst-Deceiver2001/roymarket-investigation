#!/usr/bin/env python3
"""Fixtures for scripts/sanctions_citations.py (plain assertions, run directly).

Synthetic registry and watcher result (a real record stops being OpenSanctions-only once its
official entries are read, so the fixture must not depend on the live registry): a record
whose claims rest only on OpenSanctions must appear with the official entries found and the
unmatched claims listed as look-ups.
"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import sanctions_citations as sc  # noqa: E402

WATCH = {"as_of": "2026-10-02", "lists": {"us": {}, "eu": {}, "uk": {"error": "x"}, "ch": {}},
         "hits": [
             {"list": "us", "slug": "ooo-trimiks", "entry_id": "47713", "identifier": "7802942873",
              "list_names": ["3MX"], "programs": ["RUSSIA-EO14024"], "refs": [], "dates": [], "urls": []},
             {"list": "us", "slug": "ooo-trimiks", "entry_id": "47713", "identifier": "1237800084235",
              "list_names": ["3MX"], "programs": ["RUSSIA-EO14024"], "refs": [], "dates": [], "urls": []},
         ]}


def main():
    tmp = Path(tempfile.mkdtemp())
    (tmp / "entities.json").write_text(json.dumps([{"slug": "ooo-trimiks", "name_ru": "ООО «Тримикс»", "sanctions": [
        {"source_id": "s1", "regime": ["US (OFAC)", "EU (Ukraine-related restrictive measures)",
                                       "Switzerland (SECO)", "Ukraine (Presidential sanctions decree/list)"]}]}]), encoding="utf-8")
    (tmp / "people.json").write_text("[]", encoding="utf-8")
    (tmp / "sources.json").write_text(json.dumps([{"id": "s1", "title": "Sanctions-list entries compiled by OpenSanctions",
                                                    "path": "data/sources/OPENSANCTIONS_x.json"}]), encoding="utf-8")
    sc.REG = tmp
    rows = {r["slug"]: r for r in sc.build(WATCH)}
    t = rows["ooo-trimiks"]
    assert t["os_only"], "Тримикс's sanctions rest only on OpenSanctions"
    assert len(t["entries"]) == 1, "one entry, two identifiers, listed once"
    e = t["entries"][0]
    assert e["identifiers"] == ["1237800084235", "7802942873"], e
    assert e["urls"][0] == "https://sanctionssearch.ofac.treas.gov/Details.aspx?id=47713"
    # Claimed EU and Swiss listings with no hit become look-ups; Ukraine too.
    todo = " ".join(t["todo"])
    assert "EU consolidated list: claimed" in todo and "Swiss SECO list: claimed" in todo, todo
    assert "Ukraine: claimed" in todo
    assert all(r["os_only"] or r["entries"] for r in rows.values())
    print("ok: sanctions_citations fixtures pass")


if __name__ == "__main__":
    main()
