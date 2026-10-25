"""Draws the Kherson / Dnipro left-bank map for the landing page's front section.

Input: the saved DeepState download (data/sources/WEBCAPTURE_20261025_deepstatemap-last-state-20261023.json), whose
"Окуповано" polygon is the Russian-held area on that date. Output: exhibits/images/maps/kherson-front.svg (a small file
with only the cropped area, so the page needs no source file). Town positions are the places' public coordinates.
Units are NOT placed by position: no source gives one. Each unit is a callout pointing at the place or sector its source
names, with its grade.

    ~/.venvs/roymarket311/bin/python exhibits/make_front_map.py
"""
import json
import math
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "data" / "sources" / "WEBCAPTURE_20261025_deepstatemap-last-state-20261023.json"
OUT = REPO / "exhibits" / "images" / "maps" / "kherson-front.svg"

LON0, LON1, LAT0, LAT1 = 32.15, 34.05, 46.3, 47.0
W = 1150
K = math.cos(math.radians(46.8))
H = round(W * (LAT1 - LAT0) / ((LON1 - LON0) * K))

TOWNS = [  # name, lat, lon, held by (as the front line shows it), label side
    ("Kherson", 46.6354, 32.6169, "ua", "l"),
    ("Hola Prystan", 46.5103, 32.5084, "ru", "r"),
    ("Oleshky", 46.6256, 32.7189, "ru", "r"),
    ("Nova Kakhovka", 46.7547, 33.3482, "ua", "l"),
    ("Beryslav", 46.8419, 33.4256, "ua", "l"),
]


def xy(lon, lat):
    return (lon - LON0) / (LON1 - LON0) * W, (LAT1 - lat) / (LAT1 - LAT0) * H


def ring_path(ring):
    pts, far = [], 0
    for lon, lat, *_ in ring:
        inside = LON0 - .3 <= lon <= LON1 + .3 and LAT0 - .3 <= lat <= LAT1 + .3
        if inside:
            far = 0
        else:
            far += 1
            if far % 12:
                continue
        pts.append(xy(lon, lat))
    return "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + "Z"


def main():
    d = json.loads(SRC.read_text())
    feats = d["map"]["features"]
    held = [f for f in feats if f["properties"].get("name", "").startswith("Окуповано") and f["geometry"]["type"] == "Polygon"
            and any(LON0 <= p[0] <= LON1 and LAT0 <= p[1] <= LAT1 for r in f["geometry"]["coordinates"] for p in r)]
    assert held, "no occupied polygon in the box"
    path = "".join(ring_path(r) for f in held for r in f["geometry"]["coordinates"])
    stamp = f'{__import__("datetime").datetime.utcfromtimestamp(d["id"]):%d.%m.%Y}'
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" class="front-map" '
         f'aria-label="Map of the Kherson area and the Dnipro left bank, with the Russian-held area as of {stamp}">',
         '<defs><pattern id="fm-hatch" width="9" height="9" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
         '<line x1="0" y1="0" x2="0" y2="9" stroke="var(--ink-3)" stroke-width="1.2" opacity=".45"/></pattern>'
         f'<clipPath id="fm-clip"><rect width="{W}" height="{H}"/></clipPath></defs>',
         f'<rect width="{W}" height="{H}" fill="var(--panel-2)"/>',
         f'<g clip-path="url(#fm-clip)"><path d="{path}" fill="var(--panel)" stroke="none"/>'
         f'<path d="{path}" fill="url(#fm-hatch)" stroke="var(--ink)" stroke-width="2.2" stroke-linejoin="round"/></g>']
    for name, lat, lon, side, _ in TOWNS:
        x, y = xy(lon, lat)
        right = side == "ru"
        tx = x + 11 if right else x - 11
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="var(--ink)" stroke="var(--paper)" stroke-width="1.5"/>'
                 f'<text x="{tx:.1f}" y="{y + 4:.1f}" text-anchor="{"start" if right else "end"}" class="fm-t">{name}</text>')
    # the units: DeepState's own markers (Point features) for the formations this section names; the callouts sit in the
    # empty Ukrainian-held corner and point at them. A unit with no marker in the area is listed without a pin.
    marks = {}
    for f in feats:
        g, n = f["geometry"], f["properties"].get("name", "")
        if g["type"] != "Point":
            continue
        for key, needle in (("205", "205th Separate Motorized"), ("49", "49th combined-arms army"),
                            ("98a", "331st Airborne"), ("98b", "217th Airborne"), ("98c", "299th Airborne")):
            if needle in n:
                marks[key] = xy(g["coordinates"][0], g["coordinates"][1])
    assert {"205", "49", "98a", "98b", "98c"} <= set(marks), marks
    cx, cw = 20, 345
    callouts = [  # (y, grade, title, line 1, line 2, pins)
        (14, "rep", "205th motor-rifle brigade", "DeepState's marker. DW and the CIR say its drones", "worked over Beryslav; they could not prove who fired", [marks["205"]]),
        (90, "rep", "49th Army", "DeepState's marker for its headquarters. A channel", "that posts the 205th's footage places the brigade in it", [marks["49"]]),
        (166, "rep", "98th Airborne Division", "Three of its regiments as DeepState marks them; the", "channel's 24.10.2026 clip carries the division's watermark", [marks["98a"], marks["98b"], marks["98c"]]),
        (242, "doc", "18th Combined Arms Army", "Named in the UN's October 2025 report; DeepState", "has no marker for it in this area", []),
    ]
    names = {"205": "205th brigade", "49": "49th Army HQ", "98a": "331st (98th Div.)", "98b": "217th (98th Div.)", "98c": "299th (98th Div.)"}
    for k, (px, py) in ((k, marks[k]) for k in ("205", "49", "98a", "98b", "98c")):
        s.append(f'<g transform="translate({px:.1f} {py:.1f})"><rect x="-9" y="-9" width="18" height="18" transform="rotate(45)" fill="var(--panel)" '
                 'stroke="var(--ink)" stroke-width="2.2"/><path d="M-6 -6L6 6M6 -6L-6 6" stroke="var(--ink)" stroke-width="1.6"/></g>'
                 f'<text x="{px + 16:.1f}" y="{py + 18:.1f}" class="fm-t">{names[k]}</text>')
    for y, g, t, l1, l2, pins in callouts:
        s.append(f'<g><rect x="{cx}" y="{y}" width="{cw}" height="62" rx="4" fill="var(--panel)" stroke="var(--g-{g})" stroke-width="2" '
                 f'stroke-dasharray="{"0" if g == "doc" else "7 4"}"/>'
                 f'<text x="{cx + 12}" y="{y + 21}" class="fm-h">{t}</text>'
                 f'<text x="{cx + 12}" y="{y + 40}" class="fm-n">{l1}</text><text x="{cx + 12}" y="{y + 54}" class="fm-n">{l2}</text></g>')
    s.append(f'<text x="{W - 12}" y="{H - 12}" text-anchor="end" class="fm-s">Hatched: Russian-held, {stamp}. Diamonds: unit markers. Both from DeepState</text>')
    s.append("</svg>")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(s))
    print(f"wrote {OUT.relative_to(REPO)} {W}x{H}, {len(held)} polygon(s), {OUT.stat().st_size} bytes; towns:",
          {n: tuple(round(v) for v in xy(lo, la)) for n, la, lo, *_ in TOWNS})


main()
