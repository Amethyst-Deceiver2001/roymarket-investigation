#!/usr/bin/env python3
"""Chain view: one product's path from ЦБСТ to the end user, generated from the registry.

    python3 exhibits/build_chain_view.py bulat            # -> exhibits/chain_bulat.html

Reader-facing: no slugs, no source ids, no file names, no field names on the page. Each
claim carries a numbered note that resolves to a plain description of the document (a
Telegram post, a procurement record, a registry extract) with a public link where one
exists. Names link to the published profile pages, where the identifiers live.

Layout: ЦБСТ and programmes | maker | product, then one row per sale channel or donor with
its buyers or recipients beside it. A line's style is the grade of its evidence
(STYLE_GUIDE §5.6). Lines that would carry no distinguishing information are not drawn: the
product feeds the channel rows through one line, and each row's own grade is on its tick.

Selection rules (same as the page's method note):
- channels: the product's listings[] that have an archived source, entities with a
  sells_for edge to the maker, and entities whose state contract names the product in its
  subject_ru / items;
- buyers: those contracts; recipients: the product's deliveries[], grouped by donor;
- a ЦБСТ link: cbst_tie (t-doc / t-open / press), memberships[], participations[], a
  delivery's co_donors.
Local file processing only.
"""
import argparse
import datetime as dt
import html
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REG = REPO / "data" / "registry"
SRC_DIR = REPO / "data" / "sources"
PAGES = "https://amethyst-deceiver2001.github.io/roymarket-investigation/"
sys.path.insert(0, str(REPO / "scripts"))
from graph_contract import source_grade  # noqa: E402
import deliveries as dl  # noqa: E402
from source_citation import cite, reader_terms  # noqa: E402
from display_helpers import (NAME_JS, design_head, sanction_regimes, display_name, figure_html, kind_icon, latin_display, latin_text,  # noqa: E402
                             latinize_gloss, load_media, media_about, name_html, orig_line, person_names, popup_originals, publish_copy, quote_html, translation,
                             reader_grade, ru_date)

CBST = "ano-tsbst-centre-for-unmanned-systems-technologies"
# card kind -> (icon, extra class)
KIND_MARK = {"hub": ("company", " hub"), "programme": ("program", ""), "event": ("event", ""),
             "maker": ("company", ""), "product": ("product", ""), "channel": ("company", ""),
             "storefront": ("storefront", ""), "donor": ("company", ""), "buyer": ("buyer", ""),
             "field": ("unit", ""), "absent": ("storefront", " absent")}
PROV_GROUP = {"self": "Published by the company", "platform": "From a marketplace listing",
              "third_party": "Posted by buyers and others", "press": "Press", "counterparty": "From the counterparty"}
ROLE_EN = {"exhibitor": "Showed «{p}» at the event", "resident": "Resident", "finalist": "Finalist",
           "co-organiser": "Co-organised by", "organiser": "Organised by"}



_REC = [0]   # numbers the recipient popovers so every id on a page is unique


def recipient_html(text: str | None, en: str | None = None) -> str:
    """The donor's wording in guillemets (STYLE_GUIDE §5.1: never let «спецоперация» and the like
    read as our own words); our English note after it, outside the quote."""
    text = (text or "").strip()
    m = re.match(r"^(.*?)(\s*[(;]\s*[A-Za-z].*)?$", text)
    words, note = (m.group(1).strip(), (m.group(2) or "").strip()) if m else (text, "")
    if not words:
        return esc(text)
    words = re.sub(r"«([^«»]*)»", "„\\1“", words)  # inner quotes: Russian „…“ inside «…»
    if en:   # our English gloss first; the donor's own words are under RU, verbatim (STYLE_GUIDE §2.1, §3.1)
        _REC[0] += 1
        return name_html(en, f"«{words}»", key=f"rec-{_REC[0]}", what="The donor's own wording of")
    return f'<span lang="ru">«{esc(words)}»</span>' + (f" {esc(note)}" if note else "")

def load(name):
    d = json.loads((REG / name).read_text())
    if isinstance(d, dict):
        for k in ("entities", "products", "programs", "sources"):
            if k in d:
                d = d[k]
                break
    return list(d.values()) if isinstance(d, dict) else d


def esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def fold(s):
    return (s or "").lower().replace("ё", "е")


def money(v):
    if v is None:
        return ""
    if v >= 1e9:
        return f"₽{v / 1e9:.2f}bn"
    if v >= 1e6:
        return f"₽{v / 1e6:.1f}m"
    return "₽" + f"{v:,.0f}".replace(",", " ")


def cap(s):
    return (s[:1].upper() + s[1:]) if s else ""


def en_text(s):
    """English for a mixed line from the record ("dealer shop, Горбушка (Москва)"): a Cyrillic phrase with an entry in
    name_translations.json (a place, a state body) takes its English name; any other is transliterated."""
    def one(m):
        tr = translation(m.group(0))
        return tr["en"] if tr else latin_text(m.group(0))
    return re.sub(r"[А-Яа-яЁё][А-Яа-яЁё\- ]*[А-Яа-яЁё]|[А-Яа-яЁё]", one, s or "")


def split_name(e):
    """'АНО «ЦБСТ» | Centre for …' -> ('АНО «ЦБСТ»', 'Centre for …'). Our own bracketed notes are dropped."""
    n = display_name(e)
    return n["legal"] or n["head"] if not n["legal"] else n["legal"], n["gloss"]


def describe_source(s):
    """A reader-facing description and public link for one sources.json record. Both are derived once per
    source by scripts/source_citation.py (B4) and stored on the record; a page never builds its own."""
    title = s.get("title") or ""
    if not title or title.startswith("Archived document"):   # a rule added since the Mac last catalogued it
        title = cite(s, None)[0]
    return reader_terms(title), s.get("public_url")


