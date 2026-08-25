#!/usr/bin/env python3
"""Validate data/registry/*.json before it is trusted or built from.

Local file processing, no network calls — safe to run directly and often.
Run it after any hand-edit of the registry and before any site build.

Checks:
  1. Schema — required keys present, correct types.
  2. ИНН control digits — the Russian ИНН checksum. This is the single most
     useful check here: a mistyped or mis-attributed ИНН almost always fails
     it, which catches transcription errors that no amount of proofreading
     will.
  3. ОГРН control digit — same idea (remainder of the first n-1 digits
     divided by 11, mod 10).
  4. Duplicates — by ИНН, and by normalised name (case-folded, legal-form
     prefix stripped, ё→е), which catches the ООО «X» / «X» / OOO "X"
     variants that plain string comparison misses.
  5. Referential integrity — recursive, not a fixed field list: every
     source_id and every entity/person slug reference found ANYWHERE inside
     an entity or person record must resolve, however deeply nested (a
     trademarks[]/patents[]/images[] entry is checked the same as
     director_history). is_brand_of resolves against ИНН (that field uses
     ИНН, not slug); _merged_into resolves against the same file's own
     slugs. Slugs are unique.
  6. History arrays (director_history, charter_capital_history, financials,
     etc.) — entries are date-ordered. A history entry with a null
     source_id is a placeholder, not evidence — flagged as a warning so it
     surfaces as verification work, not silently.
  7. Coverage report — how much of the registry is still unverified, and
     which high-priority records are missing key fields.

Exit code is non-zero if any ERROR-level check fails. Warnings do not fail
the run; they are the work list.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REG = REPO / "data" / "registry"

ENTITY_REQUIRED = ["slug", "name_ru", "inn", "ogrn", "tier", "_verified"]
PERSON_REQUIRED = ["slug", "fio_ru", "roles", "_verified"]

LEGAL_PREFIX = re.compile(
    r"^(ФГКУ|ФГУП|ФКУ|ГУП|МУП|АНО|ОАО|ПАО|ЗАО|ООО|АО|НПЦ|НПО|НПП|ОПКБ|"
    r"СКБ|КБ|ГК|ИП|Фонд|НТЦ|НИПП|УЦ|ЮФ|ЗПИФ|УК)\s*"
)


def load(name: str):
    path = REG / name
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def inn_valid(inn: str) -> bool:
    """Russian ИНН control-digit check: 10-digit (legal) or 12-digit (person)."""
    if not inn or not inn.isdigit():
        return False
    d = [int(c) for c in inn]
    if len(inn) == 10:
        w = [2, 4, 10, 3, 5, 9, 4, 6, 8]
        return (sum(a * b for a, b in zip(w, d[:9])) % 11) % 10 == d[9]
    if len(inn) == 12:
        w1 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        w2 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        c1 = (sum(a * b for a, b in zip(w1, d[:10])) % 11) % 10
        c2 = (sum(a * b for a, b in zip(w2, d[:11])) % 11) % 10
        return c1 == d[10] and c2 == d[11]
    return False


def ogrn_valid(ogrn: str) -> bool:
    """ОГРН (13) / ОГРНИП (15) control digit."""
    if not ogrn or not ogrn.isdigit() or len(ogrn) not in (13, 15):
        return False
    body, check = ogrn[:-1], int(ogrn[-1])
    divisor = 11 if len(ogrn) == 13 else 13
    return int(body) % divisor % 10 == check


def find_refs(obj, key_names: set[str], path: str = ""):
    """Recursively yield (field_path, value) for every string-valued key in
    key_names found anywhere inside obj, at any nesting depth. Used to catch
    a source_id/slug reference wherever a record happens to carry one,
    instead of only in the handful of fields a human remembered to list."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_path = f"{path}.{k}" if path else k
            if k in key_names and isinstance(v, str) and v:
                yield (new_path, v)
            yield from find_refs(v, key_names, new_path)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            yield from find_refs(item, key_names, f"{path}[{i}]")


