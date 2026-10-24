#!/usr/bin/env python3
"""Landing page (plan A3): what the investigation shows, where to start, how to read it.

    python3 exhibits/build_landing.py             # -> exhibits/landing.html, chain links relative
    python3 exhibits/build_landing.py --preview   # chain links point at their private preview Artifacts

Generated from data/registry like the chain views, on the same design system, with the same
citation rules: no slugs, source ids, field or file names on the page; every claim carries a
numbered note in plain words. Counts are computed here, never typed in.
Local file processing only.
"""
import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "exhibits"))
sys.path.insert(0, str(REPO / "scripts"))
from build_chain_view import CBST, Chain, cap, esc, load, money  # noqa: E402
from display_helpers import NAME_JS, design_head, display_name, latin_text, latinize_gloss, media_about, name_html, orig_line, person_names, popup_originals, quote_html, reader_grade, ru_date, sanction_regimes  # noqa: E402
from graph_contract import source_grade  # noqa: E402

MPTM, NP, PSB, SIDYAKIN = "ooo-mptm", "fond-nasha-pravda", "pao-bank-psb", "aleksandr-sidyakin"
# One entry per published chain view: product slug -> private preview Artifact (until the public cutoff).
CHAINS = {"bulat": "https://claude.ai/artifact/6UaTv2jSwdNdfNUCibCwrf",
          "kapyushon": "https://claude.ai/artifact/5iYx5RsGmTRrAeooi8wdPd"}
# The foundation story's private preview; the public page links it only once it is published in docs/.
STORY = "https://claude.ai/artifact/DfLGJYwQY5mENE31J4tf8u"
# Other preview pages: (kind, title, one line, preview Artifact)
MORE = [("People", "One person, many companies", "The people who direct or own two or more of the companies on file",
         "https://claude.ai/artifact/RDUCMFfzWc5G6f62sV9dTT"),
        ("Project file", "«Arkhangel»", "A drone school that trains operators for the army and publishes an armed interceptor's parts list",
         "https://claude.ai/artifact/RABnZkrCUwktU5b91cNZTn")]

# The opening (24.10.2026). These posts were read in full and saved as TGPOST files on a machine without the source
# archive, so they have no catalogued source record yet: their notes are written here in plain words with the public
# link, and each quotation is checked word for word against the scrape at build time. Once the files are catalogued
# where the archive lives, the quotations move to the records' marketing_claims and the notes to self.ref().
OPENING_SOURCES = {
    "gag": ("Telegram, @my_el_lab (Gagaring), post 5142, 19.10.2026", "https://t.me/my_el_lab/5142"),
    "cbst": ("Telegram, @ANO_CBST, post 2677, 20.10.2026", "https://t.me/ANO_CBST/2677"),
    "ukrinform": ("Ukrinform, «Ворог вдарив дроном по будівлі Запорізької ОВА», 08.10.2026, citing the head of the "
                  "Zaporizhzhia regional military administration",
                  "https://www.ukrinform.ua/rubric-regions/4172418-vorog-vdariv-dronom-po-budivli-zaporizkoi-ova.html"),
    "tsentr": ("Telegram, @ANO_CBST, post 2610, 04.10.2026", "https://t.me/ANO_CBST/2610"),
    "tsentr_pics": ("Telegram, @ANO_CBST, posts 2605–2610 (one album of six pictures, captioned on 2610), 04.10.2026",
                    "https://t.me/ANO_CBST/2605"),
    "dw_film": ("DW, documentary «Targeting Civilians: How Russian Drones Terrorize a Ukrainian City», 2024, shown on YouTube "
                "(footage credit at 8:46, unit map at 16:53)", "https://www.youtube.com/watch?v=kuTo94TnMPo"),
    "yakim": ("Telegram, @asidyakin (Alexander Sidyakin), post 1405, 15.10.2026", "https://t.me/asidyakin/1405"),
    # The supplier page and the Kherson section (24.10.2026): saved as WEBCAPTURE/PDF files on this machine, not catalogued.
    "rm_aug": ("ROY.MARKET, «Начать продавать на РОЙ.МАРКЕТ» (page for prospective sellers), Internet Archive copy of 22.08.2026",
               "https://web.archive.org/web/20260822091346/https://xn--80akkfikneu.xn--p1ai/"),
    "rm_oct": ("The same page, Internet Archive copy of 12.10.2026",
               "https://web.archive.org/web/20261012125816/https://xn--80akkfikneu.xn--p1ai/"),
    "rm_now": ("The same page as published on 24.10.2026", "https://xn--80akkfikneu.xn--p1ai/"),
    "un_crp": ("Independent International Commission of Inquiry on Ukraine, «“They are hunting us”: systematic drone "
               "attacks targeting civilians in Kherson», UN document A/HRC/59/CRP.2, 28.05.2025",
               "https://www.ohchr.org/sites/default/files/documents/hrbodies/hrcouncil/coiukraine/a-hrc-59-crp2-en.pdf"),
    "un_ga": ("Independent International Commission of Inquiry on Ukraine, report to the UN General Assembly, A/80/497, 21.10.2025",
              "https://docs.un.org/en/A/80/497"),
    "cir": ("Centre for Information Resilience, «Tracing the Russian units responsible for drone attacks in Kherson», with DW, 2024",
            "https://www.info-res.org/eyes-on-russia/articles/tracing-the-russian-units-responsible-for-drone-attack-in-kherson/"),
    "arch_9067": ("Telegram, @projectArchangel, post 9067, 01.12.2025", "https://t.me/projectArchangel/9067"),
    "arch_10667": ("Telegram, @projectArchangel, post 10667, 17.08.2026", "https://t.me/projectArchangel/10667"),
    "cbst_1562": ("Telegram, @ANO_CBST, post 1562, 25.11.2025", "https://t.me/ANO_CBST/1562"),
    "osv_27702": ("Telegram, @osvedomitell_alex («От Мариуполя до Карпат»), post 27702, 23.07.2025", "https://t.me/osvedomitell_alex/27702"),
    "osv_19953": ("Telegram, @osvedomitell_alex, post 19953, 19.08.2024", "https://t.me/osvedomitell_alex/19953"),
    "osv_36192": ("Telegram, @osvedomitell_alex, post 36192, 24.07.2026", "https://t.me/osvedomitell_alex/36192"),
    "osv_38703": ("Telegram, @osvedomitell_alex, post 38703, 24.10.2026", "https://t.me/osvedomitell_alex/38703"),
    "osv_20344": ("Telegram, @osvedomitell_alex, post 20344, 28.08.2024", "https://t.me/osvedomitell_alex/20344"),
    "osv_20801": ("Telegram, @osvedomitell_alex, post 20801, 15.09.2024", "https://t.me/osvedomitell_alex/20801"),
    "osv_20993": ("Telegram, @osvedomitell_alex, post 20993, 22.09.2024", "https://t.me/osvedomitell_alex/20993"),
    "osv_21384": ("Telegram, @osvedomitell_alex, post 21384, 06.10.2024, signed @habr_bpla", "https://t.me/osvedomitell_alex/21384"),
    "osv_34459": ("Telegram, @osvedomitell_alex, post 34459, 15.05.2026", "https://t.me/osvedomitell_alex/34459"),
    "rog_8057": ("Telegram, @rogozin_do (Dmitry Rogozin), post 8057, 19.01.2026", "https://t.me/rogozin_do/8057"),
    "rog_7780": ("Telegram, @rogozin_do (Dmitry Rogozin), post 7780, 12.11.2025", "https://t.me/rogozin_do/7780"),
    "np_280": ("Telegram, @nashapravdafond, post 280, 07.05.2024", "https://t.me/nashapravdafond/280"),
    "np_580": ("Telegram, @nashapravdafond, post 580, 05.03.2026", "https://t.me/nashapravdafond/580"),
    "gag_2811": ("Telegram, @my_el_lab (Gagaring), post 2811, 23.12.2025", "https://t.me/my_el_lab/2811"),
}
# Two lines of the supplier page, read from the saved copies; not in the Telegram scrape, so not checked by oq().
SUPPLIER_LINES = {
    "dual": ("РОЙ.МАРКЕТ - защищённый канал продаж товаров двойного назначения.",
             "ROY.MARKET is a secure sales channel for dual-use goods."),
    "special": ("РОЙ.МАРКЕТ - защищённый канал продаж товаров специального назначения.",
                "ROY.MARKET is a secure sales channel for special-purpose goods."),
}
# English-original passages of the UN papers, copied from the PDFs (A/HRC/59/CRP.2 para 42; A/80/497 para 40).
UN_QUOTES = {
    "safari": ("Russian Federation soldiers behave like this is a safari […]; they are simply chasing and hunting civilians who "
               "are on their way to work or walking their dogs."),
    "dnepr": ("They are affiliated with various army units, all of which are part of the “Dnepr” Group of Forces"),
}
OPENING_QUOTES = {   # key: (channel, post, verbatim Russian, our translation)
    "gag": ("my_el_lab", 5142,
            "А вот кадры результатов работы дуэта Кузнечика и Совы 5.8. […] У Запорожской администрации тризуб отклеился.",
            "And here is footage of the results of the Kuznechik and Sova 5.8 duo at work. […] The Zaporizhzhia "
            "administration's trident has come unstuck."),
    "cbst": ("ANO_CBST", 2677,
             "«Тризуб отклеился»: резидент ЦБСТ показал кадры удара по украинской администрации Запорожья […] "
             "Удар осуществлялся дроном-камикадзе с применением системы связи «Кузнечик» и выносного видеоприёмника «Сова 5.8». […] "
             "Военнослужащие могут заказать их на специализированной платформе товаров двойного назначения РОЙ.МАРКЕТ.",
             "“The trident came unstuck”: a TsBST resident showed footage of the strike on the Ukrainian administration of "
             "Zaporizhzhia […] The strike was carried out by a kamikaze drone using the «Kuznechik» communication system and "
             "the «Sova 5.8» remote video receiver. […] Servicemen can order them on ROY.MARKET, the specialised platform "
             "for dual-use goods."),
    "tsentr": ("ANO_CBST", 2610,
               "Учения посетил Президент России Владимир Путин. […] В ходе выставки представители ЦБСТ договорились более "
               "чем с 10 участниками о размещении их ассортимента на платформе РОЙ.МАРКЕТ.",
               "The exercise was visited by the President of Russia, Vladimir Putin. […] During the exhibition, TsBST "
               "representatives agreed with more than 10 participants to place their range on the ROY.MARKET platform."),
    "yakim": ("asidyakin", 1405,
              "Это часть системы «Яким», которая разработана ЦБСТ и уже год помогает контролировать воздушное пространство "
              "региона. […] В будущем планируем связать «Яким» с военной системой «Свод» для лучшего анализа ситуации. "
              "Также хотим подключить автоматические пулемётные турели",
              "This is part of the «Yakim» system, which was developed by TsBST and has been helping to control the region's "
              "airspace for a year now. […] In future we plan to link «Yakim» with the military system «Svod» for better "
              "analysis of the situation. We also want to connect automatic machine-gun turrets"),
    "cbst_1562": ("ANO_CBST", 1562,
                  "режим внедрён в Михайловской военной артиллерийской академии и в новом учебном центре БПЛА «Архангел» в Туапсе",
                  "the mode has been introduced at the Mikhailovsky Military Artillery Academy and at the new «Arkhangel» drone "
                  "training centre in Tuapse"),
    "arch_9067": ("projectArchangel", 9067,
                  "Заключай контракт с Министерством обороны и неси дальнейшую службу  в подразделении БПЛА 205-ой Гв ОМСБр. […] "
                  "Выпускной экзамен - это Твое первое боевое задание, на котором Ты под присмотром строгих инструкторов поразишь свою первую цель.",
                  "Sign a contract with the Ministry of Defence and go on to serve in the drone unit of the 205th Guards Separate "
                  "Motor Rifle Brigade. […] The final exam is your first combat mission, in which, under the eye of strict "
                  "instructors, you will hit your first target."),
    "arch_10667": ("projectArchangel", 10667,
                   "205-ая бригада - гроза Херсонской области. Парни работают и на перехвате и на ударниках, частенько передают приветы.",
                   "The 205th brigade is the terror of Kherson region. The guys work both on interception and on strike drones, "
                   "and often send their regards."),
    "osv_27702": ("osvedomitell_alex", 27702,
                  "Бериславский отрезок фронта. Работают мужчины из стали 205 бригада 49 ОА ГВ \"Днепр\" […] "
                  "Любое передвижение автотранспорта будет считаться законной целью. Все объекты критической инфраструктуры являются законной целью.",
                  "Beryslav sector of the front. The men of steel of the 205th brigade, 49th Combined Arms Army, «Dnepr» Group of "
                  "Forces, at work […] Any movement of vehicles will be considered a legitimate target. All objects of critical "
                  "infrastructure are a legitimate target."),
    "osv_19953": ("osvedomitell_alex", 19953,
                  "Операторы работали точечно, так как наблюдали поблизости гражданских. Не находитесь рядом с автотранспортом, "
                  "не передвигайтесь в красной зоне. Вся техника будет уничтожена.",
                  "The operators worked precisely, as they observed civilians nearby. Do not stay near vehicles, do not move "
                  "about in the red zone. All vehicles will be destroyed."),
    "osv_36192": ("osvedomitell_alex", 36192,
                  "Транспорт двойного назначения. Противник в очередной раз использует кареты скорой помощи для подвоза БК […] "
                  "Естественно, техника будет уничтожаться и уничтожается.",
                  "Dual-use transport. Once again the enemy is using ambulances to bring up ammunition […] Naturally, the "
                  "vehicles will be destroyed and are being destroyed."),
    "osv_38703": ("osvedomitell_alex", 38703,
                  "Транспорт двойного назначения. Расчет Родной выявил технику, которая перемещается по Красной зоне под видом ритуальных услуг.",
                  "Dual-use transport. The «Rodnoy» crew spotted a vehicle moving through the Red Zone in the guise of funeral "
                  "services."),
    "rog_8057": ("rogozin_do", 8057,
                 "Центр специального назначения беспилотных систем \"Барс-Сармат\", командиром которого я являюсь, выполняет "
                 "боевые задачи командующего ВДВ и Генерального штаба.",
                 "The «Bars-Sarmat» special-purpose centre for unmanned systems, which I command, carries out combat tasks of "
                 "the commander of the Airborne Forces and of the General Staff."),
    "rog_7780": ("rogozin_do", 7780,
                 "многие наши союзники — армейские подразделения Группировки войск \"Днепр\" и части ВДВ предпочитают использовать "
                 "в качестве боевой части штурмовых дронов боеприпасы, разработанные инженерами ЦСН \"Барс-Сармат\"",
                 "many of our allies, army units of the «Dnepr» Group of Forces and Airborne units, prefer to use munitions "
                 "developed by the engineers of the «Bars-Sarmat» centre as the warheads of assault drones"),
    "np_580": ("nashapravdafond", 580,
               "Автомобиль, который ранее Фонд «Наша Правда» передал участникам спецоперации, бойцы 18 армии дооборудовали РЭБ "
               "и успешно используют для доставки грузов на ЛБС и переброски личного состава.",
               "A vehicle that the Nasha Pravda Foundation earlier handed to participants in the «special operation» has been "
               "fitted with electronic warfare by fighters of the 18th Army, who use it successfully to deliver cargo to the "
               "line of contact and to move personnel."),
    "gag_2811": ("my_el_lab", 2811,
                 "Воины 49-й Армии на страже неба Днепра... […] Без Совы перехватывать видео  было бы на много тяжелее",
                 "Warriors of the 49th Army guarding the sky over the Dnipro… […] Without the Sova, intercepting video would be "
                 "much harder"),
}

