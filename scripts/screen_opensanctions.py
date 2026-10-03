#!/usr/bin/env python3
"""Screen every registry entity and person against OpenSanctions' batch
/match/default endpoint (api.opensanctions.org) — aggregates OFAC, EU, UK
OFSI, Ukraine's war-sanctions.gur.gov.ua and many more designation lists,
plus corporate-disqualification and PEP data.

Confirmed working 2026-08-24 (OPENSANCTIONS_API_KEY in .env, tested inline
against Osadchuk — returned an exact, high-confidence match reproducing this
project's own already-cited DOB/sourceUrl data).

**Quota (2026-08-25): the key is a non-commercial `journalist` grant, 150
requests/month, no expiration.** **Corrected 2026-10-02:** this docstring used
to say one /match/default call of up to 20 records costs ONE request. The
user's first run used up the whole month's 150 in one go, so the quota is
evidently counted per record (per query in the batch), not per HTTP call. The
script now budgets per record: `--budget` (default 25) is the number of
records a run may screen. Records are picked never-screened first, then oldest
screen first, and anything screened within `--max-age` days (default 90) is
skipped. `--dry-run` prints the plan without the key or the network.
Batching (BATCH=20) still saves round trips, not quota.

What to spend it on: since 2026-10-02 `sanctions_watch.py` checks the official
EU/US/UK/Swiss lists by identifier for free every week, so this quota is best
kept for what that cannot do: people (lists rarely print a personal ИНН, and
OpenSanctions matches on name + date of birth), regimes the watcher does not
read (Canada, Australia, Japan, Ukraine's NSDC), and new records.

**Licensing (CC BY-NC, per OpenSanctions' 2026-08-25 reply):** quoting a
match in the published brief with attribution is fine under this key;
republishing the dataset itself, or a file derived from it, as a public
download or in a repository requires a commercial license. The archived
snapshots below land in `data/sources/`, which is gitignored — never commit
one directly, and don't fold raw OpenSanctions response bodies into any file
that IS committed (docs/index.html, data/registry/*.json already only ever
carry the hand-curated `matches[]` summary — caption/score/topics/source
URL — not the full response object; keep it that way).

**Live network job against a third-party API — per CLAUDE.md's crawling-jobs
policy, tested inline on a handful of records first (ordinary
reconnaissance), but the full-roster sweep should be run by you, not
executed in the background.**

This does NOT write into `sanctions[]` directly — that field is hand-curated
and source-verified elsewhere in this project (see CLAUDE.md's
sanctions_legal_basis convention), and an automated fuzzy match is a lead,
not a fact, per this project's standing "triage list, not a source" rule
(same discipline as mine_leads.py's output). Matches land in a SEPARATE
field, `opensanctions_matches[]`, plus `opensanctions_screened_at`, written
directly onto entities.json/people.json the same way screen_rom.py writes
`securing_measures[]` — screened data, not a hand correction, so this does
NOT go through corrections.json. A human still has to read each match and
decide whether it upgrades an entity/person's `sanctions[]` array.

Any match scoring >=0.7 (OpenSanctions' own "likely match" threshold) also
gets archived as a primary-source snapshot in data/sources/
(OPENSANCTIONS_<INN-or-slug>_<YYYYMMDD>_<slug>.json), same pattern as
ROM_*.json and EGRULAPI_*.json.

After running this, refresh the pipeline:
    python3 scripts/scan_sources.py --out data/sources/MANIFEST.md
    python3 scripts/inventory_sources.py
    python3 scripts/extract_registry.py
    python3 scripts/check_registry.py

Usage:
    python3 scripts/screen_opensanctions.py --dry-run         # the plan: which records, how much quota
    python3 scripts/screen_opensanctions.py                   # up to 25 records, never-screened first
    python3 scripts/screen_opensanctions.py --only slug-a,slug-b   # just these records
    python3 scripts/screen_opensanctions.py --limit 5         # first 5 only
    python3 scripts/screen_opensanctions.py --kind people      # people only (default: both)
    python3 scripts/screen_opensanctions.py --kind entities
    python3 scripts/screen_opensanctions.py --force            # ignore --max-age (still within --budget)
    python3 scripts/screen_opensanctions.py --budget 10         # screen at most 10 records this run
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from datetime import date, timedelta
from pathlib import Path
from source_files import write_new  # never overwrite a catalogued source

REPO = Path(__file__).resolve().parent.parent
ENTITIES = REPO / "data" / "registry" / "entities.json"
PEOPLE = REPO / "data" / "registry" / "people.json"
SOURCES = REPO / "data" / "sources"
ENV_FILE = REPO / ".env"

API_URL = "https://api.opensanctions.org/match/default?algorithm=best"
MATCH_THRESHOLD_ARCHIVE = 0.7  # OpenSanctions' own "likely match" cutoff
DELAY_SECONDS = 0.5  # batch endpoint is generous, but still a shared service
BATCH = 20  # records per /match/default call: saves round trips, NOT quota (quota is per record)
DEFAULT_BUDGET = 25  # records this run may screen; the key's monthly cap is 150 records in all
DEFAULT_MAX_AGE = 90  # days: a record screened more recently than this is skipped


def load_api_key() -> str:
    key = os.environ.get("OPENSANCTIONS_API_KEY")
    if key:
        return key
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            if line.startswith("OPENSANCTIONS_API_KEY="):
                return line.split("=", 1)[1].strip()
    sys.exit("OPENSANCTIONS_API_KEY not found in environment or .env")


def slugify(name: str) -> str:
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    ascii_name = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_name).strip("-").lower()
    return ascii_name or "record"


def match_batch(api_key: str, queries: dict) -> dict:
    """queries: {query_id: {schema, properties}} — up to ~50 per call is safe."""
    body = json.dumps({"queries": queries}).encode("utf-8")
    req = urllib.request.Request(
        API_URL, data=body, method="POST",
        headers={
            "Authorization": f"ApiKey {api_key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def build_entity_query(e: dict) -> dict:
    props = {"name": [e["name_ru"]]}
    if e.get("name_latin"):
        props["name"].append(e["name_latin"])
    if e.get("inn"):
        props["innCode"] = [e["inn"]]
    if e.get("ogrn"):
        props["registrationNumber"] = [e["ogrn"]]
    props["country"] = ["ru"]
    return {"schema": "Company", "properties": props}


def build_person_query(p: dict) -> dict:
    name = p.get("fio_ru") or p.get("name_latin")
    if not name:
        return None
    props = {"name": [name]}
    if p.get("name_latin") and p["name_latin"] != name:
        props["name"].append(p["name_latin"])
    if p.get("dob"):
        props["birthDate"] = [p["dob"]]
    if p.get("inn_personal"):
        props["idNumber"] = [p["inn_personal"]]
    return {"schema": "Person", "properties": props}


def pending_targets(records: list, kind: str, today: str, force: bool,
                    max_age: int = DEFAULT_MAX_AGE, only: set | None = None) -> list:
    """(record, query) pairs due for screening, never-screened first, then oldest first."""
    cutoff = (date.fromisoformat(today) - timedelta(days=max_age)).isoformat()
    targets = []
    for r in records:
        if r.get("_merged_into"):
            continue
        if only is not None and r.get("slug") not in only:
            continue
        last = (r.get("opensanctions_screened_at") or "")[:10]
        if not force and only is None and last and last > cutoff:
            continue
        q = build_entity_query(r) if kind == "entities" else build_person_query(r)
        if q is None:
            continue
        targets.append((r, q))
    targets.sort(key=lambda rq: (rq[0].get("opensanctions_screened_at") or "")[:10])
    return targets


def requests_needed(n_targets: int) -> int:
    """Quota cost of screening n records: one per record (see the docstring)."""
    return n_targets


def process(targets: list, kind: str, api_key: str, today: str) -> int:
    field_screened = "opensanctions_screened_at"
    field_matches = "opensanctions_matches"

    if not targets:
        print(f"  [{kind}] nothing to do")
        return 0

    print(f"  [{kind}] screening {len(targets)} record(s) in "
          f"{(len(targets) + BATCH - 1) // BATCH} call(s), costing {requests_needed(len(targets))} of the quota ...")
    hit_count = 0
    for start in range(0, len(targets), BATCH):
        chunk = targets[start:start + BATCH]
        queries = {f"q{i}": q for i, (_, q) in enumerate(chunk)}
        try:
            resp = match_batch(api_key, queries)
        except urllib.error.HTTPError as ex:
            if ex.code == 429:
                body = ex.read().decode("utf-8", errors="replace")
                sys.exit(f"    batch {start}-{start+len(chunk)}: HTTP 429 — {body}\n"
                         f"    This is the monthly quota, not a burst limit — retrying won't help until "
                         f"it resets. Stopping (already-screened records from earlier batches were saved).")
            print(f"    batch {start}-{start+len(chunk)} FAILED: HTTP {ex.code}: {ex.reason}")
            time.sleep(DELAY_SECONDS)
            continue
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as ex:
            print(f"    batch {start}-{start+len(chunk)} FAILED: {ex}")
            time.sleep(DELAY_SECONDS)
            continue

        for i, (r, q) in enumerate(chunk):
            qid = f"q{i}"
            result = resp.get("responses", {}).get(qid, {})
            results = result.get("results", [])
            slug = r.get("slug") or slugify(r.get("name_ru") or r.get("fio_ru") or "record")

            matches = []
            for m in results:
                score = m.get("score", 0)
                matches.append({
                    "match_id": m.get("id"),
                    "caption": m.get("caption"),
                    "schema": m.get("schema"),
                    "score": round(score, 4),
                    "topics": (m.get("properties") or {}).get("topics", []),
                    "source_urls": (m.get("properties") or {}).get("sourceUrl", []),
                })

            r[field_matches] = matches
            r[field_screened] = today

            best = max((m["score"] for m in matches), default=0)
            if best >= MATCH_THRESHOLD_ARCHIVE:
                hit_count += 1
                inn_or_slug = r.get("inn") or r.get("inn_personal") or slug
                out = SOURCES / f"OPENSANCTIONS_{inn_or_slug}_{today.replace('-', '')}_{slug}.json"
                out = write_new(out, json.dumps({"query": q, "response": result}, ensure_ascii=False, indent=2))
                print(f"    *** {slug}: best score {best:.2f} — {matches[0]['caption']} — saved {out.name} ***")
            else:
                print(f"    {slug}: best score {best:.2f} (below archive threshold, still recorded)")

        time.sleep(DELAY_SECONDS)

    return hit_count


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--kind", choices=["entities", "people", "both"], default="both")
    ap.add_argument("--force", action="store_true",
                    help="ignore --max-age (still capped by --budget)")
    ap.add_argument("--only", help="comma-separated slugs to screen, whatever their screen date")
    ap.add_argument("--max-age", type=int, default=DEFAULT_MAX_AGE,
                    help=f"skip records screened within this many days (default {DEFAULT_MAX_AGE})")
    ap.add_argument("--budget", type=int, default=DEFAULT_BUDGET,
                    help=f"max records this run may screen (default {DEFAULT_BUDGET}; the key's "
                         "monthly cap is 150 records, shared with any other use of it)")
    ap.add_argument("--dry-run", action="store_true",
                    help="print which records would be screened and the quota cost; no key, no network")
    args = ap.parse_args()

    today = date.today().isoformat()
    only = set(args.only.split(",")) if args.only else None

    entities = json.loads(ENTITIES.read_text(encoding="utf-8")) if args.kind in ("entities", "both") else []
    people = json.loads(PEOPLE.read_text(encoding="utf-8")) if args.kind in ("people", "both") else []

    entity_targets = (entities if args.limit is None else entities[:args.limit]) if entities else []
    people_targets = (people if args.limit is None else people[:args.limit]) if people else []

    due = ([("entities", rq) for rq in pending_targets(entity_targets, "entities", today, args.force,
                                                       args.max_age, only)] +
           [("people", rq) for rq in pending_targets(people_targets, "people", today, args.force,
                                                     args.max_age, only)])
    # One queue across both kinds, never-screened first, then oldest screen first.
    due.sort(key=lambda kr: (kr[1][0].get("opensanctions_screened_at") or "")[:10])
    chosen, deferred = due[:args.budget], due[args.budget:]
    print(f"Due for screening: {len(due)} record(s). This run: {len(chosen)} "
          f"(budget {args.budget}; quota is per record, monthly cap 150). Deferred: {len(deferred)}.")
    for kind, (r, _) in chosen:
        print(f"  {'entity' if kind == 'entities' else 'person'}: {r.get('slug')} "
              f"(last screened {r.get('opensanctions_screened_at') or 'never'})")
    if args.dry_run or not chosen:
        return

    api_key = load_api_key()
    total_hits = 0
    for kind, path, data in (("entities", ENTITIES, entities), ("people", PEOPLE, people)):
        targets = [rq for k, rq in chosen if k == kind]
        if targets:
            total_hits += process(targets, kind, api_key, today)
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"\nDone. {total_hits} record(s) with a likely match (score >= {MATCH_THRESHOLD_ARCHIVE}) archived to data/sources/.")
    print("Every screened record (hit or not) now carries opensanctions_matches[] + opensanctions_screened_at.")
    print("Re-run scripts/check_registry.py, then hand-review matches before promoting anything into sanctions[].")


if __name__ == "__main__":
    main()
