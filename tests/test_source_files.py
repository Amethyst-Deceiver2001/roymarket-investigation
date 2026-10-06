#!/usr/bin/env python3
"""Fixtures for scripts/source_files.py: a catalogued source is never overwritten.

No pytest dependency - plain assertions, run directly:
    python3 tests/test_source_files.py
"""
import sys
import tempfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from source_files import write_new  # noqa: E402


def main():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "ZAKUPKI_7700000001_20261003_supplier-search.html"
        assert write_new(p, "first") == p and p.read_text() == "first"
        assert write_new(p, "first") == p, "same bytes: nothing new written"
        p2 = write_new(p, "second")
        assert p2.name == "ZAKUPKI_7700000001_20261003_supplier-search-r2.html"
        assert p.read_text() == "first" and p2.read_text() == "second", "the original is untouched"
        assert write_new(p, "third").name.endswith("-r3.html")
        assert write_new(p, "second") == p2, "an identical earlier version is reused"
        assert write_new(Path(d) / "x.bin", b"\x00\x01").read_bytes() == b"\x00\x01"

    # A second writer claiming the exact same candidate name between this
    # call's `cand.exists()` check and its write (the TOCTOU gap a plain
    # exists()-then-write_bytes() has) must not get overwritten: write_new
    # should detect the race via os.link's exclusivity and fall through to
    # the next -rN name instead. Simulated by racing a write onto the
    # candidate from inside os.link itself, the exact window being tested.
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "race.txt"
        real_link = __import__("os").link
        raced = {"done": False}

        def racing_link(src, dst):
            if not raced["done"]:
                raced["done"] = True
                Path(dst).write_bytes(b"raced-in-first")
            return real_link(src, dst)

        with mock.patch("os.link", side_effect=racing_link):
            result = write_new(p, b"mine")
        assert p.read_bytes() == b"raced-in-first", "the racing writer's bytes must survive untouched"
        assert result.name == "race-r2.txt", f"write_new must retry onto -r2, got {result.name}"
        assert result.read_bytes() == b"mine"

    print("ok: source_files fixtures pass")


if __name__ == "__main__":
    main()