# Stills from the Kherson channel's own videos (and one map it posted), each looked at full size (notes/
# osvedomitell_alex_media_looked_20261024.md). The files are not catalogued on this Mac, so they have no media.json
# record: they appear on the private preview only, never in a docs/ build, and move to media.json once catalogued.
# key: (post, file in exhibits/images/kherson, what the frame shows, verbatim Russian from the post, our translation)
# Two of the six pictures of ЦБСТ's own album from the «Tsentr-2026» exercise (post 2605–2610, 04.10.2026): its stall and
# the ROY.MARKET booklet. The other four (the range) are not used. Each looked at full size 24.10.2026. Fetched from the public preview; not catalogued on this Mac (no source ids here), so like the Kherson
# stills they appear on the private preview only. key: (file in exhibits/images/center2026, what the frame shows,
# (verbatim Russian, English) of a line printed in it or None)
CENTER_STILLS = [
    ("c2605-1.jpg", "The stand under camouflage netting: a roll-up banner with the TsBST and ROY.MARKET logos and a QR code, a "
     "monitor, a laptop and papers on the table. The face of the man standing at the stand is blurred in the post itself; "
     "we leave it so.", ("Технологии превосходства", "Technologies of superiority")),
    ("c2605-2.jpg", "Folded ROY.MARKET leaflets and a red round patch. Each leaflet shows a gimbal camera and is printed "
     "“3000+” product items.", None),
]

KHERSON_STILLS = {
    "osv_27702": (27702, "k27702.jpg", "A drone's view down into a ruined house. On the left, the bear emblem with “205 brigade”; "
                  "bottom right, the caption “settlement of Kazatskoe” and grid coordinates. Still at 0:40.",
                  "205 бригада 49 ОА ГВ \"Днепр\"", "205th brigade, 49th Combined Arms Army, «Dnepr» Group of Forces"),
    "osv_21384": (21384, "k21384.jpg", "The map posted with the warning: a red zone over the Kherson riverside, both banks of "
                  "the Dnipro and the bridge.",
                  "в этих районах наши расчёты будут вести уничтожение любого транспорта",
                  "in these districts our crews will destroy any vehicle"),
    "osv_19953": (19953, "k19953.jpg", "From above: a blue van in a yard, under a crosshair, with people standing at its side. "
                  "No one can be identified. Still at 2:40, before the strike.",
                  "Операторы работали точечно, так как наблюдали поблизости гражданских.",
                  "The operators worked precisely, as they observed civilians nearby."),
    "osv_20344": (20344, "k20344.jpg", "From above: a white van stopped in a street. Probably the video the UN Commission "
                  "reproduces as a figure; that is not shown. Still at 0:03.",
                  "Горе \"медиков\" оставили в живых только потому, что на авто был номер \"101\" пожарная охрана",
                  "The would-be “medics” were left alive only because the vehicle carried the number “101”, the fire service"),
    "osv_20801": (20801, "k20801.jpg", "From above: one person walking along a wall, with a crosshair beside them. No one "
                  "can be identified. Still at 0:15.",
                  "Задача выполнена. Цель поражена.", "Task completed. Target hit."),
    "osv_20993": (20993, "k20993.jpg", "From above: a person walking a dog along a road, under a crosshair. The post's text "
                  "is about a taxi driver; this part of the video is not what it describes. Still at 0:03.",
                  "Уничтожать нужно весь транспорт. Весь.", "All transport must be destroyed. All of it."),
    "osv_36192": (36192, "k36192.jpg", "From above: a white van under trees in a courtyard between apartment blocks. Lettering "
                  "on its side is partly hidden by the trees. Still at 0:10.",
                  "Противник в очередной раз использует кареты скорой помощи для подвоза БК",
                  "Once again the enemy is using ambulances to bring up ammunition"),
    "osv_38703": (38703, "k38703.jpg", "A drone's approach into a courtyard: a dark van lettered “RITUAL” (funeral services), "
                  "a yellow minibus beyond it. Watermark “Rodnaya 98 vdd”, the 98th Airborne Division. Still at 0:04.",
                  "Расчет Родной выявил технику, которая перемещается по Красной зоне под видом ритуальных услуг.",
                  "The «Rodnoy» crew spotted a vehicle moving through the Red Zone in the guise of funeral services."),
    "osv_34459": (34459, "k34459.jpg", "Title card of the video: “SVO”, the emblem of the «Dnepr» Group of Forces, then "
                  "“presents”. The post says the people struck were soldiers.",
                  "кадры объективного контроля с камер дронов БпС 18 ОА ГВ \"Днепр\"",
                  "footage from the cameras of the drone forces of the 18th Combined Arms Army, «Dnepr» Group of Forces"),
}


def ln(grade, w=56):
    return (f'<svg class="ln" width="{w}" height="8" aria-hidden="true">'
            f'<line x1="0" x2="{w}" y1="4" y2="4" class="rm-ln {grade}"/></svg>')


def short(e):
    return e if isinstance(e, str) else display_name(e)["head"]


