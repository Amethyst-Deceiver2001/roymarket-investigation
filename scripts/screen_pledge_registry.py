#!/usr/bin/env python3
"""Screen registry entities against the Federal Notary Chamber's Реестр
уведомлений о залоге движимого имущества (reestr-zalogov.ru) — the
national notice-of-pledge-of-movable-property registry, cross-searching
Федресурс at the same time (the site's UI defaults "Искать на Федресурсе"
to checked).

**Confirmed hard-gated behind Google reCAPTCHA v3 — every single search
request, not a rate-limit-triggered wall like pb.nalog.ru's disqualified-
persons search.** The real endpoints are:

    POST https://www.reestr-zalogov.ru/api/search/notary?token=<recaptcha-v3-token>
    POST https://www.reestr-zalogov.ru/api/search/fedresurs?token=<recaptcha-v3-token>

with a JSON body of `{"inn": "..."}` (also accepts `name`/`ogrn`, matching
the UI's three fields). Confirmed 2026-09-08: a bare POST with no `token`
param (or an empty one) gets an immediate `HTTP 403
{"message":"Не пройдена проверка CAPTCHA"}` — this is not a soft/scored
check that occasionally waves a request through, it is a hard block on
every call. A valid token can only come from Google's reCAPTCHA v3 JS
actually executing in a real browser context (site key
`6LdKJhMaAAAAAIfeHC6FZc-UVfzDQpiOjaJUWoxr`, invisible/score-based, no
visible checkbox) — there is no unattended way to obtain one from a plain
HTTP client, and this script does not attempt to (no captcha-solving
service, per this project's standing conventions).

**This means: no full-roster automation is possible for this source.**
Same class of wall as kad.arbitr.ru (see
`kad_arbitr_ru_ddos_guard_blocked.md`), but confirmed via chrome-devtools
(a real browser session) that a *single* lookup works cleanly through the
actual site UI — no visible challenge appeared in the one test run
(2026-09-08, ООО «Гагаринг» ИНН 2312321660, 0 hits) — reCAPTCHA v3 must
have scored that session highly enough to pass silently. There is no
guarantee of that on every attempt.

**How to actually use this for a real check (manual, one entity at a
time)**: open a chrome-devtools browser session, navigate to
https://www.reestr-zalogov.ru/search/index, click "По информации о
залогодателе" then "Юридическое лицо", fill the ИНН field, click "НАЙТИ".
Read the result text directly (no captcha *widget* is shown when v3 scores
you high enough — if a visible image/audio challenge DOES appear, solve it
the same way `screen_gagaring`-style Честный Знак/kad.arbitr.ru sessions
already did in this project). This script exists to (a) document the real
API shape for whoever picks this up next, and (b) give a single-entity CLI
that fails loudly and explains the wall, rather than silently returning
nothing — never guess or fabricate a "0 hits" result without actually
having read one.

Writes nothing on its own (see LIMITATION above) — a real result must be
saved by hand via the same pattern used for the first entity checked
(`data/sources/REESTRZALOGOV_<ИНН>_<YYYYMMDD>_<result>.txt` +
`pledge_registry_matches[]`/`pledge_registry_checked_at` via
corrections_entities.json).

Usage:
    python3 scripts/screen_pledge_registry.py --inn 2312321660
    python3 scripts/screen_pledge_registry.py --slug ooo-gagaring
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTITIES = REPO / "data" / "registry" / "entities.json"

NOTARY_URL = "https://www.reestr-zalogov.ru/api/search/notary"
FEDRESURS_URL = "https://www.reestr-zalogov.ru/api/search/fedresurs"
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def attempt(url: str, inn: str) -> dict:
    body = json.dumps({"inn": inn}).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{e.code} {e.reason} -- {detail}") from None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inn", default=None)
    ap.add_argument("--slug", default=None)
    args = ap.parse_args()

    inn = args.inn
    if args.slug:
        entities = json.loads(ENTITIES.read_text(encoding="utf-8"))
        match = next((e for e in entities if e["slug"] == args.slug), None)
        if not match:
            sys.exit(f"No entity with slug={args.slug}")
        inn = match.get("inn")
        if not inn:
            sys.exit(f"{args.slug} has no ИНН on file")

    if not inn:
        sys.exit("Pass --inn or --slug")

    print(f"Attempting unattended lookup for ИНН {inn} (expected to fail — see docstring) ...")
    try:
        result = attempt(NOTARY_URL, inn)
        print("Unexpected success (no captcha enforced this time):")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    except RuntimeError as e:
        print(f"  notary endpoint: {e}")

    print(
        "\nAs expected: reestr-zalogov.ru requires a Google reCAPTCHA v3 token on "
        "every /api/search/* call, which cannot be obtained from a plain HTTP "
        "client. This source has NO unattended screening path.\n\n"
        "Use a real browser session instead (chrome-devtools MCP or similar):\n"
        "  1. Navigate to https://www.reestr-zalogov.ru/search/index\n"
        "  2. Click \"По информации о залогодателе\" -> \"Юридическое лицо\"\n"
        f"  3. Fill ИНН = {inn}, click \"НАЙТИ\"\n"
        "  4. Solve any visible CAPTCHA challenge that appears (often none — v3 "
        "is score-based and may pass silently)\n"
        "  5. Read the result text and save it by hand as "
        f"data/sources/REESTRZALOGOV_{inn}_<YYYYMMDD>_<result>.txt, then wire "
        "pledge_registry_matches[]/pledge_registry_checked_at via "
        "corrections_entities.json (see ooo-gagaring for the precedent)."
    )


if __name__ == "__main__":
    main()
