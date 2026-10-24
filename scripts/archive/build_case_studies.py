#!/usr/bin/env python3
"""Generates exhibits/case_study_excerpts.html.

Five small, fixed, non-interactive sub-graph exhibits (Part 3 of the
Network Graph split plan in notes/rebuild_plan.md) -- one per flagship
case-study entity already prioritized by the 2026-09-15 evidence-depth
audit. Positions are hand-placed (a fixed radial layout per panel), not a
frozen force simulation -- reasonable for graphs this small (4-8 nodes)
where a deliberate layout reads more clearly than a simulated one, and
position carries no evidentiary meaning either way, same as the live graph.

Node/edge sets are exact 1-hop neighborhoods of each anchor pulled from
data/registry/relationship_graph.json (trimmed of duplicate customer nodes
and product entries where a case's caption only discusses 1-2 named
products) -- every node/edge here is traceable to a real registry record,
not invented for the narrative. Colors/shapes are copied verbatim from the
live Network Graph artifact's own CSS custom properties.

Product icons (added in this pass) reuse scripts/classify_product_icon.py's
category read of each product's own name_ru/description -- but only a
REAL keyword match, never its "keyword-generic-default" fallback tier
(see ooo-skb-piranya's «Пиранья-10», classified only by the generic
default, left as a plain unlabeled square below rather than guessing an
icon for it).

Photos and quotes are pulled directly from entities.json's images[]/
marketing_claims[]/battlefield_evidence[] -- every one already has a real
source_id in the registry. No stock photography, no paraphrase: quotes are
verbatim Russian with an inline English gloss, per this project's
STYLE_GUIDE.md quote-handling rule. Photos publish as separate files (see
the Artifact `files` parameter in the publish call), not inlined as
base64, referenced here by their eventual served path under images/.
"""

import json

NODE_COUNT = json.load(open("data/registry/relationship_graph.json", encoding="utf-8"))["node_count"]
TITLE = "Five Residents"

