import json

SVGS = json.load(open('/private/tmp/claude-501/-Users-ak-Downloads-roymarket-investigation/f2a0c6cb-5635-40da-ac73-3c3d3f9f5370/scratchpad/svgs.json'))

CASES = [
    {
        'key': 'gagaring', 'eyebrow': 'Case 01 — the flagship',
        'name_ru': 'ООО «Гагаринг»', 'name_en': 'OOO Gagaring',
        'inn': '2312321660',
        'caption': 'Products, a sourced ЦБСТ tie, three years of financials — peaking at '
                    '₽2.16bn in 2025 — marketing copy, and a military thank-you letter '
                    'naming Gagaring staff and 500 «Кузнечик» comms modules delivered to a '
                    'combat unit. The one subject that carries the argument end to end, from '
                    'a registered company to a named battlefield user. Not currently sanctioned.',
        'note': 'ownership/founding ties fan out around the hub; the 24-product catalogue is '
                'summarized below, not spoked — see the size note for why the hub itself is '
                'this large.',
    },
    {
        'key': 'goudron', 'eyebrow': 'Case 02 — the sanctioned counterpart',
        'name_ru': 'ООО «ГОУДРОН»', 'name_en': 'OOO Goudron',
        'inn': '9721203814',
        'caption': 'A smaller, already-designated file, shown for contrast rather than scale: '
                    'one founder-director, one named product line («Набат v3»), and a '
                    'sanctions record already attached. The control case for what the '
                    'evidentiary standard looks like once a designation has actually landed. '
                    'Its hub reads small here deliberately — FY2025 revenue is real but two '
                    'orders of magnitude below Гагаринг on the same scale, not a smaller graph.',
        'note': None,
    },
    {
        'key': 'cherezov', 'eyebrow': 'Case 03 — the two-entity structure',
        'name_ru': 'ООО «Воздушный трактат» + ООО «Русская лаборатория воздушного транспорта» (РЛВТ)',
        'name_en': 'Vozdushnyy Traktat + RLVT',
        'inn': '7100046925 / 7100027464',
        'caption': 'One owner — Черезов Андрей Павлович — two companies, one product brand '
                    '(«Овод»), both entities under EU/US sanctions. ЦБСТ’s self-declared '
                    '"flagship resident," structured across two legal shells that manufacture '
                    'and sell overlapping product lines under the same name.',
        'note': 'shared owner and shared customers sit above both hubs; each hub keeps its own '
                'remaining ties. The two circles are sized independently on the shared scale — '
                'Трактат’s FY2025 filing reported ₽0 revenue (a real filed figure, not a gap), '
                'while РЛВТ reported ₽1.31bn the same year, which is why one hub all but '
                'disappears next to the other despite sharing a brand.',
    },
    {
        'key': 'piranya', 'eyebrow': 'Case 04 — the growth curve',
        'name_ru': 'ООО «СКБ Пиранья»', 'name_en': 'OOO SKB Piranya',
        'inn': '7300024069',
        'caption': 'Revenue climbed ₽36.8m → ₽516.7m → ₽870.7m across '
                    '2023–2025 — an order-of-magnitude jump inside two years. Two named '
                    'founders, an eight-product «Пиранья» airframe and payload-module line, '
                    'already under sanctions.',
        'note': None,
    },
    {
        'key': 'tsyganov', 'eyebrow': 'Case 05 — the sole trader with state contracts',
        'name_ru': 'ИП Цыганов Вадим Борисович', 'name_en': 'IP Tsyganov Vadim Borisovich',
        'inn': '504405055721 (personal)',
        'caption': '₽28.2m in «Булат»/«Покров» government contracts with Russian MЧС '
                    'and civil-defense customers, contracts and attachments already archived. '
                    'A single registered tradesman, not a marketing operation — the '
                    'network’s procurement layer at its smallest, most literal scale.',
        'note': 'no financials[] exist for a sole trader of this kind, so the hub is sized by '
                'the summed value of his own dated government contracts instead — the closest '
                'real figure on record, not a substitute for revenue.',
    },
]

