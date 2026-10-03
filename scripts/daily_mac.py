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

The day's report goes to data/watch/daily/<date>.md, which the cloud routines
read through git; the texts stay in gitignored data/sources/_inbox/. With
--publish (what the scheduled job uses) the round starts from the latest main
and ends by committing and pushing the report and the files the ingest chain
regenerates (data/registry/, data/watch/). It refuses to commit when the tree
had tracked changes before the run or when a corrections_*.json file changed:
a mechanical round never writes a hand-made fact. The worksheet is a proposal: a fact enters the registry only through
corrections_*.json after someone has read the document (CLAUDE.md hard rule).

The pull queue is the user's standing go-ahead (capped daily batch). A
full-roster sweep is still handed to the user as a command.

Usage:
  python3 scripts/daily_mac.py --dry-run         # print the plan only
  python3 scripts/daily_mac.py                   # pulls, ingest, first reading, diff
  python3 scripts/daily_mac.py --archive 150     # plus one Wayback batch
  python3 scripts/daily_mac.py --skip-pulls      # re-read and re-board only
  python3 scripts/daily_mac.py --publish         # scheduled: pull main, run, commit, push
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

DAILY = ROOT / "data" / "watch" / "daily"
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


def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True)


def tracked_changes():
    return [l for l in git("status", "--porcelain").stdout.splitlines() if not l.startswith("??")]


# Files the round itself regenerates or appends to. A manual pull or ingest leaves these modified, and the
# round commits them with its own outputs, so they must not block it; a hand-held file (corrections_*,
# products.json, handovers.json, programs.json, ...) or any code file still does.
GENERATED = {"data/registry/" + n for n in (
    "_pull_misses.json", "source_archives.json", "_source_ids.json", "_source_content_cache.json",
    "_bfo_financials.json", "_scaffold_leads.json", "entities.json", "people.json", "sources.json",
    "quotes.json", "open_questions.json", "relationship_graph.json", "relationship_graph_views.json")}
# A step in this chain reads what the one before wrote: after a failure the rest would run on stale input.
INGEST = ("inventory_sources.py", "scan_sources.py", "parse_bfo_financials.py", "parse_egrul_vypiska.py",
          "extract_registry.py", "build_relationship_graph.py", "check_registry.py")


def hand_changes():
    return [l for l in tracked_changes() if l[3:].strip() not in GENERATED and not l[3:].startswith("data/watch/")]


