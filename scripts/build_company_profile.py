#!/usr/bin/env python3
"""Render a company profile page (Markdown + HTML) from the registry.

Local file processing over data/registry/*.json — no network calls, safe to
run directly/repeatedly, like extract_registry.py/check_registry.py.

Reads entities.json/people.json/sources.json, builds a rendering context for
one entity, and fills templates/company_profile.{md,html}.jinja2 with it,
writing docs/profiles/<slug>.md and docs/profiles/<slug>.html. The HTML page
links docs/assets/profile.css (same design tokens/classes as docs/index.html)
and only embeds an <img> for files that already have a docs/images/ copy —
data/sources/ is gitignored and not part of the published site, so a photo
that only exists there gets a text citation instead of a broken <img> src.
The Markdown output is the internal working copy and references
data/sources/ paths directly, since it isn't published.

Follows STYLE_GUIDE.md's "expert-witness / forensic" register for company
profiles: Latin name primary with the Cyrillic ФИО/name shown alongside (not
hidden), legal-entity legal-form abbreviation transliterated not translated,
ИНН/ОГРН as bare digits, no internal notation (`source_id` etc.) in visible
prose — sources are cited by a short bracketed id resolved in the "Sources
cited" table, not by dumping registry field names.

Usage:
  python3 scripts/build_company_profile.py --slug ooo-skb-piranya
  python3 scripts/build_company_profile.py --inn 7300024069
  python3 scripts/build_company_profile.py --all
"""
import argparse
import json
import re
from pathlib import Path

import jinja2
from profile_text import bracket_source_ids_html, bracket_source_ids_md
import sys

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
from build_product_profile import FLAGSHIP_PRODUCTS  # noqa: E402

# name_ru -> product-profile slug, for the handful of flagship products that
# have a real docs/profiles/products/ page (see build_product_profile.py's
# own FLAGSHIP_PRODUCTS docstring for why this is a short hand-maintained
# list, not the full ~489-entry products[] corpus).
PRODUCT_PROFILE_BY_NAME = {
    name: cfg["slug"] for cfg in FLAGSHIP_PRODUCTS for name in cfg["product_names"]
}
REG = REPO / "data" / "registry"
TEMPLATES = REPO / "templates"
def _link_parts(item):
    """(href, text, note) for a web/social entry of any recorded shape.

    Entries are a bare URL string, {url}, {handle} (a Telegram @handle or
    t.me/... path) or {type, value} (an email/phone). Only something that
    really is a URL gets an href -- a handle is resolved to https://t.me/,
    an email to mailto:, anything else renders as plain text instead of a
    dead href="None" link. A scheme-less host/path gets https:// so it does
    not resolve as a relative path.
    """
    note = None
    if isinstance(item, dict):
        note = item.get("note")
        raw = item.get("url") or item.get("handle") or item.get("value") or item.get("id")
    else:
        raw = item
    if not raw:
        return None, None, note
    raw = str(raw).strip()
    if re.match(r"https?://", raw):
        return raw, raw, note
    if raw.startswith("@"):
        return "https://t.me/" + raw[1:], raw, note
    if re.match(r"^(t\.me|max\.ru|vk\.com|youtube\.com|www\.)[/\w]", raw):
        return "https://" + raw, raw, note
    if re.match(r"^[^\s@/]+@[^\s@/]+\.[a-z]{2,}$", raw, re.I):
        return "mailto:" + raw, raw, note
    return None, raw, note


OUT_DIR = REPO / "docs" / "profiles"
DOCS_IMAGES = REPO / "docs" / "images"

LEGAL_FORM_GLOSS = {
    "ООО": "limited liability company",
    "АО": "joint-stock company",
    "ПАО": "public joint-stock company",
    "ЗАО": "closed joint-stock company (pre-2015 form)",
    "АНО": "autonomous non-profit organisation",
    "Фонд": "foundation",
    "ИП": "sole proprietor",
    "НПЦ": "research and production centre",
    "НПО": "research and production association",
    "НПП": "research and production enterprise",
    "КБ": "design bureau",
    "СКБ": "special design bureau",
    "ГК": "group of companies",
    "ФГУП": "federal state unitary enterprise",
}
LEGAL_FORM_TRANSLIT = {
    "ООО": "OOO", "АО": "AO", "ПАО": "PAO", "ЗАО": "ZAO", "АНО": "ANO",
    "Фонд": "Fond", "ИП": "IP", "НПЦ": "NPTs", "НПО": "NPO", "НПП": "NPP",
    "КБ": "KB", "СКБ": "SKB", "ГК": "GK", "ФГУП": "FGUP",
}

