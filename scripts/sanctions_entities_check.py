#!/usr/bin/env python3
"""Check registry organisations against the lists the people check does not cover, in one local pass.

Lists (the newest SANCTIONS_* file of each in data/sources/): the US Consolidated Screening List without its OFAC
parts (Commerce Entity List, Military End User, Unverified, Denied Persons, State nonproliferation and ITAR), the New
Zealand register, Japan MOF, Australia DFAT and Switzerland SECO. The EU, US SDN and UK entity lists are covered by
sanctions_watch.py (identifier match) and are not searched here.

An organisation is a candidate when (1) an ИНН or ОГРН appears in the list entry's ids or remarks, or (2) its
distinctive name words (legal forms and generic words dropped, Cyrillic transliterated) match those of a list entry:
all words of the shorter name inside the longer, and at least one word of five letters or more. A candidate is a work
item, never an identity: a name match is a lead until an identifier, an address or a named person agrees. No candidate
is not a clean result: the Entity List mostly prints Latin names without Russian tax ids.

    python3 scripts/sanctions_entities_check.py [--slug SLUG ...] [--out FILE] [--min-words 1]
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sanctions_people_check as sp  # noqa: E402
from sanctions_people_check import ET, newest, translit, xlsx_rows  # noqa: E402

ROOT = sp.ROOT
OFAC_PARTS = ("Specially Designated", "Sectoral Sanctions", "Palestinian", "Capta", "Non-SDN Menu")
GENERIC = set("""ooo ao pao zao oao nko ano llc ltd jsc ojsc pjsc ogsc co company limited liability joint stock society
the of and for group holding centre center ce
obsestvo ogranicenoi otvetstvennostu akcionernoe publicnoe zakrytoe otkrytoe nauchno proizvodstvennoe predpriiatie
firma kompania gruppa kompaniia cent ceh ru com""".split())


# generic business words, folded the way names are (translit), so Latin and Cyrillic forms drop together
GENERIC |= {translit(w) for w in """center centre investments investment unmanned systems system technologies technology
bespilotnye sistemy tekhnologii tsentr centr investicii holding invest trade trading international industrial
production scientific research institute design bureau""".split()}
GENERIC |= {translit(w) for w in """общество с ограниченной ответственностью акционерное публичное закрытое открытое
непубличное научно производственное исследовательский институт предприятие компания группа""".split()}
GENERIC |= {translit(w) for w in """центр инвестиции инвестментс беспилотные системы технологии холдинг трейд торг""".split()}
GENERIC = {translit(w) for w in GENERIC} | GENERIC
RECORDED = {"CH": ("switzerland", "swiss", "seco"), "AU": ("australia",), "JP": ("japan",), "NZ": ("new zealand",),
            "Entity List (EL)": ("entity list", "bis"), "Military End User (MEU) List": ("military end user", "bis"),
            "Unverified List (UVL)": ("unverified",), "Denied Persons List (DPL)": ("denied persons",)}


def recorded(org: dict, lst: str) -> bool:
    keys = RECORDED.get(lst, ())
    blob = json.dumps(org.get("sanctions") or [], ensure_ascii=False).lower()
    return any(k in blob for k in keys)


def words(name: str) -> set[str]:
    return {w for w in translit(name).split() if w not in GENERIC and len(w) > 1}


def load_csl(path: Path) -> list[dict]:
    csv.field_size_limit(10**9)
    out = []
    for r in csv.DictReader(path.open(encoding="utf-8-sig", newline="")):
        if r["source"].startswith(OFAC_PARTS) or r["type"] in ("Individual", "Vessel", "Aircraft"):
            continue
        names = [r["name"]] + [a.strip() for a in re.split(r";", r.get("alt_names") or "") if a.strip()]
        out.append({"list": r["source"].split(" - ")[0], "id": r["entity_number"] or r["_id"], "names": names,
                    "text": (r.get("ids") or "") + " " + (r.get("remarks") or ""),
                    "info": f"{r.get('start_date', '')}; {r.get('addresses', '')}"[:200]})
    return out


def load_nz_ent(path: Path) -> list[dict]:
    out = []
    for d in xlsx_rows(path):
        if d.get("A") not in ("Entity", "Bank"):
            continue
        names = [d.get("F") or d.get("E") or ""] + [a.strip() for a in re.split(r"[;\n]", d.get("J", "")) if a.strip()]
        out.append({"list": "NZ", "id": d.get("B", ""), "names": [n for n in names if n], "text": "",
                    "info": f"sanctioned {sp.excel_date(d.get('R', ''))}; {d.get('K', '')}"[:200]})
    return out


def load_jp_ent(path: Path) -> list[dict]:
    out = []
    for r in csv.DictReader(path.open(encoding="utf-8-sig", newline="")):
        if r.get("個人・団体") == "個人":
            continue
        names = [r.get("氏名（英語）", "")] + [x.strip() for x in (r.get("別名・別称（英語）") or "").split(";") if x.strip()]
        out.append({"list": "JP", "id": "MOF " + r.get("番号", ""), "names": [n for n in names if n], "text": "",
                    "info": f"notice {r.get('告示日付', '')}; {r.get('住所・所在地（国）（英語）', '')}"[:200]})
    return out


def load_au_ent(path: Path) -> list[dict]:
    by: dict[str, dict] = {}
    for d in xlsx_rows(path):
        if d.get("C") != "Entity":
            continue
        ref = re.match(r"\d+", d.get("A", ""))
        if ref:
            e = by.setdefault(ref.group(0), {"list": "AU", "id": "DFAT " + ref.group(0), "names": [], "text": "",
                                              "info": f"{d.get('K', '')}; {d.get('I', '')}"[:200]})
            e["names"].append(d.get("B", ""))
    return list(by.values())


def load_ch_ent(path: Path) -> list[dict]:
    seen: dict[str, dict] = {}
    for t in ET.parse(path).getroot().iter("target"):
        ent = t.find("entity")
        if ent is None:
            continue
        names = []
        for nm in ent.iter("name"):
            for x in nm.iter("name-part"):
                names += [v for v in [x.findtext("value") or ""] + [s.text or "" for s in x.iter("spelling-variant")] if v]
        e = seen.setdefault("SECO " + t.get("ssid", ""), {"list": "CH", "id": "SECO " + t.get("ssid", ""), "names": [], "text": "", "info": ""})
        e["names"] += [n for n in names if n not in e["names"]]
    return list(seen.values())


def candidates(org: dict, entries: list[dict], min_words: int = 1) -> list[tuple[str, dict]]:
    ids = [org.get("inn"), org.get("ogrn")]
    ids = [i for i in ids if i]
    mine = [w for w in (words(n) for n in (org.get("name_ru"), org.get("name_latin"), org.get("name_en")) if n) if w]
    out = []
    for e in entries:
        if any(i in e["text"] for i in ids):
            out.append(("id", e))
            continue
        for n in e["names"]:
            theirs = words(n)
            if not theirs:
                continue
            for m in mine:
                small, big = (m, theirs) if len(m) <= len(theirs) else (theirs, m)
                if len(small) >= min_words and small <= big and any(len(w) >= 5 for w in small) and (len(small) >= 2 or small == big):
                    out.append(("name" if small == big else "name-part", e))
                    break
            else:
                continue
            break
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--slug", action="append", default=[])
    ap.add_argument("--out", default=None)
    ap.add_argument("--min-words", type=int, default=1)
    args = ap.parse_args()
    raw = json.load(open(ROOT / "data" / "registry" / "entities.json", encoding="utf-8"))
    ents = raw if isinstance(raw, list) else raw.get("entities", raw)
    todo = [e for e in ents if not args.slug or e["slug"] in args.slug]
    entries, loaded = [], []
    for label, pat, fn in (("CSL", "SANCTIONS_CSL_*.csv", load_csl), ("NZ", "SANCTIONS_NZ_*.xlsx", load_nz_ent),
                           ("JP", "SANCTIONS_JP_*.csv", load_jp_ent), ("AU", "SANCTIONS_AU_*.xlsx", load_au_ent),
                           ("CH", "SANCTIONS_CH_*.xml", load_ch_ent)):
        p = newest(pat)
        if p is None:
            loaded.append(f"{label}: no file")
            continue
        got = fn(p)
        entries += got
        loaded.append(f"{label}: {p.name} ({len(got)})")
    lines = ["# Organisations against the other sanctions lists we hold", "", "Lists: " + "; ".join(loaded) +
             ". A candidate is a work item, not a fact; no candidate is not a clean result.", ""]
    n = 0
    for org in todo:
        hits = candidates(org, entries, args.min_words)
        if not hits:
            continue
        n += 1
        lines.append(f"## {org.get('name_ru')} (`{org['slug']}`; ИНН {org.get('inn')})")
        for how, e in hits[:8]:
            lines.append(f"- **{how}**{' (list already in sanctions[])' if recorded(org, e['list']) else ''}: {e['list']} {e['id']}: {'; '.join(e['names'][:2])[:120]}; {e['info']}")
        if len(hits) > 8:
            lines.append(f"- ... {len(hits) - 8} more")
    lines.append("")
    lines.append(f"{n} of {len(todo)} organisations have at least one candidate.")
    text = "\n".join(lines)
    print(text)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
