#!/usr/bin/env python3
"""Find names that a channel removed or changed in a post after other channels had forwarded it.

**Why this exists.** `data/roymarket.db` stores each post as it stood when scraped. A channel can
edit a post afterwards, and a forward made before the edit keeps the original wording. On
2026-10-01 a comparison of ЦБСТ's own posts against their forwards in other channels found:

  * post 2080 (17.04.2026): ЦБСТ now says «Компания из Санкт-Петербурга»; mil_hub's forward of the
    same day says «Петербургская компания «Титан Северо-Запад»» (ЦБСТ edited the post on 20.04.2026,
    and the company is sanctioned);
  * post 410: «противника («Площадь», «Стратим»)» became «противника.»;
  * post 1270: «СуперХроно» became «СХ».

Only forwards can expose this (284 forwards of 253 ЦБСТ posts, about 11% of the channel), so a
clean result proves nothing about the other 89%. The script says so in its header line.

It compares the names written inside «guillemets» and Latin brand names, folded for case, ё and
hyphen spacing (so «БАРС-Курск» vs «Барс-Курск» is not a difference), and prints for each flagged
pair whether the forward was made before the origin's last edit.

Local processing over the DB, no network.

Usage:
    python3 scripts/tg_forward_diff.py                       # forwards of ЦБСТ posts
    python3 scripts/tg_forward_diff.py --origin tulaovod     # forwards of another channel
    python3 scripts/tg_forward_diff.py --show-words          # also print the word-level diff
    python3 scripts/tg_forward_diff.py --out diff.md

A flagged name is a lead to read in both posts, not proof of intent: people edit for style, and the
forward can carry extra text. Archive both copies (TGPOST) before citing either.
"""
from __future__ import annotations

import argparse
import difflib
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tg_post_coverage as T  # noqa: E402

QUOTED = re.compile(r"«([^»]{2,60})»")
LATIN = re.compile(r"\b([A-Z][A-Za-z0-9]{3,}(?: [A-Z][A-Za-z0-9]+)?)\b")


def canon(name: str) -> str:
    return re.sub(r"[^0-9a-zа-я]+", " ", T.fold(name)).strip()


def names(text: str) -> dict[str, str]:
    """canonical -> display, for quoted and Latin names in a text."""
    out: dict[str, str] = {}
    for m in QUOTED.finditer(text or ""):
        out.setdefault(canon(m.group(1)), m.group(1))
    for m in LATIN.finditer(text or ""):
        out.setdefault(canon(m.group(1)), m.group(1))
    return {k: v for k, v in out.items() if len(k) >= 2}


def compare(origin_text: str, forward_text: str):
    """(removed, added): names only in the forward (gone from the origin now), names only in the origin."""
    o, f = names(origin_text), names(forward_text)
    return ({k: f[k] for k in f if k not in o}, {k: o[k] for k in o if k not in f})


def word_diff(a: str, b: str) -> list[str]:
    x, y = re.findall(r"\S+", a or ""), re.findall(r"\S+", b or "")
    out = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, x, y, autojunk=False).get_opcodes():
        if tag != "equal":
            out.append(f"{tag}: origin now «{' '.join(x[i1:i2])}» | forward «{' '.join(y[j1:j2])}»")
    return out


def pairs(con, origin_id: int):
    origin = {r[0]: r for r in con.execute(
        "select msg_id,text,date,edited_date from tg_posts where channel_id=? and text is not null", (origin_id,))}
    q = ("select ch.username,p.msg_id,p.text,p.date,p.edited_date,p.fwd_msg_id from tg_posts p "
         "join tg_channels ch on ch.id=p.channel_id where p.is_forward=1 and p.fwd_channel_id=? and p.text is not null")
    for user, mid, text, fdate, fedit, oid in con.execute(q, (origin_id,)):
        if oid in origin:
            yield user, mid, text, fdate, fedit, origin[oid]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--origin", default="ANO_CBST", help="origin channel username or id (default ЦБСТ)")
    ap.add_argument("--show-words", action="store_true")
    ap.add_argument("--out")
    args = ap.parse_args()
    if not T.DB.exists():
        sys.exit(f"{T.DB} missing")
    con = sqlite3.connect(f"file:{T.DB}?mode=ro", uri=True)
    chans = {r[0]: (r[1], r[2]) for r in con.execute("select id,username,title from tg_channels")}
    oid = T.resolve_channel(args.origin, chans)
    total = con.execute("select count(*) from tg_posts where channel_id=?", (oid,)).fetchone()[0]

    # positive control: a forward compared with itself must show no difference, and a known rename must
    control_ok = compare("Компания «Титан» и Acme Corp", "Компания «Титан» и Acme Corp") == ({}, {}) and \
        "титан северо запад" in compare("Компания из города", "Компания «Титан Северо-Запад»")[0]
    if not control_ok:
        print("ABORT: comparison control failed.", file=sys.stderr)
        return 2

    rows, checked, origins = [], 0, set()
    for user, mid, ftext, fdate, fedit, o in pairs(con, oid):
        checked += 1
        origins.add(o[0])
        removed, added = compare(o[1], ftext)
        if not removed and not added:
            continue
        rows.append({"origin": o, "user": user, "fmsg": mid, "fdate": fdate, "removed": removed, "added": added,
                     "ftext": ftext, "len_origin": len(o[1]), "len_fwd": len(ftext)})
    lines = [f"# Forward vs origin name diff - {chans[oid][0]}", "",
             f"{checked} forwards compared ({len(origins)} distinct origin posts of {total} in the channel, "
             f"{100 * len(origins) // max(total, 1)}%). A clean result covers only those posts.", "",
             f"{len(rows)} forwards differ in a quoted or Latin name.", ""]
    removed_first = sorted(rows, key=lambda r: (not r["removed"], r["origin"][0]))
    for r in removed_first:
        o = r["origin"]
        predates = bool(o[3]) and (r["fdate"] or "") < o[3]
        trimmed = "  (forward is much longer: extra text appended)" if r["len_fwd"] > 1.4 * r["len_origin"] else ""
        lines.append(f"## {chans[oid][0]}/{o[0]} vs {r['user']}/{r['fmsg']} - origin posted {o[2][:10]}, "
                     f"last edited {(o[3] or 'never')[:10]}; forward copied {(r['fdate'] or '')[:10]}"
                     f"{' (BEFORE the origin edit)' if predates else ''}{trimmed}")
        if r["removed"]:
            lines.append("- in the forward, absent from the origin now: " + ", ".join(f"«{v}»" for v in r["removed"].values()))
        if r["added"]:
            lines.append("- in the origin now, absent from the forward: " + ", ".join(f"«{v}»" for v in r["added"].values()))
        if args.show_words:
            lines += [f"    {w}" for w in word_diff(o[1], r["ftext"])]
        lines.append("")
    text = "\n".join(lines)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
