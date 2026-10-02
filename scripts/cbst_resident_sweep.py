#!/usr/bin/env python3
"""Find ЦБСТ residents the registry does not hold, or holds without a ЦБСТ tie.

Scans every post in `data/roymarket.db` (all channels by default) for the word
«резидент…» used near a ЦБСТ token, pulls the company and product names written beside
it, and classes each against the registry:

  TIE-GAP    an entity/product of ours is named a resident, but its `cbst_tie` is none
  NEW        no entity, brand, alias or product of ours matches the name
  MENTIONED  the name appears in registry prose only (open question, note) - no record
  known      an entity of ours with a ЦБСТ tie (hidden unless --all)

Why the match is strict: `id_patterns.load_known_text` treats a name as "known" if it
appears anywhere in the registry text, which is right for deduplicating mined leads and
wrong here - «SR Space» in an open question is not an entity. Here "known" means an entity
name, brand, name_history value or product name, compared whole (folded for case and ё).

Fixed traps, each one a real miss (see memory feedback_sqlite_cyrillic_and_truncated_hit_lists):
  * «президент» contains the letters «резидент»; the word match is anchored at a word start.
  * ЦБСТ is misspelled in the channel itself («резидент ЦСБТ», post 2041); the ЦБСТ token
    list includes ЦСБТ and ЦБТС, and ЦБСТ's own channel counts as ЦБСТ context by itself.
  * Matching is in Python on folded text, never SQL LIKE/lower().
  * A positive control runs first; nothing is capped unless --max is passed, and then the
    output says what it hides.

Local processing over the DB and registry, no network. Scanning all 328k posts takes about
a minute; `--channel ANO_CBST` takes seconds.

Usage:
    python3 scripts/cbst_resident_sweep.py                    # all channels
    python3 scripts/cbst_resident_sweep.py --channel ANO_CBST
    python3 scripts/cbst_resident_sweep.py --all --out sweep.md
    python3 scripts/cbst_resident_sweep.py --watchlist        # channels worth adding to config/channels.txt

A hit is a lead, not a finding: read the post, archive it (TGPOST), then record a tie or a
`cbst_channel_review`. The candidate extractor takes names from a window around the word, so a
list of residents yields every name in it, and unrelated names nearby can slip in.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tg_post_coverage as T  # noqa: E402
from registry_lookup import key_latin, translit  # noqa: E402
from id_patterns import RE_ENTITY_QUOTED, RE_QUOTED_NAME, is_noise_quote  # noqa: E402

REGISTRY, REPO, CBST = T.REGISTRY, T.REPO, T.CBST_CHANNEL_ID

RESIDENT = re.compile(r"(?<![0-9a-zа-я])резидент[а-я]*")
# --kind accelerator: the ЦБСТ accelerator is how «статус резидента» is granted (cbst.ru/accelerator),
# so finalists, winners and participants are resident candidates even when the post never says «резидент».
ACCELERATOR = re.compile(r"(?<![0-9a-zа-я])акселератор[а-я]*|(?<![0-9a-zа-я])(?:финалист|победител|участник)[а-я]*")
KINDS = {"resident": RESIDENT, "accelerator": ACCELERATOR}
ACTIVE = {"word": RESIDENT, "kind": "resident"}
CBST_TOKENS = re.compile(r"цбст|цсбт|цбтс|центр[а-я]* беспилотных систем|анонс цбст|#резиденты_цбст|\bcbst\b")
DIRECT, NEAR = 110, 300          # chars around the word: direct adjacency / same passage
LATIN_NAME = re.compile(r"\b([A-Z][A-Za-z0-9]{1,}(?:[ \-][A-Z][A-Za-z0-9]{1,}){0,2})\b")
# Names that are not companies: the network's own labels, events, programmes, places, latin jargon.
NOT_A_COMPANY = {T.fold(x) for x in (
    "ЦБСТ", "Центр беспилотных систем и технологий", "Дронница", "Акселератор", "Навигатор", "Народный ВПК",
    "Мулино", "Единая Россия", "Единой России", "СВО", "Яким", "Навигатор мер господдержки", "Резиденты",
    "Минпромторг", "Минобороны", "Гагаринг", "Запад-2025", "Флот-2026", "Форпост", "Орион", "Охотник")}
LATIN_STOP = {"FPV", "UAV", "MAX", "CBST", "OSINT", "GPS", "GNSS", "NATO", "AI", "IT", "DJI", "USA", "EU", "RT",
              "Telegram", "YouTube", "VK", "The", "Russia", "Russian", "Ukraine", "Kalashnikov"}


def match_key(s: str) -> str:
    """Comparison key: legal forms and quotes stripped, punctuation and hyphen spacing ignored,
    Cyrillic transliterated so «Нейри» and «Neiry» meet. («ТИТАН - СЕВЕРО-ЗАПАД» vs
    «Титан Северо-Запад» were different strings until this existed.)"""
    c = T.clean_name(s, 2)
    base = c[0] if c else T.fold(s)
    # y and i are folded together: Нейри transliterates to «neiri», the company writes «Neiry».
    return key_latin(translit(base)).replace("y", "i")


def product_names(e: dict):
    for p in e.get("products") or []:
        name = p if isinstance(p, str) else (p.get("name_ru") or p.get("name") or p.get("name_en") or "")
        if name:
            yield name


def index_registry(entities):
    """folded name -> [(slug, kind, tie_state)] for entity names, brands, history and products."""
    idx: dict[str, list] = defaultdict(list)
    for e in entities:
        if e.get("_merged_into"):
            continue
        tie = T.tie_state(e)
        names = [(n, "entity") for raw in (e.get("name_ru"), e.get("brand_ru"), e.get("name_en"))
                 for n in T.clean_name(raw or "", 3)]
        for h in e.get("name_history") or []:
            names += [(n, "entity") for n in T.clean_name(h.get("value") or "", 3)]
        for pname in product_names(e):
            names += [(T.fold(x.strip(" «»\"")), "product") for x in re.split(r"\s+\|\s+|\s+/\s+", pname) if len(x.strip()) >= 3]
        for n, kind in names:
            if len(n) >= 3:
                idx[match_key(n)].append((e["slug"], kind, tie))
    return idx


def norm_candidate(s: str) -> str:
    return match_key(s)


EVENT_PREP = re.compile(r"(?:на|в|во|по|при|про|после|накануне|для|от|из|у|о|об)\s*$", re.I)
ROMAN = re.compile(r"^[IVXLC]+$")


def candidates(window: str):
    """(name, how, key) triples from a text window."""
    out = []
    for m in RE_ENTITY_QUOTED.finditer(window):
        out.append((f"{m.group(1)} «{m.group(2).strip()}»", "legal"))
    for m in RE_QUOTED_NAME.finditer(window):
        n = m.group(1).strip()
        # «…» right after a preposition names an event, place or publication («на «Дрон Экспо»»),
        # not a company; a company is the subject or apposition («компания «X»»).
        if EVENT_PREP.search(window[max(0, m.start() - 12):m.start()]):
            continue
        if not is_noise_quote(n) and len(n) <= 40 and not n.endswith((".", "!", "?")):
            out.append((n, "quoted"))
    for m in LATIN_NAME.finditer(window):
        n = m.group(1)
        first = n.split()[0]
        if first in LATIN_STOP or n in LATIN_STOP or ROMAN.match(n) or len(n) < 4:
            continue
        if n.isupper() and len(n) <= 5 and " " not in n:     # bare acronyms (DARPA, FCSS): not company leads
            continue
        out.append((n, "latin"))
    seen, res = set(), []
    for n, how in out:
        k = norm_candidate(n)
        if k and k not in seen and k not in NOT_A_COMPANY and not k.isdigit():
            seen.add(k)
            res.append((n, how, k))
    return res


SEGMENT = re.compile(r"(?<=[.!?])\s+|\n+")


def segments(text: str):
    """(start, end) spans of sentences/lines, so a window never crosses a news item's boundary."""
    spans, pos = [], 0
    for m in SEGMENT.finditer(text):
        if m.start() > pos:
            spans.append((pos, m.start()))
        pos = m.end()
    if pos < len(text):
        spans.append((pos, len(text)))
    return spans


