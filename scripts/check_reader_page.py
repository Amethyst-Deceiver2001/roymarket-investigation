#!/usr/bin/env python3
"""Pre-publication check of a built reader page (a chain view, company file, story, landing page, matrix).

check_registry.py checks the registry; this checks what a page actually shows, before it leaves private preview:

- **english-first**: Cyrillic in visible text outside an RU popover, a card's registered name (`small.cyr`) or the
  source list (titles stay as published), and Cyrillic in alt text or aria labels (STYLE_GUIDE §2.1).
- **references**: every `#anchor` link and every popover control points at an element that exists; popover ids
  are unique (two equal ids open the wrong original).
- **notation**: internal notation in visible text: source and media ids, registry slugs, file names, field names.
- **sanctions**: every Sanctioned flag sits on a name that resolves to a registry record, and every regime it shows
  is one that record's sanctions[] backs under display_helpers.sanction_regimes (no unproven identity, no
  aggregator-only regime).
- **pii**: a person's date of birth or personal INN anywhere on the page, popovers included, unless the record
  carries a per-field source for it (`dob_source`, `inn_personal_source`).
- **tags**: open and close counts of the block tags check_tag_balance.py counts.

Errors exit 1. Warnings (a flag whose name does not resolve) are printed and do not fail the run.

    python3 scripts/check_reader_page.py exhibits/chain_bulat.html exhibits/story_01.html
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup, Comment

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from check_tag_balance import TAGS, scope_content  # noqa: E402
from display_helpers import sanction_regimes  # noqa: E402

CYR = re.compile(r"[А-Яа-яЁё]")
# visible-text notation that never belongs on a reader page
NOTATION = [
    (re.compile(r"\b[sm]\d{4}\b"), "source or media id"),
    (re.compile(r"\b(?:ooo|ao|pao|ano|ip|fond|npo|kb)-[a-z0-9]+(?:-[a-z0-9]+)+\b"), "registry slug"),
    (re.compile(r"\b[\w.-]+\.(?:json|py|pdf|zip|xlsx)\b"), "file name"),
    (re.compile(r"\b(?:data/sources|data/registry)\b"), "repository path"),
    (re.compile(r"\b\w+_(?:history|matches|id|tie|roles)\b"), "field name"),
    (re.compile(r"\bmsg \d+"), "message number (say the channel and date)"),
]
# containers whose Cyrillic is allowed: RU popovers, a card's registered name (small.cyr on cards, the names line on a
# company file), the source list (titles as published), lettering drawn in a figure (svg [lang=ru])
ALLOWED = "[popover], small.cyr, .names [lang=ru], .rm-sources, svg [lang=ru], script, style, template, noscript"
FOLD = str.maketrans({"ё": "е", "Ё": "Е", "«": "", "»": "", '"': "", "“": "", "”": "", "„": ""})


def norm_name(s: str) -> str:
    return " ".join((s or "").translate(FOLD).lower().split())


def load(name: str) -> list:
    d = json.loads((REPO / "data" / "registry" / name).read_text(encoding="utf-8"))
    return d if isinstance(d, list) else next(iter(d.values()))


class Registry:
    def __init__(self):
        self.people = load("people.json")
        self.by_name = {}
        for e in load("entities.json"):
            for n in [e.get("name_ru"), *(h.get("value") for h in e.get("name_history") or [] if isinstance(h, dict))]:
                if isinstance(n, str) and n:
                    self.by_name.setdefault(norm_name(n.split(" | ")[0]), e)
        for p in self.people:
            if p.get("fio_ru"):
                self.by_name.setdefault(norm_name(p["fio_ru"]), p)
        # a product card carries its maker's flag: a product name resolves to the maker's record
        ents = {e["slug"]: e for e in load("entities.json")}
        for pr in load("products.json"):
            if pr.get("name_ru") and pr.get("maker") in ents:
                self.by_name.setdefault(norm_name(pr["name_ru"]), ents[pr["maker"]])

    def find(self, names: list[str]):
        for n in names:
            r = self.by_name.get(norm_name(n))
            if r:
                return r
        return None


def check(path: Path, reg: Registry) -> tuple[list[str], list[str]]:
    raw = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(raw, "html.parser")
    errors, warnings = [], []
    allowed = set()
    for el in soup.select(ALLOWED):
        allowed.add(id(el))
        allowed.update(id(d) for d in el.descendants)

    def snip(t):
        t = " ".join(t.split())
        return t if len(t) <= 90 else t[:87] + "..."

    # english-first
    cyr = []
    for el in soup.find_all(string=CYR):
        if id(el) in allowed or isinstance(el, Comment) or not el.strip():
            continue
        cyr.append(snip(str(el)))
    for t in cyr:
        errors.append(f"english-first: Cyrillic outside an RU control: {t!r}")
    for el in soup.find_all(True):
        if id(el) in allowed:
            continue
        for attr in ("alt", "aria-label", "title"):
            v = el.get(attr)
            if isinstance(v, str) and CYR.search(v):
                errors.append(f"english-first: Cyrillic in {attr}=: {snip(v)!r}")

    # references
    ids = [el["id"] for el in soup.find_all(id=True)]
    idset = set(ids)
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        errors.append(f"references: id {dup!r} is used {ids.count(dup)} times")
    for a in soup.find_all(href=re.compile(r"^#.")):
        if a["href"][1:] not in idset:
            errors.append(f"references: link to #{a['href'][1:]} has no target")
    for b in soup.find_all(attrs={"popovertarget": True}):
        if b["popovertarget"] not in idset:
            errors.append(f"references: popover control for {b['popovertarget']!r} has no popover")

    # notation (visible text outside popovers; the source list is included: it must not leak ids either)
    for el in soup.find_all(string=True):
        if isinstance(el, Comment) or el.find_parent(["script", "style", "template", "noscript"]) or not el.strip():
            continue
        for rx, what in NOTATION:
            m = rx.search(str(el))
            if m:
                errors.append(f"notation: {what} {m.group(0)!r} in {snip(str(el))!r}")

    # sanctions
    for flag in soup.select(".rm-sanction"):
        shown = [x.strip() for x in (flag.b.get_text() if flag.b else "").split(",") if x.strip()]
        # the name the flag belongs to sits in the same item: the nearest list item, card, table row or figure
        item = flag.find_parent(["li", "article", "tr", "figure"]) or flag.parent
        names = [c.get_text(" ", strip=True) for c in item.select("small.cyr, [popover] .rm-nm-v[lang=ru]")]
        if not names:   # a flag in a page's own sanctions section is about the page's subject, named in its header
            head = (soup.find("h1") or soup).find_parent(["header", "section", "main"]) or soup
            names = [c.get_text(" ", strip=True) for c in head.select(".names [lang=ru], small.cyr")][:2]
        rec = reg.find(names)
        if rec is None:
            warnings.append(f"sanctions: flag {', '.join(shown) or '(no regime)'} sits on no name that resolves "
                            f"to a registry record (nearest names: {names[:2]})")
            continue
        backed = {lab for lab, _ in sanction_regimes(rec.get("sanctions"))}
        who = rec.get("name_ru") or rec.get("fio_ru")
        if not backed:
            errors.append(f"sanctions: {who} is flagged but has no proven official listing")
        for lab in shown:
            if lab not in backed:
                errors.append(f"sanctions: {who} shows {lab!r}, not backed by its sanctions[] ({sorted(backed)})")

    # pii (whole page, popovers included)
    text = soup.get_text(" ")
    for p in reg.people:
        dob = p.get("dob")
        if dob and not p.get("dob_source") and re.fullmatch(r"\d{4}-\d{2}-\d{2}", dob):
            y, mo, d = dob.split("-")
            for form in (dob, f"{d}.{mo}.{y}"):
                if form in text:
                    errors.append(f"pii: date of birth of {p.get('fio_ru')} ({form}) shown without a per-field source")
        inn = p.get("inn_personal")
        if inn and not p.get("inn_personal_source") and re.search(rf"(?<!\d){re.escape(str(inn))}(?!\d)", text):
            errors.append(f"pii: personal INN of {p.get('fio_ru')} shown without a per-field source")

    # tags
    seg, _ = scope_content(raw)
    for t in TAGS:
        o, c = len(re.findall(rf"<{t}[ >]", seg)), len(re.findall(rf"</{t}>", seg))
        if o != c:
            errors.append(f"tags: <{t}> opened {o}, closed {c}")
    return errors, warnings


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("pages", nargs="+")
    a = ap.parse_args(argv)
    reg, bad = Registry(), 0
    for page in a.pages:
        errors, warnings = check(Path(page), reg)
        print(f"{page}: {len(errors)} error(s), {len(warnings)} warning(s)")
        for e in errors:
            print(f"  ERROR {e}")
        for w in warnings:
            print(f"  warn  {w}")
        bad += bool(errors)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