class Landing(Chain):
    """Reuses the chain view's notes, names, sanctions and logo; builds no chain itself."""

    def __init__(self):
        super().__init__("bulat")
        self.graph = json.loads((REPO / "data" / "registry" / "relationship_graph.json").read_text())
        self.img_dir = REPO / "exhibits" / "images" / "media"
        self.preview = False
        people = json.loads((REPO / "data" / "registry" / "people.json").read_text())
        self.people = {x["slug"]: x for x in (people if isinstance(people, list) else people.get("people", []))}

    def claim(self, slug, needle):
        return next(m for m in self.ents[slug].get("marketing_claims") or [] if needle in m["text_ru"])

    def board_role(self, person):
        """A person's role on ЦБСТ's supervisory board: (title, from, source_id)."""
        r = next(r for r in self.people[person].get("roles") or []
                 if r.get("entity_slug") == CBST and "Secretary" in (r.get("title") or ""))
        return r

    def g(self, sid):
        """A row's grade from its document's kind: the same table that grades every graph edge (B1)."""
        return source_grade(self.src.get(sid))

    def hist(self, slug, field, value_part):
        return next((h for h in self.ents[slug].get(field) or [] if value_part in (h.get("value") or "")), {})

    def ledger(self):
        """Who stands behind ЦБСТ and what it holds: a short list of graded relations."""
        c, rows = self.ents[CBST], []
        np_f = self.hist(CBST, "founders_history", "Наша Правда")
        psb_f = self.hist(CBST, "founders_history", "ПСБ")
        reg = min((h["as_of"] for h in c.get("founders_history") or [] if h.get("as_of")), default=None)
        ur = self.claim(CBST, "Учредители ЦБСТ")
        rows.append(("United Russia", self.g(ur["source_id"]),
                     "named by TsBST itself as one of its three founders, with PSB and Nasha Pravda; "
                     "the company register lists only those two", self.ref(ur["source_id"]), None))
        sid = self.board_role(SIDYAKIN)
        rows.append((self.person_pop(SIDYAKIN).replace(f'id="nm-{SIDYAKIN}"', f'id="nm-{SIDYAKIN}-l"').replace(f'popovertarget="nm-{SIDYAKIN}"', f'popovertarget="nm-{SIDYAKIN}-l"'), self.g(sid.get("source_id")),
                     f"secretary of TsBST's supervisory board since {ru_date(sid['from'])}, while head of United Russia's "
                     "central executive committee", self.ref(sid.get("source_id")), None))
        rows.append((self.ents[NP], self.g(np_f.get("source_id")), f"co-founder of TsBST since its registration on {ru_date(reg)}",
                     self.ref(np_f.get("source_id")), self.ents[CBST]))
        rows.append((self.ents[PSB], self.g(psb_f.get("source_id")), f"co-founder of TsBST since {ru_date(psb_f.get('as_of'))}",
                     self.ref(psb_f.get("source_id")), self.ents[CBST]))
        sub = next(s for s in c.get("subsidiaries") or [] if s["slug"] == MPTM)
        tie = self.ents[MPTM].get("cbst_tie") or {}
        # The supplier offer is the document that names МПТМ as the platform's operator; it is also the source of
        # МПТМ's bank partner, so it is read from there rather than typed in.
        offer = next(pp["source_id"] for pp in self.ents[MPTM].get("platform_partners") or [] if pp.get("kind") == "bank")
        rows.append((self.ents[CBST], reader_grade(tie.get("confidence")),
                     f"lists MPTM, in its report for 2025, as a company it has taken part in since {ru_date(sub['as_of'])}; "
                     "the size of its share is not stated",
                     self.ref(sub.get("source_id")), self.ents[MPTM]))
        rows.append((self.ents[MPTM], self.g(offer), "the operator of the ROY.MARKET marketplace, by the platform's own supplier offer",
                     self.ref(offer), None))
        stock = next((c for c in self.p.get("claims") or [] if c.get("metric") == "donor_stock" and c.get("entity") == NP), None)
        if stock:
            n = re.search(r"Кол\. (\d+)", stock["text_ru"])
            rows.append((self.ents[NP], self.g(stock["source_id"]),
                         f"held {n.group(1) if n else 'a stock of'} «Bulat» on {ru_date(stock['as_of'])}, bought for transfer "
                         "to military units, by its audited accounts; the seller is not named",
                         self.ref(stock["source_id"]), None))
        ds = [d for d in self.p.get("deliveries") or [] if d.get("donor") == NP]
        if ds:
            dates = sorted(d["date"] for d in ds if d.get("date"))
            rows.append((self.ents[NP], reader_grade(ds[0].get("credibility")),
                         f"reports handing «Bulat» drone detectors to military units {len(ds)} times, "
                         f"{ru_date(dates[0])} to {ru_date(dates[-1])}; each handover is cited in the chain view",
                         self.ref(ds[0].get("source_id")), None))
        out = []
        for a, g, text, ref, b in rows:
            out.append(f'<li><span class="from">{a if isinstance(a, str) else self.en(a, pop=True)}</span>{ln(g)}<span class="what">{esc(text)}{ref}</span>'
                       f'<span class="rm-grade {g}">{esc({"doc": "Documented", "rep": "Reported", "open": "Not documented"}[g])}</span></li>')
        return "".join(out)

    def restricted(self):
        """The date from which the register withholds МПТМ's owners, with its source."""
        h = next((h for h in self.ents[MPTM].get("founders_history") or [] if "restricted" in (h.get("value") or "")), None)
        return (ru_date(h["as_of"]), self.ref(h.get("source_id"))) if h else (None, "")

    def quote(self):
        """Two sentences from Сидякин's post 618, in the post's order, recorded verbatim as claims on ЦБСТ and МПТМ."""
        a, b = self.claim(CBST, "поставили на фронт"), self.claim(MPTM, "военный маркетплейс")
        return a, b, self.ref(a["source_id"], b["source_id"])

    def money_line(self):
        fy = {}
        for f in self.ents[CBST].get("financials") or []:
            if f.get("funds_received") is not None:
                fy.setdefault(f["year"], f)
        parts = [f"{money(f['funds_received'])} in {y}{self.ref(f['source_id'])}" for y, f in sorted(fy.items())]
        return " and ".join(parts)

    def network(self):
        ties = [e for e in self.graph["edges"] if e["type"] == "cbst_tie"]
        slugs = {(e["source"] if CBST not in e["source"] else e["target"]).split("::")[-1]: reader_grade(e.get("confidence"))
                 for e in ties}
        by = {g: sum(1 for v in slugs.values() if v == g) for g in ("doc", "rep")}
        # Listed means a sanctions[] entry that names a regime, the same test the cards use to print "Sanctioned".
        # An entry with no regime (an aggregator's "linked" topic) is not a listing.
        def listed(e):
            return bool(sanction_regimes(e.get("sanctions")))
        sanc = sum(1 for s in slugs if listed(self.ents.get(s, {})))
        return len(slugs), by, sanc

    # -- the network as pictures ---------------------------------------------------------
    TIER_ORDER = [("cbst-core", "TsBST and its core"), ("money-layer", "Money"), ("plumbing", "Platform and services"),
                  ("manufacturer", "Makers"), ("adjacent", "Other")]

    def tied(self):
        ties = [e for e in self.graph["edges"] if e["type"] == "cbst_tie"]
        return sorted({(e["source"] if CBST not in e["source"] else e["target"]).split("::")[-1] for e in ties})

    def wall(self):
        """Every organisation linked to TsBST as a tile: its logo where one is on file, its name, and the Sanctioned
        flag naming the regimes. Grouped by its place in the network."""
        groups = []
        for tier, label in self.TIER_ORDER:
            slugs = [s for s in self.tied() if self.ents.get(s, {}).get("tier") == tier]
            if not slugs:
                continue
            slugs.sort(key=lambda s: (not self.logo(s), not sanction_regimes(self.ents[s].get("sanctions")), short(self.ents[s])))
            tiles = []
            for s in slugs:
                e = self.ents[s]
                regs = [lab for lab, _ in sanction_regimes(e.get("sanctions"))]
                logo = self.logo(s)
                flag = f'<span class="rm-sanction">Sanctioned <b>{esc(", ".join(regs))}</b></span>' if regs else ""
                tiles.append(f'<li class="tile{" has-logo" if logo else ""}">{logo}<span class="tn">{self.en(e, pop=True)}</span>{flag}</li>')
            groups.append(f'<div class="wall-g"><h3 class="rm-label">{esc(label)} · {len(slugs)}</h3><ul class="wall">{"".join(tiles)}</ul></div>')
        return "".join(groups)

    def sanctions_grid(self):
        """When the linked organisations were listed, by regime and year: one count per cell, from dated entries."""
        cells, undated = {}, 0
        for s in self.tied():
            e = self.ents.get(s, {})
            first = {}
            for x in e.get("sanctions") or []:
                for lab, _ in sanction_regimes([x]):
                    d = (x.get("date") or "")[:4]
                    if d:
                        first[lab] = min(first.get(lab) or d, d)
                    elif lab not in first:
                        first.setdefault(lab, None)
            for lab, y in first.items():
                if y:
                    cells[(lab, y)] = cells.get((lab, y), 0) + 1
                else:
                    undated += 1
        regs = [r for r in ("Ukraine", "US", "UK", "EU", "Switzerland", "Canada", "Australia", "New Zealand", "Japan")
                if any(k[0] == r for k in cells)]
        years = [str(y) for y in range(2022, dt.date.today().year + 1)]
        x0, cw, rh = 110, 92, 34
        w, h = x0 + cw * len(years) + 10, 30 + rh * len(regs)
        out = [f'<svg class="sg" viewBox="0 0 {w} {h}" role="img" aria-label="Linked organisations first listed, by regime and year">']
        for j, y in enumerate(years):
            out.append(f'<text class="yr" x="{x0 + cw * j + cw / 2}" y="16" text-anchor="middle">{y}</text>')
        for i, r in enumerate(regs):
            cy = 30 + rh * i + rh / 2
            out.append(f'<text class="rg" x="0" y="{cy + 4}">{esc(r)}</text><line class="row" x1="{x0}" x2="{w - 10}" y1="{cy}" y2="{cy}"/>')
            for j, y in enumerate(years):
                n = cells.get((r, y))
                if n:
                    rad = 6 + 3.2 * n ** 0.5 * 2
                    out.append(f'<circle class="sd" cx="{x0 + cw * j + cw / 2}" cy="{cy}" r="{min(rad, 15):.1f}"/>'
                               f'<text class="sn" x="{x0 + cw * j + cw / 2}" y="{cy + 4}" text-anchor="middle">{n}</text>')
        out.append("</svg>")
        return "".join(out), undated

    # Years held off the chart until re-read: the record's own note disagrees with the stored figure.
    HELD_YEARS = {("ooo-tsugam", 2025): "the filing note's original figures differ from the stored ones by a factor of ten"}

    def revenue_bars(self):
        """The largest revenues as filed, latest year on file, with the year before as a ghost bar. Non-profit funds
        are not revenue and do not appear (CLAUDE.md, БФО parser lessons)."""
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
                pw = f'<span class="prev" style="width:{100 * prev / top:.1f}%" title="{y - 1}: {money(prev)}"></span>' if prev else ""
                bars.append(f'<li><span class="bn">{self.en(self.ents[s])}</span><span class="bt">{pw}'
                            f'<span class="cur{"" if filed else " rep"}" style="width:{100 * v / top:.1f}%"></span></span>'
                            f'<span class="bv">{money(v)} <small>{y}</small>'
                            + ("" if filed else ' <span class="rm-grade rep">Reported</span>') + f'{self.ref(sid)}</span></li>')
            return f'<div class="rv-p"><h3 class="rm-label">{esc(title)}</h3><ol class="rv">{"".join(bars)}</ol></div>'
        big = [r for r in rows if r[0] >= 10e9]
        rest = [r for r in rows if r[0] < 10e9][:10]
        return (panel(big, f"Over ₽10bn · {len(big)}") if big else "") + panel(rest, "The next ten"), len(rows)

    # -- how we got here ------------------------------------------------------------------
    def pop(self, slug):
        """An entity in prose, Latin first, its Cyrillic name a click away; each popover id is unique on the page."""
        self._pops = getattr(self, "_pops", 0) + 1
        e = self.ents[slug]
        n = display_name(e)
        legal = n["legal"] or n["head"]
        return name_html(latin_text(n["head"]) if n["legal"] else n["latin"], legal, key=f"{slug}-{self._pops}")

    def person_pop(self, slug):
        """A person's first mention: given name and surname in Latin, the full Russian name in the popover."""
        x = self.people[slug]
        pn = person_names(x["fio_ru"], x.get("name_latin"))
        return name_html(pn["first"], pn["fio"], key=slug)

    def mclaim(self, slug, sid):
        return next(m for m in self.ents[slug].get("marketing_claims") or [] if m.get("source_id") == sid)

    def timeline(self):
        """Dated events on one scale (Feb 2024 to Oct 2026), dots stacked where months coincide; keyed list below."""
        c, mp = self.ents[CBST], self.ents[MPTM]
        np_f, psb_f = self.hist(CBST, "founders_history", "Наша Правда"), self.hist(CBST, "founders_history", "ПСБ")
        sub = next(s for s in c.get("subsidiaries") or [] if s["slug"] == MPTM)
        restr = next((h for h in mp.get("founders_history") or [] if "restricted" in (h.get("value") or "")), {})
        oq = next(o for o in mp.get("open_questions") or [] if "masked" in o.get("text", ""))
        ev = [(np_f["as_of"], "TsBST registered in Moscow, with the Nasha Pravda foundation as founder", np_f.get("source_id"), "doc"),
              (sub["as_of"], "MPTM registered; TsBST has taken part in it from the same day", sub.get("source_id"), "doc"),
              ("2025-02-15", "The platform starts as a closed pilot, by Kommersant's account", "s8866", "rep"),
              (psb_f["as_of"], "Bank PSB joins TsBST as co-founder", psb_f.get("source_id"), "doc"),
              ("2025-12-15", "Sidyakin: the party, PSB and TsBST “launched the military marketplace”", "s8847", "rep"),
              (restr.get("as_of"), "The company register starts withholding MPTM's owners", restr.get("source_id"), "doc"),
              ("2026-08-13", "The platform opens to outside sellers, “first of all” those on Wildberries and Ozon", "s8854", "rep"),
              ("2026-08-22", "An archived copy of the supplier offer names MPTM as the platform's operator", "s8817", "doc"),
              ("2026-09-02", "3mx tells a customer «Bulat» is sold only by 3mx and its dealers", "s8860", "rep"),
              ("2026-10-01", "The live offer prints the operator as “OOO «****»”", oq.get("source_id"), "doc")]
        ev = sorted((e for e in ev if e[0]), key=lambda e: e[0])
        d0, d1 = dt.date(2024, 1, 1), dt.date(2026, 12, 31)
        W, X0, X1, AX = 960, 24, 936, 96

        def x(d):
            return X0 + (X1 - X0) * (dt.date.fromisoformat(d) - d0).days / (d1 - d0).days
        marks, stack = [], {}
        for i, (d, _, _, g) in enumerate(ev, 1):
            px = x(d)
            # Dots closer than 22 px stack upward so each number stays legible; the stem keeps the true date.
            lvl = next((k for k in range(6) if all(abs(px - q) >= 22 for q in stack.get(k, []))), 5)
            stack.setdefault(lvl, []).append(px)
            cy = AX - 18 - lvl * 22
            marks.append(f'<line x1="{px:.1f}" x2="{px:.1f}" y1="{AX}" y2="{cy + 9:.1f}" class="stem"/>'
                         f'<circle cx="{px:.1f}" cy="{cy:.1f}" r="9" class="dot {g}"/>'
                         f'<text x="{px:.1f}" y="{cy + 3.6:.1f}" class="num">{i}</text>')
        ticks = []
        for y in (2024, 2025, 2026):
            for mth in (1, 4, 7, 10):
                px = x(f"{y}-{mth:02d}-01")
                ticks.append(f'<line x1="{px:.1f}" x2="{px:.1f}" y1="{AX}" y2="{AX + (8 if mth == 1 else 4)}" class="tick"/>')
                if mth == 1:
                    ticks.append(f'<text x="{px + 4:.1f}" y="{AX + 20}" class="yr">{y}</text>')
        svg = (f'<svg class="tl-svg" viewBox="0 0 {W} {AX + 28}" role="img" aria-label="Timeline, January 2024 to December 2026">'
               f'<line x1="{X0}" x2="{X1}" y1="{AX}" y2="{AX}" class="axis"/>{"".join(ticks)}{"".join(marks)}</svg>')
        items = "".join(f'<li><span class="d">{esc(ru_date(d) if d != "2025-02-15" else "early 2025")}</span>'
                        f'<span class="t">{esc(t)}{self.ref(s)}</span></li>' for d, t, s, _ in ev)
        return f'<div class="tl"><div class="tl-scroll">{svg}</div><ol class="tl-list">{items}</ol></div>'

    def test_bar(self):
        """The first hypothesis tested: every maker on file, by what the Wildberries seller check found."""
        makers = [e for e in self.ents.values() if e.get("tier") == "manufacturer"]
        k = {key: sum(1 for e in makers if e.get("wb_overlap") == key)
             for key in ("confirmed_direct", "confirmed_reseller", "none_found", "not_checked")}
        direct = [e for e in makers if e.get("wb_overlap") == "confirmed_direct"]
        segs = [("direct", k["confirmed_direct"], "sell under their own INN",
                 ", ".join(self.pop(e["slug"]) for e in direct)),
                ("resell", k["confirmed_reseller"], "records for one brand, «Bulat» (its maker, the brand and a related sole trader): sold through other sellers", ""),
                ("none", k["none_found"], "no Wildberries seller carries their INN", ""),
                ("unchecked", k["not_checked"], "not checked: no INN, or added later", "")]
        total = len(makers)
        bar = "".join(f'<span class="seg {c}" style="flex-grow:{n}" title="{n}"></span>' for c, n, _, _ in segs if n)
        keys = "".join(f'<li><span class="sw {c}"></span><b>{n}</b> {esc(t)}{(": " + extra) if extra else ""}</li>'
                       for c, n, t, extra in segs)
        return (f'<figure class="test"><div class="bar" role="img" aria-label="{total} makers by Wildberries check result">{bar}</div>'
                f'<figcaption><ul class="keys">{keys}</ul><p class="note">{total} makers on file, checked against the sellers '
                f'in the earlier Wildberries dataset by INN. Counted from the registry.</p></figcaption></figure>')

    def blind_spot(self):
        """What an INN screen of the maker sees, beside the storefronts the record actually holds for «Bulat»."""
        rows, seen = [], set()
        for li in self.p.get("listings") or []:
            s = li.get("seller") or {}
            ent = self.ents.get(s.get("entity") or "")
            chan = re.sub(r"\s*\(.*", "", li.get("channel") or "")
            if ent and ent["slug"] == self.p["maker"]:
                # The maker's brand page: the seller behind it is not the maker's INN, and has not been captured yet.
                if chan in seen:
                    continue
                seen.add(chan)
                who, kind = f'{self.en(ent)} brand page', "seller behind it not yet captured"
            else:
                n = display_name(ent) if ent else {}
                ip = ent and (n.get("legal") or n.get("head") or "").startswith("ИП ")
                who = self.en(ent, pop=True) if ent else esc(latin_text(re.sub(r"\s*\(.*", "", s.get("storefront") or "")))
                kind = "sole trader" if ip else ("company" if ent else "storefront, seller unidentified")
            rows.append(f'<li><span class="ch">{esc(latin_text(chan))}</span><span class="who">{who}</span>'
                        f'<span class="k">{esc(kind)}</span>{self.ref(li.get("source_id"))}</li>')
        return (f'<div class="blind"><div class="side screen"><span class="rm-label">Screening by the maker\'s INN</span>'
                f'<p class="zero">0</p><p>Wildberries sellers carrying {self.pop(self.p["maker"])}\'s INN in the earlier dataset</p></div>'
                f'<div class="side found"><span class="rm-label">Where «Bulat» is actually sold</span><ul>{"".join(rows)}</ul></div></div>')

    def masked(self):
        """The operator's name as printed before and after it was masked, and the TsBST report row, as text."""
        oq = next(o for o in self.ents[MPTM].get("open_questions") or [] if "masked" in o.get("text", ""))
        sub = next(s for s in self.ents[CBST].get("subsidiaries") or [] if s["slug"] == MPTM)
        cells = [("22.08.2026", "Supplier offer, archived copy", ("OOO «MPTM» · INN 9714068459", "ООО «МПТМ» · ИНН 9714068459"), self.ref("s8817"), "named"),
                 ("01.10.2026", "Supplier offer, live site", ("Name of the Agent: OOO «****»", "Наименование Агента: ООО «****»"), self.ref(oq.get("source_id"), "s8822"), "hidden"),
                 (ru_date(sub["as_of"]), "TsBST's report to the Justice Ministry, for 2025",
                  ("OOO \"MPTM\" · OGRN 1257700021468 · 22.01.2025 · as a participant", "ООО \"МПТМ\" · 1257700021468 · 22.01.2025 · в качестве участника"), self.ref(sub.get("source_id")), "named")]
        return '<div class="docs">' + "".join(
            f'<figure class="doc {c}"><figcaption><span class="rm-label">{esc(d)}</span> {esc(w)}{r}</figcaption>'
            f'<p class="print">{name_html(t[0], t[1], key=f"doc-{i}", what="Line as printed, in Russian:")}</p></figure>' for i, (d, w, t, r, c) in enumerate(cells)) + \
            '<p class="note">Lines as printed in each document, rendered in English; the Russian original is under RU. The masked version shows the requisites only after login.</p></div>'

    def models(self):
        """Hypothesis 1 beside hypothesis 2, as two small flow diagrams."""
        def box(x, y, w, t, cls=""):
            lines = t.split("|")
            h = 18 + 16 * len(lines)
            tx = "".join(f'<text x="{x + w / 2}" y="{y + 22 + 16 * i}" class="bt">{esc(s)}</text>' for i, s in enumerate(lines))
            return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" class="bx {cls}"/>{tx}', (x, y, w, h)

        def arrow(a, b, cls="doc"):
            (ax, ay, aw, ah), (bx, by, bw, bh) = a, b
            return (f'<path d="M{ax + aw} {ay + ah / 2} C{(ax + aw + bx) / 2} {ay + ah / 2} {(ax + aw + bx) / 2} {by + bh / 2} '
                    f'{bx} {by + bh / 2}" class="rm-ln {cls}" marker-end="url(#ah)"/>')
        defs = '<defs><marker id="ah" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L8 4L0 8z" class="ah"/></marker></defs>'
        p = []
        a, ra = box(10, 20, 170, "Wildberries and|Ozon sellers")
        b, rb = box(10, 100, 170, "TsBST residents")
        c, rc = box(250, 58, 150, "ROY.MARKET", "hub")
        d, rd = box(470, 58, 150, "Military|units")
        p += [a, b, c, d, arrow(ra, rc, "open"), arrow(rb, rc, "open"), arrow(rc, rd, "open")]
        one = f'<svg viewBox="0 0 630 160" class="mdl" role="img" aria-label="First hypothesis">{defs}{"".join(p)}</svg>'
        p = []
        h, rh = box(10, 100, 150, "TsBST, United|Russia, Bank PSB,|Nasha Pravda", "hub")
        m, rm = box(210, 112, 120, "Maker")
        outs = [("Dealers and|marketplaces", "doc", 10), ("State|contracts", "doc", 80), ("Donor foundation|handovers", "rep", 150),
                ("ROY.MARKET|(other sellers)", "rep", 220)]
        u, ru = box(560, 112, 90, "Military|units")
        p += [h, m, u, arrow(rh, rm, "doc")]
        for t, g, y in outs:
            o, ro = box(380, y, 140, t)
            p += [o, arrow(rm, ro, g), arrow(ro, ru, g)]
        two = f'<svg viewBox="0 0 660 290" class="mdl" role="img" aria-label="Working model">{defs.replace("ah", "ah2")}{"".join(p).replace("url(#ah)", "url(#ah2)")}</svg>'
        return (f'<div class="models"><figure><figcaption><span class="rm-label">First guess</span> The platform would be '
                f'stocked by people already selling on the mass marketplaces and by TsBST\'s own residents.</figcaption>'
                f'<div class="mdl-wrap">{one}</div></figure>'
                f'<figure><figcaption><span class="rm-label">Working model</span> The platform is one outlet among several. '
                f'Makers sell through their own dealers and marketplaces, to the state, and to donors who hand the goods to units.'
                f'</figcaption><div class="mdl-wrap">{two}</div></figure></div>')

    # -- pictures: registered media only (media.json), each opening its full figure with caption, date and source ----
    HERO = "m0085"   # Nasha Pravda's crates and cases by a truck, 24.04.2026: no faces, the supply itself

    def pics(self, slugs, genres=None, skip=()):
        """Publishable pictures about any of these entities, oldest first, optionally of some genres only."""
        ms = media_about(self.media, {("entity", s) for s in slugs})
        return sorted((m for m in ms if m["id"] not in skip and m.get("genre") != "logo"
                       and (genres is None or m.get("genre") in genres) and self.img(m)),
                      key=lambda m: (m.get("published") or "", m["id"]))

    @staticmethod
    def tile_label(text, when=None):
        """A short visible label for a lead tile: the first clause of what the picture shows, and its date."""
        first = re.split(r"(?<=[a-z0-9\)”»])[.;:] ", text.strip(), 1)[0].rstrip(".")
        first = first if len(first) <= 60 else first[:58].rsplit(" ", 1)[0].rstrip(" ,;:-") + "…"
        return f"{first}, {when}" if when else first

    @staticmethod
    def tile(fig, img, aria, cap=None, big=False, contain=False):
        c = " ".join(x for x, on in (("pic", True), ("big", big), ("contain", contain)) if on)
        label = f'<span class="cap">{esc(cap)}</span>' if cap and big else ""
        return (f'<button class="{c}" type="button" data-fig="{fig}" aria-label="{esc(aria)}">'
                f'<img src="{esc(img)}" alt="" loading="lazy">{label}</button>')

    def band(self, ms, label, big=3, lead=(), limit=9):
        """A band of pictures. Pictures named in `lead` come first; the first `big` are drawn large with a visible label;
        any past `limit` sit behind "Show all". Each opens its full figure."""
        if not ms:
            return ""
        ms = sorted(ms, key=lambda m: (m["id"] not in lead, lead.index(m["id"]) if m["id"] in lead else 0))
        tiles, sids = [], []
        for i, m in enumerate(ms):
            self.template(m)
            if m.get("source_id") not in sids:
                sids.append(m.get("source_id"))
            en = m.get("shows_en") or latinize_gloss(m["shows"])
            tiles.append(self.tile(f"fig-{m['id']}", self.img(m), en, self.tile_label(en, ru_date(m.get("published"))), big=i < big))
        shown, rest = tiles[:limit], tiles[limit:]
        more = (f'<details class="more"><summary>Show all {len(tiles)} pictures</summary>'
                f'<div class="band-grid">{"".join(rest)}</div></details>') if rest else ""
        return (f'<figure class="band"><div class="band-grid">{"".join(shown)}</div>{more}'
                f'<figcaption><span class="rm-label">Pictures · {len(ms)}</span> {label} Each opens with its caption, '
                f'date and source.{self.ref(*sids)}</figcaption></figure>')

    def hero(self):
        """The header's background: one handover picture, credited and openable like any other."""
        m = next((m for m in self.media if m["id"] == self.HERO), None)
        if not m or not self.img(m):
            return "", ""
        self.template(m)
        credit = (f'<button class="hero-credit" type="button" data-fig="fig-{m["id"]}">Background: crates and cases by a '
                  f'truck, from a handover post of «Nasha Pravda», {ru_date(m.get("published"))}</button>')
        return f' style="--hero: url({esc(self.img(m))})"', credit

    def tref(self, key):
        """A note for a document from OPENING_SOURCES: plain words and its public link (see the table's comment)."""
        note = OPENING_SOURCES[key]
        if note not in self.notes:
            self.notes.append(note)
        n = self.notes.index(note) + 1
        return f'<sup class="rm-ref"><a href="#n{n}">{n}</a></sup>'

    @staticmethod
    def verbatim(key, chan, msg, ru):
        """Stop the build if a quoted line is not word for word in the scraped post (where the scrape exists)."""
        db = REPO / "data" / "roymarket.db"
        if db.exists():
            import sqlite3
            row = sqlite3.connect(f"file:{db}?mode=ro", uri=True).execute(
                "select p.text from tg_posts p join tg_channels c on c.id = p.channel_id where c.username = ? and p.msg_id = ?",
                (chan, msg)).fetchone()
            for part in ru.split(" […] "):
                if not row or part not in row[0]:
                    raise SystemExit(f"quote {key}: not verbatim in {chan}/{msg}")

    def oq(self, key, cite):
        """A quotation from OPENING_QUOTES, checked word for word against the scraped post where the scrape exists."""
        chan, msg, ru, en = OPENING_QUOTES[key]
        self.verbatim(key, chan, msg, ru)
        return quote_html(ru, en, cite, f"q-{key}")

    def kherson_band(self):
        """Stills from the Kherson channel (KHERSON_STILLS), as a picture band. Preview only: they have no media record."""
        if not self.preview:
            return ""
        src_dir, dest = REPO / "exhibits" / "images" / "kherson", self.img_dir.parent / "kherson"
        tiles = []
        for key, (msg, name, shows, ru, en) in KHERSON_STILLS.items():
            if not (src_dir / name).exists():
                continue
            self.verbatim(key, "osvedomitell_alex", msg, ru)
            if dest != src_dir:
                dest.mkdir(parents=True, exist_ok=True)
                (dest / name).write_bytes((src_dir / name).read_bytes())
            rel = f"images/kherson/{name}"
            if (rel, dest / name) not in self.media_files:
                self.media_files.append((rel, dest / name))
            when = OPENING_SOURCES[key][0].rsplit(", ", 1)[-1] if key != "osv_21384" else "06.10.2024"
            video = "" if name == "k21384.jpg" else ('<span class="orig">Still from a video. Original on Telegram, kept in '
                                                     'our own record of the channel.</span>')
            self.templates[f"k{msg}"] = (
                f'<figure class="rm-fig"><div class="frame"><img src="{esc(rel)}" alt="{esc(shows)}"></div><figcaption>'
                f'<span class="rm-prov">Posted by «From Mariupol to the Carpathians»</span><span>{esc(shows)} The post: '
                f'{orig_line(ru, f"ks-{msg}", en)}{self.tref(key)}</span>{video}<span class="when">{esc(when)}</span>'
                f'</figcaption></figure>')
            cap = self.tile_label(shows.split(" Still at")[0], when)
            tiles.append(self.tile(f"fig-k{msg}", rel, shows, cap, big=len(tiles) < 2, contain=name in ("k27702.jpg", "k34459.jpg")))
        if not tiles:
            return ""
        return (f'<figure class="band"><div class="band-grid">{"".join(tiles)}</div><figcaption><span class="rm-label">'
                f'Pictures · {len(tiles)}</span> Stills from the channel\'s own videos, 2024–2026, and the map it posted with '
                f'one of its warnings. Nobody in them can be identified, and no frame we looked at shows a dead or wounded '
                f'person. Each opens with its caption, date and the post\'s own words.</figcaption></figure>')

    def center_band(self):
        """ЦБСТ's own album from the «Tsentr-2026» exercise (CENTER_STILLS) as a picture band. Preview only: no media record."""
        if not self.preview:
            return ""
        src_dir, dest = REPO / "exhibits" / "images" / "center2026", self.img_dir.parent / "center2026"
        tiles = []
        for n, (name, shows, line) in enumerate(CENTER_STILLS, 1):
            if not (src_dir / name).exists():
                continue
            if dest != src_dir:
                dest.mkdir(parents=True, exist_ok=True)
                (dest / name).write_bytes((src_dir / name).read_bytes())
            rel = f"images/center2026/{name}"
            if (rel, dest / name) not in self.media_files:
                self.media_files.append((rel, dest / name))
            printed = f' Printed on the banner: {orig_line(line[0], f"cs-{n}", line[1])}.' if line else ""
            self.templates[f"c{n}"] = (
                f'<figure class="rm-fig"><div class="frame"><img src="{esc(rel)}" alt="{esc(shows)}"></div><figcaption>'
                f'<span class="rm-prov">Posted by TsBST itself, picture {n} of 6 in the album</span><span>{esc(shows)}{printed} '
                f'The post\'s caption says TsBST presented ROY.MARKET at the main stage of the exercise; it does not '
                f'describe the pictures.{self.tref("tsentr_pics")}</span><span class="when">04.10.2026</span></figcaption></figure>')
            tiles.append(self.tile(f"fig-c{n}", rel, shows, self.tile_label(shows, "04.10.2026"), big=len(tiles) < 2))
        if not tiles:
            return ""
        return (f'<figure class="band"><div class="band-grid">{"".join(tiles)}</div><figcaption><span class="rm-label">'
                f'Pictures · {len(tiles)}</span> TsBST\'s own stall at the exercise, and ROY.MARKET\'s printed booklet and patch. '
                f'Neither shows a listing on the platform. Each opens with its caption, date and source.</figcaption></figure>')

    def opening(self):
        """The cold open: a maker's strike footage, re-posted by ЦБСТ with an order line for its marketplace."""
        g = self.ents["ooo-gagaring"]
        tie = g.get("cbst_tie") or {}
        listed = bool(g.get("sanctions"))
        nodes = [("8 October", "Zaporizhzhia", "The head of the regional administration reports that an FPV drone hit the coat of arms on its building.", "rep"),
                 ("19 October", "Gagaring", "The maker posts a video of “the results” of its Kuznechik and Sova 5.8.", "rep"),
                 ("20 October", "TsBST", "Re-posts it as “a TsBST resident showed footage of the strike” and names both products.", "rep"),
                 ("Order line", "ROY.MARKET", "“Servicemen can order them” there. The catalogue is behind a login, so TsBST's post is the only evidence.", "rep")]
        joins = [("open", "neither post dates the strike"), ("rep", "same video"), ("rep", "sales line")]
        return (
            self.gag_video()
            + f'<p>On 19 October 2026 {self.pop("ooo-gagaring")}, a drone-electronics maker in Krasnodar, posted this short video '
            f'to its Telegram channel:</p>'
            + self.oq("gag", f"Gagaring, Telegram, 19.10.2026{self.tref('gag')}") +
            f'<p>The next morning TsBST, the Moscow non-profit for the drone industry that counts the company among its '
            f'residents{self.ref(tie.get("source_id"))}, posted the same video under its own headline, named the two '
            f'products used, and closed with a sales line:</p>'
            + self.oq("cbst", f"TsBST, Telegram, 20.10.2026{self.tref('cbst')}")
            + f'<ol class="flow" aria-label="From the strike report to the order line">{self.flow_html(nodes, joins)}</ol>' +
            f'<p>TsBST calls the city “occupied”. Zaporizhzhia is held by Ukraine; the building is the seat of its regional '
            f'government. On 8 October the head of the regional administration reported that an FPV drone had hit the coat '
            f'of arms on its façade: smoke, no fire, nobody hurt{self.tref("ukrinform")}. ROY.MARKET is TsBST\'s own '
            f'marketplace for military units. '
            + ("" if listed else "No sanctions listing for the maker is on file. ") +
            '</p><p class="note"><span class="rm-grade rep">Reported</span> Both posts are the parties\' own word. We watched '
            'the 25-second video. It follows a drone in over a large government building, labelled “Kuznechik/Sova 5.8”, '
            'down to a trident coat of arms on its façade; the last eight seconds are a separate vertical clip, with its own '
            'watermark, of the coat of arms hanging damaged from its frame. That is consistent with the report of 8 October, '
            'but neither post dates the strike, we have not placed the building on a map, and the impact itself is not in the '
            'frames we checked.</p>'
            + self.band(self.pics(["ooo-gagaring", "ano-dpo-obrazovatelny-tsentr-gagaring"]),
                        "Gagaring's own: its director at one of its field courses, and graduates of its training centre.", big=2)
            + self.dual_use())

    def flow_html(self, nodes, joins):
        flow = []
        for i, (d, who, what, g) in enumerate(nodes):
            flow.append(f'<li class="node{" last" if i == len(nodes) - 1 else ""}">{self.shot(i)}<span class="d">{esc(d)}</span>'
                        f'<span class="who">{esc(who)}</span><span class="what">{esc(what)}</span>'
                        f'<span class="rm-grade {g}">Reported</span></li>')
            if i < len(joins):
                gj, lab = joins[i]
                flow.append(f'<li class="join" aria-hidden="true">{ln(gj, 44)}<span>{esc(lab)}</span></li>')
        return "".join(flow)

    SHOTS = [
        ("opening/ukrinform-zaporizhzhia-ova.jpg", "Ukrinform, 08.10.2026",
         "Screenshot of the Ukrinform article «The enemy hit the Zaporizhzhia regional administration building with a drone» "
         "(8 October 2026), with its photograph of the building's façade.", "ukrinform"),
        ("video/gagaring-5142.jpg", "Gagaring's video, 19.10.2026",
         "A frame from Gagaring's video: the government building seen from above, before the drone flies in.", "gag"),
        ("opening/tsbst-post-2677.jpg", "TsBST's post, 20.10.2026",
         "Screenshot of TsBST's Telegram post of 20 October 2026: the same video, the headline «The trident came unstuck» "
         "(Russian original) and the sales line.", "cbst"),
        ("opening/roymarket-supplier-page.jpg", "ROY.MARKET's public page, 24.10.2026",
         "Screenshot of ROY.MARKET's public page for prospective sellers as it read on 24 October 2026. The catalogue itself "
         "is behind a login.", "rm_now"),
    ]

    def shot(self, i):
        """A screenshot for box i of the opening strip, openable like any picture. Preview only: third-party captures
        have no media record."""
        if not self.preview:
            return ""
        name, label, shows, key = self.SHOTS[i]
        src_dir, dest = REPO / "exhibits" / "images", self.img_dir.parent
        rel = f"images/{name}"
        if dest != src_dir:
            (dest / name).parent.mkdir(parents=True, exist_ok=True)
            (dest / name).write_bytes((src_dir / name).read_bytes())
        if (rel, dest / name) not in self.media_files:
            self.media_files.append((rel, dest / name))
        self.templates[f"o{i}"] = (
            f'<figure class="rm-fig"><div class="frame"><img src="{esc(rel)}" alt="{esc(shows)}"></div><figcaption>'
            f'<span class="rm-prov">Screenshot taken 24.10.2026</span><span>{esc(shows)}{self.tref(key)}</span></figcaption></figure>')
        return (f'<button class="shot" type="button" data-fig="fig-o{i}" aria-label="{esc(shows)}">'
                f'<img src="{esc(rel)}" alt=""><span class="cap">{esc(label)}</span></button>')

    def step_shot(self, i, caption):
        """A screenshot from SHOTS under a step of the origin story, with its own plain caption. Preview only."""
        btn = self.shot(i)
        return f'<figure class="step-shot">{btn}<figcaption>{esc(caption)}</figcaption></figure>' if btn else ""

    def gag_video(self):
        """The 25-second clip from Gagaring's post, playable. Preview only: the file is not catalogued, and a public
        page shows key frames plus a link to the archived original."""
        src = REPO / "exhibits" / "images" / "video"
        if not self.preview or not (src / "gagaring-5142.mp4").exists():
            return ""
        dest = self.img_dir.parent / "video"
        for name in ("gagaring-5142.mp4", "gagaring-5142.jpg"):
            if dest != src:
                dest.mkdir(parents=True, exist_ok=True)
                (dest / name).write_bytes((src / name).read_bytes())
            if (f"images/video/{name}", dest / name) not in self.media_files:
                self.media_files.append((f"images/video/{name}", dest / name))
        return ('<figure class="clip"><video controls preload="none" playsinline poster="images/video/gagaring-5142.jpg" '
                'aria-label="Gagaring\'s video: a drone flies in over a large government building to a trident coat of arms on '
                'its façade, then a separate clip of the coat of arms hanging damaged">'
                '<source src="images/video/gagaring-5142.mp4" type="video/mp4"></video>'
                '<figcaption><span class="rm-label">Video · 0:25</span> As posted by Gagaring, labelled “Kuznechik/Sova 5.8”. '
                'The drone flies in over the building to the coat of arms on its façade; the last eight seconds are a separate '
                f'vertical clip, with its own watermark, of the coat of arms hanging damaged. It has no spoken words, only footage. Re-encoded smaller for this page; '
                f'the original is kept in our own record of the channel{self.tref("gag")}.</figcaption></figure>')

    def dual_use(self):
        """The label on the order line: the supplier page's own sentence before and after it changed."""
        (d_ru, d_en), (s_ru, s_en) = SUPPLIER_LINES["dual"], SUPPLIER_LINES["special"]
        return (
            f'<p>TsBST\'s “dual-use” is the platform\'s own label. From August 2026 its page for prospective sellers opened with '
            f'{orig_line(d_ru, "rm-dual", d_en)}{self.tref("rm_aug")} The copy archived on 12 October still did'
            f'{self.tref("rm_oct")}. By 24 October the same sentence read {orig_line(s_ru, "rm-special", s_en)}'
            f'{self.tref("rm_now")} The kamikaze drone in TsBST\'s post used the two products it advertises; the platform\'s '
            f'public terms and buyer offer use neither phrase.</p>')

    @staticmethod
    def un_quote(key, cite):
        """A passage of a UN paper, quoted in its original English: no translation, no RU control."""
        return (f'<blockquote class="rm-quote"><span class="rm-label">Quotation</span>'
                f'<span class="q">“{esc(UN_QUOTES[key])}”</span><cite>{cite}</cite></blockquote>')

    def front(self):
        """The Kherson drone campaign: the UN's finding, the circle's own ties to the formations it names, and how the
        units' channels describe their targets. Three layers, each at the level its documents support."""
        intro = (
            f'<p class="lede">In May 2025 the UN\'s Independent International Commission of Inquiry on Ukraine concluded that '
            f'Russian drone operators on the left bank of the Dnipro had spent ten months attacking civilians in Kherson, and '
            f'that the attacks amount to the crime against humanity of murder{self.tref("un_crp")}. In October it extended the '
            f'finding to 300 km of the river and three regions, and named the formation the operators serve in:</p>'
            + self.un_quote("dnepr", f'UN report A/80/497, para. 40, 21.10.2025{self.tref("un_ga")}') +
            f'<p>The Commission names the 18th Combined Arms Army; it names no brigade. The Centre for Information Resilience '
            f'and DW named the 205th among three units whose drones were at work over Beryslav during the attacks there, and '
            f'said they could not prove who carried them out{self.tref("cir")}. The 205th is a motor-rifle brigade, as DW\'s film labels it on a map{self.tref("dw_film")}; the channel '
            f'that posts its footage, under the brigade\'s emblem, places it in the 49th Army{self.tref("osv_27702")}. A senior '
            f'doctor at a Kherson hospital told the Commission:</p>'
            + self.un_quote("safari", f'UN paper A/HRC/59/CRP.2, para. 42, 28.05.2025{self.tref("un_crp")}'))
        np_ = self.ents[NP]
        rows = [
            ("«Arkhangel» drone school", "open",
             "TsBST's own channel says a resident's anti-drone simulator runs at the school's training centre in Tuapse"
             + self.tref("cbst_1562") + ". The school's channel recruits operators for the 205th brigade" + self.tref("arch_9067")
             + ", which it calls “the terror of Kherson region”" + self.tref("arch_10667")
             + ". The school says it trains within Bars-Sarmat, Dmitry Rogozin's drone centre" + self.ref("s6915") + "."),
            ("Bars-Sarmat", "rep",
             "Its commander, Dmitry Rogozin, says the centre fights for the commander of the Airborne Forces and that units of "
             "the «Dnepr» Group of Forces fit its munitions to their assault drones" + self.tref("rog_8057") + self.tref("rog_7780") + "."),
            (np_, "rep",
             "reports delivering 100 strike drones to fighters of the 49th Army on the Kherson direction in May 2024"
             + self.tref("np_280") + ", and a vehicle now used by the 18th Army to move cargo and troops to the front line"
             + self.tref("np_580") + "."),
            (self.ents["ooo-gagaring"], "rep",
             "the maker of the Kuznechik and Sova posts thanks from 49th Army air-defence crews who use the Sova to intercept "
             "drone video over the Dnipro" + self.tref("gag_2811") + "."),
        ]
        lis = []
        for who, g, text in rows:
            name = who if isinstance(who, str) else self.en(who, pop=True)
            lis.append(f'<li><span class="from">{name}</span>{ln(g)}<span class="what">{text}</span>'
                       f'<span class="rm-grade {g}">{esc({"doc": "Documented", "rep": "Reported", "open": "Not documented"}[g])}</span></li>')
        return (
            intro +
            '<h3 class="rm-h3">What TsBST\'s circle says about that front</h3>'
            f'<ul class="ledger front" aria-label="Ties to the formations the UN names">{"".join(lis)}</ul>'
            + self.oq("arch_9067", f'«Arkhangel», Telegram, 01.12.2025{self.tref("arch_9067")}')
            + (f'<p>DW\'s film on the Beryslav attacks shows the school too. In a passage on Russia\'s volunteer drone groups, '
               f'over footage of men soldering a drone at a workbench, watermarked with the school\'s channel address, its '
               f'narration says: “This Russian volunteer group proudly posts on Telegram” how it makes drones and trains '
               f'operators{self.tref("dw_film")}. The film does not say the school supplied the 205th, and the footage of the '
               f'attacks it shows is credited to another channel.</p>'
               '<p class="note"><span class="rm-grade rep">Reported</span> DW\'s own film, as press: it shows the school\'s '
               'footage as an example of such groups. It does not show the school\'s tie to TsBST, which is still not '
               'documented.</p>')
            + self.band(self.pics(["proekt-kb-arkhangel"]), "The «Arkhangel» school's own channel: its lab bench, a device it "
                        "builds, its flight-instruction video and its recruitment video. Its tie to TsBST is not documented.", big=2)
            + self.band(self.pics(["csn-bars-sarmat"]), "Bars-Sarmat's own, from its stand at «Dronnitsa 2025», a gathering "
                        "of combat drone operators in Novgorod region, 6–7 September 2025.", big=2) +
            '<h3 class="rm-h3">What the units say about their targets</h3>'
            f'<p>The Commission reproduces posts of a Kherson-front channel, «From Mariupol to the Carpathians», as figures in '
            f'its paper{self.tref("un_crp")}. The channel signs its strike videos with the units\' names. Under footage of the '
            f'205th brigade:</p>'
            + self.oq("osv_27702", f'«From Mariupol to the Carpathians», Telegram, 23.07.2025{self.tref("osv_27702")}') +
            '<p>Under a video of a van being struck in a residential yard:</p>'
            + self.oq("osv_19953", f'the same channel, 19.08.2024{self.tref("osv_19953")}') +
            '<p>And under the heading the platform used for its sellers:</p>'
            + self.oq("osv_36192", f'the same channel, 24.07.2026{self.tref("osv_36192")}')
            + self.oq("osv_38703", f'the same channel, 24.10.2026, over a clip watermarked by the 98th Airborne Division{self.tref("osv_38703")}')
            + self.kherson_band() +
            '<p class="note"><span class="rm-grade rep">Reported</span> The ties above are the parties\' own posts. They show '
            'TsBST\'s circle supplying and recruiting for the formations the UN names; they do not show that any item from it '
            'was used against civilians, and the UN names no unit below the army.</p>')

    def beyond_shop(self):
        """Two of TsBST's own lines on what it does besides the shop."""
        return (
            f'<p>TsBST presents itself as a support body for drone makers, and ROY.MARKET as a catalogue. Its own posts and its '
            'board secretary\'s describe more than that. It says it showed the marketplace at «Tsentr-2026», a strategic '
            'military exercise with delegations from 41 countries, and signed up sellers there:</p>'
            + self.oq("tsentr", f"TsBST, Telegram, 04.10.2026{self.tref('tsentr')}") + self.center_band() +
            f'<p>On 15 October its board secretary, the United Russia official {self.person_pop(SIDYAKIN)}, announced an app '
            f'that assigns incoming Ukrainian drones to mobile fire teams in Kursk region, and placed it inside a TsBST system:</p>'
            + self.oq("yakim", f"Sidyakin, Telegram, 15.10.2026{self.tref('yakim')}") +
            '<p class="note"><span class="rm-grade rep">Reported</span> Both are the parties\' own claims; no document on file '
            'shows the system in service.</p>')

    def origin(self):
        """How the investigation got here, in six steps; each step carries its own picture."""
        recruit = self.mclaim(MPTM, "s8854")
        only = self.claim("ooo-trimiks", "только у нас")
        steps = [
            ("We had been watching Wildberries",
             '<p>The investigation started as <a href="https://amethyst-deceiver2001.github.io/wb-watcher/">WB Watch</a>, a tracker of '
             'military goods sold on Russia\'s largest consumer marketplace. It found a large, open trade in kit for the war.</p>'
             '<div class="figs"><div class="fig"><span class="n">7,666</span><span class="w">military-item listings</span></div>'
             '<div class="fig"><span class="n">89%</span><span class="w">shipped from Wildberries\' own warehouses</span></div>'
             '<div class="fig"><span class="n">802</span><span class="w">sellers</span></div></div>'),
            ("Then a military marketplace announced itself",
             f'<p>In December 2025 Sidyakin wrote that the '
             f'party, Bank PSB and TsBST had launched a military marketplace. In August 2026 the platform opened to outside sellers '
             f'and named the ones it wanted first.</p>'
             + quote_html(recruit["text_ru"], latinize_gloss(recruit["text_en"]),
                          f"ROY.MARKET's announcement, {ru_date(recruit['as_of'])}{self.ref(recruit['source_id'])}", "q-recruit")
             + self.step_shot(3, "ROY.MARKET's page for prospective sellers as it reads now, captured 24.10.2026. The August version "
                                 "is archived as text only. The catalogue itself is behind a login.")
             + '<p>Its target was the seller base we had already mapped.</p>'),
            ("The site hid its operator. An older copy did not",
             f'<p>The platform\'s public terms print the operator as “OOO «****»”. A copy archived on 22.08.2026 names it: '
             f'{self.pop(MPTM)}, INN 9714068459. TsBST\'s own report to the Justice Ministry lists the same company as one it has '
             f'taken part in since the day it was registered.</p>{self.masked()}'),
            ("First guess: the usual sellers, plus TsBST's residents",
             '<p>If the platform recruits Wildberries sellers, and TsBST runs a residency for drone makers, the likely suppliers are '
             'makers that are both. We checked every maker on file against the Wildberries sellers by INN.</p>' + self.test_bar()),
            ("The check missed the best case",
             f'<p>«Bulat», a drone detector shown at Dronnitsa 2025, a showcase TsBST takes part in, returned nothing: no Wildberries seller carries its '
             f'maker\'s INN. The detector is on sale all the same, through dealers and sole traders. A sanctions screen keyed on the '
             f'maker\'s identifier would make the same mistake.</p>{self.blind_spot()}'),
            ("The marketplace is one outlet among several",
             f'<p>Asked whether the new «Bulat» would go on ROY.MARKET, 3mx answered:</p>'
             + quote_html(only["text_ru"], latinize_gloss(only["text_en"]),
                          f"3mx, in its customer chat, {ru_date(only['as_of'])}{self.ref(only['source_id'])}", "q-3mx") +
             '<p>The detector reaches units another way: a foundation that co-founded TsBST buys it and posts the handovers. So we '
             'stopped following the platform and started following products, from the maker to the people who receive them.</p>'
             + self.models()),
        ]
        return "".join(f'<li class="step"><h3 class="rm-h3">{esc(h)}</h3>{body}</li>' for h, body in steps)

    def more_cards(self, preview):
        """The company file and the foundation story, linked only in the preview until they are public."""
        from build_company_page import COMPANY_PAGES   # noqa: E402
        cards = []
        for slug, url in COMPANY_PAGES.items():
            e = self.ents[slug]
            href = url if preview else None
            cards.append(f'<article class="rm-card chain-card"><header><span class="rm-kind">Company file</span>{self.logo(slug)}</header>'
                         f'<h3 class="rm-name">{f"<a href={chr(34)}{esc(href)}{chr(34)}>" if href else ""}{self.name(e, sub=False)}'
                         f'{"</a>" if href else ""}</h3>{self.sanctions(e)}<p class="row">Register history, people, sanctions, '
                         f'accounts, products, pictures and the company in its own words.</p>'
                         + (f'<p class="go"><a href="{esc(href)}">Open the company file →</a></p>' if href
                            else '<p class="go wait">The company file is in review and not yet public.</p>') + '</article>')
        if preview and STORY:
            cards.append(f'<article class="rm-card chain-card"><header><span class="rm-kind">Story</span>{self.logo(NP)}</header>'
                         f'<h3 class="rm-name"><a href="{esc(STORY)}">Aid for the Zone</a><small>How {self.en(self.ents[NP])} '
                         f'raises money, co-founded TsBST and hands equipment to units</small></h3>'
                         f'<p class="go"><a href="{esc(STORY)}">Read the story →</a></p></article>')
        if preview:
            for kind, title, line, url in MORE:
                cards.append(f'<article class="rm-card chain-card"><header><span class="rm-kind">{esc(kind)}</span></header>'
                             f'<h3 class="rm-name"><a href="{esc(url)}">{esc(title)}</a><small>{esc(line)}</small></h3>'
                             f'<p class="go"><a href="{esc(url)}">Open →</a></p></article>')
        return "".join(cards)

    def chain_card(self, slug, href):
        """href None: the chain view is not public yet, so the card states that instead of linking."""
        ch = Chain(slug)
        ch.img_dir = REPO / "exhibits" / "images" / "media"   # the chain's own pictures never go to this page's folder
        ch.build()
        p, m = ch.p, ch.maker
        n_buy = sum(len([b for b in r["buyers"] if "k-buyer" in b]) for r in ch.rows)
        n_list = sum(1 for li in p.get("listings") or [] if li.get("source_id"))
        n_del = len(p.get("deliveries") or [])
        logo = self.logo(p["maker"])   # only the logo is published with this page
        regimes = self.sanctions(m)
        return (f'<article class="rm-card chain-card"><header><span class="rm-kind">Chain view</span>{logo}</header>'
                f'<h3 class="rm-name">{f"<a href={chr(34)}{esc(href)}{chr(34)}>{esc(ch.pq_en)}</a>" if href else esc(ch.pq_en)}<small>{esc(cap(p.get("category")))} made by '
                f'{ch.en(m)}{(" (" + esc(display_name(m)["latin"]) + ")") if display_name(m)["legal"] else ""}</small><small class="cyr" lang="ru">{esc(ch.pq)}</small></h3>'
                f'{regimes}<dl class="counts"><div><dt>Sale channels</dt><dd>{len(ch.rows)}</dd></div>'
                f'<div><dt>Listings</dt><dd>{n_list}</dd></div><div><dt>State contracts</dt><dd>{n_buy}</dd></div>'
                f'<div><dt>Handovers to units</dt><dd>{n_del}</dd></div></dl>'
                + (f'<p class="go"><a href="{esc(href)}">Follow {esc(ch.pq_en)} from TsBST to the front line →</a></p>' if href
                   else '<p class="go wait">The chain view is in review and not yet public.</p>') + '</article>')


