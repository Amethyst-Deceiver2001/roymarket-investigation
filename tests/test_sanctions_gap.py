#!/usr/bin/env python3
"""Fixtures for scripts/sanctions_gap.py.

No pytest dependency - plain assertions, run directly:
    python3 tests/test_sanctions_gap.py

Runs over the real registry with a synthetic watcher result.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import sanctions_gap as sg  # noqa: E402

WATCH = {"as_of": "2026-10-02",
         "lists": {"eu": {"publish_date": "x", "sha256": "a" * 64},
                   "us": {"publish_date": "x", "sha256": "b" * 64},
                   "uk": {"error": "HTTPError"}},
         "hits": [{"list": "us", "slug": "ooo-trimiks", "entry_id": "99001",
                   "programs": ["RUSSIA-EO14024"]}]}


def main():
    rows, meta = sg.build(None, False)
    assert meta["rows"] >= 50 and all(r["cbst_tie"] for r in rows), "rows are the ЦБСТ-tied set"
    assert all(r["eu"] == "not checked" for r in rows), "no watch data, nothing claimed"

    rows, meta = sg.build(WATCH, False)
    by = {r["slug"]: r for r in rows}
    t = by["ooo-trimiks"]
    assert t["us"].startswith("listed: entry 99001"), t["us"]
    # The registry claims an EU listing for Тримикс; with no ID match it must be
    # flagged for reading, not counted as a gap.
    assert t["eu"] == "no ID match; registry: listed", t["eu"]
    # A list that failed to download is "not checked", never "no ID match".
    assert t["uk"] == "not checked" and t["ch"] == "not checked"
    assert t["western_status"] == "listed"
    # Revenue carries its basis: Атлант Аэро's figure is relayed by the press, not filed.
    if "ooo-atlant-aero" in by:
        assert by["ooo-atlant-aero"]["revenue_basis"] == "press-relayed", by["ooo-atlant-aero"]
    # A non-profit's funds are never shown as revenue.
    if "assotsiatsiya-vzaimopomoshch" in by:
        assert by["assotsiatsiya-vzaimopomoshch"]["revenue_basis"] == "non-profit funds, not revenue"
    # Gaps sort first.
    order = [r["western_status"] for r in rows]
    assert order == sorted(order, key=lambda s: {"no ID match on any": 0,
                                                 "registry claims, no ID match": 1,
                                                 "not checked": 2, "listed": 3}[s])
    # Week-on-week: a list newly matching Тримикс shows as a change, unchanged rows do not.
    import csv, tempfile
    before, _ = sg.build({**WATCH, "hits": []}, False)
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=sg.COLUMNS, extrasaction="ignore")
        w.writeheader()
        w.writerows(before)
    changes = sg.status_changes(rows, Path(f.name))
    assert len(changes) == 1 and "ooo-trimiks" in changes[0] and "US: no ID match" in changes[0], changes
    print("ok: sanctions_gap fixtures pass")


if __name__ == "__main__":
    main()
