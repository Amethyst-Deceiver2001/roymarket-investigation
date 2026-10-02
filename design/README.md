# Reader design system, v2 (2026-10-02)

Replaces the 2026-09-21 system (archived in `data/sources/ARTIFACT_20260921_roymarket-design-system/`). Built for the chain views and every reader page after them. The prose rules stay in `STYLE_GUIDE.md`; this file covers marks, colour and type.

- `design/roymarket.css`: tokens (light and dark), base, shared components. The only place a colour is defined.
- `scripts/display_helpers.py`: `design_head()` inlines the font link, this CSS and a page's own CSS; `reader_grade()` maps registry confidence to a reader grade; `kind_icon()` and `unit_mark()` draw the kind marks.
- A builder never copies a token. Page CSS (e.g. `exhibits/chain_view.css`) holds layout only.

## Colour has four jobs, no more

| Job | Tokens | Rule |
|---|---|---|
| Evidence grade | `--g-doc` green, `--g-rep` amber, `--g-open` grey | Only on grade chips and lines. The line style and chip text carry the grade too. |
| Sanction | `--sanction` red | Only the "Sanctioned" flag, which always names the regimes. Nothing else on a page is red. |
| Structure | `--accent` navy | Links, focus rings, footnote numbers. Never a finding. |
| Ground and ink | `--paper`, `--panel`, `--ink*`, `--rule*` | Chrome. |

There is no hub hue. ЦБСТ is marked by weight: a 2px ink border and the label "Hub". The old orange collided with the amber grade for deuteranope readers (ΔE 0.6).

Validated with the dataviz six checks on 02.10.2026, all pairs. Light set (`#0b7550`, `#9a6b00`, `#b3262e` on `#eef0f2`) passes, with red–amber at ΔE 6.2 for deuteranopes. That is within the floor band and legal because both always carry a second encoding: the dash pattern, or the flag's text. Dark set (`#2fa58f`, `#c99a2e`, `#dd5a5a` on `#101418`) passes CVD at ΔE 8.0. Its amber sits 0.03 over the lightness band; it is only ever a line or a chip, never a filled area. Re-run the validator before changing any of these.

Text contrast is at least 4.5:1 in both themes (checked 02.10.2026). The Reported chip's text uses `--g-rep-ink`, a darker amber. The line amber is under 4.5:1 as small text, and darkening the line itself would merge it with sanction red for deuteranopes.

Registry `tier` is not a colour on reader pages. Tier is said in words where it matters. The graph explorer keeps its own tier palette until B6.

## Evidence grades

Three grades for readers, from one table (`READER_GRADE` in `display_helpers.py`). A page never decides a grade itself.

| Reader grade | Line | Legend text | Registry values that map to it |
|---|---|---|---|
| Documented (`doc`) | solid | A document shows it | basis `doc`; cbst_tie `t-doc`; family `confirmed` |
| Reported (`rep`) | dashed 7/4 | Reported: the party's own word or the press | basis `press`; cbst_tie `t-open`, `press`; credibility `corroborated`, `single`; family `probable` |
| Not documented (`open`) | dotted, round caps | Not documented | basis `inferred`; family `unconfirmed`; any missing or unknown value |

"Not documented" is grey, not red. It marks a link that must exist (the donor got the product from somewhere) but that no source shows. It is a gap, not an alarm.

## Kind marks

24px line icons in `currentColor`, shown beside the kind label on a card. The label is always text; the icon only repeats it.

| Mark | Used for (graph kind) |
|---|---|
| company | `entity`: maker, seller, donor, hub |
| person | `person` |
| product | `product` |
| storefront | `storefront`: a dealer shop with no legal identity on file |
| buyer | `government_customer` |
| unit (diamond) | `military_unit` and recipient lists |
| program, event, group | `program`, `event`, `group` |

A dashed card with no shadow (`.rm-card.absent`) is something the reader would expect that is not there: «Булат» has no РОЙ.МАРКЕТ listing.

**Unit mark (provisional until the unit-naming decision).** `unit_mark(echelon)` draws a monochrome APP-6 hostile frame (diamond) with the echelon mark from the unit record's own `echelon` field. It draws no branch glyph and no echelon unless the record has a sourced value. It is monochrome so red stays reserved for sanctions.

## Media

Pictures are evidence records (`data/registry/media.json`), not decoration. Four components show them: EvidenceFigure, VideoCard, FrameStrip and FacilityPair. On a chain, pictures sit on the card or line they support, as a thumbnail strip (`rm-thumbs`) that opens the full EvidenceFigure in a viewer (`rm-lightbox`); a separate gallery would cut them off from the claims they back.

- **Provenance is said in words.** A mono label over each caption reads "Published by …", "Posted by a third party" or "From press coverage". It is never shown by colour or by a grade chip: who published a picture is a different question from how well a link is documented.
- **The caption is what is visible.** A picture supports only what someone who looked at it wrote down.
- **No embedded players.** A video is a poster or a strip of timestamped stills, plus a line saying where the original is and whether we hold a copy.
- **Faces** of everyone involved (recipients, donors, staff, participants) are shown; only a clearly uninvolved bystander is blurred. Nobody is named from a face. A record still awaiting a blur is never rendered.
- **Facility views** name their provider, imagery date and how the coordinates were found. A view not yet captured is an empty dashed slot that says so.

## Type

- **Spectral** (serif, 400/500): headlines, names on cards, verbatim quotes. A finding's voice.
- **IBM Plex Sans** (400/600): body and notes.
- **IBM Plex Mono** (400/600): labels, kind tags, grade chips, identifiers (ИНН, ОГРН, в/ч numbers), dates on timelines.

All three have full Cyrillic. The scale is 11 / 13 / 15 / 17 / 22 / 34 px, and the measure is 68ch. Fonts load from Google Fonts. Before the public cutoff, `docs/` pages should self-host the three families (OFL), so readers' browsers make no third-party request. Private Artifacts may keep the Google link.

## Components

All are in `roymarket.css`, prefixed `rm-`:

- Masthead: `rm-eyebrow`, `rm-h1`, `rm-dek`.
- `rm-grade` chip and `rm-ln` lines.
- `rm-legend`, `rm-sanction` flag, `rm-id` identifier.
- `rm-card`, with `.hub` and `.absent`; `rm-kind` and `rm-name` inside it.
  The header carries the company logo (`rm-logo`, `.on-dark` for a mark drawn for a dark ground) when a logo media record exists. `rm-name` leads with the documented primary brand from `display_name()`, the legal name beneath it in `<small>` with the brand's footnote. The transliterated legal name follows in mono (`small.lat`, OOO «Trimiks», STYLE_GUIDE §2.3), the string a screening analyst searches.
- `rm-quote` (original Russian, labelled; the gloss sits apart).
- `rm-callout` (one per section at most).
- `rm-ref` footnote numbers and the `rm-sources` list.

Footnotes resolve to plain words and a public link, never to a source id (STYLE_GUIDE §3.4–3.5).
