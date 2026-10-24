#!/usr/bin/env python3
"""Inventory of the Telegram channels and websites the registry records for each entity, with gaps flagged.

Local processing over `data/registry/entities.json`, `config/channels.txt`, `data/roymarket.db` and
the filenames in `data/sources/`; no network. It reports what the registry *records*, not whether a
site is alive: a link check is a network job at scale and is handed to the user.

Gaps flagged (per entity):
  NO-PRESENCE      no site, Telegram, VK or YouTube on file (a search may still have been done: read the open questions)
  TG-NOT-SCRAPED   Telegram URL on file, channel absent from the DB (the user runs tg_scan.py; add to config/channels.txt first)
  TG-NOT-ON-LIST   channel is in the DB but not in config/channels.txt (refresh would skip it)
  TG-EMPTY         channel in the DB with 0 posts
  TG-BAD-URL       a Telegram entry with no usable handle (private invite, numeric id, or missing url)
  TG-BOT           a bot account (not scrapeable as a channel; listed so it is not mistaken for a gap)
  SITE-NOT-ARCHIVED site on file, no WEB_/SITE_/WEBCAPTURE_/CATALOG_/TGWEB_ capture keyed by the entity's ИНН in data/sources/
  (sibling note) a NO-PRESENCE entity whose `related_entities` names a same-brand or group sibling that has a site or Telegram is
                   annotated with that sibling. Added 2026-10-01 after ООО «Ушкуйник» was searched as a gap while the brand's site and
                   channel sit on the АНО. The note is a pointer, not an attribution: a sibling's site is never recorded as this entity's.
And one global list: channels in the DB that no entity links to.

Usage:
    python3 scripts/entity_presence_inventory.py                 # summary to stdout
    python3 scripts/entity_presence_inventory.py --out notes/entity_presence_inventory.md
    python3 scripts/entity_presence_inventory.py --tier manufacturer --tie    # filter
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_PREFIXES = ("WEB_", "SITE_", "WEBCAPTURE_", "CATALOG_", "TGWEB_")
TIE = {"t-doc", "t-open", "press"}
SIBLING_TYPES = {"same-name-different-entity", "group-structure", "sister-entity", "parent", "subsidiary", "successor", "predecessor"}


def handle(url) -> str | None:
    """Telegram handle from a URL or @name; None for invites, numeric ids, missing."""
    if not url or not isinstance(url, str):
        return None
    u = url.strip()
    m = re.match(r"^@([A-Za-z0-9_]{4,})$", u)
    if m:
        return m.group(1).lower()
    p = urlparse(u if "//" in u else "https://" + u)
    if "t.me" not in p.netloc and "telegram.me" not in p.netloc:
        return None
    parts = [x for x in p.path.split("/") if x]
    if not parts or parts[0].startswith("+") or parts[0] in ("joinchat", "c"):
        return None
    return parts[0].lower().lstrip("@")


def entity_list():
    E = json.loads((ROOT / "data/registry/entities.json").read_text(encoding="utf-8"))
    return E if isinstance(E, list) else (list(E["entities"].values()) if isinstance(E.get("entities"), dict) else E["entities"])


def watchlist() -> set[str]:
    out = set()
    for ln in (ROOT / "config/channels.txt").read_text(encoding="utf-8").splitlines():
        ln = ln.split("#")[0].strip()
        if ln:
            h = handle(ln if ln.startswith("@") or "t.me" in ln else "@" + ln)
            if h:
                out.add(h)
    return out


def db_channels():
    con = sqlite3.connect(f"file:{ROOT / 'data/roymarket.db'}?mode=ro", uri=True)
    posts = dict(con.execute("select channel_id,count(*) from tg_posts group by channel_id"))
    return {(u or "").lower(): (cid, t, posts.get(cid, 0)) for cid, u, t in con.execute("select id,username,title from tg_channels")}


def people_handles() -> set[str]:
    """Telegram handles recorded on person records (`social` entries)."""
    P = json.loads((ROOT / "data/registry/people.json").read_text(encoding="utf-8"))
    PL = P if isinstance(P, list) else (list(P["people"].values()) if isinstance(P.get("people"), dict) else P["people"])
    out = set()
    for pr in PL:
        for so in pr.get("social") or []:
            if isinstance(so, str):
                h = handle(so)
            elif str(so.get("platform", "")).lower() == "telegram" or "t.me" in str(so.get("url", "")):
                h = handle(so.get("url") or so.get("handle"))
            else:
                h = None
            if h:
                out.add(h)
    return out


def archived_inns() -> set[str]:
    out = set()
    for p in (ROOT / "data/sources").iterdir():
        if p.name.startswith(ARCHIVE_PREFIXES):
            m = re.match(r"^[A-Z]+_(\d{10,13})_", p.name)
            if m:
                out.add(m.group(1))
    return out


def urls(web, key):
    out = []
    for x in (web or {}).get(key) or []:
        out.append(x if isinstance(x, str) else ((x or {}).get("url") or (x or {}).get("handle")))
    return out


def inventory():
    wl, dbc, arch = watchlist(), db_channels(), archived_inns()
    rows, linked = [], set()
    for e in entity_list():
        if e.get("_merged_into"):
            continue   # tombstone of a merged duplicate (e.g. bulat-3mx -> ooo-trimiks): the canonical record carries the presence
        w = e.get("web") or {}
        sites = [u for k in ("sites", "official_sites") for u in urls(w, k) if u]
        tgs = urls(w, "telegram")
        chat_urls = {(x.get("url") or x.get("handle")) for x in w.get("telegram") or []
                     if isinstance(x, dict) and "chat" in (x.get("note") or "").lower()[:40]}
        vk, yt = [u for u in urls(w, "vk") if u], [u for u in urls(w, "youtube") if u]
        flags, handles = [], []
        for u in tgs:
            h = handle(u)
            if not h:
                if u not in chat_urls:        # a private users' chat is recorded on purpose, not a defect
                    flags.append("TG-BAD-URL")
                continue
            if h.endswith("_bot") or h.endswith("bot"):
                flags.append(f"TG-BOT:{h}")
                continue
            handles.append(h)
            linked.add(h)
            if h not in dbc:
                flags.append(f"TG-NOT-SCRAPED:{h}")
            else:
                if h not in wl:
                    flags.append(f"TG-NOT-ON-LIST:{h}")
                if dbc[h][2] == 0:
                    flags.append(f"TG-EMPTY:{h}")
        if not (sites or tgs or vk or yt):
            flags.append("NO-PRESENCE")
        if sites and not (e.get("inn") in arch):
            flags.append("SITE-NOT-ARCHIVED")
        rows.append({"slug": e["slug"], "name": e.get("name_ru"), "inn": e.get("inn"), "tier": e.get("tier"),
                     "tie": (e.get("cbst_tie") or {}).get("confidence") in TIE,
                     "sites": sites, "tg": handles, "vk": vk, "yt": yt, "flags": flags})
    linked |= people_handles()
    by_slug = {r["slug"]: r for r in rows}
    ents = {e["slug"]: e for e in entity_list()}
    for r in rows:
        if "NO-PRESENCE" not in r["flags"]:
            continue
        sib = []
        for rel in ents[r["slug"]].get("related_entities") or []:
            o = by_slug.get(rel.get("slug"))
            if o and (o["sites"] or o["tg"]) and rel.get("relationship_type") in SIBLING_TYPES:
                sib.append(f"{o['slug']} ({rel['relationship_type']}: {', '.join(o['sites'][:1] + ['@' + h for h in o['tg'][:1]])})")
        r["siblings"] = sib
    unlinked = sorted(((h, dbc[h][1], dbc[h][2]) for h in dbc if h and h not in linked), key=lambda x: -x[2])
    return rows, unlinked


def render(rows, unlinked):
    n = len(rows)
    c = Counter(f.split(":")[0] for r in rows for f in r["flags"])
    L = [f"# Entity web and Telegram presence inventory", "",
         f"{n} entities. Records what the registry holds; a dead link or a moved channel is not detected here.", "",
         "| Gap | Entities |", "|---|---|"]
    for k in ("NO-PRESENCE", "TG-NOT-SCRAPED", "TG-NOT-ON-LIST", "TG-EMPTY", "TG-BAD-URL", "TG-BOT", "SITE-NOT-ARCHIVED"):
        L.append(f"| {k} | {c.get(k, 0)} |")
    L += ["", f"With a site: {sum(1 for r in rows if r['sites'])}; with Telegram: {sum(1 for r in rows if r['tg'])}; "
          f"with VK: {sum(1 for r in rows if r['vk'])}; with YouTube: {sum(1 for r in rows if r['yt'])}.", ""]
    by = defaultdict(list)
    for r in rows:
        for f in r["flags"]:
            by[f.split(":")[0]].append((r, f))
    titles = {"NO-PRESENCE": "No site, Telegram, VK or YouTube on file",
              "TG-NOT-SCRAPED": "Telegram on file, never scraped (hand to user: add to config/channels.txt, run tg_scan.py)",
              "TG-NOT-ON-LIST": "In the DB but not on the watchlist (a refresh skips it)",
              "TG-EMPTY": "In the DB with 0 posts", "TG-BAD-URL": "Telegram entry without a usable handle", "TG-BOT": "Bot accounts on file (not scrapeable)",
              "SITE-NOT-ARCHIVED": "Site on file, no archived capture keyed by ИНН"}
    order = {"cbst-core": 0, "network": 0, "manufacturer": 1, "money-layer": 2, "plumbing": 3, "adjacent": 4, "unverified": 5}
    for k in ("NO-PRESENCE", "TG-NOT-SCRAPED", "TG-NOT-ON-LIST", "TG-EMPTY", "TG-BAD-URL", "TG-BOT", "SITE-NOT-ARCHIVED"):
        items = sorted(by.get(k, []), key=lambda x: (not x[0]["tie"], order.get(x[0]["tier"], 9), x[0]["slug"]))
        L += [f"## {titles[k]} ({len(items)})", "", "Entities with a ЦБСТ tie are listed first.", ""]
        for r, f in items:
            extra = f" `{f.split(':', 1)[1]}`" if ":" in f else ""
            sib = f" - sibling has presence, not attributed: {'; '.join(r['siblings'])}" if k == "NO-PRESENCE" and r.get("siblings") else ""
            L.append(f"- {'**ЦБСТ-tied** ' if r['tie'] else ''}`{r['slug']}` ({r['tier']}, ИНН {r['inn']}){extra}{sib}")
        L.append("")
    L += [f"## Channels in the DB that no entity or person links to ({len(unlinked)})", "",
          "Channels linked from an entity or from a person record are excluded. Each remaining one is a registry gap or a blog channel; read before linking.", ""]
    for h, t, p in unlinked:
        L.append(f"- `@{h}` {t or ''} ({p} posts)")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out")
    ap.add_argument("--tier")
    ap.add_argument("--tie", action="store_true", help="only entities with a ЦБСТ tie")
    a = ap.parse_args()
    rows, unlinked = inventory()
    if a.tier:
        rows = [r for r in rows if r["tier"] == a.tier]
    if a.tie:
        rows = [r for r in rows if r["tie"]]
    text = render(rows, unlinked)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
        print(f"wrote {a.out}")
    print("\n".join(text.splitlines()[:16]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
