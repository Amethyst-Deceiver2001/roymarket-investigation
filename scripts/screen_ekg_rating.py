#!/usr/bin/env python3
"""Screen every entity with an ИНН against Индекс «ЭКГ» (Экология — Кадры —
Государство), the national corporate-responsibility rating index run under
Rosstandart/РСПП technical-committee methodology (ГОСТ Р 71198-2026) —
экг-рейтинг.рф (punycode xn----etbbhpfd3axw8i.xn--p1ai).

**Discovered 2026-09-08** while reverse-engineering a Kontur.Focus Pro
export for АНО «НПЦ «Ушкуйник»» (see [[roymarket]] session notes) — Kontur
displays this index's score on its own company page and links out to
экг-рейтинг.рф/companies/<ИНН> for "Подробнее". экг-рейтинг.рф is a Nuxt SPA
whose actual company data comes from an unauthenticated public GraphQL API,
NOT visible in a plain `curl` of the HTML (the real fetch happens
server-side during Nuxt SSR, so it never shows up as a client-side XHR in a
naive network capture — only a set of Dynatrace-style telemetry-beacon POSTs
to scrambled per-session hashed paths do, e.g. `POST /_oCefAic2...` →
`{"status": "success", "result": 0}` — same noise pattern already documented
for proverki.gov.ru, ignore those).

**Real endpoint**, confirmed working 2026-09-08:

    GET  https://xn----etbbhpfd3axw8i.xn--p1ai/sanctum/csrf-cookie
         -> 204, sets XSRF-TOKEN + ekg_new_session cookies (Laravel Sanctum
            SPA auth — this is a same-origin CSRF guard, not a login; no
            account/credentials needed)
    POST https://xn----etbbhpfd3axw8i.xn--p1ai/graphql/public
         headers: Cookie (from the csrf-cookie response), plus
         `x-xsrf-token: <url-decoded XSRF-TOKEN cookie value>`, Origin and
         Referer both set to the site's own origin (a bare POST with no
         Origin/Referer/cookie gets a flat nginx-level 403, not a GraphQL
         error — this is a WAF rule, not app auth)
         body: {"query": "query CompanyEkg($inn: String!) { company(inn:
         $inn) { ... } }", "variables": {"inn": "<ИНН>"}}

**Introspection is wide open** (`{ __schema { queryType { fields { name } } } }`
returns the full root field list, `{ __type(name: "Company") { fields {...} } }`
the full return-object shape) — this is how the field list below was
confirmed rather than guessed from the rendered page alone.

Confirmed via two real ИНН, 2026-09-08:
  - 5300010714 (АНО «НПЦ «Ушкуйник»»): level_1 "A", level_2 "Продвинутый",
    ecology_points 15, staff_points 31.5, government_points 35.783,
    result_points 83 — matches the Kontur.Focus Pro PDF's own displayed
    83/15/32/36 exactly (Kontur rounds staff/government to whole numbers).
  - 2312321660 (ООО «Гагаринг»): level_1 "BBB", level_2 "Средний",
    ecology_points 15, staff_points 27.3, government_points 38.375,
    result_points 80 — a rating this project had NOT previously found for
    Гагаринг by any other route; the two ИНН above were tested independently
    of each other, both real hits, confirming this isn't a fixed/cached
    response.
  - A bogus ИНН ("0000000000") returns `{"data":{"company":null}}` cleanly —
    a real, distinguishable negative, not an error.

This is a THIRD-PARTY RATING, not a government registry — a company applies
or is nominated into the index and self-reports data behind the "Кадры"/
"Государство" subscores (see the `is_application_completed`/
`application_result_points` fields, which distinguish an entity that
submitted its own additional data from one purely externally scored).
Treat a rating as a legitimacy/self-presentation signal, same tier as
`state_programs[]` or `checko_status` — not sanctions- or debarment-grade
evidence, and not a substitute for `financials[]`/`workforce_history[]`
(the index's own `revenue_year`/`average_headcount` fields are useful
corroboration but shallower than a primary БФО filing).

Writes `ekg_rating_matches[]` (empty list on a clean/no-rating result,
one-element list with the full record on a hit) + `ekg_rating_checked_at`
directly onto entities.json — fetched screening data, not a hand
correction (see CLAUDE.md's carry-forward-fields rule); has been added to
`ENTITY_CARRY_FORWARD_FIELDS` in extract_registry.py.

Live network job against a third-party (if unauthenticated) rating site —
per CLAUDE.md's crawling-jobs policy, tested inline on 2 entities first
(see above); `--slug`/`--inn` is ordinary inline reconnaissance, a
full-roster sweep (no `--slug`/`--limit`) should be handed to the user to
run themselves, not executed in the background — the csrf-cookie handshake
plus a GraphQL POST per entity is two requests each, cheap individually but
still real work at roster scale.

Usage:
    python3 scripts/screen_ekg_rating.py --slug ano-npts-ushkuynik
    python3 scripts/screen_ekg_rating.py --inn 2312321660
    python3 scripts/screen_ekg_rating.py --limit 20
    python3 scripts/screen_ekg_rating.py --force
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTITIES = REPO / "data" / "registry" / "entities.json"

ORIGIN = "https://xn----etbbhpfd3axw8i.xn--p1ai"
CSRF_URL = f"{ORIGIN}/sanctum/csrf-cookie"
GRAPHQL_URL = f"{ORIGIN}/graphql/public"
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")
CONNECT_TIMEOUT = 10
DELAY_BETWEEN_QUERIES = 1.5

COMPANY_QUERY = """
query CompanyEkg($inn: String!) {
  company(inn: $inn) {
    id
    inn
    name
    level_1
    level_2
    ecology_points
    staff_points
    government_points
    result_points
    status
    is_application_completed
    scoring_result_points
    application_result_points
    founded_at
    average_headcount
    revenue_year
    region_registration { name }
    okved { name }
    okved_code { kod name }
    company_category { name }
  }
}
""".strip()


class EkgSession:
    """Handles the Sanctum CSRF handshake once, reuses cookies across queries."""

    def __init__(self) -> None:
        self.cookiejar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookiejar))
        self._prime()

    def _prime(self) -> None:
        req = urllib.request.Request(
            CSRF_URL,
            headers={"User-Agent": USER_AGENT, "Origin": ORIGIN, "Referer": ORIGIN + "/"},
        )
        with self.opener.open(req, timeout=CONNECT_TIMEOUT) as resp:
            resp.read()
        self.xsrf_token = None
        for cookie in self.cookiejar:
            if cookie.name == "XSRF-TOKEN":
                self.xsrf_token = urllib.parse.unquote(cookie.value)
        if not self.xsrf_token:
            raise RuntimeError("csrf-cookie handshake did not set XSRF-TOKEN")

    def query_company(self, inn: str) -> dict | None:
        body = json.dumps({
            "operationName": "CompanyEkg",
            "query": COMPANY_QUERY,
            "variables": {"inn": inn},
        }).encode("utf-8")
        req = urllib.request.Request(
            GRAPHQL_URL, data=body, method="POST",
            headers={
                "Content-Type": "application/json",
                "Accept": "*/*",
                "Origin": ORIGIN,
                "Referer": f"{ORIGIN}/companies/{inn}",
                "x-xsrf-token": self.xsrf_token,
                "User-Agent": USER_AGENT,
            },
        )
        with self.opener.open(req, timeout=CONNECT_TIMEOUT) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        if result.get("errors"):
            raise RuntimeError(f"GraphQL error(s): {result['errors']}")
        return result.get("data", {}).get("company")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", default=None)
    ap.add_argument("--inn", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    entities = json.loads(ENTITIES.read_text(encoding="utf-8"))
    today = date.today().isoformat()

    targets = [e for e in entities if e.get("inn")]
    if args.slug:
        targets = [e for e in targets if e["slug"] == args.slug]
    elif args.inn:
        targets = [e for e in targets if e["inn"] == args.inn]
    if not args.force:
        targets = [e for e in targets if e.get("ekg_rating_checked_at") != today]
    if args.limit:
        targets = targets[: args.limit]

    if not targets:
        print("Nothing to do (everyone already checked today — use --force).")
        return

    print(f"Screening {len(targets)} entities against экг-рейтинг.рф "
          f"({ORIGIN}/graphql/public) ...")
    session = EkgSession()

    hits = 0
    for i, e in enumerate(targets, 1):
        inn = e["inn"]
        try:
            company = session.query_company(inn)
        except (urllib.error.URLError, RuntimeError) as exc:
            print(f"  [{i}/{len(targets)}] {e['slug']} ({inn})  ERROR {exc}")
            time.sleep(DELAY_BETWEEN_QUERIES)
            continue

        if company:
            hits += 1
            e["ekg_rating_matches"] = [company]
            print(f"  [{i}/{len(targets)}] {e['slug']} ({inn})  "
                  f"{company.get('level_1')}/{company.get('level_2')} "
                  f"score={company.get('result_points')}")
        else:
            e["ekg_rating_matches"] = []
            print(f"  [{i}/{len(targets)}] {e['slug']} ({inn})  no rating")
        e["ekg_rating_checked_at"] = today

        if i < len(targets):
            time.sleep(DELAY_BETWEEN_QUERIES)

    ENTITIES.write_text(json.dumps(entities, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote entities.json — {hits} rated entit{'y' if hits == 1 else 'ies'} "
          f"found out of {len(targets)} checked.")
    print("Run scripts/extract_registry.py then scripts/check_registry.py next.")


if __name__ == "__main__":
    main()
