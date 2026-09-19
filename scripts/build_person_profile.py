#!/usr/bin/env python3
"""Render a person profile page (Markdown + HTML) from the registry.

Local file processing over data/registry/*.json -- no network calls, safe to
run directly/repeatedly, like build_company_profile.py. Reads
people.json/entities.json/sources.json, builds a rendering context for one
person, and fills templates/person_profile.{md,html}.jinja2 with it, writing
docs/profiles/persons/<slug>.md and docs/profiles/persons/<slug>.html.

Design source: a canvas mockup built and approved 2026-09-15 for one real
person (Барашков Александр Сергеевич) -- see notes/rebuild_plan.md's
dataviz-research entry. This script generalizes that layout: a masthead,
roles table, a radial ego-network SVG (person at center, this person's own
entities on a ring, each entity's products/co-role people/sister-entities as
satellites), a products-via-companies section, a related-persons section,
and sanctions/screening -- reusing docs/assets/profile.css tokens verbatim,
same discipline as company/product profiles.

Every claim renders with its own [sNNNN] citation resolved in the page's own
"Sources cited" table -- no internal field names or raw source_ids in
visible prose (STYLE_GUIDE.md's forensic register).

Usage:
  python3 scripts/build_person_profile.py --slug barashkov-aleksandr-sergeevich
  python3 scripts/build_person_profile.py --inn 252201766438
  python3 scripts/build_person_profile.py --all
"""
import argparse
import json
import re
import sys
from pathlib import Path

import jinja2
from profile_text import bracket_source_ids_html, bracket_source_ids_md

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from build_company_profile import ru_date, source_type_label  # noqa: E402

REG = REPO / "data" / "registry"
TEMPLATES = REPO / "templates"
OUT_DIR = REPO / "docs" / "profiles" / "persons"
DOCS_IMAGES = REPO / "docs" / "images"

# Radial layout constants (same visual grammar as the approved mockup).
CX, CY = 460, 260
RING_R = 170
SAT_R = 300
MAX_PRIMARY = 6      # entities drawn on the primary ring before "+N more"
MAX_SATELLITES = 2   # per-entity satellites (product summary, co-role person)


def load_json(name):
    return json.loads((REG / name).read_text(encoding="utf-8"))


def role_kind(role_texts):
    """Classify a person's role(s) at one entity from their free-text titles."""
    blob = " ".join(t.lower() for t in role_texts if t)
    has_dir = "директор" in blob or "director" in blob
    has_founder = "учредит" in blob or "founder" in blob or "основател" in blob
    if has_dir and has_founder:
        return "director+founder"
    if has_dir:
        return "director"
    if has_founder:
        return "founder"
    return "other"


ROLE_LABEL = {
    "director+founder": "director + founder",
    "director": "director",
    "founder": "founder",
    "other": "role",
}
ROLE_CSS = {
    "director+founder": "rk-both",
    "director": "rk-director",
    "founder": "rk-founder",
    "other": "rk-other",
}


