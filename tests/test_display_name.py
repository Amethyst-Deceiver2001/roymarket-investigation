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
from display_helpers import display_name, latin_display, latin_text, name_html, person_names, translation  # noqa: E402

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


def test_person_first_mention_and_surname():
    # STYLE_GUIDE §2.2: "Given Surname" on first mention with the full ФИО beside it, surname after
    p = person_names("ИП Цыганов Вадим Борисович")
    assert (p["first"], p["surname"], p["fio"]) == ("Vadim Tsyganov", "Tsyganov", "Цыганов Вадим Борисович"), p
    # a registry name_latin (register order) wins; a former surname in brackets stays out of prose
    p = person_names("Цыганова Виктория Юрьевна", "Tsyganova (Zhukova) Viktoriya Yuryevna")
    assert (p["first"], p["surname"]) == ("Viktoriya Tsyganova", "Tsyganova"), p


def test_proper_names_transliterated():
    assert latin_text("«Булат» в.3") == "«Bulat» v.3"
    assert latin_text("Дронница 2025 (IV)") == "Dronnitsa 2025 (IV)"
    assert latin_display("РОЙ.МАРКЕТ") == "ROY.MARKET"


def test_state_body_translated_with_original_attached():
    # §2.3a: translated, official Cyrillic and its transliteration in the popover, both copyable
    tr = translation("ГЛАВНОЕ УПРАВЛЕНИЕ МЧС РОССИИ ПО КУРСКОЙ ОБЛАСТИ")
    assert tr and "Kursk Oblast" in tr["en"], tr
    h = name_html(tr["en"], "ГЛАВНОЕ УПРАВЛЕНИЕ МЧС РОССИИ ПО КУРСКОЙ ОБЛАСТИ",
                  latin_text("ГЛАВНОЕ УПРАВЛЕНИЕ МЧС РОССИИ ПО КУРСКОЙ ОБЛАСТИ"), key="t")
    assert 'popovertarget="nm-t"' in h and 'id="nm-t"' in h and h.count('data-copy=') == 2, h
    assert "GLAVNOE UPRAVLENIE MChS ROSSII PO KURSKOY OBLASTI" in h, h
    assert translation("Нет такого органа") is None


def test_person_names_reads_given_name_first_order():
    assert person_names("Александр Геннадьевич Сидякин")["first"] == "Aleksandr Sidyakin"
    assert person_names("Дмитрий Медведев")["first"] == "Dmitriy Medvedev"
    assert person_names("Андрей Анатольевич Безруков")["surname"] == "Bezrukov"
    assert person_names("Цыганов Вадим Борисович")["first"] == "Vadim Tsyganov"
    assert person_names("Белоглазова (Мешкова) Людмила Александровна")["first"] == "Lyudmila Beloglazova"
    assert person_names("Филиппов Михаил Геннадьевич", "Mikhail Gennadevich Filippov")["first"] == "Mikhail Filippov"
    assert person_names("Агиевич Сергей Николаевич", "Agievich Sergey Nikolaevich")["first"] == "Sergey Agievich"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