class Chain:
    def __init__(self, product_slug):
        self.ents = {e["slug"]: e for e in load("entities.json")}
        self.people = {x["slug"]: x for x in load("people.json")}
        self.untranslated = []   # state bodies with no English name yet (name_translations.json)
        self.programs = {p["slug"]: p for p in load("programs.json")}
        self.src = {s["id"]: s for s in load("sources.json")}
        prods = {p["slug"]: p for p in dl.load_products()}
        if product_slug not in prods:
            sys.exit(f"no product {product_slug!r} in products.json")
        self.p = prods[product_slug]
        self.pq = self.p["name_ru"]                       # «Булат»
        self.pq_en = latin_text(self.pq)                  # «Bulat»
        self.pname = re.sub(r"[«»]", "", self.pq).strip()  # Булат
        self.maker = self.ents[self.p["maker"]]
        self.notes = []          # source ids in order of first citation
        self.top = {c: [] for c in "ABC"}
        self.rows = []           # (seller card html, [buyer card html])
        self.edges = []
        self.limits = []
        self.media = load_media()
        self.media_files = []    # (published name, local path) for the artifact publish
        self.img_dir = None      # set by render(): where publish copies go
        self.templates = {}      # media id -> full evidence figure, opened from a thumbnail
        self.figures = []        # "How many": (figure, what it counts, refs html), each from a document

    # -- notation ------------------------------------------------------------------------
    def ref(self, *sids):
        nums = []
        for s in sids:
            if not s or s not in self.src:
                continue
            s = self.src[s].get("duplicate_of") or s
            desc = describe_source(self.src[s])
            if desc not in self.notes:
                self.notes.append(desc)
            nums.append(self.notes.index(desc) + 1)
        if not nums:
            return ""
        return "<sup class=\"rm-ref\">" + ",".join(f'<a href="#n{n}">{n}</a>' for n in sorted(set(nums))) + "</sup>"

    def name(self, e, sub=True):
        """A card's name block, Latin first (STYLE_GUIDE §2.2-2.3): the documented brand or the transliterated
        legal name, then the registered Cyrillic name beneath it. A sole trader leads with the person's name."""
        n = display_name(e)
        legal = n["legal"] or n["head"]
        if legal.startswith("ИП "):
            pn = person_names(legal, (self.people.get(e.get("person") or "") or {}).get("name_latin"))
            return (f'{esc(pn["first"])}<small>Sole trader (IP)</small>'
                    f'<small class="cyr" lang="ru">{esc(legal)}</small>')
        brand = next((b for b in e.get("brands") or [] if b.get("primary")), None)
        out = esc(latin_text(n["head"]) if brand else n["latin"])
        if brand:
            out += f'<small class="lat" lang="ru-Latn">{esc(n["latin"])}{self.ref(brand.get("source_id"))}</small>'
        out += f'<small class="cyr" lang="ru">{esc(legal)}</small>'
        if sub and n["gloss"] and not n["legal"]:
            out += f"<small>{esc(n['gloss'])}</small>"
        return out

    def en(self, e, pop=False):
        """The name in English prose: brand or transliterated legal name; pop=True attaches the Cyrillic original."""
        n = display_name(e)
        legal = n["legal"] or n["head"]
        if legal.startswith("ИП "):
            pn = person_names(legal)
            return name_html(pn["first"], pn["fio"], key=e["slug"]) if pop else esc(pn["first"])
        vis = latin_text(n["head"]) if n["legal"] else n["latin"]
        return name_html(vis, legal, key=e["slug"]) if pop else esc(vis)

    def body_name(self, s):
        """A co-donor or other named body as the record writes it: an entity slug, a party, or an acronym."""
        if s in self.ents:
            return self.en(self.ents[s])
        tr = translation(s)
        return esc(tr["en"] if tr else latin_text(s))

    def sanctions(self, e):
        regs = sanction_regimes(e.get("sanctions"))
        seen, sids = [lab for lab, _ in regs], [x for _, ss in regs for x in ss]
        from build_company_page import list_mark   # noqa: E402  (dated "no Western listing" line)
        mark = list_mark(e, self.ref)
        if not seen:
            return mark
        return (f'<p class="row sanc"><span class="rm-sanction">Sanctioned <b>{esc(", ".join(seen))}</b></span>'
                f'{self.ref(*sids)}</p>' + mark)

    def card(self, cid, kind, label, title, body, slug=None):
        icon, extra = KIND_MARK.get(kind, ("", ""))
        return (f'<article class="rm-card k-{kind}{extra}" id="{cid}"><header><span class="rm-kind">'
                f'{kind_icon(icon)}{esc(label)}</span>{self.logo(slug)}</header><h3 class="rm-name">{title}</h3>{body}</article>')

    def logo(self, slug):
        """The entity's own logo, from a media record of genre logo; nothing when none is on file."""
        if not slug:
            return ""
        m = next((x for x in media_about(self.media, {("entity", slug)}) if x.get("genre") == "logo"), None)
        src = self.img(m) if m else None
        dark = " on-dark" if m and m.get("logo_ground") == "dark" else ""
        return f'<img class="rm-logo{dark}" src="{esc(src)}" alt="Logo of {self.en(self.ents[slug])}">' if src else ""

    def contract_lines(self, gc):
        """The contract's lines for this product (B2): quantity × version at the unit price, as the contract prints them."""
        vname = {v.get("slug"): v.get("name_ru") for v in self.p.get("versions") or []}
        out = []
        for cp in gc.get("products") or []:
            if cp.get("product") != self.p["slug"]:
                continue
            what = esc(latin_text(vname.get(cp.get("version")) or self.pq))
            if cp.get("item_ru") and "антенн" in cp["item_ru"]:
                what += " with remote antennas"
            qty = f'{cp["qty"]} × ' if cp.get("qty") else ""
            price = f' at {money(cp["unit_price_rub"])}' if cp.get("unit_price_rub") else ""
            if not qty and not price:
                what += ", quantity not stated"
            out.append(f'<li>{qty}{what}{price}{self.ref(cp.get("source_id"))}</li>')
        return f'<ul class="rec">{"".join(out)}</ul>' if out else ""

    def edge(self, a, b, grade, label, bus=False):
        self.edges.append({"from": a, "to": b, "grade": grade, "label": label, "bus": bus})

    # -- build ---------------------------------------------------------------------------
    def build(self):
        p, m = self.p, self.maker
        maker_left = self.en(m)

        # A: ЦБСТ, programmes, events
        c = self.ents[CBST]
        self.top["A"].append(self.card("hub", "hub", "Hub", self.name(c), self.sanctions(c), slug=CBST))
        tie = m.get("cbst_tie") or {}
        g = reader_grade(tie.get("confidence")) if tie.get("confidence") in ("t-doc", "t-open", "press") else None
        if g:
            self.edge("hub", "maker", g, "Link to TsBST")
        for mem in m.get("memberships") or []:
            prog = self.programs.get(mem["program"], {})
            cid = "prog-" + mem["program"]
            self.top["A"].append(self.card(cid, "programme", "Programme", esc(latin_text(prog.get("name_ru"))),
                                           f'<p class="row">{esc(ROLE_EN.get(mem.get("role"), mem.get("role")))}, '
                                           f'{ru_date(mem.get("as_of"))}{self.ref(mem.get("source_id"))}</p>'))
            self.edge(cid, "maker", reader_grade(mem.get("basis")), "Member")
        if not m.get("memberships"):
            self.limits.append(f"No document records {maker_left} as a formal member of a TsBST programme. "
                               "Its link to TsBST rests on the posts and statements cited on its card.")
        for part in m.get("participations") or []:
            ev = self.programs.get(part["event"], {})
            cid = "ev-" + part["event"]
            orgs = "".join(
                f'<p class="note">{esc(ROLE_EN.get(o.get("role"), "Organised by"))} '
                f'{self.en(self.ents[o["slug"]]) if o.get("slug") in self.ents else ""}'
                f'{self.ref(o.get("source_id"))}</p>'
                for o in ev.get("organisers") or [] if isinstance(o, dict))
            role = ROLE_EN.get(part.get("role"), part.get("role") or "").replace("{p}", latin_text(self.pname))
            self.top["A"].append(self.card(cid, "event", "Event", esc(latin_text(ev.get("name_ru"))),
                                           f'<p class="row">{esc(role)}, {ru_date(part.get("as_of"))}'
                                           f'{self.ref(part.get("source_id"))}</p>{orgs}'))
            self.edge(cid, "maker", reader_grade(part.get("basis")), "Exhibitor")

        # B: maker
        rows = [self.sanctions(m)]
        fin = sorted((f for f in m.get("financials") or [] if f.get("revenue")), key=lambda f: str(f["year"]))
        if fin:
            rows.append(f'<p class="row">Revenue {fin[-1]["year"]}: {money(fin[-1]["revenue"])}{self.ref(fin[-1].get("source_id"))}</p>')
        restricted = [h for h in m.get("director_history") or [] if "restricted" in fold(h.get("value"))]
        if restricted:
            rows.append(f'<p class="row warn">Owners and director closed to public view in the company register '
                        f'since {ru_date(restricted[0]["as_of"])}{self.ref(restricted[0].get("source_id"))}</p>')
        if g:
            rows.append(f'<p class="row">Linked to TsBST{self.ref(tie.get("source_id"))}</p>')
        if m.get("inn"):   # the identifier tells namesakes apart (two Липецк ООО НПО «Киловатт»)
            rows.append(f'<p class="row"><span class="rm-id">INN {esc(m["inn"])}</span></p>')
        from build_company_page import COMPANY_PAGES   # noqa: E402  (company file preview links)
        if m["slug"] in COMPANY_PAGES:
            rows.append(f'<p class="row"><a href="{esc(COMPANY_PAGES[m["slug"]])}" target="_blank" rel="noopener">Company file ↗</a></p>')
        self.top["B"].append(self.card("maker", "maker", "Maker", self.name(m), "".join(rows), slug=m["slug"]))

        # C: product
        # model names without the repeated product name: «Капюшон» К-8М -> К-8М
        vlist = [re.sub(r"^" + re.escape(self.pq) + r"\s*", "", v["name_ru"]) or v["name_ru"] for v in p.get("versions") or []]
        vers = (f"{len(vlist)} models: " if len(vlist) > 5 else "Versions: ") + ", ".join(esc(latin_text(v)) for v in vlist)
        acc = len(p.get("accessories") or [])
        vsrc = [v.get("source_id") for v in p.get("versions") or []]
        self.top["C"].append(self.card(
            "product", "product", "Product", f'{esc(self.pq_en)}<small class="cyr" lang="ru">{esc(self.pq)}</small>',
            self.thumb() + f'<p class="row">{esc(cap(p.get("category")))}</p>'
            f'<p class="row">{vers}{self.ref(*vsrc)}'
            + (f'; {acc} add-on module{"s" if acc > 1 else ""}' if acc else "") + "</p>"))
        self.edge("maker", "product", "doc" if any(vsrc) else "open", "Makes")

        # Rows: channels
        row_of = {}  # entity slug -> index in self.rows

        def add_row(key, slug, html_card, grade, label):
            self.rows.append({"id": key, "card": html_card, "buyers": []})
            self.edge("product", key, grade, label, bus=True)
            if slug:
                row_of[slug] = len(self.rows) - 1

        def extra(slug, html_bit):
            i = row_of[slug]
            self.rows[i]["card"] = self.rows[i]["card"].replace("</article>", html_bit + "</article>")

        fronts = {}
        dropped = 0
        for li in p.get("listings") or []:
            if not li.get("source_id"):
                dropped += 1
                continue
            fronts.setdefault(li["seller"].get("storefront") or li["channel"], []).append(li)
        if dropped:
            self.limits.append(f"{dropped} further marketplace listing{'s' if dropped > 1 else ''} without an "
                               "archived copy of the page " + ("are" if dropped > 1 else "is") + " left out.")
        for i, (front, lis) in enumerate(fronts.items()):
            ent = lis[0]["seller"].get("entity")
            e = self.ents.get(ent) if ent else None
            shop = re.sub(r"\s*\(.*\)$", "", front)
            title = self.name(e) if e else f'{esc(en_text(shop))}<small class="cyr" lang="ru">{esc(shop)}</small>'
            when = ", ".join(sorted({ru_date(li["as_of"]) for li in lis}))
            body = (f'<p class="row">{esc(en_text(lis[0]["channel"]))}</p>'
                    f'<p class="row">Listed {when}{self.ref(*[li["source_id"] for li in lis])}</p>'
                    + (self.sanctions(e) if e and ent != m["slug"] else "")
                    + self.strip(media_about(self.media, {("listing", li["id"]) for li in lis}), label="Pictures of this listing"))
            add_row(f"ch-{i}", ent, self.card(f"ch-{i}", "channel" if e else "storefront", "Sells", title, body, slug=ent),
                    "doc" if all(li.get("basis") == "doc" for li in lis) else "rep", "Listed")

        for e in self.ents.values():
            for sf in e.get("sells_for") or []:
                if sf.get("slug") != m["slug"]:
                    continue
                prods = sf.get("products")
                if prods and not any(fold(self.pname) in fold(x) for x in prods):
                    continue
                if sf.get("authorised") == "yes":
                    txt = "Named as a dealer on the maker's website"
                elif sf.get("authorised") == "no":
                    txt = "Not authorised by the maker"
                else:
                    txt = "Not on the maker's dealer list"
                line = f'<p class="row">{txt}{self.ref(sf.get("source_id"))}</p>'
                if e["slug"] in row_of:
                    extra(e["slug"], line)
                else:
                    cid = f"sf-{len(self.rows)}"
                    add_row(cid, e["slug"], self.card(cid, "channel", "Sells", self.name(e), line + self.sanctions(e), slug=e["slug"]),
                            reader_grade(sf.get("basis")), "Sells")

        contracts = []
        for e in self.ents.values():
            for gc in e.get("government_contracts") or []:
                # B2: a contract's own products[] decides; the text match only covers contracts not yet linked.
                if gc.get("products") is not None:
                    if any(cp.get("product") == self.p["slug"] for cp in gc["products"]):
                        contracts.append((e, gc))
                elif fold(self.pname) in fold((gc.get("subject_ru") or "") + " " + (gc.get("items") or "")):
                    contracts.append((e, gc))
        for e, gc in contracts:
            if e["slug"] not in row_of:
                cid = f"gc-{len(self.rows)}"
                add_row(cid, e["slug"], self.card(cid, "channel", "Supplies the state", self.name(e),
                                                  f'<p class="row">State supplier of {esc(self.pq_en)}</p>' + self.sanctions(e), slug=e["slug"]),
                        "doc", "Supplies")
        for slug, i in list(row_of.items()):
            e = self.ents[slug]
            hist = (e.get("founders_history") or []) + (e.get("director_history") or [])
            for other, j in row_of.items():
                o = self.ents[other]
                if other == slug or not o["name_ru"].startswith("ИП "):
                    continue
                person = o["name_ru"][3:]
                hit = next((h for h in hist if fold(person) in fold(h.get("value"))), None)
                if hit:   # first mention of a person: Latin name with the full ФИО beside it (STYLE_GUIDE §2.2)
                    pn = person_names(person)
                    extra(slug, f'<p class="row person">Owned and run by {esc(pn["first"])} (<span lang="ru">{esc(pn["fio"])}</span>), '
                                f'who also trades as a sole trader (<a href="#{self.rows[j]["id"]}">IP</a>){self.ref(hit.get("source_id"))}</p>')
        for k, (e, gc) in enumerate(sorted(contracts, key=lambda x: str(x[1].get("date")))):
            cid = f"buy-{k}"
            customer = re.sub(r"\s*\((?:ИНН \d+|[^)]*[a-z][^)]*)\)", "", gc.get("customer") or "").strip()  # drop the ИНН and our notes
            tr = translation(customer)
            if not tr:
                self.untranslated.append(customer)
            subj = gc.get("subject_ru")
            self.rows[row_of[e["slug"]]]["buyers"].append(self.card(
                cid, "buyer", "State buyer",   # a state body is translated; its official name and transliteration beneath (§2.3a)
                f'{esc(tr["en"] if tr else latin_text(customer))}<small class="cyr" lang="ru">{esc(customer)}</small>'
                f'<small class="lat" lang="ru-Latn">{esc(latin_text(customer))}</small>',
                f'<p class="row"><b>{money(gc.get("value_rub"))}</b>, '
                f'{esc(ru_date(gc.get("date")) if gc.get("date") else "")}{self.ref(gc.get("source_id"))}</p>'
                + self.contract_lines(gc)
                + (f'<p class="note">Subject line: {orig_line(subj, "subj-" + cid)}</p>' if subj else "")))
            self.edge(self.rows[row_of[e["slug"]]]["id"], cid, "doc", "State contract")
        lines = [(cp, gc) for _, gc in contracts for cp in gc.get("products") or [] if cp.get("product") == p["slug"]]
        qty = sum(cp["qty"] for cp, _ in lines if cp.get("qty"))
        no_qty = {id(gc) for cp, gc in lines if not cp.get("qty")}
        if qty:
            self.figures.append((f"{qty}+", f"bought under {len(contracts)} state contracts"
                                 + (f" ({len(no_qty)} gives no quantity)" if no_qty else ""),
                                 self.ref(*[cp.get("source_id") for cp, _ in lines if cp.get("qty")])))
        prices = sorted(cp["unit_price_rub"] for cp, _ in lines if cp.get("unit_price_rub"))
        if prices:
            self.figures.append((money(prices[0]) + (f"–{money(prices[-1])[1:]}" if prices[-1] != prices[0] else ""),
                                 "per unit in those contracts",
                                 self.ref(*[cp.get("source_id") for cp, _ in lines if cp.get("unit_price_rub")])))

        # Rows: donors and the recipients they report
        donors = {}
        for d in p.get("deliveries") or []:
            donors.setdefault(d["donor"], []).append(d)
        for slug, ds in donors.items():
            e = self.ents.get(slug)
            ds = sorted(ds, key=lambda d: d["date"])
            cid = f"don-{len(self.rows)}"
            dtie = (e or {}).get("cbst_tie") or {}
            co = sorted({c for d in ds for c in d.get("co_donors") or []})
            ffin = next((f for f in sorted((e or {}).get("financials") or [], key=lambda f: str(f.get("year")), reverse=True)
                         if f.get("funds_received")), None)
            body = (f'<p class="row">Reports handing over {esc(self.pq_en)}</p>'
                    + (f'<p class="row">Named alongside it: {", ".join(self.body_name(c) for c in co)}</p>' if co else "")
                    + (f'<p class="row">Linked to TsBST{self.ref(dtie.get("source_id"))}</p>' if dtie.get("confidence") in ("t-doc", "t-open", "press") else "")
                    + (f'<p class="row">Donations received in {ffin["year"]}: {money(ffin["funds_received"])}'
                       f'{self.ref(ffin.get("source_id"))}</p>' if ffin else "")
                    + (self.sanctions(e) if e else ""))
            # B3: the donor's own accounts may show it bought the product; the seller can still be unknown.
            stock = next((c for c in p.get("claims") or [] if c.get("metric") == "donor_stock" and c.get("entity") == slug), None)
            sn = re.search(r"Кол\. (\d+)", stock["text_ru"]) if stock else None
            if sn:
                self.figures.append((sn.group(1), f"held by {self.en(e)} on {ru_date(stock['as_of'])}, by its audited accounts",
                                     self.ref(stock["source_id"])))
            if stock:
                n = re.search(r"Кол\. (\d+)", stock["text_ru"])
                body = (f'<p class="row">Held {n.group(1) if n else "a stock of"} {esc(self.pq_en)} on {ru_date(stock["as_of"])}, '
                        f'bought for transfer to units, by its audited accounts{self.ref(stock["source_id"])}</p>') + body
            self.rows.append({"id": cid, "card": self.card(cid, "donor", "Donates", self.name(e) if e else esc(slug), body,
                                                           slug=slug if e else None),
                              "buyers": []})
            if stock:
                self.edge("product", cid, source_grade(self.src.get(stock["source_id"])),
                          "Bought by the donor (its accounts); the seller is not named", bus=True)
            else:
                self.edge("product", cid, "open", "How the donor obtained it is not documented", bus=True)
            rid = f"rec-{len(self.rows)}"
            items = "".join(
                f'<li><time>{ru_date(d["date"])}</time> {recipient_html(d.get("recipient"), d.get("recipient_en"))}'
                + (f' <span class="co">with {", ".join(self.body_name(c) for c in d["co_donors"])}</span>' if d.get("co_donors") else "")
                + f'{self.ref(d.get("source_id"), *(d.get("other_source_ids") or []))}'
                + (self.strip(media_about(self.media, {("delivery", d["id"])}), label="") if d.get("id") else "")
                + '</li>' for d in ds)
            self.rows[-1]["buyers"].append(self.card(
                rid, "field", "Recipients",
                f'{len(ds)} handovers <small>{ru_date(ds[0]["date"])} – {ru_date(ds[-1]["date"])}</small>',
                f'<p class="note">As reported by the donor on its own Telegram channel. Each recipient is glossed in English, with the donor\'s own words in «».</p>'
                + self.timeline(ds) + f'<ul class="rec">{items}</ul>'))
            self.edge(cid, rid, "rep", "Reported by the donor")
            dname = self.en(e) if e else esc(slug)
            if stock:
                self.limits.append(f"{dname}'s accounts show it bought {esc(self.pq_en)} for transfer to units, "
                                   "but name no seller. Who sold them to it is not documented.")
            else:
                self.limits.append(f"No document shows where {dname} obtained {esc(self.pq_en)}. "
                                   "The line from the product to the donor is dotted for that reason.")
            self.limits.append(f"The {len(ds)} handovers are {dname}'s own reports. None is confirmed by the "
                               "receiving unit or an independent source, and the post date is not always the handover date.")

        # РОЙ.МАРКЕТ: shown as absent only when a document speaks to it (the maker's own distribution statement).
        # Without one, nobody has checked, and an "absent" card would assert what was never looked for.
        claim = next((cl for cl in p.get("claims") or [] if cl.get("metric") == "distribution"), None)
        if claim and not any("рой" in fold(li["channel"]) or "roimarket" in fold(li.get("url")) for li in p.get("listings") or []):
            body = ('<p class="row">No listing found.</p>'
                    + quote_html(claim["text_ru"], self.claim_en(claim), "", key="q-distribution") +
                    f'<p class="note">{esc(cap(claim.get("asserted_by"))) if claim.get("asserted_by") else maker_left}, {ru_date(claim.get("as_of"))}'
                    f'{self.ref(claim.get("source_id"))}</p>')
            self.rows.append({"id": "roymarket", "card": self.card("roymarket", "absent", "Not sold here", f'{esc(latin_display("РОЙ.МАРКЕТ"))}<small class="cyr" lang="ru">РОЙ.МАРКЕТ</small>', body),
                              "buyers": []})

    def claim_en(self, claim):
        """Our English for a product claim: the maker's marketing_claim with the same Russian text, else the Russian."""
        mk = self.ents.get(self.p.get("maker")) or {}
        m = next((c for c in mk.get("marketing_claims") or [] if c.get("text_ru") == claim.get("text_ru") and c.get("text_en")), None)
        return latinize_gloss(m["text_en"]) if m else latinize_gloss(claim["text_ru"])

    # -- media (track V) -------------------------------------------------------------------
    def media_refs(self):
        p = self.p
        refs = {("product", p["slug"])}
        refs |= {("version", v["slug"]) for v in p.get("versions") or []}
        refs |= {("listing", l_["id"]) for l_ in p.get("listings") or []}
        refs |= {("delivery", d["id"]) for d in p.get("deliveries") or [] if d.get("id")}
        return refs

    def img(self, m):
        name = publish_copy(m, self.img_dir)
        if not name:
            return None
        rel = f"images/media/{name}"
        if (rel, self.img_dir / name) not in self.media_files:
            self.media_files.append((rel, self.img_dir / name))
        return rel

    def who(self, m):
        for a_ in m.get("about") or []:
            if a_["type"] == "entity" and a_["id"] in self.ents:
                return self.en(self.ents[a_["id"]])
        return self.en(self.maker)

    def thumb(self):
        """The product card's picture (a self-published photo or screenshot of the product) and the
        strip of its other pictures that are not tied to one listing or one handover."""
        p = self.p
        own = {("product", p["slug"])} | {("version", v["slug"]) for v in p.get("versions") or []}
        ms = [m for m in media_about(self.media, own) if m.get("genre") != "logo"
              and not any(a_["type"] in ("listing", "delivery") for a_ in m.get("about") or [])]
        main = next((m for m in ms if m.get("asserted_by") == "self" and m.get("kind") in ("photo", "screenshot")
                     and m.get("genre") == "marketing" and self.img(m)), None)
        if main is None:   # fall back to a dealer's own product picture tied to a listing
            main = next((m for m in media_about(self.media, own) if m.get("asserted_by") == "self"
                         and m.get("genre") == "marketing" and m.get("kind") in ("photo", "screenshot") and self.img(m)), None)
        out = ""
        if main:
            self.template(main)
            out += (f'<button class="rm-thumb-main" type="button" data-fig="fig-{main["id"]}" aria-label="{esc(main.get("shows_en") or latinize_gloss(main["shows"]))}">'
                    f'<img class="rm-thumb" src="{esc(self.img(main))}" alt=""></button>'
                    f'<p class="note">Picture: {esc(self.who(main))}{self.ref(main.get("source_id"))}</p>')
        return out + self.strip([m for m in ms if m is not main], by_provenance=True)

    def template(self, m):
        if m["id"] not in self.templates:
            v = m.get("video")
            note = (f"Video. Original on {v['original']}." + ("" if v.get("archived") else " Not archived.")) if v else ""
            self.templates[m["id"]] = figure_html(m, self.img(m), self.who(m), self.ref(m.get("source_id")), note)

    def strip(self, ms, label=None, by_provenance=False):
        """Thumbnails for the pictures that support one card or one line; each opens its full figure."""
        ms = [m for m in sorted(ms, key=lambda m: (m.get("published") or "", m["id"])) if self.img(m)]
        if not ms:
            return ""
        groups = {}
        for m in ms:
            if label is not None:
                key = label
            elif by_provenance:
                key = f"Published by {self.who(m)}" if m["asserted_by"] == "self" else PROV_GROUP.get(m["asserted_by"], "Pictures")
            else:
                key = "Pictures"
            groups.setdefault(key, []).append(m)
        out = []
        for key, grp in groups.items():
            btns = []
            for m in grp:
                self.template(m)
                btns.append(f'<button class="rm-thumb-btn" type="button" data-fig="fig-{m["id"]}" '
                            f'aria-label="{esc(m.get("shows_en") or latinize_gloss(m["shows"]))}"><img src="{esc(self.img(m))}" alt=""></button>')
            lbl = f'<span class="lbl">{esc(key)} ({len(grp)})</span>' if key else ""
            out.append(f'<div class="rm-thumbs">{lbl}{"".join(btns)}</div>')
        return "".join(out)

    def timeline(self, ds):
        dates = [dt.date.fromisoformat(d["date"]) for d in ds]
        lo = dt.date(dates[0].year, dates[0].month, 1)
        hi = dt.date(dates[-1].year + (dates[-1].month == 12), dates[-1].month % 12 + 1, 1)
        span = (hi - lo).days
        W, H, pad = 320, 44, 8

        def x(d):
            return pad + (W - 2 * pad) * (d - lo).days / span
        out = [f'<svg class="tl" viewBox="0 0 {W} {H}" role="img" aria-label="Handover dates">',
               f'<line x1="{pad}" x2="{W - pad}" y1="18" y2="18" class="axis"/>']
        cur = lo
        while cur <= hi:
            if cur.month in (1, 7):
                out.append(f'<line x1="{x(cur):.1f}" x2="{x(cur):.1f}" y1="14" y2="22" class="tick"/>'
                           f'<text x="{x(cur):.1f}" y="{H - 6}" text-anchor="middle">{cur.strftime("%m.%Y")}</text>')
            cur = dt.date(cur.year + (cur.month == 12), cur.month % 12 + 1, 1)
        for d, dd in zip(ds, dates):
            hub = "ЦБСТ" in (d.get("co_donors") or [])   # the record's own spelling
            out.append(f'<circle cx="{x(dd):.1f}" cy="18" r="{6 if hub else 4.5}" class="dot{" hub" if hub else ""}">'
                       f'<title>{ru_date(d["date"])}: {esc(d.get("recipient_en") or d.get("recipient"))}</title></circle>')
        out.append("</svg>")
        if any("ЦБСТ" in (d.get("co_donors") or []) for d in ds):
            out.append('<p class="note"><span class="dot-key"></span>TsBST named as a co-donor</p>')
        return "".join(out)

    def notes_list(self):
        out = []
        for n, (text, url) in enumerate(self.notes, 1):
            short = re.sub(r"^https?://(www\.)?", "", url or "").rstrip("/")
            short = short if len(short) <= 40 else short.split("/")[0]
            link = f' <a href="{esc(url)}" target="_blank" rel="noopener">{esc(short)} ↗</a>' if url else ""
            out.append(f'<li id="n{n}">{esc(text)}.{link}</li>')
        return "".join(out)