CASES = [
    {
        "key": "gagaring",
        "eyebrow": "Case 01 · Multi-role principal",
        "heading": "Гагаринг: one man, four companies, one ЦБСТ tie",
        "body": (
            "Барашков Александр Сергеевич founded and directs ООО «Гагаринг» "
            "and, through it, three sister labs and a training center. ЦБСТ's "
            "own channel names Гагаринг a &laquo;резидент ЦБСТ&raquo; directly "
            "[s5440]. Its «Кузнечик» comms module was named by call sign in a "
            "front-line unit's thank-you letter for 500 delivered units "
            "(30.08.2026)."
        ),
        "sources": "s5440 · ЦБСТ Telegram, 02.05.2026 · my_el_lab post 4546, 30.08.2026 — note: the three sister labs sit farther out and lighter than «Кузнечик» below, since they share only a founder with Гагаринг, not its actual product line.",
        "photo": {
            "src": "gagaring_barashkov_portrait.jpg",
            "caption": "Барашков А.С. at a «Гагаринг» training-centre field course.",
            "source": "t.me/my_el_lab/4210 · s5387",
        },
        "quote": {
            "ru": "Выражаю огромную благодарность Товарищу Александру Сергеевичу и всему коллективу лаборатории «Гагаринг» за предоставленные «Кузнечики» в количестве 500 шт. Благодарим за постоянную поддержку!",
            "en": "“Gratitude to Comrade Aleksandr Sergeevich and the whole «Gagaring» lab for the 500 «Kuznechik» units provided. Thank you for your constant support!”",
            "source": "Front-line unit thank-you letter · s5447",
        },
        "nodes": [
            {"id": "barashkov", "kind": "person", "label": "Барашков А.С.", "x": 65, "y": 45, "href": "profiles/persons/barashkov-aleksandr-sergeevich.html"},
            {"id": "gagaring", "kind": "entity", "label": "ООО «Гагаринг»", "x": 205, "y": 140, "r": 20, "type_icon": "manufacturer", "href": "profiles/ooo-gagaring.html"},
            {"id": "cbst", "kind": "cbst", "label": "АНО «ЦБСТ»", "x": 365, "y": 45, "type_icon": "ngo", "href": "profiles/ano-tsbst-centre-for-unmanned-systems-technologies.html"},
            {"id": "kuznechik", "kind": "product", "label": "«Кузнечик»\nсвязь", "x": 300, "y": 210, "r": 14, "icon": "video_link", "href": "profiles/products/kuznechik.html"},
            {"id": "eyler", "kind": "entity", "label": "НПО «Эйлер»", "x": 50, "y": 250, "r": 8, "weight": "secondary", "href": "profiles/ooo-npo-eyler.html"},
            {"id": "yangel", "kind": "entity", "label": "Лаб. Янгеля", "x": 125, "y": 280, "r": 8, "weight": "secondary", "href": "profiles/ooo-laboratoriya-yangelya.html"},
            {"id": "intel", "kind": "entity", "label": "«Интел Дрон»", "x": 330, "y": 285, "r": 8, "weight": "secondary", "type_icon": "manufacturer", "href": "profiles/ooo-intel-dron.html"},
        ],
        "edges": [
            {"s": "barashkov", "t": "gagaring", "type": "founded"},
            {"s": "gagaring", "t": "cbst", "type": "cbst_tie"},
            {"s": "gagaring", "t": "kuznechik", "type": "produces"},
            {"s": "gagaring", "t": "eyler", "type": "founded", "weight": "secondary"},
            {"s": "gagaring", "t": "yangel", "type": "founded", "weight": "secondary"},
            {"s": "gagaring", "t": "intel", "type": "founded", "weight": "secondary"},
        ],
    },
    {
        "key": "goudron",
        "eyebrow": "Case 02 · Self-reported tie",
        "heading": "ГОУДРОН: «we've worked with ЦБСТ for months»",
        "body": (
            "A small, single-founder manufacturer. Its own Telegram channel, "
            "commenting on ЦБСТ's «Яким» combat-testing detachment, wrote: "
            "&laquo;Мы работаем с ЦБСТ не первый месяц&raquo; — a first-person, "
            "self-reported confirmation of an ongoing working relationship, "
            "not a third-party claim."
        ),
        "sources": "@GoDrone Telegram, 09.12.2025",
        "photo": {
            "src": "ooo-goudron_showroom_svoih-ne-brosaem-slogan.jpg",
            "caption": "ГОУДРОН's own showroom wall: &laquo;СВОих не бросаем&raquo;.",
            "source": "s1396",
        },
        "quote": {
            "ru": "Сферы применения: Защита техники и личного состава в условиях СВО.",
            "en": "“Fields of application: protection of equipment and personnel in the conditions of the SVO [Russia's official term for its war on Ukraine].”",
            "source": "набат.рф product page · s6457",
        },
        "nodes": [
            {"id": "kozlov", "kind": "person", "label": "Козлов Д.С.", "x": 80, "y": 60, "href": "profiles/persons/kozlov-dmitriy-sergeevich.html"},
            {"id": "goudron", "kind": "entity", "label": "ООО «ГОУДРОН»", "x": 230, "y": 150, "r": 18, "type_icon": "manufacturer", "href": "profiles/ooo-goudron.html"},
            {"id": "cbst", "kind": "cbst", "label": "АНО «ЦБСТ»", "x": 380, "y": 60, "type_icon": "ngo", "href": "profiles/ano-tsbst-centre-for-unmanned-systems-technologies.html"},
            {"id": "nabat", "kind": "product", "label": "«Набат v3»", "x": 230, "y": 260, "icon": "detector", "href": "profiles/products/nabat.html"},
        ],
        "edges": [
            {"s": "kozlov", "t": "goudron", "type": "founded"},
            {"s": "goudron", "t": "cbst", "type": "cbst_tie"},
            {"s": "goudron", "t": "nabat", "type": "produces"},
        ],
    },
    {
        "key": "ovod",
        "eyebrow": "Case 03 · One brand, two sanctioned entities",
        "heading": "«Овод»: the same owner behind two sanctioned companies",
        "body": (
            "Черезов Андрей Павлович owns and directs both ООО «Воздушный "
            "трактат» and ООО «РЛВТ» — separately EU/US-sanctioned — selling "
            "the same «Овод»/«Провод» strike-drone family under both entities. "
            "ЦБСТ's own channel calls «Овод» its &laquo;флагманский "
            "резидент&raquo; (flagship resident)."
        ),
        "sources": "ЦБСТ Telegram post 2159491523:623, 15.04.2025 · theins.ru, 23.08.2026",
        "photo": {
            "src": "ovod_shipment_50-drones-narodny-front-2023.jpg",
            "caption": "First batch of 50 «Овод» kamikaze drones, packed for shipment to the SVO zone with the &laquo;Народный фронт&raquo; project.",
            "source": "s6455",
        },
        "quote": {
            "ru": "Боевая группа создана из опытных воинов - ветеранов СВО. Военные специалисты ОВОДА содействуют подразделениям МО РФ и других силовых служб в зоне СВО.",
            "en": "“The combat group was formed from experienced fighters — SVO veterans. Ovod's military specialists assist Russian MoD units and other security services in the SVO zone.”",
            "source": "Ovod's own Telegram · s6456",
        },
        "nodes": [
            {"id": "cherezov", "kind": "person", "label": "Черезов А.П.", "x": 220, "y": 45, "href": "profiles/persons/cherezov-andrey-pavlovich.html"},
            {"id": "traktat", "kind": "entity", "label": "«Воздушный трактат»", "x": 100, "y": 165, "r": 16, "type_icon": "manufacturer", "href": "profiles/ooo-vozdushnyy-traktat.html"},
            {"id": "ovod_ent", "kind": "entity", "label": "«РЛВТ»", "x": 340, "y": 165, "r": 16, "type_icon": "manufacturer", "href": "profiles/ovod.html"},
            {"id": "cbst", "kind": "cbst", "label": "АНО «ЦБСТ»", "x": 220, "y": 270, "type_icon": "ngo", "href": "profiles/ano-tsbst-centre-for-unmanned-systems-technologies.html"},
            {"id": "prod_t", "kind": "product", "label": "«Овод»", "x": 60, "y": 270, "icon": "fpv_strike", "href": "profiles/products/ovod.html"},
            {"id": "prod_o", "kind": "product", "label": "«Овод»", "x": 380, "y": 270, "icon": "fpv_strike", "href": "profiles/products/ovod.html"},
        ],
        "edges": [
            {"s": "cherezov", "t": "traktat", "type": "directs"},
            {"s": "cherezov", "t": "ovod_ent", "type": "directs"},
            {"s": "traktat", "t": "cbst", "type": "cbst_tie"},
            {"s": "traktat", "t": "prod_t", "type": "produces"},
            {"s": "ovod_ent", "t": "prod_o", "type": "produces"},
        ],
    },
    {
        "key": "piranya",
        "eyebrow": "Case 04 · Named in the EU's 20th package",
        "heading": "СКБ «Пиранья»: named directly by ЦБСТ's own channel",
        "body": (
            "Two owners (Чернышов 40%, Корчагина 60%). ЦБСТ's channel listed "
            "&laquo;СКБ «Пиранья»&raquo; by name among six ЦБСТ-circle "
            "organizations newly hit by the EU's 20th sanctions package, "
            "alongside «Технодрон» and «Архангел». It makes a cargo-capable "
            "strike-drone family plus its own fiber-optic comms line."
        ),
        "sources": "ЦБСТ Telegram post 2159491523:2095, 24.04.2026",
        "photo": {
            "src": "TGMEDIA_7300024069_20250801_piranhafpv-post384-1.jpg",
            "caption": "An FPV drone operator at a field position, &laquo;Север&raquo; grouping, Kursk border area — company-claimed кill of a US-supplied Abrams tank.",
            "source": "@piranhafpv, 01.08.2025 · s7512",
        },
        "quote": {
            "ru": "Первый американский танк Abrams в зоне СВО уничтожен FPV-дроном «Пиранья-10»",
            "en": "“The first American Abrams tank in the SVO zone was destroyed by a «Piranha-10» FPV drone.”",
            "source": "СКБ «Пиранья» own channel · s1410",
        },
        "nodes": [
            {"id": "chernyshov", "kind": "person", "label": "Чернышов П.А.\n40%", "x": 70, "y": 55, "href": "profiles/persons/chernyshov-pavel-alekseevich.html"},
            {"id": "korchagina", "kind": "person", "label": "Корчагина О.А.\n60%", "x": 70, "y": 245, "href": "profiles/persons/korchagina-olga-aleksandrovna.html"},
            {"id": "piranya", "kind": "entity", "label": "СКБ «Пиранья»", "x": 230, "y": 150, "r": 20, "type_icon": "manufacturer", "href": "profiles/ooo-skb-piranya.html"},
            {"id": "cbst", "kind": "cbst", "label": "АНО «ЦБСТ»", "x": 380, "y": 55, "type_icon": "ngo", "href": "profiles/ano-tsbst-centre-for-unmanned-systems-technologies.html"},
            {"id": "p10", "kind": "product", "label": "«Пиранья-10»", "x": 380, "y": 165, "href": "profiles/products/piranya.html"},
            {"id": "p13", "kind": "product", "label": "«Пиранья-13»", "x": 380, "y": 260, "icon": "fpv_strike", "href": "profiles/products/piranya.html"},
        ],
        "edges": [
            {"s": "chernyshov", "t": "piranya", "type": "founded"},
            {"s": "korchagina", "t": "piranya", "type": "role"},
            {"s": "piranya", "t": "cbst", "type": "cbst_tie"},
            {"s": "piranya", "t": "p10", "type": "produces"},
            {"s": "piranya", "t": "p13", "type": "produces"},
        ],
    },
    {
        "key": "tsyganov",
        "eyebrow": "Case 05 · No ЦБСТ tie found",
        "heading": "Цыганов: a direct line to federal buyers, no ЦБСТ tie",
        "body": (
            "ИП Цыганов В.Б. sells the «Булат» v.4 drone detector through its "
            "own subsidiary ООО «Покров», and has won government contracts "
            "directly from Kursk's regional MChS directorate and the "
            "FSB-linked «Лидер» rescue center. Покров is itself a registry-"
            "named dealer for a second manufacturer, АО «Тримикс»/3mx, "
            "reselling its «Булат»/«Марс» line alongside Покров's own "
            "branded EW jammers [s1386] — one downstream node serving two "
            "manufacturers at once. No ЦБСТ tie is recorded for this "
            "entity in the registry — the ecosystem's downstream reach "
            "extends past ЦБСТ's own named residents."
        ),
        "sources": "zakupki.gov.ru contract cards · see government_contracts[] · s1386",
        "photo": None,
        "quote_note": "No self-incriminating marketing copy is on file for this entity — its government-contract cards are the only sourced material.",
        "nodes": [
            {"id": "tsyganov", "kind": "person", "label": "Цыганов В.Б.", "x": 80, "y": 60, "href": "profiles/persons/tsyganov-vadim-borisovich.html"},
            {"id": "ip", "kind": "entity", "label": "ИП Цыганов", "x": 230, "y": 150, "r": 18, "type_icon": "manufacturer", "href": "profiles/ip-tsyganov-vadim-borisovich.html"},
            {"id": "pokrov", "kind": "entity", "label": "ООО «Покров»", "x": 230, "y": 270, "r": 12, "type_icon": "dealer", "href": "profiles/ooo-pokrov.html"},
            {"id": "bulat", "kind": "product", "label": "«Булат» v.4", "x": 380, "y": 90, "icon": "detector", "href": "profiles/products/bulat.html"},
            {"id": "mchs", "kind": "gov", "label": "МЧС Курской обл.", "x": 380, "y": 200, "type_icon": "govt"},
            {"id": "lider", "kind": "gov", "label": "ФГКУ «Лидер»", "x": 380, "y": 270, "type_icon": "govt"},
        ],
        "edges": [
            {"s": "tsyganov", "t": "ip", "type": "role"},
            {"s": "ip", "t": "pokrov", "type": "founded"},
            {"s": "ip", "t": "bulat", "type": "produces"},
            {"s": "mchs", "t": "ip", "type": "procures"},
            {"s": "lider", "t": "ip", "type": "procures"},
        ],
    },
]


