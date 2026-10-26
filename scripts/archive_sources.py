#!/usr/bin/env python3
"""Public snapshots of every Telegram post and web page the registry cites.

Each `sources.json` record with a `public_url` already has a local copy in
`data/sources/` (its `path` and `sha256`). That copy proves what we saw, but a
reader cannot open it. If a channel deletes a post or a company pulls a page, a
claim that cites it can only be checked against an independent public copy. This
script gives every cited URL one: a Wayback Machine capture, recorded with its
date and the SHA-256 of the archived bytes, in `data/registry/source_archives.json`.

**`lookup` and `save` are live network jobs against a third-party service.** Per
CLAUDE.md's crawling-jobs policy they run on the user's Mac, in batches, never
in the background from a cloud session (the cloud network blocks both
web.archive.org and most of the cited sites anyway). `plan`, `local` and
`report` are local file processing and safe to run anywhere.

A Wayback capture is public: anyone can see that the URL was archived and when.
The capture does not record who asked for it.

Subcommands:
    plan     Rebuild the URL list from sources.json (no network). New citations
             appear as pending; captures already recorded are kept.
    local    Check each cited URL's local copy in data/sources/ against the
             sha256 in sources.json (no network; needs data/sources/).
    lookup   Ask the Wayback CDX index whether a capture already exists; record
             it. Read-only: creates nothing public. Telegram posts are looked up
             one request per channel (a CDX prefix query over the past
             FRESH_DAYS); other URLs one request each.
    save     Ask the Wayback Machine to capture pending URLs, then hash the
             archived bytes. Uses SPN2 with keys when WAYBACK_S3_ACCESS and
             WAYBACK_S3_SECRET are set (free archive.org account, Settings ->
             S3 API keys; put them in .env), otherwise the anonymous endpoint,
             which is slower and rate-limited harder.
    run      plan, then lookup, then save, for one daily batch.
    report   Coverage by tier and kind (no network).

Tiers (what gets archived first):
    1  Telegram posts and web pages cited by a registry record
    2  procurement (zakupki.gov.ru) and trademark (fips.ru) registry pages cited
       by a registry record; official records, less likely to vanish
    3  everything with a public URL that no registry record cites yet
`save` and `lookup` take tiers 1-2 unless --tier says otherwise.

Usage (on the Mac):
    python3 scripts/archive_sources.py run --limit 150
    python3 scripts/archive_sources.py report
"""
from __future__ import annotations

import argparse
import base64
import glob
import gzip
import hashlib
from http.client import HTTPException
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REGISTRY = REPO / "data" / "registry"
SOURCES_JSON = REGISTRY / "sources.json"
ARCHIVES_JSON = REGISTRY / "source_archives.json"
SCHEMA_VERSION = 1

USER_AGENT = "roymarket-investigation source archiver (journalism; contact via repo owner)"
WAYBACK = "https://web.archive.org"
# SPN asks anonymous clients for no more than a few captures a minute; keyed
# clients can go faster, but this is a daily batch, not a race.
DELAY_ANON = 20.0
DELAY_KEYED = 8.0
DELAY_LOOKUP = 1.5
# A capture younger than this counts as current; no new capture is requested.
FRESH_DAYS = 365

SKIP_FILES = ("sources.json", "_source_ids.json", "source_archives.json")


# ---------------------------------------------------------------- planning --

def classify(url: str) -> str | None:
    """Kind of a public URL, or None when it cannot be archived as given."""
    p = urllib.parse.urlparse(url)
    if p.scheme not in ("http", "https") or not p.netloc:
        return None
    host = p.netloc.lower()
    if host in ("t.me", "telegram.me"):
        return "telegram"
    if host.endswith("web.archive.org") or host in ("archive.ph", "archive.today", "archive.is"):
        return "archived"
    if host.endswith("zakupki.gov.ru"):
        return "procurement"
    if host.endswith("fips.ru"):
        return "trademark"
    return "web"


def tier_of(kind: str, cited: bool) -> int:
    if not cited:
        return 3
    return 2 if kind in ("procurement", "trademark") else 1


def telegram_variants(url: str) -> list[str]:
    """The post page plus its embed view, which renders the full text and media."""
    m = re.match(r"https?://(?:t|telegram)\.me/(?:s/)?([A-Za-z0-9_]+)/(\d+)", url)
    if not m:
        return [url]
    base = f"https://t.me/{m.group(1)}/{m.group(2)}"
    return [base, base + "?embed=1&mode=tme"]


