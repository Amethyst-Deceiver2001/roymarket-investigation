#!/usr/bin/env python3
"""Search the triage pictures by what they show: a text prompt or a reference picture.

`media_triage.py rank` asks CLIP one fixed question ("does this look like evidence"). This script embeds every
working picture once (`embed`, ~17 minutes for 12,000 on the Intel Mac, CPU) and then answers any number of
questions in seconds (`find`), writing the best matches as contact sheets that can be looked at like any other:

    ~/.venvs/roymarket-media/bin/python scripts/media_find.py embed
    ~/.venvs/roymarket-media/bin/python scripts/media_find.py find --text "a wooden crate with a company logo" --top 48
    ~/.venvs/roymarket-media/bin/python scripts/media_find.py find --like data/sources/TGMEDIA_..._post593-1.jpg --top 48
    ~/.venvs/roymarket-media/bin/python scripts/media_find.py find --text "a drone with a printed brand name" --text "boxes beside a truck" --top 32

Several --text prompts are averaged (a picture must resemble all of them); --like adds a reference picture. Matches
already labelled in the ledger are left out unless --all is given. Sheets are written to
data/sources/_media_triage/find/ (a work folder, not catalogued) with the post id and a caption under each cell.
The model is the same ViT-B/32 as `rank`; it is not asked to read text, so print is for OCR (`process`) to find.
A match is a lead to look at, never a fact.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import media_triage as mt  # noqa: E402

EMB = mt.WORK / "clip_embeddings.npz"
OUT = mt.WORK / "find"


def _model():
    try:
        import open_clip
        import torch
    except ImportError:
        sys.exit("needs the media venv: ~/.venvs/roymarket-media/bin/python scripts/media_find.py ...")
    model, _, pre = open_clip.create_model_and_transforms("ViT-B-32", pretrained="openai")
    return torch, open_clip, model.eval(), pre, open_clip.get_tokenizer("ViT-B-32")


def cmd_embed(args) -> None:
    import numpy as np
    from PIL import Image
    torch, _, model, pre, _ = _model()
    names = sorted(p.name for p in mt.FILES.iterdir() if p.suffix.lower() in mt.IMAGE_EXT)
    have = {}
    if EMB.exists() and not args.force:
        z = np.load(EMB, allow_pickle=False)
        have = dict(zip(z["names"].tolist(), z["emb"]))
    todo = [n for n in names if n not in have]
    if args.limit:
        todo = todo[:args.limit]
    print(f"{len(have)} embedded, {len(todo)} to do of {len(names)} pictures")
    with torch.no_grad():
        for i in range(0, len(todo), 32):
            batch = todo[i:i + 32]
            ims = []
            for n in batch:
                try:
                    with Image.open(mt.FILES / n) as im:
                        ims.append(pre(im.convert("RGB")))
                except Exception:  # noqa: BLE001 - an unreadable file is skipped
                    ims.append(None)
            ok = [(n, t) for n, t in zip(batch, ims) if t is not None]
            if ok:
                f = model.encode_image(torch.stack([t for _, t in ok]))
                f = (f / f.norm(dim=-1, keepdim=True)).numpy().astype("float32")
                for (n, _), row in zip(ok, f):
                    have[n] = row
            print(f"  {min(i + 32, len(todo))}/{len(todo)}", flush=True)
            if (i // 32) % 40 == 39:   # save as we go: a 17-minute job survives an interruption
                np.savez(EMB, names=np.array(list(have)), emb=np.stack(list(have.values())))
    if have:
        np.savez(EMB, names=np.array(list(have)), emb=np.stack(list(have.values())))
    print(f"saved {len(have)} embeddings to {EMB.relative_to(mt.ROOT)}")


def cmd_find(args) -> None:
    import numpy as np
    from PIL import Image
    if not EMB.exists():
        sys.exit("no embeddings yet: run `embed` first")
    torch, open_clip, model, pre, tok = _model()
    z = np.load(EMB, allow_pickle=False)
    names, emb = z["names"].tolist(), z["emb"]
    qs = []
    with torch.no_grad():
        if args.text:
            t = model.encode_text(tok(args.text))
            qs += list((t / t.norm(dim=-1, keepdim=True)).numpy())
        for path in args.like or []:
            with Image.open(path) as im:
                f = model.encode_image(pre(im.convert("RGB")).unsqueeze(0))
            qs.append((f / f.norm(dim=-1, keepdim=True)).numpy()[0])
    if not qs:
        sys.exit("give --text and/or --like")
    q = np.mean(qs, axis=0)
    q = q / np.linalg.norm(q)
    score = emb @ q
    queue = mt.load_json(mt.QUEUE, {}).get("items", [])
    by_file = {it["file"]: it for it in queue}
    ledger = {} if args.all else mt.load_json(mt.LEDGER, {})
    order = np.argsort(-score)
    picked, seen_alb = [], {}
    for i in order:
        n = names[i]
        it = by_file.get(n)
        if it and (it["key"] in ledger or mt.ignored(it)):
            continue
        alb = it["album"] if it else n
        if seen_alb.get(alb, 0) >= mt.MAX_PER_ALBUM:
            continue
        seen_alb[alb] = seen_alb.get(alb, 0) + 1
        picked.append((n, it, float(score[i])))
        if len(picked) >= args.top:
            break
    OUT.mkdir(parents=True, exist_ok=True)
    tag = args.name or "q"
    per = mt.GRID * mt.GRID
    for s in range(0, len(picked), per):
        chunk = picked[s:s + per]
        cells, index = [], {}
        for k, (n, it, sc) in enumerate(chunk, 1):
            post = f"{it['channel']}/{it['msg_id']}" if it else n
            cells.append((mt.FILES / n, f"{post} {sc:.2f}", (it or {}).get("caption", ""), bool(it and it["kind"] == "video")))
            index[str(k)] = {"file": n, "post": post, "score": round(sc, 3), "url": (it or {}).get("url", ""),
                             "caption": (it or {}).get("caption", "")[:120]}
        name = f"{tag}-{s // per + 1:02d}"
        mt.draw_sheet(cells, OUT / f"{name}.jpg")
        mt.dump_json(OUT / f"{name}.json", {"query": {"text": args.text, "like": args.like}, "cells": index})
        print(f"wrote {(OUT / name).relative_to(mt.ROOT)}.jpg  ({len(chunk)} cells)")
    print("best five: " + ", ".join(f"{(it or {}).get('channel', n)}/{(it or {}).get('msg_id', '')} {sc:.2f}" for n, it, sc in picked[:5]))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("embed", help="embed every working picture (CPU, resumable)")
    a.add_argument("--limit", type=int, default=0, help="only this many new pictures (a test)")
    a.add_argument("--force", action="store_true", help="start again")
    a = sub.add_parser("find", help="best matches for a text prompt and/or reference picture")
    a.add_argument("--text", action="append", help="what to look for (repeatable; prompts are averaged)")
    a.add_argument("--like", action="append", help="a reference picture (repeatable)")
    a.add_argument("--top", type=int, default=48)
    a.add_argument("--all", action="store_true", help="include pictures already labelled")
    a.add_argument("--name", default=None, help="sheet name prefix")
    args = ap.parse_args()
    {"embed": cmd_embed, "find": cmd_find}[args.cmd](args)


if __name__ == "__main__":
    main()
