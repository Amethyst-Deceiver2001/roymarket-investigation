#!/usr/bin/env python3
"""Cross-check entities against ФСТЭК's two licence registries: reg1
(лицензии на деятельность по технической защите конфиденциальной
информации — ТЗИ) and reg2 (лицензии на разработку и производство средств
защиты конфиденциальной информации — СЗИ). A licence here is directly
relevant for any entity claiming information-security/defence-electronics
work under either regime.

**Not a per-entity query -- a bulk pull matched locally.** The registry's
own per-column server-side filter (`column_filters` in the DataTables AJAX
call) turned out not to work no matter which parameter shape was tried
(numeric column index, column-letter key, native DataTables `columns[N]
[search][value]`) -- every variant silently returned the full unfiltered
3755/1685-row table. Rather than keep reverse-engineering a filter that
may not function at all server-side, this exploits the fact that
`length=-1` ("Все") returns the ENTIRE table in one request -- 3755 rows
for reg1, 1685 for reg2, both confirmed 2026-09-05 -- so the two registries
are pulled ONCE each and matched against every entity's ИНН locally. This
is the same "one bulk pull, match many records offline" pattern as
`aeronext_catalog_api`/rk2035's full-roster sweeps, not a live query per
entity like screen_rmsp.py.

Confirmed endpoint (a Joomla `com_ajax` DataTables handler, found by
reading the reg1/reg2 page's own inline JS `dataTable_191`/`192`
initialization -- table id differs per registry, 191 for reg1, 192 for
reg2):
  POST https://reestr.fstec.ru/?option=com_ajax&module=rtable&method=
       getTableData&format=json&id=<191|192>
  body: draw=1&start=0&length=-1&search[value]=&search[regex]=false&
        module_params=<JSON blob copied verbatim from the page's own
        `var moduleParams = {...}` -- table-specific, re-extract from the
        live page if this ever needs refreshing rather than hand-editing>
The response is a Joomla `{"success":true,...,"data":"<JSON-as-string>"}`
envelope -- `data` itself needs a second `json.loads()`. Columns are keyed
by letter (B..L per the table's own `columnNameDB` mapping); ИНН is
column G.

Two subcommands:
- `fetch` -- pulls both full tables fresh, archives raw responses to
  data/sources/FSTEC_REG1_<YYYYMMDD>.json / FSTEC_REG2_<YYYYMMDD>.json,
  and caches a flat ИНН-indexed lookup to
  data/registry/_fstec_licence_cache.json (not part of the published
  registry -- a working cache, same spirit as
  data/registry/_source_content_cache.json).
- `match` -- reads that cache (fetching fresh first if it's missing) and
  writes `fstec_reg1_hit`/`fstec_reg2_hit`/`fstec_checked_at` onto every
  entity in data/registry/entities.json -- carry-forward screening fields,
  must NOT be set via corrections_entities.json (see CLAUDE.md); wired into
  extract_registry.py's ENTITY_CARRY_FORWARD_FIELDS.

`fetch` is the one live network call in this script (two POSTs total,
not per-entity) -- ordinary reconnaissance scale, fine to run directly.
`match` is pure local processing over the cache, safe to run
directly/repeatedly like mine_leads.py. Re-run `fetch` periodically (the
registries change) rather than trusting a stale cache indefinitely.

Usage:
    python3 scripts/fstec_pull.py fetch
    python3 scripts/fstec_pull.py match
"""
from __future__ import annotations

import argparse
import json
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTITIES = REPO / "data" / "registry" / "entities.json"
SOURCES = REPO / "data" / "sources"
CACHE_FILE = REPO / "data" / "registry" / "_fstec_licence_cache.json"

BASE_URL = "https://reestr.fstec.ru/"
USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36")
CONNECT_TIMEOUT = 60

_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE

REGISTRIES = {
    "reg1": {"table_id": 191, "label": "ТЗИ (техническая защита конфиденциальной информации)"},
    "reg2": {"table_id": 192, "label": "СЗИ (разработка и производство средств защиты информации)"},
}


def get_module_params(reg_slug: str) -> dict:
    req = urllib.request.Request(f"{BASE_URL}{reg_slug}", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=CONNECT_TIMEOUT, context=_SSL_CTX) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    m = re.search(r"var moduleParams = (\{.*?\});", html)
    if not m:
        raise RuntimeError(f"couldn't find moduleParams on /{reg_slug} — page structure may have changed")
    return json.loads(m.group(1))


def fetch_full_table(reg_slug: str, table_id: int, module_params: dict) -> list[dict]:
    url = f"{BASE_URL}?option=com_ajax&module=rtable&method=getTableData&format=json&id={table_id}"
    body = urllib.parse.urlencode({
        "draw": "1", "start": "0", "length": "-1",
        "search[value]": "", "search[regex]": "false",
        "module_params": json.dumps(module_params, ensure_ascii=False),
    }).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={
            "User-Agent": USER_AGENT,
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    with urllib.request.urlopen(req, timeout=CONNECT_TIMEOUT, context=_SSL_CTX) as resp:
        envelope = json.loads(resp.read().decode("utf-8"))
    inner = json.loads(envelope["data"])
    return inner.get("aaData") or []


def cmd_fetch(_args) -> None:
    today = date.today().isoformat()
    stamp = today.replace("-", "")
    cache: dict[str, dict[str, list]] = {}

    for reg_slug, meta in REGISTRIES.items():
        print(f"Fetching {reg_slug} ({meta['label']}) ...")
        module_params = get_module_params(reg_slug)
        rows = fetch_full_table(reg_slug, meta["table_id"], module_params)
        print(f"  {len(rows)} rows")

        out = SOURCES / f"FSTEC_{reg_slug.upper()}_{stamp}.json"
        out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

        by_inn: dict[str, list] = {}
        for row in rows:
            inn = (row.get("G") or "").strip()
            if inn:
                by_inn.setdefault(inn, []).append(row)
        cache[reg_slug] = {"fetched_at": today, "by_inn": by_inn}

    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nWrote cache to {CACHE_FILE}")


def cmd_match(_args) -> None:
    if not CACHE_FILE.exists():
        print("No cache found — running fetch first.")
        cmd_fetch(_args)

    cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    entities = json.loads(ENTITIES.read_text(encoding="utf-8"))
    today = date.today().isoformat()

    hit_total = 0
    for entity in entities:
        inn = entity.get("inn")
        if not inn:
            continue
        for reg_slug in REGISTRIES:
            hits = cache.get(reg_slug, {}).get("by_inn", {}).get(inn, [])
            entity[f"fstec_{reg_slug}_hit"] = hits
            if hits:
                hit_total += 1
        entity["fstec_checked_at"] = today

    ENTITIES.write_text(json.dumps(entities, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Matched {len(entities)} entities against cached ФСТЭК licence data "
          f"(fetched {cache.get('reg1', {}).get('fetched_at', '?')}).")
    print(f"{hit_total} entity-registry hit(s):")
    for entity in entities:
        for reg_slug in REGISTRIES:
            hits = entity.get(f"fstec_{reg_slug}_hit") or []
            if hits:
                print(f"  {entity['slug']} — {reg_slug} ({REGISTRIES[reg_slug]['label']}): "
                      f"{len(hits)} licence(s), status: {hits[0].get('L')}")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("fetch")
    sub.add_parser("match")
    args = ap.parse_args()

    if args.cmd == "fetch":
        cmd_fetch(args)
    elif args.cmd == "match":
        cmd_match(args)


if __name__ == "__main__":
    try:
        main()
    except urllib.error.URLError as e:
        print(f"Network error: {e}", file=sys.stderr)
        sys.exit(1)
