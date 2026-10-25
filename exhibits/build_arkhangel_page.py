#!/usr/bin/env python3
"""Project file for «Arkhangel» (Proekt KB «Arkhangel»): what the project says it builds, who it trains, the parts
its own bill of materials names, and its own pictures.

    python3 exhibits/build_arkhangel_page.py      # -> exhibits/arkhangel.html, pictures in exhibits/images/media/

Replaces the hand-made exhibits/archive/retired_2026-10-24/arkhangel_exhibit.html (21.09.2026) on the reader design system and the
English-first rule: every fact from data/registry, footnoted in plain words; quotations in English with the
Russian under RU. The silhouette is redrawn from the project's own CAD and bench stills; it states no dimension,
wiring, print setting or assembly order. Local file processing only.
"""
import datetime as dt
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "exhibits"))
sys.path.insert(0, str(REPO / "scripts"))
from build_chain_view import CBST, describe_source, esc, load  # noqa: E402
from display_helpers import (NAME_JS, caption_html, design_head, display_name, figure_html, latin_text,  # noqa: E402
                             latinize_gloss, load_media, name_html, person_names, popup_originals, quote_html,
                             reader_grade, ru_date, translation)

SLUG = "proekt-kb-arkhangel"
LEADER = "filippov-mikhail-gennadevich"
# The project's own words, grouped by what they show. Keyed by (source, first words of the Russian). Build
# instructions that only help assemble the device (where to put the payload weight) are left out on purpose.
GROUPS = [
    ("It trains drone operators for the army", [("s7651", ""), ("s7650", ""), ("s7654", ""), ("s7649", ""), ("s7648", ""),
                                                ("s7907", "«Архангел» предлагает"), ("s7907", "образование")]),
    ("It builds an interceptor and says how it is armed", [("s5475", "Мы решили"), ("s5454", "В боевой"), ("s5454", "Гражданское"),
                                                          ("s7653", "скорость"), ("s7653", "Программа"), ("s7652", "")]),
    ("It recruits, and announced its own private military company", [("s5475", "К.Б."), ("s5475", "Архангел запускает"),
                                                                       ("s5475", "Группа компаний"), ("s5463", "")]),
    ("Weapons tested around it", [("s5457", "")]),
    ("Who it works with", [("s7693", ""), ("s7694", ""), ("s7704", ""), ("s7705", "")]),
    ("Designs it gives away", [("s7655", "")]),
]
LEFT_OUT = ("s7653", "Дрон нужно загружать")
# Bill-of-materials parts -> the numbered callout on the silhouette (0 = the body itself, None = not on this drone)
CALLOUT = [("Brotherhobby", 1), ("GEPRC", 2), ("Caddx", 3), ("SpeedyBee", 4), ("BEASTFPV", 4), ("Betaflight", 4),
           ("Gaoneng", 5), ("Bambu", 0), ("SolidWorks", 0), ("Ночник", None)]
REL_EN = {"training-partnership": "trains with it", "component-supplier": "supplies components"}

