#!/usr/bin/env python3
"""Render a product profile page (Markdown + HTML) from the registry.

Local file processing over data/registry/*.json — no network calls, safe to
run directly/repeatedly, like build_company_profile.py.

There is no product-level registry file: products[] entries live nested
under each entity. This script pulls a named product's entries across a
short, hand-maintained FLAGSHIP_PRODUCTS list (one entry per flagship
product, keyed to its maker entity_slug and a set of name-match keywords),
gathers real linked data — images and battlefield_evidence whose caption/
text actually names the product (substring match on the product's own
distinct proper noun, e.g. "Кузнечик"/"Набат"/"Овод"/"Пиранья"/"Булат" —
never a generic keyword that would pull in unrelated evidence), and any
government_contracts on the maker/reseller/distributor chain — and renders
templates/product_profile.{md,html}.jinja2.

This is a first pass covering flagship products only (the same five case-
study entities already central to the coverage audit and the "From ЦБСТ to
the Front" exhibit) — see CLAUDE.md's product-profile section before
expanding FLAGSHIP_PRODUCTS to the full ~489-entry products[] corpus, most
of which currently has no specs/images/field-testing data to build a real
profile from.

Usage:
  python3 scripts/build_product_profile.py --slug kuznechik
  python3 scripts/build_product_profile.py --all
"""
import argparse
import json
import re
from pathlib import Path

import jinja2

REPO = Path(__file__).resolve().parent.parent
REG = REPO / "data" / "registry"
TEMPLATES = REPO / "templates"
OUT_DIR = REPO / "docs" / "profiles" / "products"
DOCS_IMAGES = REPO / "docs" / "images"

# One entry per flagship product. `match` is the list of distinct proper
# nouns used to link images/battlefield_evidence by substring (case-
# insensitive) -- keep these specific (a real product brand name), never a
# generic term, or unrelated evidence gets pulled in.
FLAGSHIP_PRODUCTS = [
    {
        "slug": "kuznechik",
        "maker_slug": "ooo-gagaring",
        "product_names": ["Система связи «Кузнечик»", "Режим «Подхват» (модуль связи «Кузнечик»)"],
        "match": ["кузнечик", "kuznechik"],
        "display_name": "«Кузнечик» (Kuznechik)",
    },
    {
        "slug": "nabat",
        "maker_slug": "ooo-goudron",
        "product_names": ["«Набат v3»"],
        "match": ["набат", "nabat"],
        "display_name": "«Набат» (Nabat)",
    },
    {
        "slug": "ovod",
        "maker_slug": "ooo-vozdushnyy-traktat",
        "reseller_slug": "ovod",
        "product_names": ["«Овод»", "«Провод» / «Провод-15»", "«Провод-15»"],
        "match": ["овод", "ovod", "провод"],
        "display_name": "«Овод» (Ovod)",
    },
    {
        "slug": "piranya",
        "maker_slug": "ooo-skb-piranya",
        "product_names": ["БПЛА «Пиранья-7»", "БПЛА «Пиранья-10»", "БПЛА «Пиранья-13»", "Пиранья 15"],
        "match": ["пиранья", "piranha", "piranya"],
        "display_name": "«Пиранья» (Piranha)",
    },
    {
        "slug": "bulat",
        "maker_slug": "ooo-trimiks-bulat-3mx",
        "reseller_slug": "ooo-pokrov",
        "distributor_slug": "ip-tsyganov-vadim-borisovich",
        "product_names": ["«Булат» в.4", "«Булат» в.3", "Детектор «Булат» v.4 (3MX)",
                           "Детектор беспилотных летательных аппаратов «Булат» v.4",
                           "Детектор «Марс»"],
        "match": ["булат", "bulat"],
        "display_name": "«Булат» / 3MX detector line",
    },
]

TYPE_LABELS = {
    "EGRUL": "EGRUL extract", "EGRULAPI": "EGRUL open-API record",
    "EGRIP": "EGRIP record", "РЕСУРС": "БФО annual-accounts filing",
    "UD": "Founding-Устав bundle", "TGMEDIA": "Telegram media",
    "CATALOG": "product catalog", "WEBCAPTURE": "site capture", "SITE": "site capture",
    "TRANSCRIPT": "transcript", "ZAKUPKI": "zakupki.gov.ru contract record",
    "DOSSIER": "third-party OSINT dossier", "PRESS": "press coverage",
}


