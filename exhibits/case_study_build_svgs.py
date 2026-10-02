import json, math, html, sys, os

sys.path.insert(0, '/Users/ak/Downloads/roymarket-investigation/scripts')
from classify_product_icon import classify, CATEGORY_LABELS  # noqa: E402

SCRATCH = '/private/tmp/claude-501/-Users-ak-Downloads-roymarket-investigation/f2a0c6cb-5635-40da-ac73-3c3d3f9f5370/scratchpad'
REGISTRY = '/Users/ak/Downloads/roymarket-investigation/data/registry'

D = json.load(open(f'{SCRATCH}/case_study_subgraphs.json'))
ENTITIES = json.load(open(f'{REGISTRY}/entities.json'))
ENTITIES_BY_SLUG = {e['slug']: e for e in ENTITIES if isinstance(e, dict) and e.get('slug')}

EDGE_PRIORITY = ['owns', 'produces', 'founded', 'directs', 'procures', 'role', 'related']
EDGE_LABEL_RU = {
    'owns': 'владеет', 'produces': 'производит', 'founded': 'учредил(а)',
    'directs': 'руководит', 'procures': 'закупает у', 'role': 'роль', 'related': 'связь',
}

# --- revenue-based hub sizing (shared scale across all five panels) -------
# Hub circle size used to be an accident of how many neighbor spokes a
# panel happened to fan out (which made Гагаринг's 23-product catalogue
# dominate the page over ГОУДРОН's much smaller one, even though ГОУДРОН
# -- already-sanctioned -- is the more load-bearing panel for the
# argument). Replaced with a real metric: each entity's latest known
# annual revenue from financials[], mapped through ONE shared sqrt scale
# so a bigger circle always means a bigger real number. Circle *area*
# (not radius) is made proportional to the value -- radius = sqrt(value)
# -- which is the standard perceptually-correct encoding for size-by-value
# circles (linear radius overstates big values to the eye).

def latest_financial_revenue(entity):
    """Latest-year financials[] entry with a real (non-None) revenue
    figure -- 'latest known annual revenue', literally. A recorded 0 (as
    filed) is a real data point, not a gap, and is returned as such."""
    fin = entity.get('financials') or []
    fin_sorted = sorted(fin, key=lambda f: str(f.get('year', '')))
    for f in reversed(fin_sorted):
        if f.get('revenue') is not None:
            return f['revenue'], f.get('year'), f.get('source_id')
    return None, None, None


def contract_value_fallback(entity):
    """For an entity with no financials[] at all (ИП Цыганов): sum the
    dated government_contracts[] values already on record -- the same
    ₽28.2m figure already used in this panel's caption -- rather than
    inventing a revenue number. Flags itself as contract-value, not
    revenue, so it's never conflated with the other four panels' figures."""
    contracts = entity.get('government_contracts') or []
    total = 0.0
    any_value = False
    for c in contracts:
        v = c.get('value')
        if isinstance(v, (int, float)):
            total += v
            any_value = True
    if any_value:
        return total
    return None


HUB_ENTITY_SLUGS = {
    'gagaring': ['ooo-gagaring'],
    'goudron': ['ooo-goudron'],
    'piranya': ['ooo-skb-piranya'],
    'tsyganov': ['ip-tsyganov-vadim-borisovich'],
    'cherezov': ['ooo-vozdushnyy-traktat', 'ovod'],
}


def compute_hub_metric(slug):
    """Returns dict: value (rubles or None), year, type ('revenue' |
    'contract_value' | 'no_data'), source_id, note."""
    e = ENTITIES_BY_SLUG.get(slug)
    if not e:
        return {'value': None, 'year': None, 'type': 'no_data', 'source_id': None,
                'note': f'{slug} not found in entities.json'}
    rev, year, sid = latest_financial_revenue(e)
    if rev is not None:
        return {'value': rev, 'year': year, 'type': 'revenue', 'source_id': sid, 'note': None}
    cv = contract_value_fallback(e)
    if cv is not None:
        return {'value': cv, 'year': None, 'type': 'contract_value', 'source_id': None,
                'note': 'no financials[] on record; using summed government_contracts[] value instead'}
    return {'value': None, 'year': None, 'type': 'no_data', 'source_id': None,
            'note': 'no financials[] and no government_contracts[] value on record'}


