#!/usr/bin/env python3
"""Generates the site's front door and case studies from notes/ and the registry.

  docs/index.html            landing page (routes: cases, graph, profiles, guided read)
  docs/cases/index.html      case list
  docs/cases/<slug>.html     one page per published case: notes/case_study_<slug>.md
                             rendered + a static graph excerpt + a resolved sources table

Local file processing only, no network. Run after any change to a case note or the registry:

  python3 scripts/build_case_pages.py
  python3 scripts/check_tag_balance.py docs/index.html docs/cases/*.html

Case text lives in notes/case_study_<slug>.md. Grade chips: {doc} {press} {open}.
The static excerpt reuses the live graph's tier colours (docs/relationship-graph.html).
"""
import html
import json
import math
import random
import re
from pathlib import Path

from classify_product_icon import classify as classify_product, CATEGORY_LABELS
from profile_text import popover_html

REPO = Path(__file__).resolve().parent.parent
DOCS = REPO / "docs"
REG = REPO / "data" / "registry"

# Tier colours copied from docs/relationship-graph.html (--t-*).
TIER_COL = {"manufacturer": "#2a78d6", "cbst-core": "#eb6834", "plumbing": "#1baf7a",
            "money-layer": "#eda100", "adjacent": "#e87ba4", "network": "#008300",
            "unverified": "#4a3aa7", None: "#898781"}
PERSON_COL = "#7a8a99"

# Demand-side node glyphs (government_customer / military_unit), copied
# verbatim from exhibits/case_study_build_svgs.py / the Demand-Side
# Icon Set mockup -- a pediment for a government/institutional customer, a
# shield-with-checkmark for a named military unit -- instead of the plain
# tier-colored rect every other non-person node gets. 24x24 viewBox source;
# icon_glyph_svg() below rescales and repositions it per node.
CUSTOMER_ICON_PATHS = (
    '<rect x="4" y="10" width="16" height="9" rx="1"/>'
    '<path d="M4 10 L12 4 L20 10"/>'
    '<line x1="7" y1="10" x2="7" y2="19"/>'
    '<line x1="12" y1="10" x2="12" y2="19"/>'
    '<line x1="17" y1="10" x2="17" y2="19"/>'
)
CUSTOMER_ICON_CENTER = (12, 11.5)
MILITARY_UNIT_ICON_PATHS = (
    '<path d="M12 3 L19 6 L19 12 C19 17 15.5 20 12 21 C8.5 20 5 17 5 12 L5 6 Z"/>'
    '<path d="M9 12 L11 14 L15 9"/>'
)
MILITARY_UNIT_ICON_CENTER = (12, 12)