def normalise_name(name: str) -> str:
    """Fold an entity name for duplicate detection."""
    s = name.lower().replace("ё", "е")
    s = s.replace("«", "").replace("»", "").replace('"', "")
    s = re.sub(r"\s*\|.*$", "", s)          # drop "| formerly ..." tails
    s = re.split(r"\s/\s", s)[0]            # compound row -> first entity
    s = LEGAL_PREFIX.sub("", s)
    s = re.sub(r"[^0-9a-zа-я]+", "", s)
    return s


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quiet", action="store_true",
                    help="suppress the coverage report, show problems only")
    args = ap.parse_args()

    entities = load("entities.json")
    people = load("people.json")
    sources = load("sources.json")
    quotes = load("quotes.json")

    if entities is None:
        print("error: data/registry/entities.json not found — run "
              "scripts/extract_registry.py first", file=sys.stderr)
        return 1

    errors: list[str] = []
    warnings: list[str] = []

    # --- 1. schema -------------------------------------------------------
    for i, e in enumerate(entities):
        for k in ENTITY_REQUIRED:
            if k not in e:
                errors.append(f"entities[{i}] ({e.get('name_ru', '?')}): missing key '{k}'")
    for i, p in enumerate(people or []):
        for k in PERSON_REQUIRED:
            if k not in p:
                errors.append(f"people[{i}] ({p.get('fio_ru', '?')}): missing key '{k}'")

    # --- 2/3. identifier checksums ---------------------------------------
    for e in entities:
        name = e.get("name_ru", "?")
        inn = e.get("inn")
        if inn and not inn_valid(inn):
            errors.append(f"ИНН checksum FAILED: {inn} on {name} "
                          f"[{e.get('_origin', '?')}]")
        ogrn = e.get("ogrn")
        if ogrn and not ogrn_valid(ogrn):
            errors.append(f"ОГРН checksum FAILED: {ogrn} on {name} "
                          f"[{e.get('_origin', '?')}]")

    for p in people or []:
        inn = p.get("inn_personal")
        if inn and not inn_valid(inn):
            errors.append(f"personal ИНН checksum FAILED: {inn} on {p.get('fio_ru')}")

    # --- 4. duplicates ---------------------------------------------------
    by_inn = defaultdict(list)
    by_norm = defaultdict(list)
    for e in entities:
        if e.get("inn"):
            by_inn[e["inn"]].append(e["name_ru"])
        by_norm[normalise_name(e.get("name_ru", ""))].append(e["name_ru"])

    for inn, names in by_inn.items():
        if len(names) > 1:
            errors.append(f"duplicate ИНН {inn}: {names}")
    for norm, names in by_norm.items():
        if len(names) > 1 and norm:
            warnings.append(f"possible duplicate by name ({norm}): {names}")

    slugs = Counter(e.get("slug") for e in entities)
    for slug, n in slugs.items():
        if n > 1:
            errors.append(f"duplicate entity slug '{slug}' x{n}")

    pslugs = Counter(p.get("slug") for p in people or [])
    for slug, n in pslugs.items():
        if n > 1:
            warnings.append(f"duplicate person slug '{slug}' x{n}")

    # --- 5. referential integrity ----------------------------------------
    # Generic and recursive: catches a source_id/slug reference anywhere in
    # a record, not just the fields a human remembered to enumerate here —
    # a bare per-field list has repeatedly missed new nested arrays (e.g.
    # trademarks[], patents[], images[]) as the schema grew.
    source_ids = {s["id"] for s in sources or []}
    entity_slugs = {e["slug"] for e in entities}
    entity_inns = {e["inn"] for e in entities if e.get("inn")}
    people_slugs = {p.get("slug") for p in (people or [])}

    for e in entities:
        for sid in e.get("sources", []):
            if sid not in source_ids:
                errors.append(f"{e['name_ru']}: unknown source_id '{sid}'")
        for path, sid in find_refs(e, {"source_id"}):
            if sid not in source_ids:
                errors.append(f"{e['name_ru']}: {path} cites unknown source_id '{sid}'")
        for path, val in find_refs(e, {"slug", "entity_slug"}):
            if path == "slug":
                continue  # the record's own identity, not a reference
            if val not in entity_slugs:
                errors.append(f"{e['name_ru']}: {path} references unknown entity slug '{val}'")
        brand_of = e.get("is_brand_of")
        if brand_of and brand_of not in entity_inns:
            errors.append(f"{e['name_ru']}: is_brand_of references unknown ИНН '{brand_of}'")
        merged = e.get("_merged_into")
        if merged and merged not in entity_slugs:
            errors.append(f"{e['name_ru']}: _merged_into references unknown entity slug '{merged}'")

    for p in people or []:
        for path, sid in find_refs(p, {"source_id"}):
            if sid not in source_ids:
                errors.append(f"{p['fio_ru']}: {path} cites unknown source_id '{sid}'")
        for path, es in find_refs(p, {"entity_slug"}):
            if es not in entity_slugs:
                errors.append(f"{p['fio_ru']}: {path} references unknown entity slug '{es}'")
        merged = p.get("_merged_into")
        if merged and merged not in people_slugs:
            errors.append(f"{p['fio_ru']}: _merged_into references unknown person slug '{merged}'")

    for q in quotes or []:
        sid = q.get("source_id")
        if sid and sid not in source_ids:
            errors.append(f"quote {q.get('id')}: unknown source_id '{sid}'")

    # --- 6. history arrays -------------------------------------------------
    HISTORY_KEYS = ["director_history", "charter_capital_history",
                    "address_history", "name_history", "founders_history",
                    "facility_type_history", "financials"]
    FACILITY_TYPES = {"soviet_legacy_defense_industrial",
                      "purpose_built_technopark_sez",
                      "generic_registered_address",
                      "claimed_future_secure_technopark", "unknown"}
    WB_OVERLAP_VALUES = {"confirmed_direct", "confirmed_reseller",
                          "none_found", "not_checked"}
    unsourced_history = 0
    for e in entities:
        ft = e.get("facility_type")
        if ft and ft not in FACILITY_TYPES:
            errors.append(f"{e['name_ru']}: unknown facility_type '{ft}'")
        wbo = e.get("wb_overlap")
        if wbo and wbo not in WB_OVERLAP_VALUES:
            errors.append(f"{e['name_ru']}: unknown wb_overlap value '{wbo}' "
                          f"(valid: {sorted(WB_OVERLAP_VALUES)})")
        for h in e.get("facility_type_history") or []:
            v = h.get("value")
            if v and v not in FACILITY_TYPES:
                errors.append(f"{e['name_ru']}: facility_type_history has "
                              f"unknown value '{v}'")
        for key in HISTORY_KEYS:
            hist = e.get(key) or []
            if not isinstance(hist, list):
                errors.append(f"{e['name_ru']}: '{key}' is not a list")
                continue
            dated = [h for h in hist if h.get("as_of") or h.get("year")]
            stamps = [h.get("as_of") or str(h.get("year")) for h in dated]
            if stamps != sorted(stamps):
                errors.append(f"{e['name_ru']}: '{key}' entries are not "
                              f"date-ordered ({stamps})")
            for h in hist:
                # resolution already checked generically above; this pass
                # only counts unsourced placeholders, which is specific to
                # history-style fields (a trademark/patent with no source_id
                # is just incomplete, not a "placeholder awaiting a fact")
                if not h.get("source_id"):
                    unsourced_history += 1
    if unsourced_history:
        warnings.append(f"{unsourced_history} history entries have no "
                        f"source_id — placeholders awaiting verification, "
                        f"not evidence yet")

    # --- source date sanity --------------------------------------------
    for s in sources or []:
        if s.get("captured_date") and not re.match(
                r"^\d{4}-\d{2}-\d{2}$", s["captured_date"]):
            errors.append(f"source {s['id']}: malformed captured_date "
                          f"'{s['captured_date']}'")
        if s.get("as_of") and not s.get("type"):
            warnings.append(f"source {s['id']}: has as_of but no doc type "
                            f"— {s.get('path')}")

    # --- byte-identical files under different names ----------------------
    # sha256 is filled by inventory_sources.py from actual file bytes. Two
    # different filenames hashing the same usually means an accidental
    # re-download saved under a new name (wasted disk, and a MANIFEST row
    # that looks like independent corroboration but is the same document
    # twice) rather than a real second source — worth a human glance, not
    # an error, since a legitimate case exists (e.g. an identical zero-diff
    # egrul_api re-pull, already handled separately via supersedes chains).
    by_hash: dict[str, list[str]] = {}
    for s in sources or []:
        h = s.get("sha256")
        if h:
            by_hash.setdefault(h, []).append(s["path"])
    for h, paths in by_hash.items():
        if len(paths) > 1:
            warnings.append(f"identical file content under {len(paths)} "
                            f"names: {', '.join(paths)}")

    # --- source version chains --------------------------------------------
    for s in sources or []:
        for key in ("supersedes", "superseded_by"):
            sid = s.get(key)
            if sid and sid not in source_ids:
                errors.append(f"source {s['id']}: {key} references "
                              f"unknown source '{sid}'")

    # --- 6. records needing a human --------------------------------------
    # A brand record legitimately carries a slashed display name («Булат» /
    # 3mx); it points at its maker via is_brand_of rather than being a company.
    compound = [e["name_ru"] for e in entities
                if re.search(r"\s/\s", e.get("name_ru", ""))
                and not e.get("is_brand_of")]
    no_tier = [e["name_ru"] for e in entities if not e.get("tier")]
    no_inn = [e["name_ru"] for e in entities if not e.get("inn")]
    unverified = [e for e in entities if not e.get("_verified")]
    manufacturers = [e for e in entities if e.get("tier") == "manufacturer"]

    for name in compound:
        warnings.append(f"compound record holds >1 entity, needs splitting: {name}")

    # --- report ----------------------------------------------------------
    for err in errors:
        print(f"ERROR   {err}")
    for w in warnings:
        print(f"warn    {w}")

    if not args.quiet:
        print()
        print("--- coverage ---")
        print(f"entities              {len(entities)}")
        print(f"  verified            {len(entities) - len(unverified)}")
        print(f"  unverified          {len(unverified)}")
        print(f"  without ИНН         {len(no_inn)}")
        print(f"  without tier        {len(no_tier)}")
        print(f"manufacturers         {len(manufacturers)}")
        print(f"  with financials     {sum(1 for e in manufacturers if e.get('financials'))}")
        print(f"  with a ЦБСТ tie     {sum(1 for e in manufacturers if e.get('cbst_tie'))}")
        print(f"  wb_overlap checked  {sum(1 for e in manufacturers if e.get('wb_overlap') != 'not_checked')}")
        print(f"people                {len(people or [])}")
        print(f"  with DOB            {sum(1 for p in (people or []) if p.get('dob'))}")
        print(f"sources               {len(sources or [])}")
        print(f"  typed               {sum(1 for s in (sources or []) if s.get('type'))}")
        print(f"  with captured_date  {sum(1 for s in (sources or []) if s.get('captured_date'))}")
        print(f"  with as_of          {sum(1 for s in (sources or []) if s.get('as_of'))}")
        print(f"quotes                {len(quotes or [])}")

    print()
    print(f"{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
