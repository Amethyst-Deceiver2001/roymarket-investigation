# Working rules for roymarket-investigation

This repo is a standalone spin-off of a ЦБСТ/РОЙ.МАРКЕТ (Russian "military
marketplace" and its parent defence-tech body) OSINT investigation, migrated
out of the `wb_watch` project on 2026-08-18 once it outgrew "annex to a WB
tracker" scope. Read `notes/rebuild_plan.md` first in any new session — a lean live
status doc (rewritten 2026-09-19) with current state, standing policy and
pointers; the old 4,284-line session log is preserved verbatim at
`notes/archive/rebuild_plan_archive_2026-09-19.md`.

## This repo has its own Telegram scraping pipeline — separate from wb_watch

**Correction (2026-08-18, same day as migration):** the original design had
data collection staying in `wb_watch` and this repo only exporting/
analyzing. The user explicitly overrode that — this investigation needs its
own scraping, independent of `wb_watch`'s WB-tracker-oriented one, both
because the targets are different (corporate entities/UAV terminology, not
WB/Ozon links) and because it shouldn't depend on another repo's auth
session or channel list going forward.

**How it actually works now:**

- `tg/client.py`, `tg/scraper.py`, `tg/db.py` — this repo's own Telethon
  client, scraper, and storage layer, structurally modeled on wb_watch's
  working patterns (same resolve/iterate/forward-resolution approach — no
  reason to reinvent something that already works) but with its own
  session/config and WITHOUT wb_watch's WB/Ozon-item-matching logic, which
  is irrelevant here. Posts are stored raw; entity/product/person
  extraction happens separately in `scripts/mine_leads.py` over the stored
  text — scraping and mining are deliberately decoupled so mining patterns
  can be iterated on without re-scraping.
- `config/channels.txt` — this repo's own watchlist (currently the 11
  channels already known to matter; add new ones as research finds them).