SILHOUETTE = """<svg viewBox="0 0 400 460" role="img" aria-label="Silhouette redrawn from the project's CAD and bench stills, with numbered parts" class="sil">
<defs><linearGradient id="tube" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#3a3f45"/><stop offset=".5" stop-color="#5c6169"/><stop offset="1" stop-color="#2c3035"/></linearGradient>
<linearGradient id="fin" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#4a4f56"/><stop offset="1" stop-color="#24272b"/></linearGradient></defs>
<g fill="url(#fin)" stroke="#15171a" stroke-width="1.5"><path d="M180 260 L60 400 L85 415 L192 300 Z"/><path d="M220 260 L340 400 L315 415 L208 300 Z"/>
<path d="M175 270 L70 320 L82 345 L185 305 Z" opacity=".85"/><path d="M225 270 L330 320 L318 345 L215 305 Z" opacity=".85"/></g>
<g class="mot"><circle cx="66" cy="405" r="15"/><circle cx="334" cy="405" r="15"/><circle cx="76" cy="330" r="12"/><circle cx="324" cy="330" r="12"/></g>
<g class="prop"><circle cx="66" cy="405" r="28"/><circle cx="334" cy="405" r="28"/><circle cx="76" cy="330" r="22"/><circle cx="324" cy="330" r="22"/></g>
<path d="M172 100 Q170 90 200 60 Q230 90 228 100 L232 270 Q200 285 168 270 Z" fill="url(#tube)" stroke="#15171a" stroke-width="2"/>
<text x="200" y="230" class="emb" lang="ru" transform="rotate(-90 200 230)">АРХАНГЕЛ</text>
<circle cx="200" cy="80" r="10" class="part"/><circle cx="200" cy="80" r="4" class="dot"/>
<line x1="200" y1="62" x2="200" y2="30" class="ant"/><circle cx="200" cy="27" r="4" class="dot"/>
<rect x="181" y="150" width="38" height="26" rx="3" class="part"/><rect x="177" y="185" width="46" height="42" rx="4" class="part"/>
<rect x="180" y="230" width="40" height="42" rx="3" class="war"/>
<g class="co">
<line x1="66" y1="405" x2="18" y2="440"/><circle cx="18" cy="440" r="11"/><text x="18" y="444">1</text>
<line x1="334" y1="405" x2="382" y2="440"/><circle cx="382" cy="440" r="11"/><text x="382" y="444">1</text>
<line x1="200" y1="27" x2="200" y2="16"/><circle cx="200" cy="16" r="11"/><text x="200" y="20">2</text>
<line x1="200" y1="80" x2="340" y2="70"/><circle cx="360" cy="70" r="11"/><text x="360" y="74">3</text>
<line x1="200" y1="163" x2="360" y2="163"/><circle cx="380" cy="163" r="11"/><text x="380" y="167">4</text>
<line x1="200" y1="206" x2="20" y2="206"/><circle cx="18" cy="206" r="11"/><text x="18" y="210">5</text>
<line x1="200" y1="251" x2="20" y2="270"/><circle cx="18" cy="270" r="11" class="w"/><text x="18" y="274">6</text>
</g></svg>"""


