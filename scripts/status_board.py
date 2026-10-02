#!/usr/bin/env python3
"""Status board: what is missing, stale or behind for every entity, person,
product and Telegram channel in the investigation.

**Why this exists.** `coverage_report.py` answers "which fields are filled".
It does not say when a record was last pulled, whether a sanctions screen is a
month old, or whether the network posted something last week that the record
does not carry yet. The user asked (02.10.2026) for a way to always know the
status of each entity: a missing registry pull, a record behind on recent
developments, and the like. This script derives that from the repo itself, so
it cannot drift from the registry the way a hand-kept tracker would.

Every flag is a mechanical test stated in this file. A flag is a work item, not
a finding: "no ЕГРЮЛ extract on file" can mean "never pulled" or "pulled under a
file name that does not carry the ИНН". Read the record before acting.

Inputs (all local, no network calls, safe to run repeatedly):
  data/registry/{entities,people,products,sources,open_questions}.json
  config/channels.txt                       the local tg_scan.py watchlist
  --scan-state  weekly_scan_state.json      high-water marks of the weekly scan
  --developments developments.json          findings of the weekly scan

Both scan files live in the project's shared folder (/mnt/project-files/watch/)
and are read from there by default when it exists; on a machine without it,
pass the paths or leave them out and the "behind" flags that need them are
skipped (the output says so).

developments.json shape (written by the weekly scan, one item per finding):
  {"items": [{"id", "found" (YYYY-MM-DD), "url", "channel", "post",
              "about": [slug, ...], "kind": update|contradicts|new|lead,
              "summary", "status": open|recorded|dismissed, "note"}]}
An open item whose channel/post is already in sources.json (tg_post) is shown
as "archived, not yet closed", because archiving a post is not the same as
wiring its fact into the record.

Usage:
  python3 scripts/status_board.py                       # summary to stdout
  python3 scripts/status_board.py --json out.json       # full board for a page
  python3 scripts/status_board.py --slug ooo-trimiks    # one record's flags
  python3 scripts/status_board.py --today 2026-10-02    # fixed date (tests)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REG = ROOT / "data" / "registry"
SHARED_WATCH = Path("/mnt/project-files/watch")

# Thresholds in days. Sanctions lists move weekly; company register data monthly.
EGRUL_STALE_DAYS = 45
SCREEN_STALE_DAYS = 30
# The screens a sanctions submission leans on; the rest are reported as gaps only.
KEY_SCREENS = [
    ("opensanctions_screened_at", "OpenSanctions"),
    ("gur_screened_at", "ГУР war-sanctions"),
    ("aleph_screened_at", "Aleph"),
]
TIER_ORDER = ["cbst-core", "money-layer", "network", "manufacturer", "plumbing",
              "unverified", "adjacent"]
REGISTER_PREFIXES = ("EGRUL", "EGRULAPI", "EGRIP", "ul-", "fl-")
REVIEW_DONE = {"closed", "wired", "namesake", "named_no_tie", "tie_wired"}

# kind: what sort of work closes the flag. The page filters on it.
KINDS = {
    "pull": "Registry pull missing",
    "stale": "Pull or screen out of date",
    "behind": "Behind on developments",
    "review": "Needs a human read",
    "gap": "Record gap",
}


def load(name):
    return json.loads((REG / name).read_text(encoding="utf-8"))


def parse_date(v):
    if not v or not isinstance(v, str):
        return None
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", v)
    if not m:
        return None
    try:
        return date(int(m[1]), int(m[2]), int(m[3]))
    except ValueError:
        return None


def flag(kind, code, text, **extra):
    assert kind in KINDS, kind
    return {"kind": kind, "code": code, "text": text, **extra}


def tg_handles(obj):
    """Telegram channel handles named anywhere in a record's web/social block."""
    s = json.dumps(obj or {}, ensure_ascii=False)
    hs = set(re.findall(r"t\.me/(?:s/)?([A-Za-z0-9_]{4,})", s))
    return sorted(h for h in hs if not h.lower().endswith("bot") and h.lower() not in {"joinchat", "addstickers"})


