#!/usr/bin/env python3
"""Triage Telegram media before anyone looks at it (user, 03.10.2026: spend tokens only on pictures worth seeing).

Every look at a picture costs tokens; every step here costs none, so a picture reaches a person only after
the cheap steps have said it is worth seeing:

  queue      local. Picks media from posts whose TEXT already matters: cited in sources.json, a delivery-scan
             hit, a caption naming a registry company or product, or a captionless album in a core channel.
             An album is one item set with the caption of whichever member has text. Repeats are removed
             before anything is downloaded: Telegram keeps one photo_id / document_id across forwards.
             Media already labelled in the ledger are dropped. Writes data/sources/_media_triage/queue.json
             and prints the download command.
  (download) live Telegram job, run by the user:  python3 scripts/tg_media_pull.py download --queue
             data/sources/_media_triage/queue.json  - photos in full (they are small), a video's thumbnail
             only. Files land in data/sources/_media_triage/files/ (a working folder, never a source).
  process    local. SHA-256, a 64-bit difference hash for near-duplicates (re-crops, re-encodes), Tesseract
             OCR (rus+eng) of full photos, scene stills of full videos with ffmpeg, Whisper speech-to-text
             with --whisper (slow). OCR and transcripts are matched for ИНН, ОГРН, в/ч numbers and registry
             names, so text inside a picture surfaces as a text hit.
  rank       local, needs the media venv. CLIP scores each picture against nine classes; sheets then show the
             likeliest evidence first inside each priority group. Nothing is dropped.
  sheets     local. 4x4 contact sheets of small labelled previews, priority order (cited, delivery,
             registry, uncaptioned): one look covers 16 items for about the price of one picture.
  record     writes labels from a sheet look into the ledger data/registry/_media_looked.json, keyed by the
             Telegram media id, so nothing is looked at twice in any session. A label from the cheap first
             pass (--by haiku) is a lead, like a paraphrase: it never fills media.json `shows` or `redact`.
  shortlist  items labelled keep that the main session has not yet looked at in full size.
  promote    copies a kept photo from the working folder to data/sources/ under the TGMEDIA name (through
             source_files.write_new); a kept video prints the full-download command instead.

Nothing here writes a fact: a media.json record is still made by a person who looked at the full picture.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "roymarket.db"
REG = ROOT / "data" / "registry"
SOURCES = ROOT / "data" / "sources"
WORK = SOURCES / "_media_triage"
FILES = WORK / "files"
QUEUE = WORK / "queue.json"
PROCESSED = WORK / "processed.json"
SHEETS = WORK / "sheets"
LEDGER = REG / "_media_looked.json"

# Captionless albums are worth a look only in channels whose pictures are themselves evidence.
CORE_CHANNELS = {"ano_cbst", "nashapravdafond"}
REASONS = ("cited", "delivery", "registry", "uncaptioned")  # priority order on the sheets
LABELS = ("handover", "equipment", "people", "document", "logo", "combat", "screenshot", "facility",
          "nothing")
MISSION = ("ties", "none", "unclear")   # does the picture tie to ЦБСТ / Наша Правда / РОЙ.МАРКЕТ? (a separate call from `label`)
RE_HANDOVER = re.compile(r"передал|передач|вручил|доставил|отправил|груз|гуманитар|бойцам|подразделени|группировк", re.I)
FONT_PATHS = ("/System/Library/Fonts/Supplemental/Arial.ttf", "/Library/Fonts/Arial.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXT = {".mp4", ".mov", ".webm", ".mkv"}
NEAR_DUP_BITS = 6          # Hamming distance at or under which two pictures count as the same picture
CELL, GRID = 256, 4        # contact sheet: 4x4 cells of 256 px
RE_VCH = re.compile(r"\b(?:в/ч|в\.ч\.|войсковая часть)\s*№?\s*(\d{5})\b", re.I)


# --- small pure helpers (tested in tests/test_media_triage.py) --------------------------------------------

def media_key(media_json: str | None) -> str | None:
    """Telegram's own id for the file: the same across every forward of it."""
    try:
        m = json.loads(media_json or "{}")
    except ValueError:
        return None
    if m.get("photo_id"):
        return f"p{m['photo_id']}"
    if m.get("document_id"):
        return f"d{m['document_id']}"
    return None


