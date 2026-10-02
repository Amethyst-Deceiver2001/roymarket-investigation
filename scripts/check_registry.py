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
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reverse_source_index import build_index  # noqa: E402
from graph_contract import (validate_graph, validate_views, SELLS_FOR_BASIS, SALE_STATUSES, ASSERTED_BY,
                            CREDIBILITY, AUTHORISED, BASIS_CREDIBILITY, RELATION_ROLES, PARTNER_KIND_EDGE,  # noqa: E402
                            ECOSYSTEM_ROLES, LEGAL_ENTITY_STATUS, PROGRAM_KINDS, PROGRAM_SUBTYPES,
                            MEMBERSHIP_ROLES, MEDIA_KINDS, MEDIA_GENRES, MEDIA_PUBLISH, MEDIA_ABOUT_TYPES,
                            MEDIA_GEO_PRECISION, MEDIA_GEO_METHOD, MEDIA_REDACT, MEDIA_REDACT_GENRES, MEDIA_ASSERTED_BY,
                            BRAND_KINDS)
from build_relationship_graph import build_graph, build_views  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
REG = REPO / "data" / "registry"

ENTITY_REQUIRED = ["slug", "name_ru", "inn", "ogrn", "tier", "_verified"]
PERSON_REQUIRED = ["slug", "fio_ru", "roles", "_verified"]

LEGAL_PREFIX = re.compile(
    r"^(ФГКУ|ФГУП|ФКУ|ГУП|МУП|АНО|ОАО|ПАО|ЗАО|ООО|АО|НПЦ|НПО|НПП|ОПКБ|"
    r"СКБ|КБ|ГК|ИП|Фонд|НТЦ|НИПП|УЦ|ЮФ|ЗПИФ|УК)\s*",
    re.IGNORECASE,
)
# normalise_name() lowercases its input before applying LEGAL_PREFIX, so this
# flag is load-bearing: without it, none of the (capitalized-Cyrillic)
# alternatives above ever match, and the legal-form-prefix strip this
# function's docstring promises ("ООО «X» / «X» / OOO "X" variants") silently
# never fires. Found 2026-09-07 while chasing why an obviously-matching
# guillemet-quoted entity name in a role's title text wasn't resolving.


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


