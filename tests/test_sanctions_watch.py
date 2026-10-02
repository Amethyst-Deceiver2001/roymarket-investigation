#!/usr/bin/env python3
"""Fixtures for scripts/sanctions_watch.py.

No pytest dependency - plain assertions, run directly:
    python3 tests/test_sanctions_watch.py

Small synthetic files in the shape of each official list, matched against the
real registry (ООО «Тримикс», ИНН 7802942873 / ОГРН 1237800084235), so the
parser and the comparison are exercised without network access.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import sanctions_watch as sw  # noqa: E402

US = b"""<?xml version="1.0"?>
<sdnList xmlns="https://sanctionslistservice.ofac.treas.gov/api/PublicationPreview/exports/XSD">
 <publshInformation><Publish_Date>09/30/2026</Publish_Date></publshInformation>
 <sdnEntry><uid>99001</uid><lastName>TRIMIKS LLC</lastName><sdnType>Entity</sdnType>
  <programList><program>RUSSIA-EO14024</program></programList>
  <idList><id><idType>Tax ID No.</idType><idNumber>7802942873</idNumber></id>
   <id><idType>Registration Number</idType><idNumber>1237800084235</idNumber></id></idList></sdnEntry>
 <sdnEntry><uid>99002</uid><lastName>UNRELATED LLC</lastName><sdnType>Entity</sdnType>
  <idList><id><idType>Tax ID No.</idType><idNumber>0000000000</idNumber></id></idList></sdnEntry>
</sdnList>"""

EU = b"""<?xml version="1.0"?>
<export xmlns="http://eu.europa.ec/fpi/fsd/export" generationDate="2026-09-30T10:00:00">
 <sanctionEntity logicalId="1" euReferenceNumber="EU.1.1">
  <regulation numberTitle="2026/509 (OJ L)" programme="UKR"/>
  <nameAlias wholeName="Limited Liability Company Trimiks"/>
  <identification identificationTypeCode="tin" number="7802942873"/>
 </sanctionEntity>
 <sanctionEntity logicalId="2" euReferenceNumber="EU.2.2"><nameAlias wholeName="Other"/></sanctionEntity>
</export>"""

CH = b"""<?xml version="1.0"?>
<swiss-sanctions-list date="2026-09-30">
 <target ssid="5001"><sanctions-set-id>12</sanctions-set-id>
  <entity><identity><name><name-part><value>OOO Trimiks</value></name-part></name></identity></entity>
 </target>
</swiss-sanctions-list>"""

BROKEN = b"""<?xml version="1.0"?><somethingElse><row/></somethingElse>"""


def main():
    reg = sw.load_registry()
    assert reg["7802942873"]["slug"] == "ooo-trimiks", "registry identifier map"

    us = sw.scan("us", US, reg)
    assert us["entries"] == 2 and us["publish_date"] == "09/30/2026", us
    # Control digits: Тримикс's real ИНН and ОГРН pass, a one-digit change fails.
    assert sw.ru_id_valid("7802942873") and sw.ru_id_valid("1237800084235")
    assert not sw.ru_id_valid("7802942874")
    # Both identifiers of one entry produce two hits for the same record.
    assert {h["identifier"] for h in us["hits"]} == {"7802942873", "1237800084235"}, us["hits"]
    assert all(h["entry_id"] == "99001" and h["slug"] == "ooo-trimiks" for h in us["hits"])
    assert us["hits"][0]["programs"] == ["RUSSIA-EO14024"]

    eu = sw.scan("eu", EU, reg)
    assert eu["entries"] == 2 and len(eu["hits"]) == 1, eu
    assert eu["hits"][0]["entry_id"] == "EU.1.1"
    assert "2026/509 (OJ L)" in eu["hits"][0]["programs"]

    # A name alone is never a hit: the SECO entry has no identifier.
    ch = sw.scan("ch", CH, reg)
    assert ch["entries"] == 1 and ch["hits"] == [], ch

    # A changed format is an error, never a silent "no hits".
    try:
        sw.scan("uk", BROKEN, reg)
        raise AssertionError("broken format must raise")
    except ValueError:
        pass

    result = {"lists": {"us": {}, "eu": {}, "ch": {}}, "hits": us["hits"] + eu["hits"]}
    first = sw.compare(result, None, reg)
    assert first["new"] == [] and first["removed"] == [], "first run is a baseline"
    # Тримикс's registry entry names SECO, EU and OFAC: no list-vs-registry gap for
    # US and EU, and the SECO claim has no identifier match on the CH fixture.
    assert not [r for r in first["listed_not_in_registry"] if r["slug"] == "ooo-trimiks"]
    assert {"slug": "ooo-trimiks", "list": "ch", "name": reg["7802942873"]["name"]} \
        in first["registry_claims_not_matched"]

    later = sw.compare({"lists": result["lists"], "hits": eu["hits"]}, result, reg)
    assert len(later["removed"]) == 1 and later["removed"][0]["list"] == "us", later["removed"]
    # A list that failed this run (not in lists) reports no removals.
    partial = sw.compare({"lists": {"eu": {}}, "hits": eu["hits"]}, result, reg)
    assert partial["removed"] == [], partial["removed"]

    text = sw.report({"as_of": "2026-10-02", "lists": {
        "us": {"publish_date": "09/30/2026", "entries": 2, "sha256": "ab" * 32},
        "uk": {"error": "HTTPError: 404"}}, "hits": us["hits"]}, first)
    assert "failed: HTTPError: 404" in text and "Registry says listed" in text
    print("ok: sanctions_watch fixtures pass")


if __name__ == "__main__":
    main()
