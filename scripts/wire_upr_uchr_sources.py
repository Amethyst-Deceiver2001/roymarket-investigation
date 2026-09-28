#!/usr/bin/env python3
"""Stamp source_id onto people.json's other_entities[] entries, using the
FNS_PB_UPR_UCHR_<inn>_<date>_<slug>-raw.json files scripts/screen_upr_uchr.py
archives to data/sources/.

Run AFTER the usual pipeline (inventory_sources.py -> scan_sources.py ->
extract_registry.py) so the new raw files already have real sNNNN ids in
sources.json. This script only edits people.json directly -- it does not
touch corrections_entities.json/corrections_people.json, because
other_entities is a carry-forward field (see CLAUDE.md): a correction can't
set it, the next extract_registry.py run just re-carries whatever is on
people.json at that point.

Matching: a source path FNS_PB_UPR_UCHR_<inn>_<date>_<slug>-raw.json names
its person by <slug> in the filename. For that person, every other_entities[]
entry whose (inn, role) pair also appears in the archived raw JSON's upr/uchr
lists gets source_id set to that file's sNNNN id (only if not already set --
never overwrites an existing, possibly different, source).

Local file processing over data/registry/*.json + data/sources/*.json -- no
network calls, safe to run directly/repeatedly.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PEOPLE = REPO / "data" / "registry" / "people.json"
SOURCES = REPO / "data" / "registry" / "sources.json"

FNAME_RE = re.compile(r"^FNS_PB_UPR_UCHR_(\d+)_(\d{8})_(.+)-raw\.json$")


def main() -> None:
    people = json.loads(PEOPLE.read_text(encoding="utf-8"))
    sources = json.loads(SOURCES.read_text(encoding="utf-8"))
    src_list = sources["sources"] if isinstance(sources, dict) else sources

    by_slug = {p["slug"]: p for p in people}

    path_to_id = {}
    for s in src_list:
        path = s.get("path", "")
        fname = Path(path).name
        m = FNAME_RE.match(fname)
        if m:
            path_to_id[fname] = (m.group(3), s["id"])  # slug, sNNNN

    changed_people = 0
    changed_entries = 0
    skipped_no_person = []
    for fname, (slug, source_id) in path_to_id.items():
        person = by_slug.get(slug)
        if person is None:
            skipped_no_person.append(fname)
            continue
        raw_path = REPO / "data" / "sources" / fname
        if not raw_path.exists():
            continue
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
        raw_pairs = set()
        if isinstance(raw, dict):
            for role_key, role_label in (("upr", "director"), ("uchr", "founder")):
                for row in raw.get(role_key, []):
                    inn = row.get("inn")
                    if inn:
                        raw_pairs.add((inn, role_label))
        elif isinstance(raw, list):
            # earlier hand-captured files (e.g. Бессонов, before this script
            # archived automatically) stored a flat director-only list
            for row in raw:
                inn = row.get("inn")
                if inn:
                    raw_pairs.add((inn, "director"))

        this_person_changed = False
        for oe in person.get("other_entities") or []:
            if oe.get("source_id"):
                continue
            pair = (oe.get("inn"), oe.get("role"))
            if pair in raw_pairs:
                oe["source_id"] = source_id
                changed_entries += 1
                this_person_changed = True
        if this_person_changed:
            changed_people += 1

    PEOPLE.write_text(json.dumps(people, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Wired {changed_entries} other_entities[] entries across {changed_people} people.")
    if skipped_no_person:
        print(f"WARNING: {len(skipped_no_person)} archived file(s) matched no person slug:")
        for f in skipped_no_person:
            print(f"  {f}")


if __name__ == "__main__":
    main()
