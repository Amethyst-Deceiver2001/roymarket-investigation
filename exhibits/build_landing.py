#!/usr/bin/env python3
"""Landing page (plan A3): what the investigation shows, where to start, how to read it.

    python3 exhibits/build_landing.py             # -> exhibits/landing.html, chain links relative
    python3 exhibits/build_landing.py --preview   # chain links point at their private preview Artifacts

Generated from data/registry like the chain views, on the same design system, with the same
citation rules: no slugs, source ids, field or file names on the page; every claim carries a
numbered note in plain words. Counts are computed here, never typed in.
Local file processing only.
"""
import argparse
import datetime as dt
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "exhibits"))
sys.path.insert(0, str(REPO / "scripts"))
from build_chain_view import CBST, Chain, cap, esc, load, money  # noqa: E402
from display_helpers import design_head, display_name, reader_grade, ru_date  # noqa: E402

MPTM, NP, PSB, SIDYAKIN = "ooo-mptm", "fond-nasha-pravda", "pao-bank-psb", "aleksandr-sidyakin"
# One entry per published chain view: product slug -> private preview Artifact (until the public cutoff).
CHAINS = {"bulat": "https://claude.ai/artifact/6UaTv2jSwdNdfNUCibCwrf"}


def ln(grade, w=56):
    return (f'<svg class="ln" width="{w}" height="8" aria-hidden="true">'
            f'<line x1="0" x2="{w}" y1="4" y2="4" class="rm-ln {grade}"/></svg>')


def short(e):
    return e if isinstance(e, str) else display_name(e)["head"]


