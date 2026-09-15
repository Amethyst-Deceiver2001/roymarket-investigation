#!/usr/bin/env python3
"""Build the evidence-ledger exhibit: every sourced battlefield_evidence[]/
government_contracts[]/marketing_claims[] entry that carries an event_type
(see scripts/graph_contract.py's EVENT_TYPES), re-read as a dated,
individually-citable transaction between two named parties instead of a
paragraph on one entity's own page.

This generalizes the hand-built 9-row Кузнечик/Булат timeline prototype
(approved 2026-09-15) into a real, re-runnable generator: it reads whatever
entries have actually been backfilled with event_type via
corrections_entities.json, rather than a hardcoded row list. Extend the
backfill deliberately, one entity/chain at a time (same discipline as
FLAGSHIP_PRODUCTS in build_product_profile.py) -- this script does not
invent event_type for entries that don't have it.

Local file processing over data/registry/*.json -- no network calls, safe
to run directly/repeatedly. Output: scratch_design/evidence_ledger.html (a
curated exhibit, same publishing path as affiliation_matrix.html/
cbst_chain.html -- not part of the docs/profiles/ generated-page family,
since it draws rows from across many entities rather than rendering one).

Usage:
  python3 scripts/build_evidence_ledger.py
"""
import html
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANE_COLORS = [
    ("var(--lane-a)", "#17456b"),
    ("var(--lane-b)", "#96700a"),
    ("var(--lane-c)", "#0a7a53"),
    ("var(--lane-d)", "#8a3030"),
]

EVENT_LABELS = {
    "press_self_report": "press self-report",
    "field_confirmation": "field confirmation",
    "thank_you_letter": "thank-you letter",
    "commendation": "commendation",
    "delivery_confirmation": "delivery confirmation",
    "contract_award": "contract award",
    "handover_ceremony": "handover ceremony",
    "battlefield_sighting": "battlefield sighting",
    "marketing_claim": "marketing claim",
}


def load():
    entities = json.load(open(os.path.join(REPO, "data/registry/entities.json")))
    return {e["slug"]: e for e in entities}


def collect_rows(by_slug):
    rows = []
    for slug, e in by_slug.items():
        display = e.get("name_latin") or e.get("name_ru") or slug
        for b in e.get("battlefield_evidence") or []:
            if not b.get("event_type"):
                continue
            rows.append({
                "lane": slug, "lane_label": display,
                "date": b.get("as_of"), "event_type": b.get("event_type"),
                "from_label": display,
                "to_label": (b.get("actor_to") or {}).get("label"),
                "quote_ru": b.get("text_ru"), "quote_en": b.get("text_en"),
                "note": b.get("context"),
                "value": None, "source": b.get("source_id"),
            })
        for g in e.get("government_contracts") or []:
            if not g.get("event_type"):
                continue
            rows.append({
                "lane": slug, "lane_label": display,
                "date": g.get("date"), "event_type": g.get("event_type"),
                "from_label": display,
                "to_label": (g.get("actor_to") or {}).get("label"),
                "quote_ru": None, "quote_en": None,
                "note": g.get("items") or g.get("subject_ru") or g.get("note"),
                "value": g.get("value_rub") or g.get("value"),
                "source": g.get("source_id"),
            })
            dc = g.get("delivery_confirmed")
            if dc:
                rows.append({
                    "lane": slug, "lane_label": display,
                    "date": dc.get("as_of"), "event_type": dc.get("event_type"),
                    "from_label": display,
                    "to_label": (g.get("actor_to") or {}).get("label"),
                    "quote_ru": None, "quote_en": None,
                    "note": dc.get("note"),
                    "value": None, "source": dc.get("source_id"),
                })
        for m in e.get("marketing_claims") or []:
            if not m.get("event_type"):
                continue
            rows.append({
                "lane": slug, "lane_label": display,
                "date": m.get("as_of"), "event_type": m.get("event_type"),
                "from_label": display,
                "to_label": (m.get("actor_to") or {}).get("label"),
                "quote_ru": m.get("text_ru"), "quote_en": m.get("text_en"),
                "note": m.get("context"),
                "value": None, "source": m.get("source_id"),
            })
    rows.sort(key=lambda r: (r["date"] is None, r["date"] or ""))
    return rows


