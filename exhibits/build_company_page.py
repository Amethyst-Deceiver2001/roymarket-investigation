#!/usr/bin/env python3
"""Company page: one legal entity for a reader, generated from the registry (a private preview until the cutoff).

    python3 exhibits/build_company_page.py ooo-trimiks        # -> exhibits/company_ooo-trimiks.html

Same rules as the chain view: Latin names first with the Cyrillic attached (STYLE_GUIDE §2.2-2.3a), no internal
notation, every claim footnoted to a plain-words source. A fact is shown only when its source grades as a document;
history entries resting on anything weaker (a working spreadsheet, a screening aggregator) are counted in "What this
page does not show" instead of being printed. brief() is shared with the chain view's "About the maker" note.
Local file processing only.
"""
import argparse
import datetime as dt
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "exhibits"))
from graph_contract import source_grade  # noqa: E402
import deliveries as dl  # noqa: E402
from display_helpers import (NAME_JS, design_head, display_name, figure_html, latin_display, latin_text, load_media, media_about, latinize_gloss, name_html, orig_line, popup_originals, quote_html, sanction_regimes,  # noqa: E402
                             person_names, publish_copy, reader_grade, ru_date, translation)
from build_chain_view import ROLE_EN, describe_source, esc, load, money  # noqa: E402

# Published company pages (private preview Artifacts until the public cutoff), as CHAINS in build_landing.py.
LANDING_URL = "https://claude.ai/artifact/W5m6W6w663RjwfqqTEjQ6z"   # private preview of the landing page
COMPANY_PAGES = {"ooo-trimiks": "https://claude.ai/artifact/GVG9YdHZVHPZNtKqBoZqEc",
                 "ovod": "https://claude.ai/artifact/37aScZhS6wfCYedygwrjbk",
                 "ooo-goudron": "https://claude.ai/artifact/3rMXcnJ8DZ66WmvcTFk9Yi",
                 "ooo-skb-piranya": "https://claude.ai/artifact/XNDYQXZjVQ2cr77D8nkadw",
                 "csn-bars-sarmat": "https://claude.ai/artifact/WxuirHyRS5bMTcZwLHryoV"}
LIST_CHECKS = __import__("json").loads((REPO / "data" / "registry" / "list_checks.json").read_text())
ROLE_TITLE_EN = {"Директор по развитию": "Development director", "Генеральный директор": "Director general",
                 "Дилер (Москва, Мариуполь)": "Dealer (Moscow, Mariupol)"}
CITY_EN = {"St Petersburg": "St Petersburg", "Санкт-Петербург": "St Petersburg", "Москва": "Moscow"}


def regimes(e):
    """[(label, [source ids])] in first-seen order, from the entity's sanctions[] entries (display_helpers rule)."""
    return sanction_regimes(e.get("sanctions"))


WESTERN = ["US", "EU", "UK", "Switzerland"]


def list_mark(e, ref):
    """A dated line for a Western list with no entry carrying the entity's INN or OGRN. Only for an identifier the
    run actually searched (data/registry/list_checks.json); otherwise it says the entity has not been checked."""
    have = {lab for lab, _ in regimes(e)}
    missing = [w for w in WESTERN if w not in have]
    if not missing:
        return ""
    ids = {e.get("inn"), e.get("ogrn")} - {None}
    if not ids:   # a brand with no legal identity on file cannot be checked by identifier
        return ""
    runs = [r for r in LIST_CHECKS["runs"] if ids & set(r["identifiers"])]
    if not runs:
        return '<p class="row nolist">Not yet checked against the US, EU, UK or Swiss lists.</p>'
    r = max(runs, key=lambda r: r["date"])
    adj = [{"Switzerland": "Swiss"}.get(m, m) for m in missing]
    names = ", ".join(adj[:-1]) + " or " + adj[-1] if len(adj) > 1 else adj[0]
    return (f'<p class="row nolist">No {esc(names)} list entry carries its INN, as of the lists downloaded '
            f'{ru_date(r["date"])}{ref(*[r["lists"][m] for m in missing])}</p>')


def egrul_source(e, src):
    """The latest company register extract on file for this entity: the source a registration date rests on."""
    ogrn, inn = e.get("ogrn") or "-", e.get("inn") or "-"
    cands = [s for s in src.values() if s.get("type") == "egrul" and (ogrn in s["path"] or inn in (s.get("inns") or []))]
    return max(cands, key=lambda s: s.get("captured_date") or "")["id"] if cands else None


def restricted(e, src):
    """The first dated, documented entry saying the register hides the owners and director, or None."""
    for h in sorted(e.get("director_history") or [], key=lambda h: h.get("as_of") or ""):
        if "restricted" in (h.get("value") or "").lower() and source_grade(src.get(h.get("source_id"))) == "doc":
            return h
    return None


def brief(e, ref, src):
    """Two to four sentences on a company, each from a documented field and footnoted. No sentence without a source."""
    n = display_name(e)
    legal = n["legal"] or n["head"]
    out = []
    reg_src = egrul_source(e, src)
    when = e.get("registered")
    city = CITY_EN.get(e.get("city") or "", e.get("city") or "")
    who = (f'{esc(latin_text(n["head"]))} is the trade name of {name_html(n["latin"], legal, key="brief-" + e["slug"])}'
           if n["legal"] else name_html(n["latin"], legal, key="brief-" + e["slug"]))
    if when and reg_src:
        out.append(f'{who}, registered{" in " + esc(city) if city else ""} on {esc(when)}{ref(reg_src)}.')
    else:
        out.append(f"{who}.")
    tm = next((b for b in e.get("brands") or [] if b.get("primary") and b.get("kind") == "trademark"), None)
    if tm and tm.get("registration"):
        out.append(f'It trades under the trademark «{esc(tm["name"])}», no. {esc(re.sub("^RU", "", tm["registration"]))}'
                   f'{ref(tm.get("source_id"))}.')
    r = restricted(e, src)
    if r:
        out.append(f'Its owners and director have been hidden in the company register since {ru_date(r["as_of"])}'
                   f'{ref(r.get("source_id"))}.')
    regs = regimes(e)
    if regs:
        names = [lab for lab, _ in regs]
        txt = ", ".join(names[:-1]) + (" and " if len(names) > 1 else "") + names[-1]
        out.append(f"It is under sanctions in {esc(txt)}{ref(*[s for _, ss in regs for s in ss])}.")
    fin = sorted((f for f in e.get("financials") or [] if f.get("revenue")), key=lambda f: str(f["year"]))
    if fin:
        out.append(f'Revenue in {fin[-1]["year"]}: {money(fin[-1]["revenue"])}{ref(fin[-1].get("source_id"))}.')
    return " ".join(out)


