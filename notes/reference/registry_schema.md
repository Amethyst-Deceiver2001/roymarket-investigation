# Registry schema and modelling rules

Moved verbatim from CLAUDE.md on 24.10.2026, when CLAUDE.md was cut to a short rulebook; stale facts corrected where marked. CLAUDE.md keeps the rule in one line and points here for the detail.

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
  Optional `site_operator` (added 26.10.2026): the operator's wording shown
  under a price list, kept when the claim is the price list itself.
- `appearances[]` and `timeline_extra[]` (26.10.2026) — hand-held, English only.
  `appearances[]` is `{date, date_end, kind: report|programme|exhibition, outlet,
  speaker (people slug), text_en, source_id, also[]}`: a public statement or show as a
  source reports it; the company page lists it under "Public appearances" and on the
  timeline. `timeline_extra[]` is `{date, text_en, source_id}` for one dated
  event with no field of its own (an announcement).
- People on a company page (26.10.2026): a role entry with no title shows the
  register-derived role (director, owner) from the entity's `director`/`founders`;
  a title starting "Co-founder" shows as the company's own claim. Under each person the
  page lists, from their record, `egrip_hits[]` that carry `source_id` (with
  `terminated`, `activity_en`), `other_entities[]` where they are director, and
  sanctions with a read source. A person's `inn_basis` text goes to the page's limits:
  use it when the personal INN came from the investigator, not from a document that
  names the person in the role.
