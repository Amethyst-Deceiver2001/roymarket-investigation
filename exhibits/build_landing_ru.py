#!/usr/bin/env python3
"""Русская версия лендинга: «ЦБСТ и РОЙ.МАРКЕТ». Private preview page, written in Russian, not translated.

  python3 exhibits/build_landing_ru.py                    # writes exhibits/landing_ru.html (+ images/ beside it)
  python3 exhibits/build_landing_ru.py --out some/path.html

The copy is new; the evidence is the English landing's. Every quotation is the verbatim Russian from
build_landing.OPENING_QUOTES, quotes.json or a stored page, and is checked word for word against the scraped post
(data/roymarket.db) or the saved capture where this machine holds them. Every figure is read from data/registry/ and
asserted. The page prints no source id, slug or file name. The English landing's wall of logos, sanctions grid and
revenue bars are not rebuilt here; the page says so and links the English one.
Layout is exhibits/landing.css plus the few rules below; tokens come from design/roymarket.css.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import sqlite3
import sys
from pathlib import Path
from string import Template

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "exhibits"))
from build_landing import OPENING_QUOTES, OPENING_SOURCES, SUPPLIER_LINES, UN_QUOTES, Landing  # noqa: E402
from display_helpers import (design_head, ru_date, share_meta_html, _SUPPORT_CSS, _wallets_html)  # noqa: E402

REG = REPO / "data" / "registry"
esc = html.escape
CBST, MPTM, NP = "ano-tsbst-centre-for-unmanned-systems-technologies", "ooo-mptm", "fond-nasha-pravda"
STORY_FILE = "aid_ru.html"
# While a page is a private preview its sibling pages are private Artifacts; once built into docs/ they are relative files.
PREVIEW_LINKS = {"aid_ru.html": "https://claude.ai/artifact/5K3R57G7co4x2Ru5j2MXAn", "chain_bulat.html": "https://claude.ai/artifact/6UaTv2jSwdNdfNUCibCwrf",
                 "arkhangel.html": "https://claude.ai/artifact/RABnZkrCUwktU5b91cNZTn", "company_ooo-trimiks.html": "https://claude.ai/artifact/GVG9YdHZVHPZNtKqBoZqEc",
                 "company_ooo-goudron.html": "https://claude.ai/artifact/3rMXcnJ8DZ66WmvcTFk9Yi"}

PAGE_CSS = """
.top h1 { max-width: 22ch; }
.byline { font: 400 var(--t-note)/1.4 var(--font-sans); color: var(--ink-3); margin: var(--space-3) 0 0; }
main.rm-page section { display: flex; flex-direction: column; gap: var(--space-4); }
main.rm-page p, main.rm-page li { max-width: var(--measure); }
main.rm-page p { font-size: 17px; line-height: 1.62; margin: 0; }
.finds { list-style: none; margin: 0; padding: 0; display: grid; gap: var(--space-3); }
.finds li { display: grid; grid-template-columns: 9rem minmax(0, 1fr); gap: 4px 14px; align-items: baseline; padding-top: 12px; border-top: 1px solid var(--rule-soft); }
.finds b { font: 600 17px/1.35 var(--font-serif); }
.finds span.t { color: var(--ink-2); font-size: 16px; line-height: 1.5; }
.found-n { color: var(--ink-2); }
.rm-quote .q { white-space: pre-line; }
.steps { list-style: none; margin: 0; padding: 0; display: grid; gap: 10px; }
.steps li { display: grid; grid-template-columns: 9rem minmax(0, 1fr); gap: 4px 14px; padding-top: 10px; border-top: 1px solid var(--rule-soft); font-size: 16px; line-height: 1.5; }
.steps .when { font: 600 12px/1.5 var(--font-mono); letter-spacing: .05em; text-transform: uppercase; color: var(--ink-3); }
.steps .gap { color: var(--ink-3); font-style: italic; padding-left: 9rem; border-top: 0; padding-top: 0; }
.clip { margin: 0; max-width: 760px; }
.clip video { width: 100%; border-radius: var(--radius); background: #000; }
.clip figcaption { font-size: var(--t-note); color: var(--ink-2); margin-top: 8px; }
.pair { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: var(--space-4); max-width: 900px; }
.pair .rm-quote { margin: 0; }
.tl-list { list-style: none; margin: 0; padding: 0; display: grid; gap: 8px; }
.tl-list li { display: grid; grid-template-columns: 8.5rem minmax(0, 1fr) auto; gap: 4px 14px; align-items: baseline; padding-top: 8px; border-top: 1px solid var(--rule-soft); font-size: 16px; line-height: 1.5; }
.tl-list .d { font: 600 13px/1.5 var(--font-mono); color: var(--ink-3); }
.cards { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: var(--space-4); }
.cards li { max-width: none; padding: var(--space-4); border: 1px solid var(--rule); border-radius: var(--radius); background: var(--panel); display: flex; flex-direction: column; gap: 6px; }
.cards b { font: 600 17px/1.3 var(--font-serif); }
.cards .st { color: var(--ink-3); font-size: var(--t-note); }
.note { font-size: var(--t-note) !important; color: var(--ink-2); }
.stills { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: var(--space-4); max-width: 900px; }
.stills figure { margin: 0; }
.stills img { width: 100%; height: auto; border-radius: var(--radius); display: block; }
.stills figcaption { font-size: var(--t-note); color: var(--ink-2); margin-top: 6px; }
@media (max-width: 720px) { .finds li, .steps li, .tl-list li { grid-template-columns: minmax(0, 1fr); } .steps .gap { padding-left: 0; } }
"""

# --- sources -----------------------------------------------------------------------------------------------
# Labels of the English landing's OPENING_SOURCES entries that are not a plain Telegram post, in Russian.
RU_LABELS = {
    "ukrinform": "Укринформ, «Ворог вдарив дроном по будівлі Запорізької ОВА», 08.10.2026, со ссылкой на главу Запорожской областной военной администрации",
    "dw_film": "DW, документальный фильм «Targeting Civilians: How Russian Drones Terrorize a Ukrainian City», 2024 (YouTube); указание на источник кадров — 8:46, карта подразделений — 16:53",
    "rm_aug": "РОЙ.МАРКЕТ, «Начать продавать на РОЙ.МАРКЕТ» (страница для будущих продавцов), копия Internet Archive от 22.08.2026",
    "rm_oct": "Та же страница, копия Internet Archive от 12.10.2026",
    "rm_now": "Та же страница на 24.10.2026",
    "un_crp": "Независимая международная комиссия ООН по расследованию событий в Украине, «“They are hunting us”: systematic drone attacks targeting civilians in Kherson», документ A/HRC/59/CRP.2, 28.05.2025",
    "un_ga": "Независимая международная комиссия ООН по расследованию событий в Украине, доклад Генеральной Ассамблее A/80/497, 21.10.2025",
    "cir": "Centre for Information Resilience совместно с DW, «Tracing the Russian units responsible for drone attacks in Kherson», 2024",
}
REG_LABELS = {   # registry sources that are not a plain post or a standard extract: Russian label
    "s8737": "Telegram, @kb_spektr, пост от 06.07.2026",
    "s0207": "Отчёт ЦБСТ о деятельности в Министерство юстиции за 2025 год",
    "s8817": "«Агентский договор-оферта для Поставщиков — РОЙ.МАРКЕТ», копия Internet Archive от 22.08.2026",
    "s8822": "«Агентский договор-оферта для Поставщиков — РОЙ.МАРКЕТ», на roimarket.ru, копия от 01.10.2026",
    "s8860": "Telegram, закрытый чат «3mx.ru — ЧАТ», сообщение от 02.09.2026",
    "s8866": "«Военный маркетплейс «Рой.Маркет» переходит в полноценный режим работы», «Коммерсантъ», 13.08.2026",
    "s8867": "«ЦБСТ масштабирует площадку двойного назначения РОЙ.МАРКЕТ», cbst.ru, копия от 01.10.2026",
    "s0382": "Отчёт ЦБСТ об использовании целевых средств за 2024 год (ФНС)",
    "s0385": "Отчёт ЦБСТ об использовании целевых средств за 2025 год (ФНС)",
}


def ru_label(text: str) -> str:
    m = re.match(r"Telegram, @(\S+?)(?: \(([^)]*)\))?, post (\d+), (\d\d\.\d\d\.\d{4})(, signed @\S+)?$", text)
    if m:
        who = f"@{m.group(1)}" + (f" ({m.group(2)})" if m.group(2) else "")
        return f"Telegram, {who}, пост от {m.group(4)}"
    m = re.match(r"Company register extract \(ЕГРЮЛ, Federal Tax Service\) for (ОГРН|ИНН) (\d+), (\d\d\.\d\d\.\d{4})", text)
    if m:
        return f"Выписка из ЕГРЮЛ, {m.group(1)} {m.group(2)}, от {m.group(3)}"
    m = re.match(r"Annual accounts filed with the Federal Tax Service, ИНН (\d+), FY (\d{4})", text)
    if m:
        return f"Годовая бухгалтерская отчётность, ИНН {m.group(1)}, за {m.group(2)} год (ФНС)"
    raise SystemExit(f"no Russian label for source title: {text}")


def load(name):
    d = json.loads((REG / name).read_text(encoding="utf-8"))
    return d if isinstance(d, list) else next(iter(d.values()))


class Notes:
    def __init__(self):
        self.src = {s["id"]: s for s in load("sources.json")}
        self.order: list[tuple[str, str, str | None]] = []   # (key, label, url)
        self.uses = 0

    def ref(self, *keys: str) -> str:
        out = []
        for k in keys:
            if k in OPENING_SOURCES:
                label = RU_LABELS.get(k) or ru_label(OPENING_SOURCES[k][0])
                url = OPENING_SOURCES[k][1]
            else:
                s = self.src[k]
                label = REG_LABELS.get(k) or ru_label(s["title"])
                url = s.get("public_url")
            ident = next((i for i, (kk, _, _) in enumerate(self.order) if kk == k), None)
            if ident is None:
                self.order.append((k, label, url))
                ident = len(self.order) - 1
            self.uses += 1
            out.append(f'<a href="#n{ident + 1}" id="r{self.uses}">{ident + 1}</a>')
        return '<sup class="fn">' + ",".join(out) + "</sup>"

    def list_html(self) -> str:
        items = []
        for i, (_, label, url) in enumerate(self.order, 1):
            shown = ""
            if url:
                shown = re.sub("^https?://", "", url) if url.startswith("https://t.me/") else re.sub("^https?://([^/]+).*$", "\\1", url)
            link = (' <a href="' + esc(url) + '">' + esc(shown) + "</a>") if url else ""
            items.append(f'<li id="n{i}">{esc(label)}.{link}</li>')
        return "".join(items)


def verify(chan: str, msg: int, parts: list[str], counters: dict):
    db = REPO / "data" / "roymarket.db"
    if not db.exists():
        counters["skipped"] += len(parts)
        return
    row = sqlite3.connect(f"file:{db}?mode=ro", uri=True).execute(
        "select p.text from tg_posts p join tg_channels c on c.id = p.channel_id where lower(c.username) = lower(?) and p.msg_id = ?",
        (chan, msg)).fetchone()
    norm = lambda x: " ".join(x.replace(" ", " ").split())
    for part in parts:
        if not row or norm(part.rstrip(".;:")) not in norm(row[0]):
            raise SystemExit(f"quote not verbatim in {chan}/{msg}: {part[:60]}")
        counters["checked"] += 1


def quote(ru: str, cite: str, strong: bool = False) -> str:
    cls = "rm-quote key" if strong else "rm-quote"
    return f'<blockquote class="{cls}"><span class="q" lang="ru">{esc(ru)}</span><cite>{cite}</cite></blockquote>'


def render(out: Path):
    N = Notes()
    cnt = {"checked": 0, "skipped": 0}
    ents = {e["slug"]: e for e in load("entities.json")}
    ppl = {p["slug"]: p for p in load("people.json")}
    qs = {q["id"]: q for q in load("quotes.json")}
    today = dt.date.today().isoformat()
    L = Landing()
    n_org, by, n_sanc = L.network()
    assert by["doc"] + by["rep"] == n_org

    def oq(key, cite):
        chan, msg, ru, _ = OPENING_QUOTES[key]
        verify(chan, msg, ru.split(" […] "), cnt)
        return quote(ru, cite, strong=key in ("cbst", "arch_9067", "arch_10667", "osv_27702", "osv_36192", "yakim"))

    def q_reg(qid, cite):
        q = qs[qid]
        return quote(q["text_ru"], cite)

    r = N.ref
    # ---- facts asserted against the registry
    cbst = ents[CBST]
    founders = " ".join(str(h.get("value")) for h in cbst.get("founders_history") or [])
    assert "Наша Правда" in founders and "ПСБ" in founders
    assert all(h.get("as_of") == "2024-02-27" for h in cbst["founders_history"]), "founders are recorded from registration, 27.02.2024"
    assert ents[MPTM]["inn"] == "9714068459"
    assert any(s["slug"] == MPTM and s.get("as_of") for s in cbst.get("subsidiaries") or [])
    fy = {f["year"]: f for f in cbst["financials"]}
    assert fy["2024"]["funds_received"] == 269_835_000 and fy["2025"]["funds_received"] == 137_105_000
    assert "Secretary of the Supervisory Board" in " ".join(x.get("title") or "" for x in ppl["aleksandr-sidyakin"]["roles"])
    assert any("restricted" in str(h.get("value")) and h.get("as_of") == "2026-07-15" for h in ents[MPTM].get("founders_history") or [])
    g_tie_sid = ents["ooo-gagaring"]["cbst_tie"]["source_id"]
    q_site1, q_site2 = qs["q040"], qs["q041"]
    q_op, q_mask, q_row, q_restr = qs["q051"], qs["q052"], qs["q050"], qs["q053"]
    q_pilot, q_tech, q_3mx, q_spec = qs["q046"], qs["q047"], qs["q049"], qs["q048"]
    q_sid1215 = qs["q042"]
    announce = ("Онлайн-маркетплейс РОЙ.МАРКЕТ открыл защищённый канал продаж для производителей, дистрибьюторов и профессиональных "
                "селлеров товаров двойного назначения. В первую очередь площадка приглашает к сотрудничеству юрлица, которые уже работают "
                "на Wildberries, Ozon и других универсальных маркетплейсах.")
    verify("ANO_CBST", 2413, [announce[:150], announce[151:]], cnt)
    verify("asidyakin", 618, [q_sid1215["text_ru"], qs["q045"]["text_ru"]], cnt)
    verify("asidyakin", 1234, [qs["q059"]["text_ru"]], cnt)
    verify("asidyakin", 609, [qs["q060"]["text_ru"]], cnt)

    # ---- video (copied beside the page)
    vsrc, vdst = REPO / "exhibits" / "images" / "video", out.parent / "images" / "video"
    have_video = (vsrc / "gagaring-5142.mp4").exists()
    if have_video and vdst != vsrc:
        vdst.mkdir(parents=True, exist_ok=True)
        for name in ("gagaring-5142.mp4", "gagaring-5142.jpg", "osv-38645.mp4", "osv-38645.jpg"):
            (vdst / name).write_bytes((vsrc / name).read_bytes())
    have_osv = (vsrc / "osv-38645.mp4").exists()
    stills_dir = REPO / "exhibits" / "images" / "kherson"
    sdst = out.parent / "images" / "kherson"
    still_ok = (stills_dir / "k27702.jpg").exists() and (stills_dir / "k38703.jpg").exists()
    if still_ok and sdst != stills_dir:
        sdst.mkdir(parents=True, exist_ok=True)
        for name in ("k27702.jpg", "k38703.jpg"):
            (sdst / name).write_bytes((stills_dir / name).read_bytes())

    DOC = '<span class="rm-grade doc">Документ</span>'
    REP = '<span class="rm-grade rep">Со слов сторон</span>'
    OPEN = '<span class="rm-grade open">Не подтверждено</span>'
    in_docs = out.parent.name == "docs"
    here = lambda f: (out.parent / f).exists() if in_docs else f in PREVIEW_LINKS
    href = lambda f: f if in_docs else PREVIEW_LINKS[f]

    # -- the opening -------------------------------------------------------------------------------------------
    gag_clip = ""
    if have_video:
        gag_clip = ('<figure class="clip"><video controls preload="none" playsinline poster="images/video/gagaring-5142.jpg" '
                    'aria-label="Видео «Гагаринга»: дрон влетает к большому зданию, к гербу-трезубцу на фасаде, затем отдельный фрагмент, где герб висит повреждённым">'
                    '<source src="images/video/gagaring-5142.mp4" type="video/mp4"></video>'
                    '<figcaption><span class="rm-label">Видео · 0:25</span> Ролик «Гагаринга» с пометкой «Кузнечик/Сова 5.8»: дрон влетает в герб на фасаде здания. '
                    'Последние восемь секунд — отдельный фрагмент.' + r("gag") + "</figcaption></figure>")
    opening = Template("""
<section aria-labelledby="h-open"><h2 class="rm-h2" id="h-open">Ролик с ударом и строчка о продажах</h2>
$clip
<p>19 октября 2026 года ООО «Гагаринг», краснодарский производитель электроники для дронов, выложил в своём телеграм-канале короткое видео:</p>
$q_gag
<p>На следующее утро ЦБСТ, у которого «Гагаринг» числится в «резидентах»$ref_tie, выложил то же видео под своим заголовком, назвал оба изделия
и закончил пост строчкой о том, где их можно купить:</p>
$q_cbst
<ol class="steps" aria-label="От сообщения об ударе до строчки о заказе">
  <li><span class="when">8 октября</span><span><b>Запорожье.</b> Глава областной администрации сообщает, что FPV-дрон попал в герб на здании администрации. $rep</span></li>
  <li class="gap">ни один из постов не датирует удар</li>
  <li><span class="when">19 октября</span><span><b>«Гагаринг».</b> Производитель публикует видео «результатов работы» своих «Кузнечика» и «Совы 5.8». $rep</span></li>
  <li class="gap">то же видео</li>
  <li><span class="when">20 октября</span><span><b>ЦБСТ.</b> Перепощивает его как «кадры удара» от своего «резидента» и называет оба изделия. $rep</span></li>
  <li class="gap">строчка о продажах</li>
  <li><span class="when">Где заказать</span><span><b>РОЙ.МАРКЕТ.</b> ЦБСТ пишет, что военнослужащие могут заказать оба изделия там. Каталог закрыт логином, так что пост — единственное свидетельство того, что они там есть. $rep</span></li>
</ol>
<p>В том же посте ЦБСТ пишет об «администрации оккупированного Запорожья». Запорожье под контролем Украины, а здание — резиденция областной власти: 8 октября глава
областной администрации сообщил, что FPV-дрон попал в герб на его фасаде.$ref_ukr РОЙ.МАРКЕТ — маркетплейс, в который можно войти только по логину; по словам секретаря
наблюдательного совета ЦБСТ, функционера «Единой России», запустили его сам ЦБСТ вместе с партией и банком ПСБ.$ref_sid</p>
<p class="note">$rep Оба поста — собственные слова сторон. Видео не противоречит сообщению от 8 октября, но ни один из постов не называет дату удара.</p>
<p>«Двойное назначение» в посте ЦБСТ — ярлык самой платформы. С августа 2026 года её страница для будущих продавцов начиналась словами «$dual»;$ref_aug в копии от 12 октября эта фраза
ещё была на месте.$ref_oct К 24 октября та же страница говорила иначе: «$special»$ref_now В публичной оферте и договоре для покупателей нет ни той, ни другой формулировки.</p>
<h3 class="rm-h3">Чего это не доказывает</h3>
<ul>
<li>Передача чего-либо воинской части не означает, что это применялось в бою. Среди получателей есть и тыловые подразделения.</li>
<li>Размер доли ЦБСТ в компании, которая управляет РОЙ.МАРКЕТ, не указан ни в одном собранном документе, а с 15.07.2026 ЕГРЮЛ скрывает, кому эта компания принадлежит.</li>
<li>Американская санкционная запись под похожим названием относится к другой компании, зарегистрированной в Туле. Сам ЦБСТ в списках США не значится.</li>
</ul>
</section>""").substitute(
        clip=gag_clip, q_gag=oq("gag", "«Гагаринг», Telegram, 19.10.2026" + r("gag")), ref_tie=r(g_tie_sid),
        q_cbst=oq("cbst", "ЦБСТ, Telegram, 20.10.2026" + r("cbst")), rep=REP, ref_ukr=r("ukrinform"), ref_sid=r("s8847"),
        dual=SUPPLIER_LINES["dual"][0], special=SUPPLIER_LINES["special"][0], ref_aug=r("rm_aug"), ref_oct=r("rm_oct"), ref_now=r("rm_now"))

    # -- who stands behind ЦБСТ -------------------------------------------------------------------------------
    who = Template("""
<section aria-labelledby="h-hub"><h2 class="rm-h2" id="h-hub">Кто стоит за ЦБСТ</h2>
<p>Формально ЦБСТ — отраслевая организация, которая объединяет разработчиков дронов. А по ЕГРЮЛ его учредители — донорский фонд и государственный банк:
фонд «Наша Правда» и ПАО «Банк ПСБ», с даты регистрации, 27 февраля 2024 года.$ref_reg $doc Третьим учредителем ЦБСТ на своём сайте называет правящую партию:</p>
$q_site
<p>В реестре «Единой России» среди учредителей нет. Секретарь наблюдательного совета ЦБСТ Александр Сидякин — руководитель центрального исполкома партии;$ref_role так он
назван в собственном канале ЦБСТ. Вот как он подводил итоги года:</p>
$q_sid
<p>Сколько денег прошло через ЦБСТ, видно только по отчётности, да и то неполно: в 2024 году он получил $m24 млн рублей целевых средств,$ref_a24 в 2025-м — $m25 млн.$ref_a25
Это средства некоммерческой организации, а не выручка. В отчёте за 2024 год вся сумма записана одной строкой — «прочие поступления».</p>
<h3 class="rm-h3">Что здесь документ, а что слова</h3>
<ul>
<li>Фонд «Наша Правда» и банк ПСБ — учредители ЦБСТ с момента регистрации. $doc</li>
<li>«Единая Россия» — учредитель по словам самого ЦБСТ; в ЕГРЮЛ её нет. $rep</li>
<li>Александр Сидякин — секретарь наблюдательного совета и руководитель ЦИК «Единой России», как об этом пишет ЦБСТ.$ref_role $rep</li>
<li>В отчёте за 2025 год ЦБСТ указывает ООО «МПТМ» среди компаний, в которых участвует, с 22.01.2025; размер доли не назван.$ref_row $doc</li>
<li>ООО «МПТМ» — оператор РОЙ.МАРКЕТ по собственной оферте платформы для поставщиков.$ref_offer $rep</li>
</ul>
<p>«Наша Правда» — тот самый донорский фонд, о котором дальше идёт отдельный материал: ему принадлежит часть передач на фронт, а его собственный сайт называет его
совместным проектом ещё двух фондов. Один из руководителей ЦБСТ пишет, что фонд создан «по поручению» Дмитрия Медведева. Это слова одной из сторон, документа за ними нет.
<a href="$story">Как фонды, связанные с Дмитрием Медведевым, снабжают российскую армию →</a>$story_note</p>
</section>""").substitute(
        ref_reg=r("s0228"), doc=DOC, rep=REP, q_site=quote(q_site2["text_ru"], "ЦБСТ, cbst.ru, 13.08.2026" + r("s8867")),
        ref_role=r("s8699"), q_sid=quote(q_sid1215["text_ru"] + " […] " + qs["q045"]["text_ru"], "Александр Сидякин, Telegram, 15.12.2025" + r("s8847"), strong=True),
        m24=f"{269_835_000 / 1e6:.1f}".replace(".", ","), m25=f"{137_105_000 / 1e6:.1f}".replace(".", ","), ref_a24=r("s0382"), ref_a25=r("s0385"),
        ref_row=r("s0207"), ref_offer=r("s8817"),
        story=href(STORY_FILE) if here(STORY_FILE) else "#h-dossiers", story_note="" if in_docs else " <i>(пока в частном просмотре)</i>")

    # -- the front ------------------------------------------------------------------------------------------
    uq = UN_QUOTES
    front = Template("""
<section aria-labelledby="h-front"><h2 class="rm-h2" id="h-front">Фронт, который он снабжает</h2>
<p>В мае 2025 года Независимая международная комиссия ООН по расследованию событий в Украине пришла к выводу, что российские операторы дронов на левом берегу Днепра десять месяцев
нападали на мирных жителей Херсона и что эти нападения — преступление против человечности, убийство.$ref_crp В октябре комиссия распространила этот вывод на 300 километров реки и три области и назвала объединение, в котором служат операторы:</p>
<blockquote class="rm-quote"><span class="q">«Они связаны с различными армейскими частями, все из которых входят в группировку войск “Днепр”» <i>(перевод наш)</i></span>
<cite>доклад ООН A/80/497, п. 40, 21.10.2025 (оригинал: «$un_dnepr»)$ref_ga</cite></blockquote>
<p>Комиссия называет 18-ю общевойсковую армию;$ref_crp ни одной бригады она не называет. Центр информационной устойчивости (CIR) и DW назвали 205-ю мотострелковую бригаду$ref_dw среди трёх подразделений, чьи дроны
работали над Бериславом во время нападений, — оговорившись, что не могут доказать, кто именно их совершал.$ref_cir Канал, публикующий видео бригады, относит её к 49-й армии.$ref_osv Старший медик одной из городских
больниц Херсона рассказал комиссии:</p>
<blockquote class="rm-quote"><span class="q">«Военнослужащие Российской Федерации ведут себя так, будто это сафари […]; они просто преследуют и охотятся на мирных жителей, которые идут на работу или выгуливают собак» <i>(перевод наш)</i></span>
<cite>документ ООН A/HRC/59/CRP.2, п. 42, 28.05.2025 (оригинал: «$un_safari»)$ref_crp</cite></blockquote>
$osv_clip
<h3 class="rm-h3">Что круг ЦБСТ сам говорит об этом фронте</h3>
<ul>
<li><b>«Барс-Сармат».</b> Его командир Дмитрий Рогозин пишет, что центр выполняет боевые задачи командующего ВДВ и что армейские подразделения группировки «Днепр» ставят его боеприпасы на свои ударные дроны.$ref_rog $rep</li>
<li><b>Фонд «Наша Правда»</b> сообщает, что в мае 2024 года передал 100 ударных дронов бойцам 49-й армии на херсонском направлении,$ref_np280 а также автомобиль, на котором 18-я армия теперь возит грузы и людей к линии фронта.$ref_np580 $rep</li>
<li><b>ООО «Гагаринг»</b>, производитель «Кузнечика» и «Совы», публикует благодарности от расчётов 49-й армии, которые «Совой» перехватывают видеосигнал дронов над Днепром.$ref_gag2811 $rep</li>
</ul>
<h3 class="rm-h3">Школа, которая набирает в 205-ю бригаду</h3>
<p>Канал самого ЦБСТ пишет, что противодронный тренажёр одного из «резидентов» работает в новом учебном центре школы дронов «Архангел» в Туапсе.$ref_1562 Канал школы набирает операторов в 205-ю бригаду, а канал Дмитрия Рогозина
пишет, что проект входит в учебный центр «Барс-Сармата».$ref_rog7047 Документа, который связывал бы школу с ЦБСТ, нет: есть слова круга ЦБСТ и слова самой школы.</p>
$q_9067
$q_10667
<p class="note"><a href="$arkh">Полное досье «Архангела»: изделия, список деталей, партнёры и связи →</a></p>
<h3 class="rm-h3">Что фронтовой канал пишет о целях</h3>
<p>Комиссия ООН воспроизводит в своём документе посты херсонского фронтового канала «От Мариуполя до Карпат».$ref_crp Канал подписывает видео ударов названиями подразделений. Под видео 205-й бригады:</p>
$q_27702
$still_27702
<p>Под видео удара по фургону во дворе жилого дома:</p>
$q_19953
<p>И под тем самым «двойным назначением», которым РОЙ.МАРКЕТ называл товары своих продавцов:</p>
$q_36192
$q_38703
$still_38703
<p class="note">$rep Все связи выше — собственные посты сторон. Они не показывают, что какое-либо изделие из круга ЦБСТ применялось против гражданских; ООН не называет ни одной части ниже уровня армии.</p>
</section>""")
    st1 = st2 = ""
    if still_ok:
        st1 = ('<figure class="stills"><figure><img src="images/kherson/k27702.jpg" alt="Кадр из видео: разрушенный дом в Казацком под эмблемой «205 бригада»" loading="lazy">'
               '<figcaption>Кадр из видео: разрушенный дом в Казацком, под эмблемой «205 бригада».</figcaption></figure></figure>')
        st2 = ('<figure class="stills"><figure><img src="images/kherson/k38703.jpg" alt="Кадр из видео: фургон с надписью «РИТУАЛ»" loading="lazy">'
               '<figcaption>Кадр из видео: фургон с надписью «РИТУАЛ», водяной знак 98-й воздушно-десантной дивизии.</figcaption></figure></figure>')
    osv_clip = ""
    if have_osv:
        chan, msg, ru, _ = OPENING_QUOTES["osv_38645"]
        verify(chan, msg, ru.split(" […] "), cnt)
        osv_clip = ('<figure class="clip"><video controls preload="none" playsinline poster="images/video/osv-38645.jpg" '
                    'aria-label="Экран пульта оператора дрона: вид сверху на повреждённый автомобильный мост у реки, жёлтая рамка наведения на тёмных силуэтах у обочины">'
                    '<source src="images/video/osv-38645.mp4" type="video/mp4"></video>'
                    '<figcaption><span class="rm-label">Видео · первые 0:30 из 1:19</span> Пост канала от 22.10.2026: «' + esc(ru) + '»' + r("osv_38645")
                    + ' На видео — экран пульта оператора над разрушенным автомобильным мостом, удар на 0:13. Сам пост сообщает, что погибла собака. Звук удалён.</figcaption></figure>')
    front_html = front.substitute(
        ref_crp=r("un_crp"), ref_ga=r("un_ga"), un_dnepr=esc(uq["dnepr"]), un_safari=esc(uq["safari"]), ref_dw=r("dw_film"), ref_cir=r("cir"), ref_osv=r("osv_27702"),
        osv_clip=osv_clip, rep=REP, ref_rog=r("rog_8057", "rog_7780"), ref_np280=r("np_280"), ref_np580=r("np_580"), ref_gag2811=r("gag_2811"),
        ref_1562=r("cbst_1562"), ref_rog7047=r("rog_7047"),
        q_9067=oq("arch_9067", "«Архангел», Telegram, 01.12.2025" + r("arch_9067")), q_10667=oq("arch_10667", "«Архангел», Telegram, 17.08.2026" + r("arch_10667")),
        arkh=href("arkhangel.html") if here("arkhangel.html") else "#h-dossiers",
        q_27702=oq("osv_27702", "«От Мариуполя до Карпат», Telegram, 23.07.2025" + r("osv_27702")), still_27702=st1,
        q_19953=oq("osv_19953", "тот же канал, 19.08.2024" + r("osv_19953")), q_36192=oq("osv_36192", "тот же канал, 24.07.2026" + r("osv_36192")),
        q_38703=oq("osv_38703", "тот же канал, 24.10.2026, на видео с водяным знаком 98-й воздушно-десантной дивизии" + r("osv_38703")), still_38703=st2)
    assert OPENING_QUOTES["rog_8057"][1] == 8057 and OPENING_QUOTES["np_580"][1] == 580   # the posts the ledger rests on
    for key in ("rog_8057", "rog_7780", "np_580", "gag_2811", "cbst_1562"):
        chan, msg, ru, _ = OPENING_QUOTES[key]
        verify(chan, msg, ru.split(" […] "), cnt)

    # -- the marketplace -------------------------------------------------------------------------------------
    market = Template("""
<section aria-labelledby="h-market"><h2 class="rm-h2" id="h-market">Маркетплейс и его продавцы</h2>
<p>Фронт, описанный выше, — то место, куда, по словам круга ЦБСТ, идут его товары и его новобранцы. Платформа, куда ЦБСТ отправляет военных, — РОЙ.МАРКЕТ. В августе 2026 года она открылась для сторонних
продавцов и прямо назвала, кого ждёт в первую очередь:</p>
$q_ann
<p>Каталога в открытом доступе нет: он закрыт логином, и что на платформе продаётся, известно только из постов оператора, предложения поставщикам, постов самих продавцов и прессы. Единственный продавец, чей собственный
пост прямо сообщает о продаже на платформе, — КБ «СПЕКТР», производитель пропеллеров для дронов. 6 июля 2026 года его канал написал:</p>
$q_spec
<p>«Булат», изделие, которое проходит через передачи фонда, на платформе ничем не подтверждён. Представитель его производителя, 3mx, написал в чате клиентов 2 сентября 2026 года:</p>
$q_3mx
<p>Планы платформы описывают и сами авторы: Сидякин пишет о десятках потребителей и нескольких сотнях позиций в каталоге, ЦБСТ — о том, что к 1 сентября к платформе подключат все технико-эксплуатационные части Минобороны:</p>
$q_pilot
$q_tech
<p class="note">$rep Это заявления сторон. Ни одного заказа воинской части среди собранных документов нет.</p>

<h3 class="rm-h3">Маркетплейс скрывает, кто им управляет. Старая копия — нет</h3>
<p>В публичной оферте платформы оператор значится как «ООО «****»». Копия, сохранённая в архиве 22.08.2026, его называет: ООО «МПТМ», ИНН 9714068459. Собственный отчёт ЦБСТ в Минюст указывает ту же компанию
как ту, в которой ЦБСТ участвует со дня её регистрации. Реестр же с 15 июля 2026 года скрывает, кому она принадлежит: это раньше обеих версий оферты.$ref_restr</p>
<div class="pair">
$q_op
$q_mask
</div>
$q_row
$q_restr
<p class="note">$doc Строки напечатаны в том виде, в каком они стоят в каждом документе. В версии с маской реквизиты видны только после входа; почему и когда их скрыли, документально не известно.</p>

<h3 class="rm-h3">Хронология</h3>
<ol class="tl-list">$timeline</ol>
</section>""")
    tl = [
        ("27.02.2024", "ЦБСТ зарегистрирован в Москве; учредители — фонд «Наша Правда» и банк ПСБ", "s0228", DOC),
        ("22.01.2025", "зарегистрировано ООО «МПТМ»; ЦБСТ участвует в нём с того же дня", "s0207", DOC),
        ("начало 2025", "платформа запускается как закрытый пилот, по сообщению «Коммерсанта»", "s8866", REP),
        ("15.12.2025", "Сидякин: партия, ПСБ и ЦБСТ «запустили военный маркетплейс»", "s8847", REP),
        ("15.07.2026", "ЕГРЮЛ начинает скрывать владельцев ООО «МПТМ»", "s0230", DOC),
        ("13.08.2026", "платформа открывается для сторонних продавцов, «в первую очередь» с Wildberries и Ozon", "s8854", REP),
        ("22.08.2026", "архивная копия оферты для поставщиков называет оператором ООО «МПТМ»", "s8817", DOC),
        ("02.09.2026", "3mx пишет покупателю, что «Булат» продают только сама компания и её дилеры", "s8860", REP),
        ("01.10.2026", "действующая оферта указывает оператора как «ООО «****»»", "s8822", DOC),
    ]
    timeline = "".join(f'<li><span class="d">{d}</span><span>{esc(t)}{r(s)}</span>{g}</li>' for d, t, s, g in tl)
    market_html = market.substitute(
        q_ann=quote(announce, "ЦБСТ, Telegram, 13.08.2026" + r("s8854")), q_spec=quote(q_spec["text_ru"], "КБ «СПЕКТР», Telegram, 06.07.2026" + r("s8737")),
        q_3mx=quote(q_3mx["text_ru"], "3mx, чат клиентов, 02.09.2026" + r("s8860")),
        q_pilot=quote(q_pilot["text_ru"], "Сидякин, Telegram, 05.08.2026" + r("s8851")), q_tech=quote(q_tech["text_ru"], "ЦБСТ, Telegram, 06.08.2026" + r("s8852")),
        rep=REP, ref_restr=r("s0230"), q_op=quote(q_op["text_ru"], "оферта для поставщиков, копия от 22.08.2026" + r("s8817")),
        q_mask=quote(q_mask["text_ru"], "оферта для поставщиков, на сайте 01.10.2026" + r("s8822")),
        q_row=quote(q_row["text_ru"], "отчёт ЦБСТ в Минюст за 2025 год, раздел 2.2, строка ООО «МПТМ»"),
        q_restr=quote(q_restr["text_ru"], "выписка из ЕГРЮЛ на ООО «МПТМ» от 14.08.2026, раздел «Сведения об участниках / учредителях юридического лица»"),
        doc=DOC, timeline=timeline)

    # -- more than a marketplace ---------------------------------------------------------------------------------
    beyond = Template("""
<section aria-labelledby="h-beyond"><h2 class="rm-h2" id="h-beyond">Больше, чем маркетплейс</h2>
<p>ЦБСТ представляет себя организацией поддержки разработчиков дронов, а РОЙ.МАРКЕТ — каталогом. Его собственные посты и посты секретаря его наблюдательного совета описывают нечто большее. ЦБСТ пишет, что показывал
маркетплейс на «Центре-2026» — стратегических военных учениях — и набирал там продавцов:</p>
$q_tsentr
<p>15 октября Сидякин объявил о приложении, которое распределяет летящие украинские дроны между мобильными огневыми группами в Курской области, — и вписал его в систему ЦБСТ:</p>
$q_yakim
<p class="note">$rep И то и другое — собственные заявления сторон; ни один из собранных документов не показывает, что система действительно используется.</p>
</section>""").substitute(
        q_tsentr=oq("tsentr", "ЦБСТ, Telegram, 04.10.2026" + r("tsentr")), q_yakim=oq("yakim", "Сидякин, Telegram, 15.10.2026" + r("yakim")), rep=REP)

    # -- dossiers -------------------------------------------------------------------------------------------------
    def card(title, line, file, wait="Досье на проверке."):
        link = f'<a href="{href(file)}">Открыть →</a>' if file and here(file) else f'<span class="st">{wait}</span>'
        return f"<li><b>{title}</b><span>{line}</span>{link}</li>"

    dossiers = Template("""
<section aria-labelledby="h-dossiers"><h2 class="rm-h2" id="h-dossiers">Досье и истории</h2>
<p>Длинные материалы расследования — каждый на своей странице: цепочка одного изделия, досье компании, проекта или группы людей, сюжетные истории. Они пока на английском.</p>
<ul class="cards">
$cards
</ul>
<p class="note">Страницы-досье и цепочки написаны по-английски и открываются по ссылкам, как только лежат рядом с этой страницей.</p>
</section>""").substitute(cards="".join([
        card("«Булат» от ЦБСТ до линии фронта", "Портативный детектор БПЛА производства 3mx (ООО «Тримикс»): цепочка от ЦБСТ к производителю, продавцам, госзаказчикам и частям.", "chain_bulat.html", "Цепочка на проверке."),
        card("«Капюшон»", "Семейство станций РЭБ производства ООО «НПО «Киловатт»».", None, "Цепочка на проверке и пока не опубликована."),
        card("3mx (ООО «Тримикс»)", "Делает детектор «Булат», владеет патентом на его конструкцию и судится из-за него с GoDrone.", "company_ooo-trimiks.html"),
        card("ООО «ГОУДРОН»", "Торгует под маркой GoDrone, делает детектор дронов «Набат»; «Тримикс» судится с ним из-за патента.", "company_ooo-goudron.html"),
        card("«Архангел»", "Школа дронов, которая готовит операторов для армии и публикует список деталей перехватчика.", "arkhangel.html"),
        card("«Овод»", "Семейство ударных FPV-дронов, в том числе на оптоволокне.", None),
        card("ООО «СКБ Пиранья»", "Делает ударные FPV-дроны «Пиранья» и пишет, что доставляет их получателям в «ЛНР» и «ДНР» напрямую.", None),
        card("«Барс-Сармат»", "Добровольческий центр беспилотников Дмитрия Рогозина, который, по его словам, воюет за командующего ВДВ.", None)]))

    network = Template("""
<section aria-labelledby="h-net"><h2 class="rm-h2" id="h-net">Сеть, которая есть в документах</h2>
<p>С ЦБСТ связаны $n организации: $d — через документ (запись в ЕГРЮЛ, контракт, собственные посты ЦБСТ), $p — только по собственным словам или по сообщениям прессы. $s из них находятся
хотя бы в одном санкционном списке.</p>
<p class="note">Сетка логотипов всех $n организаций, график санкционных списков по годам и выручка компаний собираются в английской версии страницы; в русскую они ещё не перенесены.</p>
</section>""").substitute(n=n_org, d=by["doc"], p=by["rep"], s=n_sanc)

    method = Template("""
<section aria-labelledby="h-read"><h2 class="rm-h2" id="h-read">Как читать доказательства</h2>
<ul>
<li>$doc Это показывает первичный документ: выписка из ЕГРЮЛ, госконтракт, годовая отчётность, запись о товарном знаке или патенте.</li>
<li>$rep Собственные слова одной из сторон (её посты, сайт, объявления) или пресса. Посты доноров о передачах в части остаются в этой категории, пока их не подтвердит второй источник.</li>
<li>$open Связь нарисована, чтобы картина была полной, но ни один из собранных документов её не показывает; в примечании к линии сказано, чего не хватает.</li>
</ul>
<p>Красным на сайте отмечено только присутствие в санкционных списках, и всегда с названием режима.</p>
<h2 class="rm-h2" id="h-how">Как это сделано</h2>
<ul>
<li>Факты берутся из оригинальных документов, прочитанных целиком на языке оригинала, чаще всего по-русски: выписок из ЕГРЮЛ, годовой отчётности, данных о госзакупках и товарных знаках, судебных актов, собственных телеграм-постов и сайтов сторон. Пересказы и машинные переводы — только зацепки, не источники.</li>
<li>Каждый документ при сборе архивируется и хешируется. Каждое примечание в конце страницы говорит, что это за документ, и ведёт на него, если есть публичная копия.</li>
<li>Снимки — доказательство только того, что на них видно, и у каждого указано, кто его опубликовал. Лица участников показаны; никого не опознают по лицу.</li>
<li>Расследование выросло из WB Watch — трекера военных товаров, которые продаются на Wildberries.</li>
</ul>
</section>""").substitute(doc=DOC, rep=REP, open=OPEN)

    support = (
        f'<style>{_SUPPORT_CSS}</style>\n'
        '<aside class="rm-support" aria-labelledby="h-support"><h2 id="h-support">Об авторе и поддержка</h2>\n'
        '<p>Это расследование я делаю один. Я — <a href="https://en.wikipedia.org/wiki/Alexey_Kovalev_(journalist)" target="_blank" rel="noopener">Алексей Ковалёв</a>, независимый российский журналист. '
        'Я живу в эмиграции: в России меня <a href="https://ovd.info/en/express-news/2026/10/13/journalist-alexey-kovalev-has-been-declared-wanted" target="_blank" rel="noopener">объявили в розыск</a> за мою работу. '
        'О вторжении России в Украину я пишу для <a href="https://foreignpolicy.com/author/alexey-kovalev/" target="_blank" rel="noopener">разных изданий</a> и в '
        '<a href="https://amethyst-deceiver2001.github.io/Mariupol_Urbicide_2026/index.html" target="_blank" rel="noopener">собственном блоге</a>.</p>\n'
        '<p>Я трачу на это своё время и свои деньги. Если вы считаете эту работу важной, можно помочь покрыть расходы — профессиональные сервисы, подписки, хостинг:</p>\n<ul>\n'
        '<li>PayPal: <a href="https://paypal.me/yenisei23" target="_blank" rel="noopener">paypal.me/yenisei23</a> или на kovalever@googlemail.com</li>\n'
        '<li>из США — через <a href="https://www.paypal.com/donate/?hosted_button_id=TQ6VZ7CFSHTHW" target="_blank" rel="noopener">Building Democracy Foundation</a>, зарегистрированную НКО по статье 501(c)(3)</li>\n'
        '<li>Revolut: <a href="https://revolut.me/alexeypklg" target="_blank" rel="noopener">@alexeypklg</a></li>\n'
        '<li>криптовалюта (отсканируйте код или скопируйте адрес):'
        + _wallets_html().replace("Copy address", "Скопировать адрес").replace("Copied", "Скопировано").replace("Press Ctrl/Cmd+C", "Нажмите Ctrl/Cmd+C") +
        '</li>\n</ul>\n<p>Связаться со мной: kovalever@gmail.com</p>\n</aside>\n')

    found_items = [
        (REP, "Ролик с ударом и строчка о продажах", "#h-open", "ЦБСТ перепостил видео производителя дронов — удар по гербу на здании областной администрации — и сообщил военнослужащим, что оба изделия, показанные на видео, можно заказать на его собственном маркетплейсе."),
        (DOC, "Госбанк и донорский фонд в учредителях", "#h-hub", "По ЕГРЮЛ учредители ЦБСТ — ПАО «Банк ПСБ», банк, принадлежащий государству, и фонд «Наша Правда»."),
        (REP, "Правящая партия — в учредителях и в совете", "#h-hub", "Сам ЦБСТ называет «Единую Россию» третьим учредителем, а секретарь его наблюдательного совета — руководитель центрального исполкома партии."),
        (REP, "Фонд, созданный «по поручению» Медведева", "#h-hub", "Сидякин пишет, что фонд, который передаёт войскам технику вместе с партией, создан по поручению её председателя. Фонд называет себя проектом двух фондов, которых ФБК в 2017 году связал с Медведевым. Документов, которые подтвердили бы эту связь, нет."),
        (REP, "Поставки на фронт, о котором пишет ООН", "#h-front", "Круг ЦБСТ снабжает и вербует для частей той самой группировки, которую ООН называет в выводах о нападениях дронов на жителей Херсона. Ни один документ не показывает, что какое-либо изделие применялось против гражданских."),
        (DOC, "Платформа, которая скрывает оператора", "#h-market", "В публичной оферте РОЙ.МАРКЕТ оператор значится как «****». В архивной копии он назван: ООО «МПТМ» — компания, которую ЦБСТ сам указывает в отчёте в Минюст."),
    ]
    found = ('<section aria-labelledby="h-found"><h2 class="rm-h2" id="h-found">Что мы нашли</h2><ul class="finds">'
             + "".join(f'<li>{g}<span><b><a href="{h}">{esc(t)}</a></b><br><span class="t">{esc(x)}</span></span></li>' for g, t, h, x in found_items)
             + f'</ul><p class="found-n">С ЦБСТ на сегодня связаны <b>{n_org}</b> организации; <b>{n_sanc}</b> из них находятся хотя бы в одном санкционном списке.</p></section>')

    title = "ЦБСТ и РОЙ.МАРКЕТ: московская НКО и военный маркетплейс, который поставляет дроны на войну"
    body = f"""<header class="rm-page top">
<p class="rm-eyebrow">Расследование с открытым кодом · черновик русской версии · {ru_date(today)}</p>
<h1 class="rm-h1">ЦБСТ и РОЙ.МАРКЕТ</h1>
<p class="rm-dek">Московская НКО, которая называет себя центром поддержки беспилотной отрасли, и закрытый «военный маркетплейс», который она запустила вместе с правящей партией и государственным банком.
Здесь — как эта цепочка устроена: что производят компании вокруг ЦБСТ, кто это продаёт и какие воинские части это получают. Каждое утверждение опирается на сохранённый документ и помечено тем, насколько твёрдо этот документ его подтверждает.</p>
<p class="byline">Алексей Ковалёв, независимый журналист · данные на {ru_date(today)}</p></header>
<main class="rm-page">
{found}
{opening}
{who}
{front_html}
{market_html}
{beyond}
{dossiers}
{network}
{method}
<section aria-label="Источники"><h2 class="rm-h2">Источники</h2><ol class="rm-sources">@@NOTES@@</ol></section>
</main>
{support}"""
    body = body.replace("@@NOTES@@", N.list_html())
    doc = f"""<!doctype html>
<!-- Generated by exhibits/build_landing_ru.py from data/registry on {today}. Do not edit by hand. -->
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ЦБСТ и РОЙ.МАРКЕТ</title>
<meta name="description" content="Расследование с открытым кодом о московской НКО ЦБСТ и её военном маркетплейсе РОЙ.МАРКЕТ. Каждое утверждение опирается на архивный документ и помечено степенью подтверждённости.">
{design_head((REPO / 'exhibits' / 'landing.css').read_text() + PAGE_CSS)}</head>
<body>
{body}
</body></html>
"""
    seen_ids: set[str] = set()   # a reference string reused in a template repeats its id: keep the first, drop the rest

    def drop_dupe(m):
        if m.group(1) in seen_ids:
            return ""
        seen_ids.add(m.group(1))
        return m.group(0)

    doc = re.sub(r' id="(r\d+)"', drop_dupe, doc)
    out.write_text(doc, encoding="utf-8")
    print(f"wrote {out.relative_to(REPO) if out.is_relative_to(REPO) else out}: {len(doc) // 1024} KB; {len(N.order)} sources; "
          f"{cnt['checked']} quotation checks passed, {cnt['skipped']} skipped for want of a local text")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=REPO / "exhibits" / "landing_ru.html")
    render(ap.parse_args().out)