class Page:
    def __init__(self, slug):
        self.ents = {e["slug"]: e for e in load("entities.json")}
        if slug not in self.ents:
            sys.exit(f"no entity {slug!r} in entities.json")
        self.e = self.ents[slug]
        self.src = {s["id"]: s for s in load("sources.json")}
        self.products = dl.load_products()
        self.programs = {p["slug"]: p for p in load("programs.json")}
        self.notes = []
        self.limits = []
        self.media = load_media()
        self.media_files = []
        self._shown = set()   # media ids already placed by reported_by_others()

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
        return '<sup class="rm-ref">' + ",".join(f'<a href="#n{k}">{k}</a>' for k in sorted(set(nums))) + "</sup>"

    def doc(self, sid):
        return source_grade(self.src.get(sid)) == "doc"

    def en(self, e):
        n = display_name(e)
        legal = n["legal"] or n["head"]
        if legal.startswith("ИП "):
            return esc(person_names(legal)["first"])
        return esc(latin_text(n["head"]) if n["legal"] else n["latin"])

    def logo(self, img_dir):
        m = next((x for x in media_about(self.media, {("entity", self.e["slug"])}) if x.get("genre") == "logo"), None)
        name = publish_copy(m, img_dir) if m else None
        if not name:
            return ""
        self.media_files.append((f"images/media/{name}", img_dir / name))
        dark = " on-dark" if m.get("logo_ground") == "dark" else ""
        return f'<img class="rm-logo co-logo{dark}" src="images/media/{esc(name)}" alt="Logo of {self.en(self.e)}">'

    # -- sections ----------------------------------------------------------------------------------
    def register(self):
        e = self.e
        rows = []
        reg_src = egrul_source(e, self.src)
        if self.unit():
            rows.append(("Legal form", "Military unit. It is not a registered company and has no INN or OGRN of its own."))
            fd = self.foundation()
            if fd:
                fe, fsrc = fd
                ids = ", ".join(f"{lab} {fe[k]}" for lab, k in (("INN", "inn"), ("OGRN", "ogrn")) if fe.get(k))
                rows.append(("Supporting foundation", f'{self.en(fe)} ({esc(ids)}){self.ref(fsrc)}'))
        rows.append(("INN", f'<span class="rm-id">{esc(e.get("inn"))}</span>' if e.get("inn") else ""))
        rows.append(("OGRN", f'<span class="rm-id">{esc(e.get("ogrn"))}</span>' if e.get("ogrn") else ""))
        if e.get("registered"):
            rows.append(("Registered", f'{esc(e["registered"])}{self.ref(reg_src)}'))
        addr = next((h for h in sorted(e.get("address_history") or [], key=lambda h: h.get("as_of") or "", reverse=True)
                     if self.doc(h.get("source_id"))), None)
        if addr:
            rows.append(("Registered address", f'{name_html(latin_text(addr["value"]), addr["value"], key="addr-1", what="Register address in Russian:")}{self.ref(addr["source_id"])}'))
        if e.get("okved_code"):
            tr = translation(e.get("okved_label") or "")
            label = (name_html(tr["en"], e["okved_label"], key="okved") if tr
                     else name_html("description as registered", e["okved_label"], key="okved", what="Registered activity, in Russian:"))
            rows.append(("Main activity (OKVED)", f'{esc(e["okved_code"])}: {label}{self.ref(reg_src)}'))
        cap_ = next((h for h in e.get("charter_capital_history") or [] if self.doc(h.get("source_id"))), None)
        if cap_:
            rows.append(("Charter capital", f'{money(cap_["value"])}{self.ref(cap_["source_id"])}'))
        r = restricted(e, self.src)
        if r:
            rows.append(("Owners and director", f'Hidden in the register since {ru_date(r["as_of"])}{self.ref(r["source_id"])}'))
        else:
            for key, label in (("director_history", "Director"), ("founders_history", "Owner")):
                hs = [h for h in e.get(key) or [] if self.doc(h.get("source_id")) and h.get("value")]
                if not hs:
                    continue
                last = max(h.get("as_of") or "" for h in hs)
                for h in (x for x in hs if (x.get("as_of") or "") == last):
                    m = re.match(r"^(.*?)\s+(\d+%)\s*(\(.*\))?$", h["value"])
                    who, share = (m.group(1), m.group(2)) if m else (h["value"], "")
                    pn = person_names(who)
                    rows.append((label, f'{esc(pn["first"])} (<span lang="ru">{esc(who)}</span>)'
                                        f'{", " + share + " share" if share else ""}, as of {ru_date(h["as_of"])}'
                                        f'{self.ref(h["source_id"])}'))
                    self.reg_people = True
        return self.dl(rows)

    def unit(self):
        return (self.e.get("legal_form") or "").lower() == "military unit"

    def foundation(self):
        """The unit's supporting foundation: the group-structure link whose record carries an INN/OGRN, with the
        source that shows the unit's own page naming it (a fresh capture of the foundation's page where one is on file)."""
        for r in self.e.get("related_entities") or []:
            f = self.ents.get(r.get("slug"))
            if r.get("relationship_type") == "group-structure" and f and (f.get("inn") or f.get("ogrn")):
                return f, r.get("source_id")
        return None

    def before(self):
        """Owners, directors and names recorded only from a weaker source (an investigator's dossier): shown, graded
        Reported, each with its period and footnote, and named once in the limits."""
        e = self.e
        rows = []
        for key, label in (("name_history", "Name"), ("director_history", "Director"), ("founders_history", "Owner")):
            for h in e.get(key) or []:
                if not h.get("source_id") or self.doc(h["source_id"]) or "restricted" in (h.get("value") or "").lower():
                    continue
                val = h.get("value") or ""
                m = re.match(r"^([\d\-–]+%)\s+(.*)$", val)
                share, who = (m.group(1).replace("-", "–"), m.group(2)) if m else ("", val)
                if key == "name_history":
                    shown = name_html(latin_display(who), who, key=f"nm-{h['source_id']}")
                else:
                    pn = person_names(who)
                    shown = f'{esc(pn["first"])} (<span lang="ru">{esc(who)}</span>)'
                per = re.search(r"(\d{2}\.\d{2}\.\d{4})\s*[–-]\s*(\d{2}\.\d{2}\.\d{4})", h.get("note") or "")
                when = f"{per.group(1)} – {per.group(2)}" if per else (f"to {ru_date(h['as_of'])}" if h.get("as_of") else "")
                rows.append((label, f'{shown}{", " + share + " share" if share else ""}{", " + when if when else ""}'
                                    f'{self.ref(h["source_id"])}'))
        if not rows:
            return ""
        if self.unit():
            self.limits.append("The unit's commander is named on its own site and posts. There is no register to confirm it.")
            return ('<p class="lead-note"><span class="rm-grade rep">Reported</span> From the unit\'s own site. A military '
                    'unit is not in the company register.</p>' + self.dl(rows))
        self.limits.append("The owners, directors and original name before the register was closed come from an "
                           "investigator's dossier. They are graded Reported until a register extract from before that "
                           "date confirms them.")
        return ('<p class="lead-note"><span class="rm-grade rep">Reported</span> From an investigator\'s dossier, not '
                'yet confirmed by a company register extract.</p>' + self.dl(rows))

    def people_block(self):
        """People tied to the company by a role other than staff; each Latin first with the full ФИО (§2.2)."""
        items, staff = [], 0
        reg_people = getattr(self, "reg_people", False)
        for p in load("people.json"):
            for r in p.get("roles") or []:
                if r.get("entity_slug") != self.e["slug"] or r.get("_candidate"):
                    continue
                t = r.get("title") or ""
                if t.startswith("Сотрудник"):
                    staff += 1
                    continue
                m = re.match(r"co-inventor \(patent (\w+)\)", t)
                role = f"Inventor on patent {m.group(1)}" if m else ROLE_TITLE_EN.get(t)
                if not role:
                    continue
                grade = "doc" if self.doc(r.get("source_id")) else "rep"
                pn = person_names(p.get("fio_ru") or "", p.get("name_latin"))
                items.append(f'<li><span class="rm-grade {grade}">{"Documented" if grade == "doc" else "Reported"}</span> '
                             f'{esc(pn["first"])} (<span lang="ru">{esc(pn["fio"])}</span>): {esc(role)}{self.ref(r.get("source_id"))}</li>')
        if staff:
            self.limits.append(f"The dossier names {staff} further staff members. They are not listed here.")
        return f'<ul class="plain">{"".join(items)}</ul>' if items else ("" if reg_people else "<p>None recorded.</p>")

    def place(self):
        """Where it is: the register address, and slots for the satellite and street views until they are captured."""
        addr = next((h for h in sorted(self.e.get("address_history") or [], key=lambda h: h.get("as_of") or "", reverse=True)
                     if self.doc(h.get("source_id"))), None)
        figs = self.premises()
        any_fac = any(m.get("genre") == "facility" for m in media_about(self.media, {("entity", self.e["slug"])}))
        if not addr and not figs and not any_fac:
            return ""
        slot = lambda t: (f'<figure class="rm-fig empty"><div class="frame">{t} not yet captured</div>'
                          f'<figcaption><span class="rm-prov">{t}</span><span class="rm-geo">Coordinates · provider · imagery date</span></figcaption></figure>')
        line = (f'<p>Registered address, as the register gives it: {name_html(latin_text(addr["value"]), addr["value"], key="addr-2", what="Register address in Russian:")}'
                f'{self.ref(addr["source_id"])}</p>') if addr else ""
        views = f'<div class="rm-facility">{slot("Satellite view")}{slot("Street view")}</div>' if (addr or any_fac) else ""
        even = " even" if figs.count("<figure") in (2, 4) else ""   # four pictures sit 2x2, never three and one
        return line + (f'<div class="rm-gallery{even}">{figs}</div>' if figs else "") + views

    def premises(self):
        """Pictures of the company's own premises (media genre facility), with their captions and sources."""
        figs = []
        for m in media_about(self.media, {("entity", self.e["slug"])}):
            if m.get("genre") != "facility" or m.get("publish") == "internal":
                continue
            name = publish_copy(m, self.img_dir)
            if name:
                self.media_files.append((f"images/media/{name}", self.img_dir / name))
                figs.append(figure_html(m, f"images/media/{name}", self.en(self.e), self.ref(m.get("source_id"))))
        return "".join(figs)

    def timeline(self):
        """Dated events from the record, each footnoted; graded events say so."""
        e, ev = self.e, []
        reg_src = egrul_source(e, self.src)
        if e.get("registered") and reg_src:
            d, mth, y = e["registered"].split(".")
            ev.append((f"{y}-{mth}-{d}", "Registered in the company register", reg_src))
        for t in e.get("trademarks") or []:
            for k, verb in (("filed", "filed"), ("registered", "registered")):
                v = t.get(k) or ""
                iso = f"{v[:4]}-{v[4:6]}-{v[6:]}" if v.isdigit() else (f"{v[6:]}-{v[3:5]}-{v[:2]}" if re.match(r"\d\d\.\d\d\.\d{4}", v) else "")
                if iso:
                    ev.append((iso, f'Trademark {esc(t.get("reg_number") or t.get("application_number"))} {verb}', t.get("source_id")))
        for p in e.get("patents") or []:
            for k, verb in (("filed", "filed"), ("published", "published")):
                if p.get(k):
                    ev.append((p[k].replace(".", "-"), f'Patent {esc(p.get("reg_number"))} {verb}', p.get("source_id")))
        r = restricted(e, self.src)
        if r:
            ev.append((r["as_of"], "Owners and director hidden in the company register", r.get("source_id")))
        for s in e.get("sanctions") or []:
            if s.get("date"):
                lab = ", ".join(lab for lab, _ in sanction_regimes([s])) or "Sanctions"
                ev.append((s["date"], f"Listed under {esc(lab)} sanctions", s.get("source_id")))
        undated = [lab for lab, ss in regimes(e) if not any(x.get("date") for x in e.get("sanctions") or []
                                                             if x.get("source_id") in ss)]
        if undated:
            txt = ", ".join(undated[:-1]) + " and " + undated[-1] if len(undated) > 1 else undated[0]
            self.limits.append(f"No listing date is recorded for {esc(txt)}; those listings are not on the timeline.")
        for owner in self.ents.values():
            for gc in owner.get("government_contracts") or []:
                prods = [cp for cp in gc.get("products") or [] if any(p["slug"] == cp.get("product") and p.get("maker") == e["slug"]
                                                                       for p in self.products)]
                if prods and gc.get("date"):
                    ev.append((gc["date"], f'State contract for {money(gc.get("value_rub"))}, supplied by {self.en(owner)}', gc.get("source_id")))
        for part in e.get("participations") or []:
            ev.append((part["as_of"], f'Showed its products at {esc(latin_text(self.programs.get(part["event"], {}).get("name_ru")))}',
                       part.get("source_id")))
        for sp in e.get("state_programs") or []:
            if re.match(r"\d{4}-\d{2}-\d{2}", sp.get("as_of") or "") and sp.get("name_en"):
                ev.append((sp["as_of"], esc(latinize_gloss(sp["name_en"])), sp.get("source_id")))
        for p in self.products:
            if p.get("maker") != e["slug"]:
                continue
            ds = sorted(p.get("deliveries") or [], key=lambda d: d["date"])
            if ds:
                ev.append((ds[0]["date"], f'First reported handover of {esc(latin_text(p["name_ru"]))} to a unit '
                                          f'({len(ds)} reported to {ru_date(ds[-1]["date"])})', ds[0].get("source_id")))
        ev.sort(key=lambda x: x[0])
        rows = "".join(f'<li id="tl{i}"><time>{ru_date(d)}</time><span>{t}{self.ref(sid)}</span></li>' for i, (d, t, sid) in enumerate(ev, 1))
        return self.timeline_strip(ev) + f'<ol class="tline">{rows}</ol>'

    LANES = [("Register", ("Registered", "Owners")), ("Trademarks and patents", ("Trademark", "Patent")),
             ("Sanctions", ("Listed under",)), ("State and programmes", ("State contract", "Showed")),
             ("Handovers", ("First reported handover",))]

    def timeline_strip(self, ev):
        """The same events on one date scale, one lane per kind; each mark is numbered like the list beneath."""
        if len(ev) < 3:
            return ""
        lanes = [(n, [(i, d) for i, (d, t, _) in enumerate(ev, 1) if t.startswith(keys)]) for n, keys in self.LANES]
        placed = {i for _, xs in lanes for i, _ in xs}
        other = [(i, d) for i, (d, _, _) in enumerate(ev, 1) if i not in placed]
        if other:
            lanes.append(("Other", other))
        lanes = [(n, xs) for n, xs in lanes if xs]
        to_ord = lambda d: dt.date.fromisoformat((d[:10] + "-07-01")[:10] if len(d) == 4 else
                                                 (d[:7] + "-15" if len(d) == 7 else d[:10])).toordinal()
        lo = dt.date(int(ev[0][0][:4]), 1, 1).toordinal()
        hi = dt.date.today().toordinal()
        x0, x1, rh = 150, 900, 30
        h = 26 + rh * len(lanes)
        X = lambda d: x0 + (x1 - x0) * (to_ord(d) - lo) / max(1, hi - lo)
        out = [f'<div class="tls-scroll"><svg class="tls" viewBox="0 0 {x1 + 20} {h}" role="img" aria-label="The dated events on one scale">']
        for y in range(dt.date.fromordinal(lo).year, dt.date.today().year + 1):
            x = X(f"{y}-01-01")
            out.append(f'<line class="yl" x1="{x:.1f}" x2="{x:.1f}" y1="14" y2="{h}"/><text class="yt" x="{x + 3:.1f}" y="11">{y}</text>')
        for k, (n, xs) in enumerate(lanes):
            cy = 26 + rh * k + rh / 2
            cls = "sanc" if n == "Sanctions" else ""
            out.append(f'<text class="ln" x="0" y="{cy + 4}">{esc(n)}</text><line class="lr" x1="{x0}" x2="{x1}" y1="{cy}" y2="{cy}"/>')
            for i, d in xs:
                out.append(f'<a href="#tl{i}"><circle class="ev {cls}" cx="{X(d):.1f}" cy="{cy}" r="8"/>'
                           f'<text class="en" x="{X(d):.1f}" y="{cy + 3.5}">{i}</text></a>')
        out.append("</svg></div>")
        return "".join(out)


    def dl(self, rows):
        return '<dl class="facts">' + "".join(f"<dt>{esc(k)}</dt><dd>{v}</dd>" for k, v in rows if v) + "</dl>"

    def sanctions_block(self):
        regs = regimes(self.e)
        if not regs:
            return '<p>No sanctions listing is recorded.</p>'
        out = []
        for lab, ss in regs:
            unread = not any(self.doc(x) for x in ss)
            out.append(f'<p class="sanc"><span class="rm-sanction">Sanctioned <b>{esc(lab)}</b></span>{self.ref(*ss)}'
                       + (' <span class="rm-muted">from a sanctions aggregator; the official entry has not been read</span>'
                          if unread else "") + "</p>")
            if unread:
                self.limits.append(f"The {esc(lab)} listing rests on a sanctions aggregator's match by tax number. "
                                   "The official list entry has not yet been read.")
        out.append(list_mark(self.e, self.ref).replace('class="row nolist"', 'class="nolist"'))
        return "".join(out)

    def accounts(self):
        fin = sorted(self.e.get("financials") or [], key=lambda f: str(f.get("year")))
        if not fin:
            return "<p>No annual accounts are on file.</p>"
        rows = "".join(f'<tr><td>{esc(f.get("year"))}</td><td class="num">{money(f.get("revenue"))}</td>'
                       f'<td class="num">{money(f.get("profit"))}</td><td>{self.ref(f.get("source_id"))}</td></tr>' for f in fin)
        return (f'<div class="tbl"><table><thead><tr><th>Year</th><th class="num">Revenue</th><th class="num">Net profit</th>'
                f'<th></th></tr></thead><tbody>{rows}</tbody></table></div>')

    def products_block(self, chains):
        recs = {p["slug"]: p for p in self.products if p.get("maker") == self.e["slug"]}
        items = []
        for p in self.e.get("products") or []:
            tr = translation(p.get("name_ru") or "")   # a descriptive name is translated, a product name transliterated
            name = tr["en"] if tr else latin_text(p.get("name_ru"))
            link = next((f' <a href="{esc(chains[s])}">chain view ↗</a>' for s, r in recs.items()
                         if s in chains and (p.get("name_ru") or "").startswith(r["name_ru"])), "")
            items.append(f'<li>{esc(name)} <span class="cyr" lang="ru">{esc(p.get("name_ru"))}</span>'
                         f'{self.ref(p.get("source_id"))}{link}</li>')
        prices = [f'<p class="lead-note">Price list on the company\'s own site, {ru_date(c["as_of"])}: '
                  f'{orig_line(c["text_ru"], f"price-{i}", latinize_gloss(c.get("text_en") or ""))}{self.ref(c.get("source_id"))}</p>'
                  for i, c in enumerate(self.e.get("marketing_claims") or [], 1) if (c.get("context") or "").startswith("price list")]
        for c in self.e.get("marketing_claims") or []:
            so = c.get("site_operator")
            if so and (c.get("context") or "").startswith("price list"):
                prices.append(f'<p class="lead-note">{esc(so["text_en"])}{"".join(self.ref(x) for x in so["source_ids"])}</p>')
        return (f'<ul class="plain">{"".join(items)}</ul>' if items else "<p>No products recorded.</p>") + "".join(prices)

    def ip_block(self):
        items = []
        for t in self.e.get("trademarks") or []:
            num = t.get("reg_number") or t.get("application_number")
            kind = "Trademark no." if t.get("reg_number") else "Trademark application no."
            when = t.get("registered") or t.get("filed")
            when = f"{when[6:8]}.{when[4:6]}.{when[:4]}" if when and when.isdigit() and len(when) == 8 else (when or "")
            classes = sorted({c.split()[0] for c in t.get("goods_classes") or []} |
                             set(re.findall(r"(?:^|; )(\d{2}) \(", t.get("goods_classes_summary") or "")))
            items.append(f'<li>{kind} {esc(num)}{" " + (name_html("«" + latin_text(t["title"]) + "»", "«" + t["title"] + "»", key="tm-" + str(num), what="Trademark as registered, in Russian:") if re.search("[А-Яа-я]", t["title"]) else "«" + esc(t["title"]) + "»") if t.get("title") else ""}, '
                         f'{"registered" if t.get("registered") else "filed"} {when}'
                         f'{", classes " + ", ".join(classes) if classes else ""}{self.ref(t.get("source_id"))}</li>')
        for p in self.e.get("patents") or []:
            inv = [person_names(re.sub(r"\s*\(RU\)$", "", i)) for i in p.get("inventors") or []]
            invs = "; ".join(f'{esc(i["first"])} (<span lang="ru">{esc(i["fio"])}</span>)' for i in inv)  # popup_originals() turns the bracket into RU
            pub = (p.get("published") or "").replace(".", "-")
            ttl = (p.get("title") or "").capitalize()
            tr = translation(ttl)
            ttl_html = name_html("«" + tr["en"] + "»", ttl, key="pat-" + (p.get("reg_number") or "")) if tr else f'<span lang="ru">«{esc(ttl)}»</span>'
            items.append(f'<li>Patent {esc(p.get("reg_number"))}, published {ru_date(pub)}: '
                         f'{ttl_html}'
                         f'{"; inventor " + invs if invs else ""}{self.ref(p.get("source_id"))}</li>')
        return f'<ul class="plain">{"".join(items)}</ul>' if items else "<p>None recorded.</p>"

    def network(self):
        e = self.e
        items = []
        tie = e.get("cbst_tie") or {}
        if tie.get("confidence") in ("t-doc", "t-open", "press"):
            g = reader_grade(tie.get("confidence"))
            items.append(f'<li><span class="rm-grade {g}">{ {"doc": "Documented", "rep": "Reported", "open": "Not documented"}[g] }'
                         f'</span> Linked to TsBST{self.ref(tie.get("source_id"))}</li>')
        for part in e.get("participations") or []:
            ev = self.programs.get(part["event"], {})
            prod = next((latin_text(p["name_ru"]).strip("«»") for p in self.products if p.get("maker") == e["slug"]), "its products")
            role = ROLE_EN.get(part.get("role"), part.get("role") or "").replace("{p}", prod)
            items.append(f'<li>{esc(latin_text(ev.get("name_ru")))}: {esc(role[:1].lower() + role[1:])}, '
                         f'{ru_date(part.get("as_of"))}{self.ref(part.get("source_id"))}</li>')
        for sp in e.get("state_programs") or []:
            if sp.get("name_en"):
                when = ru_date(sp["as_of"]) if re.match(r"\d{4}-\d{2}-\d{2}", sp.get("as_of") or "") else esc(sp.get("as_of") or "")
                items.append(f'<li>{esc(latinize_gloss(sp["name_en"]))}, {when}{self.ref(sp.get("source_id"))}</li>')
        if not e.get("memberships"):
            self.limits.append("No document records the company as a formal member of a TsBST programme. Its link to "
                               "TsBST rests on the posts and statements cited here.")
        return f'<ul class="plain">{"".join(items)}</ul>' if items else "<p>None recorded.</p>"

    def own_words(self):
        """Verbatim claims (marketing_claims[]) in the original Russian, each with our gloss and its source. Contact
        lines (phone numbers) are cut and marked, as in the exports."""
        out = []
        for c in sorted(self.e.get("marketing_claims") or [], key=lambda c: c.get("as_of") or ""):
            if (c.get("context") or "").startswith(("third_party", "price list")):
                continue   # someone else's words: reported_by_others(); a price list is not a statement: products_block()
            ru = c.get("text_ru") or ""
            if not ru or not c.get("source_id"):
                continue
            lines = [ln for ln in ru.split("\n")]
            cut = [("[…]" if re.search(r"📞|\+7\d{6,}|\+79\d", ln) else ln) for ln in lines]
            ru = re.sub(r"(\[…\]\n?)+", "[…]\n", "\n".join(cut)).strip()
            m = re.match(r"^\[([^\]]+)\]\s*(.*)$", c.get("text_en") or "", re.S)
            who, gloss = (m.group(1), m.group(2)) if m else ("", c.get("text_en") or "")
            if not who:
                title = describe_source(self.src.get(c["source_id"], {}))[0] if c["source_id"] in self.src else ""
                who = ("Posted on 3mx's own channel" if title.startswith("Telegram, @ru3mx") else
                       "In 3mx's customer chat" if "closed chat" in title else "")
            gloss = re.sub(r"\+7\d[\d ()-]{8,}", "[…]", gloss)
            gloss, who = latinize_gloss(gloss), latinize_gloss(who)
            when = ru_date(c["as_of"]) if re.match(r"\d{4}-\d{2}-\d{2}", c.get("as_of") or "") else ""
            cite = f'{esc(who[:1].upper() + who[1:])}{", " + when if when else ""}{self.ref(c["source_id"])}'
            out.append(quote_html(ru, gloss, cite, key=f"claim-{len(out) + 1}"))
        return "".join(out)

    def reported_by_others(self, img_dir):
        """Another body's post about the company (marketing_claims with a third_party context), quoted, with the
        pictures from the same post (event photos published by a third party, matched on the post's link)."""
        out = []
        for c in sorted(self.e.get("marketing_claims") or [], key=lambda c: c.get("as_of") or ""):
            if not (c.get("context") or "").startswith("third_party") or not c.get("source_id"):
                continue
            m = re.match(r"^\[([^\]]+)\]\s*(.*)$", c.get("text_en") or "", re.S)
            who, gloss = (m.group(1), m.group(2)) if m else ("", c.get("text_en") or "")
            when = ru_date(c["as_of"]) if re.match(r"\d{4}-\d{2}-\d{2}", c.get("as_of") or "") else ""
            cite = f'{esc(latinize_gloss(who))}{", " + when if when else ""}{self.ref(c["source_id"])}'
            out.append(quote_html(c["text_ru"], latinize_gloss(gloss), cite, key=f"other-{len(out) + 1}"))
            post = (self.src.get(c["source_id"], {}).get("public_url") or "").rstrip("/")
            base = post.rsplit("/", 1)[0] + "/" if post else None
            figs = []
            for md in media_about(self.media, {("entity", self.e["slug"])}):
                if base and md.get("asserted_by") == "third_party" and md.get("genre") == "event" and (md.get("original_url") or "").startswith(base):
                    name = publish_copy(md, img_dir)
                    if name:
                        self.media_files.append((f"images/media/{name}", img_dir / name))
                        self._shown.add(md["id"])
                        figs.append(figure_html(md, f"images/media/{name}", esc(latinize_gloss(who)), self.ref(md.get("source_id"))))
            if figs:
                out.append(f'<div class="rm-gallery even">{"".join(figs)}</div>')
        return "".join(out)

    def pictures(self, img_dir):
        """Pictures of the company and its products (not handovers: those sit on the chain view)."""
        keys = {("entity", self.e["slug"])} | {("product", p["slug"]) for p in self.products if p.get("maker") == self.e["slug"]}
        figs = []
        for m in media_about(self.media, keys):
            if m.get("genre") in ("logo", "handover", "facility") or m.get("publish") == "internal" or m["id"] in self._shown:
                continue
            name = publish_copy(m, img_dir)
            if not name:
                continue
            self.media_files.append((f"images/media/{name}", img_dir / name))
            pub = next((a["id"] for a in m.get("about") or [] if a.get("type") == "entity" and a["id"] in self.ents), self.e["slug"])
            prov = self.en(self.ents[pub])   # who published it: the entity the record is about, else this company
            figs.append(figure_html(m, f"images/media/{name}", prov, self.ref(m.get("source_id"))))
        return f'<div class="rm-gallery{" even" if len(figs) in (2, 4) else ""}">{"".join(figs)}</div>' if figs else ""

    def handovers(self):
        """Handovers the company itself reports on its own channel (deliveries.json, donor = this company), as it words them."""
        evs = sorted((d for d in load("deliveries.json") if d.get("donor") == self.e["slug"] and d.get("source_id")
                            and all(i.get("item_en") for i in d["items"])),   # only handovers glossed in English by hand
                     key=lambda d: d["date"])
        if not evs:
            return ""
        items = []
        for d in evs:
            what = "; ".join(esc(i.get("item_en") or latinize_gloss(i.get("item") or "equipment")) for i in d["items"])
            rec = name_html(d.get("recipient_en") or d["recipient"], d["recipient"], key=f"ho-{d['id']}")
            via = d.get("carrier_en")
            via = f", via {esc(via)}" if via and via != "not stated" else ""
            items.append(f'<li><time>{ru_date(d["date"])}</time> {rec}: {what}{via}{self.ref(d["source_id"])}</li>')
        self.limits.append("Handovers listed here are the company's own account on its Telegram channel. Each is one post; none is "
                           "confirmed by the recipient, and a post that names a regiment by number alone does not identify the unit.")
        return f'<p class="lead-note">As the company reports them on its own channel.</p><ul class="plain">{"".join(items)}</ul>'

    def sellers(self):
        items = []
        for s in self.ents.values():
            for sf in s.get("sells_for") or []:
                if sf.get("slug") != self.e["slug"]:
                    continue
                how = {"yes": "named as a dealer on the maker's website", "no": "not authorised by the maker"}.get(
                    sf.get("authorised"), "not on the maker's dealer list")
                items.append(f'<li>{self.en(s)}: {esc(how)}{self.ref(sf.get("source_id"))}{list_mark(s, self.ref)}</li>')
        return f'<ul class="plain">{"".join(items)}</ul>' if items else "<p>None recorded.</p>"

    def gaps(self):
        e = self.e
        fd = self.foundation() if self.unit() else None
        if fd and not any(lab == "Ukraine" for lab, _ in regimes(e)) and not any(lab == "Ukraine" for lab, _ in regimes(fd[0])):
            self.limits.append("A military unit has no INN or OGRN to match. No entry in Ukraine's State Register of "
                               "Sanctions carries the INN or OGRN of its supporting foundation, in the register's export of "
                               "26.10.2026.")
        elif not any(lab == "Ukraine" for lab, _ in regimes(e)):
            self.limits.append("No entry in Ukraine's State Register of Sanctions carries its INN or OGRN, in the register's "
                               "export of 26.10.2026." if (e.get("inn") or e.get("ogrn")) else
                               "No Ukrainian sanction is recorded. Ukraine's State Register of Sanctions is matched by identifier, "
                               "and none is on file for it.")
        if not e.get("foreign_components"):
            self.limits.append("No foreign components in its products are documented.")
        if not e.get("battlefield_evidence"):
            self.limits.append("No use of its products in the field is documented. Handovers to military units are "
                               "reported by donors and do not show use.")


