#!/usr/bin/env python3
"""One-time interactive Telegram auth. Prompts for phone/code/2FA on the
console, prints a session string to paste into .env as TG_SESSION.

Own session, independent of wb_watch's — see CLAUDE.md for why this repo
has its own Telegram app registration/session rather than sharing wb_watch's.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tg import client  # noqa: E402


def main() -> None:
    session = client.login()
    print("\nAdd this line to your .env:")
    print(f"TG_SESSION={session}")


if __name__ == "__main__":
    main()