def lane_color_map(rows):
    lanes = []
    for r in rows:
        if r["lane"] not in lanes:
            lanes.append(r["lane"])
    return {lane: LANE_COLORS[i % len(LANE_COLORS)][1] for i, lane in enumerate(lanes)}


def esc(s):
    return html.escape(s or "")


def render_row(r, color):
    date = r["date"] or "date unknown"
    etype = EVENT_LABELS.get(r["event_type"], r["event_type"])
    quote_block = ""
    if r["quote_ru"]:
        en = f'<span class="en">{esc(r["quote_en"])}</span>' if r["quote_en"] else ""
        quote_block = f'<div class="tl-quote">«{esc(r["quote_ru"])}»{en}</div>'
    note_block = f'<p class="tl-note">{esc(r["note"])}</p>' if r.get("note") else ""
    value_block = f'<span class="tl-value">₽{r["value"]:,.0f}</span>' if r.get("value") else "<span></span>"
    to_label = esc(r["to_label"]) if r["to_label"] else "(unspecified recipient)"
    return f"""
    <div class="tl-item" style="color: {color}">
      <span class="tl-dot"></span>
      <div class="tl-date">{esc(date)} <span class="evt-tag">{esc(etype)}</span></div>
      <div class="tl-card" style="border-left-color: {color}">
        <p class="tl-flow">{esc(r["from_label"])} <span class="arrow">→</span> {to_label}</p>
        {quote_block}
        {note_block}
        <div class="tl-foot">{value_block}<span class="id">[{esc(r["source"] or "unsourced")}]</span></div>
      </div>
    </div>"""


def render(rows):
    lane_colors = lane_color_map(rows)
    legend_items = "\n      ".join(
        f'<span><span class="lane-dot" style="background:{c}"></span>{esc(next(r["lane_label"] for r in rows if r["lane"]==lane))}</span>'
        for lane, c in lane_colors.items()
    )
    body_rows = "\n".join(render_row(r, lane_colors[r["lane"]]) for r in rows)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Evidence Ledger — РОЙ.МАРКЕТ</title>
