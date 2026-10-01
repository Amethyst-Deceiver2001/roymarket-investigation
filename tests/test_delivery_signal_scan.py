#!/usr/bin/env python3
"""Regression fixtures for scripts/delivery_signal_scan.py.

    python3 tests/test_delivery_signal_scan.py
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import delivery_signal_scan as D  # noqa: E402

M = [("Булат", "ooo-trimiks", re.compile(r"«\s*Булат\s*»|\bБулат\w{0,3}\b", re.I))]

# 1. A handover to a unit naming a registry product is class A.
r = D.classify("Сегодня передали бойцам 155-й бригады детекторы «Булат» и два FPV-дрона.", M)
assert r and r["class"] == "A" and r["products"][0]["entity"] == "ooo-trimiks" and r["recipients"], r
# 2. The same handover with only a category word is class B.
r = D.classify("Привезли парням из батальона «Сомали» три квадрокоптера и рации.", M)
assert r and r["class"] == "B" and "квадрокоптер" in " ".join(r["categories"]), r
# 3. A verb with no recipient, or a recipient with no verb, is not a signal.
assert D.classify("Вчера передали документы в суд, дроны здесь ни при чём, это просто длинный текст.", M) is None
assert D.classify("Бойцы бригады рассказали про дроны и антенны на фронте, видео ниже, подробности в канале.", M) is None
# 4. A verb and a recipient with no product or category is not a signal either.
assert D.classify("Передали бойцам бригады горячий обед и тёплые носки, спасибо всем неравнодушным.", M) is None
# 5. Greetings and condolences do not count.
assert D.classify("Передал привет всем бойцам и поздравил подразделение с праздником, дроны не обсуждали.", M) is None
# 6. ё/е and case do not matter; the window around the verb is returned.
r = D.classify("ПЕРЕДАЛИ БОЙЦАМ ДРОНЫ", M)
assert r and r["class"] == "B" and "ПЕРЕДАЛИ" in r["window"], r
# 7. Reposts of one text share a key.
assert D.norm_key("Передали,  бойцам «Булат»!") == D.norm_key("передали бойцам булат")
print("delivery_signal_scan: all checks passed")
