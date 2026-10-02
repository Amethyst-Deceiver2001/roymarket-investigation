#!/usr/bin/env python3
"""The daily mechanical round on the user's Mac, in one command (user, 02.10.2026).

Chains tools that already exist, in the order CLAUDE.md gives them:

  1. status_board.py      board before; the capped pull queue (8 ЕГРЮЛ/ЕГРИП
                          + 8 БФО per day, top tiers first)
  2. the pull queue       egrul_vypiska_pull.py / bfo_pull.py and the capped
                          sanctions re-screens (screen_opensanctions/gur/aleph
                          --only), then the ingest
                          steps the queue prints (inventory, manifest, parsers,
                          extract_registry, build_relationship_graph,
                          check_registry)
  3. first_reading.py     export the day's new pulls as text (to the private
                          `pull-inbox` branch unless --no-push, and locally),
                          then `read` them into a worksheet beside the registry
  4. archive_sources.py   only with --archive N: one Wayback batch of N cited URLs
  5. status_board.py      board after, and the flags new or cleared today

What it writes stays in gitignored data/sources/_daily/ and data/sources/_inbox/.
Registry files that extract_registry.py regenerates are left uncommitted for
review. The worksheet is a proposal: a fact enters the registry only through
corrections_*.json after someone has read the document (CLAUDE.md hard rule).

The pull queue is the user's standing go-ahead (capped daily batch). A
full-roster sweep is still handed to the user as a command.

Usage:
  python3 scripts/daily_mac.py --dry-run         # print the plan only
  python3 scripts/daily_mac.py                   # pulls, ingest, first reading, diff
  python3 scripts/daily_mac.py --archive 150     # plus one Wayback batch
  python3 scripts/daily_mac.py --skip-pulls      # re-read and re-board only
"""
import argparse
import json
import shlex
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import status_board as sb  # noqa: E402

DAILY = ROOT / "data" / "sources" / "_daily"
INBOX = ROOT / "data" / "sources" / "_inbox"


def board_now(today):
    ss, dv = sb.default_path("weekly_scan_state.json"), sb.default_path("developments.json")
    return sb.Board(today,
                    json.loads(ss.read_text(encoding="utf-8")) if ss and ss.exists() else None,
                    json.loads(dv.read_text(encoding="utf-8")) if dv and dv.exists() else None).build()


def run(cmd, log):
    print(f"\n$ {cmd}", flush=True)
    r = subprocess.run(shlex.split(cmd), cwd=ROOT, capture_output=True, text=True)
    out = (r.stdout + r.stderr).rstrip()
    print(out[-4000:], flush=True)
    log.append(f"$ {cmd}\n(exit {r.returncode})\n{out[-1500:]}\n")
    return r.returncode


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="print the plan, run nothing")
    ap.add_argument("--cap", type=int, default=sb.PULL_CAP, help="pulls per registry (default %(default)s)")
    ap.add_argument("--skip-pulls", action="store_true")
    ap.add_argument("--no-push", action="store_true", help="do not push texts to pull-inbox")
    ap.add_argument("--archive", type=int, default=0, metavar="N", help="Wayback batch size (default: off)")
    a = ap.parse_args()

    today = date.today()
    day = today.isoformat()
    before = board_now(today)
    queue = [l for l in sb.pull_queue(before, a.cap).splitlines() if l.startswith("python3 ")]
    has_pulls = any("_pull.py" in l or "/screen_" in l for l in queue)  # pulls or capped re-screens
    steps = queue if has_pulls and not a.skip_pulls else []
    steps.append(f"python3 scripts/first_reading.py export --since {day} --local-dir data/sources/_inbox"
                 + ("" if a.no_push else " --push"))
    if a.archive:
        steps.append(f"python3 scripts/archive_sources.py run --limit {a.archive}")

    if a.dry_run:
        print("\n".join(steps))
        print(f"python3 scripts/first_reading.py read --inbox data/sources/_inbox/{day} --out data/sources/_inbox/{day}/reading.md")
        return 0

    DAILY.mkdir(parents=True, exist_ok=True)
    log, failed = [], []
    for cmd in steps:
        if run(cmd, log):
            failed.append(cmd.split()[1])

    reading = INBOX / day / "reading.md"
    if (INBOX / day / "manifest.json").exists():
        if run(f"python3 scripts/first_reading.py read --inbox {INBOX / day} --out {reading}", log):
            failed.append("first_reading read")

    after = board_now(today)
    changes = sb.diff(before, after)
    report = [f"# Daily round {day}", "",
              "Pulls: " + ("skipped" if a.skip_pulls else "ran" if has_pulls else "nothing flagged"),
              "First-reading worksheet: " + (str(reading.relative_to(ROOT)) if reading.exists() else "none (no new pulls)"),
              "Failed steps: " + (", ".join(failed) or "none"), "",
              "```", changes, "```", "", "## Log", "", *log]
    out = DAILY / f"{day}.md"
    out.write_text("\n".join(report), encoding="utf-8")
    print("\n" + changes)
    print(f"\nwrote {out.relative_to(ROOT)}; failed steps: {len(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
