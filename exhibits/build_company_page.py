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
from display_helpers import (NAME_JS, design_head, display_name, latin_text, load_media, media_about, name_html,  # noqa: E402
                             person_names, publish_copy, reader_grade, ru_date, translation)
from build_chain_view import REGIMES, ROLE_EN, describe_source, esc, load, money  # noqa: E402

# Published company pages (private preview Artifacts until the public cutoff), as CHAINS in build_landing.py.
COMPANY_PAGES = {"ooo-trimiks": "https://claude.ai/artifact/GVG9YdHZVHPZNtKqBoZqEc"}
CITY_EN = {"St Petersburg": "St Petersburg", "Санкт-Петербург": "St Petersburg", "Москва": "Moscow"}


def regimes(e):
    """[(label, [source ids])] in first-seen order, from the entity's sanctions[] entries."""
    out = {}
    for s in e.get("sanctions") or []:
        regs = s.get("regime") or []
        for r in regs if isinstance(regs, list) else [regs]:
            label = next((lab for key, lab in REGIMES if key in r), None)
            if label:
                out.setdefault(label, []).append(s.get("source_id"))
    return list(out.items())


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
        self.products = load("products.json")
        self.programs = {p["slug"]: p for p in load("programs.json")}
        self.notes = []
        self.limits = []
        self.media = load_media()
        self.media_files = []

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
        rows.append(("ИНН", f'<span class="rm-id">{esc(e.get("inn"))}</span>' if e.get("inn") else ""))
        rows.append(("ОГРН", f'<span class="rm-id">{esc(e.get("ogrn"))}</span>' if e.get("ogrn") else ""))
        if e.get("registered"):
            rows.append(("Registered", f'{esc(e["registered"])}{self.ref(reg_src)}'))
        addr = next((h for h in sorted(e.get("address_history") or [], key=lambda h: h.get("as_of") or "", reverse=True)
                     if self.doc(h.get("source_id"))), None)
        if addr:
            rows.append(("Registered address", f'<span lang="ru">{esc(addr["value"])}</span>{self.ref(addr["source_id"])}'))
        if e.get("okved_code"):
            rows.append(("Main activity code", f'{esc(e["okved_code"])}, in the register\'s words '
                         f'<span lang="ru">«{esc(e.get("okved_label"))}»</span>{self.ref(reg_src)}'))
        cap_ = next((h for h in e.get("charter_capital_history") or [] if self.doc(h.get("source_id"))), None)
        if cap_:
            rows.append(("Charter capital", f'{money(cap_["value"])}{self.ref(cap_["source_id"])}'))
        r = restricted(e, self.src)
        if r:
            rows.append(("Owners and director", f'Hidden in the register since {ru_date(r["as_of"])}{self.ref(r["source_id"])}'))
        hidden = [h for k in ("director_history", "founders_history", "name_history")
                  for h in e.get(k) or [] if h.get("source_id") and not self.doc(h["source_id"])
                  and "restricted" not in (h.get("value") or "").lower()]
        if hidden:
            self.limits.append(f"{len(hidden)} earlier entries for the company's name, owners or director come from a "
                               "working file, not from a company register extract. They are left out until an extract "
                               "from before the register was closed confirms them.")
        return self.dl(rows)

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
        return f'<ul class="plain">{"".join(items)}</ul>' if items else "<p>No products recorded.</p>"

    def ip_block(self):
        items = []
        for t in self.e.get("trademarks") or []:
            num = t.get("reg_number") or t.get("application_number")
            kind = "Trademark no." if t.get("reg_number") else "Trademark application no."
            when = t.get("registered") or t.get("filed")
            when = f"{when[6:8]}.{when[4:6]}.{when[:4]}" if when and when.isdigit() and len(when) == 8 else (when or "")
            classes = sorted({c.split()[0] for c in t.get("goods_classes") or []} |
                             set(re.findall(r"(?:^|; )(\d{2}) \(", t.get("goods_classes_summary") or "")))
            items.append(f'<li>{kind} {esc(num)}{" «" + esc(t["title"]) + "»" if t.get("title") else ""}, '
                         f'{"registered" if t.get("registered") else "filed"} {when}'
                         f'{", classes " + ", ".join(classes) if classes else ""}{self.ref(t.get("source_id"))}</li>')
        for p in self.e.get("patents") or []:
            inv = [person_names(re.sub(r"\s*\(RU\)$", "", i)) for i in p.get("inventors") or []]
            invs = "; ".join(f'{esc(i["first"])} (<span lang="ru">{esc(i["fio"])}</span>)' for i in inv)
            pub = (p.get("published") or "").replace(".", "-")
            items.append(f'<li>Patent {esc(p.get("reg_number"))}, published {ru_date(pub)}: '
                         f'<span lang="ru">«{esc((p.get("title") or "").capitalize())}»</span>'
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
                items.append(f'<li>{esc(sp["name_en"])}, {when}{self.ref(sp.get("source_id"))}</li>')
        if not e.get("memberships"):
            self.limits.append("No document records the company as a formal member of a TsBST programme. Its link to "
                               "TsBST rests on the posts and statements cited here.")
        return f'<ul class="plain">{"".join(items)}</ul>' if items else "<p>None recorded.</p>"

    def sellers(self):
        items = []
        for s in self.ents.values():
            for sf in s.get("sells_for") or []:
                if sf.get("slug") != self.e["slug"]:
                    continue
                how = {"yes": "named as a dealer on the maker's website", "no": "not authorised by the maker"}.get(
                    sf.get("authorised"), "not on the maker's dealer list")
                items.append(f'<li>{self.en(s)}: {esc(how)}{self.ref(sf.get("source_id"))}</li>')
        return f'<ul class="plain">{"".join(items)}</ul>' if items else "<p>None recorded.</p>"

    def gaps(self):
        e = self.e
        if not e.get("foreign_components"):
            self.limits.append("No foreign components in its products are documented.")
        if not e.get("battlefield_evidence"):
            self.limits.append("No use of its products in the field is documented. Handovers to military units are "
                               "reported by donors and do not show use.")


def render(pg, out, chains):
    e = pg.e
    n = display_name(e)
    legal = n["legal"] or n["head"]
    img_dir = out.parent / "images" / "media"
    head = esc(latin_text(n["head"]) if n["legal"] else n["latin"])
    sub = (f'<p class="names"><span lang="ru-Latn">{esc(n["latin"])}</span> · <span lang="ru">{esc(legal)}</span></p>'
           if n["legal"] else f'<p class="names"><span lang="ru">{esc(legal)}</span></p>')
    logo = pg.logo(img_dir)
    dek = brief(e, pg.ref, pg.src)
    sections = [("Company register", pg.register()), ("Sanctions", pg.sanctions_block()), ("Annual accounts", pg.accounts()),
                ("Products", pg.products_block(chains)), ("Trademarks and patents", pg.ip_block()),
                ("Links to TsBST and the state", pg.network()), ("Sellers of its products", pg.sellers())]
    pg.gaps()
    body = "".join(f'<section class="sec"><h2 class="rm-h2">{t}</h2>{h}</section>' for t, h in sections)
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
@media (max-width: 600px) { .facts { grid-template-columns: 1fr; gap: 2px 0; } .facts dd { margin-bottom: 8px; } }
"""
    doc = f"""<!doctype html>
<!-- Generated by exhibits/build_company_page.py {esc(e['slug'])} from data/registry on {dt.date.today().isoformat()}. Do not edit by hand. -->
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{head}: Company File</title>
{design_head(css)}</head>
<body>
<header class="rm-page top">
  <p class="rm-eyebrow">Company · Draft · {ru_date(dt.date.today().isoformat())}</p>
  <div class="co-head"><h1 class="rm-h1">{head}</h1>{logo}</div>
  {sub}
  <p class="rm-dek">{dek}</p>
</header>
<main class="rm-page"><div class="body">
  {body}
  <section class="prose rm-prose"><h2 class="rm-h2">What this page does not show</h2><ul>{limits}</ul>
  <p class="rm-muted" style="font-size:13.5px">Facts here come from documents: the company register, its filed accounts,
  the patent and trademark registers, sanctions lists and its own posts. Entries resting on anything weaker are left out
  and counted above.</p></section>
  <section class="prose rm-prose rm-sources"><h2 class="rm-h2">Sources</h2><ol>{notes}</ol></section>
</div></main>
<script>{NAME_JS}</script>
</body></html>
"""
    out.write_text(doc)
    print(f"wrote {out.relative_to(REPO)}: {len(pg.notes)} sources, {len(pg.limits)} limits")
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
