#!/usr/bin/env python3
"""Fixtures for display_helpers.display_name / latin_display (B5).

No pytest dependency - plain assertions, run directly:
    python3 tests/test_display_name.py

The Latin form follows STYLE_GUIDE §2.3: legal form transliterated, never translated; the name
in «» transliterated, never translated; our own bracketed notes are not part of the name.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from display_helpers import display_name, latin_display  # noqa: E402

CASES = {
    "ООО «Тримикс»": "OOO «Trimiks»",
    "АНО «ЦБСТ»": "ANO «TsBST»",
    "НПЦ «Ушкуйник»": "NPTs «Ushkuynik»",
    "ПАО «Банк ПСБ»": "PAO «Bank PSB»",
    "ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ «ЭЛЬФ»": "OOO «ELF»",
    'ООО "НАУЧНО-ПРОИЗВОДСТВЕННАЯ КОМПАНИЯ "ЗЕВС"': 'OOO "NAUCHNO-PROIZVODSTVENNAYA KOMPANIYA "ZEVS"',
    "ИП Братеньков Андрей Алексеевич (прекратил деятельность 23.04.2020)": "IP Bratenkov Andrey Alekseevich",
    "ООО «Финконсалтингк» (ФКК)": "OOO «Finkonsaltingk» (FKK)",
    "ООО «Аэро-Хит»": "OOO «Aero-Khit»",
    "ООО «ТИ ЭС ДЖИ ГРУПП»": "OOO «TI ES DZHI GRUPP»",
    "ООО «ЦКБР»": "OOO «TsKBR»",
}


def test_latin_display():
    for ru, lat in CASES.items():
        assert latin_display(ru) == lat, (ru, latin_display(ru))


def test_brand_first_keeps_legal_and_latin():
    e = {"name_ru": "ООО «Тримикс»", "brands": [{"name": "3mx", "primary": True}]}
    n = display_name(e)
    assert (n["head"], n["legal"], n["latin"]) == ("3mx", "ООО «Тримикс»", "OOO «Trimiks»"), n


def test_hand_correction_wins():
    e = {"name_ru": "ООО «Тримикс» | gloss", "name_display": "OOO «TRIMIKS»"}
    assert display_name(e)["latin"] == "OOO «TRIMIKS»"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