def kind_of(media_type: str | None, media_json: str | None) -> str | None:
    """photo / video / image (an image sent as a file); None for everything this triage does not look at."""
    if media_type in ("photo", "video"):
        return media_type
    if media_type == "document":
        mime = (json.loads(media_json or "{}") or {}).get("mime_type") or ""
        if mime.startswith("image/"):
            return "image"
        if mime.startswith("video/"):
            return "video"
    return None


def group_albums(rows):
    """rows: (channel_id, msg_id, date, text, ...) sorted by channel, msg. An album is the posts of one
    channel sent in the same second; returns {(channel_id, date): caption} with the first non-empty text."""
    caption = {}
    for r in rows:
        k = (r[0], r[2])
        if (r[3] or "").strip() and not caption.get(k):
            caption[k] = r[3]
        caption.setdefault(k, "")
    return caption


def dhash(path: Path) -> int:
    """64-bit difference hash: survives resizing and re-encoding, not cropping much."""
    from PIL import Image
    with Image.open(path) as im:
        g = im.convert("L").resize((9, 8))
        # Pillow 12+ deprecates getdata(); get_flattened_data() returns the same pixels
        px = list(g.get_flattened_data() if hasattr(g, "get_flattened_data") else g.getdata())
    bits = 0
    for row in range(8):
        for col in range(8):
            bits = (bits << 1) | (px[row * 9 + col] > px[row * 9 + col + 1])
    return bits


def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def cluster_near_dups(hashes: dict[str, int], bits: int = NEAR_DUP_BITS) -> dict[str, str]:
    """{name: representative name} for every picture within `bits` of an earlier one (sorted name order)."""
    reps: list[tuple[str, int]] = []
    dup_of = {}
    for name in sorted(hashes):
        h = hashes[name]
        for rname, rh in reps:
            if hamming(h, rh) <= bits:
                dup_of[name] = rname
                break
        else:
            reps.append((name, h))
    return dup_of


def file_stem(username: str, msg_id: int) -> str:
    return f"{re.sub(r'[^A-Za-z0-9_]+', '', username or 'chat')}-{msg_id}"


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def dump_json(path: Path, data, indent=1):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=indent) + "\n", encoding="utf-8")
    tmp.replace(path)


# --- matching text (captions, OCR, transcripts) ------------------------------------------------------------

def registry_matcher():
    """One folded alternation over registry company names (5+ letters) and product names."""
    from tg_post_coverage import entity_terms, fold, term_regex
    from delivery_signal_scan import product_matchers
    raw = json.loads((REG / "entities.json").read_text(encoding="utf-8"))
    ents = raw if isinstance(raw, list) else raw.get("entities", raw)
    terms = set()
    for e in ents:
        if e.get("_merged_into") or e.get("tier") == "cbst-core":
            continue
        terms |= entity_terms(e)
    for name, _slug, _rx in product_matchers():
        if len(name) >= 4:
            terms.add(fold(name))
    # one big alternation costs ~30 ms a caption; index each term by the first 4 letters of its first word
    # and run only the terms whose prefix occurs in the text
    index: dict[str, list[re.Pattern]] = defaultdict(list)
    for t in terms:
        first = re.split(r"[\s\-–—]+", t.strip())[0]
        if len(first) >= 3:
            index[first[:4]].append(term_regex(t))

    def hits(text: str) -> list[str]:
        if not text:
            return []
        f = fold(text)
        out = set()
        for pre in {w[:4] for w in re.findall(r"[0-9a-zа-я]{3,}", f)} & index.keys():
            for rx in index[pre]:
                out.update(m.group(0) for m in rx.finditer(f))
        return sorted(out)[:8]
    return hits


def id_hits(text: str) -> list[str]:
    from id_patterns import RE_INN, RE_OGRN
    out = [f"ИНН {m}" for m in RE_INN.findall(text or "")]
    out += [f"ОГРН {m}" for m in RE_OGRN.findall(text or "")]
    out += [f"в/ч {m}" for m in RE_VCH.findall(text or "")]
    return sorted(set(out))


