#!/usr/bin/env python3
"""Story 1, chapters 0 and 1 (draft): Фонд «Наша Правда». A private preview page for the general reader.

  python3 exhibits/build_story.py              # writes exhibits/story_01.html (picture embedded, Google Fonts)

Every figure is read from data/registry/ (the foundation's accounts as recorded in its
marketing_claims, the deliveries in products.json); every quotation comes from quotes.json and is
checked against the stored post text. Citations are the generated titles and public links from
sources.json; the page prints no source id, slug or field name. Layout is exhibits/story.css, tokens
come from design/roymarket.css. Local, no network. Outline: notes/story_01_outline_20261007.md.
"""
from __future__ import annotations

import base64
import datetime as dt
import html
import json
import re
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from display_helpers import design_head, ru_date  # noqa: E402

REG = REPO / "data" / "registry"
SLUG = "fond-nasha-pravda"
esc = html.escape


def load(name):
    return json.loads((REG / name).read_text(encoding="utf-8"))


def num(text: str) -> float:
    """The first amount in a printed line such as '… – 1 099 813,00' (thousand rubles)."""
    m = re.search(r"(\d[\d\s ]*\d),(\d\d)", text)
    return float(m.group(1).replace(" ", "").replace(" ", "") + "." + m.group(2))


class Story:
    def __init__(self):
        self.ent = {e["slug"]: e for e in load("entities.json")}[SLUG]
        self.src = {s["id"]: s for s in load("sources.json")}
        self.quotes = {q["text_ru"][:60]: q for q in load("quotes.json")}
        self.media = {m["id"]: m for m in load("media.json")}
        self.notes: list[str] = []
        self.uses: dict[str, int] = {}

    # -- citations: the generated title and public link. ref() leaves a token; finalize() numbers the
    # sources by first appearance in the finished page, so the numbers always run in reading order.
    def ref(self, sid: str) -> str:
        assert sid in self.src, f"unknown source {sid}"
        return f"@@REF:{sid}@@"

    def finalize(self, doc: str) -> str:
        order: list[str] = []
        for m in re.finditer(r"@@REF:(s\d+)@@", doc):
            if m.group(1) not in order:
                order.append(m.group(1))
        seen: set[str] = set()

        def sub(m):
            sid = m.group(1)
            n = order.index(sid) + 1
            ident = "" if sid in seen else f' id="r{n}"'
            seen.add(sid)
            return f'<sup class="fn"><a href="#n{n}"{ident}>{n}</a></sup>'

        doc = re.sub(r"@@REF:(s\d+)@@", sub, doc)
        items = []
        for i, sid in enumerate(order, 1):
            src = self.src[sid]
            title, url = src.get("title") or "Archived document", src.get("public_url")
            link = f' <a href="{esc(url)}">{esc(url)}</a>' if url else " (no public link on file)"
            items.append(f'<li id="n{i}">{esc(title)}.{link} <a href="#r{i}" aria-label="Back to text">↩</a></li>')
        self.notes = order
        return doc.replace("@@NOTES@@", "".join(items))

    def quote(self, ru_start: str) -> dict:
        q = next((q for k, q in self.quotes.items() if q["text_ru"].startswith(ru_start)), None)
        assert q, f"quote not in quotes.json: {ru_start}"
        return q

    def check_posts(self, quotes: list[dict], channel_id=1905141464, msg=422):
        """Each passage must stand in the stored post text, ellipses and the closing full stop aside."""
        text = sqlite3.connect(REPO / "data" / "roymarket.db").execute(
            "select text from tg_posts where channel_id=? and msg_id=?", (channel_id, msg)).fetchone()[0]
        norm = lambda x: " ".join(x.replace("\u00a0", " ").split())
        for q in quotes:
            assert norm(q["text_ru"].rstrip(".;:")) in norm(text), f"not in post {msg}: {q['text_ru'][:50]}"

    # -- figures
    def figures(self):
        claims = {c["text_ru"][:24]: c for c in self.ent["marketing_claims"] if c["source_id"] == "s0389"}
        aid = num(next(c for k, c in claims.items() if k.startswith("Социальная"))["text_ru"])
        donors = num(next(c for k, c in claims.items() if k.startswith("Целевые средства от юр"))["text_ru"])
        fy = {f["year"]: f for f in self.ent["financials"]}["2024"]
        used, got = fy["funds_used"] / 1000, fy["funds_received"] / 1000
        prods = load("products.json")
        events = {d["post_id"]: d["date"] for p in prods for d in p["deliveries"] if d["donor"] == SLUG}
        dates = sorted(events.values())
        return {"aid_bn": aid / 1e6, "aid_share": 100 * aid / used, "donor_share": 100 * donors / got,
                "got_bn": got / 1e6, "events": len(events), "first": dates[0], "last": dates[-1]}