SHAPE = {
    "person": "diamond",
    "entity": "circle",
    "cbst": "circle",
    "product": "square",
    "gov": "circle",
}

FILL = {
    "person": "var(--person-fill)",
    "product": "var(--product-fill)",
    "cbst": "var(--t-cbst-core)",
    "gov": "var(--t-network)",
}

SANCTIONED = {"goudron", "traktat", "ovod_ent", "piranya"}

EDGE_STYLE = {
    "founded": {"dash": "5,3", "color": "var(--edge)", "arrow": True},
    "directs": {"dash": "1.5,2.5", "color": "var(--edge)", "arrow": True},
    "owns": {"dash": None, "color": "var(--edge-owns)", "arrow": True},
    "produces": {"dash": None, "color": "var(--edge-produces)", "arrow": True},
    "cbst_tie": {"dash": None, "color": "var(--t-cbst-core)", "arrow": False},
    "procures": {"dash": "5,3", "color": "var(--t-network)", "arrow": True},
    "role": {"dash": None, "color": "var(--edge)", "arrow": False, "opacity": 0.55},
}

# Product icon glyphs -- drawn centered at (0,0), overlaid on the product
# square. Only three categories are used here (see module docstring on why
# «Пиранья-10» gets none): "video_link" (Кузнечик, a comms/control-link
# module, not a UAV itself), "detector" (Набат/Булат counter-UAS units,
# glyph reused near-verbatim from the live graph's own radar-sweep icon),
# "fpv_strike" (Овод family -- a genuinely new glyph, since the live
# graph's own icon set has no strike-specific glyph yet: an X-frame quad
# with a warhead nose, distinct from the live graph's plain 4-arm
# "multirotor" glyph which marks airframe shape only, not intent).
ICON_GLYPH = {
    "video_link": (
        '<path d="M-6,4 A8,8 0 0 1 6,4" fill="none"/>'
        '<path d="M-3.2,4 A4.3,4.3 0 0 1 3.2,4" fill="none"/>'
        '<circle cy="4" r="1.3" class="p-fill"/>'
    ),
    "detector": (
        '<circle r="7" fill="none"/>'
        '<path d="M0,0 L6,-6 A8,8 0 0 1 8,0 Z" class="p-fill" opacity="0.78"/>'
        '<circle cx="3" cy="-3" r="1.1" class="p-fill"/>'
    ),
    "fpv_strike": (
        '<path d="M0,-7 L-7,-9 M0,-7 L7,-9 M0,4 L-7,7 M0,4 L7,7" fill="none"/>'
        '<circle cx="-7" cy="-9" r="1.6"/><circle cx="7" cy="-9" r="1.6"/>'
        '<circle cx="-7" cy="7" r="1.6"/><circle cx="7" cy="7" r="1.6"/>'
        '<path d="M-3,-2 L3,-2 L0,7 Z" class="p-fill"/>'
    ),
}

