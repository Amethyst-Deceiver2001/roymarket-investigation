#!/usr/bin/env python3
"""Enrich each ИП hit from scripts/screen_egrip_ip.py's log with detail
rusprofile.ru's public page exposes that egrul.nalog.ru's basic search does
not: active/liquidated status, main OKVED code, region, and — where present —
a summary of any zakupki.gov.ru government contracts won under that ИП.

This is a LIVE NETWORK JOB against a third-party site (rusprofile.ru) — per
CLAUDE.md's crawling-jobs policy, the full batch (66 ОГРНИП as of the
2026-09-04 scan) must be handed to the user as an exact command, never run
directly or in the background. A handful of single-ОГРНИП lookups (--ogrnip)
is ordinary inline reconnaissance and fine to run directly — tested inline
on 3 before this script existed (Безруков 315519000001043, Барашков's two:
313251103800105 and 305251108300364).

Usage:
    python3 scripts/enrich_egrip_hits.py --ogrnip 315519000001043
    python3 scripts/enrich_egrip_hits.py --limit 5
    python3 scripts/enrich_egrip_hits.py                # full batch (hand to user)
"""
import argparse
import json
import re
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCAN_LOG_PATH = REPO / "data" / "registry" / "_egrip_scan_log.json"
ENRICH_PATH = REPO / "data" / "registry" / "_egrip_enrichment.json"
SLEEP_SEC = 2.0


def fetch_rusprofile(ogrnip: str) -> str:
    req = urllib.request.Request(
        f"https://www.rusprofile.ru/ip/{ogrnip}",
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="ignore")


_TITLE_RE = re.compile(r"<title>([^<]*)</title>")
_ACTIVE_RE = re.compile(r'"active":"(yes|no)"')
_OKVED_RE = re.compile(r'"okved":"([^"]*)"')
_REGDATE_RE = re.compile(r"Дата регистрации\s*</[^>]+>\s*([\d.]{10})")
_REGDATE_PLAIN_RE = re.compile(r"Дата регистрации\D{0,40}?(\d{2}\.\d{2}\.\d{4})")
_PROCUREMENT_RE = re.compile(
    r"Статус закупки(.{0,600}?)Категории закупок", re.S
)


def _strip_tags(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text)


def parse_rusprofile(html: str) -> dict:
    title_m = _TITLE_RE.search(html)
    active_m = _ACTIVE_RE.search(html)
    okved_m = _OKVED_RE.search(html)
    text = _strip_tags(html)
    regdate_m = _REGDATE_PLAIN_RE.search(text)
    proc_m = _PROCUREMENT_RE.search(text)
    return {
        "title": title_m.group(1).strip() if title_m else None,
        "active": active_m.group(1) if active_m else None,
        "okved_main": okved_m.group(1) if okved_m and okved_m.group(1) != "0" else None,
        "registration_date": regdate_m.group(1) if regdate_m else None,
        "procurement_summary": re.sub(r"\s+", " ", proc_m.group(1)).strip() if proc_m else None,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ogrnip", type=str, default=None, help="single ОГРНИП (inline reconnaissance)")
    ap.add_argument("--limit", type=int, default=None, help="cap the batch (for a smoke-test)")
    args = ap.parse_args()

    scan_log = json.loads(SCAN_LOG_PATH.read_text(encoding="utf-8"))
    ogrnip_to_slug: dict[str, str] = {}
    for slug, rec in scan_log.items():
        for hit in rec.get("hits", []):
            ogrnip_to_slug[hit["ogrnip"]] = slug

    targets = list(ogrnip_to_slug.keys())
    if args.ogrnip:
        targets = [args.ogrnip]
    elif args.limit:
        targets = targets[: args.limit]

    enrich = json.loads(ENRICH_PATH.read_text(encoding="utf-8")) if ENRICH_PATH.exists() else {}
    for i, ogrnip in enumerate(targets, 1):
        if ogrnip in enrich and not args.ogrnip:
            continue
        try:
            html = fetch_rusprofile(ogrnip)
            info = parse_rusprofile(html)
        except Exception as exc:  # noqa: BLE001
            print(f"[{i}/{len(targets)}] {ogrnip}: ERROR {exc}")
            time.sleep(SLEEP_SEC)
            continue
        enrich[ogrnip] = info
        slug = ogrnip_to_slug.get(ogrnip, "?")
        flag = " [PROCUREMENT]" if info["procurement_summary"] else ""
        print(f"[{i}/{len(targets)}] {slug} / {ogrnip}: active={info['active']} "
              f"okved={info['okved_main']}{flag}")
        time.sleep(SLEEP_SEC)

    ENRICH_PATH.write_text(json.dumps(enrich, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nenriched {len(targets)} ОГРНИП, written to {ENRICH_PATH}")


if __name__ == "__main__":
    main()
