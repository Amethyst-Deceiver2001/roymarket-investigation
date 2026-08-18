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
import re
import sqlite3
import unicodedata
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DB = REPO / "data" / "roymarket.db"
BRIEF = REPO / "docs" / "index.html"

LEGAL_PREFIXES = [
    "ООО", "АО", "ОАО", "ЗАО", "ПАО", "НПО", "НПП", "НПЦ", "КБ", "СКБ",
    "ОКБ", "ОПКБ", "ГК", "ФГУП", "ГУП", "МУП", "АНО", "ИП", "НИИ", "ЦНИИ",
]
PREFIX_ALT = "|".join(LEGAL_PREFIXES)

# Prefix + guillemet/straight-quoted name, e.g. ООО «Архангел», АО "Технодрон"
RE_ENTITY_QUOTED = re.compile(
    rf'\b({PREFIX_ALT})\s*[«"]([^»"]{{2,60}})[»"]'
)
# Prefix + bare capitalized name (1-4 tokens), e.g. НПЦ БАСиРТК, ГК МВС
RE_ENTITY_BARE = re.compile(
    rf'\b({PREFIX_ALT})[ \t]+((?:[А-ЯЁ][А-Яа-яёЁ\-]*[ \t]*){{1,4}})'
)
# Bare guillemet-quoted product/brand name
RE_QUOTED_NAME = re.compile(r'«([^»]{2,45})»')
# ИНН (10 or 12 digits) / ОГРН (13 or 15 digits), anchored to a label
RE_INN = re.compile(r'\bИНН[:\s]*([0-9]{10}|[0-9]{12})\b')
RE_OGRN = re.compile(r'\bОГРН[:\s]*([0-9]{13}|[0-9]{15})\b')
# Role title + a 2-3 word Capitalized name
ROLE_TITLES = [
    "Генеральный директор", "Генеральный[ -]директор", "Учредитель",
    "Директор", "Председатель", "Руководитель", "Основатель",
]
RE_ROLE_NAME = re.compile(
    rf'(?:{"|".join(ROLE_TITLES)})[ \t:—-]+'
    r'([А-ЯЁ][а-яёА-Я]+(?:[ \t]+[А-ЯЁ][а-яёА-Я]+){1,2})'
)

UAV_TERMS = [
    "бпла", "беспилотник", "дрон", "коптер", "квадрокоптер", "октокоптер",
    "гексакоптер", "fpv", "фпв", "рэб", "рэр", "антидрон", "перехватчик",
    "камикадзе", "оптоволокон", "ретранслятор", "автопилот", "тепловизор",
    "целеуказан", "полётный контроллер", "полетный контроллер", "цбст",
    "резидент", "войсковая часть", "полевая почта", "рой.маркет",
    "роймаркет", "минобороны", "мо рф", "техносовет", "техсовет",
]


def norm(name: str) -> str:
    """Normalize an entity/product name for dedup — see [[roymarket_fuzzy_dedup]]."""
    name = unicodedata.normalize("NFKC", name)
    name = name.strip().strip('«»"\'').lower()
    for p in LEGAL_PREFIXES:
        name = re.sub(rf'^{p.lower()}\s+', '', name)
    name = re.sub(r'[^\w\s]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name


def uav_score(text: str) -> int:
    t = text.lower()
    return sum(1 for term in UAV_TERMS if term in t)


def load_brief_text() -> str:
    if not BRIEF.exists():
        return ""
    return norm(BRIEF.read_text(encoding="utf-8"))


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

        for m in RE_ENTITY_QUOTED.finditer(text):
            prefix, name = m.group(1), m.group(2).strip()
            key = norm(name)
            if len(key) < 2:
                continue
            record(entities, key, f"{prefix} «{name}»", row["channel_id"], row["msg_id"], row["date"], weight)

        for m in RE_ENTITY_BARE.finditer(text):
            prefix, name = m.group(1), m.group(2).strip()
            key = norm(name)
            if len(key) < 2:
                continue
            record(entities, key, f"{prefix} {name}", row["channel_id"], row["msg_id"], row["date"], weight)

        if score >= 1:  # only mine bare product names from UAV-relevant posts — too noisy otherwise
            for m in RE_QUOTED_NAME.finditer(text):
                name = m.group(1).strip()
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

    report = "\n".join(out)
    if args.out:
        args.out.write_text(report, encoding="utf-8")
        print(f"Wrote {args.out}")
    else:
        print(report)


if __name__ == "__main__":
    main()
