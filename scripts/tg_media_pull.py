#!/usr/bin/env python3
"""Pull photo/video-still evidence from already-scraped Telegram posts.

Generalizes the ad-hoc pass done for СКБ «Пиранья» (2026-08-25, @piranhafpv)
into a repeatable two-step pipeline for any company's channel:

  1. `candidates` — LOCAL text scan over data/roymarket.db (already scraped
     by tg_scan.py), scoring each post by UAV/battlefield-language density.
     No network calls; safe to run directly/repeatedly, same as
     mine_leads.py/scan_sources.py — see CLAUDE.md's crawling-jobs policy.

  2. `fetch` — for a human-picked list of msg_ids, fetches each post's public
     t.me/s/<channel>/<id> preview (no auth), extracts any photo/video-thumb
     URLs (grouped-album aware), and downloads them to data/sources/ as
     TGMEDIA_<INN>_<YYYYMMDD>_<channel>-post<id>-<n>.jpg. Also prints a JSON
     scaffold of battlefield_evidence-shaped entries (Russian text verbatim
     from the DB, English left for a human to translate, source_id left as
     TODO until inventory_sources.py/extract_registry.py assign one) ready
     to hand-paste into corrections.json.

     These are single-post lookups (like a one-off WebFetch), which
     CLAUDE.md's crawling-jobs policy already treats as fine to run
     directly — but capped at MAX_FETCH per invocation so a large batch
     doesn't turn into the kind of scripted-loop-at-scale that policy
     reserves for a user-run command (see egrul_batch_pull.py precedent).

Does NOT do a live Telegram scrape itself — that's still tg_scan.py's job,
handed to the user per the crawling-jobs policy. This script only re-fetches
public preview HTML for posts already known to exist in the local DB.

Usage:
  python3 scripts/tg_media_pull.py candidates --channel piranhafpv --top 30
  python3 scripts/tg_media_pull.py fetch --channel piranhafpv --inn 7300024069 \\
      --msg-ids 300,355,360,384 --out /tmp/piranha_battlefield_scaffold.json
"""
import argparse
import json
import re
import sqlite3
import sys
import time
import urllib.request
from pathlib import Path

from id_patterns import uav_score

REPO = Path(__file__).resolve().parent.parent
DB = REPO / "data" / "roymarket.db"
SOURCES_DIR = REPO / "data" / "sources"
UA = "Mozilla/5.0"
MAX_FETCH = 15

BATTLEFIELD_TERMS = [
    "уничтож", "поражен", "поразил", "сбит", "подбит", "ликвидир",
    "боевое применение", "боевых услови", "фронт", "передов", "штурм",
    "передач", "вручен", "благодарствен", "почетн", "почётн", "минобороны",
    "мо рф", "группировк", "направлени", "приграничь", "свои", "заводу",
]


def battlefield_score(text: str) -> int:
    t = (text or "").lower()
    return sum(1 for term in BATTLEFIELD_TERMS if term in t)


def cmd_candidates(args) -> None:
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    # A private/invite-only channel (e.g. the Академия Противодействия БПЛА
    # chat) has no public username in tg_channels — ch.username is "" or
    # NULL, so matching only by username silently returns zero rows for it.
    # Accept a bare numeric channel_id as an alternative --channel value
    # (still local-DB-only, no network call) so `candidates` still works
    # for a private chat even though `fetch` genuinely can't (it needs a
    # public t.me/s/<username>/<id> preview URL, which a private chat has
    # no equivalent of).
    usernames = [ref for ref in args.channel if not ref.isdigit()]
    channel_ids = [int(ref) for ref in args.channel if ref.isdigit()]
    clauses, params = [], []
    if usernames:
        clauses.append(f"ch.username IN ({','.join('?' for _ in usernames)})")
        params.extend(usernames)
    if channel_ids:
        clauses.append(f"ch.id IN ({','.join('?' for _ in channel_ids)})")
        params.extend(channel_ids)
    c.execute(
        f"""SELECT p.channel_id, ch.username, p.msg_id, p.date, p.text
            FROM tg_posts p JOIN tg_channels ch ON ch.id = p.channel_id
            WHERE {' OR '.join(clauses)}""",
        params,
    )
    rows = c.fetchall()
    scored = []
    for channel_id, username, msg_id, date, text in rows:
        s = uav_score(text or "") + battlefield_score(text or "")
        if s >= args.min_score:
            scored.append((s, username, msg_id, date, (text or "").replace("\n", " ")[:180]))
    scored.sort(key=lambda r: -r[0])
    for s, username, msg_id, date, snippet in scored[: args.top]:
        print(f"{s}\t{username}\t{msg_id}\t{date}\t{snippet}")
    print(f"\n{len(scored)} candidates >= score {args.min_score} (of {len(rows)} posts scanned)", file=sys.stderr)


