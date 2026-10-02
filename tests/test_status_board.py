#!/usr/bin/env python3
"""Fixtures for scripts/status_board.py.

No pytest dependency - plain assertions, run directly:
    python3 tests/test_status_board.py

Runs the board over the real registry with a fixed date and synthetic scan
files, so each flag family is exercised without the shared watch folder.
"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import status_board as sb  # noqa: E402

TODAY = date(2026, 10, 2)
STATE = {"channels": {"ru3mx": 742, "tulaovod": None}}
DEVS = {"items": [
    {"id": "t-1", "found": "2026-10-02", "url": "https://t.me/ru3mx/741", "channel": "ru3mx", "post": 741,
     "about": ["bulat", "ooo-trimiks"], "kind": "update", "status": "open", "summary": "в.6 announced"},
    {"id": "t-2", "found": "2026-10-02", "channel": "ru3mx", "post": 1,
     "about": ["ooo-trimiks"], "kind": "new", "status": "recorded", "summary": "closed item"},
    {"id": "t-3", "found": "2026-10-02", "about": [], "kind": "lead", "status": "open", "summary": "lead"},
]}


def rows_by_slug(board):
    return {r["slug"]: r for r in board["rows"]}


def codes(row):
    return [f["code"] for f in row["flags"]]


def main():
    board = sb.Board(TODAY, STATE, DEVS).build()
    r = rows_by_slug(board)

    # An open development flags every record it names; a closed one flags none.
    devs = [f for f in r["ooo-trimiks"]["flags"] if f["code"] == "development"]
    assert [f["dev_id"] for f in devs] == ["t-1"], devs
    assert "development" in codes(r["bulat"])
    assert len(board["unattached_developments"]) == 1

    # A watched channel not yet read by the scan is "behind".
    assert "channel_unread" in codes(r["ovod"]), codes(r["ovod"])
    # A record whose own channels are all off the scan gets one flag naming them.
    unw = [f for f in r["uraldronzavod"]["flags"] if f["code"] == "channel_unwatched"]
    assert len(unw) == 1 and "@urfpv" in unw[0]["text"], unw

    # Stale thresholds: the same registry ages past them a few months later.
    later = sb.Board(date(2027, 1, 15), STATE, DEVS).build()
    lr = rows_by_slug(later)
    assert "egrul_stale" in codes(lr["ooo-trimiks"]), codes(lr["ooo-trimiks"])
    assert "screen_stale" in codes(lr["ooo-trimiks"])

    # Without scan files the scan-dependent flags are skipped and the board says so.
    bare = sb.Board(TODAY).build()
    assert any("developments.json" in n for n in bare["notes"])
    assert not any(f["code"].startswith("channel_") or f["code"] == "development"
                   for row in bare["rows"] for f in row["flags"] if row["kind"] != "channel")

    # The pull queue is capped per registry and ends with the local ingest steps.
    q = sb.pull_queue(board, cap=3)
    bfo_line = [l for l in q.splitlines() if l.startswith("python3 scripts/bfo_pull.py")]
    assert len(bfo_line) == 1 and bfo_line[0].count("--inn") <= 3, q
    assert q.rstrip().endswith("check_registry.py"), q
    # A company whose record says it no longer exists is not asked for new accounts.
    assert not any(f["code"].startswith("bfo") for f in r["ao-borey-absorbed-no-longer-exists"]["flags"])

    # A БФО filing already on disk but not read into financials[] is a reading
    # task, not a pull; one with only older years on disk is still a pull,
    # queued after records never pulled.
    b = sb.Board(TODAY)
    b.bfo_files["7700000001"] = {2024, 2025}
    b.bfo_files["7700000002"] = {2022}
    unread = b.bfo_flags({"inn": "7700000001", "financials": []})
    assert [f["code"] for f in unread] == ["bfo_unread"] and unread[0]["years_on_disk"] == [2024, 2025], unread
    old = b.bfo_flags({"inn": "7700000002", "financials": [{"year": 2022}]})
    assert [f["code"] for f in old] == ["bfo_behind"] and old[0]["on_disk"], old
    never = b.bfo_flags({"inn": "7700000003", "financials": []})
    assert [f["code"] for f in never] == ["bfo_missing"] and not never[0]["on_disk"], never
    rows = {"generated": "2026-10-02", "rows": [
        {"kind": "entity", "slug": s, "inn": i, "tier": "manufacturer", "flags": fl}
        for s, i, fl in (("a-old", "7700000002", old), ("b-never", "7700000003", never))]}
    assert "b-never" in sb.pull_queue(rows, cap=1) and "a-old" not in sb.pull_queue(rows, cap=1)

    # Every flag kind is a declared one.
    assert {f["kind"] for row in board["rows"] for f in row["flags"]} <= set(sb.KINDS)
    print("ok: status_board fixtures pass")


if __name__ == "__main__":
    main()
