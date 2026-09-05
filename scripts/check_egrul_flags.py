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
    (
        r"Доступ\s+к\s+сведениям[^\n]{0,15}ограничен",
        "access to this field is restricted (director/founder — the most common "
        "EGRUL redaction phrasing, distinct from the shorter 'Ограничение доступа' "
        "form above; catches this even when field content wraps across a line)",
    ),
    (r"ОгрДосСв", "access-restriction flag (short form)"),
    (
        r"ПризнНедДанУчр",
        "individual has disavowed being recorded as owner (possible nominee/strawman)",
    ),
    (
        r"сведения недостоверны",
        "reliability flag on SOME field (address/director/founder — check which "
        "one from context; ФНС uses this generic phrase for any failed "
        "verification, not owner-disavowal specifically — don't assume nominee/"
        "strawman without confirming the flagged field is the founder/owner one",
    ),
    (r"доступ ограничен", "access restricted (founder/director field)"),
    (
        r"сведени\w*\s+о\s+недостоверности",
        "ФНС has entered a недостоверность (unreliable-data) record against the "
        "entity — the phrasing used in the ЕГРЮЛ record-history section ('Внесение "
        "в ЕГРЮЛ сведений о недостоверности сведений о юридическом лице'), which "
        "the shorter 'сведения недостоверны' pattern above does NOT match. Read "
        "the surrounding record entry for its ГРН/date, and check which field the "
        "flag attaches to before drawing any nominee/strawman conclusion",
    ),
    (
        r"предстоящем\s+исключении\s+юридического\s+лица",
        "ФНС has resolved to STRIKE THE ENTITY OFF the register as a "
        "недействующее юридическое лицо — look for the decision number/date and "
        "the «Вестник государственной регистрации» publication issue nearby. On a "
        "sanctioned entity this is a material event (dissolution frequently "
        "precedes re-registration under a fresh name)",
    ),
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
