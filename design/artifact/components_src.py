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
from display_helpers import FONT_LINK, KIND_ICONS, figure_html, kind_icon, load_media, unit_mark  # noqa: E402
import base64, io  # noqa: E402
from PIL import Image  # noqa: E402

MEDIA = {m["id"]: m for m in load_media()}


def data_uri(mid, px=360):
    """A small inline copy of a media record's file, so a card needs no upload."""
    im = Image.open(HERE.parent.parent / MEDIA[mid]["file"]).convert("RGB")
    im.thumbnail((px, px))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=72)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def fig(mid, who, ref="1", note=""):
    return figure_html(MEDIA[mid], data_uri(mid), who, f'<sup class="rm-ref"><a href="#">{ref}</a></sup>', note)


def svg_uri(mid):
    """An SVG media file inline, for a logo card."""
    return "data:image/svg+xml;base64," + base64.b64encode((HERE.parent.parent / MEDIA[mid]["file"]).read_bytes()).decode()


def frame(mid, ref):
    m = MEDIA[mid]
    t = (m.get("frame") or {}).get("t") or "time not recorded"
    return (f'<figure class="rm-fig"><div class="frame"><img src="{data_uri(mid, 320)}" alt=""><span class="t">{t}</span></div>'
            f'<figcaption><span>{m["shows"].split(":")[0].split(";")[0][:90]}<sup class="rm-ref"><a href="#">{ref}</a></sup></span></figcaption></figure>')

OUT = HERE / "project" / "components"
WRAP = '<div style="padding:20px;background:var(--paper);color:var(--ink);font-family:var(--font-sans);display:flex;flex-wrap:wrap;gap:16px;align-items:flex-start">'


def line(grade, w=44):
    return f'<svg width="{w}" height="8" aria-hidden="true"><line x1="0" x2="{w}" y1="4" y2="4" class="rm-ln {grade}"/></svg>'


