"""Central configuration: env loading, paths.

Independent of wb_watch — own .env, own session, own channel list. See
CLAUDE.md for why: this investigation needs its own scraping targets
(corporate entities, product names) rather than wb_watch's WB/Ozon-link
matching, and shouldn't depend on another repo's auth session.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

DB_PATH = ROOT / "data" / "roymarket.db"
CHANNELS_FILE = ROOT / "config" / "channels.txt"

TG_API_ID = os.environ.get("TG_API_ID", "").strip()
TG_API_HASH = os.environ.get("TG_API_HASH", "").strip()
TG_SESSION = os.environ.get("TG_SESSION", "").strip()
