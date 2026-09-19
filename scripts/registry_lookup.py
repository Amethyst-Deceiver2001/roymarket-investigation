#!/usr/bin/env python3
"""Fuzzy lookup of a name against every entity and person in data/registry/.

Why this exists: on 2026-09-19 the graph builder reported Фонд «Градислава» as an
"unresolved stub" although it was in entities.json all along -- the record's name_ru is
"Фонд «Градислава» | historic & cultural heritage preservation" and the exact-string
index missed the plain name. A miss like that reads as "we have no record", which is
the one claim a sanctions submission cannot afford to get wrong. So a name is never
called unrecorded until it has been through this lookup.

Local, no network. Usage:

    python3 scripts/registry_lookup.py "Фонд Градислава" "OOO Kronshtadt"
    python3 scripts/registry_lookup.py --stubs      # every unresolved stub in the graph
    python3 scripts/registry_lookup.py --nulls      # related/parent/subsidiary refs with no slug

Match tiers, strongest first (a lower tier is a lead to read, never an automatic merge):
  exact     same name after dropping quotes, case, legal form (ООО/АО/Фонд...), ё->е,
            and after splitting a " | " alias -- what the graph builder already does
  translit  same name once Cyrillic is transliterated to Latin, or vice versa
  contains  every word of the shorter name occurs in the longer one (2+ words)
  fuzzy     character similarity >= 0.86
  initials  surname + initials ("Руденко Д.А.") matches a person's surname and BOTH
            initials -- always ambiguous evidence, since common surnames collide
"""
import argparse
import difflib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from build_relationship_graph import normalize  # noqa: E402  (same normaliser as the graph)

_CYR = dict(zip(
    "абвгдежзийклмнопрстуфхцчшщъыьэюя",
    ["a", "b", "v", "g", "d", "e", "zh", "z", "i", "i", "k", "l", "m", "n", "o", "p", "r", "s",
     "t", "u", "f", "kh", "ts", "ch", "sh", "shch", "", "y", "", "e", "yu", "ya"]))
_LATIN_FORMS = re.compile(
    r"\b(?:llc|ooo|oao|zao|pao|ao|ano|jsc|ltd|limited liability company|joint[- ]stock company|"
    r"autonomous non[- ]profit organi[sz]ation|foundation|fund|the|of|and)\b", re.I)


def translit(s: str) -> str:
    return "".join(_CYR.get(ch, ch) for ch in s.lower().replace("ё", "е"))


def key_latin(s: str) -> str:
    s = _LATIN_FORMS.sub(" ", s.lower())
    s = re.sub(r"(?<=[bcdfghjklmnpqrstvwxz])yo|(?<=\b)yo", "e", s)  # Kiselyov/Kiselev, Artyom/Artem
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def key_cyr(s: str) -> str:
    return normalize(s).replace("ё", "е")


def _load(name):
    d = json.load(open(os.path.join(ROOT, "data/registry", name), encoding="utf-8"))
    return d if isinstance(d, list) else next(v for v in d.values() if isinstance(v, list))


def _same_but_surname(a: str, b: str) -> bool:
    """People: a fuzzy hit counts only when the given name and patronymic agree exactly and
    one word differs by a spelling variant (Сиразетдинов/Сиразатдинов). Whole-string similarity
    alone pairs unrelated people who share a first name and patronymic."""
    ta, tb = a.split(), b.split()
    if len(ta) != 3 or len(tb) != 3:
        return False
    diff = [(x, y) for x, y in zip(ta, tb) if x != y]
    return len(diff) == 1 and difflib.SequenceMatcher(None, *diff[0]).ratio() >= 0.9