def unique_popovers(doc):
    """The same name can be mentioned twice; each button and its popover get a numbered id so they stay paired."""
    count = {}

    def one(m):
        pid = m.group(1)
        count[pid] = count.get(pid, 0) + 1
        new = pid if count[pid] == 1 else f"{pid}-r{count[pid]}"   # "-r": pop() already numbers its own ids "-N"
        return m.group(0).replace(f'popovertarget="{pid}"', f'popovertarget="{new}"').replace(f'id="{pid}"', f'id="{new}"')
    return re.sub(r'popovertarget="(nm-[^"]+)".*?<span popover id="\1"', one, doc, flags=re.S)


# The chain view's picture viewer, shared rather than copied: everything in chain_view.js from its comment on.
# The contents bar: (section heading id, short label), in page order.
TOC_ITEMS = [("h-open", "The strike"), ("h-limits", "Limits"), ("h-hub", "Who stands behind"), ("h-front", "The front"),
             ("h-beyond", "Beyond the shop"), ("h-chains", "Products"), ("h-net", "Network"), ("h-origin", "How we found it"),
             ("h-read", "How to read"), ("h-method", "Method"), ("h-sources", "Sources")]
TOC = ('<nav class="toc" aria-label="Contents"><ol>' + "".join(f'<li><a href="#{i}">{esc(t)}</a></li>' for i, t in TOC_ITEMS)
       + '</ol></nav>')
