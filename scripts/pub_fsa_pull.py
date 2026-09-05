#!/usr/bin/env python3
"""Screen entities against pub.fsa.gov.ru (ФГИС Росаккредитация) — the
certificates and declarations of conformity registry. Certification records
are hard evidence of what a manufacturer actually makes, distinct from and
corroborating `products[]`/`marketing_claims[]`.

**Corrects notes/SOURCE_REGISTER.md's earlier "Tier A, High priority" call.**
This site sits behind a JS-based anti-bot challenge — a family of obfuscated
per-load endpoints (random-looking paths, binary/enciphered response bodies)
that must run in a real browser before the app will hand out a working
"anonymous" JWT. A bare `curl` to any real API path 403s with no way to
mint a token from scratch; reverse-engineering the challenge itself was not
attempted (out of scope, and these things are deliberately moving targets).
**But the JWT itself, once minted, is fully portable** — confirmed by lifting
one out of a live browser session and reusing it from plain `curl` with zero
cookies, no session, no fingerprint check. So this is genuinely Tier A/B
hybrid: mint a token in a browser roughly every 8 hours (its lifetime, per
its own `exp`/`iat` claims), then script everything else with this file.

**Token refresh recipe** (needs chrome-devtools or equivalent):
1. Navigate to https://pub.fsa.gov.ru/rss/certificate and let it load.
2. Read `localStorage.getItem('fgis_token')` — that's the Bearer token.
3. Pass it to this script via `--token`, or write it to
   `data/.pub_fsa_token` (gitignored, matches `data/sources/`'s own
   local-secret handling) and the script will read it automatically.

Confirmed endpoints (reverse-engineered from live devtools traffic
2026-09-05, see notes/SOURCE_REGISTER.md #40):

- `POST /api/v1/rss/common/certificates/get` — certificates. Filter shape:
  `{"size":N,"page":0,"filter":{"idCertScheme":[],"regDate":{"startDate":
  null,"endDate":null},"endDate":{"startDate":null,"endDate":null},
  "columnsSearch":[{"column":"applicantName","search":"<name>"},
  {"column":"manufacterName","search":"<name>"}]},"columnsSort":
  [{"column":"date","sort":"DESC"}]}`. Note the date-filter key names:
  `startDate`/`endDate`.
- `POST /api/v1/rds/common/declarations/get` — declarations. Same shape but
  under `/rds/` not `/rss/`, its date-filter keys are `minDate`/`maxDate`
  (NOT `startDate`/`endDate` — confirmed the two endpoints are inconsistent
  here, a genuine API quirk not a bug in this script), and its sort column
  is `declDate` not `date`.

**Free-text name search, not ИНН-keyed** — same caveat as
`screen_fas_br.py`: a generic applicant/manufacturer name will pull in
unrelated companies. Every hit needs a human read of the actual
certificate/declaration record before being treated as a fact.

Writes `fsa_cert_hit_count`/`fsa_decl_hit_count`/`fsa_checked_at` onto each
entity in data/registry/entities.json — carry-forward screening fields, so
they must NOT be set via corrections_entities.json (see CLAUDE.md) and are
wired into extract_registry.py's ENTITY_CARRY_FORWARD_FIELDS. A real hit's
full item list is archived to data/sources/ as
`FSA_<CERT|DECL>_<ИНН>_<YYYYMMDD>.json` for a human read.

Once you have a token, every request is a single unauthenticated-looking
POST (Bearer header only, no cookies/session needed) — same class as
screen_rmsp.py/screen_fas_br.py. `--slug`/`--limit` is inline
reconnaissance; a full-roster sweep is handed to the user per CLAUDE.md's
crawling-jobs policy.

Usage:
    python3 scripts/pub_fsa_pull.py --token <JWT> --slug ooo-gagaring
    python3 scripts/pub_fsa_pull.py --limit 20      # reads data/.pub_fsa_token
    python3 scripts/pub_fsa_pull.py --force
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
SOURCES = REPO / "data" / "sources"
TOKEN_FILE = REPO / "data" / ".pub_fsa_token"

USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36")
CONNECT_TIMEOUT = 15
DELAY_BETWEEN_QUERIES = 1.5

CERT_URL = "https://pub.fsa.gov.ru/api/v1/rss/common/certificates/get"
DECL_URL = "https://pub.fsa.gov.ru/api/v1/rds/common/declarations/get"
PAGE_SIZE = 50


def load_token(cli_token: str | None) -> str:
    if cli_token:
        return cli_token
    if TOKEN_FILE.exists():
        return TOKEN_FILE.read_text(encoding="utf-8").strip()
    raise SystemExit(
        "No token. Pass --token <JWT> or write one to data/.pub_fsa_token.\n"
        "Mint one via a browser: open https://pub.fsa.gov.ru/rss/certificate, "
        "then read localStorage.getItem('fgis_token'). Valid ~8 hours."
    )


def post(url: str, body: dict, token: str) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"), method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
            "User-Agent": USER_AGENT,
        },
    )
    with urllib.request.urlopen(req, timeout=CONNECT_TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def search_certificates(name: str, token: str) -> dict:
    body = {
        "size": PAGE_SIZE, "page": 0,
        "filter": {
            "idCertScheme": [],
            "regDate": {"startDate": None, "endDate": None},
            "endDate": {"startDate": None, "endDate": None},
            "columnsSearch": [
                {"column": "applicantName", "search": name},
                {"column": "manufacterName", "search": name},
            ],
        },
        "columnsSort": [{"column": "date", "sort": "DESC"}],
    }
    return post(CERT_URL, body, token)


def search_declarations(name: str, token: str) -> dict:
    # NOTE: this endpoint's columnsSearch items use "name"/"type" keys, NOT
    # "column" like the certificates endpoint above -- confirmed by capturing
    # a live filtered search; using "column" here silently 500s ("Произошла
    # неизвестная ошибка") instead of a helpful schema-mismatch error.
    body = {
        "size": PAGE_SIZE, "page": 0, "count": 0,
        "filter": {
            "status": [], "idDeclType": [], "idCertObjectType": [],
            "idProductType": [], "idGroupRU": [], "idGroupEEU": [],
            "idTechReg": [], "idApplicantType": [],
            "regDate": {"minDate": "", "maxDate": ""},
            "endDate": {"minDate": "", "maxDate": ""},
            "columnsSearch": [
                {"name": "applicantName", "search": name, "type": 0},
                {"name": "manufacterName", "search": name, "type": 0},
            ],
        },
        "columnsSort": [{"column": "declDate", "sort": "DESC"}],
    }
    return post(DECL_URL, body, token)


def clean_name(name_ru: str) -> str:
    m = re.search(r"«([^»]+)»", name_ru)
    return m.group(1) if m else name_ru


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", default=None)
    ap.add_argument("--slug", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    token = load_token(args.token)
    entities = json.loads(ENTITIES.read_text(encoding="utf-8"))
    today = date.today().isoformat()

    targets = [e for e in entities if e.get("name_ru")]
    if args.slug:
        targets = [e for e in targets if e["slug"] == args.slug]
    if not args.force:
        targets = [e for e in targets if e.get("fsa_checked_at") != today]
    if args.limit:
        targets = targets[: args.limit]

    if not targets:
        print("Nothing to do (everyone already checked today — use --force).")
        return

    print(f"Screening {len(targets)} entities against pub.fsa.gov.ru "
          f"(certificates + declarations) ...")
    for i, entity in enumerate(targets, 1):
        name = clean_name(entity["name_ru"])
        inn = entity.get("inn", "noinn")
        label = f"{entity['slug']} ({name})"
        try:
            cert_result = search_certificates(name, token)
            time.sleep(DELAY_BETWEEN_QUERIES)
            decl_result = search_declarations(name, token)
        except urllib.error.HTTPError as e:
            if e.code == 401:
                raise SystemExit(
                    f"\n401 Unauthorized on {label} — token expired. "
                    "Mint a fresh one (see docstring) and re-run."
                )
            print(f"  {i}/{len(targets)}  {label}  ERROR: HTTP {e.code}")
            continue
        except (urllib.error.URLError, TimeoutError) as e:
            print(f"  {i}/{len(targets)}  {label}  ERROR: {e}")
            continue

        # The API's own "total" field is unreliable -- a genuinely 0-item
        # response was observed carrying total:1000 (looks like a stale/
        # unfiltered placeholder, not the real filtered count). So this
        # counts actual returned items, capped at PAGE_SIZE, and flags a
        # count exactly at the cap as a probable undercount rather than
        # trusting "total".
        cert_items = cert_result.get("items") or []
        decl_items = decl_result.get("items") or []
        cert_n, decl_n = len(cert_items), len(decl_items)
        entity["fsa_cert_hit_count"] = cert_n
        entity["fsa_decl_hit_count"] = decl_n
        entity["fsa_checked_at"] = today

        if cert_items:
            out = SOURCES / f"FSA_CERT_{inn}_{today.replace('-', '')}.json"
            out.write_text(json.dumps(cert_items, ensure_ascii=False, indent=2), encoding="utf-8")
        if decl_items:
            out = SOURCES / f"FSA_DECL_{inn}_{today.replace('-', '')}.json"
            out.write_text(json.dumps(decl_items, ensure_ascii=False, indent=2), encoding="utf-8")

        ENTITIES.write_text(json.dumps(entities, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        flag = ""
        if cert_items or decl_items:
            cert_label = f"{cert_n}{'+' if cert_n == PAGE_SIZE else ''}"
            decl_label = f"{decl_n}{'+' if decl_n == PAGE_SIZE else ''}"
            flag = f" *** {cert_label} cert(s), {decl_label} decl(s) — READ BEFORE USE ***"
        print(f"  {i}/{len(targets)}  {label}  {flag or 'clean'}")
        time.sleep(DELAY_BETWEEN_QUERIES)

    print("\nDone. Free-text name search, not ИНН-keyed — every hit needs a human "
          "read of the archived record before it goes near products[]/tier_basis.")


if __name__ == "__main__":
    main()
