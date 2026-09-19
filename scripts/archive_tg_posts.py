"""Archive already-scraped Telegram posts from data/roymarket.db as citable
source files under data/sources/.

The scrape DB is the underlying record for many cbst_tie claims, but a DB row
has no sNNNN id, so a claim resting on it could not be cited. This exports one
post to `TGPOST_<YYYYMMDD>_<channel>-<msg_id>-<slug>.txt` (the post's own date, the
project's existing TGPOST_ naming and header format), which
inventory_sources.py / extract_registry.py then register like any other source.

Local read of data/roymarket.db, no network. Usage:
    python3 scripts/archive_tg_posts.py --channel-id 2159491523 --msg-ids 2095,2198
"""
import argparse
import json
import sqlite3
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SOURCES = REPO / "data" / "sources"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel-id", type=int, required=True)
    ap.add_argument("--msg-ids", required=True)
    ap.add_argument("--slug", default="cbst-tie-evidence", help="descriptive filename suffix")
    args = ap.parse_args()
    db = sqlite3.connect(REPO / "data" / "roymarket.db")
    ch = db.execute("select username, title from tg_channels where id=?", (args.channel_id,)).fetchone()
    if not ch:
        raise SystemExit(f"channel {args.channel_id} not in tg_channels")
    for mid in (int(m) for m in args.msg_ids.split(",")):
        r = db.execute("select date, text from tg_posts "
                       "where channel_id=? and msg_id=?", (args.channel_id, mid)).fetchone()
        if not r:
            print(f"msg {mid}: not in DB, skipped")
            continue
        date, text = r
        out = SOURCES / f"TGPOST_{date[:10].replace('-', '')}_{ch[0].lower()}-{mid}-{args.slug}.txt"
        if out.exists():
            print(f"{out.name}: exists, skipped")
            continue
        out.write_text(
            f"t.me/{ch[0].lower()} ({ch[1]} own Telegram channel), channel_id {args.channel_id}, "
            f"msg_id {mid}, {date}.\n\nFull text (Russian, verbatim from local DB, data/roymarket.db):\n\n{text}\n",
            encoding="utf-8")
        print(f"wrote {out.name}")


if __name__ == "__main__":
    main()
