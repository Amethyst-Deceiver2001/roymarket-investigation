#!/usr/bin/env python3
"""VK API helper — read-only wall/newsfeed pulls for this investigation.

Not a live-crawl job in the tg_scan.py sense (no continuous scraping, no
per-channel backfill) — a single bounded API call per invocation, same
class of thing as a WebFetch/curl one-off. Safe to run directly.

Requires VK_API_TOKEN in .env (see HANDOFF.md / memory for how it was
obtained — Standalone app, implicit-flow OAuth, read-only scope).

Usage:
    python3 scripts/vk_fetch.py search "резидент цбст" --days 365
    python3 scripts/vk_fetch.py search "ЦБСТ" --days 30 --count 50
    python3 scripts/vk_fetch.py wall <group_screen_name> --count 20
"""
import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

API_VERSION = "5.199"
API_BASE = "https://api.vk.com/method"


def load_token() -> str:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    token = os.environ.get("VK_API_TOKEN")
    if token:
        return token
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("VK_API_TOKEN="):
                return line.split("=", 1)[1].strip()
    sys.exit("VK_API_TOKEN not found in environment or .env")


def call(method: str, token: str, **params) -> dict:
    params = {k: v for k, v in params.items() if v is not None}
    params["access_token"] = token
    params["v"] = API_VERSION
    url = f"{API_BASE}/{method}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=20) as resp:
        data = json.load(resp)
    if "error" in data:
        err = data["error"]
        sys.exit(f"VK API error {err.get('error_code')}: {err.get('error_msg')}")
    return data["response"]


def cmd_search(args, token: str):
    end_time = int(time.time())
    start_time = end_time - args.days * 86400
    seen_ids = set()
    total = []
    start_from = None
    fetched = 0
    while fetched < args.count:
        page_count = min(200, args.count - fetched)
        resp = call(
            "newsfeed.search",
            token,
            q=args.query,
            count=page_count,
            start_time=start_time,
            end_time=end_time,
            extended=0,
            start_from=start_from,
        )
        items = resp.get("items", [])
        if not items:
            break
        for it in items:
            key = (it.get("owner_id"), it.get("id"))
            if key in seen_ids:
                continue
            seen_ids.add(key)
            total.append(it)
        fetched += len(items)
        start_from = resp.get("next_from")
        if not start_from:
            break

    for it in total:
        owner_id = it.get("owner_id")
        post_id = it.get("id")
        date = time.strftime("%Y-%m-%d", time.localtime(it.get("date", 0)))
        text = (it.get("text") or "").replace("\n", " ")
        link = f"https://vk.com/wall{owner_id}_{post_id}"
        print(f"[{date}] {link}")
        print(f"  {text[:400]}")
        print()

    print(f"--- {len(total)} posts, {args.days}-day window, query={args.query!r} ---",
          file=sys.stderr)


def cmd_wall(args, token: str):
    owner = args.owner
    if not owner.lstrip("-").isdigit():
        resolved = call("utils.resolveScreenName", token, screen_name=owner)
        if not resolved:
            sys.exit(f"Could not resolve screen name: {owner}")
        obj_id = resolved["object_id"]
        owner_id = -obj_id if resolved["type"] == "group" else obj_id
    else:
        owner_id = int(owner)

    resp = call("wall.get", token, owner_id=owner_id, count=args.count)
    for it in resp.get("items", []):
        date = time.strftime("%Y-%m-%d", time.localtime(it.get("date", 0)))
        text = (it.get("text") or "").replace("\n", " ")
        link = f"https://vk.com/wall{owner_id}_{it.get('id')}"
        print(f"[{date}] {link}")
        print(f"  {text[:400]}")
        print()
    print(f"--- {resp.get('count', 0)} total posts on wall, showing {len(resp.get('items', []))} ---",
          file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("search", help="newsfeed.search across public VK posts")
    sp.add_argument("query")
    sp.add_argument("--days", type=int, default=365)
    sp.add_argument("--count", type=int, default=100)

    wp = sub.add_parser("wall", help="wall.get for a group/user (screen name or numeric id)")
    wp.add_argument("owner")
    wp.add_argument("--count", type=int, default=20)

    args = ap.parse_args()
    token = load_token()

    if args.cmd == "search":
        cmd_search(args, token)
    elif args.cmd == "wall":
        cmd_wall(args, token)


if __name__ == "__main__":
    main()
