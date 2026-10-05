# Unit name normalization: design, 05.10.2026

Status: BUILT 05.10.2026 (freeze broken for this by the user, "built unit schema overriding freeze"). Extends the "Unit naming" item in `notes/rebuild_plan.md`.

What exists: `scripts/unit_names.py` (parser and field validation), `scripts/unit_lookup.py` (lookup and `--check`), checks in `check_registry.py`, `division` added to `UNIT_TYPES`, fixtures in `tests/test_unit_lookup.py`. Records: the two 76th records merged into `76-я-гвардейская-десантно-штурмовая-дивизия`; the two 237ths added; handovers h0009, h0025, h0041, h0042 point at them.

Departure from the design below: the record id stays the existing `slug`, not an opaque `u####`. The graph (`unit::<slug>`), media `about`, `battlefield_evidence.unit_slug` and handovers all key on it, and a slug never changes once set; `legacy_slugs[]` keeps the merged ones. Number, type and arm are read from the name forms at lookup time for the older records, so only new or merged records carry `number`, `arm`, `names[]` and `parent_history[]`.

Done later the same day (05.10.2026): the 24 older records now carry explicit `number` and `arm` (read from their own names) and, for the 15 whose posts were archived (s9209-s9229), each post's own wording as a stated name form, checked verbatim against the post text; parents are `stated` only where a post says so (seven records). `91-я-бригада-управления` added for h0040. English label and card rules below.

Correction found while doing it: the volunteer detachment «Валькирия» was recorded with the 4-я гвардейская военная база as its parent. Post 486 lists «добровольческому отряду «Валькирия», бойцам 10-го разведотряда 4-й гвардейской военной базы», which reads as two recipients or as one detachment of that base; the text does not say. The parent is now a `lead` with that caveat and `parent_grouping` is empty.

Not done: five records sourced only to media items (337-й гв. полк, 9-й полк группировки «Центр», «Яким», the народное ополчение дивизион, the Васильевский подразделение) have no archived post and carry no name forms; the unnumbered units keep their hand-set slugs.

## English label and card (built 05.10.2026; the user confirms or changes the convention)

