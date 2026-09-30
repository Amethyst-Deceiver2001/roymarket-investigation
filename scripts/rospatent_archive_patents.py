#!/usr/bin/env python3
"""Fetch and archive the full documents for every patent this investigation
has identified as a genuine, on-topic hit from the 2026-08-24
`rospatent_searchplatform_search.py` full-roster sweep (see
data/registry/entities.json's rospatent_director_matches[] and the plan file
for the triage that produced this list).

This is a ONE-TIME PROMOTION JOB over a fixed, hand-curated list of 72
doc_ids across 14 entities -- not a recurring screen. The list below was
built by filtering rospatent_director_matches[] for method=patent_holders_filter
(exact entity-name substring match) plus four inventor_field_query hits whose
patentee string exact-matches the entity's own name (own IP filed and found
via a director search rather than a name search). Every other candidate from
the sweep was reviewed and rejected as a common-word/common-name collision
(Гермес, Логос, Площадь, Росс, Прайм, Проммаш, Покров, an ИНФОТЕКС word-order
collision, etc.) -- see the plan file's Phase 2b writeup.

For each doc_id: POST https://searchplatform.rospatent.gov.ru/docs/<doc_id>
(confirmed live, unauthenticated, same API reverse-engineered earlier this
session) and save the full JSON response to
data/sources/PATENT_<document_number><kind>_<YYYYMMDD>_<slug>.json.

This does NOT write corrections.json -- that happens in a separate pass after
a human reads each archived document (abstract/claims/inventors) and confirms
it belongs in patents[]. This script only pulls and archives.

**Live network job against a third-party site, ~72 sequential requests -- per
CLAUDE.md's crawling-jobs policy, tested inline on a handful first, but the
full run should be executed by you, not run in the background.**

After running this:
    python3 scripts/scan_sources.py --out data/sources/MANIFEST.md
    python3 scripts/inventory_sources.py

Usage:
    python3 scripts/rospatent_archive_patents.py                # everything
    python3 scripts/rospatent_archive_patents.py --limit 3       # first 3 only
    python3 scripts/rospatent_archive_patents.py --slug ao-nii-vektor
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SOURCES_DIR = REPO / "data" / "sources"
DOCS_URL = "https://searchplatform.rospatent.gov.ru/docs/{}"
DELAY_SECONDS = 1.5

# (slug, doc_id) pairs -- the curated real-hit list, built from
# rospatent_director_matches[] as described above.
PATENTS: list[tuple[str, str]] = [
    ("ao-kotlin-novator", "RU2851746C1_20251128"),

    ("ao-nii-stt", "RU2644630C1_20180213"),
    ("ao-nii-stt", "RU2637799C1_20171207"),
    ("ao-nii-stt", "RU2758565C9_20211206"),
    ("ao-nii-stt", "RU2663193C1_20180802"),
    ("ao-nii-stt", "RU134783S_20230110"),
    ("ao-nii-stt", "RU2758565C1_20211029"),
    ("ao-nii-stt", "RU2782475C1_20221028"),
    ("ao-nii-stt", "RU2626575C1_20170728"),

    ("ao-nii-vektor", "RU2769566C2_20220404"),
    ("ao-nii-vektor", "RU2279098C1_20060627"),
    ("ao-nii-vektor", "RU2859188C1_20260331"),
    ("ao-nii-vektor", "RU234467U1_20250528"),
    ("ao-nii-vektor", "RU2845089C1_20250813"),
    ("ao-nii-vektor", "RU2741142C2_20210122"),
    ("ao-nii-vektor", "RU2818393C1_20240502"),
    ("ao-nii-vektor", "RU2765196C2_20220126"),
    ("ao-nii-vektor", "RU2746221C2_20210409"),
    ("ao-nii-vektor", "RU203165U1_20210324"),
    ("ao-nii-vektor", "RU2820521C1_20240604"),
    ("ao-nii-vektor", "RU2861850C1_20260513"),
    ("ao-nii-vektor", "RU2858409C1_20260317"),
    ("ao-nii-vektor", "RU2761983C2_20211214"),
    ("ao-nii-vektor", "RU2839399C1_20250430"),
    ("ao-nii-vektor", "RU2860540C1_20260421"),
    ("ao-nii-vektor", "RU2716283C2_20200311"),
    ("ao-nii-vektor", "RU2763583C2_20211230"),
    ("ao-nii-vektor", "RU2752249C2_20210723"),
    ("ao-nii-vektor", "RU2765484C2_20220131"),

    ("npts-elvis", "RU2766442C1_20220315"),
    ("npts-elvis", "RU140982U1_20140520"),
    ("npts-elvis", "RU202224U1_20210208"),
    ("npts-elvis", "RU2698157C1_20190822"),
    ("npts-elvis", "RU2746394C1_20210413"),
    ("npts-elvis", "RU2752861C1_20210811"),
    ("npts-elvis", "RU2689820C1_20190529"),
    ("npts-elvis", "RU2847063C1_20250924"),
    ("npts-elvis", "RU2743886C1_20210301"),
    ("npts-elvis", "RU2790094C1_20230214"),
    ("npts-elvis", "RU2758587C1_20211101"),
    ("npts-elvis", "RU2717950C1_20200327"),
    ("npts-elvis", "RU182852U1_20180904"),
    ("npts-elvis", "RU182981U1_20180906"),
    ("npts-elvis", "RU197098U1_20200330"),
    ("npts-elvis", "RU227818U1_20240807"),
    ("npts-elvis", "RU2700560C1_20190917"),
    ("npts-elvis", "RU2713517C1_20200205"),
    ("npts-elvis", "RU231126U1_20250113"),
    ("npts-elvis", "RU117356S_20191031"),

    ("ooo-trimiks", "RU2826668C1_20240916"),
    ("ooo-kravt-udmurtiya", "RU2858174C1_20260313"),
    ("npp-radar-mms", "RU2705387C1_20191107"),
    ("npp-radar-mms", "RU2722633C1_20200602"),
    ("ooo-tskbr", "RU236504U1_20250811"),
    ("ooo-kleverkopter", "RU134797S_20230110"),
    ("ooo-eyartek", "RU2857656C1_20260304"),
    ("ooo-aeroplatformy", "RU2779484C1_20220907"),
    ("ooo-sibirskaya-navigatsionnaya-kompaniya", "RU2851338C1_20251124"),
    ("ooo-sibirskaya-navigatsionnaya-kompaniya", "RU2856043C1_20260210"),
    ("ooo-tsentr-dinarus", "RU242557U1_20260330"),

    ("ooo-arkodim", "RU214746U1_20221111"),
    ("ooo-arkodim", "RU2696508C1_20190802"),
    ("ooo-arkodim", "RU2793019C1_20230328"),
    ("ooo-arkodim", "RU114291S_20190423"),
    ("ooo-arkodim", "RU213519U1_20220914"),
    ("ooo-arkodim", "RU172336U1_20170704"),
    ("ooo-arkodim", "RU216464U1_20230207"),
    ("ooo-arkodim", "RU2782021C1_20221021"),
    ("ooo-arkodim", "RU209336U1_20220315"),
    ("ooo-arkodim", "RU208483U1_20211221"),
    ("ooo-arkodim", "RU2644608C1_20180213"),
    ("ooo-arkodim", "RU2813430C1_20240212"),
]


def fetch_doc(doc_id: str) -> dict:
    req = urllib.request.Request(
        DOCS_URL.format(doc_id),
        data=json.dumps({}).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def archive_name(slug: str, doc: dict, today: str) -> str:
    common = doc.get("common", {})
    docnum = (common.get("document_number") or "UNKNOWN").replace(" ", "")
    kind = (common.get("kind") or "").replace(" ", "")
    return f"PATENT_RU{docnum}{kind}_{today}_{slug}.json"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--slug", default=None, help="only archive patents for this entity slug")
    args = ap.parse_args()

    today = date.today().isoformat()
    targets = PATENTS
    if args.slug:
        targets = [(s, d) for s, d in targets if s == args.slug]
    if args.limit is not None:
        targets = targets[: args.limit]

    print(f"archiving {len(targets)} patent document(s) ...")
    ok, failed = 0, []
    for i, (slug, doc_id) in enumerate(targets, 1):
        try:
            doc = fetch_doc(doc_id)
        except (urllib.error.URLError, TimeoutError) as ex:
            print(f"  [{i}/{len(targets)}] {slug} {doc_id} FAILED: {ex}")
            failed.append((slug, doc_id))
            time.sleep(DELAY_SECONDS)
            continue

        fname = archive_name(slug, doc, today)
        out_path = SOURCES_DIR / fname
        out_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        biblio = doc.get("biblio", {}).get("ru", {})
        title = biblio.get("title", "?")
        print(f"  [{i}/{len(targets)}] {slug}: wrote {fname} -- {title[:70]}")
        ok += 1
        time.sleep(DELAY_SECONDS)

    print(f"\nDone. {ok} archived, {len(failed)} failed.")
    if failed:
        print("Failed doc_ids (re-run with --slug to retry):")
        for slug, doc_id in failed:
            print(f"  {slug}  {doc_id}")
    print("\nNext: python3 scripts/scan_sources.py --out data/sources/MANIFEST.md")
    print("      python3 scripts/inventory_sources.py")
    print("Then a human reads each archived JSON's abstract/claims/inventors and")
    print("promotes into patents[] via corrections.json -- this script only archives.")


if __name__ == "__main__":
    main()
