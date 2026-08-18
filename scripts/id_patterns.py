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
# ИНН (10 or 12 digits) / ОГРН (13 or 15 digits), anchored to a label
RE_INN = re.compile(r'\bИНН[:\s]*([0-9]{10}|[0-9]{12})\b')
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
]


def norm(name: str) -> str:
    """Normalize an entity/product name for dedup — see [[roymarket_fuzzy_dedup]]."""
    name = unicodedata.normalize("NFKC", name)
    name = name.strip().strip('«»"\'').lower()
    for p in LEGAL_PREFIXES:
        name = re.sub(rf'^{p.lower()}\s+', '', name)
    name = re.sub(r'[^\w\s]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def uav_score(text: str) -> int:
    t = text.lower()
    return sum(1 for term in UAV_TERMS if term in t)