# Product-node glyphs, keyed by scripts/classify_product_icon.py's category
# id -- all 17 real categories (everything but "unclassified", which keeps
# the plain tier-colored rect every other entity node already gets -- that
# fallback IS the point, per the Product Icon Set's own "a gap, not a
# guess" rule, not a placeholder to fill in later).
#
# Transcribed directly from the canonical standalone "Product Icon Set"
# artifact (https://claude.ai/artifact/XuPK3vgfj2L7St4kEzzLEW), confirmed
# 2026-09-21 as the source of truth over this file's own earlier 3-icon
# subset (which used differently-drawn glyphs for the 3 categories it did
# cover) -- both existed and had drifted apart; re-sync here whenever that
# artifact's icon paths change. `class="accent"/"accent-fill"` styling from
# that artifact's swatch-on-white presentation has no equivalent token on
# this page's colored node fills, so every path renders in the single
# var(--paper) stroke/fill this file's icon_glyph_svg() already uses for
# the demand-side icons above -- same simplification, not a redraw.
PRODUCT_ICONS = {
    "fpv_kamikaze_strike": (
        '<path d="M12 3 L15 9 L9 9 Z" fill="var(--paper)" stroke="none"/>'
        '<path d="M12 9 L5 5 M12 9 L19 5 M12 13 L5 19 M12 13 L19 19"/>'
        '<circle cx="5" cy="5" r="2"/><circle cx="19" cy="5" r="2"/>'
        '<circle cx="5" cy="19" r="2"/><circle cx="19" cy="19" r="2"/>'
        '<line x1="12" y1="9" x2="12" y2="13"/>',
        (12, 12)),
    "multirotor_cargo_utility": (
        '<path d="M12 8 L5 5 M12 8 L19 5 M12 14 L5 19 M12 14 L19 19"/>'
        '<circle cx="5" cy="5" r="2"/><circle cx="19" cy="5" r="2"/>'
        '<circle cx="5" cy="19" r="2"/><circle cx="19" cy="19" r="2"/>'
        '<rect x="9" y="8" width="6" height="6" rx="1"/>',
        (12, 12)),
    "fixed_wing_vtol": (
        '<line x1="12" y1="2" x2="12" y2="20"/>'
        '<path d="M12 8 L3 13 M12 8 L21 13"/>'
        '<path d="M12 16 L8 19 M12 16 L16 19"/>'
        '<circle cx="12" cy="2" r="1.1" fill="var(--paper)"/>',
        (12, 12)),
    "helicopter_uas": (
        '<ellipse cx="12" cy="5" rx="8" ry="1.6"/>'
        '<line x1="12" y1="6.5" x2="12" y2="10"/>'
        '<path d="M8 10 L16 10 L14 16 L10 16 Z"/>'
        '<line x1="14" y1="13" x2="19" y2="13"/><circle cx="19" cy="13" r="1.4"/>',
        (12, 12)),
    "ew_jammer_vehicle": (
        '<rect x="4" y="13" width="16" height="6" rx="1"/>'
        '<circle cx="7" cy="19" r="1.4" fill="var(--paper)"/>'
        '<circle cx="17" cy="19" r="1.4" fill="var(--paper)"/>'
        '<path d="M12 13 L12 6 M12 6 L8 3 M12 6 L16 3 M12 6 L12 2"/>',
        (12, 12)),
    "ew_jammer_stationary": (
        '<path d="M6 15 A6 6 0 0 1 18 15 Z"/>'
        '<line x1="4" y1="15" x2="20" y2="15"/>'
        '<line x1="12" y1="15" x2="12" y2="20"/><line x1="8" y1="20" x2="16" y2="20"/>'
        '<path d="M12 9 L8 4 M12 9 L16 4 M12 9 L12 2"/>',
        (12, 12)),
    "ew_jammer_portable": (
        '<line x1="4" y1="14" x2="16" y2="14"/>'
        '<path d="M7 14 L7 19 L10 19 L10 15"/>'
        '<path d="M16 14 L20 11 M16 14 L20 14 M16 14 L20 17"/>',
        (12, 12)),
    "detector_counter_uas": (
        '<circle cx="12" cy="12" r="8"/>'
        '<path d="M12 12 L18 6 A8 8 0 0 1 20 12 Z" fill="var(--paper)" stroke="none" opacity="0.85"/>'
        '<circle cx="15" cy="9" r="1.3" fill="var(--paper)"/>',
        (12, 12)),
    "antenna_mast": (
        '<line x1="12" y1="2" x2="12" y2="21"/>'
        '<line x1="7" y1="8" x2="17" y2="8"/><line x1="8.5" y1="12" x2="15.5" y2="12"/>'
        '<line x1="9.5" y1="16" x2="14.5" y2="16"/><circle cx="12" cy="2" r="1.3" fill="var(--paper)"/>',
        (12, 12)),
    "battery_power": (
        '<rect x="6" y="7" width="12" height="14" rx="1.5"/>'
        '<rect x="10" y="4" width="4" height="3" rx="0.8"/>'
        '<rect x="8" y="10" width="8" height="4" fill="var(--paper)" stroke="none"/>',
        (12, 12)),
    "motor_propeller_part": (
        '<ellipse cx="12" cy="12" rx="9" ry="2.4" transform="rotate(45 12 12)"/>'
        '<ellipse cx="12" cy="12" rx="9" ry="2.4" transform="rotate(-45 12 12)"/>'
        '<circle cx="12" cy="12" r="1.7" fill="var(--paper)"/>',
        (12, 12)),
    "electronics_compute": (
        '<rect x="7" y="7" width="10" height="10" rx="1"/>'
        '<line x1="9" y1="4" x2="9" y2="7"/><line x1="15" y1="4" x2="15" y2="7"/>'
        '<line x1="9" y1="17" x2="9" y2="20"/><line x1="15" y1="17" x2="15" y2="20"/>'
        '<line x1="4" y1="9" x2="7" y2="9"/><line x1="4" y1="15" x2="7" y2="15"/>'
        '<line x1="17" y1="9" x2="20" y2="9"/><line x1="17" y1="15" x2="20" y2="15"/>'
        '<circle cx="12" cy="12" r="1.6" fill="var(--paper)"/>',
        (12, 12)),
    "nav_gnss": (
        '<rect x="10" y="4" width="4" height="4" rx="0.6"/>'
        '<path d="M10 6 L6 4 L6 8 L10 6"/><path d="M14 6 L18 4 L18 8 L14 6"/>'
        '<path d="M9 10 A5 5 0 0 1 15 10"/><path d="M7 13 A8 8 0 0 1 17 13"/>'
        '<circle cx="12" cy="20" r="1.4" fill="var(--paper)"/>',
        (12, 12)),
    "video_control_link": (
        '<circle cx="12" cy="19" r="1.4" fill="var(--paper)"/>'
        '<path d="M9.5 15.5 A3.5 3.5 0 0 1 14.5 15.5"/>'
        '<path d="M6.5 12.5 A7.5 7.5 0 0 1 17.5 12.5"/>'
        '<path d="M3.5 9.5 A11.5 11.5 0 0 1 20.5 9.5"/>',
        (12, 12)),
    "ground_control_station": (
        '<rect x="4" y="6" width="16" height="10" rx="1"/>'
        '<line x1="9" y1="20" x2="15" y2="20"/><line x1="12" y1="16" x2="12" y2="20"/>'
        '<circle cx="9" cy="11" r="1.6"/>'
        '<line x1="14" y1="9" x2="17" y2="9"/><line x1="14" y1="13" x2="17" y2="13"/>',
        (12, 12)),
    "munition_warhead": (
        '<path d="M12 2 C15 2 16 6 16 10 L16 18 C16 20 14 21 12 21 C10 21 8 20 8 18 L8 10 C8 6 9 2 12 2 Z"/>'
        '<line x1="8" y1="10" x2="16" y2="10"/><line x1="9" y1="6" x2="15" y2="6"/>',
        (12, 12)),
    "repeater_relay": (
        '<path d="M12 3 L7 20 M12 3 L17 20"/>'
        '<line x1="9.3" y1="12" x2="14.7" y2="12"/><line x1="8" y1="16" x2="16" y2="16"/>'
        '<path d="M3 9 A9 9 0 0 1 6 4 M21 9 A9 9 0 0 0 18 4"/>',
        (12, 12)),
}


def icon_glyph_svg(x, y, r, paths, center):
    """Places a 24x24-viewBox icon centered at (x, y), scaled to roughly
    2*r across -- same visual weight as the circle it's drawn over. Icon
    ink is var(--paper) -- the page's own light/dark background token --
    so it reads against any tier color in either theme without a new
    token (same trick --product-icon-ink solves for in the live graph)."""
    cx0, cy0 = center
    s = (2.0 * r) / 20.0
    transform = f'translate({x:.1f},{y:.1f}) scale({s:.3f}) translate({-cx0:.2f},{-cy0:.2f})'
    return (f'<g transform="{transform}" fill="none" stroke="var(--paper)" stroke-width="1.6" '
            f'stroke-linecap="round" stroke-linejoin="round">{paths}</g>')

