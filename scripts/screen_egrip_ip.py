#!/usr/bin/env python3
"""Check every POI's personal ИНН against egrul.nalog.ru's open ИП (ЕГРИП)
search, looking for individual-entrepreneur registrations that reveal a
business affiliation not already captured in people.json/entities.json.

This is a LIVE NETWORK JOB against a third-party service (egrul.nalog.ru) —
per CLAUDE.md's crawling-jobs policy, a full-roster sweep (no --slug/--limit)
must be handed to the user as an exact command, never run directly or in the
background. A handful of individual lookups (--slug) is ordinary inline
reconnaissance and fine to run directly — see the memory
`egrul_nalog_ru_open_api` for the two-step token flow this reuses.

Usage:
    python3 scripts/screen_egrip_ip.py --slug barashkov-aleksandr-sergeevich
    python3 scripts/screen_egrip_ip.py --limit 5
    python3 scripts/screen_egrip_ip.py                # full roster (hand to user)
"""
import argparse
import json
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PEOPLE_PATH = REPO / "data" / "registry" / "people.json"
LOG_PATH = REPO / "data" / "registry" / "_egrip_scan_log.json"
SLEEP_SEC = 2.0


def _post(url: str, data: bytes) -> dict:
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def query_inn(inn: str) -> list[dict]:
    """Query egrul.nalog.ru's open search by personal ИНН. Returns the raw
    rows list — 'k':'fl' rows with a nonzero 'tot' are real ИП hits;
    'k':'sprav-fl' with 'tot':'0' means no ИП registration found."""
    body = f"vyp3CaptchaToken=&query={inn}&region=&PreventChromeAutocomplete=".encode()
    tok = _post("https://egrul.nalog.ru/", body).get("t")
    if not tok:
        return []
    time.sleep(SLEEP_SEC)
    result = _get(f"https://egrul.nalog.ru/search-result/{tok}")
    return result.get("rows", [])


def hits_from_rows(rows: list[dict]) -> list[dict]:
    """A real ИП hit is any row with k=='fl' carrying an ОГРНИП ('o') — NOT
    a check on 'tot'/'cnt', which are pagination metadata attached
    inconsistently (only to some rows, e.g. the first of several ИП
    registrations under one ИНН) and NOT a per-row validity flag. The
    'sprav-fl' kind with tot=0 is the real "no results" sentinel, and is a
    distinct k value from 'fl' — it can appear ALONGSIDE real 'fl' hits in
    the same response, not just in place of them.

    Bug history: the original version filtered on
    `r.get("tot", "0") != "0"`, which silently dropped any 'fl' row that
    lacked a 'tot' field — true for every registration after the first when
    a person has 2+ ИП records under one ИНН (caught cross-referencing
    Барашков's known 2-registration case against rusprofile.ru, which showed
    the 2005 registration this filter had dropped from the logged hits)."""
    out = []
    for r in rows:
        if r.get("k") == "fl" and r.get("o"):
            out.append({
                "ogrnip": r.get("o"),
                "name": r.get("n"),
                "registered": r.get("r"),
                "excluded_or_flag": r.get("e"),
            })
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", type=str, default=None, help="single person slug (inline reconnaissance)")
    ap.add_argument("--limit", type=int, default=None, help="cap the roster (for a smoke-test batch)")
    ap.add_argument("--force", action="store_true",
                     help="re-scan slugs already in the log (needed once after the hits_from_rows "
                          "undercount fix — a prior full run may have missed a person's 2nd+ ИП record)")
    args = ap.parse_args()

    people = json.loads(PEOPLE_PATH.read_text(encoding="utf-8"))
    roster = [p for p in people if p.get("inn_personal")]
    if args.slug:
        roster = [p for p in roster if p.get("slug") == args.slug]
        if not roster:
            print(f"no person with slug {args.slug!r} and inn_personal set")
            return
    elif args.limit:
        roster = roster[: args.limit]

    log = json.loads(LOG_PATH.read_text(encoding="utf-8")) if LOG_PATH.exists() else {}
    found = 0
    for i, p in enumerate(roster, 1):
        slug = p["slug"]
        inn = p["inn_personal"]
        if slug in log and not args.slug and not args.force:
            continue  # already scanned in a prior run
        try:
            rows = query_inn(inn)
        except Exception as exc:  # noqa: BLE001
            print(f"[{i}/{len(roster)}] {slug} ({inn}): ERROR {exc}")
            time.sleep(SLEEP_SEC)
            continue
        hits = hits_from_rows(rows)
        log[slug] = {"inn": inn, "hits": hits}
        if hits:
            found += 1
            print(f"[{i}/{len(roster)}] {slug} ({inn}): {len(hits)} ИП record(s) — {[h['ogrnip'] for h in hits]}")
        else:
            print(f"[{i}/{len(roster)}] {slug} ({inn}): none")
        time.sleep(SLEEP_SEC)

    LOG_PATH.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nscanned {len(roster)}, {found} with at least one ИП registration, log written to {LOG_PATH}")


if __name__ == "__main__":
    main()