class Landing(Chain):
    """Reuses the chain view's notes, names, sanctions and logo; builds no chain itself."""

    def __init__(self):
        super().__init__("bulat")
        self.graph = json.loads((REPO / "data" / "registry" / "relationship_graph.json").read_text())
        self.img_dir = REPO / "exhibits" / "images" / "media"
        people = json.loads((REPO / "data" / "registry" / "people.json").read_text())
        self.people = {x["slug"]: x for x in (people if isinstance(people, list) else people.get("people", []))}

    def claim(self, slug, needle):
        return next(m for m in self.ents[slug].get("marketing_claims") or [] if needle in m["text_ru"])

    def board_role(self, person):
        """A person's role on ЦБСТ's supervisory board: (title, from, source_id)."""
        r = next(r for r in self.people[person].get("roles") or []
                 if r.get("entity_slug") == CBST and "Secretary" in (r.get("title") or ""))
        return r

    def hist(self, slug, field, value_part):
        return next((h for h in self.ents[slug].get(field) or [] if value_part in (h.get("value") or "")), {})

    def ledger(self):
        """Who stands behind ЦБСТ and what it holds: a short list of graded relations."""
        c, rows = self.ents[CBST], []
        np_f = self.hist(CBST, "founders_history", "Наша Правда")
        psb_f = self.hist(CBST, "founders_history", "ПСБ")
        reg = min((h["as_of"] for h in c.get("founders_history") or [] if h.get("as_of")), default=None)
        ur = self.claim(CBST, "Учредители ЦБСТ")
        rows.append(("Партия «Единая Россия»", "doc",
                     "named by ЦБСТ itself as one of its three founders, with ПСБ and Наша Правда; "
                     "the company register lists only those two", self.ref(ur["source_id"]), None))
        sid = self.board_role(SIDYAKIN)
        rows.append((self.people[SIDYAKIN]["fio_ru"].split()[0] + " " + self.people[SIDYAKIN]["fio_ru"].split()[2], "doc",
                     f"secretary of ЦБСТ's supervisory board since {ru_date(sid['from'])}, while head of United Russia's "
                     "central executive committee", self.ref(sid.get("source_id")), None))
        rows.append((self.ents[NP], "doc", f"co-founder of ЦБСТ since its registration on {ru_date(reg)}",
                     self.ref(np_f.get("source_id")), self.ents[CBST]))
        rows.append((self.ents[PSB], "doc", f"co-founder of ЦБСТ since {ru_date(psb_f.get('as_of'))}",
                     self.ref(psb_f.get("source_id")), self.ents[CBST]))
        sub = next(s for s in c.get("subsidiaries") or [] if s["slug"] == MPTM)
        tie = self.ents[MPTM].get("cbst_tie") or {}
        # The supplier offer is the document that names МПТМ as the platform's operator; it is also the source of
        # МПТМ's bank partner, so it is read from there rather than typed in.
        offer = next(pp["source_id"] for pp in self.ents[MPTM].get("platform_partners") or [] if pp.get("kind") == "bank")
        rows.append((self.ents[CBST], reader_grade(tie.get("confidence")),
                     f"lists ООО «МПТМ», in its report for 2025, as a company it has taken part in since {ru_date(sub['as_of'])}; "
                     "the size of its share is not stated",
                     self.ref(sub.get("source_id")), self.ents[MPTM]))
        rows.append((self.ents[MPTM], "doc", "the operator of the РОЙ.МАРКЕТ marketplace, by the platform's own supplier offer",
                     self.ref(offer), None))
        ds = [d for d in self.p.get("deliveries") or [] if d.get("donor") == NP]
        if ds:
            dates = sorted(d["date"] for d in ds if d.get("date"))
            rows.append((self.ents[NP], reader_grade(ds[0].get("credibility")),
                         f"reports handing «Булат» drone detectors to military units {len(ds)} times, "
                         f"{ru_date(dates[0])} to {ru_date(dates[-1])}; each handover is cited in the chain view",
                         self.ref(ds[0].get("source_id")), None))
        out = []
        for a, g, text, ref, b in rows:
            out.append(f'<li><span class="from">{esc(short(a))}</span>{ln(g)}<span class="what">{esc(text)}{ref}</span>'
                       f'<span class="rm-grade {g}">{esc({"doc": "Documented", "rep": "Reported", "open": "Not documented"}[g])}</span></li>')
        return "".join(out)

    def restricted(self):
        """The date from which the register withholds МПТМ's owners, with its source."""
        h = next((h for h in self.ents[MPTM].get("founders_history") or [] if "restricted" in (h.get("value") or "")), None)
        return (ru_date(h["as_of"]), self.ref(h.get("source_id"))) if h else (None, "")

    def quote(self):
        """Two sentences from Сидякин's post 618, in the post's order, recorded verbatim as claims on ЦБСТ and МПТМ."""
        a, b = self.claim(CBST, "поставили на фронт"), self.claim(MPTM, "военный маркетплейс")
        return a, b, self.ref(a["source_id"], b["source_id"])

    def money_line(self):
        fy = {}
        for f in self.ents[CBST].get("financials") or []:
            if f.get("funds_received") is not None:
                fy.setdefault(f["year"], f)
        parts = [f"{money(f['funds_received'])} in {y}{self.ref(f['source_id'])}" for y, f in sorted(fy.items())]
        return " and ".join(parts)

    def network(self):
        ties = [e for e in self.graph["edges"] if e["type"] == "cbst_tie"]
        slugs = {(e["source"] if CBST not in e["source"] else e["target"]).split("::")[-1]: reader_grade(e.get("confidence"))
                 for e in ties}
        by = {g: sum(1 for v in slugs.values() if v == g) for g in ("doc", "rep")}
        sanc = sum(1 for s in slugs if self.ents.get(s, {}).get("sanctions"))
        return len(slugs), by, sanc

    def chain_card(self, slug, href):
        """href None: the chain view is not public yet, so the card states that instead of linking."""
        ch = Chain(slug)
        ch.img_dir = REPO / "exhibits" / "images" / "media"   # the chain's own pictures never go to this page's folder
        ch.build()
        p, m = ch.p, ch.maker
        n_buy = sum(len([b for b in r["buyers"] if "k-buyer" in b]) for r in ch.rows)
        n_list = sum(1 for li in p.get("listings") or [] if li.get("source_id"))
        n_del = len(p.get("deliveries") or [])
        logo = self.logo(p["maker"])   # only the logo is published with this page
        regimes = self.sanctions(m)
        return (f'<article class="rm-card chain-card"><header><span class="rm-kind">Chain view</span>{logo}</header>'
                f'<h3 class="rm-name">{f"<a href={chr(34)}{esc(href)}{chr(34)}>{esc(ch.pq)}</a>" if href else esc(ch.pq)}<small>{esc(cap(p.get("category")))} made by '
                f'{esc(short(m))}{(" (" + esc(display_name(m)["legal"]) + ")") if display_name(m)["legal"] else ""}</small></h3>'
                f'{regimes}<dl class="counts"><div><dt>Sale channels</dt><dd>{len(ch.rows)}</dd></div>'
                f'<div><dt>Listings</dt><dd>{n_list}</dd></div><div><dt>State contracts</dt><dd>{n_buy}</dd></div>'
                f'<div><dt>Handovers to units</dt><dd>{n_del}</dd></div></dl>'
                + (f'<p class="go"><a href="{esc(href)}">Follow «{esc(ch.pname)}» from ЦБСТ to the front line →</a></p>' if href
                   else '<p class="go wait">The chain view is in review and not yet public.</p>') + '</article>')


