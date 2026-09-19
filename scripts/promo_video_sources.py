#!/usr/bin/env python3
"""Inventory where each registry entity publishes promo video, and what is already scraped.

Local only (reads data/registry/entities.json, config/channels.txt, data/roymarket.db).

  python3 scripts/promo_video_sources.py --out data/registry/_promo_video_sources.md
  python3 scripts/promo_video_sources.py --tiers manufacturer --gaps-only
"""
import argparse, json, re, sqlite3, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLATFORMS = ("telegram", "vk", "youtube", "rutube", "dzen", "other", "sites")


def tg_handle(url: str) -> str | None:
    m = re.search(r"(?:t\.me|telegram\.me)/(?:s/)?([A-Za-z0-9_+]+)", url or "")
    return m.group(1).lower() if m else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tiers", default="manufacturer", help="comma list of tiers")
    ap.add_argument("--gaps-only", action="store_true", help="only entities with a video-bearing URL not yet scraped")
    ap.add_argument("--out")
    a = ap.parse_args()
    tiers = set(a.tiers.split(","))

    ents = json.load(open(ROOT / "data/registry/entities.json"))
    listed = {
        l.strip().lstrip("@").lower().replace("https://t.me/", "")
        for l in (ROOT / "config/channels.txt").read_text().splitlines()
        if l.strip() and not l.startswith("#")
    }
    con = sqlite3.connect(ROOT / "data/roymarket.db")
    scraped = {}
    for uname, n in con.execute(
        "select c.username, count(p.id) from tg_channels c left join tg_posts p on p.channel_id=c.id group by c.id"
    ):
        if uname:
            scraped[uname.lower()] = n

    rows, no_presence = [], []
    for e in ents:
        if e.get("tier") not in tiers:
            continue
        name = e.get("name_ru") or e.get("name") or e.get("inn")
        web = e.get("web") or {}
        found = []
        for plat in PLATFORMS:
            for item in web.get(plat) or []:
                url = item.get("url") if isinstance(item, dict) else str(item)
                if not url:
                    continue
                if plat == "sites" and not re.search(r"youtu|vk\.|rutube|dzen|t\.me", url):
                    found.append((plat, url, ""))
                    continue
                status = ""
                h = tg_handle(url) if "t.me" in url or "telegram.me" in url else None
                if h:
                    if h in scraped:
                        status = f"scraped ({scraped[h]} posts)"
                    elif h in listed:
                        status = "in channels.txt, not scraped"
                    else:
                        status = "NOT WATCHED"
                found.append((plat, url, status))
        video_bearing = [f for f in found if f[0] != "sites"]
        if not video_bearing:
            no_presence.append(name)
        if a.gaps_only and not any("NOT WATCHED" in f[2] or "not scraped" in f[2] or (f[2] == "" and f[0] != "sites") for f in video_bearing):
            continue
        rows.append((name, e.get("inn"), e.get("slug"), found))

    out = [f"# Promo-video source inventory ({', '.join(sorted(tiers))})\n"]
    out.append(f"{len(rows)} entities listed; {len(no_presence)} have no known video-bearing presence (site-only or none).\n")
    for name, inn, slug, found in rows:
        out.append(f"\n## {name} (ИНН {inn}, {slug})")
        for plat, url, status in found:
            out.append(f"- {plat}: {url}" + (f"  [{status}]" if status else ""))
        if not found:
            out.append("- (no web presence recorded)")
    out.append("\n## No video-bearing presence recorded\n")
    out += [f"- {n}" for n in no_presence]
    text = "\n".join(out)
    if a.out:
        Path(a.out).write_text(text)
        print("wrote", a.out, "-", len(rows), "entities,", len(no_presence), "without video presence")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
