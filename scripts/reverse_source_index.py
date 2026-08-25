#!/usr/bin/env python3
"""Derive the entity<->source and person<->source citation map from
sources.json's own `inns[]` field, instead of hand-maintaining
entities[].sources[] / sources[].entities as duplicated static data.

Phase 3.5 §5 of notes/rebuild_plan.md: `entities[].sources[]` was non-empty
on 1 of 149 entities and `sources[].entities` was empty on all 1392 sources
-- provenance in practice already runs the other way, through
`sources.json[].inns` (every ИНН/ОГРН `scan_sources.py`/`inventory_sources.py`
found inside a document's own text). The plan's own guidance is to build
this map "at build time... rather than duplicating data" -- so this module
is a pure function a future `scripts/build_site.py` (Phase 4) can import
directly, not a migration that writes the map into the JSON files. Run this
file directly for a coverage report; nothing it does is persisted.

A source's `inns[]` is every identifier the extractor found in the document
text, not filtered to "the subject of this document" -- a court filing
naming both parties, or an EGRUL extract's own subject plus its director's
personal ИНН, will legitimately list more than one. build_index() therefore
treats every match as "this source mentions this entity/person", which is
the correct citation-strength claim; it is not a claim that the document is
*exclusively* about that entity.

Local file processing only (reads the registry JSON already on disk) -- no
network calls, safe to run directly/repeatedly.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REG = REPO / "data" / "registry"


def load(name: str):
    path = REG / name
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def build_index(entities: list[dict], people: list[dict], sources: list[dict]):
    """Return (entity_sources, person_sources, source_refs).

    entity_sources: {entity_slug: [source_id, ...]}
    person_sources: {person_slug: [source_id, ...]}
    source_refs:    {source_id: [("entity"|"person", slug), ...]}
    """
    entity_by_inn = {e["inn"]: e["slug"] for e in entities if e.get("inn")}
    person_by_inn = {p["inn_personal"]: p["slug"] for p in people if p.get("inn_personal")}

    entity_sources: dict[str, list[str]] = defaultdict(list)
    person_sources: dict[str, list[str]] = defaultdict(list)
    source_refs: dict[str, list[tuple[str, str]]] = defaultdict(list)

    for s in sources:
        sid = s.get("id")
        for inn in s.get("inns") or []:
            if inn in entity_by_inn:
                slug = entity_by_inn[inn]
                entity_sources[slug].append(sid)
                source_refs[sid].append(("entity", slug))
            if inn in person_by_inn:
                slug = person_by_inn[inn]
                person_sources[slug].append(sid)
                source_refs[sid].append(("person", slug))

    return dict(entity_sources), dict(person_sources), dict(source_refs)


def main() -> int:
    entities = load("entities.json")
    people = load("people.json")
    sources = load("sources.json")

    if not entities or not sources:
        print("error: entities.json/sources.json not found or empty — run "
              "scripts/extract_registry.py first", file=sys.stderr)
        return 1

    entity_sources, person_sources, source_refs = build_index(entities, people, sources)

    entities_with_own_inn = sum(1 for e in entities if e.get("inn"))
    people_with_own_inn = sum(1 for p in people if p.get("inn_personal"))

    print(f"entities with an ИНН on file:  {entities_with_own_inn}")
    print(f"  reachable via this index:    {len(entity_sources)} "
          f"({sum(len(v) for v in entity_sources.values())} source citations total)")
    print(f"people with a personal ИНН:    {people_with_own_inn}")
    print(f"  reachable via this index:    {len(person_sources)} "
          f"({sum(len(v) for v in person_sources.values())} source citations total)")
    print(f"sources with at least one match: {len(source_refs)} / {len(sources)}")

    zero_source_entities = [
        e["name_ru"] for e in entities
        if e.get("inn") and e["slug"] not in entity_sources
    ]
    if zero_source_entities:
        print(f"\n{len(zero_source_entities)} entities have an ИНН on file "
              f"but zero sources mention it (worth a look — either the "
              f"source(s) backing this entity haven't been ИНН-extracted "
              f"yet, or the entity's evidence is prose-only with no "
              f"ИНН-bearing document on file):")
        for name in zero_source_entities[:20]:
            print(f"  - {name}")
        if len(zero_source_entities) > 20:
            print(f"  ... and {len(zero_source_entities) - 20} more")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