def resident_windows(row):
    """For each «резидент…» in a ЦБСТ-context post: (scope_text, direct_text, context).
    scope = the sentence holding the word plus the next one (a headline «Резидент ЦБСТ
    представил…» names the company in the following sentence), and the previous one when the
    sentence itself names nobody."""
    folded, text = row[7], row[3]
    own = row[0] == CBST
    spans = segments(text)
    wins = []
    for m in ACTIVE["word"].finditer(folded):
        i = next((k for k, (a, b) in enumerate(spans) if a <= m.start() < b), None)
        if i is None:
            continue
        near = folded[max(0, m.start() - NEAR):min(len(text), m.end() + NEAR)]
        if not (own or CBST_TOKENS.search(near)):
            continue
        a, b = spans[i]
        scope = text[a:spans[min(i + 1, len(spans) - 1)][1]]
        if not candidates(text[a:b]) and i > 0:
            scope = text[spans[i - 1][0]:spans[min(i + 1, len(spans) - 1)][1]]
        wins.append((scope, text[max(a, m.start() - DIRECT):min(b, m.end() + DIRECT)],
                     text[max(0, m.start() - 160):m.end() + 200]))
    return wins


_BLOB_CACHE: dict[int, str] = {}


def blob_keys(blob: str) -> str:
    """Registry prose in match_key form, computed once."""
    k = id(blob)
    if k not in _BLOB_CACHE:
        _BLOB_CACHE[k] = key_latin(translit(blob)).replace("y", "i")
    return _BLOB_CACHE[k]