- `.env` — own `TG_API_ID`/`TG_API_HASH` (register a fresh app at
  https://my.telegram.org, doesn't need to match wb_watch's) and
  `TG_SESSION` (one-time `python3 scripts/tg_login.py`, interactive).
  No `.env.example` template — removed as redundant once `.env` itself
  held real credentials; if `.env` is ever missing, the two vars above
  plus `TG_SESSION` are the whole schema.
- `scripts/tg_scan.py` — the actual scraper entry point. **This is a live
  network job against a third-party service** — per the crawling-jobs
  policy below, hand the user the exact command to run themselves, don't
  execute it directly or in the background.
- `scripts/export_from_wb_watch.py` — **historical bootstrap only**. This
  is how `data/roymarket.db` got its initial ~98,700 posts at migration
  time, pulled from wb_watch's already-scraped archive. Not the ongoing
  collection method — don't reach for it for routine updates.

## Lead mining is purpose-built here, not inherited from wb_watch

`scripts/mine_leads.py` is this investigation's own extraction pass — it
does NOT reuse wb_watch's tg-scan matching logic, which looks for
wildberries.ru/ozon.ru links and has nothing to do with corporate-entity
mapping. It instead mines already-collected post text for: corporate
entities (legal-form prefix regex — АО/ООО/НПЦ/НПО/КБ/etc, quoted or bare),
«guillemet-quoted» product/brand names, ИНН/ОГРН sequences, and named
individuals with a role title (Генеральный директор/Учредитель/etc + name).
It scores posts by UAV/military-industry keyword density to down-rank noise
from broad general-news channels (mil_hub alone is 60k+ posts of mixed
content), and cross-checks every candidate against `docs/index.html` so
already-documented entities/people don't get reported as new.

This is **local text processing over already-scraped data, not a live
network job** — safe to run directly/repeatedly regardless of scale, unlike
an actual Telegram scrape (see the crawling-jobs section below). Run it with
`python3 scripts/mine_leads.py --out report.md` after any DB refresh, or
without `--out` to print to stdout. Treat its output as a triage list, not
a source — every candidate still needs the same primary-source verification
(EGRUL, БФО, a real post read) before it goes anywhere near the brief. Adjust
`UAV_TERMS`/`LEGAL_PREFIXES`/`ROLE_TITLES` at the top of the script as new
terminology patterns turn up.

The extraction patterns themselves (entity/product/ИНН/ОГРН/role+name regex)
live in `scripts/id_patterns.py`, shared between `mine_leads.py`'s DB scan
and `scripts/extract_ids.py` — a general-purpose CLI over arbitrary text.
**Use `extract_ids.py` whenever discovery work involves reading text that
might contain an entity's own ИНН/ОГРН/legal name — not just Telegram
posts.** Corporate "О компании"/"Контакты" pages routinely state this
directly, and so do EGRUL extracts, БФО filing notes and founding-charter
text. Pipe fetched/pasted text through it (`... | python3
scripts/extract_ids.py`) instead of eyeballing it for these patterns by
hand. Related: `scripts/check_egrul_flags.py` flags known EGRUL access-
restriction/disavowal markers (ОгрДосСв, ПризнНедДанУчр, etc.) the same
way, over the same kind of pasted extract text.

## Same crawling-jobs discipline as wb_watch

Inline reconnaissance (single post lookups, one-off WebFetch/curl checks,
EGRUL/БФО document reads) is fine to run directly. Anything that does real
work at scale against a live third-party service must be handed to the user
as an exact command to run themselves, never run in the background — this
applies to `scripts/tg_scan.py` here (see above) and to EGRUL/БФО pulls,
which are the user's own manual downloads due to daily rate limits.
`scripts/mine_leads.py` is NOT covered by this — it's local processing over
already-scraped data, no live network call, fine to run directly/repeatedly.

**`scripts/egrul_batch_pull.py`** (added 2026-08-22) is the same discipline
applied to a *scripted* EGRUL job, not just the manual PDF-download case:
it hits egrul.nalog.ru's open (no-captcha) lookup API in a loop across every
registry entity with an ИНН, to give the whole roster one synchronized
baseline snapshot date instead of scattered pull dates. Tested inline on a
handful of entities first (ordinary reconnaissance, fine to do directly),
but the full-roster batch was handed to the user as an exact command — a
systematic loop of 100+ automated calls is exactly the "real work at scale"
case this policy exists for, even against an unauthenticated open API.

**Per-script detail** (`egrul_batch_pull`, `tg_media_pull`, `zakupki_batch_pull` incl. the `zakupki_review` field rule, `tg_scan_users`, `screen_egrip_ip`, the ФНС «Прозрачный бизнес» screeners) and the **parser lessons** (sample before a full run, all-null is a parser signal, БФО non-profit `funds_*` never presented as revenue, filer read from the filename) are in `notes/reference/script_notes.md` — read it before running or changing any of them. Rules that stay here:

- Live network jobs at scale (`tg_scan.py`, `tg_scan_users.py`, batch EGRUL/zakupki/ЕГРИП/ФНС sweeps) are handed to the user as an exact command, never run or backgrounded. Single lookups are fine inline.
- After `tg_media_pull.py fetch`: run `inventory_sources.py` → `extract_registry.py` for real sNNNN ids, and copy the image into `docs/images/` or the HTML profile will not show it.
- Record a closed zakupki triage in the structured `zakupki_review` field (`{as_of, outcome: wired|partial|closed, note}`), not only in prose; trust `zakupki_coverage.py --gaps-only` over your own file counts.
- Any local job over ~100 files or ~2 minutes: say so up front and either give the user the command or announce the background task. Run `tests/test_zakupki_parser.py` / `tests/test_bfo_parser.py` after touching those parsers.
- An all-null result for one entity or one field across the corpus is a parser bug until proven otherwise. Non-profit `funds_*` figures are never revenue.


## Primary-source documents: check `data/sources/` before re-downloading

`data/sources/` (gitignored — local working copy, ~424MB) holds the EGRUL
extracts (`ul-*.pdf`), БФО annual-accounts filings (`РЕСУРС_БФО_*.zip`),
founding-Устав bundles (`UD_*.zip`), arbitration-court filings
(`A40-*_Opredelenie.pdf`), and a handful of press/OSINT captures backing
the brief's claims. Before asking the user to re-download or re-pull a
document, grep the ИНН/ОГРН against filenames — or, better, against
`data/sources/MANIFEST.md` — before assuming it's not already there.

**`scripts/scan_sources.py`** runs the same ИНН/ОГРН/entity/person
extraction `mine_leads.py` does on Telegram posts, but over every file in
`data/sources/` (PDF via `pdftotext`, zip/xlsx via `openpyxl`, html via
`bs4`) and writes `data/sources/MANIFEST.md` — a filename → ИНН/ОГРН/
entities table. Like `mine_leads.py` this is local file processing, no
network calls, safe to run directly/repeatedly — not covered by the
crawling-jobs policy below. Run it with `--out data/sources/MANIFEST.md
--leads-out <file>` after any batch of new downloads; the `--leads-out`
report is a triage list of candidates not yet in `docs/index.html`, same
verify-before-use discipline as `mine_leads.py`'s output — a name/case
matching a known figure (amount, entity) is a lead to verify, not a
confirmed link (see `A40-119451/26` — same ₽83.27m figure the brief
attributes to «Инвестментс», but the filing itself names a different
defendant, ООО «АФК» — flagged, not yet resolved).

**Archiving convention**: existing files are NOT renamed (nothing should
have to track a rename) — `MANIFEST.md` is the lookup layer for them.
Going forward, name new pulls `<TYPE>_<INN-or-OGRN>_<YYYYMMDD>_<slug>.<ext>`
(e.g. `EGRUL_7714389530_20260817_fond-natsmorprog.pdf`) so they're
self-describing. For sources with no ИНН/ОГРН to key on — video/podcast
transcripts, press captures — drop that segment: `TRANSCRIPT_<YYYYMMDD>_
<slug>.<ext>` (e.g. `TRANSCRIPT_20250421_peregovorka-cbst-er-sidyakin-
bezrukov.txt`, the date being the source's publish date, not the pull
date). This also solves a real problem: `notes/` isn't gitignored the way
`data/sources/` is, so a full broadcast/video transcript belongs here, not
in `notes/`, to avoid it landing in a commit. Save new EGRUL/БФО/court/
transcript pulls here going forward rather than leaving them in
`~/Downloads` or `notes/`.

**Generic model-charter templates are not entity-specific evidence.**
`data/sources/Устав №20.pdf` is the government-issued boilerplate text of
Типовой устав №20 (Приказ Минэкономразвития от 01.08.2018 №411) — a
company adopts one of these *instead of* filing a custom charter, and the
template's own text carries zero entity-specific content (no names, no
capital, no address). Don't try to extract facts from a template copy, and
don't attribute it to a single entity as that entity's founding-doc source.
The useful fact is *which* entity adopted *which* numbered template and
*when* — recorded in `data/registry/ustav_templates.json`, cross-referenced
from the entity record, not treated as that entity's primary source. There
are 36 of these templates; keep a reference copy of each new one
encountered the same way (`inventory_sources.py` types them
`ustav_template` automatically via the "ТИПОВОЙ УСТАВ №" heading).

