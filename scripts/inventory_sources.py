#!/usr/bin/env python3
"""Read every file in data/sources/ once and record what it IS and WHEN it
is dated — not just its filename, which scan_sources.py already indexes.

Local file processing (pdftotext, zip/xlsx, html) — no network calls, same
"safe to run directly and repeatedly" category as scan_sources.py and
mine_leads.py per CLAUDE.md's crawling-jobs policy. This is what "inventory
the source docs" actually means for files already sitting on disk: reading
content once and caching the result, since pdftotext/openpyxl over 300 files
is real work worth not repeating on every registry rebuild.

Two things it fills in that filename-based inference (in extract_registry.py)
cannot:

- `type` for the ~30 files whose name gives no hint (opaque ФНС UUIDs, press
  captures, a generic "Устав №20.pdf" template) — classified by keyword
  content instead.
- `as_of` — the document's own effective date, which is NEVER the same thing
  as when we happened to download it. A БФО filing's as_of is its fiscal
  year-end (a formulaic derivation, no read needed — Russian annual accounts
  report position as of 31 December). An EGRUL extract states "по состоянию
  на DD.MM.YYYY" in its own text. A court ruling states its own decision
  date. These require an actual read, so this script does one and caches it.

Output: data/registry/_source_content_cache.json, keyed by filename, each
entry {type, type_method, as_of, as_of_method, sample}. extract_registry.py's
parse_sources() reads this cache (if present) to enrich sources.json beyond
what the filename alone can tell it — see its docstring for the
captured_date/as_of distinction this preserves.

Nothing here is asserted as verified: every entry keeps `sample` (the text
the date/type was pulled from) so a human can check the read against the
actual document before trusting it for anything that goes in a profile.

Usage:
    python3 scripts/inventory_sources.py             # process new/changed files only
    python3 scripts/inventory_sources.py --all        # reprocess everything
    python3 scripts/inventory_sources.py --report     # print summary, don't write
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from scan_sources import extract_text  # reuses the pdf/zip/html readers

REPO = Path(__file__).resolve().parent.parent
SOURCES = REPO / "data" / "sources"
CACHE = REPO / "data" / "registry" / "_source_content_cache.json"

RE_DATE_DMY = re.compile(r"\b(\d{2})\.(\d{2})\.(\d{4})\b")
RE_INN12 = re.compile(r"\b(\d{10}|\d{12})\b")

MONTHS = {
    "января": "01", "февраля": "02", "марта": "03", "апреля": "04",
    "мая": "05", "июня": "06", "июля": "07", "августа": "08",
    "сентября": "09", "октября": "10", "ноября": "11", "декабря": "12",
}
RE_DATE_RU_WORDS = re.compile(
    # tolerates a fill-in-the-blank day quoted like «03»/"03"/"03" (straight,
    # curly “”, or guillemet «») — the standard Russian legal-document
    # convention for a protocol/charter date (see UD_*.zip founding docs,
    # e.g. 'от "03" апреля 2013 г.' — OCR renders the source's curly quotes
    # literally) — without this the day is followed by a quote mark, not
    # whitespace, and the whole date silently fails to match.
    r"\b[\"'«“‘]?(\d{1,2})[\"'»”’]?\s+(" + "|".join(MONTHS) + r")\s+(\d{4})\s*(?:г|года)?\b")

# Type classification by content keyword, checked in this order — first
# match wins. Only reached for files the filename-based pass in
# extract_registry.py could not classify.
# Order matters: more specific document families are checked before generic
# ones that share vocabulary with them. "Форма №УН000Х"/"ОН0002" (Minjust's
# annual NCO activity/foreign-funding report forms) mention "ЕГРЮЛ" once in
# their own boilerplate ("Дата включения в единый государственный реестр
# юридических лиц") and were being misclassified as egrul extracts before
# this form-number check was added first.
# bfo is checked BEFORE ustav: a balance sheet's own "уставный капитал"
# (charter capital) line item contains "УСТАВ" as a substring, and every
# БФО filing has one — an ordering bug caught 2026-08-22 when it
# misclassified all 115 БФО zips as founding-document bundles. The \b word
# boundary in the ustav pattern (below) also fixes this independently:
# "УСТАВНЫЙ" has no boundary after "УСТАВ" (В and Н are both word chars),
# so \bУСТАВ\b cannot match inside it — but bfo-before-ustav ordering is
# kept too, since a single bug should not depend on only one of two fixes.
TYPE_KEYWORDS = [
    # Government-issued generic model charters (Типовые уставы №1-36,
    # Приказ Минэкономразвития от 01.08.2018 №411) — boilerplate text a
    # company adopts INSTEAD OF a custom charter, carrying zero
    # entity-specific content. Checked before "ustav" (a real company's own
    # charter bundle) so a template copy never gets mistaken for founding
    # evidence about one entity. See data/registry/ustav_templates.json —
    # the useful fact is WHICH entities adopted which template and WHEN,
    # not anything extractable from the template text itself.
    ("ustav_template", [r"ТИПОВОЙ\s+УСТАВ\s*№"]),
    ("minjust", ["Форма №УН000Х", "Форма № ОН0002", "Форма № ОН0001",
                 "Отчет о деятельности некоммерческой организации",
                 "Отчет о расходовании"]),
    ("egrul", ["ВЫПИСКА ИЗ ЕДИНОГО ГОСУДАРСТВЕННОГО РЕЕСТРА ЮРИДИЧЕСКИХ",
               "сведения о юридическом лице"]),
    ("bfo", ["Бухгалтерский баланс", "Отчет о финансовых результатах"]),
    # \bУСТАВ\b (bug found 2026-08-22): a word-boundary immediately after
    # "УСТАВ" only matches the bare nominative form — it misses every
    # case-inflected form ("Устава", "Уставом", "Уставе", "Уставу"), which
    # is how the word overwhelmingly appears in real legal prose ("на
    # основании настоящего Устава"). \b was doing double duty — the intent
    # was excluding "УСТАВНЫЙ" (charter *capital*, an unrelated adjective),
    # not excluding every inflected noun form. Fixed to a negative lookahead
    # on the very next letter instead: "УСТАВ" not immediately followed by
    # "Н" catches "Устава/Уставом/Уставе/Уставу" while still excluding
    # "УСТАВНЫЙ/УСТАВНОЙ/УСТАВНОГО/etc" (all of which have Н right after
    # the stem). Caught when a 42-page scanned Устав OCR'd cleanly and
    # still didn't classify as `ustav`.
    ("ustav", [r"\bУСТАВ(?!Н)", "утвержден решением единственного участника",
               "Протокол общего собрания"]),
    # Checked AFTER "ustav" (bug found 2026-08-22): a charter's own cover
    # page routinely reads "Утвержден Решением единственного учредителя...",
    # which matches the bare "РЕШЕНИЕ" keyword below — every founding-
    # document bundle was misclassifying as a court filing before the
    # "УСТАВ" heading ever got a chance to match, since court was checked
    # first. Found when 20 of 26 UD_*.zip founding-doc bundles came back
    # type:court after the full OCR batch.
    ("court", ["АРБИТРАЖНЫЙ СУД", "ОПРЕДЕЛЕНИЕ", "РЕШЕНИЕ", "ПОСТАНОВЛЕНИЕ",
               "Дело №", "резолютивную часть"]),
    # «Благодарственное письмо» genre (military_thankyou_letter_genre memory)
    # — checked before "press" since OCR'd scans of these can pick up noisy
    # matches elsewhere; the heading itself is a reliable, distinctive hit
    # even through OCR noise (see Благодарность.pdf, 2026-08-22).
    ("military_thankyou", ["БЛАГОДАРСТВЕННОЕ"]),
    # EU Council Decisions/Regulations under the CFSP sanctions regimes —
    # distinct from a generic press capture; see Phase 1.5a/1.5c of the
    # rebuild plan. Checked before "press" for the same reason.
    ("eu_sanctions_annex", ["COUNCIL DECISION (CFSP)",
                            "COUNCIL REGULATION (EU)"]),
    # Regional НПЦ БАС/technopark program decks (delegation rosters,
    # investment-pitch slides) — a recurring genre in data/sources/, kept
    # distinct from generic press since it's promotional/statistical
    # program material, not reporting. See npc_bas_technopark_network
    # memory — parked, adjacent-not-core to the ЦБСТ investigation.
    ("regional_program_deck", ["Состав команды"]),
    ("press", ["ТАСС", "Интервью", "корреспондент", "OSINT"]),
]


def _keyword_pattern(kw: str) -> str:
    """A multi-word keyword becomes escaped-word-tokens joined by \\s+, so a
    literal phrase still matches text pdftotext padded with extra spaces to
    preserve table alignment. A keyword that already IS a regex (contains a
    backslash, e.g. \\bУСТАВ\\b) is used as-is."""
    if "\\" in kw:
        return kw
    return r"\s+".join(re.escape(w) for w in kw.split())


def guess_type(sample: str) -> tuple[str | None, str | None]:
    folded = re.sub(r"\s+", " ", sample)
    for t, keywords in TYPE_KEYWORDS:
        for kw in keywords:
            if re.search(_keyword_pattern(kw), folded, re.I):
                return t, f"keyword:{kw}"
    return None, None


def find_as_of(sample: str, doc_type: str | None) -> tuple[str | None, str | None]:
    """Best-effort extraction of the document's own effective date."""
    sample = re.sub(r"[ \t]+", " ", sample)

    # Minjust annual reports state their own reporting year ("за 2025 г.")
    # — same Dec-31 convention as a БФО filing.
    if doc_type == "minjust":
        m = re.search(r"за\s+(\d{4})\s*г", sample)
        if m:
            return f"{m.group(1)}-12-31", "minjust:за YYYY г."

    # EGRUL extracts state their own issue date near "по состоянию на" or
    # "Дата формирования".
    if doc_type == "egrul":
        m = re.search(r"(?:по состоянию на|Дата формирования[^:]*:?)\s*"
                      r"(\d{2}\.\d{2}\.\d{4})", sample, re.I)
        if m:
            d, mo, y = m.group(1).split(".")
            return f"{y}-{mo}-{d}", "egrul:по состоянию на"

    # Court rulings: look for a Russian-worded date near the top of the
    # document (the standard "город Москва\n\nДД месяц ГГГГ года" heading),
    # falling back to the first numeric dd.mm.yyyy date in the first 1500
    # chars if the worded form isn't found (some scanned/OCR filings only
    # carry the numeric form cleanly).
    if doc_type == "court":
        head = sample[:1500]
        m = RE_DATE_RU_WORDS.search(head)
        if m:
            d, month_word, y = m.groups()
            return f"{y}-{MONTHS[month_word]}-{int(d):02d}", "court:worded-date"
        m = RE_DATE_DMY.search(head)
        if m:
            d, mo, y = m.groups()
            return f"{y}-{mo}-{d}", "court:numeric-date"

    if doc_type == "ustav":
        m = re.search(r"[Пп]ротокол[^.]{0,40}от\s*(\d{2}\.\d{2}\.\d{4})",
                      sample)
        if m:
            d, mo, y = m.group(1).split(".")
            return f"{y}-{mo}-{d}", "ustav:protocol-date"
        # Founding-document protocols routinely give the date in worded
        # form with a quoted day ('от "03" апреля 2013 г.') rather than
        # numeric — same convention as a court ruling's heading date.
        m = RE_DATE_RU_WORDS.search(sample)
        if m:
            d, month_word, y = m.groups()
            return f"{y}-{MONTHS[month_word]}-{int(d):02d}", "ustav:worded-protocol-date"

    return None, None