TYPE_LABELS = {
    "EGRUL": "EGRUL extract",
    "EGRULAPI": "EGRUL open-API record",
    "EGRIP": "EGRIP (sole-proprietor registry) record",
    "РЕСУРС": "БФО annual-accounts filing",
    "UD": "Founding-Устав bundle",
    "TGMEDIA": "Telegram media",
    "CATALOG": "product catalog",
    "WEBCAPTURE": "site capture",
    "SITE": "site capture",
    "TRANSCRIPT": "transcript",
    "ATR": "АТР federal-grant registry PDF",
    "AERONEXT": "АЭРОНЕКСТ member record",
    "DOSSIER": "third-party OSINT dossier",
    "TRADEMARK": "Rospatent trademark record",
    "PATENT": "Rospatent patent record",
    "ROSPATENT": "Rospatent record",
    "ALEPH": "OCCRP Aleph screening record",
    "OPENSANCTIONS": "OpenSanctions screening record",
    "GUR": "GUR war-sanctions record",
    "COURT": "court filing",
    "PRESS": "press coverage",
    "CERT": "certificate/licence record",
    "DATASET": "bulk open-data extract",
    "ROM": "securing-measures registry record",
    "RMSP": "SME-registry record",
    "OZON": "Ozon marketplace capture",
    "HAR": "browser HAR capture",
}


def load_json(name):
    return json.loads((REG / name).read_text(encoding="utf-8"))


def ru_date(iso_date):
    """YYYY-MM-DD -> DD.MM.YYYY (Russian convention), per STYLE_GUIDE.md §2.4.
    Passes through unchanged if it doesn't match the expected ISO shape."""
    if not iso_date:
        return iso_date
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", iso_date)
    if not m:
        return iso_date
    year, month, day = m.groups()
    return f"{day}.{month}.{year}"


def source_type_label(path: str) -> str:
    stem = Path(path).name
    if stem.startswith("ul-") or stem.startswith("ip-"):
        return "EGRUL extract"
    if re.match(r"^A\d", stem):
        return "arbitration court filing"
    prefix = stem.split("_", 1)[0]
    if prefix in TYPE_LABELS:
        return TYPE_LABELS[prefix]
    return prefix.title() if prefix.isalpha() else "document"


def humanize_item(item):
    """Return (text, source_id) for a heterogeneous list-of-dict-or-str field."""
    if isinstance(item, str):
        return item, None
    if not isinstance(item, dict):
        return str(item), None
    sid = item.get("source_id")
    for key in ("text", "note", "activity", "description"):
        if item.get(key):
            return item[key], sid
    if item.get("part"):
        bits = [item["part"]]
        if item.get("marking"):
            bits.append(f"marked {item['marking']}")
        if item.get("manufacturer"):
            loc = f", {item['country']}" if item.get("country") else ""
            bits.append(f"made by {item['manufacturer']}{loc}")
        return " — ".join(bits), sid
    # generic fallback: join remaining scalar fields
    skip = {"source_id", "_meta"}
    pairs = [f"{k}: {v}" for k, v in item.items() if k not in skip and v not in (None, "", [])]
    return "; ".join(pairs) if pairs else "(no detail)", sid


