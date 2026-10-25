"""sanctions_people_check.py: name folding and the grade (no lists loaded)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import sanctions_people_check as sp  # noqa: E402

assert sp.tokens("Водолацкий") == sp.tokens("VODOLATSKY") or sp.translit("Водолацкий") == sp.translit("Vodolatsky"), (sp.translit("Водолацкий"), sp.translit("Vodolatsky"))
assert sp.translit("Пушилин") == sp.translit("PUSHYLIN")
assert sp.translit("Петр") == sp.translit("Пётр")
E = {"list": "EU", "id": "x", "names": ["Виктор Петрович ВОДОЛАЦКИЙ"], "dob": ["1957-08-19"], "info": ""}
assert sp.grade(sp.tokens("Виктор Петрович Водолацкий"), E, None)[0] == "name+patronymic"
assert sp.grade(sp.tokens("Виктор Петрович Водолацкий"), E, "1957-08-19")[0] == "name+patronymic+DOB"
# first name + patronymic alone is no match
G = {"list": "EU", "id": "y", "names": ["Виктор Петрович ГОРЕМЫКИН"], "dob": [], "info": ""}
assert sp.grade(sp.tokens("Виктор Петрович Водолацкий"), G, None)[0] == ""
# surname + patronymic with a different first name is another person; surname + first name still shows
F = {"list": "EU", "id": "z", "names": ["Юрий Андреевич ФЁДОРОВ"], "dob": [], "info": ""}
assert sp.grade(sp.tokens("Фёдоров Андрей Андреевич"), F, None)[0] == ""
assert sp.grade(sp.tokens("Фёдоров Юрий Петрович"), F, None)[0] == "surname+first name"
M = {"list": "EU", "id": "m", "names": ["Зураб Гайозович МАКИЕВ"], "dob": [], "info": ""}
assert sp.grade(sp.tokens("Зураб Макиев"), M, None)[0] == "surname+first name"
assert sp.surname_of(sp.tokens("Рогозин Дмитрий Олегович")) == sp.translit("Рогозин")
assert sp.norm_dob("21/12/1963") == "1963-12-21" and sp.norm_dob("09 May 1981") == "1981-05-09" and sp.norm_dob("1957-08-19") == "1957-08-19"
print("test_sanctions_people_check: ok")
