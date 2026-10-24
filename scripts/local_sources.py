#!/usr/bin/env python3
"""Local source ids for a machine that cannot assign sNNNN ids (no archive Mac).

The registry's source ids (sNNNN) are assigned by `inventory_sources.py` on the archive Mac. Until that Mac is
back, a record that needs a source the registry does not hold yet gets a LOCAL id instead: `L0001`, `L0002`, ...
They live in `sources.json` beside the s-ids (flagged `"_local": true`), so `check_registry.py`, the graph builder and
the page builders treat them like any source. They cannot collide with an s-id.

    python3 scripts/local_sources.py add data/sources/<file> [--url URL] [--title T] [--captured YYYY-MM-DD] [--inn INN ...]
    python3 scripts/local_sources.py list          # pending local sources and who cites them
    python3 scripts/local_sources.py merge         # ARCHIVE MAC: dry run of the L -> s rewrite
    python3 scripts/local_sources.py merge --apply # ARCHIVE MAC: do it

`add` is idempotent: a file whose sha256 is already registered (as an s-id or an L-id) returns that id.

Merge (on the archive Mac, after `git pull` and after copying the files `list` names into data/sources/):
`inventory_sources.py` gives each copied file its s-id in `_source_ids.json` (path -> id). `merge` maps every
L-id to the s-id of the same path (after checking the sha256 of the file on disk), rewrites each quoted "L0001"
in data/registry/*.json, and drops the L records. The notes/ files that cite an L-id are listed, not rewritten.
Full protocol: notes/local_registry_protocol.md.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REG = REPO / "data" / "registry"
SOURCES_JSON = REG / "sources.json"
IDS_JSON = REG / "_source_ids.json"
L_RE = re.compile(r"^L\d{4}$")
# Files that hold ids themselves and are never rewritten.
SKIP = {"sources.json", "_source_ids.json"}


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_sources() -> list:
    return json.loads(SOURCES_JSON.read_text())


def save_sources(rows: list) -> None:
    SOURCES_JSON.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")


def next_local_id(rows: list) -> str:
    nums = [int(r["id"][1:]) for r in rows if L_RE.match(r["id"])]
    return f"L{(max(nums) + 1) if nums else 1:04d}"


def citation_for(rec: dict) -> tuple:
    """(title, public_url) from source_citation.py, the only place those two fields come from."""
    sys.path.insert(0, str(REPO / "scripts"))
    try:
        from source_citation import cite, facts
        return cite(rec, facts(REPO / rec["path"]))
    except Exception as e:   # a file type the citation module cannot read: the caller passes --title
        print(f"note: source_citation could not read {rec['path']} ({type(e).__name__}); pass --title / --public-url")
        return None, None


def cmd_add(a) -> int:
    path = Path(a.path)
    path = path if path.is_absolute() else REPO / path
    if not path.is_file():
        raise SystemExit(f"{path}: no such file")
    rel = path.resolve().relative_to(REPO).as_posix()
    if not rel.startswith("data/sources/"):
        raise SystemExit("a local source lives in data/sources/ (write it with source_files.write_new() first)")
    digest = sha256_of(path)
    rows = load_sources()
    for r in rows:
        if r.get("sha256") == digest:
            print(f"{r['id']}  (already registered)  {rel}")
            return 0
    rec = {"id": next_local_id(rows), "type": None, "path": rel, "url": a.url, "captured_date": a.captured,
           "fiscal_year": None, "as_of": None, "as_of_method": None, "supersedes": None, "superseded_by": None,
           "inns": list(a.inn or []), "entities": [], "sha256": digest, "_verified": False,
           "_origin": "local-mac", "_local": True}
    title, public_url = citation_for(rec)
    rec["title"] = a.title or title
    rec["public_url"] = a.public_url or public_url or a.url
    if not rec["title"]:
        raise SystemExit("no title could be derived: pass --title")
    rows.append(rec)
    save_sources(rows)
    print(f"{rec['id']}  {rel}\n   title: {rec['title']}\n   public_url: {rec['public_url']}")
    return 0


def registry_files():
    return [p for p in sorted(REG.glob("*.json")) if p.name not in SKIP]


def cmd_list(_a) -> int:
    local = [r for r in load_sources() if L_RE.match(r["id"])]
    if not local:
        print("no local sources pending")
        return 0
    texts = {p.name: p.read_text() for p in registry_files()}
    print(f"{len(local)} local source(s) pending merge. Copy these files to data/sources/ on the archive Mac:\n")
    for r in local:
        cited = [n for n, t in texts.items() if f'"{r["id"]}"' in t]
        print(f"{r['id']}  {r['path']}\n   sha256 {r['sha256'][:16]}…  cited in: {', '.join(cited) or 'nothing yet'}")
    return 0


def cmd_merge(a) -> int:
    rows = load_sources()
    ids = json.loads(IDS_JSON.read_text())
    mapping, waiting = {}, []
    for r in rows:
        if not L_RE.match(r["id"]):
            continue
        f = REPO / r["path"]
        sid = ids.get(r["path"])
        if not f.is_file():
            waiting.append((r["id"], r["path"], "file not copied to data/sources/ yet"))
        elif sha256_of(f) != r["sha256"]:
            waiting.append((r["id"], r["path"], "file on disk differs from the one recorded (sha256): stop and look"))
        elif not sid or not re.match(r"^s\d{4}$", sid):
            waiting.append((r["id"], r["path"], "no s-id yet: run inventory_sources.py"))
        else:
            mapping[r["id"]] = sid
    for lid, p, why in waiting:
        print(f"WAIT  {lid}  {p}: {why}")
    for lid, sid in mapping.items():
        print(f"MAP   {lid} -> {sid}")
    if not mapping:
        return 1 if waiting else 0
    touched = 0
    for p in registry_files():
        t = p.read_text()
        n = t
        for lid, sid in mapping.items():
            n = n.replace(f'"{lid}"', f'"{sid}"')
        if n != t:
            touched += 1
            print(f"{'REWRITE' if a.apply else 'would rewrite'}  {p.name}")
            if a.apply:
                p.write_text(n)
    notes = [p.relative_to(REPO).as_posix() for p in (REPO / "notes").rglob("*.md")
             if any(re.search(rf"\b{lid}\b", p.read_text()) for lid in mapping)]
    if notes:
        print("notes that cite an L-id (edit by hand):", ", ".join(notes))
    if a.apply:
        save_sources([r for r in rows if r["id"] not in mapping])
        print(f"done: {len(mapping)} source(s) merged, {touched} file(s) rewritten. Now: extract_registry.py, "
              f"build_relationship_graph.py, check_registry.py")
    else:
        print("dry run: nothing written. Re-run with --apply")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("add")
    p.add_argument("path")
    p.add_argument("--url")
    p.add_argument("--title")
    p.add_argument("--public-url")
    p.add_argument("--captured")
    p.add_argument("--inn", action="append")
    p.set_defaults(fn=cmd_add)
    sub.add_parser("list").set_defaults(fn=cmd_list)
    m = sub.add_parser("merge")
    m.add_argument("--apply", action="store_true")
    m.set_defaults(fn=cmd_merge)
    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