CASES = [
    {"slug": "arkhangel", "status": "published", "title": "Проект «Архангел»",
     "line": "An interceptor drone, combat-drone training and state-format diplomas from one Telegram network, with no public contract behind any of it.",
     "graph": {
         "hub": "proekt-kb-arkhangel",
         "nodes": {
             "proekt-kb-arkhangel": "Проект «Архангел»",
             "filippov-mikhail-gennadevich": "Филиппов М.Г.",
             "ooo-arkhangel-grupp": "ООО «Архангел Групп»",
             "ano-nii-dpo": "АНО «НИИ ДПО»",
             "ooo-nii-dpo": "ООО «НИИ ДПО»",
             "eskov-nikolay-leonidovich": "Еськов Н.Л.",
             "npo-kaysant": "НПО «КАЙСАНТ»",
             "ano-tsbst-centre-for-unmanned-systems-technologies": "АНО «ЦБСТ»",
             "csn-bars-sarmat": "ЦСН «Барс-Сармат»",
             "fond-sarmat": "Фонд «Сармат»",
             "rogozin-dmitriy-olegovich": "Рогозин Д.О.",
             "rogozin-aleksey-dmitrievich": "Рогозин А.Д.",
             "ano-tsvp-zov-aa": "АНО «ЗОВ-АА»",
          },
         "caption": "Static excerpt of the registry graph: the Архангел cluster and its documented neighbours. The one link from the cluster to the core network runs through the ЦБСТ resident КАЙСАНТ, and it is a self-reported component supply, not a contract.",
     }},
    {"slug": "gagaring", "status": "published", "title": "Гагаринг",
     "kicker": "Case study · ЦБСТ resident",
     "line": "A company registered in September 2023 reports ₽2.16bn in 2025 revenue, is named a ЦБСТ resident by ЦБСТ itself, and appears in no public procurement record.",
     "graph": {
         "hub": "ooo-gagaring",
         "nodes": {
             "ooo-gagaring": "ООО «Гагаринг»",
             "barashkov-aleksandr-sergeevich": "Барашков А.С.",
             "aleksandrov-aleksey-vitalevich": "Александров А.В.",
             "ano-dpo-obrazovatelny-tsentr-gagaring": "АНО ДПО «Образовательный центр»",
             "ooo-aviron": "ООО «Авирон»",
             "ooo-intel-dron": "ООО «Интел Дрон»",
             "ooo-npo-eyler": "ООО «НПО Эйлер»",
             "ano-arrs-krasnodar": "АРРС",
             "ooo-akr-begak": "ООО «АКР «Бегак»",
             "ooo-praym": "ООО «Прайм»",
             "ano-arkhangel": "АНО «Архангел» (Легион)",
             "ano-tsbst-centre-for-unmanned-systems-technologies": "АНО «ЦБСТ»",
         },
         "caption": "Static excerpt of the registry graph: Гагаринг, its owners, part-owned companies, training body and industry association. Гагаринг and Авирон carry a documented ЦБСТ resident tie. The Архангел ties described on this page rest on posts and are only partly in the graph.",
     }},
    {"slug": "goudron", "status": "published", "title": "ГОУДРОН",
     "kicker": "Case study · ЦБСТ tie from the company's own channel",
     "line": "A household-electrical wholesaler registered at an apartment sells «Набат» drone detectors with a price tier for soldiers.",
     "graph": {
         "hub": "ooo-goudron",
         "extra_edges": ["produces"],
         "nodes": {
             "ooo-goudron": "ООО «ГОУДРОН»",
             "kozlov-dmitriy-sergeevich": "Козлов Д.С.",
             "product::ooo-goudron::набат-v3": "«Набат V.3»",
             "ano-tsbst-centre-for-unmanned-systems-technologies": "АНО «ЦБСТ»",
         },
         "caption": "Static excerpt of the registry graph: the whole documented network is one owner, one product and one ЦБСТ tie, which rests on the company's own channel. The red outline is a sanctions flag: Ukraine's register lists the company (signed extract), and no other regime is on file.",
     }},
    {"slug": "ovod", "status": "published", "title": "Овод and Черезов",
     "kicker": "Case study · ЦБСТ resident",
     "line": "Two Tula companies with one owner, a ₽1.3bn FPV-drone maker that ЦБСТ calls its flagship resident, and a founder shot in July 2026.",
     "graph": {
         "hub": "ovod",
         "extra_edges": ["produces", "procures"],
         "nodes": {
             "ovod": "ООО «РЛВТ» («Овод»)",
             "ooo-vozdushnyy-traktat": "ООО «Воздушный трактат»",
             "cherezov-andrey-pavlovich": "Черезов А.П.",
             "ano-tsbst-centre-for-unmanned-systems-technologies": "АНО «ЦБСТ»",
             "product::ovod::овод": "«Овод»",
             "product::ovod::провод-15": "«Провод-15»",
             "customer::фгбоу-во-воронежский-государственный-технический-университет": "Воронежский ГТУ",
             "customer::фгбоу-во-белгородский-государственный-технологический-университет-им-в-г-шухова": "Белгородский ГТУ",
         },
         "caption": "Static excerpt of the registry graph: one owner, two companies, two products, two university customers and the ЦБСТ tie. The red outlines are sanctions flags from aggregator and press-level entries, not primary listings.",
     }},
    {"slug": "piranya", "status": "published", "title": "Пиранья",
     "kicker": "Case study · ЦБСТ resident on the EU list",
     "line": "A company registered as software development sells combat FPV drones from one unit on its website, and the EU says it makes up to 10,000 a month.",
     "graph": {
         "hub": "ooo-skb-piranya",
         "extra_edges": ["produces"],
         "nodes": {
             "ooo-skb-piranya": "ООО «СКБ Пиранья»",
             "chernyshov-pavel-alekseevich": "Чернышов П.А.",
             "korchagina-olga-aleksandrovna": "Корчагина О.А.",
             "ano-tsbst-centre-for-unmanned-systems-technologies": "АНО «ЦБСТ»",
             "product::ooo-skb-piranya::бпла-пиранья-7": "«Пиранья-7»",
             "product::ooo-skb-piranya::бпла-пиранья-10": "«Пиранья-10»",
             "product::ooo-skb-piranya::бпла-пиранья-13": "«Пиранья-13»",
         },
         "caption": "Static excerpt of the registry graph: two owners, three drone models and the ЦБСТ tie. The red outline on the company is the EU listing; the 60% owner's outline is an aggregator match, and the director has no outline because his match is only plausible.",
     }},
    {"slug": "bulat", "status": "published", "title": "Цыганов and «Булат»",
     "kicker": "Case study · ЦБСТ tie on the maker",
     "line": "A Petersburg detector maker with hidden owners, a sole trader in Khimki, and ₽28.2m of МЧС contracts awarded without a tender.",
     "graph": {
         "hub": "ooo-pokrov",
         "extra_edges": ["produces", "procures"],
         "nodes": {
             "ooo-pokrov": "ООО «ПОКРОВ»",
             "ip-tsyganov-vadim-borisovich": "ИП Цыганов В.Б.",
             "tsyganov-vadim-borisovich": "Цыганов В.Б.",
             "ooo-trimiks": "ООО «Тримикс» (3MX)",
             "ano-tsbst-centre-for-unmanned-systems-technologies": "АНО «ЦБСТ»",
             "customer::главное-управление-мчс-россии-по-курской-области": "ГУ МЧС по Курской обл.",
             "customer::фгку-центр-по-проведению-спасательных-операций-особого-риска-лидер": "ЦСООР «Лидер»",
             "customer::администрация-белгородского-муниципального-округа": "Администрация Белгородского м.о.",
             "product::ooo-trimiks::булат-в-4": "«Булат» в.4",
         },
         "caption": "Static excerpt of the registry graph: the maker, the dealer company, the sole trader, the owner and three public buyers. Red outlines are sanctions flags: the dealer company's is a primary listing, the others are aggregator matches.",
     }},
    {"slug": "basirtk", "status": "published", "title": "НПЦ БАСиРТК",
     "kicker": "Case study · ЦБСТ core",
     "line": "A micro-enterprise with two employees reports ₽83.7m in its second year, hands cardboard drones to army units, and sits in ЦБСТ's accelerator.",
     "graph": {
         "hub": "ooo-npts-basirtk",
         "extra_edges": ["produces"],
         "nodes": {
             "ooo-npts-basirtk": "ООО «НПЦ БАСиРТК»",
             "baygutlina-irina-anatolevna": "Байгутлина И.А.",
             "product::ooo-npts-basirtk::ковровец": "«Ковровец»",
             "ano-tsbst-centre-for-unmanned-systems-technologies": "АНО «ЦБСТ»",
         },
         "caption": "Static excerpt of the registry graph: one owner, one product and one ЦБСТ tie. The tie rests on the company's own report of its accelerator selection.",
     }},
]

