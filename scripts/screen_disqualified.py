#!/usr/bin/env python3
"""Screen every person with a personal ИНН against ФНС's Реестр
дисквалифицированных лиц (disqualified-persons registry — people barred by
court order from holding a director/management role, usually for prior
corporate misconduct: unpaid taxes as director, fraudulent bankruptcy, etc).

Same underlying infrastructure as scripts/screen_upr_uchr.py — pb.nalog.ru's
two-stage async search-proc.json flow — but a different mode (`search-rdl`,
fields `queryRdl`=ФИО and optionally `dateRdl`=DOB). Confirmed working
2026-08-22 (Бессонов С.Н. tested clean, 0 hits).

If a person has no `dob` on file, this searches by name only and cannot
rule out a same-name/different-person false positive on its own — every
hit is written with `needs_dob_verification: true` and must be manually
confirmed (DOB, or at minimum patronymic + region) against the actual
person before being treated as a real finding. If `dob` IS on file, it is
sent as `dateRdl` — **must be reformatted from this repo's ISO
`YYYY-MM-DD` to `ДД.ММ.ГГГГ` first** (bug found and fixed 2026-09-06: the
raw ISO string gets an immediate 400 with `ERRORS.dateRdl` citing this
exact format requirement — the original 2026-08-22 confirmation predates
this repo having any DOBs on file, so the bug went unexercised until now).

**2026-09-06: pb.nalog.ru's search-rdl now gates behind a captcha
(`pbSearchCaptcha`) after only a handful of requests from one IP in a
short window** — reproduced from two independent networks. The very first
request of a session can still succeed cleanly (confirmed), but a handful
more in quick succession trip `{"ERRORS":{"pbSearchCaptcha":[...]}}`,
which cannot be solved unattended. This is new since the 2026-08-22
confirmation — the endpoint was not captcha-gated then. A full-roster run
will very likely stall partway through; there is no known workaround short
of a human solving the captcha in a browser session, so treat repeated
`pbSearchCaptcha` errors as this wall, not a bug to keep chasing. Try a
long gap between attempts (hours, not minutes) or a small `--limit`/
`--slug` batch per session rather than the full sweep.

Writes `disqualification_hits[]` + `disqualification_checked_at` onto each
person in data/registry/people.json. Fetched screening data, not a hand
correction — survives extract_registry.py regeneration via the same
preserve-forward merge added for securing_measures/other_entities.

**Live network job against a third-party service — per CLAUDE.md's
crawling-jobs policy, tested inline on one person first (see conversation),
full-roster sweep handed to the user to run themselves.**

Usage:
    python3 scripts/screen_disqualified.py
    python3 scripts/screen_disqualified.py --slug bessonov-sergey-nikolaevich
    python3 scripts/screen_disqualified.py --force
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
DELAY_BETWEEN_PEOPLE = 2.0


CONNECT_TIMEOUT = 10  # short on purpose — a hung/geoblocked connection should
                       # surface fast (see below), not sit silent for 30s per
                       # call with up to 10 polls stacked on top of that.


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
        # pb.nalog.ru returns 400 with a JSON body explaining why (bad date
        # format, captcha required, etc) -- surface that instead of the bare
        # "HTTP Error 400: Bad Request" urllib gives by default, since the
        # two failure modes need very different responses (one is a client
        # bug to fix, the other is an anti-bot wall this script cannot get
        # past unattended).
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


def search_rdl(fio: str, dob: str | None) -> list[dict]:
    data = {"mode": "search-rdl", "queryRdl": fio, "page": "1", "pageSize": "50"}
    if dob:
        # dateRdl must be ДД.ММ.ГГГГ -- confirmed 2026-09-06 (this repo's own
        # dob field is ISO YYYY-MM-DD; sending that raw gets an immediate 400
        # with ERRORS.dateRdl citing exactly this format requirement).
        y, m, d = dob.split("-")
        data["dateRdl"] = f"{d}.{m}.{y}"
    print(f"  submitting query ...", end=" ", flush=True)
    ack = post(data)
    print("ok, polling for result")
    if ack.get("captchaRequired"):
        raise RuntimeError("captcha required on search-rdl — cannot proceed unattended")
    result = poll(ack["id"])
    return (result.get("rdl") or {}).get("data") or []


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
        targets = [p for p in targets if p.get("disqualification_checked_at") != today]

    if not targets:
        print("Nothing to do (everyone already checked today — use --force).")
        return

    print(f"Screening {len(targets)} people against {BASE_URL} (search-rdl) ...")
    for i, person in enumerate(targets, 1):
        fio = person.get("fio_ru", "")
        dob = person.get("dob")
        label = f"{person['slug']} ({fio})"
        try:
            rows = search_rdl(fio, dob)
        except (urllib.error.URLError, RuntimeError, TimeoutError) as e:
            print(f"  {i}/{len(targets)}  {label}  ERROR: {e}")
            continue

        hits = [dict(row, needs_dob_verification=not dob) for row in rows]
        person["disqualification_hits"] = hits
        person["disqualification_checked_at"] = today
        PEOPLE.write_text(json.dumps(people, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        flag = " *** DISQUALIFICATION HIT — VERIFY BEFORE USE ***" if hits else ""
        print(f"  {i}/{len(targets)}  {label}  {len(hits)} hit(s){flag}")
        time.sleep(DELAY_BETWEEN_PEOPLE)

    print("\nDone. Any hit needs manual DOB/namesake confirmation before it's treated as real — "
          "see needs_dob_verification on each hit (false for anyone whose DOB was sent as dateRdl).")


if __name__ == "__main__":
    main()