def dek(ch, n_buy):
    """The page's one-sentence summary, built only from what the record holds (no product-specific text)."""
    p, m = ch.p, ch.maker
    n = display_name(m)
    who = ch.en(m) + (f" ({name_html(n['latin'], n['legal'], key='dek-maker')})" if n["legal"] else "")
    sanctioned = ", a company under sanctions" if ch.sanctions(m) else ""
    ways = []
    if any(li.get("source_id") for li in p.get("listings") or []):
        ways.append("sold online and through dealers")
    if n_buy:
        ways.append(f"bought by state agencies under {n_buy} contract{'s' if n_buy != 1 else ''}")
    donors = {d.get("donor") for d in p.get("deliveries") or []}
    if donors:
        tied = {x for x in donors if x in ch.ents and (ch.ents[x].get("cbst_tie") or {}).get("confidence") in ("t-doc", "t-open", "press")}
        maker = ch.maker.get("slug")
        who_gave = (["a foundation that works with TsBST"] if len(tied - {maker}) == 1 else
                    ["donors tied to TsBST"] if tied - {maker} else [])
        if maker in donors:
            who_gave.append("the maker itself")
        rest = donors - tied - {maker}
        if rest:
            who_gave.append("other donors" if who_gave else ("donors" if len(rest) > 1 else "a donor"))
        ways.append("handed to military units by " + " and by ".join(who_gave))
    tail = (" It is " + ", ".join(ways[:-1]) + (" and " if len(ways) > 1 else "") + ways[-1] + ".") if ways else ""
    return f"{esc(cap(p.get('category')))} made by {who}{sanctioned}.{tail}"