## `data/registry/` is the source of truth, not `docs/index.html`

Since 2026-08-22 the investigation's facts live in `data/registry/*.json`,
not in the HTML. `docs/` becomes a *generated* site; editing a fact into the
HTML by hand puts it somewhere the next build overwrites.

- `entities.json` — every legal entity: identifiers, ownership, ОКВЭД and
  the declared-vs-actual mismatch, financials, sanctions, IP, foreign
  components, web/social presence, `tier`, `wb_overlap`, open questions.
- `people.json` — every named individual, with identifying detail per the
  PII section below, and their roles.
- `quotes.json` — verbatim Russian quotations, so EN and RU pages render the
  same string instead of two hand-copies that drift.
- `sources.json` / `open_questions.json` — the provenance catalogue and the
  unresolved-work list. Every source separates `captured_date` (when we
  pulled it — derived from the filename where the naming convention encodes
  it) from `as_of` (the document's own effective date — a charter amendment
  date, an EGRUL extract's issue date). These are frequently different and
  must never be collapsed into one field: a БФО filing pulled 21.08.2026 can
  report on fiscal year 2024; a Устав pulled the same day can record
  ownership as it stood after a 2022 amendment. `as_of` is filled only by a
  human who has actually read the document — never guessed from a filename.

### Time-variant facts get a dated history, not a scalar

A director changes. A charter is amended. EGRUL gets re-pulled and states
something different than the last pull. `financials[]` already modelled
this correctly (`{year, revenue, profit, source_id}` — a dated array, not a
single number); the same shape now applies to `director_history`,
`charter_capital_history`, `address_history`, `name_history` and
`founders_history` on every entity. Each entry: `{value, as_of, source_id,
note}`. The flat scalar field (`director`, `charter_capital`, etc.) stays as
a display convenience holding the latest known value — the `_history` array
is the actual record, and it is what lets a claim read "director as of the
most recent founding-document amendment (DATE), per SOURCE" instead of an
undated assertion a later pull could silently overwrite. A history entry
with no `source_id` is a placeholder, not evidence — `check_registry.py`
flags it as a warning so it surfaces as verification work.

### Entity profile fields added 2026-08-25 (company-profile checklist gap-fill)

Six new arrays on every entity, defaulting empty, populated by hand via
`corrections.json` like any other human-conclusion field:
- `government_contracts[]` — госзакупки/госконтракт records (customer,
  contract number/value/date, `source_id`).
- `workforce_history[]` — `{count, as_of, source_id, note}`, same dated-array
  shape as `financials[]`. Use `note` for self-reported production-scale
  claims (units/day, assembly lines) when no headcount figure exists.
- `state_programs[]` — grant/association/residency participation (Сколково,
  АТР grants, АЭРОНЕКСТ, rk.2035.university, etc.) — corroborates legitimacy
  claims and gives cross-reference IDs into other public registries.
- `marketing_claims[]` — `{text_ru, text_en, context, source_id, as_of}`,
  verbatim self-incriminating marketing copy (see the capture-verbatim rule
  under [[roymarket_capture_self_incriminating_marketing_copy]] in memory) —
  a structured home for what used to get buried in prose `why[]` notes.
- `battlefield_evidence[]` — combat-footage/downed-unit sightings that
  independently confirm a product is fielded, distinct from the
  manufacturer's own marketing claims.
- `domain_history[]` — WHOIS registrant history where pre-privacy-shield
  records reveal a founder's name/email/phone.

None of these get a `check_registry.py` shape check yet, matching the
existing (also-unvalidated) `litigation[]`/`licences[]` fields — add one only
if a real malformed-data incident calls for it, not preemptively.

- `corrections.json` — **hand-made fixes, each with its reasoning and the
  source it was checked against.** Applied last by the extractor, so
  regenerating never silently reverts a verified correction. Add corrections
  here rather than editing generated records in place.
  **Split 2026-08-26** into `corrections_entities.json` (`entities`,
  `add_entities`) and `corrections_people.json` (`people`,
  `people_add_entities`) — the single file had grown to 23k lines/1.5MB.
  Same shape, same semantics, just two files instead of one; "corrections.json"
  below and elsewhere in this doc/memory refers to that mechanism generically,
  not a literal remaining file. `extract_registry.py`'s `load_corrections()`
  reads both and merges by key — add a fix to whichever file's `entities`/
  `people` section matches what you're correcting.
  **Exception — cannot be used for raw screening fields.** Any field listed in
  `extract_registry.py`'s `ENTITY_CARRY_FORWARD_FIELDS`/
  `PEOPLE_CARRY_FORWARD_FIELDS` (`gur_matches`, `opensanctions_matches`,
  `aleph_matches`, `rospatent_director_matches`, `gur_components_matches`,
  etc. — the raw evidence a `screen_*.py` script writes) is carried forward
  from the *previous* regeneration AFTER corrections are applied, so setting
  one via `corrections.json` gets silently overwritten by the prior run's
  value. Write these directly onto `entities.json`/`people.json` instead
  (the way a `screen_*.py` script would), then re-run `extract_registry.py` —
  it will read your edit as "prev" on that run and carry it forward correctly.
  Human-conclusion fields (`sanctions[]`, `patents[]`, `foreign_components[]`,
  `director`, `tier`, etc.) are not on that list and work normally via
  `corrections.json`.
- `_scaffold_leads.json` — extraction leftovers needing a human: ИНН that
  could not be attributed to a company, and the catch-all table rows that
  still need splitting into per-entity open questions.

**Workflow**: `python3 scripts/inventory_sources.py` (reads every file in
`data/sources/` once — pdftotext/zip/xlsx — and caches its type and `as_of`
date to `data/registry/_source_content_cache.json`; only processes files not
already cached, so re-run it after adding new sources rather than every
session) → `python3 scripts/extract_registry.py` (one-time scaffold from the
frozen `docs/_archive/` snapshot, consuming that cache; re-runnable while
Phase 1 continues) → `python3 scripts/check_registry.py` before trusting or
building from anything. All three are local file processing — no network,
safe to run repeatedly.

`check_registry.py` validates ИНН and ОГРН control digits. **Take a checksum
failure seriously**: it caught a transposed ОГРН for АО «Стратим» that had
been sitting in the brief, and two personal ИНН that had been mis-attributed
to organisations. A wrong identifier in a sanctions submission is a serious
defect, not a typo.

## `relationship_graph.json` — generated, schema-versioned, rebuild after any registry change

`scripts/build_relationship_graph.py` derives `data/registry/
relationship_graph.json` (+`relationship_graph_views.json`) from
`entities.json`/`people.json`/`military_units.json` — the same
generated-not-hand-written discipline as company profiles. Always run it
after any `corrections_entities.json`/`corrections_people.json` change
that could touch ownership, roles, products, government contracts, or
`cbst_tie`; `check_registry.py` fails loudly (`does not exactly match the
deterministic rebuild`) if it's stale, so a forgotten rebuild surfaces
immediately rather than silently shipping an out-of-date graph.
`scripts/graph_contract.py` is the schema itself — `GRAPH_SCHEMA_VERSION`,
the `EDGE_TYPES` table (endpoint-kind validation per edge type), and any
controlled vocabularies (e.g. `CBST_TIE_CONFIDENCE`). Bump the version and
extend the contract there first when adding a genuinely new edge type or
field, the same way `entities.json`'s own field additions get documented
above.

**`cbst_tie`** (added 2026-09-15, schema v4) is an entity→ЦБСТ edge, one
per entity whose own `cbst_tie` field (a normal `entities.json` field, set
via `corrections_entities.json` like any other human-conclusion field) has
`confidence` in `{t-doc, t-open, press}` — `none`/`not_established`
entities are excluded, not shown as ties. This exists because the
registry could already assert an entity was ЦБСТ-tied in prose but the
graph had no corresponding edge, making the network's actual center-and-
satellite structure invisible in any graph-based exhibit; don't add a
`cbst_tie` claim without setting `confidence` from that exact vocabulary,
or the edge silently won't render.

**`graph_tier: "reference"`** (people.json, set via `corrections_people.json`) keeps a
minor person -- a relative, a staff member, a contract signatory -- fully on file
(record, `other_entities`, family/role fields) but off the relationship graph, so they
don't clutter it. It is a display decision, not a verdict on the person: if a reference
person gains an `owns`/`founded`/`directs` edge (say, a relative turns out to be
registered as an entity's founder) the builder surfaces them automatically. Their
profile pages are unaffected. Set it deliberately per person with a `why` note; it is
not inferred.

**ё policy (STYLE_GUIDE.md §2.5):** names are *spelled* with ё wherever a source for that
person gives it, and *matched* with ё folded to е on both sides -- never let one depend on
the other. Do not add a ё without a source for that person, and never edit verbatim
quotes or source text. `python3 scripts/yo_audit.py` reports spelling splits.

**Look a name up with `scripts/registry_lookup.py` before calling it unrecorded.** A graph
"unresolved stub", a name in a post, a counterparty in a court filing -- none of them is
"not in the registry" until it has been through the fuzzy lookup (`python3
scripts/registry_lookup.py "Фонд Градислава"`, or `--stubs` / `--nulls` for a rescan). It
matches the bare name, name with ООО/АО/Фонд, a `" | "` alias part, `brand_ru`, Latin names,
`name_history`, ё/е (and Latin yo/e), Cyrillic<->Latin transliteration, `_merged_into` tombstones (answered with the canonical record), plus spelling variants for
people. On 2026-09-19 Фонд «Градислава» was called unrecorded while sitting in
`entities.json` under `"Фонд «Градислава» | historic & cultural heritage preservation"`.
Its lower tiers (`contains`, `fuzzy`, `initials`) are leads to read, never automatic
merges -- "Песков Дмитрий Николаевич" is not the Kremlin spokesman.

**Multi-hop reachability, not just direct edges, is what "connected to
ЦБСТ" means.** A published exhibit once reported an entity as having "no
traceable ЦБСТ edge" based on a 1-hop check, when a real 3-hop path
(Цыганов → «ПОКРОВ» → «Тримикс» → ЦБСТ, all real ties) already existed in
the graph. Before asserting any entity/person is unconnected to the
network, run an actual BFS over `relationship_graph.json` treating every
edge type as undirected for reachability, not a single-hop scan.

`scripts/classify_product_icon.py` maps `products[]` entries to the
17-category Product Icon Set (structured `type_bvs` first, keyword
fallback second) — presentation-layer classification only, same
discipline as the hub-badge offensive/defensive/dual read: not a new
sourced registry field, a deterministic, reviewable rule set. Used by
exhibit build scripts under `scratch_design/`, not by the generated
company profiles.

## Writing: read `STYLE_GUIDE.md` before drafting any prose

`STYLE_GUIDE.md` (repo root, added 2026-08-22) is authoritative for everything
this project publishes: which voice register belongs to which kind of page,
transliteration and legal-form glossing, the EN-is-analysis/RU-is-evidence
rule, identifier formatting, the confidence vocabulary, the euphemism list,
and the pre-publish checklist. It is not in `docs/` on purpose — `docs/` is
the published site, and this is an internal drafting tool.

A draft written in generic register is not a draft that needs editing; it
needs rewriting. Read the guide first, not after.

## Quotes: never paraphrase or invent

Any review, post, testimonial, or other quoted material must be the original
text only — verbatim, punctuation and typos preserved. If a quote can't be
verified against a primary source, don't use it. Full quote-handling rules
(drafting from the original Russian, `[так в оригинале]`, italic-vs-guillemets)
are in `STYLE_GUIDE.md` §3.1.

## Company profiles: generated, not hand-written

`docs/profiles/<slug>.{html,md}` are per-entity profile pages, generated from
`data/registry/` by `scripts/build_company_profile.py` — not edited by hand
(a regeneration would silently discard hand edits, the same reason
`corrections.json` exists for `entities.json`/`people.json`). Run it after
any registry change that touches a profiled entity:

```
python3 scripts/build_company_profile.py --slug ooo-skb-piranya
python3 scripts/build_company_profile.py --inn 7300024069   # equivalent
python3 scripts/build_company_profile.py --all              # every non-adjacent entity
```

Local file processing over `data/registry/*.json` — no network calls, safe to
run directly/repeatedly. Always follow with
`python3 scripts/check_tag_balance.py docs/profiles/<slug>.html`.

`templates/company_profile.{html,md}.jinja2` are the two Jinja2 templates
(one script, two outputs — the section order and field coverage are kept in
sync between them by construction, not by hand). The HTML page links
`docs/assets/profile.css`, a standalone copy of `docs/index.html`'s design
tokens/classes (same `--paper`/`--ink`/`.tag`/`.t-doc` etc. — kept in sync by
hand since profile pages didn't exist when `index.html`'s `<style>` block was
written) plus profile-specific additions (`.person-card`, `.meta-grid`, …).

Follows `STYLE_GUIDE.md`'s expert-witness/forensic register by construction:
Latin name primary with the Cyrillic ФИО/name shown alongside (never hidden
in a tooltip), legal-form abbreviation transliterated not translated, ИНН/
ОГРН as bare digits, and — the important one — **no internal notation in
visible prose**. A claim is cited by a short bracketed `[sNNNN]` id resolved
in the page's own "Sources cited" table (locator + captured/as-of dates, no
sha256 — the hash belongs on a site-wide provenance page this project
doesn't have yet, not repeated on every profile), never by printing a raw
`source_id`/registry-field name. A person's freeform `notes` field is **not**
dumped into the page — it's an internal working note (often containing
passport/phone numbers alongside research-process commentary); only the
structured PII fields already vetted under the PII policy below (`dob`,
`birthplace`, `address`, `inn_personal`) render on the page.

**Images**: `entities.json`'s `images[]` and `people.json`'s `photo` already
point at `docs/images/<file>` (the publish-ready copy) — `data/sources/` is
the gitignored raw archive, not part of the published site. The HTML output
only embeds an `<img>` when a `docs/images/` copy actually exists (checked at
build time); otherwise it falls back to a text citation so a photo that's
only in `data/sources/` doesn't render as a broken image. The Markdown
output isn't published, so it links `data/sources/` paths directly. This
means a fresh `battlefield_evidence[]`/`images[]` entry (e.g. from
`scripts/tg_media_pull.py`) needs its file copied into `docs/images/` before
it'll actually appear in the HTML profile — pulling the media isn't enough
on its own.

Ground/satellite views of a facility are just `images[]` entries distinguished
by caption text (e.g. `_ground.jpg`/`_satellite.jpg` naming, already used at
`ooo-aeromaks`) — there's no separate schema field for them.

The landing page (`docs/index.html`) links the profile index (`docs/profiles/index.html`) and every case page carries the same site nav; both are generated (see Publishing).

### Product profiles and `relationship_type`

Product profiles (`build_product_profile.py`, `FLAGSHIP_PRODUCTS`, flagship products only) and the `related_entities[].relationship_type` vocabulary are documented in `notes/reference/script_notes.md`. Standing rules: extend `FLAGSHIP_PRODUCTS` one real product at a time; set `relationship_type` from `graph_contract.RELATED_ENTITY_RELATIONSHIP_TYPES` whenever adding a `related_entities[]` entry; never populate `competitor` without a sourced claim.


## Publishing

**Changed 2026-09-20 at user direction: the old brief is no longer the landing page.** `docs/` (repo Settings → Pages → `/docs`) is now a small site:

- `docs/index.html` — generated landing page (routes to cases, the graph explorer, the profile index, `story.html`, the dossier).
- `docs/cases/index.html`, `docs/cases/<slug>.html` — case studies, generated from `notes/case_study_<slug>.md` plus a static graph excerpt and a resolved sources table. Case list and status live in `CASES` in `scripts/build_case_pages.py` (seven cases: Архангел, Гагаринг, ГОУДРОН, Овод and НПЦ БАСиРТК published, Цыганов/Булат built; Пиранья planned). Grades use the registry vocabulary (`{doc}` Primary doc, `{press}` Press-reported, `{open}` Open); a case note must state the entity's registry tier and ЦБСТ-tie position accurately.
- `docs/dossier.html` — the former `docs/index.html` (the long written brief), kept and linked as the "Registry dossier"; it is also the source of the standalone Artifact companion (https://claude.ai/code/artifact/5450bf7e-7f7b-4788-93c0-761503dd5ea4). Edit it freely; only republish the Artifact when the user calls an explicit investigation cutoff — see `roymarket_no_per_fold_publish` (seeded memory) for why (the Artifact intentionally lags the local file between cutoffs). Nothing new here is published as an Artifact before that call.

**Pushing `docs/` publishes it (Pages serves `/docs`): a Pages-only page is still public, so push new landing or case pages only on the user's explicit go-ahead.** Regenerate after a case note or registry change: `python3 scripts/build_case_pages.py`, then `python3 scripts/check_tag_balance.py docs/index.html docs/cases/*.html`.

## Tag-balance check before any publish

Run `scripts/check_tag_balance.py` (see the seeded memory
`html_brief_tag_balance_check`) after every `docs/dossier.html` edit, before
publishing; with no arguments it checks the dossier, and for generated pages pass them explicitly (`docs/index.html docs/cases/*.html`).

## PII handling

**Policy changed 2026-08-22 at explicit user direction. The former name+role
default no longer applies — do not restore it.**

Named individuals in this investigation are recorded with **full identifying
detail**: name (ФИО and Latin), date of birth, place of birth, address,
personal ИНН, and any other identifier that supports a match. The rationale
the user gave: these are public PEPs, and the output feeds sanctions
screening, where a date of birth is frequently the field that makes a match
legally usable rather than merely suggestive. The user supplies this data
where available.

Rules that still hold:

- **Every identifying field carries its own source.** A DOB or address with
  no `source_id` is left null, never inferred, never filled from a
  plausible-looking namesake. The scale-up in what gets published is a
  reason for more sourcing discipline, not less — see
  [[roymarket_project_goal]]: this material has to survive a hostile lawyer.
- **Photographs** are sourced from the subject's public or professional
  presence — their own channel, their company's site, press coverage, an
  official event. Not private or family imagery.
- **Individuals who are not PEPs, network principals, or affiliated
  participants** — a resident mentioned in passing, a private person named
  in a court filing unrelated to this network — are not in scope for this
  treatment. Ask before extending it to anyone who doesn't fit an already-
  established category below.

**Policy amended 2026-09-04 at explicit user direction, to add a second
in-scope category: confirmed participants of a network's own recruitment/
training/operational apparatus** — course students, instructors, chat
admins/moderators, named contacts — not just its owners/directors/officials.
Rationale the user gave: for an operation like Проект «Архангел» that trains
and equips people for combat drone operations feeding the war, a documented
participant is not a bystander — they are plausibly someone who goes on to
serve in the operations this investigation exists to document (see
[[roymarket_project_goal]]), and identifying them is itself a legitimate
finding, not incidental collateral. This is DISTINCT from indiscriminately
cataloguing every name that surfaces near the network — the bar is a
**confirmed** participation link (posted in the network's own chat, listed
as a course student/instructor, tagged admin, etc.), sourced the same way
any other identifying field is (see the sourcing-discipline bullet above).
A name that only appears as a stray mention, forwarded content, or someone
else's contact reference does NOT clear this bar on its own.

**Photographs**, for this category specifically, may be sourced from a
self-published Telegram/social profile picture in the network's own
chat/channel — this is the person's own chosen public-facing image on a
platform where the group itself has 1,000+ members, not private or family
imagery, even though it isn't press-sourced. The existing rule (own
channel/company site/press/official event) still governs PEPs and
principals; this paragraph only widens what counts as "public presence"
for confirmed affiliated participants.

**Proportionality still applies.** Finding 500+ names in a single chat scan
does not mean 500+ full person records — triage for a real signal (exposed
phone number, distinctive photo, a named role/title in their own bio,
cross-referenced elsewhere in the network) before promoting someone to
people.json, the same judgment call already used for zakupki
vendor-mention triage and press-lead triage elsewhere in this file. When in
doubt on a specific name, it's fine to ask.

The earlier logged exception (an InformNapalm OSINT dossier carrying full
addresses and passport numbers) is no longer an exception; it is now
consistent with the standard.

## Adjacent-but-not-ЦБСТ networks

Entities/networks that turn out to lack a confirmed ЦБСТ/РОЙ.МАРКЕТ tie
(same industry, physical proximity, name collision — but no institutional
link) get a one-line disambiguation in `docs/index.html` at most, with full
detail parked in memory instead. See the seeded `roymarket_adjacent_networks`
memory file — check it before starting a fresh deep-dive on something that
smells adjacent-not-core.
