#!/usr/bin/env python3
"""Match the registry's identifiers against an export of Ukraine's State Register of Sanctions (DRS).

The register's site and API block automated requests, so the user downloads the four CSV exports by hand
(legal / individual subjects and actions). This reads the subject files and reports every subject whose
reg_id or tax_id field carries an ИНН or ОГРН held by an entity (inn, ogrn) or a person (inn_personal) in the
registry. Matching is on the full identifier only, never on a name. A hit is a work item: the subject row is
then read and recorded in the entity's sanctions[] by hand.

    ~/.venvs/roymarket311/bin/python scripts/drs_match.py data/sources/DRS_<date>_…-legal-subjects.tsv \\
        data/sources/DRS_<date>_…-individual-subjects.tsv [--out report.json]
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
csv.field_size_limit(sys.maxsize)


def registry_ids():
    ids = {}
    for e in json.loads((REPO / "data" / "registry" / "entities.json").read_text()):
        for k in ("inn", "ogrn"):
            if e.get(k):
                ids.setdefault(str(e[k]), []).append(("entity", e["slug"], k))
    for p in json.loads((REPO / "data" / "registry" / "people.json").read_text()):
        v = p.get("inn_personal") or p.get("inn")
        if v:
            ids.setdefault(str(v), []).append(("person", p.get("slug") or p.get("id"), "inn_personal"))
    return ids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("subjects", nargs="+", help="DRS subject exports (tab-separated)")
    ap.add_argument("--out")
    a = ap.parse_args()
    ids = registry_ids()
    hits = []
    for f in a.subjects:
        with open(f, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh, delimiter="\t"):
                found = set(re.findall(r"\d{10,15}", (row.get("reg_id") or "") + " " + (row.get("tax_id") or "")))
                for n in found & ids.keys():
                    for kind, slug, field in ids[n]:
                        hits.append({"file": Path(f).name, "sid": row["sid"], "name": row["name"], "status": row.get("status"),
                                     "identifier": n, "field": field, "kind": kind, "slug": slug,
                                     "last_action_decree": row.get("last_action_decree"), "decree_date": row.get("decree_date"),
                                     "decree_appendix": row.get("decree_appendix"), "position": row.get("position_in_appendix"),
                                     "active_sanctions": (row.get("active_sanctions") or "")[:300]})
    hits.sort(key=lambda h: (h["kind"], h["slug"]))
    for h in hits:
        print(f'{h["kind"]:6} {h["slug"]:45} {h["field"]:12} {h["identifier"]:15} sid {h["sid"]:6} {h["status"]:8} '
              f'{h["last_action_decree"]} {h["decree_date"]}')
    print(f"{len(hits)} hit(s) on {len({(h['kind'], h['slug']) for h in hits})} record(s); {len(ids)} identifiers searched")
    if a.out:
        Path(a.out).write_text(json.dumps(hits, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