def publish(day, summary):
    """Commit the round's mechanical outputs and push; returns a one-line outcome."""
    if any("corrections_" in l for l in tracked_changes()):
        return "not published: a corrections_*.json file changed during the round"
    git("add", "data/registry", "data/watch")
    if not git("diff", "--cached", "--quiet").returncode:
        return "nothing to commit"
    msg = (f"Daily round {day} (scheduled): {summary}\n\nMechanical outputs only: pulled files catalogued, "
           "screens recorded, report in data/watch/daily/. Nothing here is a read fact.\n\n"
           "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>")
    if git("commit", "-q", "-m", msg).returncode:
        return "commit failed"
    for _ in range(3):
        if not git("pull", "--rebase", "-q").returncode and not git("push", "-q").returncode:
            return "published " + git("rev-parse", "--short", "HEAD").stdout.strip()
        git("rebase", "--abort")
    return "committed locally, push failed (rebase conflict?): resolve by hand"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="print the plan, run nothing")
    ap.add_argument("--cap", type=int, default=sb.PULL_CAP, help="pulls per registry (default %(default)s)")
    ap.add_argument("--skip-pulls", action="store_true")
    ap.add_argument("--no-push", action="store_true", help="do not push texts to pull-inbox")
    ap.add_argument("--archive", type=int, default=0, metavar="N", help="Wayback batch size (default: off; "
                    "the daily Wayback batch runs in GitHub Actions, .github/workflows/wayback.yml)")
    ap.add_argument("--publish", action="store_true", help="start from latest main, then commit and push the outputs")
    a = ap.parse_args()

    blocked = None
    if a.publish and not a.dry_run:
        if hand_changes():
            blocked = ("not published: the working tree had uncommitted changes before the round ("
                       + ", ".join(l[3:].strip() for l in hand_changes()[:4]) + ")")
        elif git("pull", "--rebase", "-q").returncode:
            blocked = "not published: could not update from origin"

    today = date.today()
    day = today.isoformat()
    before = board_now(today)
    queue = [l for l in sb.pull_queue(before, a.cap, sb.done_today(today)).splitlines() if l.startswith("python3 ")]
    has_pulls = any("_pull.py" in l or "/screen_" in l for l in queue)  # pulls or capped re-screens
    steps = queue if has_pulls and not a.skip_pulls else []
    if not any("first_reading.py export" in l for l in steps):  # the queue ends with one when it pulled
        steps.append(f"python3 scripts/first_reading.py export --since {day} --local-dir data/sources/_inbox"
                     + ("" if a.no_push else " --push"))
    elif a.no_push:
        steps = [l.replace(" --push", "") if "first_reading.py export" in l else l for l in steps]
    if a.archive:
        steps.append(f"python3 scripts/archive_sources.py run --limit {a.archive}")
    if (ROOT / "data" / "sources" / "_media_triage" / "files").exists():  # after a media download: local only
        steps.append("python3 scripts/media_triage.py process")
        venv_py = Path.home() / ".venvs" / "roymarket-media" / "bin" / "python"
        if venv_py.exists():  # CLIP ranking needs open_clip, which lives in that venv, not in Homebrew's Python
            steps.append(f"{venv_py} scripts/media_triage.py rank")
        steps.append("python3 scripts/media_triage.py sheets")

    if a.dry_run:
        print("\n".join(steps))
        print(f"python3 scripts/first_reading.py read --inbox data/sources/_inbox/{day} --out data/sources/_inbox/{day}/reading.md")
        return 0

    DAILY.mkdir(parents=True, exist_ok=True)
    log, failed = [], []
    ingest_broken = False
    for cmd in steps:
        is_ingest = any(x in cmd for x in INGEST)
        if is_ingest and ingest_broken:
            print(f"\n$ {cmd}\nskipped: an earlier ingest step failed", flush=True)
            log.append(f"$ {cmd}\n(skipped: an earlier ingest step failed)\n")
            continue
        if run(cmd, log):
            failed.append(cmd.split()[1])
            ingest_broken = ingest_broken or is_ingest

    reading = INBOX / day / "reading.md"
    if (INBOX / day / "manifest.json").exists():
        if run(f"python3 scripts/first_reading.py read --inbox {INBOX / day} --out {reading}", log):
            failed.append("first_reading read")

    after = board_now(today)
    changes = sb.diff(before, after)
    pulled = sum(1 for l in log if "_pull.py" in l.splitlines()[0])
    screened = sum(1 for l in log if "/screen_" in l.splitlines()[0])
    summary = f"{pulled} pull step(s), {screened} screen step(s), {len(failed)} failed"
    report = [f"# Daily round {day}", "",
              "Summary: " + summary,
              "Pulls: " + ("skipped" if a.skip_pulls else "ran" if has_pulls else "nothing flagged"),
              "First-reading worksheet: " + (str(reading.relative_to(ROOT)) if reading.exists() else "none (no new pulls)"),
              "Failed steps: " + (", ".join(failed) or "none"), "",
              "```", changes, "```", "", "## Log", "", *log]
    out = DAILY / f"{day}.md"
    out.write_text("\n".join(report), encoding="utf-8")
    print("\n" + changes)
    print(f"\nwrote {out.relative_to(ROOT)}; failed steps: {len(failed)}")
    if a.publish:
        outcome = blocked or publish(day, summary)
        print(outcome)
        if blocked or not outcome.startswith(("published", "nothing")):
            with out.open("a", encoding="utf-8") as f:
                f.write(f"\n\nPublish: {outcome}\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
