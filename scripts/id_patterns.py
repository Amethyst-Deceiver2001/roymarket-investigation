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
            try:
                chunks.append(path.read_text(encoding="utf-8"))
            except OSError:
                continue

    brief = repo / "docs" / "index.html"
    if brief.exists():
        chunks.append(brief.read_text(encoding="utf-8"))

    # Generated pages, once they exist.
    for extra in sorted((repo / "docs").glob("dossier*.html")):
        chunks.append(extra.read_text(encoding="utf-8"))
    for extra in sorted((repo / "docs" / "companies").glob("*.html")):
        chunks.append(extra.read_text(encoding="utf-8"))

    return norm("\n".join(chunks))
