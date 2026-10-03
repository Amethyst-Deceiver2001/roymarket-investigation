#!/bin/zsh
# Scheduled daily round on the user's Mac (launchd: ops/launchd/com.roymarket.daily-round.plist).
# Runs the capped pull queue, ingest, first-reading export and board diff, then commits
# and pushes the mechanical outputs and the report in data/watch/daily/<date>.md.
# Standing go-ahead: the capped daily batch (CLAUDE.md, user 02.10.2026). Nothing beyond it.
export PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin
cd "$(dirname "$0")/.." || exit 1
echo "=== $(date '+%F %T') daily round"
python3 -u scripts/daily_mac.py --publish
echo "=== $(date '+%F %T') done (exit $?)"
