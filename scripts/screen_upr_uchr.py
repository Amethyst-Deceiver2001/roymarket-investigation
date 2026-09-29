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

**2026-09-29: archives raw evidence.** Every hit this script finds used to
sit unsourced (no raw file backed it, so `other_entities[]` claims had no
`source_id` and fed unsourced `role` edges in the relationship graph — 108
people affected as of this writing). Each person with any real hit this run
now gets their raw upr/uchr card rows written to
`data/sources/FNS_PB_UPR_UCHR_<inn_personal>_<YYYYMMDD>_<slug>-raw.json`
(same convention as the two hand-captured files this convention was proven
on: Барахтин А.В., Бессонов С.Н.). Run the usual pipeline
(`inventory_sources.py` -> `scan_sources.py` -> `extract_registry.py`) to
assign real `sNNNN` ids to the new files, then
`scripts/wire_upr_uchr_sources.py` to match each archived file back to its
person by filename and stamp `source_id` onto their `other_entities[]`
entries.

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

**2026-09-14: interactive captcha solving added (`--solve-captcha`).**
Reverse-engineered from a user-supplied HAR capture of pb.nalog.ru's own
captcha-dialog flow (no login/cookies involved — every step is a plain,
stateless GET/POST keyed only by an explicit token value):

  1. GET  /captcha-dialog.html            -> HTML with a hidden
     `<input name="captchaToken" value="...">` — a fresh token, freshly
     generated server-side on every load, not tied to the request that
     originally triggered the wall.
  2. GET  /static/captcha.bin?a=<token>&version=4  -> a small JPEG (200x100,
     6 distorted digits) keyed by that same token.
  3. POST /captcha-proc.json  captcha=<the 6 digits>&captchaToken=<token>
     -> a JSON-encoded string, e.g. "5A4C05DC..." — call this pbCaptchaToken.
  4. Retry the ORIGINAL blocked request with `pbCaptchaToken=<that value>`
     added to its POST body (alongside its normal fields) — this is the
     `['mode','page','pageSize','token','pbCaptchaToken']` field pb's own
     `pb-search-form.js` already special-cases.