class ProfileBuilder:
    def __init__(self):
        self.entities = load_json("entities.json")
        self.people = load_json("people.json")
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

    def docs_image_url(self, rel_path, for_md=False):
        """rel_path is stored relative to docs/ (e.g. 'images/foo.jpg'). Both the
        html and md outputs live in docs/profiles/, so '../' gets back to docs/."""
        if not rel_path:
            return None
        candidate = REPO / "docs" / rel_path
        if not candidate.exists():
            return None
        return f"../{rel_path}"

    def battlefield_image(self, source_id, image_path=None):
        """A battlefield_evidence entry may name its own docs/images/ photo
        directly via image_path (e.g. a letter scan or product still pulled
        separately from the cited source document) -- preferred when present.
        Otherwise fall back to the old heuristic: a battlefield_evidence
        source usually only lives in data/sources/ (gitignored, unpublished),
        so guess a docs/images/ copy by matching filename stem. Returns None
        if neither resolves, so the template shows the text citation without
        a broken <img>."""
        if image_path:
            html_url = self.docs_image_url(image_path)
            if html_url:
                return html_url, image_path
        s = self.src_by_id.get(source_id)
        if not s:
            return None, None
        raw_path = REPO / s["path"]
        md_path = str(raw_path.relative_to(REPO)) if raw_path.exists() else None
        stem = Path(s["path"]).stem
        html_url = None
        if DOCS_IMAGES.exists():
            for f in DOCS_IMAGES.glob(f"{stem}.*"):
                html_url = f"../images/{f.name}"
                break
        return html_url, md_path

    def build_context(self, e):
        slug = e["slug"]
        legal_form = e.get("legal_form")
        legal_gloss = LEGAL_FORM_GLOSS.get(legal_form)
        legal_translit = LEGAL_FORM_TRANSLIT.get(legal_form, legal_form)

        display_name = e.get("name_latin") or e.get("name_ru")
        if e.get("name_latin") and legal_translit and legal_form:
            # keep the legal-form transliterated even if name_latin already has it
            pass

        chips = []
        if e.get("sanctions"):
            chips.append({"label": "sanctioned", "cls": "t-doc"})
        if e.get("tier"):
            chips.append({"label": e["tier"], "cls": "t-open"})
        if e.get("wb_overlap") and e["wb_overlap"] not in ("none_found", None):
            chips.append({"label": f"WB: {e['wb_overlap']}", "cls": "t-press"})

        logo_url = None
        images_gallery = []
        for img in e.get("images", []):
            url = self.docs_image_url(img.get("path"))
            src = self.source_label(img.get("source_id"))
            entry = {"url": url, "caption": img.get("caption"), "source": src,
                      "md_path": f"../{img['path']}" if (REPO / 'docs' / img['path']).exists() else img.get("path")}
            images_gallery.append(entry)
            if url and "logo" in (img.get("caption") or "").lower():
                logo_url = url

        meta_grid = []
        def add_meta(label, value):
            if value not in (None, "", []):
                meta_grid.append({"label": label, "value": value, "value_plain": value})
        add_meta("Legal form", f"{legal_translit} ({legal_gloss})" if legal_gloss else legal_translit)
        add_meta("Registered", e.get("registered"))
        add_meta("Address", e.get("address"))
        add_meta("Director", e.get("director"))
        add_meta("Charter capital", f"₽{e['charter_capital']:,}" if e.get("charter_capital") else None)
        add_meta("ОКВЭД", f"{e.get('okved_code','')} — {e.get('okved_label','')}" if e.get("okved_code") else None)
        add_meta("ЦБСТ tie", (e.get("cbst_tie") or {}).get("claim") if isinstance(e.get("cbst_tie"), dict) else e.get("cbst_tie"))
        add_meta("Wildberries overlap", e.get("wb_overlap"))

        okved_note = None
        if isinstance(e.get("okved_mismatch"), dict) and e["okved_mismatch"].get("mismatch"):
            okved_note = e["okved_mismatch"].get("note")

        def history_table(field, title):
            rows = e.get(field) or []
            if not rows:
                return None
            out_rows = []
            for r in rows:
                out_rows.append({
                    "value": r.get("value"),
                    "as_of": r.get("as_of"),
                    "note": r.get("note"),
                    "source": self.source_label(r.get("source_id")),
                })
            return {"title": title, "rows": out_rows}

        history_tables = [t for t in [
            history_table("director_history", "Director"),
            history_table("founders_history", "Founders / ownership"),
            history_table("charter_capital_history", "Charter capital"),
            history_table("address_history", "Address"),
            history_table("name_history", "Legal name"),
            history_table("facility_type_history", "Facility type"),
        ] if t]

        products = [
            {"name": p.get("name_ru"), "description": p.get("description"),
             "source": self.source_label(p.get("source_id")),
             "profile_url": f"products/{PRODUCT_PROFILE_BY_NAME[p['name_ru']]}.html" if p.get("name_ru") in PRODUCT_PROFILE_BY_NAME else None}
            if isinstance(p, dict) else
            {"name": p, "description": None, "source": None, "profile_url": None}
            for p in e.get("products", [])
        ]

        financials = [{"year": f.get("year"),
                       "revenue": f"₽{f['revenue']:,.0f}" if f.get("revenue") else "—",
                       "profit": f"₽{f['profit']:,.0f}" if f.get("profit") else "—",
                       "source": self.source_label(f.get("source_id"))} for f in e.get("financials", [])]

        def simple_list(field):
            out = []
            for item in e.get(field, []):
                text, sid = humanize_item(item)
                out.append({"text": text, "source": self.source_label(sid)})
            return out

        government_contracts = simple_list("government_contracts")
        state_programs = simple_list("state_programs")
        litigation = simple_list("litigation")
        licences = simple_list("licences")
        foreign_components = simple_list("foreign_components")
        egrul_flags = [humanize_item(x)[0] for x in e.get("egrul_flags", [])]
        securing_measures = [humanize_item(x)[0] for x in e.get("securing_measures", [])]

        workforce_history = [{"count": w.get("count"), "as_of": w.get("as_of"), "note": w.get("note"),
                               "source": self.source_label(w.get("source_id"))} for w in e.get("workforce_history", [])]

        def claim_list(field):
            out = []
            for m in e.get(field, []):
                out.append({
                    "ru": m.get("text_ru"), "en": m.get("text_en"),
                    "context": m.get("context"), "as_of": m.get("as_of"),
                    "source": self.source_label(m.get("source_id")),
                })
            return out

        marketing_claims = claim_list("marketing_claims")

        battlefield_evidence = []
        for b in e.get("battlefield_evidence", []):
            html_url, md_path = self.battlefield_image(b.get("source_id"), b.get("image_path"))
            battlefield_evidence.append({
                "ru": b.get("text_ru"), "en": b.get("text_en"),
                "context": b.get("context"), "as_of": b.get("as_of"),
                "source": self.source_label(b.get("source_id")),
                "image_url": html_url, "image_path": md_path,
            })

        trademarks = []
        for tm in e.get("trademarks", []):
            classes = tm.get("goods_classes_summary") or ", ".join(tm.get("goods_classes", []) or [])
            trademarks.append({"title": tm.get("title"), "reg_number": tm.get("reg_number"),
                                "filed": tm.get("filed"), "registered": tm.get("registered"), "classes": classes})
        patents = []
        for pt in e.get("patents", []):
            inventors = ", ".join(pt.get("inventors", []) or [])
            patents.append({"title": pt.get("title"), "reg_number": pt.get("reg_number"),
                             "filed": pt.get("filed"), "inventors": inventors})

        sanctions = []
        for s in e.get("sanctions", []):
            regimes = s.get("regime")
            regimes_str = ", ".join(regimes) if isinstance(regimes, list) else (regimes or "Sanctioned")
            sanctions.append({"regimes": regimes_str, "note": None, "source": self.source_label(s.get("source_id"))})
            # note field on sanctions[] is a long internal-screening writeup, not
            # publication prose (source_id URLs, "NOT yet independently read"
            # caveats) -- deliberately not surfaced verbatim here, only the
            # regime list + a resolvable source id.

        screening_summary = []
        if e.get("gur_matches"):
            screening_summary.append(f"Listed on Ukraine's GUR war-sanctions UAV-industry registry (screened {e.get('gur_screened_at','—')}).")
        if e.get("opensanctions_matches"):
            screening_summary.append(f"{len(e['opensanctions_matches'])} OpenSanctions match(es) (screened {e.get('opensanctions_screened_at','—')}).")
        if e.get("aleph_matches"):
            screening_summary.append(f"{len(e['aleph_matches'])} OCCRP Aleph match(es) (screened {e.get('aleph_screened_at','—')}).")

        web = e.get("web") or {}
        web_group_labels = [("sites", "Website"), ("telegram", "Telegram"), ("vk", "VK"),
                             ("youtube", "YouTube"), ("marketplace_listings", "Marketplace listings"), ("other", "Other")]
        web_groups = []
        for key, label in web_group_labels:
            items = web.get(key) or []
            if items:
                links = []
                for i in items:
                    href, text, note = _link_parts(i)
                    if text:
                        links.append({"url": href, "text": text, "note": note})
                web_groups.append({"label": label, "links": links})

        # --- principals ---
        principals = []
        seen_person_slugs = set()
        for p in self.people:
            for r in p.get("roles", []):
                if not isinstance(r, dict):
                    continue
                if r.get("entity_slug") == slug and p["slug"] not in seen_person_slugs:
                    seen_person_slugs.add(p["slug"])
                    photo_url = self.docs_image_url(p.get("photo"))
                    photo_md = f"../{p['photo']}" if p.get("photo") and (REPO / 'docs' / p['photo']).exists() else None
                    roles_text = []
                    for role in p.get("roles", []):
                        if not isinstance(role, dict):
                            continue
                        if role.get("entity_slug") == slug and role.get("title"):
                            span = ""
                            if role.get("from") or role.get("to"):
                                span = f" ({role.get('from') or '?'}–{role.get('to') or 'present'})"
                            roles_text.append(f"{role['title']}{span}")
                    sanctions_chip = None
                    if p.get("sanctions"):
                        sanctions_chip = {"label": "sanctions lead", "cls": "t-open"}
                    display = p.get("name_latin") or p.get("fio_ru")
                    person_profile_path = REPO / "docs" / "profiles" / "persons" / f"{p['slug']}.html"
                    principals.append({
                        "slug": p["slug"], "display_name": display, "fio_ru": p.get("fio_ru"),
                        "profile_url": f"persons/{p['slug']}.html" if person_profile_path.exists() else None,
                        "dob": ru_date(p.get("dob")), "birthplace": p.get("birthplace"),
                        "address": p.get("address"), "inn_personal": p.get("inn_personal"),
                        "photo_url": photo_url, "photo_md_path": photo_md,
                        "roles": roles_text, "sanctions_chip": sanctions_chip,
                        "social": [dict(zip(("url", "text", "note"), _link_parts(s))) for s in p.get("social", []) if _link_parts(s)[1]],
                    })
                    break

        # --- related entities ---
        related_entities = []
        for r in e.get("related_entities", []):
            rel_slug = r.get("slug")
            label = self.by_slug[rel_slug]["name_latin"] or self.by_slug[rel_slug]["name_ru"] if rel_slug and rel_slug in self.by_slug else (rel_slug or "Unresolved entity")
            profile_url = f"{rel_slug}.html" if rel_slug and rel_slug in self.by_slug and (OUT_DIR / f"{rel_slug}.html").exists() else None
            relationship = r.get("relationship")
            if isinstance(relationship, list):
                relationship = "; ".join(relationship)
            related_entities.append({
                "label": label, "profile_url": profile_url,
                "relationship": relationship, "relationship_type": r.get("relationship_type"),
                "source": self.source_label(r.get("source_id")),
            })
        def linked_entity_entry(item, default_relationship):
            """parents[]/subsidiaries[] hold either a bare slug string (older
            scaffold shape) or a structured dict (slug/name/inn/share_percent/
            role/source_id -- the shape most entries actually use). Handle
            both rather than assuming the simpler shape, which crashed here
            on every entity using the structured form."""
            if isinstance(item, dict):
                rel_slug = item.get("slug")
                name = item.get("name")
                label = name or (self.by_slug[rel_slug]["name_latin"] or self.by_slug[rel_slug]["name_ru"] if rel_slug and rel_slug in self.by_slug else rel_slug) or "Unresolved entity"
                share = item.get("share_percent")
                relationship = item.get("relationship") or item.get("role") or default_relationship
                if share is not None:
                    relationship = f"{relationship} ({share}%)"
                return {
                    "label": label,
                    "profile_url": f"{rel_slug}.html" if rel_slug and rel_slug in self.by_slug and (OUT_DIR / f"{rel_slug}.html").exists() else None,
                    "relationship": relationship,
                    "source": self.source_label(item.get("source_id")),
                }
            return {"label": item, "profile_url": f"{item}.html" if item in self.by_slug else None, "relationship": default_relationship, "source": None}

        for p in e.get("parents", []):
            related_entities.append(linked_entity_entry(p, "Parent entity"))
        for s in e.get("subsidiaries", []):
            related_entities.append(linked_entity_entry(s, "Subsidiary"))

        open_questions = [{"text": q.get("text"), "source": self.source_label(q.get("source_id"))} for q in e.get("open_questions", [])]

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
            "slug": slug,
            "display_name": display_name,
            "name_ru": e.get("name_ru"),
            "brand": e.get("brand_latin") or e.get("brand_ru"),
            "legal_form_gloss": legal_gloss,
            "inn": e.get("inn"), "ogrn": e.get("ogrn"), "city": e.get("city"),
            "chips": chips, "logo_url": logo_url,
            "meta_grid": meta_grid, "okved_mismatch_note": okved_note,
            "history_tables": history_tables, "products": products,
            "financials": financials, "government_contracts": government_contracts,
            "state_programs": state_programs, "workforce_history": workforce_history,
            "marketing_claims": marketing_claims, "battlefield_evidence": battlefield_evidence,
            "trademarks": trademarks, "patents": patents,
            "litigation": litigation, "licences": licences, "foreign_components": foreign_components,
            "sanctions": sanctions, "screening_summary": screening_summary,
            "egrul_flags": egrul_flags, "securing_measures": securing_measures,
            "web_groups": web_groups, "images_gallery": [i for i in images_gallery if i["url"] or i["md_path"]],
            "principals": principals, "related_entities": related_entities,
            "open_questions": open_questions, "sources_table": sources_table,
        }

    def render(self, slug):
        e = self.by_slug.get(slug)
        if not e:
            raise SystemExit(f"no entity with slug {slug!r} in entities.json")
        if e.get("_merged_into"):
            raise SystemExit(
                f"{slug!r} is a tombstone (_merged_into -> {e['_merged_into']!r}) — "
                f"it is a duplicate record folded into the live entity, not a "
                f"publishable profile. Render {e['_merged_into']!r} instead, or "
                f"delete docs/profiles/{slug}.{{html,md}} if a stale page for it "
                f"already exists.")
        self.cited_ids = set()
        ctx = self.build_context(e)

        # HTML is whitespace-insensitive, so trim/lstrip_blocks keeps the
        # source tidy. Markdown structure (blank line before a heading,
        # one list item per line) depends on real newlines, and trim_blocks
        # also eats the newline after an *inline* {% endif %} mid-line (not
        # just one that starts a line) -- so the md template uses an
        # environment with both off, and any resulting extra blank lines
        # get collapsed afterward.
        html_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(TEMPLATES)),
            autoescape=True, trim_blocks=True, lstrip_blocks=True,
        )
        md_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(TEMPLATES)),
            autoescape=False, trim_blocks=False, lstrip_blocks=False,
        )

        OUT_DIR.mkdir(parents=True, exist_ok=True)
        html = html_env.get_template("company_profile.html.jinja2").render(**ctx)
        html = bracket_source_ids_html(html, self.src_by_id)
        (OUT_DIR / f"{slug}.html").write_text(html, encoding="utf-8")
        md = md_env.get_template("company_profile.md.jinja2").render(**ctx)
        md = bracket_source_ids_md(md)
        md = re.sub(r"\n{3,}", "\n\n", md)
        (OUT_DIR / f"{slug}.md").write_text(md, encoding="utf-8")
        return OUT_DIR / f"{slug}.html", OUT_DIR / f"{slug}.md"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--slug")
    g.add_argument("--inn")
    g.add_argument("--all", action="store_true")
    args = ap.parse_args()

    builder = ProfileBuilder()
    if args.all:
        slugs = [e["slug"] for e in builder.entities
                 if e.get("tier") not in ("adjacent",) and not e.get("_merged_into")]
    elif args.inn:
        matches = [e["slug"] for e in builder.entities
                   if e.get("inn") == args.inn and not e.get("_merged_into")]
        if not matches:
            raise SystemExit(f"no live entity with ИНН {args.inn} "
                              f"(it may belong to a tombstoned duplicate record)")
        slugs = matches
    else:
        slugs = [args.slug]

    for slug in slugs:
        html_path, md_path = builder.render(slug)
        print(f"{slug}: wrote {html_path.relative_to(REPO)} + {md_path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