class Page:
    def __init__(self, img_dir):
        self.ents = {e["slug"]: e for e in load("entities.json")}
        self.people = {p["slug"]: p for p in load("people.json")}
        self.src = {s["id"]: s for s in load("sources.json")}
        self.e = self.ents[SLUG]
        self.media = load_media()
        self.img_dir = img_dir
        self.files = []
        self.notes, self.pops = [], 0

    def ref(self, *sids):
        nums = []
        for s in sids:
            if not s or s not in self.src:
                continue
            s = self.src[s].get("duplicate_of") or s
            d = describe_source(self.src[s])
            if d not in self.notes:
                self.notes.append(d)
            nums.append(self.notes.index(d) + 1)
        return ("<sup class=\"rm-ref\">" + ",".join(f'<a href="#n{n}">{n}</a>' for n in sorted(set(nums))) + "</sup>") if nums else ""

    def pop(self, vis, ru, what="Original name of"):
        self.pops += 1
        return name_html(vis, ru, key=f"ar-{self.pops}", what=what)

    def ent(self, e):
        n = display_name(e)
        legal = n["legal"] or n["head"]
        return self.pop(latin_text(n["head"]) if n["legal"] else n["latin"], legal)

    # -- sections -----------------------------------------------------------------------
    def who(self):
        p = self.people[LEADER]
        pn = person_names(p["fio_ru"], p.get("name_latin"))
        r = next(r for r in p.get("roles") or [] if r.get("entity_slug") == SLUG)
        own = next((r for r in p.get("roles") or [] if "80%" in (r.get("title") or "")), None)
        out = (f'<p>The channel names {self.pop(pn["first"], pn["fio"])} as the project\'s head.{self.ref(r.get("source_id"))} '
               "No company register entry for the project itself is on file: it works through its Telegram channels.")
        if own:
            oe = self.ents.get(own["entity_slug"])
            out += (f' {pn["surname"]} holds 80% of {self.ent(oe) if oe else esc(latin_text(own["entity_name"]))}'
                    f', registered {ru_date(own.get("from"))}.{self.ref(own.get("source_id"))}')
        out += "</p>"
        href, m = self.mark("m0095")
        lhref, lm = self.mark("m0096")
        return (f'{out}<div class="head-card"><figure class="head-pic"><img src="{href}" alt="{esc(m["shows_en"])}" width="544" height="848">'
                f'<figcaption>A frame of the video in the project\'s post of 23.10.2026, which is signed with his name as head of the project.'
                f'{self.ref(m.get("source_id"))}</figcaption></figure>'
                f'<figure class="head-pic logo"><img src="{lhref}" alt="{esc(lm["shows_en"])}" width="320" height="320">'
                f'<figcaption>The project\'s channel emblem, its public profile picture.{self.ref(lm.get("source_id"))}</figcaption></figure></div>')

    def tie(self):
        t = self.e.get("cbst_tie") or {}
        g = reader_grade(t.get("confidence"))
        label = {"doc": "Documented", "rep": "Reported", "open": "Not documented"}[g]
        return (f'<p><span class="rm-grade {g}">{label}</span> TsBST\'s own channel names the project\'s school in Tuapse as a site '
                "running a TsBST resident's drone-interception training mode. That makes the school a user of a resident's "
                f"product; it does not make the project a resident.{self.ref(t.get('source_id'))}</p>")

    def tref(self, key):
        """A note for a post or page read in full but not catalogued on this machine: plain words and its public link."""
        from build_landing import OPENING_SOURCES   # lazy: the landing builder is heavy and not needed elsewhere
        note = OPENING_SOURCES[key]
        if note not in self.notes:
            self.notes.append(note)
        return f'<sup class="rm-ref"><a href="#n{self.notes.index(note) + 1}">{self.notes.index(note) + 1}</a></sup>'

    def circle(self):
        """Where the project meets TsBST's circle and the 205th brigade: the school's recruitment, Bars-Sarmat, DW's film,
        and the Kvadrosim / Shatrakova link. Moved here from the landing page, which keeps one paragraph and two quotes."""
        from build_landing import OPENING_QUOTES
        def q(key, cite):
            _, _, ru, en = OPENING_QUOTES[key]
            return quote_html(ru, en, cite, key=f"ci-{key}", strong=True)
        sh = self.people.get("shatrakova-anastasiya-artemovna")
        shn = person_names(sh["fio_ru"], sh.get("name_latin")) if sh else None
        shat = self.pop(shn["first"] if shn else "Anastasiya Shatrakova", sh["fio_ru"] if sh else "Анастасия Шатракова")
        return (
            '<p>The project\'s channel recruits operators for the 205th Guards Separate Motor Rifle Brigade, which Russian-language '
            f'channels place in the 49th Army of the «Dnepr» Group of Forces{self.tref("osv_27702")}. Its own words:</p>'
            + q("arch_9067", f'The project\'s channel, 01.12.2025{self.tref("arch_9067")}')
            + q("arch_10667", f'The project\'s channel, 17.08.2026{self.tref("arch_10667")}')
            + f'<p>The school says it trains within Bars-Sarmat, Dmitry Rogozin\'s drone centre.{self.ref("s6915")}</p>'
            + '<p>DW\'s film on the drone attacks in Beryslav shows the school too: over footage of men soldering a drone, '
              'watermarked with the school\'s channel address, the narration says “This Russian volunteer group proudly posts on '
              f'Telegram” how it makes drones and trains operators{self.tref("dw_film")}. The film does not say the school supplied '
              'the 205th, and the footage of the attacks it shows is credited to another channel. It does not show the school\'s '
              'tie to TsBST.</p>'
            + '<p>The school\'s forum channel calls Kvadrosim, the simulator maker TsBST names as a resident, “our partners”, and '
              f'says the heads of its Moscow branch, among them {shat}, presented an interceptor called «Arkhangel» to a security '
              f'agency together with that company{self.tref("arch_175293")}. TsBST\'s own post names an Anastasia Shatrakova as '
              f'general director of the interceptor maker «Arkhangel», a finalist of its accelerator{self.tref("cbst_1976")}, and '
              f'the company register lists a person of that name as director of OOO «Arkhangel» since it was registered'
              f'{self.ref("s5507")}. The name and the product match, so the records are read as one person. No document links '
              'that company to the school.</p>')

    def partners(self):
        items = []
        for r in self.e.get("related_entities") or []:
            o = self.ents.get(r["slug"])
            if not o:
                continue
            items.append(f'<li>{self.ent(o)}: {esc(REL_EN.get(r.get("relationship_type"), "linked"))}{self.ref(r.get("source_id"))}</li>')
        return f'<ul class="plain">{"".join(items)}</ul>'

    def products(self):
        out = []
        for p in self.e.get("products") or []:
            d = re.sub(r'"[^"]*[А-Яа-яЁё][^"]*"\s*\(([^)]*)\)', r"“\1”", p.get("description") or "")
            d = re.sub(r'\s*\((?:"[^"]*[А-Яа-яЁё][^"]*"|[^()]*«[^»]*[А-Яа-яЁё][^»]*»[^()]*)\)', "", d)   # a Russian phrase we already paraphrase
            d = re.sub(r'\s*\((?:[^()]*\bs\d{4}\b[^()]*)\)', "", d)          # our own notes that cite a source id
            d = re.sub(r"\bs\d{4}\b", "", d)
            sent = re.split(r"(?<=[.!?])\s+", d)
            d = " ".join(sent[:2])
            name = p["name_ru"].split(" — ")[0]
            tr = translation(name)
            out.append(f'<li><h3 class="rm-name">{self.pop(tr["en"] if tr else latin_text(name), p["name_ru"])}</h3>'
                       f'<p>{caption_html(d, "pd-" + str(len(out)))}{self.ref(p.get("source_id"))}</p></li>')
        return f'<ul class="prods">{"".join(out)}</ul>'

    def bom(self):
        rows = []
        for c in self.e.get("foreign_components") or []:
            num = next((n for k, n in CALLOUT if k.lower() in (c.get("name") or "").lower()), None)
            if num is None and "Ночник" in (c.get("name") or ""):
                continue
            mark = "body" if num == 0 else (str(num) if num else "")
            seen = "seen in the video" if (c.get("context") or "").startswith("Seen, not stated") else "named in the parts list"
            rows.append((num if num is not None else 9, f'<tr><td class="no">{esc(mark)}</td><td>{esc(latinize_gloss(c.get("name")))}</td>'
                        f'<td>{esc(latinize_gloss(c.get("manufacturer")))}</td><td>{seen}{self.ref(c.get("source_id"))}</td></tr>'))
        rows.sort(key=lambda r: (r[0] if r[0] else 0))
        body = "".join(r for _, r in rows)
        china = sum(1 for c in self.e.get("foreign_components") or [] if "China" in (c.get("manufacturer") or ""))
        return body, china

    def own_words(self):
        claims = {}
        for c in self.e.get("marketing_claims") or []:
            claims.setdefault(c["source_id"], []).append(c)
        used, out = set(), []
        for title, keys in GROUPS:
            qs = []
            for sid, start in keys:
                for c in claims.get(sid, []):
                    if id(c) in used or not c["text_ru"].startswith(start):
                        continue
                    if (c["source_id"], c["text_ru"][:len(LEFT_OUT[1])]) == LEFT_OUT:
                        continue
                    used.add(id(c))
                    ru = re.sub(r"\+7\d[\d ()-]{8,}", "[…]", c["text_ru"])
                    cite = f'The project\'s own channel, {ru_date(c.get("as_of"))}{self.ref(c["source_id"])}'
                    if sid == "s5457":
                        cite = f'A member of the project\'s private training chat, {ru_date(c.get("as_of"))}{self.ref(c["source_id"])}'
                    qs.append(quote_html(ru, latinize_gloss(c.get("text_en") or ""), cite, key=f"aw-{len(used)}"))
                    break
            if qs:
                out.append(f'<h3 class="rm-h3">{esc(title)}</h3>' + "".join(qs))
        return "".join(out)

    def mark(self, mid):
        """The path of a mark or portrait shown beside the text (logo, headshot), copied into the page's image folder."""
        m = next(m for m in self.media if m["id"] == mid)
        src = REPO / m["file"]
        name = f'{mid}{src.suffix}'
        if self.img_dir:
            self.img_dir.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, self.img_dir / name)
        self.files.append(name)
        return f"images/media/{name}", m

    def pictures(self):
        figs = []
        for m in self.media:
            if m.get("genre") in ("logo", "portrait"):
                continue
            if not any(a.get("type") == "entity" and a.get("id") == SLUG for a in m.get("about") or []):
                continue
            if m.get("publish") not in ("ok", "excerpt"):
                continue
            src = REPO / (m.get("file") or "")
            if not src.exists():
                continue
            name = f'{m["id"]}{src.suffix}'
            if self.img_dir:
                self.img_dir.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src, self.img_dir / name)
            self.files.append(name)
            m = dict(m, shows=re.sub(r"\s*\(see open questions\)", "", m.get("shows") or ""))
            figs.append(figure_html(m, f"images/media/{name}", "the project", self.ref(m.get("source_id"))))
        return "".join(figs)

    def notes_list(self):
        out = []
        for n, (text, url) in enumerate(self.notes, 1):
            short = re.sub(r"^https?://(www\.)?", "", url or "").rstrip("/")
            short = short if len(short) <= 40 else short.split("/")[0]
            link = f' <a href="{esc(url)}" target="_blank" rel="noopener">{esc(short)} ↗</a>' if url else ""
            out.append(f'<li id="n{n}">{esc(text)}.{link}</li>')
        return "".join(out)


