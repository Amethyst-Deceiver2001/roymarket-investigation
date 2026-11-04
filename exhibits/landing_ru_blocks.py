"""The generated blocks of the Russian landing: ties diagram, logo wall, sanctions grid, revenue bars, front map.

They reuse the English landing's data and geometry (build_landing.Landing) and set the text in Russian. Every fixed
English string is replaced through a table that is asserted to match, so a changed English template fails here rather
than leaving English on the page. Footnotes go through the Russian page's own Notes (`ref`).
"""
from __future__ import annotations

import html
import re
import json
import datetime as dt
from pathlib import Path

from build_landing import Landing, CBST, NP, PSB, MPTM, REPO
from display_helpers import display_name, sanction_regimes, guillemets

esc = html.escape

REGIME_RU = {"Ukraine": "Украина", "US": "США", "UK": "Великобритания", "EU": "ЕС", "Switzerland": "Швейцария", "Canada": "Канада",
             "Australia": "Австралия", "New Zealand": "Новая Зеландия", "Japan": "Япония"}
TIER_RU = {"TsBST and its core": "ЦБСТ и его ядро", "Money": "Деньги", "Partners, institutions and services": "Партнёры, институты и сервисы",
           "Makers": "Производители", "Other": "Прочие"}


def money_ru(v):
    if v is None:
        return ""
    if v >= 1e9:
        return f"₽{v / 1e9:.2f}".replace(".", ",") + " млрд"
    return f"₽{v / 1e6:.1f}".replace(".", ",") + " млн"


def replace_all(s: str, table: dict[str, str], what: str, tail: str = "</text>") -> str:
    """Replace each `>English<` text node; fail if one is missing."""
    for en, ru in table.items():
        needle = f">{esc(en, quote=False)}{tail}"
        if needle not in s:
            raise SystemExit(f"{what}: English string not found: {en!r}")
        s = s.replace(needle, f">{esc(ru, quote=False)}{tail}")
    return s