# Entity-TYPE glyphs (added on user request), distinct from the product
# glyphs above -- these mark what kind of organization a circle node IS
# (manufacturer / dealer / government agency / NGO-GONGO), not what it
# makes. Each is driven by a real, already-recorded field, never guessed:
#   manufacturer -> node["tier"] == "manufacturer" (the same field that
#     already sets the node's fill color -- this just makes the same fact
#     legible without relying on color alone).
#   ngo          -> node["legal_form"] == "АНО" (АНО/Ассоциация/Фонд are
#     Russia's non-profit legal forms; ЦБСТ itself is one).
#   govt         -> node kind "gov" (already a distinct government_customer
#     node kind in the live graph).
#   dealer       -> a SOURCED related_entities[].relationship_type=="dealer"
#     edge naming this entity, never inferred from an empty products[]. Of
#     this exhibit's nodes only ООО «Покров» qualifies: АО «Тримикс»/3mx's
#     own registry record names Покров as its dealer for the «Булат»/«Марс»
#     detector line (s1386) -- alongside Покров's own branded EW jammers,
#     so it is a manufacturer AND a dealer, not purely one or the other.
ENTITY_ICON = {
    "manufacturer": (
        '<circle r="3.6" fill="none"/>'
        + "".join(
            f'<line x1="{3.6*_c:.2f}" y1="{3.6*_s:.2f}" x2="{6.4*_c:.2f}" y2="{6.4*_s:.2f}"/>'
            for _c, _s in (
                (1, 0), (0.5, 0.866), (-0.5, 0.866),
                (-1, 0), (-0.5, -0.866), (0.5, -0.866),
            )
        )
    ),
    "ngo": (
        '<path d="M-6,6 C-7,-2 -1,-8 7,-8 C8,1 2,7 -6,6 Z" fill="none"/>'
        '<path d="M-5,5 L6,-7" fill="none"/>'
    ),
    "govt": (
        '<line x1="-8" y1="7" x2="8" y2="7"/>'
        '<line x1="-8" y1="1" x2="8" y2="1"/>'
        '<line x1="-5" y1="1" x2="-5" y2="7"/>'
        '<line x1="0" y1="1" x2="0" y2="7"/>'
        '<line x1="5" y1="1" x2="5" y2="7"/>'
        '<path d="M-8,1 L0,-7 L8,1 Z" fill="none"/>'
    ),
    "dealer": (
        '<rect x="-8" y="-4" width="9" height="8" rx="1" fill="none"/>'
        '<path d="M0,0 L8,0 M4,-3.2 L8,0 L4,3.2" fill="none"/>'
    ),
}