def render(preview: bool, out: Path):
    L = Landing()
    L.img_dir = out.parent / "images" / "media"
    c = L.ents[CBST]
    today = dt.date.today().isoformat()
    # Called in page order, so footnotes number from the top.
    qa, qb, qref = L.quote()
    cbst_name, cbst_sanc, funds = L.name(c), L.sanctions(c), L.money_line()
    ledger = L.ledger()
    n, by, sanc = L.network()
    chains = "".join(L.chain_card(s, url if preview else (f"chain_{s}.html" if (out.parent / f"chain_{s}.html").exists() else None))
                     for s, url in CHAINS.items())
    restr_date, restr_ref = L.restricted()
    doc = f"""<!doctype html>
<!-- Generated by exhibits/build_landing.py from data/registry on {today}. Do not edit by hand. -->
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>РОЙ.МАРКЕТ Investigation</title>
{design_head((REPO / 'exhibits' / 'landing.css').read_text(), None if preview else 'fonts/fonts.css')}</head>
<body>
<header class="rm-page top">
  <p class="rm-eyebrow">Draft · {ru_date(today)}</p>
  <h1 class="rm-h1">ЦБСТ and РОЙ.МАРКЕТ <span class="rm-muted">a Moscow non-profit, its military marketplace, and the drone-war supply around it</span></h1>
  <p class="rm-dek">An open-source investigation of АНО «ЦБСТ», a Moscow non-profit for the drone industry, and of the
  companies, products, sales and handovers to military units that connect to it. Every claim rests on an archived
  document and is graded by how well that document shows it.</p>
</header>
<main class="rm-page">
  <blockquote class="rm-quote lead-quote"><span class="rm-label">Original Russian</span>«{esc(qa['text_ru'])} […] {esc(qb['text_ru'])}»
    <cite>Александр Сидякин, secretary of ЦБСТ's supervisory board and head of United Russia's central executive committee, on ЦБСТ's year, Telegram, {ru_date(qb['as_of'])}{qref}</cite>
    <span class="gloss">"{esc(qa['text_en'])} […] {esc(qb['text_en'].replace('«Roymarket»', 'Roymarket'))}"</span></blockquote>

  <section class="hub" aria-labelledby="h-hub">
    <h2 class="rm-h2" id="h-hub">Who stands behind ЦБСТ</h2>
    <div class="hub-grid">
      <article class="rm-card hub"><header><span class="rm-kind">Hub</span>{L.logo(CBST)}</header>
        <h3 class="rm-name">{cbst_name}</h3>{cbst_sanc}
        <p class="row">Targeted funding received: {funds}. These are a non-profit's funds, not revenue.</p>
        <p class="row"><span class="rm-id">ИНН {esc(c['inn'])}</span> <span class="rm-id">ОГРН {esc(c['ogrn'])}</span></p></article>
      <ul class="ledger" aria-label="Relations">{ledger}</ul>
    </div>
  </section>

  <section aria-labelledby="h-chains">
    <h2 class="rm-h2" id="h-chains">Follow a product</h2>
    <p class="lede">A chain view follows one product from ЦБСТ and its events to the maker, the shops and dealers that
    sell it, the state agencies that buy it and the units that receive it. Each line is drawn in the style of its evidence.</p>
    <div class="chains">{chains}
      <aside class="rm-card absent"><header><span class="rm-kind">Next</span></header>
        <p>More chain views follow one product at a time, each after its record has been read in full.</p></aside>
    </div>
  </section>

  <section aria-labelledby="h-net">
    <h2 class="rm-h2" id="h-net">The network on file</h2>
    <p class="lede">The investigation's registry links <b>{n}</b> organisations to ЦБСТ: {by['doc']} through a document
    (a register entry, a contract, ЦБСТ's own posts), {by['rep']} on their own word or press reports alone.
    <b>{sanc}</b> of them are on at least one sanctions list. Counted from the registry on {ru_date(today)}.</p>
  </section>

  <section class="read" aria-labelledby="h-read">
    <h2 class="rm-h2" id="h-read">How to read the evidence</h2>
    <ul class="rm-legend">
      <li>{ln("doc", 34)} <span class="rm-grade doc">Documented</span> <span>A primary document shows it: a register extract, a contract, an annual filing, a post by the party itself.</span></li>
      <li>{ln("rep", 34)} <span class="rm-grade rep">Reported</span> <span>One party's own word, or the press. Donors' handover posts are graded here until a second source confirms them.</span></li>
      <li>{ln("open", 34)} <span class="rm-grade open">Not documented</span> <span>The link must exist, but no document on file shows it.</span></li>
    </ul>
    <p>Red marks only a sanctions listing, and always names the regimes. Names appear as registered, in Russian; a
    company known by its brand is shown by the brand, with the registered name beneath it.</p>
  </section>

  <section class="rm-prose" aria-labelledby="h-method">
    <h2 class="rm-h2" id="h-method">How this is made</h2>
    <ul>
      <li>Facts come from the original Russian documents, read in full: company register extracts, annual accounts,
      procurement records, trademark records, court filings and the parties' own Telegram posts and websites.
      Summaries and machine translations are leads, never sources.</li>
      <li>Every document is archived and hashed when it is collected. Each note at the end of a page says what the
      document is and links to it where a public copy exists.</li>
      <li>Pictures are evidence only for what they show, and each says who published it. Faces of people taking part
      are shown; nobody is named from a face.</li>
    </ul>
  </section>

  <section class="rm-prose" aria-labelledby="h-limits">
    <h2 class="rm-h2" id="h-limits">What this does not show</h2>
    <ul>
      <li>A handover to a unit does not show that the equipment was used in combat. Some recipients are rear units.</li>
      <li>ЦБСТ's share in the company that runs РОЙ.МАРКЕТ is not stated in any document on file, and since
      {restr_date} the company register withholds who owns that company{restr_ref}.</li>
      <li>A US sanctions entry under a similar name belongs to a different company registered in Tula. ЦБСТ itself is
      not shown here as sanctioned by the US.</li>
      <li>This is a draft. The earlier case studies and company profiles were withdrawn while the site is rebuilt
      around chain views.</li>
    </ul>
  </section>

  <section class="rm-prose rm-sources"><h2 class="rm-h2">Sources</h2><ol>{L.notes_list()}</ol></section>
</main>
</body></html>
"""
    out.write_text(doc)
    print(f"wrote {out.relative_to(REPO)}: {len(L.notes)} sources, {n} tied organisations, {len(L.media_files)} pictures")
    return L


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true", help="link chain views to their preview Artifacts")
    ap.add_argument("--out")
    a = ap.parse_args()
    render(a.preview, Path(a.out).resolve() if a.out else REPO / "exhibits" / "landing.html")


if __name__ == "__main__":
    main()
