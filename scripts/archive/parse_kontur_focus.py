#!/usr/bin/env python3
"""Parse a Kontur.Focus Pro company-profile PDF export into structured data.

**Added 2026-09-08.** The user confirmed Kontur.Focus Pro exports will be a
*recurring* input to this project (their own paid-subscription pulls, not a
scrape) — this replaces the one-off manual read done for АНО «НПЦ
«Ушкуйник»» (see notes/full_pipeline_catalogue.md and the
ushkuynik_kontur_teardown Artifact) with a repeatable parser.

Kontur.Focus Pro exports follow a fixed template regardless of the entity —
confirmed by comparing the Ушкуйник and Гагаринг pulls — so this parses
generically rather than per-entity:

  - Header block: full/short name, status, ИНН/КПП/ОГРН, reg. date,
    address, phone, director (name + personal ИНН + date), main ОКВЭД,
    ОКПО/statistical codes, a "Статистика" mini-summary (balance/revenue/
    profit-or-loss for the latest year, gov. contract totals).
  - Виды деятельности — full ОКВЭД list (code + name), usually richer than
    what an EGRUL extract alone carries.
  - Учредители и участники — founders/participants with ИНН, share, date.
  - Конечные владельцы — Kontur's own computed beneficial-ownership chain
    (indirect %), NOT the same as учредители — see
    [[egrul_uchastiya_vs_uchrediteli]] for the general distinction; this is
    Kontur's own derived layer, not a primary-source fact by itself.
  - Арбитраж (истец/ответчик/третье лицо/другое) — case number, date, role,
    claimed amount, and an AI-generated case annotation (Kontur states this
    is machine-generated and may contain errors — treat accordingly, same
    caution as any LLM-summarized source).
  - Форма №1/2/4/6 — balance sheet / P&L / cash flow / (for non-profits)
    ОЦИС, by year, in тыс. руб. — same units caveat as
    [[verify_bfo_units_against_known_figure]].
  - Госзакупки – Участник / Заказчик — contract lists, both roles.
  - Ближайшие связи — Kontur's own affiliated-entity graph. This is the
    single most valuable non-primary-source layer in the document: it
    surfaces adjacent legal entities (co-founders, sister organizations,
    the founding ministry, etc.) that may not yet be in this project's own
    registry at all. Confirmed useful on the first real pull: the Ушкуйник
    export's "Ближайшие связи" surfaced АНО «НПЦ БАС «Белгород»» and АНО
    «НПЦ БАС «Протос»» — sister organizations under the same АНО «Платформа
    НТИ» founder, neither previously tracked here.
  - ЭКГ-рейтинг — cross-validates scripts/screen_ekg_rating.py's own live
    pull (confirmed identical on the first parse: 83/15/32/36 both ways).

**What this script does NOT do**: it does not silently write litigation[],
government_contracts[], financials[], or founders_history[] into
entities.json. Those are human-conclusion fields (see CLAUDE.md's
corrections.json section) and this document's litigation/procurement
entries substantially overlap with what zakupki_batch_pull.py /
kad.arbitr.ru manual pulls may have already wired — auto-writing risks
silent duplication. Instead this script:
  1. Writes the full parsed structure to
     data/registry/_kontur_focus_cache.json, keyed by ИНН (a structured
     cache, same pattern as _source_content_cache.json).
  2. Writes a compact RAW summary directly onto entities.json —
     `kontur_focus_matches` (status/ЭКГ/counts) + `kontur_focus_checked_at`
     — since that's fetched screening-style corroboration, same tier as
     `checko_status`. Added to ENTITY_CARRY_FORWARD_FIELDS in
     extract_registry.py.
  3. Prints a review scaffold: litigation cases / gov. contracts /
     affiliated-network entities that don't already appear (by case/
     contract number, or by ИНН for the network) in entities.json — a work
     queue for a human to verify and wire via corrections.json, the same
     discipline as _scaffold_leads.json.

This is local file processing over a PDF the user already downloaded (their
own Kontur.Focus Pro subscription) — no network call, safe to run directly/
repeatedly, not covered by CLAUDE.md's crawling-jobs policy.

Usage:
    python3 scripts/parse_kontur_focus.py --pdf data/sources/CHECKO_5300010714_20260908_ano-npts-ushkuynik.pdf
    python3 scripts/parse_kontur_focus.py --pdf <path> --slug ano-npts-ushkuynik --source-id s7369
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTITIES = REPO / "data" / "registry" / "entities.json"
CACHE = REPO / "data" / "registry" / "_kontur_focus_cache.json"

MONTHS_RU = {
    "января": 1, "февраля": 2, "марта": 3, "апреля": 4, "мая": 5, "июня": 6,
    "июля": 7, "августа": 8, "сентября": 9, "октября": 10, "ноября": 11, "декабря": 12,
}


def pdf_text(path: Path) -> str:
    out = subprocess.run(
        ["pdftotext", "-layout", str(path), "-"],
        capture_output=True, check=True, text=True,
    ).stdout
    return out.replace("\x0c", "")  # page-break form-feeds land mid-line, breaking regexes


def to_number(tok: str):
    tok = tok.strip()
    if tok in ("–", "-", "", "—"):
        return None
    neg = False
    if tok.startswith("(") and tok.endswith(")"):
        neg = True
        tok = tok[1:-1]
    tok = tok.replace(" ", "").replace(" ", "").replace(",", ".")
    try:
        val = float(tok) if "." in tok else int(tok)
    except ValueError:
        return None
    return -abs(val) if neg else val


def ru_date_to_iso(text: str) -> str | None:
    m = re.search(r"(\d{1,2})\s+([а-я]+)\s+(\d{4})", text)
    if not m:
        return None
    day, month_ru, year = m.groups()
    month = MONTHS_RU.get(month_ru.lower())
    if not month:
        return None
    return f"{int(year):04d}-{month:02d}-{int(day):02d}"


HEADER_LABELS = [
    "Полное наименование", "Краткое наименование", "Статус", "ИНН", "КПП", "ОГРН",
    "Дата регистрации", "Юр. адрес", "Код налог. органа", "Дата пост. на учет",
    "Телефоны", "Генеральный директор", "Директор", "Основной вид", "ОКПО",
    "Рег. номер ПФР", "Рег. номер ФСС", "ОКАТО", "ОКТМО", "ОКОПФ", "ОКОГУ", "ОКФС",
    "Статистика", "Маркеры",
]
_TRAILING_DATE_RE = re.compile(r"\s+(\d{2}\.\d{2}\.\d{4}|–)\s*(\(.*\))?\s*$")


def parse_header(text: str) -> dict:
    block = text.split("Виды деятельности (", 1)[0]
    lines = block.splitlines()
    fields: dict[str, str] = {}
    current_key = None
    for line in lines:
        if not line.strip():
            continue
        matched = None
        for label in HEADER_LABELS:
            if line.strip().startswith(label) and (
                len(line.strip()) == len(label) or line.strip()[len(label)] in " :"
            ):
                matched = label
                break
        if matched:
            rest = line.strip()[len(matched):].strip()
            rest = _TRAILING_DATE_RE.sub("", rest).strip()
            current_key = matched
            fields[current_key] = rest
        elif current_key and line.startswith(" "):
            cont = _TRAILING_DATE_RE.sub("", line).strip()
            if cont:
                fields[current_key] = (fields.get(current_key, "") + " " + cont).strip()

    director_raw = fields.get("Генеральный директор") or fields.get("Директор")
    director = None
    if director_raw:
        m = re.match(r"(.+?),\s*ИНН\s*(\d+)", director_raw)
        director = {"name": m.group(1).strip(), "inn": m.group(2)} if m else {"name": director_raw.strip(), "inn": None}

    stats_raw = fields.get("Статистика", "")
    statistics = {}
    for m in re.finditer(
        r"(Баланс|Выручка|Чистая прибыль|Чистый убыток|Госконтракты за год|Госзакупки за год)"
        r"[^:]*:\s*([\d,.]+)\s*(млрд|млн|тыс)?\s*р\.?",
        stats_raw,
    ):
        label, num, scale = m.groups()
        val = to_number(num) or 0
        mult = {"млрд": 1e9, "млн": 1e6, "тыс": 1e3}.get(scale, 1)
        statistics[label] = val * mult

    return {
        "name_full": fields.get("Полное наименование"),
        "name_short": fields.get("Краткое наименование"),
        "status": fields.get("Статус"),
        "inn": fields.get("ИНН"),
        "kpp": fields.get("КПП"),
        "ogrn": fields.get("ОГРН"),
        "reg_date": fields.get("Дата регистрации"),
        "address": fields.get("Юр. адрес"),
        "phones": fields.get("Телефоны"),
        "director": director,
        "okved_main": fields.get("Основной вид"),
        "statistics": statistics,
    }


def parse_okved(text: str) -> list[dict]:
    m = re.search(r"Наименование вида деятельности\s+Код\n\n\n(.*?)\n\n\n", text, re.S)
    if not m:
        return []
    out = []
    buffer: list[str] = []
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line:
            continue
        cm = re.match(r"^(.+?)\s{2,}(\d{2}\.\d{2}(?:\.\d{1,2})?)\s*$", line)
        if cm:
            name = " ".join(buffer + [cm.group(1)]).strip()
            out.append({"name": name, "code": cm.group(2)})
            buffer = []
        else:
            buffer.append(line)
    return out


def parse_founders(text: str) -> list[dict]:
    m = re.search(r"Учредители и участники \(\d+\)\n(.*?)\n\n\nКонечные владельцы", text, re.S)
    if not m:
        return []
    block = m.group(1)
    starts = list(re.finditer(r"^\s*(–|[\d.,]+%?)\s{2,}(–|[\d\s,.]+?)\s{2,}(?=\S)", block, re.M))
    boundaries = [s.end() for s in starts]
    out = []
    for i, s in enumerate(starts):
        end = starts[i + 1].start() if i + 1 < len(starts) else len(block)
        chunk = " ".join(x.strip() for x in block[boundaries[i]:end].splitlines() if x.strip())
        dm = re.search(r"(\d{2}\.\d{2}\.\d{4})\s*$", chunk)
        date_str = dm.group(1) if dm else None
        rest = chunk[: dm.start()].strip() if dm else chunk
        nm = re.search(r"(.+?),\s*ИНН\s*(\d+)", rest)
        name, inn = (nm.group(1).strip(" ,"), nm.group(2)) if nm else (rest, None)
        out.append({
            "share_pct": s.group(1).strip(),
            "share_rub": s.group(2).strip(),
            "name": name,
            "inn": inn,
            "date": date_str,
        })
    return out


def parse_beneficial_owners(text: str) -> list[dict]:
    m = re.search(r"Конечные владельцы \(\d+\)\n(.*?)(?:\n\n\nАрбитраж|\n\n\nФорма|\Z)", text, re.S)
    if not m:
        return []
    block = m.group(1)
    starts = list(re.finditer(r"^(~?\d+%|–)\s{2,}(?=\S)", block, re.M))
    boundaries = [s.end() for s in starts]
    out = []
    for i, s in enumerate(starts):
        end = starts[i + 1].start() if i + 1 < len(starts) else len(block)
        chunk = " ".join(x.strip() for x in block[boundaries[i]:end].splitlines() if x.strip())
        nm = re.search(r"(.+?),?\s*ИНН:?\s*(\d+)", chunk)
        name, inn = (nm.group(1).strip(" ,"), nm.group(2)) if nm else (chunk.strip(), None)
        out.append({"share": s.group(1), "name": name, "inn": inn})
    return out


def parse_litigation(text: str) -> list[dict]:
    cases = []
    for cat, cat_text in re.findall(
        r"Арбитраж – (истец|ответчик|третье лицо|другое) \(\d+\)\n(.*?)(?=\n\n\n(?:Арбитраж|Форма|Госзакупки)|\Z)",
        text, re.S,
    ):
        starts = list(re.finditer(
            r"^\s*(\d{2}\.\d{2}\.\d{4})\s+(\S+-?\d*/\d{4})(?:\s*[–-]\s*(\S.*?))?\s*\n",
            cat_text, re.M,
        ))
        boundaries = [m.start() for m in starts] + [len(cat_text)]
        for i, m in enumerate(starts):
            chunk = cat_text[m.start(): boundaries[i + 1]]
            amount_m = re.search(r"Начальная сумма\s+([\d\s,.]+)\s*руб", chunk)
            annot_m = re.search(r"Аннотация\s+(.*?)(?:Аннотация сгенерирована|\Z)", chunk, re.S)
            subject_m = re.match(r"[^\n]*\n\s*(.+)", chunk[m.end() - m.start():])
            cases.append({
                "date": m.group(1),
                "case_number": m.group(2),
                "outcome": m.group(3),
                "role": cat,
                "subject": subject_m.group(1).strip() if subject_m else None,
                "amount_rub": to_number(amount_m.group(1)) if amount_m else None,
                "annotation": re.sub(r"\s+", " ", annot_m.group(1)).strip()[:800] if annot_m else None,
            })
    return cases


FORM_TITLES = {
    "1": "Бухгалтерский баланс",
    "2": "Отчет о финансовых результатах",
    "4": "Отчет о движении денежных средств",
    "6": "Отчет о целевом использовании полученных средств",
}


def parse_financials(text: str) -> dict:
    out = {}
    for num, title in FORM_TITLES.items():
        m = re.search(rf"Форма №{num}\. {re.escape(title)}\n(.*?)(?=\n\n\n(?:Форма|Госзакупки)|\Z)", text, re.S)
        if not m:
            continue
        section = m.group(1)
        years = re.findall(r"конец (\d{4})", section)
        rows = {}
        for line in section.splitlines():
            tokens = re.split(r"\s{2,}", line.strip())
            if len(tokens) < 2:
                continue
            code = tokens[1] if len(tokens) > 1 else None
            if not code or not re.fullmatch(r"\d{4}", code):
                continue
            values = [to_number(t) for t in tokens[2:]]
            if years and len(values) >= len(years):
                values = values[: len(years)]
            rows[code] = dict(zip(years, values)) if years else values
        out[f"form_{num}"] = {"title": title, "rows": rows}
    return out


def parse_gov_contracts(text: str) -> list[dict]:
    out = []
    for role, role_text in re.findall(
        r"Госзакупки – (Участник|Заказчик) \(\d+\)\n(.*?)(?=\n\n\nГосзакупки|\n\n\nБлижайшие|\Z)",
        text, re.S,
    ):
        starts = list(re.finditer(r"^\s*(\d{2}\.\d{2}\.\d{4})\s+(.+)$", role_text, re.M))
        boundaries = [m.start() for m in starts] + [len(role_text)]
        for i, m in enumerate(starts):
            chunk = role_text[m.start(): boundaries[i + 1]]
            price_m = re.search(r"Цена (?:контракта|договора)\s+([\d\s,.]+)\s*руб", chunk)
            num_m = re.search(r"№ (?:контракта|договора)\s+(\S+)\s*(44-ФЗ|223-ФЗ)?", chunk)
            date_m = re.search(r"Дата (?:контракта|договора)\s+(\d{2}\.\d{2}\.\d{4})", chunk)
            status_m = re.search(r"Статус (?:контракта|договора)\s+(.+)", chunk)
            out.append({
                "role": role,
                "posted_date": m.group(1),
                "subject": m.group(2).strip()[:300],
                "price_rub": to_number(price_m.group(1)) if price_m else None,
                "contract_number": num_m.group(1) if num_m else None,
                "law": num_m.group(2) if num_m and num_m.group(2) else None,
                "contract_date": date_m.group(1) if date_m else None,
                "status": status_m.group(1).strip() if status_m else None,
            })
    return out


def parse_affiliated_network(text: str) -> list[dict]:
    m = re.search(r"Ближайшие связи – Актуальные \(\d+\)\n(.*?)(?=\n\n\n(?:Товарные знаки|Лицензии|ЭКГ-рейтинг)|\Z)", text, re.S)
    if not m:
        return []
    section = m.group(1)
    starts = list(re.finditer(r"^(\S.{2,120}?)\s{5,}(\d{1,3})\s*$", section, re.M))
    out = []
    for i, sm in enumerate(starts[1:], start=1):  # skip index 1 (the subject entity itself)
        block_start = sm.end()
        block_end = starts[i + 1].start() if i + 1 < len(starts) else len(section)
        block = section[block_start:block_end]
        req_m = re.search(r"ИНН:\s*(\d+),\s*ОГРН:\s*(\d+)", block)
        addr_m = re.search(r"Адрес\s+(.+?)(?:\d{2}\.\d{2}\.\d{4}|\Z)", block, re.S)
        out.append({
            "name": sm.group(1).strip(),
            "inn": req_m.group(1) if req_m else None,
            "ogrn": req_m.group(2) if req_m else None,
            "address": re.sub(r"\s+", " ", addr_m.group(1)).strip() if addr_m else None,
        })
    return out


def parse_ekg(text: str) -> dict | None:
    m = re.search(
        r"ЭКГ-рейтинг\s*\n\s*Оценка\s+(.+?)\n\s*Статус\s+(.+?)\n\s*Итоговый балл\s+(\d+)"
        r"\s*\n\s*Экология\s+([\d.]+)\s*\n\s*Кадры\s+([\d.]+)\s*\n\s*Государство\s+([\d.]+)",
        text,
    )
    if not m:
        return None
    level, status, total, ecology, staff, government = m.groups()
    return {
        "level": level.strip(), "status": status.strip(), "result_points": int(total),
        "ecology_points": float(ecology), "staff_points": float(staff), "government_points": float(government),
    }


def as_of_from_title(text: str) -> str | None:
    m = re.match(r"\s*.+\n\s*(\d{1,2}\s+[а-я]+\s+\d{4})\s+года", text)
    return ru_date_to_iso(m.group(1)) if m else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--slug", default=None, help="entity slug in entities.json; inferred from ИНН if omitted")
    ap.add_argument("--source-id", default=None, help="sources.json id for this PDF (recorded on kontur_focus_matches)")
    args = ap.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.is_absolute():
        pdf_path = REPO / pdf_path
    text = pdf_text(pdf_path)

    parsed = {
        "as_of": as_of_from_title(text),
        "header": parse_header(text),
        "okved": parse_okved(text),
        "founders": parse_founders(text),
        "beneficial_owners": parse_beneficial_owners(text),
        "litigation": parse_litigation(text),
        "financials": parse_financials(text),
        "gov_contracts": parse_gov_contracts(text),
        "affiliated_network": parse_affiliated_network(text),
        "ekg_rating": parse_ekg(text),
    }

    inn = parsed["header"]["inn"]
    if not inn:
        print("Could not extract ИНН from header — aborting without writing anything.")
        print(json.dumps(parsed["header"], ensure_ascii=False, indent=2))
        return

    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    cache[inn] = {
        "pdf_path": str(pdf_path.relative_to(REPO)) if pdf_path.is_relative_to(REPO) else str(pdf_path),
        "parsed_at": date.today().isoformat(),
        "parsed": parsed,
    }
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {CACHE.relative_to(REPO)} [{inn}]")

    entities = json.loads(ENTITIES.read_text(encoding="utf-8"))
    target = None
    if args.slug:
        target = next((e for e in entities if e["slug"] == args.slug), None)
    if not target:
        target = next((e for e in entities if e.get("inn") == inn), None)

    today = date.today().isoformat()
    summary = {
        "status": parsed["header"]["status"],
        "as_of": parsed["as_of"],
        "ekg_rating": parsed["ekg_rating"],
        "litigation_count": len(parsed["litigation"]),
        "gov_contracts_participant_count": sum(1 for c in parsed["gov_contracts"] if c["role"] == "Участник"),
        "gov_contracts_customer_count": sum(1 for c in parsed["gov_contracts"] if c["role"] == "Заказчик"),
        "affiliated_network_count": len(parsed["affiliated_network"]),
        "founders_count": len(parsed["founders"]),
        "beneficial_owners_count": len(parsed["beneficial_owners"]),
        "source_id": args.source_id,
    }

    if target:
        target["kontur_focus_matches"] = [summary]
        target["kontur_focus_checked_at"] = today
        ENTITIES.write_text(json.dumps(entities, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"wrote kontur_focus_matches onto entities.json [{target['slug']}]")
    else:
        print(f"No entity in entities.json matches ИНН {inn} — kontur_focus_matches not written. "
              f"Add the entity first (corrections_entities.json), then re-run with --slug.")

    print("\n--- Review scaffold (not auto-wired — verify before adding via corrections.json) ---")
    print(f"ОКВЭД codes parsed: {len(parsed['okved'])}")
    print(f"Founders parsed: {len(parsed['founders'])}")
    print(f"Beneficial owners parsed: {len(parsed['beneficial_owners'])}")
    print(f"Litigation cases parsed: {len(parsed['litigation'])}")
    known_case_numbers = set()
    if target:
        for lit in target.get("litigation") or []:
            known_case_numbers.add(str(lit.get("case_number") or lit.get("case") or ""))
    new_cases = [c for c in parsed["litigation"] if c["case_number"] not in known_case_numbers]
    if new_cases:
        print(f"  -> {len(new_cases)} case(s) not obviously already in entities.json's litigation[]:")
        for c in new_cases:
            print(f"     {c['case_number']} ({c['role']}, {c['date']}) — {c['subject'][:80] if c['subject'] else ''}")
    known_contract_numbers = set()
    if target:
        for gc in target.get("government_contracts") or []:
            known_contract_numbers.add(str(gc.get("contract_number") or gc.get("number") or ""))
    new_contracts = [c for c in parsed["gov_contracts"] if c["contract_number"] not in known_contract_numbers]
    print(f"Gov. contracts parsed: {len(parsed['gov_contracts'])}"
          + (f" -> {len(new_contracts)} not obviously already in government_contracts[]" if parsed["gov_contracts"] else ""))
    known_inns = {e.get("inn") for e in entities if e.get("inn")}
    new_network = [n for n in parsed["affiliated_network"] if n["inn"] and n["inn"] not in known_inns]
    print(f"Affiliated network entities parsed: {len(parsed['affiliated_network'])}"
          + (f" -> {len(new_network)} NOT currently in entities.json (candidate new entities):" if new_network else ""))
    for n in new_network:
        print(f"     {n['name']} (ИНН {n['inn']}, ОГРН {n['ogrn']})")

    print(f"\nFull parsed structure: {CACHE.relative_to(REPO)}[\"{inn}\"]")
    print("Run scripts/extract_registry.py then scripts/check_registry.py next.")


if __name__ == "__main__":
    main()
