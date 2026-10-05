#!/usr/bin/env python3
"""Normalise Russian military-unit names: number, type, arm, parent hint.

A unit is told apart by number + type + arm + parent formation, never by the number alone
(there are two 237th regiments). parse() reads one phrase; match() compares a query with
one name form of a record. Local text processing, no network, no model.
"""
from __future__ import annotations

import re

KINDS = {"army", "division", "brigade", "regiment", "battalion", "detachment"}
ARMS = {"tank", "air_assault", "airborne", "motor_rifle", "artillery", "recon", "spetsnaz", "marine", "engineer", "command"}
# Airborne is the branch, air assault a type inside it: a post may use either for one formation.
ARM_COMPATIBLE = {frozenset({"airborne", "air_assault"})}
NAME_FORMS = {"official", "short", "informal", "post_wording", "vch"}
PARENT_STATUS = {"stated", "lead", "open"}
NAME_GRADES = {"stated", "lead"}

_KIND_STEMS = (("дивизион", "battalion"), ("дивизи", "division"), ("бригад", "brigade"), ("полк", "regiment"),
               ("батальон", "battalion"), ("разведотряд", "detachment"), ("отряд", "detachment"), ("арми", "army"))
_ARM_STEMS = (("десантно-штурмов", "air_assault"), ("воздушно-десантн", "airborne"), ("танков", "tank"),
              ("мотострелков", "motor_rifle"), ("артиллерийск", "artillery"), ("разведыват", "recon"),
              ("специального назначения", "spetsnaz"), ("спецназ", "spetsnaz"), ("морской пехоты", "marine"),
              ("инженерно", "engineer"), ("разведк", "recon"), ("управления", "command"))
# abbreviation -> (kind, arm); an army or branch abbreviation carries only one of them.
_ABBR = {"тп": ("regiment", "tank"), "дшп": ("regiment", "air_assault"), "мсп": ("regiment", "motor_rifle"),
         "мсд": ("division", "motor_rifle"), "дшд": ("division", "air_assault"), "тд": ("division", "tank"),
         "дшб": ("brigade", "air_assault"), "омсбр": ("brigade", "motor_rifle"), "мсбр": ("brigade", "motor_rifle"),
         "обрмп": ("brigade", "marine"), "оа": ("army", None), "вдв": (None, "airborne"),
         "апп": ("regiment", "artillery"), "ап": ("regiment", "artillery"), "дшбр": ("brigade", "air_assault")}
_NUM = re.compile(r"^(\d{1,4})(?:-[а-я]{1,3})?$")
_TOKEN = re.compile(r"\d{1,6}(?:-[а-я]{1,3})?|[а-я]+(?:-[а-я]+)*|[a-z]+")
_VCH = re.compile(r"(?:войсковая часть|в/ч|вч)\s*№?\s*(\d{5})")


def fold(text: str) -> str:
    return (text or "").lower().replace("ё", "е")


def _word(tok: str) -> tuple[str | None, str | None]:
    """(kind, arm) a single token names, or (None, None)."""
    if tok in _ABBR:
        return _ABBR[tok]
    if tok.startswith("разведотряд"):
        return "detachment", "recon"
    kind = next((k for stem, k in _KIND_STEMS if tok.startswith(stem)), None)
    arm = next((a for stem, a in _ARM_STEMS if tok.startswith(stem)), None)
    return kind, arm


def _unit_at(tokens: list[str], i: int) -> tuple[dict, int] | None:
    """Read the unit whose number sits at tokens[i]; return it and the index after its type word."""
    m = _NUM.match(tokens[i])
    if not m:
        return None
    unit = {"number": int(m.group(1)), "kind": None, "arm": None, "guards": False}
    for j in range(i + 1, min(i + 7, len(tokens))):
        t = tokens[j]
        if _NUM.match(t):
            break
        if t.startswith("гвардейск"):
            unit["guards"] = True
            continue
        kind, arm = _word(t)
        if arm and not unit["arm"]:
            unit["arm"] = arm
        if kind:
            unit["kind"] = kind
            return unit, j + 1
    return unit, i + 1