LEGEND_TIERS = [
    ('manufacturer', 'Manufacturer'),
    ('plumbing', 'Plumbing / intermediary'),
    ('network', 'Network / association'),
    ('none', 'Unspecified'),
]

# --- Product Icon Set: inner <svg viewBox="0 0 24 24"> markup, copied
# verbatim from scratch_design/product_icon_set.html §02 (only the
# categories that actually turn up in these five panels' top-3 picks, plus
# the unclassified fallback for robustness against a future registry
# change). var(--icon-accent) in the source mockup is swapped for this
# page's own --accent token; no path/shape geometry is altered.
CATEGORY_ICON_SVG = {
    'fpv_kamikaze_strike': '<path d="M12 3 L15 9 L9 9 Z" class="accent-fill"/><path d="M12 9 L5 5 M12 9 L19 5 M12 13 L5 19 M12 13 L19 19"/><circle cx="5" cy="5" r="2"/><circle cx="19" cy="5" r="2"/><circle cx="5" cy="19" r="2"/><circle cx="19" cy="19" r="2"/><line x1="12" y1="9" x2="12" y2="13"/>',
    'multirotor_cargo_utility': '<path d="M12 8 L5 5 M12 8 L19 5 M12 14 L5 19 M12 14 L19 19"/><circle cx="5" cy="5" r="2"/><circle cx="19" cy="5" r="2"/><circle cx="5" cy="19" r="2"/><circle cx="19" cy="19" r="2"/><rect x="9" y="8" width="6" height="6" rx="1"/>',
    'fixed_wing_vtol': '<line x1="12" y1="2" x2="12" y2="20"/><path d="M12 8 L3 13 M12 8 L21 13"/><path d="M12 16 L8 19 M12 16 L16 19"/><circle cx="12" cy="2" r="1.1" class="fill"/>',
    'helicopter_uas': '<ellipse cx="12" cy="5" rx="8" ry="1.6"/><line x1="12" y1="6.5" x2="12" y2="10"/><path d="M8 10 L16 10 L14 16 L10 16 Z"/><line x1="14" y1="13" x2="19" y2="13"/><circle cx="19" cy="13" r="1.4"/>',
    'ew_jammer_vehicle': '<rect x="4" y="13" width="16" height="6" rx="1"/><circle cx="7" cy="19" r="1.4" class="fill"/><circle cx="17" cy="19" r="1.4" class="fill"/><path class="accent" d="M12 13 L12 6 M12 6 L8 3 M12 6 L16 3 M12 6 L12 2"/>',
    'ew_jammer_stationary': '<path d="M6 15 A6 6 0 0 1 18 15 Z"/><line x1="4" y1="15" x2="20" y2="15"/><line x1="12" y1="15" x2="12" y2="20"/><line x1="8" y1="20" x2="16" y2="20"/><path class="accent" d="M12 9 L8 4 M12 9 L16 4 M12 9 L12 2"/>',
    'ew_jammer_portable': '<line x1="4" y1="14" x2="16" y2="14"/><path d="M7 14 L7 19 L10 19 L10 15"/><path class="accent" d="M16 14 L20 11 M16 14 L20 14 M16 14 L20 17"/>',
    'detector_counter_uas': '<circle cx="12" cy="12" r="8"/><path style="fill:var(--accent);stroke:none;opacity:0.85" d="M12 12 L18 6 A8 8 0 0 1 20 12 Z"/><circle cx="15" cy="9" r="1.3" class="fill"/>',
    'antenna_mast': '<line x1="12" y1="2" x2="12" y2="21"/><line x1="7" y1="8" x2="17" y2="8"/><line x1="8.5" y1="12" x2="15.5" y2="12"/><line x1="9.5" y1="16" x2="14.5" y2="16"/><circle cx="12" cy="2" r="1.3" class="fill"/>',
    'battery_power': '<rect x="6" y="7" width="12" height="14" rx="1.5"/><rect x="10" y="4" width="4" height="3" rx="0.8"/><rect x="8" y="10" width="8" height="4" class="fill"/>',
    'motor_propeller_part': '<ellipse cx="12" cy="12" rx="9" ry="2.4" transform="rotate(45 12 12)"/><ellipse cx="12" cy="12" rx="9" ry="2.4" transform="rotate(-45 12 12)"/><circle cx="12" cy="12" r="1.7" class="fill"/>',
    'electronics_compute': '<rect x="7" y="7" width="10" height="10" rx="1"/><line x1="9" y1="4" x2="9" y2="7"/><line x1="15" y1="4" x2="15" y2="7"/><line x1="9" y1="17" x2="9" y2="20"/><line x1="15" y1="17" x2="15" y2="20"/><line x1="4" y1="9" x2="7" y2="9"/><line x1="4" y1="15" x2="7" y2="15"/><line x1="17" y1="9" x2="20" y2="9"/><line x1="17" y1="15" x2="20" y2="15"/><circle cx="12" cy="12" r="1.6" class="fill"/>',
    'nav_gnss': '<rect x="10" y="4" width="4" height="4" rx="0.6"/><path d="M10 6 L6 4 L6 8 L10 6"/><path d="M14 6 L18 4 L18 8 L14 6"/><path class="accent" d="M9 10 A5 5 0 0 1 15 10"/><path class="accent" d="M7 13 A8 8 0 0 1 17 13"/><circle cx="12" cy="20" r="1.4" class="fill"/>',
    'video_control_link': '<circle cx="12" cy="19" r="1.4" class="fill"/><path d="M9.5 15.5 A3.5 3.5 0 0 1 14.5 15.5"/><path d="M6.5 12.5 A7.5 7.5 0 0 1 17.5 12.5"/><path d="M3.5 9.5 A11.5 11.5 0 0 1 20.5 9.5"/>',
    'ground_control_station': '<rect x="4" y="6" width="16" height="10" rx="1"/><line x1="9" y1="20" x2="15" y2="20"/><line x1="12" y1="16" x2="12" y2="20"/><circle cx="9" cy="11" r="1.6" class="accent"/><line x1="14" y1="9" x2="17" y2="9"/><line x1="14" y1="13" x2="17" y2="13"/>',
    'munition_warhead': '<path d="M12 2 C15 2 16 6 16 10 L16 18 C16 20 14 21 12 21 C10 21 8 20 8 18 L8 10 C8 6 9 2 12 2 Z" class="accent"/><line x1="8" y1="10" x2="16" y2="10"/><line x1="9" y1="6" x2="15" y2="6"/>',
    'repeater_relay': '<path d="M12 3 L7 20 M12 3 L17 20"/><line x1="9.3" y1="12" x2="14.7" y2="12"/><line x1="8" y1="16" x2="16" y2="16"/><path class="accent" d="M3 9 A9 9 0 0 1 6 4 M21 9 A9 9 0 0 0 18 4"/>',
    'unclassified': '<rect x="5" y="5" width="14" height="14" rx="1" stroke-dasharray="2.5 2.2"/>',
}