def text_score(caption: str, reasons: dict, hits: list | None = None) -> int:
    """How strongly the post's own text points at a handover: the caption decides before the picture does."""
    score = len(set(m.lower() for m in RE_HANDOVER.findall(caption or "")))
    d = (reasons.get("delivery") or "").split("/")[-1]
    score += (3 if d == "strong" else 1) if d else 0
    score += 2 * bool(reasons.get("registry")) + bool(hits)
    return score


def post_url(channel: str, msg_id: int) -> str:
    return f"https://t.me/{channel}/{msg_id}" if channel and not channel.isdigit() else ""


def origin_of(rows: list[tuple]) -> tuple | None:
    """Earliest (date, channel, msg_id) among posts carrying one file, when it is not the kept post."""
    return min(rows) if rows else None


# --- queue ---------------------------------------------------------------------------------------------------

def cited_posts() -> set[tuple[str, int]]:
    out = set()
    for s in load_json(REG / "sources.json", []):
        tp = s.get("tg_post")
        if tp and "/" in tp:
            ch, msg = tp.rsplit("/", 1)
            if msg.isdigit():
                out.add((ch.lower(), int(msg)))
    return out


def cmd_queue(args) -> None:
    if not DB.exists():
        sys.exit(f"{DB} missing - the queue needs the local scrape.")
    from delivery_signal_scan import classify, product_matchers
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    chans = {r[0]: r[1] or "" for r in con.execute("select id, username from tg_channels")}
    want = {c.lower().lstrip("@") for c in args.channels.split(",")} if args.channels else None
    ids = [cid for cid, u in chans.items() if want is None or u.lower() in want or str(cid) in want]
    q = ("select channel_id, msg_id, date, text, media_type, media_json, fwd_channel_username, fwd_msg_id from tg_posts "
         f"where channel_id in ({','.join('?' * len(ids))}) order by channel_id, msg_id")
    rows = con.execute(q, ids).fetchall()
    if args.since:
        rows = [r for r in rows if (r[2] or "") >= args.since]
    caption = group_albums(rows)
    cited = cited_posts()
    reg_hits = registry_matcher()
    matchers = product_matchers()
    ledger = load_json(LEDGER, {})
    reasons_by_album: dict[tuple, dict] = {}
    for k, cap in caption.items():
        uname = chans.get(k[0], "").lower()
        rs = {}
        if cap:
            d = classify(cap, matchers)
            if d:
                rs["delivery"] = d["class"] + "/" + d["strength"]
            h = reg_hits(cap)
            if h:
                rs["registry"] = ", ".join(h[:4])
        elif uname in CORE_CHANNELS:
            rs["uncaptioned"] = "no text in the album"
        reasons_by_album[k] = rs
    items, seen, dup_count, ledgered, skipped_kind = [], {}, 0, 0, Counter()
    for cid, mid, dt, text, mtype, mjson, fwd_u, fwd_m in rows:
        kind = kind_of(mtype, mjson)
        if not kind:
            if mtype:
                skipped_kind[mtype] += 1
            continue
        uname = chans.get(cid, "")
        rs = dict(reasons_by_album.get((cid, dt), {}))
        if (uname.lower(), mid) in cited:
            rs["cited"] = "sources.json"
        if not rs:
            continue
        key = media_key(mjson) or f"m{cid}-{mid}"
        if key in seen:
            seen[key]["copies"].append(f"{uname or cid}/{mid}")
            seen[key]["copy_dates"].append((dt, f"{uname or cid}/{mid}"))
            for r, v in rs.items():
                seen[key]["reasons"].setdefault(r, v)
            dup_count += 1
            continue
        if key in ledger:
            ledgered += 1
            continue
        info = json.loads(mjson or "{}")
        it = {"key": key, "channel": uname or str(cid), "channel_id": cid, "msg_id": mid, "date": dt,
              "kind": kind, "size": info.get("size") or 0, "reasons": rs, "copies": [],
              "copy_dates": [(dt, f"{uname or cid}/{mid}")], "url": post_url(uname, mid),
              "fwd": f"{fwd_u}/{fwd_m}" if fwd_u and fwd_m else "",
              "caption": (caption.get((cid, dt)) or "").replace("\n", " ")[:200],
              "file": file_stem(uname or str(cid), mid) + (".jpg" if kind != "video" else "-thumb.jpg")}
        seen[key] = it
        items.append(it)
    prio = {r: i for i, r in enumerate(REASONS)}
    for it in items:   # the earliest copy, which is the origin unless the kept post is it
        first = origin_of(it.pop("copy_dates"))
        it["earliest"] = first[1] if first and first[1] != f"{it['channel']}/{it['msg_id']}" else ""
        it["text_score"] = text_score(it["caption"], it["reasons"])
    items.sort(key=lambda it: (min(prio[r] for r in it["reasons"]), -it["text_score"], it["date"]), reverse=False)
    if args.max:
        dropped = len(items) - args.max
        items = items[:args.max]
        if dropped > 0:
            print(f"--max {args.max}: {dropped} lower-priority items left out of this queue")
    dump_json(QUEUE, {"built": date.today().isoformat(), "channels": args.channels or "all", "items": items})
    by_reason = Counter(min(it["reasons"], key=prio.get) for it in items)
    by_kind = Counter(it["kind"] for it in items)
    photo_mb = sum(it["size"] for it in items if it["kind"] != "video") / 1048576
    full_video_mb = sum(it["size"] for it in items if it["kind"] == "video") / 1048576
    have = sum((FILES / it["file"]).exists() for it in items)
    print(f"{len(items)} media to triage from {len(rows)} posts "
          f"({dup_count} repeats folded by Telegram id, {ledgered} already labelled in the ledger)")
    print("  by first reason: " + ", ".join(f"{r} {by_reason[r]}" for r in REASONS if by_reason[r]))
    print("  by kind: " + ", ".join(f"{k} {n}" for k, n in by_kind.most_common()))
    print(f"  download: photos and images {photo_mb:.0f} MB in full; {by_kind['video']} video thumbnails "
          f"(the full videos would be {full_video_mb:.0f} MB); {have} already in the working folder")
    if skipped_kind:
        print("  not triaged here: " + ", ".join(f"{k} {n}" for k, n in skipped_kind.most_common()))
    print(f"  {len(items) // (GRID * GRID) + 1} contact sheets at most")
    print(f"\nwrote {QUEUE.relative_to(ROOT)}")
    print("download (live Telegram job, run it yourself):\n"
          f"  python3 scripts/tg_media_pull.py download --queue {QUEUE.relative_to(ROOT)}")
    print("then: python3 scripts/media_triage.py process && python3 scripts/media_triage.py sheets")


