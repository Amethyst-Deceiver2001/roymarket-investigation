#!/usr/bin/env python3
"""Entity/product-name mining pass over data/roymarket.db, purpose-built for
this investigation — NOT a port of wb_watch's tg-scan, which matches posts
against wildberries.ru/ozon.ru links and has nothing to do with corporate-
entity extraction.

This is local text processing over already-scraped posts, not a live network
job, so it's fine to run directly/repeatedly (unlike an actual Telegram
scrape) — see CLAUDE.md's crawling-jobs policy for the distinction.

What it looks for, per post:
  - Corporate entities: legal-form prefix (ООО/АО/НПЦ/etc) + a name, quoted
    or not.
  - «Quoted product names» — the guillemet-branding convention used
    throughout this network (see [[tg_channel_dual_sweep]] — both sweeps are
    needed, one alone misses real leads).
  - ИНН/ОГРН sequences (10/12 and 13/15 digit) near a labeling word.
  - Named individuals with a role title (Генеральный директор/Учредитель/
    Директор/Председатель + a 2-3 word Capitalized name).
  - A per-post UAV/military relevance score (drone/EW/military-industry
    keyword hits) — used to down-rank noise from the broad general-news
    channels (mil_hub alone is 62k+ posts of mixed war-news content, most
    of it irrelevant to entity mapping).

Candidates get normalized (strip legal-form prefix, casefold, strip
punctuation — see [[roymarket_fuzzy_dedup]]) and cross-checked against
docs/index.html so already-documented entities don't get re-reported as new.

Output: a markdown report to stdout (or --out FILE), ranked by a relevance
score (UAV-context weight x frequency x distinct-channel spread), split into
"not yet in the brief" vs "already documented" sections.
"""
import argparse
import sqlite3
from collections import defaultdict
from pathlib import Path

from id_patterns import (
    RE_ENTITY_BARE, RE_ENTITY_QUOTED, RE_INN, RE_OGRN, RE_QUOTED_NAME,
    RE_ROLE_NAME, is_noise_quote, load_known_text, norm, uav_score,
)

REPO = Path(__file__).resolve().parent.parent
DB = REPO / "data" / "roymarket.db"


