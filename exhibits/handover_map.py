"""Handover map: where the recorded deliveries say the equipment went, drawn on region outlines.

A delivery that names a town or a direction named after a town is a dot at that town; one that names only a region
shades the region; one that names a group of forces, a unit without a place, or nothing is listed under the map,
not placed. The place of each delivery is read by hand from its recipient wording and kept in PLACE_OF below, so the
choice is reviewable. Borders are the internationally recognised ones; the map draws no front line, because no
source on file gives one. Outlines and town points: exhibits/geo/handover_map.json (geoBoundaries / OpenStreetMap,
ODbL; Wikidata).
"""
from __future__ import annotations

import html
import json
import math
from pathlib import Path

GEO = json.loads((Path(__file__).resolve().parent / "geo" / "handover_map.json").read_text(encoding="utf-8"))
esc = html.escape

# delivery id -> places it names: ("town", key in GEO["places"]) or ("region", region name in GEO["regions"])
PLACE_OF = {
    "bulat-d01": [("town", "Pokrovsk")],             # «Красноармейское направление»: Pokrovsk's Russian name
    "bulat-d04": [("region", "Kursk Oblast")],       # «Курское направление»
    "bulat-d05": [("town", "Donetsk")],              # «Донецкое направление» (the 132nd «Горловская» brigade)
    "bulat-d07": [("region", "Zaporizhia Oblast")],
    "bulat-d08": [("region", "Luhansk Oblast")],     # «ЛНР»
    "bulat-d09": [("town", "Pokrovsk")],             # «Покровское направление»
    "bulat-d14": [("region", "Kursk Oblast")],
    "bulat-d15": [("region", "Kursk Oblast")],
    "bulat-d16": [("town", "Svatove")],              # «Сватовское направление»
    "bulat-d17": [("region", "Kherson Oblast")],
    "bulat-d18": [("region", "Kursk Oblast")],
    "kapyushon-d01": [("region", "Kherson Oblast"), ("region", "Zaporizhia Oblast")],
    "kapyushon-d03": [("town", "Kursk")],            # Kursk Regional Clinical Hospital
    "kapyushon-d05": [("region", "Kherson Oblast")],
    "kapyushon-d08": [("region", "Zaporizhia Oblast")],
}
REGION_EN = {"Zaporizhia Oblast": "Zaporizhzhia", "Kherson Oblast": "Kherson", "Luhansk Oblast": "Luhansk",
             "Kursk Oblast": "Kursk", "Donetsk Oblast": "Donetsk"}
TOWN_EN = {"Pokrovsk": "Pokrovsk", "Donetsk": "Donetsk", "Svatove": "Svatove", "Kursk": "Kursk"}
BBOX = (32.0, 45.6, 40.8, 52.6)   # lon0, lat0, lon1, lat1
W = 760


def _proj():
    lon0, lat0, lon1, lat1 = BBOX
    k = math.cos(math.radians((lat0 + lat1) / 2))
    sx = W / ((lon1 - lon0) * k)
    h = (lat1 - lat0) * sx
    return (lambda lon, lat: ((lon - lon0) * k * sx, (lat1 - lat) * sx)), h


def _centroid(rings):
    xs = [p for r in rings for p in r]
    big = max(rings, key=len)
    return sum(x for x, _ in big) / len(big), sum(y for _, y in big) / len(big)