# --- process -------------------------------------------------------------------------------------------------

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ocr(path: Path) -> str:
    try:
        r = subprocess.run(["tesseract", str(path), "-", "-l", "rus+eng"], capture_output=True, text=True,
                           timeout=90)
        return r.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def scene_stills(video: Path, out_dir: Path, max_frames: int = 12) -> list[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    pattern = out_dir / f"{video.stem}-s%02d.jpg"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(video), "-vf",
                    "select='eq(n\\,0)+gt(scene\\,0.35)',scale=512:-2", "-vsync", "vfr",
                    "-frames:v", str(max_frames), str(pattern)], capture_output=True, timeout=600)
    return sorted(p.name for p in out_dir.glob(f"{video.stem}-s*.jpg"))


def transcribe(video: Path) -> str:
    try:
        import whisper
    except ImportError:
        return ""
    model = getattr(transcribe, "_model", None) or whisper.load_model("small")
    transcribe._model = model
    return (model.transcribe(str(video), language="ru", fp16=False) or {}).get("text", "").strip()


def _changed_since_processed(p: Path, prior: dict) -> bool:
    """Same path, same byte-size but different content (a retried download
    that landed a different payload of coincidentally equal length) must
    still count as changed -- a size-only check would keep the prior run's
    stale sha256/dhash/OCR text forever. Size is checked first because it's
    free; the sha256 (cheap, unlike the OCR/ffmpeg this gates) only runs
    when size alone can't tell them apart. (Found 05.10.2026 by an
    adversarial code review.)"""
    if prior.get("size") != p.stat().st_size:
        return True
    return prior.get("sha256") != sha256(p)


