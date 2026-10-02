#!/usr/bin/env python3
"""Build the person x entity affiliation exhibit (people with >=2 sourced
entity ties in relationship_graph.json), answering "how many individuals
sit across how many organizations, and who are they" as a single glance --
not answerable from any single person profile page or from the full force
graph. See notes/rebuild_plan.md's 2026-09-15 dataviz-research entry for
the rationale (bipartite/affiliation-network technique, small-multiples
over a dense bipartite plot).

Local file processing over data/registry/*.json -- no network calls, safe
to run directly/repeatedly. Re-run after any relationship_graph.json
rebuild. Output: exhibits/affiliation_matrix.html (a curated static
exhibit, same publishing path as cbst_chain.html -- not part of the
docs/profiles/ generated-page family).
"""
import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROLE_EDGE_TYPES = {"role", "directs", "founded", "owns"}


def load():
    graph = json.load(open(os.path.join(ROOT, "data/registry/relationship_graph.json")))
    entities = {e["slug"]: e for e in json.load(open(os.path.join(ROOT, "data/registry/entities.json")))}
    people = {p["slug"]: p for p in json.load(open(os.path.join(ROOT, "data/registry/people.json")))}
    return graph, entities, people


def classify(recs):
    types = {r[0] for r in recs}
    has_dir = "directs" in types or any("директор" in (r[1] or "").lower() or "director" in (r[1] or "").lower() for r in recs)
    has_founder = "founded" in types or "owns" in types or any(
        "учредит" in (r[1] or "").lower() or "founder" in (r[1] or "").lower() for r in recs
    )
    if has_dir and has_founder:
        kind = "director+founder"
    elif has_dir:
        kind = "director"
    elif has_founder:
        kind = "founder"
    else:
        kind = "other"
    best = None
    for typ, label, src in recs:
        if label and src and (best is None or len(label) > len(best[0])):
            best = (label, src)
    src_ids = sorted({r[2] for r in recs if r[2]})
    return kind, (best[0] if best else None), src_ids


def build_rows(graph, entities, people):
    node_by_id = {n["id"]: n for n in graph["nodes"]}
    pairs = {}
    for e in graph["edges"]:
        if e.get("type") not in ROLE_EDGE_TYPES:
            continue
        a, b = e.get("source"), e.get("target")
        na, nb = node_by_id.get(a), node_by_id.get(b)
        if not na or not nb:
            continue
        if na.get("kind") == "person" and nb.get("kind") == "entity":
            p_id, e_id = a, b
        elif nb.get("kind") == "person" and na.get("kind") == "entity":
            p_id, e_id = b, a
        else:
            continue
        pairs.setdefault((p_id, e_id), []).append((e.get("type"), e.get("label"), e.get("source_id")))

    person_entities = {}
    for (p, e) in pairs:
        person_entities.setdefault(p, set()).add(e)
    multi = {p: es for p, es in person_entities.items() if len(es) >= 2}

    profiled = set()
    profdir = os.path.join(ROOT, "docs/profiles")
    if os.path.isdir(profdir):
        profiled = {f[:-5] for f in os.listdir(profdir) if f.endswith(".html")}

    rows = []
    for p, eset in multi.items():
        pdata = people.get(p, {})
        cells = []
        for e in eset:
            edata = entities.get(e, {})
            kind, label, srcs = classify(pairs[(p, e)])
            cells.append({
                "entity_slug": e,
                "entity_name": edata.get("name_latin") or edata.get("name_ru") or node_by_id[e].get("label"),
                "tier": edata.get("tier"),
                "role_kind": kind,
                "role_label": label,
                "sources": srcs,
                "has_profile": e in profiled,
            })
        cells.sort(key=lambda c: (0 if c["tier"] == "cbst-core" else 1, c["entity_name"] or ""))
        rows.append({
            "person_slug": p,
            "fio_ru": pdata.get("fio_ru") or node_by_id[p].get("label"),
            "sanctioned": bool(pdata.get("sanctions")),
            "has_profile": p in profiled,
            "entity_count": len(eset),
            "cells": cells,
        })
    rows.sort(key=lambda r: -r["entity_count"])
    return rows


ROLE_CLASS = {
    "director+founder": "rk-both",
    "director": "rk-dir",
    "founder": "rk-fnd",
    "other": "rk-oth",
}
ROLE_TEXT = {
    "director+founder": "director + founder",
    "director": "director",
    "founder": "founder",
    "other": "role",
}


def render_chip(cell):
    e = html.escape(cell["entity_name"] or cell["entity_slug"])
    rk = cell["role_kind"]
    cls = ROLE_CLASS.get(rk, "rk-oth")
    txt = ROLE_TEXT.get(rk, "role")
    src_note = f' [{"".join(cell["sources"][:1])}]' if cell["sources"] else ""
    tier_mark = ' <span class="tier-dot" title="ЦБСТ-core entity"></span>' if cell.get("tier") == "cbst-core" else ""
    return (
        f'<span class="chip {cls}" title="{html.escape(cell["role_label"] or txt)}">'
        f'{e}{tier_mark}<span class="rk">{txt}</span>'
        f'</span>'
    )