CSS = """
/* Project file layout. Tokens and shared components come from design/roymarket.css. */
.top { padding-top: 36px; }
main.rm-page { display: flex; flex-direction: column; gap: var(--space-6); padding-bottom: 64px; }
main section > .rm-h2 { margin-top: 0; }
.lede, section > p { max-width: var(--measure); color: var(--ink-2); }
.rm-h3 { font: 500 18px/1.3 var(--font-serif); margin: var(--space-4) 0 var(--space-2); }
.figs { display: flex; flex-wrap: wrap; gap: 10px 36px; margin: var(--space-3) 0 0; }
.fig { display: flex; flex-direction: column; gap: 2px; max-width: 220px; }
.fig .n { font: 500 30px/1.1 var(--font-serif); font-variant-numeric: tabular-nums; color: var(--ink); }
.fig .w { font-size: var(--t-note); color: var(--ink-2); }
.build { display: grid; grid-template-columns: minmax(240px, 360px) minmax(0, 1fr); gap: var(--space-5); align-items: start; }
.sil { width: 100%; height: auto; background: var(--panel-2); border-radius: var(--radius); }
.sil .mot circle { fill: #1c1e21; stroke: var(--accent); stroke-width: 2; }
.sil .prop circle { fill: none; stroke: #6b7683; stroke-width: 1.2; opacity: .6; }
.sil .emb { font: 700 17px var(--font-sans); fill: #8b9096; text-anchor: middle; letter-spacing: 2px; }
.sil .part { fill: #101113; stroke: var(--accent); stroke-width: 1.8; }
.sil .dot { fill: var(--accent); }
.sil .ant { stroke: var(--accent); stroke-width: 2; }
.sil .war { fill: var(--g-rep-bg); stroke: var(--g-rep); stroke-width: 2; stroke-dasharray: 4 3; }
.sil .co line { stroke: var(--ink-3); stroke-width: 1; }
.sil .co circle { fill: var(--accent); }
.sil .co circle.w { fill: var(--g-rep); }
.sil .co text { font: 600 13px var(--font-mono); fill: var(--paper); text-anchor: middle; }
.sil-note { font-size: 12.5px; color: var(--ink-3); margin: 6px 0 0; }
.bomwrap { overflow-x: auto; }
table.bom { border-collapse: collapse; width: 100%; font-size: var(--t-note); }
table.bom th { text-align: left; font: 600 10.5px/1.3 var(--font-mono); letter-spacing: .06em; text-transform: uppercase; color: var(--ink-3);
  padding: 6px 10px 6px 0; border-bottom: 1px solid var(--rule); }
table.bom td { padding: 7px 10px 7px 0; border-bottom: 1px solid var(--rule-soft); color: var(--ink-2); vertical-align: top; }
table.bom td:nth-child(2) { color: var(--ink); }
table.bom td.no { font: 600 12px var(--font-mono); color: var(--accent); width: 3.5em; }
.prods { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: var(--space-3); }
.prods li { background: var(--panel); border: 1px solid var(--rule); border-radius: var(--radius); padding: 10px 12px; min-width: 0; }
.prods p { margin: 6px 0 0; font-size: var(--t-note); color: var(--ink-2); }
.rm-quote { max-width: 760px; margin: 0 0 var(--space-3); }
ul.plain { padding-left: 20px; color: var(--ink-2); max-width: var(--measure); }
ul.plain li { margin: 4px 0; }
.top { padding-bottom: var(--space-5); }
.head-card { display: flex; flex-wrap: wrap; align-items: flex-start; gap: var(--space-4) var(--space-5); margin-bottom: var(--space-4); }
.head-pic { margin: 0; width: 240px; max-width: 100%; }
.head-pic img { display: block; width: 100%; height: auto; border-radius: var(--radius); border: 1px solid var(--rule); background: #fff; }
.head-pic.logo img { aspect-ratio: 1; object-fit: cover; border-radius: 50%; }
.head-pic figcaption { font-size: var(--t-note); color: var(--ink-3); margin-top: 6px; }
.rm-gallery { grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); }
.prose ul { padding-left: 20px; color: var(--ink-2); max-width: var(--measure); }
@media (max-width: 760px) { .build { grid-template-columns: minmax(0, 1fr); } }
"""


