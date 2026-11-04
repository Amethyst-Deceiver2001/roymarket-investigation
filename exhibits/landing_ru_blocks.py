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