FOLD_JS = """// Open the sources fold when a footnote link or an address points into it
(function () {
  var f = document.getElementById('sources-fold');
  if (!f) return;
  function open(h) { if (/^#n\\d+$/.test(h) && !f.open) f.open = true; }
  document.addEventListener('click', function (e) {
    var a = e.target.closest('a[href^="#n"]');
    if (a) open(a.getAttribute('href'));
  });
  window.addEventListener('hashchange', function () { open(location.hash); });
  open(location.hash);
})();
"""
TOC_JS = """// Contents bar: mark the section in view
(function () {
  var links = document.querySelectorAll('.toc a');
  if (!links.length || !('IntersectionObserver' in window)) return;
  var byId = {};
  links.forEach(function (a) { byId[a.getAttribute('href').slice(1)] = a; });
  var seen = {};
  function mark() {
    var cur = null;
    Object.keys(byId).forEach(function (id) { if (seen[id]) cur = id; });
    links.forEach(function (a) { a.removeAttribute('aria-current'); });
    if (cur) {
      byId[cur].setAttribute('aria-current', 'true');
      var bar = byId[cur].closest('ol');
      var a = byId[cur];
      if (bar && (a.offsetLeft < bar.scrollLeft || a.offsetLeft + a.offsetWidth > bar.scrollLeft + bar.clientWidth)) {
        bar.scrollTo({left: a.offsetLeft - 16, behavior: 'smooth'});
      }
    }
  }
  var io = new IntersectionObserver(function (es) {
    es.forEach(function (e) { seen[e.target.id] = e.isIntersecting; });
    mark();
  }, {rootMargin: '-52px 0px -60% 0px'});
  Object.keys(byId).forEach(function (id) { var h = document.getElementById(id); if (h) io.observe(h); });
})();
"""
VIEWER_JS = "// Picture viewer" + (REPO / "exhibits" / "chain_view.js").read_text().split("// Picture viewer", 1)[1]


