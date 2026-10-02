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
from display_helpers import (design_head, figure_html, kind_icon, load_media, media_about, publish_copy,  # noqa: E402
                             reader_grade, ru_date)

CBST = "ano-tsbst-centre-for-unmanned-systems-technologies"
REGIMES = [("Switzerland", "Switzerland"), ("EU", "EU"), ("OFAC", "US"), ("US ", "US"),
           ("United Kingdom", "UK"), ("UK ", "UK"), ("Japan", "Japan"), ("Canada", "Canada"),
           ("Australia", "Australia"), ("New Zealand", "New Zealand"), ("Ukraine", "Ukraine")]
# card kind -> (icon, extra class)
KIND_MARK = {"hub": ("company", " hub"), "programme": ("program", ""), "event": ("event", ""),
             "maker": ("company", ""), "product": ("product", ""), "channel": ("company", ""),
             "storefront": ("storefront", ""), "donor": ("company", ""), "buyer": ("buyer", ""),
             "field": ("unit", ""), "absent": ("storefront", " absent")}
PROV_GROUP = {"self": "Published by the company", "platform": "From a marketplace listing",
              "third_party": "Posted by buyers and others", "press": "Press", "counterparty": "From the counterparty"}
ROLE_EN = {"exhibitor": "Showed «{p}» at the event", "resident": "Resident", "finalist": "Finalist",
           "co-organiser": "Co-organised by", "organiser": "Organised by"}


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


def split_name(e):
    """'АНО «ЦБСТ» | Centre for …' -> ('АНО «ЦБСТ»', 'Centre for …')."""
    parts = (e.get("name_ru") or "").split(" | ", 1)
    return parts[0], (parts[1] if len(parts) > 1 else "")


def describe_source(s):
    """A reader-facing description and public link for one sources.json record."""
    path = Path(s["path"])
    name = path.name
    prefix = name.split("_", 1)[0]
    date = ru_date(s.get("as_of") or s.get("captured_date")) or ""
    url = s.get("url")
    if prefix == "TGPOST":
        head = ""
        try:
            head = (REPO / s["path"]).read_text(errors="ignore")[:400]
        except OSError:
            pass
        m = re.search(r"t\.me/(\w+).*?msg_id (\d+)", head, re.S)
        if m:
            return f"Telegram, @{m.group(1)}, post {m.group(2)}, {date}", f"https://t.me/{m.group(1)}/{m.group(2)}"
        m = re.search(r"private Telegram chat «([^»]+)».*?msg_id (\d+)", head, re.S)
        if m:
            return f"Telegram, closed chat «{m.group(1).strip()}», message {m.group(2)}, {date}", None
        return f"Telegram post, {date}", None
    if prefix == "TGMEDIA":
        m = re.search(r"post(\d+)", name)
        return f"File posted in the maker's Telegram customer chat{', message ' + m.group(1) if m else ''}, {date}", None
    if prefix.startswith("ZAKUPKI"):
        m = re.search(r"(\d{19})", name)
        if m:
            return (f"State procurement record no. {m.group(1)}, zakupki.gov.ru",
                    f"https://zakupki.gov.ru/epz/contract/contractCard/common-info.html?reestrNumber={m.group(1)}")
        return "State procurement record, zakupki.gov.ru", None
    if prefix in ("EGRUL",) or name.startswith("ul-"):
        return f"Company register extract (ЕГРЮЛ, Federal Tax Service), {date}", None
    if prefix == "РЕСУРС" or "БФО" in name:
        fy = s.get("fiscal_year") or (s.get("as_of") or "")[:4]
        return f"Annual accounts filed with the Federal Tax Service, FY {fy}", None
    if prefix == "OPENSANCTIONS":
        return f"Sanctions-list entries compiled by OpenSanctions, checked {date}", None
    if prefix == "GUR":
        return f"Ukraine's defence intelligence (ГУР) War & Sanctions portal, {date}", url
    if prefix == "NSDC":
        return f"Extract from Ukraine's State Register of Sanctions, {date}", None
    if prefix == "WILDBERRIES":
        return f"Wildberries seller page, archived {date}", url
    if prefix == "OZON":
        return f"Ozon seller page, archived {date}", url
    if prefix in ("WEBCAPTURE", "SITE", "WEB"):
        if not url and path.suffix in (".html", ".htm"):
            try:
                head = (REPO / s["path"]).read_text(errors="ignore")[:200000]
                m = (re.search(r'rel="canonical"[^>]*href="([^"]+)"', head)
                     or re.search(r'og:url"[^>]*content="([^"]+)"', head))
                url = m.group(1) if m else None
            except OSError:
                pass
        site = re.sub(r"^https?://(www\.)?", "", url).split("/")[0] if url else ""
        return (f"Web page{' on ' + site if site else ''}, archived {date}", url)
    return f"Archived document, {date}", url


