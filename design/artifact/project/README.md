# РОЙ.МАРКЕТ Reader System

The visual system for the reader pages of an open-source investigation into ЦБСТ and the РОЙ.МАРКЕТ defence-tech marketplace: chain views (maker to front line), entity pages for specialists, and the landing page. Every page has to survive a hostile lawyer's read. So the system has few colours, each with one job. A line's style says how well the link is documented, and nothing on a page implies more than its source shows.

Source of truth: `design/roymarket.css` in the investigation repository. This artifact is generated from it (`design/build_ds_artifact.py`); change the CSS, not the tokens here.

## Content fundamentals

- **The headline is the finding, stated flat.** "«Булат» from ЦБСТ to the front line". No hedge in the head; the evidence earns it below.
- **English is analysis, Russian is evidence.** Names appear as registered, in Cyrillic: ООО «Тримикс», АНО «ЦБСТ». An English gloss sits beneath in smaller sans. Verbatim quotes stay in the original Russian, punctuation and typos kept, with a gloss apart.
- **No internal notation.** Never print source ids, slugs, field names or file names. A footnote resolves to plain words ("State procurement record no. 1463204748024000101, zakupki.gov.ru") and a public link where one exists.
- **Identifiers are bare digits in mono**: ИНН 7802942873, ОГРН, в/ч numbers.
- **Dates in the Russian convention**: 08.09.2025.
- **Say what the page does not show.** Each chain ends with a "What this does not show" list. A gap gets a dotted line on the chain and a sentence in that list.

## Visual foundations

**Colour has four jobs, no more.**

| Job | Tokens | Rule |
|---|---|---|
| Evidence grade | `g-doc` green · `g-rep` amber · `g-open` grey | Only on grade chips and lines. The line style and chip text carry the grade as well. |
| Sanction | `sanction` red | Only the Sanctioned flag, which always names the regimes ("Switzerland, EU, US, Ukraine"). Nothing else is red. |
| Structure | `accent` navy | Links, focus rings, footnote numbers. Never a finding. |
| Ground and ink | `paper`, `panel`, `ink*`, `rule*` | Chrome. |

There is no hub colour. ЦБСТ, the centre of the network, is marked by weight: a 2px ink border (`hub-edge`) and the label "Hub". An orange hub was tried and dropped, because for deuteranope readers it could not be told from the Reported amber (ΔE 0.6).

The grade and sanction hues were checked with a colour-vision validator in both themes, against every pair. Light red against light amber is the closest pair for deuteranopes (ΔE 6.2). That gap is allowed only because neither colour is ever the sole signal: a sanction is a labelled flag, and Reported is a dashed line.

Text is at least 4.5:1 in both themes. The Reported chip's text uses `g-rep-ink`, because the line amber is too light for small text. Darkening the line would have merged it with the red.

**Type.** Spectral carries findings: headlines, names on cards, quotes. IBM Plex Sans is the body and notes face. IBM Plex Mono is for labels, chips and identifiers. All three cover Cyrillic fully. The scale runs 11 / 13 / 15 / 17 / 22 / 34 px, and running text is set to a 68ch measure.

**Shape.** Square-ish 4px corners, because these are documents. A 1px rule border and a soft shadow appear on cards only. A dashed card with no shadow is something a reader would expect to find but which is absent, such as «Булат» on РОЙ.МАРКЕТ.

**Motion.** None, apart from the hover focus on a chain: other cards fade to 35% so one card's path stands out.

## Evidence grades

Three grades, from one table that maps every registry confidence value. A page never chooses a grade by itself.

| Grade | Line | Legend wording |
|---|---|---|
| Documented | solid | A document shows it |
| Reported | dashed 7/4 | Reported: the party's own word or the press |
| Not documented | dotted | Not documented |

"Not documented" is grey, not red. It marks a link that must exist but that no source shows: the donor obtained the product from somewhere. It is a gap, not an alarm.

## Iconography

Kind marks are 24px line icons in `currentColor` (stroke 1.6, round joins). They always sit beside a text kind label and never replace it. The marks are company, person, product, storefront (a dealer shop with no legal identity on file), state buyer (a pediment), unit (a diamond), programme, event and group.

**Military units** use a monochrome APP-6 hostile frame (diamond). The echelon mark is drawn only when the unit record carries a sourced echelon, and no branch glyph is guessed. It is monochrome so red stays reserved for sanctions. This mark is provisional until the unit-naming convention is settled.

No logo exists. The wordmark is the name set in Spectral.

## Using it

Load `components/bundle.css` after the tokens. Load the three families from Google Fonts with the Cyrillic subset; published `docs/` pages will self-host them. Components are plain markup with `rm-` classes and no script bundle. Each component card shows the markup.