def cited_source_ids() -> set[str]:
    """Source ids referenced by any registry file other than the catalogue itself."""
    ids: set[str] = set()
    for f in glob.glob(str(REGISTRY / "*.json")):
        name = os.path.basename(f)
        if name in SKIP_FILES or (name.startswith("_") and name.endswith("_cache.json")):
            continue
        ids |= set(re.findall(r'"(s\d{4,5})"', Path(f).read_text(encoding="utf-8")))
    return ids


def load_archives() -> dict:
    if ARCHIVES_JSON.exists():
        return json.loads(ARCHIVES_JSON.read_text(encoding="utf-8"))
    return {"schema_version": SCHEMA_VERSION, "urls": {}}


def save_archives(data: dict) -> None:
    data["urls"] = dict(sorted(data["urls"].items()))
    tmp = ARCHIVES_JSON.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    tmp.replace(ARCHIVES_JSON)


def company_sites() -> dict[str, list[str]]:
    """Site URLs on entity records (`web.sites`), keyed by URL, listing the slugs."""
    out: dict[str, list[str]] = {}
    for e in json.loads((REGISTRY / "entities.json").read_text(encoding="utf-8")):
        web = e.get("web")
        for s in (web.get("sites") or []) if isinstance(web, dict) else []:
            u = s.get("url") if isinstance(s, dict) else s
            if u and classify(u) == "web":
                out.setdefault(u, []).append(e["slug"])
    return out


def build_plan(sources: list[dict], cited: set[str], prev: dict,
               sites: dict[str, list[str]] | None = None) -> tuple[dict, list[dict]]:
    """Merge the current citations into the archive file. Returns (data, unusable).

    `sites` are company sites on record: tier 1 like a cited page, with the
    entity slugs in `entities` and no source ids."""
    urls: dict[str, dict] = {}
    unusable = []
    for r in sources:
        pu = r.get("public_url")
        if not pu:
            continue
        kind = classify(pu)
        if kind is None:
            unusable.append({"source_id": r["id"], "public_url": pu})
            continue
        targets = telegram_variants(pu) if kind == "telegram" else [pu]
        for i, u in enumerate(targets):
            e = urls.setdefault(u, {"kind": kind, "source_ids": [], "cited": False})
            if i:
                e["variant_of"] = targets[0]
            if r["id"] not in e["source_ids"]:
                e["source_ids"].append(r["id"])
            e["cited"] = e["cited"] or r["id"] in cited
    for u, slugs in (sites or {}).items():
        e = urls.setdefault(u, {"kind": "web", "source_ids": [], "cited": True})
        e["cited"] = True
        e["entities"] = sorted(set(slugs))
    old = prev.get("urls", {})
    for u, e in urls.items():
        e["source_ids"].sort()
        e["tier"] = tier_of(e["kind"], e["cited"])
        o = old.get(u, {})
        e["captures"] = o.get("captures", [])
        if e["kind"] == "archived" and not e["captures"]:
            # The citation already is an archive copy; record it as such.
            m = re.search(r"/web/(\d{14})", u)
            e["captures"] = [{"service": "wayback" if "archive.org" in u else "archive_today",
                              "archive_url": u, "timestamp": m.group(1) if m else None,
                              "method": "cited", "checked": None, "sha256": None}]
        for k in ("last_attempt", "last_error"):
            if k in o:
                e[k] = o[k]
    # A URL nobody cites any more keeps its captures, flagged, so history is not lost.
    for u, o in old.items():
        if u not in urls and o.get("captures"):
            o = dict(o)
            o["dropped"] = True
            urls[u] = o
    return {"schema_version": SCHEMA_VERSION, "urls": urls}, unusable


def is_current(e: dict, today: date) -> bool:
    """A web page goes stale after FRESH_DAYS. A Telegram post does not: any
    capture shows it as published, and an early one predates later edits
    (user, 03.10.2026). Our own copy is fixed by timestamp_sources.py."""
    for c in e.get("captures", []):
        ts = c.get("timestamp")
        if c.get("method") == "cited" or (ts and e.get("kind") == "telegram"):
            return True
        if ts and datetime.strptime(ts[:8], "%Y%m%d").date() >= today - timedelta(days=FRESH_DAYS):
            return True
    return False


