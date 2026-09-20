"""Shared entity/product/ИНН/ОГРН extraction patterns for this investigation.

Factored out of mine_leads.py so the same matching logic works on any text,
not just the Telegram-scraped DB — corporate "About"/"Contacts" pages
routinely list a company's own ИНН/ОГРН and legal name directly, and that
text should get the same treatment as a Telegram post. See extract_ids.py
for the general-purpose CLI over arbitrary text; mine_leads.py uses these
same patterns for its DB scan.
"""
from __future__ import annotations

import re
import unicodedata

LEGAL_PREFIXES = [
    "ООО", "АО", "ОАО", "ЗАО", "ПАО", "НПО", "НПП", "НПЦ", "КБ", "СКБ",
    "ОКБ", "ОПКБ", "ГК", "ФГУП", "ГУП", "МУП", "АНО", "ИП", "НИИ", "ЦНИИ",
]
PREFIX_ALT = "|".join(LEGAL_PREFIXES)

# Prefix + guillemet/straight-quoted name, e.g. ООО «Архангел», АО "Технодрон"
RE_ENTITY_QUOTED = re.compile(
    rf'\b({PREFIX_ALT})\s*[«"]([^»"]{{2,60}})[»"]'
)
# Prefix + bare capitalized name (1-4 tokens), e.g. НПЦ БАСиРТК, ГК МВС
RE_ENTITY_BARE = re.compile(
    rf'\b({PREFIX_ALT})[ \t]+((?:[А-ЯЁ][А-Яа-яёЁ\-]*[ \t]*){{1,4}})'
)
# Bare guillemet-quoted product/brand name
RE_QUOTED_NAME = re.compile(r'«([^»]{2,45})»')

# UI/menu-button junk from interactive product-bot channels (firmware
# settings, inline keyboards) — pure noise for entity/product triage.
# Discovered 2026-08-21 scanning @asellabs/@orient4gnss (bot-style channels).
_QUOTED_NOISE_WORDS = {
    "вкл", "вкл.", "выкл", "выкл.", "максимум", "минимум", "средний",
    "стандарт", "update", "update firmware", "no update found", "xs",
}
RE_QUOTED_NOISE = re.compile(r'^\d+$')  # pure-digit button labels


def is_noise_quote(name: str) -> bool:
    """True if a RE_QUOTED_NAME match is UI-button junk, not a real name."""
    s = name.strip()
    if len(s) <= 2:
        return True
    if RE_QUOTED_NOISE.match(s):
        return True
    if s.lower().strip('.') in _QUOTED_NOISE_WORDS:
        return True
    return False


# ИНН (10 or 12 digits) / ОГРН (13 or 15 digits), anchored to a label.
# Official letterheads routinely write the combined "ИНН/КПП 7701356086/
# 770301001" form (found live OCR'ing a Moscow-government default-notice
# PDF) — a bare `ИНН[:\s]*` stops at the "/КПП" text and never reaches the
# digits at all, silently returning zero ИНН hits on a document whose own
# letterhead states one in plain sight. `(?:/КПП)?` absorbs that label
# variant before the digits, and the trailing `(?:/\d{9})?` absorbs the
# КПП's own digits after the slash — a bare "ИНН: 12345..." with no КПП
# suffix still matches exactly as before.
RE_INN = re.compile(r'\bИНН(?:/КПП)?[:\s]*([0-9]{10}|[0-9]{12})(?:/\d{9})?\b')
RE_OGRN = re.compile(r'\bОГРН[:\s]*([0-9]{13}|[0-9]{15})\b')
# Role title + a 2-3 word Capitalized name
ROLE_TITLES = [
    "Генеральный директор", "Генеральный[ -]директор", "Учредитель",
    "Директор", "Председатель", "Руководитель", "Основатель",
]
RE_ROLE_NAME = re.compile(
    rf'(?:{"|".join(ROLE_TITLES)})[ \t:—-]+'
    r'([А-ЯЁ][а-яёА-Я]+(?:[ \t]+[А-ЯЁ][а-яёА-Я]+){1,2})'
)

