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
from telethon.tl.types import (
    Channel,
    Chat,
    ChatInviteAlready,
    ChatInvitePeek,
    DocumentAttributeFilename,
    MessageEntityTextUrl,
    MessageMediaDocument,
    MessageMediaPhoto,
    PeerChannel,
)

DEFAULT_LOOKBACK_DAYS = 730  # 2 years — same default as wb_watch, same gotcha:
# pass a larger --days explicitly for a channel whose real history predates this.

_URL = re.compile(r"https?://[^\s)>\]]+", re.I)


def resolve_channel(client: TelegramClient, ref: str) -> Any:
    ref = ref.strip()
    if ref.startswith("https://") or ref.startswith("http://"):
        ref = ref.split("://", 1)[1]
    # Private/members-only chats have no username — only a t.me/+HASH (or the
    # older /joinchat/HASH) invite link. get_entity() can't resolve those
    # directly; CheckChatInviteRequest is the only way in, and for a chat
    # we're already a member of it comes back as ChatInviteAlready/Peek
    # (not an error) carrying the actual chat object to resolve from.
    if ref.startswith("t.me/+") or "t.me/joinchat/" in ref:
        invite_hash = ref.rsplit("/", 1)[-1].lstrip("+")
        from telethon.tl.functions.messages import CheckChatInviteRequest
        invite = client(CheckChatInviteRequest(invite_hash))
        if isinstance(invite, (ChatInviteAlready, ChatInvitePeek)):
            return client.get_entity(invite.chat)
        raise RuntimeError(f"not a member of invite {ref} — join it first, then re-run")
    if ref.startswith("t.me/"):
        ref = "@" + ref.split("/", 1)[1]
    if ref.lstrip("-").isdigit():
        ref = int(ref)
    return client.get_entity(ref)


def _media_info(msg: Any) -> tuple[str | None, str | None]:
    """Catalog (don't download) any photo/video/document attached to a post:
    type, mime, size, filename where present. Actual file retrieval for a
    specific post stays a human-curated follow-up (scripts/tg_media_pull.py's
    pattern), not something a full-history scan does automatically — that
    would mean downloading every image/video a forum has ever posted."""
    media = getattr(msg, "media", None)
    if media is None:
        return None, None
    if isinstance(media, MessageMediaPhoto):
        photo = media.photo
        sizes = getattr(photo, "sizes", None) or []
        largest = max((getattr(s, "size", 0) for s in sizes if hasattr(s, "size")), default=None)
        info = {"kind": "photo", "photo_id": getattr(photo, "id", None), "size": largest}
        return "photo", json.dumps(info, ensure_ascii=False)
    if isinstance(media, MessageMediaDocument):
        doc = media.document
        if doc is None:
            return "document", None
        mime = getattr(doc, "mime_type", None) or ""
        filename = None
        for attr in getattr(doc, "attributes", None) or []:
            if isinstance(attr, DocumentAttributeFilename):
                filename = attr.file_name
        kind = "video" if mime.startswith("video/") else ("audio" if mime.startswith("audio/") else "document")
        info = {
            "kind": kind, "document_id": getattr(doc, "id", None),
            "mime_type": mime or None, "size": getattr(doc, "size", None), "filename": filename,
        }
        return kind, json.dumps(info, ensure_ascii=False)
    return "other", None


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
        media_type, media_json = _media_info(msg)
        yield {
            "channel_id": entity.id,
            "msg_id": msg.id,
            "date": msg.date.isoformat() if msg.date else None,
            "text": text,
            "views": getattr(msg, "views", None),
            "forwards": getattr(msg, "forwards", None),
            "links": json.dumps(links, ensure_ascii=False) if links else None,
            "edited_date": msg.edit_date.isoformat() if msg.edit_date else None,
            "media_type": media_type,
            "media_json": media_json,
            "sender_id": getattr(msg, "sender_id", None),
            **fwd_info,
        }


_PHONE_RE = re.compile(r"(?:\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}")


def iter_participants(client: TelegramClient, entity: Any) -> Iterator[dict[str, Any]]:
    """Enumerate every member of a forum/chat and catalog identity signal:
    username, the account's phone field (only populated where the member's
    privacy settings expose it — most won't), any phone number written into
    the freeform bio itself (a much more common leak than the phone field),
    and a profile-photo count (catalog only — see tg_media_pull.py's
    candidates/fetch split for the human-curated download-and-review step
    that follows, e.g. flagging a photo with an identifiable license plate
    or location). Full user info (bio) needs one GetFullUserRequest per
    member — fine for a single forum/chat's roster, not something to run
    across every channel in config/channels.txt without cause."""
    from telethon.tl.functions.users import GetFullUserRequest

    for user in client.iter_participants(entity, aggressive=True):
        bio = None
        try:
            full = client(GetFullUserRequest(user))
            bio = getattr(full.full_user, "about", None)
        except Exception:
            pass
        bio_phone = None
        if bio:
            m = _PHONE_RE.search(bio)
            if m:
                bio_phone = m.group(0)
        photo_count = None
        photo_ids: list[int] = []
        try:
            photos = client.get_profile_photos(user, limit=100)
            photo_count = getattr(photos, "total", None) or len(photos)
            photo_ids = [p.id for p in photos]
        except Exception:
            pass
        yield {
            "id": user.id,
            "username": getattr(user, "username", None),
            "first_name": getattr(user, "first_name", None),
            "last_name": getattr(user, "last_name", None),
            "phone": getattr(user, "phone", None),
            "bio": bio,
            "bio_phone": bio_phone,
            "is_bot": getattr(user, "bot", False),
            "is_verified": getattr(user, "verified", False),
            "is_scam": getattr(user, "scam", False),
            "is_fake": getattr(user, "fake", False),
            "is_premium": getattr(user, "premium", False),
            "profile_photo_count": photo_count,
            "profile_photo_ids": json.dumps(photo_ids, ensure_ascii=False) if photo_ids else None,
            "seen_in_channel_id": entity.id,
        }