- `address_history[]` entries may carry `kind` (26.10.2026): `registered` (the
  default; from the register extract), `legal-own-site` (the legal address the
  company's own site gives) or `actual` (where it receives visitors or post),
  and `also` (further `source_id`s). The register block and "Registered address"
  use only `registered`; a page lists all kinds under "Where it is".
- `contacts[]` (26.10.2026) — `{kind: phone|email|messenger, value, label,
  as_of, source_id, also[], note}`. One entry per number, address or handle
  as a source prints it; `as_of` is the date of the source it was read from,
  `also` lists later or other sources, and `label` is English (the Russian
  wording goes in `note`). A number seen only in a post is cited by that
  post's source. A look-alike domain (gdrone.ru for godrone.ru) is recorded as
  printed, with the difference named in `label`.
- `legal_form: "Military unit"` (26.10.2026) — a unit with no INN or OGRN of
  its own. Its supporting foundation is the `related_entities` link with
  `relationship_type: "group-structure"` whose record holds the INN/OGRN; the
  company page shows that foundation's identifiers and matches screening
  lists on them. Never invent an identifier for the unit.
- `zakupki_review` — `{as_of, outcome: wired|partial|closed, note, hits}`
  (see `script_notes.md`). `hits` (26.10.2026) is the supplier hit count of
  the 44-ФЗ search; the company page prints a Limits line "No state contract
  is on record" only when `hits` is 0, the entity has an INN and no
  `government_contracts[]`. Record the exact query and date in `note`.
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


**Reader citations (B4, 2026-10-02).** Every `sources.json` record carries a generated `title` (plain words: what the document is, its publisher, number and date) and `public_url` (only where the file or a registry number gives one), plus `tg_post` (`channel/msg`) and `duplicate_of` for a Telegram post captured twice. All rules are in `scripts/source_citation.py`; never write a citation rule in a page builder, and never hand-edit these fields. A new kind of source file gets a rule there and a fixture in `tests/test_source_citation.py`; bump `CITE_VERSION` so `inventory_sources.py` re-reads the files. `check_registry.py` errors on a missing title or one that leaks a file name or source id.

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

**`grade` on every edge** (schema v12, B1, 2026-10-02): doc / rep / open, the reader's three grades. It is derived, never hand-set: from the edge's `confidence` via `CONFIDENCE_GRADE`, else from its source's filename prefix via `SOURCE_PREFIX_GRADE` in `graph_contract.py`, else open. A party's own posts, site and listings grade rep. A new kind of source file needs a row in that table. `build_graph(..., sources)` takes `sources.json` for this.

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

**`graph_tier: "held-off"`** (entities.json, set via `corrections_entities.json`) keeps an
entity fully on file (record, profile page, `sanctions[]`) but off the relationship graph
outright. Unlike a `reference` person it is NOT surfaced by `owns`/`founded`/`directs` edges:
it exists for an entity that ownership chains connect to the network but whose *own* tie to
ЦБСТ is unproven (the Tula ООО «Центр беспилотных систем», 2026-09-30, was linked only by an
OpenSanctions merge with the Moscow АНО). Held slugs are listed in `detached_ids`, so the omission
is visible. Set it deliberately with a `why` note and remove it when a solid link is found.

**`government_contracts[].graph: false`** keeps one contract fully on file but produces no `procures`
edge or customer node. It exists so a long, old or unrelated B2G history (АО «Кронштадт», 2026-09-30: 176
pre-2018 simulator contracts under the former ЗАО «Транзас» ИНН) doesn't swamp the entity's neighbourhood.
Set it per contract with a `why` note stating the rule used; never delete the contract to thin the graph.

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
**`scripts/graph_query.py`** does exactly this BFS for you: a name/slug
neighborhood (`python3 scripts/graph_query.py "Цыганов Вадим Борисович"`,
fuzzy-resolved via `registry_lookup.py`'s `Registry.find()`) or a shortest
path between two nodes (`--between "A" "B"`), printed as cited
`(source) --[type: label]--> (target) [sNNNN]` triples with any
source-less edge flagged in a trailing warning. Local, no network, no LLM
call -- it prints grounded context to read and verify, it does not answer
a question on its own; reach for it before ever asserting two things are
(un)connected.

`scripts/classify_product_icon.py` maps `products[]` entries to the
17-category Product Icon Set (structured `type_bvs` first, keyword
fallback second) — presentation-layer classification only, same
discipline as the hub-badge offensive/defensive/dual read: not a new
sourced registry field, a deterministic, reviewable rule set. Used by
exhibit build scripts under `exhibits/`, not by the generated
company profiles.

**Where exhibit assets live (consolidated 2026-10-01).** `exhibits/` (renamed from `scratch_design/`) holds every standalone exhibit, mockup, icon set and their builder scripts, plus `exhibits/images/` for their pictures. `docs/` holds only what is published: generated pages and `docs/images/` (profile media). A finished exhibit that is published is generated into `docs/` by a build script; do not hand-copy it there, and do not leave drafts in `docs/` or `notes/`.

## Ecosystem roles and sellers (added 2026-10-01 at user direction)

A maker's goods reach buyers through legal entities that are not the maker: the Ozon sole traders that sell КБ «СПЕКТР» propellers, the named dealers of «3mx». The registry models them without a new tier.

- **`ecosystem_roles`** (list on an entity, vocabulary `graph_contract.ECOSYSTEM_ROLES`: `manufacturer`, `brand`, `seller_of_record`, `licensed_dealer`, `distributor`). It is orthogonal to `tier`, which measures closeness to ЦБСТ: a seller can sit at any tier. Absent means unclassified, not manufacturer.
- **`sells_for[]`** (on the seller): `{slug, channel, basis, source_id, as_of, note}`. The builder draws a `sells_for` edge (schema v7) labelled with the channel and graded `doc` / `press` / `inferred` in `confidence`. `doc` means a primary document (a marketplace seller panel, a dealer certificate, the maker's dealer page, the seller's own site) states the sale. It never says the maker authorised it unless the document does. `check_registry.py` validates the shape; an edge to a mistyped slug is otherwise dropped silently by the builder.
- **Relation envelope (schema v9, 2026-10-02, piloted on `sells_for`).** Optional fields on a `sells_for[]` record, drawn into the edge's `detail` object (null on every other edge): `products[]` (strings as the document names them), `status_history[]` (`{status, as_of, source_id, note}`, status in `announced`/`onboarding`/`listed`/`shipping`/`delisted`; an undated or unsourced state is not recorded, and the edge shows the latest), `asserted_by` (`self`/`counterparty`/`platform`/`regulator`/`press`/`investigator`), `credibility` (`doc`/`corroborated`/`single`/`inferred`; may not contradict `basis`), `authorised` (`yes`/`no`/`unknown`/`n/a`), `role` (what the seller is on this edge: `manufacturer`/`seller_of_record`/`licensed_dealer`/`distributor`; the entity's `ecosystem_roles` is only a summary and `check_registry.py` warns when it misses a role used on an edge) and `open` (what the edge does not prove). `basis` stays the coarse grade the graph draws; the envelope separates who said it from how sure we are. All six current edges carry it (КБ «СПЕКТР», the 3mx dealers, НПЦ БАСиРТК). Extend to other edge types only if a real case needs it; `check_registry.py` validates the fields, `tests/test_relationship_graph.py` holds the fixtures.
- **`platform_partners[]` (schema v10, 2026-10-02)**: on a platform operator, `{slug, kind: bank|acquirer|logistics, basis, source_id, as_of, note}` draws `banks_with` / `acquiring_via` / `ships_via` edges to the partner's entity, graded like `sells_for`. A partner is recorded only from a document that names it: a generic «эквайеры» or «логистический партнёр» is not a partner. First use: `ooo-mptm` banks with `pao-bank-psb` (offer s8817). Acquirer and logistics partner stay open questions until a primary document is archived.
- **`candidate_identities[]` (2026-10-02)**: unverified same-name legal entities for a brand stub or an unresolved identity: `{name_ru, inn, status: unverified|rejected, as_of, source_id, note}`. It is **not an edge and not a node**: nothing is drawn or counted as a tie, the ИНН is never copied into the record's own `inn`, and no entity record is made for a namesake (a record needs a documented link). `check_registry.py` validates the checksum, the date and the source, and errors if a candidate ИНН equals the entity's own. The three same-name ООО «КБ «СПЕКТР»…» of 2019 are the first use (`kb-spektr-novosibirsk`).
- **Brand without a legal entity:** an entity may be a brand stub with `legal_entity_status: "unresolved"` and no ИНН (КБ «СПЕКТР», `kb-spektr-novosibirsk`), so sellers can point at it without a guessed identity. Never fill the ИНН from a name match; the three same-name Новосибирск ООО of 2019 are in `notes/roymarket_vendor_leads.md`, not in the registry.
- **`related_entities[].relationship_type: "operated-brand"`:** a company or sole trader that traded under the other record's brand during a dated period, per a document. The older prose `dealer` entries stay on file (the case-study builder reads them); where a seller also carries `sells_for` for the same pair, the graph draws only the structured edge.
- A seller's cluster is drawn only if a path reaches the ЦБСТ hub; otherwise it is listed in `detached_ids`. The РОЙ.МАРКЕТ operator is `ooo-mptm` (role `platform_operator`, `cbst_tie` t-doc from ЦБСТ's 2025 Минюст report s0207 and the supplier offer s8817); non-resident vendors point at it with `sells_for`, so they join the graph through it.
- **PII scope, third category:** a seller (usually a sole trader) gets an entity record, and its owner a person record only on user direction, when it has a **documented link to a registry manufacturer or to РОЙ.МАРКЕТ**. A marketplace listing alone is not enough. (2026-10-02: an owner who is involved in the trade is a person of interest under the PII section's amended rule.) Same sourcing rule as every identifying field: the ИП's ИНН comes from its ЕГРИП extract, never from a plausible namesake, and no date of birth or address is filled without a source. Individuals recorded under this category so far: Братеньков, Маврин (person of interest, user, 2026-10-01). ИП Карпушин has an entity record but no person record.

## Products (`data/registry/products.json`, added 2026-10-02 at user direction)

One record per product with a stable slug, so a product sold by several dealers is one record and does not crowd its maker's node. Records: «Булат» (`bulat`, maker `ooo-trimiks`) and «Капюшон» (`kapyushon`, maker `ooo-npo-kilovatt-shestopalov`, trademark held by the sister `ooo-npo-kilovatt`; B7, 02.10.2026). Fields: `versions[]` (each with firmware and the maker's own page as source), `accessories[]` (`pairs_with` a version), `shown_at[]` (events in `programs.json`), `listings[]`, `claims[]`, `open_questions[]`. Its handovers are in `deliveries.json` (below), not on the product.

