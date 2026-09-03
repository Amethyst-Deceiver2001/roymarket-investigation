#!/usr/bin/env python3
"""Scrape config/channels.txt into data/roymarket.db.

This is a LIVE NETWORK JOB against a third-party service (Telegram) — per
CLAUDE.md's crawling-jobs policy, Claude should hand the exact command to
run to the user rather than executing this directly/in the background.
Inline reconnaissance (single post lookups) is a different matter and fine
to run directly.

Usage:
    python3 scripts/tg_scan.py                          # incremental, all channels
    python3 scripts/tg_scan.py --full                    # full history (first run)
    python3 scripts/tg_scan.py --full --days 1500         # extend past the 730-day default
    python3 scripts/tg_scan.py --only projectArchangel    # just one channel
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tg import client as tg_client  # noqa: E402
from tg import db, scraper  # noqa: E402


def _normalize_ref(ref: str) -> str:
    """Reduce a channel reference to a bare handle/invite-hash for matching
    --only against config/channels.txt regardless of which form either side
    is written in (@handle, t.me/handle, a full https://t.me/+HASH invite
    link, or just the bare hash). Without this, --only +HASH silently
    matched nothing against a channels.txt line stored as a full URL —
    tg_scan.py would report success while quietly skipping that channel."""
    ref = ref.strip()
    if ref.startswith("https://") or ref.startswith("http://"):
        ref = ref.split("://", 1)[1]
    if ref.startswith("t.me/"):
        ref = ref.split("t.me/", 1)[1]
    if ref.startswith("joinchat/"):
        ref = ref.split("joinchat/", 1)[1]
    return ref.lstrip("@+").lower()


def _load_channels(only: list[str] | None) -> list[str]:
    from tg import config
    if not config.CHANNELS_FILE.exists():
        return []
    lines = config.CHANNELS_FILE.read_text(encoding="utf-8").splitlines()
    channels = [ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")]
    if only:
        wanted = {_normalize_ref(ref) for ref in only}
        channels = [c for c in channels if _normalize_ref(c) in wanted]
    return channels


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true", help="pull full history (first run)")
    ap.add_argument("--days", type=int, default=scraper.DEFAULT_LOOKBACK_DAYS,
                     help=f"with --full, stop this many days back (default {scraper.DEFAULT_LOOKBACK_DAYS} = 2 years — "
                          "pass a larger value for a channel whose real history predates this)")
    ap.add_argument("--only", type=str, default=None,
                     help="comma-separated channel handles to scan (must be in config/channels.txt)")
    args = ap.parse_args()

    only = [h.strip() for h in args.only.split(",")] if args.only else None
    channels = _load_channels(only)
    if not channels:
        print("No channels matched — check config/channels.txt.")
        return

    conn = db.connect()
    cutoff = scraper.lookback_cutoff(args.days) if args.full else None
    totals = {"posts": 0, "channels": 0}

    client = tg_client.make_client()
    with client:
        for ref in channels:
            try:
                entity = scraper.resolve_channel(client, ref)
            except Exception as exc:  # noqa: BLE001
                print(f"cannot resolve {ref}: {exc}")
                continue

            meta = scraper.channel_metadata(client, entity)
            db.upsert_channel(conn, meta)
            min_id = 0 if args.full else db.channel_last_msg_id(conn, entity.id)
            print(
                f"channel {meta.get('title') or ref} (id {entity.id}) from msg_id>{min_id}"
                + (f", back to {cutoff.date()}" if cutoff else "")
            )

            max_seen = min_id
            n = 0
            for post in scraper.iter_posts(client, entity, min_id=min_id, cutoff_date=cutoff):
                db.add_post(conn, post)
                max_seen = max(max_seen, post["msg_id"])
                n += 1
            db.update_last_msg_id(conn, entity.id, max_seen)
            conn.commit()
            totals["posts"] += n
            totals["channels"] += 1

    print(f"tg-scan: {totals['posts']} posts across {totals['channels']} channel(s)")


if __name__ == "__main__":
    main()