def figures(ch):
    """The "How many" strip: minimum counts, each from a document and footnoted; nothing summed across kinds."""
    ds = ch.p.get("deliveries") or []
    figs = list(ch.figures)
    if ds:
        dates = sorted(d["date"] for d in ds)
        figs.append((str(len(ds)), f"handovers reported, {ru_date(dates[0])} – {ru_date(dates[-1])}", ""))
    if not figs:
        return ""
    cells = "".join(f'<div class="fig"><span class="n">{esc(n)}</span><span class="w">{w}{r}</span></div>' for n, w, r in figs)
    return (f'<div class="figs" aria-label="How many">{cells}</div>'
            '<p class="figs-note">Minimums from documents. They may overlap, so they are not added up.</p>')


def about(ch):
    """A short note on the maker, from documented fields only (build_company_page.brief), and its company file."""
    from build_company_page import COMPANY_PAGES, brief   # noqa: E402
    m = ch.maker
    link = (f'<p><a href="{esc(COMPANY_PAGES[m["slug"]])}" target="_blank" rel="noopener">Company file for {ch.en(m)} ↗</a></p>'
            if m["slug"] in COMPANY_PAGES else "")
    return f'<section class="prose rm-prose"><h2 class="rm-h2">About the maker</h2><p>{brief(m, ch.ref, ch.src)}</p>{link}</section>'