def fmt_rub(v):
    if v is None:
        return '—'
    if v >= 1_000_000_000:
        return f'₽{v/1_000_000_000:.2f}bn'
    if v >= 1_000_000:
        return f'₽{v/1_000_000:.1f}m'
    if v >= 1_000:
        return f'₽{v/1_000:.0f}k'
    return f'₽{v:.0f}'


def render_hub_metric(metrics):
    """One line per hub in the panel (one for a single-hub case, two for
    the Черезов dual-hub case), stating exactly what sized the circle."""
    chips = []
    for m in metrics:
        val = fmt_rub(m['value'])
        if m['type'] == 'revenue':
            basis = f"FY{m['year']} revenue {val}" if m['year'] else f"revenue {val}"
        elif m['type'] == 'contract_value':
            basis = f"summed gov't-contract value {val} (no financials[] on record)"
        else:
            basis = 'no financial data on record — hub at the scale floor'
        chips.append(f'<span class="hub-metric-chip">{m["slug"]}: {basis}</span>')
    return '<div class="hub-metric-row">' + ' '.join(chips) + '</div>'


def render_product_summary(products):
    if not products or products.get('total', 0) == 0:
        return ''
    cells = []
    for p in products['top3']:
        cat = p['category']
        icon = CATEGORY_ICON_SVG.get(cat, CATEGORY_ICON_SVG['unclassified'])
        cls = 'mini-icon-swatch unclassified' if cat == 'unclassified' else 'mini-icon-swatch'
        cells.append(
            f'<div class="mini-icon-cell">'
            f'<div class="{cls}"><svg viewBox="0 0 24 24">{icon}</svg></div>'
            f'<div class="mini-icon-label">{p["label"]}<br><span class="mini-icon-name">{p["name"]}</span></div>'
            f'</div>'
        )
    more_note = ''
    if products['more'] > 0:
        more_note = f'<span class="products-more">+{products["more"]} more product{"s" if products["more"] != 1 else ""}</span>'
    all_list = ' · '.join(products['all_names'])
    return f'''
    <div class="product-summary">
      <p class="product-summary-kicker">Product line ({products["total"]} total) — Product Icon Set categories, up to 3 representative, not one spoke each</p>
      <div class="mini-icon-row">{''.join(cells)}{more_note}</div>
      <p class="product-full-list">All {products["total"]}: {all_list}</p>
    </div>'''