<style>
:root {{
  --paper: #eceef1; --panel: #f6f7f9; --panel-2: #e3e6ea;
  --ink: #12161b; --ink-2: #414a55; --ink-3: #6b7683;
  --rule: #c8ced6; --rule-soft: #dbe0e6;
  --accent: #17456b; --accent-soft: #e0e9f1;
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
    --shadow: 0 1px 2px rgba(0,0,0,.4), 0 8px 24px rgba(0,0,0,.3);
  }}
}}
:root[data-theme="dark"] {{
  --paper: #0e1216; --panel: #151b21; --panel-2: #1d242c;
  --ink: #e6eaee; --ink-2: #b3bcc6; --ink-3: #838f9c;
  --rule: #2c353f; --rule-soft: #222a33;
  --accent: #7db4dd; --accent-soft: #16252f;
  --shadow: 0 1px 2px rgba(0,0,0,.4), 0 8px 24px rgba(0,0,0,.3);
}}
* {{ box-sizing: border-box; }}
body {{ background: var(--paper); color: var(--ink); font-family: var(--sans); font-size: 16px; line-height: 1.6; margin: 0; padding: 0 1.25rem 6rem; -webkit-font-smoothing: antialiased; }}
a {{ color: var(--accent); text-underline-offset: 2px; }}
.wrap {{ max-width: 46rem; margin: 0 auto; }}
.mast {{ border-bottom: 3px double var(--rule); padding: 3rem 0 1.5rem; margin-bottom: 1rem; }}
.kicker {{ font-family: var(--mono); font-size: .7rem; letter-spacing: .16em; text-transform: uppercase; color: var(--accent); margin: 0 0 1rem; }}
h1 {{ font-family: var(--serif); font-size: clamp(1.9rem, 5vw, 2.6rem); line-height: 1.1; font-weight: 400; letter-spacing: -.015em; text-wrap: balance; margin: 0 0 .5rem; }}
.standfirst {{ font-family: var(--serif); font-size: 1.05rem; line-height: 1.55; color: var(--ink-2); margin: 0 0 1.25rem; }}
.legend {{ display: flex; flex-wrap: wrap; gap: .5rem 1.5rem; margin: 0 0 2.5rem; font-size: .8rem; color: var(--ink-2); }}
.legend > span {{ display: flex; align-items: center; gap: .5rem; }}
.lane-dot {{ width: .7rem; height: .7rem; border-radius: 50%; display: inline-block; flex-shrink: 0; }}
.evt-tag {{ font-family: var(--mono); font-size: .6rem; letter-spacing: .06em; text-transform: uppercase; padding: .15em .5em; border-radius: 2px; background: var(--panel-2); color: var(--ink-3); }}
.timeline {{ position: relative; padding-left: 1.9rem; }}
.timeline::before {{ content: ""; position: absolute; left: .4rem; top: .4rem; bottom: .4rem; width: 2px; background: var(--rule-soft); }}
.tl-item {{ position: relative; margin-bottom: 2.25rem; }}
.tl-item:last-child {{ margin-bottom: 0; }}
.tl-dot {{ position: absolute; left: -1.9rem; top: .35rem; width: .85rem; height: .85rem; border-radius: 50%; border: 2px solid var(--paper); box-shadow: 0 0 0 1.5px currentColor; }}
.tl-date {{ font-family: var(--mono); font-size: .72rem; color: var(--ink-3); letter-spacing: .03em; margin-bottom: .4rem; display: flex; align-items: center; gap: .6rem; flex-wrap: wrap; }}
.tl-card {{ background: var(--panel); border: 1px solid var(--rule-soft); border-left-width: 3px; border-radius: 0 4px 4px 0; padding: 1rem 1.15rem; box-shadow: var(--shadow); }}
.tl-flow {{ font-size: .92rem; font-weight: 640; margin: 0 0 .5rem; display: flex; align-items: center; gap: .5rem; flex-wrap: wrap; }}
.tl-flow .arrow {{ color: var(--ink-3); font-weight: 400; }}
.tl-quote {{ font-family: var(--mono); font-size: .78rem; line-height: 1.6; background: var(--panel-2); border-radius: 3px; padding: .7rem .85rem; margin: .6rem 0; white-space: pre-wrap; }}
.tl-quote .en {{ display: block; margin-top: .5rem; font-family: var(--sans); color: var(--ink-2); white-space: normal; }}
.tl-note {{ font-size: .84rem; color: var(--ink-2); margin: .5rem 0 0; }}
.tl-foot {{ display: flex; justify-content: space-between; align-items: center; margin-top: .7rem; padding-top: .6rem; border-top: 1px solid var(--rule-soft); font-size: .74rem; color: var(--ink-3); flex-wrap: wrap; gap: .5rem; }}
.tl-value {{ font-family: var(--mono); font-variant-numeric: tabular-nums; color: var(--ink); font-weight: 640; }}
.id {{ font-family: var(--mono); }}
.footnote {{ font-size: .84rem; color: var(--ink-3); border-top: 1px solid var(--rule-soft); padding-top: 1.25rem; margin-top: 3rem; }}
</style>
</head>
<body>
<div class="wrap">
  <div class="mast">
    <p class="kicker">Evidence ledger · РОЙ.МАРКЕТ investigation</p>
    <h1>Every claim, dated and typed</h1>
    <p class="standfirst">{len(rows)} sourced prose claims re-read as discrete, dated transactions between two named parties, generated from <code>data/registry/</code>'s own <code>event_type</code> fields — not a hand-picked exhibit. Extend by backfilling more entities' <code>battlefield_evidence[]</code>/<code>government_contracts[]</code>/<code>marketing_claims[]</code> entries with <code>event_type</code> via <code>corrections_entities.json</code>, then re-run this generator.</p>
    <div class="legend">
      {legend_items}
    </div>
  </div>
  <div class="timeline">
{body_rows}
  </div>
  <div class="footnote">
    <p>Generated from <code>data/registry/entities.json</code> by <code>scripts/build_evidence_ledger.py</code>. Not hand-edited — corrections go through <code>corrections_entities.json</code>.</p>
  </div>
</div>
</body>
</html>
"""


def main():
    by_slug = load()
    rows = collect_rows(by_slug)
    out_path = os.path.join(REPO, "scratch_design/evidence_ledger.html")
    with open(out_path, "w") as f:
        f.write(render(rows))
    print(f"wrote {out_path} — {len(rows)} typed transaction rows")


if __name__ == "__main__":
    main()