class Registry:
    def __init__(self):
        self.records = []  # (slug, kind, label, [(field, string)])
        self.merged = {}   # tombstone slug -> canonical slug (_merged_into)
        for e in _load("entities.json"):
            if e.get("_merged_into"):
                self.merged[e["slug"]] = e["_merged_into"]
            names = [("name_ru", e.get("name_ru")), ("brand_ru", e.get("brand_ru")),
                     ("name_latin", e.get("name_latin")), ("brand_latin", e.get("brand_latin"))]
            names += [("name_history", h.get("value")) for h in e.get("name_history") or []
                      if isinstance(h, dict)]
            self.records.append((e["slug"], "entity", e.get("name_ru") or e["slug"], self._expand(names)))
        for p in _load("people.json"):
            if p.get("_merged_into"):
                self.merged[p["slug"]] = p["_merged_into"]
            names = [("fio_ru", p.get("fio_ru")), ("name_latin", p.get("name_latin"))]
            self.records.append((p["slug"], "person", p.get("fio_ru") or p["slug"], self._expand(names)))
        self.by_key = {}
        for slug, kind, label, names in self.records:
            for field, s in names:
                for k in self._keys(s):
                    self.by_key.setdefault(k, []).append((slug, kind, label, field))

    @staticmethod
    def _expand(names):
        out = []
        for field, s in names:
            if not s or not isinstance(s, str):
                continue
            out.append((field, s))
            out += [(field + "-alias", part) for part in s.split(" | ") if part != s and part.strip()]
        return out

    @staticmethod
    def _keys(s):
        keys = {key_cyr(s)}
        if re.search(r"[A-Za-z]", s):
            keys.add(key_latin(s))
        if re.search(r"[А-Яа-яЁё]", s):
            keys.add(key_latin(translit(key_cyr(s))))
        keys.discard("")
        return keys

    def find(self, query: str, kinds=("entity", "person")):
        """Return [(tier, score, slug, kind, label, matched_field)], strongest first."""
        hits, seen = [], set()

        def add(tier, score, slug, kind, label, field):
            if slug in self.merged:  # a tombstone answers with the record it was merged into
                field, slug = f"{field}; tombstone of {self.merged[slug]}", self.merged[slug]
            if kind in kinds and (slug, tier) not in seen:
                seen.add((slug, tier))
                hits.append((tier, score, slug, kind, label, field))

        qkeys = self._keys(query)
        cyr_key = key_cyr(query)
        for k in qkeys:
            for slug, kind, label, field in self.by_key.get(k, []):
                exact = k == cyr_key and not field.endswith("alias") or k == cyr_key
                add("exact" if exact else "translit", 1.0, slug, kind, label, field)
        exact_slugs = {h[2] for h in hits}
        qtok = set(cyr_key.split()) | set(key_latin(translit(cyr_key)).split())
        for k, refs in self.by_key.items():
            ktok = set(k.split())
            for slug, kind, label, field in refs:
                if slug in exact_slugs:
                    continue
                short, long_ = (qtok, ktok) if len(qtok) <= len(ktok) else (ktok, qtok)
                if len(short) >= 2 and short <= long_ and sum(map(len, short)) >= 8:
                    add("contains", 0.9, slug, kind, label, field)
                    continue
                if min(len(k), len(cyr_key)) >= 6:
                    r = difflib.SequenceMatcher(None, cyr_key, k).ratio()
                    if r >= 0.86 and (kind != "person" or _same_but_surname(cyr_key, k)):
                        add("fuzzy", round(r, 2), slug, kind, label, field)
        m = re.match(r"^([А-ЯЁ][а-яё\-]+)\s+([А-ЯЁ])\.\s?([А-ЯЁ])\b", query.strip())
        if m and "person" in kinds:
            sur, i1, i2 = (x.lower().replace("ё", "е") for x in m.groups())
            for slug, kind, label, names in self.records:
                if kind != "person":
                    continue
                toks = [t.lower().replace("ё", "е") for t in (label or "").split()]
                if len(toks) == 3 and sur in (toks[0], toks[2]):
                    rest = [t for t in toks if t != sur] if toks.count(sur) == 1 else []
                    given, patr = (rest[0], rest[1]) if toks[0] == sur else (rest[0], rest[1])
                    if len(rest) == 2 and given[0] == i1 and patr[0] == i2:
                        add("initials", 0.6, slug, kind, label, "fio_ru")
        order = {"exact": 0, "translit": 1, "contains": 2, "fuzzy": 3, "initials": 4}
        best = {}
        for h in sorted(hits, key=lambda h: (order[h[0]], -h[1])):
            best.setdefault(h[2], h)  # one row per record, strongest tier
        return list(best.values())


def _stub_names():
    g = json.load(open(os.path.join(ROOT, "data/registry/relationship_graph.json"), encoding="utf-8"))
    return [n["label"] for n in g["nodes"] if n["kind"] == "unresolved"]


def _null_refs():
    out = []
    for e in _load("entities.json"):
        for key in ("related_entities", "parents", "subsidiaries"):
            for r in e.get(key) or []:
                if isinstance(r, dict) and not r.get("slug") and (r.get("name") or r.get("name_ru")):
                    out.append((f"{e['slug']}.{key}", r.get("name") or r.get("name_ru")))
    return out


_FORMS = ("ооо", "оао", "зао", "пао", "ао", "ано", "фгуп", "ип", "llc", "ooo", "jsc")


def _form(s):
    m = re.match(r"^\s*(" + "|".join(_FORMS) + r")\b", s.lower())
    return m.group(1) if m else None


def report(items, reg, show_none=False):
    n_hit = 0
    for where, name in items:
        hits = [h for h in reg.find(name)][:4]
        if hits:
            n_hit += 1
            print(f"{name}   [{where}]")
            for tier, score, slug, kind, label, field in hits:
                fq, fc = _form(name), _form(label)
                warn = "  !legal form differs" if kind == "entity" and fq and fc and fq != fc else ""
                print(f"    {tier:8} {score:.2f}  {kind:6} {slug}  <- {label[:60]}  ({field}){warn}")
        elif show_none:
            print(f"{name}   [{where}]\n    no candidate")
    print(f"\n{n_hit} of {len(items)} have at least one candidate")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("names", nargs="*")
    ap.add_argument("--stubs", action="store_true")
    ap.add_argument("--nulls", action="store_true")
    ap.add_argument("--all", action="store_true", help="also print names with no candidate")
    a = ap.parse_args()
    reg = Registry()
    items = [("query", n) for n in a.names]
    if a.stubs:
        items += [("graph stub", n) for n in _stub_names()]
    if a.nulls:
        items += _null_refs()
    if not items:
        ap.error("give a name, --stubs or --nulls")
    report(items, reg, show_none=a.all or bool(a.names))


if __name__ == "__main__":
    main()