def parse(text: str) -> dict:
    """{number, kind, arm, guards, parent} for a phrase; parent is the next numbered formation named."""
    folded = fold(text)
    vch = _VCH.search(folded)
    tokens = _TOKEN.findall(folded)
    first = None
    parents = []
    i = 0
    while i < len(tokens):
        got = _unit_at(tokens, i)
        if got:
            unit, nxt = got
            if first is None:
                first = unit
            elif unit["kind"] or unit["arm"]:
                parents.append(unit)
            i = max(nxt, i + 1)
        else:
            i += 1
    out = first or {"number": None, "kind": None, "arm": None, "guards": False}
    # "ВДВ" or an arm word after the type still tells the arm ("76-й бригады ВДВ").
    if not out["arm"]:
        nums = [k for k, t in enumerate(tokens) if _NUM.match(t)]
        end = nums[1] if len(nums) > 1 else len(tokens)  # stop before the parent's own words
        for t in tokens[:end]:
            kind, arm = _word(t)
            if arm and not kind:
                out["arm"] = arm
                break
    out["parent"] = parents[0] if parents else None
    out["vch"] = vch.group(1) if vch else None
    return out


def _arm_ok(a: str | None, b: str | None) -> bool:
    return not a or not b or a == b or frozenset({a, b}) in ARM_COMPATIBLE


def forms(unit: dict) -> list[dict]:
    """Every parsed name form of a record: its name_ru, its names[] and its legacy slugs."""
    texts = [unit.get("name_ru")] + [n.get("value") for n in unit.get("names") or []]
    out = []
    for t in texts:
        if t:
            p = parse(t)
            if p["number"] is not None:
                out.append(p)
    return out


def parents_of(unit: dict, by_slug: dict) -> list[dict]:
    """Parsed parents the record states or leads to (a parent_unit slug is resolved to its own form).

    A record with no parent_history falls back to the older free-text parent_grouping."""
    out = []
    if not unit.get("parent_history") and unit.get("parent_grouping"):
        p = parse(unit["parent_grouping"])
        return [p] if p["number"] is not None else []
    for h in unit.get("parent_history") or []:
        text = h.get("parent_text")
        if h.get("parent_unit") in by_slug:
            text = by_slug[h["parent_unit"]].get("name_ru") or text
        if text:
            p = parse(text)
            if p["number"] is not None:
                out.append(p)
    return out


def match(q: dict, f: dict) -> bool:
    return (q["number"] is not None and q["number"] == f["number"]
            and _arm_ok(q["arm"], f["arm"]) and (not q["kind"] or not f["kind"] or q["kind"] == f["kind"]))


def validate_unit(u: dict, slugs: set) -> list[str]:
    """Shape errors in the optional normalisation fields of one record (absent fields are fine)."""
    where, errs = f"military_units[{u.get('slug')}]", []
    if "number" in u and not (isinstance(u["number"], int) and u["number"] > 0):
        errs.append(f"{where}.number must be a positive integer")
    if u.get("arm") is not None and u["arm"] not in ARMS:
        errs.append(f"{where}.arm {u['arm']!r} must be one of {sorted(ARMS)}")
    for i, n in enumerate(u.get("names") or []):
        w = f"{where}.names[{i}]"
        if n.get("form") not in NAME_FORMS:
            errs.append(f"{w}.form {n.get('form')!r} must be one of {sorted(NAME_FORMS)}")
        if not (n.get("value") or "").strip():
            errs.append(f"{w}.value is required")
        if n.get("grade") not in NAME_GRADES:
            errs.append(f"{w}.grade {n.get('grade')!r} must be one of {sorted(NAME_GRADES)}")
        if n.get("grade") == "stated" and not n.get("source_id"):
            errs.append(f"{w} is graded stated but has no source_id")
    for i, h in enumerate(u.get("parent_history") or []):
        w = f"{where}.parent_history[{i}]"
        if h.get("status") not in PARENT_STATUS:
            errs.append(f"{w}.status {h.get('status')!r} must be one of {sorted(PARENT_STATUS)}")
        if not (h.get("parent_unit") or h.get("parent_text")):
            errs.append(f"{w} needs parent_unit or parent_text")
        if h.get("parent_unit") and h["parent_unit"] not in slugs:
            errs.append(f"{w}.parent_unit {h['parent_unit']!r} is not a unit slug")
        if h.get("status") == "stated" and not h.get("source_id"):
            errs.append(f"{w} is graded stated but has no source_id")
        if h.get("status") in ("lead", "open") and not (h.get("note") or "").strip():
            errs.append(f"{w} is a {h.get('status')} and must say in note where the lead came from")
    return errs


_ARM_EN = {"tank": "Tank", "air_assault": "Air Assault", "airborne": "Airborne", "motor_rifle": "Motor Rifle",
           "artillery": "Artillery", "recon": "Reconnaissance", "spetsnaz": "Spetsnaz", "marine": "Naval Infantry",
           "engineer": "Engineer", "command": "Command"}
_KIND_EN = {"army": "Army", "division": "Division", "brigade": "Brigade", "regiment": "Regiment",
            "battalion": "Battalion", "detachment": "Detachment"}