def read_channels_txt():
    p = ROOT / "config" / "channels.txt"
    out = []
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            h = re.sub(r"^(@|https?://t\.me/|t\.me/)", "", line).strip("/")
            if h:
                out.append(h)
    return out


RISK_TOPICS = ("sanction", "debarment", "export.control", "crime.war")


def risky_matches(rec):
    """Screening hits that would matter to a sanctions desk: a GUR hit, or an
    OpenSanctions hit at score 0.9+ carrying a sanction/debarment/export topic."""
    n = len(rec.get("gur_matches") or [])
    for m in rec.get("opensanctions_matches") or []:
        if (m.get("score") or 0) >= 0.9 and any(t.startswith(RISK_TOPICS) for t in m.get("topics") or []):
            n += 1
    return n


def open_items(qs):
    """Open questions on a record: entries without a closed/resolved status."""
    n = 0
    for q in qs or []:
        st = (q.get("status") if isinstance(q, dict) else None) or "open"
        if st not in ("closed", "resolved", "answered"):
            n += 1
    return n


class Board:
    def __init__(self, today, scan_state=None, developments=None):
        self.today = today
        self.entities = [e for e in load("entities.json") if not e.get("_merged_into")]
        self.people = [p for p in load("people.json") if not p.get("_merged_into")]
        self.products = load("products.json") if (REG / "products.json").exists() else []
        self.sources = load("sources.json")
        self.src = {s["id"]: s for s in self.sources}
        self.global_oq = load("open_questions.json")
        self.scan_state = scan_state
        self.developments = developments
        self.notes = []
        if scan_state is None:
            self.notes.append("Weekly scan state not found: channel lag flags skipped.")
        if developments is None:
            self.notes.append("Weekly scan findings (developments.json) not found: development flags skipped.")

        # Latest archived post per channel, from sources.json tg_post.
        self.archived_posts = set()
        self.last_archived = {}
        for s in self.sources:
            tp = s.get("tg_post")
            if not tp or "/" not in tp:
                continue
            ch, _, msg = tp.partition("/")
            self.archived_posts.add((ch.lower(), msg))
            if msg.isdigit():
                k = ch.lower()
                self.last_archived[k] = max(self.last_archived.get(k, 0), int(msg))

        # Register extracts on file, keyed by any ИНН/ОГРН in the file name.
        self.register_pulls = defaultdict(list)
        for s in self.sources:
            path = s.get("path") or ""
            name = path.rsplit("/", 1)[-1]
            if s.get("type") in ("egrul", "egrul_api") or name.startswith(REGISTER_PREFIXES):
                d = parse_date(s.get("as_of")) or parse_date(s.get("captured_date"))
                for ident in re.findall(r"\d{10,15}", name):
                    self.register_pulls[ident].append((d, s["id"]))

        self.dev_by_slug = defaultdict(list)
        for it in (developments or {}).get("items", []):
            if it.get("status", "open") != "open":
                continue
            ch = (it.get("channel") or "").lower()
            archived = (ch, str(it.get("post"))) in self.archived_posts if ch and it.get("post") else False
            for slug in it.get("about") or []:
                self.dev_by_slug[slug].append({**it, "archived": archived})

        self.oq_by_slug = Counter()
        for q in self.global_oq:
            for k in ("entity_slug", "person_slug"):
                if q.get(k):
                    self.oq_by_slug[q[k]] += 1

    # --- shared tests -------------------------------------------------------

    def age(self, d):
        return (self.today - d).days if d else None

    def dev_flags(self, slug):
        out = []
        for it in self.dev_by_slug.get(slug, []):
            txt = it.get("summary") or "Weekly scan finding"
            out.append(flag("behind", "development", txt, url=it.get("url"), found=it.get("found"),
                            dev_kind=it.get("kind"), archived=it["archived"], dev_id=it.get("id")))
        return out

    def channel_flags(self, handles, allow_unwatched=True):
        """Lag on a record's own channels. A record whose channels are all off the
        weekly scan gets one flag naming them; a person's handles are often
        private contact accounts, so people are flagged only for watched channels."""
        out = []
        if self.scan_state is None or not handles:
            return out
        chans = {k.lower(): v for k, v in self.scan_state.get("channels", {}).items()}
        watched = [h for h in handles if h.lower() in chans]
        if not watched:
            if allow_unwatched:
                out.append(flag("behind", "channel_unwatched",
                                "Own Telegram not on the weekly scan: " + ", ".join("@" + h for h in handles),
                                channels=handles))
            return out
        for h in watched:
            hw = chans[h.lower()]
            last = self.last_archived.get(h.lower())
            if hw is None:
                out.append(flag("behind", "channel_unread",
                                f"@{h} is on the weekly scan but has not been read yet", channel=h,
                                last_archived=last))
            elif last is None:
                out.append(flag("review", "channel_never_archived",
                                f"No post from @{h} is archived; the channel is at post {hw}",
                                channel=h, high_water=hw))
        return out

    def screen_flags(self, rec):
        out, never, stale = [], [], []
        for field, label in KEY_SCREENS:
            if field not in rec and field == "gur_screened_at" and "inn" not in rec:
                continue
            d = parse_date(rec.get(field))
            if d is None:
                never.append(label)
            elif self.age(d) > SCREEN_STALE_DAYS:
                stale.append((label, d))
        if never:
            out.append(flag("pull", "screen_never", "Never screened: " + ", ".join(never)))
        if stale:
            oldest = min(d for _, d in stale)
            out.append(flag("stale", "screen_stale",
                            "Screen older than %d days: %s" % (SCREEN_STALE_DAYS, ", ".join(l for l, _ in stale)),
                            as_of=oldest.isoformat(), age_days=self.age(oldest)))
        return out

    # --- entities -----------------------------------------------------------

    def entity_row(self, e):
        fl = []
        inn, ogrn, form = e.get("inn"), e.get("ogrn"), e.get("legal_form")
        if not inn and not ogrn:
            if e.get("legal_entity_status") == "unresolved":
                fl.append(flag("gap", "identity_unresolved",
                               "Brand without a resolved legal entity (recorded as unresolved)"))
            else:
                fl.append(flag("gap", "no_identifier", "No ИНН or ОГРН on file"))
        else:
            pulls = [p for i in (inn, ogrn) if i for p in self.register_pulls.get(i, [])]
            dated = [d for d, _ in pulls if d]
            reg = "ЕГРИП" if form == "ИП" else "ЕГРЮЛ"
            if not pulls:
                fl.append(flag("pull", "egrul_missing", f"No {reg} extract on file"))
            else:
                last = max(dated) if dated else None
                if last and self.age(last) > EGRUL_STALE_DAYS:
                    fl.append(flag("stale", "egrul_stale", f"Latest {reg} extract is {self.age(last)} days old",
                                   as_of=last.isoformat(), age_days=self.age(last)))
            fl += self.screen_flags(e)
            if form != "ИП":
                fl += self.bfo_flags(e)
        # Screening hits nobody has reviewed.
        n_risk = risky_matches(e)
        if n_risk and not e.get("sanctions_review") and not e.get("sanctions"):
            fl.append(flag("review", "screen_hits_unreviewed",
                           f"{n_risk} sanctions-type screening hit(s), no sanctions review recorded", count=n_risk))
        n_oq = open_items(e.get("open_questions")) + self.oq_by_slug.get(e["slug"], 0)
        if n_oq:
            fl.append(flag("review", "open_questions", f"{n_oq} open question(s)", count=n_oq))
        n_ph = self.placeholder_count(e)
        if n_ph:
            fl.append(flag("gap", "unsourced_history", f"{n_ph} history entr(ies) with no source", count=n_ph))
        handles = tg_handles(e.get("web"))
        fl += self.channel_flags(handles)
        fl += self.dev_flags(e["slug"])
        last_pull = self.last_register_pull(e)
        return {
            "kind": "entity", "slug": e["slug"], "name": e.get("name_ru"),
            "latin": e.get("name_display"), "tier": e.get("tier"), "inn": inn,
            "channels": handles, "last_register_pull": last_pull,
            "screened": e.get("opensanctions_screened_at"),
            "sanctioned": bool(e.get("sanctions")),
            "flags": fl,
        }

    def last_register_pull(self, e):
        ds = [d for i in (e.get("inn"), e.get("ogrn")) if i for d, _ in self.register_pulls.get(i, []) if d]
        return max(ds).isoformat() if ds else None

    def bfo_flags(self, e):
        fin = e.get("financials") or []
        review = e.get("bfo_review") or {}
        if review.get("outcome") in REVIEW_DONE and not fin:
            return []
        years = [int(f["year"]) for f in fin if str(f.get("year", "")).isdigit()]
        reg = parse_date(e.get("registered"))
        expected = self.today.year - 1 if self.today.month >= 5 else self.today.year - 2
        if reg and reg.year >= expected:
            return []
        if not years:
            return [flag("pull", "bfo_missing", "No annual accounts (БФО) on file")]
        if max(years) < expected:
            rv = parse_date(review.get("as_of"))
            if rv and rv >= date(expected + 1, 5, 1):
                return []
            return [flag("behind", "bfo_behind", f"Latest accounts on file are for {max(years)}; {expected} should be filed",
                         latest_year=max(years))]
        return []

    @staticmethod
    def placeholder_count(rec):
        n = 0
        for k, v in rec.items():
            if k.endswith("_history") and isinstance(v, list):
                n += sum(1 for h in v if isinstance(h, dict) and not h.get("source_id"))
        return n

    # --- people -------------------------------------------------------------

    def person_row(self, p):
        fl = []
        d = parse_date(p.get("opensanctions_screened_at"))
        if d is None:
            fl.append(flag("pull", "screen_never", "Never screened: OpenSanctions"))
        elif self.age(d) > SCREEN_STALE_DAYS:
            fl.append(flag("stale", "screen_stale", f"OpenSanctions screen is {self.age(d)} days old",
                           as_of=d.isoformat(), age_days=self.age(d)))
        reference = p.get("graph_tier") == "reference"
        if not reference:
            if p.get("inn_personal") and not p.get("other_entities_checked_at"):
                fl.append(flag("pull", "other_entities_unchecked",
                               "Other companies under this personal ИНН not checked"))
            principal = any(isinstance(r, dict) and r.get("entity_slug") for r in p.get("roles") or [])
            if principal and not p.get("inn_personal"):
                fl.append(flag("gap", "no_inn", "Holds a company role but no personal ИНН on file"))
        n_risk = risky_matches(p)
        if n_risk and not p.get("sanctions") and not p.get("sanctions_review"):
            fl.append(flag("review", "screen_hits_unreviewed",
                           f"{n_risk} sanctions-type screening hit(s), no sanctions entry recorded", count=n_risk))
        unsourced_roles = sum(1 for r in p.get("roles") or [] if isinstance(r, dict) and not r.get("source_id"))
        if unsourced_roles:
            fl.append(flag("gap", "unsourced_roles", f"{unsourced_roles} role(s) with no source", count=unsourced_roles))
        n_oq = open_items(p.get("open_questions")) + self.oq_by_slug.get(p["slug"], 0)
        if n_oq:
            fl.append(flag("review", "open_questions", f"{n_oq} open question(s)", count=n_oq))
        handles = tg_handles(p.get("social"))
        fl += self.channel_flags(handles, allow_unwatched=False)
        fl += self.dev_flags(p["slug"])
        current = [r for r in p.get("roles") or [] if isinstance(r, dict) and not r.get("to")]
        return {
            "kind": "person", "slug": p["slug"], "name": p.get("fio_ru") or p.get("name_ru"),
            "latin": p.get("name_latin"), "tier": "reference" if reference else "person",
            "role": (current[0].get("title") if current else None),
            "channels": handles, "screened": p.get("opensanctions_screened_at"),
            "sanctioned": bool(p.get("sanctions")), "flags": fl,
        }

    # --- products -----------------------------------------------------------

    def product_row(self, pr):
        fl = []
        for li in pr.get("listings") or []:
            if not li.get("source_id"):
                fl.append(flag("pull", "listing_uncaptured",
                               f"Listing on {li.get('channel') or 'a storefront'} has no archived capture",
                               url=li.get("url")))
        for v in pr.get("versions") or []:
            if not v.get("source_id"):
                fl.append(flag("gap", "version_unsourced", f"Version {v.get('name') or v.get('id')} has no source"))
        n_oq = open_items(pr.get("open_questions"))
        if n_oq:
            fl.append(flag("review", "open_questions", f"{n_oq} open question(s)", count=n_oq))
        fl += self.dev_flags(pr["slug"])
        dels = [parse_date(d.get("date")) for d in pr.get("deliveries") or []]
        dels = [d for d in dels if d]
        return {
            "kind": "product", "slug": pr["slug"], "name": pr.get("name_ru") or pr.get("name"),
            "latin": pr.get("name_latin") or pr.get("name_en"), "tier": "product",
            "maker": pr.get("maker"), "versions": len(pr.get("versions") or []),
            "deliveries": len(pr.get("deliveries") or []),
            "last_delivery": max(dels).isoformat() if dels else None,
            "flags": fl,
        }

    # --- channels -----------------------------------------------------------

    def channel_rows(self, rows):
        owners = defaultdict(list)
        entity_owned = set()
        for r in rows:
            for h in r.get("channels") or []:
                owners[h.lower()].append(r["slug"])
                if r["kind"] == "entity":
                    entity_owned.add(h.lower())
        local = {h.lower(): h for h in read_channels_txt()}
        scan = {k.lower(): (k, v) for k, v in (self.scan_state or {}).get("channels", {}).items()}
        handles = {}
        for k, h in local.items():
            handles[k] = h
        for k, (h, _) in scan.items():
            handles.setdefault(k, h)
        for r in rows:
            for h in r.get("channels") or []:
                if h.lower() in entity_owned or h.lower() in scan or h.lower() in local:
                    handles.setdefault(h.lower(), h)
        out = []
        for k, h in sorted(handles.items()):
            fl = []
            hw = scan[k][1] if k in scan else None
            last = self.last_archived.get(k)
            if self.scan_state is not None:
                if k not in scan and k in entity_owned:
                    fl.append(flag("behind", "channel_unwatched", "A registry record's own channel, not on the weekly scan"))
                elif k in scan and hw is None:
                    fl.append(flag("behind", "channel_unread", "On the weekly scan, not read yet"))
            if k not in local:
                fl.append(flag("gap", "not_in_local_scrape", "Not on config/channels.txt (local scrape)"))
            if hw and last and hw > last:
                fl.append(flag("review", "posts_since_archive",
                               f"{hw - last} post number(s) since the last archived post",
                               high_water=hw, last_archived=last))
            elif hw and not last:
                fl.append(flag("review", "channel_never_archived", f"No post archived; channel is at post {hw}",
                               high_water=hw))
            fl += self.dev_flags(f"@{h}")
            out.append({"kind": "channel", "slug": f"@{h}", "name": f"@{h}", "tier": "channel",
                        "owners": owners.get(k, []), "high_water": hw, "last_archived": last,
                        "in_local_scrape": k in local, "in_weekly_scan": k in scan, "flags": fl})
        return out

    def build(self):
        rows = [self.entity_row(e) for e in self.entities]
        rows += [self.person_row(p) for p in self.people]
        rows += [self.product_row(p) for p in self.products]
        rows += self.channel_rows(rows)
        known = {r["slug"] for r in rows}
        orphans = [it for it in (self.developments or {}).get("items", [])
                   if it.get("status", "open") == "open" and not (set(it.get("about") or []) & known)]
        return {
            "generated": self.today.isoformat(),
            "thresholds": {"egrul_stale_days": EGRUL_STALE_DAYS, "screen_stale_days": SCREEN_STALE_DAYS},
            "kinds": KINDS, "notes": self.notes, "rows": rows, "unattached_developments": orphans,
        }