def render_case(c):
    svg = SVGS[c['key']]['svg']
    stats = SVGS[c['key']]['stats']
    note = f'<p class="panel-note">{c["note"]}</p>' if c.get('note') else ''
    metric_html = render_hub_metric(SVGS[c['key']]['hub_metric'])
    products_html = render_product_summary(SVGS[c['key']].get('products'))
    return f'''
<article class="case" id="case-{c['key']}">
  <div class="case-caption">
    <p class="eyebrow">{c['eyebrow']}</p>
    <h3 class="case-name">{c['name_ru']}</h3>
    <p class="case-latin">{c['name_en']}</p>
    <div class="case-meta">
      <span class="meta-chip">ИНН {c['inn']}</span>
      <span class="meta-chip">{stats['nodes']} nodes · {stats['edges']} edges in this excerpt</span>
    </div>
    <p class="case-desc">{c['caption']}</p>
    {products_html}
  </div>
  <div class="case-diagram">
    <div class="svg-frame">
      {svg}
    </div>
    {metric_html}
    {note}
  </div>
</article>'''


cases_html = "\n".join(render_case(c) for c in CASES)

tier_legend_html = "\n".join(
    f'<div class="legend-row"><span class="legend-swatch legend-circle" style="background:var(--t-{key})"></span><span>{label}</span></div>'
    for key, label in LEGEND_TIERS
)