# FY2024 notes §18 (p.35 of 35) and FY2025 notes §3.17 (pp.15-16 of 20), as printed, thousand rubles. Read from
# the page images on 07-08.10.2026; render() asserts that they agree with the accounts record.
RECEIVED_2024 = [
    ("Целевые средства от юридических и физических лиц на ведение уставной деятельности", "targeted funds from legal entities and individuals for statutory activity", 1_099_813),
    ("Целевые средства от учредителей деньгами: Фонд «ДАР» 5 000, Фонд «Градислава» 54 000", "targeted funds from the founders, in money: «ДАР» 5,000 and «Градислава» 54,000", 59_000),
    ("Добровольные имущественные взносы и пожертвования от учредителей и юридических лиц", "voluntary property contributions and donations from founders and legal entities", 59_000),
    ("Прибыль от приносящей доход деятельности", "profit from income-generating activity", 14_700),
]
USED_2024 = [
    ("Социальная и благотворительная помощь для зоны СВО", "social and charitable aid for the SVO zone", 1_302_289),
    ("Расходы на содержание аппарата управления (включая начисления и страховые взносы)", "upkeep of the management apparatus, including contributions and insurance", 36_324),
    ("Расходы по содержанию организации", "upkeep of the organisation", 13_726),
    ("Расходы на приобретение основных средств материальных активов", "purchase of fixed assets", 9_865),
]
PRINTED_USED_2024 = 1_362_206
AID_2025 = 592_889.7


def k(n):
    return f"{n:,.0f}"


def money_chart(fin) -> str:
    """Received and used, 2024 and 2025, drawn to one scale (million rubles)."""
    rows = [(y, lab, fin[y][key] / 1e6) for y in ("2024", "2025") for lab, key in (("received", "funds_received"), ("used", "funds_used"))]
    mx, x0, w = 1500.0, 70, 560
    out = ['<svg class="chart" viewBox="0 0 760 232" role="img" aria-label="Funds received and used, 2024 and 2025">']
    for t in (0, 500, 1000, 1500):
        x = x0 + w * t / mx
        out.append(f'<line class="grid" x1="{x:.1f}" y1="8" x2="{x:.1f}" y2="196"/><text class="tick" x="{x:.1f}" y="216" text-anchor="middle">{t / 1000:.1f}bn</text>')
    y = 14
    for i, (yr, lab, v) in enumerate(rows):
        if lab == "received":
            out.append(f'<text class="yr" x="0" y="{y + 20}">{yr}</text>')
        out.append(f'<rect class="bar {lab}" x="{x0}" y="{y}" width="{w * v / mx:.1f}" height="26"/>'
                   f'<text class="lbl" x="{x0 + w * v / mx + 8:.1f}" y="{y + 18}">{v / 1000:.2f}bn {lab}</text>')
        y += 34 if lab == "received" else 50
    out.append("</svg>")
    return "".join(out)


# How each of the 21 handover posts names its recipients (registry delivery records, 'as the post names it').
# Buckets are ours; render() asserts that every event is placed once.
BUCKETS = [
    ("A formation by name or number", [422, 310, 448]),
    ("A grouping or a type of unit only", [397, 487, 454, 369, 444, 493, 494]),
    ("Servicemen on a direction or in a region, or no unit named", [393, 473, 615, 302, 398, 408, 519, 593, 608]),
    ("A civilian service", [311, 382]),
]
# Values the posts print for the whole batch, million rubles (the batch mixes products). 'more' = «более», 'about' = «около».
STATED_VALUE = {382: (10.5, ""), 397: (14.0, "more"), 408: (8.6, ""), 422: (18.2, ""), 444: (7.5, "about"), 448: (4.6, ""),
                473: (1.5, ""), 493: (1.3, "about"), 519: (1.3, "about"), 593: (2.8, "more"), 608: (10.0, "more"), 615: (2.0, "more")}
GALLERY = ["m0068", "m0070", "m0073", "m0076", "m0077", "m0080", "m0083", "m0087"]
GALLERY_RECIPIENT = {"m0068": "Krasnoarmeysk direction", "m0070": "“Participants of the operation”", "m0073": "Servicemen from Altai, Kursk direction",
                     "m0076": "EW and UAV units of group “Center”", "m0077": "1st motor-rifle company, Zaporizhzhia region",
                     "m0080": "Motor-rifle regiment", "m0083": "Kursk region", "m0087": "Svatove direction"}


def handover_events():
    prods = load("products.json")
    ev: dict = {}
    for p in prods:
        for d in p["deliveries"]:
            if d["donor"] != SLUG:
                continue
            e = ev.setdefault(d["post_id"], {"post": d["post_id"], "date": d["date"], "prods": set(), "recipient": d["recipient"], "cred": set()})
            e["prods"].add(p["slug"])
            e["cred"].add(d["credibility"])
    return sorted(ev.values(), key=lambda e: e["date"])


