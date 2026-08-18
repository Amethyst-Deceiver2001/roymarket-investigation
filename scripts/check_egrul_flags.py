#!/usr/bin/env python3
"""Flag known EGRUL access-restriction/disavowal markers in pasted extract
text. Not a DB tool — this runs over EGRUL extracts (pasted into a file, or
piped via stdin) that a session is reading during entity resolution, so the
redaction pattern this investigation keeps finding by hand (Kaysant,
Ушкуйник-СП, Тримикс/3mx, Rustechdron, «АУРИН» — see docs/index.html) gets
caught automatically instead of relying on someone noticing the string.

Usage:
    python3 scripts/check_egrul_flags.py extract.txt
    cat extract.txt | python3 scripts/check_egrul_flags.py
"""
import re
import sys
from pathlib import Path

# (marker regex, what it means)
FLAGS = [
    (r"Ограничение доступа к сведениям", "access to this field is restricted"),
    (r"ОгрДосСв", "access-restriction flag (short form)"),
    (
        r"ПризнНедДанУчр|сведения недостоверны",
        "individual has disavowed being recorded as owner (possible nominee/strawman)",
    ),
    (r"доступ ограничен", "access restricted (founder/director field)"),
]


def scan(text: str) -> list[tuple[str, str, str]]:
    hits = []
    for pattern, meaning in FLAGS:
        for m in re.finditer(pattern, text):
            start = max(0, m.start() - 60)
            end = min(len(text), m.end() + 60)
            context = text[start:end].replace("\n", " ")
            hits.append((m.group(0), meaning, context))
    return hits


def main() -> None:
    if len(sys.argv) > 1:
        text = Path(sys.argv[1]).read_text(encoding="utf-8")
    else:
        text = sys.stdin.read()

    hits = scan(text)
    if not hits:
        print("No EGRUL restriction/disavowal markers found.")
        return

    print(f"{len(hits)} marker(s) found:\n")
    for marker, meaning, context in hits:
        print(f"- \"{marker}\" — {meaning}")
        print(f"  ...{context}...\n")


if __name__ == "__main__":
    main()