def node_fill(n, case):
    if n["kind"] == "entity":
        return "var(--t-manufacturer)"
    return FILL[n["kind"]]


def node_shape_svg(n, case):
    x, y = n["x"], n["y"]
    default_r = 10 if n["kind"] == "person" else 11 if n["kind"] == "product" else 14
    r = n.get("r", default_r)
    fill = node_fill(n, case)
    sanctioned = n["id"] in SANCTIONED
    stroke = "var(--sanctioned-ring)" if sanctioned else "var(--node-stroke)"
    sw = 2.5 if sanctioned else 1
    shape = SHAPE[n["kind"]]
    secondary = n.get("weight") == "secondary"
    group_opacity = 0.6 if secondary else 1
    icon_svg = ""
    if shape == "circle":
        el = f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
        type_icon = n.get("type_icon")
        if type_icon:
            scale = r / 10
            icon_svg = (f'<g transform="translate({x},{y}) scale({scale:.2f})" class="product-icon">'
                        f'{ENTITY_ICON[type_icon]}</g>')
    elif shape == "diamond":
        pts = f"{x},{y-r} {x+r},{y} {x},{y+r} {x-r},{y}"
        el = f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
    else:  # square
        s = r * 1.7
        el = f'<rect x="{x-s/2:.1f}" y="{y-s/2:.1f}" width="{s:.1f}" height="{s:.1f}" rx="2.5" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
        icon_key = n.get("icon")
        if icon_key:
            icon_svg = (f'<g transform="translate({x},{y})" class="product-icon">'
                        f'{ICON_GLYPH[icon_key]}</g>')
    label_lines = n["label"].split("\n")
    dy0 = r + 14
    label_cls = "node-label secondary" if secondary else "node-label"
    label_svg = ""
    for i, line in enumerate(label_lines):
        label_svg += f'<text x="{x}" y="{y + dy0 + i * 12}" class="{label_cls}" text-anchor="middle">{line}</text>'
    group = f'<g opacity="{group_opacity}">{el}{icon_svg}{label_svg}</g>'
    href = n.get("href")
    if href:
        return f'<a href="{href}" class="node-link" aria-label="Open profile: {n["label"].replace(chr(10), " ")}">{group}</a>'
    return group


