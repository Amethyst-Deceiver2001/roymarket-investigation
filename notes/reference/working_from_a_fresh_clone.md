# Working as main from a fresh clone (no local archive)

Internal. For a session on a machine that has the repo but not `data/sources/` or `data/roymarket.db` (a borrowed laptop, a new Mac, a cloud session). Written 22.10.2026 when the main session's machine was unavailable.

## What carries over and what does not

- The state is in the repo: `CLAUDE.md`, `notes/rebuild_plan.md`, `data/registry/`, `data/watch/`, the commit history. A new session reads these.
- A session's conversation does not move. As far as is known, `claude --resume` lists only sessions stored on the same machine, so a session from another computer cannot be resumed; start a new one and give it a handoff prompt (below). A Remote Control session record can stay "disconnected" for good; its queued model switches never apply.
- A cloud session cannot message a local session (CLAUDE.md, Coordination). Leave a GitHub issue or a note.

## Setup

1. Clone the repo, then `git config core.hooksPath ops/git-hooks`.
2. Python 3.11 matches CI. On an old macOS where Homebrew builds from source, use the python.org 3.11 installer, then `pip install -r requirements.txt`.
3. Check: `python3 scripts/check_registry.py --no-local-files` (expects 0 errors; skips only the `data/sources/` existence checks).

## What is safe and what is not

Safe: reading, registry and notes work from sources already cited, tests, `check_registry.py`, `status_board.py`, generating packets and exports, commits confined to the paths CLAUDE.md lists.

Not from this setup: `daily_mac.py`, `timestamp_sources.py`, any pull or screening job, `inventory_sources.py`, `scan_sources.py`, `tg_*` jobs. They assume the full local archive; run against an empty `data/sources/` they would write partial files and could look like changes to the real archive. Nothing under `docs/` is pushed without the user's go-ahead.

## When the usual machine comes back

Two machines must not both act as main. On the returning machine run `git pull` before anything else; its scheduled daily round (`ops/launchd/...`) refuses to publish when a `corrections_*.json` changed, which is the safety net. Check `data/watch/daily/` for the last round date.

## Handoff prompt (fill the two bracketed parts)

> Read CLAUDE.md, notes/rebuild_plan.md and the newest notes/repo_review_*.md. You are taking over as main from [previous session] (offline since [date]). Its work in progress: [what, which script or note, last commit]. It was waiting on: [the open question]. This machine has no data/sources or Telegram database; use check_registry.py --no-local-files. Do not publish under docs/ and do not run pulls or timestamp jobs. Tell me where things stand, then wait.
