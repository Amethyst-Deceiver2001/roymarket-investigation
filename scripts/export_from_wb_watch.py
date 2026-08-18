#!/usr/bin/env python3
"""Regenerate data/roymarket.db from wb_watch's data/wb_watch.db.

Data collection (Telegram scraping via wb-watch tg-scan) still happens in the
wb_watch repo — see HANDOFF.md for why. Run this after any new tg-scan pull
that touches one of the channels below, then commit nothing (the .db itself
is gitignored — it's a local working copy, not source of truth; the source
of truth is wb_watch's own data/wb_watch.db).
"""
import sqlite3
import sys
from pathlib import Path

WB_WATCH_DB = Path.home() / "Downloads" / "wb_watch" / "data" / "wb_watch.db"
OUT_DB = Path(__file__).resolve().parent.parent / "data" / "roymarket.db"

# Channel IDs specific to the ЦБСТ/РОЙ.МАРКЕТ investigation. Add new ones
# here as new channels get scanned in wb_watch for this investigation.
CHANNEL_IDS = [
    1905141464,  # nashapravdafond — Фонд "Наша Правда"
    2159491523,  # ANO_CBST — ЦБСТ
    1360364343,  # evgeniy_lisitsyn — Военкор Z Лисицын ZOV-TV
    1787192065,  # dronnitsa — ДРОННИЦА
    1746605280,  # chadayevru — ЧАДАЕВ
    1737759730,  # mil_hub — Military hub
    2347755482,  # potapov_npp — Потапов. АО «НПП».
    1903515928,  # UAS_development — НПЦ БАСиРТК
    2522149131,  # tsg_group71 — TSG Group
    2651871820,  # nponebo — НПО "НЕБО"
    1711795532,  # projectArchangel — Проект «Архангел» (adjacent-network, see memory)
]


def main() -> None:
    if not WB_WATCH_DB.exists():
        sys.exit(f"wb_watch DB not found at {WB_WATCH_DB} — adjust the path at the top of this script.")

    src = sqlite3.connect(WB_WATCH_DB)
    src.row_factory = sqlite3.Row
    OUT_DB.parent.mkdir(parents=True, exist_ok=True)
    OUT_DB.unlink(missing_ok=True)
    dst = sqlite3.connect(OUT_DB)

    placeholders = ",".join("?" * len(CHANNEL_IDS))

    dst.execute("""CREATE TABLE tg_channels (
        id INTEGER PRIMARY KEY, username TEXT, title TEXT, about TEXT,
        participants INTEGER, first_scraped TEXT, last_scraped TEXT, last_msg_id INTEGER
    )""")
    dst.execute("""CREATE TABLE tg_posts (
        id TEXT PRIMARY KEY, channel_id INTEGER, msg_id INTEGER, date TEXT, text TEXT,
        views INTEGER, forwards INTEGER, links TEXT, addresses TEXT, phones TEXT,
        payment_details TEXT, edited_date TEXT, first_seen TEXT, wb_links TEXT,
        is_forward INTEGER, fwd_channel_id INTEGER, fwd_channel_username TEXT,
        fwd_channel_title TEXT, fwd_msg_id INTEGER, fwd_date TEXT
    )""")
    dst.execute("CREATE INDEX idx_posts_channel ON tg_posts(channel_id, msg_id)")

    chans = src.execute(f"SELECT * FROM tg_channels WHERE id IN ({placeholders})", CHANNEL_IDS).fetchall()
    for row in chans:
        dst.execute(f"INSERT INTO tg_channels VALUES ({','.join('?' * len(row.keys()))})", tuple(row))

    n = 0
    cur = src.execute(f"SELECT * FROM tg_posts WHERE channel_id IN ({placeholders})", CHANNEL_IDS)
    cols = [d[0] for d in cur.description]
    for row in cur:
        dst.execute(f"INSERT INTO tg_posts VALUES ({','.join('?' * len(cols))})", tuple(row))
        n += 1

    dst.commit()
    print(f"Exported {len(chans)} channels, {n} posts -> {OUT_DB}")


if __name__ == "__main__":
    main()