def edge_svg(e, nodes_by_id):
    s = nodes_by_id[e["s"]]
    t = nodes_by_id[e["t"]]
    style = EDGE_STYLE[e["type"]]
    secondary = e.get("weight") == "secondary"
    dash = ' stroke-dasharray="3,3"' if secondary else (f' stroke-dasharray="{style["dash"]}"' if style["dash"] else "")
    opacity = 0.45 if secondary else style.get("opacity", 1)
    width = 1 if secondary else 1.6
    color = "var(--edge)" if secondary else style["color"]
    marker = ' marker-end="url(#arrow)"' if (style["arrow"] and not secondary) else ""
    return (f'<line x1="{s["x"]}" y1="{s["y"]}" x2="{t["x"]}" y2="{t["y"]}" '
            f'stroke="{color}" stroke-width="{width}" opacity="{opacity}"{dash}{marker}/>')


def render_panel(case):
    nodes_by_id = {n["id"]: n for n in case["nodes"]}
    edges_svg = "\n      ".join(edge_svg(e, nodes_by_id) for e in case["edges"])
    nodes_svg = "\n      ".join(node_shape_svg(n, case) for n in case["nodes"])
    return f'''
    <svg viewBox="0 0 440 300" class="case-svg" role="img" aria-label="{case['heading']}">
      <defs>
        <marker id="arrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M0,0 L8,4 L0,8 z" fill="var(--edge)"/>
        </marker>
      </defs>
      {edges_svg}
      {nodes_svg}
    </svg>'''


def render_photo(photo):
    if not photo:
        return ""
    return f'''
        <figure class="case-photo">
          <img src="images/{photo['src']}" alt="{photo['caption']}" loading="lazy">
          <figcaption>{photo['caption']} (cropped to frame) <span class="cite">{photo['source']}</span></figcaption>
        </figure>'''


def render_quote(case):
    q = case.get("quote")
    if q:
        return f'''
        <blockquote class="pull-quote">
          <p class="ru">&laquo;{q['ru']}&raquo;</p>
          <p class="en">{q['en']}</p>
          <cite>{q['source']}</cite>
        </blockquote>'''
    note = case.get("quote_note")
    if note:
        return f'<p class="quote-absent">{note}</p>'
    return ""


def render_case(case, idx):
    svg = render_panel(case)
    reverse = " reverse" if idx % 2 == 1 else ""
    photo_html = render_photo(case.get("photo"))
    quote_html = render_quote(case)
    return f'''
    <section class="case{reverse}">
      <div class="case-diagram">{svg}{photo_html}</div>
      <div class="case-copy">
        <p class="eyebrow">{case['eyebrow']}</p>
        <h2>{case['heading']}</h2>
        <p class="body">{case['body']}</p>
        {quote_html}
        <p class="sources">{case['sources']}</p>
      </div>
    </section>'''


CASES_HTML = "\n".join(render_case(c, i) for i, c in enumerate(CASES))

ICON_LEGEND_LABELS = {
    "manufacturer": "Manufacturer (tier)",
    "ngo": "NGO / GONGO (АНО, Ассоциация, Фонд)",
    "govt": "Government agency",
    "dealer": "Dealer (sourced relationship_type)",
}
ICON_LEGEND_HTML = "\n".join(
    f'<span class="item"><svg width="18" height="18" viewBox="-10 -10 20 20" class="icon-legend-swatch">'
    f'<circle r="9" fill="var(--ink-2)"/>'
    f'<g class="product-icon">{ENTITY_ICON[key]}</g></svg> {label}</span>'
    for key, label in ICON_LEGEND_LABELS.items()
)