MODEL_WORDS = [("рюкзак", "backpack"), ("Багажный Бокс", "luggage box"), ("мото", "motorcycle"), ("ВИП", "VIP")]


def models(ch):
    """A product with many models: one tile per model as the catalogue names it, grouped by the series letters in the
    name. Only words printed in the model name are translated; nothing is inferred about what a series means."""
    vs = ch.p.get("versions") or []
    if len(vs) <= 5:
        return ""
    groups = {}
    for v in vs:
        short = re.sub(r"^" + re.escape(ch.pq) + r"\s*", "", v["name_ru"]) or v["name_ru"]
        series = re.sub(r"^(рюкзак\s*)", "", short).split("-")[0].split()[0].rstrip("0123456789 ")
        en = short
        for ru, w in MODEL_WORDS:
            en = en.replace(ru, w)
        num = re.search(r"product card (\d+)", v.get("description") or "")
        groups.setdefault(series, []).append(
            f'<li class="mdl-t"><span class="mn">{name_html(latin_text(en), v["name_ru"], key="model-" + v["slug"])}</span>'
            + (f'<span class="mc">catalogue card {num.group(1)}</span>' if num else "") + f'{ch.ref(v.get("source_id"))}</li>')
    tiles = "".join(f'<div class="mdl-g"><h3 class="rm-label">{esc(latin_text(k))} series · {len(g)}</h3><ul>{"".join(g)}</ul></div>'
                    for k, g in groups.items())
    return (f'<section class="prose"><h2 class="rm-h2">The models</h2><p class="mdl-lede">{len(vs)} models of {esc(ch.pq_en)} '
            f'are listed in the state industrial catalogue (GISP), each with its own card. Grouped by the letters in the model '
            f'name; the catalogue does not say what the letters stand for.</p><div class="mdl-w">{tiles}</div></section>')