def cmd_process(args) -> None:
    files = sorted(p for p in FILES.glob("*") if p.suffix.lower() in IMAGE_EXT | VIDEO_EXT) if FILES.exists() else []
    done = load_json(PROCESSED, {})
    todo = [p for p in files if _changed_since_processed(p, done.get(p.name, {}))]
    print(f"{len(files)} files in the working folder, {len(todo)} new or changed"
          + (" (OCR takes about a second a picture)" if todo else ""))
    reg_hits = registry_matcher() if todo else None
    for i, p in enumerate(todo, 1):
        rec = {"size": p.stat().st_size, "sha256": sha256(p)}
        text = ""
        if p.suffix.lower() in IMAGE_EXT:
            try:
                rec["dhash"] = f"{dhash(p):016x}"
            except Exception as exc:  # noqa: BLE001 - a broken file is recorded, not fatal
                rec["error"] = str(exc)[:120]
            if not p.stem.endswith("-thumb") and not args.no_ocr and "error" not in rec:
                text = ocr(p)
        else:
            rec["stills"] = scene_stills(p, WORK / "stills")
            if args.whisper:
                text = transcribe(p)
        if text:
            (WORK / "text").mkdir(parents=True, exist_ok=True)
            (WORK / "text" / f"{p.stem}.txt").write_text(text, encoding="utf-8")
            rec["text_chars"] = len(text)
            rec["text_hits"] = id_hits(text) + reg_hits(text)
        done[p.name] = rec
        if i % 50 == 0:
            dump_json(PROCESSED, done)
            print(f"  {i}/{len(todo)}", flush=True)
    hashes = {n: int(r["dhash"], 16) for n, r in done.items() if r.get("dhash")}
    dup_of = cluster_near_dups(hashes)
    for n, r in done.items():
        if n in dup_of:
            r["near_dup_of"] = dup_of[n]
        else:
            r.pop("near_dup_of", None)
    dump_json(PROCESSED, done)
    hit_files = {n: r["text_hits"] for n, r in done.items() if r.get("text_hits")}
    print(f"{len(done)} processed; {len(dup_of)} near-duplicates of another picture; "
          f"{len(hit_files)} with an identifier or registry name in their text")
    for n, h in sorted(hit_files.items())[:40]:
        print(f"  {n}: {', '.join(h)}")
    if len(hit_files) > 40:
        print(f"  ... {len(hit_files) - 40} more in {PROCESSED.relative_to(ROOT)}")


# --- rank (local CLIP; needs the media venv: ~/.venvs/roymarket-media) ------------------------------------

CLIP_CLASSES = {
    "handover": "a photo of soldiers receiving boxes of supplies or equipment",
    "equipment": "a photo of a drone or military equipment on display",
    "people": "a group photo of people posing outdoors",
    "document": "a photo of a printed document or letter",
    "screenshot": "a screenshot of a phone or computer screen with text",
    "combat": "a photo of a destroyed military vehicle or an explosion",
    "facility": "a photo of a workshop, warehouse or building",
    "logo": "a logo or graphic design on a plain background",
    "nothing": "a blurry dark photo with nothing visible",
}
EVIDENCE_CLASSES = ("handover", "equipment", "document", "screenshot", "combat", "facility")


def evidence_score(clip: dict | None) -> float:
    """Share of CLIP's probability on classes that can be evidence; 0.5 when a picture was not ranked."""
    if not clip:
        return 0.5
    return sum(clip["p"].get(c, 0) for c in EVIDENCE_CLASSES)