- **Listings and deliveries are dated events on the product, not graph edges.** A listing is `{id, version|null, channel, url, seller{entity|null, storefront, identity}, status, as_of, source_id, basis, asserted_by}`; `status` uses the sale vocabulary of the relation envelope. A storefront whose seller is not a registry entity says so in `seller.identity` and keeps `entity: null`; no entity is created for a dealer without a documented link (PII scope, third category). A seller entity other than the maker needs a `sells_for` edge to the maker, or `check_registry.py` warns.
- **A listing with no `source_id` is a placeholder** and warns. The two WB brand-store listings of «Булат» are in that state: capture the pages.
- **`data/registry/deliveries.json` is the one record of reported handovers (merged 24.10.2026, user; it replaces `handovers.json` and the `deliveries[]` that sat on each product).** One event per post per recipient, 65 so far: 23 name «Булат» or «Капюшон» in `items[]` (26 product items; three posts report both), 42 name no product ("equipment"). Field list and the compatibility view are in `scripts/deliveries.py`; code that wants a product's handovers calls `deliveries.load_products()`, which attaches `deliveries` in the shape the pages read. An event needs `{id, date, donor, carrier, recipient, source_channel, post_id, asserted_by, credibility, items[]}`; a product item also needs `version` (null when the post names only the product) and a catalogued `source_id`. `source_id` may be null for a handover post not catalogued yet (one warning). Ids are stable names, never renamed (`bulat-d05`, `h0025`); media records point at them. Several channels reporting one handover are one event with `other_source_ids`. Optional English fields (26.10.2026), hand-written, never machine-transliterated: `carrier_en` and `items[].item_en`; the company page's "Handovers it reports" section lists only events of its own donor whose items all have `item_en`. Posts 382, 397 and 448 report both products to one recipient: one event with two items, and the second item's `id` (`kapyushon-d05`, `-d06`, `-d08`) is the name its product's view and media records use. Recorded so far: 24 «Булат»/«Капюшон» rows from Фонд «Наша Правда»'s own posts, 1 from ЦБСТ and 1 from the maker 3mx (18 «Булат», 8 «Капюшон»). Recipients include civilian services (a hospital, power-repair crews), recorded as the post names them. An accessory's `pairs_with` may be null when the source fits it to the whole product family. A product shows a «not sold on РОЙ.МАРКЕТ» card only when a document speaks to it.
- **Deliveries come from `python3 scripts/delivery_signal_scan.py`** (delivery verb near a recipient near a product; local, 22 s; class A names a registry product, class B only a category). A hit is read in full before it becomes a delivery. `version` may be null when the post names only the product.
- **Delivery rules (user, 2026-10-02).** The fact of a delivery matters more than the exact recipient. Record the recipient as the post names it: a unit, a town (allowed), or only a direction (enough). A recipient unit may sit in the rear (a «Булат» guarding a base inside Russia or in occupied Donetsk), so a delivery never implies combat use and no field-use claim is drawn from it. Donors and carriers may be volunteer groups and individuals: anyone involved in a delivery is a person of interest (PII section). Every donor or volunteer report defaults to `asserted_by: self`, `credibility: single`; it is upgraded only by an independent second source, such as the receiving unit's thank-you letter. Units named only in a manufacturer's marketing still do not enter `military_units.json` (peer audit 15.09.2026); units named in a recorded delivery do.
- **Unit names (user, 2026-10-02).** A unit can appear as `в/ч XXXXX`, a full official name with honorifics («123-я отдельная гвардейская мотострелковая … бригада имени …»), a short military abbreviation («123 омсбр») or an informal name («Пятнашка»). Keep every form the sources give on the unit record, each with its source. A bare `в/ч` number is resolved to the formation's name only through a source that states the pairing (a sanctions entry, a court or procurement record), never from a lookup site alone. **Normalized 05.10.2026** (`notes/unit_normalization_design_20261005.md`): a unit is identified by number + type + arm + parent formation, never the number alone (there are two 237th regiments, tank and air-assault, and the 76th is one formation the donor's posts call «бригада» and «дивизия»). Records carry `number`, `arm`, `names[]` (form official/short/informal/post_wording/vch, each with its own grade `stated` or `lead` and source) and `parent_history[]` (dated, graded); the record id stays the slug and merged slugs sit in `legacy_slugs`. `python3 scripts/unit_lookup.py "<free text>"` resolves a phrase to `resolved`, `ambiguous` (a bare number never picks a unit) or `unrecorded`; `--check` lists duplicate records and handover recipients that do not resolve. Fixtures: `tests/test_unit_lookup.py`; the field checks run in `check_registry.py`. The English label is generated (`unit_names.name_en`, e.g. «237th Guards Air Assault Regiment»), not an official name; the public card shows only `stated` items. A parent, в/ч or official name from the user, an encyclopedia or a search summary is a `lead`. The workbook `~/Downloads/ОЗ ВС РФ.xlsx` (unit hierarchy and tactical markings) is an internal finder only: never cited, catalogued or copied into `data/sources/`. `notes/delivery_signal_scan_20261002.md` has the method, limits and first result («Булат»: 16 donor deliveries).
- **In the graph (schema v11):** a product record is one `product` node (`product::<maker>::<slug>`), and the maker's own per-version `products[]` leaves that it covers are not drawn separately. Each distinct storefront in `listings[]` is a `storefront` node (no legal identity), linked `lists` to the product (the latest listing per storefront, label = channel) and `operated_by` to its seller entity only when the listing names one; a dealer with no registry entity stays a storefront. Entity nodes carry `product_count` for a count badge and expand-on-click in a viewer (the viewer is outside the repo). `clone_of` (`{product, status: alleged|shown|denied, asserted_by, source_id}`) is validated but unused: a product is a clone only where a cited source says so, never because it competes in the same class (the «QD-HD-003» and «Сокол» manuals in the 3mx chat are competing devices per the registry's own read, not clones of «Булат»).
- **State contracts name their products (B2, 2026-10-02):** `government_contracts[].products[]` = `{product, version|null, item_ru, qty|null, unit, unit_price_rub|null, source_id, note}`, read from the printed contract or its specification, never from the subject line alone. `item_ru` is the line as printed. A supplier delivering another maker's product needs a `sells_for` edge to that maker (`check_registry.py` warns). Give a contract's `date` to the day where the document states it.
- `python3 scripts/product_chain.py bulat` prints the chain (maker, versions, listings with their basis and source, deliveries, open questions). 

