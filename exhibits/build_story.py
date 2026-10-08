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

    # -- citations: the generated title and public link, numbered in page order
    def ref(self, sid: str) -> str:
        if sid not in self.notes:
            self.notes.append(sid)
        n = self.notes.index(sid) + 1
        self.uses[sid] = self.uses.get(sid, 0) + 1
        ident = f' id="r{n}"' if self.uses[sid] == 1 else ""
        return f'<sup class="fn"><a href="#n{n}"{ident}>{n}</a></sup>'

    def notes_list(self) -> str:
        out = []
        for i, sid in enumerate(self.notes, 1):
            s = self.src[sid]
            title, url = s.get("title") or "Archived document", s.get("public_url")
            link = f' <a href="{esc(url)}">{esc(url)}</a>' if url else " (no public link on file)"
            out.append(f'<li id="n{i}">{esc(title)}.{link} <a href="#r{i}" aria-label="Back to text">↩</a></li>')
        return "".join(out)

    def quote(self, ru_start: str) -> dict:
        q = next((q for k, q in self.quotes.items() if q["text_ru"].startswith(ru_start)), None)
        assert q, f"quote not in quotes.json: {ru_start}"
        return q

    def check_posts(self, quotes: list[dict], channel_id=1905141464, msg=422):
        """Each passage must stand in the stored post text, ellipses and the closing full stop aside."""
        text = sqlite3.connect(REPO / "data" / "roymarket.db").execute(
            "select text from tg_posts where channel_id=? and msg_id=?", (channel_id, msg)).fetchone()[0]
        for q in quotes:
            assert q["text_ru"].rstrip(".;") in text, f"not in post {msg}: {q['text_ru'][:50]}"

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
    <p>handovers to units that the foundation reports in its own posts, {month_year(F['first'])} to {month_year(F['last'])}.</p>
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
    <header><span>Telegram · @nashapravdafond</span><span>{ru_date(q_hosp['date'])}</span><span>The foundation's own post</span></header>
    {passage(q_hosp)}{passage(q_hosp2)}{S.ref("s8992")}
  </article>
  <article class="post" aria-label="Excerpts from the post of 15 January 2025">
    <header><span>Telegram · @nashapravdafond</span><span>{ru_date(q_kher['date'])}</span><span>The foundation's own post</span></header>
    {passage(q_kher)}{passage(q_kher2)}{S.ref("s8994")}
  </article>
  <p>Most of its reports name soldiers and units. Whether these two deliveries sit under the line for the zone, the notes do not say.</p>
</section>

<section class="chapter" aria-label="Chapters in draft">
  <aside class="rm-card coming"><header><span class="rm-kind">In draft</span></header>
    <p>The chapters that follow are outlined and not yet written:</p>
    <ol><li>The centre it co-founded</li><li>The handovers</li><li>The marketplace</li><li>What this does not show</li></ol></aside>
</section>

<section class="rm-sources"><h2 class="rm-h2">Sources</h2><ol>{S.notes_list()}</ol></section>
</main>
</body></html>
"""
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