def telegram_key(url: str) -> tuple[str, str, bool] | None:
    """(channel lowercased, post id, embed view) for a post URL; None otherwise.

    Telegram usernames are case-insensitive and the Wayback index folds case, so
    t.me/ANO_CBST/5 and t.me/ano_cbst/5 are one post with one set of captures."""
    m = re.match(r"https?://(?:t|telegram)\.me/(?:s/)?([A-Za-z0-9_]+)/(\d+)/?(\?.*)?$", url)
    if not m:
        return None
    return m.group(1).lower(), m.group(2), "embed=1" in (m.group(3) or "")


def channel_hits(rows: list[list[str]]) -> dict[tuple[str, str, bool], dict]:
    """CDX prefix rows (timestamp, original, digest) -> the earliest capture per post.

    Only the bare post page and its embed view count; ?single, ?comment and other
    query variants render something else and are ignored."""
    out: dict[tuple[str, str, bool], dict] = {}
    for ts, orig, digest in rows:
        k = telegram_key(orig)
        if not k:
            continue
        q = orig.split("?", 1)[1] if "?" in orig else ""
        if q and not (k[2] and set(q.split("&")) <= {"embed=1", "mode=tme"}):
            continue
        if k not in out or ts < out[k]["timestamp"]:
            out[k] = {"timestamp": ts, "original": orig, "wayback_sha1": digest}
    return out


# Telegram cuts the text in a post page's og:description at about 1,000 characters (seen
# 03.10.2026, e.g. t.me/vadim_dzema_fpv/378). Only the embed view and the channel preview
# carry a long post whole, so a post that long keeps its embed view in the queue.
# user, 03.10.2026: Telegram posts are not archived on the Wayback Machine ("we're not web archiving telegram posts");
# their preservation is our own record, the RFC 3161 stamps and a per-post evidence bundle. The code stays behind
# --include-telegram; every Telegram URL enters a batch through pending(), so this one switch covers lookup, preview
# pages and per-post saves.
INCLUDE_TELEGRAM = False
LONG_POST_BYTES = 800


def needs_embed(data: dict, e: dict) -> bool:
    """True when a cited post's saved text is long enough that the post page may be truncated."""
    try:
        sources = {s["id"]: s for s in json.loads(SOURCES_JSON.read_text(encoding="utf-8"))}
    except (OSError, ValueError):
        return True
    base = data["urls"].get(e.get("variant_of") or "", {})
    sids = base.get("source_ids") or e.get("source_ids") or []
    if not sids:
        return True
    for sid in sids:
        p = REPO / (sources.get(sid, {}).get("path") or "")
        if p.is_file() and p.stat().st_size > LONG_POST_BYTES:
            return True
        if not p.is_file():
            return True  # cannot tell: keep the embed view
    return False


def pending(data: dict, tiers: set[int], today: date, *, skip_looked_up: bool = False) -> list[str]:
    out = []
    for u, e in data["urls"].items():
        if e.get("dropped") or e.get("tier") not in tiers or is_current(e, today):
            continue
        if e.get("kind") == "telegram" and not INCLUDE_TELEGRAM:
            continue
        base = data["urls"].get(e.get("variant_of") or "")
        if base and is_current(base, today) and not needs_embed(data, e):
            continue  # the post page is captured and the post is short enough to be whole in it
        if skip_looked_up and e.get("looked_up") == today.isoformat():
            continue
        out.append(u)
    out.sort(key=lambda u: (data["urls"][u]["tier"], data["urls"][u]["kind"] != "telegram",
                            "variant_of" in data["urls"][u], u))
    return out


# ----------------------------------------------------------------- network --

def _ssl_context() -> ssl.SSLContext:
    try:
        import certifi  # python.org builds on macOS ship without a CA bundle
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


CTX = _ssl_context()


def http(url: str, *, data: bytes | None = None, headers: dict | None = None,
         timeout: int = 90) -> tuple[int, dict, bytes, str]:
    h = {"User-Agent": USER_AGENT, **(headers or {})}
    # a Cyrillic address inside a Wayback path must be percent-encoded for the request line
    url = urllib.parse.quote(url, safe="".join(chr(c) for c in range(33, 127)))
    req = urllib.request.Request(url, data=data, headers=h)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=CTX) as resp:
                return resp.status, dict(resp.headers), resp.read(), resp.geturl()
        except urllib.error.HTTPError as err:
            return err.code, dict(err.headers or {}), err.read() or b"", url
        except (ConnectionError, HTTPException, urllib.error.URLError, TimeoutError):
            # archive.org drops connections now and then; a retry usually goes through
            if attempt == 2:
                raise
            time.sleep(15 * (attempt + 1))


