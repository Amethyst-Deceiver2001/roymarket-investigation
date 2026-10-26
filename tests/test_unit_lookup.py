#!/usr/bin/env python3
"""Fixtures for scripts/unit_names.py and scripts/unit_lookup.py.

No pytest dependency - plain assertions, run directly:
    python3 tests/test_unit_lookup.py

The units are synthetic, so the test does not depend on what the registry holds.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import unit_lookup as ul  # noqa: E402
import unit_names as un  # noqa: E402

TANK = {"slug": "237-tp", "name_ru": "237-й танковый полк", "unit_type": "regiment", "arm": "tank", "number": 237,
        "names": [{"form": "post_wording", "value": "237-го танкового полка 3-й мотострелковой дивизии",
                   "grade": "stated", "source_id": "s9203"},
                  {"form": "vch", "value": "в/ч 91726", "grade": "lead"}],
        "parent_history": [{"parent_text": "3-я мотострелковая дивизия", "status": "stated", "source_id": "s9203"}]}
AIR = {"slug": "237-dshp", "name_ru": "237-й гвардейский десантно-штурмовой полк", "unit_type": "regiment",
       "arm": "air_assault", "number": 237,
       "names": [{"form": "official", "value": "237 гвардейский десантно-штурмовой Торуньский полк",
                  "grade": "stated", "source_id": "s9205"}],
       "parent_history": [{"parent_unit": "76-dshd", "status": "lead", "note": "user statement"}]}
DIV = {"slug": "76-dshd", "name_ru": "76-я гвардейская десантно-штурмовая дивизия", "unit_type": "division",
       "arm": "air_assault", "number": 76,
       "names": [{"form": "post_wording", "value": "76-й бригады ВДВ", "grade": "stated", "source_id": "s1"},
                 {"form": "post_wording", "value": "76-й гвардейской десантно-штурмовой бригаде",
                  "grade": "stated", "source_id": "s2"}]}
UNITS = [TANK, AIR, DIV]


def main():
    # Reading a phrase: number, type, arm, parent, в/ч.
    p = un.parse("237-му гвардейскому десантно-штурмовому полку")
    assert (p["number"], p["kind"], p["arm"], p["guards"]) == (237, "regiment", "air_assault", True), p
    p = un.parse("237-го танкового полка 3-й мотострелковой дивизии")
    assert (p["number"], p["kind"], p["arm"]) == (237, "regiment", "tank"), p
    assert (p["parent"]["number"], p["parent"]["kind"], p["parent"]["arm"]) == (3, "division", "motor_rifle"), p
    assert un.parse("237 дшп")["arm"] == "air_assault" and un.parse("3 мсд")["kind"] == "division"
    assert un.parse("76-й бригады ВДВ")["arm"] == "airborne"
    assert un.parse("237 тп, в/ч 91726")["vch"] == "91726"
    # a product name with a hyphenated number is not a unit number
    assert un.parse("пусковой расчёт БПЛА «Герань-2»")["number"] is None
    assert un.parse("2-й батальон, расчёт «Герань-2»")["number"] == 2
    q = un.parse("войсковая часть 33000")
    assert q["number"] is None and q["vch"] == "33000", q  # a five-digit number is a в/ч, not a unit number

    # The two 237ths are never mixed up, and a bare number picks nothing.
    r = ul.lookup("237-му гвардейскому десантно-штурмовому полку", UNITS)
    assert (r["state"], r["candidates"]) == ("resolved", ["237-dshp"]), r
    r = ul.lookup("237-го танкового полка", UNITS)
    assert (r["state"], r["candidates"]) == ("resolved", ["237-tp"]), r
    r = ul.lookup("237", UNITS)
    assert r["state"] == "ambiguous" and set(r["candidates"]) == {"237-tp", "237-dshp"}, r
    r = ul.lookup("237-й полк", UNITS)
    assert r["state"] == "ambiguous" and len(r["candidates"]) == 2, r
    r = ul.lookup("237-й полк 3-й мотострелковой дивизии", UNITS)
    assert (r["state"], r["candidates"]) == ("resolved", ["237-tp"]), "a stated parent decides between the two"
    r = ul.lookup("237-й полк 76-й дивизии", UNITS)
    assert (r["state"], r["candidates"]) == ("resolved", ["237-dshp"]), "a parent on a lead decides too"
    r = ul.lookup("999-й танковый полк", UNITS)
    assert r["state"] == "unrecorded", r
    assert ul.lookup("в/ч 91726", UNITS)["candidates"] == ["237-tp"]

    # One formation, several wordings: brigade and division both reach the same record.
    for wording in ("76-й гвардейской десантно-штурмовой дивизии", "76-й бригады ВДВ", "76-й гвардейской десантно-штурмовой бригаде"):
        r = ul.lookup(wording, UNITS)
        assert (r["state"], r["candidates"]) == ("resolved", ["76-dshd"]), (wording, r)

    # Two records that read as one unit are reported, unless their parents differ.
    twin = dict(DIV, slug="76-brigade", name_ru="76-я бригада ВДВ", names=[], unit_type="brigade", arm="airborne")
    seen = []
    import io
    import contextlib
    with contextlib.redirect_stdout(io.StringIO()) as out:
        ul.check([DIV, twin])
    assert "76-dshd  /  76-brigade" in out.getvalue(), out.getvalue()
    with contextlib.redirect_stdout(io.StringIO()) as out:
        ul.check([TANK, AIR])
    assert "237-tp  /  237-dshp" not in out.getvalue(), "different arms are different units"

    # Shape checks on the new fields.
    slugs = {u["slug"] for u in UNITS}
    assert un.validate_unit(TANK, slugs) == [] and un.validate_unit(AIR, slugs) == [] and un.validate_unit(DIV, slugs) == []
    bad = dict(TANK, arm="spaceship", number=0,
               names=[{"form": "nickname", "value": "", "grade": "stated"}],
               parent_history=[{"parent_unit": "nowhere", "status": "lead"}, {"parent_text": "x", "status": "stated"}])
    msgs = un.validate_unit(bad, slugs)
    for needle in ("number must be", "arm 'spaceship'", ".form 'nickname'", "value is required", "stated but has no source_id",
                   "not a unit slug", "must say in note"):
        assert any(needle in m for m in msgs), (needle, msgs)
    # English label: generated from number, guards, arm and type; never a translation of honorifics.
    assert un.name_en(TANK) == "237th Tank Regiment", un.name_en(TANK)
    assert un.name_en(AIR) == "237th Guards Air Assault Regiment", un.name_en(AIR)
    assert un.name_en(DIV) == "76th Guards Air Assault Division", un.name_en(DIV)
    assert [un.ordinal_en(n) for n in (1, 2, 3, 4, 11, 12, 13, 21, 22, 102, 111)] == \
        ["1st", "2nd", "3rd", "4th", "11th", "12th", "13th", "21st", "22nd", "102nd", "111th"]
    assert un.name_en({"name_ru": "дивизион народного ополчения", "unit_type": "detachment"}) is None
    assert un.name_en({"name_ru": "114-я ОМСБР", "unit_type": "brigade"}) == "114th Motor Rifle Brigade"
    assert un.name_en({"name_ru": "91-я бригада управления", "unit_type": "brigade", "arm": "command"}) == "91st Command Brigade"

    # The public card shows only stated items; internal pages also show leads, each with its grade.
    by = {u["slug"]: u for u in UNITS}
    pub = un.display_unit(TANK, by, public=True)
    assert pub["head"] == "237th Tank Regiment" and pub["vch"] == [] and pub["short"] == []
    assert [x["grade"] for x in pub["parents"]] == ["stated"], pub
    inner = un.display_unit(TANK, by, public=False)
    assert inner["vch"] == [{"value": "в/ч 91726", "grade": "lead"}], inner
    assert un.display_unit(AIR, by, public=True)["parents"] == [], "a lead parent is not shown publicly"
    assert un.display_unit(AIR, by, public=False)["parents"][0]["text"] == DIV["name_ru"]
    assert un.display_unit(AIR, by, public=True)["ru"] == "237 гвардейский десантно-штурмовой Торуньский полк"

    # Same number, same type and arm, different parents: the stated parent (or в/ч) goes into the label.
    # (The two 237ths differ by arm, so their labels already differ; this is the case arm cannot settle.)
    MA = {"slug": "345-a", "name_ru": "345-й мотострелковый полк", "unit_type": "regiment", "arm": "motor_rifle", "number": 345,
          "parent_history": [{"parent_text": "104-я дивизия", "status": "stated", "source_id": "s1"}]}
    MB = {"slug": "345-b", "name_ru": "345-й мотострелковый полк", "unit_type": "regiment", "arm": "motor_rifle", "number": 345,
          "parent_history": [{"parent_text": "7-я дивизия", "status": "lead", "note": "user statement"}]}
    MC = {"slug": "345-c", "name_ru": "345-й мотострелковый полк", "unit_type": "regiment", "arm": "motor_rifle", "number": 345,
          "names": [{"form": "vch", "value": "в/ч 12345", "grade": "stated", "source_id": "s2"}]}
    MD = {"slug": "345-d", "name_ru": "345-й мотострелковый полк", "unit_type": "regiment", "arm": "motor_rifle", "number": 345}
    GRP = [MA, MB, MC, MD]
    byg = {u["slug"]: u for u in GRP}
    assert un.siblings(TANK, UNITS) == [] and un.siblings(DIV, UNITS) == [], "different arms are not confusable"
    assert [x["slug"] for x in un.siblings(MA, GRP)] == ["345-b", "345-c", "345-d"]
    assert un.display_unit(MA, byg, public=True, units=GRP)["head"] == "345th Motor Rifle Regiment (104th Division)"
    pb = un.display_unit(MB, byg, public=True, units=GRP)
    assert pb["head"] == "345th Motor Rifle Regiment" and pb["needs_disambiguation"], "a lead parent is not enough in public"
    assert un.display_unit(MB, byg, public=False, units=GRP)["head"] == "345th Motor Rifle Regiment (7th Division)"
    assert un.display_unit(MC, byg, public=True, units=GRP)["head"].endswith("(в/ч 12345)")
    assert un.display_unit(MD, byg, public=False, units=GRP)["needs_disambiguation"]
    assert un.display_unit(DIV, by, public=True, units=UNITS)["head"] == "76th Guards Air Assault Division", "no sibling, no suffix"
    import contextlib as _c, io as _io
    with _c.redirect_stdout(_io.StringIO()) as out2:
        ul.check(GRP)
    assert "345-d: NOTHING" in out2.getvalue() and "345-a: parent" in out2.getvalue(), out2.getvalue()
    # A record with only the older free-text parent still narrows a lookup.
    old = {"slug": "345", "name_ru": "345-й полк 104-й дивизии", "unit_type": "regiment", "parent_grouping": "104-я дивизия"}
    other = {"slug": "345b", "name_ru": "345-й полк", "unit_type": "regiment", "parent_grouping": "7-я дивизия"}
    r = ul.lookup("345-й полк 104-й дивизии", [old, other])
    assert (r["state"], r["candidates"]) == ("resolved", ["345"]), r
    print("ok: unit_names / unit_lookup fixtures pass")


if __name__ == "__main__":
    main()