HTML = f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head><body>
<title>{TITLE}</title>
<meta name="description" content="Five hand-verified sub-networks from the РОЙ.МАРКЕТ registry, each showing one manufacturer's real ownership, product, and ЦБСТ ties, with photos and verbatim quotes.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Oswald:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root {{
  color-scheme: light;
  --bg: #f9f9f7;
  --panel: #ffffff;
  --ink: #17160f;
  --ink-2: #52514e;
  --ink-muted: #898781;
  --hairline: #e1e0d9;
  --accent: #4c5f2f;
  --node-stroke: rgba(11,11,11,0.15);
  --quote-bg: #fbf3ec;
  --quote-rule: #c9784a;

  --t-manufacturer: #2a78d6;
  --t-cbst-core: #eb6834;
  --t-network: #008300;
  --person-fill: #7a8a99;
  --product-fill: #8a7a5c;
  --product-icon-ink: #f7f4ea;
  --sanctioned-ring: #d03b3b;
  --edge: #b9b8b1;
  --edge-owns: #52514e;
  --edge-produces: #8a7a5c;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    color-scheme: dark;
    --bg: #14140f;
    --panel: #1d1c17;
    --ink: #f2f1ea;
    --ink-2: #c3c2b7;
    --ink-muted: #93917f;
    --hairline: #35342b;
    --accent: #8fae6b;
    --node-stroke: rgba(255,255,255,0.18);
    --quote-bg: #241d16;
    --quote-rule: #e2966a;

    --t-manufacturer: #3987e5;
    --t-cbst-core: #e2966a;
    --t-network: #3fae3f;
    --person-fill: #8fa3b3;
    --product-fill: #b3a480;
    --product-icon-ink: #211c11;
    --sanctioned-ring: #e66767;
    --edge: #3a3a37;
    --edge-owns: #c3c2b7;
    --edge-produces: #b3a480;
  }}
}}
:root[data-theme="dark"] {{
  color-scheme: dark;
  --bg: #14140f;
  --panel: #1d1c17;
  --ink: #f2f1ea;
  --ink-2: #c3c2b7;
  --ink-muted: #93917f;
  --hairline: #35342b;
  --accent: #8fae6b;
  --node-stroke: rgba(255,255,255,0.18);
  --quote-bg: #241d16;
  --quote-rule: #e2966a;

  --t-manufacturer: #3987e5;
  --t-cbst-core: #e2966a;
  --t-network: #3fae3f;
  --person-fill: #8fa3b3;
  --product-fill: #b3a480;
  --product-icon-ink: #211c11;
  --sanctioned-ring: #e66767;
  --edge: #3a3a37;
  --edge-owns: #c3c2b7;
  --edge-produces: #b3a480;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: "IBM Plex Sans", system-ui, sans-serif;
  padding-block: 48px 80px;
}}
.wrap {{ max-width: 980px; margin: 0 auto; padding-inline: 20px; }}
header.hero {{ margin-bottom: 56px; }}
header.hero .kicker {{
  font-family: "IBM Plex Mono", monospace;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--accent);
  margin: 0 0 10px;
}}
header.hero h1 {{
  font-family: "Oswald", sans-serif;
  font-weight: 700;
  font-size: clamp(32px, 5vw, 48px);
  line-height: 1.08;
  margin: 0 0 16px;
  text-wrap: balance;
}}
header.hero p.lede {{
  font-size: 16px;
  line-height: 1.6;
  color: var(--ink-2);
  max-width: 62ch;
  margin: 0;
}}
.legend {{
  display: flex;
  flex-wrap: wrap;
  gap: 14px 22px;
  margin-top: 28px;
  padding: 14px 18px;
  background: var(--panel);
  border: 1px solid var(--hairline);
  border-radius: 10px;
  font-size: 12.5px;
  color: var(--ink-2);
}}
.legend .item {{ display: flex; align-items: center; gap: 7px; }}
.legend .sw {{ width: 12px; height: 12px; flex-shrink: 0; border: 1px solid var(--node-stroke); }}
.legend .sw.circle {{ border-radius: 50%; }}
.legend .sw.diamond {{ transform: rotate(45deg); border-radius: 2px; }}
.legend .sw.square {{ border-radius: 2px; }}
.legend .sw.ring {{ background: transparent; border: 2px solid var(--sanctioned-ring); }}
.icon-legend {{ margin-top: 10px; }}
.icon-legend-swatch {{ flex-shrink: 0; vertical-align: middle; }}

