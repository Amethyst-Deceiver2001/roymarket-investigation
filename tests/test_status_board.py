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
    assert "python3 scripts/check_registry.py" in q.splitlines(), q
    # After pulls, their text is exported locally for first reading (pull-inbox retired, issue #30).
    assert q.rstrip().endswith("first_reading.py export --local-dir data/sources/_inbox"), q
    # Re-screens are queued per screen, capped, by slug; OpenSanctions within its quota cap.
    for key, cap in sb.SCREEN_CAPS.items():
        line = [l for l in sb.pull_queue(board).splitlines() if l.startswith(sb.SCREEN_COMMANDS[key].split(" --")[0])]
        assert len(line) <= 1, line
        if line:
            slugs = line[0].split("--only ")[1].split(",")
            assert 0 < len(slugs) <= cap and all(s in r for s in slugs), line
    assert sb.SCREEN_CAPS["opensanctions"] * 31 <= 150
    # A never-screened record is due for every screen it lacks.
    never = [f for f in r["ooo-trimiks"]["flags"] if f["code"] == "screen_never"]
    assert all(f.get("due") for f in never), never
    # OpenSanctions goes stale after 90 days (its quota), ГУР after 30.
    rec = {"inn": "1", "opensanctions_screened_at": "2026-08-01", "gur_screened_at": "2026-08-01",
           "aleph_screened_at": "2026-09-30"}
    st = [f for f in sb.Board(TODAY).screen_flags(rec) if f["code"] == "screen_stale"]
    assert len(st) == 1 and st[0]["due"] == ["gur"], st

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

    # A registry that answered "not found" is not asked again for MISS_RETRY_DAYS.
    import json as _json, tempfile as _tf
    orig = sb.MISSES
    with _tf.TemporaryDirectory() as d:
        sb.MISSES = Path(d) / "m.json"
        sb.MISSES.write_text(_json.dumps({"bfo": {"7700000003": "2026-10-01"}}))
        assert "b-never" not in sb.pull_queue(rows, cap=1), "a fresh miss is skipped"
        sb.MISSES.write_text(_json.dumps({"bfo": {"7700000003": "2026-08-01"}}))
        assert "b-never" in sb.pull_queue(rows, cap=1), "an old miss is retried"
    sb.MISSES = orig

    # A second run on the same day takes only what is left of each cap.
    never2 = b.bfo_flags({"inn": "7700000004", "financials": []})
    rows2 = {"generated": "2026-10-02", "rows": [
        {"kind": "entity", "slug": f"c{n}", "inn": f"770000000{n}", "tier": "manufacturer", "flags": never2}
        for n in range(5, 9)]}
    assert sb.pull_queue(rows2, cap=3).count("--inn") == 3
    assert sb.pull_queue(rows2, cap=3, used={"bfo": 2}).count("--inn") == 1, "one slot left"
    q = sb.pull_queue(rows2, cap=3, used={"bfo": 3})
    assert "--inn" not in q and "caps are used up" in q, "cap used: no pull command, and it says why"
    scr = {"generated": "2026-10-02", "rows": [
        {"kind": "person", "slug": f"p{n}", "tier": "x", "flags": [{"kind": "screen", "code": "screen_never",
         "text": "never", "due": ["opensanctions"]}]} for n in range(6)]}
    assert "screen_opensanctions" not in sb.pull_queue(scr, used={"opensanctions": 4}), "screen cap used up"
    assert "screen_opensanctions" in sb.pull_queue(scr, used={"opensanctions": 3}), "one screen left"

    # A sanctions claim counts as read only when an entry is not marked as an unread aggregator match.
    base = {"slug": "t-co", "name_ru": "T", "inn": None, "ogrn": None}
    unread = {"note": "Confirmed via OpenSanctions API match. NOT yet independently read against each underlying primary designation document."}
    official = {"note": "Read in the Official Journal text of the act, entry 42."}
    assert sb.sanction_primary_read({"sanctions": [unread]}) is False
    assert sb.sanction_primary_read({"sanctions": [unread, official]}) is True
    assert "sanction_unread" in codes(b.entity_row(dict(base, sanctions=[unread])))
    assert "sanction_unread" not in codes(b.entity_row(dict(base, sanctions=[unread, official])))
    assert "sanction_unread" not in codes(b.entity_row(dict(base)))
    # A ЦБСТ tie without a document is flagged; a documented one is not.
    assert "tie_not_documented" in codes(b.entity_row(dict(base, cbst_tie={"confidence": "t-open"})))
    assert "tie_not_documented" in codes(b.entity_row(dict(base, cbst_tie={"confidence": "press"})))
    assert "tie_not_documented" not in codes(b.entity_row(dict(base, cbst_tie={"confidence": "t-doc"})))
    # A sanctions entry that says the identity link is unproven flags the person.
    person = {"slug": "t-p", "fio_ru": "T", "sanctions": [{"note": "IDENTITY LINK UNPROVEN (reviewed): ..."}]}
    assert "identity_unproven" in codes(b.person_row(person))
    assert "identity_unproven" not in codes(b.person_row(dict(person, sanctions=[{"note": "Read in full."}])))
    # System checks: declared statuses, the expected ids, and each carries a label and a value.
    sysc = board["system"]
    assert {c["status"] for c in sysc} <= sb.SYSTEM_STATUS, sysc
    ids = {c["id"] for c in sysc}
    assert {"sanctions_primary_read", "weak_ties", "daily_round"} <= ids, ids
    assert all(c["label"] and c["value"] for c in sysc), sysc
    assert "system:" in sb.summary(board)

    # Every flag kind is a declared one.
    assert {f["kind"] for row in board["rows"] for f in row["flags"]} <= set(sb.KINDS)

    # Priority: sanctions evidence to read, then a ЦБСТ-tied organisation no Western list names, then listed, then the
    # rest; within a level nearer ЦБСТ first; a record with no flags last.
    flag = lambda code, kind="review": {"code": code, "kind": kind, "text": code}
    hops, degree = {"a": 1, "b": 1, "c": 3, "d": 1}, {"a": 2, "b": 9, "c": 50, "d": 1}
    tied = {"cbst_tie": {"confidence": "t-doc"}}
    listed = {"cbst_tie": {"confidence": "t-doc"}, "sanctions": [{"regime": ["EU (Ukraine-related)"]}]}
    unproven = {"sanctions": [{"regime": ["EU"], "note": "PLAUSIBLE namesake"}], **tied}
    cases = [({"slug": "a", "kind": "entity", "flags": [flag("sanction_unread")]}, {}),
             ({"slug": "b", "kind": "entity", "flags": [flag("egrul_stale", "stale")]}, tied),
             ({"slug": "c", "kind": "entity", "flags": [flag("egrul_stale", "stale")]}, tied),
             ({"slug": "d", "kind": "entity", "flags": [flag("egrul_stale", "stale")]}, listed),
             ({"slug": "e", "kind": "entity", "flags": [flag("egrul_stale", "stale")]}, unproven),
             ({"slug": "f", "kind": "entity", "flags": []}, tied)]
    for row, rec in cases:
        row["priority"] = sb.priority(row, rec, hops, degree)
    levels = {r["slug"]: r["priority"]["level"] for r, _ in cases}
    assert levels == {"a": 3, "b": 2, "c": 2, "d": 1, "e": 2, "f": 2}, levels   # an unproven listing is no listing
    order = [r["slug"] for r in sorted((r for r, _ in cases), key=sb.priority_key)]
    assert order == ["a", "b", "c", "e", "d", "f"], order   # e is off the graph: after c, which is 3 hops out
    assert all("rank" in r["priority"] for r in board["rows"])
    assert "Next 3 records" in sb.next_actions(board, 3)
    print("ok: status_board fixtures pass")


if __name__ == "__main__":
    main()
