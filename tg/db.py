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
    fwd_date        TEXT,
    media_type      TEXT,
    media_json      TEXT,
    sender_id       INTEGER
);
CREATE INDEX IF NOT EXISTS idx_posts_channel ON tg_posts(channel_id, msg_id);

CREATE TABLE IF NOT EXISTS tg_users (
    id                   INTEGER PRIMARY KEY,
    username             TEXT,
    first_name           TEXT,
    last_name            TEXT,
    phone                TEXT,
    bio                  TEXT,
    bio_phone            TEXT,
    is_bot               INTEGER,
    is_verified          INTEGER,
    is_scam              INTEGER,
    is_fake              INTEGER,
    is_premium           INTEGER,
    profile_photo_count  INTEGER,
    profile_photo_ids    TEXT,
    seen_in_channel_id   INTEGER,
    first_seen           TEXT,
    last_seen            TEXT
);
CREATE INDEX IF NOT EXISTS idx_users_username ON tg_users(username);
"""

# media_type/media_json/sender_id and the whole tg_users table were added
# after the original schema shipped — ALTER TABLE is needed for any
# pre-existing data/roymarket.db, since CREATE TABLE IF NOT EXISTS is a
# no-op on a table that already exists without them.
_POST_COLUMNS = ("media_type", "media_json", "sender_id")


def _ensure_post_columns(conn: sqlite3.Connection) -> None:
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(tg_posts)")}
    for col in _POST_COLUMNS:
        if col not in existing:
            coltype = "INTEGER" if col == "sender_id" else "TEXT"
            conn.execute(f"ALTER TABLE tg_posts ADD COLUMN {col} {coltype}")


def connect() -> sqlite3.Connection:
    Path(config.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    # Column migration must run before any index referencing a migrated
    # column — CREATE TABLE IF NOT EXISTS above is a no-op on a pre-existing
    # tg_posts, so an index on sender_id in SCHEMA itself would fail on a
    # database that predates that column (caught when tested against the
    # real 186k-row data/roymarket.db, which had no sender_id column yet).
    _ensure_post_columns(conn)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_posts_sender ON tg_posts(sender_id)")
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
             fwd_channel_username, fwd_channel_title, fwd_msg_id, fwd_date,
             media_type, media_json, sender_id
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(id) DO UPDATE SET
             text=excluded.text, views=excluded.views, forwards=excluded.forwards,
             links=excluded.links, edited_date=excluded.edited_date,
             media_type=excluded.media_type, media_json=excluded.media_json,
             sender_id=excluded.sender_id""",
        (
            post_id, post["channel_id"], post["msg_id"], post["date"], post["text"],
            post.get("views"), post.get("forwards"), post.get("links"),
            post.get("edited_date"), int(post.get("is_forward", False)),
            post.get("fwd_channel_id"), post.get("fwd_channel_username"),
            post.get("fwd_channel_title"), post.get("fwd_msg_id"), post.get("fwd_date"),
            post.get("media_type"), post.get("media_json"), post.get("sender_id"),
        ),
    )


def update_last_msg_id(conn: sqlite3.Connection, channel_id: int, msg_id: int) -> None:
    conn.execute("UPDATE tg_channels SET last_msg_id=? WHERE id=?", (msg_id, channel_id))


def upsert_user(conn: sqlite3.Connection, user: dict[str, Any]) -> None:
    """Store/refresh a per-user profile record — username, exposed phone
    (from the account's phone field where privacy settings allow it, or a
    phone number written into the freeform bio text), bio, and profile-photo
    count/ids (catalog only — actual download of a specific photo for
    identifiable-feature review is a human-curated follow-up, same division
    of labor as scripts/tg_media_pull.py's candidates/fetch split)."""
    conn.execute(
        """INSERT INTO tg_users (
             id, username, first_name, last_name, phone, bio, bio_phone,
             is_bot, is_verified, is_scam, is_fake, is_premium,
             profile_photo_count, profile_photo_ids, seen_in_channel_id,
             first_seen, last_seen
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
           ON CONFLICT(id) DO UPDATE SET
             username=excluded.username, first_name=excluded.first_name,
             last_name=excluded.last_name, phone=excluded.phone, bio=excluded.bio,
             bio_phone=excluded.bio_phone, is_bot=excluded.is_bot,
             is_verified=excluded.is_verified, is_scam=excluded.is_scam,
             is_fake=excluded.is_fake, is_premium=excluded.is_premium,
             profile_photo_count=excluded.profile_photo_count,
             profile_photo_ids=excluded.profile_photo_ids,
             seen_in_channel_id=excluded.seen_in_channel_id,
             last_seen=datetime('now')""",
        (
            user["id"], user.get("username"), user.get("first_name"), user.get("last_name"),
            user.get("phone"), user.get("bio"), user.get("bio_phone"),
            int(user.get("is_bot", False)), int(user.get("is_verified", False)),
            int(user.get("is_scam", False)), int(user.get("is_fake", False)),
            int(user.get("is_premium", False)), user.get("profile_photo_count"),
            user.get("profile_photo_ids"), user.get("seen_in_channel_id"),
        ),
    )