class PersonProfileBuilder:
    def __init__(self):
        self.people = load_json("people.json")
        self.entities = load_json("entities.json")
        self.sources = load_json("sources.json")
        self.by_person_slug = {p["slug"]: p for p in self.people}
        self.by_slug = {e["slug"]: e for e in self.entities}
        self.src_by_id = {s["id"]: s for s in self.sources}
        self.cited_ids = set()

    def source_label(self, source_id):
        if not source_id:
            return None
        self.cited_ids.add(source_id)
        return source_id

    def source_locator(self, s):
        if s.get("url"):
            return s["url"], s["url"]
        label = source_type_label(s["path"])
        return f"{label} ({Path(s['path']).name})", None

    def docs_image_url(self, rel_path):
        if not rel_path:
            return None
        candidate = REPO / "docs" / rel_path
        if not candidate.exists():
            return None
        return f"../../{rel_path}"

    def entity_display(self, slug, fallback=None):
        e = self.by_slug.get(slug)
        if e:
            return e.get("name_latin") or e.get("name_ru")
        return fallback or slug

    def entity_profile_url(self, slug):
        if slug and slug in self.by_slug and not self.by_slug[slug].get("_merged_into") \
                and (OUT_DIR.parent / f"{slug}.html").exists():
            return f"../{slug}.html"
        return None

    # --- per-person data assembly -------------------------------------

    def person_roles(self, p):
        """Group this person's roles[] by resolved entity_slug (skip
        unresolved _candidate entries -- same convention build_relationship_
        graph.py uses)."""
        by_entity = {}
        for r in p.get("roles", []):
            if not isinstance(r, dict) or r.get("_candidate"):
                continue
            slug = r.get("entity_slug")
            key = slug or f"unresolved::{r.get('entity_name')}"
            by_entity.setdefault(key, {"slug": slug, "name": r.get("entity_name"), "recs": []})
            by_entity[key]["recs"].append(r)
        return by_entity

    def entity_co_role_people(self, entity_slug, exclude_person_slug):
        """Other people with a resolved role at the same entity."""
        out = []
        for other in self.people:
            if other["slug"] == exclude_person_slug:
                continue
            for r in other.get("roles", []):
                if isinstance(r, dict) and not r.get("_candidate") and r.get("entity_slug") == entity_slug:
                    out.append({"slug": other["slug"], "fio_ru": other.get("fio_ru"),
                                "name_latin": other.get("name_latin"),
                                "title": r.get("title"), "source": self.source_label(r.get("source_id"))})
                    break
        return out

    def build_context(self, p):
        slug = p["slug"]
        display_name = p.get("name_latin") or p.get("fio_ru")

        chips = []
        if p.get("sanctions"):
            chips.append({"label": "sanctioned", "cls": "t-low"})
        else:
            chips.append({"label": "no sanctions on file", "cls": "t-clean"})

        by_entity = self.person_roles(p)

        # --- roles table ---
        role_rows = []
        for key, group in by_entity.items():
            recs = group["recs"]
            titles = [r.get("title") for r in recs if r.get("title")]
            since = next((r.get("from") for r in recs if r.get("from")), None)
            until = next((r.get("to") for r in recs if r.get("to")), None)
            src = next((self.source_label(r.get("source_id")) for r in recs if r.get("source_id")), None)
            entity_name = self.entity_display(group["slug"], group["name"])
            role_rows.append({
                "entity_slug": group["slug"], "entity_name": entity_name,
                "profile_url": self.entity_profile_url(group["slug"]),
                "role_text": "; ".join(titles) if titles else None,
                "since": ru_date(since), "until": ru_date(until),
                "source": src,
                "kind": role_kind(titles),
                "kind_label": ROLE_LABEL[role_kind(titles)],
                "kind_cls": ROLE_CSS[role_kind(titles)],
            })
        role_rows.sort(key=lambda r: (r["entity_slug"] is None, r["kind"] != "director+founder"))

        # --- products via this person's entities ---
        products = []
        for key, group in by_entity.items():
            e = self.by_slug.get(group["slug"])
            if not e:
                continue
            plist = e.get("products") or []
            if not plist:
                continue
            names = [pr.get("name_ru") if isinstance(pr, dict) else pr for pr in plist]
            names = [n for n in names if n]
            if not names:
                continue
            k = role_kind([r.get("title") for r in group["recs"] if r.get("title")])
            products.append({
                "entity_slug": group["slug"], "entity_name": self.entity_display(group["slug"]),
                "profile_url": self.entity_profile_url(group["slug"]),
                "first": names[0], "rest_count": len(names) - 1,
                "kind": k, "kind_label": ROLE_LABEL[k],
            })

        # --- related persons (co-role at any shared entity) ---
        related_persons = []
        seen_pairs = set()
        for key, group in by_entity.items():
            if not group["slug"]:
                continue
            for other in self.entity_co_role_people(group["slug"], slug):
                pair = (other["slug"], group["slug"])
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)
                related_persons.append({
                    **other,
                    "via_entity": self.entity_display(group["slug"]),
                    "via_profile_url": self.entity_profile_url(group["slug"]),
                })

        # --- sanctions / screening ---
        screening = []
        if p.get("opensanctions_matches"):
            best = max(p["opensanctions_matches"], key=lambda m: m.get("score") or 0)
            rejected = not p.get("sanctions")
            verdict = "rejected — different identity" if rejected else "confirmed"
            screening.append({"label": "OpenSanctions", "value": f"{len(p['opensanctions_matches'])} candidate(s), best score {best.get('score')} — {verdict}"})
        if p.get("disqualification_hits") is not None:
            screening.append({"label": "Disqualified-director registry",
                               "value": f"{len(p['disqualification_hits'])} hit(s)" if p["disqualification_hits"] else f"No hits (checked {p.get('disqualification_checked_at','—')})"})
        if p.get("subsidiary_liability_hits") is not None:
            screening.append({"label": "Subsidiary-liability registry",
                               "value": f"{len(p['subsidiary_liability_hits'])} hit(s)" if p["subsidiary_liability_hits"] else f"No hits (checked {p.get('subsidiary_liability_checked_at','—')})"})
        if p.get("egrip_hits"):
            screening.append({"label": "ЕГРИП (personal ИП)", "value": f"{len(p['egrip_hits'])} registration(s) on file"})

        sanctions = []
        for s in p.get("sanctions", []):
            regimes = s.get("regime")
            regimes_str = ", ".join(regimes) if isinstance(regimes, list) else (regimes or "Sanctioned")
            sanctions.append({"regimes": regimes_str, "note": s.get("note"), "source": self.source_label(s.get("source_id"))})

        network_svg = self.build_ego_svg(role_rows, products, related_persons)

        meta_grid = []

        def add_meta(label, value):
            if value not in (None, "", []):
                meta_grid.append({"label": label, "value": value})

        add_meta("DOB", ru_date(p.get("dob")))
        add_meta("Birthplace", p.get("birthplace"))
        add_meta("Personal ИНН", p.get("inn_personal"))
        add_meta("Address", p.get("address"))
        add_meta("Entities linked", len(by_entity) if by_entity else None)
        primary = next((r for r in role_rows if r["kind"] == "director+founder"), role_rows[0] if role_rows else None)
        add_meta("Primary role", f'{primary["role_text"] or ROLE_LABEL[primary["kind"]]}, {primary["entity_name"]}' if primary else None)

        photo_url = self.docs_image_url(p.get("photo"))

        sources_table = []
        for sid in sorted(self.cited_ids):
            s = self.src_by_id.get(sid)
            if not s:
                continue
            locator, url = self.source_locator(s)
            sources_table.append({
                "id": sid, "type": source_type_label(s["path"]), "url": url,
                "locator": locator, "locator_md": locator,
                "captured_date": s.get("captured_date"), "as_of": s.get("as_of"),
            })

        return {
            "slug": slug, "display_name": display_name, "fio_ru": p.get("fio_ru"),
            "photo_url": photo_url, "chips": chips, "meta_grid": meta_grid,
            "role_rows": role_rows, "products": products, "related_persons": related_persons,
            "screening": screening, "sanctions": sanctions,
            "network_svg": network_svg,
            "sources_table": sources_table,
        }

    # --- radial ego-network diagram ------------------------------------

    def build_ego_svg(self, role_rows, products, related_persons):
        resolved = [r for r in role_rows if r["entity_slug"]]
        shown = resolved[:MAX_PRIMARY]
        overflow = len(resolved) - len(shown)
        if not shown:
            return None

        import math
        n = len(shown)
        nodes_svg = []
        edges_svg = []
        products_by_entity = {pr["entity_slug"]: pr for pr in products}
        persons_by_entity = {}
        for rp in related_persons:
            persons_by_entity.setdefault(rp.get("via_entity"), rp)

        max_x = CX + SAT_R + 140
        max_y = CY + SAT_R + 80
        min_x = CX - SAT_R - 140
        min_y = 20

        for i, r in enumerate(shown):
            angle = (2 * math.pi * i / n) - math.pi / 2
            ex = CX + RING_R * math.cos(angle)
            ey = CY + RING_R * math.sin(angle)
            kind_fill = "var(--accent-soft)" if r["kind"] == "director+founder" else "var(--panel-2)"
            kind_stroke = "var(--accent)" if r["kind"] == "director+founder" else "var(--rule)"
            edges_svg.append(f'<line x1="{CX}" y1="{CY}" x2="{ex:.0f}" y2="{ey:.0f}" stroke="var(--ink-3)" stroke-width="1.6"/>')
            name = (r["entity_name"] or "?")[:26]
            nodes_svg.append(
                f'<g><rect x="{ex-58:.0f}" y="{ey-24:.0f}" width="116" height="48" rx="6" '
                f'fill="{kind_fill}" stroke="{kind_stroke}" stroke-width="2"/>'
                f'<text x="{ex:.0f}" y="{ey-2:.0f}" text-anchor="middle" font-family="var(--sans)" '
                f'font-size="10.5" font-weight="640" fill="var(--ink)">{escape_xml(name)}</text>'
                f'<text x="{ex:.0f}" y="{ey+12:.0f}" text-anchor="middle" font-family="var(--mono)" '
                f'font-size="8.5" fill="var(--ink-3)">{ROLE_LABEL[r["kind"]]}</text></g>'
            )
            sat_angle_offsets = [-0.28, 0.28]
            sats = []
            pr = products_by_entity.get(r["entity_slug"])
            if pr:
                sats.append(("prod", pr["first"][:22] + ("…" if len(pr["first"]) > 22 else ""), pr["rest_count"]))
            rp = persons_by_entity.get(r["entity_name"])
            if rp:
                nm = (rp.get("name_latin") or rp.get("fio_ru") or "?")[:20]
                sats.append(("person", nm, None))
            for j, (skind, label, extra) in enumerate(sats[:MAX_SATELLITES]):
                soff = sat_angle_offsets[j] if j < len(sat_angle_offsets) else 0
                sangle = angle + soff
                sx = CX + SAT_R * math.cos(sangle)
                sy = CY + SAT_R * math.sin(sangle)
                edges_svg.append(f'<line x1="{ex:.0f}" y1="{ey:.0f}" x2="{sx:.0f}" y2="{sy:.0f}" stroke="var(--ink-3)" stroke-width="1.2" stroke-dasharray="3 3"/>')
                if skind == "prod":
                    fill, stroke = "var(--ok-bg)", "var(--ok)"
                    sub = f"+{extra} more products" if extra else "product"
                else:
                    fill, stroke = "var(--person-bg, var(--mid-bg))", "var(--person, var(--mid))"
                    sub = "co-role person"
                nodes_svg.append(
                    f'<g><rect x="{sx-52:.0f}" y="{sy-20:.0f}" width="104" height="40" rx="5" '
                    f'fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>'
                    f'<text x="{sx:.0f}" y="{sy-2:.0f}" text-anchor="middle" font-family="var(--sans)" '
                    f'font-size="9.5" fill="var(--ink)">{escape_xml(label)}</text>'
                    f'<text x="{sx:.0f}" y="{sy+11:.0f}" text-anchor="middle" font-family="var(--mono)" '
                    f'font-size="7.5" fill="var(--ink-3)">{escape_xml(sub)}</text></g>'
                )

        overflow_svg = ""
        if overflow > 0:
            overflow_svg = (
                f'<text x="{CX:.0f}" y="{max_y-30:.0f}" text-anchor="middle" font-family="var(--mono)" '
                f'font-size="10" fill="var(--ink-3)">+{overflow} more entities not shown</text>'
            )

        ego = (
            f'<circle cx="{CX}" cy="{CY}" r="32" fill="var(--person-bg, var(--accent-soft))" '
            f'stroke="var(--person, var(--accent))" stroke-width="2.5"/>'
            f'<text x="{CX}" y="{CY-2}" text-anchor="middle" font-family="var(--sans)" font-size="10" '
            f'font-weight="640" fill="var(--ink)">this profile</text>'
        )

        width = max_x - min_x
        height = max_y - min_y
        return (
            f'<svg viewBox="{min_x} {min_y} {width:.0f} {height:.0f}" width="{width:.0f}" height="{height:.0f}" role="img" '
            f'aria-label="Ego network diagram">'
            + "".join(edges_svg) + "".join(nodes_svg) + ego + overflow_svg + "</svg>"
        )

    def render(self, slug):
        p = self.by_person_slug.get(slug)
        if not p:
            raise SystemExit(f"no person with slug {slug!r} in people.json")
        self.cited_ids = set()
        ctx = self.build_context(p)

        html_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(TEMPLATES)),
            autoescape=True, trim_blocks=True, lstrip_blocks=True,
        )
        md_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(TEMPLATES)),
            autoescape=False, trim_blocks=False, lstrip_blocks=False,
        )

        OUT_DIR.mkdir(parents=True, exist_ok=True)
        html = html_env.get_template("person_profile.html.jinja2").render(**ctx)
        html = bracket_source_ids_html(html)
        (OUT_DIR / f"{slug}.html").write_text(html, encoding="utf-8")
        md = md_env.get_template("person_profile.md.jinja2").render(**ctx)
        md = bracket_source_ids_md(md)
        md = re.sub(r"\n{3,}", "\n\n", md)
        (OUT_DIR / f"{slug}.md").write_text(md, encoding="utf-8")
        return OUT_DIR / f"{slug}.html", OUT_DIR / f"{slug}.md"


def escape_xml(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--slug")
    g.add_argument("--inn")
    g.add_argument("--all", action="store_true")
    args = ap.parse_args()

    builder = PersonProfileBuilder()
    if args.all:
        # Only people with at least one resolved (non-candidate) role --
        # a bare name with nothing linked isn't a profilable person yet.
        slugs = []
        for p in builder.people:
            if any(isinstance(r, dict) and not r.get("_candidate") for r in p.get("roles", [])):
                slugs.append(p["slug"])
    elif args.inn:
        slugs = [p["slug"] for p in builder.people if p.get("inn_personal") == args.inn]
        if not slugs:
            raise SystemExit(f"no person with personal ИНН {args.inn}")
    else:
        slugs = [args.slug]

    for slug in slugs:
        html_path, md_path = builder.render(slug)
        print(f"{slug}: wrote {html_path.relative_to(REPO)} + {md_path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