# Compute metrics for every hub entity across all five panels up front, so
# the sqrt scale below is shared across the whole set (not re-derived per
# panel, which would silently re-introduce the local-scale problem this
# revision exists to fix).
HUB_METRICS = {}
for case_key, slugs in HUB_ENTITY_SLUGS.items():
    for slug in slugs:
        HUB_METRICS[slug] = compute_hub_metric(slug)

_ALL_VALUES = [m['value'] for m in HUB_METRICS.values() if m['value'] is not None]
MAX_VALUE = max(_ALL_VALUES) if _ALL_VALUES else 1.0
MIN_HUB_R, MAX_HUB_R = 14, 48


def hub_radius_for(slug):
    m = HUB_METRICS[slug]
    v = m['value']
    if v is None or v <= 0 or MAX_VALUE <= 0:
        return MIN_HUB_R
    frac = math.sqrt(v / MAX_VALUE)
    return MIN_HUB_R + (MAX_HUB_R - MIN_HUB_R) * frac


def fmt_rub(v):
    if v is None:
        return None
    if v >= 1_000_000_000:
        return f'₽{v/1_000_000_000:.2f}bn'
    if v >= 1_000_000:
        return f'₽{v/1_000_000:.1f}m'
    if v >= 1_000:
        return f'₽{v/1_000:.0f}k'
    return f'₽{v:.0f}'


# --- product classification / icon summary (replaces one-spoke-per-product) ----

def entity_products(slug):
    e = ENTITIES_BY_SLUG.get(slug)
    if not e:
        return []
    return [p for p in (e.get('products') or []) if isinstance(p, dict)]


def build_product_summary(slugs):
    """Union of products[] across one or more hub entities (cherezov's two
    hubs share the «Овод» brand). Classifies each via the project's own
    classify_product_icon.classify(), picks up to 3 DISTINCT-category
    representatives (falling back to unclassified only when there aren't
    3 classified ones to choose from), and keeps the full name list so
    nothing is dropped -- just not given one spoke each."""
    seen_names = set()
    products = []
    for slug in slugs:
        for p in entity_products(slug):
            name = p.get('name_ru') or '?'
            if name in seen_names:
                continue
            seen_names.add(name)
            products.append(p)

    classified = []
    for p in products:
        cat, tier = classify(p)
        classified.append((p, cat, tier))

    real = [c for c in classified if c[1] != 'unclassified']
    unclassified = [c for c in classified if c[1] == 'unclassified']

    chosen = []
    seen_cats = set()
    for p, cat, tier in real:
        if cat not in seen_cats:
            chosen.append((p, cat, tier))
            seen_cats.add(cat)
        if len(chosen) == 3:
            break
    if len(chosen) < 3:
        for p, cat, tier in real:
            if (p, cat, tier) in chosen:
                continue
            chosen.append((p, cat, tier))
            if len(chosen) == 3:
                break
    if len(chosen) < 3:
        for p, cat, tier in unclassified:
            chosen.append((p, cat, tier))
            if len(chosen) == 3:
                break

    top3 = [{'name': p.get('name_ru', '?'), 'category': cat, 'label': CATEGORY_LABELS[cat]}
            for p, cat, tier in chosen]
    return {
        'total': len(products),
        'top3': top3,
        'more': max(0, len(products) - len(top3)),
        'all_names': [p.get('name_ru', '?') for p in products],
    }


def esc(s):
    return html.escape(s or '', quote=True)


def node_r(n):
    if n['kind'] == 'product':
        return 7
    return 9


