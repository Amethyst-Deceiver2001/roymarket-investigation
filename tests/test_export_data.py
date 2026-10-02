#!/usr/bin/env python3
"""Fixtures for scripts/export_data.py, against the real registry.

No pytest dependency - plain assertions, run directly:
    python3 tests/test_export_data.py
Schema validation needs the followthemoney package (and ICU); without it this
checks the export's own invariants only.
"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import export_data as ex  # noqa: E402


def main():
    assert ex.iso("04.09.2023") == "2023-09-04" and ex.iso("2025") == "2025" and ex.iso("Q3 2024") is None

    ftm, entities, people, *_ = ex.build()
    by_id = {d["id"]: d for d in ftm}
    assert len(by_id) == len(ftm), "FtM ids are unique"
    gag = by_id["rm-ooo-gagaring"]["properties"]
    assert gag["innCode"] == ["2312321660"] and gag["ogrnCode"] == ["1232300051235"]
    assert gag["incorporationDate"] == ["2023-09-04"]
    # Every link points at entities in the same file.
    for d in ftm:
        p = d["properties"]
        for a, b in (("owner", "asset"), ("director", "organization"), ("subject", "object"), ("person", "relative")):
            if a in p:
                assert p[a][0] in by_id and p[b][0] in by_id, d
    # Researcher notes and contact details never leave the registry.
    blob = json.dumps(ftm, ensure_ascii=False)
    for field in ('"notes"', '"email"', '"phone"', "_corrected"):
        assert field not in blob, field
    # Out of scope: adjacent-only records the graph leaves out, merged records, reference people.
    ref = [s for s, p in people.items() if p.get("graph_tier") == "reference"]
    assert ref and not any(f"rm-{s}" in by_id for s in ref)
    assert not any(d["schema"] == "Sanction" for d in ftm)

    no_pii, *_ = ex.build(no_pii=True)
    assert not any(k in d["properties"] for d in no_pii for k in ("birthDate", "birthPlace", "innCode")
                   if d["schema"] == "Person")

    with tempfile.TemporaryDirectory() as tmp:
        counts = ex.write(Path(tmp), False)
        assert counts["ftm"] == len(ftm) and counts["entities"] > 100
        assert (Path(tmp) / "csv" / "ties.csv").read_text(encoding="utf-8").startswith("from_id,")
        print(counts["validation"])
    print("ok: export fixtures pass")


if __name__ == "__main__":
    main()
