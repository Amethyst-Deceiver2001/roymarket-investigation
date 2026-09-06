#!/usr/bin/env python3
"""Cross-check entity ИНН against МЧС's fire-safety license registry
(digital.mchs.gov.ru/fgpn/license) — a real, live, unauthenticated,
non-WAF-gated search (plain GET, no session/cookie/token needed, confirmed
working via raw curl 2026-09-06).

Single-ИНН/--slug lookups are ordinary inline reconnaissance, fine to run
directly. A full-roster sweep (no --slug/--limit) is real work at scale
against a live third-party service and is handed to the user per
CLAUDE.md's crawling-jobs policy, same precedent as screen_disqualified.py/
screen_subsidiary.py/screen_upr_uchr.py.

A hit means the ИНН appears in МЧС's registry with a real license record
(number/status/authority) -- this is a lead to verify and wire via
corrections_entities.json, not an automatic fact. Before wiring, check
whether it's a NEW license or the SAME one already on file under a
different reference number (this happened for ao-nii-stt 2026-09-06: its
existing EGRUL-sourced "#67-Б/00064" and МЧС's own "Л014-00101-67/00092572"
share date+authority+activity -- almost certainly one license cited two
ways, not two licenses).

Usage:
    python3 scripts/screen_mchs_fire_licenses.py --slug ao-nii-stt
    python3 scripts/screen_mchs_fire_licenses.py --inn 6730046954
    python3 scripts/screen_mchs_fire_licenses.py            # full roster, hand to user
"""
from __future__ import annotations

import argparse
import html
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTITIES = REPO / "data" / "registry" / "entities.json"

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36")
DELAY_SECONDS = 0.5


def check_inn(inn: str) -> dict | None:
    url = f"https://digital.mchs.gov.ru/fgpn/license?search={inn}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=15) as r:
        page = r.read().decode("utf-8", errors="ignore")
    if "Результаты поиска" not in page or inn not in page or "Номер лицензии" not in page:
        return None
    text = re.sub(r"<[^>]+>", "\n", page)
    lines = [html.unescape(l.strip()) for l in text.splitlines() if l.strip()]
    def after(label: str) -> str | None:
        for i, l in enumerate(lines):
            if l == label and i + 1 < len(lines):
                return lines[i + 1]
        return None
    return {
        "org_name": after("Результаты поиска") and lines[lines.index("Результаты поиска") + 1],
        "ogrn": after("ОГРН:"),
        "inn": after("ИНН:"),
        "license_number": after("Номер лицензии:"),
        "status": after("Статус реестровой записи:"),
        "authority": after("Наименование лицензирующего органа:"),
        "order": after("Номер и дата (приказа) лицензирующего органа о предоставлении лицензии:"),
        "date": after("Дата предоставления лицензии (формирования реестровой записи):"),
        "activity": after("Лицензируемый вид деятельности (в составе работ):"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inn", action="append", default=[])
    ap.add_argument("--slug", action="append", default=[])
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    entities = json.loads(ENTITIES.read_text())
    by_slug = {e["slug"]: e for e in entities}

    targets: list[tuple[str, str]] = []
    for inn in args.inn:
        targets.append((inn, next((e["slug"] for e in entities if e.get("inn") == inn), f"inn-{inn}")))
    for slug in args.slug:
        e = by_slug.get(slug)
        if e and e.get("inn"):
            targets.append((e["inn"], slug))
    if not targets:
        targets = [(e["inn"], e["slug"]) for e in entities if e.get("inn")]
        if args.limit:
            targets = targets[: args.limit]

    print(f"{len(targets)} ИНН to check against digital.mchs.gov.ru/fgpn/license")
    hits = []
    for i, (inn, slug) in enumerate(targets, 1):
        try:
            result = check_inn(inn)
        except urllib.error.URLError as ex:
            print(f"  [{i}/{len(targets)}] {slug} ({inn}): ERROR {ex}")
            continue
        if result:
            hits.append({"slug": slug, "inn": inn, **result})
            print(f"  [{i}/{len(targets)}] HIT {slug} ({inn}): {result['license_number']} — {result['status']}")
        time.sleep(DELAY_SECONDS)

    print(f"\n{len(hits)} hit(s) out of {len(targets)} checked")
    out_path = REPO / "data" / "registry" / "_mchs_fire_license_hits.json"
    out_path.write_text(json.dumps(hits, ensure_ascii=False, indent=2))
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