def handover_map(ch):
    """Where the handovers say the equipment went (exhibits/handover_map.py); nothing when none are on file."""
    import handover_map as hm   # noqa: E402
    ds = ch.p.get("deliveries") or []
    if not ds:
        return ""
    svg, unplaced = hm.render(ds)
    placed = len(ds) - len(unplaced)
    rest = "".join(f'<li>{ru_date(d["date"])}: {esc(d.get("recipient_en") or latin_text(d["recipient"]))}</li>'
                   for d in sorted(unplaced, key=lambda d: d["date"]))
    return (f'<section class="prose"><h2 class="rm-h2">Where the handovers went</h2>'
            f'<figure class="hmap-fig"><div class="hmap-scroll">{svg}</div><figcaption>{placed} of the {len(ds)} handovers on file '
            'name a place. A dot is a town, or a front direction named after a town; a shaded region is a handover that '
            'names only the region. The recipient may be anywhere along that direction or in that region, and a handover '
            'is not evidence of use in combat. Borders are the internationally recognised ones; the map does not show the '
            'front line. Each handover and its source is in the chain above. Boundaries: geoBoundaries, © OpenStreetMap '
            'contributors (ODbL); town positions: Wikidata.</figcaption>'
            + (f'<p class="rm-label">Not placed: no town or region named</p><ul class="unplaced">{rest}</ul>' if rest else "")
            + '</figure></section>')