def cdx_latest(url: str) -> dict | None:
    q = urllib.parse.urlencode({"url": url, "output": "json", "limit": "-1",
                                "fl": "timestamp,original,statuscode,digest",
                                "filter": "statuscode:200"})
    status, _, body, _ = http(f"{WAYBACK}/cdx/search/cdx?{q}", timeout=60)
    if status != 200:
        raise RuntimeError(f"CDX HTTP {status}")
    rows = json.loads(body or b"[]")
    if len(rows) < 2:
        return None
    ts, orig, code, digest = rows[-1]
    return {"timestamp": ts, "original": orig, "wayback_sha1": digest}


def cdx_channel(channel: str) -> list[list[str]]:
    """The earliest 200 capture of every URL under t.me/<channel>/, one row each."""
    q = urllib.parse.urlencode({"url": f"t.me/{channel}/", "matchType": "prefix", "output": "json",
                                "fl": "timestamp,original,digest", "filter": "statuscode:200",
                                "collapse": "urlkey"})
    status, _, body, _ = http(f"{WAYBACK}/cdx/search/cdx?{q}", timeout=300)
    if status != 200:
        raise RuntimeError(f"CDX HTTP {status}")
    rows = json.loads(body or b"[]")
    return rows[1:]


def raw_body(ts: str, url: str) -> bytes | None:
    """The archived bytes as Wayback serves them unmodified (id_ view)."""
    status, _, body, _ = http(f"{WAYBACK}/web/{ts}id_/{url}", timeout=120)
    return body if status == 200 else None


def raw_sha256(ts: str, url: str) -> tuple[str | None, int | None]:
    body = raw_body(ts, url)
    if body is None:
        return None, None
    return hashlib.sha256(body).hexdigest(), len(body)


def preview_url(channel: str, post: int) -> str:
    """The channel's public web preview ending at `post` (about 20 posts per page)."""
    return f"https://t.me/s/{channel}?before={post + 1}"


def decoded(body: bytes) -> bytes:
    """The id_ view returns bytes as the site sent them, often gzip-compressed."""
    if body[:2] == b"\x1f\x8b":
        try:
            return gzip.decompress(body)
        except OSError:
            return body
    return body


def existing_preview(page: str) -> tuple[str, bytes] | None:
    """The newest archived copy of a preview page, if one exists (ours or anyone's)."""
    status, _, body, final = http(f"{WAYBACK}/web/2id_/{page}", timeout=120)
    m = re.search(r"/web/(\d{14})id_/", final or "")
    if status != 200 or not m:
        return None
    return m.group(1), body


def posts_on_page(html: bytes, channel: str) -> set[int]:
    """Post ids the preview page actually shows (its data-post attributes)."""
    html = decoded(html)
    pat = rf'data-post="{re.escape(channel)}/(\d+)"'.encode()
    return {int(m) for m in re.findall(pat, html, flags=re.I)}


def spn_keyed(url: str, access: str, secret: str) -> str:
    auth = {"Authorization": f"LOW {access}:{secret}", "Accept": "application/json"}
    form = urllib.parse.urlencode({"url": url, "skip_first_archive": "1",
                                   "if_not_archived_within": f"{FRESH_DAYS}d"}).encode()
    status, _, body, _ = http(f"{WAYBACK}/save", data=form, headers=auth)
    if status == 429:
        raise RateLimited()
    j = json.loads(body or b"{}")
    if "job_id" not in j:
        raise RuntimeError(j.get("message") or f"SPN HTTP {status}")
    for _ in range(40):
        time.sleep(6)
        _, _, sb, _ = http(f"{WAYBACK}/save/status/{j['job_id']}", headers=auth)
        st = json.loads(sb or b"{}")
        if st.get("status") == "success":
            return st["timestamp"]
        if st.get("status") == "error":
            raise RuntimeError(st.get("message") or st.get("status_ext") or "SPN error")
    raise RuntimeError("SPN job still pending after 4 minutes")


