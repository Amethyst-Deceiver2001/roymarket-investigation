#!/usr/bin/env python3
"""Enrich every registry trademark record that has a reg_number but no
wordmark/title -- these came from the bulk CSV sweep (rospatent_tm_search.py,
sources s0433/s0945/s0539), which is bibliographic-only: it has reg_number,
holder and dates but no wordmark text or goods/services classes.

Individually pulls each record's FIPS registration-view page
(https://www.fips.ru/registers-doc-view/fips_servlet?DB=RUTM&DocNumber=<reg>&
TypeFile=html), confirmed working 2026-08-24 (see
webfetch_hallucination_on_blocked_fips memory -- fetch this with plain curl/
urllib + a browser User-Agent + explicit windows-1251 decode; do NOT rely on
WebFetch's own summarizer for this site, it hallucinated contradictory data
on a blocked/garbled fetch). Extracts: wordmark text (or "no plain text --
combined/figurative mark" if none), mark type, holder, dates, goods/services
classes, and the mark's own image if present.

Writes, per record:
  data/sources/TRADEMARK_RU<regnum>_<filed-date>_<slug>.html   (raw archive)
  data/sources/TRADEMARK_RU<regnum>_<filed-date>_<slug>.jpg    (mark image, if any)
  data/sources/TRADEMARK_RU<regnum>_<filed-date>_<slug>.json   (extracted fields)

Does NOT touch corrections.json -- promotion into entities.json's
trademarks[] is a separate, human-reviewed step (same two-stage pattern as
the patent archive/promote split), run after this and after
scan_sources.py/inventory_sources.py/extract_registry.py have picked up the
new files and assigned them source_ids.

**Live network job against a third-party site, ~97 sequential HTML/image
pulls -- per CLAUDE.md's crawling-jobs policy, tested inline on a handful
first (ao-pk-azimut's 5, all succeeded), but the full run should be executed
by you, not run in the background.**

After running this:
    python3 scripts/scan_sources.py --out data/sources/MANIFEST.md
    python3 scripts/inventory_sources.py
    (then hand the extracted JSONs back for review/promotion into
    corrections.json)

Usage:
    python3 scripts/fips_trademark_enrich.py                # everything missing a title
    python3 scripts/fips_trademark_enrich.py --limit 5       # first 5 only
"""
from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SOURCES_DIR = REPO / "data" / "sources"
BASE = "https://www.fips.ru/registers-doc-view/fips_servlet"
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")
DELAY_SECONDS = 3.0
RETRY_BACKOFF_SECONDS = 20.0
MAX_RETRIES = 3


def slugify_date(d: str | None) -> str:
    if not d:
        return "unknown"
    m = re.match(r"^(\d{4})(\d{2})(\d{2})$", d)
    if m:
        return f"{m.group(1)}{m.group(2)}{m.group(3)}"
    return re.sub(r"\D", "", d) or "unknown"


def collect_targets() -> list[dict]:
    entities = json.loads((REPO / "data" / "registry" / "entities.json").read_text(encoding="utf-8"))
    targets = []
    seen_regnums = set()
    for rec in entities:
        for tm in rec.get("trademarks") or []:
            reg = tm.get("reg_number")
            if not reg or tm.get("title"):
                continue
            key = reg
            if key in seen_regnums:
                continue
            seen_regnums.add(key)
            targets.append({"slug": rec["slug"], "reg_number": reg, "filed": tm.get("filed")})
    return targets


def fetch(url: str) -> str:
    last_ex: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw = resp.read()
            return raw.decode("windows-1251", errors="replace")
        except urllib.error.HTTPError as ex:
            last_ex = ex
            if ex.code == 429 and attempt < MAX_RETRIES:
                wait = RETRY_BACKOFF_SECONDS * attempt
                print(f"    429 rate-limited, backing off {wait:.0f}s (attempt {attempt}/{MAX_RETRIES}) ...")
                time.sleep(wait)
                continue
            raise
    raise last_ex  # type: ignore[misc]


def flatten(html: str) -> str:
    body = html.split("<body>", 1)[-1]
    text = re.sub(r"<[^>]+>", " | ", body)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"(\s*\|\s*)+", " | ", text)
    return text.strip()


def field(flat: str, label_pattern: str, value_pattern: str = r"([\d.]+)") -> str | None:
    m = re.search(rf"{label_pattern}\s*(?:\|\s*)*{value_pattern}", flat)
    return m.group(1).strip() if m else None


