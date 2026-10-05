#!/usr/bin/env python3
"""Normalise Russian military-unit names: number, type, arm, parent hint.

A unit is told apart by number + type + arm + parent formation, never by the number alone
(there are two 237th regiments). parse() reads one phrase; match() compares a query with
one name form of a record. Local text processing, no network, no model.
"""
from __future__ import annotations

import re

KINDS = {"army", "division", "brigade", "regiment", "battalion", "detachment"}
ARMS = {"tank", "air_assault", "airborne", "motor_rifle", "artillery", "recon", "spetsnaz", "marine", "engineer", "signals"}
# Airborne is the branch, air assault a type inside it: a post may use either for one formation.
ARM_COMPATIBLE = {frozenset({"airborne", "air_assault"})}
NAME_FORMS = {"official", "short", "informal", "post_wording", "vch"}
PARENT_STATUS = {"stated", "lead", "open"}
NAME_GRADES = {"stated", "lead"}

_KIND_STEMS = (("дивизион", "battalion"), ("дивизи", "division"), ("бригад", "brigade"), ("полк", "regiment"),
               ("батальон", "battalion"), ("разведотряд", "detachment"), ("отряд", "detachment"), ("арми", "army"))
_ARM_STEMS = (("десантно-штурмов", "air_assault"), ("воздушно-десантн", "airborne"), ("танков", "tank"),
              ("мотострелков", "motor_rifle"), ("артиллерийск", "artillery"), ("разведыват", "recon"),
              ("специального назначения", "spetsnaz"), ("морской пехоты", "marine"), ("инженерно", "engineer"),
              ("управления", "signals"))
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
    """Parsed parents the record states or leads to (a parent_unit slug is resolved to its own form)."""
    out = []
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