def dedup_edges(edges, hub_ids):
    """Group edges between the same unordered (a,b) pair; return list of
    dicts: {a, b, hub_is_source, types:[...], labels:[...], style_type}"""
    groups = {}
    order = []
    for e in edges:
        s, t = e['source'], e['target']
        if s in hub_ids and t in hub_ids:
            key = (s, t)
        elif s in hub_ids:
            key = (s, t)
        elif t in hub_ids:
            key = (t, s)
        else:
            key = (s, t)
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(e)
    out = []
    for key in order:
        grp = groups[key]
        types = sorted({e['type'] for e in grp}, key=lambda x: EDGE_PRIORITY.index(x) if x in EDGE_PRIORITY else 99)
        style_type = types[0]
        labels = sorted({e.get('label') for e in grp if e.get('label')})
        hub_a, other_b = key
        rep = next(e for e in grp if e['type'] == style_type)
        hub_is_source = (rep['source'] == hub_a)
        out.append({
            'hub': hub_a, 'other': other_b, 'types': types, 'style_type': style_type,
            'labels': labels, 'hub_is_source': hub_is_source,
        })
    return out


def label_text(n):
    lbl = n['label']
    if n['kind'] == 'product' and lbl.startswith('«') and lbl.endswith('»'):
        lbl = lbl[1:-1]
    return lbl


def truncate(s, n):
    return s if len(s) <= n else s[:n-1] + '…'


def radial_layout(hub, neighbors, cx, cy, radius, hub_r=20, start_deg=-90, span_deg=360, sort_key=None):
    pos = {hub['id']: (cx, cy, 0)}
    n = len(neighbors)
    if n == 0:
        return pos
    if sort_key:
        neighbors = sorted(neighbors, key=sort_key)
    step = span_deg / n
    for i, nb in enumerate(neighbors):
        deg = start_deg + step * (i + 0.5)
        rad = math.radians(deg)
        x = cx + radius * math.cos(rad)
        y = cy + radius * math.sin(rad)
        pos[nb['id']] = (x, y, deg)
    return pos


def kind_sort_key(n):
    order = {'person': 0, 'entity': 1, 'government_customer': 2, 'product': 3}
    return (order.get(n['kind'], 9), label_text(n))


# --- demand-side icon glyphs, copied verbatim from
# exhibits/demand_side_icon_set.html §02/§03 (pediment for
# government_customer, shield for military_unit) instead of a plain circle.
CUSTOMER_ICON_PATHS = (
    '<rect x="4" y="10" width="16" height="9" rx="1"/>'
    '<path d="M4 10 L12 4 L20 10"/>'
    '<line x1="7" y1="10" x2="7" y2="19"/>'
    '<line x1="12" y1="10" x2="12" y2="19"/>'
    '<line x1="17" y1="10" x2="17" y2="19"/>'
    '<circle cx="12" cy="4" r="1" class="node-icon-accent-fill"/>'
)
CUSTOMER_ICON_CENTER = (12, 11.5)

MILITARY_UNIT_ICON_PATHS = (
    '<path d="M12 3 L19 6 L19 12 C19 17 15.5 20 12 21 C8.5 20 5 17 5 12 L5 6 Z"/>'
    '<path class="node-icon-accent" d="M9 12 L11 14 L15 9"/>'
)
MILITARY_UNIT_ICON_CENTER = (12, 12)


def icon_group_svg(x, y, r, paths, center, cid, extra_cls=''):
    """Places a 24x24-viewBox icon (copied verbatim from the icon-set
    mockups) centered at (x, y), scaled so its bounding box is roughly
    2*r across -- same visual weight as the circle it replaces."""
    cx0, cy0 = center
    s = (2.0 * r) / 20.0  # icon content roughly 16-18 units wide in the 24 box
    transform = f'translate({x:.1f},{y:.1f}) scale({s:.3f}) translate({-cx0:.2f},{-cy0:.2f})'
    return (f'<g class="node-icon {extra_cls}" data-id="{cid}" transform="{transform}">'
            f'{paths}</g>')


