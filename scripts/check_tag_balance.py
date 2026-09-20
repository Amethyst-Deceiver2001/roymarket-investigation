#!/usr/bin/env python3
"""Run after any hand-edited HTML page is changed, before publishing.

Scoped to the authored content region, not the whole file — an unscoped
check false-positives on tag-like string literals inside embedded runtime
JS (seen at the top/bottom of docs/index.html). Scoping strategy, in order
of preference:
  1. <div class="wrap"> ... </body>  (docs/index.html's own convention)
  2. <body ...> ... </body>          (a generic fallback for any other page)
  3. the whole file, if neither marker pair is found — printed as a loud
     note, since this reintroduces the JS-literal false-positive risk the
     scoping exists to avoid; still better than refusing to check a file
     that doesn't happen to use this project's specific convention.

Accepts zero or more file paths/glob patterns; defaults to docs/index.html
(the only page that has existed until Phase 4 adds more) when none are
given. Every generated page from a future scripts/build_site.py should be
checked the same way — pass a glob (e.g. "docs/companies/*.html") rather
than hardcoding each filename.
"""
import glob
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_PATHS = [REPO / "docs" / "dossier.html"]

TAGS = [
    "section", "table", "div", "blockquote", "tr", "td", "ul", "li", "ol",
    "a", "p", "strong", "h3", "em", "code", "cite", "figure", "figcaption",
]


def scope_content(s: str) -> tuple[str, str]:
    """Return (scoped_content, strategy_label)."""
    try:
        start = s.index('<div class="wrap">')
        end = s.index("</body>")
        return s[start:end], '<div class="wrap"> ... </body>'
    except ValueError:
        pass
    try:
        start = s.index("<body")
        start = s.index(">", start) + 1
        end = s.index("</body>")
        return s[start:end], "<body> ... </body>"
    except ValueError:
        pass
    return s, "WHOLE FILE (no wrap/body markers found — JS-literal false positives possible)"


def check_file(path: Path) -> bool:
    """Return True if the file's tag counts balance."""
    s = path.read_text(encoding="utf-8")
    seg, strategy = scope_content(s)

    print(f"\n=== {path.relative_to(REPO) if path.is_relative_to(REPO) else path} "
          f"(scope: {strategy}) ===")

    bad = False
    for t in TAGS:
        opens = len(re.findall(rf"<{t}[ >]", seg))
        closes = len(re.findall(rf"</{t}>", seg))
        status = "OK" if opens == closes else "MISMATCH"
        if opens != closes:
            bad = True
        print(f"{t:12s} {opens:4d} {closes:4d} {status}")

    return not bad


def resolve_paths(args: list[str]) -> list[Path]:
    if not args:
        return DEFAULT_PATHS
    resolved: list[Path] = []
    for arg in args:
        matches = glob.glob(arg, recursive=True)
        if matches:
            resolved.extend(Path(m) for m in sorted(matches))
        else:
            resolved.append(Path(arg))
    return resolved


def main() -> int:
    paths = resolve_paths(sys.argv[1:])
    missing = [p for p in paths if not p.exists()]
    for p in missing:
        print(f"error: {p} not found", file=sys.stderr)
    paths = [p for p in paths if p.exists()]
    if not paths:
        return 1

    results = {p: check_file(p) for p in paths}

    print()
    n_ok = sum(results.values())
    for p, ok in results.items():
        print(f"{'OK ' if ok else 'FIX'}  {p}")
    print(f"\n{n_ok}/{len(results)} file(s) OK")

    return 1 if (not all(results.values()) or missing) else 0


if __name__ == "__main__":
    raise SystemExit(main())