CHIPS = {"doc": ("t-doc", "Primary doc"), "press": ("t-press", "Press-reported"), "open": ("t-open", "Open")}

# Set once per build_case() call: lets inline() turn a single-id [sNNNN]
# citation into a native-popover button (see .cite/.cite-pop in profile.css
# and profile_text.py, which this reuses). A multi-id/range bracket
# ([s7973, s7975-s7980]) is left as plain text; a plain comma list gets one
# popover per id (see cite() in inline()).
_CITE_SRC_BY_ID = {}
_CITE_USED = set()

NAV = ('<nav class="topnav" aria-label="Site">'
       '<a href="{r}index.html">Home</a><a href="{r}cases/index.html">Cases</a>'
       '<a href="{r}relationship-graph.html">Graph</a><a href="{r}profiles/index.html">Profiles</a>'
       '<a href="{r}story.html">Guided read</a></nav>')

EXTRA_CSS = """
.topnav{display:flex;flex-wrap:wrap;gap:.4rem 1.4rem;padding:1rem 0;border-bottom:1px solid var(--rule-soft);font-family:var(--mono);font-size:.72rem;letter-spacing:.08em;text-transform:uppercase}
.topnav a{color:var(--ink-2);text-decoration:none}.topnav a:hover{color:var(--accent)}
.case-list{display:grid;grid-template-columns:repeat(auto-fit,minmax(17rem,1fr));gap:1px;background:var(--rule-soft);border:1px solid var(--rule-soft);border-radius:3px;overflow:hidden;margin:1.25rem 0}
.case-list .card{display:block;text-decoration:none;color:inherit}
.case-list a.card:hover{background:var(--accent-soft)}
.case-list .planned{opacity:.6}
.route-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(14rem,1fr));gap:1.25rem;margin:1.5rem 0}
.route{background:var(--panel);border:1px solid var(--rule-soft);border-radius:4px;padding:1.1rem;text-decoration:none;color:inherit;display:block}
.route:hover{border-color:var(--accent)}
.route .lbl{font-family:var(--mono);font-size:.66rem;letter-spacing:.12em;text-transform:uppercase;color:var(--accent);display:block;margin-bottom:.4rem}
.route .name{font-family:var(--serif);font-size:1.15rem;display:block;margin-bottom:.35rem}
.route .note{font-size:.85rem;color:var(--ink-2)}
.case-body h2{margin-top:3rem}.case-body ul,.case-body ol{padding-left:1.3rem;margin:0 0 1rem}.case-body li{margin-bottom:.4rem}
.case-body{max-width:100%}.case-body p,.case-body ul,.case-body ol{max-width:46rem}
details.srcs summary{cursor:pointer;font-family:var(--mono);font-size:.78rem;color:var(--ink-2);margin:.5rem 0}

/* ---------- landing page ---------- */
.hero-row{display:flex;gap:2.5rem;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;margin-top:.5rem}
.hero-text{flex:1 1 22rem;min-width:0;font-size:.95rem;color:var(--ink-2);line-height:1.6;max-width:34rem;padding-top:.6rem}
.net-motif{flex:0 0 15rem;width:15rem;max-width:100%}
.net-motif svg{width:100%;height:auto;display:block}
.net-motif text{font-family:var(--mono);font-size:8.5px;fill:var(--ink-3)}
.net-motif text.hub{fill:var(--ink-2);font-weight:600}
.net-motif .cap{font-family:var(--mono);font-size:.64rem;color:var(--ink-3);text-align:center;margin-top:.5rem;letter-spacing:.02em}

.case-feed{display:flex;flex-direction:column;gap:1px;background:var(--rule-soft);border:1px solid var(--rule-soft);border-radius:3px;overflow:hidden;margin:1.25rem 0}
.case-feed a{display:grid;grid-template-columns:6.5rem 1fr;gap:1.1rem;align-items:baseline;background:var(--panel);padding:1rem 1.1rem;text-decoration:none;color:inherit}
.case-feed a:hover{background:var(--accent-soft)}
.case-feed .kick{font-family:var(--mono);font-size:.66rem;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-3)}
.case-feed h3{font-family:var(--serif);font-size:1.08rem;font-weight:400;margin:0 0 .3rem}
.case-feed p{margin:0;font-size:.88rem;color:var(--ink-2);line-height:1.5;max-width:42rem}
@media (max-width:34rem){.case-feed a{grid-template-columns:1fr}.case-feed .kick{order:-1}}

.route-grid.secondary{margin-top:.5rem}
.route-grid.secondary .route{padding:.9rem 1rem}
.route-grid.secondary .name{font-size:1rem}
""".strip()