class LandingRu(Landing):
    # -- ties diagram ---------------------------------------------------------------------
    def ties_ru(self, notes_ref):
        svg = super().ties_diagram()
        nh = len([d for d in self.p.get("deliveries") or [] if d.get("donor") == NP])
        names = {display_name(self.ents[s])["latin"]: ru for s, ru in
                 ((NP, "Наша Правда"), (PSB, "Банк ПСБ"), (CBST, "ЦБСТ"), (MPTM, "МПТМ"))}
        table = {**names, "ROI.MARKET": "РОЙ.МАРКЕТ", "donor foundation": "донорский фонд", "state-owned bank": "госбанк",
                 "ruling party": "правящая партия", "non-profit, Moscow": "НКО, Москва", "board secretary": "секретарь совета",
                 "Military units": "Воинские части", "recipients": "получатели", "company": "компания",
                 "login-only catalogue": "каталог по логину", "United Russia": "Единая Россия", "Aleksandr Sidyakin": "Александр Сидякин",
                 "co-founder": "учредитель", "named by TsBST as a founder": "учредитель по словам ЦБСТ", "sits on its board": "в наблюдательном совете",
                 "heads its central committee": "руководит исполкомом", "takes part; share not stated": "участвует; доля не названа",
                 "operates": "оператор", "says units order": "заказ частей", "here directly": "напрямую",
                 f"hands equipment to units: {nh} «Bulat» handovers posted": f"передаёт технику частям: {nh} постов о передаче «Булата»"}
        # "co-founder" is drawn twice
        n_co = svg.count(">co-founder</text>")
        assert n_co == 2, n_co
        svg = svg.replace(">co-founder</text>", ">учредитель</text>")
        table.pop("co-founder")
        svg = replace_all(svg, table, "ties diagram")
        svg = re.sub(r'aria-label="Who is tied to TsBST[^"]*"',
                     'aria-label="С кем связан ЦБСТ: его учредители, секретарь наблюдательного совета, компания, в которой он участвует, '
                     'и передачи фонда частям"', svg, count=1)
        arms = getattr(self, "_arm_names", [])
        arm_ru = {"army and motor-rifle (and reconnaissance)": ("сухопутные и мотострелковые (и разведывательные)", "emb_sv"),
                  "airborne and air-assault": ("воздушно-десантные и десантно-штурмовые", "emb_vdv"),
                  "special forces": ("спецназ", "emb_gru")}
        kinds = []
        for en_name, (ru_name, key) in arm_ru.items():
            if any(a.startswith(en_name) for a in arms):
                kinds.append(ru_name + notes_ref(key))
        cap = ('<figcaption>Стиль линии показывает, насколько твёрдо подтверждена связь, — как в ключе внизу страницы. Пояснения к каждой линии — в списке ниже. '
               'Эмблемы под «Воинскими частями» обозначают, какие части называют в постах получателями: ' + ", ".join(kinds) + '. '
               'Они не показывают, какая часть что получила. Рисунки: Сидякин — фото Karmaks, 2016, CC BY-SA 4.0' + notes_ref("sid_photo") +
               '; логотип партии' + notes_ref("er_logo") + '; логотип РОЙ.МАРКЕТ с сайта платформы' + notes_ref("rm_logo") + '.</figcaption>')
        svg, k = re.subn(r"<figcaption>.*?</figcaption>", lambda m: cap, svg, count=1, flags=re.S)
        assert k == 1
        return svg

    # -- logo wall ------------------------------------------------------------------------
    def city_ru(self, e):
        m = re.search(r"г\.\s*((?:[А-ЯЁ][а-яё-]+)(?:\s[А-ЯЁ][а-яё]+)?)", e.get("address") or "")
        return m.group(1) if m else e.get("city")

    def wall_ru(self, tile_link):
        where_en = self.namesakes()
        where = {}
        for s, v in where_en.items():
            e = self.ents[s]
            if v == "no registered company on file":
                where[s] = "юрлица в реестре нет"
            elif v.startswith("INN "):
                where[s] = "ИНН " + v[4:]
            else:
                where[s] = self.city_ru(e) or v
        groups = []
        for tiers, label in self.TIER_ORDER:
            slugs = [s for s in self.tied() if self.ents.get(s, {}).get("tier") in tiers]
            if not slugs:
                continue
            slugs.sort(key=lambda s: (not self.logo(s), not sanction_regimes(self.ents[s].get("sanctions")),
                                      display_name(self.ents[s])["head"].lower().replace("ё", "е")))
            tiles = []
            for s in slugs:
                e = self.ents[s]
                n = display_name(e)
                regs = [lab for lab, _ in sanction_regimes(e.get("sanctions"))]
                logo = re.sub(r'alt="[^"]*"', f'alt="Логотип: {esc(n["head"])}"', self.logo(s))
                flag = f'<span class="rm-sanction">Под санкциями: <b>{esc(", ".join(regs))}</b></span>' if regs else ""
                go = tile_link(s)
                brand = f'<span class="br">{esc(n["head"])}</span>' if n["legal"] else ""
                legal = n["legal"] or n["head"]
                sub = f'<small class="tw">{esc(where[s])}</small>' if s in where else ""
                tiles.append(f'<li class="tile{" has-logo" if logo else ""}">{logo}<span class="tn">{brand}'
                             f'<small class="cyr" lang="ru">{esc(legal)}</small>{sub}</span>{go}{flag}</li>')
            groups.append(f'<div class="wall-g"><h3 class="rm-label">{esc(TIER_RU[label])} · {len(slugs)}</h3><ul class="wall">{"".join(tiles)}</ul></div>')
        return "".join(groups)

    # -- sanctions grid -------------------------------------------------------------------
    def grid_ru(self):
        svg, undated = self.sanctions_grid()
        for en, ru in REGIME_RU.items():
            svg = svg.replace(f'>{en}</text>', f'>{ru}</text>')
        assert "Linked organisations first listed" in svg
        svg = svg.replace('aria-label="Linked organisations first listed, by regime and year"',
                          'aria-label="Организации, связанные с ЦБСТ: когда их впервые внесли в списки, по режимам и годам"')
        return svg, undated

    # -- revenue --------------------------------------------------------------------------
    def revenue_ru(self, notes_ref):
        rows = []
        for s in self.tied():
            fs = {int(f["year"]): f for f in self.ents[s].get("financials") or []
                  if f.get("revenue") and (s, int(f["year"])) not in self.HELD_YEARS}
            if fs:
                y = max(fs)
                rows.append((fs[y]["revenue"], y, s, fs[y].get("source_id"), fs.get(y - 1, {}).get("revenue")))
        rows.sort(reverse=True)

        def panel(rs, title):
            top = max(max(r[0], r[4] or 0) for r in rs)
            bars = []
            for v, y, s, sid, prev in rs:
                filed = (self.src.get(sid, {}).get("title") or "").startswith("Annual accounts filed")
                pw = f'<span class="prev" style="width:{100 * prev / top:.1f}%" title="{y - 1}: {money_ru(prev)}"></span>' if prev else ""
                nm = display_name(self.ents[s])["head"]
                bars.append(f'<li><span class="bn" title="{esc(nm)}" lang="ru">{esc(nm)}</span><span class="bt">{pw}'
                            f'<span class="cur{"" if filed else " rep"}" style="width:{100 * v / top:.1f}%"></span></span>'
                            f'<span class="bv">{money_ru(v)} <small>{y}</small>'
                            + ("" if filed else ' <span class="rm-grade rep">Со слов прессы</span>') + f'{notes_ref(sid)}</span></li>')
            return f'<div class="rv-p"><h3 class="rm-label">{esc(title)}</h3><ol class="rv">{"".join(bars)}</ol></div>'
        big = [r for r in rows if r[0] >= 10e9]
        rest = [r for r in rows if r[0] < 10e9][:10]
        return (panel(big, f"Больше ₽10 млрд · {len(big)}") if big else "") + panel(rest, "Следующие десять"), len(rows)

    # -- front map ------------------------------------------------------------------------
    MAP = {"Dnipro": "Днепр", "Kherson": "Херсон", "Hola Prystan": "Голая Пристань", "Oleshky": "Алешки", "Nova Kakhovka": "Новая Каховка",
           "Beryslav": "Берислав", "205th brigade": "205-я бригада", "49th Army HQ": "штаб 49-й армии",
           "331st (98th Div.)": "331-й (98-я див.)", "217th (98th Div.)": "217-й (98-я див.)", "299th (98th Div.)": "299-й (98-я див.)",
           "205th motor-rifle brigade": "205-я мотострелковая бригада",
           "DeepState's marker. DW and the CIR say its drones": "Метка DeepState. DW и CIR пишут, что её дроны",
           "worked over Beryslav; they could not prove who fired": "работали над Бериславом; кто стрелял, не доказано",
           "49th Army": "49-я армия",
           "DeepState's marker for its headquarters. A channel": "Метка DeepState для штаба. Канал, публикующий",
           "that posts the 205th's footage places the brigade in it": "видео 205-й бригады, относит бригаду к этой армии",
           "98th Airborne Division": "98-я воздушно-десантная дивизия",
           "Three of its regiments as DeepState marks them; the": "Три её полка по меткам DeepState; в ролике",
           "channel's 24.10.2026 clip carries the division's watermark": "канала от 24.10.2026 стоит водяной знак дивизии",
           "18th Combined Arms Army": "18-я общевойсковая армия", "Named in the UN's May 2025 paper": "Названа в майском докладе ООН 2025 года",
           "Red: Russian-held, 23.10.2026. Diamonds: unit markers (X brigade, III regiment, XXXX army headquarters). Map and markers: DeepState; river: Natural Earth":
               "Красным — занятая российскими войсками территория на 23.10.2026. Ромбы — метки частей (X — бригада, III — полк, XXXX — штаб армии). Карта и метки: DeepState; река: Natural Earth"}

    def map_ru(self, notes_ref):
        p = REPO / "exhibits" / "images" / "maps" / "kherson-front.svg"
        if not p.exists():
            return ""
        svg = p.read_text()
        svg = replace_all(svg, self.MAP, "front map")
        svg, k = re.subn(r'aria-label="Map of the Kherson area[^"]*"',
                         'aria-label="Карта района Херсона и левого берега Днепра: занятая российскими войсками территория на 23.10.2026"', svg, count=1)
        assert k == 1
        return ('<figure class="front-map-fig"><div class="front-map-wrap">' + svg + '</div><figcaption>Карта собрана из данных DeepState'
                + notes_ref("deepstate") + '; ход реки взят из набора Natural Earth' + notes_ref("natural_earth") +
                '. Метки показывают, где источники помещают части, и не говорят о том, кто именно стрелял.</figcaption></figure>')


