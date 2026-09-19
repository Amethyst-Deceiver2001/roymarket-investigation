#!/usr/bin/env python3
"""Rank t.me handles mentioned in stored posts that are not yet in the DB or config/channels.txt.

Local only. Output is a lead list for config/channels.txt (a live scrape of any of them is
tg_scan.py, handed to the user). Handles that look like people/bots are flagged, not dropped.

  python3 scripts/find_candidate_channels.py --min-mentions 3 --out data/registry/_candidate_channels.md
"""
import argparse, collections, re, sqlite3, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINK = re.compile(r"(?:https?://)?t\.me/(?:s/)?([A-Za-z][A-Za-z0-9_]{3,31})(?![A-Za-z0-9_])")
SKIP = {"joinchat", "addstickers", "share", "proxy", "c", "boost", "bot", "iv", "s"}
UAV = re.compile(r"дрон|бпла|fpv|фпв|беспилот|связ|пилот|коптер|перехватчик|тепловиз|рэб", re.I)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-mentions", type=int, default=3)
    ap.add_argument("--out")
    a = ap.parse_args()

    con = sqlite3.connect(ROOT / "data/roymarket.db")
    watched = {r[0].lower() for r in con.execute("select username from tg_channels where username is not null")}
    listed = {
        l.strip().lstrip("@").lower().replace("https://t.me/", "")
        for l in (ROOT / "config/channels.txt").read_text().splitlines()
        if l.strip() and not l.startswith("#")
    }
    known = watched | listed

    n = collections.Counter()
    src = collections.defaultdict(collections.Counter)
    uav_ctx = collections.Counter()
    video_ctx = collections.Counter()
    first = {}
    example = {}
    for ch, mid, date, mtype, text in con.execute(
        "select c.username, p.msg_id, p.date, p.media_type, p.text from tg_posts p "
        "join tg_channels c on c.id = p.channel_id where p.text like '%t.me/%'"
    ):
        seen = set()
        for m in LINK.finditer(text):
            h = m.group(1).lower()
            if h in SKIP or h in known or h in seen:
                continue
            seen.add(h)
            n[h] += 1
            src[h][ch or "?"] += 1
            if UAV.search(text):
                uav_ctx[h] += 1
            if mtype == "video":
                video_ctx[h] += 1
            first.setdefault(h, date[:10])
            example.setdefault(h, (ch, mid, text[:140].replace("\n", " ")))

    rows = [(h, c) for h, c in n.items() if c >= a.min_mentions]
    rows.sort(key=lambda x: (-uav_ctx[x[0]], -x[1]))
    out = [f"# Candidate channels (not in DB or channels.txt), >= {a.min_mentions} mentions\n",
           f"{len(rows)} handles. Ranked by mentions in UAV-related posts, then total. Lead list, not verified.\n"]
    for h, c in rows:
        kind = "bot" if h.endswith("bot") else ""
        ex = example[h]
        out.append(f"- @{h} {kind}: {c} mentions ({uav_ctx[h]} in UAV-related posts, {video_ctx[h]} in video posts), "
                   f"first seen {first[h]}, cited by {', '.join(f'@{k}({v})' for k, v in src[h].most_common(3))}; "
                   f"e.g. @{ex[0]} #{ex[1]}: {ex[2]}")
    text = "\n".join(out)
    if a.out:
        Path(a.out).write_text(text)
        print("wrote", a.out, "-", len(rows), "handles")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
