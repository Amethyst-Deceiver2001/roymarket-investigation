#!/usr/bin/env python3
"""Generates scratch_design/case_study_excerpts.html.

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
not invented for the narrative. Colors/shapes below are copied verbatim
from the live Network Graph artifact's own CSS custom properties.
"""

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
        "sources": "s5440 · ЦБСТ Telegram, 02.05.2026 · my_el_lab post 4546, 30.08.2026",
        "nodes": [
            {"id": "barashkov", "kind": "person", "label": "Барашков А.С.", "x": 70, "y": 55},
            {"id": "gagaring", "kind": "entity", "label": "ООО «Гагаринг»", "x": 220, "y": 150, "r": 20},
            {"id": "cbst", "kind": "cbst", "label": "АНО «ЦБСТ»", "x": 380, "y": 55},
            {"id": "kuznechik", "kind": "product", "label": "«Кузнечик»\nсвязь", "x": 380, "y": 245},
            {"id": "eyler", "kind": "entity", "label": "НПО «Эйлер»", "x": 100, "y": 250, "r": 12},
            {"id": "yangel", "kind": "entity", "label": "Лаб. Янгеля", "x": 220, "y": 270, "r": 12},
            {"id": "intel", "kind": "entity", "label": "«Интел Дрон»", "x": 340, "y": 270, "r": 12},
        ],
        "edges": [
            {"s": "barashkov", "t": "gagaring", "type": "founded"},
            {"s": "gagaring", "t": "cbst", "type": "cbst_tie"},
            {"s": "gagaring", "t": "kuznechik", "type": "produces"},
            {"s": "gagaring", "t": "eyler", "type": "founded"},
            {"s": "gagaring", "t": "yangel", "type": "founded"},
            {"s": "gagaring", "t": "intel", "type": "founded"},
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
        "nodes": [
            {"id": "kozlov", "kind": "person", "label": "Козлов Д.С.", "x": 80, "y": 60},
            {"id": "goudron", "kind": "entity", "label": "ООО «ГОУДРОН»", "x": 230, "y": 150, "r": 18},
            {"id": "cbst", "kind": "cbst", "label": "АНО «ЦБСТ»", "x": 380, "y": 60},
            {"id": "nabat", "kind": "product", "label": "«Набат v3»", "x": 230, "y": 260},
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
        "nodes": [
            {"id": "cherezov", "kind": "person", "label": "Черезов А.П.", "x": 220, "y": 45},
            {"id": "traktat", "kind": "entity", "label": "«Воздушный трактат»", "x": 100, "y": 165, "r": 16},
            {"id": "ovod_ent", "kind": "entity", "label": "«РЛВТ»", "x": 340, "y": 165, "r": 16},
            {"id": "cbst", "kind": "cbst", "label": "АНО «ЦБСТ»", "x": 220, "y": 270},
            {"id": "prod_t", "kind": "product", "label": "«Овод»", "x": 60, "y": 270},
            {"id": "prod_o", "kind": "product", "label": "«Овод»", "x": 380, "y": 270},
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
        "nodes": [
            {"id": "chernyshov", "kind": "person", "label": "Чернышов П.А.\n40%", "x": 70, "y": 55},
            {"id": "korchagina", "kind": "person", "label": "Корчагина О.А.\n60%", "x": 70, "y": 245},
            {"id": "piranya", "kind": "entity", "label": "СКБ «Пиранья»", "x": 230, "y": 150, "r": 20},
            {"id": "cbst", "kind": "cbst", "label": "АНО «ЦБСТ»", "x": 380, "y": 55},
            {"id": "p10", "kind": "product", "label": "«Пиранья-10»", "x": 380, "y": 165},
            {"id": "p13", "kind": "product", "label": "«Пиранья-13»", "x": 380, "y": 260},
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
            "FSB-linked «Лидер» rescue center. No ЦБСТ tie is recorded for "
            "this entity in the registry — the ecosystem's downstream reach "
            "extends past ЦБСТ's own named residents."
        ),
        "sources": "zakupki.gov.ru contract cards · see government_contracts[]",
        "nodes": [
            {"id": "tsyganov", "kind": "person", "label": "Цыганов В.Б.", "x": 80, "y": 60},
            {"id": "ip", "kind": "entity", "label": "ИП Цыганов", "x": 230, "y": 150, "r": 18},
            {"id": "pokrov", "kind": "entity", "label": "ООО «Покров»", "x": 230, "y": 270, "r": 12},
            {"id": "bulat", "kind": "product", "label": "«Булат» v.4", "x": 380, "y": 90},
            {"id": "mchs", "kind": "gov", "label": "МЧС Курской обл.", "x": 380, "y": 200},
            {"id": "lider", "kind": "gov", "label": "ФГКУ «Лидер»", "x": 380, "y": 270},
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


def node_fill(n, case):
    if n["kind"] == "entity":
        return "var(--t-manufacturer)"
    return FILL[n["kind"]]


def node_shape_svg(n, case):
    x, y = n["x"], n["y"]
    r = n.get("r", 10 if n["kind"] == "person" else 8 if n["kind"] == "product" else 14)
    fill = node_fill(n, case)
    sanctioned = n["id"] in SANCTIONED
    stroke = "var(--sanctioned-ring)" if sanctioned else "var(--node-stroke)"
    sw = 2.5 if sanctioned else 1
    shape = SHAPE[n["kind"]]
    if shape == "circle":
        el = f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
    elif shape == "diamond":
        pts = f"{x},{y-r} {x+r},{y} {x},{y+r} {x-r},{y}"
        el = f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
    else:  # square
        s = r * 1.5
        el = f'<rect x="{x-s/2:.1f}" y="{y-s/2:.1f}" width="{s:.1f}" height="{s:.1f}" rx="2" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'
    label_lines = n["label"].split("\n")
    dy0 = r + 14
    label_svg = ""
    for i, line in enumerate(label_lines):
        label_svg += f'<text x="{x}" y="{y + dy0 + i * 12}" class="node-label" text-anchor="middle">{line}</text>'
    return el + label_svg


def edge_svg(e, nodes_by_id):
    s = nodes_by_id[e["s"]]
    t = nodes_by_id[e["t"]]
    style = EDGE_STYLE[e["type"]]
    dash = f' stroke-dasharray="{style["dash"]}"' if style["dash"] else ""
    opacity = style.get("opacity", 1)
    marker = ' marker-end="url(#arrow)"' if style["arrow"] else ""
    return (f'<line x1="{s["x"]}" y1="{s["y"]}" x2="{t["x"]}" y2="{t["y"]}" '
            f'stroke="{style["color"]}" stroke-width="1.6" opacity="{opacity}"{dash}{marker}/>')


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


def render_case(case, idx):
    svg = render_panel(case)
    reverse = " reverse" if idx % 2 == 1 else ""
    return f'''
    <section class="case{reverse}">
      <div class="case-diagram">{svg}</div>
      <div class="case-copy">
        <p class="eyebrow">{case['eyebrow']}</p>
        <h2>{case['heading']}</h2>
        <p class="body">{case['body']}</p>
        <p class="sources">{case['sources']}</p>
      </div>
    </section>'''


CASES_HTML = "\n".join(render_case(c, i) for i, c in enumerate(CASES))

HTML = f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head><body>
<title>{TITLE}</title>
<meta name="description" content="Five hand-verified sub-networks from the РОЙ.МАРКЕТ registry, each showing one manufacturer's real ownership, product, and ЦБСТ ties.">
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

  --t-manufacturer: #2a78d6;
  --t-cbst-core: #eb6834;
  --t-network: #008300;
  --person-fill: #7a8a99;
  --product-fill: #8a7a5c;
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

    --t-manufacturer: #3987e5;
    --t-cbst-core: #e2966a;
    --t-network: #3fae3f;
    --person-fill: #8fa3b3;
    --product-fill: #b3a480;
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

  --t-manufacturer: #3987e5;
  --t-cbst-core: #e2966a;
  --t-network: #3fae3f;
  --person-fill: #8fa3b3;
  --product-fill: #b3a480;
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

section.case {{
  display: grid;
  grid-template-columns: 440px 1fr;
  gap: 32px;
  align-items: center;
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
  margin: 0 0 12px;
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
    <p class="lede">Every claim below traces to a primary source already cited in the registry — ЦБСТ's own channel, a manufacturer's own Telegram post, a front-line unit's thank-you letter, or a government contract card. These are fixed excerpts of a much larger, queryable network; the full interactive graph is linked at the bottom.</p>
    <div class="legend">
      <span class="item"><span class="sw circle" style="background:var(--t-manufacturer)"></span> Manufacturer</span>
      <span class="item"><span class="sw circle" style="background:var(--t-cbst-core)"></span> АНО «ЦБСТ»</span>
      <span class="item"><span class="sw diamond" style="background:var(--person-fill)"></span> Person</span>
      <span class="item"><span class="sw square" style="background:var(--product-fill)"></span> Product</span>
      <span class="item"><span class="sw circle" style="background:var(--t-network)"></span> Govt. customer</span>
      <span class="item"><span class="sw ring"></span> Sanctioned</span>
    </div>
  </header>

  {CASES_HTML}

  <footer class="note">
    Positions are laid out for legibility, not computed — they carry no evidentiary meaning, same convention as the live graph. Every node and edge shown here is drawn from <code>data/registry/relationship_graph.json</code>; nothing is invented for narrative effect. For the full 1,430-node registry — search, filters, every citation — see the live <a href="https://claude.ai/artifact/2m4hhbSUG9XqNRvU5K1Ha9">РОЙ.МАРКЕТ Network Graph</a>.
  </footer>
</div>
</body></html>'''

if __name__ == "__main__":
    open("scratch_design/case_study_excerpts.html", "w", encoding="utf-8").write(HTML)
    print("wrote scratch_design/case_study_excerpts.html", len(HTML), "chars")