def load_brief_text() -> str:
    """Everything already documented, for the 'is this actually new?' check.

    Reads `data/registry/*.json` plus the brief — see
    `id_patterns.load_known_text`. Previously this grepped `docs/index.html`
    alone, which the move to a generated site would have quietly broken.
    """
    return load_known_text(REPO)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=None, help="write report here instead of stdout")
    ap.add_argument("--top", type=int, default=60, help="max candidates per section")
    ap.add_argument("--min-score", type=int, default=2, help="minimum relevance score to surface")
    args = ap.parse_args()

    if not DB.exists():
        raise SystemExit(f"{DB} not found — run scripts/export_from_wb_watch.py first.")

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    chans = {r["id"]: r["title"] for r in conn.execute("SELECT id, title FROM tg_channels")}

    # candidate_key -> {display, kind, hits: [(channel_id, msg_id, date)], score}
    entities = defaultdict(lambda: {"display": None, "kind": "entity", "hits": [], "score": 0})
    products = defaultdict(lambda: {"display": None, "kind": "product", "hits": [], "score": 0})
    people = defaultdict(lambda: {"display": None, "kind": "person", "hits": [], "score": 0})
    inns = defaultdict(lambda: {"display": None, "kind": "inn", "hits": [], "score": 0})
    ogrns = defaultdict(lambda: {"display": None, "kind": "ogrn", "hits": [], "score": 0})

    def record(bucket, key, display, channel_id, msg_id, date, weight):
        rec = bucket[key]
        rec["display"] = rec["display"] or display
        rec["hits"].append((channel_id, msg_id, date))
        rec["score"] = rec.get("score", 0) + weight

    rows = conn.execute("SELECT channel_id, msg_id, date, text FROM tg_posts WHERE text IS NOT NULL AND length(text) > 10")
    n_posts = 0
    for row in rows:
        n_posts += 1
        text = row["text"]
        score = uav_score(text)
        weight = 1 + score  # posts with more UAV-context terms count for more

        # A post that names both an entity and its own ИНН/ОГРН is a much
        # stronger candidate than a bare name mention — the identifier is
        # already sitting right next to the name, no separate EGRUL lookup
        # needed to pin it down. Boost entity weight in that case.
        has_id = bool(RE_INN.search(text) or RE_OGRN.search(text))
        entity_weight = weight * 2 if has_id else weight

        for m in RE_ENTITY_QUOTED.finditer(text):
            prefix, name = m.group(1), m.group(2).strip()
            key = norm(name)
            if len(key) < 2:
                continue
            record(entities, key, f"{prefix} «{name}»", row["channel_id"], row["msg_id"], row["date"], entity_weight)

        for m in RE_ENTITY_BARE.finditer(text):
            prefix, name = m.group(1), m.group(2).strip()
            key = norm(name)
            if len(key) < 2:
                continue
            record(entities, key, f"{prefix} {name}", row["channel_id"], row["msg_id"], row["date"], entity_weight)

        if score >= 1:  # only mine bare product names from UAV-relevant posts — too noisy otherwise
            for m in RE_QUOTED_NAME.finditer(text):
                name = m.group(1).strip()
                if is_noise_quote(name):
                    continue
                key = norm(name)
                if len(key) < 2 or key.isdigit():
                    continue
                record(products, key, f"«{name}»", row["channel_id"], row["msg_id"], row["date"], weight)

        for m in RE_ROLE_NAME.finditer(text):
            name = m.group(1).strip()
            key = norm(name)
            if len(key) < 4:
                continue
            record(people, key, name, row["channel_id"], row["msg_id"], row["date"], weight)

        for m in RE_INN.finditer(text):
            key = m.group(1)
            record(inns, key, key, row["channel_id"], row["msg_id"], row["date"], weight)

        for m in RE_OGRN.finditer(text):
            key = m.group(1)
            record(ogrns, key, key, row["channel_id"], row["msg_id"], row["date"], weight)

    brief_text = load_brief_text()
    brief_words = set(brief_text.split())

    def rank(bucket, min_score):
        items = []
        for key, rec in bucket.items():
            n_channels = len(set(h[0] for h in rec["hits"]))
            freq = len(rec["hits"])
            relevance = rec["score"] * (1 + 0.5 * (n_channels - 1))
            if relevance < min_score:
                continue
            if bucket is people:
                # People match on word-set, not substring: the brief writes
                # full names with a patronymic ("Нина Олеговна Яныкина") but
                # RE_ROLE_NAME only ever captures bare first+last, so a
                # substring check never lines up. Order-independent whole-
                # word membership catches this (and last-first orderings)
                # at the cost of being slightly looser than exact-phrase.
                words = [w for w in key.split() if len(w) > 1]
                in_brief = bool(words) and all(w in brief_words for w in words)
            else:
                in_brief = bool(key) and key in brief_text
            items.append((relevance, freq, n_channels, in_brief, key, rec))
        items.sort(key=lambda x: -x[0])
        return items

    def fmt_section(title, items, top):
        lines = [f"## {title}", ""]
        new_items = [it for it in items if not it[3]][:top]
        known_items = [it for it in items if it[3]][:20]
        lines.append(f"### Not yet in the brief ({len(new_items)} of {len([i for i in items if not i[3]])} shown)")
        lines.append("")
        for relevance, freq, n_ch, _, key, rec in new_items:
            example = rec["hits"][0]
            ch_title = chans.get(example[0], str(example[0]))
            lines.append(
                f"- **{rec['display']}** — score {relevance:.1f}, {freq}x across {n_ch} channel(s), "
                f"e.g. {ch_title} msg {example[1]} ({example[2][:10]})"
            )
        lines.append("")
        lines.append(f"### Already in the brief (sample, {len(known_items)} shown) — for sanity-checking the matcher")
        lines.append("")
        for relevance, freq, n_ch, _, key, rec in known_items:
            lines.append(f"- {rec['display']} — score {relevance:.1f}, {freq}x")
        lines.append("")
        return "\n".join(lines)

    out = []
    out.append(f"# Lead-mining report — {n_posts} posts scanned across {len(chans)} channels\n")
    out.append(fmt_section("Corporate entities (АО/ООО/НПЦ/etc.)", rank(entities, args.min_score), args.top))
    out.append(fmt_section("Product/brand names (« »)", rank(products, args.min_score), args.top))
    out.append(fmt_section("Named individuals (role + name)", rank(people, args.min_score), args.top))
    out.append(fmt_section("ИНН sightings", rank(inns, 1), args.top))
    out.append(fmt_section("ОГРН sightings", rank(ogrns, 1), args.top))

    report = "\n".join(out)
    if args.out:
        args.out.write_text(report, encoding="utf-8")
        print(f"Wrote {args.out}")
    else:
        print(report)


if __name__ == "__main__":
    main()
