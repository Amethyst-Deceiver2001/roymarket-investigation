import json, math

REPO = "/Users/ak/Downloads/roymarket-investigation"
ents = json.load(open(f"{REPO}/data/registry/entities.json"))
g = json.load(open(f"{REPO}/data/registry/relationship_graph.json"))
nodes = {n['id']: n for n in g['nodes']}
byslug = {e['slug']: e for e in ents}

HUB = "ano-tsbst-centre-for-unmanned-systems-technologies"
CORE = ['ooo-mptm','fond-nasha-pravda','ao-spetstekh-investitsii-ao-spetstekh-pervyy',
        'ooo-sistemnyy-integrator','pao-bank-psb','ao-spetstekh-perviy',
        'ooo-npts-basirtk','ooo-tsentr-bespilotnykh-sistem-tula']

FLAGSHIP_OUTER = ['ooo-gagaring', 'ooo-goudron', 'ooo-vozdushnyy-traktat', 'ooo-skb-piranya']
OTHER_OUTER = ['ano-npts-ushkuynik','ao-npp-bat','ao-stratim','ao-tekhnodron','gk-logos',
         'kulibin-klub','npo-kaysant','npts-ushkuynik','ooo-aeroplatformy','ooo-arkhangel',
         'ooo-atlant-aero','ooo-gaskar','ooo-gk-logos',
         'ooo-konstruktorskoe-byuro-sinergiya','ooo-kopterlab','ooo-mentastep',
         'ooo-npo-kilovatt-shestopalov','ooo-npo-rustekhdron','ooo-rtd-zashchita',
         'ooo-smart-teknolodzhis','ooo-superkhrono','ooo-trimiks-bulat-3mx',
         'ooo-tsentr-dinarus','ooo-vizionero','uraldronzavod']
# place the 4 flagship entities at N / E / S / W (index 0, 7, 14, 22 of 29 slots)
N_OUTER = 29
OUTER = [None] * N_OUTER
flagship_slots = {0: 'ooo-gagaring', 7: 'ooo-goudron', 14: 'ooo-vozdushnyy-traktat', 22: 'ooo-skb-piranya'}
for idx, slug in flagship_slots.items():
    OUTER[idx] = slug
fillers = iter(OTHER_OUTER)
for i in range(N_OUTER):
    if OUTER[i] is None:
        OUTER[i] = next(fillers)
assert len(OUTER) == 29 and len(set(OUTER)) == 29

MARGIN = 210
R_HUB = 60
R_INNER = 175
R_OUTER = 380
R_SAT1 = 460   # cherezov
R_SAT2 = 545   # ovod
CANVAS = R_SAT2 + MARGIN
CX = CY = CANVAS

def deg_of(slug):
    return nodes.get(slug, {}).get('degree', 0)

degs = [deg_of(s) for s in OUTER]
dmin, dmax = min(degs), max(degs)
def outer_radius(slug):
    d = deg_of(slug)
    t = (math.sqrt(d) - math.sqrt(dmin)) / (math.sqrt(dmax) - math.sqrt(dmin) + 1e-9)
    return 6 + t * 13

def tier_color(tier):
    return {
        'manufacturer': 'var(--t-manufacturer)',
        'plumbing': 'var(--t-plumbing)',
        'money-layer': 'var(--t-money-layer)',
        'network': 'var(--t-network)',
        'cbst-core': 'var(--t-cbst-core)',
        'adjacent': 'var(--t-adjacent)',
        'unverified': 'var(--t-unverified)',
    }.get(tier, 'var(--t-none)')

def pt(cx, cy, r, angle_deg):
    a = math.radians(angle_deg)
    return cx + r * math.cos(a), cy + r * math.sin(a)

def label_text(x, y, angle_deg, text, cls="node-label small"):
    left = math.cos(math.radians(angle_deg)) < -0.05
    rot = angle_deg + 180 if left else angle_deg
    anchor = "end" if left else "start"
    return f'<text x="{x:.1f}" y="{y:.1f}" transform="rotate({rot:.1f} {x:.1f} {y:.1f})" text-anchor="{anchor}" dominant-baseline="middle" class="{cls}">{text}</text>'

def short(name, n=34):
    return name if len(name) <= n else name[:n-1] + "…"

svg = []
defs = ('<defs>'
  '<marker id="orbit-arrow-owns" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0L10,5L0,10z" fill="var(--edge-owns)"/></marker>'
  '<marker id="orbit-arrow-generic" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0L10,5L0,10z" fill="var(--edge)"/></marker>'
  '</defs>')
svg.append(defs)

svg.append(f'<circle cx="{CX}" cy="{CY}" r="{R_INNER}" fill="none" stroke="var(--line)" stroke-width="1" stroke-dasharray="2,4"/>')
svg.append(f'<circle cx="{CX}" cy="{CY}" r="{R_OUTER}" fill="none" stroke="var(--line)" stroke-width="1" stroke-dasharray="2,4"/>')

