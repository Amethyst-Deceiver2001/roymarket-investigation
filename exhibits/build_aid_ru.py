#!/usr/bin/env python3
"""«Как фонды, связанные с Дмитрием Медведевым, снабжают российскую армию»: the Russian story page (private preview).

  python3 exhibits/build_aid_ru.py                       # writes exhibits/aid_ru.html
  python3 exhibits/build_aid_ru.py --out some/path.html

Written in Russian on purpose (<html lang="ru">; scripts/check_reader_page.py skips only its English-first rule on such a
page). Every figure is read from data/registry/ and asserted; every quotation comes from quotes.json or is a short phrase
checked against the stored text (Telegram posts in data/roymarket.db, the ФБК capture in data/sources/) when this machine
holds them, and counted as skipped when it does not. The page prints no source id, slug or file name. Copy outline:
exhibits/story_aid_ru_draft.md. Layout is exhibits/story.css plus the few rules below; tokens come from design/roymarket.css.
"""
from __future__ import annotations

import argparse
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
sys.path.insert(0, str(REPO / "exhibits"))
from display_helpers import design_head, ru_date  # noqa: E402
from build_story import (BUCKETS, CBST_LINES, CONTRIBUTIONS, STATED_VALUE, USED_2024, RECEIVED_2024,  # noqa: E402
                         PRINTED_USED_2024, handover_events, handover_timeline, stack_bar)

REG = REPO / "data" / "registry"
esc = html.escape
BLANK = "data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=="
NP, DAR, GRAD, LEVIT = ("fond-nasha-pravda", "fond-dar-fond-regionalnykh-nekommercheskikh-proektov",
                        "fond-gradislava-historic-cultural-heritage-preservation", "ooo-levit")
CH_NP, CH_ASID, CH_CBST = 1905141464, 2581147715, 2159491523   # Telegram channel ids of @nashapravdafond, @asidyakin, @ANO_CBST
FBK_TEXT = REPO / "data" / "sources" / "WEBCAPTURE_20261024_navalny-dimon-on-vam-ne-dimon-text.txt"

PAGE_CSS = """
.verdict { width: 100%; max-width: 820px; border-collapse: collapse; font-size: 16px; line-height: 1.5; }
.verdict td { padding: 12px 14px 12px 0; border-top: 1px solid var(--rule); vertical-align: top; }
.verdict td:first-child { width: 150px; white-space: nowrap; }
.story .lines td:not(:first-child), .story .lines th:not(:first-child) { text-align: right; font-variant-numeric: tabular-nums; }
.story .lines.board td:not(:first-child), .story .lines.board th:not(:first-child) { text-align: left; }
.story .lines td.hl { font-weight: 600; }
.note { max-width: var(--measure); font-size: var(--t-note); color: var(--ink-2); margin: 0; }
.qa { max-width: var(--measure); display: grid; gap: 6px; padding-left: 20px; margin: 0; font-size: 17px; line-height: 1.55; }
.draftnote { font: 600 11px/1.3 var(--font-mono); letter-spacing: .06em; text-transform: uppercase; color: var(--ink-3); }
"""

MONTHS = {"Jan": "янв", "Feb": "фев", "Mar": "мар", "Apr": "апр", "May": "май", "Jun": "июн", "Jul": "июл",
          "Aug": "авг", "Sep": "сен", "Oct": "окт", "Nov": "ноя", "Dec": "дек"}

