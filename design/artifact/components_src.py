#!/usr/bin/env python3
"""Write the Design System artifact's component cards (preview.html + README.md) and cover.

    python3 design/artifact/components_src.py

Icons and unit marks come from scripts/display_helpers.py, the same code the page builders
call, so a card cannot drift from what pages draw. Example content is from the «Булат» chain.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "scripts"))
from display_helpers import FONT_LINK, KIND_ICONS, kind_icon, unit_mark  # noqa: E402

OUT = HERE / "project" / "components"
WRAP = '<div style="padding:20px;background:var(--paper);color:var(--ink);font-family:var(--font-sans);display:flex;flex-wrap:wrap;gap:16px;align-items:flex-start">'


def line(grade, w=44):
    return f'<svg width="{w}" height="8" aria-hidden="true"><line x1="0" x2="{w}" y1="4" y2="4" class="rm-ln {grade}"/></svg>'


CARDS = {
    "Masthead": ("Page head", 190, """<header style="max-width:760px">
<p class="rm-eyebrow">Draft · 02.10.2026</p>
<h1 class="rm-h1">«Булат» <span class="rm-muted">from ЦБСТ to the front line</span></h1>
<p class="rm-dek">Portable UAV detector made by ООО «Тримикс», a company under sanctions. It is sold on marketplaces and through dealers, and bought by state agencies under 3 contracts.</p>
</header>""", """# Masthead

The page head: an eyebrow, the finding as a flat headline, and a dek. Use one per page.

- `rm-eyebrow` holds status and date: mono, uppercase, `ink-3`.
- `rm-h1` states the finding in Spectral. A `rm-muted` span may carry the second half of the headline in `ink-2`.
- `rm-dek` is one or two sentences in the lead size, at most 68ch.
- The headline carries no hedge. Qualifications go in the dek or below."""),

    "Grade": ("Evidence", 96, """<span class="rm-grade doc">Documented</span>
<span class="rm-grade rep">Reported</span>
<span class="rm-grade open">Not documented</span>""", """# Grade

A chip that states how well a claim is documented: Documented, Reported or Not documented.

- Text is always present; the colour repeats it. Never show a grade by colour alone.
- The grade comes from `reader_grade()`, which maps every registry confidence value in one table. A page never picks one.
- The Reported chip uses `g-rep-ink` for its text, because the line amber is under 4.5:1 as small text."""),

    "Line": ("Evidence", 130, f"""<ul class="rm-legend" style="margin:0">
<li>{line("doc")} A document shows it</li>
<li>{line("rep")} Reported: the party's own word or the press</li>
<li>{line("open")} Not documented</li>
</ul>""", """# Line

The connector grammar for chain views: an SVG stroke whose style carries the grade.

- `rm-ln doc` is solid, `rm-ln rep` dashed 7/4, and `rm-ln open` dotted with round caps, all 1.75px.
- `rm-ln trunk` is the neutral bus from a product to its seller rows. Each row's own grade sits on its tick.
- A line is drawn only where it carries information. A line that would repeat its neighbours is folded into a trunk.
- Every chain page shows this legend above the chain."""),

    "SanctionFlag": ("Evidence", 96, """<span class="rm-sanction">Sanctioned <b>Switzerland, EU, US, Ukraine</b></span>
<span class="rm-sanction">Sanctioned <b>Ukraine</b></span>""", """# SanctionFlag

The only red on a page. It marks an entity under sanctions and always names the regimes.

- Regime names are the reader's (EU, US, UK, Switzerland, Japan, Ukraine…), never list codes.
- It is followed by a footnote to the listing or the sanctions dataset that was checked.
- It wraps inside a narrow card rather than overflowing."""),

    "ChainCard": ("Chain", 260, f"""<article class="rm-card hub" style="width:240px"><header><span class="rm-kind">{kind_icon("company")}Hub</span></header>
<h3 class="rm-name">АНО «ЦБСТ»<small>Centre for Unmanned Systems &amp; Technologies</small></h3>
<p><span class="rm-sanction">Sanctioned <b>Ukraine</b></span><sup class="rm-ref"><a href="#">1</a></sup></p></article>
<article class="rm-card" style="width:240px"><header><span class="rm-kind">{kind_icon("company")}Maker</span></header>
<h3 class="rm-name">ООО «Тримикс»</h3><p>Revenue 2023: ₽45.6m<sup class="rm-ref"><a href="#">5</a></sup></p>
<p><span class="rm-id">ИНН 7802942873</span></p></article>
<article class="rm-card absent" style="width:240px"><header><span class="rm-kind">{kind_icon("storefront")}Not sold here</span></header>
<h3 class="rm-name">РОЙ.МАРКЕТ</h3><p>No listing found.</p></article>""", """# ChainCard

One object in a chain: a company, product, storefront, buyer or recipient list.

