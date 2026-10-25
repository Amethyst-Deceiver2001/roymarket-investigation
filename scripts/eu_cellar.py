#!/usr/bin/env python3
"""Read EU Official Journal acts through CELLAR (no account) and find a person in the Ukraine-regime listings.

EUR-Lex itself blocks scripts. The EU Publications Office's CELLAR does not: one act by CELEX number, and an open
SPARQL endpoint for metadata. This tool uses both. Tested 25.10.2026 on Regulation 269/2014 (the "territorial
integrity of Ukraine" regime), whose Annex I the EU amends by Council Implementing Regulations.

    python3 scripts/eu_cellar.py acts [--year 2014]
        list the acts based on Regulation 269/2014 (CELEX, date), oldest first
    python3 scripts/eu_cellar.py act 32014R0433
        fetch one act and print where it was saved
    python3 scripts/eu_cellar.py find "Pushylin" "Пушилин" [--year 2014] [--max 30]
        fetch the acts (oldest first, within --year if given) and print every entry that names the person

How `find` works: each act is fetched once into data/sources/_cellar/ (a working folder, not a catalogued source),
the text is searched case-insensitively with ё folded to е, and the entry around each hit is cut out between the
date stamps that bound it (in these acts the listing date closes an entry). The cut is a convenience: read the
act itself before citing it. A hit is a lead until read, a name alone never an identity.

Cap (CLAUDE.md, 25.10.2026): a pull over 30 documents from one service is the user's job. `find` fetches at most
--max (default 30) not yet cached acts per run, says how many it left, and stops. Narrow with --year, or run it
yourself with a higher --max.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import source_files  # noqa: E402

CACHE = ROOT / "data" / "sources" / "_cellar"
SPARQL = "https://publications.europa.eu/webapi/rdf/sparql"
CELEX_URL = "http://publications.europa.eu/resource/celex/"
# The work "Regulation (EU) No 269/2014" (CELEX 32014R0269) in CELLAR: acts "based on" it amend its Annex I.
BASE_WORK = "http://publications.europa.eu/resource/cellar/4295095e-ae10-11e3-86f9-01aa75ed71a1"
STAMP = re.compile(r"\b\d{1,2}\.\d{1,2}\.\d{4}\b")


def sparql(query: str) -> list[dict]:
    body = urllib.parse.urlencode({"query": query}).encode()
    req = urllib.request.Request(SPARQL, data=body, headers={"Accept": "application/sparql-results+json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))["results"]["bindings"]


def list_acts(year: str | None = None) -> list[tuple[str, str]]:
    q = ("PREFIX cdm: <http://publications.europa.eu/ontology/cdm#> SELECT ?celex ?d WHERE { "
         "?w cdm:resource_legal_based_on_resource_legal <" + BASE_WORK + "> . "
         "?w cdm:resource_legal_id_celex ?celex . OPTIONAL { ?w cdm:work_date_document ?d } } ORDER BY ?d")
    rows = []
    for b in sparql(q):
        celex, d = b["celex"]["value"], b.get("d", {}).get("value", "")
        if not celex.startswith("3"):      # 5... are notices and communications, not the regulations
            continue
        if year and not d.startswith(year):
            continue
        rows.append((celex, d))
    return rows


def fetch(celex: str) -> Path | None:
    """The act's XHTML, from the cache or CELLAR. None if CELLAR has no such act."""
    path = CACHE / (celex + ".xhtml")
    if path.exists():
        return path
    req = urllib.request.Request(CELEX_URL + celex, headers={"Accept": "application/xhtml+xml", "Accept-Language": "eng"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            data = r.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    return source_files.write_new(path, data)


def text_of(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", raw)))


def fold(s: str) -> str:
    return s.lower().replace("ё", "е")


def title_of(text: str) -> str:
    m = re.search(r"(COUNCIL|REGULATION)[^.]{0,200}?of \d+ \w+ \d{4}", text)
    return m.group(0) if m else text[:90]


def entries(text: str, names: list[str]) -> list[str]:
    """The entry around each hit, cut between the date stamps that bound it."""
    out, folded = [], fold(text)
    stamps = [m.span() for m in STAMP.finditer(text)]
    seen = set()
    for name in names:
        start = 0
        while True:
            i = folded.find(fold(name), start)
            if i < 0:
                break
            start = i + len(name)
            before = [s for s in stamps if s[1] <= i]
            after = [s for s in stamps if s[0] >= i]
            a = before[-1][1] if before else max(0, i - 200)
            b = after[0][1] if after else min(len(text), i + 1500)
            if (a, b) in seen:
                continue
            seen.add((a, b))
            out.append(text[a:b].strip())
    return out


def cmd_acts(args) -> None:
    rows = list_acts(args.year)
    for celex, d in rows:
        print(celex, d)
    print(len(rows), "acts based on Regulation 269/2014", f"(year {args.year})" if args.year else "")


def cmd_act(args) -> None:
    p = fetch(args.celex)
    print("not found" if p is None else p.relative_to(ROOT))


def cmd_find(args) -> None:
    rows = list_acts(args.year)
    todo = [c for c, _ in rows if not (CACHE / (c + ".xhtml")).exists()]
    fetched = 0
    left = 0
    for idx, (celex, d) in enumerate(rows):
        cached = (CACHE / (celex + ".xhtml")).exists()
        if not cached and fetched >= args.max:
            left += 1
            continue
        p = fetch(celex)
        if not cached:
            fetched += 1
            time.sleep(0.5)
        if p is None:
            continue
        t = text_of(p)
        hits = entries(t, args.names)
        if hits:
            print("=" * 78)
            print(celex, d, "|", title_of(t))
            for h in hits:
                print("  -", h[:1400])
    print("-" * 78)
    print(f"{len(rows)} acts in scope, {fetched} fetched this run, {len(rows) - left - fetched} already cached, {left} not fetched (cap --max {args.max}).")
    if left:
        print("Narrow with --year, or raise --max yourself (a pull over 30 documents is the user's job).")
    del todo


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("acts", help="list the acts based on Regulation 269/2014")
    a.add_argument("--year", default=None)
    a = sub.add_parser("act", help="fetch one act by CELEX number")
    a.add_argument("celex")
    a = sub.add_parser("find", help="find a person in those acts")
    a.add_argument("names", nargs="+", help="spellings to look for (Latin and Cyrillic)")
    a.add_argument("--year", default=None)
    a.add_argument("--max", type=int, default=30)
    args = ap.parse_args()
    {"acts": cmd_acts, "act": cmd_act, "find": cmd_find}[args.cmd](args)


if __name__ == "__main__":
    main()
