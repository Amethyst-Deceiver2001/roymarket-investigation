#!/usr/bin/env python3
"""Extract charter capital / founders / director from full signed ЕГРЮЛ
выписка PDFs already pulled by egrul_vypiska_pull.py.

Local file processing only (reads already-downloaded PDFs via pdftotext) --
no network calls, safe to run directly/repeatedly per CLAUDE.md's
crawling-jobs policy.

The выписка is a fixed, numbered-row layout (`пдфtotext -layout` keeps it
readable): a "Сведения об уставном капитале..." section carries one
"Размер (в рублях)" value; a "Сведения о лице, имеющем право без
доверенности..." section names the current director; a "Сведения об
участниках / учредителях юридического лица" section repeats one block per
founder -- either a legal-entity block (ОГРН/ИНН/Полное наименование) or an
individual block (Фамилия/Имя/Отчество/ИНН), each followed by "Номинальная
стоимость доли (в рублях)" and "Размер доли (в процентах)". Each fact's own
"ГРН и дата внесения в ЕГРЮЛ записи" line gives that specific fact's as_of
date -- NOT the выписка's own formation date, which is just when this copy
was pulled.

Usage:
    python3 scripts/parse_egrul_vypiska.py                 # all entities with an EGRUL_ pdf on file
    python3 scripts/parse_egrul_vypiska.py --inn 9731094770 # one entity
    python3 scripts/parse_egrul_vypiska.py --out data/registry/_egrul_vypiska.json
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTITIES = REPO / "data" / "registry" / "entities.json"
SOURCES = REPO / "data" / "registry" / "sources.json"

GRN_DATE_RE = re.compile(r"(\d{10,13})[\s\S]{0,120}?(\d{2}\.\d{2}\.\d{4})")
DATE_RE = re.compile(r"\d{2}\.\d{2}\.\d{4}")


def pdf_text(path: Path) -> str:
    out = subprocess.run(["pdftotext", "-layout", str(path), "-"],
                          capture_output=True, timeout=120)
    return out.stdout.decode("utf-8", errors="replace")


def to_iso(d: str) -> str | None:
    m = re.match(r"(\d{2})\.(\d{2})\.(\d{4})", d)
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else None


def section(text: str, start_marker: str, end_markers: list[str]) -> str | None:
    i = text.find(start_marker)
    if i == -1:
        return None
    j = len(text)
    for em in end_markers:
        k = text.find(em, i + len(start_marker))
        if k != -1:
            j = min(j, k)
    return text[i:j]


def first_grn_date_after(block: str, label: str) -> str | None:
    i = block.find(label)
    if i == -1:
        return None
    m = GRN_DATE_RE.search(block, i)
    return to_iso(m.group(2)) if m else None


def parse_capital(text: str) -> dict | None:
    sec = section(text, "Сведения об уставном капитале",
                  ["Сведения об участниках", "Сведения об учете"])
    if not sec:
        return None
    # Value is usually a plain integer but can carry kopecks as a decimal
    # (e.g. "13333.33" -- an unevenly divided share count) -- found
    # 2026-09-07 on ooo-vizionero, whose whole capital section was silently
    # dropped by an integer-only regex.
    m = re.search(r"Размер \(в рублях\)[ \t]+([\d ]+(?:[.,]\d+)?)\n", sec)
    if not m:
        return None
    raw = re.sub(r"\s", "", m.group(1)).replace(",", ".")
    value = float(raw) if "." in raw else int(raw)
    as_of = first_grn_date_after(sec, "Размер (в рублях)")
    return {"value": value, "as_of": as_of}


def parse_director(text: str) -> dict | None:
    sec = section(text, "Сведения о лице, имеющем право без доверенности",
                  ["Сведения об уставном капитале", "Сведения об участниках",
                   "Сведения о держателе реестра"])
    if not sec:
        return None
    if RESTRICTED_MARKER in sec:
        # ФЗ-129 access restriction covers the director too, not just
        # founders -- confirmed 2026-09-07 on ooo-mptm and the other 9
        # RESTRICTED entities parse_founders() flags.
        return {"restricted": True}
    m = re.search(r"Фамилия\s+(\S.*)\n\s*Имя\s+(\S.*)\n\s*Отчество\s+(\S.*)\n", sec)
    if not m:
        return None
    fam, im, otch = (g.strip() for g in m.groups())
    name = f"{fam.title()} {im.title()} {otch.title()}"
    m_inn = re.search(r"\bИНН\s+(\d{10,12})", sec)
    inn_personal = m_inn.group(1) if m_inn else None
    m_pos = re.search(r"Должность\s+(.+)", sec)
    position = m_pos.group(1).strip() if m_pos else None
    as_of = first_grn_date_after(sec, "Должность") or first_grn_date_after(sec, "Фамилия")
    return {"name": name, "inn_personal": inn_personal, "position": position, "as_of": as_of}


RESTRICTED_MARKER = "Доступ к сведениям ограничен"


def parse_founders(text: str) -> dict:
    """Returns {"founders": [...], "restricted": bool}. `restricted` flags
    the ФЗ-129 "Доступ к сведениям ограничен" marker -- ЕГРЮЛ actively
    withholding founder identity, not merely a section this parser missed.
    Found 2026-09-07 on 6 UAV-industry ООО entities (rustekhdron,
    ushkuynik-sp, gk-aeromaks, radiofid-sistemy, trimiks-bulat-3mx, mptm) --
    the first concrete instance of the data-closure risk the
    `egrul_uav_data_closure_risk_2025` memory flagged as still deliberating
    as of Dec 2025; it appears to already be in effect for at least these."""
    end_markers = ["Сведения об учете в налоговом органе",
                   "Сведения о регистрации в качестве страхователя",
                   "Сведения о держателе реестра акционеров"]
    sec = section(text, "Сведения об участниках", end_markers)
    if not sec:
        # АО (joint-stock) entities carry ownership under a differently
        # named section -- "Сведения о единственном акционере" only when
        # there is exactly one shareholder; a multi-shareholder АО's real
        # register sits with an external регистратор and is genuinely NOT
        # disclosed in this document at all (not a parser gap -- confirmed
        # 2026-09-07 across ao-prominvest/ao-npp-real/etc, which only ever
        # carry a "Сведения о держателе реестра акционеров" block naming
        # the registrar company, never the actual shareholders).
        sec = section(text, "Сведения о единственном акционере", end_markers)
        sole = True
    else:
        sole = False
    if not sec:
        return {"founders": [], "restricted": False}
    if RESTRICTED_MARKER in sec:
        return {"founders": [], "restricted": True}
    # Each founder block starts at its own "ГРН и дата внесения в ЕГРЮЛ
    # сведений о\n данном лице" marker (the block-open marker, distinct
    # from the per-fact "...записи, содержащей указанные сведения" ones
    # that recur inside a block).
    starts = [m.start() for m in re.finditer(r"ГРН и дата внесения в ЕГРЮЛ сведений о", sec)]
    if not starts:
        return {"founders": [], "restricted": False}
    starts.append(len(sec))
    founders = []
    for a, b in zip(starts, starts[1:]):
        block = sec[a:b]
        entry: dict = {}
        m_ogrn = re.search(r"\bОГРН\s+(\d{13,15})", block)
        m_name = re.search(r"Полное наименование\s+(.+?)(?:\n\s*\d+\s+ГРН|\n\n|$)", block, re.S)
        m_fam = re.search(r"Фамилия\s+(\S.*)\n\s*Имя\s+(\S.*)\n\s*Отчество\s+(\S.*)\n", block)
        if m_ogrn and m_name:
            entry["ogrn"] = m_ogrn.group(1)
            entry["name"] = re.sub(r"\s+", " ", m_name.group(1)).strip()
            m_inn = re.search(r"\bИНН\s+(\d{10})\b", block)
            if m_inn:
                entry["inn"] = m_inn.group(1)
        elif m_fam:
            fam, im, otch = (g.strip() for g in m_fam.groups())
            entry["name"] = f"{fam.title()} {im.title()} {otch.title()}"
            m_inn = re.search(r"\bИНН\s+(\d{12})\b", block)
            if m_inn:
                entry["inn_personal"] = m_inn.group(1)
        else:
            continue  # not a recognisable founder block (e.g. РФ/regional govt owner -- rare, skip rather than guess)

        m_nom = re.search(r"Номинальная стоимость доли \(в рублях\)[ \t]+([\d ]+(?:[.,]\d+)?)\n", block)
        if m_nom:
            raw_nom = re.sub(r"\s", "", m_nom.group(1)).replace(",", ".")
            entry["nominal_value"] = float(raw_nom) if "." in raw_nom else int(raw_nom)
        m_pct = re.search(r"Размер доли \(в процентах\)[ \t]+([\d.,]+)", block)
        if m_pct:
            entry["share_percent"] = float(m_pct.group(1).replace(",", "."))
        elif sole:
            # "единственном акционере" carries no explicit percent line --
            # sole ownership implies 100% by definition of the section.
            entry["share_percent"] = 100.0
        as_of = first_grn_date_after(block, "Номинальная стоимость доли") \
            or first_grn_date_after(block, "ГРН и дата внесения в ЕГРЮЛ сведений о")
        if as_of:
            entry["as_of"] = as_of
        founders.append(entry)
    return {"founders": founders, "restricted": False}


def parse_one(path: Path) -> dict:
    text = pdf_text(path)
    fr = parse_founders(text)
    return {
        "capital": parse_capital(text),
        "director": parse_director(text),
        "founders": fr["founders"],
        "founders_restricted": fr["restricted"],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--inn", default=None)
    ap.add_argument("--out", default="data/registry/_egrul_vypiska.json")
    args = ap.parse_args()

    entities = json.loads(ENTITIES.read_text(encoding="utf-8"))
    sources = json.loads(SOURCES.read_text(encoding="utf-8"))
    target_inns = {e["inn"] for e in entities if e.get("inn")}
    if args.inn:
        target_inns = {args.inn}
    slug_by_inn = {e["inn"]: e.get("slug") for e in entities if e.get("inn")}

    # Filename is authoritative for which ИНН filed this выписка (same
    # rationale as parse_bfo_financials.py: a filing's `inns` list includes
    # related parties -- director, founders -- not just the filer, and is
    # not ordered filer-first). Match on the EGRUL_<INN>_<date>_ filename
    # shape directly rather than on `type`, since egrul_batch_pull.py's
    # lightweight JSON snapshots are typed identically ("egrul").
    vypiska_sources = [s for s in sources
                        if re.match(r"^EGRUL_\d{10,12}_\d{8}_",
                                    Path(s.get("path", "")).name)]
    print(f"{len(vypiska_sources)} EGRUL выписка(s) to parse across {len(target_inns)} target ИНН")

    results: dict[str, dict] = {}
    for i, src in enumerate(vypiska_sources, 1):
        path = REPO / src["path"]
        m = re.match(r"EGRUL_(\d{10,12})_", Path(src["path"]).name)
        inn = m.group(1) if m else None
        if inn is None or inn not in target_inns:
            continue
        slug = slug_by_inn.get(inn, inn)
        try:
            parsed = parse_one(path)
        except Exception as e:
            print(f"  [{i}/{len(vypiska_sources)}] {src['id']} {slug}: FAILED {e}")
            continue
        parsed["source_id"] = src["id"]
        parsed["inn"] = inn
        results[slug] = parsed
        cap = parsed["capital"]["value"] if parsed["capital"] else None
        n_founders = len(parsed["founders"])
        restr = " FOUNDERS-RESTRICTED" if parsed["founders_restricted"] else ""
        d = parsed["director"]
        director = "RESTRICTED" if (d and d.get("restricted")) else (d["name"] if d else None)
        print(f"  [{i}/{len(vypiska_sources)}] {src['id']} {slug}: "
              f"capital={cap} founders={n_founders}{restr} director={director}")

    out_path = REPO / args.out
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out_path} ({len(results)} entities)")


if __name__ == "__main__":
    main()
