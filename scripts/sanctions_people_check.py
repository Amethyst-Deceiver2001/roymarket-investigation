#!/usr/bin/env python3
"""Check registry people against the sanctions lists we hold, in one local pass (no network, no quota).

For each person it searches the full downloads in data/sources/ (EU consolidated XML, US OFAC SDN XML, UK Sanctions
List CSV) by name and prints the candidates with the list, the list's own id, the date of birth, the office or the
reasons, and a grade of how far the name agrees. It writes NOTHING into the registry: a hit is a work item (CLAUDE.md:
a tool's output is never a fact). What to do with a hit is the same chain we used by hand on 25.10.2026:

    1. name + patronymic + date of birth agree      -> read the first-listing act (eu_cellar.py find), OFAC's change
                                                       notice and Recent Actions page, the UK statement of reasons,
                                                       then record sanctions[] with those sources
    2. name + patronymic agree, no date of birth    -> an open question until a document ties the two (oq028)
    3. surname + first name only                    -> a lead, never recorded

    python3 scripts/sanctions_people_check.py --slug denis-pushilin --slug aleksandr-amelin
    python3 scripts/sanctions_people_check.py --pick 10          # the first 10 people with no sanctions[] yet
    python3 scripts/sanctions_people_check.py --pick 10 --out data/watch/sanctions/people_check_20261025.md

The lists are the ones the sanctions watch downloaded (SANCTIONS_EU_*, SANCTIONS_US_*) and the UK CSV with statements of
reasons (SANCTIONS_UK_*.csv); the newest of each is used. The Swiss SECO list (SANCTIONS_CH_*.xml) the Japan MOF list (SANCTIONS_JP_*.csv) the Australian DFAT list (SANCTIONS_AU_*.xlsx) the New Zealand MFAT register (SANCTIONS_NZ_*.xlsx) the Canadian SEMA list (SANCTIONS_CA_*.pdf; Russia and Belarus rows) and the UN Security Council list (SANCTIONS_UN_*.xml) are searched too. Names are compared with
ё folded to е and a plain transliteration, so «Водолацкий» finds VODOLATSKY, but a spelling the table does not
reach (a Ukrainian-form name, a different Latin rendering) can be missed: no hit is not a clean result.
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import re
import sys
try:  # the lists are downloads: parse with defusedxml where it is installed
    import defusedxml.ElementTree as ET
except ImportError:  # pragma: no cover
    import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "sources"

TR = {"а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh", "з": "z", "и": "i", "й": "y",
      "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f",
      "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch", "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu",
      "я": "ya", "і": "i", "ї": "yi", "є": "ye", "ґ": "g"}


def translit(s: str) -> str:
    out = "".join(TR.get(c, c) for c in s.lower())
    # collapse the renderings that differ between lists (y/i/j, double letters, ks/x, ii/iy/yy endings)
    out = re.sub(r"[^a-z ]", "", out)
    out = out.replace("kh", "h").replace("ts", "c").replace("ch", "c").replace("sh", "s").replace("zh", "z")
    out = out.replace("yu", "u").replace("ya", "a").replace("ye", "e").replace("yi", "i")
    out = re.sub(r"(.)\1+", r"\1", out)
    out = re.sub(r"[yj]", "i", out)
    out = re.sub(r"(ii|iy)\b", "i", out)
    out = out.replace("ck", "k").replace("x", "ks")
    return out


def tokens(name: str) -> list[str]:
    return [translit(t) for t in re.split(r"[\s,]+", name) if len(t) > 1]


def load_eu(path: Path) -> list[dict]:
    ln = lambda e: e.tag.split("}")[-1]
    out = []
    for ent in ET.parse(path).getroot().iter():
        if ln(ent) != "sanctionEntity":
            continue
        if "P" not in [c.attrib.get("classificationCode") for c in ent if ln(c) == "subjectType"]:
            continue
        names = [n.get("wholeName") or "" for n in ent.iter() if ln(n) == "nameAlias"]
        reg = [(c.attrib.get("numberTitle"), c.attrib.get("publicationDate")) for c in ent if ln(c) == "regulation"]
        dob = [c.attrib.get("birthdate") or c.attrib.get("year") or "" for c in ent if ln(c) == "birthdate"]
        out.append({"list": "EU", "id": ent.attrib.get("euReferenceNumber"), "names": names, "dob": [d for d in dob if d],
                    "info": "latest act " + "; ".join(f"{a} ({b})" for a, b in reg[:2])})
    return out


def load_us(path: Path) -> list[dict]:
    s = path.read_text(encoding="utf-8")
    out = []
    for m in re.finditer(r"<sdnEntry>.*?</sdnEntry>", s, re.S):
        b = m.group(0)
        if "<sdnType>Individual" not in b:
            continue
        first = re.search(r"<firstName>([^<]*)", b)
        last = re.search(r"<lastName>([^<]*)", b)
        names = [((first.group(1) + " ") if first else "") + (last.group(1) if last else "")]
        for a in re.finditer(r"<aka>.*?</aka>", b, re.S):
            f2, l2 = re.search(r"<firstName>([^<]*)", a.group(0)), re.search(r"<lastName>([^<]*)", a.group(0))
            names.append(((f2.group(1) + " ") if f2 else "") + (l2.group(1) if l2 else ""))
        out.append({"list": "US", "id": "SDN " + re.search(r"<uid>(\d+)", b).group(1), "names": names,
                    "dob": re.findall(r"<dateOfBirth>([^<]*)", b)[:2],
                    "info": "programmes " + ",".join(re.findall(r"<program>([^<]*)", b)) + "; " + "; ".join(re.findall(r"<remarks>([^<]*)", b))[:160]})
    return out


def load_uk(path: Path) -> list[dict]:
    f = path.open(encoding="utf-8-sig", newline="")
    f.readline()
    by: dict[str, dict] = {}
    for row in csv.DictReader(f):
        if row.get("Designation Type") != "Individual":
            continue
        e = by.setdefault(row["Unique ID"], {"list": "UK", "id": row["Unique ID"], "names": [], "dob": [],
                                             "info": (row.get("UK Statement of Reasons") or "").strip()[:220]})
        e["names"].append(" ".join(row.get(k, "") for k in ("Name 1", "Name 2", "Name 3", "Name 6")).strip())
        if row.get("Name non-latin script"):
            e["names"].append(row["Name non-latin script"])
        if row.get("D.O.B"):
            e["dob"].append(row["D.O.B"])
    return list(by.values())


def load_ch(path: Path) -> list[dict]:
    """SECO (SESAM) whole list: individuals, with every spelling variant (Latin and Cyrillic) as a name."""
    root = ET.parse(path).getroot()
    sets = {}
    for e in root.iter("sanctions-set"):
        if e.get("lang") == "eng":
            sets[e.get("ssid")] = (e.text or "").strip()
    seen: dict[str, dict] = {}
    for t in root.iter("target"):
        ind = t.find("individual")
        if ind is None:
            continue
        names, dob = [], []
        for ident in ind.iter("identity"):
            for nm in ident.iter("name"):
                parts = sorted(nm.iter("name-part"), key=lambda x: int(x.get("order", "0")))
                opts = [[(x.findtext("value") or "")] + [v.text or "" for v in x.iter("spelling-variant")] for x in parts]
                names.append(" ".join(o[0] for o in opts))
                for i in range(1, max((len(o) for o in opts), default=1)):
                    names.append(" ".join(o[i] if i < len(o) else o[0] for o in opts))
            for d in ident.iter("day-month-year"):
                if d.get("year"):
                    dob.append(f"{d.get('year')}-{int(d.get('month', 0)):02d}-{int(d.get('day', 0)):02d}" if d.get("day") and d.get("month") else d.get("year"))
        just = " ".join((j.text or "") for j in t.iter("justification"))[:200]
        sid = (t.findtext("sanctions-set-id") or "")
        key = "SECO " + t.get("ssid", "")
        if key in seen:      # SECO repeats a person once per version of the entry
            seen[key]["names"] += [n for n in names if n not in seen[key]["names"]]
            seen[key]["dob"] += [d for d in dob if d not in seen[key]["dob"]]
            continue
        seen[key] = {"list": "CH", "id": key, "names": names, "dob": dob, "info": (sets.get(sid, "") + "; " + just).strip("; ")}
    return list(seen.values())


def load_jp(path: Path) -> list[dict]:
    """Japan MOF asset-freeze list (all regimes, one CSV): individuals, English and Japanese names, the notice date."""
    out = []
    for row in csv.DictReader(path.open(encoding="utf-8-sig", newline="")):
        if row.get("個人・団体") != "個人":
            continue
        names = [row.get("氏名（英語）", ""), row.get("氏名（日本語）", "")]
        for k in ("別名・別称（英語）", "旧称（英語）"):
            names += [x.strip() for x in (row.get(k) or "").split(";") if x.strip()]
        out.append({"list": "JP", "id": "MOF " + row.get("番号", ""), "names": [n for n in names if n],
                    "dob": [row["生年月日"]] if row.get("生年月日") else [],
                    "info": f"notice {row.get('告示日付', '')}; {row.get('役職（英語）') or row.get('その他の情報', '')}"[:200]})
    return out


def xlsx_rows(path: Path, sheet: int = 1):
    """Rows of one sheet as {column letter: text}, read from the sheet XML (stdlib only; Strict OOXML needs this)."""
    import zipfile
    z = zipfile.ZipFile(path)
    ln = lambda e: e.tag.split("}")[-1]
    ss = ["".join(t.text or "" for t in si.iter() if ln(t) == "t") for si in ET.fromstring(z.read("xl/sharedStrings.xml"))]
    for r in ET.fromstring(z.read(f"xl/worksheets/sheet{sheet}.xml")).iter():
        if ln(r) != "row":
            continue
        d = {}
        for c in r:
            v = next((x.text for x in c if ln(x) == "v"), None)
            if v is not None:
                d[re.match(r"[A-Z]+", c.get("r")).group(0)] = ss[int(v)] if c.get("t") == "s" else v
        yield d


def excel_date(v: str) -> str:
    """An Excel serial day number as YYYY-MM-DD; text is returned as it is."""
    import datetime
    try:
        return (datetime.date(1899, 12, 30) + datetime.timedelta(days=int(float(v)))).isoformat()
    except (ValueError, OverflowError):
        return v


def load_au(path: Path) -> list[dict]:
    """Australian Sanctions Consolidated List (DFAT). The workbook is Strict OOXML, which openpyxl cannot open,
    so the sheet XML is read directly. One row per name; aliases share the reference number (2, 2a, 2b)."""
    by: dict[str, dict] = {}
    for d in xlsx_rows(path):
        if d.get("C") != "Individual":
            continue
        ref = re.match(r"\d+", d.get("A", ""))
        if not ref:
            continue
        e = by.setdefault(ref.group(0), {"list": "AU", "id": "DFAT " + ref.group(0), "names": [], "dob": [],
                                          "info": f"{d.get('O', '')}; {d.get('K', '')}"[:200]})
        e["names"].append(d.get("B", ""))
        if d.get("F"):
            e["dob"] += [x.strip() for x in d["F"].split(",") if x.strip() and x.strip() not in e["dob"]]
    return list(by.values())


def load_nz(path: Path) -> list[dict]:
    """New Zealand Russia Sanctions Register (MFAT), first sheet: individuals, with their alternate spellings.
    Columns: B id, C-E first/middle/last name, H DOB, I title, J aliases, R date of sanction."""
    out = []
    for d in xlsx_rows(path):
        if d.get("A") != "Individual":
            continue
        names = [" ".join(d[k] for k in ("C", "D", "E") if d.get(k))]
        names += [a.strip() for a in re.split(r"[;\n]", d.get("J", "")) if a.strip()]
        out.append({"list": "NZ", "id": d.get("B", ""), "names": names, "dob": [excel_date(d["H"])] if d.get("H") else [],
                    "info": f"sanctioned {excel_date(d.get('R', ''))}; {d.get('I', '')}"[:200]})
    return out


CA_REGIMES = ("Russia / Russie", "Belarus / Bélarus")
CA_TAIL = re.compile(r"\s(\d+(?:, Part [\d.]+)?)\s+(\d+)\s+(\d{4}-\d{2}-\d{2})$")


def ca_text(path: Path) -> str:
    """The Canadian list is a PDF table. Its text is extracted once (pypdf, in the roymarket311 venv) into a working
    file beside it (underscore name: not a catalogued source); the system python then reads that."""
    cache = path.with_name("_" + path.stem + ".txt")
    if not cache.exists():
        from pypdf import PdfReader
        cache.write_text("\n".join(pg.extract_text() for pg in PdfReader(path).pages), encoding="utf-8")
    return cache.read_text(encoding="utf-8")


def parse_ca(path: Path) -> list[dict]:
    """Russia and Belarus rows of the Canadian consolidated list (SEMA). One row per record: regime, name text (Latin
    and Cyrillic as printed), date of birth, schedule, item number, listing date. Schedule 1 Part 1 is persons."""
    rows, buf = [], ""
    for line in ca_text(path).split("\n"):
        if line.startswith("UNCLASSIFIED"):
            continue
        if not buf and not line.startswith(CA_REGIMES):
            continue
        buf = (buf + " " + line.strip()).strip()
        m = CA_TAIL.search(buf)
        if not m:
            if len(buf) > 700:      # a row that never closes (ships and the like): drop it, do not swallow the next
                buf = ""
            continue
        head = buf[:m.start()]
        for r in CA_REGIMES:
            if head.startswith(r):
                head = head[len(r):].strip()
        dob = re.search(r"\s(\d{4}(?:-\d{2}-\d{2})?)$", head)
        if dob:
            head = head[:dob.start()].strip()
        latin = re.split(r"[\u0400-\u04FF]", head, 1)[0].strip()
        cyr = head[len(latin):].strip()
        rows.append({"regime": buf.split(" / ")[0], "schedule": m.group(1), "item": m.group(2), "date": m.group(3),
                     "dob": dob.group(1) if dob else "", "latin": re.sub(r"\s+", " ", latin), "cyr": re.sub(r"\s+", " ", cyr)})
        buf = ""
    return rows


def load_ca(path: Path) -> list[dict]:
    out = []
    for r in parse_ca(path):
        if not r["schedule"].startswith("1, Part 1"):      # Part 1 (and Belarus Part 1.1): persons
            continue
        out.append({"list": "CA", "id": f"SEMA {r['regime']} {r['item']}", "names": [n for n in (r["latin"], r["cyr"]) if n],
                    "dob": [r["dob"]] if r["dob"] else [], "info": f"listed {r['date']}"})
    return out


def load_un(path: Path, kind: str = "INDIVIDUAL") -> list[dict]:
    """UN Security Council consolidated list. kind INDIVIDUAL or ENTITY (an entity's name is in FIRST_NAME)."""
    out = []
    for e in ET.parse(path).getroot().iter(kind):
        g = lambda tag: (e.findtext(tag) or "").strip()
        names = [" ".join(g(t) for t in ("FIRST_NAME", "SECOND_NAME", "THIRD_NAME", "FOURTH_NAME") if g(t))]
        alias_tag = "INDIVIDUAL_ALIAS" if kind == "INDIVIDUAL" else "ENTITY_ALIAS"
        names += [a.findtext("ALIAS_NAME").strip() for a in e.iter(alias_tag) if (a.findtext("ALIAS_NAME") or "").strip()]
        dob = []
        for d in e.iter("INDIVIDUAL_DATE_OF_BIRTH"):
            v = d.findtext("DATE") or d.findtext("YEAR") or ""
            if v:
                dob.append(v[:10])
        out.append({"list": "UN", "id": g("REFERENCE_NUMBER"), "names": names, "dob": dob,
                    "text": "", "info": f"{g('UN_LIST_TYPE')}; listed {g('LISTED_ON')}; {g('COMMENTS1')[:120]}"})
    return out


def newest(pattern: str) -> Path | None:
    files = sorted(glob.glob(str(SRC / pattern)))
    return Path(files[-1]) if files else None


def norm_dob(d: str) -> str:
    """To YYYY-MM-DD where the list gives a full date in a form we know; else ''."""
    d = d.strip()
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", d)
    if m:
        return d
    m = re.match(r"^(\d{4})/(\d{1,2})/(\d{1,2})$", d)      # Japan MOF
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", d)
    if m:
        return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    m = re.match(r"^(\d{1,2}) (\w{3}) (\d{4})$", d)
    if m:
        mo = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"].index(m.group(2).lower()[:3]) + 1
        return f"{m.group(3)}-{mo:02d}-{int(m.group(1)):02d}"
    return ""


PATRONYMIC = re.compile(r"(ovic|evic|ic|ovna|evna|icna|inicna)$")  # applied to the transliterated token


def surname_of(person_tokens: list[str]) -> str | None:
    """With three tokens and a patronymic, the first name sits next to it and the surname is the other end."""
    if len(person_tokens) != 3:
        return None
    if PATRONYMIC.search(person_tokens[1]):
        return person_tokens[2]
    if PATRONYMIC.search(person_tokens[2]):
        return person_tokens[0]
    return None


def grade(person_tokens: list[str], entry: dict, dob: str | None) -> tuple[str, str]:
    best = ("", "")
    sur = surname_of(person_tokens)
    for n in entry["names"]:
        et = tokens(n)
        hit = [t for t in person_tokens if t in et]
        if sur and sur not in hit:
            continue        # first name + patronymic alone is not a name match
        if len(person_tokens) >= 3 and len(hit) == len(person_tokens):
            g = "name+patronymic"
        elif len(person_tokens) >= 2 and len(hit) >= 2:
            g = "surname+first name"
        else:
            continue
        if not best[0] or g == "name+patronymic":
            best = (g, n)
    if best[0] and dob and any(norm_dob(d) == dob for d in entry["dob"]):
        best = ("name+patronymic+DOB" if best[0] == "name+patronymic" else "name+DOB", best[1])
    return best


LOG = ROOT / "data" / "watch" / "sanctions" / "people_checked.json"


def read_log() -> dict:
    return json.loads(LOG.read_text(encoding="utf-8")) if LOG.exists() else {}


def pick(people: list[dict], n: int) -> list[dict]:
    done = read_log()
    chosen = [p for p in people if not p.get("sanctions") and p.get("fio_ru") and p["slug"] not in done]
    # people whose OpenSanctions screen already flagged a sanction topic come first: they are the likeliest to be listed
    flagged = lambda p: any("sanction" in (m.get("topics") or []) and (m.get("score") or 0) >= 0.9 for m in p.get("opensanctions_matches") or [])
    chosen.sort(key=lambda p: not flagged(p))
    return chosen[:n]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--slug", action="append", default=[])
    ap.add_argument("--pick", type=int, default=0, help="the first N people with no sanctions[] yet")
    ap.add_argument("--out", default=None, help="write the report here too (markdown)")
    args = ap.parse_args()
    raw = json.load(open(ROOT / "data/registry/people.json", encoding="utf-8"))
    people = raw if isinstance(raw, list) else raw["people"]
    by = {p["slug"]: p for p in people}
    todo = [by[s] for s in args.slug if s in by] + (pick(people, args.pick) if args.pick else [])
    missing = [s for s in args.slug if s not in by]
    if missing:
        sys.exit("unknown slug: " + ", ".join(missing))
    if not todo:
        sys.exit("give --slug or --pick")
    lists, loaded = [], []
    for label, pat, fn in (("EU", "SANCTIONS_EU_*.xml", load_eu), ("US", "SANCTIONS_US_*.xml", load_us), ("UK", "SANCTIONS_UK_*.csv", load_uk), ("CH", "SANCTIONS_CH_*.xml", load_ch), ("JP", "SANCTIONS_JP_*.csv", load_jp), ("AU", "SANCTIONS_AU_*.xlsx", load_au), ("NZ", "SANCTIONS_NZ_*.xlsx", load_nz), ("CA", "SANCTIONS_CA_*.pdf", load_ca), ("UN", "SANCTIONS_UN_*.xml", load_un)):
        p = newest(pat)
        if p is None:
            loaded.append(f"{label}: no file")
            continue
        lists += fn(p)
        loaded.append(f"{label}: {p.name}")
    lines = ["# People against the sanctions lists we hold", "", "Lists: " + "; ".join(loaded) + ". A hit is a work item, not a fact; no hit is not a clean result.", ""]
    for p in todo:
        pt = tokens(p["fio_ru"])
        dob = p.get("dob")
        hits = []
        for e in lists:
            g, n = grade(pt, e, dob)
            if g:
                hits.append((g, e, n))
        order = {"name+patronymic+DOB": 0, "name+DOB": 1, "name+patronymic": 2, "surname+first name": 3}
        hits.sort(key=lambda h: order[h[0]])
        lines.append(f"## {p['fio_ru']} (`{p['slug']}`; DOB on record: {dob or 'none'})")
        if not hits:
            lines += ["no candidate on the three lists", ""]
            continue
        for g, e, n in hits[:12]:
            lines.append(f"- **{g}**: {e['list']} {e['id']}: {n}; DOB {', '.join(e['dob'][:2]) or 'not given'}; {e['info'][:200]}")
        if len(hits) > 12:
            lines.append(f"- … {len(hits) - 12} more weaker candidates not shown")
        lines.append("")
    text = "\n".join(lines)
    print(text)
    if args.pick:   # a --pick run remembers whom it looked at, so the next --pick takes the next people
        log = read_log()
        for p in todo:
            log.setdefault(p["slug"], __import__("datetime").date.today().isoformat())
        LOG.write_text(json.dumps(log, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
