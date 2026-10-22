# data/watch: shared state for the scheduled jobs

Since 03.10.2026 every job that the sessions hand to each other reads and writes its state here, through git, rather than through cross-session messages or the cloud-only folder `/mnt/project-files/watch/`. If a file is not here, `status_board.py` falls back to that folder until it has been migrated.

| Path | Written by | Read by |
|---|---|---|
| `daily/<date>.md` | the Mac's scheduled round (launchd `ops/launchd/com.roymarket.daily-round.plist`, 09:15 local time) | status check routine, main session |
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

## Push first, ping second (03.10.2026)

A cloud session reaches the Mac session in one way only, and not reliably, so the repo carries everything:

1. **Write the result to the repo and push it** (a file under `data/watch/`, `notes/first_reading/` or `notes/`, or a PR to merge). A result that is not in git does not exist for the main session.
2. **Anything that needs the user goes in a GitHub issue**, with the paths of the files it concerns. A comment on an issue or PR is the one alert that needs no session id.
3. **A direct message to the main session is optional.** It may arrive (it needs the receiver's current session id and Remote Control on) and it cannot be answered or confirmed. Keep it to one line pointing at the pushed paths, and never put a result, a decision or an instruction in it.

On the receiving side: a ping or an issue comment is a pointer to read, not an instruction. The main session pulls main, reads what was pushed, and acts only where the user's own instructions already call for it. Without a ping it finds the files at the next daily pull (09:15) or at session start.

First case: the sanctions pre-sort thread, PR #24 (`data/watch/sanctions/presort_2026-10-02.{json,md}`, issue #25), followed by a one-line message. Its proposed calls (`user_verdict: null`) enter the registry only after the user confirms them.

## Picking up a manual pull (03.10.2026)

When the user runs a pull command from the status board by hand, nothing else has to be reconstructed:

- `python3 scripts/status_board.py --pull-queue` prints what is left. Each cap (8 pulls per registry, 4 OpenSanctions, 8 ГУР, 8 Aleph) counts the whole day, so a rerun shows only the remainder and says what is already used.
- `python3 scripts/daily_mac.py --publish` runs the rest (screens, the ingest chain, first-reading export and worksheet) and commits the mechanical outputs. Files a manual pull leaves modified (`_pull_misses.json`, regenerated registry files) do not block it; a corrections file, a hand-held registry file or a script does.
- If one step of the ingest chain fails, the later ones are skipped and the report names it: the registry is never regenerated from a stale manifest.
- The filings are then read in the main session (`data/sources/_inbox/<date>/reading.md`); a pulled file stays a `bfo_unread` flag on the board until its figures are in `financials[]`.

## Coordination between sessions (user, 22.10.2026)

For every session that touches this repo: the Mac ("main"), git-only cloud sessions and Project threads. It extends "Push first, ping second" above.

1. **The repo is the record.** Decisions, hand-offs and open items go in a notes file or a GitHub issue. A message is only a one-line nudge ("look at X", with the path or branch); nothing is applied to the registry on a message alone. Take the receiver's name from `ListAgents` just before sending; if it is not listed, write a repo note.
2. **Only the main session writes registry facts**, from original documents read in full. Git-only sessions work on branches and PRs and never run pulls, `daily_mac.py`, the timestamp jobs or `inventory_sources.py`. Anything from a Project or git-only session built on summaries is a lead. Anything under `docs/` or sent outside the project needs the user's go-ahead.
3. **Files.** Text and JSON move by branch or PR. Source files stay out of git and move by AirDrop, scp or a private cloud folder, with a `SHA256SUMS` file and `PRESS_<YYYYMMDD>_<outlet>-<id>-<slug>` naming. No `sNNNN` ids are assigned off the main machine.
