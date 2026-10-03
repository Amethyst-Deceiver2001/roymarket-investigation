#!/usr/bin/env python3
"""Screen entities against zakupki.gov.ru's РНП — реестр недобросовестных
поставщиков (the 44-ФЗ / 223-ФЗ / ПП РФ 615 debarment registries).

Added 2026-09-05 after `notes/SOURCE_REGISTER.md`'s access-tier probe confirmed
all three sub-registries answer a plain `requests` GET with no captcha and no
session (tier A). Reachability re-confirmed the same day against a known ИНН.

**Why a clean result is worth recording.** Unlike most screens here, the
expected outcome is "no record" for nearly every entity. That negative is the
point: "this supplier holds state contracts and has never been debarred" is a
citable fact about a company's standing, and its absence from the registry is
what makes a later appearance meaningful. So this writes a `rnp_screened_at`
timestamp alongside `rnp_matches: []`, following the screened_at convention the
other `screen_*.py` scripts use — a null timestamp means "never checked", an
empty list with a timestamp means "checked, genuinely clean". `coverage_report.py`
reads that distinction directly.

Detection: the results page renders `Поиск не дал результатов` when an ИНН has
no record. Anything else is a hit and gets its page archived to `data/sources/`
for a human read — a hit is a lead to verify against the record card itself,
never a fact to write into the brief straight from a search page.

**Carry-forward caveat** (see CLAUDE.md): `rnp_matches`/`rnp_screened_at` are
raw screening fields, so they must be written directly onto `entities.json` —
NOT via `corrections.json`, where `ENTITY_CARRY_FORWARD_FIELDS` would silently
overwrite them with the previous run's value. This script writes entities.json
directly, the same way every other screen_*.py does.

Live network job. A single `--inn`/`--slug`, or a small `--limit`, is inline
reconnaissance and fine to run directly; a full-roster sweep must be handed to
the user as an exact command per CLAUDE.md's crawling-jobs policy.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import time
from pathlib import Path

import requests
from source_files import write_new  # never overwrite a catalogued source

ROOT = Path(__file__).resolve().parent.parent
REG = ROOT / "data" / "registry"
SOURCES = ROOT / "data" / "sources"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,*/*",
}

# All three debarment sub-registries live on ONE results page, selected by
# three checkboxes (fz94 / fz223 / ppRf615) that are all ticked by default --
# confirmed by reading the live form 2026-09-05. An earlier version of this
# script guessed separate `dishonestsupplier223`/`dishonestsupplier615` paths
# and got HTTP 404 from both; there is only one path, and passing all three
# flags explicitly searches all three registries in a single request.
REGISTRY_FLAGS = "fz94=on&fz223=on&ppRf615=on"
REGISTRY_LABEL = "РНП (44-ФЗ + 223-ФЗ + ПП РФ 615)"

NO_RESULTS = "Поиск не дал результатов"


def strip_html(html: str) -> str:
    t = re.sub(r"(?s)<(script|style).*?</\1>", " ", html)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t)


def check(inn: str) -> tuple[str, str]:
    """Return (verdict, raw_html). verdict is 'clean' | 'hit' | 'error:...'."""
    url = (
        "https://zakupki.gov.ru/epz/dishonestsupplier/search/results.html"
        f"?searchString={inn}&morphology=on&pageNumber=1"
        f"&recordsPerPage=_10&{REGISTRY_FLAGS}"
    )
    try:
        r = requests.get(url, headers=HEADERS, verify=False, timeout=40)
    except Exception as ex:
        return f"error:{type(ex).__name__}", ""
    if r.status_code != 200:
        return f"error:http{r.status_code}", r.text
    text = strip_html(r.text)
    if NO_RESULTS in text:
        return "clean", r.text
    # A page that is neither a no-results page nor recognisably a results page
    # is reported as unknown rather than silently counted as a hit -- the
    # zakupki front end changes layout periodically and a false "hit" would
    # send a human chasing a record that does not exist.
    if "Реестр недобросовестных" not in text:
        return "error:unrecognised-page", r.text
    return "hit", r.text


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--inn", action="append", help="ИНН (repeatable)")
    ap.add_argument("--slug", action="append", help="entity slug (repeatable)")
    ap.add_argument("--limit", type=int, help="screen only the first N unscreened entities")
    ap.add_argument("--force", action="store_true", help="re-screen entities already carrying a timestamp")
    ap.add_argument("--dry-run", action="store_true", help="list what would be screened, make no requests")
    args = ap.parse_args()

    requests.packages.urllib3.disable_warnings()
    entities = json.loads((REG / "entities.json").read_text(encoding="utf-8"))

    if args.inn or args.slug:
        targets = [
            e for e in entities
            if (args.inn and e.get("inn") in args.inn) or (args.slug and e["slug"] in args.slug)
        ]
    else:
        targets = [e for e in entities if e.get("inn")]
        if not args.force:
            targets = [e for e in targets if not e.get("rnp_screened_at")]
        if args.limit:
            targets = targets[: args.limit]

    if not targets:
        print("nothing to screen (all covered? try --force)", file=sys.stderr)
        return 0

    print(f"{len(targets)} entit{'y' if len(targets) == 1 else 'ies'} to screen "
          f"against {REGISTRY_LABEL}")
    if args.dry_run:
        for e in targets:
            print(f"  {e.get('inn'):<14s} {e['slug']}")
        return 0

    today = dt.date.today().isoformat()
    stamp = today.replace("-", "")
    hits_total = 0

    for i, e in enumerate(targets, 1):
        inn = e["inn"]
        matches, errors = [], []
        verdict, html = check(inn)
        if verdict == "hit":
            out = SOURCES / f"RNP_{inn}_{stamp}_debarment.html"
            out = write_new(out, html)
            matches.append({
                "registry": REGISTRY_LABEL,
                "archived_as": out.name,
                "note": "SEARCH-PAGE HIT — verify against the record "
                        "card before citing",
            })
            hits_total += 1
        elif verdict.startswith("error"):
            errors.append({"registry": REGISTRY_LABEL, "error": verdict})
        time.sleep(1.0)  # be polite; this is a public service

        e["rnp_matches"] = matches
        e["rnp_screened_at"] = today
        if errors:
            e["rnp_screen_errors"] = errors

        flag = f"** {len(matches)} HIT(S) **" if matches else ("errors" if errors else "clean")
        print(f"  [{i}/{len(targets)}] {inn:<14s} {flag:<16s} {(e.get('name_ru') or e['slug'])[:48]}")

    (REG / "entities.json").write_text(
        json.dumps(entities, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"\nwrote entities.json — {hits_total} debarment hit(s) across {len(targets)} entities")
    if hits_total:
        print("Verify each hit against its own record card before it goes anywhere near the brief.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
