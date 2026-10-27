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
from display_helpers import NAME_JS, support_block_html, design_head, display_name, guillemets, latin_text, latinize_gloss, media_about, media_caption, name_html, orig_line, person_names, popup_originals, quote_html, reader_grade, ru_date, sanction_regimes  # noqa: E402
from graph_contract import source_grade  # noqa: E402

MPTM, NP, PSB, SIDYAKIN = "ooo-mptm", "fond-nasha-pravda", "pao-bank-psb", "aleksandr-sidyakin"
# One entry per published chain view: product slug -> private preview Artifact (until the public cutoff).
CHAINS = {"bulat": "https://claude.ai/artifact/6UaTv2jSwdNdfNUCibCwrf",
          "kapyushon": "https://claude.ai/artifact/5iYx5RsGmTRrAeooi8wdPd"}
# The foundation story's private preview; the public page links it only once it is published in docs/.
STORY = "https://claude.ai/artifact/DfLGJYwQY5mENE31J4tf8u"
# One line under each company card's name, so a reader knows why to open it. Each line says only what that
# company file itself sources.
FILE_LINES = {   # (line, source ids it rests on)
    "ooo-trimiks": ("Makes the «Bulat» drone detector, holds a patent on its design and is suing GoDrone over it", ("L0567", "L0558")),
    "ovod": ("Makes the «Ovod» family of FPV strike drones, some of them guided over optical fibre", ("s6456",)),
    "ooo-goudron": ("Trades as GoDrone and makes the «Nabat» drone detector; Trimiks is suing it over a detector patent", ("L0485", "L0558")),
    "ooo-skb-piranya": ("Makes the «Piranya» FPV strike drones and says it delivers drones directly to recipients in the «LNR» and «DNR»", ("s1411",)),
    "csn-bars-sarmat": ("Dmitry Rogozin's volunteer drone centre, which he says fights for the commander of the Airborne Forces", ()),
}
# Other preview pages: (kind, title, one line, preview Artifact)
MORE = [("People", "One person, many companies", "The people who direct or own two or more of the companies on file",
         "https://claude.ai/artifact/RDUCMFfzWc5G6f62sV9dTT", None),
        ("Project file", "«Arkhangel»", "A drone school that trains operators for the army and publishes an interceptor drone's parts list",
         "https://claude.ai/artifact/RABnZkrCUwktU5b91cNZTn", "proekt-kb-arkhangel")]

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
    "arch_175293": ("Telegram, @Archangel_Forum, post 175293, 08.03.2026", "https://t.me/Archangel_Forum/175293"),
    "cbst_1976": ("Telegram, @ANO_CBST, post 1976, 17.03.2026", "https://t.me/ANO_CBST/1976"),
    "yakim": ("Telegram, @asidyakin (Alexander Sidyakin), post 1405, 15.10.2026", "https://t.me/asidyakin/1405"),
    # The supplier page and the Kherson section (24.10.2026): saved as WEBCAPTURE/PDF files on this machine, not catalogued.
    "rm_aug": ("ROI.MARKET, «Начать продавать на РОЙ.МАРКЕТ» (page for prospective sellers), Internet Archive copy of 22.08.2026",
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
    "osv_38645": ("Telegram, @osvedomitell_alex, post 38645, 22.10.2026", "https://t.me/osvedomitell_alex/38645"),
    "osv_20344": ("Telegram, @osvedomitell_alex, post 20344, 28.08.2024", "https://t.me/osvedomitell_alex/20344"),
    "osv_20801": ("Telegram, @osvedomitell_alex, post 20801, 15.09.2024", "https://t.me/osvedomitell_alex/20801"),
    "osv_20993": ("Telegram, @osvedomitell_alex, post 20993, 22.09.2024", "https://t.me/osvedomitell_alex/20993"),
    "osv_21384": ("Telegram, @osvedomitell_alex, post 21384, 06.10.2024, signed @habr_bpla", "https://t.me/osvedomitell_alex/21384"),
    "osv_34459": ("Telegram, @osvedomitell_alex, post 34459, 15.05.2026", "https://t.me/osvedomitell_alex/34459"),
    "rog_7047": ("Telegram, @rogozin_do (Dmitry Rogozin), post 7047, 22.04.2025", "https://t.me/rogozin_do/7047"),
    "rog_8057": ("Telegram, @rogozin_do (Dmitry Rogozin), post 8057, 19.01.2026", "https://t.me/rogozin_do/8057"),
    "rog_7780": ("Telegram, @rogozin_do (Dmitry Rogozin), post 7780, 12.11.2025", "https://t.me/rogozin_do/7780"),
    "np_280": ("Telegram, @nashapravdafond, post 280, 07.05.2024", "https://t.me/nashapravdafond/280"),
    "np_580": ("Telegram, @nashapravdafond, post 580, 05.03.2026", "https://t.me/nashapravdafond/580"),
    "gag_2811": ("Telegram, @my_el_lab (Gagaring), post 2811, 23.12.2025", "https://t.me/my_el_lab/2811"),
    # Pictures in the ties diagram (25.10.2026): the credit and licence the photograph needs travel with it.
    "sid_photo": ("Photograph of Aleksandr Sidyakin by Karmaks, 28.09.2016, Wikimedia Commons, licence CC BY-SA 4.0", "https://commons.wikimedia.org/wiki/File:SidyakinA.G..jpg"),
    "privacy": ("ROI.MARKET privacy policy, revision 2.0, on roimarket.ru, captured 26.10.2026", "https://roimarket.ru/privacy"),
    "natural_earth": ("Natural Earth, 1:10m rivers and lake centerlines (public domain); the Dnipro's course on the map is drawn from it",
                      "https://www.naturalearthdata.com/downloads/10m-physical-vectors/10m-rivers-lake-centerlines/"),
    "gur_logos": ("War & Sanctions, the database of Ukraine's Defence Intelligence (GUR): company pages, logos as shown there",
                  "https://war-sanctions.gur.gov.ua/en"),
    "deepstate": ("DeepState, the map of the front line, latest state of 23.10.2026 (its own data download); the Russian-held area is drawn from it",
                  "https://deepstatemap.live/en"),
    "emb_sv": ("Small emblem of the Russian Ground Forces (collar insignia), public domain, Wikimedia Commons",
               "https://commons.wikimedia.org/wiki/File:Small_emblem_of_the_Russian_Ground_Forces.svg"),
    "emb_vdv": ("Small emblem of the Russian Airborne Forces, public domain, Wikimedia Commons",
                "https://commons.wikimedia.org/wiki/File:Small_emblem_of_the_Russian_Airborne_Forces.svg"),
    "emb_gru": ("Emblem of the GRU's special-purpose units as circulated (not an official emblem), public domain, Wikimedia Commons",
                "https://commons.wikimedia.org/wiki/File:Spetsnaz_emblem.svg"),
    "rm_logo": ("ROI.MARKET's logo, as served by the platform's own site, roimarket.ru", "https://roimarket.ru/logo-400.png"),
    "er_logo": ("United Russia's logo, as hosted on Russian Wikipedia and credited there to the party's official site",
                "https://ru.wikipedia.org/wiki/%D0%A4%D0%B0%D0%B9%D0%BB:%D0%9B%D0%BE%D0%B3%D0%BE%D1%82%D0%B8%D0%BF_%D0%BF%D0%B0%D1%80%D1%82%D0%B8%D0%B8_%22%D0%95%D0%B4%D0%B8%D0%BD%D0%B0%D1%8F_%D0%A0%D0%BE%D1%81%D1%81%D0%B8%D1%8F%22.svg"),
}
# Two lines of the supplier page, read from the saved copies; not in the Telegram scrape, so not checked by oq().
SUPPLIER_LINES = {
    "dual": ("РОЙ.МАРКЕТ - защищённый канал продаж товаров двойного назначения.",
             "ROI.MARKET is a secure sales channel for dual-use goods."),
    "special": ("РОЙ.МАРКЕТ - защищённый канал продаж товаров специального назначения.",
                "ROI.MARKET is a secure sales channel for special-purpose goods."),
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
             "the «Sova 5.8» remote video receiver. […] Servicemen can order them on ROI.MARKET, the specialised platform "
             "for dual-use goods."),
    "tsentr": ("ANO_CBST", 2610,
               "Учения посетил Президент России Владимир Путин. […] В ходе выставки представители ЦБСТ договорились более "
               "чем с 10 участниками о размещении их ассортимента на платформе РОЙ.МАРКЕТ.",
               "The exercise was visited by the President of Russia, Vladimir Putin. […] During the exhibition, TsBST "
               "representatives agreed with more than 10 participants to place their range on the ROI.MARKET platform."),
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
    "osv_38645": ("osvedomitell_alex", 38645,
                  "Херсон. Красная зона. […] Объективный контроль уничтожения живой силы противника на первом берегу переодетого по \"гражданке\". Все цели подтверждены",
                  "Kherson. Red zone. […] Objective monitoring of the destruction of enemy manpower on the first bank, disguised "
                  "in \"civilian\" clothes. All targets confirmed"),
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
# the ROI.MARKET booklet. The other four (the range) are not used. Each looked at full size 24.10.2026. Fetched from the public preview; not catalogued on this Mac (no source ids here), so like the Kherson
# stills they appear on the private preview only. key: (file in exhibits/images/center2026, what the frame shows,
# (verbatim Russian, English) of a line printed in it or None)
CENTER_STILLS = [
    ("c2605-1.jpg", "TsBST's stand at «Tsentr-2026».", None),
    ("c2605-2.jpg", "ROI.MARKET's printed leaflets and patch.", None),
]