def fetch_post_html(channel: str, msg_id: int) -> str:
    req = urllib.request.Request(f"https://t.me/s/{channel}/{msg_id}", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="replace")


def extract_media_urls(html: str, channel: str, msg_id: int) -> list[str]:
    marker = f'data-post="{channel}/{msg_id}"'
    idx = html.find(marker)
    if idx == -1:
        return []
    end = html.find(f'data-post="{channel}/', idx + len(marker))
    block = html[idx: end if end > 0 else idx + 12000]
    photos = re.findall(r"photo_wrap[^>]*background-image:url\('([^']+)'\)", block)
    vid_thumbs = re.findall(r"video_thumb[^>]*background-image:url\('([^']+)'\)", block)
    # dedupe, preserve order
    seen, out = set(), []
    for u in photos + vid_thumbs:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def cmd_fetch(args) -> None:
    msg_ids = [int(x) for x in args.msg_ids.split(",") if x.strip()]
    if len(msg_ids) > MAX_FETCH:
        print(
            f"Refusing: {len(msg_ids)} posts requested, cap is {MAX_FETCH} per "
            "invocation (single-post lookups are fine directly per CLAUDE.md's "
            "crawling-jobs policy; a bigger batch is scripted-loop-at-scale — "
            "split into multiple runs or hand it to the user).",
            file=sys.stderr,
        )
        sys.exit(1)

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)

    scaffold = []
    for msg_id in msg_ids:
        c.execute(
            """SELECT p.date, p.text FROM tg_posts p JOIN tg_channels ch ON ch.id = p.channel_id
               WHERE ch.username = ? AND p.msg_id = ?""",
            (args.channel, msg_id),
        )
        row = c.fetchone()
        if not row:
            print(f"msg_id {msg_id}: not found in local DB for @{args.channel}, skipping", file=sys.stderr)
            continue
        date, text = row
        yyyymmdd = date[:10].replace("-", "")

        html = fetch_post_html(args.channel, msg_id)
        urls = extract_media_urls(html, args.channel, msg_id)
        if not urls:
            print(f"msg_id {msg_id} ({date}): no photo/video-thumb media found", file=sys.stderr)
            continue

        saved = []
        for i, url in enumerate(urls, start=1):
            ext = "jpg"
            fname = f"TGMEDIA_{args.inn}_{yyyymmdd}_{args.channel}-post{msg_id}-{i}.{ext}"
            dest = SOURCES_DIR / fname
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as resp:
                dest.write_bytes(resp.read())
            saved.append(str(dest.relative_to(REPO)))
            print(f"msg_id {msg_id}: saved {fname}", file=sys.stderr)

        scaffold.append({
            "msg_id": msg_id,
            "date": date,
            "text_ru": text,
            "text_en": "TODO — human translation",
            "context": "TODO — what does the media actually show?",
            "source_id": "TODO — assign after inventory_sources.py + extract_registry.py",
            "as_of": date[:10],
            "media_files": saved,
        })
        time.sleep(0.5)

    out_text = json.dumps(scaffold, ensure_ascii=False, indent=1)
    if args.out:
        Path(args.out).write_text(out_text, encoding="utf-8")
        print(f"\nwrote scaffold for {len(scaffold)} post(s) to {args.out}", file=sys.stderr)
    else:
        print(out_text)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    ap_c = sub.add_parser("candidates", help="local DB scan, no network calls")
    ap_c.add_argument("--channel", nargs="+", required=True,
                       help="channel username(s), no @ — or a numeric channel_id for a "
                            "private/invite-only channel with no public username")
    ap_c.add_argument("--top", type=int, default=40)
    ap_c.add_argument("--min-score", type=int, default=2)
    ap_c.set_defaults(func=cmd_candidates)

    ap_f = sub.add_parser("fetch", help=f"fetch media for up to {MAX_FETCH} posts, single-post-lookup network calls")
    ap_f.add_argument("--channel", required=True, help="channel username, no @")
    ap_f.add_argument("--inn", required=True, help="entity ИНН, used in the saved filename")
    ap_f.add_argument("--msg-ids", required=True, help="comma-separated msg_id list")
    ap_f.add_argument("--out", type=Path, default=None, help="write JSON scaffold here instead of stdout")
    ap_f.set_defaults(func=cmd_fetch)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
