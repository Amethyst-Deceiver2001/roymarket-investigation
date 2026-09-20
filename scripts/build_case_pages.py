#!/usr/bin/env python3
"""Generates the site's front door and case studies from notes/ and the registry.

  docs/index.html            landing page (routes: cases, graph, profiles, guided read, dossier)
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

REPO = Path(__file__).resolve().parent.parent
DOCS = REPO / "docs"
REG = REPO / "data" / "registry"

# Tier colours copied from docs/relationship-graph.html (--t-*).
TIER_COL = {"manufacturer": "#2a78d6", "cbst-core": "#eb6834", "plumbing": "#1baf7a",
            "money-layer": "#eda100", "adjacent": "#e87ba4", "network": "#008300",
            "unverified": "#4a3aa7", None: "#898781"}
PERSON_COL = "#7a8a99"

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
         "caption": "Static excerpt of the registry graph: the whole documented network is one owner, one product and one ЦБСТ tie, which rests on the company's own channel. The red outline is a sanctions flag from an aggregator match, not a primary listing.",
     }},
    {"slug": "ovod-cherezov", "status": "planned", "title": "Овод and Черезов",
     "line": "In preparation."},
    {"slug": "piranya", "status": "planned", "title": "Пиранья", "line": "In preparation."},
    {"slug": "tsyganov", "status": "planned", "title": "Цыганов and «Булат»", "line": "In preparation."},
    {"slug": "npts-basirtk", "status": "planned", "title": "НПЦ БАСиРТК",
     "line": "In preparation. Currently a paragraph in the registry dossier."},
]

CHIPS = {"doc": ("t-doc", "Primary doc"), "press": ("t-press", "Press-reported"), "open": ("t-open", "Open")}

NAV = ('<nav class="topnav" aria-label="Site">'
       '<a href="{r}index.html">Home</a><a href="{r}cases/index.html">Cases</a>'
       '<a href="{r}relationship-graph.html">Graph</a><a href="{r}profiles/index.html">Profiles</a>'
       '<a href="{r}story.html">Guided read</a><a href="{r}dossier.html">Registry dossier</a></nav>')

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
""".strip()


def esc(t):
    return html.escape(t, quote=False)


def inline(t):
    t = esc(t)
    t = re.sub(r"\{(doc|press|open)\}", lambda m: f'<span class="tag {CHIPS[m[1]][0]}">{CHIPS[m[1]][1]}</span>', t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"\[((?:s\d{4}(?:[–-]s\d{4})?(?:, ?)?)+|[^\]]*(?:s\d{4}|msg|t\.me)[^\]]*)\]",
              lambda m: f'<span class="id">[{m[1]}]</span>', t)
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


def graph_svg(cfg, g, weak=frozenset()):
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
                 "directs": 'stroke="var(--ink-3)" stroke-width="1.4"', "role": 'stroke="var(--ink-3)" stroke-width="1.2" stroke-dasharray="1 3"', "produces": 'stroke="var(--ink-3)" stroke-width="1.2"',
                 
                 "related": 'stroke="var(--ink-3)" stroke-width="1.4" stroke-dasharray="6 4"'}[t]
        svg.append(f'<line x1="{pos[a][0]:.0f}" y1="{pos[a][1]:.0f}" x2="{pos[b][0]:.0f}" y2="{pos[b][1]:.0f}" {style}/>')
    for k in want:
        n, (x, y) = ids[k], pos[k]
        col = PERSON_COL if n["kind"] == "person" else TIER_COL.get(n.get("tier"), TIER_COL[None])
        ring = ' stroke="#c0392b" stroke-width="2.5"' if n.get("sanctioned") and k not in weak else ""
        r = 14 if k == cfg["hub"] else 9
        if n["kind"] == "person":
            svg.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="{col}"{ring}/>')
        else:
            svg.append(f'<rect x="{x - r:.0f}" y="{y - r * 0.75:.0f}" width="{2 * r}" height="{1.5 * r:.0f}" rx="3" fill="{col}"{ring}/>')
        svg.append(f'<text x="{x:.0f}" y="{y + r + 13:.0f}" text-anchor="middle" font-size="11.5" fill="var(--ink)" stroke="var(--panel)" stroke-width="3.5" paint-order="stroke">{esc(cfg["nodes"][k])}</text>')
    svg.append("</svg>")
    legend = ('<div class="net-legend">'
              '<span><span class="net-swatch" style="background:#e87ba4"></span> adjacent</span>'
              '<span><span class="net-swatch" style="background:#2a78d6"></span> manufacturer</span>'
              '<span><span class="net-swatch" style="background:#1baf7a"></span> plumbing</span>'
              '<span><span class="net-swatch" style="background:#eb6834"></span> ЦБСТ core</span>'
              f'<span><span class="net-swatch" style="background:{PERSON_COL};border-radius:50%"></span> person</span>'
              '<span>thick orange = ЦБСТ resident tie · solid = ownership/directs/produces · fine dotted = role/family · dashed = related · red outline = sanctions flag in the registry (weak name-only matches are not outlined)</span></div>')
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


def build_case(case, g, sources, weak=frozenset()):
    md = (REPO / "notes" / f"case_study_{case['slug']}.md").read_text(encoding="utf-8")
    title, body = md_to_html(md)
    graph = graph_svg(case["graph"], g, weak)
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
    (DOCS / "cases" / f"{case['slug']}.html").write_text(html_out, encoding="utf-8")


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
    routes = [
        ("Start here", "Case studies", "One network at a time, each with a flat finding, a graph excerpt and graded claims.", "cases/index.html"),
        ("Explore", "Network graph", f"{stats['nodes']:,} nodes and {stats['edges']:,} sourced ties. Search, filter, click into any node.", "relationship-graph.html"),
        ("Look up", "Profiles", f"{stats['entities']} entities, {stats['people']} people and the flagship products, one page each.", "profiles/index.html"),
        ("Guided read", "From ЦБСТ to the Front", "A short guide to the supply chains, for a first read.", "story.html"),
        ("Full record", "Registry dossier", "The complete written brief the registry grew out of.", "dossier.html"),
    ]
    rc = "".join(f'<a class="route" href="{h}"><span class="lbl">{esc(l)}</span><span class="name">{esc(n)}</span><span class="note">{esc(t)}</span></a>' for l, n, t, h in routes)
    legend = ('<div class="legend"><span><span class="tag t-doc">Primary doc</span> verified in an official extract, a platform document, or a post that exists (proves it was said, not that it is true)</span>'
              '<span><span class="tag t-press">Press-reported</span> attributed to a named outlet, wording not verified</span>'
              '<span><span class="tag t-open">Open</span> unresolved: not published as fact</span></div>')
    body = (f'<section><div class="route-grid">{rc}</div></section>'
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
            if r.get("sanctions") and all(str(s.get("note") or "").upper().startswith("PLAUSIBLE") for s in r["sanctions"])}
    (DOCS / "cases").mkdir(exist_ok=True)
    for c in CASES:
        if c["status"] == "published":
            build_case(c, g, sources, weak)
    build_indexes({"nodes": g["node_count"], "edges": g["edge_count"], "entities": len(ents), "people": len(ppl), "sources": len(sources)})
    print("wrote docs/index.html, docs/cases/index.html and", sum(c["status"] == "published" for c in CASES), "case page(s)")


if __name__ == "__main__":
    main()
