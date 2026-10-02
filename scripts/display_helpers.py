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