# source key -> (label as printed, public link or None, registry source ids the page leans on: asserted to exist)
SOURCES = {
    "np_post_422": ("Telegram, @nashapravdafond, пост от 10.04.2025", "https://t.me/nashapravdafond/422", ["s8896"]),
    "np_accounts24": ("Годовая бухгалтерская отчётность фонда «Наша Правда» за 2024 год с пояснительной запиской (ФНС, открытый ресурс бухгалтерской отчётности)", None, ["s0389"]),
    "np_accounts25": ("Годовая бухгалтерская отчётность фонда «Наша Правда» за 2025 год (ФНС)", None, ["s0390"]),
    "np_egrul": ("Выписка из ЕГРЮЛ на фонд «Наша Правда» от 15.08.2026", None, ["s0221"]),
    "np_site": ("Сайт фонда «Наша Правда», раздел «О фонде», запись от 08.09.2026", "https://xn----7sbabalo0evak8f.xn--p1ai", ["s7370"]),
    "vedomosti": ("«Для поддержки армии и людей в зоне спецоперации создан фонд «Наша правда»», «Ведомости», 18.04.2023", "https://www.vedomosti.ru/politics/articles/2023/04/18/971308-sozdan-fond-nasha-pravda", ["s7521"]),
    "dar_egrul": ("Выписка из ЕГРЮЛ на фонд «ДАР» от 15.08.2026", None, ["s0214"]),
    "dar_accounts": ("Годовая бухгалтерская отчётность фонда «ДАР» за 2023–2025 годы (ФНС); пояснительная записка за 2023 год составлена 18.03.2024", None, ["s0298", "s0299", "s0300"]),
    "grad_egrul": ("Выписка из ЕГРЮЛ на фонд «Градислава» от 24.10.2026", None, ["L0011"]),
    "grad_accounts": ("Годовая бухгалтерская отчётность фонда «Градислава» за 2023–2025 годы (ФНС)", None, ["s0293", "s0294", "s0295"]),
    "levit_egrul": ("Выписка из ЕГРЮЛ на ООО «ЛЕВИТ» от 07.09.2026", None, ["s6697"]),
    "fbk": ("ФБК, «Он вам не Димон. Тайная империя Дмитрия Медведева», 2017 (страница сохранена 24.10.2026)", "https://dimon.navalny.com/", ["L0255"]),
    "us": ("Список SDN Управления по контролю за иностранными активами Минфина США (OFAC), выгрузка от 21.10.2026", None, ["L0389"]),
    "uk": ("Санкционный список Великобритании (FCDO) с обоснованиями, CSV от 16.10.2026", "https://sanctionslist.fcdo.gov.uk/docs/UK-Sanctions-List.csv", ["L0403"]),
    "ca": ("Консолидированный санкционный список Канады (SEMA), PDF от 25.10.2026", "https://www.international.gc.ca/world-monde/assets/pdfs/international_relations-relations_internationales/sanctions/sema-lmes.pdf", ["L0424"]),
    "au": ("Консолидированный санкционный список Австралии (DFAT), выгрузка от 25.10.2026", "https://www.dfat.gov.au/sites/default/files/Australian_Sanctions_Consolidated_List.xlsx", ["L0422"]),
    "nz": ("Реестр санкций Новой Зеландии против России (MFAT), выгрузка от 25.10.2026", "https://www.mfat.govt.nz/assets/Countries-and-Regions/Europe/Ukraine/Russia-Sanctions-Register.xlsx", ["L0423"]),
    "eu": ("Сводный список финансовых санкций ЕС, выгрузка от 25.10.2026", None, ["L0354"]),
    "np_post_656": ("Telegram, @nashapravdafond, пост от 10.08.2026", "https://t.me/nashapravdafond/656", ["s9229"]),
    "np_post_448": ("Telegram, @nashapravdafond, пост от 09.06.2025", "https://t.me/nashapravdafond/448", ["s8898"]),
    "np_post_311": ("Telegram, @nashapravdafond, пост от 08.08.2024", "https://t.me/nashapravdafond/311", ["s8992"]),
    "np_post_382": ("Telegram, @nashapravdafond, пост от 15.01.2025", "https://t.me/nashapravdafond/382", ["s8994"]),
    "np_channel": ("Telegram-канал фонда «Наша Правда»: посты о передачах, июль 2024 — май 2026", "https://t.me/nashapravdafond", ["s8896"]),
    "cbst_post_1484": ("Telegram, @ANO_CBST, пост от 07.11.2025", "https://t.me/ano_cbst/1484", []),
    "sid_post_609": ("Telegram, @asidyakin, пост от 10.12.2025", "https://t.me/asidyakin/609", []),
    "sid_post_1234": ("Telegram, @asidyakin, пост от 07.08.2026", "https://t.me/asidyakin/1234", []),
    "sid_post_618": ("Telegram, @asidyakin, пост от 15.12.2025", "https://t.me/asidyakin/618", ["s8847"]),
    "cbst_post_934": ("Telegram, @ANO_CBST, пост от 18.07.2025", "https://t.me/ano_cbst/934", ["s8699"]),
    "cbst_egrul": ("Выписка из ЕГРЮЛ на АНО «ЦБСТ» от 15.08.2026", None, ["s0228"]),
    "cbst_accounts": ("Отчёты ЦБСТ об использовании целевых средств за 2024 и 2025 годы (ФНС)", None, ["s0382", "s0385"]),
    "cbst_site": ("Сайт ЦБСТ, статья «ЦБСТ масштабирует площадку двойного назначения РОЙ.МАРКЕТ», копия от 01.10.2026", "https://cbst.ru/tpost/9j5esvv061-tsbst-masshtabiruet-ploschadku-dvoinogo", ["s8867"]),
    "vot_tak": ("«Все дороги ведут в Кремль: кто стоит за Wildberries и Ozon», «Вот Так», 24.09.2026", "https://vot-tak.tv/95546179/wildberries-ozon-kreml", []),
}


def load(name):
    d = json.loads((REG / name).read_text(encoding="utf-8"))
    return d if isinstance(d, list) else next(iter(d.values()))


def rub_bn(n, places=2):
    return f"{n / 1e9:.{places}f}".replace(".", ",")


def rub_m(n, places=1):
    return f"{n / 1e6:.{places}f}".replace(".", ",")


def pct(x):
    return f"{x:.1f}".replace(".", ",")


