#!/usr/bin/env python3
"""Run after every docs/index.html edit, before publishing.

Scoped to the authored content region (<div class="wrap"> ... </body>) —
the unscoped full-file version false-positives on tag-like string literals
inside the embedded runtime JS at the top/bottom of the file.
"""
import re
import sys
from pathlib import Path

PATH = Path(__file__).resolve().parent.parent / "docs" / "index.html"
TAGS = [
    "section", "table", "div", "blockquote", "tr", "td", "ul", "li", "ol",
    "a", "p", "strong", "h3", "em", "code", "cite", "figure", "figcaption",
]


def main() -> int:
    s = PATH.read_text(encoding="utf-8")
    try:
        seg = s[s.index('<div class="wrap">'):s.index("</body>")]
    except ValueError:
        sys.exit("Couldn't find <div class=\"wrap\"> ... </body> markers — check the file structure.")

    bad = False
    for t in TAGS:
        opens = len(re.findall(rf"<{t}[ >]", seg))
        closes = len(re.findall(rf"</{t}>", seg))
        status = "OK" if opens == closes else "MISMATCH"
        if opens != closes:
            bad = True
        print(f"{t:12s} {opens:4d} {closes:4d} {status}")

    print("ALL OK" if not bad else "FIX NEEDED")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