def render(out: Path):
    P = Page(out.parent / "images" / "media")
    today = dt.date.today().isoformat()
    e = P.e
    # called in page order so the footnotes number from the top
    who, tie = P.who(), P.tie()
    circle = P.circle()
    pics = P.pictures()
    bom, china = P.bom()
    prods, words, partners = P.products(), P.own_words(), P.partners()
    n_claims = len(e.get("marketing_claims") or []) - 1
    doc = f"""<!doctype html>
<!-- Generated by exhibits/build_arkhangel_page.py from data/registry on {today}. Do not edit by hand. -->
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Arkhangel: Project File</title>
{design_head(CSS)}</head>
<body>
<header class="rm-page top">
  <p class="rm-eyebrow">Draft · Project file · {ru_date(today)}</p>
  <h1 class="rm-h1">«Arkhangel» <span class="rm-muted">a drone school and design bureau that trains operators for the army and gives away an armed interceptor's build files</span></h1>
  <p class="rm-dek">{P.pop("Proekt KB «Arkhangel»", e["name_ru"])} works through Telegram. Its own posts say it trains drone and
  air-defence operators for named army units, builds an interceptor drone with a declared combat version, and publishes the
  drone's parts list. Almost every part in that list is made in China.</p>
</header>
<main class="rm-page">
  <section aria-labelledby="h-who"><h2 class="rm-h2" id="h-who">Who runs it, and its link to TsBST</h2>{who}{tie}</section>
  <section aria-labelledby="h-circle"><h2 class="rm-h2" id="h-circle">Where it meets TsBST's circle and the 205th brigade</h2>{circle}
    <p class="note"><span class="rm-grade rep">Reported</span> The school's, TsBST's and the register's own text, joined by a name. The
    school's tie to TsBST is still not documented.</p></section>
  <section aria-labelledby="h-pics"><h2 class="rm-h2" id="h-pics">Its own pictures</h2>
    <p>Stills from the project's own posts and videos: the build bench, the airframe in CAD, the flight controller, an
    observation device it released, and a recruitment video.</p>
    <div class="rm-gallery">{pics}</div></section>
  <section aria-labelledby="h-build"><h2 class="rm-h2" id="h-build">What the interceptor is made of</h2>
    <p>The project published a parts list for its interceptor and a 32-minute build video. The parts are off-the-shelf
    hobby components. The drawing marks where each sits; the table says who makes it.</p>
    <div class="build"><figure style="margin:0">{SILHOUETTE}
      <figcaption class="sil-note">Silhouette redrawn from the project's own CAD and bench stills above. Not to scale; it states no
      dimension, wiring, print setting or assembly order. Part 6 is the warhead cylinder of the declared combat version.</figcaption></figure>
      <div class="bomwrap"><table class="bom"><thead><tr><th>Part</th><th>Component</th><th>Maker</th><th>How we know</th></tr></thead>
      <tbody>{bom}<tr><td class="no">6</td><td>Warhead cylinder (combat version)</td><td>the project</td><td>its own build post, quoted below</td></tr></tbody></table></div></div></section>
  <section aria-labelledby="h-prod"><h2 class="rm-h2" id="h-prod">What it says it makes</h2>{prods}</section>
  <section aria-labelledby="h-words"><h2 class="rm-h2" id="h-words">In its own words</h2>
    <p>Translations of the project's posts, grouped by what they show. The Russian original of each is under RU.</p>{words}</section>
  <section aria-labelledby="h-part"><h2 class="rm-h2" id="h-part">Organisations it names as partners</h2>{partners}</section>
  <section class="prose rm-prose"><h2 class="rm-h2">What this does not show</h2><ul>
    <li>No legal entity for the project itself is on file. Who owns the brand, the school and the equipment is not documented here.</li>
    <li>Every statement about training, units and the drone's performance is the project's own. None is confirmed by the units named.</li>
    <li>The parts list shows what the project says it uses. It does not show who sold the parts to it or how many drones were built.</li>
    <li>One instruction on how to load the drone is left out on purpose. The page is not sufficient to build the device it describes.</li>
    <li>The tie to TsBST is one mention of the project's school as a user of a TsBST resident's product, and the school's forum calling that resident a partner.</li>
  </ul></section>
  <section class="prose rm-prose rm-sources"><h2 class="rm-h2">Sources</h2><ol>{P.notes_list()}</ol></section>
</main>
<script>{NAME_JS}</script>
</body></html>
"""
    out.write_text(popup_originals(doc))
    print(f"wrote {out.relative_to(REPO) if out.is_relative_to(REPO) else out}: {len(P.notes)} sources, {len(P.files)} pictures")
    return P


if __name__ == "__main__":
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
    render(Path(out).resolve() if out else REPO / "exhibits" / "arkhangel.html")