def render(preview: bool, out: Path):
    L = Landing()
    L.img_dir = out.parent / "images" / "media"
    L.preview = preview
    c = L.ents[CBST]
    today = dt.date.today().isoformat()
    # Called in page order, so footnotes number from the top.
    hero_style, hero_credit = L.hero()
    opening = L.opening()
    qa, qb, qref = L.quote()
    cbst_name, cbst_sanc, funds = L.name(c), L.sanctions(c), L.money_line()
    sid_name = L.person_pop(SIDYAKIN)
    sid_name_l = sid_name.replace(f'id="nm-{SIDYAKIN}"', f'id="nm-{SIDYAKIN}-q"').replace(
        f'popovertarget="nm-{SIDYAKIN}"', f'popovertarget="nm-{SIDYAKIN}-q"')
    ledger = L.ledger()
    handed = L.pics([NP], {"handover"})
    handovers = L.band(handed, f"Published by «Nasha Pravda» with its handover posts, {ru_date(handed[0]['published'])} – "
                       f"{ru_date(handed[-1]['published'])}: deliveries of «Bulat» detectors and other kit to units. A handover "
                       "does not show use in combat.", big=3, lead=("m0085", "m0070", "m0083")) if handed else ""
    front = L.front()
    beyond = L.beyond_shop()
    chains = "".join(L.chain_card(s, url if preview else (f"chain_{s}.html" if (out.parent / f"chain_{s}.html").exists() else None))
                     for s, url in CHAINS.items())
    extra_cards = L.more_cards(preview)
    n, by, sanc = L.network()
    shown = {m["id"] for m in L.pics(["ooo-gagaring", "ano-dpo-obrazovatelny-tsentr-gagaring", NP, "csn-bars-sarmat", "proekt-kb-arkhangel"])}
    own = L.band(L.pics([s for s in L.tied() if s != CBST], skip=shown | {L.HERO}),
                 "What the linked organisations publish of themselves: products, shops, exhibition stands, workshops and "
                 "handovers. "
                 "Product pictures are evidence of what a company offers, not of sales.", big=4)
    wall = L.wall()
    sgrid, undated = L.sanctions_grid()
    revenue, n_rev = L.revenue_bars()
    origin, timeline = L.origin(), L.timeline()
    restr_date, restr_ref = L.restricted()
    lead_quote = quote_html(f"{qa['text_ru']} […] {qb['text_ru']}",
                            latinize_gloss(f"{qa['text_en']} […] {qb['text_en']}"),
                            f"{sid_name_l}, secretary of TsBST's supervisory board and head of United Russia's central executive committee, "
                            f"on TsBST's year, Telegram, {ru_date(qb['as_of'])}{qref}", "q-lead").replace(
                                '<blockquote class="rm-quote">', '<blockquote class="rm-quote lead-quote">', 1)
    doc = f"""<!doctype html>
<!-- Generated by exhibits/build_landing.py from data/registry on {today}. Do not edit by hand. -->
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ROY.MARKET Investigation</title>
<meta name="description" content="An open-source investigation of ANO TsBST, a Moscow non-profit for the drone industry, its military marketplace ROY.MARKET, and the companies, products and handovers around them. Every claim is graded by the document behind it.">
<meta property="og:type" content="article"><meta property="og:site_name" content="ROY.MARKET Investigation">
<meta property="og:title" content="TsBST and ROY.MARKET: a Moscow non-profit, its military marketplace, and the drone-war supply around it">
<meta property="og:description" content="Every claim rests on an archived document and is graded by how well that document shows it.">
<meta name="twitter:card" content="summary">
{design_head((REPO / 'exhibits' / 'landing.css').read_text(), None if preview else 'fonts/fonts.css')}</head>
<body>
<div class="hero"{hero_style}><header class="rm-page top">
  <p class="rm-eyebrow">Draft · {ru_date(today)}</p>
  <h1 class="rm-h1">TsBST and ROY.MARKET <span class="rm-muted">a Moscow non-profit, its military marketplace, and the drone-war supply around it</span></h1>
  <p class="rm-dek">An open-source investigation of ANO «TsBST», a Moscow non-profit for the drone industry, and of the
  companies, products, sales and handovers to military units that connect to it. Every claim rests on an archived
  document and is graded by how well that document shows it.</p>
  {hero_credit}
</header></div>
{TOC}
<main class="rm-page">
  <section class="open" aria-labelledby="h-open">
    <h2 class="rm-h2" id="h-open">A strike, then a sales line</h2>
    {opening}
  </section>

  <section class="limits" aria-labelledby="h-limits">
    <details open><summary><h2 class="rm-h2" id="h-limits">What this does not show</h2></summary>
    <ul>
      <li>A handover to a unit does not show that the equipment was used in combat. Some recipients are rear units.</li>
      <li>TsBST's share in the company that runs ROY.MARKET is not stated in any document on file, and since
      {restr_date} the company register withholds who owns that company{restr_ref}.</li>
      <li>A US sanctions entry under a similar name belongs to a different company registered in Tula. TsBST itself is
      not shown here as sanctioned by the US.</li>
      <li>This is a draft. The earlier case studies and company profiles were withdrawn while the site is rebuilt
      around chain views.</li>
    </ul>
    </details>
  </section>

  <section class="hub" aria-labelledby="h-hub">
    <h2 class="rm-h2" id="h-hub">Who stands behind TsBST</h2>
    <p class="lede">The seller in that post is not an ordinary shop. TsBST's co-founders on the company register are a donor foundation and a state-owned bank; TsBST names the ruling party as a third, and the head of the party's central executive committee is secretary of its supervisory board.</p>
    {lead_quote}
    <div class="hub-grid">
      <article class="rm-card hub"><header><span class="rm-kind">Hub</span>{L.logo(CBST)}</header>
        <h3 class="rm-name">{cbst_name}</h3>{cbst_sanc}
        <p class="row">Targeted funding received: {funds}. These are a non-profit's funds, not revenue.</p>
        <p class="row"><span class="rm-id">INN {esc(c['inn'])}</span> <span class="rm-id">OGRN {esc(c['ogrn'])}</span></p></article>
      <ul class="ledger" aria-label="Relations">{ledger}</ul>
    </div>
    {handovers}
  </section>

  <section class="front-sec" aria-labelledby="h-front">
    <h2 class="rm-h2" id="h-front">The front it supplies</h2>
    {front}
  </section>

  <section class="beyond" aria-labelledby="h-beyond">
    <h2 class="rm-h2" id="h-beyond">More than a marketplace</h2>
    {beyond}
  </section>

  <section aria-labelledby="h-chains">
    <h2 class="rm-h2" id="h-chains">Follow a product</h2>
    <p class="lede">A chain view follows one product from TsBST and its events to the maker, the shops and dealers that
    sell it, the state agencies that buy it and the units that receive it. Each line is drawn in the style of its evidence.</p>
    <div class="chains">{chains}{extra_cards}
      <aside class="rm-card absent"><header><span class="rm-kind">Next</span></header>
        <p>More chain views follow one product at a time, each after its record has been read in full.</p></aside>
    </div>
  </section>

  <section aria-labelledby="h-net">
    <h2 class="rm-h2" id="h-net">The network on file</h2>
    <p class="lede">The investigation's registry links <b>{n}</b> organisations to TsBST: {by['doc']} through a document
    (a register entry, a contract, TsBST's own posts), {by['rep']} on their own word or press reports alone.
    <b>{sanc}</b> of them are on at least one sanctions list. Counted from the registry on {ru_date(today)}.</p>
    {own}
    <details class="fold"><summary>Show all {n} organisations, with logos and charts</summary>
    <figure class="netfig">{wall}
      <figcaption>Every organisation the registry links to TsBST, with its logo where one is on file. A red flag names
      the regimes that list it.</figcaption></figure>
    <div class="net2">
      <figure class="netfig"><h3 class="rm-h3">When they were listed</h3><div class="sg-scroll">{sgrid}</div>
        <figcaption>Linked organisations first listed by each regime, by year of the listing on file. {undated} listings
        carry no date in the record and are not drawn.</figcaption></figure>
      <figure class="netfig"><h3 class="rm-h3">How large they are</h3>{revenue}
        <figcaption>Revenue as filed in each company's annual accounts, latest year on file; the pale bar is the year
        before. A Reported bar comes from press citing an accounts database, not from the filing itself.
        {n_rev} of the {n} organisations have accounts on file. Non-profits' funds are not revenue and are left out.</figcaption></figure>
    </div>
    </details>
  </section>

  <section class="origin" aria-labelledby="h-origin">
    <h2 class="rm-h2" id="h-origin">How we found it</h2>
    <p class="lede">We did not set out to investigate TsBST. We were following military goods on a consumer marketplace,
    and a new marketplace came looking for the same sellers.</p>
    <ol class="steps">{origin}</ol>
    <h3 class="rm-h3">The dates</h3>
    {timeline}
  </section>

  <section class="read" aria-labelledby="h-read">
    <h2 class="rm-h2" id="h-read">How to read the evidence</h2>
    <ul class="rm-legend">
      <li>{ln("doc", 34)} <span class="rm-grade doc">Documented</span> <span>A primary document shows it: a register extract, a state contract, an annual filing, a trademark or patent record.</span></li>
      <li>{ln("rep", 34)} <span class="rm-grade rep">Reported</span> <span>One party's own word (its posts, its website, its listings), or the press. Donors' handover posts are graded here until a second source confirms them.</span></li>
      <li>{ln("open", 34)} <span class="rm-grade open">Not documented</span> <span>Drawn to complete the picture, but no document on file shows it. The line's own note says what is missing.</span></li>
    </ul>
    <p>Red marks only a sanctions listing, and always names the regimes. Names appear as registered, in Russian; a
    company known by its brand is shown by the brand, with the registered name beneath it.</p>
  </section>

  <section class="rm-prose" aria-labelledby="h-method">
    <h2 class="rm-h2" id="h-method">How this is made</h2>
    <ul>
      <li>Facts come from the original Russian documents, read in full: company register extracts, annual accounts,
      procurement records, trademark records, court filings and the parties' own Telegram posts and websites.
      Summaries and machine translations are leads, never sources.</li>
      <li>Every document is archived and hashed when it is collected. Each note at the end of a page says what the
      document is and links to it where a public copy exists.</li>
      <li>Pictures are evidence only for what they show, and each says who published it. Faces of people taking part
      are shown; nobody is named from a face.</li>
    </ul>
  </section>

  <section class="rm-prose rm-sources" aria-labelledby="h-sources"><h2 class="rm-h2" id="h-sources">Sources</h2>
    <details class="fold" id="sources-fold"><summary>Full list of sources <span class="count">{len(L.notes)}</span></summary><ol>{L.notes_list()}</ol></details></section>
</main>
{''.join(f'<template id="fig-{k}">{v}</template>' for k, v in L.templates.items())}
<dialog class="rm-lightbox" id="lightbox" aria-label="Picture"><div class="bar"><button type="button" data-close>Close</button></div><div class="body"></div></dialog>
<script>{VIEWER_JS}
{NAME_JS}
{TOC_JS}
{FOLD_JS}</script>
</body></html>
"""
    out.write_text(unique_popovers(popup_originals(doc)))
    print(f"wrote {out.relative_to(REPO) if out.is_relative_to(REPO) else out}: {len(L.notes)} sources, {n} tied organisations, {len(L.media_files)} pictures")
    return L


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true", help="link chain views to their preview Artifacts")
    ap.add_argument("--out")
    a = ap.parse_args()
    render(a.preview, Path(a.out).resolve() if a.out else REPO / "exhibits" / "landing.html")


if __name__ == "__main__":
    main()
