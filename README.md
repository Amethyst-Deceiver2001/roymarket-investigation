# РОЙ.МАРКЕТ / ЦБСТ investigation

Corporate-genealogy OSINT investigation into ЦБСТ (Центр беспилотных систем
и технологий) and the РОЙ.МАРКЕТ "military marketplace" its subsidiary runs
— a companion piece to Alexey Kovalev's Foreign Policy article, and a
sanctions-lobbying reference document.

- **Read the brief**: `docs/index.html`, or the published Artifact
  (https://claude.ai/code/artifact/5450bf7e-7f7b-4788-93c0-761503dd5ea4 —
  may lag the local file, see `HANDOFF.md`).
- **New Claude Code session on this repo**: read `HANDOFF.md` first, then
  `CLAUDE.md` for working rules.
- **Migrated from** the `wb_watch` project on 2026-08-18.

## Layout

```
docs/index.html          the brief (GitHub Pages source once a remote exists)
docs/images/              evidence photos referenced by the brief
data/roymarket.db         local Telegram-post DB (gitignored — own data, see below)
tg/                        own Telethon client/scraper/storage, independent of wb_watch
config/channels.txt        this investigation's own channel watchlist
.env.example                copy to .env, fill in TG_API_ID/TG_API_HASH/TG_SESSION
scripts/tg_login.py         one-time interactive Telegram auth
scripts/tg_scan.py          scrape config/channels.txt into data/roymarket.db (live network job — see CLAUDE.md)
scripts/mine_leads.py       entity/product/person extraction over data/roymarket.db (local, safe to rerun anytime)
scripts/check_tag_balance.py   run after every docs/index.html edit
scripts/export_from_wb_watch.py   historical bootstrap only, not the ongoing method
HANDOFF.md                full context for a new session — read this first
CLAUDE.md                 working rules
```
