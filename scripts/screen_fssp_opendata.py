#!/usr/bin/env python3
"""Cross-check entity ИНН against ФССП's own **open-data** bulk CSV export
of the legal-entity enforcement-proceedings registry — a genuinely
different, unauthenticated route into the same data as the captcha-gated
`fssp.gov.ru/iss/ip` search UI (already Tier C in notes/SOURCE_REGISTER.md).

**How this was found (2026-09-06/07)**: `opendata.fssp.gov.ru`'s SPA shell
calls `GET /api/ssp-open_data/data-sets?perPage=N`, a plain JSON:API-style
endpoint, no auth, no captcha. One of its 33 published datasets —
identifier `7709576929-iplegallist`, "Общедоступные сведения банка данных
исполнительных производств в отношении юридических лиц" — is exactly the
debt-enforcement data for legal entities, published daily, with columns
including "Наименование юридического лица", "Сумма долга", "Остаток
непогашенной задолженности", and critically **"Debtor TIN"** (ИНН).
Confirmed real via direct download of a byte-range sample. The dataset's
own structure/data URLs are discovered dynamically (see `discover()`
below) rather than hardcoded, since the data filename embeds its publish
timestamp and changes daily.

**Scale note — this is a genuinely large file (~1.95GB as of 2026-09-06),
not a small bulk dataset like the Roscosmos/ФСТЭК pulls.** At this
sandbox's observed throughput (~420KB/s) a full download takes over an
hour. Per CLAUDE.md's crawling-jobs and long-running-job conventions, this
is handed to the user to run in their own terminal, not something to
background from here. The script streams the CSV via `curl` piped into a
CSV parser rather than saving the full file to disk first, matching rows
against the registry's ИНН as they arrive, so it never needs 1.95GB of
local disk space.

No individuals (физлица) equivalent dataset exists in this catalogue —
ФССП's open-data export only covers legal entities, consistent with
personal-debt privacy protections elsewhere in this project.

Usage:
    python3 scripts/screen_fssp_opendata.py
    python3 scripts/screen_fssp_opendata.py --local-csv /path/to/already-downloaded.csv
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTITIES = REPO / "data" / "registry" / "entities.json"
OUT = REPO / "data" / "registry" / "_fssp_debt_hits.json"

API_BASE = "https://opendata.fssp.gov.ru/api/ssp-open_data"
DATASET_ID = "dc22d088-898e-428a-bfc4-33526f15dfba"  # 7709576929-iplegallist
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def discover_data_url() -> str:
    req = urllib.request.Request(f"{API_BASE}/data-sets/{DATASET_ID}", headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    versions = data["data"]["versions"]["data"]
    return versions[0]["url"]  # first entry is the most recent publish


def iter_rows_from_stream(stream) -> "csv.DictReader":
    text_stream = io.TextIOWrapper(stream, encoding="utf-8", errors="replace")
    return csv.DictReader(text_stream)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--local-csv", help="Use an already-downloaded CSV instead of streaming from the live URL")
    args = ap.parse_args()

    entities = json.loads(ENTITIES.read_text(encoding="utf-8"))
    by_inn = {e["inn"]: e["slug"] for e in entities if e.get("inn")}
    print(f"Matching against {len(by_inn)} known entity ИНН.")

    if args.local_csv:
        f = open(args.local_csv, "rb")
        reader = iter_rows_from_stream(f)
    else:
        url = discover_data_url()
        print(f"Streaming {url} ...")
        proc = subprocess.Popen(
            ["curl", "-sk", "-A", UA, url],
            stdout=subprocess.PIPE,
        )
        reader = iter_rows_from_stream(proc.stdout)

    hits: dict[str, list[dict]] = {}
    n = 0
    for row in reader:
        n += 1
        inn = (row.get("Debtor TIN") or "").strip()
        if inn in by_inn:
            slug = by_inn[inn]
            hits.setdefault(slug, []).append({
                "debtor_name": row.get("The name of the debtor"),
                "proceeding_number": row.get("The number of enforcement proceeding"),
                "institution_date": row.get("Date of the institution of proceeding"),
                "document_type": row.get("The executive document type"),
                "execution_object": row.get("The object of the execution"),
                "amount_due": row.get("Amount due"),
                "debt_remaining": row.get("Debt remaining balance"),
                "bailiff_department": row.get("Departments of bailiffs"),
                "inn": inn,
            })
            print(f"  [{n}] HIT {slug} ({inn}): {row.get('The object of the execution')} — due {row.get('Amount due')}, remaining {row.get('Debt remaining balance')}")
        if n % 200000 == 0:
            print(f"  ... {n} rows scanned, {len(hits)} entities hit so far", file=sys.stderr)

    print(f"\n{n} total rows scanned. {len(hits)} entities hit.")
    OUT.write_text(json.dumps(hits, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