section.case {{
  display: grid;
  grid-template-columns: 440px 1fr;
  gap: 32px;
  align-items: start;
  padding: 36px 0;
  border-top: 1px solid var(--hairline);
}}
section.case.reverse {{ grid-template-columns: 1fr 440px; }}
section.case.reverse .case-diagram {{ order: 2; }}
section.case.reverse .case-copy {{ order: 1; }}
@media (max-width: 760px) {{
  section.case, section.case.reverse {{ grid-template-columns: 1fr; }}
  section.case.reverse .case-diagram, section.case.reverse .case-copy {{ order: initial; }}
}}
.case-diagram {{
  background: var(--panel);
  border: 1px solid var(--hairline);
  border-radius: 12px;
  padding: 10px;
}}
.case-svg {{ width: 100%; height: auto; display: block; }}
.node-label {{
  font-family: "IBM Plex Sans", sans-serif;
  font-size: 11.5px;
  fill: var(--ink-2);
  font-weight: 500;
}}
.node-label.secondary {{ font-size: 10px; fill: var(--ink-muted); font-weight: 400; }}
.node-link {{ cursor: pointer; }}
.node-link:hover .node-label {{ fill: var(--accent); text-decoration: underline; }}
.node-link:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px; }}
.product-icon {{ fill: none; stroke: var(--product-icon-ink); stroke-width: 1.4px; stroke-linecap: round; stroke-linejoin: round; }}
.product-icon .p-fill {{ fill: var(--product-icon-ink); stroke: none; }}
.case-photo {{
  margin: 10px 0 0;
  border-top: 1px solid var(--hairline);
  padding-top: 10px;
}}
.case-photo img {{
  width: 100%;
  display: block;
  border-radius: 8px;
  aspect-ratio: 4 / 3;
  object-fit: cover;
}}
.case-photo figcaption {{
  font-size: 11.5px;
  line-height: 1.5;
  color: var(--ink-muted);
  margin-top: 6px;
}}
.case-photo figcaption .cite {{
  font-family: "IBM Plex Mono", monospace;
  display: block;
  margin-top: 2px;
}}
.case-copy .eyebrow {{
  font-family: "IBM Plex Mono", monospace;
  font-size: 11.5px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--accent);
  margin: 0 0 8px;
}}
.case-copy h2 {{
  font-family: "Oswald", sans-serif;
  font-weight: 600;
  font-size: 23px;
  line-height: 1.25;
  margin: 0 0 12px;
  text-wrap: balance;
}}
.case-copy .body {{
  font-size: 14.5px;
  line-height: 1.65;
  color: var(--ink-2);
  margin: 0 0 16px;
}}
blockquote.pull-quote {{
  margin: 0 0 16px;
  padding: 12px 16px;
  background: var(--quote-bg);
  border-left: 3px solid var(--quote-rule);
  border-radius: 0 8px 8px 0;
}}
blockquote.pull-quote .ru {{
  font-size: 15px;
  font-style: italic;
  line-height: 1.5;
  margin: 0 0 6px;
  color: var(--ink);
}}
blockquote.pull-quote .en {{
  font-size: 13px;
  line-height: 1.5;
  margin: 0 0 8px;
  color: var(--ink-2);
}}
blockquote.pull-quote cite {{
  font-family: "IBM Plex Mono", monospace;
  font-style: normal;
  font-size: 11px;
  color: var(--ink-muted);
}}
p.quote-absent {{
  font-size: 12.5px;
  font-style: italic;
  color: var(--ink-muted);
  margin: 0 0 16px;
}}
.case-copy .sources {{
  font-family: "IBM Plex Mono", monospace;
  font-size: 11px;
  color: var(--ink-muted);
  margin: 0;
}}
footer.note {{
  margin-top: 56px;
  padding-top: 20px;
  border-top: 1px solid var(--hairline);
  font-size: 12.5px;
  color: var(--ink-muted);
  line-height: 1.6;
}}
</style>

<div class="wrap">
  <header class="hero">
    <p class="kicker">РОЙ.МАРКЕТ / ЦБСТ &middot; case study excerpts</p>
    <h1>Five residents, five kinds of proof</h1>
    <p class="lede">Every claim below traces to a primary source already cited in the registry — ЦБСТ's own channel, a manufacturer's own Telegram post, a front-line unit's thank-you letter, or a government contract card. Photos are the subjects' own public posts; quotes are verbatim with an English gloss. These are fixed excerpts of a much larger, queryable network; the full interactive graph is linked at the bottom.</p>
    <div class="legend">
      <span class="item"><span class="sw circle" style="background:var(--t-manufacturer)"></span> Manufacturer</span>
      <span class="item"><span class="sw circle" style="background:var(--t-cbst-core)"></span> АНО «ЦБСТ»</span>
      <span class="item"><span class="sw diamond" style="background:var(--person-fill)"></span> Person</span>
      <span class="item"><span class="sw square" style="background:var(--product-fill)"></span> Product</span>
      <span class="item"><span class="sw circle" style="background:var(--t-network)"></span> Govt. customer</span>
      <span class="item"><span class="sw ring"></span> Sanctioned</span>
    </div>
    <div class="legend icon-legend">{ICON_LEGEND_HTML}</div>
  </header>

  {CASES_HTML}

  <footer class="note">
    Positions are laid out for legibility, not computed — they carry no evidentiary meaning, same convention as the live graph. Every node and edge shown here is drawn from <code>data/registry/relationship_graph.json</code>; product icons reflect a real keyword classification from <code>scripts/classify_product_icon.py</code>, never a guess (see the generator's own note on which products were left unlabeled). Every person, company, and product name is a link to its full sourced profile page. Fainter, dashed ties mark a relationship that shares only a founder, not a product line or ЦБСТ tie -- weight in these diagrams tracks how central a tie is to the case, not just whether one exists. Photos and quotes are the subjects' own public material, not stock imagery. For the full {NODE_COUNT:,}-node registry — search, filters, every citation — see the live <a href="https://claude.ai/artifact/2m4hhbSUG9XqNRvU5K1Ha9">РОЙ.МАРКЕТ Network Graph</a>.
  </footer>
</div>
</body></html>'''

if __name__ == "__main__":
    open("exhibits/case_study_excerpts.html", "w", encoding="utf-8").write(HTML)
    print("wrote exhibits/case_study_excerpts.html", len(HTML), "chars")
