"""Scrape watchlist channels: pull history (first run) or new messages
(incremental). Structurally mirrors wb_watch's tg/scraper.py (same working
Telethon patterns — resolve, iterate newest-first down to a msg_id/date
floor, resolve forward sources) but WITHOUT the WB/Ozon-item-matching
"intel" extraction, which is irrelevant here. Entity/product/person mining
happens separately, over already-stored text, in scripts/mine_leads.py —
keeping scraping (dumb, raw storage) and mining (the actual investigation
logic) decoupled so the mining patterns can be iterated on without
re-scraping anything.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Iterator

from telethon import TelegramClient
from telethon.tl.types import Channel, Chat, MessageEntityTextUrl, PeerChannel

DEFAULT_LOOKBACK_DAYS = 730  # 2 years — same default as wb_watch, same gotcha:
# pass a larger --days explicitly for a channel whose real history predates this.

_URL = re.compile(r"https?://[^\s)>\]]+", re.I)


def resolve_channel(client: TelegramClient, ref: str) -> Any:
    ref = ref.strip()
    if ref.startswith("t.me/"):
        ref = "@" + ref.split("/", 1)[1]
    if ref.lstrip("-").isdigit():
        ref = int(ref)
    return client.get_entity(ref)


def channel_metadata(client: TelegramClient, entity: Any) -> dict[str, Any]:
    full = None
    if isinstance(entity, (Channel, Chat)):
        try:
            from telethon.tl.functions.channels import GetFullChannelRequest
            full = client(GetFullChannelRequest(entity))
        except Exception:
            full = None
    about = None
    participants = None
    if full is not None:
        about = getattr(getattr(full, "full_chat", None), "about", None)
        participants = getattr(getattr(full, "full_chat", None), "participants_count", None)
    return {
        "id": entity.id,
        "username": getattr(entity, "username", None),
        "title": getattr(entity, "title", None),
        "about": about,
        "participants": participants,
    }


def _forward_info(client: TelegramClient, msg: Any) -> dict[str, Any]:
    fwd = getattr(msg, "fwd_from", None)
    if fwd is None:
        return {"is_forward": False, "fwd_channel_id": None, "fwd_channel_username": None,
                "fwd_channel_title": None, "fwd_msg_id": None, "fwd_date": None}

    out: dict[str, Any] = {
        "is_forward": True,
        "fwd_channel_id": None,
        "fwd_channel_username": None,
        "fwd_channel_title": None,
        "fwd_msg_id": getattr(fwd, "channel_post", None),
        "fwd_date": fwd.date.isoformat() if getattr(fwd, "date", None) else None,
    }
    from_id = getattr(fwd, "from_id", None)
    if isinstance(from_id, PeerChannel):
        out["fwd_channel_id"] = from_id.channel_id
        try:
            entity = client.get_entity(from_id)
            out["fwd_channel_username"] = getattr(entity, "username", None)
            out["fwd_channel_title"] = getattr(entity, "title", None)
        except Exception:
            pass
    elif getattr(fwd, "from_name", None):
        out["fwd_channel_title"] = fwd.from_name
    return out


def _hidden_urls(msg: Any) -> list[str]:
    """URLs behind styled link text — invisible in msg.message, only present
    as MessageEntityTextUrl entities. See wb_watch's scraper.py for the
    original discovery of this (fundraising posts hiding WB links this way);
    same mechanism can hide any link, not just marketplace ones."""
    return [
        e.url for e in (getattr(msg, "entities", None) or [])
        if isinstance(e, MessageEntityTextUrl)
    ]


def lookback_cutoff(days: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=days)


def iter_posts(
    client: TelegramClient,
    entity: Any,
    min_id: int = 0,
    limit: int | None = None,
    cutoff_date: datetime | None = None,
) -> Iterator[dict[str, Any]]:
    """Yield posts with msg_id > min_id, newest first."""
    for msg in client.iter_messages(entity, min_id=min_id, limit=limit):
        if cutoff_date is not None and msg.date is not None:
            msg_date = msg.date if msg.date.tzinfo else msg.date.replace(tzinfo=timezone.utc)
            if msg_date < cutoff_date:
                return

        text = msg.message or ""
        hidden = _hidden_urls(msg)
        links = sorted(set(_URL.findall(text)) | set(hidden))
        fwd_info = _forward_info(client, msg)
        yield {
            "channel_id": entity.id,
            "msg_id": msg.id,
            "date": msg.date.isoformat() if msg.date else None,
            "text": text,
            "views": getattr(msg, "views", None),
            "forwards": getattr(msg, "forwards", None),
            "links": json.dumps(links, ensure_ascii=False) if links else None,
            "edited_date": msg.edit_date.isoformat() if msg.edit_date else None,
            **fwd_info,
        }