def clean_recipient(r: str) -> str:
    return re.sub(r"\s*\([^)]*\)", "", r).strip().rstrip(";")


def handover_timeline(events) -> str:
    d0, d1 = dt.date(2024, 6, 15), dt.date(2026, 6, 30)
    x0, w = 96, 640
    xs = lambda iso: x0 + w * (dt.date.fromisoformat(iso) - d0).days / (d1 - d0).days
    rows = {"bulat": 58, "kapyushon": 112}
    civilian = {311, 382}
    o = ['<svg class="chart tl" viewBox="0 0 760 190" role="img" aria-label="Twenty-one handovers by date, by product">']
    m = dt.date(2024, 7, 1)
    while m <= dt.date(2026, 6, 1):
        x = xs(m.isoformat())
        o.append(f'<line class="grid" x1="{x:.1f}" y1="22" x2="{x:.1f}" y2="150"/>')
        if m.month in (1, 7):
            o.append(f'<text class="tick" x="{x:.1f}" y="170" text-anchor="middle">{m.strftime("%b %Y")}</text>')
        m = dt.date(m.year + (m.month // 12), m.month % 12 + 1, 1)
    o.append(f'<text class="lbl" x="0" y="{rows["bulat"] + 4}">«Булат»</text><text class="lbl" x="0" y="{rows["kapyushon"] + 4}">«Капюшон»</text>')
    last, stack = {}, {}
    for e in events:
        x = xs(e["date"])
        for pr, y in rows.items():
            if pr not in e["prods"]:
                continue
            if pr in last and x - last[pr] < 11:
                stack[pr] += 1
            else:
                stack[pr] = 0
            last[pr] = x
            yy = y - 12 * stack[pr]
            ring = f'<circle class="ring" cx="{x:.1f}" cy="{yy}" r="10"/>' if e["post"] in civilian else ""
            shape = (f'<circle class="dot b" cx="{x:.1f}" cy="{yy}" r="5.5"/>' if pr == "bulat"
                     else f'<rect class="dot k" x="{x - 5:.1f}" y="{yy - 5}" width="10" height="10"/>')
            o.append(ring + shape)
    o.append("</svg>")
    return "".join(o)


# ЦБСТ's own accounts (form 0710003, report on the use of targeted funds), as printed, thousand rubles: (printed line,
# translation, 2024, 2025). Read from the filings' spreadsheets; render() asserts the totals against the accounts record.
CBST_LINES = [
    ("Остаток средств на начало отчетного года", "balance at the start of the year", 0, 171_788),
    ("Прочие поступления", "other receipts", 269_835, 137_105),
    ("На целевые мероприятия", "for target events", 0, 48_679),
    ("На содержание организации", "upkeep of the organisation", 81_371, 167_858),
    ("На приобретение основных средств и иного имущества", "purchase of fixed assets and other property", 4_990, 0),
    ("Прочие", "other", 11_686, 59_050),
    ("Использовано средств – всего", "used in total", 98_047, 275_587),
    ("Остаток средств на конец периода", "balance at the end of the period", 171_788, 33_306),
]
# The five agreements printed under the ЦБСТ line in the foundation's FY2024 notes (p.33 of 35), rubles.
CONTRIBUTIONS = [("22.08.2024", "Соглашение", 10_000_000), ("07.10.2024", "Соглашение № 2", 18_000_000), ("28.11.2024", "Соглашение № 3", 9_200_000),
                 ("20.12.2024", "Соглашение № 4", 20_435_024), ("23.12.2024", "Соглашение № 5", 13_500_000)]


def month_year(iso: str) -> str:
    return dt.date.fromisoformat(iso).strftime("%B %Y")


def pic(path: Path) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(path.read_bytes()).decode()


def render(out: Path):
    S = Story()
    F = S.figures()
    today = dt.date.today().isoformat()

    q_head = S.quote("Фонд «Наша Правда», «Единая Россия» и ЦБСТ доставили очередную")
    q_list = S.quote("средства радиоэлектронной разведки")
    q_cost = S.quote("Оборудование стоимостью 18,2")
    q_total = S.quote("Всего за три дня")
    q_aim = S.quote("поддержка отдельных юридических лиц")
    q_site = S.quote('Фонд "Наша Правда" - это совместный')
    S.check_posts([q_head, q_list, q_cost, q_total])
    m = S.media["m0075"]
    assert m["publish"] == "ok" and m["redact"] == "none_needed"

    # Page order fixes the footnote numbers.
    r_notes = S.ref("s0389")
    r_posts = S.ref("s8896")
    r_reg = S.ref("s0221")
    r_site = S.ref("s7370")
    r_notes2 = S.ref("s0389")
    d = S.ent["director"]
    registered = month_year(dt.datetime.strptime(S.ent["registered"], "%d.%m.%Y").date().isoformat())

    q_aid = S.quote("Фонд не получал государственную помощь")
    q_boy = S.quote("Рации для связи, проверенное")
    q_gru = S.quote("Помощь от фонда «Наша Правда», Единой России и ЦБСТ передали")
    q_3d = S.quote("Ударные дроны и гексакоптеры")
    q_vic = S.quote("Шаг за шагом")
    S.check_posts([q_boy], msg=448)
    S.check_posts([q_gru, q_3d, q_vic], msg=656)
    events = handover_events()
    posts = {e["post"] for e in events}
    placed = [x for _, ids in BUCKETS for x in ids]
    assert len(events) == 21 and sorted(placed) == sorted(posts), "buckets must place every handover once"
    assert all(c == {"single"} for c in (e["cred"] for e in events)), "chapter says all 21 are single-source"
    db = sqlite3.connect(REPO / "data" / "roymarket.db")
    norm = lambda x: " ".join(x.replace("\u00a0", " ").split())
    for mid, (v, qual) in STATED_VALUE.items():
        t = norm(db.execute("select text from tg_posts where channel_id=1905141464 and msg_id=?", (mid,)).fetchone()[0])
        assert re.search(rf"(?<!\d){str(v).replace('.', ',').rstrip('0').rstrip(',')}(?:\d)? ?(?:млн|тыс)", t) or re.search(rf"{int(v)} ?млн", t), f"value of post {mid} not in text"
    value_sum = sum(v for v, _ in STATED_VALUE.values())
    value_lo, value_hi = min(v for v, _ in STATED_VALUE.values()), max(v for v, _ in STATED_VALUE.values())
    by_post = {e["post"]: e for e in events}
    bucket_rows = "".join(
        f'<tr><td>{esc(lab)}</td><td>{len(ids)}</td><td class="ru">{"; ".join(esc(clean_recipient(by_post[i]["recipient"])) for i in ids[:3])}</td></tr>'
        for lab, ids in BUCKETS)
    timeline = handover_timeline(events)
    gal = []
    for mid in GALLERY:
        mm = S.media[mid]
        assert mm["publish"] == "ok" and mm["redact"] == "none_needed"
        gal.append(f'<figure class="rm-fig"><div class="frame"><img src="{pic(REPO / mm["file"])}" alt="{esc(mm["shows"])}" loading="lazy"></div>'
                   f'<figcaption><span class="rm-prov">Published by the foundation</span><span>{esc(mm["shows"])}</span>'
                   f'<span class="when">{month_year(mm["published"])} · {esc(GALLERY_RECIPIENT[mid])}</span></figcaption></figure>')
    gallery = "".join(gal)
    q_site1 = S.quote("Автономная некоммерческая организация «Центр беспилотных систем")
    q_site2 = S.quote("Учредители ЦБСТ")
    q_sid = S.quote("ЦБСТ вместе с Единой Россией и фондом")
    q_sub = S.quote("дочернее предприятие Фонда")
    q_contrib = S.quote("Внесение добровольного целевого")
    norm_ = lambda x: " ".join(x.replace("\u00a0", " ").split())
    web = norm_(html.unescape(re.sub(r"<[^>]+>", " ", (REPO / "data/sources/WEBCAPTURE_20261001_cbst-ru-masshtabiruet-ploschadku-rojmarket.html").read_text(encoding="utf-8", errors="ignore"))))
    for qq in (q_site1, q_site2):
        assert norm_(qq["text_ru"]) in web, "ЦБСТ website quote not in the capture"
    S.check_posts([q_sid], channel_id=2581147715, msg=618)
    cbst = {e["slug"]: e for e in load("entities.json")}["ano-tsbst-centre-for-unmanned-systems-technologies"]
    cf = {f["year"]: f for f in cbst["financials"]}
    for yr, col in (("2024", 2), ("2025", 3)):
        assert cf[yr]["funds_received"] == CBST_LINES[1][col] * 1000 and cf[yr]["funds_used"] == CBST_LINES[6][col] * 1000, f"ЦБСТ {yr} totals differ from the accounts record"
        assert cf[yr]["funds_balance_end"] == CBST_LINES[7][col] * 1000
        assert sum(r[col] for r in CBST_LINES[2:6]) == CBST_LINES[6][col]
    contrib_total = sum(c[2] for c in CONTRIBUTIONS)
    assert contrib_total == 71_135_024
    dash = lambda n: "—" if n == 0 else k(n)
    cbst_rows = "".join(
        f'<tr{" class=tot" if i in (6, 7) else ""}><td class="ru">{esc(r[0])}</td><td>{esc(r[1])}</td><td>{dash(r[2])}</td><td>{dash(r[3])}</td></tr>'
        for i, r in enumerate(CBST_LINES))
    contrib_rows = "".join(f'<tr><td>{c[0]}</td><td class="ru">{esc(c[1])}</td><td>{k(c[2])}</td></tr>' for c in CONTRIBUTIONS)
    ev_share = 100 * CBST_LINES[2][3] / CBST_LINES[6][3]
    up_share = 100 * CBST_LINES[3][3] / CBST_LINES[6][3]
    centre_ev25, centre_up25 = CBST_LINES[2][3] / 1000, CBST_LINES[3][3] / 1000
    centre_used25 = CBST_LINES[6][3] / 1000
    r_641 = S.ref("s9229")
    q_hosp = S.quote("Фонд «Наша Правда» при поддержке представителей партии")
    q_hosp2 = S.quote("«Капюшоны» помогут обезопасить")
    q_kher = S.quote("Фонд «Наша Правда» привез детекторы дронов")
    q_kher2 = S.quote("Оборудование передадут бригадам")
    S.check_posts([q_hosp, q_hosp2], msg=311)
    S.check_posts([q_kher, q_kher2], msg=382)
    fin = {f["year"]: f for f in S.ent["financials"]}
    recv_total, used_sum = sum(r[2] for r in RECEIVED_2024), sum(r[2] for r in USED_2024)
    assert recv_total * 1000 == fin["2024"]["funds_received"], "received lines do not add to the accounts"
    assert abs(PRINTED_USED_2024 * 1000 - fin["2024"]["funds_used"]) < 1, "printed total differs from the accounts"
    assert 0 <= PRINTED_USED_2024 - used_sum <= 2
    used25 = fin["2025"]["funds_used"] / 1000
    F["got25_bn"] = fin["2025"]["funds_received"] / 1e9
    r_notes25 = S.ref("s0390")
    shade = ["s1", "s2", "s3", "s4"]
    split_bar = "".join(f'<span class="seg {c}" style="width:{100 * r[2] / recv_total:.2f}%"><b>{100 * r[2] / recv_total:.1f}%</b></span>' for c, r in zip(shade, RECEIVED_2024))
    recv_rows = "".join(f'<tr><td class="ru">{esc(r[0])}</td><td>{esc(r[1])}</td><td>{k(r[2])}</td><td>{100 * r[2] / recv_total:.1f}%</td></tr>' for r in RECEIVED_2024)
    used_rows = "".join(f'<tr><td class="ru">{esc(r[0])}</td><td>{esc(r[1])}</td><td>{k(r[2])}</td><td>{100 * r[2] / PRINTED_USED_2024:.1f}%</td></tr>' for r in USED_2024)
    chart = money_chart(fin)

    def passage(q):
        return f'<p class="pass"><span class="ru">{esc(q["text_ru"])}</span><span class="en">{esc(q["translation_en"])}</span></p>'

    doc = f"""<!doctype html>
<!-- Generated by exhibits/build_story.py from data/registry on {today}. Do not edit by hand. -->
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Aid for the Zone</title>
{design_head((REPO / 'exhibits' / 'story.css').read_text())}</head>
<body>
<main class="story">
<header>
  <p class="rm-eyebrow">Draft · Story 1 · {ru_date(today)}</p>
  <h1 class="rm-h1">In 2024 a Moscow foundation booked {F['aid_bn']:.2f} billion rubles as <em>«social and charitable aid for the SVO zone»</em></h1>
  <p class="rm-dek">Its accounts do not name the donors behind nearly nine-tenths of its money. Its stated purposes include
  supporting companies that develop and make defence products. Its Telegram channel reports handing drones and
  electronic-warfare equipment to army units, with the ruling party and a drone-industry non-profit named as co-donors.
  «СВО», the Kremlin's term for its invasion of Ukraine, appears here only inside quotations.</p>
</header>

<section class="figures" aria-label="Three figures">
  <div class="figure"><span class="n">{F['aid_bn']:.2f}<small>bn rubles</small></span>
    <p>booked in 2024 as aid for the zone: {F['aid_share']:.1f}% of everything the foundation spent that year.{r_notes}</p>
    <p class="ru">«Социальная и благотворительная помощь для зоны СВО»</p><span class="rm-grade doc">Documented</span></div>
  <div class="figure"><span class="n">{F['donor_share']:.0f}<small>%</small></span>
    <p>of the {F['got_bn']:.2f} billion rubles it received in 2024 came from legal entities and individuals the accounts do not name.</p>
    <span class="rm-grade doc">Documented</span></div>
  <div class="figure"><span class="n">{F['events']}</span>
    <p>handovers naming «Булат» or «Капюшон» that the foundation reports in its own posts, {month_year(F['first'])} to {month_year(F['last'])}. Not a full count.</p>
    <span class="rm-grade rep">Reported</span></div>
</section>

<section class="chapter" aria-labelledby="c0">
  <p class="rm-eyebrow">The post</p>
  <h2 class="rm-h2" id="c0">Three days, 80 million rubles</h2>
  <div class="lead-in">
    <div class="text">
      <p>On 10 April 2025 the foundation's Telegram channel announced that it, the party «Единая Россия» and ЦБСТ had
      delivered another batch of equipment to servicemen of the 132nd Gorlovka Brigade on the Donetsk direction.{r_posts}
      The post lists FPV drones, Mavic quadcopters, motorcycles, quad bikes, remotely operated evacuation platforms,
      «Перехват» electronic-intelligence equipment and «Булат». It puts the batch at 18.2 million
      rubles and the whole trip at about 80 million.</p>
    </div>
    <figure class="rm-fig"><div class="frame"><img src="{pic(REPO / m['file'])}" alt="{esc(m['shows'])}"></div>
      <figcaption><span class="rm-prov">Published by the foundation</span>
      <span>A still posted with the announcement: {esc(m['shows'][0].lower() + m['shows'][1:])}</span>
      <span class="when">{ru_date(m['published'])}</span></figcaption></figure>
  </div>
  <article class="post" aria-label="Excerpts from the post">
    <header><span>Telegram · @nashapravdafond</span><span>{ru_date(q_head['date'])}</span><span>The foundation's own post</span></header>
    {passage(q_head)}{passage(q_list)}{passage(q_cost)}{passage(q_total)}
  </article>
  <p>The post's word for the delivery is <span class="ru-word">помощь</span>, <i>aid</i>. It is also the word on the largest line in the foundation's accounts for 2024.</p>
</section>

<section class="chapter" aria-labelledby="c1">
  <p class="rm-eyebrow">The foundation</p>
  <h2 class="rm-h2" id="c1">Its stated purposes include supporting defence-product makers</h2>
  <p><b>Фонд «Наша Правда»</b> (<i>Our Truth</i>) was registered in Moscow in {registered}. Its general director since
  registration is <b>Alexander Brovchenko</b> ({esc(d)}).{r_reg} Its website describes it as a joint project of two older
  foundations, «ДАР» and «Градислава», for servicemen and citizens in the «СВО» territory.{r_site}</p>
  <div class="excerpt"><p class="where">Foundation's website, «О фонде»</p>
    <blockquote class="rm-quote"><span class="rm-label">Original Russian</span>{esc(q_site['text_ru'])}
      <span class="gloss">{esc(q_site['translation_en'])}</span></blockquote></div>
  <p>The notes to the foundation's 2024 annual accounts, filed with the tax service, list what it is for.{r_notes2}
  The list begins with strengthening Russia's defence capability and takes in support for state bodies and the armed
  forces, and for «patriotic, volunteer and other public movements». One entry reads:</p>
  <div class="excerpt"><p class="where">Notes to the 2024 accounts, section 1.3, page 5</p>
    <blockquote class="rm-quote"><span class="rm-label">Original Russian</span>{esc(q_aim['text_ru'])}
      <span class="gloss">{esc(q_aim['translation_en'])}</span></blockquote></div>
  <p>That is the foundation's own description of its purposes. The figures come next: where the money came from, and where the accounts say it went.</p>
</section>

<section class="chapter" aria-labelledby="c2">
  <p class="rm-eyebrow">The money in</p>
  <h2 class="rm-h2" id="c2">Nearly nine-tenths of the 2024 money came from donors the notes do not name</h2>
  <p>In 2024 the foundation received {F['got_bn']:.2f} billion rubles in targeted funds. The notes to its accounts print four lines to say from whom.{r_notes2}</p>
  <div class="split" role="img" aria-label="Shares of the 2024 receipts by printed line">{split_bar}</div>
  <table class="lines"><thead><tr><th>As printed</th><th>Translation</th><th>Thousand rubles</th><th>Share</th></tr></thead><tbody>{recv_rows}
    <tr class="tot"><td colspan="2">Received in 2024, as printed</td><td>{k(recv_total)}</td><td>100%</td></tr></tbody></table>
  <p>Two donors are named: «ДАР», which gave 5 million rubles, and «Градислава», which gave 54 million. The 1.10 billion
  that make up the rest are credited to <span class="ru-word">юридических и физических лиц</span>, legal entities and
  individuals. The notes print no names and no amount per donor.</p>
  <p>The same notes say, in a sentence about something else, that <i>«{esc(q_aid['text_ru'])}»</i>, the foundation did not receive state aid, in 2024. They do not say what they mean by the term.{S.ref("s0389")}</p>
  <p>For 2025 the notes give the total, {F['got25_bn']:.2f} billion rubles, and no breakdown.{r_notes25}</p>
  {chart}
  <p class="chart-note">Targeted funds received and used, million rubles, from the filings. The balance carried forward fell from 434.4 million at the start of 2024 to 304.7 million at its end, and stood at 307.6 million at the end of 2025.</p>
</section>

<section class="chapter" aria-labelledby="c3">
  <p class="rm-eyebrow">The money out</p>
  <h2 class="rm-h2" id="c3">{F['aid_share']:.1f}% of what it spent in 2024 is booked as aid for the zone</h2>
  <table class="lines"><thead><tr><th>As printed</th><th>Translation</th><th>Thousand rubles</th><th>Share</th></tr></thead><tbody>{used_rows}
    <tr class="tot"><td colspan="2">Used in 2024, as printed</td><td>{k(PRINTED_USED_2024)}</td><td>100%</td></tr></tbody></table>
  <p>The four lines add to {k(used_sum)}. The filing's own total is {PRINTED_USED_2024 - used_sum} thousand rubles higher, and the notes do not say why.</p>
  <p>The first line says nothing of what was bought. For 2025 the notes give one line of use: <span class="ru-word">Целевые пожертвования в рамках уставной деятельности</span>, targeted donations within statutory activity, {AID_2025 / 1000:.1f} million rubles. That is {100 * AID_2025 / used25:.1f}% of the {used25 / 1000:.1f} million used. The other {(used25 - AID_2025) / 1000:.1f} million is not broken down.</p>
  <p>The foundation's posts say what "aid" covered, for some of it. They show it reaching more than servicemen.</p>
  <article class="post" aria-label="Excerpts from the post of 8 August 2024">
    <header><span>Telegram · @nashapravdafond</span><span>{ru_date(q_hosp['date'])}</span><span>The foundation's own post{S.ref("s8992")}</span></header>
    {passage(q_hosp)}{passage(q_hosp2)}
  </article>
  <article class="post" aria-label="Excerpts from the post of 15 January 2025">
    <header><span>Telegram · @nashapravdafond</span><span>{ru_date(q_kher['date'])}</span><span>The foundation's own post{S.ref("s8994")}</span></header>
    {passage(q_kher)}{passage(q_kher2)}
  </article>
  <p>Most of its reports name soldiers and units. Whether these two deliveries sit under the line for the zone, the notes do not say.</p>
</section>

<section class="chapter" aria-labelledby="c5">
  <p class="rm-eyebrow">The centre</p>
  <h2 class="rm-h2" id="c5">ЦБСТ's accounts book all of its money as «other receipts»</h2>
  <p>ЦБСТ, the autonomous non-profit «Центр беспилотных систем и технологий» (Centre for Unmanned Systems and
  Technologies), was registered in Moscow on 27 February 2024. The register names two founders: the foundation from the
  start, and the bank ПАО «Банк ПСБ» from 1 April 2025.{S.ref("s0228")} Its registered main activity is market research.
  The register lists publishing, software development, research and conference organising beside it, and nothing coded to defence.</p>
  <article class="post" aria-label="Excerpts from the ЦБСТ website">
    <header><span>cbst.ru</span><span>{ru_date(q_site2['date'])}</span><span>ЦБСТ's own website{S.ref("s8867")}</span></header>
    {passage(q_site1)}{passage(q_site2)}
  </article>
  <p>The register names two founders. ЦБСТ's own text names three.</p>
  <table class="lines"><thead><tr><th>As printed in ЦБСТ's accounts</th><th>Translation</th><th>2024</th><th>2025</th></tr></thead><tbody>{cbst_rows}</tbody></table>
  <p class="chart-note">Thousand rubles. Report on the use of targeted funds, FY2024{S.ref("s0382")} and FY2025.{S.ref("s0385")}</p>
  <p>In 2024 the line for target events is empty. In 2025 it holds {centre_ev25:.1f} million rubles, {ev_share:.1f}% of the
  {centre_used25:.1f} million used; upkeep of the organisation takes {centre_up25:.1f} million, {up_share:.1f}%.</p>
  <p>The accounts print no source for any of the money. In 2024 the line for contributions and other targeted receipts is
  empty and all 269.8 million sits under «other receipts»; the 2025 form has only that line. The 2025 notes say that,
  because ЦБСТ counts as a small business, it does not apply the accounting rule on related-party disclosure.</p>
  <p>The foundation's notes for 2024 describe ЦБСТ in their own words and list five agreements beneath them:</p>
  <article class="post" aria-label="Excerpts from the foundation's notes">
    <header><span>Notes to the foundation's 2024 accounts, section 16, page 33</span><span>The foundation's own filing{S.ref("s0389")}</span></header>
    {passage(q_sub)}{passage(q_contrib)}
  </article>
  <table class="lines plain3"><thead><tr><th>Date</th><th>As printed</th><th>Rubles</th></tr></thead><tbody>{contrib_rows}
    <tr class="tot"><td colspan="2">Together</td><td>{k(contrib_total)}</td></tr></tbody></table>
  <p>The notes print no recipient beside the amounts. «Subsidiary» is the foundation's word: the register records two
  founders and no ownership share. ЦБСТ's own 2024 accounts book every receipt as «other receipts», so the two filings
  cannot be matched to each other.</p>
  <p>On 15 December 2025 Александр Сидякин, secretary of ЦБСТ's supervisory board and head of the central executive
  committee of «Единая Россия»,{S.ref("s8699")} summed up the centre's year on his own channel:</p>
  <article class="post" aria-label="Excerpt from the post of 15 December 2025">
    <header><span>Telegram · @asidyakin</span><span>{ru_date(q_sid['date'])}</span><span>His own channel{S.ref("s8847")}</span></header>
    {passage(q_sid)}
  </article>
  <p>The post gives no source for the 2.5 billion dollars.</p>
</section>

<section class="chapter" aria-labelledby="c4">
  <p class="rm-eyebrow">The handovers</p>
  <h2 class="rm-h2" id="c4">Between July 2024 and May 2026 the foundation reported at least 21 handovers that name «Булат» or «Капюшон»</h2>
  <p>Two products recur in its posts. It calls «Булат» a drone detector, <i>детектор дронов</i>, and «Капюшон» an
  electronic-warfare station, <i>станция РЭБ</i>.{S.ref("s8994")} Each mark below is one post that names one or both.</p>
  {timeline}
  <p class="chart-note">Circle: a post naming «Булат». Square: a post naming «Капюшон». Ringed: the recipient is a civilian service. Source of every mark: the foundation's own channel.</p>
  <p>All 21 are the foundation's own reports. None has a second source on file. Where the foundation says a unit sent
  thanks, the thanks too appear on the foundation's channel.{S.ref("s8904")} The posts name the recipients at whatever
  level suits them:</p>
  <table class="lines plain"><thead><tr><th>How the post names the recipient</th><th>Posts</th><th>Examples, as the posts word them</th></tr></thead><tbody>{bucket_rows}</tbody></table>
  <p>The foundation says what the equipment is for in the same posts. One of them, to a motor-rifle company in the
  Zaporizhzhia region:</p>
  <article class="post" aria-label="Excerpt from the post of 9 June 2025">
    <header><span>Telegram · @nashapravdafond</span><span>{ru_date(q_boy['date'])}</span><span>The foundation's own post{S.ref("s8898")}</span></header>
    {passage(q_boy)}
  </article>
  <p>Twelve of the 21 posts put a value on the batch. The figures run from {value_lo:.1f} to {value_hi:.1f} million rubles
  and add up to about {value_sum:.0f} million, taking «more than» at the figure given. They are the foundation's values
  for whole batches, which also hold drones, radios and motorcycles, not prices of the two products.</p>
  <div class="rm-gallery" aria-label="Photographs published with the posts">{gallery}</div>
  <p>These 21 are only the handovers that name those two products. The foundation reports others. The most recent in
  this record, on 10 August 2026, is a different kind of list:{r_641}</p>
  <article class="post" aria-label="Excerpts from the post of 10 August 2026">
    <header><span>Telegram · @nashapravdafond</span><span>{ru_date(q_gru['date'])}</span><span>The foundation's own post</span></header>
    {passage(q_gru)}{passage(q_3d)}{passage(q_vic)}
  </article>
  <p>A handover to a unit does not show that the equipment was used in combat. Some recipients are rear units, and two
  of the 21 are civilian services.</p>
</section>

<section class="chapter" aria-label="Chapters in draft">
  <aside class="rm-card coming"><header><span class="rm-kind">In draft</span></header>
    <p>The chapters that follow are outlined and not yet written:</p>
    <ol><li>The marketplace</li><li>What this does not show</li></ol></aside>
</section>

<section class="rm-sources"><h2 class="rm-h2">Sources</h2><ol>@@NOTES@@</ol></section>
</main>
</body></html>
"""
    doc = S.finalize(doc)
    out.write_text(doc, encoding="utf-8")
    print(f"wrote {out.relative_to(REPO)}: {len(S.notes)} sources, {len(doc)//1024} KB")


def artifact_fragment(doc: str) -> str:
    """The Artifact tool wraps a page in its own skeleton, so it takes the title, style and body content only."""
    title = re.search(r"<title>.*?</title>", doc, re.S).group(0)
    head = re.search(r"</title>(.*)</head>", doc, re.S).group(1)
    body = re.search(r"<body>(.*)</body>", doc, re.S).group(1)
    return f"{title}\n{head}\n{body}\n"


if __name__ == "__main__":
    out = REPO / "exhibits" / "story_01.html"
    render(out)
    if "--artifact" in sys.argv:
        frag = out.with_name("story_01_artifact.html")
        frag.write_text(artifact_fragment(out.read_text(encoding="utf-8")), encoding="utf-8")
        print(f"wrote {frag.relative_to(REPO)}")
