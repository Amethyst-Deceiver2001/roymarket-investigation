#!/usr/bin/env python3
"""Fetch a patent / utility model / industrial design document from FIPS's
classic doc-view servlet, given a document number.

FIPS serves human-readable bibliographic+abstract+claims pages at a fixed
URL pattern per registry (DB=). Known codes:
    RUPM   Полезная модель (utility model)      — e.g. RU218475U1
    RUPAT  Изобретение (invention/patent)         — e.g. RU2723203C1
    RUTM   Товарный знак (trademark)              — use rospatent_tm_search.py
            instead for bulk lookups; this also works for a single known
            registration number.
    RUDIZ  Промышленный образец (industrial design)

Usage:
    python3 scripts/fips_patent_lookup.py RUPM 218475
    python3 scripts/fips_patent_lookup.py RUPAT 2723203
    python3 scripts/fips_patent_lookup.py --db RUTM --number 982517

If you only have the searchplatform.rospatent.gov.ru/doc/<id> URL (e.g.
RU218475U1_20230529), pass it directly with --doc-id and this script will
parse out the DB code and number itself.

Prints the cleaned bibliographic + abstract + claims text. Pipe through
extract_ids.py to pull any ИНН/ОГРН/named individuals it contains:
    python3 scripts/fips_patent_lookup.py RUPM 218475 | python3 scripts/extract_ids.py
"""
import argparse
import re
import sys
import ssl
import urllib.request

_UNVERIFIED_CTX = ssl.create_default_context()
_UNVERIFIED_CTX.check_hostname = False
_UNVERIFIED_CTX.verify_mode = ssl.CERT_NONE

BASE_URL = "https://www1.fips.ru/fips_servl/fips_servlet"

DOC_ID_RE = re.compile(r"^RU(\d+)([A-Z]\d)_\d+$")

# doc-type suffix -> likely DB code, used only to help guess when parsing
# a searchplatform doc id; RUPM/RUPAT still need disambiguation since both
# exist for the same number range historically, so this is a starting guess
# and the caller should retry the other DB on a miss.
SUFFIX_DB_GUESS = {
    "U1": "RUPM",
    "C1": "RUPAT",
    "C2": "RUPAT",
    "S": "RUDIZ",
}


def parse_doc_id(doc_id: str):
    m = DOC_ID_RE.match(doc_id)
    if not m:
        sys.exit(f"Could not parse doc id: {doc_id!r} (expected RU<number><suffix>_<date>)")
    number, suffix = m.group(1), m.group(2)
    db = SUFFIX_DB_GUESS.get(suffix, "RUPAT")
    return db, number


def fetch(db: str, number: str) -> str:
    url = f"{BASE_URL}?DB={db}&DocNumber={number}&TypeFile=html"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30, context=_UNVERIFIED_CTX) as resp:
        raw = resp.read()
    try:
        return raw.decode("cp1251")
    except UnicodeDecodeError:
        return raw.decode("utf-8", errors="replace")


def clean(html: str) -> str:
    html = re.sub(r"<style[^>]*>.*?</style>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", html)
    text = text.replace("&laquo;", "«").replace("&raquo;", "»")
    text = text.replace("&nbsp;", " ").replace("&mdash;", "—")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return text.strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("db", nargs="?", help="DB code, e.g. RUPM, RUPAT, RUTM, RUDIZ")
    ap.add_argument("number", nargs="?", help="document number, e.g. 218475")
    ap.add_argument("--doc-id", help="searchplatform.rospatent.gov.ru doc id, e.g. RU218475U1_20230529")
    args = ap.parse_args()

    if args.doc_id:
        db, number = parse_doc_id(args.doc_id)
        print(f"Guessed DB={db} number={number} from doc id (retry other DB if this 404s)", file=sys.stderr)
    elif args.db and args.number:
        db, number = args.db, args.number
    else:
        sys.exit("Provide either DB + number, or --doc-id")

    html = fetch(db, number)
    text = clean(html)
    if "Нет номера документа" in text or len(text) < 200:
        sys.exit(f"No document found for DB={db} number={number} — try a different DB code")
    print(text)


if __name__ == "__main__":
    main()