class Page:
    def __init__(self):
        self.ents = {e["slug"]: e for e in load("entities.json")}
        self.people = {p["slug"]: p for p in load("people.json")}
        self.src = {s["id"]: s for s in load("sources.json")}
        self.quotes = {q["id"]: q for q in load("quotes.json")}
        self.skipped = 0
        self.checked = 0
        try:
            self.db = sqlite3.connect(REPO / "data" / "roymarket.db")
            self.db.execute("select 1 from tg_posts limit 1")
        except Exception:
            self.db = None
        for key, (_, _, sids) in SOURCES.items():
            for sid in sids:
                assert sid in self.src, f"source {sid} for {key} is not in the registry"

    # -- citations numbered by first appearance
    def ref(self, *keys):
        for k in keys:
            assert k in SOURCES, k
        return "@@REF:" + ",".join(keys) + "@@"

    def finalize(self, doc: str) -> str:
        order: list[str] = []
        for m in re.finditer(r"@@REF:([a-z0-9_,]+)@@", doc):
            for k in m.group(1).split(","):
                if k not in order:
                    order.append(k)
        seen: set[str] = set()

        def sub(m):
            out = []
            for k in m.group(1).split(","):
                n = order.index(k) + 1
                ident = "" if k in seen else f' id="r{n}"'
                seen.add(k)
                out.append(f'<a href="#n{n}"{ident}>{n}</a>')
            return '<sup class="fn">' + ",".join(out) + "</sup>"

        doc = re.sub(r"@@REF:([a-z0-9_,]+)@@", sub, doc)
        items = []
        for i, k in enumerate(order, 1):
            label, url, _ = SOURCES[k]
            shown = re.sub(r"^https?://", "", url or "") if (url or "").startswith("https://t.me/") else re.sub(r"^https?://([^/]+).*$", r"\1", url or "")
            link = f' <a href="{esc(url)}">{esc(shown)}</a>' if url else ""
            items.append(f'<li id="n{i}">{esc(label)}.{link} <a href="#r{i}" aria-label="Назад к тексту">↩</a></li>')
        return doc.replace("@@NOTES@@", "".join(items))

    # -- quotations
    def quote(self, ru_start: str) -> dict:
        hits = [q for q in self.quotes.values() if q["text_ru"].startswith(ru_start)]
        assert hits, f"quote not in quotes.json: {ru_start}"
        return next((q for q in hits if q.get("source_id")), hits[0])

    def post_text(self, channel, msg):
        if self.db is None:
            return None
        row = self.db.execute("select text from tg_posts where channel_id=? and msg_id=?", (channel, msg)).fetchone()
        return row[0] if row else None

    def check_post(self, phrases, channel, msg):
        text = self.post_text(channel, msg)
        if text is None:
            self.skipped += len(phrases)
            return
        norm = lambda x: " ".join(x.replace(" ", " ").split())
        for ph in phrases:
            assert norm(ph.rstrip(".;:")) in norm(text), f"not in post {msg}: {ph[:60]}"
            self.checked += 1

    def check_fbk(self, phrases):
        if not FBK_TEXT.exists():
            self.skipped += len(phrases)
            return
        t = " ".join(FBK_TEXT.read_text(encoding="utf-8").split())
        for ph in phrases:
            assert ph in t, f"not in the ФБК page: {ph[:60]}"
            self.checked += 1

    @staticmethod
    def bq(text, cite, refs=""):
        return (f'<blockquote class="rm-quote"><span class="q" lang="ru">«{esc(text)}»</span>'
                f'<cite>{esc(cite)}{refs}</cite></blockquote>')


def image_uri(path: Path) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(path.read_bytes()).decode() if path.exists() else BLANK


