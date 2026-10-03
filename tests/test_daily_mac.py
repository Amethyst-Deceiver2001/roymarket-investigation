#!/usr/bin/env python3
"""Fixtures for scripts/daily_mac.py: a manual pull leaves only regenerated files dirty, and that must not
block --publish; a hand-held registry file or a script still does.

    python3 tests/test_daily_mac.py
"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import daily_mac as dm  # noqa: E402


def main():
    orig = dm.tracked_changes
    try:
        dm.tracked_changes = lambda: [" M data/registry/_pull_misses.json", " M data/registry/entities.json",
                                      " M data/registry/sources.json", " M data/watch/daily/2026-10-03.md"]
        assert dm.hand_changes() == [], "regenerated outputs of a manual pull do not block the round"
        dm.tracked_changes = lambda: [" M data/registry/entities.json", " M data/registry/corrections_entities.json"]
        assert dm.hand_changes() == [" M data/registry/corrections_entities.json"], "a corrections file blocks"
        dm.tracked_changes = lambda: [" M data/registry/products.json", " M scripts/status_board.py"]
        assert len(dm.hand_changes()) == 2, "a hand-held registry file and a script block"
    finally:
        dm.tracked_changes = orig
    # the board file: first write has nothing to compare with; the second lists what changed since the first
    row = lambda flags: {"slug": "ooo-x", "flags": flags}
    flag = {"code": "bfo_missing", "kind": "pull", "text": "no БФО on file"}
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "status" / "board.json"
        assert "no earlier" in dm.publish_board({"generated": "2026-10-03", "rows": [row([flag])]}, path)
        out = dm.publish_board({"generated": "2026-10-04", "rows": [row([])]}, path)
        assert "1 cleared flag" in out and "0 new flag" in out, out
        assert json.loads(path.read_text(encoding="utf-8"))["generated"] == "2026-10-04"
    assert "extract_registry.py" in dm.INGEST and "scan_sources.py" in dm.INGEST
    print("ok: daily_mac fixtures pass")


if __name__ == "__main__":
    main()