def spn_anon(url: str) -> str:
    status, headers, _, final = http(f"{WAYBACK}/save/{url}", timeout=180)
    if status == 429:
        raise RateLimited()
    for cand in (headers.get("Content-Location", ""), final):
        m = re.search(r"/web/(\d{14})", cand or "")
        if m:
            return m.group(1)
    if status >= 400:
        raise RuntimeError(f"SPN HTTP {status}")
    # Some anonymous saves return 200 without naming the snapshot; ask the index.
    time.sleep(5)
    hit = cdx_latest(url)
    if hit and hit["timestamp"][:8] == datetime.now(timezone.utc).strftime("%Y%m%d"):
        return hit["timestamp"]
    raise RuntimeError("capture requested but no snapshot found yet")


class RateLimited(Exception):
    pass


def record_capture(e: dict, ts: str, url: str, method: str, sha1: str | None = None) -> None:
    """`url` is the address as the archive holds it (case may differ from ours)."""
    sha256, size = raw_sha256(ts, url)
    e["captures"] = [c for c in e.get("captures", []) if c.get("timestamp") != ts]
    e["captures"].append({
        "service": "wayback",
        "archive_url": f"{WAYBACK}/web/{ts}/{url}",
        "timestamp": ts,
        "method": method,          # existing (found in the index) | saved (requested by us) | cited
                                   # (preview_page: a channel page that shows the post, see save_previews)
        "checked": date.today().isoformat(),
        "sha256": sha256,          # of the raw archived bytes (id_ view)
        "bytes": size if sha256 else None,
        "wayback_sha1": sha1,
    })
    e["captures"].sort(key=lambda c: c.get("timestamp") or "")
    e.pop("last_error", None)


# ---------------------------------------------------------------- commands --

def cmd_plan(args) -> dict:
    sources = json.loads(SOURCES_JSON.read_text(encoding="utf-8"))
    data, unusable = build_plan(sources, cited_source_ids(), load_archives(), company_sites())
    save_archives(data)
    print(f"{len(data['urls'])} URLs on file; {len(unusable)} public_url values cannot be archived as given")
    for u in unusable[:20]:
        print(f"  unusable: {u['source_id']} {u['public_url']}")
    if len(unusable) > 20:
        print(f"  ... and {len(unusable) - 20} more")
    return data


def cmd_local(args) -> int:
    sources = {r["id"]: r for r in json.loads(SOURCES_JSON.read_text(encoding="utf-8"))}
    data = load_archives()
    missing, mismatch, ok = [], [], 0
    seen = set()
    for e in data["urls"].values():
        for sid in e.get("source_ids", []):
            if sid in seen or sid not in sources:
                continue
            seen.add(sid)
            r = sources[sid]
            p = REPO / r["path"]
            if not p.exists():
                missing.append(sid)
                continue
            if r.get("sha256") and hashlib.sha256(p.read_bytes()).hexdigest() != r["sha256"]:
                mismatch.append(sid)
            else:
                ok += 1
    print(f"local copies: {ok} match sources.json, {len(mismatch)} differ, {len(missing)} missing")
    for sid in mismatch:
        print(f"  differs: {sid} {sources[sid]['path']}")
    for sid in missing[:30]:
        print(f"  missing: {sid} {sources[sid]['path']}")
    if len(missing) > 30:
        print(f"  ... and {len(missing) - 30} more missing")
    return 1 if mismatch else 0


def parse_tiers(s: str) -> set[int]:
    return {int(x) for x in s.split(",") if x.strip()}


def lookup_channels(data: dict, todo: list[str], today: date) -> int:
    """One CDX prefix query per channel for the pending Telegram posts in `todo`.

    Every post asked about is marked looked_up, found or not, so the per-URL
    lookup skips it and an unarchived post goes straight to `save`."""
    by_channel: dict[str, list[str]] = {}
    for u in todo:
        k = telegram_key(u)
        if k:
            by_channel.setdefault(k[0], []).append(u)
    found = 0
    for ch, urls in sorted(by_channel.items()):
        try:
            hits = channel_hits(cdx_channel(ch))
        except Exception as err:  # leave these to the per-URL lookup
            print(f"  channel {ch}: {err}", flush=True)
            time.sleep(DELAY_LOOKUP)
            continue
        n = 0
        for u in urls:
            e = data["urls"][u]
            e["looked_up"] = today.isoformat()
            hit = hits.get(telegram_key(u))
            if not hit:
                continue
            try:
                record_capture(e, hit["timestamp"], hit["original"], "existing", hit["wayback_sha1"])
                n += 1
            except Exception as err:
                e["last_error"] = f"lookup {today}: {err}"
            time.sleep(DELAY_LOOKUP)
        save_archives(data)
        found += n
        print(f"  channel {ch}: {n} of {len(urls)} posts already captured", flush=True)
        time.sleep(DELAY_LOOKUP)
    return found


