#!/usr/bin/env python3
"""Download and archive the original PDF for every patent document already
pulled via searchplatform.rospatent.gov.ru this investigation (see
data/sources/PATENT_RU*.json, produced by rospatent_archive_patents.py and
earlier ad-hoc pulls).

Each archived JSON doc carries its own `ex_media_list` field -- the exact PDF
directory path on searchplatform's media host, e.g.
"/media/National/RU/C1/2024/09/16/0002826668/" -- confirmed 2026-08-24 by the
user supplying a real PDF URL
(https://searchplatform.rospatent.gov.ru/media/National/RU/C1/2026/03/30/
0002859152//0002859152.pdf) that matches this exact pattern. The PDF filename
is the same 10-digit zero-padded document number + ".pdf", appended with an
extra "/" (confirmed from the working example URL, which has a double slash
before the filename): `ex_media_list + "/" + docnum10 + ".pdf"`.

Confirmed 2026-08-24 inline: works for invention (C1) and utility-model (U1)
kind documents. Industrial-design (S kind, dataset dsgn_ru) documents
consistently 404 at this path (tested on ooo-kleverkopter's RU134797S) --
design registrations are evidently not hosted as a text PDF here. Those are
skipped automatically (ex_media_list present but no PDF exists) and logged,
not treated as a failure to retry.

Writes each PDF to data/sources/PATENT_RU<docnum><kind>_<date>_<slug>.pdf
(same naming/date/slug as the paired .json, just a .pdf extension) --
alongside the existing .json (which stays authoritative for structured
biblio/abstract/claims/description text; the PDF is the primary-document
image for citation/archival completeness).

**Live network job against a third-party site, ~75 sequential PDF downloads
(some multi-MB) -- per CLAUDE.md's crawling-jobs policy, tested inline on a
handful first, but the full run should be executed by you, not run in the
background.**

After running this:
    python3 scripts/scan_sources.py --out data/sources/MANIFEST.md
    python3 scripts/inventory_sources.py

Usage:
    python3 scripts/rospatent_download_pdfs.py                # everything
    python3 scripts/rospatent_download_pdfs.py --limit 5       # first 5 only
"""
from __future__ import annotations

import argparse
import glob
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from source_files import write_new  # never overwrite a catalogued source

REPO = Path(__file__).resolve().parent.parent
SOURCES_DIR = REPO / "data" / "sources"
BASE = "https://searchplatform.rospatent.gov.ru"
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")
DELAY_SECONDS = 1.5


def pdf_url_for(doc: dict) -> str | None:
    ex_media = doc.get("ex_media_list")
    common = doc.get("common", {})
    docnum = (common.get("document_number") or "").strip()
    if not ex_media or not docnum:
        return None
    docnum10 = docnum.zfill(10)
    return f"{BASE}{ex_media}/{docnum10}.pdf"


def fetch_pdf(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    json_files = sorted(glob.glob(str(SOURCES_DIR / "PATENT_RU*.json")))
    if args.limit is not None:
        json_files = json_files[: args.limit]

    print(f"processing {len(json_files)} patent record(s) ...")
    ok, skipped_design, failed = 0, [], []
    for i, jf in enumerate(json_files, 1):
        jpath = Path(jf)
        pdf_path = jpath.with_suffix(".pdf")
        if pdf_path.exists():
            print(f"  [{i}/{len(json_files)}] {jpath.name}: already have PDF, skipping")
            continue

        doc = json.loads(jpath.read_text(encoding="utf-8"))
        url = pdf_url_for(doc)
        if url is None:
            print(f"  [{i}/{len(json_files)}] {jpath.name}: no ex_media_list, skipping")
            continue

        try:
            data = fetch_pdf(url)
        except urllib.error.HTTPError as ex:
            if ex.code == 404 and (doc.get("common", {}).get("kind") or "").strip() == "S":
                print(f"  [{i}/{len(json_files)}] {jpath.name}: 404 (industrial design, expected -- no PDF hosted)")
                skipped_design.append(jpath.name)
            else:
                print(f"  [{i}/{len(json_files)}] {jpath.name}: FAILED {ex}")
                failed.append((jpath.name, url))
            time.sleep(DELAY_SECONDS)
            continue
        except (urllib.error.URLError, TimeoutError) as ex:
            print(f"  [{i}/{len(json_files)}] {jpath.name}: FAILED {ex}")
            failed.append((jpath.name, url))
            time.sleep(DELAY_SECONDS)
            continue

        pdf_path = write_new(pdf_path, data)
        print(f"  [{i}/{len(json_files)}] {jpath.name}: wrote {pdf_path.name} ({len(data)} bytes)")
        ok += 1
        time.sleep(DELAY_SECONDS)

    print(f"\nDone. {ok} PDF(s) archived, {len(skipped_design)} industrial-design records "
          f"skipped (no PDF hosted, expected), {len(failed)} failed.")
    if failed:
        print("Failed (re-run to retry, or investigate individually):")
        for name, url in failed:
            print(f"  {name}  {url}")
    print("\nNext: python3 scripts/scan_sources.py --out data/sources/MANIFEST.md")
    print("      python3 scripts/inventory_sources.py")


if __name__ == "__main__":
    main()