def ordinal_en(n: int) -> str:
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def is_guards(unit: dict) -> bool:
    """Guards status as a stated name form gives it (an official or post wording says «гвардейск»)."""
    return any("гвардейск" in fold(n.get("value")) for n in unit.get("names") or []
               if n.get("grade") == "stated") or "гвардейск" in fold(unit.get("name_ru"))


def name_en(unit: dict) -> str | None:
    """A generated descriptive English label from number, type, arm and guards: «237th Guards Air Assault Regiment».

    It is not an official English name and never translates honorifics; numberless units return None."""
    n = unit.get("number")
    if n is None:
        n = parse(unit.get("name_ru") or "")["number"]
    p = parse(unit.get("name_ru") or "")
    kind = unit.get("unit_type") if unit.get("unit_type") in _KIND_EN else p["kind"]
    if n is None or kind not in _KIND_EN:
        return None
    arm = unit.get("arm") or p["arm"]
    parts = [ordinal_en(n)] + (["Guards"] if is_guards(unit) else []) + ([_ARM_EN[arm]] if arm in _ARM_EN else []) + [_KIND_EN[kind]]
    return " ".join(parts)


def _en_parsed(p: dict) -> str | None:
    """English descriptor of a parsed phrase («3rd Motor Rifle Division»); None without a number."""
    if p.get("number") is None:
        return None
    parts = [ordinal_en(p["number"])] + (["Guards"] if p.get("guards") else []) \
        + ([_ARM_EN[p["arm"]]] if p.get("arm") in _ARM_EN else []) + ([_KIND_EN[p["kind"]]] if p.get("kind") in _KIND_EN else [])
    return " ".join(parts)


def siblings(unit: dict, units: list[dict]) -> list[dict]:
    """Other records that share this unit's number with a compatible type and arm: the ones a bare label would confuse."""
    mine = forms(unit)
    return [o for o in units if o.get("slug") != unit.get("slug")
            and any(match(f, g) for f in mine for g in forms(o))]


def disambiguator(unit: dict, by_slug: dict, public: bool = False) -> dict | None:
    """What tells this unit from a same-number sibling: its stated parent first, then a stated в/ч.

    Returns {kind: parent|vch, text, grade} or None when the record gives neither. A lead is offered on
    internal pages only, never on the public card, and always carries its grade."""
    for h in unit.get("parent_history") or []:
        if h.get("status") == "stated" or (not public and h.get("status") == "lead"):
            ref = by_slug.get(h.get("parent_unit"))
            text = (name_en(ref) if ref else None) or _en_parsed(parse(h.get("parent_text") or "")) or h.get("parent_text")
            if text:
                return {"kind": "parent", "text": text, "grade": h["status"]}
    if not unit.get("parent_history") and unit.get("parent_grouping"):
        text = _en_parsed(parse(unit["parent_grouping"]))
        if text:
            return {"kind": "parent", "text": text, "grade": "lead"} if not public else None
    for n in unit.get("names") or []:
        if n.get("form") == "vch" and (n.get("grade") == "stated" or not public):
            return {"kind": "vch", "text": n["value"], "grade": n.get("grade")}
    return None


def display_unit(unit: dict, by_slug: dict, public: bool = False, units: list[dict] | None = None) -> dict:
    """What a unit card shows: English label, best Russian name, and parent and в/ч each with its grade.

    The public card shows only `stated` items; leads appear on internal pages only."""
    names = unit.get("names") or []
    ru = next((n["value"] for f in ("official", "post_wording") for n in names
               if n.get("form") == f and n.get("grade") == "stated"), unit.get("name_ru"))
    keep = lambda g: g == "stated" or not public
    parents = [{"text": h.get("parent_text") or (by_slug.get(h.get("parent_unit")) or {}).get("name_ru"),
                "grade": h.get("status")} for h in unit.get("parent_history") or [] if keep(h.get("status"))]
    vch = [{"value": n["value"], "grade": n.get("grade")} for n in names if n.get("form") == "vch" and keep(n.get("grade"))]
    short = [n["value"] for n in names if n.get("form") == "short" and keep(n.get("grade"))]
    head = name_en(unit) or ru
    needs = False
    if units is not None and siblings(unit, units):
        d = disambiguator(unit, by_slug, public)
        if d:
            head = f"{head} ({d['text']})"
        else:
            needs = True  # a same-number sibling exists and this record states neither a parent nor a в/ч
    return {"head": head, "ru": ru, "short": short, "parents": parents, "vch": vch, "needs_disambiguation": needs}