KHERSON_STILLS = {
    "osv_27702": (27702, "k27702.jpg", "Still from the video: a ruined house in Kazatskoe, under the “205 brigade” emblem.",
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
    "osv_38703": (38703, "k38703.jpg", "Still from the video: a van lettered “RITUAL” (funeral services), watermarked by the 98th Airborne Division.",
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
        self.out_dir = REPO / "exhibits"
        self.k_inline = set()   # Kherson stills already set under a quote
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

    def ledger_rows(self):
        """Who stands behind ЦБСТ and what it holds: graded relations (from, grade, text, note, to). Built once, because
        each call numbers its footnotes."""
        if getattr(self, "_ledger_rows", None):
            return self._ledger_rows
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
                     f"named by TsBST on {ru_date(sid['from'])} as secretary of its supervisory board and head of United Russia's "
                     "central executive committee", self.ref(sid.get("source_id")), None))
        rows.append((self.ents[NP], self.g(np_f.get("source_id")), f"co-founder of TsBST since its registration on {ru_date(reg)}",
                     self.ref(np_f.get("source_id")), self.ents[CBST]))
        rows.append((self.ents[PSB], self.g(psb_f.get("source_id")), f"co-founder of TsBST since its registration on {ru_date(psb_f.get('as_of'))}",
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
        rows.append((self.ents[MPTM], self.g(offer), "the operator of the ROI.MARKET marketplace, by the platform's own supplier offer",
                     self.ref(offer), None))
        # The platform's own word that units buy on it: TsBST's posts on connected units (marketing claims of MPTM).
        tech, conn = self.mclaim(MPTM, "s8852"), self.mclaim(MPTM, "s8857")
        rows.append(("ROI.MARKET", self.g(conn["source_id"]),
                     f"says military units buy on it directly: TsBST's posts speak of units “connected to ROI.MARKET” "
                     f"({ru_date(conn['as_of'])}) and plan to connect all the Defence Ministry's technical-maintenance units by "
                     f"1 September 2026 ({ru_date(tech['as_of'])}); no order by a unit is on file",
                     self.ref(conn["source_id"]) + self.ref(tech["source_id"]), None))
        stock = next((c for c in self.p.get("claims") or [] if c.get("metric") == "donor_stock" and c.get("entity") == NP), None)
        if stock:
            n = re.search(r"Кол\. (\d+)", stock["text_ru"])
            rows.append((self.ents[NP], self.g(stock["source_id"]),
                         f"held {n.group(1) if n else 'a stock of'} «Bulat» on {ru_date(stock['as_of'])}, bought for transfer "
                         "to military units, by its audited accounts; the seller is not named",
                         self.ref(stock["source_id"]), None))
        # the fund's own posts only: the party's channels re-report some of the same handovers
        ds = [d for d in self.p.get("deliveries") or [] if d.get("donor") == NP and d.get("source_channel") == "@nashapravdafond"]
        mil = sorted((d for d in ds if d.get("recipient_kind") != "civilian" and d.get("date")), key=lambda d: d["date"])
        civ = [d for d in ds if d.get("recipient_kind") == "civilian"]
        if mil:
            civ_txt = "".join(f", and once to district heads in Kherson region for power-repair crews ({ru_date(d['date'])})"
                              for d in civ[:1])
            rows.append((self.ents[NP], reader_grade(mil[0].get("credibility")),
                         f"reports handing «Bulat» drone detectors to military units in {len(mil)} of its posts, "
                         f"{ru_date(mil[0]['date'])} to {ru_date(mil[-1]['date'])}{civ_txt}; each handover is cited in the chain view",
                         self.ref(mil[0].get("source_id"), *[d.get("source_id") for d in civ[:1]]), None))
        self._ledger_rows = rows
        return rows

    def ledger(self):
        """The ledger as a list: the same rows the ties diagram draws, with their notes."""
        out = []
        for a, g, text, ref, b in self.ledger_rows():
            out.append(f'<li><span class="from">{a if isinstance(a, str) else self.en(a, pop=True)}</span>{ln(g)}<span class="what">{esc(text)}{ref}</span>'
                       f'<span class="rm-grade {g}">{esc({"doc": "Documented", "rep": "Reported", "open": "Not documented"}[g])}</span></li>')
        return "".join(out)

    def ties_diagram(self):
        """The ledger's relations as one picture: who holds TsBST, who sits on its board, what it takes part in, and the
        donor's handovers. Line style is the grade of the row it draws (rm-ln). The notes stay in the list beside it."""
        rows = self.ledger_rows()
        gr = {"ur": rows[0][1], "sid": rows[1][1], "np": rows[2][1], "psb": rows[3][1], "mptm": rows[4][1], "op": rows[5][1], "units": rows[6][1],
              "del": rows[-1][1]}
        nh = len([d for d in self.p.get("deliveries") or [] if d.get("donor") == NP])

        def lat(slug):
            return display_name(self.ents[slug])["latin"]
        W, H = 1150, 350
        box = {}
        pics = {}
        wanted = [("sid", next((x for x in self.media if x["id"] == "m0092"), None), "face"),
                  ("ur", next((x for x in self.media if x["id"] == "m0093"), None), "logo"),
                  ("rm", next((x for x in self.media if x["id"] == "m0094"), None), "logo")]
        for key, slug in (("np", NP), ("psb", PSB), ("cbst", CBST)):   # the entity's own logo, as its cards show it
            wanted.append((key, next((x for x in media_about(self.media, {("entity", slug)}) if x.get("genre") == "logo"), None), "logo"))
        for key, m, kind in wanted:
            src = self.img(m) if m else None
            if src:
                pics[key] = (src, kind, "dark" if m.get("logo_ground") == "dark" else "light")

        def node(key, x, y, w, title, sub, cls="", pic=None):
            h = 58
            box[key] = (x, y, w, h)
            tx = x + w / 2
            img = ""
            if pic:   # a picture of the party's logo or the person, 42 px, at the left of the box
                href, kind, ground = pic
                plate = (f'<rect x="{x + 6}" y="{y + 6}" width="46" height="46" rx="4" class="plate {ground}"/>'
                         if kind == "logo" else "")
                img = (f'{plate}<image href="{esc(href)}" x="{x + 8}" y="{y + 8}" width="42" height="42" class="pic {kind}" '
                       f'preserveAspectRatio="xMidYMid {"slice" if kind == "face" else "meet"}"/>')
                tx = x + 54 + (w - 54) / 2
            return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" class="bx {cls}"/>{img}'
                    f'<text x="{tx}" y="{y + 25}" class="bt">{esc(title)}</text>'
                    f'<text x="{tx}" y="{y + 44}" class="bs">{esc(sub)}</text>')

        def edge(a, b, g, label="", ay=None, by=None, side="mid", dx=0, dy=-7):
            (ax, ay0, aw, ah), (bx, by0, bw, bh) = box[a], box[b]
            x1, y1 = ax + aw, (ay if ay is not None else ay0 + ah / 2)
            x2, y2 = bx, (by if by is not None else by0 + bh / 2)
            if side == "up":    # from the top-middle of a to the bottom-middle of b
                x1, y1, x2, y2 = ax + aw / 2, ay0, bx + bw / 2, by0 + bh
                d = f"M{x1} {y1} L{x2} {y2}"
                lx, ly, anchor = x1 + 10, (y1 + y2) / 2 + 4, "start"
            else:
                c = (x1 + x2) / 2
                d = f"M{x1} {y1} C{c} {y1} {c} {y2} {x2} {y2}"
                lx, ly, anchor = (x1 + x2) / 2 + dx, (y1 + y2) / 2 + dy, "middle"
            lab = f'<text x="{lx}" y="{ly}" class="lbl" text-anchor="{anchor}">{esc(label)}</text>' if label else ""
            return f'<path d="{d}" class="rm-ln {g}" marker-end="url(#ah3)"/>{lab}'
        n = [node("np", 10, 22, 190, lat(NP), "donor foundation", pic=pics.get("np")),
             node("psb", 10, 146, 190, lat(PSB), "state-owned bank", pic=pics.get("psb")),
             node("ur", 10, 270, 190, "United Russia", "ruling party", pic=pics.get("ur")),
             node("cbst", 380, 146, 190, lat(CBST), "non-profit, Moscow", "hub", pic=pics.get("cbst")),
             node("sid", 380, 270, 190, "Aleksandr Sidyakin", "board secretary", pic=pics.get("sid")),
             node("units", 760, 22, 140, "Military units", "recipients"),
             node("mptm", 760, 146, 140, lat(MPTM), "company"),
             node("rm", 970, 146, 170, "ROI.MARKET", "login-only catalogue", pic=pics.get("rm"))]
        e = [edge("np", "cbst", gr["np"], "co-founder", by=160, dx=-14, dy=-14),
             edge("psb", "cbst", gr["psb"], "co-founder", by=175, dx=-4, dy=-5),
             edge("ur", "cbst", gr["ur"], "named by TsBST as a founder", by=190, dx=46, dy=2),
             edge("sid", "cbst", gr["sid"], "sits on its board", side="up"),
             edge("sid", "ur", gr["sid"], "heads its central executive committee", ay=299, by=299, dy=-8),
             edge("np", "units", gr["del"], f"hands equipment to units: {nh} «Bulat» handovers posted", ay=51, by=51, dy=-9),
             edge("cbst", "mptm", gr["mptm"], "takes part; share not stated", dy=-9),
             edge("mptm", "rm", gr["op"], "operates", dy=-9)]
        # ROI.MARKET -> units: from the top of the platform's box up and left to the units box
        rx, ry, rw = box["rm"][0], box["rm"][1], box["rm"][2]
        ux, uy, uw, uh = box["units"]
        e.append(f'<path d="M{rx + rw / 2} {ry} C{rx + rw / 2} {uy + uh / 2} {ux + uw + 40} {uy + uh / 2} {ux + uw + 2} {uy + uh / 2}" '
                 f'class="rm-ln {gr["units"]}" marker-end="url(#ah3)"/>'
                 f'<text x="{rx + rw / 2 + 8}" y="{uy + uh / 2 + 34}" class="lbl">says units order</text>'
                 f'<text x="{rx + rw / 2 + 8}" y="{uy + uh / 2 + 49}" class="lbl">here directly</text>')
        # the Sidyakin -> United Russia line runs right-to-left; draw it by hand
        sx, sy = box["sid"][0], 299
        ux = box["ur"][0] + box["ur"][2]
        e[4] = (f'<path d="M{sx} {sy} L{ux + 6} {sy}" class="rm-ln {gr["sid"]}" marker-end="url(#ah3)"/>'
                f'<text x="{(sx + ux) / 2}" y="{sy + 19}" class="lbl" text-anchor="middle">heads its central committee</text>')
        # Emblems of the arms the handover posts' recipients name (counted from the delivery record), under the units box.
        # They show what kinds of unit the posts name, not which unit got which item.
        arms = [("army", "army and motor-rifle (and reconnaissance)", r"мотострелк|ОМСБР|армия|армии|армей|разведк|разведотряд",
                 "ground-forces", "emb_sv"),
                ("airborne", "airborne and air-assault", r"десантн|ВДВ|воздушно-десант", "airborne-forces", "emb_vdv"),
                ("sf", "special forces", r"спецназ|специального назначения", "spetsnaz-gru", "emb_gru")]
        recip = [e.get("recipient") or "" for e in json.loads((REPO / "data" / "registry" / "deliveries.json").read_text())]
        shown = [a for a in arms if any(re.search(a[2], r, re.I) for r in recip)]
        marks, kinds = [], []
        mx = 760 + 70 - 37 * len(shown) + 4
        edir = REPO / "exhibits" / "images" / "emblems"
        for i, (k, name, rx, fname, key) in enumerate(shown):
            rel = f"images/emblems/{fname}.svg"
            dest = self.img_dir.parent / "emblems" / f"{fname}.svg"
            if dest != edir / f"{fname}.svg":
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes((edir / f"{fname}.svg").read_bytes())
            if (rel, dest) not in self.media_files:
                self.media_files.append((rel, dest))
            marks.append(f'<g transform="translate({mx + 74 * i:.1f} 84)" class="arm"><title>{esc(name)}</title>'
                         f'<rect width="66" height="56" rx="5" class="fr"/>'
                         f'<image href="{rel}" x="4" y="4" width="58" height="48" preserveAspectRatio="xMidYMid meet"/></g>')
            kinds.append(f"{name}{self.tref(key)}")
        self._arm_names = kinds
        defs = ('<defs><marker id="ah3" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto">'
                '<path d="M0 0L8 4L0 8z" class="ah"/></marker></defs>')
        return (f'<figure class="ties"><div class="ties-svg"><svg viewBox="0 0 {W} {H}" class="mdl" role="img" '
                f'aria-label="Who is tied to TsBST: its co-founders, its supervisory board secretary, the company it takes part '
                f'in and the foundation\'s handovers to units">{defs}{"".join(e)}{"".join(n)}{"".join(marks)}</svg></div>'
                f'<figcaption>Line style is the grade of the evidence, as in the key at the foot of the page. The notes for each '
                f'line are in the list. The emblems under "Military units" stand for the kinds of unit the posts name as recipients: '
                f'{", ".join(self._arm_names)}. They do not say which unit got which item. Pictures: Sidyakin, Karmaks, 2016, CC BY-SA 4.0{self.tref("sid_photo")}; the party\'s '
                f'logo{self.tref("er_logo")}; ROI.MARKET\'s logo from its own site{self.tref("rm_logo")}.</figcaption></figure>')

    def found(self, n, sanc):
        """What the investigation found, in five lines, each graded, each pointing to its section. Says nothing the
        sections below do not source."""
        items = [
            ("rep", "A strike video, then a sales line", "#h-open",
             "TsBST re-posted a drone maker's footage of a strike and told servicemen they can order the two products used "
             "on its own marketplace."),
            ("doc", "A state bank and a donor foundation co-found it", "#h-hub",
             "TsBST's co-founders on the company register are Bank PSB, a state-owned bank, and the Nasha Pravda "
             "foundation."),
            ("rep", "The ruling party among its founders and on its board", "#h-hub",
             "TsBST names United Russia as a third founder, and the head of the party's central executive committee is "
             "secretary of its supervisory board."),
            ("rep", "Supply to a front the UN names", "#h-front",
             "TsBST's circle supplies and recruits for units of the formation the UN names in its finding on drone attacks "
             "on civilians in Kherson. Nothing on file shows an item used against civilians."),
            ("doc", "A platform that hides its operator", "#h-operator",
             "ROI.MARKET's public terms print its operator as «****». An archived copy names MPTM, a company TsBST's own "
             "report to the Justice Ministry lists."),
        ]
        cards = "".join(
            f'<li class="rm-card"><span class="rm-grade {g}">{esc({"doc": "Documented", "rep": "Reported"}[g])}</span>'
            f'<h3><a href="{h}">{esc(t)}</a></h3><p>{esc(x)}</p></li>' for g, t, h, x in items)
        return (f'<section class="found" aria-labelledby="h-found"><h2 class="rm-h2" id="h-found">What we found</h2>'
                f'<ol class="found-list">{cards}</ol>'
                f'<p class="found-n"><b>{n}</b> organisations are tied to TsBST on file; <b>{sanc}</b> of them are on a sanctions '
                f'list.</p></section>')

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
    # A group can take several tiers; "network" (a resident that sells software, not a listed good) sits with the services.
    TIER_ORDER = [(("cbst-core",), "TsBST and its core"), (("money-layer",), "Money"),
                  (("plumbing", "network"), "Partners, institutions and services"),
                  (("manufacturer",), "Makers"), (("adjacent",), "Other")]

    def tied(self):
        ties = [e for e in self.graph["edges"] if e["type"] == "cbst_tie"]
        return sorted({(e["source"] if CBST not in e["source"] else e["target"]).split("::")[-1] for e in ties})

    def wall(self):
        """Every organisation linked to TsBST as a tile: its logo where one is on file, its name, and the Sanctioned
        flag naming the regimes. Grouped by its place in the network."""
        groups, where = [], self.namesakes()
        for tiers, label in self.TIER_ORDER:
            slugs = [s for s in self.tied() if self.ents.get(s, {}).get("tier") in tiers]
            if not slugs:
                continue
            slugs.sort(key=lambda s: (not self.logo(s), not sanction_regimes(self.ents[s].get("sanctions")), short(self.ents[s])))
            tiles = []
            for s in slugs:
                e = self.ents[s]
                regs = [lab for lab, _ in sanction_regimes(e.get("sanctions"))]
                logo = self.logo(s)
                flag = f'<span class="rm-sanction">Sanctioned <b>{esc(", ".join(regs))}</b></span>' if regs else ""
                page = self.file_link(s)
                go = f'<a class="tl" href="{esc(page[0])}">{esc(page[1])} →</a>' if page else ""
                sub = f'<small class="tw">{esc(where[s])}</small>' if s in where else ""
                tiles.append(f'<li class="tile{" has-logo" if logo else ""}">{logo}<span class="tn">{self.en(e, pop=True)}{sub}</span>{go}{flag}</li>')
            groups.append(f'<div class="wall-g"><h3 class="rm-label">{esc(label)} · {len(slugs)}</h3><ul class="wall">{"".join(tiles)}</ul></div>')
        return "".join(groups)

    GENERIC_NAMES = {"научно-производственное предприятие"}   # a registered name that names nothing on its own
    CITY_EN = {"Москва": "Moscow", "Санкт-Петербург": "St Petersburg", "Великий Новгород": "Veliky Novgorod"}

    def namesakes(self):
        """{slug: line} telling apart tied organisations that share a name (three «Arkhangel», two «Ushkuynik»), or
        whose registered name is generic: the city on the register, or the INN where the cities are the same."""
        def core(e):
            inner = re.findall(r"«([^«»]+)»", guillemets(e.get("name_ru") or ""))
            name = (inner[-1] if inner else e.get("name_ru") or "").lower().replace("ё", "е")
            if name in self.GENERIC_NAMES:
                return name
            words = [w for w in re.split(r"[\s-]+", name.strip()) if w not in ("центр", "группа", "компаний")]
            return words[0] if words else name

        def city(e):
            m = re.search(r"г\.\s*((?:[А-ЯЁ][а-яё-]+)(?:\s[А-ЯЁ][а-яё]+)?)", e.get("address") or "")
            c = m.group(1) if m else e.get("city")
            return self.CITY_EN.get(c, latin_text(c)) if c else None

        by = {}
        for s in self.tied():
            by.setdefault(core(self.ents[s]), []).append(s)
        out = {}
        for key, ss in by.items():
            if len(ss) < 2 and key not in self.GENERIC_NAMES:
                continue
            cities = [city(self.ents[s]) for s in ss]
            for s, c in zip(ss, cities):
                e = self.ents[s]
                if not e.get("inn"):
                    out[s] = "no registered company on file"
                elif c and cities.count(c) == 1:
                    out[s] = c
                else:
                    out[s] = f"INN {e['inn']}"
        return out

    def file_link(self, slug):
        """(url, label) of the profile page for an organisation, where one exists. Preview only: the pages are private."""
        if not self.preview:   # public: the file is linked once it sits beside the landing
            return (f"company_{slug}.html", "Company file") if (self.out_dir / f"company_{slug}.html").exists() else None
        from build_company_page import COMPANY_PAGES   # noqa: E402
        if slug in COMPANY_PAGES:
            return COMPANY_PAGES[slug], "Company file"
        return next(((url, kind) for kind, _, _, url, sl in MORE if sl == slug), None)

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
        ev = [(np_f["as_of"], "TsBST registered in Moscow, with the Nasha Pravda foundation and Bank PSB as founders", np_f.get("source_id"), "doc"),
              (sub["as_of"], "MPTM registered; TsBST has taken part in it from the same day", sub.get("source_id"), "doc"),
              ("2025-02-15", "The platform starts as a closed pilot, by Kommersant's account", "s8866", "rep"),
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
        tied = sum(1 for s in self.tied() if self.ents.get(s, {}).get("tier") == "manufacturer")
        bar ="".join(f'<span class="seg {c}" style="flex-grow:{n}" title="{n}"></span>' for c, n, _, _ in segs if n)
        keys = "".join(f'<li><span class="sw {c}"></span><b>{n}</b> {esc(t)}{(": " + extra) if extra else ""}</li>'
                       for c, n, t, extra in segs)
        return (f'<figure class="test"><div class="bar" role="img" aria-label="{total} makers by Wildberries check result">{bar}</div>'
                f'<figcaption><ul class="keys">{keys}</ul><p class="note">{total} makers on file, checked against the sellers '
                f'in the earlier Wildberries dataset by INN: every maker the investigation has recorded, of which {tied} are '
                f'tied to TsBST. Counted from the registry.</p></figcaption></figure>')

    def blind_spot(self):
        """What an INN screen of the maker sees, beside the storefronts the record actually holds for «Bulat»."""
        rows, seen = [], set()
        for li in self.p.get("listings") or []:
            s = li.get("seller") or {}
            ent = self.ents.get(s.get("entity") or "")
            chan = re.sub(r"\s*\(.*", "", li.get("channel") or "")
            if ent and ent["slug"] == self.p["maker"]:
                # The maker's brand page: the seller behind it is not the maker's INN, and is not on file.
                if chan in seen:
                    continue
                seen.add(chan)
                who, kind = f'{self.en(ent)} brand page', "seller not identified"
            else:
                n = display_name(ent) if ent else {}
                ip = ent and (n.get("legal") or n.get("head") or "").startswith("ИП ")
                who = self.en(ent, pop=True) if ent else esc(latin_text(re.sub(r"\s*\(.*", "", s.get("storefront") or "")))
                kind = "sole trader" if ip else ("company" if ent else "storefront, seller not identified")
            rows.append(f'<li><span class="ch">{esc(latin_text(chan))}</span><span class="who">{who}</span>'
                        f'<span class="k">{esc(kind)}</span>{self.ref(li.get("source_id"))}</li>')
        return (f'<div class="blind one">'
                f'<div class="side found"><span class="rm-label">Where «Bulat» is actually sold</span><ul>{"".join(rows)}</ul></div></div>')

    def masked(self):
        """The operator's name as printed before and after it was masked, and the TsBST report row, as text."""
        oq = next(o for o in self.ents[MPTM].get("open_questions") or [] if "masked" in o.get("text", ""))
        sub = next(s for s in self.ents[CBST].get("subsidiaries") or [] if s["slug"] == MPTM)
        cells = [("22.08.2026", "Supplier offer, archived copy", ("OOO «MPTM» · INN 9714068459", "ООО «МПТМ» · ИНН 9714068459"), self.ref("s8817"), "named"),
                 ("01.10.2026", "Supplier offer, live site", ("Name of the Agent: OOO «****»", "Наименование Агента: ООО «****»"), self.ref(oq.get("source_id"), "s8822"), "hidden"),
                 ("26.10.2026", "Privacy policy, live site",
                  ("OOO «MPTM», INN 9714068459, address: 109202, Moscow, 1-ya Frezernaya st., 2/1, bldg 2", "ООО «МПТМ», ИНН 9714068459, адрес: 109202, г. Москва, вн. тер. г. муниципальный округ Нижегородский, ул. 1-я Фрезерная, д. 2/1, корп. 2"),
                  self.tref("privacy"), "named"),
                 (ru_date(sub["as_of"]), "TsBST's report to the Justice Ministry, for 2025",
                  ("OOO «MPTM» · OGRN 1257700021468 · 22.01.2025 · as a participant", "ООО \"МПТМ\" · 1257700021468 · 22.01.2025 · в качестве участника"), self.ref(sub.get("source_id")), "named")]
        return '<div class="docs">' + "".join(
            f'<figure class="doc {c}"><figcaption><span class="rm-label">{esc(d)}</span> {esc(w)}{r}</figcaption>'
            f'<p class="print">{name_html(t[0], t[1], key=f"doc-{i}", what="Line as printed, in Russian:")}</p></figure>' for i, (d, w, t, r, c) in enumerate(cells)) + \
            '<p class="note">Lines as printed in each document, rendered in English; the Russian original is under RU. The masked version shows the requisites only after login.</p></div>'

    def models(self, first):
        """The first hypothesis (method annex) or the working model (narrative), as a small flow diagram."""
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
        c, rc = box(250, 58, 150, "ROI.MARKET", "hub")
        d, rd = box(470, 58, 150, "Military|units")
        p += [a, b, c, d, arrow(ra, rc, "open"), arrow(rb, rc, "open"), arrow(rc, rd, "open")]
        one = f'<svg viewBox="0 0 630 160" class="mdl" role="img" aria-label="First hypothesis">{defs}{"".join(p)}</svg>'
        p = []
        h, rh = box(10, 100, 150, "TsBST, United|Russia, Bank PSB,|Nasha Pravda", "hub")
        m, rm = box(210, 112, 120, "Maker")
        outs = [("Dealers and|marketplaces", "doc", 10), ("State|contracts", "doc", 80), ("Donor foundation|handovers", "rep", 150),
                ("ROI.MARKET|(other sellers)", "rep", 220)]
        u, ru = box(560, 112, 90, "Military|units")
        p += [h, m, u, arrow(rh, rm, "doc")]
        for t, g, y in outs:
            o, ro = box(380, y, 140, t)
            p += [o, arrow(rm, ro, g), arrow(ro, ru, g)]
        two = f'<svg viewBox="0 0 660 290" class="mdl" role="img" aria-label="Working model">{defs.replace("ah", "ah2")}{"".join(p).replace("url(#ah)", "url(#ah2)")}</svg>'
        if first:
            return (f'<figure class="mdl-one"><figcaption><span class="rm-label">First guess</span> The platform would be '
                    f'stocked by people already selling on the mass marketplaces and by TsBST\'s own residents.</figcaption>'
                    f'<div class="mdl-wrap">{one}</div></figure>')
        return (f'<figure class="mdl-one"><figcaption><span class="rm-label">Working model</span> The platform is one outlet '
                f'among several. Makers sell through their own dealers and marketplaces, to the state, and to donors who hand '
                f'the goods to units.</figcaption><div class="mdl-wrap">{two}</div></figure>')

    # -- pictures: registered media only (media.json), each opening its full figure with caption, date and source ----
    HERO = None   # no background picture: a decorative crop backs no line of the copy (user rule, 27.10.2026)

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

    def band(self, ms, label, big=3, lead=(), limit=9, owners=False):
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
            en = media_caption(m)
            cap = self.tile_label(en, ru_date(m.get("published")))
            if owners:   # name whose picture it is: the first entity the record is about
                ent = next((self.ents[a["id"]] for a in m["about"] if a["type"] == "entity" and a["id"] in self.ents), None)
                dn = display_name(ent) if ent else None
                cap = f"{dn['head'] if dn['legal'] else dn['latin']}: {cap}" if ent else cap
            tiles.append(self.tile(f"fig-{m['id']}", self.img(m), en, cap, big=i < big))
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
        what = media_caption(m).rstrip(".")
        credit = (f'<button class="hero-credit" type="button" data-fig="fig-{m["id"]}">Background: {esc(what[:1].lower() + what[1:])}, '
                  f'{ru_date(m.get("published"))}</button>')
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

    STRONG_QUOTES = {"cbst", "arch_9067", "arch_10667", "osv_27702", "osv_36192", "yakim"}   # a party's own telling words (user, 25.10.2026)

    def oq(self, key, cite):
        """A quotation from OPENING_QUOTES, checked word for word against the scraped post where the scrape exists."""
        chan, msg, ru, en = OPENING_QUOTES[key]
        self.verbatim(key, chan, msg, ru)
        return quote_html(ru, en, cite, f"q-{key}", strong=key in self.STRONG_QUOTES)

    def _kreg(self, key):
        """Register one Kherson still (image copy, evidence figure for the viewer); returns what a tile needs. Preview only."""
        src_dir, dest = REPO / "exhibits" / "images" / "kherson", self.img_dir.parent / "kherson"
        msg, name, shows, ru, en = KHERSON_STILLS[key]
        if not (src_dir / name).exists():
            return None
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
        return msg, rel, shows, cap, name in ("k27702.jpg", "k34459.jpg")

    def kstill(self, key):
        """One still set right under the quote it belongs to. Preview only: the stills have no media record."""
        r = self._kreg(key)
        if not r:
            return ""
        self.k_inline.add(key)
        msg, rel, shows, cap, contain = r
        return (f'<figure class="band kstill"><div class="band-grid">{self.tile(f"fig-k{msg}", rel, shows, cap, big=True, contain=contain)}'
                f'</div><figcaption>{esc(shows)}</figcaption></figure>')

    def kherson_band(self):
        """The other stills from the Kherson channel (those not already set under a quote), as a picture band. Preview only."""
        tiles = []
        for key in KHERSON_STILLS:
            if key in self.k_inline or key in ("osv_21384", "osv_20993", "osv_34459"):   # the channel's own warning map: the page has the front map
                continue
            r = self._kreg(key)
            if not r:
                continue
            msg, rel, shows, cap, contain = r
            tiles.append(self.tile(f"fig-k{msg}", rel, shows, cap, big=len(tiles) < 2, contain=contain))
        if not tiles:
            return ""
        return (f'<figure class="band"><div class="band-grid">{"".join(tiles)}</div><figcaption><span class="rm-label">'
                f'More stills · {len(tiles)}</span> From the channel\'s own videos, 2024–2026. Nobody in them can be identified, and no frame we looked at shows a dead or wounded '
                f'person. Each opens with its caption, date and the post\'s own words.</figcaption></figure>')

    def center_band(self):
        """ЦБСТ's own album from the «Tsentr-2026» exercise (CENTER_STILLS) as a picture band. Preview only: no media record."""
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
                f'<span class="rm-prov">Posted by TsBST itself</span><span>{esc(shows)}{printed}{self.tref("tsentr_pics")}</span>'
                f'<span class="when">04.10.2026</span></figcaption></figure>')
            tiles.append(self.tile(f"fig-c{n}", rel, shows, self.tile_label(shows, "04.10.2026"), big=True))
        if not tiles:
            return ""
        return f'<figure class="band"><div class="band-grid">{"".join(tiles)}</div></figure>'

    def opening(self):
        """The cold open: a maker's strike footage, re-posted by ЦБСТ with an order line for its marketplace."""
        g = self.ents["ooo-gagaring"]
        tie = g.get("cbst_tie") or {}
        listed = bool(g.get("sanctions"))
        nodes = [("8 October", "Zaporizhzhia", "The head of the regional administration reports that an FPV drone hit the coat of arms on its building.", "rep"),
                 ("19 October", "Gagaring", "The maker posts a video of “the results” of its Kuznechik and Sova 5.8.", "rep"),
                 ("20 October", "TsBST", "Re-posts it as “a TsBST resident showed footage of the strike” and names both products.", "rep"),
                 ("Order line", "ROI.MARKET", "TsBST says servicemen can order both products there. The catalogue is behind a login: the post is the only evidence they are listed.", "rep")]
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
            f'<p>TsBST\'s post calls the city “occupied”. Zaporizhzhia is held by Ukraine, and the building is the seat of its '
            f'regional government. On 8 October the head of the regional administration reported that an FPV drone had hit the coat '
            f'of arms on its façade{self.tref("ukrinform")}. ROI.MARKET is a login-only '
            f'marketplace that, by the post of TsBST\'s board secretary, a United Russia official, TsBST launched with the party '
            f'and Bank PSB{self.ref("s8847")}. '
            + ("" if listed else "No sanctions listing for the maker is on file. ") +
            '</p><p class="note"><span class="rm-grade rep">Reported</span> Both posts are the parties\' own word. The video is '
            'consistent with the report of 8 October, but neither post dates the strike.</p>'
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
        ("opening/roymarket-supplier-page.jpg", "ROI.MARKET's public page, 24.10.2026",
         "Screenshot of ROI.MARKET's public page for prospective sellers as it read on 24 October 2026. The catalogue itself "
         "is behind a login.", "rm_now"),
    ]

    def shot(self, i):
        """A screenshot for box i of the opening strip, openable like any picture. Preview only: third-party captures
        have no media record."""
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

    def offer_collage(self):
        """The two captures of the supplier offer side by side (exhibits/make_offer_collage.py). Preview only: the image
        is a composite of our own captures of third-party pages."""
        name = "opening/offer-collage.png"
        if not (REPO / "exhibits" / "images" / name).exists():
            return ""
        src_dir, dest = REPO / "exhibits" / "images", self.img_dir.parent
        rel = f"images/{name}"
        if dest != src_dir:
            (dest / name).parent.mkdir(parents=True, exist_ok=True)
            (dest / name).write_bytes((src_dir / name).read_bytes())
        if (rel, dest / name) not in self.media_files:
            self.media_files.append((rel, dest / name))
        return (f'<figure class="rm-fig"><div class="frame"><img src="{esc(rel)}" alt="The supplier offer as archived on 22 August 2026 '
                f'beside our capture of 25 October 2026, with the lines that changed highlighted"></div><figcaption>'
                f'<span class="rm-prov">Composite of two captures</span><span>The same offer, revision 3.0, in the archived copy of 22.08.2026 '
                f'and our capture of 25.10.2026. Yellow: on the page in August and gone in October. Blue: new in October. Green: still public{self.ref("s8817")}'
                f'{self.ref("s8822")}{self.tref("privacy")}.</span></figcaption></figure>')

    def step_shot(self, i, caption):
        """A screenshot from SHOTS under a step of the origin story, with its own plain caption. Preview only."""
        btn = self.shot(i)
        return f'<figure class="step-shot">{btn}<figcaption>{esc(caption)}</figcaption></figure>' if btn else ""

    def gag_video(self):
        """The 25-second clip from Gagaring's post, playable. Preview only: the file is not catalogued, and a public
        page shows key frames plus a link to the archived original."""
        src = REPO / "exhibits" / "images" / "video"
        if not (src / "gagaring-5142.mp4").exists():
            return ""
        dest = self.img_dir.parent / "video"
        for name in (("gagaring-5142.mp4", "gagaring-5142.jpg") if self.preview else ("gagaring-5142.jpg",)):
            if dest != src:
                dest.mkdir(parents=True, exist_ok=True)
                (dest / name).write_bytes((src / name).read_bytes())
            if (f"images/video/{name}", dest / name) not in self.media_files:
                self.media_files.append((f"images/video/{name}", dest / name))
        if not self.preview:   # public page: a key frame and the post, not the third party's video file
            return ('<figure class="clip"><img src="images/video/gagaring-5142.jpg" alt="A frame from Gagaring\'s video: a drone '
                    'approaching a large government building">'
                    '<figcaption><span class="rm-label">Video frame</span> A frame from Gagaring\'s video, labelled “Kuznechik/Sova 5.8”: a drone '
                    f'flies in to the coat of arms on the building\'s façade. The video is in the post{self.tref("gag")}.</figcaption></figure>')
        return ('<figure class="clip"><video controls preload="none" playsinline poster="images/video/gagaring-5142.jpg" '
                'aria-label="Gagaring\'s video: a drone flies in over a large government building to a trident coat of arms on '
                'its façade, then a separate clip of the coat of arms hanging damaged">'
                '<source src="images/video/gagaring-5142.mp4" type="video/mp4"></video>'
                '<figcaption><span class="rm-label">Video · 0:25</span> Gagaring\'s video, labelled “Kuznechik/Sova 5.8”: a drone '
                f'flies in to the coat of arms on the building\'s façade. The last eight seconds are a separate clip{self.tref("gag")}.</figcaption></figure>')

    def osv_clip(self):
        """The first 30 seconds of the channel's post 38645, playable, with the post's own words in the caption. Preview
        only: the file is not catalogued, and a public page shows key frames plus a link to the archived original."""
        src = REPO / "exhibits" / "images" / "video"
        if not (src / "osv-38645.mp4").exists():
            return ""
        dest = self.img_dir.parent / "video"
        for name in (("osv-38645.mp4", "osv-38645.jpg") if self.preview else ("osv-38645.jpg",)):
            if dest != src:
                dest.mkdir(parents=True, exist_ok=True)
                (dest / name).write_bytes((src / name).read_bytes())
            if (f"images/video/{name}", dest / name) not in self.media_files:
                self.media_files.append((f"images/video/{name}", dest / name))
        chan, msg, ru, en = OPENING_QUOTES["osv_38645"]
        self.verbatim("osv_38645", chan, msg, ru)
        said = name_html("\u201c" + en + "\u201d", ru, key="q-osv_38645", what="Russian original of")
        if not self.preview:
            return ('<figure class="clip"><img src="images/video/osv-38645.jpg" alt="A frame of a drone pilot\'s controller screen: a view down onto a damaged road bridge beside a river">'
                    '<figcaption><span class="rm-label">Video frame</span> The channel\'s post of 22.10.2026 says '
                    f'<span class="rm-grade rep">Reported</span> {said}{self.tref("osv_38645")}. '
                    'The footage is a pilot\'s controller screen over a damaged road bridge. The video is in the post.</figcaption></figure>')
        return ('<figure class="clip"><video controls preload="none" playsinline poster="images/video/osv-38645.jpg" '
                'aria-label="A drone pilot\'s controller screen: a view down onto a damaged road bridge beside a river, with a '
                'yellow tracking box on small dark shapes near the kerb">'
                '<source src="images/video/osv-38645.mp4" type="video/mp4"></video>'
                '<figcaption><span class="rm-label">Video · first 0:30 of 1:19</span> The channel\'s post of 22.10.2026 says '
                f'<span class="rm-grade rep">Reported</span> {said}{self.tref("osv_38645")}. '
                'The footage is a pilot\'s controller screen over a damaged road bridge, with a strike at 0:13. The post itself says '
                'a dog was killed. Sound removed.</figcaption></figure>')

    def dual_use(self):
        """The label on the order line: the supplier page's own sentence before and after it changed."""
        (d_ru, d_en), (s_ru, s_en) = SUPPLIER_LINES["dual"], SUPPLIER_LINES["special"]
        return (
            f'<p>TsBST\'s “dual-use” is the platform\'s own label. From August 2026 its page for prospective sellers opened with '
            f'{orig_line(d_ru, "rm-dual", d_en)}{self.tref("rm_aug")} The copy archived on 12 October still did'
            f'{self.tref("rm_oct")}. By 24 October the same sentence read {orig_line(s_ru, "rm-special", s_en)}'
            f'{self.tref("rm_now")} The platform\'s public terms and buyer offer use neither '
            f'phrase.</p>')

    @staticmethod
    def un_quote(key, cite):
        """A passage of a UN paper, quoted in its original English: no translation, no RU control."""
        return (f'<blockquote class="rm-quote"><span class="rm-label">Quotation</span>'
                f'<span class="q">“{esc(UN_QUOTES[key])}”</span><cite>{cite}</cite></blockquote>')

    def front_map(self):
        """The Kherson / Dnipro left-bank map (exhibits/make_front_map.py): the Russian-held area as DeepState drew it, the
        towns, and the units the section names, pinned where a source names a place and listed where it names a sector."""
        svg_path = REPO / "exhibits" / "images" / "maps" / "kherson-front.svg"
        if not svg_path.exists():
            return ""
        self.tref("deepstate"), self.tref("natural_earth")   # credits stay in the sources list; the map's own footer names them
        return '<figure class="front-map-fig"><div class="front-map-wrap">' + svg_path.read_text() + '</div></figure>'

    def front(self):
        """The Kherson drone campaign: the UN's finding, the circle's own ties to the formations it names, and how the
        units' channels describe their targets. Three layers, each at the level its documents support."""
        intro = (
            f'<p class="lede">In May 2025 the UN\'s Independent International Commission of Inquiry on Ukraine concluded that '
            f'Russian drone operators on the left bank of the Dnipro had spent ten months attacking civilians in Kherson, and '
            f'that the attacks amount to the crime against humanity of murder{self.tref("un_crp")}. In October it extended the '
            f'finding to 300 km of the river and three regions, and named the formation the operators serve in:</p>'
            + self.un_quote("dnepr", f'UN report A/80/497, para. 40, 21.10.2025{self.tref("un_ga")}')
            + self.front_map() +
            f'<p>The Commission names the 18th Combined Arms Army{self.tref("un_crp")}; it names no brigade. The Centre for Information Resilience '
            f'and DW named the 205th motor-rifle brigade{self.tref("dw_film")} among three units whose drones worked over Beryslav '
            f'during the attacks, while saying they could not prove who carried them out{self.tref("cir")}. A channel that posts '
            f'the brigade\'s footage places it in the 49th Army{self.tref("osv_27702")}. A senior '
            f'practitioner at a Kherson city hospital told the Commission:</p>'
            + self.un_quote("safari", f'UN paper A/HRC/59/CRP.2, para. 42, 28.05.2025{self.tref("un_crp")}')
            + self.osv_clip())
        np_ = self.ents[NP]
        rows = [
            ("Bars-Sarmat", "rep",
             "Its commander, Dmitry Rogozin, says the centre fights for the commander of the Airborne Forces and that units of "
             "the «Dnepr» Group of Forces fit its munitions to their assault drones" + self.tref("rog_8057") + self.tref("rog_7780") + "."),
            (np_, "rep",
             "reports delivering 100 strike drones to fighters of the 49th Army on the Kherson direction in May 2024"
             + self.tref("np_280") + ", and a vehicle now used by the 18th Army to move cargo and troops to the front line"
             + self.tref("np_580") + "."),
            (self.ents["ooo-gagaring"], "rep",
             "the maker of the Kuznechik and Sova posts thanks from 49th Army crews who use the Sova to intercept "
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
            + '<h3 class="rm-h3">A school that recruits for the 205th brigade</h3>'
            + ('<p>TsBST\'s own channel says a resident\'s anti-drone simulator runs at the «Arkhangel» drone school\'s training '
               f'centre in Tuapse{self.tref("cbst_1562")}. The school\'s own channel recruits operators for the 205th brigade and '
               f'Dmitry Rogozin\'s channel says the project is part of the training centre of Bars-Sarmat, his drone centre{self.tref("rog_7047")}. No document ties the school to '
               'TsBST; it is the circle\'s word and the school\'s.</p>')
            + self.oq("arch_9067", f'«Arkhangel», Telegram, 01.12.2025{self.tref("arch_9067")}')
            + self.oq("arch_10667", f'«Arkhangel», Telegram, 17.08.2026{self.tref("arch_10667")}')
            + (f'<p class="note"><a href="{esc(MORE[1][3] if self.preview else "arkhangel.html")}">The full «Arkhangel» file: products, parts list, partners and ties →</a></p>'
               if self.preview or (self.out_dir / "arkhangel.html").exists() else "") +
                        '<h3 class="rm-h3">What a front channel says about the targets</h3>'
            f'<p>The Commission reproduces posts of a Kherson-front channel, «From Mariupol to the Carpathians», as figures in '
            f'its paper{self.tref("un_crp")}. The channel signs its strike videos with the units\' names. Under footage of the '
            f'205th brigade:</p>'
            + self.oq("osv_27702", f'«From Mariupol to the Carpathians», Telegram, 23.07.2025{self.tref("osv_27702")}') + self.kstill("osv_27702") +
            '<p>Under a video of a van being struck in a residential yard:</p>'
            + self.oq("osv_19953", f'the same channel, 19.08.2024{self.tref("osv_19953")}') +
            '<p>And under “dual-use”, the label ROI.MARKET used for its sellers’ goods:</p>'
            + self.oq("osv_36192", f'the same channel, 24.07.2026{self.tref("osv_36192")}')
            + self.oq("osv_38703", f'the same channel, 24.10.2026, over a clip watermarked by the 98th Airborne Division{self.tref("osv_38703")}') + self.kstill("osv_38703")
            + '<p class="note"><span class="rm-grade rep">Reported</span> The ties above are the parties\' own posts. They do not '
            'show any item from TsBST\'s circle used against civilians; the UN names no unit below the army.</p>')

    def beyond_shop(self):
        """Two of TsBST's own lines on what it does besides the shop."""
        return (
            '<p>TsBST presents itself as a support body for drone makers, and ROI.MARKET as a catalogue. Its own posts, and those '
            'of its board secretary, describe more. It says it showed the marketplace at «Tsentr-2026», a strategic '
            'military exercise with delegations from 41 countries, and signed up sellers there:</p>'
            + self.oq("tsentr", f"TsBST, Telegram, 04.10.2026{self.tref('tsentr')}") + self.center_band() +
            f'<p>On 15 October its board secretary, the United Russia official {self.person_pop(SIDYAKIN)}, announced an app '
            f'that assigns incoming Ukrainian drones to mobile fire teams in Kursk region, and placed it inside a TsBST system:</p>'
            + self.oq("yakim", f"Sidyakin, Telegram, 15.10.2026{self.tref('yakim')}") +
            '<p class="note"><span class="rm-grade rep">Reported</span> Both are the parties\' own claims; no document on file '
            'shows the system in service.</p>')

    def operator(self):
        """The operator's name, masked on the live terms and printed in an older copy, with TsBST's report row."""
        return (
            '<h3 class="rm-h3" id="h-operator">The marketplace hides who runs it. An older copy does not</h3>'
            f'<p>The platform\'s public terms print the operator as “OOO «****»”. A copy archived on 22.08.2026 names it: '
            f'{self.pop(MPTM)}, INN 9714068459. The privacy policy on the live site still names it, at a different address from the August '
            f'offer{self.tref("privacy")}. TsBST\'s own report to the Justice Ministry lists the same company as one it has '
            f'taken part in since the day it was registered.</p>{self.masked()}{self.offer_collage()}')

    def origin(self):
        """The platform: who launched it, whom it recruits, the operator it hides, and where the products go instead."""
        recruit = self.mclaim(MPTM, "s8854")
        return (
            f'<p class="lede">The front above is where TsBST\'s circle says its goods and recruits go. The platform TsBST points servicemen to is ROI.MARKET. '
            f'In August 2026 it opened to outside sellers and named the ones it wanted first:</p>'
            + quote_html(recruit["text_ru"], latinize_gloss(recruit["text_en"]),
                         f"ROI.MARKET's announcement, {ru_date(recruit['as_of'])}{self.ref(recruit['source_id'])}", "q-recruit")
            + '<h3 class="rm-h3">One outlet among several</h3>'
            '<p>«Bulat», a drone detector shown at Dronnitsa 2025, a showcase TsBST takes part in, is sold through dealers and '
            'sole traders, and a foundation that co-founded TsBST buys it and posts the handovers. No Wildberries seller carries '
            'the maker\'s INN, so a sanctions screen keyed on that identifier '
            f'finds none of them.</p>{self.blind_spot()}' + self.models(first=False))

    def annex(self):
        """Method annex: how the investigation arrived at the working model, kept off the narrative."""
        steps = [
            ("We had been watching Wildberries",
             '<p>The investigation started as <a href="https://amethyst-deceiver2001.github.io/wb-watcher/">WB Watch</a>, a tracker of '
             'military goods sold on Russia\'s largest consumer marketplace. It found a large, open trade in kit for the war. '
             'ROI.MARKET then invited “first of all” sellers already on Wildberries and Ozon: the seller base already mapped.</p>'
             '<div class="figs"><div class="fig"><span class="n">7,666</span><span class="w">military-item listings</span></div>'
             '<div class="fig"><span class="n">89%</span><span class="w">shipped from Wildberries\' own warehouses</span></div>'
             '<div class="fig"><span class="n">802</span><span class="w">sellers</span></div></div>'),
            ("First guess: the usual sellers, plus TsBST's residents",
             '<p>If the platform recruits Wildberries sellers, and TsBST runs a residency for drone makers, the likely suppliers are '
             'makers that are both. Every maker on file was checked against the Wildberries sellers by INN.</p>'
             + self.test_bar() + self.models(first=True)),
            ("The check missed the best case",
             '<p>«Bulat» returned nothing, though it is on sale through dealers and sole traders. That is why the investigation '
             'follows products, from the maker to the units that receive them, rather than the platform.</p>'),
        ]
        return ('<details class="fold annex"><summary>Annex: how the investigation got here</summary><ol class="steps">'
                + "".join(f'<li class="step"><h3 class="rm-h3">{esc(h)}</h3>{body}</li>' for h, body in steps)
                + '</ol></details>')

    def more_cards(self, preview):
        """The company file and the foundation story, linked only in the preview until they are public."""
        from build_company_page import COMPANY_PAGES   # noqa: E402
        cards = []
        for slug, url in COMPANY_PAGES.items():
            e = self.ents[slug]
            href = url if preview else (f"company_{slug}.html" if (self.out_dir / f"company_{slug}.html").exists() else None)
            line, line_src = FILE_LINES.get(slug, ("", ()))
            line_ref = self.tref("rog_8057") if slug == "csn-bars-sarmat" else self.ref(*line_src)
            nm = self.name(e, sub=False) + (f'<small>{esc(line)}{line_ref}</small>' if line else "")
            ref = ""
            if href:   # a footnote link inside the name link would nest two <a>: park it after the name instead
                for m in re.findall(r'<sup class="rm-ref">.*?</sup>', nm):
                    ref, nm = ref + m, nm.replace(m, "", 1)
            cards.append(f'<article class="rm-card chain-card"><header><span class="rm-kind">Company file</span>{self.logo(slug)}</header>'
                         f'<h3 class="rm-name">{f"<a href={chr(34)}{esc(href)}{chr(34)}>" if href else ""}{nm}'
                         f'{"</a>" if href else ""}{ref}</h3>{self.sanctions(e)}'
                         + (f'<p class="go"><a href="{esc(href)}">Open the company file →</a></p>' if href
                            else '<p class="go wait">The company file is in review and not yet public.</p>') + '</article>')
        if preview:
            for kind, title, line, url, slug in MORE:
                mark = self.logo(slug) if slug else ""
                cards.append(f'<article class="rm-card chain-card"><header><span class="rm-kind">{esc(kind)}</span>{mark}</header>'
                             f'<h3 class="rm-name"><a href="{esc(url)}">{esc(title)}</a><small>{esc(line)}</small></h3>'
                             f'<p class="go"><a href="{esc(url)}">Open →</a></p></article>')
        stories = []
        if preview and STORY:
            stories.append(f'<article class="rm-card chain-card"><header><span class="rm-kind">Story</span>{self.logo(NP)}</header>'
                           f'<h3 class="rm-name"><a href="{esc(STORY)}">Aid for the Zone</a><small>How {self.en(self.ents[NP])} '
                           f'raises money, co-founded TsBST and hands equipment to units</small></h3>'
                           f'<p class="go"><a href="{esc(STORY)}">Read the story →</a></p></article>')
        return "".join(cards), "".join(stories)

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
                f'{regimes}'
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
TOC_ITEMS = [("h-found", "What we found"), ("h-open", "The strike"), ("h-limits", "Limits"), ("h-hub", "Who stands behind"), ("h-front", "The front"),
             ("h-origin", "The marketplace"), ("h-beyond", "Beyond the shop"), ("h-chains", "Profiles"), ("h-net", "Network"),
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
    L.out_dir = out.parent
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
    ties = L.ties_diagram()
    n0, _, sanc0 = L.network()
    found = L.found(n0, sanc0)
    handed = L.pics([NP], {"handover"})
    handovers = L.band(handed, "From «Nasha Pravda»'s handover posts. A handover does not show use in combat.", big=3) if handed else ""
    front = L.front()
    beyond, operator = L.beyond_shop(), L.operator()
    origin, timeline = L.origin(), L.timeline()
    chains = "".join(L.chain_card(s, url if preview else (f"chain_{s}.html" if (out.parent / f"chain_{s}.html").exists() else None))
                     for s, url in CHAINS.items())
    file_cards, story_cards = L.more_cards(preview)
    n, by, sanc = L.network()
    shown = {m["id"] for m in L.pics(["ooo-gagaring", "ano-dpo-obrazovatelny-tsentr-gagaring", NP, "csn-bars-sarmat", "proekt-kb-arkhangel"])}
    # Product, stand and handover pictures that the makers publish of themselves. Showrooms, customer photos, interview
    # stills, documents and a CGI render are left out: they support no line of the story (owner's comment, 25.10.2026).
    own_ms = L.pics([s for s in L.tied() if s != CBST], genres={"marketing", "handover", "event"}, skip=shown | {L.HERO, "m0006"})
    own = L.band(own_ms, "Pictures the makers publish of their own products and stands. They show what a company offers, not sales.",
                 big=3, owners=True)
    wall = L.wall()
    # logos taken from GUR's War & Sanctions pages (where the company's own site or channel is not on file) are credited
    n_gur = sum(1 for m in L.media if m.get("genre") == "logo" and "war-sanctions.gur.gov.ua" in (m.get("original_url") or "")
                and any(a["id"] in L.tied() for a in m.get("about") or []))
    gur_note = (f" Most logos come from the organisation's own site or Telegram channel; {n_gur} are as GUR's War &amp; Sanctions "
                f"database shows them, on pages that print the company's INN{L.tref('gur_logos')}.") if n_gur else ""
    sgrid, undated = L.sanctions_grid()
    revenue, n_rev = L.revenue_bars()
    annex = ""   # how the investigation got here: research history, kept off the page (user rule, 27.10.2026)
    restr_date, restr_ref = L.restricted()
    lead_quote = quote_html(f"{qa['text_ru']} […] {qb['text_ru']}",
                            latinize_gloss(f"{qa['text_en']} […] {qb['text_en']}"),
                            f"{sid_name_l}, secretary of TsBST's supervisory board and head of United Russia's central executive committee, "
                            f"on TsBST's year, Telegram, {ru_date(qb['as_of'])}{qref}", "q-lead").replace(
                                '<blockquote class="rm-quote">', '<blockquote class="rm-quote lead-quote">', 1)
    doc = f"""<!doctype html>
<!-- Generated by exhibits/build_landing.py from data/registry on {today}. Do not edit by hand. -->
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ROI.MARKET Investigation</title>
<meta name="description" content="An open-source investigation of ANO TsBST, a Moscow non-profit for the drone industry, its military marketplace ROI.MARKET, and the companies, products and handovers around them. Every claim is graded by the document behind it.">
<meta property="og:type" content="article"><meta property="og:site_name" content="ROI.MARKET Investigation">
<meta property="og:title" content="TsBST and ROI.MARKET: a Moscow non-profit, its military marketplace, and the drone-war supply around it">
<meta property="og:description" content="Every claim rests on an archived document and is graded by how well that document shows it.">
<link rel="canonical" href="https://amethyst-deceiver2001.github.io/roymarket-investigation/">
<meta property="og:url" content="https://amethyst-deceiver2001.github.io/roymarket-investigation/">
<meta property="og:image" content="https://amethyst-deceiver2001.github.io/roymarket-investigation/images/social.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:image:alt" content="TsBST and ROI.MARKET: an open-source investigation. Claims graded Documented, Reported or Not documented.">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="TsBST and ROI.MARKET: a Moscow non-profit, its military marketplace, and the drone-war supply around it">
<meta name="twitter:description" content="Every claim rests on an archived document and is graded by how well that document shows it.">
<meta name="twitter:image" content="https://amethyst-deceiver2001.github.io/roymarket-investigation/images/social.png">
{design_head((REPO / 'exhibits' / 'landing.css').read_text(), None if preview else 'fonts/fonts.css')}</head>
<body>
<div class="hero"{hero_style}><header class="rm-page top">
  {f'<p class="rm-eyebrow">Draft · {ru_date(today)}</p>' if preview else ''}
  <h1 class="rm-h1">TsBST and ROI.MARKET <span class="rm-muted">a Moscow non-profit, its military marketplace, and the drone-war supply around it</span></h1>
  <p class="rm-dek">An open-source investigation of ANO «TsBST», a Moscow non-profit for the drone industry, and of the
  companies around it: what they make, who sells it, and which military units receive it. Every claim rests on an
  archived document and is graded by how well that document shows it.</p>
  <p class="rm-muted byline">By <a href="https://en.wikipedia.org/wiki/Alexey_Kovalev_(journalist)" target="_blank" rel="noopener">Alexey Kovalev</a>, independent reporter · data as of {ru_date(today)}</p>
  {hero_credit}
</header></div>
{TOC}
<main class="rm-page">
  {found}
  <section class="open" aria-labelledby="h-open">
    <h2 class="rm-h2" id="h-open">A strike, then a sales line</h2>
    {opening}
  </section>

  <section class="limits" aria-labelledby="h-limits">
    <details open><summary><h2 class="rm-h2" id="h-limits">What this does not show</h2></summary>
    <ul>
      <li>A handover to a unit does not show that the equipment was used in combat. Some recipients are rear units.</li>
      <li>TsBST's share in the company that runs ROI.MARKET is not stated in any document on file, and since
      {restr_date} the company register withholds who owns that company{restr_ref}.</li>
      <li>A US sanctions entry under a similar name belongs to a different company registered in Tula. TsBST itself is
      not shown here as sanctioned by the US.</li>
    </ul>
    </details>
  </section>

  <section class="hub" aria-labelledby="h-hub">
    <h2 class="rm-h2" id="h-hub">Who stands behind TsBST</h2>
    <p class="lede">TsBST, the non-profit that told servicemen on 20 October where to order the two products, is not an ordinary trade body. Its co-founders on the company register are a donor foundation and a state-owned bank; TsBST names the ruling party as a third, and the head of the party's central executive committee is secretary of its supervisory board.</p>
    {lead_quote}
    <article class="rm-card hub hub-solo"><header><span class="rm-kind">Hub</span>{L.logo(CBST)}</header>
        <h3 class="rm-name">{cbst_name}</h3>{cbst_sanc}
        <p class="row">Funds received: {funds}. These are a non-profit's funds, not revenue.</p>
        <p class="row"><span class="rm-id">INN {esc(c['inn'])}</span> <span class="rm-id">OGRN {esc(c['ogrn'])}</span></p></article>
    {ties}
    <ul class="ledger ledger-phone" aria-label="Relations">{ledger}</ul>
    <details class="fold ledger-desk"><summary>The ties as a list, with notes</summary><ul class="ledger" aria-label="Relations">{ledger}</ul></details>
    {handovers}
  </section>

  <section class="front-sec" aria-labelledby="h-front">
    <h2 class="rm-h2" id="h-front">The front it supplies</h2>
    {front}
  </section>

  <section class="origin" aria-labelledby="h-origin">
    <h2 class="rm-h2" id="h-origin">The marketplace and its sellers</h2>
    {origin}
    <h3 class="rm-h3">The dates</h3>
    {timeline}
    {operator}
  </section>

  <section class="beyond" aria-labelledby="h-beyond">
    <h2 class="rm-h2" id="h-beyond">More than a marketplace</h2>
    {beyond}
  </section>

  <section aria-labelledby="h-chains">
    <h2 class="rm-h2" id="h-chains">Profiles and stories</h2>
    <p class="lede">The investigation's longer pieces, each its own page: a chain view for a product, a file for a company,
    a project or a set of people, and narrative stories.</p>
    <h3 class="rm-h3">Follow a product</h3>
    <p class="note">A chain view follows one product from TsBST and its events to the maker, the shops and dealers that sell it, the
    state agencies that buy it and the units that receive it. Each line is drawn in the style of its evidence.</p>
    <div class="chains">{chains}</div>
    <h3 class="rm-h3">Company, project and people files</h3>
    <div class="chains">{file_cards}</div>
    {('<h3 class="rm-h3">Stories</h3><div class="chains">' + story_cards + '</div>') if story_cards else ''}
  </section>

  <section aria-labelledby="h-net">
    <h2 class="rm-h2" id="h-net">The network on file</h2>
    <p class="lede"><b>{n}</b> organisations are tied to TsBST on file: {by['doc']} through a document (a register entry,
    a contract, TsBST's own posts), {by['rep']} on their own word or press reports alone. <b>{sanc}</b> of them are on at
    least one sanctions list.</p>
    {own}
    <details class="fold"><summary>Show all {n} organisations, with logos and charts</summary>
    <figure class="netfig">{wall}
      <figcaption>Every organisation the registry links to TsBST, with its logo where one is on file. A red flag names
      the regimes that list it.{gur_note}</figcaption></figure>
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
      <li>The investigation grew out of <a href="https://amethyst-deceiver2001.github.io/wb-watcher/" target="_blank"
      rel="noopener">WB Watch</a>, a tracker of military goods sold on Wildberries.</li>
    </ul>
    {annex}
  </section>

  <section class="rm-prose rm-sources" aria-labelledby="h-sources"><h2 class="rm-h2" id="h-sources">Sources</h2>
    <details class="fold" id="sources-fold"><summary>Full list of sources <span class="count">{len(L.notes)}</span></summary><ol>{L.notes_list()}</ol></details></section>
</main>
{support_block_html()}
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
