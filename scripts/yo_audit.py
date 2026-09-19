#!/usr/bin/env python3
"""ё/е audit for proper names in data/registry/. Local, no network.

Policy (STYLE_GUIDE.md §2.5): matching folds ё to е everywhere; the stored and displayed
spelling uses ё where any source for that person or entity gives it. This script finds
the places where that is not yet true:

  same-person   a person's fio_ru has е, but another field of the SAME record spells a
                name word with ё (notes, role titles, Latin name "Kiselyov"...)
  cross-record  two records fold to the same name but are spelled differently
                (Барахтин Артём / Барахтин Артем)
  word-split    a capitalised name word that appears with ё in one record's name and with
                е in another's -- a lead only: Королёв and Королев are different surnames

Only same-person hits are safe to fix without a source; a cross-record or word-split hit
is a decision, because absence of ё in ЕГРЮЛ or a passport scan is not evidence of the
spelling (official documents mostly drop it).
"""
import collections
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORD = re.compile(r"[А-ЯЁ][а-яёА-ЯЁ\-]{2,}")


def load(name):
    d = json.load(open(os.path.join(ROOT, "data/registry", name), encoding="utf-8"))
    return d if isinstance(d, list) else next(v for v in d.values() if isinstance(v, list))


def fold(s):
    return s.lower().replace("ё", "е")


def own_text(person):
    parts = [person.get("notes") or "", person.get("name_latin") or ""]
    for r in person.get("roles") or []:
        parts += [str(r.get("title") or ""), str(r.get("body") or "")]
    return " ".join(parts)


def main():
    people = [p for p in load("people.json") if not p.get("_merged_into")]  # skip tombstones
    entities = [e for e in load("entities.json") if not e.get("_merged_into")]
    print("== same-person: fio_ru has е, own fields have ё ==")
    n = 0
    for p in people:
        fio = p.get("fio_ru") or ""
        text = own_text(p)
        for w in WORD.findall(fio):
            if "ё" not in w.lower():
                yo = [x for x in WORD.findall(text) if fold(x) == fold(w) and "ё" in x.lower()]
                if yo:
                    n += 1
                    print(f"  {p['slug']}: {w} -> {yo[0]}")
    print(f"  {n}")
    print("== cross-record: same folded name, different spelling ==")
    by = collections.defaultdict(dict)
    for p in people:
        if p.get("fio_ru"):
            by[re.sub(r"\s+", " ", fold(p["fio_ru"]))].setdefault(p["fio_ru"], []).append(p["slug"])
    for e in entities:
        if e.get("name_ru"):
            by[re.sub(r"\s+", " ", fold(e["name_ru"]))].setdefault(e["name_ru"], []).append(e["slug"])
    n = 0
    for k, forms in by.items():
        if len(forms) > 1:
            n += 1
            print("  " + " / ".join(f"{f} {s}" for f, s in forms.items()))
    print(f"  {n}")
    print("== word-split: a name word spelled both ways across records (leads only) ==")
    words = collections.defaultdict(lambda: collections.defaultdict(set))
    for p in people:
        for w in WORD.findall(p.get("fio_ru") or ""):
            words[fold(w)][w].add(p["slug"])
    n = 0
    for k, forms in words.items():
        if len(forms) > 1:
            n += 1
            print("  " + " / ".join(f"{f} ({len(s)})" for f, s in forms.items()))
    print(f"  {n}")


if __name__ == "__main__":
    main()