def render(out: Path):
    P = Page()
    today = dt.date.today().isoformat()
    np_, dar, grad, levit = (P.ents[s] for s in (NP, DAR, GRAD, LEVIT))
    fin = lambda e: {f["year"]: f for f in e["financials"]}
    fn, fd, fg = fin(np_), fin(dar), fin(grad)

    # ---- figures, all asserted against the registry
    recv24, used24 = fn["2024"]["funds_received"] / 1000, fn["2024"]["funds_used"] / 1000
    assert sum(r[2] for r in RECEIVED_2024) == recv24 and PRINTED_USED_2024 == used24
    aid, donors, founders_money = USED_2024[0][2], RECEIVED_2024[0][2], RECEIVED_2024[1][2]
    aid_share, donor_share, founders_share = 100 * aid / used24, 100 * donors / recv24, 100 * founders_money / recv24
    assert founders_money == 59_000 and 95 < aid_share < 96 and 89 < donor_share < 90
    g24 = fg["2024"]   # Градислава used far more than it received in 2024: it must reconcile with the balances on both sides
    assert g24["funds_balance_start"] + g24["funds_received"] - g24["funds_used"] == g24["funds_balance_end"]
    assert fg["2025"]["funds_balance_start"] == g24["funds_balance_end"], "Градислава: 2024 closing differs from 2025 opening"
    assert fg["2023"]["funds_balance_end"] == g24["funds_balance_start"]
    assert fd["2024"]["funds_received"] > 8e9 and fg["2023"]["funds_received"] > 11e9

    events = handover_events()
    assert len(events) == 21 and sum(len(ids) for _, ids in BUCKETS) == 21
    b_named, b_group, b_region, b_civil = (len(ids) for _, ids in BUCKETS)
    vmin, vmax = min(v for v, _ in STATED_VALUE.values()), max(v for v, _ in STATED_VALUE.values())
    vsum = sum(v for v, _ in STATED_VALUE.values())
    assert len(STATED_VALUE) == 12
    contrib_total = sum(c[2] for c in CONTRIBUTIONS)
    assert contrib_total == 71_135_024 and CBST_LINES[1][2] == 269_835

    # ---- people and documents
    ppl = P.people
    for slug, role_src in (("viktor-ilich-davydov", "s0389"), ("eliseev-ilya-vladimirovich", "s0389")):
        assert any(r.get("entity_slug") == NP for r in ppl[slug]["roles"]), slug
    davydov_since = next(h["as_of"] for h in dar["director_history"] if "Давыдов" in h["value"])
    karab_since = next(h["as_of"] for h in grad["director_history"] if "Карабинский" in h["value"])
    assert davydov_since == "2008-05-27" and karab_since == "2013-04-12"
    assert "78.2902%" in levit["founders_history"][0]["value"] and "21.7098%" in levit["founders_history"][0]["value"]
    np_oq = " ".join(str(q.get("text")) for q in np_.get("open_questions") or [])
    for s in ("Давыдов (Фонд «ДАР»)", "Карабинский (Фонд «Градислава»)", "Тихонов (Фонд «ДАР»)", "Манецкий (Фонд «Градислава»)", "Дукал (Фонд «ДАР»)"):
        assert s in np_oq, f"board line changed: {s}"
    el = ppl["eliseev-ilya-vladimirovich"]["sanctions"]
    regimes = " ".join(str(s.get("regime")) for s in el)
    for need in ("OFAC", "UK Russia", "Canada", "New Zealand", "Australia"):
        assert need in regimes, f"Елисеев: no {need} entry in the registry"
    assert any(s.get("date") == "2022-09-26" for s in el) and any(s.get("date") == "2022-09-29" for s in el)
    med = ppl["dmitriy-medvedev"]["sanctions"]
    assert any("EU" in str(s.get("regime")) for s in med) and any(s.get("date") == "2022-03-15" for s in med)
    sid_roles = " ".join(r.get("title") or "" for r in ppl["aleksandr-sidyakin"]["roles"])
    assert "Secretary of the Supervisory Board" in sid_roles

    # ---- quotations
    q_head = P.quote("Фонд «Наша Правда», «Единая Россия» и ЦБСТ доставили очередную")
    q_cost = P.quote("Оборудование стоимостью 18,2")
    q_total = P.quote("Всего за три дня")
    q_site = P.quote('Фонд "Наша Правда" - это совместный')
    q_gru = P.quote("Помощь от фонда «Наша Правда», Единой России и ЦБСТ передали")
    q_3d = P.quote("Ударные дроны и гексакоптеры")
    q_boy = P.quote("Рации для связи, проверенное")
    q_sub = P.quote("дочернее предприятие Фонда")
    q_sid = P.quote("ЦБСТ вместе с Единой Россией и фондом")
    q_618 = P.quote("Вместе с партией и ПСБ запустили")
    q60 = P.quote("По поручению Председателя Партии")
    q59 = P.quote("Партия и лично Дмитрий Анатольевич Медведев")
    q61 = P.quote("Техника была закуплена за счёт средств фонда")
    P.check_post([q_head["text_ru"], q_cost["text_ru"], q_total["text_ru"]], CH_NP, 422)
    P.check_post([q_gru["text_ru"], q_3d["text_ru"]], CH_NP, 656)
    P.check_post([q_boy["text_ru"]], CH_NP, 448)
    P.check_post([q_sid["text_ru"], q_618["text_ru"]], CH_ASID, 618)
    P.check_post([q60["text_ru"]], CH_ASID, 609)
    P.check_post([q59["text_ru"]], CH_ASID, 1234)
    barskurs = ("Во время недавнего визита в Курск заместитель председателя Совета безопасности РФ и председатель партии "
                "«Единая Россия» Дмитрий Медведев передал гуманитарную помощь бойцам добровольческой бригады «БАРС-Курск».")
    P.check_post([barskurs, q61["text_ru"]], CH_CBST, 1484)
    P.check_fbk(["Сам Медведев (через пресс-секретаря) отрицает свою причастность к плесской даче",
                 "сам Михельсон говорит, что к фонду «Дар» отношения не имеет",
                 "Мы убеждены, что обе эти яхты", "Мы считаем это очередным доказательством",
                 "Он самое доверенное лицо премьер-министра"])

    r = P.ref
    first, last = events[0]["date"], events[-1]["date"]
    assert first.startswith("2024-07") and last.startswith("2026-05")
    timeline = handover_timeline(events)
    timeline = timeline.replace("«Bulat»", "«Булат»").replace("«Kapyushon»", "«Капюшон»")
    timeline = timeline.replace("Twenty-one handovers by date, by product", "Двадцать одна передача по датам и изделиям")
    for en, ru in MONTHS.items():
        timeline = timeline.replace(">" + en + " ", ">" + ru + " ")
    split_bar = stack_bar([("безымянные доноры", RECEIVED_2024[0][2], "s1"), ("«ДАР» и «Градислава»", RECEIVED_2024[1][2], "s2"),
                           ("то же, второй раз", RECEIVED_2024[2][2], "s3"), ("доход от деятельности", RECEIVED_2024[3][2], "s4")],
                          "Доли поступлений 2024 года по строкам отчётности")
    split_bar = re.sub(r"(\d)\.(\d)%", r"\1,\2%", split_bar)
    still = image_uri(REPO / "exhibits" / "images" / "media" / "m0075.jpg")

    def money_row(label, e_fin, years, bold=()):
        cells = "".join(f'<td class="{"hl" if y in bold else ""}">{rub_bn(e_fin[y]["funds_received"]) + " млрд ₽" if y in e_fin else "—"}</td>' for y in years)
        return f"<tr><td>{label}</td>{cells}</tr>"

    years = ("2023", "2024", "2025")
    money_table = ('<table class="lines"><thead><tr><th>Целевые средства, поступившие за год</th>' + "".join(f"<th>{y}</th>" for y in years) + "</tr></thead><tbody>"
                   + money_row("«ДАР»", fd, years, bold=("2024",)) + money_row("«Градислава»", fg, years, bold=("2023",))
                   + money_row("«Наша Правда»", fn, years) + "</tbody></table>")

    def chip(kind, text):
        return f'<span class="rm-grade {kind}">{text}</span>'

    doc = f"""<!doctype html>
<!-- Generated by exhibits/build_aid_ru.py from data/registry on {today}. Do not edit by hand. -->
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Как фонды, связанные с Дмитрием Медведевым, снабжают армию</title>
{design_head((REPO / 'exhibits' / 'story.css').read_text() + PAGE_CSS)}</head>
<body>
<main class="story">
<header>
  <p class="rm-eyebrow">Черновик · Расследование · {ru_date(today)}</p>
  <h1 class="rm-h1">Как фонды, связанные с Дмитрием Медведевым, снабжают российскую армию</h1>
  <p class="rm-dek">Фонд «Наша Правда» передаёт войскам дроны и средства радиоэлектронной борьбы вместе с «Единой Россией», которую
  возглавляет Медведев. Участники этой схемы сами пишут, что фонд создан по его поручению. Сам фонд называет себя проектом двух других
  фондов, «ДАР» и «Градислава»; их ФБК в 2017 году назвал частью скрытой сети Медведева. Что из этого подтверждают документы,
  а что остаётся версией, показано ниже.</p>
  <p class="note">Алексей Ковалёв, независимый журналист · данные на {ru_date(today)}</p>
</header>

<section class="chapter" aria-labelledby="c0">
  <p class="rm-eyebrow">Коротко</p>
  <h2 class="rm-h2" id="c0">Что установлено, а что нет</h2>
  <table class="verdict"><tbody>
    <tr><td>{chip("doc", "Документ")}</td><td>«Наша Правда» заявляет на своём сайте, что она — совместный проект «ДАР» и «Градиславы». Руководители обоих фондов входят в её наблюдательный совет. В нём же — Илья Елисеев, имя и дата рождения которого совпадают с записями в санкционных списках США, Великобритании, Канады, Австралии и Новой Зеландии.</td></tr>
    <tr><td>{chip("rep", "Со слов сторон")}</td><td>Секретарь наблюдательного совета ЦБСТ и руководитель центрального исполкома «Единой России» Александр Сидякин пишет, что фонд создан «по поручению Председателя Партии Дмитрия Анатольевича Медведева». Сам ЦБСТ сообщает, что Медведев лично передал бойцам технику, купленную «за счёт средств фонда «Наша правда»». Сам фонд сообщает не меньше чем о {len(events)} передачах двух изделий с июля 2024 по май 2026 года.</td></tr>
    <tr><td>{chip("rep", "Версия ФБК")}</td><td>«ДАР» и «Градислава» — часть сети некоммерческих фондов, через которые, по утверждению ФБК (2017), Медведев распоряжался имуществом. Документа, который это подтверждает или опровергает, у нас нет.</td></tr>
    <tr><td>{chip("open", "Не показано")}</td><td>Что деньги «ДАР» и «Градиславы» оплатили эти передачи. Что какое-либо изделие применялось против гражданских.</td></tr>
  </tbody></table>
</section>

<section class="chapter" aria-labelledby="c1">
  <p class="rm-eyebrow">1 · Пост</p>
  <h2 class="rm-h2" id="c1">Три дня и восемьдесят миллионов</h2>
  <div class="lead-in">
    <div class="text">
      <p>10 апреля 2025 года телеграм-канал фонда «Наша Правда» сообщил:{r("np_post_422")}</p>
      {P.bq(q_head["text_ru"], "Telegram, @nashapravdafond, 10.04.2025")}
      <p>В списке — FPV-дроны, «Мавики», мотоциклы, квадроциклы, дистанционно управляемые эвакуационные платформы, станция
      радиоэлектронной разведки «Перехват» и детектор «Булат». Партия стоит 18,2 млн рублей; за всю поездку по приграничным
      территориям, как пишет фонд, передали «спецтехники на сумму около 80 млн рублей».</p>
    </div>
    <figure class="rm-fig"><div class="frame"><img src="{still}" alt="Квадроцикл, вокруг него люди и снаряжение" loading="lazy"></div>
      <figcaption><span class="rm-prov">Опубликовано фондом</span><span>Кадр из того же поста: квадроцикл, вокруг — люди и снаряжение.</span>
      <span class="when">{ru_date("2025-04-10")}</span></figcaption></figure>
  </div>
  <p>Фонд называет это помощью. То же слово стоит в самой крупной строке его отчётности: в 2024 году «социальная и благотворительная
  помощь для зоны СВО» — <b>{rub_bn(aid * 1000)} млрд рублей, {pct(aid_share)}% всех расходов</b>.{r("np_accounts24")} Что именно куплено на эти
  деньги, в отчётности не сказано.</p>
</section>

<section class="chapter" aria-labelledby="c2">
  <p class="rm-eyebrow">2 · Фонд</p>
  <h2 class="rm-h2" id="c2">Фонд, чьих учредителей в реестре нет</h2>
  <p>Формально «Наша Правда» — обычный благотворительный фонд, зарегистрированный в Москве весной 2023 года. Генеральный директор
  с первого дня — Александр Бровченко.{r("np_egrul")} А на деле из реестра о фонде ничего не узнать: у такой формы юридического лица
  список учредителей в ЕГРЮЛ не публикуется, и выписка его не содержит. Устав бумажный, в цифровом виде его нет.{r("np_site")}</p>
  <p>Единственный документ, который говорит, кто за фондом стоит, — его собственный сайт:</p>
  {P.bq(q_site["text_ru"], "сайт фонда, раздел «О фонде», запись от 08.09.2026")}
  <p>{chip("doc", "Документ")} — но самого фонда о себе. Это прямое признание, а не пересказ прессы; «Ведомости» ещё в апреле 2023 года писали
  о том же.{r("vedomosti")}</p>
  <p>Пояснительная записка к отчётности за 2024 год называет органы фонда поимённо.{r("np_accounts24")}</p>
  <table class="lines board"><thead><tr><th>Совет</th><th>Кто в него входит</th></tr></thead><tbody>
    <tr><td>Наблюдательный</td><td>Виктор Давыдов («ДАР»), Иван Карабинский («Градислава»), Илья Елисеев, Дмитрий Устратов (Фонд поддержки национальных морских программ), Татьяна Антонова</td></tr>
    <tr><td>Попечительский</td><td>Сергей Тихонов («ДАР»), Роман Манецкий («Градислава»), Марина Дукал («ДАР»)</td></tr></tbody></table>
  <p>Давыдов — генеральный директор «ДАР» с мая 2008 года,{r("dar_egrul")} Карабинский — генеральный директор «Градиславы» с апреля 2013-го.{r("grad_egrul")}
  Из восьми членов двух советов пятеро представляют фонды-основатели.</p>
</section>

<section class="chapter" aria-labelledby="c3">
  <p class="rm-eyebrow">3 · Деньги</p>
  <h2 class="rm-h2" id="c3">У основателей — миллиарды, в «Нашей Правде» от них — 59 миллионов</h2>
  <p>В отчётности «ДАР» и «Градиславы» суммы, несопоставимые с бюджетом «Нашей Правды»:{r("dar_accounts", "grad_accounts", "np_accounts24", "np_accounts25")}</p>
  {money_table}
  <p class="note">Как напечатано в годовой отчётности каждого фонда. Это целевые средства, а не выручка.</p>
  <p>Но в самой «Нашей Правде» эти деньги не видны. В примечаниях к её отчётности за 2024 год названы только два жертвователя: «ДАР»
  перечислил 5 млн рублей, «Градислава» — 54 млн. Это {rub_m(founders_money * 1000, 0)} млн из {rub_bn(recv24 * 1000)} млрд, меньше {pct(founders_share)}%
  поступлений. Ещё {rub_bn(donors * 1000)} млрд, или {pct(donor_share)}%, записаны как целевые средства «от юридических и физических лиц на ведение
  уставной деятельности». Имён и сумм по донорам в примечаниях нет.</p>
  {split_bar}
  <p class="note">Четыре строки примечаний складываются в итог только если считать «ДАР» и «Градиславу» дважды: примечания не говорят,
  один это платёж или два.</p>
  <p>Поэтому формулировка получается такая: <b>документы показывают, что два фонда стоят за «Нашей Правдой» и сидят в её совете. Они не показывают,
  что деньги «ДАР» и «Градиславы» оплатили то, что «Наша Правда» передаёт армии.</b> Откуда пришли остальные {rub_bn(donors * 1000)} млрд, в отчётности не написано.</p>
  <p>Ещё одна цифра, которую мы не объясняем. «Градислава» в 2024 году, по собственной отчётности, использовала {rub_bn(g24["funds_used"])} млрд рублей при
  поступлении {rub_bn(g24["funds_received"])} млрд: остаток упал с {rub_bn(g24["funds_balance_start"])} до {rub_bn(g24["funds_balance_end"])} млрд.
  Цифры сходятся с остатками в отчётности за соседние годы. На что потрачены деньги, в записи не расшифровано; это вопрос к фонду.{r("grad_accounts")}</p>
</section>

<section class="chapter" aria-labelledby="c4">
  <p class="rm-eyebrow">4 · Чьи это фонды</p>
  <h2 class="rm-h2" id="c4">Основатель «ДАР» — компания Михельсона и Симановского</h2>
  <p>«ДАР» зарегистрирован в 2006 году. По отчётности за 2023 год его учредитель — ООО «ЛЕВИТ» (ИНН 6330030244); то же писали «Ведомости».{r("dar_accounts", "vedomosti")}
  По выписке из ЕГРЮЛ от 7 сентября 2026 года «ЛЕВИТ» принадлежит Леониду Михельсону (78,29%) и Леониду Симановскому (21,71%).{r("levit_egrul")} {chip("doc", "Документ")}</p>
  <p>Учредителем «Градиславы» «Ведомости» называют Леонида Рубцова. В реестре этого нет: у некоммерческого фонда список учредителей не публикуется, так что это
  версия прессы, а не документ.{r("vedomosti", "grad_egrul")}</p>
  <p>Дальше начинается версия.</p>
  <p>В 2017 году Фонд борьбы с коррупцией выпустил фильм и сайт «Он вам не Димон. Тайная империя Дмитрия Медведева». ФБК утверждает, что «ДАР» и «Градислава» —
  два из четырёх некоммерческих фондов, через которые Медведев, будучи президентом и премьер-министром, распоряжался резиденциями, землёй, виноградниками и
  яхтами, а деньги пришли от подарков олигархов и кредитов госбанков.{r("fbk")} {chip("rep", "Версия ФБК")}</p>
  <ul class="qa">
    <li>Цепочки зарегистрированных связей — кто основатель, директор, член совета — проверяемы, и на них ФБК строит текст. Часть из них мы проверили (см. выше).</li>
    <li>Шаг от «эти люди руководят фондами» к «имуществом владеет Медведев» ФБК делает умозаключением и сам так пишет: «Мы убеждены, что обе эти яхты…»,
    «Мы считаем это очередным доказательством…». Самое веское доказательство, по его словам, получено из взломанного почтового ящика. <b>Такими материалами мы не пользуемся.</b></li>
    <li>В самом фильме записаны отрицания: Медведев «через пресс-секретаря» отрицает причастность к плёсской даче; Михельсон, как пишет ФБК, «говорит, что к фонду «Дар» отношения не имеет».
    Ответа Медведева на сам тезис о сети фондов в нашем распоряжении нет.</li>
    <li>Фильм вышел за шесть лет до создания «Нашей Правды». О ней, ЦБСТ и РОЙ.МАРКЕТ в нём нет ни слова.</li>
  </ul>
  <p>Одна деталь показывает, где проходит граница между документом и версией. В 2017 году Михельсон, по пересказу ФБК, к «ДАР» отношения не имел. В отчётности
  «ДАР» за 2023 год учредителем указана компания, которой Михельсон владеет на 78,29%. Оба факта могут быть верны: фонд мог быть основан через компанию без его
  личного участия, и когда и как это оформлено, мы не знаем. Сверх этого мы ничего не утверждаем.</p>
</section>

<section class="chapter" aria-labelledby="c5">
  <p class="rm-eyebrow">5 · Совет</p>
  <h2 class="rm-h2" id="c5">Человек в совете, которого ФБК называет доверенным лицом Медведева</h2>
  <p>В наблюдательном совете «Нашей Правды» — Илья Елисеев. Мы сверили имя и дату рождения с официальными выгрузками:</p>
  <ul class="qa">
    <li><b>США</b> (OFAC, список SDN): Ilya Vladimirovich YELISEYEV, программа RUSSIA-EO14024.{r("us")}</li>
    <li><b>Великобритания:</b> Ilya Vladimirovich Eliseev, внесён 26.09.2022 как «involved person» — лицо, вовлечённое в получение выгоды от правительства России или в его поддержку.{r("uk")}</li>
    <li><b>Канада:</b> Илья Владимирович Елисеев, 29.09.2022.{r("ca")}</li>
    <li><b>Австралия и Новая Зеландия:</b> тот же человек; в списке Новой Зеландии (01.03.2024) указано: «Member of the Board of Directors of Gazprombank JSC».{r("au", "nz")}</li>
  </ul>
  <p class="note">{chip("doc", "Документ")} Списки называют это лицо. Ограничение: дата рождения в нашей записи не подтверждена отдельным документом, так что это совпадение записи со
  списком, а не независимое установление личности.</p>
  <p>ФБК называет Елисеева «вице-президентом Газпромбанка, однокурсником, другом и бизнес-партнёром Медведева» и пишет: «Он самое доверенное лицо премьер-министра».{r("fbk")}
  Что он сидит в совете «Нашей Правды», подтверждает отчётность фонда. Остальное — {chip("rep", "версия ФБК")}</p>
  <p>Остальных семерых членов советов мы сверили с девятью списками (ЕС, США, Великобритании, Швейцарии, Японии, Австралии, Новой Зеландии, Канады и Совета Безопасности ООН):
  совпадений по имени и отчеству нет. Украинский список СНБО среди них не был, а отсутствие совпадения — не чистая справка.</p>
</section>

<section class="chapter" aria-labelledby="c6">
  <p class="rm-eyebrow">6 · Медведев</p>
  <h2 class="rm-h2" id="c6">Что о Медведеве пишут сами участники схемы</h2>
  <p>Версию ФБК здесь можно отложить: об участии Медведева говорят и те, кто передаёт технику. 7 ноября 2025 года канал ЦБСТ сообщил:{r("cbst_post_1484")}</p>
  {P.bq(barskurs, "Telegram, @ANO_CBST, 07.11.2025")}
  {P.bq(q61["text_ru"], "там же")}
  <p>В том же посте Сидякин назван «секретарём наблюдательного совета ЦБСТ и руководителем ЦИК «Единой России»»; отдельную поддержку проекту, по тексту поста, оказал
  Владимир Якушев, «секретарь Генерального совета партии «Единая Россия», председатель наблюдательного совета ЦБСТ». {chip("rep", "Со слов сторон")}</p>
  <p>10 декабря 2025 года Сидякин написал в собственном канале:{r("sid_post_609")}</p>
  {P.bq(q60["text_ru"], "Telegram, @asidyakin, 10.12.2025")}
  <p class="note">В предложении фонд не назван. Пост начинается словами «Нашим доблестным бойцам от Единой России и фонда «Наша Правда» передали очередную партию специальной техники», поэтому мы читаем «фонд» как «Наша Правда». Подписан пост «Сидякин в Telegram».</p>
  <p>7 августа 2026 года, после передачи 24-й бригаде спецназа и 9-му полку группировки «Центр» в районе Константиновки:{r("sid_post_1234")}</p>
  {P.bq(q59["text_ru"], "Telegram, @asidyakin, 07.08.2026")}
  <p>Что здесь документ, а что нет. Тексты — собственные слова сторон, и других свидетелей у нас нет. Они не показывают, что Медведев лично владеет или распоряжается фондом:
  «по поручению» и «держит на контроле» — слова партийного функционера о главе партии. Зато они показывают, что связь с Медведевым фонд и ЦБСТ не скрывают, а используют.</p>
  <p>Сам Медведев находится в списках ЕС и Великобритании (с 15.03.2022).{r("eu", "uk")} Обоснование британского внесения начинается словами «Dmitry Anatolyevich MEDVEDEV is Vice President of the Russian Security Council»;
  ЦБСТ в своём посте называет его «заместителем председателя Совета безопасности РФ», так что речь об одном человеке.</p>
  <p>Вот Так в сентябре 2026 года писал, что представители ЦБСТ называют Медведева «вдохновителем» РОЙ.МАРКЕТ. Кто именно это сказал, статья не уточняет, и эту строчку мы не используем.{r("vot_tak")}</p>
</section>

<section class="chapter" aria-labelledby="c7">
  <p class="rm-eyebrow">7 · Передачи</p>
  <h2 class="rm-h2" id="c7">Двадцать одна передача</h2>
  <p>Два изделия повторяются в постах фонда: «Булат», который фонд называет детектором дронов, и «Капюшон», станцию РЭБ.{r("np_post_382")} С июля 2024 по май 2026 года мы насчитали
  <b>{len(events)} поста</b>, в которых названо одно из них или оба. Все они — собственные сообщения фонда; ни по одному нет второго источника.{r("np_channel")}</p>
  {timeline}
  <p class="note">Кружок — пост с «Булатом», квадрат — пост с «Капюшоном», с обводкой — получатель гражданская служба.</p>
  <p>Получателей фонд называет с разной точностью: часть по названию или номеру — {b_named}; род войск или группировку без номера — {b_group};
  военнослужащих на направлении или в регионе без части — {b_region}; гражданские службы — {b_civil}. «Капюшон» фонд передал Курской областной клинической больнице и станции скорой помощи,{r("np_post_311")}
  а «Булат» и «Капюшон» — главам муниципальных округов Херсонской области по просьбе губернатора.{r("np_post_382")}</p>
  <p>В {len(STATED_VALUE)} постах названа стоимость партии. Она колеблется от {pct(vmin)} до {pct(vmax)} млн рублей, в сумме около {vsum:.0f} млн. Это цена всей партии,
  куда входят и дроны, и рации, и мотоциклы, а не цена двух изделий.</p>
  {P.bq(q_boy["text_ru"], "Telegram, @nashapravdafond, 09.06.2025", r("np_post_448"))}
  <p>10 августа 2026 года фонд написал о другой, более поздней партии:{r("np_post_656")}</p>
  {P.bq(q_gru["text_ru"], "Telegram, @nashapravdafond, 10.08.2026")}
  {P.bq(q_3d["text_ru"], "там же")}
  <p>Передача части не доказывает боевого применения: среди получателей есть тыловые подразделения и гражданские учреждения.</p>
</section>

<section class="chapter" aria-labelledby="c8">
  <p class="rm-eyebrow">8 · Центр</p>
  <h2 class="rm-h2" id="c8">ЦБСТ, который фонд ставит рядом с собой</h2>
  <p>ЦБСТ зарегистрирован 27 февраля 2024 года. Основатели по реестру — «Наша Правда» и ПАО «Банк ПСБ» (с 1 апреля 2025 года).{r("cbst_egrul")} На своём сайте ЦБСТ называет учредителем и «Единую Россию».{r("cbst_site")}
  Сидякин — секретарь его наблюдательного совета.{r("cbst_post_934")}</p>
  <p>В примечаниях «Нашей Правды» за 2024 год ЦБСТ назван «{esc(q_sub["text_ru"])}», а под этой строкой перечислены пять соглашений на {rub_m(contrib_total)} млн рублей, с 22 августа по 23 декабря 2024 года.
  Получатель в примечаниях не указан.{r("np_accounts24")} В собственной отчётности ЦБСТ за тот же год все {rub_m(CBST_LINES[1][2] * 1000)} млн рублей записаны как «прочие поступления», так что две отчётности не сопоставить.{r("cbst_accounts")}</p>
  <p>15 декабря 2025 года Сидякин написал в своём канале:{r("sid_post_618")}</p>
  {P.bq(q_sid["text_ru"], "Telegram, @asidyakin, 15.12.2025")}
  <p>Источник цифры в 2,5 млрд долларов в посте не указан. {chip("rep", "Со слов сторон")} О РОЙ.МАРКЕТ, который, по словам Сидякина, «вместе с партией и ПСБ запустили», — на главной странице проекта.</p>
</section>

<section class="chapter" aria-labelledby="c9">
  <p class="rm-eyebrow">9 · Пределы</p>
  <h2 class="rm-h2" id="c9">Чего мы не знаем</h2>
  <ol class="qa">
    <li><b>Откуда деньги.</b> {rub_bn(donors * 1000)} млрд из {rub_bn(recv24 * 1000)} млрд рублей поступлений 2024 года записаны как поступления «от юридических и физических лиц». Имён нет.</li>
    <li><b>Что купили на «помощь для зоны».</b> В отчётности это одна строка. По постам видна часть закупок, но не все.</li>
    <li><b>Что связывает «ДАР» и «Градиславу» с Медведевым сегодня.</b> Единственный наш источник — ФБК, 2017 год. Первичных документов, на которые он ссылается (выписок из реестра недвижимости, отчётности иностранных компаний), у нас нет: мы читали текст, а не приложения.</li>
    <li><b>Что значит «по поручению».</b> Это слова Сидякина о фонде; формы участия Медведева в фонде они не раскрывают.</li>
    <li><b>Кто остальные члены советов.</b> Про Устратова, Антонову, Тихонова, Манецкого и Дукал мы знаем только должности и места работы, как их печатает отчётность.</li>
  </ol>
</section>

<section class="chapter" aria-labelledby="c10">
  <p class="rm-eyebrow">10 · Ответ</p>
  <h2 class="rm-h2" id="c10">Вопросы, которые нужно задать до публикации</h2>
  <p class="draftnote">Письма не отправлены.</p>
  <p>Фонду «Наша Правда», «ДАР», «Градиславе», пресс-службе Дмитрия Медведева, ЦБСТ и Илье Елисееву:</p>
  <ul class="qa">
    <li>Кто и сколько перечислил «Нашей Правде» в 2024 и 2025 годах по строке «юридические и физические лица»?</li>
    <li>Участвуют ли «ДАР» и «Градислава» в финансировании закупок, о которых сообщает фонд?</li>
    <li>Что входит в строку «помощь для зоны СВО» в отчётности?</li>
    <li>Какова роль Дмитрия Медведева в создании и работе фонда: что имеет в виду Александр Сидякин, говоря о «поручении»?</li>
    <li>Является ли Дмитрий Медведев бенефициаром, донором или иным участником «ДАР», «Градиславы» или «Нашей Правды»?</li>
    <li>На что «Градислава» потратила {rub_bn(g24["funds_used"])} млрд рублей в 2024 году?</li>
  </ul>
</section>

<section class="rm-sources" aria-label="Источники"><h2 class="rm-h2">Источники</h2><ol>@@NOTES@@</ol></section>
</main>
</body></html>
"""
    doc = P.finalize(doc)
    out.write_text(doc, encoding="utf-8")
    print(f"wrote {out.relative_to(REPO) if out.is_relative_to(REPO) else out}: {len(doc) // 1024} KB; "
          f"{P.checked} quotation checks passed, {P.skipped} skipped for want of a local text")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=REPO / "exhibits" / "aid_ru.html")
    render(ap.parse_args().out)