def node_shape_svg(n, x, y, cid):
    r = node_r(n)
    fill = 'var(--person-fill)' if n['kind'] == 'person' else \
           'var(--product-fill)' if n['kind'] == 'product' else \
           'var(--t-none)' if n['kind'] == 'government_customer' else \
           f"var(--t-{(n.get('tier') or 'none')})"
    sanction_ring = ''
    if n.get('sanctioned'):
        rr = r + 4
        sanction_ring = f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rr}" class="sanction-ring"/>'

    if n['kind'] == 'government_customer':
        shape = icon_group_svg(x, y, r + 3, CUSTOMER_ICON_PATHS, CUSTOMER_ICON_CENTER, cid, 'node-icon-customer')
        return sanction_ring + shape
    if n['kind'] == 'military_unit':
        shape = icon_group_svg(x, y, r + 3, MILITARY_UNIT_ICON_PATHS, MILITARY_UNIT_ICON_CENTER, cid, 'node-icon-unit')
        return sanction_ring + shape

    shape = ''
    if n['kind'] == 'person':
        pts = f"{x:.1f},{y-r:.1f} {x+r:.1f},{y:.1f} {x:.1f},{y+r:.1f} {x-r:.1f},{y:.1f}"
        shape = f'<polygon points="{pts}" fill="{fill}" class="node-shape" data-id="{cid}"/>'
    elif n['kind'] == 'product':
        s = r
        shape = f'<rect x="{x-s:.1f}" y="{y-s:.1f}" width="{2*s:.1f}" height="{2*s:.1f}" fill="{fill}" class="node-shape" data-id="{cid}"/>'
    else:
        shape = f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}" class="node-shape" data-id="{cid}"/>'
    return sanction_ring + shape


def hub_shape_svg(n, x, y, r=20):
    fill = f"var(--t-{(n.get('tier') or 'none')})"
    ring = ''
    if n.get('sanctioned'):
        ring = f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r+5}" class="sanction-ring hub-ring"/>'
    return ring + f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{fill}" class="node-shape hub-shape"/>'


MARKER_FOR_TYPE = {'owns': 'arrow-owns', 'produces': 'arrow-produces'}

def edge_svg(x1, y1, r1, x2, y2, r2, style_type, arrow, prefix=''):
    ang = math.atan2(y2 - y1, x2 - x1)
    sx = x1 + math.cos(ang) * (r1 + 2)
    sy = y1 + math.sin(ang) * (r1 + 2)
    ex = x2 - math.cos(ang) * (r2 + (r2 * 0.35 if arrow else 2))
    ey = y2 - math.sin(ang) * (r2 + (r2 * 0.35 if arrow else 2))
    cls = f'edge edge-{style_type}'
    marker_id = prefix + MARKER_FOR_TYPE.get(style_type, 'arrow-generic')
    marker = f' marker-end="url(#{marker_id})"' if arrow else ''
    return f'<line x1="{sx:.1f}" y1="{sy:.1f}" x2="{ex:.1f}" y2="{ey:.1f}" class="{cls}"{marker}/>'


def marker_defs(prefix):
    def m(name, fill):
        return (f'<marker id="{prefix}{name}" viewBox="0 0 10 10" refX="8.5" refY="5" '
                f'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
                f'<path d="M0,0L10,5L0,10z" fill="{fill}"/></marker>')
    return ('<defs>' + m('arrow-owns', 'var(--edge-owns)') +
            m('arrow-produces', 'var(--edge-produces)') +
            m('arrow-generic', 'var(--edge)') + '</defs>')


def label_svg(x, y, angle_deg, text, cls='node-label', pad=10):
    rad = math.radians(angle_deg)
    lx = x + pad * math.cos(rad)
    ly = y + pad * math.sin(rad)
    flip = math.cos(rad) < -0.02
    rot = angle_deg + 180 if flip else angle_deg
    anchor = 'end' if flip else 'start'
    return f'<text x="{lx:.1f}" y="{ly:.1f}" transform="rotate({rot:.1f} {lx:.1f} {ly:.1f})" text-anchor="{anchor}" dominant-baseline="middle" class="{cls}">{esc(text)}</text>'


