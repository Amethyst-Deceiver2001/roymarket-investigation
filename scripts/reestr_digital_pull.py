#!/usr/bin/env python3
"""Screen entities against reestr.digital.gov.ru — the official Единый
реестр российских программ для ЭВМ и баз данных (Russian-software registry,
Минцифры). A registration here is hard evidence an entity develops its own
software (relevant to any control-software/autopilot claims), distinct from
and corroborating `products[]`.

Confirmed scriptable 2026-09-05 via plain `curl`, no JS: the registry list
page is server-rendered (Bitrix CMS) and takes a plain GET with an
`OWNER_INN` filter param -- precise, ИНН-keyed, not a name-collision-prone
free-text search. Found via live devtools capture of the actual filter form
(the homepage's own static HTML mentions "тестовые испытания"/"технические
работы" banner text that reads as permanent boilerplate, not a real outage
-- the filtered query itself returns real, current data, e.g. 28 live
registrations for a real test ИНН during reconnaissance).

Confirmed URL shape:
  GET https://reestr.digital.gov.ru/reestr/?tab=registry_active&PROD_NAME=
  &PROD_REESTR_NUM=&CLASSIFIER=&OWNER_NAME=&OWNER_INN=<ИНН>&OWNER_STATUS=
  &PROD_DES_NUM=&PROD_DES_DATE=&REQ_REG_NUM=&REQ_REG_DATE=

The result page carries two counters (`<span class="tabs-list__item-
counter">`) for active and excluded-from-registry entries, and each
registered product is one `<div class="item collection-item ...">` block
with `№ реестровой записи`, `Дата регистрации`, `Наименование ПО`,
`Правообладатель` (owner name -- sometimes NOT the queried ИНН's own name,
since a product can be jointly owned or the query catches a related
entity; always double-check `Правообладатель` against the entity before
treating a hit as confirmed).

Writes `reestr_digital_hit_count`/`reestr_digital_excluded_count`/
`reestr_digital_checked_at` onto each entity in data/registry/entities.json
-- carry-forward screening fields, so they must NOT be set via
corrections_entities.json (see CLAUDE.md) and are wired into
extract_registry.py's ENTITY_CARRY_FORWARD_FIELDS. A real hit's product
list is archived to data/sources/ as
`REESTR_DIGITAL_<ИНН>_<YYYYMMDD>.json` for a human read.

Single unauthenticated GET per ИНН, no captcha, no session -- same class as
screen_rmsp.py. `--slug`/`--limit` is inline reconnaissance; a full-roster
sweep is handed to the user per CLAUDE.md's crawling-jobs policy.

Usage:
    python3 scripts/reestr_digital_pull.py --slug ooo-gagaring
    python3 scripts/reestr_digital_pull.py --limit 20
    python3 scripts/reestr_digital_pull.py --force
"""
from __future__ import annotations

import argparse
import json
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTITIES = REPO / "data" / "registry" / "entities.json"
SOURCES = REPO / "data" / "sources"

BASE_URL = "https://reestr.digital.gov.ru/reestr/"
USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36")
CONNECT_TIMEOUT = 15
DELAY_BETWEEN_QUERIES = 3.0

# TLS: reestr.digital.gov.ru serves a Russian government cert chain not in
# standard trust stores (same class as zakupki.gov.ru's). curl needs -k;
# here we build an unverified context.
_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE

COUNTER_RE = re.compile(r'<span class="tabs-list__item-counter">(\d+)</span>')
ITEM_RE = re.compile(
    r'data-href="(/reestr/\d+/)"\s*>\s*'
    r'<div data-name="№ реестровой записи"><span>([^<]*)</span></div>\s*'
    r'<div data-name="Дата регистрации">\s*<span>([^<]*)</span>\s*</div>\s*'
    r'<div data-name="Наименование ПО"[^>]*>([^<]*)</div>\s*'
    r'<div data-name="Правообладатель">\s*<div>\s*<div class="owner-name">([^<]*)</div>',
    re.DOTALL,
)


def fetch(inn: str, tab: str) -> tuple[str, list[dict]]:
    params = {
        "tab": tab, "PROD_NAME": "", "PROD_REESTR_NUM": "", "CLASSIFIER": "",
        "OWNER_NAME": "", "OWNER_INN": inn, "OWNER_STATUS": "",
        "PROD_DES_NUM": "", "PROD_DES_DATE": "", "REQ_REG_NUM": "", "REQ_REG_DATE": "",
    }
    url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=CONNECT_TIMEOUT, context=_SSL_CTX) as resp:
        html = resp.read().decode("utf-8", errors="replace")

    counters = COUNTER_RE.findall(html)
    items = []
    for m in ITEM_RE.finditer(html):
        items.append({
            "url": "https://reestr.digital.gov.ru" + m.group(1),
            "reg_number": m.group(2).strip(),
            "reg_date": m.group(3).strip(),
            "product_name": m.group(4).strip(),
            "owner_name": m.group(5).strip(),
        })
    return counters, items


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
        targets = [e for e in targets if e.get("reestr_digital_checked_at") != today]
    if args.limit:
        targets = targets[: args.limit]

    if not targets:
        print("Nothing to do (everyone already checked today — use --force).")
        return

    print(f"Screening {len(targets)} entities against reestr.digital.gov.ru ...")
    for i, entity in enumerate(targets, 1):
        inn = entity["inn"]
        label = f"{entity['slug']} ({clean_name(entity['name_ru'])})"
        try:
            counters, items = fetch(inn, "registry_active")
        except (urllib.error.URLError, TimeoutError) as e:
            print(f"  {i}/{len(targets)}  {label}  ERROR: {e}")
            continue

        active_n = int(counters[0]) if counters else 0
        excluded_n = int(counters[1]) if len(counters) > 1 else 0
        entity["reestr_digital_hit_count"] = active_n
        entity["reestr_digital_excluded_count"] = excluded_n
        entity["reestr_digital_checked_at"] = today

        if items:
            out = SOURCES / f"REESTR_DIGITAL_{inn}_{today.replace('-', '')}.json"
            out.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")

        ENTITIES.write_text(json.dumps(entities, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        flag = f" *** {active_n} active, {excluded_n} excluded — READ BEFORE USE ***" if (active_n or excluded_n) else ""
        print(f"  {i}/{len(targets)}  {label}  {flag or 'clean'}")
        time.sleep(DELAY_BETWEEN_QUERIES)

    print("\nDone. A hit's Правообладатель is not always exactly the queried entity's "
          "own name (joint ownership, related entity) -- verify before wiring into products[].")


if __name__ == "__main__":
    main()
