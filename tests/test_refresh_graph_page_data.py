#!/usr/bin/env python3
"""Focused tests for refresh_graph_page_data.py's in-place data substitution.

Replaces tests/test_graph_explorer.py (deleted 2026-09-21 along with the
build_graph_explorer.py module it tested -- that module rendered a
different, superseded page design and had drifted out of sync with the
live docs/relationship-graph.html since 2026-09-10; see the removal
commit and refresh_graph_page_data.py's own docstring).
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

from refresh_graph_page_data import BLOCK_RE, script_json  # noqa: E402


FAKE_PAGE = """<!doctype html><html><body>
<script id="graph-data" type="application/json">{"node_count": 1, "nodes": []}</script>
</body></html>"""


class RefreshGraphPageDataTests(unittest.TestCase):
    def test_block_re_finds_and_replaces_the_graph_data_script(self):
        m = BLOCK_RE.search(FAKE_PAGE)
        self.assertIsNotNone(m)
        old = json.loads(m.group(2))
        self.assertEqual(1, old["node_count"])

        new_graph = {"node_count": 2, "nodes": [{"id": "a"}, {"id": "b"}]}
        out = FAKE_PAGE[: m.start()] + m.group(1) + script_json(new_graph) + m.group(3) + FAKE_PAGE[m.end():]

        m2 = BLOCK_RE.search(out)
        self.assertIsNotNone(m2)
        self.assertEqual(2, json.loads(m2.group(2))["node_count"])
        # exactly one graph-data block remains, not a duplicate
        self.assertEqual(1, len(BLOCK_RE.findall(out)))

    def test_script_json_escapes_closing_script_tag(self):
        # a label/note containing a literal </script> must not be able to
        # break out of the <script type="application/json"> element it's
        # embedded in.
        payload = {"label": "a </script><script>alert(1)</script> tag"}
        out = script_json(payload)
        self.assertNotIn("</script>", out)
        self.assertIn("\\u003c/script\\u003e", out)
        # round-trips back to the original value once un-escaped for parsing
        self.assertEqual(payload, json.loads(out.replace("\\u003c", "<").replace("\\u003e", ">").replace("\\u0026", "&")))

    def test_script_json_escapes_ampersand(self):
        out = script_json({"label": "Tom & Jerry"})
        self.assertNotIn("&", out)
        self.assertIn("\\u0026", out)


if __name__ == "__main__":
    unittest.main()
