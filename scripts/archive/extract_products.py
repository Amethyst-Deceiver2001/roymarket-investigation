#!/usr/bin/env python3
"""Product/brand-name catalog sweep over every scraped Telegram channel —
not just @ANO_CBST. Reuses id_patterns.RE_QUOTED_NAME (the same «guillemet-
quoted» pattern mine_leads.py already uses for product/brand detection) and
is_noise_quote (its false-positive filter), applied channel-wide instead of
per-entity, so it surfaces product names regardless of which company they
turn out to belong to — matching the roymarket_brand_vs_legal_name_search
lesson that ЦБСТ/press coverage names brands, not legal entities.

Local DB processing only (reads data/roymarket.db) — no network calls, same
"safe to rerun anytime" category as mine_leads.py and scan_sources.py.

For each normalized quoted name, records: display form, total mentions,
first/last seen date, distinct channels it appears in, and up to 3 sample
post ids — then cross-checks against every registry entity's products[]/
brand_ru/name_ru to flag whether it's already attributed, so the output is
a triage list (new leads first) rather than a re-derivation of what's known.

Usage:
    python3 scripts/extract_products.py --out data/registry/_product_scan.json
"""
import argparse
import json
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from id_patterns import RE_QUOTED_NAME, is_noise_quote, norm

REPO = Path(__file__).resolve().parent.parent
DB = REPO / "data" / "roymarket.db"
ENTITIES = REPO / "data" / "registry" / "entities.json"


def known_product_index():
    """normalized name -> list of entity slugs already claiming this product/brand.
    Splits compound brand strings ("«Булат» / 3mx") into parts and also checks
    name_ru/name_latin, since a bare product mention on Telegram often IS the
    entity's own name (e.g. «Ушкуйник»)."""
    idx = defaultdict(list)
    if not ENTITIES.exists():
        return idx
    entities = json.loads(ENTITIES.read_text(encoding="utf-8"))
    for e in entities:
        slug = e.get("slug")
        for field in ("brand_ru", "brand_latin", "name_ru", "name_latin"):
            v = e.get(field)
            if not v:
                continue
            idx[norm(v)].append(slug)
            for part in re.split(r"[/,]|(?<=»)\s+(?=«)", v):
                part = part.strip()
                if part and norm(part):
                    idx[norm(part)].append(slug)
        for p in e.get("products") or []:
            name = p.get("name_ru") if isinstance(p, dict) else p
            if name:
                idx[norm(name)].append(slug)
    return idx


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="data/registry/_product_scan.json")
    ap.add_argument("--min-mentions", type=int, default=1)
    args = ap.parse_args()

    if not DB.exists():
        raise SystemExit(f"{DB} not found")

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT id, username, title FROM tg_channels")
    channels = {row[0]: (row[1], row[2]) for row in cur.fetchall()}

    tally = {}  # norm_name -> {display, count, first, last, channels:set, samples:[]}

    cur.execute("SELECT id, channel_id, date, text FROM tg_posts WHERE text IS NOT NULL")
    rows_seen = 0
    for post_id, channel_id, date, text in cur:
        rows_seen += 1
        for m in RE_QUOTED_NAME.finditer(text):
            name = m.group(1).strip()
            if is_noise_quote(name):
                continue
            key = norm(name)
            if not key:
                continue
            entry = tally.setdefault(key, {
                "display": name, "count": 0, "first": date, "last": date,
                "channels": set(), "samples": [],
            })
            entry["count"] += 1
            if date < entry["first"]:
                entry["first"] = date
            if date > entry["last"]:
                entry["last"] = date
                entry["display"] = name  # prefer most-recent casing/form
            uname = channels.get(channel_id, (str(channel_id), ""))[0]
            entry["channels"].add(uname)
            if len(entry["samples"]) < 3:
                entry["samples"].append(post_id)

    print(f"{rows_seen} posts scanned across {len(channels)} channels, "
          f"{len(tally)} distinct quoted names found", file=sys.stderr)

    known = known_product_index()

    results = []
    for key, entry in tally.items():
        if entry["count"] < args.min_mentions:
            continue
        results.append({
            "normalized": key,
            "display": entry["display"],
            "mentions": entry["count"],
            "first_seen": entry["first"],
            "last_seen": entry["last"],
            "channels": sorted(entry["channels"]),
            "sample_post_ids": entry["samples"],
            "already_attributed_to": known.get(key, []),
        })

    results.sort(key=lambda r: (-len(r["already_attributed_to"]) if r["already_attributed_to"] else 0, -r["mentions"]))
    # unattributed-first ordering: put entries with no known attribution first, then by mention count
    results.sort(key=lambda r: (bool(r["already_attributed_to"]), -r["mentions"]))

    out_path = REPO / args.out
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    unattributed = sum(1 for r in results if not r["already_attributed_to"])
    print(f"Done: {len(results)} names (min {args.min_mentions} mention(s)), "
          f"{unattributed} not yet attributed to any registry entity")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
