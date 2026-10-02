#!/usr/bin/env python3
"""Weekly sanctions-list watcher: which registry entities and people appear on
the official EU, US, UK and Swiss lists, matched by their own identifiers.

**Why.** The registry's `sanctions[]` entries are free text, many of them
sourced to an OpenSanctions match rather than to the list itself, and nothing
says when a new designation lands on an entity we already hold. This script
downloads each official list once, finds every entry that carries a registry
ИНН or ОГРН, and reports what changed since the last run and where the list and
the registry disagree.

**What a hit is.** An identifier match: a 10/12-digit ИНН or 13/15-digit ОГРН
from `entities.json` / `people.json` printed in a list entry (OFAC "Tax ID
No.", EU `identification`, SECO and UK registration numbers). A name match is
never counted: names are recorded only as context. A hit is a work item, not a
registry fact; per the hard rule in CLAUDE.md, the entry is read on the
official list and recorded in `sanctions[]` by hand.

**What it does not cover.** Persons rarely carry an ИНН on a list, so most
person listings will not match; their absence here proves nothing. Ukraine's
NSDC register and the GUR portal have no bulk download in this script. Lists
are downloaded once per run (one request each), so the weekly schedule stays
within the live-jobs policy (user go-ahead, 02.10.2026).

Network access is needed for the download step only. The cloud sessions'
egress policy blocks these hosts, so the scheduled run is a GitHub Actions
workflow (`.github/workflows/sanctions-watch.yml`).

Usage:
  python3 scripts/sanctions_watch.py --out watch.json [--previous old.json]
      [--raw-dir DIR] [--only eu,us] [--report report.md]
  python3 scripts/sanctions_watch.py --from-file us=sdn.xml ...   # offline, tests
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REG = ROOT / "data" / "registry"

# One request per list per run. entry_tags: local XML names of one list entry,
# tried in order; the first that occurs in the file is used.
LISTS = {
    "us": {
        "label": "US OFAC SDN list",
        "url": "https://www.treasury.gov/ofac/downloads/sdn.xml",
        "entry_tags": ["sdnEntry"],
        "id_tags": ["uid"],
        "name_tags": ["lastName", "firstName"],
        "program_tags": ["program"],
    },
    "eu": {
        "label": "EU consolidated financial sanctions list",
        "url": "https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content?token=dG9rZW4tMjAxNw",
        "entry_tags": ["sanctionEntity"],
        "id_attrs": ["euReferenceNumber", "logicalId"],
        "name_attrs": ["wholeName"],
        "program_attrs": ["numberTitle", "programme"],
    },
    "ch": {
        "label": "Swiss SECO sanctions list",
        "url": "https://www.sesam.search.admin.ch/sesam-search-web/pages/downloadXmlGesamtliste.xhtml?lang=en&action=downloadXmlGesamtlisteAction",
        "entry_tags": ["target"],
        "id_attrs": ["ssid"],
        "name_tags": ["value"],
        "program_tags": ["sanctions-set-id"],
    },
    "uk": {
        "label": "UK Sanctions List (FCDO)",
        "url": "https://sanctionslist.fcdo.gov.uk/docs/UK-Sanctions-List.xml",
        "entry_tags": ["Designation", "designation", "FinancialSanctionsTarget"],
        "id_tags": ["UniqueID", "UniqueId", "uniqueId", "GroupID"],
        "name_tags": ["Name6", "name6", "Name", "name"],
        "program_tags": ["RegimeName", "regimeName", "Regime"],
    },
}

# Which registry sanctions[].regime strings count as "this list" when comparing.
REGIME_KEYS = {
    "us": re.compile(r"\b(US|OFAC|SDN|EO 14024)\b", re.I),
    "eu": re.compile(r"\b(EU|European Union|Council (Implementing )?Regulation)\b", re.I),
    "ch": re.compile(r"\b(Switzerland|Swiss|SECO|CH)\b", re.I),
    "uk": re.compile(r"\b(UK|GB|United Kingdom|OFSI|FCDO)\b", re.I),
}

ID_RE = re.compile(r"(?<!\d)(\d{15}|\d{13}|\d{12}|\d{10})(?!\d)")
UA = "roymarket-investigation sanctions watcher (weekly, one request per list)"


def ru_id_valid(s: str) -> bool:
    """Control-digit check for a Russian ИНН (10/12) or ОГРН/ОГРНИП (13/15)."""
    d = [int(c) for c in s]
    if len(s) == 10:
        w = [2, 4, 10, 3, 5, 9, 4, 6, 8]
        return sum(a * b for a, b in zip(w, d)) % 11 % 10 == d[9]
    if len(s) == 12:
        w1 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        w2 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        return (sum(a * b for a, b in zip(w1, d)) % 11 % 10 == d[10]
                and sum(a * b for a, b in zip(w2, d)) % 11 % 10 == d[11])
    if len(s) == 13:
        return int(s[:12]) % 11 % 10 == d[12]
    if len(s) == 15:
        return int(s[:14]) % 13 % 10 == d[14]
    return False


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def load_registry() -> dict[str, dict]:
    """Map every identifier to its record: {"7802942873": {slug, kind, name, field}}."""
    ids: dict[str, dict] = {}
    entities = json.loads((REG / "entities.json").read_text(encoding="utf-8"))
    people = json.loads((REG / "people.json").read_text(encoding="utf-8"))
    for e in entities:
        if e.get("_merged_into"):
            continue
        for field in ("inn", "ogrn"):
            v = str(e.get(field) or "").strip()
            if ID_RE.fullmatch(v):
                ids[v] = {"slug": e["slug"], "kind": "entity", "field": field,
                          "name": e.get("name_ru"), "sanctions": e.get("sanctions") or []}
    for p in people:
        if p.get("_merged_into"):
            continue
        v = str(p.get("inn_personal") or "").strip()
        if ID_RE.fullmatch(v):
            ids[v] = {"slug": p["slug"], "kind": "person", "field": "inn_personal",
                      "name": p.get("fio_ru"), "sanctions": p.get("sanctions") or []}
    return ids


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=300) as r:
        return r.read()


def first(el, tags=(), attrs=()) -> str | None:
    for a in attrs:
        for node in el.iter():
            if node.get(a):
                return node.get(a).strip()
    for t in tags:
        for node in el.iter():
            if local(node.tag) == t and (node.text or "").strip():
                return node.text.strip()
    return None


def all_of(el, tags=(), attrs=()) -> list[str]:
    out = []
    for node in el.iter():
        for a in attrs:
            if node.get(a):
                out.append(node.get(a).strip())
        if local(node.tag) in tags and (node.text or "").strip():
            out.append(node.text.strip())
    return sorted(set(out))


def scan(key: str, data: bytes, registry: dict[str, dict]) -> dict:
    """Parse one list. Returns {entries, entry_tag, publish_date, hits[]}."""
    cfg = LISTS[key]
    root = ET.fromstring(data)
    entry_tag = next((t for t in cfg["entry_tags"]
                      if any(local(n.tag) == t for n in root.iter())), None)
    if entry_tag is None:
        raise ValueError(f"{key}: none of {cfg['entry_tags']} found; the list format "
                         f"changed (root <{local(root.tag)}>)")
    publish = None
    for n in root.iter():
        if local(n.tag) in ("Publish_Date", "DateGenerated", "dateGenerated") and n.text:
            publish = n.text.strip()
            break
    if publish is None:
        publish = root.get("generationDate") or root.get("date")

    entries = 0
    with_ru_id = 0  # entries carrying any valid ИНН/ОГРН: how far identifier matching can reach
    hits = []
    for el in root.iter():
        if local(el.tag) != entry_tag:
            continue
        entries += 1
        blob = " ".join([*(v for n in el.iter() for v in n.attrib.values()),
                         *((n.text or "") for n in el.iter())])
        ids_here = ID_RE.findall(blob)
        if any(ru_id_valid(m) for m in ids_here):
            with_ru_id += 1
        found = {m for m in ids_here if m in registry}
        if not found:
            continue
        names = all_of(el, cfg.get("name_tags", ()), cfg.get("name_attrs", ()))
        for ident in sorted(found):
            rec = registry[ident]
            hits.append({
                "list": key,
                "entry_id": first(el, cfg.get("id_tags", ()), cfg.get("id_attrs", ())),
                "identifier": ident,
                "field": rec["field"],
                "slug": rec["slug"],
                "kind": rec["kind"],
                "registry_name": rec["name"],
                "list_names": names[:6],
                "programs": all_of(el, cfg.get("program_tags", ()),
                                   cfg.get("program_attrs", ()))[:6],
            })
    if entries == 0:
        raise ValueError(f"{key}: 0 entries parsed; treat as a parser bug")
    return {"entries": entries, "with_ru_id": with_ru_id, "entry_tag": entry_tag,
            "publish_date": publish, "hits": hits}


def hit_key(h: dict) -> str:
    return f"{h['list']}|{h['slug']}|{h['entry_id']}"


def compare(result: dict, previous: dict | None, registry: dict[str, dict]) -> dict:
    """New / removed hits vs the previous run, and list-vs-registry disagreements."""
    cur = {hit_key(h): h for h in result["hits"]}
    prev = {hit_key(h): h for h in (previous or {}).get("hits", [])}
    scanned = set(result["lists"])
    prev_scanned = set((previous or {}).get("lists", {}))
    new = [cur[k] for k in sorted(cur.keys() - prev.keys())] if previous else []
    removed = [prev[k] for k in sorted(prev.keys() - cur.keys())
               if prev[k]["list"] in scanned and prev[k]["list"] in prev_scanned]

    by_slug: dict[str, set] = {}
    for h in result["hits"]:
        by_slug.setdefault(h["slug"], set()).add(h["list"])
    records = {r["slug"]: r for r in registry.values()}
    not_in_registry, not_on_list = [], []
    for slug, lists in sorted(by_slug.items()):
        text = json.dumps(records[slug]["sanctions"], ensure_ascii=False)
        for lst in sorted(lists):
            if not REGIME_KEYS[lst].search(text):
                not_in_registry.append({"slug": slug, "list": lst,
                                        "name": records[slug]["name"]})
    for slug, rec in sorted(records.items()):
        text = json.dumps(rec["sanctions"], ensure_ascii=False)
        for lst in sorted(scanned):
            if rec["kind"] == "entity" and rec["sanctions"] and REGIME_KEYS[lst].search(text) \
                    and lst not in by_slug.get(slug, set()):
                not_on_list.append({"slug": slug, "list": lst, "name": rec["name"]})
    return {"new": new, "removed": removed,
            "listed_not_in_registry": not_in_registry,
            "registry_claims_not_matched": not_on_list}


def report(result: dict, diff: dict) -> str:
    lines = [f"# Sanctions watch, {result['as_of']}", ""]
    lines.append("| List | Published | Entries | With a Russian ИНН/ОГРН | Registry hits | SHA-256 |")
    lines.append("|---|---|---|---|---|---|")
    for k, v in result["lists"].items():
        if v.get("error"):
            lines.append(f"| {LISTS[k]['label']} | - | - | - | **failed: {v['error']}** | - |")
            continue
        n = sum(1 for h in result["hits"] if h["list"] == k)
        lines.append(f"| {LISTS[k]['label']} | {v.get('publish_date') or '?'} | "
                     f"{v['entries']} | {v.get('with_ru_id', '?')} | {n} | `{v['sha256'][:16]}…` |")

    def block(title, rows, fmt):
        lines.extend(["", f"## {title} ({len(rows)})", ""])
        lines.extend(fmt(r) for r in rows) if rows else lines.append("None.")

    hit_fmt = lambda h: (f"- **{h['list'].upper()}** {h['registry_name']} (`{h['slug']}`, "
                         f"{h['field']} {h['identifier']}), entry {h['entry_id']}; "
                         f"{'; '.join(h['programs']) or 'programme not parsed'}")
    block("New since the last run", diff["new"], hit_fmt)
    block("Gone since the last run", diff["removed"], hit_fmt)
    block("On the list, not in the registry's sanctions[]", diff["listed_not_in_registry"],
          lambda r: f"- **{r['list'].upper()}** {r['name']} (`{r['slug']}`)")
    block("Registry says listed, no identifier match on the list",
          diff["registry_claims_not_matched"],
          lambda r: f"- **{r['list'].upper()}** {r['name']} (`{r['slug']}`): read the "
                    f"registry entry; the list may name it without an ИНН/ОГРН")
    lines.extend(["", "Hits are identifier matches only. Read the entry on the official "
                  "list before recording anything in the registry."])
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, help="write the result JSON here")
    ap.add_argument("--previous", help="the previous run's JSON, for new/removed hits")
    ap.add_argument("--report", help="write a Markdown report here")
    ap.add_argument("--raw-dir", help="keep each downloaded list here, named by list and date")
    ap.add_argument("--only", help="comma-separated subset of: " + ",".join(LISTS))
    ap.add_argument("--from-file", action="append", default=[],
                    help="KEY=PATH: read a list from a local file instead of downloading")
    args = ap.parse_args()

    registry = load_registry()
    keys = args.only.split(",") if args.only else list(LISTS)
    local_files = dict(x.split("=", 1) for x in args.from_file)
    if local_files:
        keys = [k for k in keys if k in local_files]
    now = datetime.now(timezone.utc)
    result = {"as_of": now.strftime("%Y-%m-%d"), "lists": {}, "hits": []}
    failed = 0
    for k in keys:
        cfg = LISTS[k]
        try:
            data = Path(local_files[k]).read_bytes() if k in local_files else fetch(cfg["url"])
            info = {"url": cfg["url"], "sha256": hashlib.sha256(data).hexdigest(),
                    "bytes": len(data), "fetched": now.isoformat(timespec="seconds")}
            if args.raw_dir:
                d = Path(args.raw_dir)
                d.mkdir(parents=True, exist_ok=True)
                (d / f"SANCTIONS_{k.upper()}_{now:%Y%m%d}.xml").write_bytes(data)
            s = scan(k, data, registry)
            info.update(entries=s["entries"], with_ru_id=s["with_ru_id"],
                        entry_tag=s["entry_tag"], publish_date=s["publish_date"])
            result["hits"].extend(s["hits"])
        except Exception as ex:  # one list failing must not hide the others
            failed += 1
            info = {"url": cfg["url"], "error": f"{type(ex).__name__}: {ex}"[:300]}
            print(f"{k}: {info['error']}", file=sys.stderr)
        result["lists"][k] = info
        print(f"{k}: {info.get('entries', 0)} entries "
              f"({info.get('with_ru_id', 0)} with a valid ИНН/ОГРН), "
              f"{sum(1 for h in result['hits'] if h['list'] == k)} registry hits",
              file=sys.stderr)

    previous = None
    if args.previous and Path(args.previous).exists():
        previous = json.loads(Path(args.previous).read_text(encoding="utf-8"))
    scanned = {k: v for k, v in result["lists"].items() if not v.get("error")}
    diff = compare({**result, "lists": scanned}, previous, registry)
    result["diff"] = diff
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n",
                              encoding="utf-8")
    text = report(result, diff)
    if args.report:
        Path(args.report).write_text(text, encoding="utf-8")
    else:
        print(text)
    return 1 if failed == len(keys) else 0


if __name__ == "__main__":
    raise SystemExit(main())