def render_row(r, idx):
    name = html.escape(r["fio_ru"])
    chips = "\n            ".join(render_chip(c) for c in r["cells"])
    sanctioned_tag = '<span class="tag t-low">sanctioned</span>' if r["sanctioned"] else ""
    return f"""
      <div class="pmrow">
        <div class="pmrow-head">
          <span class="pmrow-rank">{idx:02d}</span>
          <div class="pmrow-name">
            <strong>{name}</strong>
            {sanctioned_tag}
          </div>
          <span class="pmrow-count">{r["entity_count"]} entities</span>
        </div>
        <div class="pmrow-chips">
            {chips}
        </div>
      </div>"""


def render(rows):
    total_people = len(rows)
    total_entity_touches = sum(r["entity_count"] for r in rows)
    body_rows = "\n".join(render_row(r, i + 1) for i, r in enumerate(rows))

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Multi-Role Individuals — РОЙ.МАРКЕТ</title>
<style>
:root {{
  --paper: #eceef1; --panel: #f6f7f9; --panel-2: #e3e6ea;
  --ink: #12161b; --ink-2: #414a55; --ink-3: #6b7683;
  --rule: #c8ced6; --rule-soft: #dbe0e6;
  --accent: #17456b; --accent-soft: #e0e9f1;
  --ok: #0a7a53; --ok-bg: #e3f0ea;
  --mid: #96700a; --mid-bg: #faf5e8;
  --low: #8a3030; --low-bg: #f2dedd;
  --shadow: 0 1px 2px rgba(18,22,27,.06), 0 8px 24px rgba(18,22,27,.05);
  --serif: Georgia, 'Iowan Old Style', 'Times New Roman', serif;
  --sans: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
  --mono: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --paper: #0e1216; --panel: #151b21; --panel-2: #1d242c;
    --ink: #e6eaee; --ink-2: #b3bcc6; --ink-3: #838f9c;
    --rule: #2c353f; --rule-soft: #222a33;
    --accent: #7db4dd; --accent-soft: #16252f;
    --ok: #6fc9a3; --ok-bg: #12261f;
    --mid: #e0b23f; --mid-bg: #2a2314;
    --low: #ec7a95; --low-bg: #2d1918;
    --shadow: 0 1px 2px rgba(0,0,0,.4), 0 8px 24px rgba(0,0,0,.3);
  }}
}}
:root[data-theme="dark"] {{
  --paper: #0e1216; --panel: #151b21; --panel-2: #1d242c;
  --ink: #e6eaee; --ink-2: #b3bcc6; --ink-3: #838f9c;
  --rule: #2c353f; --rule-soft: #222a33;
  --accent: #7db4dd; --accent-soft: #16252f;
  --ok: #6fc9a3; --ok-bg: #12261f;
  --mid: #e0b23f; --mid-bg: #2a2314;
  --low: #ec7a95; --low-bg: #2d1918;
  --shadow: 0 1px 2px rgba(0,0,0,.4), 0 8px 24px rgba(0,0,0,.3);
}}
* {{ box-sizing: border-box; }}
body {{ background: var(--paper); color: var(--ink); font-family: var(--sans); font-size: 16px; line-height: 1.6; margin: 0; padding: 0 1.25rem 6rem; -webkit-font-smoothing: antialiased; }}
a {{ color: var(--accent); text-underline-offset: 2px; }}
.wrap {{ max-width: 62rem; margin: 0 auto; }}
.mast {{ border-bottom: 3px double var(--rule); padding: 3rem 0 1.5rem; margin-bottom: 2rem; }}
.kicker {{ font-family: var(--mono); font-size: .7rem; letter-spacing: .16em; text-transform: uppercase; color: var(--accent); margin: 0 0 1rem; }}
h1 {{ font-family: var(--serif); font-size: clamp(1.9rem, 5vw, 2.8rem); line-height: 1.1; font-weight: 400; letter-spacing: -.015em; text-wrap: balance; margin: 0 0 .5rem; }}
.standfirst {{ font-family: var(--serif); font-size: 1.08rem; line-height: 1.55; color: var(--ink-2); max-width: 44rem; margin: 0 0 1.25rem; }}
.stat-row {{ display: flex; flex-wrap: wrap; gap: .5rem 1.5rem; font-family: var(--mono); font-size: .78rem; color: var(--ink-3); }}
.stat-row strong {{ color: var(--accent); font-size: 1rem; }}

.legend {{ display: flex; flex-wrap: wrap; gap: .5rem 1.25rem; margin: 1.5rem 0 0; font-size: .8rem; color: var(--ink-2); }}
.legend > span {{ display: flex; align-items: center; gap: .4rem; }}
.legend .dot {{ width: .7rem; height: .7rem; border-radius: 50%; display: inline-block; }}