HAS_ARROW = {'owns', 'founded', 'directs', 'produces'}

def build_single_hub_svg(case_key, hub_id, node_prefix_label, w, h, radius, hub_r=22, label_maxlen=34, font_small=False):
    data = D[case_key]
    nodes_by_id = {n['id']: n for n in data['nodes']}
    hub = nodes_by_id[hub_id]
    # products are no longer spoked individually -- summarized as icons
    # instead (see build_product_summary) -- so they're excluded from the
    # radial neighbor layout entirely.
    neighbors = [n for n in data['nodes'] if n['id'] != hub_id and n['kind'] != 'product']
    cx, cy = w / 2, h / 2
    pos = radial_layout(hub, neighbors, cx, cy, radius, sort_key=kind_sort_key)
    dedup = dedup_edges(data['edges'], {hub_id})
    prefix = case_key + '-'

    parts = [marker_defs(prefix)]
    for eg in dedup:
        other_id = eg['other'] if eg['hub'] == hub_id else eg['hub']
        if other_id not in pos:
            continue
        hx, hy, _ = pos[hub_id]
        ox, oy, _ = pos[other_id]
        arrow = eg['style_type'] in HAS_ARROW
        if eg['hub_is_source']:
            parts.append(edge_svg(hx, hy, hub_r, ox, oy, node_r(nodes_by_id[other_id]), eg['style_type'], arrow, prefix))
        else:
            parts.append(edge_svg(ox, oy, node_r(nodes_by_id[other_id]), hx, hy, hub_r, eg['style_type'], arrow, prefix))

    for nb in neighbors:
        x, y, deg = pos[nb['id']]
        parts.append(node_shape_svg(nb, x, y, nb['id']))
        cls = 'node-label small' if font_small else 'node-label'
        parts.append(label_svg(x, y, deg, truncate(label_text(nb), label_maxlen), cls))

    hx, hy, _ = pos[hub_id]
    parts.append(hub_shape_svg(hub, hx, hy, hub_r))
    hub_short = node_prefix_label
    parts.append(f'<text x="{hx:.1f}" y="{hy:.1f}" text-anchor="middle" dominant-baseline="middle" class="hub-label">{esc(hub_short)}</text>')

    body = "\n".join(parts)
    svg = f'<svg viewBox="0 0 {w} {h}" class="excerpt-svg" role="img" aria-label="Network excerpt for {esc(hub["label"])}">\n{body}\n</svg>'
    stats = {'nodes': len(data['nodes']), 'edges': len(data['edges'])}
    return svg, stats


