#!/usr/bin/env python3
"""The morning brief: where the investigation stands, in the shape of a news-meeting budget (user, 24.10.2026).

    python3 scripts/morning_brief.py            # print, and write data/watch/brief/<date>.md
    python3 scripts/morning_brief.py --no-write # print only
    python3 scripts/morning_brief.py --since 2026-10-20

Five short parts: what is new since the last brief, what is ready, what is stuck and why, what waits on the user,
and the next records by priority. It is written for one reader, the user, and for any fresh session taking over.

Everything is computed except the hand-kept list in data/watch/brief_items.json (what is ready, what is stuck for
a reason no file shows, decisions only the user can make). Close an item there with "status": "closed" and a note;
nothing is deleted. The board's own checks (scripts/status_board.py) supply the system signals and the priority
order, so the brief never disagrees with the board. Local only. It never reports GitHub Actions: abandoned (CLAUDE.md).
"""
import argparse
import json
import shutil
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import status_board as sb  # noqa: E402

WATCH = REPO / "data" / "watch"
OUT_DIR = WATCH / "brief"
ITEMS = WATCH / "brief_items.json"
SOURCES = REPO / "data" / "sources"
TRIAGE = SOURCES / "_media_triage"
AUTO_COMMIT = ("Daily round", "daily round", "Status board:")   # mechanical commits are not news
# The flag that explains a record's place in the priority order comes first, so "first task" is the reason it ranks.
FIRST_TASK = ("sanction_unread", "identity_unproven", "tie_not_documented", "development", "bfo_unread",
              "open_questions", "egrul_missing", "bfo_missing")


def ru(d):
    return d.strftime("%d.%m.%Y") if d else "?"


def age(since, today):
    try:
        n = (today - date.fromisoformat(since)).days
    except (TypeError, ValueError):
        return ""
    return f" · open {n} d" if n else " · new today"


def git(*args):
    r = subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True)
    return r.stdout.strip()


def previous_brief(today):
    old = sorted(p.stem for p in OUT_DIR.glob("*.md") if p.stem < today.isoformat()) if OUT_DIR.exists() else []
    return date.fromisoformat(old[-1]) if old else None


def commits_since(since):
    lines = git("log", f"--since={since.isoformat()} 00:00", "--format=%cs\t%s", "--no-merges").splitlines()
    return [ln.split("\t", 1) for ln in lines if ln and not ln.split("\t", 1)[1].startswith(AUTO_COMMIT)]


def uncatalogued():
    """Files in data/sources/ that no sources.json record points at: collected, not yet citable."""
    if not SOURCES.exists():
        return []
    known = {Path(s.get("path") or "").name for s in sb.load("sources.json")}
    return sorted(p.name for p in SOURCES.iterdir()
                  if p.is_file() and not p.name.startswith(("_", ".")) and p.name not in known)


def media_stage():
    """Where the picture pipeline stands: downloaded, fingerprinted, OCR'd, ranked, on sheets, looked at."""
    if not TRIAGE.exists():
        return None
    load = lambda p, d: json.loads(p.read_text(encoding="utf-8")) if p.exists() else d  # noqa: E731
    queued = len(load(TRIAGE / "queue.json", {}).get("items", []))
    files = len(list((TRIAGE / "files").iterdir())) if (TRIAGE / "files").exists() else 0
    proc = load(TRIAGE / "processed.json", {})
    ocr = sum(1 for v in proc.values() if "text_chars" in v)
    ranked = sum(1 for v in proc.values() if any(k.startswith(("clip", "rank")) for k in v))
    sheets = len(list((TRIAGE / "sheets").glob("*.jpg"))) if (TRIAGE / "sheets").exists() else 0
    looked = len(load(REPO / "data" / "registry" / "_media_looked.json", []))
    return (f"pictures: {files:,} of {queued:,} downloaded, {len(proc):,} fingerprinted, {ocr:,} read by OCR, "
            f"{ranked:,} ranked, {sheets} contact sheets, {looked:,} looked at in all")


def machine(today):
    out = []
    free = shutil.disk_usage(Path.home()).free / 2**30
    out.append(("act" if free < 2 else "watch" if free < 10 else "ok", f"disk: {free:.1f} GB free"))
    hooks = git("config", "core.hooksPath")
    out.append(("ok" if hooks == "ops/git-hooks" else "act",
                "commit hook installed" if hooks == "ops/git-hooks" else
                "commit hook not installed (git config core.hooksPath ops/git-hooks)"))
    for name in ("roymarket311", "roymarket-media"):
        ok = (Path.home() / ".venvs" / name / "bin" / "python").exists()
        out.append(("ok" if ok else "watch", f"venv {name}: {'present' if ok else 'missing'}"))
    return out