def pdf_creation_date(path: Path) -> str | None:
    """Fallback as_of source for scanned PDFs with no in-body date the OCR
    text can find (e.g. a thank-you letter scan — the letter names a
    recipient and a unit, not a date; the date only exists in the original
    Telegram post caption or the scanner's own metadata). Weaker evidence
    than a content-read date — it's when the file was scanned, which is
    usually but not always close to the document's own effective date —
    so callers should keep the as_of_method distinct rather than treat it
    as equal-confidence to a worded/numeric date found in the text."""
    try:
        r = subprocess.run(["pdfinfo", str(path)], capture_output=True,
                           timeout=20, text=True)
    except Exception:
        return None
    m = re.search(r"^CreationDate:\s+\w+ (\w+)\s+(\d+)\s+[\d:]+\s+(\d{4})",
                  r.stdout, re.M)
    if not m:
        return None
    month_name, day, year = m.groups()
    months3 = {"Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
              "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
              "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"}
    mo = months3.get(month_name)
    if not mo:
        return None
    return f"{year}-{mo}-{int(day):02d}"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def process_file(path: Path) -> dict:
    text = extract_text(path)
    sample = text[:2500]

    doc_type, type_method = guess_type(sample)
    as_of, as_of_method = find_as_of(sample, doc_type)

    if not as_of and doc_type == "military_thankyou" and path.suffix.lower() == ".pdf":
        as_of = pdf_creation_date(path)
        if as_of:
            as_of_method = "pdf-metadata:scan-creation-date"

    return {
        "type": doc_type,
        "type_method": type_method,
        "as_of": as_of,
        "as_of_method": as_of_method,
        "sha256": sha256_of(path),
        "sample": sample[:400],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--all", action="store_true",
                    help="reprocess every file, ignoring the existing cache")
    ap.add_argument("--report", action="store_true",
                    help="print a summary and exit; do not write the cache")
    ap.add_argument("--limit", type=int, default=None,
                    help="process at most N files this run (for a quick check)")
    args = ap.parse_args()

    if not SOURCES.exists():
        print(f"error: {SOURCES} not found", file=sys.stderr)
        return 1

    cache = {}
    if CACHE.exists() and not args.all:
        cache = json.loads(CACHE.read_text(encoding="utf-8"))

    # rglob, not iterdir: a manually-unzipped ZAKUPKI_ATTACH folder was found
    # 2026-09-05 sitting one level deep, invisible to a top-level-only scan.
    # cache_key matches the bare filename for top-level files (preserves
    # every existing cache hit) and only falls back to "subdir/filename" for
    # nested files, which were never cached under any key before.
    files = sorted(p for p in SOURCES.rglob("*")
                   if p.is_file() and p.name not in ("MANIFEST.md", ".DS_Store"))

    def cache_key(p: Path) -> str:
        rel = p.relative_to(SOURCES)
        return str(rel) if len(rel.parts) > 1 else rel.name

    to_process = [p for p in files if cache_key(p) not in cache]
    if args.limit:
        to_process = to_process[:args.limit]

    print(f"{len(files)} files total, {len(cache)} already cached, "
          f"{len(to_process)} to process this run")

    CACHE.parent.mkdir(parents=True, exist_ok=True)
    for i, path in enumerate(to_process, 1):
        t0 = time.monotonic()
        key = cache_key(path)
        try:
            cache[key] = process_file(path)
        except Exception as e:
            cache[key] = {"type": None, "type_method": None,
                                "as_of": None, "as_of_method": None,
                                "sha256": None, "sample": f"[error: {e}]"}
        elapsed = time.monotonic() - t0
        print(f"  {i}/{len(to_process)}  {elapsed:5.1f}s  {key}")
        # Write after every file, not just at the end — a zip full of
        # scanned pages can take minutes per file; losing all of it to an
        # interrupt or a killed process would make this unsafe to run and
        # stop, which it should be (local processing, no network calls).
        CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8")

    # Citation facts (B4): a header read per file, redone for every file when
    # source_citation.CITE_VERSION changes. Cheap compared with text extraction.
    from source_citation import CITE_VERSION, facts as cite_facts
    by_key = {cache_key(p): p for p in files}
    cited = 0
    for name, entry in cache.items():
        if (entry.get("cite") or {}).get("v") == CITE_VERSION or name not in by_key:
            continue
        entry["cite"] = cite_facts(by_key[name])
        cited += 1
    if cited:
        print(f"read citation facts for {cited} files")

    # sha256 was added after most entries were first cached — backfill it
    # for anything already cached (a plain hash, not a re-extraction, so
    # this is cheap even across hundreds of PDFs/zips).
    by_name = {cache_key(p): p for p in files}
    hashed = 0
    for name, entry in cache.items():
        if entry.get("sha256"):
            continue
        path = by_name.get(name)
        if path is None:
            continue
        try:
            entry["sha256"] = sha256_of(path)
            hashed += 1
        except Exception:
            pass
    if hashed:
        print(f"backfilled sha256 for {hashed} already-cached files")

    typed = sum(1 for v in cache.values() if v.get("type"))
    dated = sum(1 for v in cache.values() if v.get("as_of"))
    hashed_total = sum(1 for v in cache.values() if v.get("sha256"))
    print(f"\ncache holds {len(cache)} files: {typed} typed, {dated} with "
          f"as_of, {hashed_total} hashed")

    if args.report:
        print("\nfiles still untyped by content:")
        for name, v in sorted(cache.items()):
            if not v.get("type"):
                print(f"  {name}")
        return 0

    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n",
                     encoding="utf-8")
    print(f"wrote {CACHE.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