- The header holds the kind mark and kind label ("Maker", "Sells", "State buyer"). The name in Spectral follows: Cyrillic as registered, with an English gloss in `<small>`.
- `.hub` is for ЦБСТ only: a 2px ink border. There is no hub colour.
- `.absent` is a dashed card with no shadow, for something a reader would expect that is not there.
- Rows are `p` elements at the note size; each claim ends in a `rm-ref` footnote.
- The consumer supplies the `id` that the chain's lines attach to."""),

    "KindMarks": ("Chain", 120, "".join(
        f'<span class="rm-kind" style="display:inline-flex;align-items:center;gap:2px">{kind_icon(k)}{k}</span>'
        for k in KIND_ICONS), """# KindMarks

24px line icons for what a card is: company, person, product, storefront, buyer, programme, event, group and unit.

- They are drawn in `currentColor` with stroke 1.6 and round joins, and sized to 14px inside `rm-kind`.
- They always sit beside the text label and never replace it.
- `kind_icon(name)` in `scripts/display_helpers.py` is the source; this card renders the same paths."""),

    "UnitMark": ("Chain", 120, f"""<div style="display:flex;gap:24px;align-items:end">
<figure style="margin:0;text-align:center">{unit_mark()}<figcaption class="rm-label">No echelon</figcaption></figure>
<figure style="margin:0;text-align:center">{unit_mark("battalion")}<figcaption class="rm-label">Battalion</figcaption></figure>
<figure style="margin:0;text-align:center">{unit_mark("regiment")}<figcaption class="rm-label">Regiment</figcaption></figure>
<figure style="margin:0;text-align:center">{unit_mark("brigade")}<figcaption class="rm-label">Brigade</figcaption></figure>
<figure style="margin:0;text-align:center">{unit_mark("division")}<figcaption class="rm-label">Division</figcaption></figure></div>""", """# UnitMark

A military unit's mark: a monochrome APP-6 hostile frame (diamond) with an echelon mark. **Provisional until the unit-naming convention is settled.**

- The echelon is drawn only from the unit record's own sourced echelon. With none on record, the frame is drawn bare.
- No branch glyph (motor rifle, artillery) is drawn until the record carries a sourced branch.
- It is monochrome so red stays reserved for sanctions.
- A recipient that is a town or a direction gets no unit mark."""),

    "Quote": ("Text", 190, """<blockquote class="rm-quote" style="max-width:560px"><span class="rm-label">Original Russian</span>«Всю нашу продукцию можно приобрести только у нас на сайте 3mx.ru или у наших дилеров.»
<cite>ООО «Тримикс» customer chat, 02.09.2026<sup class="rm-ref"><a href="#">9</a></sup></cite>
<span class="gloss">"All our products can be bought only from us on our site 3mx.ru or from our dealers."</span></blockquote>""", """# Quote

A verbatim quote in the original Russian, with its source and a separate English gloss.

- The quote text is never paraphrased or corrected. Typos are kept and marked «[так в оригинале]».
- The gloss is our translation and is styled as plain text, not as part of the quote.
- An unverifiable quote is not used.
- The example is the maker's distribution claim from the «Булат» record."""),

    "Footnotes": ("Text", 200, """<div style="max-width:620px"><p style="margin:0 0 8px">Bought by a state agency under a contract<sup class="rm-ref"><a href="#n2">2</a></sup>.</p>
<section class="rm-sources"><h2 class="rm-h2">Sources</h2><ol>
<li id="n1">Telegram, @ano_cbst, post 1193, 08.09.2025. <a href="https://t.me/ano_cbst/1193">t.me/ano_cbst/1193 ↗</a></li>
<li id="n2">State procurement record no. 1463204748024000101, zakupki.gov.ru. <a href="#">zakupki.gov.ru ↗</a></li>
<li id="n3">Company register extract (ЕГРЮЛ, Federal Tax Service), 18.08.2026.</li></ol></section></div>""", """# Footnotes

Numbered references (`rm-ref`) that resolve to the page's source list (`rm-sources`).

- Each entry is plain words: the kind of document, its publisher and its date, plus a short public link when one exists.
- Never print a source id, file name or capture date (STYLE_GUIDE §3.4–3.5).
- If no public link exists, the entry says what the document is and stops.
- A targeted entry is highlighted with `accent-soft`."""),

    "Callout": ("Text", 140, """<aside class="rm-callout"><span class="rm-label">What is missing</span>
<p>No document shows where Фонд «Наша Правда» obtained «Булат». The line from the product to the donor is dotted for that reason.</p></aside>""", """# Callout

One finding lifted out of the running text. Use at most one per section.

- The label says what it is ("Finding", "What is missing").
- It has no accent rail and no shadow; it is set off by its surface and border.
- The example is a limit stated on the «Булат» chain."""),
}


def main():
    for name, (group, height, body, readme) in CARDS.items():
        d = OUT / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "preview.html").write_text(f'<!-- @dsCard group="{group}" height={height} -->\n{FONT_LINK}\n{WRAP}\n{body}\n</div>\n')
        (d / "README.md").write_text(readme + "\n")
    print(f"{len(CARDS)} cards")


if __name__ == "__main__":
    main()