## Media (`data/registry/media.json`, track V, added 2026-10-02 at user direction)

One record per photo, video, still, satellite or street-level view, screenshot, scan or graphic. It is hand-maintained like `programs.json` and not drawn on the graph. Its fields:
- `about[]` lists every record the picture shows (entity, person, product, version, delivery, listing, unit, program). One handover photo is one record, not three copies.
- `on_pages: false` keeps a picture off every reader page while leaving it publishable elsewhere (the story, packets); `display_helpers.media_about()` drops it and `on_pages()` tests it. **User rule (27.10.2026):** pages carry only a few good-resolution pictures, each backing a line of the copy; no generic people in uniform or nondescript boxes.
- `caption_en` is the one plain line a reader page captions the picture with (what it is, not an inventory of what is visible); `display_helpers.media_caption()` prefers it to `shows_en`. English only.
- `shows` says what is visible, written by someone who looked at it. On English pages, a caption containing Russian also has a translated `shows_en`; the English caption leads and the original `shows` text sits under RU. `check_registry.py` requires the translation for publishable captions.
- `asserted_by` says who published it. It is shown on pages as provenance ("the maker's own video"). `third_party` covers customer uploads.
- `publish` is `ok`, `excerpt` (a maker's marketing, used in part for reporting) or `internal`.

Rules (user, 2026-10-02):
- **No source, no record.** A picture enters only with the `source_id` of where the picture itself came from, not the document that gives an address.
- **Video:** key frames plus a link to the original, with the original archived and hashed. A still records `frame.t`, its timestamp in the video. Self-hosted clips come later; there are no embedded platform players.
- **Faces (corrected by the user 02.10.2026):** everyone involved is a person of interest, with or without a record: recipients (soldiers receiving equipment), donors, carriers, staff, course participants and recruiters. Their faces are shown. Blur only someone clearly uninvolved: a passer-by, a child, a person who happens to be in frame (`redact: blurred` in the publish copy; the original stays in `data/sources/`). A face is never used to name anyone: captions describe ("servicemen receiving…") unless a source names the person. Faces the publisher blurred stay blurred. Look at the picture before setting `redact`; never set it from a caption.
- **Facility views:** Google Earth or Yandex Maps screenshots for now. Record `imagery.provider` and `imagery.date`, and a `geo` whose `method` names how the place was found (`register_address` or `source_stated` needs the document's `source_id`).
- **Graphic content (proposed default):** stills only, a content warning, nothing showing casualties. Combat imagery needs `graphic` set.
- **Triage before looking (03.10.2026):** incoming Telegram media go through `scripts/media_triage.py` (`queue` → user-run `tg_media_pull.py download --queue …` → `process` → `sheets`): picked by their post's text, repeats folded by Telegram id and by image hash, OCR'd and matched locally, ranked by a local CLIP model (`rank`, in `~/.venvs/roymarket-media`; the 8 GB M1 cannot run local vision-language models), then looked at 16 to a contact sheet, likeliest evidence first. Cloud-model captions are not used: they invent printed text. The main session labels sheets itself (`record --by main`); a Haiku first pass costs more than it saves unless batched (measured 03.10.2026), and its label is only a lead. `shows` and `redact` come only from a full-size look. Nothing is looked at twice: `data/registry/_media_looked.json`. Detail: `notes/reference/script_notes.md`.
- **`docs/images/` is public.** Pages serves it, so blur any uninvolved bystander before a file lands there. An image with no archived original must not be added there.

A company card shows the entity's logo from a media record of genre `logo` (set `logo_ground: dark` when the mark is drawn for a dark ground; logo publish copies are trimmed to their content). Deliveries now carry stable ids (`bulat-d01`…) so media can point at them. `check_registry.py` validates the record. Backfill state and gaps: `notes/media_backfill_20261002.md`.

## Brands (`entities[].brands[]`, B5, added 2026-10-02 at user direction)

Readers recognise a brand (3mx, GoDrone, Пиранья) before a legal name (ООО «Тримикс»), so a reader card leads with a documented primary brand. The legal name sits directly beneath it, never hidden, with the Sanctioned flag, because lists name the company, not the trademark. Use `display_helpers.display_name(e)`, which returns the brand as `head`, the legal name and the English gloss.

- **Shape:** `{name, kind: trade_name|trademark, registration, primary, source_id, as_of, note}`, set via `corrections_entities.json`. At most one brand is primary. A `trademark` brand names a registration that is in the entity's own `trademarks[]`. `check_registry.py` validates all of this.
- **A product name is never a company brand** («Булат» is a product of 3mx). One brand can span several legal entities (КБ «СПЕКТР»), so a brand is never used to merge or identify entities.
- **No guessing.** The old free-text `brand_ru` / `brand_latin` are not display sources. Promote a value only after reading its source (`notes/brand_review_20261002.md` records the review of all 38: six promoted, the rest the legal name, a product, or held for a source).
- A card cites the brand: the legal-name line carries the footnote to the brand's source.
- **Latin name (`name_display`).** Generated by `display_helpers.latin_display()` per STYLE_GUIDE §2.3: the legal form is transliterated, never translated, and our own bracketed notes are dropped. It is overridable via corrections (`set.name_display`). `display_name(e)['latin']` returns it, and cards print it under the registered name. It is not the screening string (`name_latin`). Fixtures: `tests/test_display_name.py`.

## Programs, events and groups (schema v8, added 2026-10-01 at user direction)

Residencies, accelerators, the national БАС project, recurring events and same-brand clusters are modelled as records in `data/registry/programs.json` (hand-maintained, like `military_units.json`), not as entity-to-entity edges.

- **Kinds** (`graph_contract.PROGRAM_KINDS`, subtypes in `PROGRAM_SUBTYPES`): `program` (a residency, accelerator, centre network, the national project), `event` (a series and its editions, `part_of` the series), `group` (separate legal entities sharing a brand or founder network; no legal identity, never replaces its members).
- **Who belongs lives on the entity**: `memberships[]` (`{program, role, basis, source_id, as_of, note}`) and `participations[]` (`{event, role, basis, source_id, as_of, note}`), set via `corrections_entities.json`. The builder draws `resident_of` / `participated_in`; the record's own `operators[]`, `organisers[]`, `parent`, `members[]` draw `operates`, `organises`, `part_of`, `member_of`. Grade is `doc` / `press` / `inferred` in `confidence`, as for `sells_for`; `part_of` carries none. `check_registry.py` validates all of it.
- **Counts are claims, not edges.** "30+ residents" is a `claims[]` entry with `as_of`, `source_id` and `asserted_by`. No stub entity for an unnamed resident; named residents attach one at a time.
- **An organiser with no identifier gets no entity.** КЦПН (organiser of Дронница) is named in the record's `organisers` text only until an ИНН is read from a primary document.
- **Participation is not residency.** Exhibiting at an event does not make an entity a ЦБСТ resident; the role and the source say what was shown or signed. Check who organised an event before writing "ЦБСТ's event": Дронница is run by КЦПН and НПЦ «Ушкуйник», and ЦБСТ participates.