CARDS = {
    "Masthead": ("Page head", 190, """<header style="max-width:760px">
<p class="rm-eyebrow">Draft · 02.10.2026</p>
<h1 class="rm-h1">«Булат» <span class="rm-muted">from ЦБСТ to the front line</span></h1>
<p class="rm-dek">Portable UAV detector made by 3mx (ООО «Тримикс»), a company under sanctions. It is sold on marketplaces and through dealers, and bought by state agencies under 3 contracts.</p>
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
<h3 class="rm-name">АНО «ЦБСТ»<small class="lat">ANO «TsBST»</small><small>Centre for Unmanned Systems &amp; Technologies</small></h3>
<p><span class="rm-sanction">Sanctioned <b>Ukraine</b></span><sup class="rm-ref"><a href="#">1</a></sup></p></article>
<article class="rm-card" style="width:240px"><header><span class="rm-kind">{kind_icon("company")}Maker</span><img class="rm-logo on-dark" src="{svg_uri("m0019")}" alt="Logo of ООО «Тримикс»"></header>
<h3 class="rm-name">3mx<small>ООО «Тримикс»<sup class="rm-ref"><a href="#">4</a></sup></small><small class="lat">OOO «Trimiks»</small></h3><p>Revenue 2023: ₽45.6m<sup class="rm-ref"><a href="#">5</a></sup></p>
<p><span class="rm-id">ИНН 7802942873</span></p></article>
<article class="rm-card absent" style="width:240px"><header><span class="rm-kind">{kind_icon("storefront")}Not sold here</span></header>
<h3 class="rm-name">РОЙ.МАРКЕТ</h3><p>No listing found.</p></article>""", """# ChainCard

One object in a chain: a company, product, storefront, buyer or recipient list.

- The header holds the kind mark and kind label ("Maker", "Sells", "State buyer"), and the company's logo at the right when a media record of genre `logo` exists. A logo drawn for a dark ground (`logo_ground: dark`) sits on the dark plate. Never a product photo in its place.
- The name in Spectral follows. With a documented primary brand (`display_name()`), the brand leads and the registered legal name sits directly beneath it in `<small>`, footnoted to the brand's source (here trademark RU1125967). Without one, the legal name leads with its English gloss. The legal name is never hidden: sanctions lists name the company, not the brand.
- Under the registered name sits its Latin form in mono (`small.lat`, `display_name()['latin']`): the legal form transliterated, never translated (OOO, AO, ANO, NPTs), per STYLE_GUIDE §2.3. It is the string a screening analyst searches in a sanctions list. A hand correction (`name_display`) overrides the generated form.
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
<cite>3mx customer chat, 02.09.2026<sup class="rm-ref"><a href="#">9</a></sup></cite>
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

CARDS.update({
    "EvidenceFigure": ("Media", 420, f'<div style="width:260px">{fig("m0043", "ООО «ПОКРОВ»", "7")}</div>', """# EvidenceFigure

One picture as evidence: the image, who published it, what is visible, its date and a footnote.

- The provenance label comes from the media record's `asserted_by`: "Published by ООО «ПОКРОВ»", "Posted by a third party", "From press coverage". It is said in words, never with colour.
- The caption is the record's `shows`: what someone who looked at the picture saw. A picture is evidence only for that.
- The image sits in a 4:3 frame with `object-fit: contain`, so it is never cropped in a way that changes what it shows.
- Records marked `internal` or still awaiting a blur (`blur_pending`) are never rendered (`media_about()`).
- Example: the «Булат» v.4 card on the dealer's own site."""),

    "VideoCard": ("Media", 400, f'<div style="width:260px">{fig("m0063", "3mx", "3", "Video. Original on VK Clips and YouTube; the post gives no link. Not archived.")}</div>', """# VideoCard

A video shown as its poster still plus a line saying where the original is and whether we hold a copy.

- No platform player is embedded (decision 02.10.2026): players track readers, break when a post is deleted, and do not run in Artifacts.
- The play mark is drawn over the poster to say "this is a video", not to play it.
- The line under the caption is the record's `video.original`, followed by "Not archived" when `video.archived` is false.
- Example: the maker's Q&A video thumbnail from its customer chat."""),

    "FrameStrip": ("Media", 260, f'<div class="rm-frames" style="width:100%">{frame("m0048", "4")}{frame("m0049", "4")}{frame("m0053", "4")}{frame("m0054", "4")}</div>', """# FrameStrip

Timestamped stills from one video, in order, so a reader can see what the video shows without a player.

- Each still carries its timestamp in the video (`frame.t`) in the corner. Where it was not recorded, the strip says "time not recorded" rather than guessing.
- All stills in a strip come from one video and share one footnote.
- The strip scrolls sideways inside its own container at narrow widths.
- Example: four stills from a 32-minute «Архангел» instruction video; their timestamps are still to be recorded."""),

    "FacilityPair": ("Media", 440, f'''<div class="rm-facility" style="width:100%">
<figure class="rm-fig empty"><div class="frame">Satellite view not yet captured</div><figcaption><span class="rm-prov">Satellite</span><span class="rm-geo">Coordinates from the company register address · provider and imagery date shown here</span></figcaption></figure>
{fig("m0024", "ООО «ГОУДРОН»", "8")}
</div>''', """# FacilityPair

The satellite view and a ground view of one place, side by side.

- The satellite slot names its provider and imagery date (Google Earth or Yandex Maps for now, decision 02.10.2026) and gives the coordinates with how they were found: a register address, a place the source states, or our own geolocation.
- A view not yet captured is shown as an empty dashed slot that says so. It is never filled with a nearby or generic image.
- The ground view is any media record of genre `facility`: the company's own photo, a customer upload, or a street-level screenshot.
- Example: the GoDrone storefront, a customer's upload on Yandex Maps; its satellite view is not yet captured."""),
})


def main():
    for name, (group, height, body, readme) in CARDS.items():
        d = OUT / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "preview.html").write_text(f'<!-- @dsCard group="{group}" height={height} -->\n{FONT_LINK}\n{WRAP}\n{body}\n</div>\n')
        (d / "README.md").write_text(readme + "\n")
    print(f"{len(CARDS)} cards")


if __name__ == "__main__":
    main()
