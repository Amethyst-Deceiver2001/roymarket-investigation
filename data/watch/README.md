# data/watch: shared state for the scheduled jobs

Since 03.10.2026 every job that the sessions hand to each other reads and writes its state here, through git, rather than through cross-session messages or the cloud-only folder `/mnt/project-files/watch/`. If a file is not here, `status_board.py` falls back to that folder until it has been migrated.

| Path | Written by | Read by |
|---|---|---|
| `daily/<date>.md` | the Mac's scheduled round (`ops/run_daily_round.sh`, 09:15 local time) | status check routine, main session |
| `developments.json` | weekly scan routine (appends items); main session (sets `status: recorded\|dismissed` with a `note`, in the same commit as the correction it records) | `status_board.py` |
| `weekly_scan_state.json`, `watchlist.md` | weekly scan routine (state); the user (watch list) | weekly scan routine, `status_board.py` |
| `reports/<date>.md` | weekly scan routine | main session |
| `status/board.json` (one file; the diff is taken from its previous git version) | status check routine, 10:05 Berlin | status check routine |
| `sanctions/presort_*.json` | sanctions pre-sort thread | `status_board.py` |

First-reading notes go to `notes/first_reading/<date>.md`. They hold the comparison sheet and proposed corrections; nothing in them is in the registry.

Rules:
- Pull before you write and push straight after; on a conflict in an append-only file (`developments.json`), keep both sides.
- Only the main session writes `data/registry/corrections_*.json` and the other hand-held registry files, and only for facts read in full in the original document. Scheduled jobs commit mechanical outputs only: pulled files catalogued, screens recorded, reports.
- Something that needs the user goes in a GitHub issue. A session that cannot reach another one writes to the repo instead of waiting on a reply.
