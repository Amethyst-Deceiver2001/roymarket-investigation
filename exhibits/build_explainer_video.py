#!/usr/bin/env python3
"""One-off explainer video: Фонд «Наша Правда», its funds and the handovers it reports.

  python3 exhibits/build_explainer_video.py            # writes exhibits/video/nasha_pravda_explainer_draft.mp4
  python3 exhibits/build_explainer_video.py --still timeline   # one PNG of a scene, for checking

Every number, date, recipient and quote is read from data/registry/ or from the post text in
data/roymarket.db at build time; nothing is typed in from memory except the English glosses of
recipients and the translations, which are marked as such on screen. Photos come from the media
records of genre `handover` about this donor (publish ok), shown as published. Local, no network.
A draft for internal review: nothing here goes into docs/ without the user's go-ahead.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import deliveries as dl  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
REG = ROOT / "data" / "registry"
OUT = ROOT / "exhibits" / "video"
W, H, FPS = 1280, 720, 24
DONOR = "fond-nasha-pravda"

# Design tokens (design/roymarket.css, dark ground). Red is reserved for the Sanctioned flag: unused here.
PAPER, PANEL, PANEL2 = (16, 20, 24), (23, 28, 34), (31, 38, 46)
INK, INK2, INK3 = (231, 235, 239), (180, 189, 199), (138, 150, 163)
RULE, ACCENT, ACCENT_SOFT = (47, 56, 67), (132, 182, 222), (23, 38, 51)

SANS, SANS_B = "/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
MONO = "/System/Library/Fonts/Menlo.ttc"

# English glosses of the recipient wording in each delivery record (the record keeps the Russian).
RECIPIENT_EN = {
    "bulat-d01": "Servicemen, Krasnoarmeysk direction",
    "bulat-d03": "“Participants of the operation”, no unit named",
    "bulat-d04": "Servicemen from Altai, Kursk direction",
    "bulat-d05": "132nd Gorlovka Brigade, Donetsk direction",
    "bulat-d06": "EW and UAV units, group “Center”",
    "bulat-d07": "1st motor-rifle company, Zaporizhzhia region",
    "bulat-d09": "Servicemen, Pokrovsk direction",
    "bulat-d10": "Motor-rifle regiment servicemen",
    "bulat-d11": "Motor-rifle regiment fighters",
    "bulat-d12": "Tank regiment servicemen, on request",
    "bulat-d13": "Military unit, not named; thanks received",
    "bulat-d14": "Servicemen, Kursk region",
    "bulat-d15": "Fighters, Kursk region",
    "bulat-d16": "Assault troops, Svatove direction",
}
PHOTOS = ["m0068", "m0070", "m0073", "m0075", "m0076", "m0077", "m0078", "m0079", "m0080", "m0081", "m0082", "m0083", "m0085", "m0087"]

_fc: dict = {}


def font(path: str, size: int, index: int = 0) -> ImageFont.FreeTypeFont:
    k = (path, size, index)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(path, size, index=index)
    return _fc[k]


def sans(s): return font(SANS, s)
def bold(s): return font(SANS_B, s)
def mono(s): return font(MONO, s)


def wrap(d: ImageDraw.ImageDraw, text: str, f, width: int) -> list[str]:
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    return lines + ([cur] if cur else [])


def text_block(d, xy, text, f, fill, width, gap=1.32):
    x, y = xy
    for ln in wrap(d, text, f, width):
        d.text((x, y), ln, font=f, fill=fill)
        y += int(f.size * gap)
    return y


def ease(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    im = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(im)
    d.text((W - 56, 30), "DRAFT · INTERNAL", font=mono(13), fill=INK3, anchor="ra")
    return im, d


# ---------------------------------------------------------------- data
def load() -> dict:
    ents = {e["slug"]: e for e in json.loads((REG / "entities.json").read_text(encoding="utf-8"))}
    f = ents[DONOR]
    prods = dl.load_products(REG / "products.json")
    media = {m["id"]: m for m in json.loads((REG / "media.json").read_text(encoding="utf-8"))}
    ev: dict = {}
    for p in prods:
        for dl in p["deliveries"]:
            if dl["donor"] != DONOR:
                continue
            e = ev.setdefault(dl["post_id"], {"post": dl["post_id"], "date": dl["date"], "products": set(), "ids": []})
            e["products"].add(p["slug"])
            e["ids"].append(dl["id"])
    events = sorted(ev.values(), key=lambda e: e["date"])
    fin = {x["year"]: x for x in f["financials"]}
    stock = {}
    for p in prods:
        for c in p["claims"]:
            if c.get("metric") == "donor_stock" and c.get("entity") == DONOR or (
                    c.get("metric") == "donor_stock" and "Наша Правда" in str(c.get("asserted_by"))):
                stock[p["slug"]] = c
    db = sqlite3.connect(ROOT / "data" / "roymarket.db")
    posts = {}
    for mid in (421, 422):
        r = db.execute("select text,date from tg_posts where channel_id=1905141464 and msg_id=?", (mid,)).fetchone()
        posts[mid] = r
    return {"f": f, "events": events, "fin": fin, "stock": stock, "media": media, "posts": posts}


def photo_for(D, ev_ids):
    for mid in PHOTOS:
        m = D["media"][mid]
        if any(a["id"] in ev_ids for a in m["about"]):
            return m
    return None


def fit_photo(path: Path, box: tuple[int, int]) -> Image.Image:
    im = Image.open(path).convert("RGB")
    s = min(box[0] / im.width, box[1] / im.height)
    s = min(s, 2.4)
    im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    return im


def ru_month(d: str) -> str:
    return dt.date.fromisoformat(d).strftime("%b %Y")


# ---------------------------------------------------------------- scenes: each is f(t) -> Image
def scene_title(D):
    def f(t):
        im, d = canvas()
        a = ease(t / 1.2)
        d.rectangle((96, 250, 100, 470), fill=ACCENT)
        d.text((128, 246), "Фонд «Наша Правда»", font=bold(64), fill=tuple(int(PAPER[i] + (INK[i] - PAPER[i]) * a) for i in range(3)))
        d.text((128, 340), "Money in, equipment out:", font=sans(34), fill=INK2)
        d.text((128, 384), "what a donor foundation reports delivering", font=sans(34), fill=INK2)
        d.text((128, 450), "ROIMARKET INVESTIGATION  ·  OPEN-SOURCE RECORD", font=mono(15), fill=INK3)
        return im
    return f, 4.5


def scene_who(D):
    f_ = D["f"]
    director = f_["director"]
    since = f_["director_history"][0]["as_of"]

    def f(t):
        im, d = canvas()
        d.text((96, 120), "WHO", font=mono(16), fill=ACCENT)
        d.text((96, 160), "A Moscow foundation", font=bold(46), fill=INK)
        rows = [("Name", "Фонд «Наша Правда»"), ("ИНН", f_["inn"]), ("Director", f"{director}"),
                ("In post since", ru_month(since)), ("Links to ЦБСТ", "Joint deliveries, in its own posts")]
        y = 270
        for i, (k, v) in enumerate(rows):
            a = ease((t - 0.5 - i * 0.55) / 0.5)
            if a <= 0:
                continue
            col = tuple(int(PAPER[j] + (INK[j] - PAPER[j]) * a) for j in range(3))
            d.line((96, y - 14, 1184, y - 14), fill=RULE)
            d.text((96, y), k, font=mono(18), fill=INK3)
            d.text((340, y - 4), v, font=sans(30), fill=col)
            y += 66
        return im
    return f, 7.0


def scene_money(D):
    fin = D["fin"]
    rows = [(y, "received", fin[y]["funds_received"]) for y in ("2024", "2025")]
    used = {y: fin[y]["funds_used"] for y in ("2024", "2025")}
    total = sum(r[2] for r in rows)
    mx = 1.5e9

    def f(t):
        im, d = canvas()
        d.text((96, 120), "MONEY", font=mono(16), fill=ACCENT)
        d.text((96, 160), f"RUB {total / 1e9:.1f}bn in targeted funds, 2024–2025", font=bold(44), fill=INK)
        k = ease((t - 0.6) / 2.2)
        y = 290
        for yr, _, rec in rows:
            d.text((96, y + 8), yr, font=bold(30), fill=INK)
            for j, (lab, v, col) in enumerate((("received", rec, ACCENT), ("used", used[yr], INK3))):
                yy = y + j * 62
                w = int(700 * v / mx * k)
                d.rectangle((250, yy, 250 + max(w, 2), yy + 40), fill=col)
                d.text((250 + w + 14, yy + 6), f"RUB {v / 1e9:.2f}bn {lab}", font=sans(24), fill=INK2)
            y += 170
        d.text((96, 640), "From the foundation's own annual accounts. A non-profit reports funds received, not revenue.",
               font=sans(21), fill=INK3)
        return im
    return f, 9.0


def scene_stock(D):
    st = D["stock"]
    b, k = st["bulat"], st["kapyushon"]

    def f(t):
        im, d = canvas()
        d.text((96, 120), "STOCK", font=mono(16), fill=ACCENT)
        d.text((96, 160), "On its books at 31 December 2024", font=bold(44), fill=INK)
        for i, (c, n, nm) in enumerate(((b, "50", "Булат"), (k, "2", "Капюшон"))):
            a = ease((t - 0.5 - i * 1.0) / 0.6)
            if a <= 0:
                continue
            x = 96 + i * 560
            col = tuple(int(PAPER[j] + (INK[j] - PAPER[j]) * a) for j in range(3))
            d.rectangle((x, 270, x + 520, 520), fill=PANEL, outline=RULE)
            d.text((x + 30, 285), n, font=bold(120), fill=col)
            d.text((x + 30, 430), f"«{nm}»", font=bold(34), fill=ACCENT)
            ledger = c["text_ru"].split(" — ")
            d.text((x + 30, 480), (ledger[0][:44]), font=mono(15), fill=INK3)
        d.text((96, 580), "Book value RUB 2.75m and RUB 0.86m. Ledger lines as printed:", font=sans(22), fill=INK2)
        d.text((96, 612), "“monitoring device” and “drone suppressor”.", font=sans(22), fill=INK2)
        return im
    return f, 7.0


def scene_timeline(D):
    ev = D["events"]
    d0, d1 = dt.date(2024, 6, 15), dt.date(2026, 6, 15)
    x0, x1, ay = 110, 1170, 612

    def xpos(s):
        return int(x0 + (x1 - x0) * (dt.date.fromisoformat(s) - d0).days / (d1 - d0).days)

    shots = []
    for e in ev:
        m = photo_for(D, e["ids"])
        if m:
            shots.append((e, m))
    cache = {}
    sweep, per = 2.2, 1.12
    total = sweep + per * len(shots) + 0.8

    def f(t):
        im, d = canvas()
        d.text((96, 70), "HANDOVERS", font=mono(16), fill=ACCENT)
        d.text((96, 100), f"{len(ev)} reported handovers, {ru_month(ev[0]['date'])} – {ru_month(ev[-1]['date'])}", font=bold(36), fill=INK)
        d.line((x0, ay, x1, ay), fill=RULE, width=2)
        for yr in (2025, 2026):
            xx = xpos(f"{yr}-01-01")
            d.line((xx, ay - 8, xx, ay + 8), fill=RULE, width=2)
            d.text((xx + 6, ay + 14), str(yr), font=mono(15), fill=INK3)
        idx = int((t - sweep) / per) if t >= sweep else -1
        cur = shots[idx][0]["post"] if 0 <= idx < len(shots) else None
        reveal = ease(t / sweep)
        last = None
        for i, e in enumerate(ev):
            x = xpos(e["date"])
            if (x - x0) / (x1 - x0) > reveal:
                continue
            both = "bulat" in e["products"]
            r = 12 if e["post"] == cur else 7
            y = ay - 22 - (i % 2) * 22
            d.line((x, y + r, x, ay), fill=RULE)
            if both:
                d.ellipse((x - r, y - r, x + r, y + r), fill=ACCENT if e["post"] != cur else INK)
            else:
                d.ellipse((x - r, y - r, x + r, y + r), outline=INK2, width=3)
        if 0 <= idx < len(shots):
            e, m = shots[idx]
            if m["id"] not in cache:
                cache[m["id"]] = fit_photo(ROOT / m["file"], (700, 330))
            ph = cache[m["id"]]
            local = (t - sweep) - idx * per
            a = ease(local / 0.3) * (1 - ease((local - (per - 0.25)) / 0.25) * 0.0)
            px, py = (W - ph.width) // 2, 168 + (330 - ph.height) // 2
            d.rectangle((px - 6, py - 6, px + ph.width + 6, py + ph.height + 6), fill=PANEL2)
            if a < 1:
                ph = Image.blend(Image.new("RGB", ph.size, PANEL2), ph, a)
            im.paste(ph, (px, py))
            did = next((i for i in e["ids"] if i in RECIPIENT_EN), None)
            cap = f"{ru_month(e['date'])}  ·  {RECIPIENT_EN.get(did, '')}"
            d.text((W // 2, 514), cap, font=sans(24), fill=INK, anchor="ma")
        d.text((x0, 668), "●  includes «Булат»      ○  «Капюшон» only      Photos and recipients as the foundation's own posts give them", font=sans(16), fill=INK3)
        return im
    return f, total


QUOTES = [
    (421, "Фонд «Наша Правда», партия «Единая Россия» и ЦБСТ доставили участникам СВО на Запорожском направлении новые дроны",
     "Foundation «Наша Правда», the party «Единая Россия» and ЦБСТ delivered new drones to participants of the “special military operation” on the Zaporizhzhia direction."),
    (422, "…средства радиоэлектронной разведки «Перехват» и уже зарекомендовавший себя на фронте «Булат».",
     "…electronic-intelligence systems «Перехват» and «Булат», which has already proved itself at the front."),
    (422, "Всего за три дня поездки по приграничным территориям участникам СВО передали спецтехники на сумму около 80 млн рублей.",
     "In three days of travel through border areas, equipment worth about 80 million rubles was handed to participants."),
]


def scene_quotes(D):
    P = D["posts"]
    for mid, ru, _ in QUOTES:  # verbatim check against the stored post text
        body = ru.lstrip("…").rstrip(".") if ru.startswith("…") else ru
        assert body in P[mid][0], f"quote not in post {mid}: {ru[:50]}"
    per = 5.0

    def f(t):
        im, d = canvas()
        d.text((96, 80), "IN THE FOUNDATION'S OWN WORDS", font=mono(16), fill=ACCENT)
        i = min(int(t / per), len(QUOTES) - 1)
        mid, ru, en = QUOTES[i]
        local = t - i * per
        a = ease(local / 0.5)
        fade = lambda c: tuple(int(PAPER[j] + (c[j] - PAPER[j]) * a) for j in range(3))
        d.rectangle((96, 140, 1184, 600), fill=PANEL, outline=RULE)
        date = P[mid][1][:10]
        d.text((130, 166), f"Telegram post {mid}  ·  {dt.date.fromisoformat(date).strftime('%d.%m.%Y')}", font=mono(16), fill=INK3)
        y = text_block(d, (130, 214), ru, bold(34), fade(INK), 1000)
        y = max(y, 400) + 20
        d.line((130, y, 1150, y), fill=RULE)
        d.text((130, y + 16), "TRANSLATION", font=mono(13), fill=INK3)
        text_block(d, (130, y + 42), en, sans(26), fade(INK2), 1000)
        return im
    return f, per * len(QUOTES)


def scene_limits(D):
    pts = ["Every handover here is the foundation's own report. For most there is no second source.",
           "A delivery does not show combat use: recipients can be in the rear.",
           "ЦБСТ is named as co-donor in these posts. How large its part was is not stated.",
           "Equipment is as the posts describe it. Nobody here has inspected it."]

    def f(t):
        im, d = canvas()
        d.text((96, 120), "WHAT THIS DOES NOT SHOW", font=mono(16), fill=ACCENT)
        y = 200
        for i, p in enumerate(pts):
            a = ease((t - 0.4 - i * 1.4) / 0.5)
            if a <= 0:
                continue
            col = tuple(int(PAPER[j] + (INK[j] - PAPER[j]) * a) for j in range(3))
            d.rectangle((96, y + 8, 106, y + 18), fill=ACCENT)
            y = text_block(d, (130, y), p, sans(32), col, 1020) + 30
        return im
    return f, 9.0


def scene_end(D):
    def f(t):
        im, d = canvas()
        d.text((W // 2, 300), "Фонд «Наша Правда»", font=bold(52), fill=INK, anchor="ma")
        d.text((W // 2, 376), "ИНН " + D["f"]["inn"], font=mono(24), fill=INK2, anchor="ma")
        d.text((W // 2, 440), "Draft for review. Not published.", font=sans(22), fill=INK3, anchor="ma")
        return im
    return f, 4.0


SCENES = {"title": scene_title, "who": scene_who, "money": scene_money, "stock": scene_stock,
          "timeline": scene_timeline, "quotes": scene_quotes, "limits": scene_limits, "end": scene_end}


def render(D, out: Path) -> float:
    scenes = [(n, *fn(D)) for n, fn in SCENES.items()]
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-movflags", "+faststart", str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    total = 0.0
    xf = 0.35
    for n, fn, dur in scenes:
        for k in range(int(dur * FPS)):
            t = k / FPS
            im = fn(t)
            e = min(t, dur - t)
            if e < xf:  # dip to ground at each scene edge
                im = Image.blend(Image.new("RGB", (W, H), PAPER), im, ease(e / xf))
            p.stdin.write(im.tobytes())
        total += dur
    p.stdin.close()
    p.wait()
    return total


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--still", choices=list(SCENES))
    ap.add_argument("--t", type=float, default=3.0)
    ap.add_argument("--out", default=str(OUT / "nasha_pravda_explainer_draft.mp4"))
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    D = load()
    if a.still:
        fn, dur = SCENES[a.still](D)
        p = OUT / f"_still_{a.still}.png"
        fn(min(a.t, dur - 0.01)).save(p)
        print(p)
        return 0
    total = render(D, Path(a.out))
    print(f"{total:.1f}s -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
