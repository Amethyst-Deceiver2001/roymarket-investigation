#!/usr/bin/env python3
"""Build a relationship graph (nodes + edges) from data/registry/entities.json
and data/registry/people.json, for the network-relationship visualization
requested 2026-09-08 (the "bring us closer to Kontur.Focus Pro's
beneficial-ownership graph" gap — see notes/full_pipeline_catalogue.md).

This is pure local aggregation over already-verified registry data — no
network calls, no new claims. It does NOT invent relationships: every edge
comes from a structured field a human (or a screen_*.py script) already
populated, each of which already carries its own source_id per entity/
person record. The graph adds no sourcing of its own; a viewer clicking an
edge should go back to the underlying entity/person record for the
source_id, the same way the company-profile pages already do.

Edge sources (all pre-existing structured fields, nothing new mined here):
  - entities[].parents[]           entity --owns--> entity   (has slug+share)
  - entities[].subsidiaries[]      entity --owns--> entity   (has slug)
  - entities[].related_entities[]  entity --related(ambiguous)--> entity
  - entities[].founders[]          entity/person --founded--> entity
                                    (name-string only; resolved to a slug by
                                    normalized-name match against both
                                    registries — unresolved names are kept
                                    as unlinked label-only stub nodes so the
                                    graph doesn't silently drop them)
  - entities[].director / director_history[]   person --directs--> entity
                                    (name-string; resolved the same way)
  - entities[].founders_history[]  entity/person --founded--> entity, with
                                    historical=true for any name not also
                                    present in the current founders[] list
                                    (2026-09-08: the flat founders[]/
                                    director[] fields are a display
                                    convenience per CLAUDE.md's dated-history
                                    convention; the _history arrays are the
                                    actual record, so a former founder now
                                    also gets an edge, flagged historical
                                    rather than silently dropped)
  - entities[].director_history[]  additionally flags an entry
                                    historical=true when its value differs
                                    from the entity's current `director`
                                    field (a former director still gets a
                                    "directs" edge, just visually distinct)
  - people[].roles[]                person --role(title)--> entity
                                    (already carries entity_slug when known)
  - people[].other_entities[]       person --director/founder--> entity
                                    (already carries inn; resolved to slug)

Name resolution is fuzzy on purpose (legal-form prefixes/guillemets/case
stripped — see normalize()) because founders[]/director[] were extracted
from EGRUL free text, not authored with slugs. A resolution is logged as
"unresolved" (kept as a same-named stub node, not silently dropped) when no
registry match exists — this surfaces exactly the kind of gap
[[roymarket_fuzzy_dedup]] already found by hand, but automated for the
whole registry at once instead of one document at a time.

Usage:
    python3 scripts/build_relationship_graph.py
    python3 scripts/build_relationship_graph.py --slug ano-npts-ushkuynik  # ego-only subgraph, for spot-checking

Writes data/registry/relationship_graph.json. Local file processing only,
safe to run directly/repeatedly after any registry change.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTITIES = REPO / "data" / "registry" / "entities.json"
PEOPLE = REPO / "data" / "registry" / "people.json"
OUT = REPO / "data" / "registry" / "relationship_graph.json"

LEGAL_PREFIXES = [
    "ООО", "ОАО", "ЗАО", "ПАО", "АО", "АНО", "НКО", "НПЦ", "НПО", "КБ",
    "ФГУП", "ГУП", "МУП", "ИП", "ФОНД", "АССОЦИАЦИЯ", "СОЮЗ", "ОБЩЕСТВО",
]
_PREFIX_RE = re.compile(
    r"^\s*(?:" + "|".join(re.escape(p) for p in LEGAL_PREFIXES) + r")\.?\s+",
    re.IGNORECASE,
)
_QUOTE_RE = re.compile(r"[«»\"'“”‘’]")
_WS_RE = re.compile(r"\s+")
_SHARE_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*%")
_SPLIT_RE = re.compile(r",\s*(?![^(]*\))")


def parse_founder_entries(raw) -> list[dict]:
    """founders[] is shaped inconsistently across the registry — sometimes a
    list of {name, share} dicts, sometimes a single 'Name (25%), Name2 (75%)'
    string, sometimes a list of such strings (a pre-existing data-shape
    inconsistency, not introduced here — normalized on read rather than
    fixed in entities.json, which is out of scope for a graph-building pass).
    """
    if not raw:
        return []
    if isinstance(raw, str):
        raw = [raw]
    out = []
    for item in raw:
        if isinstance(item, dict):
            if item.get("name"):
                out.append({"name": item["name"], "share": item.get("share")})
            continue
        if not isinstance(item, str):
            continue
        for segment in _SPLIT_RE.split(item):
            segment = segment.strip().strip(",")
            if not segment:
                continue
            share_m = _SHARE_RE.search(segment)
            name = segment[: segment.find("(")].strip() if "(" in segment else segment
            name = name.strip(" .,")
            if len(name) < 3:
                continue
            out.append({"name": name, "share": share_m.group(1) if share_m else None})
    return out


# Offensive/defensive/dual-use classification for the hub glyph badges
# (dagger / shield / shield+dagger — see notes/hub_insignia_design_notes.md
# for the full design rationale and semiotics research behind the icon
# choice). Keyword heuristic over products[]' own name_ru/description text,
# same class of approach as id_patterns.py's UAV_TERMS scoring — a
# PRESENTATION judgment for this graph's icon layer only, not a new
# registry field or a sourced claim. A hit on both lists (common — many
# manufacturers here genuinely make both an FPV strike drone and a
# counter-drone/RF line, per the original 5-entity manual pass this
# heuristic generalizes) yields "dual", the same as the manual pass found.
OFFENSIVE_TERMS = [
    "камикадзе", "kamikaze", "ударный дрон", "ударн", "боеприпас",
    "боевая часть", "warhead", "боеголов", "снаряд", "авиабомб", "бомб",
    "штурмов",
]
DEFENSIVE_TERMS = [
    "рэб", "радиоэлектронн", "подавлен", "антидрон", "anti-drone",
    "counter-drone", "counter-uav", "jam", "глушен", "детектор бпла",
    "обнаружен", "щит", "перехватчик", "антиспуфинг", "радиоподавлен",
]


def classify_variant(entity: dict) -> str | None:
    if entity.get("tier") not in ("manufacturer", "cbst-core"):
        return None
    chunks = []
    for prod in entity.get("products") or []:
        if isinstance(prod, dict):
            chunks.append(str(prod.get("name_ru") or ""))
            chunks.append(str(prod.get("description") or ""))
        elif isinstance(prod, str):
            chunks.append(prod)
    text = " ".join(chunks).lower()
    if not text.strip():
        return None
    off = any(term in text for term in OFFENSIVE_TERMS)
    dfn = any(term in text for term in DEFENSIVE_TERMS)
    if off and dfn:
        return "dual"
    if off:
        return "offensive"
    if dfn:
        return "defensive"
    return None


# Product-node subtype classification (2026-09-09), approved from the
# standalone "Product Icon Set" mockup — 15 categories keyword-matched
# against each products[] entry's own name/description text, same
# presentation-layer-read discipline as classify_variant() above (not a
# sourced field). Order matters: earlier patterns are more specific and
# checked first so e.g. a jammer described with "vehicle" doesn't fall
# through to the generic multirotor/UAV catch-all at the bottom.
PRODUCT_CATEGORY_PATTERNS = [
    ("munition_warhead", re.compile(
        r"боеприпас|боевая часть|\bбч\b|warhead|боеголов|снаряд|"
        r"дульная насадка|дронобой", re.I)),
    ("ew_vehicle", re.compile(
        r"(глуш|jam|рэб|подавлен).{0,60}(вездеход|автомобил|машин|vehicle|"
        r"легков|кунг|kung|шасси)|(вездеход|автомобил|машин|vehicle|"
        r"легков|кунг|kung|шасси).{0,60}(глуш|jam|рэб|подавлен)", re.I)),
    ("ew_stationary", re.compile(
        r"(глуш|jam|рэб|подавлен).{0,60}(стационарн|stationary)|"
        r"(стационарн|stationary).{0,60}(глуш|jam|рэб|подавлен)", re.I)),
    ("ew_portable", re.compile(
        r"(глуш|jam|рэб|подавлен).{0,60}(портатив|ранцев|носим|portable|"
        r"handheld|man.?pack)|(портатив|ранцев|носим|portable|handheld|"
        r"man.?pack).{0,60}(глуш|jam|рэб|подавлен)", re.I)),
    ("ew_vehicle", re.compile(r"глуш|jam|рэб\b|подавлен|jammer", re.I)),
    ("detector_counter_uas", re.compile(
        r"детектор|обнаружени|antidrone|anti-drone|counter.?drone|"
        r"counter.?uas|counter-uav", re.I)),
    ("antenna_mast", re.compile(r"антенн|\bmast\b|мачт", re.I)),
    ("battery_power", re.compile(
        r"аккумулятор|батаре|\bbattery\b|повербанк|\bbms\b", re.I)),
    ("motor_part", re.compile(
        r"\bмотор\b|двигател|\bвинт\b|propeller|\bmotor\b", re.I)),
    ("video_link", re.compile(
        r"видеосвяз|видеоприемник|видеоприёмник|видеопередат|video.?link",
        re.I)),
    ("ground_control", re.compile(
        r"пульт управлен|наземная станция|ground control|\bgcs\b", re.I)),
    ("repeater_relay", re.compile(r"ретрансл|repeater|\brelay\b", re.I)),
    ("fixed_wing", re.compile(
        r"самолетн|самолётн|fixed.?wing|конвертоплан|планер", re.I)),
    ("helicopter", re.compile(
        r"вертолет|вертолёт|helicopter|однороторн", re.I)),
    ("fpv_strike", re.compile(
        r"\bfpv\b|камикадзе|kamikaze|барражирующ|ударный дрон", re.I)),
    ("multirotor_utility", re.compile(
        r"квадрокоптер|мультикоптер|октокоптер|multirotor|quadcopter|"
        r"\bбпла\b|\buav\b|\bдрон", re.I)),
]
FIBER_OPTIC_RE = re.compile(r"оптоволок|fiber.?optic|\bволс\b", re.I)


def classify_product(name: str, description: str) -> tuple[str | None, bool]:
    text = f"{name or ''} {description or ''}".strip()
    if not text:
        return None, False
    fiber = bool(FIBER_OPTIC_RE.search(text))
    for category, pattern in PRODUCT_CATEGORY_PATTERNS:
        if pattern.search(text):
            return category, fiber
    return None, fiber


def normalize(name: str) -> str:
    if not name:
        return ""
    n = _QUOTE_RE.sub("", name)
    prev = None
    while prev != n:
        prev = n
        n = _PREFIX_RE.sub("", n)
    n = _WS_RE.sub(" ", n).strip().lower()
    return n


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", default=None, help="limit output to this entity's ego-network")
    args = ap.parse_args()

    entities = json.loads(ENTITIES.read_text(encoding="utf-8"))
    people = json.loads(PEOPLE.read_text(encoding="utf-8"))

    inn_to_entity_slug = {e["inn"]: e["slug"] for e in entities if e.get("inn")}
    name_to_entity_slug = {}
    for e in entities:
        for nm in (e.get("name_ru"), e.get("brand_ru")):
            if nm:
                name_to_entity_slug.setdefault(normalize(nm), e["slug"])
    name_to_person_slug = {}
    inn_to_person_slug = {}
    for p in people:
        if p.get("fio_ru"):
            name_to_person_slug.setdefault(normalize(p["fio_ru"]), p["slug"])
        if p.get("inn_personal"):
            inn_to_person_slug[p["inn_personal"]] = p["slug"]

    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    unresolved: list[dict] = []

    def add_node(node_id, **attrs):
        if node_id not in nodes:
            nodes[node_id] = {"id": node_id, **attrs}
        else:
            nodes[node_id].update({k: v for k, v in attrs.items() if v is not None})

    for e in entities:
        add_node(
            e["slug"],
            kind="entity",
            label=e.get("name_ru") or e.get("brand_ru") or e["slug"],
            name_latin=e.get("name_latin"),
            inn=e.get("inn"),
            tier=e.get("tier"),
            sanctioned=bool(e.get("sanctions")),
            legal_form=e.get("legal_form"),
            variant=classify_variant(e),
        )

    for p in people:
        add_node(
            p["slug"],
            kind="person",
            label=p.get("fio_ru") or p["slug"],
            name_latin=p.get("name_latin"),
            sanctioned=bool(p.get("sanctions")),
            photo=p.get("photo"),
        )

    def resolve_name(raw_name: str) -> str | None:
        norm = normalize(raw_name)
        if norm in name_to_entity_slug:
            return name_to_entity_slug[norm]
        if norm in name_to_person_slug:
            return name_to_person_slug[norm]
        return None

    def add_edge(src, dst, etype, label=None, source_id=None, as_of=None, weight=1.0, historical=False):
        edges.append({
            "source": src, "target": dst, "type": etype,
            "label": label, "source_id": source_id, "as_of": as_of, "weight": weight,
            "historical": bool(historical),
        })

    for e in entities:
        slug = e["slug"]

        for par in e.get("parents") or []:
            if par.get("slug"):
                add_edge(par["slug"], slug, "owns", f"{par.get('share_percent', '?')}%",
                          par.get("source_id"), None, par.get("share_percent") or 1.0)

        for sub in e.get("subsidiaries") or []:
            if sub.get("slug"):
                add_edge(slug, sub["slug"], "owns", sub.get("role"),
                          sub.get("source_id"), sub.get("as_of"))
            elif sub.get("ogrn"):
                match = next((x["slug"] for x in entities if x.get("ogrn") == sub["ogrn"]), None)
                if match:
                    add_edge(slug, match, "owns", sub.get("role"), sub.get("source_id"), sub.get("as_of"))

        for rel in e.get("related_entities") or []:
            if rel.get("slug"):
                add_edge(slug, rel["slug"], "related", "related (ambiguous)", rel.get("source_id"))

        current_founder_names = set()
        for f in parse_founder_entries(e.get("founders")):
            nm = f.get("name")
            if not nm:
                continue
            current_founder_names.add(normalize(nm))
            target = resolve_name(nm)
            if target and target != slug:
                add_edge(target, slug, "founded", f"{f.get('share')}%" if f.get("share") else None)
            elif not target:
                stub_id = f"stub::{normalize(nm)}"
                add_node(stub_id, kind="unresolved", label=nm)
                add_edge(stub_id, slug, "founded")
                unresolved.append({"raw_name": nm, "context": f"founder of {slug}"})

        seen_hist_founders = set()
        for fh in e.get("founders_history") or []:
            raw_val = fh.get("value")
            if not raw_val or (isinstance(raw_val, str) and raw_val.startswith("—")):
                continue
            for f in parse_founder_entries(raw_val):
                nm = f.get("name")
                if not nm:
                    continue
                norm = normalize(nm)
                if norm in current_founder_names or norm in seen_hist_founders:
                    continue
                seen_hist_founders.add(norm)
                target = resolve_name(nm)
                label = f"former founder{' (' + f.get('share') + '%)' if f.get('share') else ''}, as of {fh.get('as_of')}"
                if target and target != slug:
                    add_edge(target, slug, "founded", label, fh.get("source_id"), fh.get("as_of"), historical=True)
                else:
                    stub_id = f"stub::{norm}"
                    add_node(stub_id, kind="unresolved", label=nm)
                    add_edge(stub_id, slug, "founded", label, fh.get("source_id"), fh.get("as_of"), historical=True)
                    unresolved.append({"raw_name": nm, "context": f"former founder of {slug}"})

        current_director_name = normalize(e.get("director")) if e.get("director") else None
        director_entries = e.get("director_history") or ([{"value": e["director"], "source_id": None, "as_of": None}]
                                                            if e.get("director") else [])
        seen_directors = set()
        for d in director_entries:
            nm = d.get("value")
            if not nm or nm in seen_directors or nm.startswith("—"):
                continue
            seen_directors.add(nm)
            is_historical = current_director_name is not None and normalize(nm) != current_director_name
            label = f"former director, as of {d.get('as_of')}" if is_historical and d.get("as_of") else ("former director" if is_historical else None)
            target = resolve_name(nm)
            if target and target != slug:
                add_edge(target, slug, "directs", label, d.get("source_id"), d.get("as_of"), historical=is_historical)
            elif not target:
                stub_id = f"stub::{normalize(nm)}"
                add_node(stub_id, kind="unresolved", label=nm)
                add_edge(stub_id, slug, "directs", label, d.get("source_id"), d.get("as_of"), historical=is_historical)
                unresolved.append({"raw_name": nm, "context": f"director of {slug}"})

    for p in people:
        slug = p["slug"]
        for r in p.get("roles") or []:
            target = r.get("entity_slug")
            if target and target in nodes:
                add_edge(slug, target, "role", r.get("title"), r.get("source_id"), r.get("from"))

        for oe in p.get("other_entities") or []:
            target = oe.get("inn") and inn_to_entity_slug.get(oe["inn"])
            if target and target != slug:
                add_edge(slug, target, "role", oe.get("role"))

    # Product nodes (POLE-style "Object" entity, distinct from the entity/
    # person kinds above) — one node per entities.json products[] entry,
    # dict-shaped (name_ru/description/source_id) or a bare string. Kept as
    # a distinct `kind` so the client can render/toggle them separately
    # rather than folding product facts into the parent entity's tooltip.
    for e in entities:
        slug = e["slug"]
        for i, prod in enumerate(e.get("products") or []):
            if isinstance(prod, dict):
                name = prod.get("name_ru") or prod.get("description")
                description = prod.get("description") or ""
                source_id = prod.get("source_id")
            else:
                name = prod
                description = ""
                source_id = None
            if not name:
                continue
            pid = f"{slug}__product__{i}"
            category, fiber_optic = classify_product(name, description)
            add_node(
                pid,
                kind="product",
                label=name,
                parent_entity=slug,
                source_id=source_id,
                category=category,
                fiber_optic=fiber_optic or None,
            )
            add_edge(slug, pid, "produces", None, source_id)

    if args.slug:
        keep = {args.slug}
        for ed in edges:
            if ed["source"] == args.slug or ed["target"] == args.slug:
                keep.add(ed["source"])
                keep.add(ed["target"])
        nodes = {k: v for k, v in nodes.items() if k in keep}
        edges = [ed for ed in edges if ed["source"] in keep and ed["target"] in keep]

    node_list = list(nodes.values())
    node_ids = {n["id"] for n in node_list}
    edges = [ed for ed in edges if ed["source"] in node_ids and ed["target"] in node_ids]

    degree: dict[str, int] = {}
    for ed in edges:
        degree[ed["source"]] = degree.get(ed["source"], 0) + 1
        degree[ed["target"]] = degree.get(ed["target"], 0) + 1
    for n in node_list:
        n["degree"] = degree.get(n["id"], 0)

    out = {
        "generated_from": "data/registry/entities.json + people.json",
        "node_count": len(node_list),
        "edge_count": len(edges),
        "unresolved_count": len(unresolved),
        "nodes": node_list,
        "edges": edges,
        "unresolved": unresolved,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)} — {len(node_list)} nodes, {len(edges)} edges, "
          f"{len(unresolved)} unresolved name(s) kept as stub nodes")
    edge_types: dict[str, int] = {}
    for ed in edges:
        edge_types[ed["type"]] = edge_types.get(ed["type"], 0) + 1
    print("edge types:", edge_types)


if __name__ == "__main__":
    main()
