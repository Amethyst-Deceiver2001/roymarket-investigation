"""Small display helpers shared by the page builders.

Moved out of build_company_profile.py on 2026-10-02 when the old case and profile
generators were archived (scripts/archive/); the chain view and any new builder import
them from here.
"""
import re
from pathlib import Path

TYPE_LABELS = {
    "EGRUL": "EGRUL extract",
    "EGRULAPI": "EGRUL open-API record",
    "EGRIP": "EGRIP (sole-proprietor registry) record",
    "РЕСУРС": "БФО annual-accounts filing",
    "UD": "Founding-Устав bundle",
    "TGMEDIA": "Telegram media",
    "CATALOG": "product catalog",
    "WEBCAPTURE": "site capture",
    "SITE": "site capture",
    "TRANSCRIPT": "transcript",
    "ATR": "АТР federal-grant registry PDF",
    "AERONEXT": "АЭРОНЕКСТ member record",
    "DOSSIER": "third-party OSINT dossier",
    "TRADEMARK": "Rospatent trademark record",
    "PATENT": "Rospatent patent record",
    "ROSPATENT": "Rospatent record",
    "ALEPH": "OCCRP Aleph screening record",
    "OPENSANCTIONS": "OpenSanctions screening record",
    "GUR": "GUR war-sanctions record",
    "COURT": "court filing",
    "PRESS": "press coverage",
    "CERT": "certificate/licence record",
    "DATASET": "bulk open-data extract",
    "ROM": "securing-measures registry record",
    "RMSP": "SME-registry record",
    "OZON": "Ozon marketplace capture",
    "HAR": "browser HAR capture",
}


def ru_date(iso_date):
    """YYYY-MM-DD -> DD.MM.YYYY (Russian convention), per STYLE_GUIDE.md §2.4.
    Passes through unchanged if it doesn't match the expected ISO shape."""
    if not iso_date:
        return iso_date
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", iso_date)
    if not m:
        return iso_date
    year, month, day = m.groups()
    return f"{day}.{month}.{year}"


REPO = Path(__file__).resolve().parent.parent
DESIGN_CSS = REPO / "design" / "roymarket.css"
FONT_LINK = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
             '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
             '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600'
             '&family=IBM+Plex+Sans:wght@400;600&family=Spectral:wght@400;500&subset=cyrillic&display=swap">')


def design_head(page_css: str = "") -> str:
    """Font link plus the design system CSS and a page's own CSS, inlined in that order."""
    return f"{FONT_LINK}\n<style>{DESIGN_CSS.read_text()}\n{page_css}</style>"


# Reader grades (design/README.md). Every registry confidence vocabulary maps here, in one table,
# so a page never decides a grade on its own. Values do not collide across vocabularies.
READER_GRADE_LABELS = {"doc": "Documented", "rep": "Reported", "open": "Not documented"}
READER_GRADE = {
    # basis on sells_for / memberships / participations / platform_partners; listings
    "doc": "doc", "press": "rep", "inferred": "open",
    # cbst_tie.confidence
    "t-doc": "doc", "t-open": "rep",
    # relation-envelope and delivery credibility
    "corroborated": "rep", "single": "rep",
    # family_of confidence
    "confirmed": "doc", "probable": "rep", "unconfirmed": "open",
}


def reader_grade(value) -> str:
    """Registry confidence value -> 'doc' | 'rep' | 'open'. Unknown or missing is 'open'."""
    return READER_GRADE.get(value, "open")


# Kind marks: 24x24 line icons, drawn in currentColor by .rm-kind svg. Military units use the
# APP-6 frame (unit_mark) instead.
KIND_ICONS = {
    "company": '<path d="M4 21V8l6-3v16M10 21V3l10 4v14M3 21h18M13 9h4M13 13h4M13 17h4"/>',
    "person": '<circle cx="12" cy="8" r="3.5"/><path d="M5 20c1-4 4-6 7-6s6 2 7 6"/>',
    "product": '<path d="M12 3l8 4.5v9L12 21l-8-4.5v-9z"/><path d="M4 7.5l8 4.5 8-4.5M12 12v9"/>',
    "storefront": '<path d="M4 9l1.5-5h13L20 9M4 9c0 1.7 1.3 3 3 3s2.7-1.3 2.7-3c0 1.7 1.3 3 2.3 3s2.3-1.3 2.3-3c0 1.7 1.3 3 3 3s2.7-1.3 2.7-3M5 12v8h14v-8M10 20v-5h4v5"/>',
    "buyer": '<path d="M3 9l9-5 9 5M5 9v9M9.5 9v9M14.5 9v9M19 9v9M3 20h18"/>',
    "program": '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/>',
    "event": '<rect x="4" y="5" width="16" height="15" rx="1"/><path d="M4 10h16M8 3v4M16 3v4"/>',
    "group": '<rect x="3" y="7" width="11" height="11" rx="1"/><rect x="10" y="4" width="11" height="11" rx="1"/>',
    "unit": '<path d="M12 3l9 9-9 9-9-9z"/>',   # the APP-6 hostile frame, as a label-sized mark
}


def kind_icon(kind: str) -> str:
    body = KIND_ICONS.get(kind)
    return f'<svg viewBox="0 0 24 24" aria-hidden="true">{body}</svg>' if body else ""


# APP-6 echelon marks drawn above the frame. Only from the unit record's own echelon field.
_ECHELON = {"battalion": 2, "regiment": 3, "brigade": "x1", "division": "x2", "army": "x4"}


def unit_mark(echelon: str | None = None) -> str:
    """Monochrome APP-6 hostile (diamond) land-unit frame with an optional echelon mark.
    No branch glyph is drawn until the unit record carries a sourced branch."""
    e = _ECHELON.get(echelon or "")
    marks = ""
    if isinstance(e, int):
        xs = [17 + (i - (e - 1) / 2) * 5 for i in range(e)]
        marks = "".join(f'<path class="ech" d="M{x} 3v5"/>' for x in xs)
    elif isinstance(e, str):
        n = int(e[1:])
        xs = [17 + (i - (n - 1) / 2) * 6 for i in range(n)]
        marks = "".join(f'<path class="ech" d="M{x-2} 3l4 5M{x+2} 3l-4 5"/>' for x in xs)
    return (f'<svg class="rm-unit" viewBox="0 0 34 40" aria-hidden="true">{marks}'
            '<path class="frame" d="M17 10l14 14-14 14L3 24z"/></svg>')


def source_type_label(path: str) -> str:
    stem = Path(path).name
    if stem.startswith("ul-") or stem.startswith("ip-"):
        return "EGRUL extract"
    if re.match(r"^A\d", stem):
        return "arbitration court filing"
    prefix = stem.split("_", 1)[0]
    if prefix in TYPE_LABELS:
        return TYPE_LABELS[prefix]
    return prefix.title() if prefix.isalpha() else "document"