def esc(t):
    return html.escape(t, quote=False)


def inline(t):
    t = esc(t)
    t = re.sub(r"\{(doc|press|open)\}", lambda m: f'<span class="tag {CHIPS[m[1]][0]}">{CHIPS[m[1]][1]}</span>', t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    def cite(m):
        sid = m[1]
        if re.fullmatch(r"s\d{4}", sid) and sid in _CITE_SRC_BY_ID:
            _CITE_USED.add(sid)
            return f'<button type="button" class="cite" popovertarget="cite-{sid}">[{sid}]</button>'
        # A plain comma list of known ids gets one popover per id inside a single
        # bracket; ranges and anything unresolved stay plain text.
        parts = [p.strip() for p in sid.split(",")]
        if len(parts) > 1 and all(p in _CITE_SRC_BY_ID for p in parts):
            _CITE_USED.update(parts)
            btns = ", ".join(f'<button type="button" class="cite" popovertarget="cite-{p}">{p}</button>'
                             for p in parts)
            return f'<span class="cite-group">[{btns}]</span>'
        return f'<span class="id">[{sid}]</span>'
    t = re.sub(r"\[((?:s\d{4}(?:[–-]s\d{4})?(?:, ?)?)+|[^\]]*(?:s\d{4}|msg|t\.me)[^\]]*)\]",
              cite, t)
    return t


def md_to_html(md):
    out, i, lines = [], 0, md.split("\n")
    title = None
    sec_open = False
    while i < len(lines):
        l = lines[i]
        if l.startswith("# "):
            title = l[2:].strip(); i += 1; continue
        if l.startswith("## "):
            if sec_open: out.append("</section>")
            out.append(f"<section><h2>{inline(l[3:].strip())}</h2>"); sec_open = True; i += 1; continue
        if l.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[-| ]+\|$", lines[i + 1]):
            head = [c.strip() for c in l.strip("|").split("|")]
            i += 2; rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip("|").split("|")]); i += 1
            t = "<div class='scroll'><table><thead><tr>" + "".join(f"<th>{inline(h)}</th>" for h in head) + "</tr></thead><tbody>"
            for r in rows:
                t += "<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>"
            out.append(t + "</tbody></table></div>"); continue
        if re.match(r"^- ", l):
            items = []
            while i < len(lines) and lines[i].startswith("- "):
                items.append(lines[i][2:]); i += 1
            out.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ul>"); continue
        if re.match(r"^\d+\. ", l):
            items = []
            while i < len(lines) and re.match(r"^\d+\. ", lines[i]):
                items.append(re.sub(r"^\d+\. ", "", lines[i])); i += 1
            out.append("<ol>" + "".join(f"<li>{inline(x)}</li>" for x in items) + "</ol>"); continue
        if l.strip() == "":
            i += 1; continue
        para = [l]; i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#|\||- |\d+\. )", lines[i]):
            para.append(lines[i]); i += 1
        out.append(f"<p>{inline(' '.join(para))}</p>")
    if sec_open: out.append("</section>")
    return title, "\n".join(out)


def cited_sources(md, sources):
    ids = set()
    for m in re.finditer(r"s(\d{4})\s*[–-]\s*s(\d{4})", md):
        a, b = int(m[1]), int(m[2])
        ids.update(f"s{n:04d}" for n in range(a, b + 1) if b - a < 60)
    ids.update(re.findall(r"\bs\d{4}\b", md))
    by = {s["id"]: s for s in sources}
    rows = []
    for sid in sorted(ids):
        s = by.get(sid)
        if not s:
            continue
        loc = s.get("url") or (Path(s["path"]).name if s.get("path") else "")
        rows.append((sid, loc, s.get("captured_date") or "", s.get("as_of") or ""))
    return rows