def cmd_rank(args) -> None:
    try:
        import open_clip
        import torch
        from PIL import Image
    except ImportError:
        sys.exit("rank needs open_clip: run it with ~/.venvs/roymarket-media/bin/python "
                 "(python3 -m venv --system-site-packages ~/.venvs/roymarket-media && "
                 "~/.venvs/roymarket-media/bin/pip install open_clip_torch)")
    done = load_json(PROCESSED, {})
    todo = [n for n, r in done.items() if r.get("dhash") and "clip" not in r and (FILES / n).exists()]
    print(f"{len(todo)} pictures to rank ({sum(1 for r in done.values() if 'clip' in r)} already ranked)")
    if not todo:
        return
    # mps returns identical logits for every picture on the Intel Mac (24.10.2026: all 12,565 ranked 1/9), so cpu by default
    dev = "mps" if os.environ.get("MEDIA_TRIAGE_DEVICE") == "mps" and torch.backends.mps.is_available() else "cpu"
    model, _, pre = open_clip.create_model_and_transforms("ViT-B-32", pretrained="openai")
    model = model.to(dev).eval()
    tok = open_clip.get_tokenizer("ViT-B-32")
    labels = list(CLIP_CLASSES)
    with torch.no_grad():
        t = model.encode_text(tok([CLIP_CLASSES[k] for k in labels]).to(dev))
        t = t / t.norm(dim=-1, keepdim=True)
        for i in range(0, len(todo), 32):
            batch = todo[i:i + 32]
            ims = []
            for n in batch:
                try:
                    with Image.open(FILES / n) as im:
                        ims.append(pre(im.convert("RGB")))
                except Exception:  # noqa: BLE001 - an unreadable file stays unranked
                    ims.append(torch.zeros(3, 224, 224))
            f = model.encode_image(torch.stack(ims).to(dev))
            f = f / f.norm(dim=-1, keepdim=True)
            probs = (100 * f @ t.T).softmax(dim=-1).cpu()
            for n, row in zip(batch, probs):
                p = {k: round(float(v), 3) for k, v in zip(labels, row)}
                if max(p.values()) - min(p.values()) < 0.01:
                    sys.exit(f"{n}: CLIP scores are uniform ({dev}); the device is broken, nothing saved")
                done[n]["clip"] = {"top": max(p, key=p.get), "p": p}
            print(f"  {min(i + 32, len(todo))}/{len(todo)}", flush=True)
    dump_json(PROCESSED, done)
    tops = Counter(r["clip"]["top"] for r in done.values() if "clip" in r)
    print("ranked; top class counts: " + ", ".join(f"{k} {v}" for k, v in tops.most_common()))


# --- sheets --------------------------------------------------------------------------------------------------

def sheet_candidates(items, processed, ledger):
    """Queue items with a local picture, not labelled, not a near-duplicate of one already on a sheet."""
    out, rep_seen = [], set()
    for it in items:   # a labelled picture takes its near-duplicates off the sheets with it
        rec = processed.get(it["file"])
        if it["key"] in ledger and rec is not None:
            rep_seen.add(rec.get("near_dup_of") or it["file"])
    for it in items:
        if it["key"] in ledger:
            continue
        name = it["file"]
        rec = processed.get(name)
        if rec is None or rec.get("error"):
            continue
        rep = rec.get("near_dup_of") or name
        if rep in rep_seen:
            continue
        rep_seen.add(rep)
        out.append(it)
    return out


def _font(size: int):
    from PIL import ImageFont
    for fp in FONT_PATHS:
        if Path(fp).exists():
            return ImageFont.truetype(fp, size)
    return ImageFont.load_default()   # no Cyrillic: captions print as boxes, the labels still work