def validate_generated_graph(
    graph: dict,
    graph_views: dict | None,
    entities: list[dict],
    people: list[dict],
    sources: list[dict],
    military_units: list[dict] | None = None,
    programs: list[dict] | None = None,
    products: list[dict] | None = None,
) -> list[str]:
    """Check artifacts against an independent deterministic registry rebuild."""
    graph_errors = validate_graph(graph, entities, people, sources)
    errors = [*graph_errors]
    if graph_views is None:
        errors.append("relationship_graph_views.json missing — run "
                      "scripts/build_relationship_graph.py")
    elif not graph_errors:
        errors.extend(validate_views(graph, graph_views))

    expected_graph = build_graph(entities, people, military_units, programs, products)
    if graph != expected_graph:
        errors.append(
            "relationship_graph.json does not exactly match the deterministic "
            "rebuild from live entities.json/people.json — relationship "
            "endpoints, source_id provenance, classifications, or tombstone "
            "handling are stale or altered; run scripts/build_relationship_graph.py")
    if graph_views is not None and graph_views != build_views(expected_graph):
        errors.append(
            "relationship_graph_views.json does not exactly match the "
            "deterministic derived views from the live registry; run "
            "scripts/build_relationship_graph.py")
    return errors


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

    # --- ecosystem roles and sells_for[] (schema v7, 2026-10-01) -----------
    # A seller edge that points at a misspelled slug is dropped by the graph builder without a word,
    # so the shape is checked here, not left to the builder.
    live_slugs = {e["slug"] for e in entities if not e.get("_merged_into")}
    for e in entities:
        if e.get("_merged_into"):
            continue
        roles = e.get("ecosystem_roles")
        if roles is not None:
            bad = [r for r in (roles if isinstance(roles, list) else [roles]) if r not in ECOSYSTEM_ROLES]
            if not isinstance(roles, list) or bad:
                errors.append(f"{e['slug']}: ecosystem_roles must be a list drawn from {sorted(ECOSYSTEM_ROLES)} (got {roles!r})")
        status = e.get("legal_entity_status")
        if status is not None and status not in LEGAL_ENTITY_STATUS:
            errors.append(f"{e['slug']}: legal_entity_status {status!r} not in {sorted(LEGAL_ENTITY_STATUS)}")
        if "brand" in (roles or []) and status != "unresolved" and not e.get("inn"):
            warnings.append(f"{e['slug']}: role 'brand' with no ИНН should say legal_entity_status: 'unresolved'")
        for i, sale in enumerate(e.get("sells_for") or []):
            where = f"{e['slug']}.sells_for[{i}]"
            if not isinstance(sale, dict):
                errors.append(f"{where} must be an object"); continue
            if sale.get("slug") not in live_slugs:
                errors.append(f"{where}.slug {sale.get('slug')!r} is not a live entity")
            if sale.get("slug") == e["slug"]:
                errors.append(f"{where} points at the entity itself")
            if not sale.get("channel"):
                errors.append(f"{where}.channel is required (the edge label, e.g. 'Ozon', 'own site', 'dealer network')")
            if sale.get("basis") not in SELLS_FOR_BASIS:
                errors.append(f"{where}.basis must be one of {sorted(SELLS_FOR_BASIS)} (got {sale.get('basis')!r})")
            if sale.get("basis") in ("doc", "press") and not sale.get("source_id"):
                warnings.append(f"{where} basis {sale.get('basis')!r} has no source_id")
            if sale.get("source_id") and sale["source_id"] not in source_ids:
                errors.append(f"{where}.source_id {sale['source_id']!r} is not a known source")
            # relation envelope (schema v9): all optional, each validated when present
            if "products" in sale and not (isinstance(sale["products"], list) and sale["products"]
                                           and all(isinstance(p, str) and p for p in sale["products"])):
                errors.append(f"{where}.products must be a non-empty list of strings")
            for key, vocab in (("role", RELATION_ROLES), ("asserted_by", ASSERTED_BY), ("credibility", CREDIBILITY), ("authorised", AUTHORISED)):
                if key in sale and sale[key] not in vocab:
                    errors.append(f"{where}.{key} must be one of {sorted(vocab)} (got {sale[key]!r})")
            if sale.get("credibility") and sale.get("basis") in BASIS_CREDIBILITY \
                    and sale["credibility"] not in BASIS_CREDIBILITY[sale["basis"]]:
                errors.append(f"{where}.credibility {sale['credibility']!r} contradicts basis {sale['basis']!r}")
            if sale.get("role") and sale["role"] not in (e.get("ecosystem_roles") or []):
                warnings.append(f"{where}.role {sale['role']!r} is not in the entity's ecosystem_roles summary {e.get('ecosystem_roles')}")
            if "open" in sale and not (isinstance(sale["open"], str) and sale["open"].strip()):
                errors.append(f"{where}.open must be a non-empty string")
            for j, h in enumerate(sale.get("status_history") or []):
                w = f"{where}.status_history[{j}]"
                if not isinstance(h, dict) or h.get("status") not in SALE_STATUSES:
                    errors.append(f"{w}.status must be one of {list(SALE_STATUSES)}"); continue
                if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(h.get("as_of") or "")):
                    errors.append(f"{w}.as_of must be YYYY-MM-DD (an undated state is not recorded)")
                if not h.get("source_id") or h["source_id"] not in source_ids:
                    errors.append(f"{w}.source_id is required and must be a known source")

    # --- platform_partners[] (schema v10, 2026-10-02): bank / acquirer / logistics partner of a platform ----
    for e in entities:
        if e.get("_merged_into"):
            continue
        for i, pt in enumerate(e.get("platform_partners") or []):
            w = f"{e['slug']}.platform_partners[{i}]"
            if not isinstance(pt, dict):
                errors.append(f"{w} must be an object"); continue
            if pt.get("slug") not in live_slugs or pt.get("slug") == e["slug"]:
                errors.append(f"{w}.slug {pt.get('slug')!r} must be another live entity")
            if pt.get("kind") not in PARTNER_KIND_EDGE:
                errors.append(f"{w}.kind must be one of {sorted(PARTNER_KIND_EDGE)}")
            if pt.get("basis") not in SELLS_FOR_BASIS:
                errors.append(f"{w}.basis must be one of {sorted(SELLS_FOR_BASIS)}")
            if not pt.get("source_id") or pt["source_id"] not in source_ids:
                errors.append(f"{w}.source_id is required and must be a known source (a partner is recorded only from a document that names it)")
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(pt.get("as_of") or "")):
                errors.append(f"{w}.as_of must be YYYY-MM-DD")

    # --- candidate_identities[] (2026-10-02): unverified same-name legal entities, never drawn, never a tie ----
    # They exist so a name match is recorded without becoming an identity: an ИНН here is a lead and is never
    # copied into the entity's own `inn`. No graph edge is built from this field.
    inn_owner = {e.get("inn"): e["slug"] for e in entities if e.get("inn") and not e.get("_merged_into")}
    for e in entities:
        cands = e.get("candidate_identities")
        if cands is None or e.get("_merged_into"):
            continue
        if not isinstance(cands, list):
            errors.append(f"{e['slug']}.candidate_identities must be a list"); continue
        for i, cd in enumerate(cands):
            w = f"{e['slug']}.candidate_identities[{i}]"
            if not isinstance(cd, dict) or not cd.get("name_ru"):
                errors.append(f"{w} needs name_ru"); continue
            if cd.get("status") not in ("unverified", "rejected"):
                errors.append(f"{w}.status must be 'unverified' or 'rejected'")
            if cd.get("inn") and not inn_valid(str(cd["inn"])):
                errors.append(f"{w}.inn {cd['inn']!r} fails the checksum")
            if cd.get("inn") and cd["inn"] == e.get("inn"):
                errors.append(f"{w}.inn equals the entity's own inn: a candidate is not the record")
            if cd.get("inn") in inn_owner and inn_owner[cd["inn"]] != e["slug"]:
                warnings.append(f"{w}.inn belongs to the live entity {inn_owner[cd['inn']]}: link it as a related entity, not a candidate")
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(cd.get("as_of") or "")):
                errors.append(f"{w}.as_of must be YYYY-MM-DD")
            if cd.get("source_id") is None:
                warnings.append(f"{w} has no source_id (a lead from prose, not an archived extract)")
            elif cd["source_id"] not in source_ids:
                errors.append(f"{w}.source_id {cd['source_id']!r} is not a known source")

    # --- programs, events, groups and memberships (schema v8, 2026-10-01) ----
    programs_path = REG / "programs.json"
    programs = json.loads(programs_path.read_text(encoding="utf-8")) if programs_path.exists() else []
    prog_by_key = {}
    for i, rec in enumerate(programs):
        where = f"programs[{i}]"
        kind, slug = rec.get("kind"), rec.get("slug")
        if kind not in PROGRAM_KINDS:
            errors.append(f"{where}.kind {kind!r} not in {sorted(PROGRAM_KINDS)}"); continue
        if not slug or (kind, slug) in prog_by_key:
            errors.append(f"{where}.slug missing or duplicated for kind {kind}"); continue
        prog_by_key[(kind, slug)] = rec
        if rec.get("subtype") not in PROGRAM_SUBTYPES[kind]:
            errors.append(f"{where}.subtype {rec.get('subtype')!r} not valid for kind {kind}")
        if not rec.get("name_ru"):
            errors.append(f"{where}.name_ru is required")
    def _ref(where, slug, ok):
        if slug not in ok:
            errors.append(f"{where} {slug!r} does not resolve")
    for (kind, slug), rec in prog_by_key.items():
        where = f"programs[{kind}:{slug}]"
        for key in ("operators", "organisers", "members"):
            for j, x in enumerate(rec.get(key) or []):
                w = f"{where}.{key}[{j}]"
                _ref(w + ".slug", x.get("slug"), live_slugs)
                if x.get("basis") not in SELLS_FOR_BASIS:
                    errors.append(f"{w}.basis must be one of {sorted(SELLS_FOR_BASIS)}")
                if x.get("basis") in ("doc", "press") and not x.get("source_id"):
                    warnings.append(f"{w} basis {x.get('basis')!r} has no source_id")
                if x.get("source_id") and x["source_id"] not in source_ids:
                    errors.append(f"{w}.source_id {x['source_id']!r} is not a known source")
        parent = rec.get("parent")
        if parent:
            pk = "event" if kind == "event" else "program"
            if (pk, parent) not in prog_by_key:
                errors.append(f"{where}.parent {parent!r} is not a {pk} record")
        for j, c in enumerate(rec.get("claims") or []):
            if c.get("source_id") and c["source_id"] not in source_ids:
                errors.append(f"{where}.claims[{j}].source_id {c['source_id']!r} is not a known source")
            if not c.get("as_of"):
                warnings.append(f"{where}.claims[{j}] has no as_of")
    for e in entities:
        if e.get("_merged_into"):
            continue
        for fld, key, kind in (("memberships", "program", "program"), ("participations", "event", "event")):
            for j, m in enumerate(e.get(fld) or []):
                w = f"{e['slug']}.{fld}[{j}]"
                if (kind, m.get(key)) not in prog_by_key:
                    errors.append(f"{w}.{key} {m.get(key)!r} is not a {kind} record in programs.json")
                if m.get("role") not in MEMBERSHIP_ROLES:
                    errors.append(f"{w}.role {m.get('role')!r} not in {sorted(MEMBERSHIP_ROLES)}")
                if m.get("basis") not in SELLS_FOR_BASIS:
                    errors.append(f"{w}.basis must be one of {sorted(SELLS_FOR_BASIS)}")
                if m.get("basis") in ("doc", "press") and not m.get("source_id"):
                    warnings.append(f"{w} basis {m.get('basis')!r} has no source_id")
                if m.get("source_id") and m["source_id"] not in source_ids:
                    errors.append(f"{w}.source_id {m['source_id']!r} is not a known source")

    tombstone_people_slugs = {p.get("slug") for p in (people or []) if p.get("_merged_into")}

    # build_company_profile.py now refuses to render a tombstone (2026-09-07
    # hardening pass), but a page from BEFORE that guard existed can still
    # sit in docs/profiles/ looking exactly like a live, citable entity page
    # — found 3 real instances (kb-germes, ooo-sibnk, ooo-kb-sinergiya) this
    # same pass. Flag any such leftover file directly instead of relying on
    # someone noticing docs/profiles/ doesn't match entities.json.
    profiles_dir = REPO / "docs" / "profiles"
    if profiles_dir.exists():
        for slug in sorted(tombstone_entity_slugs):
            for ext in ("html", "md"):
                stale = profiles_dir / f"{slug}.{ext}"
                if stale.exists():
                    warnings.append(
                        f"docs/profiles/{slug}.{ext} is a published profile page "
                        f"for a tombstoned entity (_merged_into -> "
                        f"{next(e['_merged_into'] for e in entities if e['slug'] == slug)!r}) "
                        f"— stale, delete it (build_company_profile.py now refuses "
                        f"to regenerate it).")

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

    # --- products (data/registry/products.json, added 2026-10-02) ----------
    # One record per product with stable ids; versions, accessories, listings and deliveries hang off it.
    # Listings and deliveries are dated events, not edges. A listing with no source_id is a placeholder.
    products_path = REG / "products.json"
    products = json.loads(products_path.read_text(encoding="utf-8")) if products_path.exists() else []
    event_slugs = {r.get("slug") for r in programs if r.get("kind") == "event"}
    sells_pairs = {(e["slug"], x.get("slug")) for e in entities for x in e.get("sells_for") or []}
    seen_products = set()
    # `version` must be present but may be null (a post that says only «Булат» names no version);
    # the donor must be a live registry entity, so a volunteer or an individual is never recorded by accident
    DELIVERY_KEYS = ("date", "donor", "carrier", "recipient", "source_channel", "post_id",
                     "asserted_by", "credibility", "source_id")
    date_re = re.compile(r"\d{4}-\d{2}-\d{2}")
    for i, pr in enumerate(products):
        where = f"products[{i}]"
        slug = pr.get("slug")
        if not slug or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", str(slug)) or slug in seen_products:
            errors.append(f"{where}.slug must be a unique lowercase slug (got {slug!r})")
        seen_products.add(slug)
        where = f"products[{slug}]"
        if pr.get("kind") != "product":
            errors.append(f"{where}.kind must be 'product'")
        co = pr.get("clone_of")
        if co is not None:
            # clone_of (2026-10-02): a product stated, by a cited source, to copy another. Never inferred from a
            # shared category: a competitor in the same class is not a clone. The maker may be unresolved only here.
            if not isinstance(co, dict) or not co.get("product"):
                errors.append(f"{where}.clone_of needs a product (a slug in products.json, or the original's name)")
            else:
                if co.get("status") not in ("alleged", "shown", "denied"):
                    errors.append(f"{where}.clone_of.status must be alleged / shown / denied")
                if co.get("asserted_by") not in ASSERTED_BY:
                    errors.append(f"{where}.clone_of.asserted_by must be one of {sorted(ASSERTED_BY)}")
                if co.get("source_id") not in source_ids:
                    errors.append(f"{where}.clone_of.source_id must be a known source")
                if co["product"] in {x.get("slug") for x in products} and co["product"] == slug:
                    errors.append(f"{where}.clone_of points at itself")
        if pr.get("maker") is None and co is not None:
            pass
        elif pr.get("maker") not in live_slugs:
            errors.append(f"{where}.maker {pr.get('maker')!r} is not a live entity")
        versions = set()
        for j, v in enumerate(pr.get("versions") or []):
            if not v.get("slug") or v["slug"] in versions:
                errors.append(f"{where}.versions[{j}].slug must be unique")
            versions.add(v.get("slug"))
            if not v.get("source_id") or v["source_id"] not in source_ids:
                errors.append(f"{where}.versions[{j}].source_id is required and must be a known source")
        for j, a_ in enumerate(pr.get("accessories") or []):
            if a_.get("pairs_with") not in versions:
                errors.append(f"{where}.accessories[{j}].pairs_with must name one of the versions")
            if not a_.get("source_id") or a_["source_id"] not in source_ids:
                errors.append(f"{where}.accessories[{j}].source_id is required and must be a known source")
        for j, s_ in enumerate(pr.get("shown_at") or []):
            if s_.get("event") not in event_slugs:
                errors.append(f"{where}.shown_at[{j}].event {s_.get('event')!r} is not an event in programs.json")
            if s_.get("source_id") not in source_ids:
                errors.append(f"{where}.shown_at[{j}].source_id must be a known source")
        listing_ids = set()
        for j, l_ in enumerate(pr.get("listings") or []):
            w = f"{where}.listings[{j}]"
            if not l_.get("id") or l_["id"] in listing_ids:
                errors.append(f"{w}.id must be unique")
            listing_ids.add(l_.get("id"))
            if l_.get("version") is not None and l_["version"] not in versions:
                errors.append(f"{w}.version must be null or one of the versions")
            seller = l_.get("seller") or {}
            if not seller.get("storefront") or not seller.get("identity"):
                errors.append(f"{w}.seller needs a storefront name and an identity statement")
            ent = seller.get("entity")
            if ent is not None:
                if ent not in live_slugs:
                    errors.append(f"{w}.seller.entity {ent!r} is not a live entity")
                elif ent != pr.get("maker") and (ent, pr.get("maker")) not in sells_pairs:
                    warnings.append(f"{w}: seller {ent} has no sells_for edge to the maker {pr.get('maker')}")
            if l_.get("status") not in SALE_STATUSES:
                errors.append(f"{w}.status must be one of {list(SALE_STATUSES)}")
            if not date_re.fullmatch(str(l_.get("as_of") or "")):
                errors.append(f"{w}.as_of must be YYYY-MM-DD")
            if l_.get("basis") not in SELLS_FOR_BASIS:
                errors.append(f"{w}.basis must be one of {sorted(SELLS_FOR_BASIS)}")
            if l_.get("asserted_by") not in ASSERTED_BY:
                errors.append(f"{w}.asserted_by must be one of {sorted(ASSERTED_BY)}")
            sid = l_.get("source_id")
            if sid is None:
                warnings.append(f"{w} has no source_id: a placeholder awaiting an archived capture, not evidence")
            elif sid not in source_ids:
                errors.append(f"{w}.source_id {sid!r} is not a known source")
        for j, d in enumerate(pr.get("deliveries") or []):
            w = f"{where}.deliveries[{j}]"
            missing = [k for k in DELIVERY_KEYS if not d.get(k)]
            if missing:
                errors.append(f"{w} is missing {missing}")
                continue
            if not date_re.fullmatch(str(d["date"])) or "version" not in d or (d["version"] is not None and d["version"] not in versions):
                errors.append(f"{w}: date must be YYYY-MM-DD and version present (null, or one of the versions)")
            if d["donor"] not in live_slugs:
                errors.append(f"{w}.donor {d['donor']!r} is not a live entity (volunteers and individuals are not recorded as donors)")
            for sid2 in d.get("other_source_ids") or []:
                if sid2 not in source_ids:
                    errors.append(f"{w}.other_source_ids has unknown source {sid2!r}")
            if d["asserted_by"] not in ASSERTED_BY or d["credibility"] not in CREDIBILITY:
                errors.append(f"{w}: asserted_by / credibility outside the vocabulary")
            if d["source_id"] not in source_ids:
                errors.append(f"{w}.source_id must be a known source")
        for j, c_ in enumerate(pr.get("claims") or []):
            if not c_.get("text_ru") or c_.get("source_id") not in source_ids or not date_re.fullmatch(str(c_.get("as_of") or "")):
                errors.append(f"{where}.claims[{j}] needs text_ru, a known source_id and an as_of date")

    # --- brands (entities[].brands, B5, added 2026-10-02) -----------------------
    # The name a reader recognises. At most one primary; every brand sourced; a trademark brand names its
    # registration, which must be in the entity's own trademarks[].
    for e in entities:
        bs = e.get("brands") or []
        if not bs:
            continue
        w = f"entities[{e['slug']}].brands"
        if sum(1 for x in bs if x.get("primary")) > 1:
            errors.append(f"{w}: more than one primary brand")
        regs = {str(tm.get("reg_number") or tm.get("registration") or tm.get("number") or "") for tm in e.get("trademarks") or []}
        for j, x in enumerate(bs):
            if not (x.get("name") or "").strip() or x.get("kind") not in BRAND_KINDS:
                errors.append(f"{w}[{j}] needs a name and kind in {sorted(BRAND_KINDS)}")
            if x.get("source_id") not in source_ids:
                errors.append(f"{w}[{j}].source_id must be a known source")
            if x.get("kind") == "trademark":
                reg = str(x.get("registration") or "").removeprefix("RU")
                if not reg or not any(reg in r for r in regs):
                    errors.append(f"{w}[{j}]: a trademark brand needs a registration found in the entity's trademarks[]")

    # --- media (data/registry/media.json, track V, added 2026-10-02) -----------
    # One record per picture, video, still or imagery view; `about` lists every record it shows, so one
    # handover photo is not copied onto the donor, the product and the unit. Not drawn on the graph.
    delivery_ids, all_listing_ids, version_slugs = set(), set(), set()
    for pr in products:
        version_slugs |= {v.get("slug") for v in pr.get("versions") or []}
        all_listing_ids |= {l_.get("id") for l_ in pr.get("listings") or []}
        for j, d in enumerate(pr.get("deliveries") or []):
            did = d.get("id")
            if did is not None and (did in delivery_ids or not re.fullmatch(r"[a-z0-9-]+-d\d{2,3}", str(did))):
                errors.append(f"products[{pr.get('slug')}].deliveries[{j}].id {did!r} must be unique, like 'bulat-d01'")
            delivery_ids.add(did)
    media_path = REG / "media.json"
    media = json.loads(media_path.read_text(encoding="utf-8")) if media_path.exists() else []
    units_path = REG / "military_units.json"
    unit_slugs = {u.get("slug") for u in (json.loads(units_path.read_text(encoding="utf-8")) if units_path.exists() else [])}
    about_ids = {"entity": live_slugs, "person": people_slugs, "product": seen_products, "version": version_slugs,
                 "delivery": delivery_ids - {None}, "listing": all_listing_ids - {None}, "unit": unit_slugs,
                 "program": {r.get("slug") for r in programs}}
    seen_media, no_frame, blur_pending, no_copy = set(), [], [], []
    for i, m in enumerate(media):
        mid = m.get("id")
        where = f"media[{mid or i}]"
        if not re.fullmatch(r"m\d{4}", str(mid)) or mid in seen_media:
            errors.append(f"{where}.id must be unique, like 'm0001'")
        seen_media.add(mid)
        for key, vocab in (("kind", MEDIA_KINDS), ("genre", MEDIA_GENRES), ("publish", MEDIA_PUBLISH),
                           ("asserted_by", MEDIA_ASSERTED_BY)):
            if m.get(key) not in vocab:
                errors.append(f"{where}.{key} {m.get(key)!r} must be one of {sorted(vocab)}")
        if not (m.get("shows") or "").strip():
            errors.append(f"{where}.shows is required: what is visible, written by someone who looked")
        if m.get("source_id") not in source_ids:
            errors.append(f"{where}.source_id {m.get('source_id')!r} must be a known source")
        about = m.get("about") or []
        if not about:
            errors.append(f"{where}.about must name at least one record the picture shows")
        for a_ in about:
            if a_.get("type") not in MEDIA_ABOUT_TYPES or a_.get("id") not in about_ids.get(a_.get("type"), ()):
                errors.append(f"{where}.about {a_!r} does not resolve to a registry record")
        for key in ("published", "captured"):
            if m.get(key) is not None and not date_re.fullmatch(str(m[key])):
                errors.append(f"{where}.{key} must be YYYY-MM-DD or null")
        f = m.get("file")
        if f and not (REPO / f).exists():
            errors.append(f"{where}.file {f!r} does not exist")
        if m.get("publish") in ("ok", "excerpt") and not (f or "").startswith(("docs/images/", "exhibits/images/")) \
                and not list((REPO / "exhibits" / "images" / "media").glob(f"{mid}.*")):
            no_copy.append(mid)
        if m.get("kind") == "still":
            fr = m.get("frame") or {}
            if not re.fullmatch(r"\d{1,2}:\d{2}(:\d{2})?", str(fr.get("t") or "")):
                no_frame.append(mid)
        if m.get("kind") in ("satellite", "street-level"):
            im = m.get("imagery") or {}
            if not im.get("provider") or not re.fullmatch(r"\d{4}(-\d{2}(-\d{2})?)?", str(im.get("date") or "")):
                errors.append(f"{where}.imagery needs provider and date (YYYY, YYYY-MM or YYYY-MM-DD)")
            if not m.get("geo"):
                errors.append(f"{where}: a {m['kind']} view needs geo")
        g = m.get("geo")
        if g is not None:
            try:
                ok_ll = -90 <= float(g.get("lat")) <= 90 and -180 <= float(g.get("lon")) <= 180
            except (TypeError, ValueError):
                ok_ll = False
            if not ok_ll or g.get("precision") not in MEDIA_GEO_PRECISION or g.get("method") not in MEDIA_GEO_METHOD:
                errors.append(f"{where}.geo needs lat, lon, precision {sorted(MEDIA_GEO_PRECISION)} "
                              f"and method {sorted(MEDIA_GEO_METHOD)}")
            elif g["method"] in ("register_address", "source_stated") and g.get("source_id") not in source_ids:
                errors.append(f"{where}.geo.source_id must name the document that gives the address or place")
        if m.get("redact") is not None and m["redact"] not in MEDIA_REDACT:
            errors.append(f"{where}.redact must be one of {sorted(MEDIA_REDACT)}")
        if m.get("genre") in MEDIA_REDACT_GENRES and m.get("publish") != "internal" \
                and m.get("redact") not in ("none_needed", "blurred"):
            blur_pending.append(mid)
        if m.get("genre") == "combat" and m.get("publish") != "internal" and m.get("graphic") is None:
            warnings.append(f"{where}: combat imagery needs graphic: true/false before it is published")
    if no_copy:
        warnings.append(f"media: {len(no_copy)} publishable record(s) have no publish copy yet (docs/images/, or "
                        f"exhibits/images/media/ written by a page builder): {', '.join(no_copy)}")
    if no_frame:
        warnings.append(f"media: {len(no_frame)} still(s) without frame.t, their timestamp in the video: {', '.join(no_frame)}")
    if blur_pending:
        warnings.append(f"media: {len(blur_pending)} record(s) where people may be visible have not been checked by eye "
                        f"(set redact: none_needed if everyone is involved, blurred once an uninvolved bystander is "
                        f"blurred): {', '.join(blur_pending)}")

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

    # --- 6b. financials row must come from the entity's own БФО filing -----
    # Found 2026-09-30: three entities (Заволжское, Борей, ГК «Логос») carried
    # rows from a DIFFERENT company's filing -- the filer ИНН is in the БФО
    # filename, and an automated attach by year had ignored it. A mismatch is
    # allowed only when the row's own note names the filer ИНН (a deliberate,
    # labelled proxy such as a parent company's accounts).
    src_path = {s_["id"]: s_.get("path") or "" for s_ in sources or []}
    for e in entities:
        own = e.get("inn")
        if not own or e.get("_merged_into"):
            continue
        for f in e.get("financials") or []:
            m = re.search(r"(?:БФО|BFO)_(\d{10,12})_", src_path.get(f.get("source_id"), "").rsplit("/", 1)[-1])
            if m and m.group(1) != own and m.group(1) not in (f.get("note") or ""):
                errors.append(
                    f"{e['name_ru']}: financials {f.get('year')} cites {f.get('source_id')}, a "
                    f"БФО filed under ИНН {m.group(1)}, not this entity's ИНН {own}, and the row's "
                    f"note does not name that filer -- wrong-entity row, or an unlabelled proxy")

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
    # A screening tool (OPENSANCTIONS_/ALEPH_) re-pulled on a later date and got
    # a byte-identical result -- "checked again, no change", not a data problem.
    # Only collapses when every filename in the group is identical apart from
    # its 8-digit date segment; a same-date or differently-keyed pair (e.g. a
    # slug typo, or ALEPH_DETAIL_unknown's hash-suffix mismatch) still differs
    # after stripping the date, so it stays flagged as worth a human glance.
    def _strip_date(path: str) -> str:
        return re.sub(r"\d{8}", "", path)
    rescreen_dup_groups = {
        h: p for h, p in dup_groups.items()
        if h not in zakupki_dup_groups
        and all(pp.split("/")[-1].startswith(("OPENSANCTIONS_", "ALEPH_")) for pp in p)
        and len({_strip_date(pp) for pp in p}) == 1
    }
    other_dup_groups = {h: p for h, p in dup_groups.items()
                        if h not in zakupki_dup_groups and h not in rescreen_dup_groups}
    if zakupki_dup_groups:
        warnings.append(
            f"{len(zakupki_dup_groups)} byte-identical zakupki attachment group(s) "
            f"under multiple filenames (expected — zakupki.gov.ru itself serves the "
            f"same document under several names; not a data-quality issue). Full list: "
            + " | ".join(f"[{', '.join(p)}]" for p in zakupki_dup_groups.values()))
    if rescreen_dup_groups:
        warnings.append(
            f"{len(rescreen_dup_groups)} byte-identical screening-tool re-pull group(s) "
            f"(OPENSANCTIONS_/ALEPH_, same key, different pull date — expected re-screen "
            f"with no change; not a data-quality issue). Full list: "
            + " | ".join(f"[{', '.join(p)}]" for p in rescreen_dup_groups.values()))
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

    # --- generated relationship graph -------------------------------------
    # The graph is a derived artifact, but it is consumed independently by
    # visualization and analysis tools. Validate it against the live registry
    # so a stale graph cannot quietly reintroduce merged records or invented
    # endpoint/source relationships.
    graph_path = REG / "relationship_graph.json"
    views_path = REG / "relationship_graph_views.json"
    if graph_path.exists():
        try:
            graph = json.loads(graph_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as ex:
            errors.append(f"relationship_graph.json: not valid JSON ({ex})")
        else:
            graph_views = None
            if views_path.exists():
                try:
                    graph_views = json.loads(views_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError as ex:
                    errors.append(f"relationship_graph_views.json: not valid JSON ({ex})")
            military_units_path = REG / "military_units.json"
            military_units = json.loads(military_units_path.read_text(encoding="utf-8")) \
                if military_units_path.exists() else []
            errors.extend(validate_generated_graph(
                graph, graph_views, entities, people or [], sources or [], military_units,
                json.loads((REG / "programs.json").read_text(encoding="utf-8"))
                if (REG / "programs.json").exists() else [],
                json.loads((REG / "products.json").read_text(encoding="utf-8"))
                if (REG / "products.json").exists() else []))
    else:
        errors.append("relationship_graph.json missing — run "
                      "scripts/build_relationship_graph.py")

    # --- guarded-enum downgrade check --------------------------------------
    # Phase 3.5 item 2's still-open half (see notes/rebuild_plan.md): a
    # shape validator alone can't catch a value flipping from one *valid*
    # enum member to another *valid* one — the actual Тримикс regression (a
    # bulk correction sweep silently overwrote a correct 'confirmed_reseller'
    # with 'none_found', both legal values, so no shape check flagged it;
    # only caught by a human noticing the brief and registry disagreed).
    # This compares every guarded field against the last COMMITTED registry
    # (git HEAD) and flags any transition ranked as a downgrade.
    #
    # Deliberately does NOT try to auto-detect "already justified" by
    # scanning correction 'why' text for the field name — tried that first,
    # and it's a false-safety trap: this exact field already carries a
    # 'why' note from the ORIGINAL Тримикс fix (2026-08-25), so a naive
    # substring search would forever suppress detection of a brand-new
    # regression on the very field it exists to protect, the first time
    # this check would matter. So it always warns on a downgrade; a human
    # (or a future session) decides in one glance whether the note above it
    # explains the change or not. Cheap to eyeball, not worth automating
    # further until a real false-positive rate shows up in practice.
    GUARDED_ENUM_RANK = {
        "wb_overlap": {"confirmed_direct": 2, "confirmed_reseller": 2,
                       "none_found": 1, "not_checked": 0},
    }

    def _git_show_json(path: str):
        try:
            out = subprocess.run(["git", "show", f"HEAD:{path}"], cwd=REPO,
                                 capture_output=True, text=True, timeout=10)
            if out.returncode != 0:
                return None
            return json.loads(out.stdout)
        except (json.JSONDecodeError, subprocess.SubprocessError, OSError):
            return None

    head_entities = _git_show_json("data/registry/entities.json")
    if head_entities is not None:
        head_by_slug = {e["slug"]: e for e in head_entities if e.get("slug")}
        for e in entities:
            slug = e.get("slug")
            old = head_by_slug.get(slug)
            if not old:
                continue
            for field, rank in GUARDED_ENUM_RANK.items():
                old_v, new_v = old.get(field), e.get(field)
                if old_v == new_v or old_v not in rank or new_v not in rank:
                    continue
                if rank[new_v] < rank[old_v]:
                    warnings.append(
                        f"{e['name_ru']}: downgrade on guarded field "
                        f"'{field}' ({old_v!r} -> {new_v!r} since the last "
                        f"commit). If this is a deliberate, verified "
                        f"correction with a why[] note explaining it, fine —"
                        f" otherwise this is the Тримикс bug recurring.")

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

    # --- 6b. ЦБСТ's own channel names an entity the registry holds no tie for ---------
    # Added 2026-10-01 after posts 1562/1976/2095 sat unread for weeks (see
    # scripts/tg_post_coverage.py). A warning is a work queue, closed by reading the posts and
    # recording `cbst_channel_review` or a tie, never by deleting the warning.
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import tg_post_coverage
        cov_errors, cov_warnings = tg_post_coverage.registry_warnings(entities)
        errors.extend(cov_errors)
        warnings.extend(cov_warnings)
    except Exception as exc:  # the check must never take the validator down with it
        warnings.append(f"tg_post_coverage could not run: {exc!r}")

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