.tag {{ display: inline-block; font-family: var(--mono); font-size: .6rem; letter-spacing: .08em; text-transform: uppercase; padding: .16em .5em; border-radius: 2px; white-space: nowrap; font-weight: 600; }}
.t-low {{ background: var(--low-bg); color: var(--low); }}

.pmlist {{ display: flex; flex-direction: column; gap: 1px; background: var(--rule-soft); border: 1px solid var(--rule-soft); border-radius: 4px; overflow: hidden; margin: 1.5rem 0 3rem; }}
.pmrow {{ background: var(--panel); padding: 1rem 1.2rem; }}
.pmrow-head {{ display: flex; align-items: baseline; gap: .8rem; margin-bottom: .7rem; flex-wrap: wrap; }}
.pmrow-rank {{ font-family: var(--mono); font-size: .72rem; color: var(--ink-3); flex-shrink: 0; }}
.pmrow-name {{ font-size: 1rem; display: flex; align-items: baseline; gap: .6rem; flex: 1; }}
.pmrow-count {{ font-family: var(--mono); font-size: .72rem; color: var(--accent); white-space: nowrap; }}
.pmrow-chips {{ display: flex; flex-wrap: wrap; gap: .4rem; padding-left: 2.3rem; }}

.chip {{ display: inline-flex; align-items: center; gap: .4rem; font-size: .78rem; padding: .35em .7em; border-radius: 3px; border: 1px solid var(--rule-soft); background: var(--panel-2); color: var(--ink-2); }}
.chip .rk {{ font-family: var(--mono); font-size: .62rem; letter-spacing: .04em; text-transform: uppercase; padding: .1em .4em; border-radius: 2px; }}
.chip.rk-both {{ border-color: var(--accent); }}
.chip.rk-both .rk {{ background: var(--accent-soft); color: var(--accent); }}
.chip.rk-dir .rk {{ background: var(--ok-bg); color: var(--ok); }}
.chip.rk-fnd .rk {{ background: var(--mid-bg); color: var(--mid); }}
.chip.rk-oth .rk {{ background: var(--panel); color: var(--ink-3); }}
.tier-dot {{ width: .4rem; height: .4rem; border-radius: 50%; background: var(--accent); display: inline-block; }}

.footnote {{ font-size: .84rem; color: var(--ink-3); border-top: 1px solid var(--rule-soft); padding-top: 1.25rem; margin-top: 2rem; max-width: 44rem; }}

@media (max-width: 34rem) {{
  .pmrow-chips {{ padding-left: 0; }}
}}
</style>
</head>
<body>
<div class="wrap">
  <div class="mast">
    <p class="kicker">Multi-role individuals · РОЙ.МАРКЕТ investigation</p>
    <h1>Not one hat each — an interconnected industry, by the numbers</h1>
    <p class="standfirst">Every person below holds a director, founder, or ownership role at two or more entities already in this registry — the same pattern documented in depth on Барашков Александр Сергеевич's own profile, here shown across the whole network at once. This is a floor, not a ceiling: only entities and roles already sourced in <code>data/registry/</code> are counted, and a person can hold further roles this investigation hasn't traced yet.</p>
    <div class="stat-row">
      <span><strong>{total_people}</strong> people hold roles at ≥2 entities</span>
      <span><strong>{total_entity_touches}</strong> total person→entity ties among them</span>
    </div>
    <div class="legend">
      <span><span class="dot" style="background:var(--accent)"></span>Director + founder (same entity)</span>
      <span><span class="dot" style="background:var(--ok)"></span>Director</span>
      <span><span class="dot" style="background:var(--mid)"></span>Founder / owner</span>
      <span><span class="tier-dot"></span>ЦБСТ-core entity</span>
    </div>
  </div>

  <div class="pmlist">
{body_rows}
  </div>

  <div class="footnote">
    <p><strong>Reading this list.</strong> Rank is by number of distinct entities touched, not by seniority or evidentiary weight — a person with three minor roles ranks above one with two central ones. Each chip names one entity and the strongest sourced role found for that pair; hovering a chip in a full render shows the exact role text and citation. Sanctioned individuals are flagged inline. This exhibit answers "how common is the multi-hat pattern across the network" — for any individual's full role history, sources, and their own ego-network diagram, see that person's own profile page.</p>
    <p>Generated from <code>data/registry/relationship_graph.json</code> by <code>scripts/build_affiliation_matrix.py</code>. Not hand-edited — re-run after any relationship_graph.json rebuild.</p>
  </div>
</div>
</body>
</html>
"""


def main():
    graph, entities, people = load()
    rows = build_rows(graph, entities, people)
    out_path = os.path.join(ROOT, "exhibits/affiliation_matrix.html")
    with open(out_path, "w") as f:
        f.write(render(rows))
    print(f"wrote {out_path} — {len(rows)} people with >=2 entity ties")


if __name__ == "__main__":
    main()