def graph_svg(cfg, g, weak=frozenset(), products=None):
    ids = {n["id"]: n for n in g["nodes"]}
    want = [k for k in cfg["nodes"] if k in ids]
    prio = {"family_tie": 0, "cbst_tie": 1, "founded": 2, "owns": 2, "directs": 3, "related": 4, "role": 9, "produces": 9, "procures": 9}
    best = {}
    for e in g["edges"]:
        a, b = e["source"], e["target"]
        if a in cfg["nodes"] and b in cfg["nodes"] and e["type"] in ("family_tie", "cbst_tie", "founded", "owns", "directs", "related", "role") + tuple(cfg.get("extra_edges", ())):
            k = tuple(sorted((a, b)))
            if k not in best or prio[e["type"]] < prio[best[k]["type"]]:
                best[k] = e
    rnd = random.Random(7)
    W, H = 900, 560
    pos = {k: [W / 2 + rnd.uniform(-200, 200), H / 2 + rnd.uniform(-150, 150)] for k in want}
    pos[cfg["hub"]] = [W / 2, H / 2]
    for it in range(400):
        f = {k: [0.0, 0.0] for k in want}
        for i, a in enumerate(want):
            for b in want[i + 1:]:
                dx, dy = pos[a][0] - pos[b][0], pos[a][1] - pos[b][1]
                d2 = max(dx * dx + dy * dy, 25); d = math.sqrt(d2); rep = 26000 / d2
                f[a][0] += rep * dx / d; f[a][1] += rep * dy / d
                f[b][0] -= rep * dx / d; f[b][1] -= rep * dy / d
        for (a, b) in best:
            dx, dy = pos[b][0] - pos[a][0], pos[b][1] - pos[a][1]
            d = max(math.sqrt(dx * dx + dy * dy), 1); att = (d - 130) * 0.02
            f[a][0] += att * dx / d; f[a][1] += att * dy / d
            f[b][0] -= att * dx / d; f[b][1] -= att * dy / d
        for k in want:
            f[k][0] += (W / 2 - pos[k][0]) * 0.004; f[k][1] += (H / 2 - pos[k][1]) * 0.004
            if k == cfg["hub"]: continue
            pos[k][0] = min(W - 70, max(70, pos[k][0] + f[k][0] * 0.6))
            pos[k][1] = min(H - 30, max(30, pos[k][1] + f[k][1] * 0.6))
    svg = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Network excerpt" style="max-width:{W}px">']
    for (a, b), e in best.items():
        t = e["type"]
        style = {"cbst_tie": 'stroke="#eb6834" stroke-width="3"', "family_tie": 'stroke="var(--ink-3)" stroke-width="1.6" stroke-dasharray="2 4"',
                 "founded": 'stroke="var(--ink-2)" stroke-width="1.8"', "owns": 'stroke="var(--ink-2)" stroke-width="1.8"',
                 "directs": 'stroke="var(--ink-3)" stroke-width="1.4"', "role": 'stroke="var(--ink-3)" stroke-width="1.2" stroke-dasharray="1 3"', "produces": 'stroke="var(--ink-3)" stroke-width="1.2"', "procures": 'stroke="var(--ink-3)" stroke-width="1.2" stroke-dasharray="8 3"',
                 
                 "related": 'stroke="var(--ink-3)" stroke-width="1.4" stroke-dasharray="6 4"'}[t]
        svg.append(f'<line x1="{pos[a][0]:.0f}" y1="{pos[a][1]:.0f}" x2="{pos[b][0]:.0f}" y2="{pos[b][1]:.0f}" {style}/>')
    for k in want:
        n, (x, y) = ids[k], pos[k]
        col = (PERSON_COL if n["kind"] == "person" else
               TIER_COL["network"] if n["kind"] in ("government_customer", "military_unit") else
               TIER_COL.get(n.get("tier"), TIER_COL[None]))
        ring = ' stroke="#c0392b" stroke-width="2.5"' if n.get("sanctioned") and k not in weak else ""
        r = 14 if k == cfg["hub"] else 9
        # Shape grammar matches the live Network Graph artifact (2026-09-22 fix): circle =
        # organization, diamond = person, square = product -- was inverted here (circle for
        # person, rect for org) before this fix, so a reader moving from a case-page excerpt
        # into the live interactive graph saw the same tier colours mean the same thing but
        # the same shapes mean different things. government_customer/military_unit keep the
        # live graph's own circle-with-glyph treatment (they're drawn as a distinct icon
        # layer there too, not folded into either "organization" or "person").
        if n["kind"] == "person":
            pts = f"{x:.0f},{y - r:.0f} {x + r:.0f},{y:.0f} {x:.0f},{y + r:.0f} {x - r:.0f},{y:.0f}"
            svg.append(f'<polygon points="{pts}" fill="{col}"{ring}/>')
        elif n["kind"] == "government_customer":
            svg.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="{col}"{ring}/>')
            svg.append(icon_glyph_svg(x, y, r, CUSTOMER_ICON_PATHS, CUSTOMER_ICON_CENTER))
        elif n["kind"] == "military_unit":
            svg.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="{col}"{ring}/>')
            svg.append(icon_glyph_svg(x, y, r, MILITARY_UNIT_ICON_PATHS, MILITARY_UNIT_ICON_CENTER))
        elif n["kind"] == "product" and products and products.get(k) in PRODUCT_ICONS:
            side = 1.7 * r
            svg.append(f'<rect x="{x - side / 2:.0f}" y="{y - side / 2:.0f}" width="{side:.0f}" height="{side:.0f}" rx="3" fill="{col}"{ring}/>')
            paths, center = PRODUCT_ICONS[products[k]]
            svg.append(icon_glyph_svg(x, y, r * 0.85, paths, center))
        elif n["kind"] == "product":
            side = 1.7 * r
            svg.append(f'<rect x="{x - side / 2:.0f}" y="{y - side / 2:.0f}" width="{side:.0f}" height="{side:.0f}" rx="3" fill="{col}"{ring}/>')
        else:
            svg.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="{col}"{ring}/>')
        svg.append(f'<text x="{x:.0f}" y="{y + r + 13:.0f}" text-anchor="middle" font-size="11.5" fill="var(--ink)" stroke="var(--panel)" stroke-width="3.5" paint-order="stroke">{esc(cfg["nodes"][k])}</text>')
    svg.append("</svg>")
    legend = ('<div class="net-legend">'
              # Shapes match the live Network Graph artifact: circle = organization,
              # diamond = person, square (below) = product -- see the graph_svg() shape fix.
              '<span><span class="net-swatch" style="background:#e87ba4;border-radius:50%"></span> adjacent</span>'
              '<span><span class="net-swatch" style="background:#2a78d6;border-radius:50%"></span> manufacturer</span>'
              '<span><span class="net-swatch" style="background:#1baf7a;border-radius:50%"></span> plumbing</span>'
              '<span><span class="net-swatch" style="background:#eb6834;border-radius:50%"></span> ЦБСТ core</span>'
              f'<span><span class="net-swatch" style="background:{PERSON_COL};border-radius:2px;transform:rotate(45deg)"></span> person</span>'
              f'<span><span class="net-swatch" style="background:{TIER_COL["network"]};border-radius:50%"></span> govt./military customer</span>'
              '<span>product squares carry one of 17 category glyphs from <code>classify_product_icon.py</code> (full legend: the standalone "Product Icon Set" exhibit); a plain square is unclassified -- a gap, not a guess</span>'
              '<span>thick orange = ЦБСТ resident tie · solid = ownership/directs/produces · long dash = buys from · fine dotted = role/family · dashed = related · red outline = sanctions flag in the registry (weak name-only matches are not outlined)</span></div>')
    return (f'<div class="net-panel"><div class="net-svg-wrap">{"".join(svg)}</div>{legend}</div>'
            f'<p class="footnote" style="margin-top:.75rem;border:none;padding:0">{esc(cfg["caption"])} '
            f'{len(want)} of {g["node_count"]:,} nodes.</p>')


