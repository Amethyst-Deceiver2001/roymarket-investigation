#!/usr/bin/env python3
"""Reverse-lookup every person on file with a personal ИНН against
pb.nalog.ru's "Участие в ЮЛ" (person -> every legal entity where they're
director/founder) search — surfaces companies a network principal is tied
to that this investigation hasn't found any other way.

No ЕСИА/login required, but it's a two-stage async flow (not a single
synchronous POST like scripts/screen_rom.py):

  1. POST search-proc.json  mode=search-upr-uchr  queryUpr=<ИНН>
     -> {"id": ...}, poll the SAME endpoint with id=<id>&method=get-response
     until it returns real data (not null) -> "upr" (director-of) and
     "uchr" (founder-of) cards, each with a role-specific `token` and a
     `ul_cnt` (how many entities).
  2. For each card: POST search-proc.json  mode=search-ul  token=<card
     token>  queryUl=<card's own "name" field, i.e. the person's full name
     as ФНС has it — required, an empty queryUl returns zero rows even with
     a valid token>, poll the same way -> the actual entity list (name,
     ИНН, ОГРН, ОКВЭД, registration date, EGRUL/BFO links).

Confirmed working 2026-08-22 end-to-end on Шатракова А.А. (ИНН
773126193790) — correctly resolved back to the already-known ООО
«Архангел» via both the "upr" and "uchr" roles.

Writes `other_entities[]` onto each person in data/registry/people.json —
each item {inn, ogrn, name, role (director|founder), okved, registered,
region}. This is fetched screening data (same category as sanctions[] on
entities), not a hand correction.

**Live network job against a third-party service — per CLAUDE.md's
crawling-jobs policy, tested inline on one person first, full-roster sweep
handed to the user to run themselves rather than executed in the
background.** Only 6-8 people currently have inn_personal populated, so
this is a short list, not a heavy batch — but the policy applies regardless
of scale.

**2026-09-06: shares pb.nalog.ru's search-proc.json backend with
screen_disqualified.py, and shares its captcha wall** — see that script's
docstring for the full writeup. A `pbSearchCaptcha` error here means the
same anti-bot gate, not a bug in this script's search-upr-uchr/search-ul
calls; confirmed via direct curl reproduction, not specific to this
script's request shape.

**2026-09-07: bumping DELAY_BETWEEN_PEOPLE (2.0 -> 15.0) did NOT avoid
the wall.** A real run against the (by then 137-person) inn_personal
roster got 35 people through before `pbSearchCaptcha` started firing
repeatedly, roughly the same request count as the original 2.0s-delay
run that stalled around #10-11 -- so this looks like a count/session
based gate, not a request-rate one. A loop errors-and-continues past a
captcha hit rather than aborting (see main()), so a full run still
crawls the whole list and picks up whatever real successes it can before
the wall reasserts itself; don't expect a longer per-request delay alone
to fix it. Confirmed effective mitigation instead: **wait hours, not
minutes, between attempts** (the wall does not appear to reset within a
session) -- a same-day immediate re-run mostly just re-hits the wall for
anyone still unchecked, though re-running is still harmless (it skips
anyone already checked today) if you want to grab the occasional
straggler that gets through.

Usage:
    python3 scripts/screen_upr_uchr.py                  # everyone with inn_personal
    python3 scripts/screen_upr_uchr.py --slug shatrakova-anastasiya-artemovna
    python3 scripts/screen_upr_uchr.py --force           # re-check even if already checked today
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PEOPLE = REPO / "data" / "registry" / "people.json"

BASE_URL = "https://pb.nalog.ru/search-proc.json"
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")

POLL_DELAY = 2.0
POLL_MAX_TRIES = 10
DELAY_BETWEEN_PEOPLE = 15.0  # bumped 2026-09-07 from 2.0 -- pb.nalog.ru's
# search-proc.json captcha-gates after ~10 requests in quick succession
# (see screen_disqualified.py's header for the discovery). Untested whether
# a longer per-request gap actually avoids the wall or just delays hitting
# it by the same request count -- worth another data point before assuming
# it works.


CONNECT_TIMEOUT = 10  # short on purpose — a hung/geoblocked connection should
                       # surface fast, not sit silent for 30s per call with
                       # up to 10 polls stacked on top of that.


def post(data: dict) -> dict:
    body = urllib.parse.urlencode(data).encode("ascii")
    req = urllib.request.Request(
        BASE_URL, data=body, method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": USER_AGENT,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=CONNECT_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # See screen_disqualified.py's identical fix (2026-09-06): pb.nalog.ru
        # returns a 400 with a JSON body explaining why (captcha wall, bad
        # field, etc) -- surface that instead of urllib's bare "HTTP Error
        # 400: Bad Request".
        try:
            detail = e.read().decode("utf-8", errors="replace")
        except Exception:
            detail = ""
        raise urllib.error.HTTPError(e.url, e.code, f"{e.reason} -- {detail}", e.headers, None) from None


def poll(request_id: str) -> dict:
    for attempt in range(1, POLL_MAX_TRIES + 1):
        time.sleep(POLL_DELAY)
        print(f"    poll {attempt}/{POLL_MAX_TRIES} ...", end=" ", flush=True)
        result = post({"id": request_id, "method": "get-response"})
        print("got data" if result is not None else "not ready")
        if result is not None:
            return result
    raise TimeoutError(f"search-proc.json never resolved id={request_id}")


def search_upr_uchr(inn: str) -> dict:
    ack = post({"mode": "search-upr-uchr", "queryUpr": inn,
                "uprType1": "1", "uprType0": "1", "page": "1", "pageSize": "50"})
    if ack.get("captchaRequired"):
        raise RuntimeError("captcha required on search-upr-uchr — cannot proceed unattended")
    return poll(ack["id"])


def search_ul_by_token(token: str, query_name: str) -> list[dict]:
    ack = post({"mode": "search-ul", "token": token, "queryUl": query_name,
                "page": "1", "pageSize": "50"})
    if ack.get("captchaRequired"):
        raise RuntimeError("captcha required on search-ul drill-down — cannot proceed unattended")
    result = poll(ack["id"])
    return (result.get("ul") or {}).get("data") or []


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", default=None)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    people = json.loads(PEOPLE.read_text(encoding="utf-8"))
    today = date.today().isoformat()

    targets = [p for p in people if p.get("inn_personal")]
    if args.slug:
        targets = [p for p in targets if p["slug"] == args.slug]
    if not args.force:
        targets = [p for p in targets if p.get("other_entities_checked_at") != today]

    if not targets:
        print("Nothing to do (everyone with inn_personal already checked today — use --force).")
        return

    print(f"Screening {len(targets)} people against {BASE_URL} ...")
    for i, person in enumerate(targets, 1):
        inn = person["inn_personal"]
        label = f"{person['slug']} ({inn})"
        try:
            summary = search_upr_uchr(inn)
        except (urllib.error.URLError, RuntimeError, TimeoutError) as e:
            print(f"  {i}/{len(targets)}  {label}  ERROR at summary stage: {e}")
            continue

        found = []
        for role_key, role_label in (("upr", "director"), ("uchr", "founder")):
            cards = (summary.get(role_key) or {}).get("data") or []
            for card in cards:
                token = card.get("token")
                query_name = card.get("name", "")
                if not token:
                    continue
                try:
                    rows = search_ul_by_token(token, query_name)
                except (urllib.error.URLError, RuntimeError, TimeoutError) as e:
                    print(f"  {i}/{len(targets)}  {label}  ERROR at drill-down ({role_label}): {e}")
                    continue
                for row in rows:
                    found.append({
                        "inn": row.get("inn"),
                        "ogrn": row.get("ogrn"),
                        "name": row.get("namep") or row.get("namec"),
                        "role": role_label,
                        "okved": row.get("okved2main"),
                        "okved_label": row.get("okved2mainname"),
                        "registered": row.get("dtreg"),
                        "region": row.get("regionname"),
                    })

        person["other_entities"] = found
        person["other_entities_checked_at"] = today
        PEOPLE.write_text(json.dumps(people, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        new_inns = {f["inn"] for f in found}
        print(f"  {i}/{len(targets)}  {label}  {len(found)} entit(y/ies) found: {', '.join(sorted(new_inns)) or '-'}")
        time.sleep(DELAY_BETWEEN_PEOPLE)

    print("\nDone. Cross-check each ИНН against data/registry/entities.json — anything new is a lead, "
          "not a confirmed link, per the usual verify-before-use discipline.")


if __name__ == "__main__":
    main()