# =====================================================================================================================
# The page's own structure, as on the English landing: strike-to-order strip with screenshots, ledger lists, timeline,
# picture bands that open a viewer. Text is Russian; geometry and data come from the English methods.
# =====================================================================================================================
from build_landing import ln, KHERSON_STILLS, CENTER_STILLS, MORE, FILE_LINES, CHAINS, OPENING_SOURCES  # noqa: E402
from build_chain_view import Chain  # noqa: E402
from display_helpers import ru_date, media_about, publish_copy  # noqa: E402

PROV_RU = {"self": "Опубликовано: {who}", "third_party": "Опубликовано третьей стороной", "platform": "Из объявления на маркетплейсе",
           "press": "Из прессы", "counterparty": "От контрагента", "regulator": "От регулятора", "investigator": "Наш снимок"}
GRADE_RU = {"doc": "Документ", "rep": "Со слов сторон", "open": "Не подтверждено"}

SHOTS_RU = [
    ("opening/ukrinform-zaporizhzhia-ova.jpg", "Укринформ, 08.10.2026",
     "Скриншот статьи «Укринформа» «Ворог вдарив дроном по будівлі Запорізької ОВА» (8 октября 2026 года) с фотографией фасада здания.", "ukrinform"),
    ("video/gagaring-5142.jpg", "Видео «Гагаринга», 19.10.2026",
     "Кадр из видео «Гагаринга»: здание администрации сверху, до того как дрон влетает в кадр.", "gag"),
    ("opening/tsbst-post-2677.jpg", "Пост ЦБСТ, 20.10.2026",
     "Скриншот телеграм-поста ЦБСТ от 20 октября 2026 года: то же видео, заголовок «Тризуб отклеился» и строчка о продаже.", "cbst"),
    ("opening/roymarket-supplier-page.jpg", "Публичная страница РОЙ.МАРКЕТ, 24.10.2026",
     "Скриншот публичной страницы РОЙ.МАРКЕТ для будущих продавцов в том виде, как она выглядела 24 октября 2026 года. Сам каталог закрыт логином.", "rm_now"),
]

