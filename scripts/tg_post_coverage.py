#!/usr/bin/env python3
"""Find Telegram posts that name a registry entity but are not archived or reviewed.

**Why this exists.** On 2026-09-30 three posts in АНО «ЦБСТ»'s own channel (1562, 1976,
2095) named «Архангел» and sat in `data/roymarket.db` for weeks while the registry said
"no ЦБСТ tie" and "not confirmed in this channel search". Four separate failures stacked:
an evidence sweep sliced to `[:3]` with no text printed; `lower(text) LIKE` in SQLite,
which does not fold Cyrillic, returned 0; the search used the legal-name variant
(«архангел-центр») where the channel only writes the bare brand; and the post's own
`links` column (the eur-lex act) was never read. See memory
`feedback_sqlite_cyrillic_and_truncated_hit_lists`.

So this script makes "does the channel say X?" a query with guard rails, not a recollection:

  * Matching is done in Python on text folded for case and ё/е, with Russian case endings
    allowed after the stem (Архангел / Архангела / Архангелом). Never SQL `lower()`/`LIKE`.
  * Nothing is truncated silently. A cap only applies when you pass `--max`, and then the
    output says how many hits it is not showing.
  * A positive control runs first on every invocation: known words are pulled out of real
    posts and must be found by the same matcher. If it fails, the run aborts (exit 2) and
    every "0 hits" is untrustworthy.
  * Every hit shows the post's `links` field, because a post can carry its primary
    document as a link rather than in its text.
  * A hit is classed against what the registry holds: ARCHIVED (a TGPOST/TGWEB source
    file for that exact channel+msg exists), CITED (the registry names the post in prose
    but no file is archived), or UNSEEN. A human closes an entity with a dated
    `cbst_channel_review` (same idea as `zakupki_review`): posts_read lists the msg ids
    actually read, so a reviewed hit stops being reported and "checked, nothing" is
    distinguishable from "never looked".

Local processing over `data/roymarket.db` and `data/registry/*.json` -- no network. The
default scope is one channel (ЦБСТ); `--all-channels` scans all 328k posts and takes about
a minute (say so before running it in a session).

Usage:
    python3 scripts/tg_post_coverage.py                       # ЦБСТ: posts naming a registry entity, unarchived
    python3 scripts/tg_post_coverage.py --slug ooo-arkhangel  # one entity
    python3 scripts/tg_post_coverage.py --term "Архангел"     # ad hoc: EVERY hit, with links
    python3 scripts/tg_post_coverage.py --term "Квадросим" --all-channels
    python3 scripts/tg_post_coverage.py --check               # exit 1 if a contradiction is unreviewed
    python3 scripts/tg_post_coverage.py --include-archived --out report.md

Read the report as a work queue. A term hit is a lead: «Орион» in a post may not be the
registry's Орион. The fix for a false lead is a `cbst_channel_review` with outcome
`namesake`, not deleting the term.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DB = REPO / "data" / "roymarket.db"
REGISTRY = REPO / "data" / "registry"
SOURCES = REPO / "data" / "sources"
CBST_CHANNEL_ID = 2159491523

LEGAL_FORMS = (
    "общество с ограниченной ответственностью", "акционерное общество",
    "закрытое акционерное общество", "публичное акционерное общество",
    "автономная некоммерческая организация", "индивидуальный предприниматель",
    "научно-производственное предприятие", "научно-производственный центр",
    "научно-производственное объединение", "федеральное государственное унитарное предприятие",
)
LEGAL_ABBR = {"ооо", "ао", "зао", "пао", "оао", "ип", "ано", "нпо", "нпп", "нпц", "нпк", "кб", "фгуп",
              "ано", "нко", "фонд", "ассоциация", "группа", "компания", "гк"}
# Words too generic to mean one entity even when they survive stripping.
STOP_TERMS = {"центр", "системы", "технологии", "технологий", "беспилотные", "беспилотных",
              "россия", "проект", "завод", "институт", "лаборатория", "союз", "платформа",
              "аэро", "авиа", "драйв", "тех", "про", "групп"}
# Case endings only, so «Архангел» matches Архангела/Архангелом but not Архангельск.
SUFFIX = r"(?:ами|ями|ов|ев|ей|ом|ем|ой|ою|ах|ях|ам|ям|а|я|у|ю|е|ы|и|ь)?"
WORD_L = r"(?<![0-9a-zа-я])"
WORD_R = r"(?![0-9a-zа-я])"
# A term matched in more than this share of a channel's posts (and at least GENERIC_MIN
# posts) is reported as generic noise, not as a per-entity lead.
GENERIC_SHARE, GENERIC_MIN = 0.015, 25


def fold(s: str) -> str:
    return (s or "").lower().replace("ё", "е")


def term_regex(term: str) -> re.Pattern:
    """Case/ё-folded, ending-tolerant, word-bounded pattern for a (possibly multi-word) term."""
    parts = [re.escape(p) for p in re.split(r"[\s\-–—]+", fold(term)) if p]
    body = r"[\s\-–—]+".join(p + SUFFIX for p in parts)
    return re.compile(WORD_L + body + WORD_R)


def clean_name(raw: str, min_len: int = 5) -> list[str]:
    """Distinctive search terms from a registry name string."""
    out = []
    for chunk in re.split(r"\s+\|\s+|\s+/\s+", raw or ""):
        quoted = re.findall(r"[«\"“]([^»\"”]+)[»\"”]", chunk)
        cand = quoted or [chunk]
        for c in cand:
            c = re.sub(r"\(.*?\)", " ", c)
            low = fold(c)
            for lf in LEGAL_FORMS:
                low = low.replace(lf, " ")
            words = [w for w in re.split(r"[\s]+", low) if w]
            while words and words[0] in LEGAL_ABBR:
                words = words[1:]
            t = " ".join(words).strip(" .,-«»\"“”'")
            if len(t) >= min_len and t not in STOP_TERMS and not t.isdigit():
                out.append(t)
    return out


def skipped_short_terms(entities: list[dict]) -> dict[str, list[str]]:
    """Brands of 3-4 letters (Овод, Гром) are not searched - too many false hits - so the
    report lists them rather than letting the omission pass unnoticed."""
    out: dict[str, list[str]] = defaultdict(list)
    for e in entities:
        if e.get("_merged_into") or e.get("tier") == "cbst-core":
            continue
        short = {x for raw in (e.get("name_ru"), e.get("brand_ru")) for x in clean_name(raw or "", 3)
                 if len(x) < 5}
        for x in short:
            out[x].append(e["slug"])
    return out


def entity_terms(e: dict) -> set[str]:
    terms: set[str] = set()
    for raw in (e.get("name_ru"), e.get("brand_ru")):
        terms.update(clean_name(raw or ""))
    for h in e.get("name_history") or []:
        terms.update(clean_name(h.get("value") or ""))
    return terms


# --- corpus ---------------------------------------------------------------------------

def load_posts(channel_ids: list[int] | None):
    if not DB.exists():
        sys.exit(f"{DB} missing - this check needs the local scrape.")
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    q = ("select channel_id,msg_id,date,text,links,is_forward,fwd_channel_username "
         "from tg_posts where text is not null")
    args: tuple = ()
    if channel_ids:
        q += " and channel_id in (%s)" % ",".join("?" * len(channel_ids))
        args = tuple(channel_ids)
    rows = [r + (fold(r[3]),) for r in con.execute(q, args).fetchall()]   # folded once, index 7
    chans = {r[0]: (r[1], r[2]) for r in con.execute("select id,username,title from tg_channels")}
    con.close()
    return rows, chans


def resolve_channel(name: str, chans: dict) -> int:
    if name.isdigit():
        return int(name)
    for cid, (user, title) in chans.items():
        if user and user.lower() == name.lower().lstrip("@"):
            return cid
    sys.exit(f"unknown channel {name!r}")


# --- what the registry already holds --------------------------------------------------

HEADER_PATTERNS = (
    re.compile(r"channel_id\s+(\d+),\s*msg_id\s+(\d+)"),
    re.compile(r"\b(\d{9,11}):(\d+)\b"),
)


def archived_posts(chans: dict) -> dict[tuple[int, int], str]:
    """(channel_id, msg_id) -> source path, for every TGPOST/TGWEB file in sources.json."""
    by_user = {(u or "").lower(): cid for cid, (u, _) in chans.items() if u}
    found: dict[tuple[int, int], str] = {}
    for s in json.load(open(REGISTRY / "sources.json", encoding="utf-8")):
        name = s["path"].split("/")[-1]
        if not re.match(r"(TGPOST|TGWEB)_", name):
            continue
        key = None
        f = SOURCES / name
        if f.exists():
            head = f.read_text(encoding="utf-8", errors="ignore")[:600]
            for pat in HEADER_PATTERNS:
                m = pat.search(head)
                if m:
                    key = (int(m.group(1)), int(m.group(2)))
                    break
        if key is None:
            m = re.match(r"(?:TGPOST|TGWEB)_\d{8}_(.+?)(?:_msg)?-?(\d+)(?:-|\.)", name)
            if m and m.group(1).lower() in by_user:
                key = (by_user[m.group(1).lower()], int(m.group(2)))
        if key:
            found[key] = s["id"]
    return found


def registry_blob() -> str:
    parts = []
    for n in ("entities.json", "people.json", "open_questions.json", "quotes.json"):
        p = REGISTRY / n
        if p.exists():
            parts.append(p.read_text(encoding="utf-8"))
    return "\n".join(parts)


def prose_cited(blob: str, chans: dict) -> set[tuple[int, int]]:
    """Posts the registry names in prose: `channel_id:msg`, t.me/<user>/<msg>, or
    `<channel> ... post/msg N` close together. Medium-strength only, reported as CITED."""
    out: set[tuple[int, int]] = set()
    for m in re.finditer(r"\b(\d{9,11}):(\d+)\b", blob):
        out.add((int(m.group(1)), int(m.group(2))))
    by_user = {(u or "").lower(): cid for cid, (u, _) in chans.items() if u}
    for m in re.finditer(r"t\.me/(?:s/)?([A-Za-z0-9_]+)/(\d+)", blob):
        cid = by_user.get(m.group(1).lower())
        if cid:
            out.add((cid, int(m.group(2))))
    for m in re.finditer(r"(?:ANO_CBST|ano_cbst|ЦБСТ)[^.\n\\]{0,80}?(?:post|msg_id|msg|пост)[ _]*(\d{2,5})\b", blob):
        out.add((CBST_CHANNEL_ID, int(m.group(1))))
    return out


def reviewed_posts(entities: list[dict]) -> dict[str, set[int]]:
    return {e["slug"]: {int(x) for x in (e.get("cbst_channel_review") or {}).get("posts_read", [])}
            for e in entities if e.get("cbst_channel_review")}


# --- search ---------------------------------------------------------------------------

PRIMARY_DOC_LINK = re.compile(r"eur-lex|europa\.eu|rospatent|fips\.ru|zakupki|egrul|nalog\.ru|"
                              r"kad\.arbitr|consultant\.ru|publication\.pravo|sanctions|\.pdf", re.I)


def snippet(text: str, m: re.Match, w: int = 110) -> str:
    # `fold` keeps string length (ё->е, lower()) for Cyrillic, so offsets map back to the original.
    # (Checked in the test suite; if it ever changes, snippets would drift, matching would not.)
    a, b = max(0, m.start() - w), min(len(text), m.end() + w)
    return re.sub(r"\s+", " ", text[a:b]).strip()


def search_posts(rows, pattern: re.Pattern, needle: str | None = None):
    """Yield (row, match) for every post whose folded text matches. `needle` is a plain
    substring every match must contain; it is only a speed prefilter (a substring test is
    ~50x cheaper than the regex) and never changes what matches."""
    for r in rows:
        if needle and needle not in r[7]:
            continue
        m = pattern.search(r[7])
        if m:
            yield r, m


def search_term(rows, term: str):
    first = [p for p in re.split(r"[\s\-–—]+", fold(term)) if p][0]
    return search_posts(rows, term_regex(term), first)


def positive_control(rows, n: int = 8) -> tuple[bool, str]:
    """Pull a distinctive word out of real posts and require the matcher to find that post."""
    cands = [r for r in rows if r[3] and re.search(r"[А-ЯЁ][а-яё]{6,}", r[3])]
    if not cands:
        return False, "corpus has no Cyrillic posts"
    step = max(1, len(cands) // n)
    tried = ok = 0
    for r in cands[::step][:n]:
        word = re.findall(r"[А-ЯЁ][а-яё]{6,}", r[3])[0]
        tried += 1
        pat = term_regex(word)
        if any(x[0] == r[0] and x[1] == r[1] for x, _ in search_posts([r], pat)) and \
           pat.search(fold(word.upper())) and pat.search(fold(word.lower())):
            ok += 1
    return ok == tried, f"control: {ok}/{tried} known words found (capital, lower and UPPER forms)"


def classify(key, archived, cited, reviewed_ids):
    if key[1] in reviewed_ids:
        return "REVIEWED"
    if key in archived:
        return "ARCHIVED"
    if key in cited:
        return "CITED"
    return "UNSEEN"


def tie_state(e: dict) -> str:
    c = ((e.get("cbst_tie") or {}).get("confidence")) or "none"
    return c if c in ("t-doc", "t-open", "press") else "no-tie"


def scan(rows, chans, entities, scope_label, slug_filter=None):
    archived = archived_posts(chans)
    cited = prose_cited(registry_blob(), chans)
    reviewed = reviewed_posts(entities)
    term_slugs: dict[str, set[str]] = defaultdict(set)
    by_slug = {e["slug"]: e for e in entities}
    for e in entities:
        if e.get("_merged_into") or e.get("tier") == "cbst-core":
            continue
        if slug_filter and e["slug"] != slug_filter:
            continue
        for t in entity_terms(e):
            term_slugs[t].add(e["slug"])
    hits = []
    generic = []
    n_posts = len(rows)
    for term, slugs in sorted(term_slugs.items()):
        found = list(search_term(rows, term))
        if not found:
            continue
        if len(found) >= max(GENERIC_MIN, GENERIC_SHARE * n_posts) and not slug_filter:
            generic.append((term, len(found), sorted(slugs)))
            continue
        for r, m in found:
            key = (r[0], r[1])
            ids = set()
            for s in slugs:
                ids |= reviewed.get(s, set())
            st = classify(key, archived, cited, ids)
            hits.append({"term": term, "slugs": sorted(slugs), "channel": chans.get(r[0], (str(r[0]),))[0],
                         "msg_id": r[1], "date": (r[2] or "")[:10], "status": st,
                         "source": archived.get(key), "forward_of": r[6] if r[5] else None,
                         "links": json.loads(r[4]) if r[4] else [],
                         "snippet": snippet(r[3], m), "tie_states": sorted({tie_state(by_slug[s]) for s in slugs})})
    return hits, generic


def contradictions(hits):
    """Class A (no tie on file): the channel names a term whose every candidate entity has no recorded tie,
    and the post is neither archived, cited nor reviewed."""
    return [h for h in hits if h["status"] == "UNSEEN" and set(h["tie_states"]) == {"no-tie"}]


# --- hook for check_registry.py --------------------------------------------------------

REVIEW_OUTCOMES = {"namesake", "named_no_tie", "tie_wired", "lead_open"}


def review_problems(entities: list[dict]) -> list[str]:
    """Shape errors in `cbst_channel_review` (`{as_of, outcome, posts_read:[msg ids], note}`)."""
    bad = []
    for e in entities:
        r = e.get("cbst_channel_review")
        if r is None:
            continue
        who = e.get("slug")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(r.get("as_of") or "")):
            bad.append(f"{who}: cbst_channel_review.as_of must be YYYY-MM-DD")
        if r.get("outcome") not in REVIEW_OUTCOMES:
            bad.append(f"{who}: cbst_channel_review.outcome must be one of {sorted(REVIEW_OUTCOMES)}")
        pr = r.get("posts_read")
        if not isinstance(pr, list) or not pr or not all(isinstance(x, int) for x in pr):
            bad.append(f"{who}: cbst_channel_review.posts_read must be a non-empty list of integer msg ids "
                       "(the posts actually read - a review with no posts read is not a review)")
        if not (r.get("note") or "").strip():
            bad.append(f"{who}: cbst_channel_review.note is required (what the posts say about this entity)")
    return bad


def registry_warnings(entities: list[dict]) -> tuple[list[str], list[str]]:
    """(errors, warnings) for check_registry.py. One warning per term whose ЦБСТ-channel hits
    are unarchived, uncited and unreviewed while the registry records no ЦБСТ tie."""
    errors = review_problems(entities)
    if not DB.exists():
        return errors, ["tg_post_coverage: data/roymarket.db absent - ЦБСТ channel coverage not checked"]
    rows, chans = load_posts([CBST_CHANNEL_ID])
    ok, msg = positive_control(rows)
    if not ok or not rows:
        return errors + [f"tg_post_coverage positive control failed ({msg}); ЦБСТ coverage results untrustworthy"], []
    hits, _ = scan(rows, chans, entities, "ANO_CBST")
    by_term = defaultdict(list)
    for h in contradictions(hits):
        by_term[h["term"]].append(h)
    warns = []
    for term, hs in sorted(by_term.items()):
        msgs = ", ".join(str(h["msg_id"]) for h in hs)
        warns.append(f"ЦБСТ's own channel names «{term}» in {len(hs)} unreviewed post(s) ({msgs}) but "
                     f"{'/'.join(hs[0]['slugs'])} has no ЦБСТ tie on file - read them, then record a "
                     f"cbst_channel_review or a tie (python3 scripts/tg_post_coverage.py --slug {hs[0]['slugs'][0]})")
    return errors, warns


# --- output ---------------------------------------------------------------------------

def render(hits, generic, include_archived, max_n, control_msg, scope_label, skipped=None):
    out = [f"# Telegram post coverage - {scope_label}", "", control_msg, ""]
    order = {"UNSEEN": 0, "CITED": 1, "ARCHIVED": 2, "REVIEWED": 3}
    shown = [h for h in hits if include_archived or h["status"] in ("UNSEEN", "CITED")]
    a = contradictions(hits)
    out.append(f"{len(hits)} term hits; {len(shown)} need a look "
               f"({sum(h['status'] == 'UNSEEN' for h in hits)} unseen, "
               f"{sum(h['status'] == 'CITED' for h in hits)} cited in prose without an archived file, "
               f"{sum(h['status'] == 'ARCHIVED' for h in hits)} archived, "
               f"{sum(h['status'] == 'REVIEWED' for h in hits)} reviewed). "
               f"**{len(a)} name an entity the registry records no ЦБСТ tie for** (the class where a miss changes a finding).")
    out.append("")
    by_term = defaultdict(list)
    for h in shown:
        by_term[h["term"]].append(h)

    def prio(item):
        term, hs = item
        return (0 if any(h in a for h in hs) else 1, -len(hs), term)
    total_hidden = 0
    for term, hs in sorted(by_term.items(), key=prio):
        hs.sort(key=lambda h: (order[h["status"]], h["date"]))
        tag = "NO-TIE-ON-FILE" if any(h in a for h in hs) else "gap"
        out.append(f"## «{term}» - {len(hs)} post(s) [{tag}] -> {', '.join(hs[0]['slugs'])}; "
                   f"tie on file: {'/'.join(hs[0]['tie_states'])}")
        for i, h in enumerate(hs):
            if max_n and i >= max_n:
                out.append(f"- ... {len(hs) - max_n} more hit(s) for this term NOT SHOWN (--max {max_n})")
                total_hidden += len(hs) - max_n
                break
            fwd = f" fwd:{h['forward_of']}" if h["forward_of"] else ""
            doc = [l for l in h["links"] if PRIMARY_DOC_LINK.search(l)]
            lk = f" | links: {', '.join(h['links'])}" if h["links"] else ""
            flag = " **PRIMARY-DOC LINK**" if doc else ""
            src = f" {h['source']}" if h["source"] else ""
            out.append(f"- {h['channel']}/{h['msg_id']} {h['date']} [{h['status']}{src}]{fwd}{flag}{lk}")
            out.append(f"    {h['snippet']}")
        out.append("")
    if generic:
        out.append("## Generic terms (too common to attribute; counts only, not hidden leads - rerun with --term)")
        for term, n, slugs in sorted(generic, key=lambda x: -x[1]):
            out.append(f"- «{term}»: {n} posts -> {', '.join(slugs)}")
    if skipped:
        out.append("")
        out.append("## Not searched (brand under 5 letters; search by hand with --term)")
        out.append(", ".join(f"«{k}» ({', '.join(v)})" for k, v in sorted(skipped.items())))
    return "\n".join(out), total_hidden


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--channel", action="append", help="username or id (repeatable); default ЦБСТ")
    ap.add_argument("--all-channels", action="store_true", help="scan all channels (~1 minute)")
    ap.add_argument("--term", help="ad hoc search: print EVERY hit with links, no registry matching")
    ap.add_argument("--slug", help="only this entity's terms")
    ap.add_argument("--include-archived", action="store_true")
    ap.add_argument("--max", type=int, default=0, help="cap hits per term (announced when it bites); default no cap")
    ap.add_argument("--check", action="store_true", help="exit 1 if an unreviewed contradiction exists")
    ap.add_argument("--out")
    args = ap.parse_args()

    rows0, chans = load_posts(None if args.all_channels else [CBST_CHANNEL_ID])
    if args.channel and not args.all_channels:
        ids = [resolve_channel(c, chans) for c in args.channel]
        rows0, _ = load_posts(ids)
    rows = rows0
    scope = "all channels" if args.all_channels else ", ".join(
        (chans.get(c, (str(c),))[0] or str(c)) for c in sorted({r[0] for r in rows})) or "empty scope"
    ok, control_msg = positive_control(rows)
    if not ok or not rows:
        print(f"ABORT: positive control failed ({control_msg}); results would be untrustworthy.", file=sys.stderr)
        return 2
    control_msg = f"{len(rows)} posts in scope ({scope}); {control_msg}."

    if args.term:
        found = list(search_term(rows, args.term))
        archived = archived_posts(chans)
        lines = [control_msg, f"«{args.term}»: {len(found)} hit(s), all shown."]
        for r, m in sorted(found, key=lambda x: x[0][2] or ""):
            key = (r[0], r[1])
            lk = json.loads(r[4]) if r[4] else []
            st = "ARCHIVED " + archived[key] if key in archived else "not archived"
            lines.append(f"- {chans.get(r[0], (str(r[0]),))[0]}/{r[1]} {(r[2] or '')[:10]} [{st}]"
                         + (f" links: {', '.join(lk)}" if lk else ""))
            lines.append(f"    {snippet(r[3], m, 160)}")
        print("\n".join(lines))
        return 0

    entities = json.load(open(REGISTRY / "entities.json", encoding="utf-8"))
    hits, generic = scan(rows, chans, entities, scope, args.slug)
    text, hidden = render(hits, generic, args.include_archived, args.max, control_msg, scope,
                          skipped_short_terms(entities))
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(text)
    bad = contradictions(hits)
    if args.check:
        print(f"\ncheck: {len(bad)} unreviewed contradiction(s)", file=sys.stderr)
        return 1 if bad else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
