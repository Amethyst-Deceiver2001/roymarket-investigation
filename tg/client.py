"""Telethon client bootstrap using a persisted StringSession.

Own session, independent of wb_watch's — see CLAUDE.md. Same pattern as
wb_watch/wb_watch/tg/client.py (deliberately — no reason to reinvent a
working auth flow), just pointed at this repo's own .env/config.
"""
from __future__ import annotations

import telethon.sync  # noqa: F401 — patches TelegramClient for sync calls
from telethon import TelegramClient
from telethon.sessions import StringSession

from . import config


def _require_creds() -> tuple[int, str]:
    if not config.TG_API_ID or not config.TG_API_HASH:
        raise RuntimeError(
            "TG_API_ID / TG_API_HASH not set. Add them to .env "
            "(get them from https://my.telegram.org — a fresh app registration "
            "is fine, doesn't need to match wb_watch's)."
        )
    return int(config.TG_API_ID), config.TG_API_HASH


def make_client() -> TelegramClient:
    """Client for non-interactive runs; requires TG_SESSION in .env."""
    api_id, api_hash = _require_creds()
    if not config.TG_SESSION:
        raise RuntimeError(
            "TG_SESSION not set. Run `python3 scripts/tg_login.py` once and "
            "paste the printed session string into .env as TG_SESSION."
        )
    return TelegramClient(StringSession(config.TG_SESSION), api_id, api_hash)


def login() -> str:
    """Interactive one-time auth. Returns the StringSession to store in .env."""
    api_id, api_hash = _require_creds()
    with TelegramClient(StringSession(), api_id, api_hash) as client:
        client.start()  # prompts for phone + code (+ 2FA) on the console
        return client.session.save()