def load_json(name):
    return json.loads((REG / name).read_text(encoding="utf-8"))


def source_type_label(path):
    stem = Path(path).name
    prefix = stem.split("_", 1)[0]
    if prefix in TYPE_LABELS:
        return TYPE_LABELS[prefix]
    return prefix.title() if prefix.isalpha() else "document"


def matches(text, keywords):
    text = (text or "").lower()
    return any(kw.lower() in text for kw in keywords)


class ProductProfileBuilder:
    def __init__(self):
        self.entities = load_json("entities.json")
        self.sources = load_json("sources.json")
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

    def battlefield_image(self, source_id, image_path=None):
        if image_path:
            url = self.docs_image_url(image_path)
            if url:
                return url, image_path
        s = self.src_by_id.get(source_id)
        if not s:
            return None, None
        raw_path = REPO / s["path"]
        md_path = str(raw_path.relative_to(REPO)) if raw_path.exists() else None
        stem = Path(s["path"]).stem
        html_url = None
        if DOCS_IMAGES.exists():
            for f in DOCS_IMAGES.glob(f"{stem}.*"):
                html_url = f"../../images/{f.name}"
                break
        return html_url, md_path

    def entity_link(self, slug, role_default=None):
        e = self.by_slug.get(slug)
        if not e:
            return {"label": slug or "(unresolved)", "profile_url": None}
        label = e.get("name_latin") or e.get("name_ru")
        return {"label": label, "profile_url": f"../{slug}.html"}

    def build_context(self, cfg):
        maker = self.by_slug[cfg["maker_slug"]]
        products = [p for p in (maker.get("products") or [])
                    if isinstance(p, dict) and p.get("name_ru") in cfg["product_names"]]

        # --- description: one paragraph per matched product entry, since a
        # flagship "product" here is often modeled as several registry
        # products[] entries (variants/sub-modules) that can each carry a
        # different source_id -- cite each paragraph on its own, not once
        # at the end of the whole block (a single trailing citation looked
        # right for a 1-product flagship but silently dropped every source
        # except the last one whenever a product had 2+ variant entries;
        # found 2026-09-15 during a peer-session review of the first batch). ---
        description = [
            {"name": p["name_ru"], "text": p["description"], "source": self.source_label(p.get("source_id"))}
            for p in products if p.get("description")
        ] or None

        # --- specs: structured specs{} dict if any product entry has one ---
        specs = []
        for p in products:
            for k, v in (p.get("specs") or {}).items():
                specs.append({"label": f"{p['name_ru']} — {k}", "value": v})

        # --- supply chain ---
        supply_chain = [{"role": "Maker", **self.entity_link(cfg["maker_slug"])}]
        if cfg.get("reseller_slug") and cfg["reseller_slug"] != cfg["maker_slug"]:
            supply_chain.append({"role": "Reseller / sister brand", **self.entity_link(cfg["reseller_slug"])})
        if cfg.get("distributor_slug"):
            supply_chain.append({"role": "Distributor / contractor", **self.entity_link(cfg["distributor_slug"])})

        # --- images: from every entity in the supply chain, matched by keyword ---
        chain_slugs = [cfg["maker_slug"]] + [cfg[k] for k in ("reseller_slug", "distributor_slug") if cfg.get(k)]
        images_gallery = []
        for slug in chain_slugs:
            ent = self.by_slug.get(slug)
            if not ent:
                continue
            for img in ent.get("images") or []:
                if matches(img.get("caption"), cfg["match"]):
                    url = self.docs_image_url(img.get("path"))
                    md_path = f"../../{img['path']}" if (REPO / "docs" / img["path"]).exists() else img.get("path")
                    images_gallery.append({
                        "url": url, "caption": img.get("caption"),
                        "source": self.source_label(img.get("source_id")), "md_path": md_path,
                    })

        # --- field testing: battlefield_evidence[] from the supply chain, matched by keyword ---
        field_testing = []
        for slug in chain_slugs:
            ent = self.by_slug.get(slug)
            if not ent:
                continue
            for b in ent.get("battlefield_evidence") or []:
                haystack = " ".join(filter(None, [b.get("text_en"), b.get("text_ru"), b.get("context")]))
                if matches(haystack, cfg["match"]):
                    html_url, md_path = self.battlefield_image(b.get("source_id"), b.get("image_path"))
                    field_testing.append({
                        "ru": b.get("text_ru"), "en": b.get("text_en"),
                        "context": b.get("context"), "as_of": b.get("as_of"),
                        "source": self.source_label(b.get("source_id")),
                        "image_url": html_url, "image_path": md_path,
                    })
        field_testing.sort(key=lambda x: x.get("as_of") or "")

        # --- handovers: government_contracts[] from the supply chain. Unlike
        # images/battlefield_evidence, a contract card rarely names the
        # product by brand in structured fields, so this is scoped to the
        # reseller/distributor entities (whose only registry-relevant
        # contracts already ARE for this product line), not keyword-matched. ---
        handovers = []
        for slug in [s for s in (cfg.get("reseller_slug"), cfg.get("distributor_slug")) if s]:
            ent = self.by_slug.get(slug)
            if not ent:
                continue
            for gc in ent.get("government_contracts") or []:
                note = gc.get("note") or gc.get("items") or ""
                if len(note) > 400:
                    note = note[:400].rstrip() + "…"
                handovers.append({
                    "customer": gc.get("customer"), "date": gc.get("date"),
                    "note": note, "source": self.source_label(gc.get("source_id")),
                })

        chips = []
        if any(self.by_slug.get(s, {}).get("sanctions") for s in chain_slugs):
            chips.append({"label": "supply-chain entity sanctioned", "cls": "t-doc"})
        if field_testing:
            chips.append({"label": f"{len(field_testing)} field-use record(s)", "cls": "t-open"})
        if handovers:
            chips.append({"label": f"{len(handovers)} government handover(s)", "cls": "t-press"})

        not_yet_sourced = []
        if not specs:
            not_yet_sourced.append("No structured specifications on file — description text above is the "
                                    "only sourced technical detail.")
        if not images_gallery:
            not_yet_sourced.append("No product-specific image confirmed on file yet.")
        if not field_testing and not handovers:
            not_yet_sourced.append("No field-testing or handover record on file yet.")

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
            "slug": cfg["slug"], "display_name": cfg["display_name"],
            "name_ru": cfg["product_names"][0] if cfg["product_names"] else None,
            "chips": chips, "supply_chain": supply_chain,
            "description": description,
            "specs": specs, "images_gallery": [i for i in images_gallery if i["url"] or i["md_path"]],
            "field_testing": field_testing, "handovers": handovers,
            "not_yet_sourced": not_yet_sourced, "sources_table": sources_table,
        }

    def render(self, cfg):
        self.cited_ids = set()
        ctx = self.build_context(cfg)
        html_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(TEMPLATES)),
            autoescape=True, trim_blocks=True, lstrip_blocks=True,
        )
        md_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(TEMPLATES)),
            autoescape=False, trim_blocks=False, lstrip_blocks=False,
        )
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        html = html_env.get_template("product_profile.html.jinja2").render(**ctx)
        (OUT_DIR / f"{cfg['slug']}.html").write_text(html, encoding="utf-8")
        md = md_env.get_template("product_profile.md.jinja2").render(**ctx)
        md = re.sub(r"\n{3,}", "\n\n", md)
        (OUT_DIR / f"{cfg['slug']}.md").write_text(md, encoding="utf-8")
        return OUT_DIR / f"{cfg['slug']}.html", OUT_DIR / f"{cfg['slug']}.md"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--slug", help="one of FLAGSHIP_PRODUCTS' own slugs (not a registry entity slug)")
    g.add_argument("--all", action="store_true")
    args = ap.parse_args()

    builder = ProductProfileBuilder()
    cfgs = FLAGSHIP_PRODUCTS if args.all else [c for c in FLAGSHIP_PRODUCTS if c["slug"] == args.slug]
    if not cfgs:
        raise SystemExit(f"no FLAGSHIP_PRODUCTS entry with slug {args.slug!r}")
    for cfg in cfgs:
        html_path, md_path = builder.render(cfg)
        print(f"{cfg['slug']}: wrote {html_path.relative_to(REPO)} + {md_path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