def classify(key, idx, blob):
    hits = idx.get(key)
    if hits:
        if any(t in ("t-doc", "t-open", "press") for _, _, t in hits):
            return "known", sorted({s for s, _, _ in hits})
        return "TIE-GAP", sorted({s for s, _, _ in hits})
    if len(key) >= 4 and key in blob_keys(blob):
        return "MENTIONED", []
    return "NEW", []


def sweep(rows, chans, entities):
    idx = index_registry(entities)
    blob = T.fold(T.registry_blob())
    archived = T.archived_posts(chans)
    agg: dict[str, dict] = {}
    n_ctx = 0
    for row in rows:
        if not ACTIVE["word"].search(row[7]):
            continue
        wins = resident_windows(row)
        if not wins:
            continue
        n_ctx += 1
        chan = chans.get(row[0], (str(row[0]),))[0] or str(row[0])
        for near_text, direct_text, ctx in wins:
            direct_keys = {k for _, _, k in candidates(direct_text)}
            for name, how, k in candidates(near_text):
                a = agg.setdefault(k, {"name": name, "how": how, "posts": {}, "direct": 0, "kinds": set()})
                key = (row[0], row[1])
                if key not in a["posts"]:
                    a["posts"][key] = {"chan": chan, "msg": row[1], "date": (row[2] or "")[:10], "ctx": re.sub(r"\s+", " ", ctx),
                                       "archived": archived.get(key), "links": row[4]}
                if k in direct_keys:
                    a["direct"] += 1
                a["kinds"].add(how)
    out = []
    for k, a in agg.items():
        cls, slugs = classify(k, idx, blob)
        a.update(key=k, cls=cls, slugs=slugs, n_posts=len(a["posts"]),
                 n_chans=len({p["chan"] for p in a["posts"].values()}),
                 own=any(p["chan"] == "ANO_CBST" for p in a["posts"].values()))
        out.append(a)
    return out, n_ctx


