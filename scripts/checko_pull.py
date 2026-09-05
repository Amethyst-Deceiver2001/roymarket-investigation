#!/usr/bin/env python3
"""Screen entities against checko.ru — a company-data aggregator. Corroboration
only, per notes/SOURCE_REGISTER.md (Medium priority: primary sources like
EGRUL/БФО/zakupki are always preferred; this exists to catch a gap those
haven't caught yet, not to replace them).

Confirmed scriptable 2026-09-05 via plain `curl`, no JS: `GET /search?query=
<ИНН>` 301-redirects straight to the company card (`/company/<slug>-<ОГРН>`)
on an exact ИНН match — precise, not a name-collision-prone free-text search
like screen_fas_br.py/pub_fsa_pull.py. The card's sidebar nav lists every
section with its own item count (`Арбитражные дела <span class="count">1
</span>`, etc) — cheap corroboration signal without parsing each section's
actual content.

**Why this is worth running despite being "just an aggregator":** the
section counts are a fast cross-check against this registry's own arrays.
An entity showing `legal-cases: 1` on checko but an empty `litigation[]`
here, or `enforcements` (ФССП) present here but not yet checked via
screen_fssp-equivalent, is a concrete lead -- not a citable fact (checko is
a secondary aggregator, its own data ultimately derives from primary
sources this project already has direct pullers for), but a pointer to go
read the primary source. Flagged prominently in this script's own output
when a mismatch like this appears; never wired into litigation[]/sanctions[]
directly from checko's own numbers.

Writes `checko_status`/`checko_section_counts`/`checko_checked_at` onto each
entity in data/registry/entities.json -- carry-forward screening fields, so
they must NOT be set via corrections_entities.json (see CLAUDE.md) and are
wired into extract_registry.py's ENTITY_CARRY_FORWARD_FIELDS.

Single unauthenticated GET per ИНН, no captcha, no session -- same class as
screen_rmsp.py. `--slug`/`--limit` is inline reconnaissance; a full-roster
sweep is handed to the user per CLAUDE.md's crawling-jobs policy.

**checko.ru rate-limits more aggressively than the other pullers in this
toolkit** -- confirmed 2026-09-05: a burst of ~8 requests inside a couple
minutes drew HTTP 429 on every subsequent request for several minutes
after. The script retries a 429 twice with backoff (15s, 30s), but a full
174-entity sweep should budget real wall-clock time for this (the 6s
per-query delay is deliberately generous) and expect occasional stretches
of ERROR lines that clear up if re-run later with `--force` on just the
failed slugs, rather than assumed to be a broken puller.

Usage:
    python3 scripts/checko_pull.py --slug ooo-gagaring
    python3 scripts/checko_pull.py --limit 20
    python3 scripts/checko_pull.py --force
"""
from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTITIES = REPO / "data" / "registry" / "entities.json"

USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36")
CONNECT_TIMEOUT = 15
DELAY_BETWEEN_QUERIES = 6.0

SECTION_RE = re.compile(
    r'href="#([a-z-]+)"[^>]*>.*?</svg></i>([^<]+?)\s*'
    r'(?:<span class="count">(\d+)</span>)?</a>'
)
STATUS_RE = re.compile(
    r'<div class="text-(success|danger|warning|muted)[^"]*"><span class="check-icon">.*?</use></svg></span>([^<]+)</div>'
)

# Sections whose counts are worth cross-checking against this registry's own
# arrays -- (checko section key, entity field it should show up in).
CROSS_CHECK = {
    "legal-cases": "litigation",
    "enforcements": None,  # no dedicated field yet; flag only
    "fedresurs": None,
}


def fetch(inn: str) -> tuple[bool, str, dict, str | None]:
    """Return (hit, status_text, section_counts, final_url)."""
    url = f"https://checko.ru/search?query={inn}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=CONNECT_TIMEOUT) as resp:
                html = resp.read().decode("utf-8", errors="replace")
                final_url = resp.geturl()
            break
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return False, "", {}, None
            if e.code == 429 and attempt < 2:
                time.sleep(15 * (attempt + 1))
                continue
            raise

    if "/company/" not in final_url and "/entrepreneur/" not in final_url:
        # Landed on a search-results page, not an exact-match redirect --
        # treat as no confirmed hit rather than guessing among candidates.
        return False, "", {}, final_url

    status_m = STATUS_RE.search(html)
    status = status_m.group(2).strip() if status_m else ""

    counts = {}
    for m in SECTION_RE.finditer(html):
        key, label, count = m.group(1), m.group(2).strip(), m.group(3)
        if count is not None:
            counts[key] = int(count)

    return True, status, counts, final_url


def clean_name(name_ru: str) -> str:
    m = re.search(r"«([^»]+)»", name_ru)
    return m.group(1) if m else name_ru


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    entities = json.loads(ENTITIES.read_text(encoding="utf-8"))
    today = date.today().isoformat()

    targets = [e for e in entities if e.get("inn")]
    if args.slug:
        targets = [e for e in targets if e["slug"] == args.slug]
    if not args.force:
        targets = [e for e in targets if e.get("checko_checked_at") != today]
    if args.limit:
        targets = targets[: args.limit]

    if not targets:
        print("Nothing to do (everyone already checked today — use --force).")
        return

    print(f"Screening {len(targets)} entities against checko.ru (ИНН redirect lookup) ...")
    for i, entity in enumerate(targets, 1):
        inn = entity["inn"]
        label = f"{entity['slug']} ({clean_name(entity['name_ru'])})"
        try:
            hit, status, counts, final_url = fetch(inn)
        except (urllib.error.URLError, TimeoutError) as e:
            print(f"  {i}/{len(targets)}  {label}  ERROR: {e}")
            continue

        entity["checko_status"] = status
        entity["checko_section_counts"] = counts
        entity["checko_checked_at"] = today
        ENTITIES.write_text(json.dumps(entities, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        gaps = []
        checko_cases = counts.get("legal-cases", 0)
        on_file = len(entity.get("litigation") or [])
        if checko_cases > on_file:
            gaps.append(f"legal-cases={checko_cases} on checko vs {on_file} in litigation[]")
        if counts.get("enforcements", 0) > 0:
            gaps.append(f"enforcements(ФССП)={counts['enforcements']} not checked elsewhere")

        if not hit:
            print(f"  {i}/{len(targets)}  {label}  no exact match")
        else:
            flag = f" *** GAP: {'; '.join(gaps)} ***" if gaps else ""
            print(f"  {i}/{len(targets)}  {label}  [{status}] {counts}{flag}")
        time.sleep(DELAY_BETWEEN_QUERIES)

    print("\nDone. checko.ru is corroboration only -- a count mismatch is a lead to "
          "read the primary source, never a fact to wire in directly from checko's own numbers.")


if __name__ == "__main__":
    main()
