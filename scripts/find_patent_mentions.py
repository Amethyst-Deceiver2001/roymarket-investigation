#!/usr/bin/env python3
"""One-off sweep of data/sources/ for Russian patent/utility-model/industrial-
design numbers mentioned in already-downloaded primary documents, so they can
be pulled individually via fips_patent_lookup.py rather than relying on the
Rospatent bulk name-matched dump (which turned out to be unproductive for
this dataset -- see the 2026-08-24 patent-sweep rejection note).

Local file processing only over data/sources/ (reuses scan_sources.py's
extract_text()) -- no network calls, safe to run directly/repeatedly.

Patterns matched:
    RU218475U1, RU2723203C1, RU145992S           -- full doc-id with suffix
    патент №218475 / патент RU 218475 / пат. 2723203
    свидетельство ... №218475 (utility model / trademark certs use this too,
        so hits here need eyeballing against context, not auto-trusted)

Usage:
    python3 scripts/find_patent_mentions.py
    python3 scripts/find_patent_mentions.py --out /tmp/patent_mentions.md
"""
import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SOURCES = REPO / "data" / "sources"
sys.path.insert(0, str(REPO / "scripts"))
from scan_sources import extract_text  # noqa: E402

# Full doc-id, e.g. RU218475U1, RU 2723203 C1, RU145992S
RE_FULL_ID = re.compile(r"\bRU\s?(\d{5,8})\s?([UC]\d|S)\b")

# Bare number near a Russian trigger word: патент/полезная модель/промышленный
# образец/изобретение, within ~40 chars before the number.
RE_TRIGGERED = re.compile(
    r"(патент[а-я]*|полезн[а-я]+\s+модел[а-я]+|промышленн[а-я]+\s+образ[а-я]+|"
    r"изобретени[а-я]+)\D{0,40}?№?\s?(\d{5,8})",
    re.IGNORECASE,
)

SKIP_SUFFIXES = {".jpg", ".jpeg", ".png", ".gif", ".mp3", ".mp4", ".xlsx"}


def scan_file(path: Path) -> list[tuple[str, str]]:
    if path.suffix.lower() in SKIP_SUFFIXES:
        return []
    try:
        text = extract_text(path)
    except Exception as ex:
        print(f"  [skip] {path.name}: {ex}", file=sys.stderr)
        return []
    if not text:
        return []

    hits = []
    for m in RE_FULL_ID.finditer(text):
        num, suffix = m.group(1), m.group(2)
        ctx = text[max(0, m.start() - 60):m.end() + 60].replace("\n", " ")
        hits.append((f"RU{num}{suffix}", ctx.strip()))
    for m in RE_TRIGGERED.finditer(text):
        num = m.group(2)
        ctx = text[max(0, m.start() - 30):m.end() + 60].replace("\n", " ")
        hits.append((num, ctx.strip()))
    return hits


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    files = sorted(p for p in SOURCES.iterdir() if p.is_file())
    print(f"Scanning {len(files)} files in {SOURCES} ...", file=sys.stderr)

    all_hits: dict[str, list[tuple[str, str]]] = {}
    for i, path in enumerate(files, 1):
        hits = scan_file(path)
        if hits:
            all_hits[path.name] = hits
        if i % 100 == 0:
            print(f"  {i}/{len(files)} ...", file=sys.stderr)

    lines = [f"# Patent/utility-model/design number mentions in data/sources/\n"]
    total_numbers = set()
    for fname, hits in all_hits.items():
        lines.append(f"## {fname}")
        for num, ctx in hits:
            total_numbers.add(re.sub(r"^RU|[UCS]\d?$", "", num))
            lines.append(f"- **{num}** — ...{ctx}...")
        lines.append("")

    lines.insert(1, f"{len(all_hits)} file(s), {sum(len(h) for h in all_hits.values())} raw mention(s)\n")
    out_text = "\n".join(lines)

    if args.out:
        args.out.write_text(out_text, encoding="utf-8")
        print(f"Wrote {args.out}", file=sys.stderr)
    else:
        print(out_text)


if __name__ == "__main__":
    main()