# ---- inner ring: core entities ----
n_core = len(CORE)
core_edges, core_nodes_svg = [], []
for i, slug in enumerate(CORE):
    angle = -90 + i * (360 / n_core)
    x, y = pt(CX, CY, R_INNER, angle)
    ent = byslug.get(slug, {})
    node = nodes.get(slug, {})
    etype = None
    for e in g['edges']:
        if (e['source'] == slug and e['target'] == HUB) or (e['source'] == HUB and e['target'] == slug):
            if e['type'] == 'owns':
                etype = 'owns'; break
            if etype is None:
                etype = e['type']
    if etype == 'owns':
        cls, marker = 'edge edge-owns', ' marker-end="url(#orbit-arrow-owns)"'
    elif etype in ('founded', 'related', 'cbst_tie'):
        cls, marker = 'edge edge-founded', ''
    else:
        cls, marker = 'edge edge-tier-only', ''
    core_edges.append(f'<line x1="{CX}" y1="{CY}" x2="{x:.1f}" y2="{y:.1f}" class="{cls}"{marker}/>')
    color = tier_color('cbst-core')
    if node.get('sanctioned'):
        core_nodes_svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="19" class="sanction-ring"/>')
    core_nodes_svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="15" fill="{color}" class="node-shape" data-id="{slug}"/>')
    label = short(ent.get('name_ru') or slug, 30)
    lx, ly = pt(CX, CY, R_INNER + 22, angle)
    core_nodes_svg.append(label_text(lx, ly, angle, label))

svg.extend(core_edges)

# ---- outer ring: cbst_tie entities ----
n_outer = len(OUTER)
outer_edges, outer_nodes_svg = [], []
pin_labels = {'ooo-gagaring': '1', 'ooo-goudron': '2', 'ooo-vozdushnyy-traktat': '3a',
              'ooo-skb-piranya': '4'}
flagship_pos = {}
outer_pos = {}  # every outer-ring slug -> (x, y, angle, r) — needed to attach satellites
for i, slug in enumerate(OUTER):
    angle = -90 + i * (360 / n_outer)
    x, y = pt(CX, CY, R_OUTER, angle)
    ent = byslug.get(slug, {})
    node = nodes.get(slug, {})
    edge = next((e for e in g['edges'] if e['type'] == 'cbst_tie' and e['source'] == slug and e['target'] == HUB), None)
    conf = edge.get('confidence') if edge else None
    conf_cls = {'t-doc': '', 't-open': 'conf-t-open', 'press': 'conf-press'}.get(conf, '')
    outer_edges.append(f'<line x1="{CX}" y1="{CY}" x2="{x:.1f}" y2="{y:.1f}" class="edge edge-cbst-tie {conf_cls}"/>')
    r = outer_radius(slug)
    outer_pos[slug] = (x, y, angle, r)
    is_flag = slug in FLAGSHIP_OUTER
    color = tier_color(ent.get('tier'))
    if is_flag:
        flagship_pos[slug] = (x, y, angle, r)
        r = r + 4
        outer_nodes_svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r+5:.1f}" fill="none" stroke="var(--accent)" stroke-width="2.5"/>')
    if node.get('sanctioned'):
        outer_nodes_svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r+3.5:.1f}" class="sanction-ring"/>')
    outer_nodes_svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{color}" class="node-shape" data-id="{slug}"/>')
    if is_flag:
        pin = pin_labels[slug]
        px, py = pt(CX, CY, R_OUTER - 2, angle)
        outer_nodes_svg.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="10" fill="var(--accent)" stroke="var(--panel)" stroke-width="1.5"/>')
        outer_nodes_svg.append(f'<text x="{px:.1f}" y="{py:.1f}" text-anchor="middle" dominant-baseline="middle" class="pin-label">{pin}</text>')
        label = short(ent.get('name_ru') or slug, 24)
        lx, ly = pt(CX, CY, R_OUTER + r + 16, angle)
        outer_nodes_svg.append(label_text(lx, ly, angle, label, cls="node-label"))

svg.extend(outer_edges)
svg.extend(core_nodes_svg)
svg.extend(outer_nodes_svg)

# ---- hub ----
svg.append(f'<circle cx="{CX}" cy="{CY}" r="{R_HUB+7}" class="sanction-ring hub-ring"/>')
svg.append(f'<circle cx="{CX}" cy="{CY}" r="{R_HUB}" fill="{tier_color("cbst-core")}" class="node-shape hub-shape"/>')
svg.append(f'<text x="{CX}" y="{CY}" text-anchor="middle" dominant-baseline="middle" class="hub-label">ЦБСТ</text>')