UAV_TERMS = [
    "бпла", "беспилотник", "дрон", "коптер", "квадрокоптер", "октокоптер",
    "гексакоптер", "fpv", "фпв", "рэб", "рэр", "антидрон", "перехватчик",
    "камикадзе", "оптоволокон", "ретранслятор", "автопилот", "тепловизор",
    "целеуказан", "полётный контроллер", "полетный контроллер", "цбст",
    "резидент", "войсковая часть", "полевая почта", "рой.маркет",
    "роймаркет", "минобороны", "мо рф", "техносовет", "техсовет",
    # Added 2026-08-21 after scanning @orient4gnss/@asellabs: GNSS/nav-tech
    # companies (Orient Systems/4ГНСС) score near-zero on drone vocabulary
    # alone, and «рубикон» is a legitimate high-signal institutional name
    # (Russia's unified drone-warfare center), not a product to filter out.
    "гнсс", "навигацион", "координат", "антиспуфинг", "радиоподавлен",
    "рубикон",
]


def norm(name: str) -> str:
    """Normalize an entity/product name for dedup.

    See [[roymarket_fuzzy_dedup]].
    """
    name = unicodedata.normalize("NFKC", name)
    name = name.strip().strip('«»"\'').lower()
    for p in LEGAL_PREFIXES:
        name = re.sub(rf'^{p.lower()}\s+', '', name)
    # Hyphens are a word-separator variant here ("Гарант-Клуб" vs "Гарант
    # Клуб"), not punctuation to delete outright — deleting them collapses
    # to a different string than the space-separated form and breaks
    # brief cross-checks for names that vary this way.
    name = name.replace('-', ' ')
    name = re.sub(r'[^\w\s]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def uav_score(text: str) -> int:
    t = text.lower()
    return sum(1 for term in UAV_TERMS if term in t)


# Delivery-attribution genre: a channel reporting "we delivered/gave <product>
# to <unit>" — the stereotyped phrasing that resolved АО «РОСС» 2026-09-08
# (@nashapravdafond post 1905141464:240, "производства АО «Росс»" paired
# with a named "Центр" group-of-forces reconnaissance unit). Verb + unit-noun
# fuzzy match, independent of which comes first or how far apart they sit —
# a delivery post routinely interleaves the verb, the unit, and the quoted
# product name in any order ("передали бойцам N-й бригады «Продукт»" vs
# "«Продукт» доставлен в расположение N-го полка").
DELIVERY_VERBS = [
    "передал", "передали", "передан", "переданы", "переданные",
    "доставил", "доставили", "доставлен", "доставлены",
    "отправил", "отправили", "отправлен", "отправлены",
    "направил", "направили", "направлен", "направлены",
    "вручил", "вручили", "вручен", "вручены",
    "переданы вместе", "приобрет", "закупил", "закупили",
]
UNIT_NOUNS = [
    "боец", "бойц", "парн", "солдат", "военнослужащ",
    "батальон", "дивизион", "полк", "бригад", "дивизи",
    "рот[аеы]", "взвод", "отряд", "расчет", "расчёт",
    "подразделен", "разведподразделен", "войсковая часть", "в/ч",
    "группировк", "группа войск", "фронт",
]
RE_DELIVERY_VERB = re.compile(
    "(?:" + "|".join(v.replace(" ", r"\s+") for v in DELIVERY_VERBS) + ")",
    re.IGNORECASE,
)
RE_UNIT_NOUN = re.compile(
    "(?:" + "|".join(UNIT_NOUNS) + ")", re.IGNORECASE
)


# Quoted strings that are never a product name in this genre: Russian
# group-of-forces codenames (a delivery post routinely names its own unit
# this way, e.g. "войск «Центр»") and this investigation's own fund names,
# which appear constantly as the *actor*, not the *product*, in this exact
# sentence shape.
_DELIVERY_NOISE_QUOTES = {
    "центр", "запад", "юг", "север", "восток", "днепр", "заря", "z",
    "наша правда", "дар", "градислава",
}


def delivery_attribution_hits(text: str, window: int = 400) -> list[dict]:
    """Find stereotyped delivery-report sentences pairing a quoted product
    name with a military-unit noun and a delivery verb, in any order,
    within `window` characters of each other.

    Returns a list of {"product": str, "verb_span": (start,end),
    "unit_span": (start,end), "snippet": str} dicts, deduped by product name
    (norm()-ed) — a channel that mentions the same product across several
    nearby sentences in one post should not produce duplicate hits.

    This is intentionally loose (proximity, not a parse) — it is a triage
    signal for a human to read the surrounding post, not a citable claim on
    its own. See [[military_thankyou_letter_genre]] for the sibling
    letterhead-photo genre this complements.
    """
    if not text:
        return []
    verb_spans = [m.span() for m in RE_DELIVERY_VERB.finditer(text)]
    unit_spans = [m.span() for m in RE_UNIT_NOUN.finditer(text)]
    if not verb_spans or not unit_spans:
        return []
    quoted = [
        m for m in RE_QUOTED_NAME.finditer(text)
        if not is_noise_quote(m.group(1))
        and norm(m.group(1)) not in _DELIVERY_NOISE_QUOTES
    ]
    hits: dict[str, dict] = {}
    for qm in quoted:
        qstart, qend = qm.span()
        nearest_verb = min(
            (v for v in verb_spans if abs(v[0] - qstart) <= window),
            key=lambda v: abs(v[0] - qstart), default=None,
        )
        nearest_unit = min(
            (u for u in unit_spans if abs(u[0] - qstart) <= window),
            key=lambda u: abs(u[0] - qstart), default=None,
        )
        if nearest_verb is None or nearest_unit is None:
            continue
        product = qm.group(1).strip()
        key = norm(product)
        if key in hits:
            continue
        lo = max(0, min(qstart, nearest_verb[0], nearest_unit[0]) - 60)
        hi = min(len(text), max(qend, nearest_verb[1], nearest_unit[1]) + 60)
        hits[key] = {
            "product": product,
            "verb_span": nearest_verb,
            "unit_span": nearest_unit,
            "snippet": text[lo:hi].replace("\n", " ").strip(),
        }
    return list(hits.values())


def load_known_text(repo_root=None) -> str:
    """Normalised blob of everything this investigation already knows.

    Both `mine_leads.py` and `scan_sources.py` triage candidates by asking
    "is this name already documented?", and both used to answer it by
    grepping `docs/index.html`. That stopped being safe once the brief became
    a *generated* artifact: names in generated markup get split across tags,
    so a substring check against the HTML silently starts missing entities it
    used to find, and known companies come back as fresh leads.

    The registry is the authority now, so read that first. The brief is still
    concatenated on top during the transition — it holds prose detail that
    has not been migrated yet, and including it costs nothing.

    Returns text already passed through `norm()`, ready for substring checks.
    """
    from pathlib import Path

    repo = Path(repo_root) if repo_root else Path(__file__).resolve().parent.parent
    chunks = []

    registry = repo / "data" / "registry"
    if registry.is_dir():
        for path in sorted(registry.glob("*.json")):
            # Underscore-prefixed files are raw scan/mine staging caches
            # (_zakupki_mined.json, _scan_sources_cache.json, etc.) — pre-
            # triage candidate data, not confirmed registry facts. Including
            # them made "already known?" self-referential: any name that
            # ever landed in a mine cache read back as "already documented"
            # forever, silently suppressing it as a new lead even before a
            # human ever saw it (caught 2026-08-29 building
            # zakupki_signatory_diff.py — two real signatory names came back
            # 0 new because their own mined JSON entry satisfied this glob).
            if path.name.startswith("_"):
                continue
            try:
                chunks.append(path.read_text(encoding="utf-8"))
            except OSError:
                continue

    brief = repo / "docs" / "dossier.html"
    if brief.exists():
        chunks.append(brief.read_text(encoding="utf-8"))

    # Generated pages, once they exist.
    for extra in sorted((repo / "docs").glob("dossier*.html")):
        chunks.append(extra.read_text(encoding="utf-8"))
    for extra in sorted((repo / "docs" / "companies").glob("*.html")):
        chunks.append(extra.read_text(encoding="utf-8"))

    return norm("\n".join(chunks))
