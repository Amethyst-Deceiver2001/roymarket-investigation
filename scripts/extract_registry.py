#!/usr/bin/env python3
"""Scaffold data/registry/*.json from the frozen brief snapshot.

This is a ONE-TIME migration aid, not an ongoing pipeline. It reads
`docs/_archive/index-2026-08-21.html` — the frozen single-file brief — and
emits skeleton registry records so that hand-verification starts from
something structured rather than from a 466KB HTML file.

Everything it produces is provisional. Each record carries `_verified: false`
and a `_raw` block holding the original cell text it was derived from, so the
verification pass can check a field against the exact prose it came from
without going back to the HTML. Nothing here is authoritative until a human
has checked it against a primary document in `data/sources/`.

Two things it deliberately does NOT do:

- It does not parse the manufacturers table with an HTML parser. That table is
  malformed in the source (an unclosed `<td colspan="3">` spanning lines
  1026-1051, with `<div class="gallery">` blocks and a 51,007-character
  unclosed `<p>` inside it). Browsers foster-parent it out of the table and it
  renders fine, but no DOM library reconstructs it correctly. Rows there happen
  to be one-per-line in the source, so it is scraped line-wise and the two
  `colspan` catch-all rows are captured separately as open questions.
- It does not invent, infer or normalise. A field it cannot read is null. A
  half-read field keeps its raw text so a human can finish it.

Usage:
    python3 scripts/extract_registry.py            # writes data/registry/
    python3 scripts/extract_registry.py --dry-run  # report only, write nothing
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SNAPSHOT = REPO / "docs" / "_archive" / "index-2026-08-21.html"
OUT_DIR = REPO / "data" / "registry"


def load_corrections(*keys: str) -> dict:
    """Load correction data for the given top-level keys.

    corrections.json was split 2026-08-26 (23k lines / 1.5MB in one file)
    into corrections_entities.json (entities, add_entities) and
    corrections_people.json (people, people_add_entities) — same content,
    just no single file dominating the registry directory. Each split file
    is self-contained (only holds the keys relevant to it), so this just
    reads whichever files exist and merges the requested keys out of them.
    """
    result: dict = {}
    for fname in ("corrections_entities.json", "corrections_people.json"):
        path = OUT_DIR / fname
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for key in keys:
            if key in data:
                result[key] = data[key]
    return result

# Line ranges (1-indexed, inclusive) of each table in the snapshot. Hardcoded
# because the snapshot is frozen — it will never move. Verified against the
# structural survey of 2026-08-22.
TABLES = {
    "deliveries": (729, 742),
    "money": (757, 772),
    "entities": (782, 926),
    "supervisory_board": (934, 947),
    "executives": (952, 968),
    "manufacturers": (980, 1054),
    "digital": (1099, 1111),
    "media": (1151, 1176),
}

RE_TAG = re.compile(r"<[^>]+>")
RE_INN = re.compile(r"\b(\d{10}|\d{12})\b")
RE_OGRN = re.compile(r"\b(\d{13}|\d{15})\b")
RE_TD = re.compile(r"<td[^>]*>(.*?)</td>", re.S)
RE_TR = re.compile(r"<tr[^>]*>(.*?)</tr>", re.S)
RE_COLSPAN_TD = re.compile(r'<td[^>]*colspan="3"[^>]*>', re.I)

# Legal-form prefixes, longest-first so "ООО «НПО ..." matches the outer form.
LEGAL_FORMS = [
    "ФГКУ", "ФГУП", "ФКУ", "ГУП", "МУП", "АНО", "ОАО", "ПАО", "ЗАО",
    "ООО", "АО", "НПЦ", "НПО", "НПП", "ОПКБ", "СКБ", "КБ", "ГК", "ИП",
    "Фонд", "НТЦ", "НИПП", "УЦ", "ЮФ", "ЗПИФ", "УК",
]
# The inner alternation allows ONE level of nested guillemets, so that
# АО «НИИ «Вектор»» yields «НИИ «Вектор»» and not the truncated «НИИ «Вектор».
# The brief has several of these (АО «НПП «Радар ММС», ООО «КБ «Синергия»,
# АО «УК ИНТЦ «Интеллектуальная электроника — Валдай»).
RE_ENTITY = re.compile(
    r"\b(" + "|".join(LEGAL_FORMS) + r")\s*«((?:[^«»]|«[^«»]*»){2,80})»"
)

# Time-variant facts get a dated history array, not just a scalar — the same
# shape `financials[]` already used ({year, revenue, ..., source_id}). A
# director, a founder list, a charter capital figure, a registered address
# and even a legal name (Рационы питания -> Боевые технологии is the model
# case already in the brief) can all change, and EGRUL/Устав pulls are
# snapshots: a later pull must not silently overwrite what an earlier one
# already established happened on a specific date. Each entry:
#   {"value": ..., "as_of": "YYYY-MM-DD" | null, "source_id": "sNNNN" | null,
#    "note": str | null}
# `as_of` is the FACT's effective date (per the document's own content — a
# charter amendment date, an EGRUL extract's issue date), never the date we
# happened to pull or read it. Leave it null rather than guess it from a
# filename or a capture date — see infer_source_type_and_dates(), which
# deliberately keeps `captured_date` and `as_of` as two different fields for
# exactly this reason. The flat scalar field (`director`, `charter_capital`,
# etc.) stays as a display convenience holding the latest known value; the
# `_history` array is the record. Both get populated together once a source
# has actually been read — the scaffold only seeds an unsourced entry when
# the brief states a value with no source_id to attach, so nothing from the
# original text is lost while it waits for verification.
HISTORY_FIELDS = {
    "director": "director_history",
    "charter_capital": "charter_capital_history",
    "facility_type": "facility_type_history",
}

FACILITY_TYPES = {
    "soviet_legacy_defense_industrial",
    "purpose_built_technopark_sez",
    "generic_registered_address",
    "claimed_future_secure_technopark",
    "unknown",
}


def seed_history(entity: dict) -> None:
    """Turn a scaffold's bare scalar into a one-entry, unsourced history.

    Called once, after all extraction and corrections have run. A history
    entry with `source_id: null` is not evidence — it is a placeholder saying
    "the brief asserted this, unverified" so the verification pass has
    somewhere to attach a real source_id instead of starting from nothing.
    """
    for flat_field, hist_field in HISTORY_FIELDS.items():
        value = entity.get(flat_field)
        if value and not entity.get(hist_field):
            entity[hist_field] = [{
                "value": value,
                "as_of": None,
                "source_id": None,
                "note": f"from {entity.get('_origin', 'brief')}, unverified",
            }]


CONFIDENCE_MAP = {"t-doc": "doc", "t-press": "press", "t-open": "open"}

# Which <h2> a prose-mentioned entity sits under, mapped to a registry tier.
# This is provisional classification, not a finding: it says "the brief
# discusses this company in its money-chain section", which is a good default
# and a traceable one, but any individual record can be overridden in
# corrections.json once a human has looked at it.
# h3 wins over h2 where both are known, because the h2 sections are not
# homogeneous: "Physical infrastructure" contains both the co-located
# Нарышкинская shell cluster (plumbing) and the "525 residents" roll-call of
# actual manufacturers.
SECTION_TIER_H3 = {
    "525 residents, and how many of them are under EU sanctions": "manufacturer",
    "The registered address is an office, not a facility": "plumbing",
    "The platform disclaims being a warehouse operator": "plumbing",
    "The real estate is at ЦБСТ level, and it is being dispersed on purpose": "cbst-core",
}
SECTION_TIER_H2 = {
    "The entity map": "money-layer",
    "Who actually makes the goods": "manufacturer",
    "Physical infrastructure: there is deliberately very little": "plumbing",
    "This was a Defence Ministry project from the start": "cbst-core",
    "Digital and operational infrastructure": "plumbing",
}


def strip_tags(s: str) -> str:
    """HTML fragment -> plain text, whitespace-collapsed."""
    s = re.sub(r"<br\s*/?>", " | ", s)
    s = RE_TAG.sub("", s)
    return html.unescape(re.sub(r"\s+", " ", s)).strip()


def confidence_of(fragment: str) -> str | None:
    for cls, level in CONFIDENCE_MAP.items():
        if cls in fragment:
            return level
    return None


def slugify(name: str) -> str:
    """Transliterate a Cyrillic entity/person name into an ASCII slug."""
    table = {
        "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
        "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
        "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
        "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch",
        "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    }
    out = []
    for ch in name.lower():
        if ch in table:
            out.append(table[ch])
        elif ch.isalnum():
            out.append(ch)
        else:
            out.append("-")
    slug = re.sub(r"-+", "-", "".join(out)).strip("-")
    return slug[:60]


def table_source(lines: list[str], key: str) -> str:
    start, end = TABLES[key]
    return "\n".join(lines[start - 1:end])


def rows_of(lines: list[str], key: str) -> list[list[str]]:
    """Well-formed tables only: return each row as a list of raw cell HTML."""
    src = table_source(lines, key)
    out = []
    for tr in RE_TR.findall(src):
        cells = RE_TD.findall(tr)
        if cells:
            out.append(cells)
    return out


# --------------------------------------------------------------------------
# entities
# --------------------------------------------------------------------------

def parse_entities(lines: list[str]) -> tuple[list[dict], list[dict]]:
    """The 'Legal entities' table: Entity | ИНН/ОГРН | Role | Confidence."""
    records, problems = [], []
    for cells in rows_of(lines, "entities"):
        if len(cells) < 3:
            problems.append({"table": "entities", "reason": "short row",
                             "raw": strip_tags(" ".join(cells))[:300]})
            continue
        name = strip_tags(cells[0])
        ids = strip_tags(cells[1])
        role = strip_tags(cells[2])
        conf = confidence_of(cells[3]) if len(cells) > 3 else None

        inns = RE_INN.findall(ids)
        ogrns = RE_OGRN.findall(ids)
        # A 13-digit ОГРН also matches nothing in RE_INN (10/12 only), but a
        # 15-digit ОГРНИП does not collide either. Still, filter defensively.
        inns = [i for i in inns if i not in ogrns]

        m = RE_ENTITY.search(name)
        records.append({
            "slug": slugify(name),
            "name_ru": name,
            "name_latin": None,
            "legal_form": m.group(1) if m else None,
            "brand_ru": None,
            "brand_latin": None,
            "inn": inns[0] if inns else None,
            "ogrn": ogrns[0] if ogrns else None,
            "extra_ids": {"inn": inns[1:], "ogrn": ogrns[1:]} if len(inns) > 1 or len(ogrns) > 1 else None,
            "registered": None,
            "address": None,
            "okved_code": None,
            "okved_label": None,
            "okved_mismatch": None,
            "director": None,
            "director_history": [],
            "founders": [],
            "founders_history": [],
            "charter_capital": None,
            "charter_capital_history": [],
            "address_history": [],
            "name_history": [],
            # Physical-footprint typology (rebuild plan Phase 1.5b) —
            # soviet_legacy_defense_industrial | purpose_built_technopark_sez
            # | generic_registered_address | claimed_future_secure_technopark
            # | unknown. Flat field is a display convenience over the latest
            # entry in facility_type_history, same pattern as director/
            # director_history — each history entry {value, as_of, source_id,
            # note}, populated by hand once an entity's real physical site is
            # resolved (see npc_bas_technopark_network for the known
            # technopark/ОЭЗ shortlist to check against first).
            "facility_type": None,
            "facility_type_history": [],
            "parents": [],
            "subsidiaries": [],
            # The 'Legal entities' table sits under 'The entity map', which is
            # the money/ownership chain. The handful of records that are
            # actually the platform itself (ЦБСТ, МПТМ, Наша Правда and the
            # ЦБСТ-owned subsidiaries) are promoted to cbst-core in
            # corrections.json.
            "tier": "money-layer",
            "tier_basis": "brief section: The entity map (Legal entities table)",
            "cbst_tie": None,
            "wb_overlap": "not_checked",
            "products": [],
            "financials": [],
            "egrul_flags": [],
            "securing_measures": [],
            "securing_measures_checked_at": None,
            "sanctions": [],
            "litigation": [],
            "licences": [],
            "trademarks": [],
            "patents": [],
            "foreign_components": [],
            "government_contracts": [],
            "workforce_history": [],
            "state_programs": [],
            "marketing_claims": [],
            "battlefield_evidence": [],
            "domain_history": [],
            "web": {"sites": [], "telegram": [], "vk": [], "youtube": [],
                    "marketplace_listings": [], "other": []},
            "images": [],
            "open_questions": [],
            "sources": [],
            "confidence": conf,
            "_verified": False,
            "_origin": "brief:legal-entities-table",
            "_raw": {"name": name, "ids": ids, "role": role},
        })
    return records, problems


# --------------------------------------------------------------------------
# manufacturers (malformed table — line-wise, not DOM)
# --------------------------------------------------------------------------

def parse_manufacturers(lines: list[str]) -> tuple[list[dict], list[dict], list[dict]]:
    """Company | Principal | Products and notes, plus two colspan catch-alls.

    Scraped line-wise on purpose. See the module docstring: this table cannot
    be reconstructed by an HTML parser, and a human has to check every row of
    it against primary documents anyway.
    """
    start, end = TABLES["manufacturers"]
    records, catchalls, problems = [], [], []

    for lineno in range(start, end + 1):
        raw = lines[lineno - 1]
        if "<tr>" not in raw or "<th>" in raw:
            continue

        if RE_COLSPAN_TD.search(raw):
            catchalls.append({
                "line": lineno,
                "text": strip_tags(raw)[:4000],
                "_note": "catch-all row inside the manufacturers table; "
                         "split into per-entity/per-product open questions",
            })
            continue

        cells = RE_TD.findall(raw)
        if len(cells) != 3:
            problems.append({"table": "manufacturers", "line": lineno,
                             "reason": f"expected 3 cells, got {len(cells)}",
                             "raw": strip_tags(raw)[:300]})
            continue

        company = strip_tags(cells[0])
        principal = strip_tags(cells[1])
        notes = strip_tags(cells[2])

        # Company cell often carries a parenthetical city and/or ИНН.
        city = None
        cm = re.search(r"\(([^)]*)\)", company)
        if cm:
            inner = cm.group(1)
            if not RE_INN.search(inner) and "." not in inner:
                city = inner.strip()
        name = re.sub(r"\s*\([^)]*\)", "", company).strip()

        inn = RE_INN.search(company + " " + notes)
        ogrn = RE_OGRN.search(company + " " + notes)
        m = RE_ENTITY.search(name)

        products = re.findall(r"«([^»]{2,60})»", notes)

        records.append({
            "slug": slugify(name),
            "name_ru": name,
            "name_latin": None,
            "legal_form": m.group(1) if m else None,
            "brand_ru": None,
            "brand_latin": None,
            "inn": inn.group(1) if inn else None,
            "ogrn": ogrn.group(1) if ogrn else None,
            "registered": None,
            "address": None,
            "city": city,
            "okved_code": None,
            "okved_label": None,
            "okved_mismatch": None,
            "director": principal if principal and principal != "—" else None,
            "director_history": [],
            "founders": [],
            "founders_history": [],
            "charter_capital": None,
            "charter_capital_history": [],
            "address_history": [],
            "name_history": [],
            "facility_type": None,
            "facility_type_history": [],
            "parents": [],
            "subsidiaries": [],
            "tier": "manufacturer",
            "cbst_tie": None,
            "wb_overlap": "not_checked",
            "products": products,
            "financials": [],
            "egrul_flags": [],
            "securing_measures": [],
            "securing_measures_checked_at": None,
            "sanctions": [],
            "litigation": [],
            "licences": [],
            "trademarks": [],
            "patents": [],
            "foreign_components": [],
            "government_contracts": [],
            "workforce_history": [],
            "state_programs": [],
            "marketing_claims": [],
            "battlefield_evidence": [],
            "domain_history": [],
            "web": {"sites": [], "telegram": [], "vk": [], "youtube": [],
                    "marketplace_listings": [], "other": []},
            "images": [],
            "open_questions": [],
            "sources": [],
            "confidence": confidence_of(cells[2]),
            "_verified": False,
            "_origin": f"brief:manufacturers-table:line-{lineno}",
            "_raw": {"company": company, "principal": principal, "notes": notes},
        })
    return records, catchalls, problems


# --------------------------------------------------------------------------
# people
# --------------------------------------------------------------------------

def parse_people(lines: list[str]) -> list[dict]:
    """Supervisory board + executives tables."""
    out = []
    for key, default_role in (("supervisory_board", "ЦБСТ Supervisory Board"),
                              ("executives", None)):
        for cells in rows_of(lines, key):
            if len(cells) < 2:
                continue
            name = strip_tags(cells[0])
            position = strip_tags(cells[1])
            note = strip_tags(cells[2]) if len(cells) > 2 else None
            out.append({
                "slug": slugify(name),
                "fio_ru": name,
                "name_latin": None,
                "dob": None,
                "birthplace": None,
                "address": None,
                "inn_personal": None,
                "roles": [{"entity_slug": None, "title": position,
                           "body": default_role, "from": None, "to": None,
                           "source_id": None}],
                "sanctions": [],
                "other_entities": [],
                "other_entities_checked_at": None,
                "disqualification_hits": [],
                "disqualification_checked_at": None,
                "subsidiary_liability_hits": [],
                "subsidiary_liability_checked_at": None,
                "social": [],
                "photo": None,
                "notes": note,
                "sources": [],
                "_verified": False,
                "_origin": f"brief:{key}-table",
                "_raw": {"name": name, "position": position, "note": note},
            })
    return out


# --------------------------------------------------------------------------
# quotes, open questions, prose identifiers
# --------------------------------------------------------------------------

CYR = r"[А-ЯЁ][а-яё]+(?:-[А-ЯЁ][а-яё]+)?"
PATRONYMIC = r"[А-ЯЁ][а-яё]+(?:вич|вна|ична|ьевич|ьевна|инична)"

# Both orders occur in the brief: registry style (Фамилия Имя Отчество) and
# narrative style (Имя Отчество Фамилия). Capture each with the patronymic
# anchoring the middle position, then normalise to Фамилия Имя Отчество.
RE_FIO_SURNAME_FIRST = re.compile(rf"\b({CYR})\s+({CYR})\s+({PATRONYMIC})\b")
RE_FIO_SURNAME_LAST = re.compile(rf"\b({CYR})\s+({PATRONYMIC})\s+({CYR})\b")

# 12-digit personal ИНН stated near a name.
RE_PERSONAL_INN = re.compile(r"ИНН\s*(\d{12})(?!\d)")
RE_DOB = re.compile(r"\bb\.\s*(\d{2}\.\d{2}\.\d{4}|\d{4})\b")


def parse_people_from_prose(text: str) -> list[dict]:
    """Every named individual in the brief, with role context.

    The two scaffolded tables (supervisory board, executives) hold 21 people;
    the document names roughly nine times that many, scattered through prose
    as directors, founders, owners and beneficiaries. Those are exactly the
    records the screening pass needs, so they are extracted here rather than
    left to be re-read out of the HTML by hand.

    Nothing is asserted beyond "this name appears here, in this context" —
    role, entity and any identifier stay as captured text for a human to
    confirm.
    """
    plain = strip_tags(text)
    found: dict[str, dict] = {}

    def add(surname: str, given: str, patronymic: str, pos: int) -> None:
        fio = f"{surname} {given} {patronymic}"
        lo, hi = max(0, pos - 200), min(len(plain), pos + 260)
        ctx = plain[lo:hi]
        rec = found.get(fio)
        if rec is None:
            inn_m = RE_PERSONAL_INN.search(ctx)
            dob_m = RE_DOB.search(ctx)
            rec = {
                "slug": slugify(fio),
                "fio_ru": fio,
                "name_latin": None,
                "dob": dob_m.group(1) if dob_m else None,
                "birthplace": None,
                "address": None,
                "inn_personal": inn_m.group(1) if inn_m else None,
                "roles": [],
                "sanctions": [],
                "other_entities": [],
                "other_entities_checked_at": None,
                "disqualification_hits": [],
                "disqualification_checked_at": None,
                "subsidiary_liability_hits": [],
                "subsidiary_liability_checked_at": None,
                "social": [],
                "photo": None,
                "notes": None,
                "sources": [],
                "mentions": 0,
                "_verified": False,
                "_origin": "brief:prose",
                "_raw": {"contexts": []},
            }
            found[fio] = rec
        rec["mentions"] += 1
        if len(rec["_raw"]["contexts"]) < 3:
            rec["_raw"]["contexts"].append(ctx)
        # Entities named in the same window are role candidates, not facts.
        for form, nm in RE_ENTITY.findall(ctx):
            cand = f"{form} «{nm}»"
            role_slugs = [r.get("entity_name") for r in rec["roles"]]
            if cand not in role_slugs:
                rec["roles"].append({
                    "entity_slug": None,
                    "entity_name": cand,
                    "title": None,
                    "from": None, "to": None,
                    "source_id": None,
                    "_candidate": True,
                })

    for m in RE_FIO_SURNAME_FIRST.finditer(plain):
        add(m.group(1), m.group(2), m.group(3), m.start())
    for m in RE_FIO_SURNAME_LAST.finditer(plain):
        add(m.group(3), m.group(1), m.group(2), m.start())

    return sorted(found.values(), key=lambda r: -r["mentions"])


def parse_quotes(text: str) -> list[dict]:
    out = []
    for i, m in enumerate(re.finditer(
            r"<blockquote[^>]*>(.*?)</blockquote>", text, re.S), 1):
        body = m.group(1)
        cite = re.search(r"<cite[^>]*>(.*?)</cite>", body, re.S)
        quote = strip_tags(re.sub(r"<cite[^>]*>.*?</cite>", "", body, flags=re.S))
        out.append({
            "id": f"q{i:03d}",
            "text_ru": quote,
            "speaker": None,
            "source_id": None,
            "date": None,
            "translation_en": None,
            "cite_raw": strip_tags(cite.group(1)) if cite else None,
            "_verified": False,
        })
    return out


def parse_global_open_questions(lines: list[str], text: str) -> list[dict]:
    """The 'What is not established' list + the 'still unmined' source cards."""
    out = []
    sec = text.split('<h2>What is not established</h2>')
    if len(sec) > 1:
        for i, li in enumerate(re.findall(r"<li>(.*?)</li>", sec[1], re.S), 1):
            out.append({"id": f"oq{i:03d}", "scope": "global",
                        "text": strip_tags(li), "entity_slug": None,
                        "person_slug": None,
                        "_origin": "brief:what-is-not-established"})
    for i, card in enumerate(re.findall(
            r'<div class="card"><h4>(.*?)</h4><p>(.*?)</p></div>', text, re.S), 1):
        out.append({"id": f"src{i:03d}", "scope": "unmined-source",
                    "text": f"{strip_tags(card[0])} — {strip_tags(card[1])}",
                    "entity_slug": None, "person_slug": None,
                    "_origin": "brief:data-sources-still-unmined"})
    return out


def attribute_open_questions(open_qs: list[dict], entities: list[dict],
                              people: list[dict]) -> None:
    """Best-effort, conservative entity_slug/person_slug attribution for the
    global open_questions.json store, run once entities/people are final.

    Only ever sets a slug on an UNAMBIGUOUS match — a guillemet-quoted entity
    name («Инвестментс») or a full Cyrillic ФИО substring, each checked
    against every entity/person so a match that hits more than one record
    (e.g. «Азимут», which genuinely names two different registry entities)
    is left unset rather than guessed. This mirrors the project's standing
    discipline elsewhere (wb_overlap, reverse_source_index) of only ever
    recording a match strength the data actually supports — a null here is
    honest ("not established which one"), not a gap in the tooling.

    Deliberately does NOT attempt transliterated-name matching (English
    "Medvedev" against Cyrillic "Медведев") — a surname-only match across
    scripts is exactly the kind of guess this project's PII/attribution
    discipline exists to prevent (a namesake risk, not a resolved reference).
    """
    guillemet_re = re.compile(r"«([^»]+)»")
    entity_names: dict[str, list[str]] = {}
    for e in entities:
        for name in guillemet_re.findall(e.get("name_ru") or ""):
            entity_names.setdefault(name, []).append(e["slug"])
    person_names: dict[str, list[str]] = {}
    for p in people:
        fio = p.get("fio_ru")
        if fio:
            person_names.setdefault(fio, []).append(p["slug"])

    for oq in open_qs:
        text = oq.get("text") or ""
        entity_hits = {slug for name, slugs in entity_names.items()
                       if name in text for slug in slugs}
        person_hits = {slug for name, slugs in person_names.items()
                       if name in text for slug in slugs}
        if len(entity_hits) == 1 and not person_hits:
            oq["entity_slug"] = next(iter(entity_hits))
        elif len(person_hits) == 1 and not entity_hits:
            oq["person_slug"] = next(iter(person_hits))


RE_REGDATE = re.compile(
    r"(?:reg\.|registered|зарегистрирован[оа]?)\s*(\d{2}\.\d{2}\.\d{4})", re.I)
RE_OKVED = re.compile(r"(?:OKVED|ОКВЭД)\s*[:\s]*(\d{2}(?:\.\d{1,2}){0,2})", re.I)

# Cities that appear as the bare second element of an identifier parenthetical.
CITY_HINT = re.compile(
    r"\b(Moscow|Москва|St\.? ?Petersburg|Санкт-Петербург|Kazan|Казань|"
    r"Tomsk|Томск|Ulyanovsk|Ульяновск|Khabarovsk|Хабаровск|Vologda|Вологда|"
    r"Lipetsk|Липецк|Smolensk|Смоленск|Taganrog|Таганрог|Kemerovo|Кемерово|"
    r"Nizhny Novgorod|Нижний Новгород|Krasnodar|Краснодар|Penza|Пенза|"
    r"Yoshkar-Ola|Йошкар-Ола|Zhukovsky|Жуковский|Novgorod|Новгород|Tula|Тула|"
    r"Murmansk|Мурманск|Ivanovo|Иваново|Kursk|Курск|Izhevsk|Ижевск)\b")


def parse_prose_identifiers(text: str) -> tuple[list[dict], list[dict]]:
    """Extract entity records from prose ИНН mentions.

    The brief states identifiers in a consistent shape — «Brand» is
    ООО «Legal Name» (ИНН NNNNNNNNNN, City, reg. DD.MM.YYYY, OKVED NN.NN) —
    which is worth parsing properly rather than leaving ~105 entities as loose
    leads for a human to re-read out of a 466KB file.

    Attribution rule: the entity named immediately before the ИНН, within 30
    characters. That tight window is deliberate — it is the difference between
    "the company this number belongs to" and "some company mentioned nearby".
    Anything that fails it is returned as an unattributed lead instead of being
    guessed at.

    Returns (records, unattributed_leads).
    """
    # Map character offsets in the plain text to the <h2> section they fall
    # under, so a prose-derived entity can be tiered by WHERE the brief
    # discusses it rather than by guesswork. The brief is organised by
    # question — the money chain, the supply side, the platform itself — so
    # section membership is a real signal, and a traceable one.
    plain = strip_tags(text)
    section_marks: list[tuple[int, str, int]] = []
    for level in (2, 3):
        for h in re.finditer(rf"<h{level}>(.*?)</h{level}>", text, re.S):
            heading = strip_tags(h.group(1))
            pos = plain.find(heading)
            if pos >= 0:
                section_marks.append((pos, heading, level))
    section_marks.sort()

    def section_at(pos: int) -> tuple[str | None, str | None]:
        """Return (h2, h3) in force at this offset. h3 resets on a new h2."""
        h2 = h3 = None
        for start, heading, level in section_marks:
            if start > pos:
                break
            if level == 2:
                h2, h3 = heading, None
            else:
                h3 = heading
        return h2, h3

    seen: set[str] = set()
    records, leads = [], []

    # 12 before 10, and an explicit right-boundary. Without both, a 12-digit
    # personal ИНН is silently truncated to a 10-digit legal-entity one that
    # looks valid but belongs to nobody — which is how Яныкина's and
    # Бровченко's personal ИНН were briefly attributed to АНО «ЦБСТ» and
    # Фонд «Наша Правда».
    for m in re.finditer(r"ИНН[:\s]*(\d{12}|\d{10})(?!\d)", plain):
        inn = m.group(1)
        if inn in seen:
            continue
        seen.add(inn)

        # A 12-digit ИНН belongs to a natural person or a sole proprietor.
        # Only an ИП record may carry one; anything else is a person lead.
        if len(inn) == 12:
            lo12 = max(0, m.start() - 200)
            near = plain[lo12:m.start()]
            if not re.search(r"\bИП\s", near[-40:]):
                leads.append({
                    "inn": inn,
                    "context": plain[lo12:min(len(plain), m.end() + 160)],
                    "entity_guess": [],
                    "_reason": "12-digit ИНН — belongs to an individual; "
                               "assign to people.json, not an entity",
                    "_verified": False,
                })
                continue

        lo = max(0, m.start() - 200)
        left = plain[lo:m.start()]
        window = plain[lo:min(len(plain), m.end() + 200)]

        name_matches = list(RE_ENTITY.finditer(left))
        gap = (m.start() - (lo + name_matches[-1].end())) if name_matches else 999

        if not name_matches or gap > 30:
            leads.append({
                "inn": inn,
                "context": window,
                "entity_guess": [f"{a} «{b}»" for a, b in RE_ENTITY.findall(window)],
                "_reason": "no entity named within 30 chars before the ИНН",
                "_verified": False,
            })
            continue

        nm = name_matches[-1]
        name = f"{nm.group(1)} «{nm.group(2)}»"

        # Secondary attributes (ОГРН, reg date, ОКВЭД, city) are only taken
        # from the SAME parenthetical the ИНН sits in. Without this guard the
        # scan runs on past the closing bracket and picks up the next
        # company's identifiers — which it did, e.g. assigning КРАВТ
        # УДМУРТИЯ's registration date to ООО «СПДББК».
        paren = None
        left_tail = plain[max(0, m.start() - 120):m.start()]
        inside_paren = left_tail.rfind("(") > left_tail.rfind(")")
        if inside_paren:
            tail = plain[m.end():m.end() + 220]
            if ")" in tail:
                candidate = tail.split(")")[0]
                # A new «name» or a second ИНН inside the tail means the
                # bracket did not close where we think it did.
                if "«" not in candidate and not re.search(r"ИНН", candidate):
                    paren = candidate

        ogrn_m = RE_OGRN.search(paren) if paren else None
        reg_m = RE_REGDATE.search(paren) if paren else None
        okved_m = RE_OKVED.search(paren) if paren else None
        city_m = CITY_HINT.search(paren) if paren else None

        records.append({
            "inn": inn,
            "name_ru": name,
            "legal_form": nm.group(1),
            "ogrn": ogrn_m.group(1) if ogrn_m else None,
            "registered": reg_m.group(1) if reg_m else None,
            "okved_code": okved_m.group(1) if okved_m else None,
            "city": city_m.group(1) if city_m else None,
            "section_h2": section_at(m.start())[0],
            "section_h3": section_at(m.start())[1],
            "context": window,
        })

    return records, leads


# --------------------------------------------------------------------------
# sources
# --------------------------------------------------------------------------

# Filename -> (doc type, fiscal/filing year if any). Covers the two naming
# eras in data/sources/: the CLAUDE.md archiving convention adopted
# 2026-08-17 (<TYPE>_<INN-or-OGRN>_<YYYYMMDD>_<slug>.<ext>) going forward,
# and older filenames that predate it and were never renamed.
SOURCE_TYPE_PATTERNS = [
    (re.compile(r"^РЕСУРС_БФО_(\d+)_(\d{4})_(\d{8})"), "bfo"),
    (re.compile(r"^UD_"), "ustav"),
    # Checked BEFORE the bare "EGRUL_" pattern below, since "EGRULAPI_" would
    # otherwise also match r"^EGRUL_"... it wouldn't (no trailing underscore
    # right after EGRUL in "EGRULAPI_"), but keeping the more specific
    # pattern first is the safer habit regardless.
    (re.compile(r"^EGRULAPI_"), "egrul_api"),  # scripts/egrul_batch_pull.py —
    # the open egrul.nalog.ru lookup (name/ИНН/ОГРН/director/reg date only),
    # lighter-weight than a full signed EGRUL PDF extract (no founder list,
    # no ОКВЭД) — kept as a distinct type so the two aren't conflated when
    # judging how much a source actually establishes.
    (re.compile(r"^EGRUL_"), "egrul"),
    (re.compile(r"^EGRIP_"), "egrul"),   # sole-proprietor extract, same family
    (re.compile(r"^RMSP_", re.I), "rmsp"),  # small-business-registry extract
    (re.compile(r"^COURT_"), "court"),
    (re.compile(r"^A\d{2}-\d+"), "court"),   # bare kad.arbitr case numbers
    (re.compile(r"^TRANSCRIPT_"), "transcript"),
    (re.compile(r"^LAW_"), "sanctions_legal_basis"),  # rebuild plan Phase 1.5c
    (re.compile(r"^DATASET_"), "reference_dataset"),  # open-data-portal
    # catalogues kept for future cross-referencing, not entity-specific —
    # see rebuild plan Phase 1.5a (DATASET_REGISTRY_2026-08-15_...csv:
    # 7,050 rows, only 6 carry any ИНН, 0 overlap with the registry at
    # first check — kept anyway per explicit user instruction).
    (re.compile(r"^ul-\d+"), "egrul"),   # pre-convention EGRUL PDF naming
    (re.compile(r"^LICENSE_"), "license_extract"),  # Rosobrnadzor/other
    # regulator licence-registry extracts (e.g. an educational licence) —
    # distinct from EGRUL: states a licensed ACTIVITY, not corporate identity.
    (re.compile(r"^QUALIFICATION_"), "qualification_standard"),  # an entity's
    # own filed professional-qualification/КИМ content on a sectoral platform
    # (e.g. rk.2035.university) -- entity-specific evidence of what it
    # actually teaches/trains, not a cross-entity template like a Устав.
    (re.compile(r"^HimeraSearch-"), "osint_leak_aggregator"),  # a Химера-style
    # person dossier assembled from breached/leaked Russian consumer, courier,
    # banking, Rosreestr and tax-service datasets — not a government registry
    # or a primary filing. Individual fields (ИНН, DOB, address) are still
    # citable once cross-checked against an independent identifier already on
    # the person's record, same discipline as any other secondary aggregator
    # (OpenSanctions, Aleph) — but the source itself is never `t-doc` tier.
]

RE_FILENAME_DATE = re.compile(r"_(\d{8})(?:_|\.)")
RE_FILENAME_YEAR = re.compile(r"_(\d{4})_\d{8}")


def infer_source_type_and_dates(fname: str) -> tuple[str | None, str | None, str | None]:
    """(doc_type, captured_date, fiscal_year) guessed from the filename alone.

    `captured_date` is when the document was PULLED — reliable whenever the
    filename carries a YYYYMMDD stamp, since every recent pull follows the
    CLAUDE.md `<TYPE>_<ID>_<YYYYMMDD>_<slug>` convention. It is NOT the same
    thing as the document's own effective date (an EGRUL extract states data
    "as of" its issue date, which is usually the same day it was pulled; a
    Устав amendment or a БФО filing states an effective/fiscal date that can
    be much earlier) — that distinction is `as_of` on the registry record,
    filled by a human who has actually read the document, not guessed here.
    """
    doc_type = None
    for pattern, t in SOURCE_TYPE_PATTERNS:
        if pattern.match(fname):
            doc_type = t
            break

    year_m = RE_FILENAME_YEAR.search(fname)
    fiscal_year = year_m.group(1) if year_m else None

    date_m = RE_FILENAME_DATE.search(fname)
    captured = None
    if date_m:
        raw = date_m.group(1)
        captured = f"{raw[0:4]}-{raw[4:6]}-{raw[6:8]}"

    return doc_type, captured, fiscal_year


def load_stable_source_ids() -> dict[str, str]:
    """path -> id, persisted in data/registry/_source_ids.json.

    IDs must be stable across regenerations because corrections.json hand-
    writes source_id references directly into entities.json/people.json
    history entries — a citation, not a display convenience. The old scheme
    (`id = f"s{i:04d}"` where i was MANIFEST.md's line index) looked stable
    but was not: MANIFEST.md's rows are sorted alphabetically by filename
    (scan_sources.py), so adding even one new file anywhere before an
    existing file in sort order silently reassigns every ID after it to a
    DIFFERENT file. Found 2026-08-22: 7 new files added mid-session shifted
    s0231 from ЦБСТ's own EGRUL extract to an unrelated document, silently
    invalidating a source_id just hand-verified and written into
    corrections.json minutes earlier. This is worse than a missing
    source_id — a citation that resolves to the wrong document reads as
    verified when it is not, exactly the "wrong identifier is a serious
    defect, not a typo" failure class check_registry.py's ИНН-checksum
    check already exists to catch for identifiers, now extended to sources.

    Fix: assign each path an ID once, persist the mapping, and never reuse
    or reassign an ID even if the file set changes — append-only, keyed by
    path (not by position).
    """
    path = OUT_DIR / "_source_ids.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def save_stable_source_ids(mapping: dict[str, str]) -> None:
    (OUT_DIR / "_source_ids.json").write_text(
        json.dumps(mapping, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")


def parse_sources(ogrn_to_inn: dict[str, str] | None = None) -> list[dict]:
    """Seed sources.json from the generated MANIFEST.md.

    Every record separates WHEN we pulled the document (`captured_date`,
    inferred from the filename where the naming convention encodes it) from
    WHEN the document's content is actually true as of (`as_of`, left null —
    reading the document is a human verification step, not something a
    filename can tell you). The two dates matter for different things: a
    БФО filing pulled 2026-08-21 might report on fiscal year 2024; a Устав
    pulled the same day might record ownership as it stood after a 2024
    charter amendment. Neither is "the pull date" and the schema must not
    collapse them into one field, or "director as of the founding docs"
    silently becomes "director as of whenever we happened to download this."

    Reads `data/registry/_source_content_cache.json` if present — built by
    `scripts/inventory_sources.py`, which actually opens each file (pdftotext/
    zip/xlsx) to find its type and `as_of` where the filename alone can't say.
    Run that script first (or after adding new files to data/sources/) for
    full coverage; this function still works without it, just with less of
    `as_of` filled in.

    IDs are stable across runs — see load_stable_source_ids() — a new file
    gets the next never-reused number; an existing file keeps the ID it was
    first assigned, regardless of where it now sorts in MANIFEST.md.
    """
    manifest = REPO / "data" / "sources" / "MANIFEST.md"
    if not manifest.exists():
        return []

    cache_path = OUT_DIR / "_source_content_cache.json"
    content_cache = (json.loads(cache_path.read_text(encoding="utf-8"))
                     if cache_path.exists() else {})

    id_map = load_stable_source_ids()
    next_id = max((int(v[1:]) for v in id_map.values()), default=0) + 1

    out = []
    for i, line in enumerate(manifest.read_text(encoding="utf-8").splitlines()):
        if not line.startswith("|") or line.startswith("|--") or "ИНН" in line[:40]:
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) < 2 or cols[0] in ("File", ""):
            continue
        fname = re.sub(r"^`|`$", "", cols[0])
        if fname == "MANIFEST.md":
            continue
        inns = RE_INN.findall(" ".join(cols[1:]))
        doc_type, captured, fiscal_year = infer_source_type_and_dates(fname)
        as_of, as_of_method = None, None

        # БФО filings report position as of fiscal year-end — a formulaic
        # derivation, not a document read: no content cache lookup needed.
        if doc_type == "bfo" and fiscal_year:
            as_of, as_of_method = f"{fiscal_year}-12-31", "bfo:fiscal-year-end"

        # An egrul_api pull is a live lookup, not a stamped document — its
        # "as of" IS the day it was queried (unlike a full EGRUL PDF
        # extract, which carries its own separate "по состоянию на" date
        # that can differ from the pull date). captured_date already comes
        # from the same filename YYYYMMDD segment, so this is definitional,
        # not inferred.
        elif doc_type == "egrul_api" and captured:
            as_of, as_of_method = captured, "egrul_api:pull-date"

        # scripts/inventory_sources.py has actually read the remaining
        # files (pdftotext/zip content) and cached what it found — type
        # for whatever the filename alone couldn't tell, as_of wherever
        # the document states its own effective date. The cache never
        # overrides a filename-derived value, only fills a gap.
        cached = content_cache.get(fname)
        sha256 = None
        if cached:
            doc_type = doc_type or cached.get("type")
            if not as_of and cached.get("as_of"):
                as_of = cached["as_of"]
                as_of_method = cached.get("as_of_method")
            sha256 = cached.get("sha256")

        path_key = f"data/sources/{fname}"
        sid = id_map.get(path_key)
        if sid is None:
            sid = f"s{next_id:04d}"
            id_map[path_key] = sid
            next_id += 1

        out.append({
            "id": sid,
            "type": doc_type,
            "path": path_key,
            "url": None,
            "captured_date": captured,
            "fiscal_year": fiscal_year,
            "as_of": as_of,
            "as_of_method": as_of_method,
            "supersedes": None,
            "superseded_by": None,
            "inns": sorted(set(inns)),
            "entities": [],
            "sha256": sha256,
            "_verified": False,
            "_origin": "manifest",
        })
    link_source_versions(out, ogrn_to_inn or {})
    save_stable_source_ids(id_map)
    return out


# Source types where a later pull genuinely supersedes an earlier one as
# "the current state of this fact" — a fresh EGRUL lookup for the same ИНН
# is a new version of the same claim (director/name/status as of today),
# unlike e.g. a БФО filing, where different fiscal years are legitimately
# different documents rather than versions of one fact and must not be
# chained.
VERSIONED_TYPES = {"egrul", "egrul_api"}

# Filename-encoded subject identifier for a versioned source — deliberately
# NOT the same as the `inns` field (full-text ИНН mentions anywhere in the
# document, which for an EGRUL extract routinely includes a registrar's or
# an unrelated referenced entity's ИНН too, not just the subject's own).
# Grouping by filename subject caught a real bug: three unrelated EGRUL
# extracts happened to all mention the same third-party ИНН in their body
# text and were being chained together as "versions of one entity" by an
# earlier, text-scan-based implementation.
RE_SUBJECT_INN_PREFIXED = re.compile(r"^(?:EGRULAPI|EGRUL|EGRIP)_(\d{10,12})_")
RE_SUBJECT_INN_BARE = re.compile(r"^(\d{10,12})_\d{8}\.")
RE_SUBJECT_OGRN = re.compile(r"^ul-(\d{13,15})-")


def extract_subject_id(fname: str) -> tuple[str, str] | None:
    """(kind, value) — kind is 'inn' or 'ogrn' — for the entity a versioned
    EGRUL-family source is actually ABOUT, read off the filename convention
    rather than scanned from document text (see VERSIONED_TYPES docstring)."""
    for pat in (RE_SUBJECT_INN_PREFIXED, RE_SUBJECT_INN_BARE):
        m = pat.match(fname)
        if m:
            return ("inn", m.group(1))
    m = RE_SUBJECT_OGRN.match(fname)
    if m:
        return ("ogrn", m.group(1))
    return None


def link_source_versions(sources: list[dict], ogrn_to_inn: dict[str, str]) -> None:
    """Chain supersedes/superseded_by across pulls of the same entity,
    ordered by captured_date. Mutates `sources` in place. Pre-convention
    EGRUL PDFs are named by ОГРН (`ul-<ogrn>-<timestamp>.pdf`); the newer
    `egrul_api`/`EGRUL_` convention is named by ИНН — `ogrn_to_inn` (built
    from the parsed entity records, which carry both) lets an ОГРН-named
    pull and an ИНН-named pull of the same entity land in the same chain
    instead of two disconnected singletons."""
    by_subject: dict[str, list[dict]] = {}
    for s in sources:
        if s["type"] not in VERSIONED_TYPES:
            continue
        fname = s["path"].rsplit("/", 1)[-1]
        subj = extract_subject_id(fname)
        if subj is None:
            continue
        kind, value = subj
        if kind == "ogrn":
            value = ogrn_to_inn.get(value, f"ogrn:{value}")
        by_subject.setdefault(value, []).append(s)

    for key, group in by_subject.items():
        if len(group) < 2:
            continue
        # Stable sort: captured_date (falls back to source id order for
        # same-day pulls, which is chronological-enough for a same-day tie).
        group.sort(key=lambda s: (s["captured_date"] or "", s["id"]))
        for prev, nxt in zip(group, group[1:]):
            if prev["id"] == nxt["id"]:
                continue
            nxt["supersedes"] = prev["id"]
            prev["superseded_by"] = nxt["id"]


# --------------------------------------------------------------------------
# Carry-forward: this is a full regeneration from the archived scaffold +
# corrections.json, so it has no memory of screening scripts (screen_rom.py,
# screen_opensanctions.py, screen_aleph.py, etc.) that wrote fetched data
# directly onto a previous entities.json/people.json between runs. Bug found
# 2026-08-22: re-running this after a screen_rom.py sweep silently wiped
# securing_measures_checked_at on every entity. Fetched data must be carried
# forward before overwriting, the same way corrections.json is applied last so
# a verified fix is never silently reverted by regeneration.
#
# (field_to_copy, gate_field) pairs -- gate_field's presence on the prior
# record is what signals "this sweep actually ran"; field_to_copy is the list
# it wrote (None when the gate field is itself the only payload, as with
# _egrul_crosschecked).
ENTITY_CARRY_FORWARD_FIELDS: list[tuple[str | None, str]] = [
    ("securing_measures", "securing_measures_checked_at"),
    (None, "_egrul_crosschecked"),
    ("opensanctions_matches", "opensanctions_screened_at"),
    ("aleph_matches", "aleph_screened_at"),
    ("gur_matches", "gur_screened_at"),
    ("gur_components_matches", "gur_components_screened_at"),
    ("rospatent_director_matches", "rospatent_director_screened_at"),
    ("rk2035_matches", "rk2035_screened_at"),
    ("wb_matches", "wb_screened_at"),
    ("rnp_matches", "rnp_screened_at"),
    ("rmsp_hit", "rmsp_checked_at"),
    ("fas_br_hit_count", "fas_br_checked_at"),
    ("fsa_cert_hit_count", "fsa_checked_at"),
    ("fsa_decl_hit_count", "fsa_checked_at"),
    ("checko_status", "checko_checked_at"),
    ("checko_section_counts", "checko_checked_at"),
    ("reestr_digital_hit_count", "reestr_digital_checked_at"),
    ("reestr_digital_excluded_count", "reestr_digital_checked_at"),
]
PEOPLE_CARRY_FORWARD_FIELDS: list[tuple[str | None, str]] = [
    ("other_entities", "other_entities_checked_at"),
    ("disqualification_hits", "disqualification_checked_at"),
    ("subsidiary_liability_hits", "subsidiary_liability_checked_at"),
    ("opensanctions_matches", "opensanctions_screened_at"),
    ("aleph_matches", "aleph_screened_at"),
    ("leader_id_matches", "leader_id_screened_at"),
]


def _load_prev_registry_file(path: Path) -> list[dict]:
    """Load a prior registry JSON file for carry-forward matching.

    A missing file just means nothing to carry forward (first run) -- fine.
    A file that EXISTS but fails to parse is a different situation: it almost
    certainly means real, hard-won screening data (sanctions matches, EGRUL
    cross-checks, etc.) is sitting on disk and currently unreadable. Silently
    treating that as "nothing to carry forward" (the previous behaviour --
    a bare `except Exception: prev_by_x = {}`) would regenerate right over it
    and destroy it with no trace. Abort loudly instead.
    """
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as ex:
        sys.exit(
            f"ABORT: {path} exists but failed to parse ({ex}) -- refusing to "
            f"regenerate over it. That file may hold screening data "
            f"(sanctions matches, EGRUL cross-checks, securing-measures "
            f"history, etc.) that a silent skip would destroy. Fix or "
            f"restore {path} before re-running."
        )


def carry_forward_screening_fields(
    current: list[dict], prev: list[dict],
    fields: list[tuple[str | None, str]],
    secondary_key: str | None = None,
) -> None:
    """Copy screened/fetched-data fields from a prior registry generation onto
    the freshly-scaffolded current one.

    Matches primarily by **slug** -- the stable, intentional identity this
    project already uses everywhere else (corrections.json is keyed by it,
    related_entities points to it, etc.) -- falling back to `secondary_key`
    (ИНН, for entities) only when the slug match misses.

    This fixes two silent-loss modes the ИНН-only version had:
      - Entities with no ИНН at all (7 of 148, e.g. `ooo-pokrov` before its
        ИНН was resolved) could never carry anything forward, because the
        match map was built by filtering `if e.get("inn")` -- an entity
        without one was simply invisible to it.
      - A corrections.json fix to a transposed or previously-missing ИНН
        changes the value between runs. A pure-ИНН match then fails to find
        the prior record under its old key and drops its screening history
        with no warning -- exactly the kind of loss `check_registry.py`'s
        checksum discipline exists to catch elsewhere in this project.

    Also detects and reports the inverse failure: a prior record that DID
    carry screening data but matches nothing in the freshly-scaffolded set
    (a slug that vanished, an ИНН that changed on both ends at once, etc.)
    would previously drop that data with zero trace. That is now a loud
    stderr warning naming the lost record, not a silent gap.
    """
    prev_by_slug = {p["slug"]: p for p in prev if p.get("slug")}
    prev_by_secondary = (
        {p[secondary_key]: p for p in prev if p.get(secondary_key)}
        if secondary_key else {}
    )

    matched_prev_slugs: set[str] = set()
    for record in current:
        candidate = prev_by_slug.get(record.get("slug"))
        if candidate is None and secondary_key:
            candidate = prev_by_secondary.get(record.get(secondary_key))
        if candidate is None:
            continue
        if candidate.get("slug"):
            matched_prev_slugs.add(candidate["slug"])
        for data_field, gate_field in fields:
            if candidate.get(gate_field):
                if data_field:
                    record[data_field] = candidate.get(data_field, [])
                record[gate_field] = candidate.get(gate_field)

    lost = []
    for p in prev:
        slug = p.get("slug")
        if slug and slug in matched_prev_slugs:
            continue
        if any(p.get(gate_field) for _, gate_field in fields):
            lost.append(slug or p.get("inn") or p.get("fio_ru") or "?")
    if lost:
        shown = ", ".join(lost[:20])
        more = f" (+{len(lost) - 20} more)" if len(lost) > 20 else ""
        print(
            f"  WARNING: {len(lost)} prior record(s) with screening data have "
            f"NO match in the freshly-scaffolded set -- their screening "
            f"history is about to be dropped: {shown}{more}",
            file=sys.stderr,
        )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true",
                    help="report counts, write nothing")
    args = ap.parse_args()

    if not SNAPSHOT.exists():
        print(f"error: snapshot not found at {SNAPSHOT}", file=sys.stderr)
        return 1

    text = SNAPSHOT.read_text(encoding="utf-8")
    lines = text.split("\n")

    ents, ent_problems = parse_entities(lines)
    mans, catchalls, man_problems = parse_manufacturers(lines)
    people = parse_people(lines)
    prose_people = parse_people_from_prose(text)

    # Table people win — their role and position are stated, not inferred.
    # Prose records fill in everyone the two tables never covered, and top up
    # a table person's identifiers where the table had none.
    people_by_slug = {p["slug"]: p for p in people}
    people_added = 0
    for pp in prose_people:
        existing = people_by_slug.get(pp["slug"])
        if existing is None:
            people.append(pp)
            people_by_slug[pp["slug"]] = pp
            people_added += 1
            continue
        for field in ("dob", "inn_personal", "birthplace"):
            if pp.get(field) and not existing.get(field):
                existing[field] = pp[field]
        existing["mentions"] = pp.get("mentions", 0)
        existing.setdefault("_raw", {})["contexts"] = pp["_raw"]["contexts"]

    # Hand-made corrections for people.json — same principle as the
    # "entities" block below (applied last so a verified fix, e.g. clearing
    # a mis-extracted inn_personal, is never silently reverted by the next
    # regeneration). Needed because parse_people_from_prose() re-derives
    # inn_personal fresh from source text every run — a JSON-only edit does
    # NOT survive re-running this script, unlike entities.json corrections.
    # Bug found 2026-08-22: a proximity-matching bug attaches a nearby
    # person's ИНН to two different names in the same paragraph; fixing it
    # by editing people.json directly silently reverted on the next run.
    corr_people = load_corrections("people", "people_add_entities")
    if corr_people:
        # people.add_entities: same principle as entities.add_entities above
        # — a person who exists ONLY in a freshly-read primary document (e.g.
        # a Минюст filing's governing-body roster) was never scaffolded from
        # docs/index.html prose, so a 'set' correction has no record to find.
        # Must run before people_by_slug is used by the 'set' loop below.
        blank_p = {k: ([] if isinstance(v, list) else ({} if isinstance(v, dict) else None))
                   for k, v in (people[0].items() if people else [])}
        for extra in (corr_people.get("people_add_entities") or []):
            existing = people_by_slug.get(extra.get("slug"))
            if existing is not None:
                # Bug fixed 2026-09-02: this branch used to unconditionally
                # append a new record and only repoint people_by_slug at it,
                # leaving the original prose-derived record sitting in the
                # `people` list too — two dicts, same slug, both surviving
                # to people.json (caught by check_registry.py's duplicate-
                # slug warning on sinelshchikov-andrey-valentinovich and
                # saidov-adil-abukovich). Merge into the existing record
                # instead: fill blank scalar/dict fields, concatenate list
                # fields (roles, sources, open_questions) without
                # duplicating identical entries, append notes rather than
                # overwrite.
                for k, v in extra.items():
                    if k in ("why", "slug"):
                        continue
                    if isinstance(v, list):
                        cur = existing.get(k) or []
                        for item in v:
                            if item not in cur:
                                cur.append(item)
                        existing[k] = cur
                    elif k == "notes":
                        old = existing.get("notes") or ""
                        if v and v not in old:
                            existing["notes"] = (old + "\n\n" + v) if old else v
                    elif not existing.get(k):
                        existing[k] = v
                existing["_corrected"] = extra.get("why")
                continue
            rec = dict(blank_p)
            rec.update({"_verified": False, "_origin": "corrections:add_entities"})
            rec.update({k: v for k, v in extra.items() if k != "why"})
            rec["_corrected"] = extra.get("why")
            people.append(rec)
            people_by_slug[rec["slug"]] = rec

        for slug, spec in (corr_people.get("people") or {}).items():
            target = people_by_slug.get(slug)
            if target is None:
                man_problems.append({"table": "corrections",
                                     "reason": f"people correction key '{slug}' matches no record"})
                continue
            for field, value in (spec.get("set") or {}).items():
                target[field] = value
            target["_corrected"] = spec.get("why")
            target["_verified_against"] = spec.get("verified_against")

    quotes = parse_quotes(text)
    # parse_quotes only reads <blockquote> tags out of the frozen
    # docs/_archive snapshot — it can never pick up a quote sourced after
    # that snapshot was taken. quotes_manual.json is the correction-file
    # equivalent for quotes (entities/people get add_entities/corrections;
    # quotes had no such mechanism until 2026-09-03), hand-maintained,
    # never overwritten by this script.
    quotes_manual_path = REPO / "data" / "registry" / "quotes_manual.json"
    if quotes_manual_path.exists():
        manual = json.loads(quotes_manual_path.read_text(encoding="utf-8"))
        next_n = len(quotes) + 1
        for q in manual:
            rec = {
                "id": f"q{next_n:03d}",
                "text_ru": q.get("text_ru"),
                "speaker": q.get("speaker"),
                "source_id": q.get("source_id"),
                "date": q.get("date"),
                "translation_en": q.get("translation_en"),
                "cite_raw": q.get("cite_raw"),
                "_verified": q.get("_verified", False),
            }
            quotes.append(rec)
            next_n += 1
    open_qs = parse_global_open_questions(lines, text)
    prose_recs, prose_leads = parse_prose_identifiers(text)
    ogrn_to_inn = {e["ogrn"]: e["inn"] for e in ents + mans
                   if e.get("ogrn") and e.get("inn")}
    sources = parse_sources(ogrn_to_inn)

    # Merge the entity streams, keyed by ИНН where known and by slug
    # otherwise. Table rows win on collision — they carry a role, a principal
    # and a confidence level that prose mentions don't.
    merged: dict[str, dict] = {}
    for rec in ents + mans:
        key = rec["inn"] or rec["slug"]
        if key in merged:
            merged[key].setdefault("_duplicate_of", []).append(rec["_origin"])
            continue
        merged[key] = rec

    def norm_name(name: str) -> str:
        """Fold a name for matching: strip legal form, tails and punctuation.

        Mirrors check_registry.normalise_name. Needed because a table row and
        a prose mention of the same company rarely spell it identically —
        'ООО «Тримикс» / «Булат»/3mx' in the table, 'ООО «Тримикс»' in prose.
        """
        s = name.lower().replace("ё", "е")
        s = s.replace("«", "").replace("»", "").replace('"', "")
        s = re.sub(r"\s*\|.*$", "", s)
        s = re.split(r"\s/\s", s)[0]
        s = re.sub(r"^(" + "|".join(LEGAL_FORMS) + r")\s*", "", s,
                   flags=re.IGNORECASE)
        return re.sub(r"[^0-9a-zа-я]+", "", s)

    # Prose-derived records: enrich a table row where one already exists,
    # otherwise become a new record. Never overwrite a non-null table value.
    enriched = 0
    for pr in prose_recs:
        target = merged.get(pr["inn"])
        if target is None:
            # Fall back to name matching, but only onto a record that has no
            # ИНН of its own — two records that both carry an ИНН are two
            # companies, however similar their names look.
            want = norm_name(pr["name_ru"])
            target = next((v for v in merged.values()
                           if not v.get("inn") and norm_name(v["name_ru"]) == want),
                          None)
        if target is not None:
            filled = False
            for field in ("inn", "ogrn", "registered", "okved_code"):
                if pr.get(field) and not target.get(field):
                    target[field] = pr[field]
                    filled = True
            if pr.get("city") and not target.get("city"):
                target["city"] = pr["city"]
                filled = True
            if filled:
                target.setdefault("_origin_extra", []).append("brief:prose")
                enriched += 1
            continue

        merged[pr["inn"]] = {
            "slug": slugify(pr["name_ru"]),
            "name_ru": pr["name_ru"],
            "name_latin": None,
            "legal_form": pr["legal_form"],
            "brand_ru": None, "brand_latin": None,
            "inn": pr["inn"], "ogrn": pr["ogrn"],
            "registered": pr["registered"], "address": None,
            "city": pr["city"],
            "okved_code": pr["okved_code"], "okved_label": None,
            "okved_mismatch": None,
            "director": None, "director_history": [],
            "founders": [], "founders_history": [],
            "charter_capital": None, "charter_capital_history": [],
            "address_history": [], "name_history": [],
            "facility_type": None, "facility_type_history": [],
            "parents": [], "subsidiaries": [],
            "tier": (SECTION_TIER_H3.get(pr.get("section_h3") or "")
                     or SECTION_TIER_H2.get(pr.get("section_h2") or "")),
            "tier_basis": (f"brief section: {pr.get('section_h3') or pr.get('section_h2')}"
                           if (pr.get("section_h3") or pr.get("section_h2")) else None),
            "cbst_tie": None, "wb_overlap": "not_checked",
            "products": [], "financials": [], "egrul_flags": [],
            "securing_measures": [],
            "securing_measures_checked_at": None,
            "sanctions": [], "litigation": [], "licences": [],
            "trademarks": [], "patents": [], "foreign_components": [],
            "government_contracts": [], "workforce_history": [],
            "state_programs": [], "marketing_claims": [],
            "battlefield_evidence": [], "domain_history": [],
            "web": {"sites": [], "telegram": [], "vk": [], "youtube": [],
                    "marketplace_listings": [], "other": []},
            "images": [], "open_questions": [], "sources": [],
            "confidence": None,
            "_verified": False,
            "_origin": "brief:prose",
            "_raw": {"context": pr["context"]},
        }

    entities = list(merged.values())

    # Hand-made corrections are applied last and always win. They exist so
    # that regenerating the scaffold never silently reverts a fix that was
    # verified against a primary source — see data/registry/corrections_entities.json,
    # which records the reasoning for each one.
    corrections_applied = 0
    corr = load_corrections("entities", "add_entities")
    if corr:
        # add_entities MUST run before the by_key/'set' loop below — a 'set'
        # correction targeting a record that only exists via add_entities
        # (e.g. the second company in a compound table row) would silently
        # fail to match otherwise, since by_key was built from `entities`
        # before that record existed. Bug found 2026-08-22: a 'set'
        # correction on kolskaya-verf (split out of "НПП «ЭЛВО» / «Кольская
        # верфь»" by an earlier add_entities entry) failed under BOTH ИНН
        # and slug keys until this reordering.
        blank = {k: v for k, v in (entities[0].items() if entities else [])}
        for extra in (corr.get("add_entities") or []):
            rec = {k: ([] if isinstance(v, list) else
                       ({} if isinstance(v, dict) else None))
                   for k, v in blank.items()}
            rec.update({
                "web": {"sites": [], "telegram": [], "vk": [], "youtube": [],
                        "marketplace_listings": [], "other": []},
                "wb_overlap": "not_checked",
                "_verified": False,
                "_origin": "corrections:add_entities",
            })
            rec.update({k: v for k, v in extra.items() if k != "why"})
            rec["_corrected"] = extra.get("why")
            entities.append(rec)
            corrections_applied += 1

        by_key = {}
        for e in entities:
            if e.get("inn"):
                by_key[e["inn"]] = e
            by_key.setdefault(e["slug"], e)
        for key, spec in (corr.get("entities") or {}).items():
            target = by_key.get(key)
            if target is None:
                problem_note = {"table": "corrections", "reason":
                                f"correction key '{key}' matches no record"}
                man_problems.append(problem_note)
                continue
            for field, value in (spec.get("set") or {}).items():
                target[field] = value
            target["_corrected"] = spec.get("why")
            target["_verified_against"] = spec.get("verified_against")
            corrections_applied += 1

    for e in entities:
        seed_history(e)

    # Filter prose_leads against the FINAL entities/people lists (post-
    # corrections) — otherwise this list rots exactly the way
    # roymarket_tracking_discipline already warns about for catch-all lists:
    # an ИНН resolved via corrections.json (attributed to an entity or
    # person) kept reappearing here as "still unattributed" indefinitely,
    # since prose_leads was computed early from raw extraction, before
    # corrections ever ran. Found 2026-08-22: resolved 8 ИНН via
    # corrections in one pass, and the unattributed count didn't drop at
    # all until this filter was added. Placed here (post-corrections,
    # pre-print) so both the printed summary and the written file agree.
    resolved_entity_inns = {e["inn"] for e in entities if e.get("inn")}
    resolved_people_inns = {p["inn_personal"] for p in people if p.get("inn_personal")}
    resolved_inns = resolved_entity_inns | resolved_people_inns
    prose_leads = [lead for lead in prose_leads if lead.get("inn") not in resolved_inns]

    problems = ent_problems + man_problems

    print(f"entities         {len(entities):>4}  "
          f"({len(ents)} entity table + {len(mans)} manufacturers + "
          f"{len(prose_recs)} prose)")
    print(f"  with ИНН       {sum(1 for e in entities if e['inn']):>4}")
    print(f"  enriched       {enriched:>4}  (prose filled a table row's gaps)")
    print(f"  corrected      {corrections_applied:>4}  (from corrections_entities/people.json)")
    print(f"  unverified     {sum(1 for e in entities if not e['_verified']):>4}")
    print(f"people           {len(people):>4}  "
          f"({len(people) - people_added} from tables + {people_added} from prose)")
    print(f"  with ИНН       {sum(1 for p in people if p.get('inn_personal')):>4}")
    print(f"quotes           {len(quotes):>4}")
    print(f"open questions   {len(open_qs):>4}  (+{len(catchalls)} catch-all rows to split)")
    print(f"unattributed ИНН {len(prose_leads):>4}  (need a human to assign)")
    print(f"sources          {len(sources):>4}")
    if problems:
        print(f"\nPARSE PROBLEMS ({len(problems)}) — need manual handling:")
        for p in problems:
            print(f"  - {p}")

    if args.dry_run:
        print("\n--dry-run: nothing written")
        return 0

    # See carry_forward_screening_fields() above for the full rationale and
    # the two silent-loss modes this fixes (no-ИНН entities, a corrected ИНН
    # invalidating the old key).
    prev_entities = _load_prev_registry_file(OUT_DIR / "entities.json")
    carry_forward_screening_fields(
        entities, prev_entities, ENTITY_CARRY_FORWARD_FIELDS, secondary_key="inn"
    )

    prev_people = _load_prev_registry_file(OUT_DIR / "people.json")
    carry_forward_screening_fields(
        people, prev_people, PEOPLE_CARRY_FORWARD_FIELDS
    )

    attribute_open_questions(open_qs, entities, people)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payloads = {
        "entities.json": entities,
        "people.json": people,
        "quotes.json": quotes,
        "open_questions.json": open_qs,
        "sources.json": sources,
        "_scaffold_leads.json": {
            "unattributed_inn": prose_leads,
            "manufacturer_catchall_rows": catchalls,
            "parse_problems": problems,
        },
    }
    for name, payload in payloads.items():
        path = OUT_DIR / name
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
        print(f"wrote {path.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