KH_RU = {   # key: (what the frame shows, Russian, as in KHERSON_STILLS)
    "osv_27702": "Кадр из видео: разрушенный дом в Казацком, под эмблемой «205 бригада».",
    "osv_38703": "Кадр из видео: фургон с надписью «РИТУАЛ» (ритуальные услуги), с водяным знаком 98-й воздушно-десантной дивизии.",
}
CENTER_RU = ["Стенд ЦБСТ на «Центре-2026».", "Печатные буклеты и нашивка РОЙ.МАРКЕТ."]

CAP_RU = {   # Russian captions for pictures whose registry description is written in English (our own analyst notes, translated)
    "m0014": "Стенд СКБ «Пиранья» на «Интерполитехе-2025»: фирменный баннер и изделия на выставочном столе.",
    "m0040": "Фото изделия против дронов с маркировкой «НПО КИЛОВАТТ» с официального сайта компании.",
    "m0074": "Несколько человек несут зелёный ящик у входа в тёмное здание; на ящике надпись «ВСЕ ДЛЯ ФРОНТА / ВСЕ ДЛЯ ПОБЕДЫ!!», знак «Единой России», эмблема «Нашей Правды» и логотип ЦБСТ. Два лица размыты самим издателем.",
    "m0077": "Трое вооружённых мужчин в камуфляже возле картонных коробок и зелёного предмета в форме тарелки; на коробках надпись «ВСЕ ДЛЯ ФРОНТА / ВСЕ ДЛЯ ПОБЕДЫ!!», знак «Единой России», эмблема «Нашей Правды» и логотип ЦБСТ.",
}
DOC_RU = {"doc": "Документ", "rep": "Со слов сторон", "open": "Не подтверждено"}


def cap_ru(m):
    text = CAP_RU.get(m["id"]) or m.get("caption_ru") or m["shows"]
    if not re.search(r"[А-Яа-яЁё]", text):
        raise SystemExit(f"no Russian caption for {m['id']}: {text[:60]}")
    return text


def _copy(src: Path, dest: Path):
    if dest != src:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(src.read_bytes())


