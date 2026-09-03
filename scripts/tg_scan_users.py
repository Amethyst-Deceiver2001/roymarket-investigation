#!/usr/bin/env python3
"""Catalog the member roster of a forum/chat in config/channels.txt:
username, exposed phone (account field or bio text), bio, and profile-photo
count — into tg_users. Companion to tg_scan.py's post-history scrape;
separate because "which posts exist" and "who's actually in this chat" are
different Telegram API calls with different costs, same decoupling reason
tg_scan.py/mine_leads.py are split.

This is a LIVE NETWORK JOB against a third-party service (Telegram) — one
GetFullUserRequest + one profile-photo listing per member — per CLAUDE.md's
crawling-jobs policy, Claude should hand the exact command to run to the
user rather than executing this directly/in the background.

Usage:
    python3 scripts/tg_scan_users.py --only Archangel_Forum
    python3 scripts/tg_scan_users.py --only +7GbNlS1SJI83ZmQy
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tg import client as tg_client  # noqa: E402
from tg import db, scraper  # noqa: E402
from scripts.tg_scan import _load_channels  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", type=str, required=True,
                     help="comma-separated channel handles/invite refs to scan (must be in config/channels.txt)")
    args = ap.parse_args()

    only = [h.strip() for h in args.only.split(",")]
    channels = _load_channels(only)
    if not channels:
        print("No channels matched — check config/channels.txt.")
        return

    conn = db.connect()
    client = tg_client.make_client()
    with client:
        for ref in channels:
            try:
                entity = scraper.resolve_channel(client, ref)
            except Exception as exc:  # noqa: BLE001
                print(f"cannot resolve {ref}: {exc}")
                continue

            print(f"scanning participants of {ref} (id {entity.id})...")
            n = 0
            phone_exposed = 0
            multi_photo = 0
            for user in scraper.iter_participants(client, entity):
                db.upsert_user(conn, user)
                n += 1
                if user.get("phone") or user.get("bio_phone"):
                    phone_exposed += 1
                    tag = f"@{user['username']}" if user.get("username") else str(user["id"])
                    print(f"  phone exposed: {tag} — {user.get('phone') or user.get('bio_phone')}")
                if (user.get("profile_photo_count") or 0) > 1:
                    multi_photo += 1
                if n % 50 == 0:
                    conn.commit()
                    print(f"  ...{n} members scanned")
            conn.commit()
            print(f"{ref}: {n} members, {phone_exposed} with an exposed phone, "
                  f"{multi_photo} with 2+ profile photos (candidates for identifiable-feature review)")

    print("done")


if __name__ == "__main__":
    main()
