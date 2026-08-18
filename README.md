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
docs/index.html         the brief (GitHub Pages source once a remote exists)
docs/images/             evidence photos referenced by the brief
data/roymarket.db        local Telegram-post export (gitignored, regenerate
                          with scripts/export_from_wb_watch.py)
scripts/                 tag-balance checker, DB export script
HANDOFF.md               full context for a new session — read this first
CLAUDE.md                working rules
```