def page(title, body, rel, kicker, standfirst=None, extra_head=""):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — РОЙ.МАРКЕТ investigation</title>
<link rel="stylesheet" href="{rel}assets/profile.css">
<style>{EXTRA_CSS}</style>
{extra_head}</head>
<body>
<div class="wrap">
{NAV.format(r=rel)}
<div class="mast">
  <p class="kicker">{esc(kicker)}</p>
  <h1>{esc(title)}</h1>
{f'  <p class="standfirst">{esc(standfirst)}</p>' if standfirst else ''}
</div>
{body}
<p class="footnote">Generated from the registry by <code>scripts/build_case_pages.py</code>. Source ids resolve in the sources table; no claim is asserted without one.</p>
</div>
</body>
</html>
"""


def build_case(case, g, sources, weak=frozenset(), products=None):
    global _CITE_SRC_BY_ID, _CITE_USED
    _CITE_SRC_BY_ID = {s["id"]: s for s in sources}
    _CITE_USED = set()
    md = (REPO / "notes" / f"case_study_{case['slug']}.md").read_text(encoding="utf-8")
    title, body = md_to_html(md)
    graph = graph_svg(case["graph"], g, weak, products)
    body = body.replace("</section>", "</section>", 1)
    first = body.index("</section>") + len("</section>")
    body = body[:first] + f"<section><p class='eyebrow'>The network</p>{graph}</section>" + body[first:]
    # the intro line (grades) sits before the first section: pull it out above the finding
    rows = cited_sources(md, sources)
    src = ("<section><p class='eyebrow'>Sources cited</p><details class='srcs'><summary>"
           f"{len(rows)} sources resolved</summary><div class='scroll'><table><thead><tr><th>Id</th><th>Locator</th><th>Captured</th><th>As of</th></tr></thead><tbody>"
           + "".join(f"<tr><td class='id'>{sid}</td><td>{esc(loc)}</td><td class='num'>{c}</td><td class='num'>{a}</td></tr>" for sid, loc, c, a in rows)
           + "</tbody></table></div></details></section>")
    intro = ""
    m = re.match(r"\s*(<p>.*?</p>)", body, re.S)
    if m:
        intro, body = m.group(1), body[m.end():]
    legend = ('<div class="legend"><span><span class="tag t-doc">Primary doc</span> official extract, platform document, or a post that exists (proves it was said, not that it is true)</span>'
              '<span><span class="tag t-press">Press-reported</span> named outlet, wording not verified</span>'
              '<span><span class="tag t-open">Open</span> unconfirmed, incl. own-channel claims</span></div>')
    html_out = page(title, f'<div class="case-body">{intro}{legend}{body}{src}</div>', "../",
                    case.get("kicker", "Case study · no confirmed ЦБСТ tie"))
    if _CITE_USED:
        pops = "".join(popover_html(sid, _CITE_SRC_BY_ID[sid]) for sid in sorted(_CITE_USED))
        html_out = html_out.replace("</body>", pops + "</body>", 1)
    (DOCS / "cases" / f"{case['slug']}.html").write_text(html_out, encoding="utf-8")


def network_motif(cases):
    """Static SVG: ЦБСТ at the centre, one spoke per published case hub. Real
    slugs/titles, frozen positions -- a diagram of the actual site content,
    not decoration (see the artifact-design 'structure is information' rule)."""
    pub = [c for c in cases if c["status"] == "published"]
    n = len(pub)
    # A spoke is solid only where the case hub has its own cbst_tie edge to ЦБСТ in the
    # registry graph; a hub that reaches ЦБСТ through a neighbour is drawn dashed.
    _g = json.loads((REG / "relationship_graph.json").read_text(encoding="utf-8"))
    _centre = "ano-tsbst-centre-for-unmanned-systems-technologies"
    _direct = {e["source"] if e["target"] == _centre else e["target"]
               for e in _g["edges"] if e["type"] == "cbst_tie" and _centre in (e["source"], e["target"])}
    cx, cy, r = 100, 100, 62
    parts = [f'<circle cx="{cx}" cy="{cy}" r="17" fill="var(--accent-soft)" stroke="var(--accent)" stroke-width="1.2"/>',
              f'<text class="hub" x="{cx}" y="{cy+3}" text-anchor="middle">ЦБСТ</text>']
    short = {"arkhangel": "Архангел", "gagaring": "Гагаринг", "goudron": "ГОУДРОН", "ovod": "Овод",
             "piranya": "Пиранья", "bulat": "Булат", "basirtk": "БАСиРТК"}
    for i, c in enumerate(pub):
        a = -math.pi / 2 + i * 2 * math.pi / n
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        lx, ly = cx + (r + 16) * math.cos(a), cy + (r + 16) * math.sin(a)
        anchor = "middle" if abs(math.cos(a)) < 0.35 else ("start" if math.cos(a) > 0 else "end")
        dash = "" if c["graph"]["hub"] in _direct else ' stroke-dasharray="3 3"'
        parts.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="var(--rule)" stroke-width="1"{dash}/>')
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5.5" fill="var(--panel)" stroke="var(--ink-3)" stroke-width="1"/>')
        parts.append(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" dominant-baseline="middle">{esc(short.get(c["slug"], c["title"]))}</text>')
    svg = f'<svg viewBox="-38 -14 276 228" role="img" aria-label="ЦБСТ and its {n} documented case-study networks">{"".join(parts)}</svg>'
    return f'<div class="net-motif">{svg}<p class="cap">{n} of the registry\'s networks around ЦБСТ: {sum(c["graph"]["hub"] in _direct for c in pub)} hold a direct tie (solid), the rest reach it through a neighbour (dashed)</p></div>'


def build_indexes(stats):
    cards = []
    for c in CASES:
        if c["status"] == "published":
            cards.append(f'<a class="card" href="{c["slug"]}.html"><span class="tag t-doc">Published</span><h3>{esc(c["title"])}</h3><p>{esc(c["line"])}</p></a>')
        else:
            cards.append(f'<div class="card planned"><span class="tag t-open">In preparation</span><h3>{esc(c["title"])}</h3><p>{esc(c["line"])}</p></div>')
    (DOCS / "cases" / "index.html").write_text(
        page("Case studies", f'<section><div class="case-list">{"".join(cards)}</div></section>', "../", "Cases",
             "Each case is one network told from the registry: a flat finding, a static graph excerpt, graded claims and every source."),
        encoding="utf-8")

    hero_note = ('<p>Every entity, person and claim below sits in the registry with a source id and a grade. '
                 'This page routes to the case studies, the full network graph, and the guided read.</p>')
    hero = f'<div class="hero-row"><div class="hero-text">{hero_note}</div>{network_motif(CASES)}</div>'

    feed_items = []
    for c in CASES:
        if c["status"] != "published":
            continue
        kick = esc(c.get("kicker", "Case study"))
        feed_items.append(
            f'<a href="cases/{c["slug"]}.html"><span class="kick">{kick}</span>'
            f'<div><h3>{esc(c["title"])}</h3><p>{esc(c["line"])}</p></div></a>')
    case_feed = (f'<section><p class="eyebrow">Start here — {len(feed_items)} case studies</p>'
                 f'<div class="case-feed">{"".join(feed_items)}</div></section>')

    routes = [
        ("Explore", "Network graph", f"{stats['nodes']:,} nodes and {stats['edges']:,} sourced ties. Search, filter, click into any node.", "relationship-graph.html"),
        ("Look up", "Profiles", f"{stats['entities']} entities, {stats['people']} people and the flagship products, one page each.", "profiles/index.html"),
        ("Guided read", "From ЦБСТ to the Front", "A short guide to the supply chains, for a first read.", "story.html"),
        ("All cases", "Case index", "The full case list, including any in preparation.", "cases/index.html"),
    ]
    rc = "".join(f'<a class="route" href="{h}"><span class="lbl">{esc(l)}</span><span class="name">{esc(n)}</span><span class="note">{esc(t)}</span></a>' for l, n, t, h in routes)
    legend = ('<div class="legend"><span><span class="tag t-doc">Primary doc</span> verified in an official extract, a platform document, or a post that exists (proves it was said, not that it is true)</span>'
              '<span><span class="tag t-press">Press-reported</span> attributed to a named outlet, wording not verified</span>'
              '<span><span class="tag t-open">Open</span> unresolved: not published as fact</span></div>')
    body = (f'<section>{hero}</section>'
            f'{case_feed}'
            f'<section><p class="eyebrow">More ways in</p><div class="route-grid secondary">{rc}</div></section>'
            f'<section><p class="eyebrow">How to read a claim</p><div class="prose"><p>Every claim on these pages carries a source id that resolves to a captured document, and a grade. '
            f'The registry holds {stats["entities"]} entities, {stats["people"]} people and {stats["sources"]:,} sources. Where a claim rests on the subject\'s own channel alone, it is graded Open.</p></div>{legend}</section>')
    (DOCS / "index.html").write_text(
        page("РОЙ.МАРКЕТ / ЦБСТ", body, "", "Open-source investigation",
             "ЦБСТ, the defence-tech body behind the РОЙ.МАРКЕТ military marketplace, and the network of manufacturers, training bodies and intermediaries around it."),
        encoding="utf-8")


def main():
    g = json.load(open(REG / "relationship_graph.json", encoding="utf-8"))
    sources = json.load(open(REG / "sources.json", encoding="utf-8"))
    ents = json.load(open(REG / "entities.json", encoding="utf-8"))
    ppl = json.load(open(REG / "people.json", encoding="utf-8"))
    weak = {r["slug"] for r in list(ents) + list(ppl)
            if r.get("sanctions") and all("PLAUSIBLE" in str(s.get("note") or "") and "ID-CONFIRMED" not in str(s.get("note") or "") for s in r["sanctions"])}
    # Product-node id -> classify_product_icon.py category, keyed the same
    # way graph node ids are built (product::<owner_slug>::<slug-of-name>)
    # so graph_svg() can look a node straight up without re-deriving the
    # entity/product it came from.
    products = {}
    for e in ents:
        for p in e.get("products") or []:
            if not isinstance(p, dict):
                continue  # a handful of entities carry bare product-name strings, not records
            for n in g["nodes"]:
                if n["kind"] == "product" and n.get("owner_slug") == e["slug"] and n["label"] == p.get("name_ru"):
                    cat, _tier = classify_product(p)
                    products[n["id"]] = cat
    (DOCS / "cases").mkdir(exist_ok=True)
    for c in CASES:
        if c["status"] == "published":
            build_case(c, g, sources, weak, products)
    build_indexes({"nodes": g["node_count"], "edges": g["edge_count"], "entities": len(ents), "people": len(ppl), "sources": len(sources)})
    print("wrote docs/index.html, docs/cases/index.html and", sum(c["status"] == "published" for c in CASES), "case page(s)")


if __name__ == "__main__":
    main()
