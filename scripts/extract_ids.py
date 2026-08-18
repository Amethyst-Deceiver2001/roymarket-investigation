#!/usr/bin/env python3
"""General-purpose entity/product/ИНН/ОГРН scan over arbitrary text — NOT
tied to the Telegram DB. Corporate "About"/"Контакты" pages routinely state
a company's own legal name, ИНН and ОГРН directly; EGRUL extracts, БФО
filing notes, and founding-charter text do too. Any time discovery work
involves reading that kind of text (a WebFetch of a company site, a pasted
EGRUL extract, a founding-document OCR dump), run it through this instead
of eyeballing it by hand — same patterns mine_leads.py uses on Telegram
posts, via the shared scripts/id_patterns.py module.

Usage:
    python3 scripts/extract_ids.py page.txt
    cat page.txt | python3 scripts/extract_ids.py
    curl -s https://example.ru/about | python3 scripts/extract_ids.py
"""
import sys
from pathlib import Path

from id_patterns import (
    RE_ENTITY_BARE, RE_ENTITY_QUOTED, RE_INN, RE_OGRN, RE_QUOTED_NAME,
    RE_ROLE_NAME,
)


def scan(text: str) -> dict[str, list[str]]:
    entities = []
    for m in RE_ENTITY_QUOTED.finditer(text):
        entities.append(f"{m.group(1)} «{m.group(2).strip()}»")
    for m in RE_ENTITY_BARE.finditer(text):
        entities.append(f"{m.group(1)} {m.group(2).strip()}")

    products = [f"«{m.group(1).strip()}»" for m in RE_QUOTED_NAME.finditer(text)]
    people = [m.group(1).strip() for m in RE_ROLE_NAME.finditer(text)]
    inns = [m.group(1) for m in RE_INN.finditer(text)]
    ogrns = [m.group(1) for m in RE_OGRN.finditer(text)]

    return {
        "Entities (АО/ООО/НПЦ/etc.)": sorted(set(entities)),
        "Products/brands (« »)": sorted(set(products)),
        "Named individuals (role + name)": sorted(set(people)),
        "ИНН": sorted(set(inns)),
        "ОГРН": sorted(set(ogrns)),
    }


def main() -> None:
    if len(sys.argv) > 1:
        text = Path(sys.argv[1]).read_text(encoding="utf-8")
    else:
        text = sys.stdin.read()

    results = scan(text)
    any_hits = any(results.values())
    if not any_hits:
        print("No entities, products, people, ИНН or ОГРН found.")
        return

    for section, items in results.items():
        if not items:
            continue
        print(f"## {section}\n")
        for item in items:
            print(f"- {item}")
        print()


if __name__ == "__main__":
    main()
