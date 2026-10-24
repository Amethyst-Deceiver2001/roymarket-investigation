#!/usr/bin/env python3
"""Derive a ЦБСТ residency / accelerator roster from the archive when no official list exists.

Reuses the sweep in `cbst_resident_sweep.py` (the word «резидент…» or the accelerator words
near a ЦБСТ token or inside ЦБСТ's own channel) and, for every registry entity the sweep
resolves, splits the evidence into two grades:

  company   the post names the company itself (legal name, brand or history name) beside the
            word: «КРАМС - резидент АНО «ЦБСТ»». The only grade that can become a membership,
            and only after the post is read in full.
  product   the post names only one of the entity's products («Скворец» in a list of residents'
            drones). A lead, never a membership.

A derived roster is a reading aid: a hit proves the post says it, not that the status is
current, and several channels repeating one ЦБСТ post are one statement. Posts in ЦБСТ's own
channel are its own statement; forwards in other channels are the same text, not a second source.

Local processing over data/roymarket.db and the registry, no network, about a minute.

    python3 scripts/cbst_roster_derive.py --out /path/roster.json
    python3 scripts/cbst_roster_derive.py --kind accelerator --out /path/acc.json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cbst_resident_sweep as S  # noqa: E402
import tg_post_coverage as T  # noqa: E402

SELF = {"ano-tsbst-centre-for-unmanned-systems-technologies", "fond-nasha-pravda"}


def derive(kind: str):
    rows, chans = T.load_posts(None)
    S.ACTIVE["word"] = S.KINDS[kind]
    S.ACTIVE["kind"] = kind
    ok, msg = T.positive_control(rows)
    if not ok or not rows:
        raise SystemExit(f"ABORT: positive control failed ({msg}).")
    entities = json.load(open(S.REGISTRY / "entities.json", encoding="utf-8"))
    items, n_ctx = S.sweep(rows, chans, entities)
    idx = S.index_registry(entities)
    roster = defaultdict(lambda: {"company": {}, "product": {}})
    for it in items:
        hits = idx.get(it["key"]) or []
        for slug, how, _tie in hits:
            if slug in SELF:
                continue
            bucket = "company" if how == "entity" else "product"
            for (cid, mid), p in it["posts"].items():
                roster[slug][bucket].setdefault(f"{p['chan']}/{p['msg']}", {
                    "name": it["name"], "chan": p["chan"], "msg": p["msg"], "date": p["date"],
                    "archived": p["archived"], "direct": it["direct"] > 0, "ctx": p["ctx"]})
    return roster, n_ctx, len(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--kind", choices=sorted(S.KINDS), default="resident")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    roster, n_ctx, n_rows = derive(a.kind)
    out = {slug: {k: sorted(v.values(), key=lambda x: x["date"]) for k, v in d.items()} for slug, d in roster.items()}
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    nc = sum(1 for d in out.values() if d["company"])
    print(f"{n_rows} posts scanned, {n_ctx} with the trigger word in ЦБСТ context; {len(out)} registry entities resolved, "
          f"{nc} named by company, {len(out) - nc} by product only. wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