def build_dual_hub_svg(case_key, hub_ids, hub_short_labels, w, h, radius_a, radius_b, hub_rs=(20, 20)):
    data = D[case_key]
    nodes_by_id = {n['id']: n for n in data['nodes']}
    hub_a_id, hub_b_id = hub_ids
    hub_a, hub_b = nodes_by_id[hub_a_id], nodes_by_id[hub_b_id]

    edges = data['edges']
    touch = {}
    for e in edges:
        s, t = e['source'], e['target']
        other = None
        hid = None
        if s in hub_ids and t not in hub_ids:
            other, hid = t, s
        elif t in hub_ids and s not in hub_ids:
            other, hid = s, t
        else:
            continue
        touch.setdefault(other, set()).add(hid)

    cx_a, cy = w * 0.30, h * 0.62
    cx_b = w * 0.70
    hub_r_a, hub_r_b = hub_rs

    pos = {hub_a_id: (cx_a, cy, 0), hub_b_id: (cx_b, cy, 0)}

    # products excluded from the spoke fan (summarized as icons instead)
    a_only = [nid for nid, hids in touch.items() if hids == {hub_a_id} and nodes_by_id.get(nid, {}).get('kind') != 'product']
    b_only = [nid for nid, hids in touch.items() if hids == {hub_b_id} and nodes_by_id.get(nid, {}).get('kind') != 'product']
    both = [nid for nid, hids in touch.items() if len(hids) == 2 and nodes_by_id.get(nid, {}).get('kind') != 'product']

    a_only_nodes = sorted([nodes_by_id[i] for i in a_only], key=kind_sort_key)
    b_only_nodes = sorted([nodes_by_id[i] for i in b_only], key=kind_sort_key)

    def fan(nodes, cx, cy, radius, start_deg, span_deg):
        out = {}
        n = len(nodes)
        if n == 0:
            return out
        step = span_deg / n
        for i, nb in enumerate(nodes):
            deg = start_deg + step * (i + 0.5)
            rad = math.radians(deg)
            out[nb['id']] = (cx + radius * math.cos(rad), cy + radius * math.sin(rad), deg)
        return out

    pos.update(fan(a_only_nodes, cx_a, cy, radius_a, 100, 160))
    pos.update(fan(b_only_nodes, cx_b, cy, radius_b, -80, 160))

    shared_nodes = [nodes_by_id[i] for i in both]
    shared_cx = (cx_a + cx_b) / 2
    shared_cy = h * 0.14
    for i, nb in enumerate(shared_nodes):
        sx = shared_cx + (i - (len(shared_nodes)-1)/2) * 90
        pos[nb['id']] = (sx, shared_cy, -90)

    prefix = case_key + '-'
    dedup = dedup_edges(edges, set(hub_ids))
    parts = [marker_defs(prefix)]
    for eg in dedup:
        hub_id = eg['hub']
        other_id = eg['other']
        if hub_id not in pos or other_id not in pos:
            continue
        hx, hy, _ = pos[hub_id]
        ox, oy, _ = pos[other_id]
        arrow = eg['style_type'] in HAS_ARROW
        hub_r_use = hub_r_a if hub_id == hub_a_id else hub_r_b
        other_node = nodes_by_id[other_id]
        if eg['hub_is_source']:
            parts.append(edge_svg(hx, hy, hub_r_use, ox, oy, node_r(other_node), eg['style_type'], arrow, prefix))
        else:
            parts.append(edge_svg(ox, oy, node_r(other_node), hx, hy, hub_r_use, eg['style_type'], arrow, prefix))

    for nb in a_only_nodes + b_only_nodes + shared_nodes:
        x, y, deg = pos[nb['id']]
        parts.append(node_shape_svg(nb, x, y, nb['id']))
        parts.append(label_svg(x, y, deg, truncate(label_text(nb), 30), 'node-label small'))

    for hid, short, r in zip(hub_ids, hub_short_labels, hub_rs):
        hx, hy, _ = pos[hid]
        parts.append(hub_shape_svg(nodes_by_id[hid], hx, hy, r))
        parts.append(f'<text x="{hx:.1f}" y="{hy:.1f}" text-anchor="middle" dominant-baseline="middle" class="hub-label small">{esc(short)}</text>')

    body = "\n".join(parts)
    svg = f'<svg viewBox="0 0 {w} {h}" class="excerpt-svg" role="img" aria-label="Network excerpt for {esc(hub_a["label"])} and {esc(hub_b["label"])}">\n{body}\n</svg>'
    stats = {'nodes': len(data['nodes']), 'edges': len(data['edges'])}
    return svg, stats


def canvas_size(radius, maxlen, small=False, node_r=9, margin=36):
    charw = 5.1 if small else 6.0
    extent = radius + node_r + 12 + maxlen * charw
    side = int(2 * extent + 2 * margin)
    return side, side


results = {}

# Hub radii now come from the shared revenue/contract-value scale computed
# above (HUB_METRICS / hub_radius_for), not from local spoke count. Spoke
# counts have also dropped sharply now that products are summarized
# instead of individually fanned (e.g. gagaring: 30 spokes -> 8), so
# canvas/radius are retuned smaller across the board.