def default_path(name):
    p = SHARED_WATCH / name
    return p if p.exists() else None


def summary(board):
    rows = board["rows"]
    lines = [f"Status board, {board['generated']}"]
    for n in board["notes"]:
        lines.append(f"  note: {n}")
    by_kind = Counter(r["kind"] for r in rows)
    flagged = Counter(r["kind"] for r in rows if r["flags"])
    for k in ("entity", "person", "product", "channel"):
        lines.append(f"  {k:8} {flagged[k]:4} of {by_kind[k]:4} flagged")
    fc = Counter((f["kind"], f["code"]) for r in rows for f in r["flags"])
    lines.append("  flags:")
    for (k, c), n in sorted(fc.items()):
        lines.append(f"    {k:7} {c:28} {n}")
    behind = [(r, f) for r in rows for f in r["flags"] if f["code"] == "development"]
    if behind:
        lines.append("  open developments:")
        for r, f in behind:
            lines.append(f"    {r['slug']}: {f['text'][:100]}" + ("  [archived]" if f.get("archived") else ""))
    if board["unattached_developments"]:
        lines.append(f"  {len(board['unattached_developments'])} open development(s) not tied to a registry record")
    return "\n".join(lines)


def diff(prev, cur):
    """Flags that appeared or cleared since a previous board, keyed by (slug, code, text)."""
    def keyed(b):
        return {(r["slug"], f["code"], f["text"]): (r, f) for r in b["rows"] for f in r["flags"]}
    p, c = keyed(prev), keyed(cur)
    lines = [f"Changes since {prev.get('generated')}:"]
    new = [c[k] for k in c.keys() - p.keys()]
    gone = [p[k] for k in p.keys() - c.keys()]
    for label, items in (("new", new), ("cleared", gone)):
        lines.append(f"  {len(items)} {label} flag(s)")
        for r, f in sorted(items, key=lambda x: (x[1]["kind"], x[0]["slug"])):
            lines.append(f"    {f['kind']:7} {r['slug']}: {f['text'][:110]}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", help="write the full board as JSON here")
    ap.add_argument("--slug", help="print one record's flags")
    ap.add_argument("--today", help="YYYY-MM-DD (default: today)")
    ap.add_argument("--diff", help="a previous --json board: print flags new or cleared since it")
    ap.add_argument("--scan-state", help="weekly_scan_state.json (default: shared watch folder)")
    ap.add_argument("--developments", help="developments.json (default: shared watch folder)")
    a = ap.parse_args()
    today = parse_date(a.today) if a.today else date.today()
    ss = Path(a.scan_state) if a.scan_state else default_path("weekly_scan_state.json")
    dv = Path(a.developments) if a.developments else default_path("developments.json")
    board = Board(today,
                  json.loads(ss.read_text(encoding="utf-8")) if ss and ss.exists() else None,
                  json.loads(dv.read_text(encoding="utf-8")) if dv and dv.exists() else None).build()
    if a.json:
        Path(a.json).write_text(json.dumps(board, ensure_ascii=False, indent=1), encoding="utf-8")
    if a.slug:
        for r in board["rows"]:
            if r["slug"] == a.slug:
                print(json.dumps(r, ensure_ascii=False, indent=1))
                return 0
        print(f"no record {a.slug}", file=sys.stderr)
        return 1
    print(summary(board))
    if a.diff:
        print(diff(json.loads(Path(a.diff).read_text(encoding="utf-8")), board))
    return 0


if __name__ == "__main__":
    sys.exit(main())