class Page(LandingRu):
    """Landing_ru's structure. `N` is the Russian page's footnote counter (set by the builder)."""
    N = None
    verify = None   # set by the builder: verify(chan, msg, parts)

    def ref(self, *keys):
        keys = [k for k in keys if k]
        return self.N.ref(*keys) if keys else ""

    def tref(self, key):
        return self.N.ref(key)

    # -- pictures ----------------------------------------------------------------------------------
    def fig_ru(self, m, img):
        who = next((display_name(self.ents[a["id"]])["head"] for a in m.get("about") or [] if a["type"] == "entity" and a["id"] in self.ents), "")
        prov = PROV_RU.get(m.get("asserted_by"), "Источник").format(who=who)
        when = ru_date(m.get("published")) or ""
        return (f'<figure class="rm-fig"><div class="frame"><img src="{esc(img)}" alt="{esc(cap_ru(m))}"></div><figcaption>'
                f'<span class="rm-prov">{esc(prov)}</span><span lang="ru">{esc(cap_ru(m))}{self.ref(m.get("source_id"))}</span>'
                + (f'<span class="when">{when}</span>' if when else "") + "</figcaption></figure>")

    def template(self, m):
        if m["id"] not in self.templates:
            self.templates[m["id"]] = self.fig_ru(m, self.img(m))

    def band_ru(self, ms, label, big=3, limit=9, owners=False):
        if not ms:
            return ""
        tiles, sids = [], []
        for i, m in enumerate(ms):
            self.template(m)
            if m.get("source_id") not in sids:
                sids.append(m.get("source_id"))
            when = ru_date(m.get("published"))
            cap = self.tile_label(cap_ru(m), when)
            if owners:
                ent = next((self.ents[a["id"]] for a in m["about"] if a["type"] == "entity" and a["id"] in self.ents), None)
                if ent:
                    cap = f"{display_name(ent)['head']}: {cap}"
            tiles.append(self.tile(f"fig-{m['id']}", self.img(m), cap_ru(m), cap, big=i < big))
        shown, rest = tiles[:limit], tiles[limit:]
        more = (f'<details class="more"><summary>Показать все {len(tiles)} картинок</summary>'
                f'<div class="band-grid">{"".join(rest)}</div></details>') if rest else ""
        return (f'<figure class="band"><div class="band-grid">{"".join(shown)}</div>{more}'
                f'<figcaption><span class="rm-label">Картинки · {len(ms)}</span> {label} Каждая открывается с подписью, датой и источником.'
                f'{self.ref(*sids)}</figcaption></figure>')

    @staticmethod
    def tile_label(text, when=None):
        first = re.split(r"(?<=[а-яa-z0-9\)”»])[.;:] ", text.strip(), 1)[0].rstrip(".")
        first = first if len(first) <= 60 else first[:58].rsplit(" ", 1)[0].rstrip(" ,;:-") + "…"
        return f"{first}, {when}" if when else first

    def shot(self, i):
        name, label, shows, key = SHOTS_RU[i]
        src_dir, dest = REPO / "exhibits" / "images", self.img_dir.parent
        rel = f"images/{name}"
        _copy(src_dir / name, dest / name)
        self.templates[f"o{i}"] = (
            f'<figure class="rm-fig"><div class="frame"><img src="{esc(rel)}" alt="{esc(shows)}"></div><figcaption>'
            f'<span class="rm-prov">Снимок экрана от 24.10.2026</span><span>{esc(shows)}{self.tref(key)}</span></figcaption></figure>')
        return (f'<button class="shot" type="button" data-fig="fig-o{i}" aria-label="{esc(shows)}">'
                f'<img src="{esc(rel)}" alt=""><span class="cap">{esc(label)}</span></button>')

    def flow_ru(self, nodes, joins):
        flow = []
        for i, (d, who, what, g) in enumerate(nodes):
            flow.append(f'<li class="node{" last" if i == len(nodes) - 1 else ""}">{self.shot(i)}<span class="d">{esc(d)}</span>'
                        f'<span class="who">{esc(who)}</span><span class="what">{esc(what)}</span>'
                        f'<span class="rm-grade {g}">{GRADE_RU[g]}</span></li>')
            if i < len(joins):
                gj, lab = joins[i]
                flow.append(f'<li class="join" aria-hidden="true">{ln(gj, 44)}<span>{esc(lab)}</span></li>')
        return "".join(flow)

    def kstill_ru(self, key):
        msg, name, _, ru, _ = KHERSON_STILLS[key]
        src_dir, dest = REPO / "exhibits" / "images" / "kherson", self.img_dir.parent / "kherson"
        if not (src_dir / name).exists():
            return ""
        _copy(src_dir / name, dest / name)
        rel = f"images/kherson/{name}"
        shows = KH_RU[key]
        when = OPENING_SOURCES[key][0].rsplit(", ", 1)[-1]
        self.templates[f"k{msg}"] = (
            f'<figure class="rm-fig"><div class="frame"><img src="{esc(rel)}" alt="{esc(shows)}"></div><figcaption>'
            f'<span class="rm-prov">Опубликовано каналом «От Мариуполя до Карпат»</span><span>{esc(shows)} Пост: «<span lang="ru">{esc(ru)}</span>»'
            f'{self.tref(key)}</span><span class="orig">Кадр из видео. Оригинал в Telegram, хранится в нашей собственной записи канала.</span>'
            f'<span class="when">{esc(when)}</span></figcaption></figure>')
        t = self.tile(f"fig-k{msg}", rel, shows, self.tile_label(shows.split(" Кадр")[0], when), big=True, contain=(name == "k27702.jpg"))
        return f'<figure class="band kstill"><div class="band-grid">{t}</div><figcaption>{esc(shows)}</figcaption></figure>'

    def center_ru(self):
        src_dir, dest = REPO / "exhibits" / "images" / "center2026", self.img_dir.parent / "center2026"
        tiles = []
        for n, ((name, _, _), shows) in enumerate(zip(CENTER_STILLS, CENTER_RU), 1):
            if not (src_dir / name).exists():
                continue
            _copy(src_dir / name, dest / name)
            rel = f"images/center2026/{name}"
            self.templates[f"c{n}"] = (
                f'<figure class="rm-fig"><div class="frame"><img src="{esc(rel)}" alt="{esc(shows)}"></div><figcaption>'
                f'<span class="rm-prov">Опубликовано самим ЦБСТ</span><span>{esc(shows)}{self.tref("tsentr_pics")}</span>'
                f'<span class="when">04.10.2026</span></figcaption></figure>')
            tiles.append(self.tile(f"fig-c{n}", rel, shows, self.tile_label(shows, "04.10.2026"), big=True))
        return f'<figure class="band"><div class="band-grid">{"".join(tiles)}</div></figure>' if tiles else ""

    def offer_ru(self):
        name = "opening/offer-collage-ru.png"
        src_dir = REPO / "exhibits" / "images"
        if not (src_dir / name).exists():
            return ""
        _copy(src_dir / name, self.img_dir.parent / name)
        return ('<figure class="rm-fig"><div class="frame"><img src="images/opening/offer-collage-ru.png" alt="Оферта для поставщиков в архивной копии от 22 августа 2026 года '
                'рядом с нашим снимком от 25 октября 2026 года; изменившиеся строки подсвечены"></div><figcaption>'
                '<span class="rm-prov">Склейка двух снимков</span><span>Та же оферта, редакция 3.0: архивная копия от 22.08.2026 и наш снимок от 25.10.2026. '
                'Жёлтым — было на странице в августе и пропало к октябрю. Синим — появилось в октябре. Зелёным — осталось открытым.'
                + self.ref("s8817") + self.ref("s8822") + self.tref("privacy") + '</span></figcaption></figure>')

    # -- ledger --------------------------------------------------------------------------------------
    def ledger_ru(self):
        rows = self.ledger_rows()
        nm = lambda s: display_name(self.ents[s])["head"]
        out = []
        for i, (a, g, text, ref, b) in enumerate(rows):
            d = re.findall(r"\d\d\.\d\d\.\d{4}", text)
            if i == 0:
                frm, t = "Единая Россия", "названа самим ЦБСТ одним из трёх учредителей наряду с ПСБ и «Нашей Правдой»; в ЕГРЮЛ — только эти двое"
            elif i == 1:
                frm, t = "Александр Сидякин", f"назван ЦБСТ с {d[0]} секретарём наблюдательного совета и руководителем центрального исполкома «Единой России»"
            elif i == 2:
                frm, t = nm(NP), f"учредитель ЦБСТ с момента регистрации, {d[0]}"
            elif i == 3:
                frm, t = nm(PSB), f"учредитель ЦБСТ с момента регистрации, {d[0]}"
            elif i == 4:
                frm, t = "ЦБСТ", f"указывает ООО «МПТМ» в отчёте за 2025 год среди компаний, в которых участвует, с {d[0]}; размер доли не назван"
            elif i == 5:
                frm, t = nm(MPTM), "оператор маркетплейса РОЙ.МАРКЕТ по собственной оферте платформы для поставщиков"
            elif i == 6:
                frm, t = "РОЙ.МАРКЕТ", (f"говорит, что воинские части покупают на нём напрямую: в постах ЦБСТ — о частях, «подключённых к РОЙ.МАРКЕТ» ({d[0]}), "
                                         f"и о плане подключить все части технического обеспечения Минобороны к 1 сентября 2026 года ({d[1]}); заказа от части в деле нет")
            elif "held" in text:
                n = re.search(r"held (\d+)", text)
                frm, t = nm(NP), (f"на {d[0]} держал {n.group(1) if n else ''} «Булатов», купленных для передачи воинским частям, по аудированной отчётности; продавец не назван")
            else:
                n = re.search(r"in (\d+) of its posts", text).group(1)
                civ = f", и один раз — главам районов Херсонской области для бригад по ремонту электросетей ({d[2]})" if len(d) > 2 else ""
                frm, t = nm(NP), f"сообщает, что передавал детекторы дронов «Булат» воинским частям в {n} своих постах, с {d[0]} по {d[1]}{civ}; каждая передача разобрана в цепочке"
            out.append(f'<li><span class="from">{esc(frm)}</span>{ln(g)}<span class="what">{esc(t)}{ref}</span>'
                       f'<span class="rm-grade {g}">{GRADE_RU[g]}</span></li>')
        return "".join(out)

    # -- timeline ------------------------------------------------------------------------------------
    def timeline_ru(self):
        c, mp = self.ents[CBST], self.ents[MPTM]
        np_f = self.hist(CBST, "founders_history", "Наша Правда")
        sub = next(s for s in c.get("subsidiaries") or [] if s["slug"] == MPTM)
        restr = next((h for h in mp.get("founders_history") or [] if "restricted" in (h.get("value") or "")), {})
        oq = next(o for o in mp.get("open_questions") or [] if "masked" in o.get("text", ""))
        ev = [(np_f["as_of"], "ЦБСТ зарегистрирован в Москве; учредители — фонд «Наша Правда» и банк ПСБ", np_f.get("source_id"), "doc"),
              (sub["as_of"], "Зарегистрирован МПТМ; ЦБСТ участвует в нём с того же дня", sub.get("source_id"), "doc"),
              ("2025-02-15", "Платформа начинает работу как закрытый пилот, по рассказу «Коммерсанта»", "s8866", "rep"),
              ("2025-12-15", "Сидякин: партия, ПСБ и ЦБСТ «запустили военный маркетплейс»", "s8847", "rep"),
              (restr.get("as_of"), "ЕГРЮЛ начинает скрывать владельцев МПТМ", restr.get("source_id"), "doc"),
              ("2026-08-13", "Платформа открывается для внешних продавцов, «в первую очередь» для работающих на Wildberries и Ozon", "s8854", "rep"),
              ("2026-08-22", "Архивная копия оферты для поставщиков называет МПТМ оператором платформы", "s8817", "doc"),
              ("2026-09-02", "3mx сообщает клиенту, что «Булат» продаёт только 3mx и её дилеры", "s8860", "rep"),
              ("2026-10-01", "Действующая оферта печатает оператора как «ООО «****»»", oq.get("source_id"), "doc")]
        ev = sorted((e for e in ev if e[0]), key=lambda e: e[0])
        d0, d1 = dt.date(2024, 1, 1), dt.date(2026, 12, 31)
        W, X0, X1, AX = 960, 24, 936, 96
        x = lambda d: X0 + (X1 - X0) * (dt.date.fromisoformat(d) - d0).days / (d1 - d0).days
        marks, stack = [], {}
        for i, (d, _, _, g) in enumerate(ev, 1):
            px = x(d)
            lvl = next((k for k in range(6) if all(abs(px - q) >= 22 for q in stack.get(k, []))), 5)
            stack.setdefault(lvl, []).append(px)
            cy = AX - 18 - lvl * 22
            marks.append(f'<line x1="{px:.1f}" x2="{px:.1f}" y1="{AX}" y2="{cy + 9:.1f}" class="stem"/><circle cx="{px:.1f}" cy="{cy:.1f}" r="9" class="dot {g}"/>'
                         f'<text x="{px:.1f}" y="{cy + 3.6:.1f}" class="num">{i}</text>')
        ticks = []
        for y in (2024, 2025, 2026):
            for mth in (1, 4, 7, 10):
                px = x(f"{y}-{mth:02d}-01")
                ticks.append(f'<line x1="{px:.1f}" x2="{px:.1f}" y1="{AX}" y2="{AX + (8 if mth == 1 else 4)}" class="tick"/>')
                if mth == 1:
                    ticks.append(f'<text x="{px + 4:.1f}" y="{AX + 20}" class="yr">{y}</text>')
        svg = (f'<svg class="tl-svg" viewBox="0 0 {W} {AX + 28}" role="img" aria-label="Шкала времени, январь 2024 — декабрь 2026">'
               f'<line x1="{X0}" x2="{X1}" y1="{AX}" y2="{AX}" class="axis"/>{"".join(ticks)}{"".join(marks)}</svg>')
        items = "".join(f'<li><span class="d">{esc(ru_date(d) if d != "2025-02-15" else "начало 2025")}</span>'
                        f'<span class="t">{esc(t)}{self.ref(s)}</span></li>' for d, t, s, _ in ev)
        return f'<div class="tl"><div class="tl-scroll">{svg}</div><ol class="tl-list">{items}</ol></div>'

    # -- the maker's blind spot, the masked operator, the model ---------------------------------------
    def blind_ru(self):
        rows, seen = [], set()
        for li in self.p.get("listings") or []:
            s = li.get("seller") or {}
            ent = self.ents.get(s.get("entity") or "")
            chan = re.sub(r"\s*\(.*", "", li.get("channel") or "")
            if ent and ent["slug"] == self.p["maker"]:
                if chan in seen:
                    continue
                seen.add(chan)
                who, kind = f'{esc(display_name(ent)["head"])}: страница бренда', "продавец не установлен"
            else:
                n = display_name(ent) if ent else {}
                ip = ent and (n.get("legal") or n.get("head") or "").startswith("ИП ")
                who = esc(n["head"]) if ent else esc(re.sub(r"\s*\(.*", "", s.get("storefront") or ""))
                kind = "ИП" if ip else ("компания" if ent else "витрина, продавец не установлен")
            chan = chan.replace("dealer site", "сайт дилера").replace("own site", "собственный сайт").replace("dealer shop", "магазин дилера").replace("pavilion", "павильон")
            rows.append(f'<li><span class="ch">{esc(chan)}</span><span class="who">{who}</span><span class="k">{esc(kind)}</span>'
                        f'{self.ref(li.get("source_id"))}</li>')
        return ('<div class="blind one"><div class="side found"><span class="rm-label">Где «Булат» продаётся на самом деле</span>'
                f'<ul>{"".join(rows)}</ul></div></div>')

    def masked_ru(self):
        oq = next(o for o in self.ents[MPTM].get("open_questions") or [] if "masked" in o.get("text", ""))
        sub = next(s for s in self.ents[CBST].get("subsidiaries") or [] if s["slug"] == MPTM)
        cells = [("22.08.2026", "Оферта для поставщиков, архивная копия", "ООО «МПТМ» · ИНН 9714068459", self.ref("s8817"), "named"),
                 ("01.10.2026", "Оферта для поставщиков, действующий сайт", "Наименование Агента: ООО «****»", self.ref(oq.get("source_id"), "s8822"), "hidden"),
                 ("26.10.2026", "Политика конфиденциальности, действующий сайт",
                  "ООО «МПТМ», ИНН 9714068459, адрес: 109202, г. Москва, вн. тер. г. муниципальный округ Нижегородский, ул. 1-я Фрезерная, д. 2/1, корп. 2",
                  self.tref("privacy"), "named"),
                 (ru_date(sub["as_of"]), "Отчёт ЦБСТ в Минюст за 2025 год", 'ООО "МПТМ" · 1257700021468 · 22.01.2025 · в качестве участника',
                  self.ref(sub.get("source_id")), "named")]
        return '<div class="docs">' + "".join(
            f'<figure class="doc {c}"><figcaption><span class="rm-label">{esc(d)}</span> {esc(w)}{r}</figcaption>'
            f'<p class="print" lang="ru">{esc(t)}</p></figure>' for d, w, t, r, c in cells) + \
            '<p class="note">Строки приведены так, как напечатаны в каждом документе. В скрытой версии реквизиты видны только после входа.</p></div>'

    MODEL = {"ROI.MARKET": "РОЙ.МАРКЕТ",
             "Military": "Воинские", "units": "части", "TsBST, United": "ЦБСТ, «Единая", "Russia, Bank PSB,": "Россия», ПСБ,",
             "Nasha Pravda": "«Наша Правда»", "Maker": "Производитель", "Dealers and": "Дилеры и", "marketplaces": "маркетплейсы",
             "State": "Государство", "contracts": "(контракты)", "Donor foundation": "Передачи", "handovers": "доноров",
             "(other sellers)": "(другие продавцы)"}

    def model_ru(self):
        svg = self.models(first=False)
        for en, ru in self.MODEL.items():
            assert f">{en}</text>" in svg, en
            svg = svg.replace(f">{en}</text>", f">{ru}</text>")
        svg = re.sub(r'<figcaption>.*?</figcaption>', '<figcaption><span class="rm-label">Рабочая модель</span> Платформа — одна из точек сбыта. '
                     'Производители продают через своих дилеров и маркетплейсы, государству и донорам, которые передают товары частям.</figcaption>',
                     svg, count=1, flags=re.S)
        return svg.replace('aria-label="Working model"', 'aria-label="Рабочая модель"')

    # -- cards ---------------------------------------------------------------------------------------
    def chain_card_ru(self, slug, href):
        ch = Chain(slug)
        ch.img_dir = REPO / "exhibits" / "images" / "media"
        ch.build()
        p, m = ch.p, ch.maker
        logo = re.sub(r'alt="[^"]*"', f'alt="Логотип: {esc(display_name(m)["head"])}"', self.logo(p["maker"]))
        pname = p.get("name_ru") or ch.pq
        link = f'<a href="{esc(href)}">{esc(pname)}</a>' if href else esc(pname)
        return (f'<article class="rm-card chain-card"><header><span class="rm-kind">Цепочка изделия</span>{logo}</header>'
                f'<h3 class="rm-name">{link}<small>Изделие: {esc(display_name(m)["head"])}</small></h3>'
                + (f'<p class="go"><a href="{esc(href)}">Проследить {esc(pname)} от ЦБСТ до линии фронта →</a></p>' if href
                   else '<p class="go wait">Цепочка на проверке, пока не опубликована.</p>') + '</article>')

    def file_card_ru(self, kind, title, line, href, slug=None, wait="Досье на проверке, пока не опубликовано."):
        logo = re.sub(r'alt="[^"]*"', f'alt="Логотип: {esc(title)}"', self.logo(slug)) if slug else ""
        t = f'<a href="{esc(href)}">{esc(title)}</a>' if href else esc(title)
        return (f'<article class="rm-card chain-card"><header><span class="rm-kind">{esc(kind)}</span>{logo}</header>'
                f'<h3 class="rm-name">{t}<small>{esc(line)}</small></h3>'
                + (f'<p class="go"><a href="{esc(href)}">Открыть →</a></p>' if href else f'<p class="go wait">{esc(wait)}</p>') + '</article>')
