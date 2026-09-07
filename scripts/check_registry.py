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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reverse_source_index import build_index  # noqa: E402

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
    global_open_qs = load("open_questions.json")

    if entities is None:
        print("error: data/registry/entities.json not found — run "
              "scripts/extract_registry.py first", file=sys.stderr)
        return 1

    errors: list[str] = []
    warnings: list[str] = []

    # --- 0. corrections files apply at all --------------------------------
    # extract_registry.py reads ONLY spec["set"] for the entities{}/people{}
    # blocks. A correction written as bare top-level fields is not an error
    # anywhere — it is simply skipped, silently, for as long as it sits in
    # the file. Six such entries were found on 2026-09-05 that had never
    # applied since the day they were written (2026-09-04), including
    # tier_basis text on three Архангел entities; they were only noticed
    # because a same-day domain_history edit failed to reach a rebuilt
    # profile. Fail loudly on the shape instead of trusting authorship.
    for fname, block, key_label in (("corrections_entities.json", "entities", "ИНН/slug"),
                                    ("corrections_people.json", "people", "slug")):
        path = REG / fname
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as ex:
            errors.append(f"{fname}: not valid JSON ({ex})")
            continue

        # A duplicate key within one JSON object is legal JSON but json.load
        # silently keeps only the last occurrence -- an earlier edit (e.g. a
        # first "open_questions" array nested inside "set", a second one
        # added later as a sibling of "set") vanishes with no error anywhere.
        # Caught by hand on 2026-09-05 after an edit to ooo-boevye-tekhnologii
        # silently dropped a freshly-added open_questions entry. Re-parse with
        # object_pairs_hook to surface any object with a repeated key.
        def _check_dupes(pairs, _fname=fname):
            keys = [k for k, _ in pairs]
            for k in set(keys):
                if keys.count(k) > 1:
                    errors.append(
                        f"{_fname}: duplicate key \"{k}\" in one JSON object "
                        f"— only the last occurrence survives json.load; the "
                        f"other(s) are silently discarded")
            return dict(pairs)
        json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_check_dupes)

        for key, spec in (data.get(block) or {}).items():
            if not isinstance(spec, dict):
                errors.append(f"{fname}: {block}['{key}'] must be an object")
            elif "set" not in spec:
                errors.append(
                    f"{fname}: {block}['{key}'] has no 'set' key — its fields "
                    f"({', '.join(k for k in spec if not k.startswith('_'))[:80]}) "
                    f"are SILENTLY IGNORED by extract_registry.py. Wrap the "
                    f"changed fields in {{\"set\": {{...}}}}; 'why' and "
                    f"'verified_against' stay alongside it.")

        # A correction key can be either a slug or an identifier (ИНН for
        # entities, personal ИНН for people is NOT used as a key today, but
        # entities are keyed inconsistently by either). Two correction
        # entries resolving to the SAME live record is a demonstrated
        # data-loss bug (see memory roymarket_correction_key_collision_bug):
        # extract_registry.py applies both 'set' dicts to the same
        # underlying object, and whichever key is processed last silently
        # wins on any overlapping field, discarding the other's edits with
        # no error anywhere. Found and hand-fixed for ~9 entities across two
        # sessions (2026-09-07); this check makes a NEW collision fail the
        # build instead of sitting undetected until it corrupts a field.
        records = entities if block == "entities" else (people or [])
        id_field = "inn" if block == "entities" else "inn_personal"
        slug_of_id = {r[id_field]: r["slug"] for r in records if r.get(id_field) and r.get("slug")}
        valid_slugs = {r["slug"] for r in records if r.get("slug")}
        resolved: dict[str, list[str]] = defaultdict(list)
        for key in (data.get(block) or {}):
            if key in valid_slugs:
                resolved[key].append(key)
            elif key in slug_of_id:
                resolved[slug_of_id[key]].append(key)
            # else: key matches no live record by slug or ИНН — not this
            # check's concern (extract_registry.py already scaffolds/warns
            # on an unmatched correction key elsewhere).
        for canonical_slug, raw_keys in resolved.items():
            if len(raw_keys) > 1:
                # Two correction keys pointing at the same record are only an
                # ACTIVE data-loss risk if their 'set' blocks actually share a
                # field — that's the case where "whichever is processed last
                # wins" can silently discard a value. A pair with no field
                # overlap is dormant risk (any future edit to either could
                # still introduce the conflict) — real technical debt, but
                # not yet corrupting anything, so it's a warning, not a
                # build-breaking error (per 2026-09-07 audit: ~43 such pairs
                # exist, only a handful had an actual conflict).
                field_sets = [set((data[block][k].get("set") or {}).keys()) for k in raw_keys]
                overlap = set.intersection(*field_sets) - {"why", "verified_against"}
                msg = (
                    f"{fname}: correction key collision — {raw_keys} all "
                    f"resolve to the same record ({canonical_slug}). "
                    f"extract_registry.py applies both 'set' blocks to the "
                    f"same object; whichever key is processed last silently "
                    f"wins on any overlapping field, discarding the other's "
                    f"edits with no error. Merge into a single key ({key_label})."
                )
                if overlap:
                    errors.append(msg + f" ACTIVE CONFLICT on field(s) {sorted(overlap)} "
                                         f"— one side's value is being silently dropped right now.")
                else:
                    warnings.append(msg + " No overlapping 'set' field today — dormant risk, "
                                           "not yet corrupting data, but merge when convenient.")
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
        corrected = p.get("_corrected")
        if corrected is not None and not isinstance(corrected, list):
            errors.append(f"{p.get('fio_ru')}: _corrected must be a list of "
                          f"note strings or null, got {type(corrected).__name__}")

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

    tombstone_entity_slugs = {e["slug"] for e in entities if e.get("_merged_into")}
    tombstone_people_slugs = {p.get("slug") for p in (people or []) if p.get("_merged_into")}

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
            elif not e.get("_merged_into") and val in tombstone_entity_slugs:
                warnings.append(f"{e['name_ru']}: {path} references '{val}', which is "
                                f"itself tombstoned (_merged_into) — should probably "
                                f"point at its merge target instead")
        brand_of = e.get("is_brand_of")
        if brand_of and brand_of not in entity_inns:
            errors.append(f"{e['name_ru']}: is_brand_of references unknown ИНН '{brand_of}'")
        merged = e.get("_merged_into")
        if merged:
            if merged not in entity_slugs:
                errors.append(f"{e['name_ru']}: _merged_into references unknown entity slug '{merged}'")
            elif merged in tombstone_entity_slugs:
                errors.append(f"{e['name_ru']}: _merged_into chains to another "
                              f"tombstone ('{merged}') — point directly at the "
                              f"final live record instead")

    for p in people or []:
        for path, sid in find_refs(p, {"source_id"}):
            if sid not in source_ids:
                errors.append(f"{p['fio_ru']}: {path} cites unknown source_id '{sid}'")
        for path, es in find_refs(p, {"entity_slug"}):
            if es not in entity_slugs:
                errors.append(f"{p['fio_ru']}: {path} references unknown entity slug '{es}'")
            elif es in tombstone_entity_slugs:
                warnings.append(f"{p['fio_ru']}: {path} references '{es}', which is "
                                f"itself tombstoned (_merged_into) — should probably "
                                f"point at its merge target instead")
        merged = p.get("_merged_into")
        if merged:
            if merged not in people_slugs:
                errors.append(f"{p['fio_ru']}: _merged_into references unknown person slug '{merged}'")
            elif merged in tombstone_people_slugs:
                errors.append(f"{p['fio_ru']}: _merged_into chains to another "
                              f"tombstone ('{merged}') — point directly at the "
                              f"final live record instead")
        for i, s in enumerate(p.get("sanctions") or []):
            regime = s.get("regime")
            if regime is not None and not (
                isinstance(regime, list) and all(isinstance(r, str) for r in regime)
            ):
                errors.append(f"{p['fio_ru']}: sanctions[{i}].regime must be "
                              f"a list of jurisdiction strings or null (not a "
                              f"semicolon-joined string, not a bare "
                              f"OpenSanctions topic code), got {regime!r}")
        for i, oq in enumerate(p.get("open_questions") or []):
            if not isinstance(oq, dict) or "text" not in oq:
                errors.append(f"{p['fio_ru']}: open_questions[{i}] must be "
                              f"{{'text': str, 'source_id': str|null}} — same "
                              f"field name as the global open_questions.json "
                              f"store, got {oq!r}")

    for q in quotes or []:
        sid = q.get("source_id")
        if sid and sid not in source_ids:
            errors.append(f"quote {q.get('id')}: unknown source_id '{sid}'")

    OQ_SCOPES = {"global", "unmined-source"}
    for oq in global_open_qs or []:
        oid = oq.get("id", "?")
        if "text" not in oq:
            errors.append(f"open_questions.json {oid}: missing 'text' — same "
                          f"field name as entity/person open_questions[]")
        if oq.get("scope") not in OQ_SCOPES:
            errors.append(f"open_questions.json {oid}: unknown scope "
                          f"'{oq.get('scope')}' (valid: {sorted(OQ_SCOPES)})")
        es = oq.get("entity_slug")
        if es and es not in entity_slugs:
            errors.append(f"open_questions.json {oid}: entity_slug "
                          f"references unknown entity slug '{es}'")
        ps = oq.get("person_slug")
        if ps and ps not in people_slugs:
            errors.append(f"open_questions.json {oid}: person_slug "
                          f"references unknown person slug '{ps}'")
        if es and ps:
            errors.append(f"open_questions.json {oid}: has both entity_slug "
                          f"and person_slug set — should be attributed to "
                          f"exactly one, or neither")

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
        cc = e.get("charter_capital")
        if cc is not None and (isinstance(cc, bool) or not isinstance(cc, (int, float))):
            errors.append(f"{e['name_ru']}: charter_capital must be a number "
                          f"or null, got {type(cc).__name__} ({cc!r})")
        om = e.get("okved_mismatch")
        if om is not None and (not isinstance(om, dict)
                                or set(om) - {"mismatch", "note"}
                                or not isinstance(om.get("mismatch"), bool)
                                or (om.get("note") is not None
                                    and not isinstance(om.get("note"), str))):
            errors.append(f"{e['name_ru']}: okved_mismatch must be null or "
                          f"{{'mismatch': bool, 'note': str|null}}, got {om!r}")
        for i, oq in enumerate(e.get("open_questions") or []):
            if not isinstance(oq, dict) or "text" not in oq:
                errors.append(f"{e['name_ru']}: open_questions[{i}] must be "
                              f"{{'text': str, 'source_id': str|null}} — same "
                              f"field name as the global open_questions.json "
                              f"store, got {oq!r}")
        for i, s in enumerate(e.get("sanctions") or []):
            regime = s.get("regime")
            if regime is not None and not (
                isinstance(regime, list) and all(isinstance(r, str) for r in regime)
            ):
                errors.append(f"{e['name_ru']}: sanctions[{i}].regime must be "
                              f"a list of jurisdiction strings or null (not a "
                              f"semicolon-joined string, not a bare "
                              f"OpenSanctions topic code), got {regime!r}")
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
    # Fix 2026-09-02: this used to emit one warning line per duplicate-hash
    # group — with the zakupki corpus alone serving the same attachment
    # under several filenames, that was 546 of 549 total warnings, burying
    # the handful of warnings that actually need a human look. Collapse to
    # one summary line (still lists every path, for anyone who greps the
    # full output) plus up-front visibility into which groups are the
    # expected zakupki-attachment case vs. something else worth a glance.
    by_hash: dict[str, list[str]] = {}
    for s in sources or []:
        h = s.get("sha256")
        if h:
            by_hash.setdefault(h, []).append(s["path"])
    dup_groups = {h: paths for h, paths in by_hash.items() if len(paths) > 1}
    zakupki_dup_groups = {h: p for h, p in dup_groups.items()
                          if all("ZAKUPKI" in path for path in p)}
    other_dup_groups = {h: p for h, p in dup_groups.items() if h not in zakupki_dup_groups}
    if zakupki_dup_groups:
        warnings.append(
            f"{len(zakupki_dup_groups)} byte-identical zakupki attachment group(s) "
            f"under multiple filenames (expected — zakupki.gov.ru itself serves the "
            f"same document under several names; not a data-quality issue). Full list: "
            + " | ".join(f"[{', '.join(p)}]" for p in zakupki_dup_groups.values()))
    for h, paths in other_dup_groups.items():
        warnings.append(f"identical file content under {len(paths)} "
                        f"names (non-zakupki — worth a look): {', '.join(paths)}")

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
        live_entity_count = len(entities) - len(tombstone_entity_slugs)
        live_people_count = len(people or []) - len(tombstone_people_slugs)
        print(f"entities              {len(entities)} raw / {live_entity_count} live "
              f"({len(tombstone_entity_slugs)} merged into another record)")
        print(f"  verified            {len(entities) - len(unverified)}")
        print(f"  unverified          {len(unverified)}")
        print(f"  without ИНН         {len(no_inn)}")
        print(f"  without tier        {len(no_tier)}")
        print(f"manufacturers         {len(manufacturers)}")
        print(f"  with financials     {sum(1 for e in manufacturers if e.get('financials'))}")
        print(f"  with a ЦБСТ tie     {sum(1 for e in manufacturers if e.get('cbst_tie'))}")
        print(f"  wb_overlap checked  {sum(1 for e in manufacturers if e.get('wb_overlap') != 'not_checked')}")
        print(f"people                {len(people or [])} raw / {live_people_count} live "
              f"({len(tombstone_people_slugs)} merged into another record)")
        print(f"  with DOB            {sum(1 for p in (people or []) if p.get('dob'))}")
        print(f"sources               {len(sources or [])}")
        print(f"  typed               {sum(1 for s in (sources or []) if s.get('type'))}")
        print(f"  with captured_date  {sum(1 for s in (sources or []) if s.get('captured_date'))}")
        print(f"  with as_of          {sum(1 for s in (sources or []) if s.get('as_of'))}")
        entity_sources, person_sources, source_refs = build_index(
            entities, people or [], sources or [])
        print(f"  reverse-indexed     {len(source_refs)} sources cite a known "
              f"entity/person ИНН, reaching {len(entity_sources)} entities + "
              f"{len(person_sources)} people (see scripts/reverse_source_index.py)")
        print(f"quotes                {len(quotes or [])}")
        oq_attributed = sum(1 for oq in (global_open_qs or [])
                            if oq.get("entity_slug") or oq.get("person_slug"))
        print(f"open_questions.json   {len(global_open_qs or [])} global "
              f"({oq_attributed} attributed to a specific entity/person)")

    print()
    print(f"{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
