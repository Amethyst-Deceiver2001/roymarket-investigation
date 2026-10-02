#!/usr/bin/env python3
"""Regression fixtures for scripts/registry_lookup.py.

    python3 tests/test_registry_lookup.py

A one-word brand must find the longer registry name that contains it. «ЭЛВО» (НПП «ЭЛВО») and
«ЗащитаИнфоТранс» (ФГУП «ЗащитаИнфоТранс» Минтранса России) were called unrecorded on 2026-10-01
because the `contains` tier needs two words.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import registry_lookup as R  # noqa: E402

ENTITIES = [
    {"slug": "npp-elvo", "name_ru": "НПП «ЭЛВО»"},
    {"slug": "fgup-zit", "name_ru": "ФГУП «ЗащитаИнфоТранс» Минтранса России"},
    {"slug": "ooo-other", "name_ru": "ООО «Другое»"},
]
PEOPLE = [{"slug": "chadaev", "fio_ru": "Чадаев Алексей Викторович"}]
R._load = lambda name: ENTITIES if name == "entities.json" else PEOPLE
reg = R.Registry()

# 1. A one-word brand finds the longer name, as the weak `word` tier.
assert [(h[0], h[2]) for h in reg.find("ЭЛВО")] == [("word", "npp-elvo")]
assert [(h[0], h[2]) for h in reg.find("ЗащитаИнфоТранс")] == [("word", "fgup-zit")]
# 2. Too short or unrelated finds nothing.
assert reg.find("Эл") == []
assert reg.find("Антелекон") == []
# 3. The full name still outranks the word tier.
assert reg.find("НПП ЭЛВО")[0][0] == "exact"
# 4. Given name first still finds the surname-first record (the Latin tokens must not mask it).
assert [(h[0], h[2]) for h in reg.find("Алексей Чадаев")] == [("contains", "chadaev")]
assert [(h[0], h[2]) for h in reg.find("Чадаев Алексей")] == [("contains", "chadaev")]
print("registry_lookup: all checks passed")
