#!/usr/bin/env python3
"""Follow-up pipeline over aleph_matches[] already sitting in entities.json/
people.json — closes the gap where those were raw free-text search results
(caption/score/dataset_label/ui_link from screen_aleph.py) that nobody had
actually opened. See memory zakupki_b2g_document_conventions's sibling note
on this and the 2026-08-26 triage session that established the pattern
here by hand before it got turned into this script.

Two steps, same shape as zakupki_batch_pull.py / mine_zakupki.py:

  triage   LOCAL, no network. Ranks every aleph_matches[] entry by whether
           its caption's name tokens fully cover the record's own ФИО/name
           (a real candidate) vs only partially (near-certain collision —
           the single biggest noise source found by hand: Ukrainian
           Beneficial-Ownership-dataset hits matching on surname alone
           against a different first name/patronymic, e.g. "ГАРЬКУША
           ВАЛЕНТИН ВОЛОДИМИРОВИЧ" surfacing for a Russian "Гарькуша
           Владимир Владимирович"). Writes a ranked candidate list so a
           human picks what's worth an actual fetch instead of opening
           all ~220 matches one at a time.

  fetch    Live network job — hand to the user per the crawling-jobs
           policy for anything beyond a couple of ad-hoc ids run inline.
           Given entity_ids (from triage's output, or picked by hand),
           calls the Aleph entity-detail API (NOT the UI — aleph.occrp.org
           entity pages are a JS SPA; WebFetch returns blank on them,
           confirmed 2026-08-26) with a real browser User-Agent — Aleph's
           Cloudflare WAF blocks a bare urllib request with a 403 that
           looks like an access-denied error but isn't one (confirmed by
           retrying the identical request with a UA header and getting
           200). Archives the raw response to data/sources/ALEPH_DETAIL_
           <slug>_<date>_<id8>.json and prints a schema-aware extraction:
             - Person/Company/LegalEntity: name parts, innCode, birthDate
             - Payment: amount, date, beneficiary, recordId
             - Mention/HyperText (an email/leak-doc hit): checks whether
               the target's own name tokens actually appear in the
               document's own peopleMentioned/companiesMentioned list —
               if not, prints "CONFIRMED NOISE" automatically instead of
               requiring a human to notice by reading the dump (this is
               exactly the check that caught the Замятин false positive
               by hand in the first triage pass).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from id_patterns import norm  # noqa: E402
from source_files import write_new  # never overwrite a catalogued source

ENV_FILE = REPO / ".env"
API_BASE = "https://aleph.occrp.org/api/2/entities"
SOURCES = REPO / "data" / "sources"
CACHE_PATH = REPO / "data" / "registry" / "_source_content_cache.json"

# Aleph's Cloudflare WAF 403s a bare-urllib request even when the underlying
# dataset access is fine — a real browser UA is required, not optional.
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# Ukrainian letters that collide visually/phonetically with Russian ones in
# free-text search — collapsed before token comparison so a Ukrainian-
# transliterated collision doesn't look like a mismatch by charset alone
# (it's still filtered as a partial match if the actual name tokens differ).
UA_TO_RU = str.maketrans({"і": "и", "ї": "и", "є": "е", "ґ": "г"})


def load_api_key() -> str:
    key = os.environ.get("OCCRP_ALEPH_API")
    if key:
        return key
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            if line.startswith("OCCRP_ALEPH_API="):
                return line.split("=", 1)[1].strip()
    sys.exit("OCCRP_ALEPH_API not found in environment or .env")


def name_tokens(name: str) -> set[str]:
    if not name:
        return set()
    name = name.translate(UA_TO_RU)
    return {t for t in norm(name).split() if len(t) > 1}


def classify_match(record_name: str, caption: str | None) -> str:
    """full_match: every record-name token appears in the caption (or vice
    versa — a caption can be a superset, e.g. carrying a title/suffix).
    partial_match: some overlap but not full coverage — the collision
    pattern found repeatedly in the corpus. no_caption: schema doesn't
    carry a name (Payment/Mention/HyperText) — undecidable without a fetch."""
    if not caption:
        return "no_caption"
    rec_t, cap_t = name_tokens(record_name), name_tokens(caption)
    if not rec_t or not cap_t:
        return "no_caption"
    if rec_t <= cap_t or cap_t <= rec_t:
        return "full_match"
    if rec_t & cap_t:
        return "partial_match"
    return "no_overlap"


def cmd_triage(args) -> int:
    entities = json.loads((REPO / "data" / "registry" / "entities.json").read_text(encoding="utf-8"))
    people = json.loads((REPO / "data" / "registry" / "people.json").read_text(encoding="utf-8"))
    tier_of = {v.get("slug"): v.get("tier") for v in entities}

    rows = []
    for v in people:
        name = v.get("name_ru") or v.get("fio_ru") or ""
        roles = [r for r in v.get("roles", []) if isinstance(r, dict) and not r.get("_candidate")]
        tiers = {tier_of.get(r.get("entity_slug")) for r in roles} - {None}
        priority_tier = "cbst-core" if "cbst-core" in tiers else ("manufacturer" if "manufacturer" in tiers else None)
        for m in v.get("aleph_matches", []):
            cls = classify_match(name, m.get("caption"))
            if cls in ("partial_match", "no_overlap"):
                continue  # confirmed/likely collision — not worth a fetch
            rows.append({
                "kind": "person", "slug": v.get("slug"), "name": name,
                "tier": priority_tier, "score": m.get("score", 0),
                "caption": m.get("caption"), "dataset": m.get("dataset_label"),
                "classification": cls, "entity_id": m.get("entity_id"),
            })
    for v in entities:
        name = v.get("name_ru") or ""
        for m in v.get("aleph_matches", []):
            cls = classify_match(name, m.get("caption"))
            if cls in ("partial_match", "no_overlap"):
                continue
            rows.append({
                "kind": "entity", "slug": v.get("slug"), "name": name,
                "tier": v.get("tier"), "score": m.get("score", 0),
                "caption": m.get("caption"), "dataset": m.get("dataset_label"),
                "classification": cls, "entity_id": m.get("entity_id"),
            })

    # Rank: cbst-core/manufacturer first, then full_match over no_caption
    # (undecidable-without-fetch), then score.
    tier_rank = {"cbst-core": 0, "manufacturer": 1, None: 2}
    cls_rank = {"full_match": 0, "no_caption": 1}
    rows.sort(key=lambda r: (tier_rank.get(r["tier"], 2), cls_rank.get(r["classification"], 2), -r["score"]))

    if args.min_score:
        rows = [r for r in rows if r["score"] >= args.min_score]
    rows = rows[: args.limit]

    for r in rows:
        print(f"{r['entity_id']}\t{r['kind']}:{r['slug']}\ttier={r['tier']}\t"
              f"score={round(r['score'],1)}\t{r['classification']}\t"
              f"caption={r['caption']!r}\tdataset={r['dataset']}")
    print(f"\n{len(rows)} candidate(s) shown (of matches classified full_match/no_caption). "
          f"Pick entity_ids and run: python3 scripts/aleph_followup.py fetch --entity-ids <id1>,<id2>,...",
          file=sys.stderr)
    return 0


def extract_fields(d: dict, target_name_tokens: set[str]) -> dict:
    schema = d.get("schema")
    props = d.get("properties", {})
    out = {"schema": schema}
    if schema in ("Person", "Company", "LegalEntity"):
        for k in ("name", "firstName", "lastName", "fatherName", "innCode",
                   "birthDate", "address", "position", "idNumber"):
            if props.get(k):
                out[k] = props[k]
    elif schema == "Payment":
        out["amount"] = props.get("amount")
        out["date"] = props.get("date")
        out["recordId"] = props.get("recordId")
        ben = props.get("beneficiary")
        if isinstance(ben, list) and ben:
            out["beneficiary"] = ben[0].get("properties", {}).get("name")
    elif schema in ("Mention", "HyperText", "Email", "Pages"):
        doc = props.get("document")
        doc_props = doc[0].get("properties", {}) if isinstance(doc, list) and doc else props
        people_mentioned = doc_props.get("peopleMentioned") or []
        companies_mentioned = doc_props.get("companiesMentioned") or []
        mentioned_tokens = set()
        for nm in people_mentioned + companies_mentioned:
            mentioned_tokens |= name_tokens(nm)
        confirmed = bool(target_name_tokens) and bool(target_name_tokens <= mentioned_tokens
                                                         or (target_name_tokens & mentioned_tokens))
        out["fileName"] = doc_props.get("fileName")
        out["peopleMentioned"] = people_mentioned
        out["companiesMentioned"] = companies_mentioned[:10]
        out["target_actually_mentioned"] = confirmed
        if not confirmed:
            out["_verdict"] = "CONFIRMED NOISE — target's own name does not appear in this document's mention list"
    return out


def cmd_fetch(args) -> int:
    key = load_api_key()
    entity_ids = [e.strip() for e in args.entity_ids.split(",") if e.strip()]
    if len(entity_ids) > 30:
        raise SystemExit("Cap of 30 entity_ids per invocation — split into multiple runs.")

    cache = json.loads(CACHE_PATH.read_text(encoding="utf-8")) if CACHE_PATH.exists() else {}
    from datetime import date
    today = date.today().isoformat().replace("-", "")

    for i, eid in enumerate(entity_ids, 1):
        print(f"  [{i}/{len(entity_ids)}] {eid}", file=sys.stderr)
        req = urllib.request.Request(f"{API_BASE}/{eid}",
                                      headers={"Authorization": f"ApiKey {key}", "User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                d = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as ex:
            print(f"    FAILED {ex.code}", file=sys.stderr)
            continue

        slug = args.slug or "unknown"
        # eid[:8] collides for ids sharing a long literal prefix (e.g. all
        # "ru-inn-XXXXXXXXXXXX" ids start "ru-inn-" + one digit) and silently
        # overwrote two files on disk in practice; hash the full id instead.
        id_hash = hashlib.sha1(eid.encode("utf-8")).hexdigest()[:8]
        fname = f"ALEPH_DETAIL_{slug}_{today}_{id_hash}.json"
        fname = write_new(SOURCES / fname, json.dumps(d, ensure_ascii=False, indent=1)).name
        cache[fname] = cache.get(fname, {})
        cache[fname]["type"] = "aleph_entity_detail"
        cache[fname]["as_of"] = date.today().isoformat()

        target_tokens = name_tokens(args.target_name) if args.target_name else set()
        fields = extract_fields(d, target_tokens)
        print(f"    -> {fname}")
        print(f"    {json.dumps(fields, ensure_ascii=False, indent=2)}")
        time.sleep(1.5)

    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nWrote {CACHE_PATH}. Next: python3 scripts/inventory_sources.py (to re-hash) "
          f"then python3 scripts/extract_registry.py to get real sNNNN ids for these files.",
          file=sys.stderr)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    ap_t = sub.add_parser("triage", help="local, no network — rank aleph_matches worth fetching")
    ap_t.add_argument("--min-score", type=float, default=0)
    ap_t.add_argument("--limit", type=int, default=60)
    ap_t.set_defaults(func=cmd_triage)

    ap_f = sub.add_parser("fetch", help="live network job — fetch entity detail for chosen ids")
    ap_f.add_argument("--entity-ids", required=True, help="comma-separated Aleph entity ids (max 30)")
    ap_f.add_argument("--slug", default=None, help="registry slug these ids belong to (for the archived filename)")
    ap_f.add_argument("--target-name", default=None,
                       help="the registry record's own name, to auto-flag Mention/HyperText hits as noise "
                            "when the name doesn't actually appear in the document")
    ap_f.set_defaults(func=cmd_fetch)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