With `--solve-captcha`, `post()` catches both captcha signals (an HTTP 400
with `pbSearchCaptcha` in the body, and a 200 response with
`captchaRequired: true`) and pauses: it saves the image locally and prompts
for the digits on stdin, submits them, and retries the original call with
`pbCaptchaToken` attached — transparent to every caller (`search_upr_uchr`/
`search_ul_by_token` don't need to know this happened). Solving one captcha
clears the wall for the request it was attached to, but the wall can
reassert a few requests later (consistent with the count/session-based
gate already documented above) — expect to solve more than one per run.
Without `--solve-captcha` (the default), behavior is unchanged from
before: a captcha hit still raises and the loop skips to the next person,
same as the original "cannot proceed unattended" design.

**2026-09-29: retry loop widened.** A wrong digit guess (easy on pb's
distorted images) comes back as a captcha-flavored 400 that doesn't
literally contain "pbSearchCaptcha" — the original retry check missed
this and gave up on that person instead of re-prompting. Now matches any
case-insensitive "captcha" mention and retries up to `MAX_CAPTCHA_ATTEMPTS`
(8, up from 3) before giving up; every non-retried failure body is also
appended to `$TMPDIR/pb_nalog_debug.log` so a real "not actually captcha"
failure can be diagnosed instead of guessed at from a possibly-truncated
terminal print.

**2026-09-29: request shape matched to a real HAR capture (user-captured
browser session against pb.nalog.ru, not checked into `data/sources/`).**
Two real findings from it, both fixed here:
1. Every `search-proc.json` call in the real UI — including the `search-ul`
   drill-down — submits the SAME ~40-field form (all its unused filters
   included as empty strings), not just the fields actually in use. This
   script was previously sending only the 4-6 fields it needed. A request
   missing most of an expected form's fields is a textbook bot-detection
   signal; this is a plausible real contributor to the wall reasserting so
   aggressively, independent of the count/session-based gate above. Fixed
   via `FULL_FORM_DEFAULTS`, merged into every call.
2. The HAR showed the exact same (digits, captchaToken) pair rejected once
   ("Цифры с картинки введены неверно") and accepted ~8s later on a plain
   resubmission — nothing else changed. So a "wrong digits" response is not
   always a real misread; `solve_captcha_interactively()` now retries the
   identical submission once before concluding the read was wrong and
   burning a fresh image on it. Missing browser headers (`Origin`, full
   `Referer` chain, `Accept`) were also added to every request to match.

Usage:
    python3 scripts/screen_upr_uchr.py                  # everyone with inn_personal
    python3 scripts/screen_upr_uchr.py --slug shatrakova-anastasiya-artemovna
    python3 scripts/screen_upr_uchr.py --force           # re-check even if already checked today
    python3 scripts/screen_upr_uchr.py --solve-captcha   # pause and prompt to solve captchas as they appear
"""
from __future__ import annotations

import argparse
import json
import re
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PEOPLE = REPO / "data" / "registry" / "people.json"
SOURCES_DIR = REPO / "data" / "sources"

BASE_URL = "https://pb.nalog.ru/search-proc.json"
CAPTCHA_DIALOG_URL = "https://pb.nalog.ru/captcha-dialog.html"
CAPTCHA_IMG_URL = "https://pb.nalog.ru/static/captcha.bin"
CAPTCHA_PROC_URL = "https://pb.nalog.ru/captcha-proc.json"
CAPTCHA_IMG_PATH = Path(tempfile.gettempdir()) / "pb_nalog_captcha.jpg"
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")

SOLVE_CAPTCHA = False  # set from --solve-captcha in main()
MAX_CAPTCHA_ATTEMPTS = 8  # per blocked call — a wrong guess retries, doesn't abort.
# Bumped from 3 -> 8 2026-09-29: a misread digit on pb.nalog.ru's distorted
# captcha image is common enough that 3 tries wasn't giving a real user a fair
# shot at getting through the wall in one sitting.
DEBUG_LOG = Path(tempfile.gettempdir()) / "pb_nalog_debug.log"  # raw failing
# response bodies get appended here so a captcha-adjacent 400 that doesn't
# match the retry pattern can actually be diagnosed instead of just printed
# (and possibly truncated by the terminal) and given up on.

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


def _raise_with_detail(e: urllib.error.HTTPError, where: str) -> None:
    """2026-09-29: the captcha-solving sub-requests (dialog page, image,
    digit submission) had NO error handling at all -- a plain HTTPError from
    any of the three crashed straight out of solve_captcha_interactively(),
    skipping post()'s retry logic and its debug-log write entirely, and
    printing as a bare 'HTTP Error 400: ' with nothing after it whenever
    pb.nalog.ru sent an empty reason phrase (which it does under this same
    anti-bot wall, apparently applied to the captcha subsystem itself when
    hit repeatedly back-to-back). Always surface the real body and log it."""
    try:
        detail = e.read().decode("utf-8", errors="replace")
    except Exception:
        detail = ""
    with DEBUG_LOG.open("a", encoding="utf-8") as f:
        f.write(f"\n--- {time.strftime('%H:%M:%S')} {where} HTTP {e.code} ---\n{detail}\n")
    raise RuntimeError(f"{where} failed: HTTP {e.code} -- {detail or '(empty body)'}") from None


def _http_get(url: str, where: str, referer: str = "https://pb.nalog.ru/search.html") -> bytes:
    # 2026-09-29: a real browser always sends Referer/Accept on these GETs
    # (HAR-confirmed, see the FULL_FORM_DEFAULTS comment below) -- a bare
    # User-Agent-only request is itself a plausible bot signal.
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Referer": referer,
        "Accept": "*/*",
    })
    try:
        with urllib.request.urlopen(req, timeout=CONNECT_TIMEOUT) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        _raise_with_detail(e, where)


def solve_captcha_interactively(_attempt: int = 0) -> str:
    """Fetch a fresh pb.nalog.ru captcha, save it locally, prompt on stdin
    for the digits, submit them, and return the resulting pbCaptchaToken to
    attach to the retried request. See the module docstring for the
    HAR-derived flow this drives.

    2026-09-29: the captcha subsystem itself (dialog page / image / digit
    submission) can get rejected under the same anti-bot wall as the main
    search endpoint, especially when solving several in a row -- retries
    with a fresh token up to MAX_CAPTCHA_ATTEMPTS instead of crashing the
    whole person on the first sub-request failure."""
    try:
        html = _http_get(CAPTCHA_DIALOG_URL, "captcha-dialog.html").decode("utf-8", errors="replace")
        m = re.search(r'name="captchaToken"\s+value="([0-9A-Fa-f]+)"', html)
        if not m:
            raise RuntimeError("could not find captchaToken in captcha-dialog.html — page shape may have changed")
        token = m.group(1)

        img_bytes = _http_get(f"{CAPTCHA_IMG_URL}?a={token}&version=4", "captcha.bin",
                               referer=CAPTCHA_DIALOG_URL)
        CAPTCHA_IMG_PATH.write_bytes(img_bytes)

        print(f"\n  >>> CAPTCHA required. Image saved to: {CAPTCHA_IMG_PATH}")
        print(f"      Open it (e.g. `open {CAPTCHA_IMG_PATH}`) and type the digits you see.")
        digits = input("      Digits: ").strip()

        # 2026-09-29: a real HAR capture showed the EXACT SAME (digits, token)
        # pair rejected once ("Цифры с картинки введены неверно") and then
        # accepted ~8s later on a plain resubmission -- no new image, no new
        # token, nothing changed. So a "wrong digits" response isn't always a
        # real misread; it can be transient. Retry the identical submission
        # once before concluding the read was actually wrong and burning a
        # fresh captcha image on it.
        def _submit(d: str, t: str) -> str:
            body = urllib.parse.urlencode({"captcha": d, "captchaToken": t}).encode("ascii")
            req = urllib.request.Request(
                CAPTCHA_PROC_URL, data=body, method="POST",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "X-Requested-With": "XMLHttpRequest",
                    "User-Agent": USER_AGENT,
                    "Origin": "https://pb.nalog.ru",
                    "Referer": CAPTCHA_DIALOG_URL,
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                },
            )
            try:
                with urllib.request.urlopen(req, timeout=CONNECT_TIMEOUT) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                _raise_with_detail(e, "captcha-proc.json")

        try:
            result = _submit(digits, token)
        except RuntimeError as e:
            if "captcha" in str(e).lower():
                print(f"      ({e} -- retrying the identical submission once, same image/digits, "
                      f"before assuming it was really misread)")
                time.sleep(2.0)
                result = _submit(digits, token)
            else:
                raise
        if not isinstance(result, str) or not result:
            raise RuntimeError(f"unexpected captcha-proc.json response: {result!r}")
        return result
    except (urllib.error.URLError, RuntimeError) as e:
        if _attempt < MAX_CAPTCHA_ATTEMPTS:
            print(f"      (captcha subsystem itself rejected this attempt: {e} -- fetching a fresh captcha, "
                  f"attempt {_attempt + 2}/{MAX_CAPTCHA_ATTEMPTS + 1})")
            time.sleep(3.0)
            return solve_captcha_interactively(_attempt + 1)
        raise


def post(data: dict, _captcha_attempts: int = 0) -> dict:
    body = urllib.parse.urlencode(data).encode("ascii")
    req = urllib.request.Request(
        BASE_URL, data=body, method="POST",
        headers={
            # 2026-09-29: matched to a real HAR-captured browser request
            # (charset suffix, Origin, Referer, Accept) -- see the
            # FULL_FORM_DEFAULTS comment for why this matters as much as the
            # field-shape fix.
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": USER_AGENT,
            "Origin": "https://pb.nalog.ru",
            "Referer": "https://pb.nalog.ru/search.html",
            "Accept": "application/json, text/javascript, */*; q=0.01",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=CONNECT_TIMEOUT) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # See screen_disqualified.py's identical fix (2026-09-06): pb.nalog.ru
        # returns a 400 with a JSON body explaining why (captcha wall, bad
        # field, etc) -- surface that instead of urllib's bare "HTTP Error
        # 400: Bad Request".
        try:
            detail = e.read().decode("utf-8", errors="replace")
        except Exception:
            detail = ""
        # 2026-09-29: matched literal "pbSearchCaptcha" only -- but a wrong
        # digit guess on the captcha we just solved comes back as a 400 with
        # a DIFFERENT-shaped body (still captcha-related, just not that exact
        # string), so the old check let it fall straight through to the
        # raise below instead of prompting again. Widened to any mention of
        # "captcha" case-insensitively.
        if SOLVE_CAPTCHA and "captcha" in detail.lower() and _captcha_attempts < MAX_CAPTCHA_ATTEMPTS:
            print(f"      (captcha-related 400, attempt {_captcha_attempts + 1}/{MAX_CAPTCHA_ATTEMPTS} -- retrying)")
            pb_captcha_token = solve_captcha_interactively()
            return post({**data, "pbCaptchaToken": pb_captcha_token}, _captcha_attempts + 1)
        with DEBUG_LOG.open("a", encoding="utf-8") as f:
            f.write(f"\n--- {time.strftime('%H:%M:%S')} HTTP {e.code} ---\n{detail}\n")
        raise urllib.error.HTTPError(e.url, e.code, f"{e.reason} -- {detail}", e.headers, None) from None

    if isinstance(result, dict) and result.get("captchaRequired") and SOLVE_CAPTCHA and _captcha_attempts < MAX_CAPTCHA_ATTEMPTS:
        print(f"      (captchaRequired in 200 response, attempt {_captcha_attempts + 1}/{MAX_CAPTCHA_ATTEMPTS} -- retrying)")
        pb_captcha_token = solve_captcha_interactively()
        return post({**data, "pbCaptchaToken": pb_captcha_token}, _captcha_attempts + 1)

    return result


def poll(request_id: str) -> dict:
    for attempt in range(1, POLL_MAX_TRIES + 1):
        time.sleep(POLL_DELAY)
        print(f"    poll {attempt}/{POLL_MAX_TRIES} ...", end=" ", flush=True)
        result = post({"id": request_id, "method": "get-response"})
        print("got data" if result is not None else "not ready")
        if result is not None:
            return result
    raise TimeoutError(f"search-proc.json never resolved id={request_id}")


# 2026-09-29: HAR-captured from a real browser session against pb.nalog.ru
# (data/sources not checked in -- captured to /Users/ak/Downloads/pb.nalog.ru1.har,
# see notes/script_notes or ask -- for the raw entries). The real UI form always
# submits this FULL ~40-field set, all its unused filters included as empty
# strings, on every single search-proc.json call -- our script was sending only
# the 4-6 fields it actually used. A request missing dozens of expected fields
# is a textbook bot-detection signal; this is very likely a real contributor to
# how aggressively the captcha wall was reasserting for scripted traffic
# (independent of the count/session-based gate already documented above -- both
# can be true at once). Every request now carries the identical field set the
# browser does, with only the fields that vary actually overridden per call.
FULL_FORM_DEFAULTS = {
    "queryAll": "", "queryUl": "", "okvedUl": "", "okvedTypeUl": "", "regionUl": "",
    "statusUl": "", "isMspUl": "", "mspUl1": "1", "mspUl2": "1", "mspUl3": "1",
    "queryIp": "", "okvedIp": "", "okvedTypeIp": "", "regionIp": "", "statusIp": "",
    "isMspIp": "", "mspIp1": "1", "mspIp2": "1", "mspIp3": "1", "taxIp": "",
    "queryUpr": "", "uprType1": "1", "uprType0": "1", "queryRdl": "", "dateRdl": "",
    "queryAddr": "", "regionAddr": "", "queryOgr": "", "ogrFl": "1", "ogrUl": "1",
    "ogrnUlDoc": "", "ogrnIpDoc": "", "npTypeDoc": "1", "nameUlDoc": "", "nameIpDoc": "",
    "formUlDoc": "", "formIpDoc": "", "ifnsDoc": "", "dateFromDoc": "", "dateToDoc": "",
    "page": "1", "pageSize": "10", "pbCaptchaToken": "", "token": "",
}


def search_upr_uchr(inn: str) -> dict:
    ack = post({**FULL_FORM_DEFAULTS, "mode": "search-upr-uchr", "queryUpr": inn})
    if ack.get("captchaRequired"):
        raise RuntimeError("captcha required on search-upr-uchr — cannot proceed unattended")
    return poll(ack["id"])


def search_ul_by_token(token: str, query_name: str, inn: str) -> list[dict]:
    # The real form keeps queryUpr populated on the drill-down call too (the
    # search box state persists across the two-stage flow in the browser) --
    # matching that here, not just the card token + query name.
    ack = post({**FULL_FORM_DEFAULTS, "mode": "search-ul", "token": token,
                "queryUl": query_name, "queryUpr": inn})
    if ack.get("captchaRequired"):
        raise RuntimeError("captcha required on search-ul drill-down — cannot proceed unattended")
    result = poll(ack["id"])
    return (result.get("ul") or {}).get("data") or []


def main() -> None:
    global SOLVE_CAPTCHA
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", default=None)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--solve-captcha", action="store_true",
                     help="pause and prompt on stdin to solve pb.nalog.ru captchas as they appear, "
                          "instead of skipping the person on a captcha hit")
    ap.add_argument("--limit", type=int, default=None,
                     help="stop after this many people this run, so a --solve-captcha session can be "
                          "sized to how many captchas you're willing to solve in one sitting")
    args = ap.parse_args()
    SOLVE_CAPTCHA = args.solve_captcha

    people = json.loads(PEOPLE.read_text(encoding="utf-8"))
    today = date.today().isoformat()

    targets = [p for p in people if p.get("inn_personal")]
    if args.slug:
        targets = [p for p in targets if p["slug"] == args.slug]
    if not args.force:
        targets = [p for p in targets if p.get("other_entities_checked_at") != today]
    if args.limit is not None:
        targets = targets[:args.limit]

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
        raw_by_role = {"upr": [], "uchr": []}
        drilldown_failed = False
        for role_key, role_label in (("upr", "director"), ("uchr", "founder")):
            cards = (summary.get(role_key) or {}).get("data") or []
            for card in cards:
                token = card.get("token")
                query_name = card.get("name", "")
                if not token:
                    continue
                try:
                    rows = search_ul_by_token(token, query_name, inn)
                except (urllib.error.URLError, RuntimeError, TimeoutError) as e:
                    print(f"  {i}/{len(targets)}  {label}  ERROR at drill-down ({role_label}): {e}")
                    drilldown_failed = True
                    continue
                raw_by_role[role_key].extend(rows)
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

        if drilldown_failed and not found:
            # BUG FIXED 2026-09-07: a captcha wall firing mid-run used to hit
            # here silently -- every card's drill-down would error, `found`
            # stayed [], and the code below unconditionally overwrote
            # other_entities with that empty list, erasing any real hits an
            # earlier successful run had recorded (found live 2026-09-07:
            # Ташматов И.С., Тимофеев В.С., Кусумов В.А. all silently lost
            # real other_entities this way). A card-drill-down failure now
            # aborts this person's write entirely -- leave their prior
            # other_entities/checked_at untouched and retry them on a later
            # run instead of recording a false "0 hits."
            print(f"  {i}/{len(targets)}  {label}  ALL drill-downs failed (captcha wall?) -- "
                  f"leaving prior other_entities untouched, not overwriting with a false empty result")
            time.sleep(DELAY_BETWEEN_PEOPLE)
            continue
        if drilldown_failed:
            # BUG FOUND 2026-09-07 (2nd instance, same run that verified the
            # all-failed fix above): a PARTIAL failure -- some cards drilled
            # down fine, others errored -- still silently regressed a person
            # (Закелов А.А. 3 hits -> 2, lost his "director @ Архангел-Центр"
            # card while "founder @ Архангел-Центр" and a new АЛЬФАМЕД hit
            # both came through fine) because `found` only ever holds THIS
            # run's successful cards, discarding whatever the failed card had
            # previously resolved to. Merge this run's successes into the
            # prior list instead of replacing it outright, so a failed card
            # falls back to its last-known value rather than vanishing.
            prior = {(e.get("inn"), e.get("role")): e for e in (person.get("other_entities") or [])}
            this_run = {(e.get("inn"), e.get("role")): e for e in found}
            merged = {**prior, **this_run}
            found = list(merged.values())
            print(f"  {i}/{len(targets)}  {label}  WARNING: partial result -- some card drill-downs "
                  f"failed, merged with prior other_entities so nothing already-found is lost")

        # Archive the raw upr/uchr rows this run actually saw (source
        # evidence, not just the flattened `found` summary) -- this used to
        # be lost entirely: other_entities[] carried a fetched claim with no
        # source_id, and no raw file backed it. inventory_sources.py ->
        # scan_sources.py -> extract_registry.py assigns this a real sNNNN
        # id on the next pipeline run; nothing here can know that id yet.
        raw_path = None
        if raw_by_role["upr"] or raw_by_role["uchr"]:
            SOURCES_DIR.mkdir(parents=True, exist_ok=True)
            raw_path = SOURCES_DIR / f"FNS_PB_UPR_UCHR_{inn}_{today.replace('-', '')}_{person['slug']}-raw.json"
            raw_path.write_text(
                json.dumps(raw_by_role, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )

        person["other_entities"] = found
        person["other_entities_checked_at"] = today
        PEOPLE.write_text(json.dumps(people, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        new_inns = {f["inn"] for f in found}
        archived_note = f", archived to {raw_path.name}" if raw_path else ""
        print(f"  {i}/{len(targets)}  {label}  {len(found)} entit(y/ies) found: {', '.join(sorted(new_inns)) or '-'}{archived_note}")
        time.sleep(DELAY_BETWEEN_PEOPLE)

    print("\nDone. Cross-check each ИНН against data/registry/entities.json — anything new is a lead, "
          "not a confirmed link, per the usual verify-before-use discipline.")


if __name__ == "__main__":
    main()
