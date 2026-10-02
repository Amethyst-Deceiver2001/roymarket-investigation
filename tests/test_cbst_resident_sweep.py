#!/usr/bin/env python3
"""Regression fixtures for scripts/cbst_resident_sweep.py and scripts/tg_forward_diff.py.

    python3 tests/test_cbst_resident_sweep.py

Each assertion is a real miss or false lead from the 2026-10-01 sweep of the ЦБСТ archive.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import cbst_resident_sweep as S  # noqa: E402
import tg_forward_diff as F  # noqa: E402
import tg_post_coverage as T  # noqa: E402

# 1. «президент» contains the letters «резидент»: the word match must be anchored.
assert S.RESIDENT.search("резидент цбст") and S.RESIDENT.search("резидентом цбст")
assert not S.RESIDENT.search("президент рф") and not S.RESIDENT.search("вице-президент")
# 2. ЦБСТ is misspelled in the channel itself (post 2041: «резидент ЦСБТ»).
assert all(S.CBST_TOKENS.search(x) for x in ("резидент цсбт", "резидент цбст", "центра беспилотных систем", "#резиденты_цбст"))
# 3. Hyphen spacing and Cyrillic/Latin do not hide an entity: «ТИТАН - СЕВЕРО-ЗАПАД» vs «Титан Северо-Запад»; Нейри vs Neiry.
assert S.match_key("ООО «ТИТАН - СЕВЕРО-ЗАПАД»") == S.match_key("Титан Северо-Запад")
assert S.match_key("Нейри") == S.match_key("Neiry")
# 4. Event names after a preposition are not companies; the subject of the sentence is.
c = {k for _, _, k in S.candidates("представил на «Дрон Экспо» компания «Витрес» новые БПЛА")}
assert S.match_key("Витрес") in c and S.match_key("Дрон Экспо") not in c, c
# 5. Bare acronyms and roman numerals are not company leads; a multi-word Latin name is.
c = {k for _, _, k in S.candidates("испытания DARPA и II потока, компания SR Space, Stratolink")}
assert S.match_key("SR Space") in c and S.match_key("Stratolink") in c and S.match_key("DARPA") not in c
# 6. The window is one sentence plus the next, so a digest item cannot borrow names from its neighbours.
text = "Резидент ЦБСТ представил БпЛА. Компания Intec показала «Метеор-2». Другая новость про «Посторонний»."
row = (T.CBST_CHANNEL_ID, 1, "2026-01-01", text, None, 0, None, T.fold(text))
wins = S.resident_windows(row)
assert wins and "Метеор-2" in wins[0][0] and "Посторонний" not in wins[0][0], wins
# 7. Classification: entity without a tie is a TIE-GAP, unknown name is NEW, prose-only is MENTIONED.
idx = {S.match_key("Титан Северо-Запад"): [("ooo-titan", "entity", "no-tie")],
       S.match_key("Аляска"): [("alyaska", "entity", "t-doc")]}
assert S.classify(S.match_key("Титан - Северо-Запад"), idx, "")[0] == "TIE-GAP"
assert S.classify(S.match_key("Аляска"), idx, "")[0] == "known"
assert S.classify(S.match_key("Неведомая компания"), idx, "")[0] == "NEW"
assert S.classify(S.match_key("Неведомая компания"), idx, S.key_latin(S.translit("... Неведомая компания ...")))[0] == "MENTIONED"

# 8. Forward diff: a removed name is reported, a case-only change is not, extra appended text is tagged.
removed, added = F.compare("Компания из Санкт-Петербурга развернула выпуск «Эгеон».",
                           "Петербургская компания «Титан Северо-Запад» развернула выпуск «Эгеон».")
assert list(removed.values()) == ["Титан Северо-Запад"] and not added
assert F.compare("бригады «БАРС-Курск».", "бригады «Барс-Курск».") == ({}, {})
removed, added = F.compare("бригады «СХ».", "бригады «СуперХроно».")
assert list(removed.values()) == ["СуперХроно"] and list(added.values()) == ["СХ"]
print("cbst_resident_sweep / tg_forward_diff: all checks passed")
