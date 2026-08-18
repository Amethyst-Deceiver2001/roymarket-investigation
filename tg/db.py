"""SQLite storage — same schema as the migrated data/roymarket.db (originally
an export of wb_watch's tg_channels/tg_posts) so scripts/mine_leads.py and
anything else built against that shape keep working unchanged. Extra
wb_watch-specific columns (wb_links, payment_details, addresses, phones) are
kept in the schema for compatibility with old rows but always NULL on new
ones written by this scraper — this investigation doesn't do WB-link/
payment-detail matching, see scripts/mine_leads.py for what it does instead.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS tg_channels (
    id              INTEGER PRIMARY KEY,
    username        TEXT,
    title           TEXT,
    about           TEXT,
    participants    INTEGER,
    first_scraped   TEXT,
    last_scraped    TEXT,
    last_msg_id     INTEGER
);
CREATE TABLE IF NOT EXISTS tg_posts (
    id              TEXT PRIMARY KEY,
    channel_id      INTEGER,
    msg_id          INTEGER,
    date            TEXT,
    text            TEXT,
    views           INTEGER,
    forwards        INTEGER,
    links           TEXT,
    addresses       TEXT,
    phones          TEXT,
    payment_details TEXT,
    edited_date     TEXT,
    first_seen      TEXT,
    wb_links        TEXT,
    is_forward      INTEGER,
    fwd_channel_id  INTEGER,
    fwd_channel_username TEXT,
    fwd_channel_title TEXT,
    fwd_msg_id      INTEGER,
    fwd_date        TEXT
);
CREATE INDEX IF NOT EXISTS idx_posts_channel ON tg_posts(channel_id, msg_id);
"""


def connect() -> sqlite3.Connection:
    Path(config.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def upsert_channel(conn: sqlite3.Connection, meta: dict[str, Any]) -> None:
    conn.execute(
        """INSERT INTO tg_channels (id, username, title, about, participants, first_scraped, last_scraped)
           VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
           ON CONFLICT(id) DO UPDATE SET
             username=excluded.username, title=excluded.title, about=excluded.about,
             participants=excluded.participants, last_scraped=datetime('now')""",
        (meta["id"], meta.get("username"), meta.get("title"), meta.get("about"), meta.get("participants")),
    )


def channel_last_msg_id(conn: sqlite3.Connection, channel_id: int) -> int:
    row = conn.execute(
        "SELECT COALESCE(MAX(msg_id), 0) AS m FROM tg_posts WHERE channel_id=?", (channel_id,)
    ).fetchone()
    return row["m"] if row else 0


def add_post(conn: sqlite3.Connection, post: dict[str, Any]) -> None:
    post_id = f"{post['channel_id']}:{post['msg_id']}"
    conn.execute(
        """INSERT INTO tg_posts (
             id, channel_id, msg_id, date, text, views, forwards, links,
             edited_date, first_seen, is_forward, fwd_channel_id,
             fwd_channel_username, fwd_channel_title, fwd_msg_id, fwd_date
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?, ?, ?, ?, ?, ?)
           ON CONFLICT(id) DO UPDATE SET
             text=excluded.text, views=excluded.views, forwards=excluded.forwards,
             links=excluded.links, edited_date=excluded.edited_date""",
        (
            post_id, post["channel_id"], post["msg_id"], post["date"], post["text"],
            post.get("views"), post.get("forwards"), post.get("links"),
            post.get("edited_date"), int(post.get("is_forward", False)),
            post.get("fwd_channel_id"), post.get("fwd_channel_username"),
            post.get("fwd_channel_title"), post.get("fwd_msg_id"), post.get("fwd_date"),
        ),
    )


def update_last_msg_id(conn: sqlite3.Connection, channel_id: int, msg_id: int) -> None:
    conn.execute("UPDATE tg_channels SET last_msg_id=? WHERE id=?", (msg_id, channel_id))