def build(today, since):
    dv, ss = sb.default_path("developments.json"), sb.default_path("weekly_scan_state.json")
    board = sb.Board(today, json.loads(ss.read_text(encoding="utf-8")) if ss and ss.exists() else None,
                     json.loads(dv.read_text(encoding="utf-8")) if dv and dv.exists() else None).build()
    hand = json.loads(ITEMS.read_text(encoding="utf-8")).get("items", []) if ITEMS.exists() else []
    hand = [h for h in hand if h.get("status", "open") == "open"]
    by = lambda k: [h for h in hand if h.get("kind") == k]  # noqa: E731

    commits = commits_since(since)
    devs = json.loads(dv.read_text(encoding="utf-8")) if dv and dv.exists() else {}
    new_devs = [d for d in devs.get("items", []) if isinstance(d, dict) and (d.get("found") or "") >= since.isoformat()]
    staged = uncatalogued()
    stuck_sys = [c for c in board["system"] if c["status"] == "act"]
    stage = media_stage()

    L = [f"# Brief, {ru(today)}", ""]
    L.append(f"{len(commits)} change(s) since {ru(since)}; {len(by('ready'))} ready; "
             f"{len(by('stuck')) + len(stuck_sys)} stuck; {len(by('decision'))} waiting on you.")

    L += ["", f"## New since {ru(since)}"]
    for d, s in commits[:10]:
        L.append(f"- {d[8:10]}.{d[5:7]} {s}")
    if len(commits) > 10:
        L.append(f"- …and {len(commits) - 10} more (git log --since={since.isoformat()})")
    for d in new_devs:
        L.append(f"- Scan finding ({d.get('status')}): {d.get('summary', '')[:140]}")
    if staged:
        L.append(f"- {len(staged)} source file(s) collected but not catalogued (no source id yet): "
                 + ", ".join(staged[:4]) + (" …" if len(staged) > 4 else ""))
    if not (commits or new_devs or staged):
        L.append("- Nothing.")

    L += ["", "## Ready"]
    L += [f"- {h['text']}{age(h.get('since'), today)}" + (f" — {h['link']}" if h.get("link") else "") for h in by("ready")] \
        or ["- Nothing marked ready."]

    L += ["", "## Stuck"]
    L += [f"- {h['text']}{age(h.get('since'), today)}" + (f". Why: {h['why']}" if h.get("why") else "") for h in by("stuck")]
    L += [f"- {c['label']}: {c['value']}. {c['detail']}" for c in stuck_sys]
    if stage:
        L.append(f"- In progress, {stage}.")

    L += ["", "## Waiting on you"]
    L += [f"- {h['text']}{age(h.get('since'), today)}" + (f". {h['why'][0].upper()}{h['why'][1:]}" if h.get("why") else "") for h in by("decision")] \
        or ["- Nothing."]

    L += ["", "## Next in the record"]
    for r in sorted(board["rows"], key=sb.priority_key)[:5]:
        p = r["priority"]
        fl = sorted(r["flags"], key=lambda f: FIRST_TASK.index(f["code"]) if f["code"] in FIRST_TASK else 99)
        first = fl[0]["text"] if fl else ""
        L.append(f"- {r.get('latin') or r.get('name')}: {p['why'] or 'no sanctions signal'}. First task: {first}")
    L.append("- Full order: python3 scripts/status_board.py --next 20")

    L += ["", "## Machine"]
    L += [f"- {'⚠ ' if s == 'act' else ''}{t}" for s, t in machine(today)]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--since", help="YYYY-MM-DD (default: the previous brief, else three days ago)")
    ap.add_argument("--today", help="YYYY-MM-DD (default: today)")
    ap.add_argument("--no-write", action="store_true")
    a = ap.parse_args()
    today = date.fromisoformat(a.today) if a.today else date.today()
    since = date.fromisoformat(a.since) if a.since else (previous_brief(today) or today - timedelta(days=3))
    text = build(today, since)
    print(text)
    if not a.no_write:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUT_DIR / f"{today.isoformat()}.md").write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