def draw_sheet(cells, path: Path) -> None:
    """cells: (image path, label, caption, is_video). Two label lines: post id (with [v] for video), caption."""
    from PIL import Image, ImageDraw
    label_h, font = 34, _font(11)
    sheet = Image.new("RGB", (GRID * CELL, GRID * (CELL + label_h)), "white")
    d = ImageDraw.Draw(sheet)
    for n, (img_path, label, caption, is_video) in enumerate(cells):
        x, y = (n % GRID) * CELL, (n // GRID) * (CELL + label_h)
        try:
            with Image.open(img_path) as im:
                im = im.convert("RGB")
                im.thumbnail((CELL - 4, CELL - 4))
                sheet.paste(im, (x + (CELL - im.width) // 2, y + (CELL - im.height) // 2))
        except Exception:  # noqa: BLE001 - an unreadable file leaves a blank cell with its label
            pass
        d.rectangle([x, y + CELL, x + CELL - 1, y + CELL + label_h - 1], fill="black")
        d.text((x + 4, y + CELL + 2), f"{n + 1}  {'[v] ' if is_video else ''}{label}"[:40], fill="white", font=font)
        d.text((x + 4, y + CELL + 18), (caption or "")[:44], fill=(200, 200, 200), font=font)
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path, quality=80)


def cmd_sheets(args) -> None:
    q = load_json(QUEUE, {}).get("items", [])
    processed = load_json(PROCESSED, {})
    cands = sheet_candidates(q, processed, load_json(LEDGER, {}))
    prio = {r: i for i, r in enumerate(REASONS)}   # reason group first, then likeliest evidence (CLIP) first
    cands.sort(key=lambda it: (min(prio[r] for r in it["reasons"]),
                               -(it.get("text_score") or 0) - len(processed.get(it["file"], {}).get("text_hits") or []),
                               -evidence_score(processed.get(it["file"], {}).get("clip"))))
    per = GRID * GRID
    n_sheets = min(args.max, (len(cands) + per - 1) // per)
    day = date.today().strftime("%Y%m%d")
    existing = len(list(SHEETS.glob(f"{day}-*.jpg"))) if SHEETS.exists() else 0
    for s in range(n_sheets):
        chunk = cands[s * per:(s + 1) * per]
        cells, index = [], {}
        for n, it in enumerate(chunk, 1):
            stills = processed.get(it["file"], {}).get("stills") or []
            img = WORK / "stills" / stills[0] if stills else FILES / it["file"]
            cells.append((img, f"{it['channel']}/{it['msg_id']}", it["caption"], it["kind"] == "video"))
            index[str(n)] = {"key": it["key"], "channel": it["channel"], "msg_id": it["msg_id"],
                             "kind": it["kind"], "reasons": sorted(it["reasons"]), "caption": it["caption"][:120],
                             "url": it.get("url") or post_url(it["channel"], it["msg_id"]),
                             "fwd": it.get("fwd") or "", "earliest": it.get("earliest") or "",
                             "copies": it.get("copies") or []}
        name = f"{day}-{existing + s + 1:03d}"
        draw_sheet(cells, SHEETS / f"{name}.jpg")
        dump_json(SHEETS / f"{name}.json", {"sheet": name, "cells": index})
    left = max(0, len(cands) - n_sheets * per)
    print(f"{n_sheets} sheet(s) in {SHEETS.relative_to(ROOT)} covering {min(len(cands), n_sheets * per)} "
          f"items; {left} more wait for the next run")
    print("label a sheet: python3 scripts/media_triage.py record --sheet <name> --by haiku|main --labels labels.json")


# --- ledger --------------------------------------------------------------------------------------------------

def validate_labels(labels: dict) -> list[str]:
    errs = []
    for cell, v in labels.items():
        if v.get("label") not in LABELS:
            errs.append(f"cell {cell}: label {v.get('label')!r} not in {LABELS}")
        if not isinstance(v.get("keep"), bool):
            errs.append(f"cell {cell}: keep must be true or false")
        if v.get("mission") is not None and v["mission"] not in MISSION:
            errs.append(f"cell {cell}: mission {v['mission']!r} not in {MISSION}")
    return errs


def apply_labels(ledger: dict, sheet: dict, labels: dict, by: str, today: str) -> int:
    n = 0
    for cell, v in labels.items():
        c = sheet["cells"].get(str(cell))
        if not c:
            continue
        prev = ledger.get(c["key"], {})
        if prev.get("by") == "main" and by != "main":
            continue  # a full-size look by the main session is never overwritten by a first pass
        ledger[c["key"]] = {"label": v["label"], "keep": v["keep"], "note": (v.get("note") or "")[:300],
                            "by": by, "as_of": today, "sheet": sheet["sheet"],
                            "post": f"{c['channel']}/{c['msg_id']}"}
        if v.get("mission"):
            ledger[c["key"]]["mission"] = v["mission"]
        n += 1
    return n


def cmd_record(args) -> None:
    sheet = load_json(SHEETS / f"{args.sheet}.json", None)
    if not sheet:
        sys.exit(f"no sheet {args.sheet} in {SHEETS}")
    labels = load_json(Path(args.labels), None)
    if not isinstance(labels, dict):
        sys.exit(f"{args.labels}: expected {{cell: {{label, keep, note}}}}")
    errs = validate_labels(labels)
    if errs:
        sys.exit("\n".join(errs))
    ledger = load_json(LEDGER, {})
    n = apply_labels(ledger, sheet, labels, args.by, date.today().isoformat())
    dump_json(LEDGER, dict(sorted(ledger.items())))
    print(f"{n} labels recorded from {args.sheet} (by {args.by}); ledger holds {len(ledger)}")


def cmd_shortlist(args) -> None:
    ledger = load_json(LEDGER, {})
    rows = [(k, v) for k, v in ledger.items() if v.get("keep") and v.get("by") != "main"]
    by = defaultdict(list)
    for k, v in rows:
        by[v["label"]].append((k, v))
    print(f"{len(rows)} kept items wait for a full-size look")
    for lab in LABELS:
        for k, v in by.get(lab, []):
            print(f"  {lab:10} {v['post']:28} {k}  {v.get('note', '')[:90]}")


def cmd_promote(args) -> None:
    from source_files import write_new
    items = {f"{it['channel']}/{it['msg_id']}": it for it in load_json(QUEUE, {}).get("items", [])}
    for post in args.posts:
        it = items.get(post)
        if not it:
            print(f"{post}: not in the current queue")
            continue
        if it["kind"] == "video":
            print(f"{post}: a video - fetch the original: python3 scripts/tg_media_pull.py download "
                  f"--channel {it['channel']} --msg-ids {it['msg_id']}")
            continue
        src = FILES / it["file"]
        if not src.exists():
            print(f"{post}: no working copy; run the queue download first")
            continue
        label = re.sub(r"[^A-Za-z0-9_]+", "", it["channel"])
        dest = SOURCES / f"TGMEDIA_{it['date'][:10].replace('-', '')}_{label}-post{it['msg_id']}-media{src.suffix}"
        out = write_new(dest, src.read_bytes())
        print(f"{post}: {out.name}")
    print("next: python3 scripts/inventory_sources.py && python3 scripts/extract_registry.py")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("queue", help="local: pick media by their post's text, fold repeats")
    a.add_argument("--channels", default=None, help="comma list of usernames or ids (default: every channel)")
    a.add_argument("--since", default=None, help="only posts from this date (YYYY-MM-DD)")
    a.add_argument("--max", type=int, default=0, help="keep only the first N by priority (dropped count is printed)")
    a = sub.add_parser("process", help="local: hashes, near-duplicates, OCR, video stills")
    a.add_argument("--no-ocr", action="store_true")
    a.add_argument("--whisper", action="store_true", help="also transcribe full videos (slow)")
    sub.add_parser("rank", help="local CLIP: score each picture's chance of being evidence (media venv)")
    a = sub.add_parser("sheets", help="local: 4x4 contact sheets for one look each")
    a.add_argument("--max", type=int, default=10, help="sheets per run (default 10)")
    a = sub.add_parser("record", help="write a sheet's labels to the ledger")
    a.add_argument("--sheet", required=True)
    a.add_argument("--labels", required=True, help="JSON file {cell: {label, keep, note}}")
    a.add_argument("--by", required=True, choices=("haiku", "main"))
    sub.add_parser("shortlist", help="kept items still waiting for a full-size look")
    a = sub.add_parser("promote", help="copy kept photos into data/sources/ under the TGMEDIA name")
    a.add_argument("posts", nargs="+", help="channel/msg_id as printed by shortlist")
    args = ap.parse_args()
    {"queue": cmd_queue, "process": cmd_process, "rank": cmd_rank, "sheets": cmd_sheets, "record": cmd_record,
     "shortlist": cmd_shortlist, "promote": cmd_promote}[args.cmd](args)


if __name__ == "__main__":
    main()