page = f'''<!doctype html>
<title>Five Networks, One Registry</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Oswald:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>
  :root {{
    /* page chrome — this project's established institutional voice
       (scratch_design/product_icon_set.html), reused verbatim */
    --bg: #efeee7; --panel: #ffffff; --panel-2: #f6f5ef; --line: #d4d2c4;
    --ink: #17180f; --ink-2: #4b4c3f; --muted: #7a7c68; --accent: #4c5f2f;
    --mono: 'IBM Plex Mono', ui-monospace, monospace;
    --sans: 'IBM Plex Sans', system-ui, sans-serif;
    --display: 'Oswald', 'Arial Narrow', sans-serif;

    /* graph tokens — copied verbatim from the live РОЙ.МАРКЕТ Network Graph
       artifact (0e402553), light block. Do not invent new values here. */
    --t-manufacturer: #2a78d6;
    --t-cbst-core: #eb6834;
    --t-plumbing: #1baf7a;
    --t-money-layer: #eda100;
    --t-adjacent: #e87ba4;
    --t-network: #008300;
    --t-unverified: #4a3aa7;
    --t-none: #898781;
    --person-fill: #7a8a99;
    --product-fill: #8a7a5c;
    --sanctioned-ring: #d03b3b;
    --edge: #b9b8b1;
    --edge-owns: #52514e;
    --edge-produces: #8a7a5c;
  }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{
      --bg: #0d0e0a; --panel: #15160f; --panel-2: #191a12; --line: #34362450;
      --ink: #dcdccc; --ink-2: #b3b39a; --muted: #7c7d64; --accent: #9db56e;

      --t-manufacturer: #3987e5;
      --t-cbst-core: #d95926;
      --t-plumbing: #199e70;
      --t-money-layer: #c98500;
      --t-adjacent: #d55181;
      --t-network: #008300;
      --t-unverified: #9085e9;
      --t-none: #898781;
      --person-fill: #8fa3b3;
      --product-fill: #b3a480;
      --sanctioned-ring: #e66767;
      --edge: #3a3a37;
      --edge-owns: #c3c2b7;
      --edge-produces: #b3a480;
    }}
  }}
  :root[data-theme="dark"] {{
    --bg: #0d0e0a; --panel: #15160f; --panel-2: #191a12; --line: #34362450;
    --ink: #dcdccc; --ink-2: #b3b39a; --muted: #7c7d64; --accent: #9db56e;

    --t-manufacturer: #3987e5;
    --t-cbst-core: #d95926;
    --t-plumbing: #199e70;
    --t-money-layer: #c98500;
    --t-adjacent: #d55181;
    --t-network: #008300;
    --t-unverified: #9085e9;
    --t-none: #898781;
    --person-fill: #8fa3b3;
    --product-fill: #b3a480;
    --sanctioned-ring: #e66767;
    --edge: #3a3a37;
    --edge-owns: #c3c2b7;
    --edge-produces: #b3a480;
  }}

  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--bg); color: var(--ink); font-family: var(--sans); line-height: 1.55; }}
  .wrap {{ max-width: 1180px; margin: 0 auto; padding: 52px 24px 100px; }}

  .eyebrow {{ font-family: var(--mono); font-size: 11px; letter-spacing: 0.14em; text-transform: uppercase; color: var(--muted); margin: 0 0 10px; }}

  header.hero {{ border-bottom: 1px solid var(--line); padding-bottom: 34px; margin-bottom: 46px; }}
  header.hero .kicker {{ font-family: var(--mono); font-size: 11.5px; letter-spacing: 0.14em; text-transform: uppercase; color: var(--muted); margin: 0 0 14px; }}
  h1 {{ font-family: var(--display); font-weight: 600; font-size: clamp(30px, 4.6vw, 46px);
    letter-spacing: 0.005em; text-transform: uppercase; margin: 0 0 16px; text-wrap: balance; max-width: 16ch; }}
  .lede {{ max-width: 680px; color: var(--ink-2); font-size: 15.5px; margin: 0 0 10px; }}
  .lede b {{ color: var(--ink); font-weight: 600; }}
  .lede code {{ font-family: var(--mono); font-size: 0.92em; background: var(--panel-2); padding: 1px 5px; border: 1px solid var(--line); }}

  section.legend {{
    background: var(--panel); border: 1px solid var(--line); padding: 20px 24px;
    margin-bottom: 56px; display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 22px 28px;
  }}
  section.legend h2 {{ font-family: var(--display); font-weight: 600; font-size: 12px; text-transform: uppercase;
    letter-spacing: 0.08em; color: var(--muted); margin: 0 0 10px; grid-column: 1/-1; padding-bottom: 8px; border-bottom: 1px solid var(--line); }}
  .legend-group h3 {{ font-family: var(--mono); font-size: 10.5px; letter-spacing: 0.06em; text-transform: uppercase; color: var(--muted); margin: 0 0 8px; }}
  .legend-row {{ display: flex; align-items: center; gap: 9px; font-size: 12.5px; color: var(--ink-2); padding: 3px 0; }}
  .legend-swatch {{ width: 13px; height: 13px; flex: none; display: inline-block; }}
  .legend-circle {{ border-radius: 50%; }}
  .legend-diamond {{ transform: rotate(45deg); background: var(--person-fill); }}
  .legend-square {{ background: var(--product-fill); }}
  .legend-ring {{ border-radius: 50%; border: 2.5px solid var(--sanctioned-ring); background: transparent; }}
  .legend-edge {{ width: 26px; height: 0; border-top-width: 2px; border-top-style: solid; flex: none; }}
  .legend-icon {{ width: 15px; height: 15px; flex: none; display: inline-flex; align-items: center; justify-content: center; }}
  .legend-icon svg {{ width: 15px; height: 15px; stroke: var(--ink-2); fill: none; stroke-width: 1.6; stroke-linecap: round; stroke-linejoin: round; }}
  .legend-icon svg .node-icon-accent {{ stroke: var(--accent); }}
  .legend-icon svg .node-icon-accent-fill {{ fill: var(--accent); stroke: none; }}
  .legend-hubsize {{ display: flex; align-items: center; gap: 10px; margin-top: 6px; }}
  .legend-hubsize .dot {{ border-radius: 50%; background: var(--t-manufacturer); flex: none; }}

  .case {{ display: grid; grid-template-columns: 300px 1fr; gap: 34px; padding: 40px 0; border-top: 1px solid var(--line); align-items: start; }}
  .case:first-of-type {{ border-top: none; padding-top: 0; }}
  .case-name {{ font-family: var(--display); font-weight: 600; font-size: 22px; letter-spacing: 0.005em; margin: 0 0 4px; text-wrap: balance; line-height: 1.15; }}
  .case-latin {{ font-family: var(--sans); font-style: italic; font-size: 12.5px; color: var(--muted); margin: 0 0 14px; }}
  .case-meta {{ display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 16px; }}
  .meta-chip {{ font-family: var(--mono); font-size: 10.5px; padding: 3px 8px; border: 1px solid var(--line); color: var(--ink-2); background: var(--panel-2); white-space: nowrap; }}
  .case-desc {{ font-size: 13.5px; color: var(--ink-2); max-width: 46ch; }}

  .svg-frame {{ background: var(--panel); border: 1px solid var(--line); padding: 10px; }}
  .excerpt-svg {{ width: 100%; height: auto; display: block; }}
  .panel-note {{ font-family: var(--mono); font-size: 10.5px; color: var(--muted); margin: 8px 2px 0; letter-spacing: 0.01em; }}
  .hub-metric-row {{ display: flex; flex-wrap: wrap; gap: 6px; margin: 10px 2px 0; }}
  .hub-metric-chip {{ font-family: var(--mono); font-size: 10px; color: var(--accent); background: var(--panel-2);
    border: 1px solid var(--line); padding: 3px 7px; white-space: nowrap; }}

  .node-shape {{ stroke: rgba(120,120,120,0.35); stroke-width: 1; }}
  .sanction-ring {{ fill: none; stroke: var(--sanctioned-ring); stroke-width: 2; }}
  .hub-shape {{ stroke: rgba(120,120,120,0.35); stroke-width: 1.5; }}
  .hub-ring {{ stroke-width: 2.5; }}
  .hub-label {{ font-family: var(--sans); font-weight: 600; font-size: 12.5px; fill: #fff; paint-order: stroke; stroke: rgba(0,0,0,0.35); stroke-width: 2.5px; pointer-events: none; }}
  .hub-label.small {{ font-size: 11px; }}
  .node-label {{ font-family: var(--sans); font-size: 10.5px; fill: var(--ink-2); }}
  .node-label.small {{ font-size: 9.3px; }}

  /* demand-side node icons (government_customer / military_unit), copied
     verbatim from scratch_design/demand_side_icon_set.html §02/§03 in
     place of a plain circle for those two node kinds */
  .node-icon {{ fill: none; stroke: var(--t-none); stroke-width: 1.5; stroke-linecap: round; stroke-linejoin: round; }}
  .node-icon-unit {{ stroke: var(--t-cbst-core); }}
  .node-icon-accent {{ stroke: var(--accent); }}
  .node-icon-accent-fill {{ fill: var(--accent); stroke: none; }}

  .edge {{ fill: none; }}
  .edge-owns {{ stroke: var(--edge-owns); stroke-width: 2; opacity: 0.85; }}
  .edge-produces {{ stroke: var(--edge-produces); stroke-width: 1.1; opacity: 0.8; }}
  .edge-founded {{ stroke: var(--edge); stroke-width: 1.3; stroke-dasharray: 4,3; opacity: 0.85; }}
  .edge-directs {{ stroke: var(--edge); stroke-width: 1.3; stroke-dasharray: 1,2.5; opacity: 0.85; }}
  .edge-role {{ stroke: var(--edge); stroke-width: 1.1; opacity: 0.5; }}
  .edge-procures {{ stroke: var(--edge); stroke-width: 1.2; opacity: 0.8; }}

  /* product icon summary — this project's own Product Icon Set glyphs,
     copied verbatim from scratch_design/product_icon_set.html §02, shown
     as a compact 3-icon summary instead of one spoke per product */
  .product-summary {{ margin-top: 18px; padding-top: 14px; border-top: 1px dashed var(--line); }}
  .product-summary-kicker {{ font-family: var(--mono); font-size: 10px; letter-spacing: 0.04em; text-transform: uppercase; color: var(--muted); margin: 0 0 10px; }}
  .mini-icon-row {{ display: flex; flex-wrap: wrap; align-items: center; gap: 10px; margin-bottom: 8px; }}
  .mini-icon-cell {{ display: flex; align-items: center; gap: 7px; }}
  .mini-icon-swatch {{ width: 34px; height: 34px; flex: none; background: var(--panel-2); border: 1px solid var(--line); display: flex; align-items: center; justify-content: center; }}
  .mini-icon-swatch.unclassified {{ border-style: dashed; }}
  .mini-icon-swatch svg {{ width: 20px; height: 20px; stroke: var(--ink); fill: none; stroke-width: 1.7; stroke-linecap: round; stroke-linejoin: round; }}
  .mini-icon-swatch svg .accent {{ stroke: var(--accent); }}
  .mini-icon-swatch svg .accent-fill {{ fill: var(--accent); stroke: none; }}
  .mini-icon-swatch svg .fill {{ fill: var(--ink); stroke: none; }}
  .mini-icon-label {{ font-size: 11px; color: var(--ink-2); line-height: 1.3; }}
  .mini-icon-name {{ font-size: 10px; color: var(--muted); }}
  .products-more {{ font-family: var(--mono); font-size: 11px; color: var(--muted); padding: 4px 8px; border: 1px dashed var(--line); }}
  .product-full-list {{ font-size: 10.5px; color: var(--muted); margin: 0; line-height: 1.6; }}

  footer {{ margin-top: 60px; padding-top: 20px; border-top: 1px solid var(--line); font-family: var(--mono); font-size: 11px; color: var(--muted); }}
  footer a {{ color: var(--accent); }}

  @media (max-width: 820px) {{
    .case {{ grid-template-columns: 1fr; }}
  }}
</style>

<div class="wrap">
  <header class="hero">
    <p class="kicker">РОЙ.МАРКЕТ investigation · case-study exhibits</p>
    <h1>Five networks, one registry</h1>
    <p class="lede">Five fixed excerpts from the investigation's full relationship graph
      (<code>data/registry/relationship_graph.json</code>, 1,483 nodes / 1,984 edges) —
      one per flagship case study from the coverage audit's own prioritization. Each panel
      shows exactly that entity's real one-hop neighborhood: its people, its subsidiaries,
      its customers, and (summarized, see below) its products. Nothing here is summarized
      away or invented — every node, edge and figure is a registry record.</p>
    <p class="lede">Hub circle size is <b>not</b> local graph density — a catalogue of 20
      products used to make a hub look more important than a catalogue of 2, regardless of
      which company actually mattered more. Every hub here is instead sized by the same real
      number — latest known annual revenue, or the nearest verified figure where no revenue
      exists — on <b>one shared scale across all five panels</b>, so a bigger circle always
      means a bigger real figure, never a busier local diagram.</p>
    <p class="lede">This is the fixed, read-only opening. The full interactive graph — search,
      filters, every entity's citation trail — is a separate tool for readers who want to dig
      past these five subjects on their own.</p>
  </header>

  <section class="legend">
    <h2>How to read a panel</h2>
    <div class="legend-group">
      <h3>Shape — what kind of node</h3>
      <div class="legend-row"><span class="legend-swatch legend-circle" style="background:var(--t-manufacturer)"></span><span>Organization</span></div>
      <div class="legend-row"><span class="legend-swatch legend-diamond"></span><span>Person</span></div>
      <div class="legend-row"><span class="legend-icon"><svg viewBox="0 0 24 24"><rect x="4" y="10" width="16" height="9" rx="1"/><path d="M4 10 L12 4 L20 10"/><line x1="7" y1="10" x2="7" y2="19"/><line x1="12" y1="10" x2="12" y2="19"/><line x1="17" y1="10" x2="17" y2="19"/><circle cx="12" cy="4" r="1" class="node-icon-accent-fill"/></svg></span><span>Government / institutional customer (Demand-Side Icon Set)</span></div>
      <div class="legend-row"><span class="legend-icon"><svg viewBox="0 0 24 24"><path d="M12 3 L19 6 L19 12 C19 17 15.5 20 12 21 C8.5 20 5 17 5 12 L5 6 Z"/><path class="node-icon-accent" d="M9 12 L11 14 L15 9"/></svg></span><span>Named military unit (Demand-Side Icon Set)</span></div>
      <div class="legend-row"><span class="legend-swatch legend-square"></span><span>Product / matériel (see per-panel icon summary, not spoked individually)</span></div>
      <div class="legend-row"><span class="legend-swatch legend-ring"></span><span>Sanctioned (EU / US / other)</span></div>
    </div>
    <div class="legend-group">
      <h3>Color — organization tier</h3>
      {tier_legend_html}
      <div class="legend-hubsize">
        <span class="dot" style="width:14px;height:14px"></span><span class="dot" style="width:26px;height:26px"></span><span class="dot" style="width:40px;height:40px"></span>
      </div>
      <div class="legend-row" style="margin-top:4px">Hub size ∝ √(latest revenue or nearest verified figure) — one shared scale, all 5 panels</div>
    </div>
    <div class="legend-group">
      <h3>Line — relationship type</h3>
      <div class="legend-row"><span class="legend-edge" style="border-color:var(--edge-owns)"></span><span>owns (equity)</span></div>
      <div class="legend-row"><span class="legend-edge" style="border-color:var(--edge);border-top-style:dashed"></span><span>founded</span></div>
      <div class="legend-row"><span class="legend-edge" style="border-color:var(--edge);border-top-style:dotted"></span><span>directs</span></div>
      <div class="legend-row"><span class="legend-edge" style="border-color:var(--edge-produces)"></span><span>produces</span></div>
      <div class="legend-row"><span class="legend-edge" style="border-color:var(--edge);opacity:.5"></span><span>role / affiliation</span></div>
      <div class="legend-row"><span class="legend-edge" style="border-color:var(--edge)"></span><span>procures (customer &rarr; supplier)</span></div>
    </div>
    <div class="legend-group">
      <h3>Products — icons, not spokes</h3>
      <div class="legend-row">Each panel shows up to 3 representative products from the
        registry's own Product Icon Set categories (<code>scripts/classify_product_icon.py</code>),
        plus a "+N more" count. A dashed square icon means the classifier found no matching
        category for that product. The full product name list is always printed beneath the
        icons — nothing is hidden, only de-emphasized visually.</div>
    </div>
  </section>

  {cases_html}

  <footer>
    Extracted from data/registry/relationship_graph.json (schema v3, 1,483 nodes / 1,984 edges),
    filtered to each entity's real one-hop neighborhood — no node, edge or figure shown here is
    invented. Hub sizing uses each entity's latest financials[] revenue (or, where none exists,
    the summed government_contracts[] value already on record) on one shared √-scale across all
    five panels. Product spokes are replaced with a Product Icon Set summary
    (<code>scripts/classify_product_icon.py</code>) capped at 3 representative categories plus a
    count; government/institutional-customer and military-unit nodes use the Demand-Side Icon
    Set glyphs in place of a plain circle. Captions paraphrase the coverage audit's own
    case-study write-ups (§03), 2026-09-15.
    Node/edge color and shape grammar otherwise reused verbatim from the live
    <a href="https://claude.ai/code/artifact/0e402553-a22e-4427-a3a9-c5b0251bdaa2">РОЙ.МАРКЕТ Network Graph</a>.
  </footer>
</div>
'''

open('/Users/ak/Downloads/roymarket-investigation/scratch_design/case_study_excerpts.html', 'w').write(page)
print(len(page), 'bytes written')