def render(ch, out):
    p = ch.p
    n_list = sum(1 for li in p.get("listings") or [] if li.get("source_id"))
    n_del = len(p.get("deliveries") or [])
    n_buy = sum(len([b for b in r["buyers"] if "k-buyer" in b]) for r in ch.rows)
    top = "".join(f'<section class="col col-{c}" aria-label="{t}"><h2>{t}</h2>{"".join(ch.top[c])}</section>'
                  for c, t in (("A", "TsBST and its events"), ("B", "Maker"), ("C", "Product")))
    rows = "".join(f'<div class="crow"><div class="cell">{r["card"]}</div><div class="cell buyers">{"".join(r["buyers"])}</div></div>'
                   for r in ch.rows)
    limits = "".join(f"<li>{x}</li>" for x in dict.fromkeys(ch.limits))
    doc = f"""<!doctype html>
<!-- Generated by exhibits/build_chain_view.py {esc(p['slug'])} from data/registry on {dt.date.today().isoformat()}. Do not edit by hand. -->
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(ch.pq_en.strip('«»'))}: Maker to Front</title>
{design_head((REPO / 'exhibits' / 'chain_view.css').read_text() + __import__('handover_map').CSS)}</head>
<body>
<header class="rm-page top">
  <p class="rm-eyebrow">Draft · {ru_date(dt.date.today().isoformat())}</p>
  <h1 class="rm-h1">{esc(ch.pq_en)} <span class="rm-muted">{'from TsBST to the front line' if ch.top['A'] else 'from the maker to the front line'}</span></h1>
  <p class="rm-dek">{dek(ch, n_buy)}</p>
  {figures(ch)}
  <ul class="rm-legend" aria-label="How to read the lines">
    <li><svg width="34" height="8" aria-hidden="true"><line x1="0" x2="34" y1="4" y2="4" class="rm-ln doc"/></svg> A document shows it</li>
    <li><svg width="34" height="8" aria-hidden="true"><line x1="0" x2="34" y1="4" y2="4" class="rm-ln rep"/></svg> Reported: the party's own word or the press</li>
    <li><svg width="34" height="8" aria-hidden="true"><line x1="0" x2="34" y1="4" y2="4" class="rm-ln open"/></svg> Not documented</li>
    <li>Numbers refer to the sources at the end.</li>
    <li>Select a picture to see it full size with its source.</li>
  </ul>
</header>
<main class="rm-page">
  <div class="chain" id="chain">
    <svg class="wires" id="wires" aria-hidden="true"></svg>
    {top}
    <section class="rows" aria-label="Who sells it and who receives it">
      <div class="crow head"><h2>Sold or given by</h2><h2>Bought or received by</h2></div>
      {rows}
    </section>
  </div>
  {models(ch)}
  {handover_map(ch)}
  {about(ch)}
  <section class="prose rm-prose"><h2 class="rm-h2">What this does not show</h2><ul>{limits}</ul>
  <p class="method">Every company, listing, contract and handover here comes from an archived document. Listings
  and handovers are as of the dates shown; {n_list} listings and {n_del} handovers are on file.</p></section>
  <section class="prose rm-prose rm-sources"><h2 class="rm-h2">Sources</h2><ol>{ch.notes_list()}</ol></section>
</main>
{''.join(f'<template id="fig-{k}">{v}</template>' for k, v in ch.templates.items())}
<dialog class="rm-lightbox" id="lightbox" aria-label="Picture"><div class="bar"><button type="button" data-close>Close</button></div><div class="body"></div></dialog>
<script>const EDGES={json.dumps(ch.edges, ensure_ascii=False)};
{(REPO / 'exhibits' / 'chain_view.js').read_text()}
{NAME_JS}</script>
</body></html>
"""
    out.write_text(popup_originals(doc))
    print(f"wrote {out.relative_to(REPO) if out.is_relative_to(REPO) else out}: {len(ch.rows)} rows, {len(ch.edges)} lines, {len(ch.notes)} sources, "
          f"{len(ch.media_files)} pictures")
    for rel, _ in ch.media_files:
        print("  picture", rel)
    for c in dict.fromkeys(ch.untranslated):
        print("  no English name yet (data/registry/name_translations.json):", c)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("product")
    ap.add_argument("--out")
    a = ap.parse_args()
    out = Path(a.out) if a.out else REPO / "exhibits" / f"chain_{a.product}.html"
    ch = Chain(a.product)
    ch.img_dir = out.parent / "images" / "media"
    ch.build()
    render(ch, out)


if __name__ == "__main__":
    main()
