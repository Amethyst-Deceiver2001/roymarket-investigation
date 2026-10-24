#!/usr/bin/env python3
"""Fixtures for scripts/morning_brief.py: the five parts are always there, closed hand items drop out, mechanical
commits are not news, and the first task named for a record is the flag that ranks it.

No pytest dependency - plain assertions, run directly:
    python3 tests/test_morning_brief.py
"""
import json
import sys
import tempfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import morning_brief as mb  # noqa: E402


def main():
    with tempfile.TemporaryDirectory() as tmp:
        items = Path(tmp) / "brief_items.json"
        items.write_text(json.dumps({"items": [
            {"id": "t1", "kind": "ready", "since": "2026-10-20", "status": "open", "text": "Page A checked"},
            {"id": "t2", "kind": "decision", "since": "2026-10-20", "status": "closed", "text": "Old call", "note": "done"},
            {"id": "t3", "kind": "stuck", "since": "2026-10-24", "status": "open", "text": "Video", "why": "no map"},
        ]}), encoding="utf-8")
        mb.ITEMS = items
        mb.SOURCES = Path(tmp) / "no-sources"        # a fresh clone: no archive, no media folder
        mb.TRIAGE = mb.SOURCES / "_media_triage"
        text = mb.build(date(2026, 10, 24), date(2026, 10, 21))

    for part in ("## New since 21.10.2026", "## Ready", "## Stuck", "## Waiting on you", "## Next in the record",
                 "## Machine"):
        assert part in text, part
    assert "Page A checked · open 4 d" in text
    assert "Old call" not in text, "a closed item must drop out"
    assert "Video · new today. Why: no map" in text
    assert "In progress, pictures:" not in text, "no media folder, no media line"

    # mechanical commits are filtered by subject
    assert all(s.startswith(mb.AUTO_COMMIT) is False for _, s in mb.commits_since(date(2026, 10, 21)))

    # the reason a record ranks is named before a stale screen
    flags = [{"code": "screen_stale", "text": "stale"}, {"code": "sanction_unread", "text": "read the list"}]
    first = sorted(flags, key=lambda f: mb.FIRST_TASK.index(f["code"]) if f["code"] in mb.FIRST_TASK else 99)[0]
    assert first["text"] == "read the list"
    print("test_morning_brief: ok")


if __name__ == "__main__":
    main()
