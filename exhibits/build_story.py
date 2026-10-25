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
from display_helpers import (NAME_JS, caption_html, design_head, latinize_gloss, name_html, orig_line,
                             person_names, quote_html, ru_date)  # noqa: E402
import deliveries as dl  # noqa: E402

REG = REPO / "data" / "registry"
SLUG = "fond-nasha-pravda"
esc = html.escape


def load(name):
    return json.loads((REG / name).read_text(encoding="utf-8"))


FIXTURE = REPO / "tests" / "fixtures" / "story_sources.json"
WEBCAPTURE = "WEBCAPTURE_20261001_cbst-ru-masshtabiruet-ploschadku-rojmarket.html"
BLANK = "data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=="


class LocalTexts:
    """The texts the builder checks its quotations and figures against: Telegram posts in data/roymarket.db and one
    web capture in data/sources/, both only on the Mac. `local` reads them there (and remembers which it read, for
    --export-fixture). `fixture` reads tests/fixtures/story_sources.json, written on the Mac by --export-fixture, so
    CI can build the page; a text the fixture lacks, and every picture, is skipped there and counted, never faked
    as checked."""

    def __init__(self, mode: str = "local"):
        self.mode, self.used_posts, self.used_web, self.skipped, self.blank = mode, {}, {}, 0, 0
        self.fx = json.loads(FIXTURE.read_text(encoding="utf-8")) if mode == "fixture" and FIXTURE.exists() else {}

    def post(self, channel_id: int, msg: int) -> str | None:
        key = f"{channel_id}/{msg}"
        if self.mode == "local":
            row = sqlite3.connect(REPO / "data" / "roymarket.db").execute(
                "select text from tg_posts where channel_id=? and msg_id=?", (channel_id, msg)).fetchone()
            self.used_posts[key] = row[0]
            return row[0]
        return self.fx.get("posts", {}).get(key)

    def web(self, name: str) -> str | None:
        if self.mode == "local":
            raw = (REPO / "data" / "sources" / name).read_text(encoding="utf-8", errors="ignore")
            self.used_web[name] = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", raw)).split())
            return self.used_web[name]
        return self.fx.get("web", {}).get(name)

    def image(self, path: Path) -> str:
        if self.mode != "local" and not path.exists():
            self.blank += 1
            return BLANK
        return "data:image/jpeg;base64," + base64.b64encode(path.read_bytes()).decode()

    def export(self):
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(json.dumps({"note": "Written by exhibits/build_story.py --export-fixture from data/roymarket.db "
                                               "and data/sources/: the public post and page texts the story checks its "
                                               "quotations against. Regenerate, never hand-edit.",
                                       "posts": dict(sorted(self.used_posts.items())),
                                       "web": self.used_web}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


LOCAL = LocalTexts()


def num(text: str) -> float:
    """The first amount in a printed line such as '… – 1 099 813,00' (thousand rubles)."""
    m = re.search(r"(\d[\d\s ]*\d),(\d\d)", text)
    return float(m.group(1).replace(" ", "").replace(" ", "") + "." + m.group(2))


class Story:
    def __init__(self):
        self.ent = {e["slug"]: e for e in load("entities.json")}[SLUG]
        self.src = {s["id"]: s for s in load("sources.json")}
        self.quotes = {q["id"]: q for q in load("quotes.json")}   # keyed by id: two quotes can open with the same 60 characters
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
            link = f' <a href="{esc(url)}">{esc(readable_url(url))}</a>' if url else " (no public link on file)"
            items.append(f'<li id="n{i}">{esc(title)}.{link} <a href="#r{i}" aria-label="Back to text">↩</a></li>')
        self.notes = order
        return doc.replace("@@NOTES@@", "".join(items))

    def quote(self, ru_start: str) -> dict:
        hits = [q for q in self.quotes.values() if q["text_ru"].startswith(ru_start)]
        q = next((q for q in hits if q.get("source_id")), hits[0] if hits else None)   # the sourced one when a quote appears twice
        assert q, f"quote not in quotes.json: {ru_start}"
        return q

    def check_posts(self, quotes: list[dict], channel_id=1905141464, msg=422):
        """Each passage must stand in the stored post text, ellipses and the closing full stop aside."""
        text = LOCAL.post(channel_id, msg)
        if text is None:
            LOCAL.skipped += len(quotes)
            return
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
        prods = dl.load_products()
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
    prods = dl.load_products()
    ev: dict = {}
    for p in prods:
        for d in p["deliveries"]:
            if d["donor"] != SLUG:
                continue
            e = ev.setdefault(d["post_id"], {"post": d["post_id"], "date": d["date"], "prods": set(),
                                             "recipient": d["recipient"], "recipient_en": d.get("recipient_en"),
                                             "cred": set()})
            e["prods"].add(p["slug"])
            e["cred"].add(d["credibility"])
    return sorted(ev.values(), key=lambda e: e["date"])


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
    o.append(f'<text class="lbl" x="0" y="{rows["bulat"] + 4}">«Bulat»</text><text class="lbl" x="0" y="{rows["kapyushon"] + 4}">«Kapyushon»</text>')
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


RAIL_JS = """<script>try{const links=[...document.querySelectorAll('.rail a')];const io=new IntersectionObserver(es=>{es.forEach(e=>{if(e.isIntersecting){links.forEach(l=>l.classList.toggle('on',l.getAttribute('href')==='#'+e.target.id))}})},{rootMargin:'-20% 0px -70% 0px'});links.forEach(l=>{const t=document.querySelector(l.getAttribute('href'));if(t)io.observe(t)})}catch(e){}</script>"""


def stack_bar(items, label) -> str:
    """One stacked bar; items = (text, value, css class). Text shows inside a segment wide enough to hold it."""
    tot = sum(v for _, v, _ in items)
    seg = "".join(
        f'<span class="seg {c}" style="width:{100 * v / tot:.2f}%">' + (f"<b>{100 * v / tot:.1f}% {esc(t)}</b>" if 100 * v / tot >= 13 else "") + "</span>"
        for t, v, c in items)
    return f'<div class="split" role="img" aria-label="{esc(label)}">{seg}</div>'


def ln(grade, w=34):
    return f'<svg class="ln" width="{w}" height="8" aria-hidden="true"><line x1="0" x2="{w}" y1="4" y2="4" class="rm-ln {grade}"/></svg>'


def structure_diagram(F, S) -> str:
    """The structure in one picture. A line is drawn in the style of its grade: solid, a document shows it; dashed,
    one party's own word; dotted, no document shows it. Documented edges are asserted against the registry."""
    ents = {e["slug"]: e for e in load("entities.json")}
    cbst = ents["ano-tsbst-centre-for-unmanned-systems-technologies"]
    founders = " ".join(str(h.get("value")) for h in cbst.get("founders_history") or [])
    assert "Наша Правда" in founders and "ПСБ" in founders, "register founders of ЦБСТ changed"
    assert any(x.get("slug") == "ooo-mptm" for x in cbst.get("subsidiaries") or []), "ЦБСТ participation in МПТМ missing"
    assert ents["ooo-mptm"].get("ecosystem_roles") == ["platform_operator"]
    aid, donors = F["aid_share"], F["donor_share"]
    got = F["got_bn"]
    st = {"n": "dn", "m": "dm", "r": "dr"}

    def node(x, y, w, h, lines, hub=False):
        t, yy = [], y + 22
        for txt, kind in lines:
            t.append(f'<text class="{st[kind]}" x="{x + 12}" y="{yy}">{esc(txt)}</text>')
            yy += 18 if kind != "m" else 16
        return f'<rect class="nd{" hub" if hub else ""}" x="{x}" y="{y}" width="{w}" height="{h}" rx="4"/>' + "".join(t)

    def edge(g, d):
        return f'<path class="rm-ln {g}" d="{d}"/>'

    def lab(x, y, txt, anchor="middle"):
        return f'<text class="el" x="{x}" y="{y}" text-anchor="{anchor}">{esc(txt)}</text>'

    svg = ['<svg class="map" viewBox="0 0 1000 412" role="img" aria-label="Who funds, founds and receives from the foundation, drawn by how well each link is documented">']
    svg += [
        edge("doc", "M170 72 L230 128"), edge("doc", "M170 192 L230 168"),
        edge("doc", "M410 128 L540 128"), edge("open", "M410 170 L540 170"),
        edge("doc", "M640 56 L640 90"), edge("rep", "M640 252 L640 200"),
        edge("doc", "M740 145 L820 145"), edge("rep", "M320 200 L320 332"),
        lab(475, 120, "co-founder"), lab(475, 188, "5 contributions,"), lab(475, 202, "RUB 71.1m: no"), lab(475, 216, "recipient printed"),
        lab(650, 76, "co-founder", "start"), lab(650, 232, "TsBST's own site", "start"),
        lab(780, 137, "participates"), lab(330, 270, "21 handovers reported", "start"),
        node(0, 30, 170, 84, [("Legal entities and", "n"), ("individuals", "n"), ("not named in the accounts", "m"), (f"RUB 1.10bn · {donors:.1f}%", "m")]),
        node(0, 150, 170, 84, [("DAR and Gradislava", "r"), ("the two founding foundations", "m"), ("RUB 59m · 4.8%", "m")]),
        node(230, 90, 180, 110, [("Nasha Pravda", "r"), ("Nasha Pravda Foundation", "m"), (f"received RUB {got:.2f}bn", "m"), (f"booked {aid:.1f}% as aid", "m")]),
        node(540, 4, 200, 52, [("Bank PSB", "r"), ("in the register since 01.04.2025", "m")]),
        node(540, 90, 200, 110, [("TsBST", "r"), ("registered 27.02.2024", "m"), ("2024: RUB 269.8m received,", "m"), ("all as «other receipts»", "m")], hub=True),
        node(540, 252, 200, 66, [("United Russia", "r"), ("a founder by TsBST's own site;", "m"), ("not in the register", "m")]),
        node(820, 90, 180, 110, [("MPTM", "r"), ("operates ROY.MARKET", "m"), ("share not stated;", "m"), ("owners withheld", "m")]),
        node(230, 332, 510, 70, [("Army units and civilian services", "n"), ("naming «Bulat» or «Kapyushon», Jul 2024 – May 2026", "m"), ("the party and TsBST named as co-donors", "m")]),
    ]
    svg.append("</svg>")
    legend = ('<ul class="rm-legend">'
              f'<li>{ln("doc")} <span class="rm-grade doc">Documented</span> a document shows it</li>'
              f'<li>{ln("rep")} <span class="rm-grade rep">Reported</span> one party\'s own word</li>'
              f'<li>{ln("open")} <span class="rm-grade open">Not documented</span> no document shows it</li></ul>')
    return f'<figure class="mapfig"><div class="mapscroll">{"".join(svg)}</div><figcaption>{legend}</figcaption></figure>'


def readable_url(url: str) -> str:
    """Link text only: an internationalised domain shown as people write it; the href keeps the encoded form."""
    m = re.match(r"(https?://)([^/]+)(.*)", url)
    if not m or "xn--" not in m.group(2):
        return url
    try:
        return m.group(1) + m.group(2).encode("ascii").decode("idna") + m.group(3)
    except UnicodeError:
        return url


def month_year(iso: str) -> str:
    return dt.date.fromisoformat(iso).strftime("%B %Y")


def pic(path: Path) -> str:
    return LOCAL.image(path)


_POPS = {}


def pop(visible, cyrillic):
    """A Latin name on its first mention, with the registered Cyrillic form in a popover (STYLE_GUIDE §2.2)."""
    key = re.sub(r"\W+", "-", visible).strip("-").lower()
    _POPS[key] = _POPS.get(key, 0) + 1
    return name_html(visible, cyrillic, key=f"{key}-{_POPS[key]}")


def render(out: Path):
    S = Story()
    F = S.figures()
    today = dt.date.today().isoformat()
    people = load("people.json")
    sp = next(x for x in (people if isinstance(people, list) else people.get("people", [])) if x["slug"] == "aleksandr-sidyakin")
    pn = person_names(sp["fio_ru"], sp.get("name_latin"))
    sid = name_html(pn["first"], pn["fio"], key="sidyakin")

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
    norm = lambda x: " ".join(x.replace("\u00a0", " ").split())
    for mid, (v, qual) in STATED_VALUE.items():
        t = LOCAL.post(1905141464, mid)
        if t is None:
            LOCAL.skipped += 1
            continue
        t = norm(t)
        assert re.search(rf"(?<!\d){str(v).replace('.', ',').rstrip('0').rstrip(',')}(?:\d)? ?(?:млн|тыс)", t) or re.search(rf"{int(v)} ?млн", t), f"value of post {mid} not in text"
    value_sum = sum(v for v, _ in STATED_VALUE.values())
    value_lo, value_hi = min(v for v, _ in STATED_VALUE.values()), max(v for v, _ in STATED_VALUE.values())
    by_post = {e["post"]: e for e in events}
    bucket_rows = "".join(
        f'<tr><td>{esc(lab)}</td><td>{len(ids)}</td><td>{"; ".join(name_html(by_post[i]["recipient_en"], by_post[i]["recipient"], key=f"recipient-{i}", what="Recipient wording from the post:") for i in ids[:3])}</td></tr>'
        for lab, ids in BUCKETS)
    timeline = handover_timeline(events)
    gal = []
    for mid in GALLERY:
        mm = S.media[mid]
        assert mm["publish"] == "ok" and mm["redact"] == "none_needed"
        gal.append(f'<figure class="rm-fig"><div class="frame"><img src="{pic(REPO / mm["file"])}" alt="{esc(mm.get("shows_en") or mm["shows"])}" loading="lazy"></div>'
                   f'<figcaption><span class="rm-prov">Published by the foundation</span><span>{caption_html(mm["shows"], "story-" + mid, mm.get("shows_en"))}</span>'
                   f'<span class="when">{month_year(mm["published"])} · {esc(GALLERY_RECIPIENT[mid])}</span></figcaption></figure>')
    gallery = "".join(gal)
    q_site1 = S.quote("Автономная некоммерческая организация «Центр беспилотных систем")
    q_site2 = S.quote("Учредители ЦБСТ")
    q_sid = S.quote("ЦБСТ вместе с Единой Россией и фондом")
    q_sub = S.quote("дочернее предприятие Фонда")
    q_contrib = S.quote("Внесение добровольного целевого")
    norm_ = lambda x: " ".join(x.replace("\u00a0", " ").split())
    web = LOCAL.web(WEBCAPTURE)
    for qq in (q_site1, q_site2):
        if web is None:
            LOCAL.skipped += 1
            continue
        assert norm_(qq["text_ru"]) in norm_(web), "ЦБСТ website quote not in the capture"
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
        f'<tr{" class=tot" if i in (6, 7) else ""}><td>{name_html(latinize_gloss(r[1]), r[0], key=f"cbst-line-{i}", what="Original account line:")}</td>'
        f'<td>{dash(r[2])}</td><td>{dash(r[3])}</td></tr>'
        for i, r in enumerate(CBST_LINES))
    contrib_rows = "".join(
        f'<tr><td>{c[0]}</td><td>{name_html("Agreement" + (f" no. {i}" if i > 1 else ""), c[1], key=f"contribution-{i}", what="Original agreement line:")}</td>'
        f'<td>{k(c[2])}</td></tr>' for i, c in enumerate(CONTRIBUTIONS, 1))
    ev_share = 100 * CBST_LINES[2][3] / CBST_LINES[6][3]
    up_share = 100 * CBST_LINES[3][3] / CBST_LINES[6][3]
    centre_ev25, centre_up25 = CBST_LINES[2][3] / 1000, CBST_LINES[3][3] / 1000
    centre_used25 = CBST_LINES[6][3] / 1000
    sid338 = next(x["id"] for x in S.src.values() if x.get("tg_post") == "ano_cbst/338")
    q_m1 = S.quote("У военнослужащих появится возможность")
    q_m2 = S.quote("Мы сделали «военный маркетплейс»")
    q_m3 = S.quote("Ребята, которые здесь работают")
    q_618 = S.quote("Вместе с партией и ПСБ запустили")
    q_row = S.quote("Участие в обществах с ограниченной")
    q_op = S.quote("Агент / Оператор платформы")
    q_mask = S.quote("Наименование Агента")
    q_restr = S.quote("Доступ к сведениям ограничен")
    q_kb = S.quote("Теперь ТЭЧ могут")
    q_3mx = S.quote("Всю нашу продукцию")
    q_pilot = S.quote("Пилотный запуск подтвердил")
    q_tech = S.quote("К 1 сентября")
    for qq in (q_m2, q_618, q_row, q_op, q_mask, q_restr, q_kb, q_3mx, q_pilot, q_tech):
        assert qq["source_id"], f"quote has no source: {qq['text_ru'][:40]}"
    S.check_posts([q_m1, q_m2, q_m3], channel_id=2159491523, msg=338)
    S.check_posts([q_618], channel_id=2581147715, msg=618)
    S.check_posts([q_pilot], channel_id=2581147715, msg=1230)
    S.check_posts([q_tech], channel_id=2159491523, msg=2392)
    # The closing (chapter 8): the foundation's posts after the 21, and its post on Сидякин's Duma appointment.
    q_91 = S.quote("Связисты 91-й бригады управления")
    q_amb = S.quote("Фонд «Наша Правда» передал 237-му")
    q_cong = S.quote("Мы давно сотрудничаем с Александром")
    S.check_posts([q_91], msg=678)
    S.check_posts([q_cong], msg=686)
    S.check_posts([q_amb], msg=688)
    S.check_posts([q_kb], channel_id=1535506795, msg=321)
    S.check_posts([q_3mx], channel_id=1651823792, msg=42146)
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
    recv_rows = "".join(
        f'<tr><td>{name_html(latinize_gloss(r[1]), r[0], key=f"received-line-{i}", what="Original account line:")}</td>'
        f'<td>{k(r[2])}</td><td>{100 * r[2] / recv_total:.1f}%</td></tr>'
        for i, r in enumerate(RECEIVED_2024))
    used_rows = "".join(
        f'<tr><td>{name_html(r[1], r[0], key=f"used-line-{i}", what="Original account line:")}</td>'
        f'<td>{k(r[2])}</td><td>{100 * r[2] / PRINTED_USED_2024:.1f}%</td></tr>'
        for i, r in enumerate(USED_2024))
    chart = money_chart(fin)
    diagram = structure_diagram(F, S)
    used_bar = stack_bar([("aid for the SVO zone", USED_2024[0][2], "s1"), ("management", USED_2024[1][2], "s2"), ("upkeep", USED_2024[2][2], "s3"), ("assets", USED_2024[3][2], "s4")], "Shares of the 2024 use of funds by printed line")
    cbst_bar = stack_bar([("upkeep of the organisation", CBST_LINES[3][3], "s1"), ("other", CBST_LINES[5][3], "s2"), ("target events", CBST_LINES[2][3], "s4")], "Shares of TsBST's 2025 use of funds by printed line")

    def passage(q):
        _POPS["pass"] = n = _POPS.get("pass", 0) + 1
        shown = name_html(latinize_gloss(q["translation_en"]), q["text_ru"], key=f"pass-{n}", what="Russian original of")
        return f'<p class="pass"><span class="en">{shown}</span></p>'

    doc = f"""<!doctype html>
<!-- Generated by exhibits/build_story.py from data/registry on {today}. Do not edit by hand. -->
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Aid for the Zone</title>
{design_head((REPO / 'exhibits' / 'story.css').read_text())}</head>
<body>
<main class="story">
<nav class="rail" aria-label="Chapters"><ol><li><a href="#c0">The post</a></li><li><a href="#c1">The foundation</a></li><li><a href="#c2">The money in</a></li><li><a href="#c3">The money out</a></li><li><a href="#c5">The centre</a></li><li><a href="#c4">The handovers</a></li><li><a href="#c6">The marketplace</a></li><li><a href="#c8">Since</a></li><li><a href="#c7">The limits</a></li></ol></nav>
<header>
  <p class="rm-eyebrow">Draft · Story 1 · {ru_date(today)}</p>
  <h1 class="rm-h1">In 2024 a Moscow foundation booked {F['aid_bn']:.2f} billion rubles as <em>{orig_line(USED_2024[0][0], "story-h1-aid", USED_2024[0][1])}</em></h1>
  <p class="rm-dek">Its accounts do not name the donors behind nearly nine-tenths of its money. Its stated purposes include
  supporting companies that develop and make defence products. Its Telegram channel reports handing drones and
  electronic-warfare equipment to army units, with the ruling party, {pop('United Russia', 'Единая Россия')}, and a drone-industry
  non-profit, {pop('TsBST', 'ЦБСТ')} (the Centre for Unmanned Systems and Technologies), named as co-donors. “SVO”, the Kremlin's term for its invasion of Ukraine, appears here only inside quotations.</p>
</header>

{diagram}

<section class="figures" aria-label="Three figures">
  <div class="figure"><span class="n">{F['aid_bn']:.2f}<small>bn rubles</small></span>
    <p>booked in 2024 as aid for the zone: {F['aid_share']:.1f}% of everything the foundation spent that year.{r_notes}</p>
    <p>{orig_line(USED_2024[0][0], "story-figure-aid", USED_2024[0][1], what="Original account line:")}</p><span class="rm-grade doc">Documented</span></div>
  <div class="figure"><span class="n">{F['donor_share']:.0f}<small>%</small></span>
    <p>of the {F['got_bn']:.2f} billion rubles it received in 2024 came from legal entities and individuals the accounts do not name.</p>
    <span class="rm-grade doc">Documented</span></div>
  <div class="figure"><span class="n">{F['events']}</span>
    <p>handovers naming «Bulat» or «Kapyushon» that the foundation reports in its own posts, {month_year(F['first'])} to {month_year(F['last'])}. Not a full count.</p>
    <span class="rm-grade rep">Reported</span></div>
</section>

<section class="chapter" aria-labelledby="c0">
  <p class="rm-eyebrow">1 of 9 · The post</p>
  <h2 class="rm-h2" id="c0">Three days, 80 million rubles</h2>
  <div class="lead-in">
    <div class="text">
      <p>On 10 April 2025 the foundation's Telegram channel announced that it, the party United Russia and TsBST had
      delivered another batch of equipment to servicemen of the 132nd Gorlovka Brigade on the Donetsk direction.{r_posts}
      The post lists FPV drones, Mavic quadcopters, motorcycles, quad bikes, remotely operated evacuation platforms,
      «Perekhvat» electronic-intelligence equipment and «Bulat». It puts the batch at 18.2 million
      rubles and the whole trip at about 80 million.</p>
    </div>
    <figure class="rm-fig"><div class="frame"><img src="{pic(REPO / m['file'])}" alt="{esc(m.get('shows_en') or m['shows'])}"></div>
      <figcaption><span class="rm-prov">Published by the foundation</span>
      <span>A still posted with the announcement: {caption_html(m['shows'], 'story-lead-still', m.get('shows_en'))}</span>
      <span class="when">{ru_date(m['published'])}</span></figcaption></figure>
  </div>
  <article class="post" aria-label="Excerpts from the post">
    <header><span>Telegram · @nashapravdafond</span><span>{ru_date(q_head['date'])}</span><span>The foundation's own post</span></header>
    {passage(q_head)}{passage(q_list)}{passage(q_cost)}{passage(q_total)}
  </article>
  <p>The post's word for the equipment is {name_html("aid", "помощь", key="story-word-aid", what="Russian word for aid:")}. It is also the word on the largest line in the foundation's accounts for 2024.</p>
</section>

<section class="chapter" aria-labelledby="c1">
  <p class="rm-eyebrow">2 of 9 · The foundation</p>
  <h2 class="rm-h2" id="c1">Its stated purposes include supporting defence-product makers</h2>
  <p><b>{pop('Nasha Pravda', 'Фонд «Наша Правда»')}</b> foundation (<i>Our Truth</i>) was registered in Moscow in {registered}. Its general director since
  registration is <b>{name_html(person_names(d)['first'], person_names(d)['fio'], key='brovchenko')}</b>.{r_reg} Its website describes it as a joint project of two older
  foundations, DAR and Gradislava, for servicemen and citizens in the «SVO» territory.{r_site}</p>
  <div class="excerpt"><p class="where">Foundation's website, page {name_html("About the foundation", "О фонде", key="site-about", what="Original page title:")}</p>
    {quote_html(q_site['text_ru'], q_site['translation_en'], key="q-site")}</div>
  <p>The notes to the foundation's 2024 annual accounts, filed with the tax service, list what it is for.{r_notes2}
  The list begins with strengthening Russia's defence capability and takes in support for state bodies and the armed
  forces, and for «patriotic, volunteer and other public movements». One entry reads:</p>
  <div class="excerpt"><p class="where">Notes to the 2024 accounts, section 1.3, page 5</p>
    {quote_html(q_aim['text_ru'], q_aim['translation_en'], key="q-aim")}</div>
  <p>The figures come next: where the money came from, and where the accounts say it went.</p>
</section>

<section class="chapter" aria-labelledby="c2">
  <p class="rm-eyebrow">3 of 9 · The money in</p>
  <h2 class="rm-h2" id="c2">Nearly nine-tenths of the 2024 money came from donors the notes do not name</h2>
  <p>In 2024 the foundation received {F['got_bn']:.2f} billion rubles in targeted funds. The notes to its accounts print four lines to say from whom.{r_notes2}</p>
  <div class="split" role="img" aria-label="Shares of the 2024 receipts by printed line">{split_bar}</div>
  <table class="lines"><thead><tr><th>Account line</th><th>Thousand rubles</th><th>Share</th></tr></thead><tbody>{recv_rows}
    <tr class="tot"><td>Received in 2024</td><td>{k(recv_total)}</td><td>100%</td></tr></tbody></table>
  <p>Two donors are named: DAR, which gave 5 million rubles, and Gradislava, which gave 54 million. The first line,
  1.10 billion rubles, is credited to {name_html("legal entities and individuals", "юридических и физических лиц", key="story-anonymous-donors", what="Original account wording:")}. The notes print no names and no amount per donor. The third line repeats the founders' 59 million in
  amount. The four lines add to the printed total only if both are counted, and the notes do not say whether it is one
  payment listed twice or two.</p>
  <p>The same notes say, in a sentence about something else, that <i>{orig_line(q_aid['text_ru'], "story-q-aid", q_aid['translation_en'])}</i>, in 2024. They do not say what they mean by the term.{S.ref("s0389")}</p>
  <p>For 2025 the notes give the total, {F['got25_bn']:.2f} billion rubles, and no breakdown.{r_notes25}</p>
  {chart}
  <p class="chart-note">Targeted funds received and used, million rubles, from the filings. The balance carried forward fell from 434.4 million at the start of 2024 to 304.7 million at its end, and stood at 307.6 million at the end of 2025.</p>
</section>

<section class="chapter" aria-labelledby="c3">
  <p class="rm-eyebrow">4 of 9 · The money out</p>
  <h2 class="rm-h2" id="c3">{F['aid_share']:.1f}% of what it spent in 2024 is booked as aid for the zone</h2>
  {used_bar}
  <table class="lines"><thead><tr><th>Account line</th><th>Thousand rubles</th><th>Share</th></tr></thead><tbody>{used_rows}
    <tr class="tot"><td>Used in 2024</td><td>{k(PRINTED_USED_2024)}</td><td>100%</td></tr></tbody></table>
  <p>The four lines add to {k(used_sum)}. The filing's own total is {PRINTED_USED_2024 - used_sum} thousand rubles higher, and the notes do not say why.</p>
  <p>The first line says nothing of what was bought. For 2025 the notes give one line of use: {name_html("targeted donations within statutory activity", "Целевые пожертвования в рамках уставной деятельности", key="story-2025-use", what="Original account wording:")}, {AID_2025 / 1000:.1f} million rubles. That is {100 * AID_2025 / used25:.1f}% of the {used25 / 1000:.1f} million used. The other {(used25 - AID_2025) / 1000:.1f} million is not broken down.</p>
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
  <p class="rm-eyebrow">5 of 9 · The centre</p>
  <h2 class="rm-h2" id="c5">TsBST's accounts book all of its money as «other receipts»</h2>
  <p>TsBST, the autonomous non-profit (ANO) {pop('Centre for Unmanned Systems and Technologies', 'Центр беспилотных систем и технологий')}, was registered in Moscow on 27 February 2024. The register names two founders: the foundation from the
  start, and Bank PSB from 1 April 2025.{S.ref("s0228")} Its registered main activity is market research.
  The register lists publishing, software development, research and conference organising beside it, and nothing coded to defence.</p>
  <article class="post" aria-label="Excerpts from the TsBST website">
    <header><span>cbst.ru</span><span>{ru_date(q_site2['date'])}</span><span>TsBST's own website{S.ref("s8867")}</span></header>
    {passage(q_site1)}{passage(q_site2)}
  </article>
  <p>The register names two founders. TsBST's own text names three.</p>
  {cbst_bar}
  <p class="chart-note">How TsBST's 2025 spending was booked, share of the 275.6 million rubles used.</p>
  <table class="lines"><thead><tr><th>TsBST account line</th><th>2024</th><th>2025</th></tr></thead><tbody>{cbst_rows}</tbody></table>
  <p class="chart-note">Thousand rubles. Report on the use of targeted funds, FY2024{S.ref("s0382")} and FY2025.{S.ref("s0385")}</p>
  <p>In 2024 the line for target events is empty. In 2025 it holds {centre_ev25:.1f} million rubles, {ev_share:.1f}% of the
  {centre_used25:.1f} million used; upkeep of the organisation takes {centre_up25:.1f} million, {up_share:.1f}%.</p>
  <p>The accounts print no source for any of the money. In 2024 the line for contributions and other targeted receipts is
  empty and all 269.8 million sits under {name_html("other receipts", "Прочие поступления", key="story-cbst-other-1", what="Original account line:")}; the 2025 form has only that line. The 2025 notes say that,
  because TsBST counts as a small business, it does not apply the accounting rule on related-party disclosure.</p>
  <p>The foundation's notes for 2024 describe TsBST in their own words and list five agreements beneath them:</p>
  <article class="post" aria-label="Excerpts from the foundation's notes">
    <header><span>Notes to the foundation's 2024 accounts, section 16, page 33</span><span>The foundation's own filing{S.ref("s0389")}</span></header>
    {passage(q_sub)}{passage(q_contrib)}
  </article>
  <table class="lines plain3"><thead><tr><th>Date</th><th>Agreement line</th><th>Rubles</th></tr></thead><tbody>{contrib_rows}
    <tr class="tot"><td colspan="2">Together</td><td>{k(contrib_total)}</td></tr></tbody></table>
  <p>The notes print no recipient beside the amounts. {name_html("Subsidiary", "дочернее предприятие", key="story-subsidiary", what="Russian term used by the foundation:")} is the foundation's word: the register records two
  founders and no ownership share. TsBST's own 2024 accounts book every receipt as {name_html("other receipts", "Прочие поступления", key="story-cbst-other-2", what="Original account line:")}, so the two filings
  cannot be matched to each other.</p>
  <p>On 15 December 2025 {sid}, secretary of TsBST's supervisory board and head of the central executive
  committee of United Russia,{S.ref("s8699")} summed up the centre's year on his own channel:</p>
  <article class="post" aria-label="Excerpt from the post of 15 December 2025">
    <header><span>Telegram · @asidyakin</span><span>{ru_date(q_sid['date'])}</span><span>His own channel{S.ref("s8847")}</span></header>
    {passage(q_sid)}
  </article>
  <p>The post gives no source for the 2.5 billion dollars.</p>
</section>

<section class="chapter" aria-labelledby="c4">
  <p class="rm-eyebrow">6 of 9 · The handovers</p>
  <h2 class="rm-h2" id="c4">Between July 2024 and May 2026 the foundation reported at least 21 handovers that name «Bulat» or «Kapyushon»</h2>
  <p>Two products recur in its posts. It calls «Bulat» a {name_html("drone detector", "детектор дронов", key="story-drone-detector", what="Original wording from the post:")}, and «Kapyushon» an
  {name_html("electronic-warfare station", "станция РЭБ", key="story-ew-station", what="Original wording from the post:")}.{S.ref("s8994")} Each mark below is one post that names one or both.</p>
  {timeline}
  <p class="chart-note">Circle: a post naming «Bulat». Square: a post naming «Kapyushon». Ringed: the recipient is a civilian service. Source of every mark: the foundation's own channel.</p>
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
  <p>These 21 are only the handovers that name those two products. The foundation reports others. One of them, on
  10 August 2026, is a different kind of list:{r_641}</p>
  <article class="post" aria-label="Excerpts from the post of 10 August 2026">
    <header><span>Telegram · @nashapravdafond</span><span>{ru_date(q_gru['date'])}</span><span>The foundation's own post</span></header>
    {passage(q_gru)}{passage(q_3d)}{passage(q_vic)}
  </article>
  <p>A handover to a unit does not show that the equipment was used in combat. Some recipients are rear units, and two
  of the 21 are civilian services.</p>
</section>

<section class="chapter" aria-labelledby="c6">
  <p class="rm-eyebrow">7 of 9 · The marketplace</p>
  <h2 class="rm-h2" id="c6">TsBST participates in the company that runs ROY.MARKET, and the register now withholds who owns it</h2>
  <p>On 25 December 2024 TsBST's own channel announced that United Russia, TsBST and Bank PSB had launched a «military
  marketplace». The post gives the party official's words and the chairman of TsBST's board:{S.ref(sid338)}</p>
  <article class="post" aria-label="Excerpts from the post of 25 December 2024">
    <header><span>Telegram · @ANO_CBST</span><span>{ru_date(q_m2['date'])}</span><span>TsBST's own channel</span></header>
    {passage(q_m1)}{passage(q_m2)}{passage(q_m3)}
  </article>
  <p>The post of 15 December 2025 quoted earlier uses the same phrase.{S.ref("s8847")}</p>
  <article class="post" aria-label="Excerpt from the post of 15 December 2025">
    <header><span>Telegram · @asidyakin</span><span>{ru_date(q_618['date'])}</span><span>His own channel</span></header>
    {passage(q_618)}
  </article>
  <p>The company that operates the platform is {pop('OOO «MPTM»', 'OOO «MPTM»')}. TsBST's report to the Ministry of Justice for 2025 lists it among
  the legal entities in which TsBST participates, from 22 January 2025, the day the company was registered.{S.ref("s0207")}
  The cell for the form of participation reads:</p>
  <article class="post" aria-label="Excerpt from the report to the Ministry of Justice">
    <header><span>Report to the Ministry of Justice, 2025, section 2.2</span><span>Row for OOO «MPTM»</span></header>
    {passage(q_row)}
  </article>
  <p>The report gives no share. The platform's own supplier offer names MPTM as its operator, with its tax number and the
  bank that holds its account, PSB.{S.ref("s8817")} By 1 October 2026 the public text no longer did.{S.ref("s8822")}</p>
  <div class="pair">
    <article class="post" aria-label="The supplier offer on 22 August 2026">
      <header><span>Supplier offer</span><span>{ru_date(q_op['date'])}</span><span>Internet Archive</span></header>{passage(q_op)}</article>
    <article class="post" aria-label="The supplier offer on 1 October 2026">
      <header><span>Supplier offer</span><span>{ru_date(q_mask['date'])}</span><span>The live site</span></header>{passage(q_mask)}</article>
  </div>
  <p>On the live site the operator's name, tax number, address and bank details are shown only after login. Why and when
  they were hidden is not documented. The company register restricted access to the section that names MPTM's
  participants on 15 July 2026, before either version.{S.ref("s0230")}</p>
  <article class="post" aria-label="Excerpt from the company register extract">
    <header><span>Company register extract, 14 August 2026</span><span>Section {name_html("Information about participants / founders of the legal entity", "Сведения об участниках / учредителях юридического лица", key="story-register-section", what="Original register heading:")}</span></header>
    {passage(q_restr)}
  </article>
  <p>The one seller whose own post states a sale on the platform is KB «SPEKTR», a maker of drone propellers. On 6 July 2026
  its channel wrote:{S.ref("s8737")}</p>
  <article class="post" aria-label="Excerpt from the KB SPEKTR post of 6 July 2026">
    <header><span>Telegram · @kb_spektr</span><span>{ru_date(q_kb['date'])}</span><span>The brand's own channel</span></header>
    {passage(q_kb)}
  </article>
  <p>No document on file puts «Bulat», the product that runs through the handovers, on the platform. A representative of its
  maker, 3mx, wrote in the company's customer chat on 2 September 2026:{S.ref("s8860")}</p>
  <article class="post" aria-label="Excerpt from the 3mx chat message of 2 September 2026">
    <header><span>3mx customer chat</span><span>{ru_date(q_3mx['date'])}</span><span>A message from the maker's representative</span></header>
    {passage(q_3mx)}
  </article>
  <p>In August 2026 Sidyakin and TsBST described the platform's next stage.{S.ref("s8851")}<sup class="fn">,</sup>{S.ref("s8852")}</p>
  <article class="post" aria-label="Excerpts from August 2026 posts">
    <header><span>Telegram · @asidyakin, 5 August 2026</span><span>Telegram · @ANO_CBST, 6 August 2026</span></header>
    {passage(q_pilot)}{passage(q_tech)}
  </article>
  <p>The first is a count given by the secretary of TsBST's own supervisory board and the second is a plan. TsBST's share in MPTM is not stated in
  any document on file.</p>
</section>

<section class="chapter" aria-labelledby="c8">
  <p class="rm-eyebrow">8 of 9 · Since</p>
  <h2 class="rm-h2" id="c8">In September the foundation congratulated the party official who announced the marketplace on chairing a Duma committee</h2>
  <p>The foundation's channel has gone on reporting handovers. On 24 September 2026 it wrote:{S.ref("s9077")}</p>
  <article class="post" aria-label="Excerpt from the post of 24 September 2026">
    <header><span>Telegram · @nashapravdafond</span><span>{ru_date(q_91['date'])}</span><span>The foundation's own post</span></header>
    {passage(q_91)}
  </article>
  <p>On 3 October:{S.ref("s9204")}</p>
  <article class="post" aria-label="Excerpt from the post of 3 October 2026">
    <header><span>Telegram · @nashapravdafond</span><span>{ru_date(q_amb['date'])}</span><span>The foundation's own post</span></header>
    {passage(q_amb)}
  </article>
  <p>Neither post names a product or a maker. Both are the foundation's own reports, like the 21 before them.</p>
  <p>Between the two, on 30 September, the foundation congratulated Sidyakin on his appointment as chair of the
  State Duma's committee on digital development and artificial intelligence.{S.ref("s9050")} He is the secretary of
  TsBST's supervisory board and the party official quoted in TsBST's launch post for the «military marketplace». The
  foundation wrote:</p>
  <article class="post" aria-label="Excerpt from the post of 30 September 2026">
    <header><span>Telegram · @nashapravdafond</span><span>{ru_date(q_cong['date'])}</span><span>The foundation's own post</span></header>
    {passage(q_cong)}
  </article>
  <p>Six days earlier TsBST's own channel had reported that {pop('Dmitriy Medvedev', 'Дмитрий Медведев')} proposed him for the post, and quoted the
  chairman of its board, {pop('Andrey Bezrukov', 'Андрей Анатольевич Безруков')}: the centre {pop('“will give him all the expert support he needs”', '«окажет ему всю необходимую экспертную поддержку»')}.{S.ref("s9049")}</p>
  <p>The foundation's notes for 2025, the latest accounts on file, name no donor.{r_notes25}</p>
</section>

<section class="chapter" aria-labelledby="c7">
  <p class="rm-eyebrow">9 of 9 · The limits</p>
  <h2 class="rm-h2" id="c7">What this does not show</h2>
  <ul class="limits">
    <li>Every handover in this story is the foundation's own report. For none of them is there a second source on file.</li>
    <li>A handover to a unit does not show that the equipment was used in combat. Some recipients are rear units, and two of the 21 are civilian services.</li>
    <li>The accounts do not name the donors behind {F['donor_share']:.0f}% of the foundation's 2024 money, and they do not define the state aid the foundation says it did not receive.</li>
    <li>The five contributions of 71.1 million rubles in the foundation's notes cannot be matched to TsBST's receipts. The register records TsBST's founders and no owner.</li>
    <li>TsBST's share in MPTM is not stated in any document on file, and the register withholds who owns the company.</li>
    <li>No document on file puts «Bulat» on ROY.MARKET. Which sellers use the platform beyond the one named here is not established.</li>
    <li>Sidyakin's figure of 2.5 billion dollars was not tested. His post gives no source for it.</li>
    <li>No document on file gives the date of the Duma vote on Sidyakin's appointment. The foundation's post shows only that it had been made by 30 September 2026.</li>
    <li>Photographs show what is visible in them. Nobody is identified from a face.</li>
    <li>This page makes no statement about sanctions listings of any company named here.</li>
  </ul>
</section>

<section class="rm-sources"><h2 class="rm-h2">Sources</h2><ol>@@NOTES@@</ol></section>
</main>
{RAIL_JS}
<script>{NAME_JS}</script>
</body></html>
"""
    doc = S.finalize(doc)
    out.write_text(doc, encoding="utf-8")
    print(f"wrote {out.relative_to(REPO) if out.is_relative_to(REPO) else out}: {len(S.notes)} sources, {len(doc)//1024} KB")


def artifact_fragment(doc: str) -> str:
    """The Artifact tool wraps a page in its own skeleton, so it takes the title, style and body content only."""
    title = re.search(r"<title>.*?</title>", doc, re.S).group(0)
    head = re.search(r"</title>(.*)</head>", doc, re.S).group(1)
    body = re.search(r"<body>(.*)</body>", doc, re.S).group(1)
    return f"{title}\n{head}\n{body}\n"


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", help="default exhibits/story_01.html")
    ap.add_argument("--artifact", action="store_true", help="also write the Artifact fragment")
    ap.add_argument("--fixture", action="store_true",
                    help="check against tests/fixtures/story_sources.json instead of the Mac's database (CI)")
    ap.add_argument("--export-fixture", action="store_true",
                    help="on the Mac: write the texts this build checked to tests/fixtures/story_sources.json")
    a = ap.parse_args()
    LOCAL.__init__("fixture" if a.fixture else "local")
    out = Path(a.out).resolve() if a.out else REPO / "exhibits" / "story_01.html"
    render(out)
    if a.fixture:
        print(f"fixture mode: {LOCAL.skipped} check(s) skipped for want of a text, {LOCAL.blank} picture(s) left blank"
              + ("" if FIXTURE.exists() else f"; {FIXTURE.relative_to(REPO)} not found, run --export-fixture on the Mac"))
    if a.export_fixture:
        LOCAL.export()
        print(f"wrote {FIXTURE.relative_to(REPO)}: {len(LOCAL.used_posts)} posts, {len(LOCAL.used_web)} page(s)")
    if a.artifact:
        frag = out.with_name("story_01_artifact.html")
        frag.write_text(artifact_fragment(out.read_text(encoding="utf-8")), encoding="utf-8")
        print(f"wrote {frag.relative_to(REPO)}")