# ---- satellite pair: Черезов + Овод, attached at vozdushnyy-traktat's angle (south) ----
tx, ty, tangle, _tr = flagship_pos['ooo-vozdushnyy-traktat']
cx1, cy1 = pt(CX, CY, R_SAT1, tangle)
ox, oy = pt(CX, CY, R_SAT2, tangle)
svg.append(f'<line x1="{tx:.1f}" y1="{ty:.1f}" x2="{cx1:.1f}" y2="{cy1:.1f}" class="edge edge-founded" marker-end="url(#orbit-arrow-generic)"/>')
svg.append(f'<line x1="{cx1:.1f}" y1="{cy1:.1f}" x2="{ox:.1f}" y2="{oy:.1f}" class="edge edge-founded" marker-end="url(#orbit-arrow-generic)"/>')
svg.append(f'<polygon points="{cx1:.1f},{cy1-9:.1f} {cx1+9:.1f},{cy1:.1f} {cx1:.1f},{cy1+9:.1f} {cx1-9:.1f},{cy1:.1f}" fill="var(--person-fill)" class="node-shape" data-id="cherezov-andrey-pavlovich"/>')
lx, ly = pt(CX, CY, R_SAT1 - 26, tangle - 14)
svg.append(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" dominant-baseline="middle" class="node-label small">Черезов А.П.</text>')
ov_r = outer_radius("ooo-vozdushnyy-traktat")
svg.append(f'<circle cx="{ox:.1f}" cy="{oy:.1f}" r="{ov_r+8:.1f}" class="sanction-ring"/>')
svg.append(f'<circle cx="{ox:.1f}" cy="{oy:.1f}" r="{ov_r+4:.1f}" fill="none" stroke="var(--accent)" stroke-width="2.5"/>')
svg.append(f'<circle cx="{ox:.1f}" cy="{oy:.1f}" r="{ov_r:.1f}" fill="{tier_color("manufacturer")}" class="node-shape" data-id="ovod"/>')
pin3b_x, pin3b_y = pt(CX, CY, R_SAT2 - 2, tangle)
svg.append(f'<circle cx="{pin3b_x:.1f}" cy="{pin3b_y:.1f}" r="10" fill="var(--accent)" stroke="var(--panel)" stroke-width="1.5"/>')
svg.append(f'<text x="{pin3b_x:.1f}" y="{pin3b_y:.1f}" text-anchor="middle" dominant-baseline="middle" class="pin-label">3b</text>')
svg.append(label_text(*pt(CX, CY, R_SAT2 + ov_r + 16, tangle), tangle, "«Овод» / РЛВТ"))

# ---- ИП Цыганов: real 3-hop chain via ООО «ПОКРОВ» (Цыганов directs/100%-owns it,
# its own tier_basis names it a "named 3mx dealer") -> ООО «Тримикс»/3MX (already
# outer-ring, real cbst_tie edge to ЦБСТ). Confirmed by a live BFS over
# relationship_graph.json before this edit: ip-tsyganov-vadim-borisovich
# -[directs]-> ooo-pokrov -[related]-> ooo-trimiks-bulat-3mx -[cbst_tie]-> ЦБСТ.
# The prior build's "no traceable ЦБСТ edge" claim on this node was wrong — the
# path was already sitting in the graph, just never walked past 1 hop.
trx, try_, trangle, tr_r = outer_pos['ooo-trimiks-bulat-3mx']
pkx, pky = pt(CX, CY, R_SAT1, trangle)
tsx, tsy = pt(CX, CY, R_SAT2, trangle)
svg.append(f'<line x1="{trx:.1f}" y1="{try_:.1f}" x2="{pkx:.1f}" y2="{pky:.1f}" class="edge edge-founded"/>')
svg.append(f'<line x1="{pkx:.1f}" y1="{pky:.1f}" x2="{tsx:.1f}" y2="{tsy:.1f}" class="edge edge-owns" marker-end="url(#orbit-arrow-owns)"/>')
pk_r = 9
svg.append(f'<circle cx="{pkx:.1f}" cy="{pky:.1f}" r="{pk_r}" fill="{tier_color("manufacturer")}" class="node-shape" data-id="ooo-pokrov"/>')
plx, ply = pt(CX, CY, R_SAT1 - 22, trangle - 10)
svg.append(f'<text x="{plx:.1f}" y="{ply:.1f}" text-anchor="middle" dominant-baseline="middle" class="node-label small">ООО «ПОКРОВ» (3mx dealer)</text>')
ts_r = 13
svg.append(f'<circle cx="{tsx:.1f}" cy="{tsy:.1f}" r="{ts_r+5:.1f}" fill="none" stroke="var(--accent)" stroke-width="2.5"/>')
svg.append(f'<circle cx="{tsx:.1f}" cy="{tsy:.1f}" r="{ts_r:.1f}" fill="{tier_color("manufacturer")}" class="node-shape" data-id="ip-tsyganov-vadim-borisovich"/>')
pin5x, pin5y = pt(CX, CY, R_SAT2 - 2, trangle)
svg.append(f'<circle cx="{pin5x:.1f}" cy="{pin5y:.1f}" r="10" fill="var(--accent)" stroke="var(--panel)" stroke-width="1.5"/>')
svg.append(f'<text x="{pin5x:.1f}" y="{pin5y:.1f}" text-anchor="middle" dominant-baseline="middle" class="pin-label">5</text>')
svg.append(label_text(*pt(CX, CY, R_SAT2 + ts_r + 16, trangle), trangle, "ИП Цыганов В.Б.", cls="node-label"))

print("\n".join(svg))
print("VIEWBOX 0 0", CANVAS * 2, CANVAS * 2)