def last_holder(flat: str) -> str | None:
    # a transferred/renamed mark logs each ownership change under a fresh
    # (732) block further down the document -- the LAST one is current.
    matches = re.findall(
        r"Правообладател[ья]:\s*(?:\|\s*)*(.*?)\s*(?:\||Адрес для переписки|\(750\)|\(580\)|Дата)",
        flat,
    )
    if not matches:
        return None
    return re.sub(r"\s+", " ", matches[-1]).strip(" |")


def goods_classes(flat: str) -> list[str]:
    m = re.search(
        r"Классы МКТУ и перечень товаров.{0,40}?\|\s*(.*?)\s*(?:Делопроизводство|Извещения|$)",
        flat,
        re.S,
    )
    if not m:
        return []
    block = m.group(1)
    # classes are separated by " | NN - text | " runs; split on the class-number pattern
    parts = re.split(r"\|\s*(?=\d\d\s*-\s)", block)
    return [re.sub(r"\s+", " ", p).strip(" |") for p in parts if re.match(r"\s*\d\d\s*-", p)]


def extract_image_url(html: str) -> str | None:
    m = re.search(r'\(540\).*?<a href="([^"]+\.jpg)"', html, re.S)
    return m.group(1) if m else None


def parse_record(html: str) -> dict:
    flat = flatten(html)
    return {
        "reg_number": field(flat, r"Номер\s+регистрации:"),
        "application_number": field(flat, r"Номер заявки:"),
        "priority_date": field(flat, r"(?:Дата приоритета|Приоритет):"),
        "filed": field(flat, r"Дата подачи заявки:"),
        "registered": field(flat, r"Дата (?:государственной )?регистрации:"),
        "expires": field(flat, r"Дата истечения срока действия (?:регистрации|исключительного права):"),
        "mark_type": field(flat, r"вида знака.{0,40}?характеристики", value_pattern=r"([^|]+)"),
        "holder": last_holder(flat),
        "goods_classes": goods_classes(flat),
        "has_image": extract_image_url(html) is not None,
        "image_url": extract_image_url(html),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    targets = collect_targets()
    if args.limit is not None:
        targets = targets[: args.limit]

    print(f"processing {len(targets)} trademark record(s) ...")
    ok, failed = 0, []
    for i, t in enumerate(targets, 1):
        reg = t["reg_number"]
        slug = t["slug"]
        date_slug = slugify_date(t.get("filed"))
        base_name = f"TRADEMARK_RU{reg}_{date_slug}_{slug}"
        json_path = SOURCES_DIR / f"{base_name}.json"
        if json_path.exists():
            print(f"  [{i}/{len(targets)}] {base_name}: already have JSON, skipping")
            continue

        url = f"{BASE}?DB=RUTM&DocNumber={reg}&TypeFile=html"
        try:
            html = fetch(url)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as ex:
            print(f"  [{i}/{len(targets)}] {base_name}: FAILED {ex}")
            failed.append((base_name, url))
            time.sleep(DELAY_SECONDS)
            continue

        if "Товарные знаки" not in html and "товарного знака" not in html:
            print(f"  [{i}/{len(targets)}] {base_name}: unexpected content, skipping (manual check needed)")
            failed.append((base_name, url))
            time.sleep(DELAY_SECONDS)
            continue

        (SOURCES_DIR / f"{base_name}.html").write_text(html, encoding="utf-8")
        parsed = parse_record(html)
        parsed["slug"] = slug
        parsed["source_url"] = url

        img_url = parsed.pop("image_url", None)
        if img_url:
            try:
                req = urllib.request.Request(img_url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=60) as resp:
                    (SOURCES_DIR / f"{base_name}.jpg").write_bytes(resp.read())
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as ex:
                print(f"    (image fetch failed: {ex})")

        json_path.write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  [{i}/{len(targets)}] {base_name}: wrote html+json"
              f"{'+jpg' if img_url else ''} -- {parsed.get('mark_type') or '?'}")
        ok += 1
        time.sleep(DELAY_SECONDS)

    print(f"\nDone. {ok} record(s) archived, {len(failed)} failed/skipped.")
    if failed:
        print("Failed (re-run to retry, or investigate individually):")
        for name, url in failed:
            print(f"  {name}  {url}")
    print("\nNext: python3 scripts/scan_sources.py --out data/sources/MANIFEST.md")
    print("      python3 scripts/inventory_sources.py")
    print("      (then hand the extracted *.json files back for review/promotion)")


if __name__ == "__main__":
    main()