gagaring_hub_r = hub_radius_for('ooo-gagaring')
w, h = canvas_size(160, 26, small=True, margin=44)
results['gagaring'] = build_single_hub_svg('gagaring', 'ooo-gagaring', 'Гагаринг', w, h, 160,
                                            hub_r=gagaring_hub_r, label_maxlen=26, font_small=True)

goudron_hub_r = hub_radius_for('ooo-goudron')
w, h = canvas_size(95, 26, margin=40)
results['goudron'] = build_single_hub_svg('goudron', 'ooo-goudron', 'ГОУДРОН', w, h, 95,
                                           hub_r=goudron_hub_r, label_maxlen=26)

piranya_hub_r = hub_radius_for('ooo-skb-piranya')
w, h = canvas_size(120, 28, small=True, margin=42)
results['piranya'] = build_single_hub_svg('piranya', 'ooo-skb-piranya', 'СКБ Пиранья', w, h, 120,
                                           hub_r=piranya_hub_r, label_maxlen=28, font_small=True)

tsyganov_hub_r = hub_radius_for('ip-tsyganov-vadim-borisovich')
w, h = canvas_size(140, 30, small=True, margin=42)
results['tsyganov'] = build_single_hub_svg('tsyganov', 'ip-tsyganov-vadim-borisovich', 'ИП Цыганов', w, h, 140,
                                            hub_r=tsyganov_hub_r, label_maxlen=30, font_small=True)

traktat_hub_r = hub_radius_for('ooo-vozdushnyy-traktat')
ovod_hub_r = hub_radius_for('ovod')
results['cherezov'] = build_dual_hub_svg('cherezov', ['ooo-vozdushnyy-traktat', 'ovod'], ['Трактат', 'РЛВТ'],
                                          980, 560, 200, 230, hub_rs=(traktat_hub_r, ovod_hub_r))

out = {}
for k, (svg, stats) in results.items():
    out[k] = {'svg': svg, 'stats': stats}

# attach product summaries + hub metric info for build_page.py to render
out['gagaring']['products'] = build_product_summary(['ooo-gagaring'])
out['gagaring']['hub_metric'] = [{'slug': 'ooo-gagaring', **HUB_METRICS['ooo-gagaring'], 'r': gagaring_hub_r}]

out['goudron']['products'] = build_product_summary(['ooo-goudron'])
out['goudron']['hub_metric'] = [{'slug': 'ooo-goudron', **HUB_METRICS['ooo-goudron'], 'r': goudron_hub_r}]

out['piranya']['products'] = build_product_summary(['ooo-skb-piranya'])
out['piranya']['hub_metric'] = [{'slug': 'ooo-skb-piranya', **HUB_METRICS['ooo-skb-piranya'], 'r': piranya_hub_r}]

out['tsyganov']['products'] = build_product_summary(['ip-tsyganov-vadim-borisovich'])
out['tsyganov']['hub_metric'] = [{'slug': 'ip-tsyganov-vadim-borisovich', **HUB_METRICS['ip-tsyganov-vadim-borisovich'], 'r': tsyganov_hub_r}]

out['cherezov']['products'] = build_product_summary(['ooo-vozdushnyy-traktat', 'ovod'])
out['cherezov']['hub_metric'] = [
    {'slug': 'ooo-vozdushnyy-traktat', **HUB_METRICS['ooo-vozdushnyy-traktat'], 'r': traktat_hub_r},
    {'slug': 'ovod', **HUB_METRICS['ovod'], 'r': ovod_hub_r},
]

json.dump(out, open(f'{SCRATCH}/svgs.json', 'w'), ensure_ascii=False, indent=2)
for k, v in out.items():
    print(k, v['stats'], 'hub_metric=', v['hub_metric'], 'products=', {kk: v['products'][kk] for kk in ('total', 'more')})
