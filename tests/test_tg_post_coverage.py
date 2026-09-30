#!/usr/bin/env python3
"""Regression fixtures for scripts/tg_post_coverage.py.

No pytest dependency - plain assertions, run directly:
    python3 tests/test_tg_post_coverage.py

Locks down the four failures behind the 2026-09-30 miss (ЦБСТ posts 1562/1976/2095 naming
«Архангел» went unseen): SQLite `lower()`/`LIKE` not folding Cyrillic, a bare brand word
being narrowed to a legal-name variant, an evidence list truncated without saying so, and a
zero-hit result with no positive control behind it.
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import tg_post_coverage as T  # noqa: E402


def row(msg, text, links=None, chan=1):
    return (chan, msg, "2026-03-17T00:00:00+00:00", text, links, 0, None, T.fold(text))


POSTS = [
    row(1976, "Среди них — производитель дронов-перехватчиков «Архангел». Гендиректор компании"),
    row(2095, "Среди них «Технодрон», СКБ «Пиранья» и «АРХАНГЕЛ».", '["https://eur-lex.europa.eu/x"]'),
    row(1562, "в новом учебном центре БПЛА «Архангела» в Туапсе"),
    row(9, "Заседание прошло в городе Архангельск, вместе с Аэро-Хит"),
    row(10, "Совещание в Ёлкино: «Ёлочка» представила образец"),
]


def ids(term):
    return sorted(r[1] for r, _ in T.search_term(POSTS, term))


# 1. The SQLite hazard itself: if SQLite ever starts folding Cyrillic this test fails, which is
#    good news to read, not a bug - but until then SQL lower()/LIKE must not be used.
con = sqlite3.connect(":memory:")
assert con.execute("select lower('Архангел')").fetchone()[0] == "Архангел", "SQLite now folds Cyrillic?"
assert con.execute("select 'Архангел' like '%архангел%'").fetchone()[0] == 0, "SQLite LIKE now folds Cyrillic?"

# 2. The matcher folds case (capital, lower, UPPER) and ё/е, and takes case endings.
assert ids("Архангел") == [1562, 1976, 2095], ids("Архангел")
assert ids("архангел") == ids("АРХАНГЕЛ") == ids("Архангел")
assert ids("ёлочка") == ids("Елочка") == [10]

# 3. ...but not a different word sharing the stem.
assert 9 not in ids("Архангел"), "Архангельск (the city) must not match Архангел"

# 4. Multi-word and hyphenated terms match across space/hyphen variants.
assert ids("аэро хит") == ids("Аэро-Хит") == [9]

# 5. Name cleaning: legal forms and quotes are stripped, generic words dropped.
assert T.clean_name("ООО «Архангел»") == ["архангел"]
assert T.clean_name("Общество с ограниченной ответственностью «Аэро-Хит»") == ["аэро-хит"]
assert T.clean_name("АНО «ЦБСТ»") == []                                   # under 5 letters
assert T.clean_name("АНО «ЦБСТ» | Центр беспилотных систем") == ["центр беспилотных систем"]
assert T.clean_name("ООО «Центр»") == []
assert T.clean_name('АНО НПЦ «Ушкуйник»') == ["ушкуйник"]
assert T.clean_name("Проект «Архангел» (КБ)") == ["архангел"]

# 5b. The bare brand is searched even when the registry's legal name is longer.
assert "архангел" in T.entity_terms({"name_ru": "ООО «Архангел-Центр»", "brand_ru": "Архангел"})

# 6. Positive control passes on real-looking text and aborts on an empty/odd corpus.
ok, msg = T.positive_control(POSTS)
assert ok, msg
ok, msg = T.positive_control([row(1, "only latin text here")])
assert not ok

# 7. Classification order: reviewed beats archived beats cited beats unseen.
key = (1, 5)
assert T.classify(key, {key: "s1"}, {key}, {5}) == "REVIEWED"
assert T.classify(key, {key: "s1"}, {key}, set()) == "ARCHIVED"
assert T.classify(key, {}, {key}, set()) == "CITED"
assert T.classify(key, {}, set(), set()) == "UNSEEN"

# 8. "No tie on file" contradictions: only UNSEEN hits whose every candidate entity lacks a tie.
hit = {"status": "UNSEEN", "tie_states": ["no-tie"]}
assert T.contradictions([hit, {"status": "UNSEEN", "tie_states": ["t-doc"]},
                         {"status": "UNSEEN", "tie_states": ["no-tie", "t-doc"]},
                         {"status": "ARCHIVED", "tie_states": ["no-tie"]}]) == [hit]
assert T.tie_state({"cbst_tie": {"confidence": "not_established"}}) == "no-tie"
assert T.tie_state({}) == "no-tie"
assert T.tie_state({"cbst_tie": {"confidence": "t-open"}}) == "t-open"

# 9. Truncation is never silent: a cap must say how many hits it hides.
many = [{"term": "x", "slugs": ["s"], "channel": "c", "msg_id": i, "date": "2026-01-01", "status": "UNSEEN",
         "source": None, "forward_of": None, "links": [], "snippet": "...", "tie_states": ["no-tie"]}
        for i in range(10)]
text, hidden = T.render(many, [], False, 3, "control", "scope")
assert hidden == 7 and "7 more hit(s) for this term NOT SHOWN" in text
text, hidden = T.render(many, [], False, 0, "control", "scope")
assert hidden == 0 and "NOT SHOWN" not in text

# 10. A post's primary document sits in its links field; the report must flag it.
hit2 = dict(many[0], links=["https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=OJ:L_202600504"])
text, _ = T.render([hit2], [], False, 0, "control", "scope")
assert "PRIMARY-DOC LINK" in text

# 11. Archived-post headers are read in both formats used in data/sources/.
assert T.HEADER_PATTERNS[0].search("channel_id 2159491523, msg_id 1976, 2026").groups() == ("2159491523", "1976")
assert T.HEADER_PATTERNS[1].search("Telegram post 2159491523:1701 | channel").groups() == ("2159491523", "1701")

# 12. cbst_channel_review shape: a review with no posts read, no note or a bad outcome is rejected.
good = {"slug": "a", "cbst_channel_review": {"as_of": "2026-10-01", "outcome": "namesake",
                                              "posts_read": [1, 2], "note": "common noun"}}
assert T.review_problems([good]) == []
for field, bad in (("as_of", "yesterday"), ("outcome", "fine"), ("posts_read", []), ("posts_read", ["1"]), ("note", " ")):
    e = {"slug": "a", "cbst_channel_review": dict(good["cbst_channel_review"], **{field: bad})}
    assert len(T.review_problems([e])) == 1, (field, bad)
assert T.review_problems([{"slug": "b"}]) == []

print("tg_post_coverage: all checks passed")