def cmd_lookup(args, data: dict | None = None) -> dict:
    data = data or load_archives()
    today = date.today()
    tg = [u for u in pending(data, parse_tiers(args.tier), today)  # cheap: re-ask every run
          if data["urls"][u]["kind"] == "telegram"]
    if tg:
        print(f"lookup: {len(tg)} Telegram posts, one index query per channel", flush=True)
        print(f"lookup: existing capture found for {lookup_channels(data, tg, today)} of {len(tg)}")
    todo = pending(data, parse_tiers(args.tier), today, skip_looked_up=True)[: args.limit]
    print(f"lookup: {len(todo)} URLs")
    found = 0
    for i, u in enumerate(todo, 1):
        e = data["urls"][u]
        try:
            hit = cdx_latest(u)
            e["looked_up"] = today.isoformat()
            if hit:
                record_capture(e, hit["timestamp"], u, "existing", hit["wayback_sha1"])
                found += 1
        except Exception as err:  # keep going; the error is recorded on the URL
            e["last_error"] = f"lookup {today}: {err}"
        if i % 25 == 0:
            save_archives(data)
        time.sleep(DELAY_LOOKUP)
    save_archives(data)
    print(f"lookup: existing capture found for {found} of {len(todo)}")
    return data


def save_previews(data: dict, tiers: set[int], today: date, capture, delay: float, budget: int) -> int:
    """Capture pending Telegram posts through channel preview pages; returns captures used.

    One preview page shows about 20 posts, so one capture can cover several
    cited posts. A post counts as captured only if the archived page's own
    markup shows it (data-post); anything a page misses is left for the
    per-post save. A channel with its preview switched off costs one capture."""
    by_channel: dict[str, dict[int, str]] = {}
    for u in pending(data, tiers, today):
        k = telegram_key(u)
        if k and not k[2]:
            by_channel.setdefault(k[0], {})[int(k[1])] = u
    used = 0
    for ch, posts in sorted(by_channel.items(), key=lambda kv: -len(kv[1])):
        if len(posts) < 2:
            continue  # a single post is cheaper to save directly
        left = dict(posts)
        while left and used < budget:
            top = max(left)
            page = preview_url(ch, top)
            used += 1
            try:
                hit = existing_preview(page)
                if hit and posts_on_page(hit[1], ch) & set(left):
                    ts, body, how = hit[0], hit[1], "existing"
                    used -= 1  # no capture requested
                else:
                    ts = capture(page)
                    body, how = raw_body(ts, page), "saved"
                shown = posts_on_page(body or b"", ch)
            except RateLimited:
                print("  rate-limited by the Wayback Machine; stopping this batch", flush=True)
                return budget
            except Exception as err:
                print(f"  failed {page}: {err}", flush=True)
                break
            covered = [p for p in left if p in shown]
            sha = hashlib.sha256(body).hexdigest() if body else None
            for p in covered:
                e = data["urls"][left.pop(p)]
                e["captures"] = e.get("captures", []) + [{
                    "service": "wayback", "archive_url": f"{WAYBACK}/web/{ts}/{page}",
                    "timestamp": ts, "method": "preview_page", "checked": today.isoformat(),
                    "sha256": sha, "bytes": len(body) if body else None, "wayback_sha1": None,
                    "shows_post": True}]
                e.pop("last_error", None)
            print(f"  {ch}: page before {top + 1} ({how}) shows {len(covered)} cited posts", flush=True)
            save_archives(data)
            time.sleep(delay if how == "saved" else DELAY_LOOKUP)
            if top not in shown:
                break  # preview off, or the page skips this post: leave the rest to per-post saves
    return used