- `name_en(unit)` is a generated descriptive label, not an official English name and not a translation: ordinal + «Guards» (only where a stated name form says гвардейск) + arm + type, e.g. «237th Tank Regiment», «237th Guards Air Assault Regiment», «76th Guards Air Assault Division», «91st Command Brigade». Honorifics (Торуньский) stay in the Russian line. A unit with no number or no type has no label and the card leads with its Russian name.
- A card shows: the label as its head; beneath it the best stated Russian name (official, else the post's own wording); then parent formation, в/ч and short forms each with its grade. **The public card shows only `stated` items; `lead` items appear on internal pages only**, so a в/ч from an encyclopedia or a parent from a user statement never reaches a reader. `display_unit(unit, by_slug, public)` returns exactly that; no page uses it yet (reader pages are not built).
- The APP-6 glyph from echelon and branch stays a later decision with the unit page.

## Why

- `military_units.json` has 26 records, slugs made from the name as first seen (`114-я-омсбр`, `114-й-полк-разведки`, `войсковая-часть-33000`). `parent_grouping` is free text. Nothing resolves a recipient string to a record, and nothing stops a bare number from matching two units.
- Two units already collide: the 237-й танковый полк of the 3-я мотострелковая дивизия (h0041, post 532) and the 237-й гвардейский десантно-штурмовой полк (h0042, post 688). Neither is a record yet; both handovers carry `recipient_unit_slug: null`.
- Duplicate confirmed by the user (05.10.2026), to be merged in the migration: `76-я-бригада-вдв` (post 232, 25.01.2024: «76-й бригады ВДВ») and `76-я-гвардейская-десантно-штурмовая-бригада` (post 421, 10.04.2025: «76-й гвардейской десантно-штурмовой бригаде») are one formation, the 76-я гвардейская десантно-штурмовая дивизия. The donor's own channel uses both wordings: post 440 (14.05.2025) says «76-й гвардейской десантно-штурмовой дивизии», and the same recipient string is on two handovers in `handovers.json` under the two slugs. This is the case the design exists for: one record, three `post_wording` forms, each with its post. The merge itself waits for the schema; until then neither record is edited.

## Key (user, 05.10.2026: the parent is the disambiguator)

A unit is identified by **number + type + parent formation**, none of them alone.

- Record id is stable and opaque (`u0001`...), never built from the name or parent: a re-subordination must not rename the id that handovers point at. The current slugs stay as `legacy_slugs[]` so nothing breaks.
- `parent_history[]`: `{parent_unit | parent_text, as_of, source_id, status}`. Parents change (both 237ths were disbanded and reinstated under new parents: tank 2009 to 2016, air-assault 2001 to 2018, per secondary sources). `status`: `stated` (a document says it), `lead` (secondary source or user), `open`.
- An **unknown parent is a state**: a recipient «237-му гвардейскому десантно-штурмовому полку» with no parent stated resolves to `ambiguous` (number + type match; parent unstated) until a source decides. A bare number never picks a record.

## Name forms

`names[]`: `{form: official | short | informal | post_wording | vch, value, source_id, as_of, grade}`.
- official: «237 гвардейский десантно-штурмовой Торуньский полк» (Указ № 478, 29.06.2023)
- short: «237 гв. дшп» / «237 тп»
- post_wording: the donor's own phrase, kept verbatim per post
- `vch` (в/ч number) is a name form with its own source. A в/ч is `stated` only where a sanctions entry, court or procurement record, or an official site pairs it with the unit; a lookup or encyclopedia is `lead`.
- Each form has its own grade, so an official name can be `stated` while the в/ч is `lead` on the same record.

## Internal reference aid (user, 05.10.2026: "only for internal reference")

A crowd-compiled workbook of unit hierarchy and tactical markings (ОЗ) sits outside the repo (`~/Downloads/ОЗ ВС РФ.xlsx`). It is a finder, not a source: it tells us what an abbreviation means, which parent to look for and where a marking might be, so the real evidence can be hunted. It is never catalogued, never gets a source id, never appears in a record's citation, and is not copied into `data/sources/`. A unit fact graded `stated` still needs a document that states it; a marking matched against the workbook is a pointer for a person to follow, not corroboration, unless the same marking-to-unit link is documented in a source we can cite.

## Lookup (local, no network, no LLM; model: `registry_lookup.py`)

`unit_lookup.py "237-му гвардейскому десантно-штурмовому полку"`:
1. normalise: case endings, ё/е, ordinal forms (237-й / 237 / 237-го), abbreviations (дшп, тп, омсбр, мсд, вдв), «гвардейский» and honorifics (Торуньский) as optional tokens;
2. extract number, type, optional parent phrase;
3. match against `names[]`; return `resolved` (one record), `ambiguous` (list, with what would decide it) or `unrecorded`.
A `--check` mode warns when two records share number + type with different or unstated parents, and when a handover's `recipient_raw` resolves to `ambiguous`.

## Worked cases

| Case | Number | Type | Parent | в/ч | State |
|---|---|---|---|---|---|
| 237 tp | 237 | танковый полк | 3-я мсд (user; ruwiki, its Interfax footnote does not mention the unit) | 91726 (ruwiki, uncited there) | all `lead` |
| 237 гв. дшп | 237 | гвардейский дшп | 76-я гв. дшд (user; en-wiki) | none (12865 from a search summary, unsupported) | name `stated` (Указ № 478), rest `lead` |

## Migration (as built; see status)

1. `legacy_slugs[]` on merged records; the slug stays the id.
2. `handovers.json`: keep `recipient_raw`; set `recipient_unit_slug` only when the lookup says `resolved`.
3. Graph: unit nodes and edges keep working off the legacy slug until the builder is switched in one step; `check_registry.py` validates the new fields; fixtures in `tests/test_unit_lookup.py`.
4. Review the 26 existing records for duplicates with a person reading the posts; no automatic merge.

## Open decisions for the user

- Whether a division is a `unit_type` or only a parent.