def render(items, n_ctx, n_rows, control, show_all, max_n, full=False):
    order = {"TIE-GAP": 0, "NEW": 1, "MENTIONED": 2, "known": 3}
    lines = [f"# ЦБСТ {ACTIVE['kind']} sweep", "", control, f"{n_rows} posts scanned; {n_ctx} carry the trigger word next to a ЦБСТ token or sit in ЦБСТ's own channel.", ""]
    counts = {c: sum(1 for i in items if i["cls"] == c) for c in order}
    lines.append("Candidates: " + ", ".join(f"{v} {k}" for k, v in counts.items()) + ".")
    lines.append("")
    hidden = 0
    for cls in order:
        grp = [i for i in items if i["cls"] == cls]
        if cls == "known" and not show_all:
            lines.append(f"## known ({len(grp)}) - hidden, use --all")
            lines.append("")
            continue
        grp.sort(key=lambda i: (-i["direct"], -i["n_chans"], -i["n_posts"], i["key"]))
        lines.append(f"## {cls} ({len(grp)})")
        for n, i in enumerate(grp):
            if max_n and n >= max_n:
                hidden += len(grp) - max_n
                lines.append(f"- ... {len(grp) - max_n} more {cls} candidate(s) NOT SHOWN (--max {max_n})")
                break
            sl = f" -> {', '.join(i['slugs'])}" if i["slugs"] else ""
            lines.append(f"### «{i['name']}» [{i['how']}]{sl} - {i['n_posts']} post(s), {i['n_chans']} channel(s), "
                         f"adjacent to «резидент» {i['direct']}x{', in ЦБСТ own channel' if i['own'] else ''}")
            for p in sorted(i["posts"].values(), key=lambda p: p["date"])[: (None if full else 3)]:
                arch = f" [ARCHIVED {p['archived']}]" if p["archived"] else ""
                lines.append(f"- {p['chan']}/{p['msg']} {p['date']}{arch}: {p['ctx']}")
            if len(i["posts"]) > 3 and not full:
                lines.append(f"- ... {len(i['posts']) - 3} more post(s) for this name (all listed with --full)")
        lines.append("")
    return "\n".join(lines), hidden


def watchlist(rows, chans):
    """Channels that forward a resident/ЦБСТ context but are not on config/channels.txt."""
    listed = {l.strip().lstrip("@").lower() for l in open(REPO / "config" / "channels.txt", encoding="utf-8")
              if l.strip() and not l.startswith("#")}
    hits: dict[str, list] = defaultdict(list)
    for r in rows:
        if not r[5] or not r[6]:
            continue
        if CBST_TOKENS.search(r[7]) and RESIDENT.search(r[7]):
            hits[r[6]].append(r)
    res = [(u, len(v), v[0][1]) for u, v in hits.items() if u.lower() not in listed]
    return sorted(res, key=lambda x: -x[1])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--channel", action="append", help="username or id (repeatable); default all channels")
    ap.add_argument("--all", action="store_true", help="also list known residents")
    ap.add_argument("--full", action="store_true", help="no per-candidate post cap")
    ap.add_argument("--max", type=int, default=0, help="cap candidates per class (announced)")
    ap.add_argument("--watchlist", action="store_true")
    ap.add_argument("--kind", choices=sorted(KINDS), default="resident",
                    help="resident: «резидент…» near ЦБСТ; accelerator: accelerator/finalist/winner mentions")
    ap.add_argument("--out")
    args = ap.parse_args()

    rows, chans = T.load_posts(None)
    if args.channel:
        ids = {T.resolve_channel(c, chans) for c in args.channel}
        rows = [r for r in rows if r[0] in ids]
    ACTIVE["word"] = KINDS[args.kind]
    ACTIVE["kind"] = args.kind
    ok, msg = T.positive_control(rows)
    if not ok or not rows:
        print(f"ABORT: positive control failed ({msg}).", file=sys.stderr)
        return 2
    control = f"{msg}."
    # sanity control specific to this sweep: the matcher must accept the known spellings and reject «президент»
    assert RESIDENT.search("резидент цбст") and RESIDENT.search("резиденты цбст") and not RESIDENT.search("президент рф")
    assert CBST_TOKENS.search("резидент цсбт") and CBST_TOKENS.search("центр беспилотных систем")

    if args.watchlist:
        res = watchlist(rows, chans)
        print(control)
        print(f"{len(res)} forwarding source channel(s) not on config/channels.txt (username, resident-context forwards, sample msg):")
        for u, n, m in res:
            print(f"  @{u}\t{n}\t(msg {m})")
        return 0

    entities = json.load(open(REGISTRY / "entities.json", encoding="utf-8"))
    items, n_ctx = sweep(rows, chans, entities)
    text, hidden = render(items, n_ctx, len(rows), control, args.all, args.max, args.full)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