def cmd_save(args, data: dict | None = None) -> int:
    data = data or load_archives()
    today = date.today()
    access, secret = os.environ.get("WAYBACK_S3_ACCESS"), os.environ.get("WAYBACK_S3_SECRET")
    if not access:
        _load_dotenv()
        access, secret = os.environ.get("WAYBACK_S3_ACCESS"), os.environ.get("WAYBACK_S3_SECRET")
    delay = DELAY_KEYED if access and secret else DELAY_ANON
    capture = (lambda u: spn_keyed(u, access, secret)) if access and secret else spn_anon
    budget = args.limit
    budget -= save_previews(data, parse_tiers(args.tier), today, capture, delay, budget)
    todo = pending(data, parse_tiers(args.tier), today)[: max(budget, 0)]
    if access and not secret:
        print("save: WAYBACK_S3_ACCESS is set but WAYBACK_S3_SECRET is not; using the anonymous endpoint")
    print(f"save: {len(todo)} URLs ({'keyed SPN2' if access and secret else 'anonymous SPN'}, {delay:.0f}s apart)")
    saved = failed = 0
    for i, u in enumerate(todo, 1):
        e = data["urls"][u]
        e["last_attempt"] = today.isoformat()
        try:
            ts = capture(u)
            record_capture(e, ts, u, "saved")
            saved += 1
            print(f"  [{i}/{len(todo)}] ok {ts} {u}")
        except RateLimited:
            print("  rate-limited by the Wayback Machine; stopping this batch")
            break
        except Exception as err:
            e["last_error"] = f"save {today}: {err}"
            failed += 1
            print(f"  [{i}/{len(todo)}] failed {u}: {err}")
        save_archives(data)
        time.sleep(delay)
    left = len(pending(data, parse_tiers(args.tier), today))
    print(f"save: {saved} captured, {failed} failed, {left} still pending in tiers {args.tier}")
    return 0


def _load_dotenv() -> None:
    env = REPO / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*(WAYBACK_S3_ACCESS|WAYBACK_S3_SECRET)\s*=\s*(.+?)\s*$", line)
        if m:
            os.environ.setdefault(m.group(1), m.group(2).strip("'\""))


def coverage(data: dict, today: date) -> dict:
    out: dict = {}
    for e in data["urls"].values():
        if e.get("dropped"):
            continue
        k = (e["tier"], e["kind"])
        c = out.setdefault(k, {"urls": 0, "archived": 0, "hashed": 0, "errors": 0})
        c["urls"] += 1
        if is_current(e, today) or e.get("captures"):
            c["archived"] += 1
        if any(x.get("sha256") for x in e.get("captures", [])):
            c["hashed"] += 1
        if e.get("last_error"):
            c["errors"] += 1
    return out


def cmd_report(args) -> int:
    data = load_archives()
    cov = coverage(data, date.today())
    print(f"{'tier':>4}  {'kind':<12} {'urls':>6} {'archived':>9} {'hashed':>7} {'errors':>7}")
    for (t, k), c in sorted(cov.items()):
        print(f"{t:>4}  {k:<12} {c['urls']:>6} {c['archived']:>9} {c['hashed']:>7} {c['errors']:>7}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("plan")
    sub.add_parser("local")
    sub.add_parser("report")
    for name in ("lookup", "save", "run"):
        p = sub.add_parser(name)
        p.add_argument("--limit", type=int, default=150, help="URLs per batch (default 150)")
        p.add_argument("--tier", default="1,2", help="comma-separated tiers (default 1,2)")
        p.add_argument("--include-telegram", action="store_true",
                       help="also archive Telegram posts (off by default, user decision 03.10.2026)")
    args = ap.parse_args(argv)
    global INCLUDE_TELEGRAM
    INCLUDE_TELEGRAM = bool(getattr(args, "include_telegram", False))
    sys.stdout.reconfigure(line_buffering=True)  # a batch killed midway still leaves its log
    if args.cmd == "plan":
        cmd_plan(args)
        return 0
    if args.cmd == "local":
        return cmd_local(args)
    if args.cmd == "report":
        return cmd_report(args)
    if args.cmd == "lookup":
        cmd_lookup(args)
        return 0
    if args.cmd == "save":
        return cmd_save(args)
    data = cmd_plan(args)
    data = cmd_lookup(args, data)
    rc = cmd_save(args, data)
    cmd_report(args)
    return rc


if __name__ == "__main__":
    sys.exit(main())