class Chain:
    def __init__(self, product_slug):
        self.ents = {e["slug"]: e for e in load("entities.json")}
        self.programs = {p["slug"]: p for p in load("programs.json")}
        self.src = {s["id"]: s for s in load("sources.json")}
        prods = {p["slug"]: p for p in load("products.json")}
        if product_slug not in prods:
            sys.exit(f"no product {product_slug!r} in products.json")
        self.p = prods[product_slug]
        self.pq = self.p["name_ru"]                       # «Булат»
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

    # -- notation ------------------------------------------------------------------------
    def ref(self, *sids):
        nums = []
        for s in sids:
            if not s or s not in self.src:
                continue
            desc = describe_source(self.src[s])
            if desc not in self.notes:
                self.notes.append(desc)
            nums.append(self.notes.index(desc) + 1)
        if not nums:
            return ""
        return "<sup class=\"rm-ref\">" + ",".join(f'<a href="#n{n}">{n}</a>' for n in sorted(set(nums))) + "</sup>"

    def name(self, e, sub=True):
        left, right = split_name(e)
        return esc(left) + (f"<small>{esc(right)}</small>" if sub and right else "")

    def sanctions(self, e):
        seen, sids = [], []
        for s in e.get("sanctions") or []:
            regs = s.get("regime") or []
            for r in regs if isinstance(regs, list) else [regs]:
                for key, label in REGIMES:
                    if key in r:
                        if label not in seen:
                            seen.append(label)
                        sids.append(s.get("source_id"))
                        break
        if not seen:
            return ""
        return (f'<p class="row sanc"><span class="rm-sanction">Sanctioned <b>{esc(", ".join(seen))}</b></span>'
                f'{self.ref(*sids)}</p>')

    def card(self, cid, kind, label, title, body):
        icon, extra = KIND_MARK.get(kind, ("", ""))
        return (f'<article class="rm-card k-{kind}{extra}" id="{cid}"><header><span class="rm-kind">'
                f'{kind_icon(icon)}{esc(label)}</span></header><h3 class="rm-name">{title}</h3>{body}</article>')

    def edge(self, a, b, grade, label, bus=False):
        self.edges.append({"from": a, "to": b, "grade": grade, "label": label, "bus": bus})

    # -- build ---------------------------------------------------------------------------
    def build(self):
        p, m = self.p, self.maker
        maker_left = split_name(m)[0]

        # A: ЦБСТ, programmes, events
        c = self.ents[CBST]
        self.top["A"].append(self.card("hub", "hub", "Hub", self.name(c), self.sanctions(c)))
        tie = m.get("cbst_tie") or {}
        g = reader_grade(tie.get("confidence")) if tie.get("confidence") in ("t-doc", "t-open", "press") else None
        if g:
            self.edge("hub", "maker", g, "Link to ЦБСТ")
        for mem in m.get("memberships") or []:
            prog = self.programs.get(mem["program"], {})
            cid = "prog-" + mem["program"]
            self.top["A"].append(self.card(cid, "programme", "Programme", esc(prog.get("name_ru")),
                                           f'<p class="row">{esc(ROLE_EN.get(mem.get("role"), mem.get("role")))}, '
                                           f'{ru_date(mem.get("as_of"))}{self.ref(mem.get("source_id"))}</p>'))
            self.edge(cid, "maker", reader_grade(mem.get("basis")), "Member")
        if not m.get("memberships"):
            self.limits.append(f"No document records {esc(maker_left)} as a formal member of a ЦБСТ programme. "
                               "Its link to ЦБСТ rests on the posts and statements cited on its card.")
        for part in m.get("participations") or []:
            ev = self.programs.get(part["event"], {})
            cid = "ev-" + part["event"]
            orgs = "".join(
                f'<p class="note">{esc(ROLE_EN.get(o.get("role"), "Organised by"))} '
                f'{esc(split_name(self.ents[o["slug"]])[0]) if o.get("slug") in self.ents else ""}'
                f'{self.ref(o.get("source_id"))}</p>'
                for o in ev.get("organisers") or [] if isinstance(o, dict))
            role = ROLE_EN.get(part.get("role"), part.get("role") or "").replace("{p}", self.pname)
            self.top["A"].append(self.card(cid, "event", "Event", esc(ev.get("name_ru")),
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
            rows.append(f'<p class="row">Linked to ЦБСТ{self.ref(tie.get("source_id"))}</p>')
        prod_refs = self.media_refs()
        own = [x for x in media_about(self.media, {("entity", m["slug"])}) if x.get("genre") != "logo"
               and not any((a_["type"], a_["id"]) in prod_refs for a_ in x.get("about") or [])]
        rows.append(self.strip(own, label=f"Published by {maker_left}"))
        self.top["B"].append(self.card("maker", "maker", "Maker", self.name(m), "".join(rows)))

        # C: product
        vers = ", ".join(esc(v["name_ru"]) for v in p.get("versions") or [])
        acc = len(p.get("accessories") or [])
        vsrc = [v.get("source_id") for v in p.get("versions") or []]
        self.top["C"].append(self.card(
            "product", "product", "Product", esc(self.pq),
            self.thumb() + f'<p class="row">{esc(cap(p.get("category")))}</p>'
            f'<p class="row">Versions: {vers}{self.ref(*vsrc)}'
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
            title = self.name(e) if e else esc(re.sub(r"\s*\(.*\)$", "", front))
            when = ", ".join(sorted({ru_date(li["as_of"]) for li in lis}))
            body = (f'<p class="row">{esc(lis[0]["channel"])}</p>'
                    f'<p class="row">Listed {when}{self.ref(*[li["source_id"] for li in lis])}</p>'
                    + (self.sanctions(e) if e and ent != m["slug"] else "")
                    + self.strip(media_about(self.media, {("listing", li["id"]) for li in lis}), label="Pictures of this listing"))
            add_row(f"ch-{i}", ent, self.card(f"ch-{i}", "channel" if e else "storefront", "Sells", title, body),
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
                    add_row(cid, e["slug"], self.card(cid, "channel", "Sells", self.name(e), line + self.sanctions(e)),
                            reader_grade(sf.get("basis")), "Sells")

        contracts = []
        for e in self.ents.values():
            for gc in e.get("government_contracts") or []:
                if fold(self.pname) in fold((gc.get("subject_ru") or "") + " " + (gc.get("items") or "")):
                    contracts.append((e, gc))
        for e, gc in contracts:
            if e["slug"] not in row_of:
                cid = f"gc-{len(self.rows)}"
                add_row(cid, e["slug"], self.card(cid, "channel", "Supplies the state", self.name(e),
                                                  f'<p class="row">State supplier of {esc(self.pq)}</p>' + self.sanctions(e)),
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
                if hit:
                    extra(slug, f'<p class="row person">Owned and run by {esc(person)}, who also trades as a sole '
                                f'trader (<a href="#{self.rows[j]["id"]}">ИП</a>){self.ref(hit.get("source_id"))}</p>')
        for k, (e, gc) in enumerate(sorted(contracts, key=lambda x: str(x[1].get("date")))):
            cid = f"buy-{k}"
            customer = re.sub(r"\s*\(ИНН \d+\)", "", gc.get("customer") or "")
            subj = gc.get("subject_ru")
            self.rows[row_of[e["slug"]]]["buyers"].append(self.card(
                cid, "buyer", "State buyer", esc(customer),
                f'<p class="row"><b>{money(gc.get("value_rub"))}</b>, '
                f'{esc(ru_date(gc.get("date")) if gc.get("date") else "")}{self.ref(gc.get("source_id"))}</p>'
                + (f'<p class="note" lang="ru">«{esc(subj)}»</p>' if subj else "")))
            self.edge(self.rows[row_of[e["slug"]]]["id"], cid, "doc", "State contract")

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
            body = (f'<p class="row">Donated {esc(self.pq)} to front-line units</p>'
                    + (f'<p class="row">Named alongside it: {esc(", ".join(co))}</p>' if co else "")
                    + (f'<p class="row">Linked to ЦБСТ{self.ref(dtie.get("source_id"))}</p>' if dtie.get("confidence") in ("t-doc", "t-open", "press") else "")
                    + (f'<p class="row">Donations received in {ffin["year"]}: {money(ffin["funds_received"])}'
                       f'{self.ref(ffin.get("source_id"))}</p>' if ffin else "")
                    + (self.sanctions(e) if e else ""))
            self.rows.append({"id": cid, "card": self.card(cid, "donor", "Donates", self.name(e) if e else esc(slug), body),
                              "buyers": []})
            self.edge("product", cid, "open", "How the donor obtained it is not documented", bus=True)
            rid = f"rec-{len(self.rows)}"
            items = "".join(
                f'<li><time>{ru_date(d["date"])}</time> <span lang="ru">{esc(d.get("recipient"))}</span>'
                + (f' <span class="co">with {esc(", ".join(d["co_donors"]))}</span>' if d.get("co_donors") else "")
                + f'{self.ref(d.get("source_id"), *(d.get("other_source_ids") or []))}'
                + (self.strip(media_about(self.media, {("delivery", d["id"])}), label="") if d.get("id") else "")
                + '</li>' for d in ds)
            self.rows[-1]["buyers"].append(self.card(
                rid, "field", "Front-line recipients",
                f'{len(ds)} handovers <small>{ru_date(ds[0]["date"])} – {ru_date(ds[-1]["date"])}</small>',
                f'<p class="note">As reported by the donor on its own Telegram channel.</p>'
                + self.timeline(ds) + f'<ul class="rec">{items}</ul>'))
            self.edge(cid, rid, "rep", "Reported by the donor")
            dname = split_name(e)[0] if e else slug
            self.limits.append(f"No document shows where {esc(dname)} obtained {esc(self.pq)}. "
                               "The line from the product to the donor is dotted for that reason.")
            self.limits.append(f"The {len(ds)} handovers are {esc(dname)}'s own reports. None is confirmed by the "
                               "receiving unit or an independent source, and the post date is not always the handover date.")

        # РОЙ.МАРКЕТ: shown as absent when no listing names it
        if not any("рой" in fold(li["channel"]) or "roimarket" in fold(li.get("url")) for li in p.get("listings") or []):
            claim = next((cl for cl in p.get("claims") or [] if cl.get("metric") == "distribution"), None)
            body = '<p class="row">No listing found.</p>'
            if claim:
                body += (f'<blockquote lang="ru">«{esc(claim["text_ru"])}»</blockquote>'
                         f'<p class="note">{esc(maker_left)} customer chat, {ru_date(claim.get("as_of"))}'
                         f'{self.ref(claim.get("source_id"))}</p>')
            self.rows.append({"id": "roymarket", "card": self.card("roymarket", "absent", "Not sold here", "РОЙ.МАРКЕТ", body),
                              "buyers": []})

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
                return split_name(self.ents[a_["id"]])[0]
        return split_name(self.maker)[0]

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
            out += (f'<button class="rm-thumb-main" type="button" data-fig="fig-{main["id"]}" aria-label="{esc(main["shows"])}">'
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
                            f'aria-label="{esc(m["shows"])}"><img src="{esc(self.img(m))}" alt=""></button>')
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
            hub = "ЦБСТ" in (d.get("co_donors") or [])
            out.append(f'<circle cx="{x(dd):.1f}" cy="18" r="{6 if hub else 4.5}" class="dot{" hub" if hub else ""}">'
                       f'<title>{ru_date(d["date"])}: {esc(d.get("recipient"))}</title></circle>')
        out.append("</svg>")
        if any("ЦБСТ" in (d.get("co_donors") or []) for d in ds):
            out.append('<p class="note"><span class="dot-key"></span>ЦБСТ named as a co-donor</p>')
        return "".join(out)

    def notes_list(self):
        out = []
        for n, (text, url) in enumerate(self.notes, 1):
            short = re.sub(r"^https?://(www\.)?", "", url or "").rstrip("/")
            short = short if len(short) <= 40 else short.split("/")[0]
            link = f' <a href="{esc(url)}" target="_blank" rel="noopener">{esc(short)} ↗</a>' if url else ""
            out.append(f'<li id="n{n}">{esc(text)}.{link}</li>')
        return "".join(out)


def render(ch, out):
    p = ch.p
    n_list = sum(1 for li in p.get("listings") or [] if li.get("source_id"))
    n_del = len(p.get("deliveries") or [])
    n_buy = sum(len([b for b in r["buyers"] if "k-buyer" in b]) for r in ch.rows)
    top = "".join(f'<section class="col col-{c}" aria-label="{t}"><h2>{t}</h2>{"".join(ch.top[c])}</section>'
                  for c, t in (("A", "ЦБСТ and its events"), ("B", "Maker"), ("C", "Product")))
    rows = "".join(f'<div class="crow"><div class="cell">{r["card"]}</div><div class="cell buyers">{"".join(r["buyers"])}</div></div>'
                   for r in ch.rows)
    limits = "".join(f"<li>{x}</li>" for x in dict.fromkeys(ch.limits))
    doc = f"""<!doctype html>
<!-- Generated by exhibits/build_chain_view.py {esc(p['slug'])} from data/registry on {dt.date.today().isoformat()}. Do not edit by hand. -->
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(ch.pname)}: Maker to Front</title>
{design_head((REPO / 'exhibits' / 'chain_view.css').read_text())}</head>
<body>
<header class="rm-page top">
  <p class="rm-eyebrow">Draft · {ru_date(dt.date.today().isoformat())}</p>
  <h1 class="rm-h1">{esc(ch.pq)} <span class="rm-muted">from ЦБСТ to the front line</span></h1>
  <p class="rm-dek">{esc(cap(p.get('category')))} made by {esc(split_name(ch.maker)[0])}, a company
  under sanctions. It is sold on marketplaces and through dealers, bought by state agencies under
  {n_buy} contract{'s' if n_buy != 1 else ''}, and handed to front-line units by a foundation that works with ЦБСТ.</p>
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
  <section class="prose rm-prose"><h2 class="rm-h2">What this does not show</h2><ul>{limits}</ul>
  <p class="method">Every company, listing, contract and handover here comes from an archived document. Listings
  and handovers are as of the dates shown; {n_list} listings and {n_del} handovers are on file.</p></section>
  <section class="prose rm-prose rm-sources"><h2 class="rm-h2">Sources</h2><ol>{ch.notes_list()}</ol></section>
</main>
{''.join(f'<template id="fig-{k}">{v}</template>' for k, v in ch.templates.items())}
<dialog class="rm-lightbox" id="lightbox" aria-label="Picture"><div class="bar"><button type="button" data-close>Close</button></div><div class="body"></div></dialog>
<script>const EDGES={json.dumps(ch.edges, ensure_ascii=False)};
{(REPO / 'exhibits' / 'chain_view.js').read_text()}</script>
</body></html>
"""
    out.write_text(doc)
    print(f"wrote {out.relative_to(REPO)}: {len(ch.rows)} rows, {len(ch.edges)} lines, {len(ch.notes)} sources, "
          f"{len(ch.media_files)} pictures")
    for rel, _ in ch.media_files:
        print("  picture", rel)


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