def render(pg, out, chains):
    e = pg.e
    n = display_name(e)
    legal = n["legal"] or n["head"]
    img_dir = pg.img_dir = out.parent / "images" / "media"
    head = esc(latin_text(n["head"]) if n["legal"] else n["latin"])
    sub = (f'<p class="names"><span lang="ru-Latn">{esc(n["latin"])}</span> · <span lang="ru">{esc(legal)}</span></p>'
           if n["legal"] else f'<p class="names"><span lang="ru">{esc(legal)}</span></p>')
    logo = pg.logo(img_dir)
    dek = brief(e, pg.ref, pg.src)
    sections = [("Company register", pg.register()), ("Command" if pg.unit() else "Before the register was closed", pg.before()),
                ("People", pg.people_block()), ("Where it is", pg.place()), ("Sanctions", pg.sanctions_block()),
                ("Timeline", pg.timeline()), ("Annual accounts", pg.accounts()),
                ("Products", pg.products_block(chains)), ("Handovers it reports", pg.handovers()), ("Reported by others", pg.reported_by_others(img_dir)),
                ("Pictures", pg.pictures(img_dir)), ("In its own words", pg.own_words()), ("Trademarks and patents", pg.ip_block()),
                ("Links to TsBST and the state", pg.network()), ("Sellers of its products", pg.sellers())]
    pg.gaps()
    shown = [(t, h) for t, h in sections if h]
    sid = lambda t: "s-" + re.sub(r"[^a-z]+", "-", t.lower()).strip("-")
    body = "".join(f'<section class="sec" id="{sid(t)}"><h2 class="rm-h2">{t}</h2>{h}</section>' for t, h in shown)
    from build_landing import TOC_JS  # noqa: E402  (the landing's contents-bar script)
    toc = ('<nav class="toc" aria-label="Contents"><ol><li><a href="' + LANDING_URL + '" target="_blank" rel="noopener">← Overview</a></li>'
           + "".join(f'<li><a href="#{sid(t)}">{esc(t)}</a></li>' for t, _ in shown)
           + '<li><a href="#s-limits">Limits</a></li><li><a href="#s-sources">Sources</a></li></ol></nav>')
    limits = "".join(f"<li>{x}</li>" for x in dict.fromkeys(pg.limits))
    notes = "".join(
        f'<li id="n{k}">{esc(t)}.' + (f' <a href="{esc(u)}" target="_blank" rel="noopener">'
                                      f'{esc(re.sub(r"^https?://(www[.])?", "", u).split("/")[0])} ↗</a>' if u else "") + "</li>"
        for k, (t, u) in enumerate(pg.notes, 1))
    css = """
.top { padding-top: 32px; }
.co-head { display: flex; align-items: flex-start; gap: 16px; flex-wrap: wrap; }
.co-head .co-logo { height: 40px; max-width: 160px; object-fit: contain; background: var(--logo-plate); border: 1px solid var(--rule-soft);
  border-radius: 3px; padding: 4px 6px; }
.co-head .co-logo.on-dark { background: var(--logo-plate-dark); }
.names { margin: 0 0 var(--space-4); font: 400 13px/1.4 var(--font-mono); color: var(--ink-3); }
.body { display: grid; grid-template-columns: minmax(0, 1fr); gap: 8px; max-width: 900px; }
.sec { border-top: 1px solid var(--rule); padding-top: 18px; margin-top: 18px; }
.facts { display: grid; grid-template-columns: max-content minmax(0, 1fr); gap: 8px 20px; margin: 0; font-size: 14px; }
.facts dt { font: 600 var(--t-label)/1.6 var(--font-mono); letter-spacing: .06em; text-transform: uppercase; color: var(--ink-3); }
.facts dd { margin: 0; color: var(--ink-2); overflow-wrap: anywhere; }
ul.plain { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; font-size: 14px; color: var(--ink-2); }
.cyr { font-size: 12.5px; color: var(--ink-3); }
.sanc { margin: 0 0 6px; }
.tbl { overflow-x: auto; }
table { border-collapse: collapse; font-size: 14px; }
th, td { text-align: left; padding: 6px 14px 6px 0; border-bottom: 1px solid var(--rule-soft); }
th { font: 600 var(--t-label)/1.4 var(--font-mono); letter-spacing: .06em; text-transform: uppercase; color: var(--ink-3); }
.num { text-align: right; font-variant-numeric: tabular-nums; }
.prose { margin-top: 40px; }
.prose ul { padding-left: 20px; color: var(--ink-2); font-size: 14px; }
.rm-sources { margin-bottom: 60px; }
.rm-quote { margin: 0 0 14px; max-width: 760px; }
.rm-quote .q { white-space: pre-line; display: block; }
.rm-gallery { max-width: 900px; }
.rm-gallery.even { grid-template-columns: repeat(2, minmax(0, 1fr)); }   /* two or four pictures: two a row, so none is left alone */
@media (max-width: 520px) { .rm-gallery.even { grid-template-columns: minmax(0, 1fr); } }
.lead-note { font-size: 13.5px; color: var(--ink-2); margin: 0 0 12px; }
.nolist { font-size: 13px; color: var(--ink-2); margin: 4px 0; }
ul.plain .nolist { margin: 2px 0 0; }
.rm-facility { margin-top: 12px; max-width: 640px; }
ol.tline { list-style: none; padding: 0; margin: 0; font-size: 14px; color: var(--ink-2); display: flex; flex-direction: column; gap: 6px; }
ol.tline li { display: grid; grid-template-columns: 92px minmax(0, 1fr); gap: 12px; }
ol.tline time { font: 400 12.5px/1.6 var(--font-mono); color: var(--ink-3); font-variant-numeric: tabular-nums; }
.tls-scroll { overflow-x: auto; margin: 0 0 var(--space-4); }
.tls { width: 100%; min-width: 640px; height: auto; display: block; }
.tls .yl { stroke: var(--rule-soft); }
.tls .yt { fill: var(--ink-3); font: 500 11px var(--font-mono); }
.tls .ln { fill: var(--ink-2); font: 500 12px var(--font-sans); }
.tls .lr { stroke: var(--rule); }
.tls .ev { fill: var(--panel); stroke: var(--ink-2); stroke-width: 1.5; }
.tls .ev.sanc { fill: var(--sanction-bg); stroke: var(--sanction); }
.tls .en { fill: var(--ink); font: 600 9px var(--font-mono); text-anchor: middle; pointer-events: none; }
.tls a:hover .ev { stroke: var(--accent); stroke-width: 2.2; }
ol.tline li:target { background: var(--accent-soft); }
@media (max-width: 600px) { .facts { grid-template-columns: 1fr; gap: 2px 0; } .facts dd { margin-bottom: 8px; } }
"""
    doc = f"""<!doctype html>
<!-- Generated by exhibits/build_company_page.py {esc(e['slug'])} from data/registry on {dt.date.today().isoformat()}. Do not edit by hand. -->
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{head}: Company File</title>
{design_head(css)}</head>
<body>
{toc}
<header class="rm-page top">
  <p class="rm-eyebrow">Company · Draft · {ru_date(dt.date.today().isoformat())}</p>
  <div class="co-head"><h1 class="rm-h1">{head}</h1>{logo}</div>
  {sub}
  <p class="rm-dek">{dek}</p>
</header>
<main class="rm-page"><div class="body">
  {body}
  <section class="prose rm-prose" id="s-limits"><h2 class="rm-h2">What this page does not show</h2><ul>{limits}</ul>
  <p class="rm-muted" style="font-size:13.5px">Facts here come from documents: the company register, its filed accounts,
  the patent and trademark registers, sanctions lists and its own posts. Entries resting on anything weaker are marked
  Reported and named above.</p></section>
  <section class="prose rm-prose rm-sources" id="s-sources"><h2 class="rm-h2">Sources</h2><ol>{notes}</ol></section>
</div></main>
<script>{NAME_JS}</script>
<script>{TOC_JS}</script>
</body></html>
"""
    out.write_text(popup_originals(doc))
    print(f"wrote {out.relative_to(REPO) if out.is_relative_to(REPO) else out}: {len(pg.notes)} sources, {len(pg.limits)} limits")
    for rel, _ in pg.media_files:
        print("  picture", rel)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--out")
    a = ap.parse_args()
    out = Path(a.out) if a.out else REPO / "exhibits" / f"company_{a.slug}.html"
    from build_landing import CHAINS  # noqa: E402  (chain view preview links)
    render(Page(a.slug), out, CHAINS)


if __name__ == "__main__":
    main()