def render(deliveries: list[dict], label_of=lambda d: d.get("recipient_en") or d.get("recipient")) -> tuple[str, list]:
    """(svg, unplaced): the map for these deliveries and the deliveries it could not place."""
    p, h = _proj()
    towns, regions, unplaced = {}, {}, []
    for d in deliveries:
        where = PLACE_OF.get(d.get("id"))
        if not where:
            unplaced.append(d)
            continue
        for kind, key in where:
            (towns if kind == "town" else regions).setdefault(key, []).append(d)
    out = [f'<svg class="hmap" viewBox="0 0 {W} {h:.0f}" role="img" aria-label="Where the recorded handovers say the '
           f'equipment went">']
    for f in GEO["regions"]:
        d_attr = " ".join("M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in (p(*pt) for pt in r)) + "Z" for r in f["rings"])
        cls = "ru" if f["country"] == "RUS" else "ua"
        n = len(regions.get(f["name"], []))
        out.append(f'<path class="rg {cls}{" hit" if n else ""}" d="{d_attr}"><title>{esc(f["name"])}'
                   f'{f": {n} handover(s)" if n else ""}</title></path>')
    for f in GEO["regions"]:   # region counts on top of every outline
        n = len(regions.get(f["name"], []))
        if n:
            cx, cy = p(*_centroid(f["rings"]))
            label = f'{REGION_EN.get(f["name"], f["name"])} region · {n}'
            bw = 7.2 * len(label) + 16
            if any(abs(p(GEO["places"][k]["lon"], GEO["places"][k]["lat"])[1] - cy) < 30 and
                   abs(p(GEO["places"][k]["lon"], GEO["places"][k]["lat"])[0] - cx) < bw / 2 + 40 for k in towns):
                cy += 34   # keep clear of a town dot in the same region
            out.append(f'<g class="rc"><rect x="{cx - bw / 2:.0f}" y="{cy - 12:.0f}" width="{bw:.0f}" height="24" rx="3"/>'
                       f'<text x="{cx:.0f}" y="{cy + 4:.0f}">{esc(label)}</text></g>')
    for key, ds in towns.items():
        pl = GEO["places"][key]
        x, y = p(pl["lon"], pl["lat"])
        r = 6 + 3 * (len(ds) - 1)
        out.append(f'<g class="tw"><circle cx="{x:.1f}" cy="{y:.1f}" r="{r}"/><text x="{x + r + 4:.1f}" y="{y + 4:.1f}">'
                   f'{esc(TOWN_EN.get(key, key))}{f" · {len(ds)}" if len(ds) > 1 else ""}</text></g>')
    for name, lon, lat in (("UKRAINE", 33.2, 48.9), ("RUSSIA", 38.6, 51.9)):
        x, y = p(lon, lat)
        out.append(f'<text class="cn" x="{x:.0f}" y="{y:.0f}">{name}</text>')
    out.append("</svg>")
    return "".join(out), unplaced


CSS = """
.hmap-fig { margin: 0; display: flex; flex-direction: column; gap: 8px; max-width: 780px; }
.hmap-scroll { overflow-x: auto; }
.hmap { width: 100%; min-width: 520px; height: auto; display: block; background: var(--panel); border: 1px solid var(--rule); border-radius: var(--radius); }
.hmap .rg { stroke: var(--rule); stroke-width: .8; }
.hmap .rg.ua { fill: var(--panel-2); }
.hmap .rg.ru { fill: var(--paper); }
.hmap .rg.hit { fill: var(--accent-soft); stroke: var(--accent); stroke-width: 1.2; }
.hmap .rc rect { fill: var(--panel); stroke: var(--accent); stroke-width: 1; }
.hmap .rc text { fill: var(--ink); font: 600 11px var(--font-sans); text-anchor: middle; }
.hmap .tw circle { fill: var(--ink); fill-opacity: .82; stroke: var(--panel); stroke-width: 1.5; }
.hmap .tw text { fill: var(--ink); font: 600 12px var(--font-sans); paint-order: stroke; stroke: var(--panel); stroke-width: 3px; }
.hmap .cn { fill: var(--ink-3); font: 600 12px var(--font-mono); letter-spacing: .2em; }
.hmap-fig figcaption { font-size: var(--t-note); color: var(--ink-3); }
.hmap-fig .unplaced { margin: 0; padding-left: 18px; font-size: var(--t-note); color: var(--ink-2); }
"""
