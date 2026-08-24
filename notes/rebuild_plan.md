# Rebuild the РОЙ.МАРКЕТ brief as a two-tier, data-driven publication

> **This is the canonical, live copy of this plan** — moved here 2026-08-24
> (later in this session) from `~/.claude/plans/spicy-beaming-kite.md` (a
> per-session, not-git-tracked location outside the repo) so it survives
> alongside the investigation it governs and doesn't depend on any one
> session's local Claude state. Read and update *this* file going forward.
> `HANDOFF.md` points here. The old external file has been left as a
> redirect stub — if you're reading it instead, come here.

## Context

`docs/index.html` is 1,219 lines / 466 KB / ~50,700 words of hand-edited HTML. It
holds roughly **200 legal entities, 188 named individuals, 45 manufacturer rows,
137 distinct ИНН**, 8 tables, 19 verbatim Russian blockquotes and 24 images. It
is a working research artifact that grew by accretion across many sessions, and
it has passed the point where it can be read or safely hand-edited
(`scripts/check_tag_balance.py` exists precisely because string-replace edits on
it silently break rendering).

Three concrete symptoms of that, found while surveying it:

- **The manufacturers table is malformed.** Line 1026 opens a
  `<tr><td colspan="3">` that stays open until 1051, and between them the source
  emits a stray `</div>`, two `<div class="gallery">` blocks and a
  `<div class="prose">` — all textually inside an open `<td>`. Line 1041 is a
  **51,007-character paragraph that never closes its `<p>`**. Browsers
  foster-parent this out of the table so it looks fine, but no DOM or regex
  edit of that region is safe.
- ~~**The ownership diagram does not render.**~~ **FIXED 2026-08-24** — was a
  ~45-node `<pre class="mermaid">` flowchart in a document with zero `<script>`
  tags, so GitHub Pages showed raw Mermaid source. Now a static inlined `<svg>`.
- ~~**Dead theme code.**~~ **FIXED 2026-08-24** — the `[data-theme]` CSS
  overrides now have a toggle script that sets the attribute and persists the
  choice.

Other structural debt worth naming: four separate "still open" mechanisms that
each rot independently (a 26-item "What is not established" list, a 17-card
"still unmined" grid, two `colspan="3"` catch-all rows buried inside the
manufacturers table, and 13 inline `t-open` chips); heading levels that nest
inconsistently, with 130 lines structured by nothing but bold lead-ins; and the
same person appearing in Cyrillic in one section and Latin transliteration in
another.

The investigation feeds sanctions lobbying, so the output must serve two readers
who want opposite things: a **general/press audience** that needs a short
narrative with the striking findings, and **specialists** (sanctions desks,
lawyers, policy staff) who need every claim, source and identifier per entity.
One document cannot do both, and the current one does neither well.

Three further gaps this rebuild closes:

- ~~**No systematic screening.**~~ **LARGELY CLOSED 2026-08-24** —
  `OPENSANCTIONS_API_KEY` and `OCCRP_ALEPH_API` now drive full-roster, dated
  sweeps. `FNS_API_KEY` is quota-exhausted and redundant;
  `NEWSAGENTDATA_API_KEY` is an unidentified vendor and was dropped by user
  decision. See Phase 2.
- **No voice.** The prose is competent research-memo English. The user is a
  professional journalist with a documented style; drafts in generic register
  need a full rewrite before they are usable.
- **No structured data.** Everything lives only as markup, so the same facts
  cannot be re-rendered, re-screened, or checked for internal consistency.

### Decisions taken (user, this session)

| Question | Answer |
|---|---|
| Structure | Three tiers — narrative recap + full dossier + one profile page per manufacturer, all generated from one registry |
| Language | **EN and RU, both, now** — RU written in RU register, not translated |
| Imagery | New Telegram media-download script; user separately supplies satellite/ground and press imagery |
| Screening scope | **Everything, scripted** — every entity and person through OpenSanctions, Aleph and a web pass |

### Stated assumptions

- **PII policy is changing, at explicit user direction.** `CLAUDE.md` currently
  sets a name+role default — "no personal addresses/ID numbers" — with one
  logged exception. The user has directed that this project now carry **full
  identifying detail on individuals, including date of birth and address**, on
  the grounds that these are public PEPs and the data exists to be run through
  sanctions screening, where a DOB is often the field that makes a match
  legally usable. The user will supply this data where available.
  - **`CLAUDE.md`'s PII section must be rewritten in Phase 0** to record this as
    the new standing policy. Leaving the old rule in place would guarantee a
    future session reverts the work, and the existing text explicitly warns
    against treating a one-off exception as the default — so the change has to
    be written down, not just remembered.
  - Registry gains `dob`, `birthplace`, `address`, `inn_personal`,
    `passport_refs` on `people.json`, each with its own `source_id`. A field
    with no source stays null.
  - The one bound I'd still keep, and will flag rather than assume: photographs
    sourced from the subject's public/professional presence (own channel,
    company site, press, official event) rather than private family imagery.
    Say if you want that dropped too.
- **Research depth is bounded by significance**, per the existing mariupol rule:
  full treatment for ЦБСТ leadership, the ~40 manufacturers and the ДАР money
  layer; a shallow pass for the long tail of registrars, auditors and property
  vehicles. "Surname I.O., role only" stays an honest fallback.
- The Artifact is **not** republished during this work — only at an explicit
  user-called cutoff (`roymarket_no_per_fold_publish`).

---

## Status as of 2026-08-24 (supersedes the per-phase notes below)

| Phase | State |
|---|---|
| 0 — Foundations | **Done.** Both remaining items closed: the Mermaid flowchart is now a static inlined `<svg>` (zero `<pre class="mermaid">` left), and the `[data-theme]` toggle has a working inline script. Verified in headless Chrome; `check_tag_balance.py` clean. |
| 1 — Registry (entities) | **Done.** 147/148 entities `_verified` (only `krams-brand-unresolved` open — genuinely unresolved, correctly left so). 141 with ИНН, 140 with ОГРН. `check_registry.py`: 0 errors. |
| 1 — Registry (people) | **Not done — the neglected half.** 148/153 people are `_verified: false`, and **120 of 153 role links carry `_candidate: true`** (~78% of person→entity claims unconfirmed). See new **Phase 1b**. |
| **1b — People verification** | **NEW.** Gates Phase 4's People block. User-chosen over shipping hedged person data. |
| 1.5 — Source triage / typology | **Partial.** Files typed, but `facility_type` is populated on **3 of 148** entities — 1.5b is effectively unstarted. |
| 2 — Screening | **Substantially done**, 4 blockers documented below. OpenSanctions, Aleph and Rospatent trademarks all swept full-roster. **People-side OpenSanctions cross-reference now also done** (2026-08-24) — see below. |
| 2b — IP sweep | **Bulk-CSV pass done and superseded by a better source.** The `rospatent_tm_search.py`/`rospatent_patent_search.py` bulk-CSV sweep (`s0945`/`s0952`) is complete, but a live, unauthenticated JSON API at `searchplatform.rospatent.gov.ru` was reverse-engineered this session (see new findings below) and is materially more capable — full-text `patent_holders` substring search plus exact-field inventor search, vs. the CSV's bibliographic-only, no-wordmark-text limitation. `scripts/rospatent_searchplatform_search.py` full-roster `--force` sweep is **done**: 51/93 manufacturer-tier entities returned at least one candidate hit. **Triaged (2026-08-24), not yet promoted**: ~14 entities carry genuinely new, exact-name-matched, on-topic UAV/counter-drone patents (АО «НИИ «Вектор» — interceptor UAV + jamming, largest new find; НПЦ «ЭЛВИС» — UAV detection + anti-drone gun; АО «НИИ СТТ» — 9 UAV-specific patents; Тримикс — UAV detection device; plus ЦКБР, Клеверкоптер, Котлин-Новатор, ЭйАрТэк, Аэроплатформы, Сибирская навигационная компания, Центр Динарус, КРАВТ Удмуртия, НПП Радар ммс, Аркодим). Common-word/surname false positives correctly rejected (Гермес, Логос, Площадь, Росс, Прайм, Проммаш, Покров, and a Информационные-системы/ИНФОТЕКС word-order collision). One ambiguous case flagged for individual verification (ao-npp-bat's RU233454U1, truncated patentee string). **Promotion into `patents[]`/`corrections.json` with proper archiving is the next concrete step — not yet done.** |
| 2c — Foreign components | **Done, full-roster.** `screen_gur.py` (sanctions/uav-companies sections) swept full-roster earlier. **New this session**: a second, previously-missed GUR section — the `/components` foreign-parts teardown catalogue (5,851 records, no ИНН/ОГРН) — was identified (user-flagged), built into `screen_gur_components.py`, and swept full-roster. One confirmed real hit: `npts-ushkuynik`'s own flagship UAV ("Князь Вандал Новгородский") named directly by GUR with 12 foreign components (China/Taiwan/US/Switzerland), archived and promoted into `foreign_components[]`. All other candidate hits (16 on the first pass, 4 after adding a stopword filter) reviewed and rejected as generic-word or unrelated-platform collisions. A same-session "CBTS.611000" naming coincidence was investigated and explicitly rejected as a ЦБСТ tie (Ц transliterates as "Ts", not "C") — logged as a correction, not silently dropped. |
| 3 — Imagery | **Started (2026-08-24, later in this session).** First small batch of real assets collected from data already harvested (not a fresh scrape): 3 POI headshots pulled from leader-id.ru profile photos (only for people with an already ID-confirmed `user_id` — Барахтин, Соловьев, Лысенко) and 3 company logos pulled from the rk.2035.university БАС-showcase dataset (`s1168`, only for entities already corroborated against it — Радар ммс, Клеверкоптер, Эколибри). Linked via `people[].photo` / `entities[].images[]`. Coverage is thin — most people have no leader-id photo set, most entities have no rk.2035.university listing at all. `scripts/tg_media.py` (Telegram media download) still doesn't exist; VK avatar pulls via the existing `scripts/vk_fetch.py` haven't been run for imagery specifically. See updated Phase 3 below. |
| **3.5 — Registry hardening** | **Partially done.** Item 8 (commit everything) is **DONE** — see "Two things to fix," now three, below. Items 1 (fix the `wb_overlap` regression) and 2–7 (overwrite guard, type normalization, `_merged_into`, reverse source index, open-question unification, generalize `check_tag_balance.py`) are **still open** — the registry is safe (committed) but not yet generator-safe. |
| 4 — Generator | Not started. New prerequisites identified — see **Phase 3.5**. |
| 5 — Prose | Not started. Thesis framing has changed — see revised Phase 5. |

**Registry now holds:** 148 entities (93 manufacturers, 28 money-layer, 14
plumbing, 9 cbst-core, 4 adjacent), 154 people, 977 sources, 19 quotes.
58 entities and **33 people** now carry `sanctions[]` entries (27 → 33 this
session, via a full triage of all people with `opensanctions_matches[]` but no
promoted `sanctions[]` yet — 6 promoted on exact score-1.0 identifier match, 2
flagged as open questions rather than promoted due to a genuine two-candidate
name collision, see below). People with `inn_personal` set: 17 → 23.

### Things to fix

1. **A regression I introduced — STILL OPEN, the one real blocker left.** The
   `wb_overlap` bulk sweep set `ooo-trimiks-bulat-3mx` to `none_found`,
   **overwriting a hand-verified `confirmed`** — the flagship "64 active
   listings, 63 of them `strict_military`" finding that `docs/index.html` still
   calls "this brief's first confirmed overlap" and that the entire Phase 5
   narrative is built on. The registry and the brief still contradict each
   other on the single most load-bearing claim in the project. Cause: Тримикс
   reaches Wildberries through **four reseller ИП accounts**, not its own ИНН,
   so an ИНН-keyed sweep found nothing and a bulk write turned that absence
   into a conclusion. Verified 2026-08-24 (later in this session) that this is
   still unfixed — `entities.json` still shows `wb_overlap: none_found` for
   `ooo-trimiks-bulat-3mx`. **Do this before Phase 4 or any publish.**
2. ~~**Nothing is committed.**~~ **FIXED 2026-08-24.** Four commits now hold the
   entire registry and everything built on top of it: `06ff756` (the structured
   registry pipeline itself — `data/registry/`, screening scripts,
   `STYLE_GUIDE.md`, 70 files), `f56e93b` (the remaining patent-sweep triage,
   see #3 below), `2918d2e` (Барашков А.С. PII enrichment via an
   identifier-confirmed OSINT dossier — see Phase 1b notes), `8d286d1` (first
   POI headshots + company logos — see Phase 3). `data/sources/` stays
   correctly gitignored throughout (verified via `git check-ignore -v` before
   each commit) — only the registry JSON, scripts and `docs/images/` assets are
   tracked.
3. ~~**Newly-triaged patent finds are not yet promoted.**~~ **DONE 2026-08-24.**
   All 37 remaining entities from the `rospatent_searchplatform_search.py`
   full-roster sweep were triaged: 8 promoted (~58 patents, incl. 3 resolved via
   confirmed-director personal-patent matching — Фоминых/«ОПКБ Экспломет»,
   Барашков/«Гагаринг», Бегак/«АКР Бегак»), 29 explicitly rejected with reasoning
   recorded, 1 (`ooo-aviron`) left as an open question rather than forced either
   way. `check_registry.py`: 0 errors throughout. Committed as `f56e93b`.

### Findings since the plan was written, that change the design

- **Reseller-mediated marketplace access is a discovery, not noise.** The
  flagship WB overlap is invisible to ИНН-keyed screening. Any "is this maker on
  WB?" check that looks only for manufacturer-owned storefronts systematically
  misses the real pathway. This belongs in the schema *and* in the prose.
- **A new OFAC-designated entity**: ООО «Центр беспилотных систем» (Tula, ИНН
  7100032961, ОГРН 1237100001467, EO 14024) — found and primary-source verified
  this session, carefully disambiguated from АНО «ЦБСТ»'s own Moscow ИНН.
- **IP filings work as the EGRUL-redaction workaround Phase 2b predicted.**
  АО «АУРИН» and ООО «НПО Рустехдрон» — both founder-access-restricted in EGRUL —
  file trademarks through the *same* patent attorney (ООО ЮФ «АЙ ПИ ПРО», Леонов
  А.В., same Moscow office).
- **Trademarks date real inception before the current legal entity.**
  UralDronZavod's brand was filed by two other holders first (АО ХК «Абсолют»
  2018, ООО «СМАРТ» 2022) before the entity itself began filing in 2023 —
  exactly the pattern 2b was written to catch.
- **Intra-group IP holding**: the «Капюшон» trademark is registered to the
  Kilovatt sister entity, not the one whose site markets the product.
- **A live, unauthenticated JSON search API exists at
  `searchplatform.rospatent.gov.ru`** — reverse-engineered from two
  user-supplied HAR captures, no session/cookie/auth required. Two techniques:
  a `patent_holders:search` substring filter (what the UI itself uses first)
  and an exact-field `IN_RU="<full ФИО>"` inventor query. Materially better
  coverage than the bulk CSV dump (which carries no wordmark text). Full-roster
  sweep found candidate hits on 51/93 manufacturer-tier entities; ~14 look like
  genuine new UAV/counter-drone patents pending promotion — see Phase 2b above.
- **A second GUR catalogue was missed and is now covered**: the `/components`
  foreign-parts teardown database (distinct from the sanctions/uav-companies
  sections `screen_gur.py` already covered) titles entries by weapon-platform
  name, not manufacturer — a brand/company search finds nothing even when the
  entity's own product is listed directly. Found one real hit this way:
  `npts-ushkuynik`'s flagship "Князь Вандал Новгородский" UAV, with 12 named
  foreign components across four countries.
- **People-side OpenSanctions triage closed the loop Phase 2's entity sweep
  opened.** All 27 people with unreviewed `opensanctions_matches[]` were
  triaged by the same identifier-over-score rule as the entity sweep: 6
  promoted (personal ИНН extracted directly from the match's own `ru-inn-`
  identifier), 2 flagged as open questions rather than promoted because two
  distinct same-name candidates exist and only one carries a sanctions-linked
  topic — promoting either without an independent ИНН to disambiguate would
  risk misattributing a sanction to the wrong namesake.
- **A new source type for OSINT-leak-aggregator dossiers** (Химера-style
  compilations of breached Russian consumer/courier/banking/Rosreestr/tax
  data — a genuinely different evidence class from a government registry).
  User-supplied a Химера dossier on Барашков А.С. (GD, «Гагаринг»); it matched
  the registry's existing record on an exact personal ИНН across ~40
  constituent leaked records, confirming DOB and adding birthplace and current
  address (with the address *history* — Приморье → Краснодар — independently
  corroborating a move already inferred from his ОГРНИП's tax-jurisdiction
  record). New source type `osint_leak_aggregator`
  (`scripts/extract_registry.py`, `SOURCE_TYPE_PATTERNS`). Deliberately did
  NOT import the dossier's passport numbers, SNILS or vehicle/insurance
  detail — out of scope for what a sanctions-screening profile needs.
  Archived as `s1171`. Committed as `2918d2e`.
- **Imagery pipeline validated end-to-end on a small first batch** (see Phase
  3 below) — confirms both harvested-data sources actually yield usable,
  downloadable images (leader-id.ru user-profile `photo` field; rk.2035.university
  showcase `cover` field, base URL `https://s3.objstor.cloud4u.com/`), not just
  metadata. The gating discipline that matters going forward: only attach a
  photo/logo to a person or entity that already has an independently confirmed
  identity match to that source — never on a name match alone.

---

## Phase 0 — Foundations

**Status (2026-08-24): DONE.** ✅ `STYLE_GUIDE.md` exists (repo root, not
`docs/` — intentional, see its own `CLAUDE.md` note: it's an internal drafting
tool, not part of the published site). ✅ `docs/images/*` staged (`git add`). ✅
`MANIFEST.md` regenerated (now 951 files). ✅
`docs/_archive/index-2026-08-21.html` snapshot exists. ✅ `CLAUDE.md`'s PII
section rewritten to the full-identifying-detail policy. ✅ **Mermaid diagram
resolved** — rendered locally via `@mermaid-js/mermaid-cli` and inlined as a
static `<svg>`; zero `<pre class="mermaid">` remain, and reference copies live
at `docs/assets/ownership-graph.{svg,mmd}`. Inlining (rather than vendoring the
JS) was chosen because `docs/index.html` doubles as the self-contained Artifact
companion, which cannot reference external relative assets. ✅ **Theme toggle
wired** — inline script sets `data-theme`, persists to `localStorage`, verified
by real headless-Chrome click test with no console errors.

Nothing outstanding in this phase.

**0.1 Port the style guide into this repo** (the user's priority 1: "keep it on
file"). New `docs/STYLE_GUIDE.md`, combining two things that are currently
separate memories belonging to a different project:

- **Prose voice**, adapted from
  `~/.claude/projects/-Users-ak-Downloads-mariupol-property-seizures/memory/authorial_voice_style_guide.md`
  — including the mode-selection table, mapped onto this project's sections:

  | Section | Mode |
  |---|---|
  | `index` narrative recap | Investigative (headline = the finding; deadpan accumulation; officials get rope, not adjectives) |
  | Company profiles | Expert-witness/forensic ("officially X, in fact Y" as the organizing unit; hedging calibrated to evidence) |
  | Methodology / provenance | Expert-witness/forensic, flattest register |
  | "Why this matters" / afterword | FP-analysis (contrarian inversion, historical anchoring, aphoristic kicker) |
  | Closing call to action, if any | Campaigning — sparingly, one barbed aside at most |
  | Academic mode | **Never** — control case for what not to do |

- **Presentation rules**, adapted from
  `mariupol-property-seizures/docs/exhibits/STYLE_GUIDE.md`: transliteration
  (Latin primary, Cyrillic beside it — the `.person-fio` pattern, not a hidden
  tooltip, for profile cards); the legal-form gloss table (ООО→LLC on first
  mention, transliterated proper name inside «», never left bare Cyrillic in EN);
  no internal notation (no DB column names, no `t-doc` in prose); sourcing kept
  out of narrative and collected in one provenance page; bold-on-first-mention
  for entities and people; verbatim-quote fidelity with `[так в оригинале]`.
- **New rules this project needs**, several of them codifying good habits the
  current brief already has by instinct:
  - **"English is the language of analysis, Russian is the language of
    evidence."** The existing document follows this almost mechanically —
    headings, argument and glosses in English; entity names, ФИО, product names,
    addresses, registry terminology and all 19 blockquotes in untranslated
    Russian, each `<cite>` marked *verbatim*. Codify it, and state its RU
    counterpart: in the RU pages the split collapses, the parenthetical English
    glosses disappear, and the blockquotes simply sit in the prose.
  - **The "own" marker.** The brief uses "its **own** filing", "ЦБСТ's **own**
    channel", "Градислава's **own** accounts" dozens of times to separate
    self-incriminating primary sources from third-party claims. That is
    self-incrimination-as-method working correctly; make it an explicit rule so
    it survives the rewrite instead of being smoothed away.
  - ИНН/ОГРН display format; the euphemism-autopsy list for this subject matter
    («резидент», «гуманитарная миссия», «народный ОПК», «безвозмездная
    передача»); the photograph bound above; and the rule that RU pages are
    *written*, never machine-translated from EN.

**0.2 Repo hygiene and live-site bugs, before anything is generated**

- `docs/images/*.jpg` are **all 24 untracked** — a Pages deploy from HEAD renders
  with broken images today. `git add` them.
- `data/sources/MANIFEST.md` is stale: header says 212 files, directory holds
  **305**. Re-run `python3 scripts/scan_sources.py --out data/sources/MANIFEST.md
  --leads-out /tmp/leads.md`.
- Snapshot the current brief as `docs/_archive/index-2026-08-21.html` so nothing
  is lost during extraction, and so any claim can be traced back.
- **Rewrite `CLAUDE.md`'s PII section** to the new full-identifying-detail policy
  (see Stated assumptions). The current text explicitly instructs future sessions
  to treat the old name+role default as binding and to ask before extending it —
  left unchanged, it will cause this work to be reverted or challenged in a later
  session.
- **The Mermaid diagram must not be carried forward as-is.** In the new site,
  render the ownership graph either as a committed static SVG (preferred — no
  runtime dependency, works everywhere, and the CSP on an Artifact republish
  blocks external scripts anyway) or with Mermaid vendored locally. Do not ship
  another `<pre class="mermaid">` with nothing to render it.
- Either wire up the `[data-theme]` toggle with a small inline script or drop the
  dead selectors. Don't leave both.

---

## Phase 1 — The registry (single source of truth)

**Status (2026-08-24): ENTITY side complete; PEOPLE side is not.**

- **Entities: 147/148 `_verified`.** All tiers cleared — `manufacturer` (93),
  `money-layer` (28), `plumbing` (14), `cbst-core` (9), `adjacent` (4). The one
  holdout, `krams-brand-unresolved`, is genuinely unresolved (no legal entity
  found for the brand) and correctly left open rather than forced closed.
  `check_registry.py`: **0 errors**, 1 standing warning (27 history entries
  awaiting a `source_id`).
- **People: 5/153 `_verified`.** This is the gate this phase exists for, and it
  has not been met for people. Split out as **Phase 1b** below.
- The source-ID stability bug (positional IDs silently reassigning) was found
  and fixed — `_source_ids.json` makes IDs append-only; verified stable.
- ✅ **`mine_leads.py` / `scan_sources.py` repointing is DONE** (the "must not
  be missed" item below). Both now call `id_patterns.load_known_text()`, which
  reads `data/registry/*.json` first and additionally forward-declares
  `docs/dossier*.html` and `docs/companies/*.html` for when Phase 4 creates
  them. `docs/index.html` is still concatenated on top as a deliberate,
  documented transitional measure. Only cosmetic staleness remains — two
  docstrings/report headers still say "not yet in docs/index.html".

This is the user's priority 4 gate: *"prepare a comprehensive list of all
entities of interest before doing it."* Nothing in Phase 2 or 4 starts until this
is complete and verified. **Entity side has now cleared that gate; the people
side has not** — see Phase 1b.

`data/registry/`, JSON, hand-verifiable, git-tracked. **Schema as designed
below; see Phase 3.5 for the fields that have since accreted and the type
instabilities that must be normalized before a generator can consume this.**

- **`entities.json`** — one record per legal entity:
  `slug`, `name_ru`, `name_latin`, `legal_form`, `brand_ru`/`brand_latin` (where
  brand ≠ legal name — the user's explicit requirement), `inn`, `ogrn`, `kpp`,
  `registered`, `address`, `okved_code`/`okved_label`, `okved_mismatch` (from
  `notes/okved_mismatches.md`), `director`, `founders[]`, `parents[]`/`subsidiaries[]`,
  `tier` (cbst-core | manufacturer | money-layer | plumbing | adjacent),
  `cbst_tie` {claim, evidence, source_id, confidence},
  `wb_overlap` — **revised 2026-08-24 to a raw/curated split** (see Phase 3.5):
  a machine sweep writes `wb_matches[]` (raw evidence: matched seller ИНН,
  supplier_id, brand, item counts, `military_class` tallies, query date), and a
  human sets `wb_overlap` (the conclusion: `confirmed_direct` |
  `confirmed_reseller` | `none_found` | `not_checked`). This mirrors the
  `opensanctions_matches[]` → `sanctions[]` pattern exactly, and exists because
  a bulk sweep writing conclusions directly **destroyed a hand-verified
  `confirmed`** — see "Two things to fix" above. Screening must never be able to
  overwrite a judgment. Join key back to the `wb_watch` dataset, see Phase 5.
  `products[]`,
  `financials[]` {year, revenue, profit, employees, source_id},
  `egrul_flags[]` (ОгрДосСв / ПризнНедДанУчр — via existing
  `scripts/check_egrul_flags.py`), `sanctions[]`, `litigation[]`, `licences[]`,
  `trademarks[]`, `patents[]`, `foreign_components[]`, `images[]`,
  `open_questions[]`, `sources[]`, plus a **`web`** block:
  `{sites[] (url, whois, hosting, first_seen), telegram[] (handle, subscribers,
  post_count), vk[], youtube[], marketplace_listings[], other[]}`. Company web
  and social presence is a first-class field, not a footnote — `scripts/vk_fetch.py`
  already exists and has never been used for this, and 22 Telegram channels are
  already scraped into `data/roymarket.db` with per-channel post counts.
- **`people.json`** — `slug`, `fio_ru`, `name_latin`, `dob`, `birthplace`,
  `address`, `inn_personal`, `roles[]` {entity_slug, title, from, to,
  source_id}, `sanctions[]`, `social[]`, `photo`, `notes`, `sources[]`. Every
  identifying field carries its own `source_id`.
- **`products.json`** — `name_ru`/`name_latin`, `maker_slug` (nullable — the
  still-open bare product names «Паук», «Рарог», «Призрак», «Катран», «Орбита»,
  «Перехват», «Шторм К-14 Альфа», «Геракл», «Довод», «Аватар», «Грань», «Ключ»
  stay in the registry as unresolved records rather than a prose catch-all that
  rots), `description`, `recipient_units[]`, `evidence[]`.
- **`sources.json`** — every primary document: `id`, `type` (egrul | bfo | ustav |
  court | telegram | press | transcript), `path` under `data/sources/`, `url`,
  `date`, `entities[]`, `sha256`.
- **`quotes.json`** — the 19 verbatim Russian blockquotes and any added later:
  `text_ru` (character-exact), `speaker`, `source_id`, `date`, `translation_en`.
  Quote fidelity is a standing project rule; putting quotes in structured data
  means the RU and EN pages render the *same* string rather than two hand-copied
  ones that can drift.

**Two fields that must be carried over, not re-derived:**

- **Confidence.** The brief already tags 128 claims `t-doc` (110, primary
  document), `t-press` (6) or `t-open` (13, unresolved). That vocabulary is
  sound and readers of a sanctions submission need it — map it onto a
  `confidence` field on every sourced claim rather than losing it in the rewrite.
  **Status 2026-08-24: mostly lost in extraction.** Only **26 of 148** entities
  carry a `confidence` value (24 `doc`, 1 `press`, 1 `open`) against 128 tagged
  claims in the brief. Either re-extract the tags from
  `docs/_archive/index-2026-08-21.html` or accept the loss explicitly — but do
  not let Phase 4 render a confidence vocabulary that is 80% absent.
- **The open-item lists.** Four separate mechanisms currently track unresolved
  work and each rots independently — the 26-item "What is not established" list,
  the 17-card "still unmined" grid, two `colspan="3"` catch-all rows buried
  *inside* the manufacturers table (lines 1026 and 1052, the second holding
  eight Дронница exhibitors never EGRUL-checked: КБ «Горизонт», КБ «Аякс
  Технологии», ГК «Мобил-груп», «ДронНЕТ», «Локтар», УЦ «Искра», КБ «Око»,
  «VECTOR»), and 13 inline `t-open` chips. `roymarket_tracking_discipline`
  records a catch-all like this rotting before and being re-reported as current.
  Collapse all four into `open_questions[]` on the entity or product they belong
  to, plus a small number of genuinely global ones, and let the build render the
  lists — so resolving something in the registry strikes it from every page at
  once, which is exactly the failure mode that rule was written for.
  **Status 2026-08-24: partially done, and it has grown a third shape.** The
  real inventory is now **128 questions across three differently-shaped stores**:
  44 in `open_questions.json` (27 `global` + 17 `unmined-source`), 83 attached to
  64 entity records, and 1 on a person record. Critically, `entity_slug` in the
  global file is **null on all 44** — the intended per-entity linkage was never
  made; the per-record arrays are what actually carries it. Phase 4 must read all
  three, and Phase 3.5 should normalize them to one shape.

**How it gets populated** — a new `scripts/extract_registry.py` scaffolds records
by parsing the archived `index.html` and `data/sources/MANIFEST.md` (reusing
`scripts/id_patterns.py`, which already has the ИНН/ОГРН/entity/person regex and
`is_noise_quote`), then **every record is verified by hand** against the brief
and the primary documents. Nothing is invented; a field with no source is left
null, not guessed.

**Extraction hazard.** The malformed manufacturers table (Context, above) means
the single densest block of entity data — 45 rows plus a 51,007-character
unclosed paragraph — cannot be trusted to a DOM parser or a naive regex. Treat
lines 974–1090 as a manual transcription job, verified row by row against the
primary documents, not as an automated extraction. Budget for that; it is the
slowest part of Phase 1.

**~~Must not be missed~~ — DONE (2026-08-24).** `mine_leads.py` and
`scan_sources.py` no longer hardcode `BRIEF`; both call
`id_patterns.load_known_text()` (`scripts/id_patterns.py:107-146`), which reads
`data/registry/*.json` and forward-declares the Phase 4 output paths. Remaining
tidy-up is cosmetic only: `scripts/mine_leads.py:27` and
`scripts/scan_sources.py:304` still *say* "docs/index.html" in a docstring and a
report header.

**Verification:** `scripts/check_registry.py` — schema validation, ИНН checksum
validation (the Russian ИНН control-digit algorithm catches transcription
errors), duplicate detection by normalized name and by ИНН (reusing the
fuzzy-dedup approach from `roymarket_fuzzy_dedup`), and orphan detection (every
`source_id` resolves; every `maker_slug` exists). Currently passing with 0
errors. Phase 3.5 adds the guards it still lacks.

---

## Phase 1b — Verify the people layer (NEW, gates Phase 4)

**Chosen 2026-08-24 at user direction: verify people first, rather than shipping
hedged or partial person data.**

The entity pass is done; people were never given the equivalent treatment, and
the numbers are stark:

| Measure | People | (Entities, for contrast) |
|---|---|---|
| `_verified: true` | **5 / 153** | 147 / 148 |
| Role links flagged `_candidate: true` | **120 / 153** | — |
| Has `dob` | 23 / 153 | — |
| Has `inn_personal` | 17 / 153 | — |
| Has a photo | 1 / 153 | — |

Phase 4's company-profile block 3 renders "People — full ФИО + Latin + role +
photo" per company. Against this data that block would present overwhelmingly
unverified identities and unconfirmed role links as established fact — in a
document built for sanctions submission, and under a PII policy that publishes
DOB and personal ИНН. That is the highest-consequence failure mode in the whole
plan, so it gets its own gate.

**Work:**

1. **Resolve the `_candidate` role links** (120). Each asserts a person→entity
   relationship extracted from prose, never checked. For each: confirm against an
   EGRUL extract, a founding document or the entity's own filing, then drop
   `_candidate` and attach a `source_id` — or delete the link. Many will resolve
   in bulk from the `EGRULAPI_*.json` snapshots already on disk (134 of them),
   since director/founder names come straight from those.
2. **Apply the significance bound** (existing plan rule): full identifying
   detail for ЦБСТ leadership, manufacturer directors/founders and the ДАР money
   layer; "Surname I.O., role only" stays the honest fallback for the long tail
   of registrars, auditors and nominees. Do not chase DOBs for people who do not
   need one.
3. **Every identifying field carries its own `source_id`** — the standing PII
   rule. A DOB or address without one stays null. `check_registry.py` should fail
   the build on a populated `dob`/`address`/`inn_personal` with no source.
4. **Reconcile the sanctions notes already gathered.** The OpenSanctions sweep
   surfaced personal ИНН and passport numbers in designation text for several
   people (e.g. Чернышов, Корчагина) that have not been folded into
   `inn_personal` yet.
5. **Fix the duplicate-person tombstone** (see Phase 3.5) — `_merged_into` is
   documentary only; nothing reads it.

**Watch for:** the person records were scaffolded from prose in two different
name orders, which already produced one confirmed duplicate
(`brovchenko-aleksandr-rufinovich` vs `aleksandr-rufinovich-brovchenko`). Run a
normalized-name dedup pass (`roymarket_fuzzy_dedup` approach, ФИО word-set
comparison rather than substring) across all 153 before verifying, so the same
person isn't verified twice under two slugs.

---

## Phase 1.5 — Source triage (5 untyped files) + physical-footprint typology

**Status (2026-08-24): 1.5a largely filed; 1.5b effectively UNSTARTED; 1.5c
unstarted.**

- **1.5a** — the five untyped files are typed and in `sources.json`. Not
  re-verified that the OCR pass on `Благодарность.pdf` actually happened.
- **1.5b — `facility_type` is populated on 3 of 148 entities** (2
  `purpose_built_technopark_sez`, 1 `soviet_legacy_defense_industrial`, 145
  null). Phase 4 §8 renders this block; against 2% coverage it would be absent
  from essentially every profile. Either do the pass or drop the block.
- **1.5c — `sanctions_legal_basis` is not in use.** No source carries that type.
  This now matters much more than when it was written: **58 entities and 28
  people carry `sanctions[]` entries**, and the great majority are sourced to an
  *aggregator* (OpenSanctions/Aleph API response JSON) rather than the
  underlying legal instrument — exactly the gap 1.5c exists to close. Every
  `sanctions[]` note added in the 2026-08-24 sweep says so explicitly ("not yet
  independently read against the underlying primary designation document").
  For a sanctions-lobbying deliverable this is the difference between `t-doc`
  and `t-press`, so it should be scheduled, not left as reference-library
  housekeeping.

**Broader source-catalogue health** (new numbers, 951 sources):
`type` null on **392** (overwhelmingly the machine-harvested `ALEPH_*` /
`OPENSANCTIONS_*` JSON dumps the typing logic never covered — a known shape, not
a random gap); `as_of` null on **426**; `url` empty on **all 951**; `entities`
empty on **all 951**; `_verified: false` on **all 951**.

Added 2026-08-22, after a full logging/hashing audit of `data/sources/`
(all 418 files now have a `sources.json` entry and a `sha256` — see
`scripts/inventory_sources.py`) surfaced 5 files content-classification
can't type, plus a user conceptual note that reframes how entity physical
locations get resolved. Small in scope; sequenced here because two of the
five files feed directly into Phase 2 screening and the typology affects
how Phase 1 records addresses.

### 1.5a — The five untyped files, resolved individually

| file | finding | action |
|---|---|---|
| `8twg968han.pdf` | Дронница-style delegation roster: АНО «НПЦ БАС «ТулаДрон»», leader Чадаев Ю.А., 38-person team — content matches the already-parked `npc_bas_technopark_network` memory's "Case study 2: НПЦ БАС «ТулаДрон»" (found 2026-08-17 via a different user-supplied deck) | Extract full text, diff against the existing case-study notes for anything new, record this file's path+sha256 as a corroborating source in the memory. **Not folded into the brief** — this program stays parked/adjacent per existing policy — but the user flagged "multiple cooccurrences" as suspicious, so add a line noting this is now the *second* independent document surfacing the same program and keep watching for a third. |
| `Благодарность.pdf` | scanned image, no text layer (`pdftotext` returns empty) — user identifies it as from в/ч п/п **71474**, «Добровольческий корпус», commander ген-майор Барило Д.А. — already documented in the brief (`docs/index.html:454`) via two other letters (to Замятин А.Ю. 01.12.2024, to Сухоненкова Н.А. 05.04.2026), both tied to НПЦ БАСиРТК | OCR pass, same fallback pattern as `egrul_founding_doc_extraction` (cp866/OCR for scanned founding docs). Once legible: identify the recipient/date and check whether this is the **source PDF underlying one of the two already-cited letters** (in which case: link it as `source_id` on that existing quote/claim, upgrading it from Telegram-screenshot-sourced to primary-document-sourced) or a **third, previously undocumented instance** (in which case: new entity/quote records, same `«Благодарственное письмо»` genre treatment as the other two). |
| `OJ_L_202600504_EN_TXT.pdf` | EU Council Decision (CFSP) 2026/504, amending the 2014/145/CFSP sanctions regime — confirmed by direct read to carry full drone-industry designations: Kosolapov/Complex Unmanned Solutions Center, LLC "UAMOC", Alabuga SEZ (SuperCam, JSC Albatros, JSC AviatestAero), JSC IEMZ Kupol, LIBSS LLC, Li Xinyang — each with DOB/passport/tax ID/associated-entities detail | Add a new source `type: eu_sanctions_annex`. Cross-check every named individual/entity here against `people.json`/`entities.json` by name (fuzzy match, reuse `roymarket_fuzzy_dedup`'s normalize-then-compare approach) — a first pass found **zero overlap with the current 130-entity/147-person registry** (these are a different, Alabuga/Kupol-centered drone cluster, not ЦБСТ-network), so treat as `tier: adjacent` per the existing adjacent-network convention unless a real tie surfaces. **Also feed into Phase 2**: this document is richer, per-individual sanctions-designation detail than a raw OpenSanctions API match would return for these names — worth adding "EU Council Decision annexes" as a documented Phase 2 screening input alongside `war-sanctions.gur.gov.ua`, not just a one-off file. |
| `DATASET_REGISTRY_2026-08-15_....csv` | a Russian open-data-portal dataset catalogue — 7,050 rows / 509 publishing orgs, but only **6 rows carry any ИНН at all**, and **0 overlap** with the current registry's 114 ИНН | Keep the file (per user instruction — "more than useful dataset" for future reference) but confirmed low *current* relevance; log as `type: reference_dataset`, no further action now. Re-check for overlap after Phase 1 entity count grows past the initial 130, since the miss rate is a function of how few entities are resolved so far, not necessarily the dataset's uselessness. |
| `VIDEO_20260818_tekhnologii-pobedy-cbst-er-rKwmelP7gvE.mp3` | the ЦБСТ board podcast, per the user — confirmed via the video ID (`rKwmelP7gvE`, YouTube-format) as **"Технологии победы: Как разрабатывают военные беспилотники..."**. Checked: no transcript file exists yet anywhere in the repo (`data/sources/`, `notes/`). User confirms (2026-08-22) they already copy-pasted the transcript from YouTube themselves — it hasn't landed on disk yet. | Once the user supplies the pasted text: save as `TRANSCRIPT_20260818_tekhnologii-pobedy-cbst-er.txt` in `data/sources/` — same pattern as the existing `TRANSCRIPT_20250421_peregovorka-cbst-er-sidyakin-bezrukov.txt` (already on file, already logged/hashed/typed `transcript`, real precedent rather than a hypothetical) — then run it through the normal pipeline (`scan_sources.py` → `inventory_sources.py` → `extract_registry.py`) so it gets logged, hashed and typed the same way. No transcription tooling needed on my end — this is a save-and-ingest step, not a blocker. |

### 1.5b — Physical-footprint typology (registry schema addition)

The user's conceptual note: ЦБСТ is *designed* to be cloud-native/address-
obscured, but its own claimed "secure technoparks" (Kommersant-reported,
>100,000m², ₽25bn, five-year build timeline — already in the brief's
"Physical infrastructure" section) don't exist yet. Until they do, current
and likely-future ЦБСТ-network/РОЙ.МАРКЕТ-candidate entities are physically
sited somewhere real — and the `npc_bas_technopark_network` memory already
identified at least three distinct patterns while parked as "adjacent, not
core": Soviet-legacy defense-industrial buildings, purpose-built modern
technoparks/ОЭЗ (special economic zones — Tula's «Узловая», the already-
brief-documented Технопарк Муроммаш case), and generic mass-registration
commercial addresses that resolve to nothing physical at all.

This reframes that memory from background context into an active input for
Phase 1 entity resolution, and adds one field:

- **`entities[].facility_type`** (and per-entry on `address_history[]`,
  since a site can change type over time — an entity could start at a
  generic registered address and later move into a technopark residency):
  enum `soviet_legacy_defense_industrial | purpose_built_technopark_sez |
  generic_registered_address | claimed_future_secure_technopark | unknown`.
  Each entry keeps its own `source_id` and `note` (e.g. which technopark,
  which ОЭЗ, which residency announcement), same pattern as the other
  `_history` arrays already in the schema.
- **Workflow change in Phase 1's entity-resolution pass**: before leaving
  an entity's address as "registered address only, physical site unknown,"
  check it against the known НПЦ БАС/technopark shortlist in
  `npc_bas_technopark_network` (SPb, Tula «Узловая», Ryazan «Протос»,
  Yaroslavl, Moscow, plus Технопарк Муроммаш already in the brief) the same
  way the memory already recommends as a "standing first move" — this makes
  that recommendation something Phase 1 actually executes per entity,
  not just a note sitting in memory.
- Phase 3 (Imagery) and Phase 4 §8 (Physical footprint profile block)
  render `facility_type` explicitly — a profile stating "purpose-built
  technopark, ОЭЗ «Узловая»" vs. "generic registered address, no verified
  physical site" is a materially different, and more honest, claim than
  the current brief's flat "registered address vs. actual production site"
  framing, and it makes the cloud-by-design-vs-current-reality point the
  user raised into something the reader sees per entity, not just asserted
  once in the narrative.

### 1.5c — Sanctions-regime legal texts as first-class reference sources

The user's follow-up: keep the actual laws/official designation documents
on file, not just entity-level match results. This matters because the
brief already carries sanctions-adjacent claims that are currently sourced
only to an *aggregator*, not the underlying legal instrument:

- **Осадчук** (`docs/index.html` finding 18) — cited via OpenSanctions,
  which itself aggregates US OFAC/UK FCDO/NZ/Ukraine's
  war-sanctions.gur.gov.ua. The primary US Treasury designation document
  (and the GRU Unit 74455 DOJ indictment it's tied to) isn't on file.
- **Фонд «ДАР» / «Градислава»** re: Medvedev's undisclosed assets (finding
  08) — currently tagged `t-press` (FBK/press-reported), not `t-doc`. If a
  real Western designation document names either fund directly, that's a
  tier upgrade worth making; if none does, that's also worth recording
  explicitly rather than leaving the sourcing ambiguous.
- `OJ_L_202600504_EN_TXT.pdf` (Phase 1.5a) is itself an *amending* decision
  — it modifies Council Regulation (EU) No 269/2014, which isn't on file
  either. An amendment is only fully legible next to what it amends.

**What this adds to the registry/source schema:**

- A new source type **`sanctions_legal_basis`** — the framework
  regulations/executive orders/statutes that establish a sanctions regime
  (EU 269/2014, US E.O. 13661/13662/14024, UK's Russia (Sanctions) (EU
  Exit) Regulations 2019, etc.) — kept distinct from `eu_sanctions_annex`
  (Phase 1.5a's type for the periodic listing/designation decisions that
  amend those frameworks and name individuals).
- Naming convention for these going forward, extending the existing
  no-ИНН-to-key-on pattern already proven in the wild — e.g.
  `data/sources/TRANSCRIPT_20250421_peregovorka-cbst-er-sidyakin-bezrukov.txt`
  (already on file, already logged/hashed/typed `transcript`,
  `captured_date` = the broadcast's own date, not the pull date) — the same
  shape applies to legal texts: **`LAW_<regime>_<YYYYMMDD>_<slug>.<ext>`**,
  e.g. `LAW_EU269-2014_20260423_council-decision-2026-504.pdf`,
  `LAW_US-EO14024_<date>_treasury-osadchuk-designation.pdf`.
- Each entity/person's `sanctions[]` entry (Phase 2's OpenSanctions/Aleph
  screening output) gets a `source_id` pointing at the archived legal
  document, not just the aggregator API response — so a sanctions claim in
  the finished brief is never sourced only to a third-party match, the same
  discipline already applied everywhere else in this project (`t-doc` over
  `t-press` wherever a primary document exists).
- Scope: EU, US (OFAC), and UK (OFSI) regimes at minimum, since those are
  the three most likely to matter for the lobbying use case this project
  serves ([[roymarket_project_goal]]); expand only if a specific claim
  needs a fourth regime's text.

This is reference-library maintenance, not a new screening pipeline —
Phase 2's `screen_opensanctions.py`/`screen_aleph.py` still do the actual
matching. This just makes sure that whenever a match is confirmed, the
underlying legal text gets pulled and archived alongside it, the same way
an EGRUL pull is archived alongside a `director` fact rather than left as
an unarchived API response.

---

## Phase 2 — The screening pass

**Status (2026-08-24): substantially DONE — 3 of 5 sweeps complete full-roster,
4 documented blockers.**

| Sweep | State |
|---|---|
| `screen_opensanctions.py` | ✅ **Full roster, and now fully triaged on the people side too (2026-08-24).** 137 entities + 100 people screened. 90 entities / 54 people scored ≥0.7. Triaged by exact-identifier cross-check (not score): **56 entity matches ID-confirmed**, 11 explicit false positives documented, **33 people now carry `sanctions[]`** (was 27+4 ID-confirmed/15 role-corroborated; this session closed out the remaining 27 with matches but no promotion — 6 more promoted via exact `ru-inn-` identifier extraction, 2 held back as open questions on an unresolved same-name collision), rejections incl. a Дмитрий Песков collision with Putin's press secretary and a Михаил Кузнецов 5-candidate ambiguity. |
| `screen_aleph.py` | ✅ **Full roster.** 139 entities + 140 people. Mostly expected noise (Aleph indexes every Russian company's own EGRUL/procurement record); one genuine ИНН-confirmed sanctions hit — ООО НПО «Киловатт» (Шестопалов). |
| `rospatent_tm_search.py` | ✅ **Full roster**, archived as `s0945`. 11 new trademark records across 5 entities, plus the brand-lineage and shared-patent-attorney findings noted at the top of this plan. Caveat: the bulk CSV carries **bibliographic data only — no wordmark text field**, so brand names are not directly extractable from it. |
| `screen_fns.py` | ⛔ **Deprioritized.** `api-fns.ru` quota exhausted (HTTP 403, "Исчерпано количество запросов"). Largely redundant anyway — 134 `EGRULAPI_*.json` snapshots already on disk from the `egrul.nalog.ru` open API. |
| `screen_press.py` | ⛔ **Dropped by user decision.** `NEWSAGENTDATA_API_KEY` is for an unidentified vendor; guessing a base URL would have sent the key to an unknown host. User: "Skip it for now." |
| `fips_patent_lookup.py` | ⛔ **Geoblocked.** `www1.fips.ru` now returns a DDoS-Guard "restricted by country" 403. Infrastructure-level, not a code bug. `rospatent.gov.ru`'s bulk dump is unaffected. |

Note the pre-existing `screen_rom.py`, `screen_upr_uchr.py`,
`screen_disqualified.py`, `screen_subsidiary.py` also ran; but
`disqualification_hits` and `subsidiary_liability_hits` are **empty on all 153
people**, with only 6 `*_checked_at` timestamps — i.e. those two sweeps covered
4% of the roster. Either finish them or record the coverage honestly.

**Carry-forward hazard — FIXED 2026-08-24.** `extract_registry.py` fully
regenerates `entities.json`/`people.json` on every run, so each screening field
needs explicit carry-forward logic or a regeneration silently wipes screening
history. All three known silent-loss risks are closed:

- **No-ИНН entities could never carry anything forward** (the old match map was
  built by filtering `if e.get("inn")`). Fixed: matching is now primarily by
  **slug** — the stable, intentional identity this project already uses
  everywhere else (`corrections.json` is keyed by it) — with ИНН only as a
  fallback for entities.
- **A corrected ИНН silently dropped data** (old key stopped matching). Fixed by
  the same slug-first change — a fixed ИНН no longer breaks the match.
- **A corrupt prior file was swallowed by a bare `except Exception: prev = {}`**,
  discarding all screening data with no trace. Fixed: `_load_prev_registry_file()`
  now aborts loudly (`sys.exit`) on a parse failure instead of silently treating
  it as "nothing to carry forward."
- **New: loss detection.** Any prior record that had screening data but matches
  nothing in the freshly-scaffolded set now prints an explicit stderr warning
  naming it, instead of vanishing with zero trace.

Implementation: `carry_forward_screening_fields()` +
`_load_prev_registry_file()` (`scripts/extract_registry.py`, just above `main()`),
replacing the old inline ИНН/slug-keyed blocks. Both entity and people call
sites now go through the same helper with an explicit field-pair list
(`ENTITY_CARRY_FORWARD_FIELDS` / `PEOPLE_CARRY_FORWARD_FIELDS`) — **any new
screening field still must be added to one of these lists at the same time it
is introduced**, but the matching and failure-handling logic itself no longer
needs to be re-derived per field.

Verified: unit-tested all three fixes directly (no-ИНН entity now carries
forward via slug; a changed ИНН no longer breaks the match; a vanished record
prints a warning; a corrupt prior file aborts with a clear message) and ran a
full `extract_registry.py` regeneration — carry-forward counts identical
before/after, `check_registry.py` still 0 errors, no warnings printed (nothing
was actually lost in this run).

Runs over the finished registry. As built (note the **raw-field** column — the
key design rule, now enforced by hard experience: a sweep writes *evidence*, a
human writes *conclusions*):

| Script | Source | Writes back (raw) | Human promotes to |
|---|---|---|---|
| `scripts/screen_opensanctions.py` ✅ | OpenSanctions `/match/default` batch API | `opensanctions_matches[]`, `opensanctions_screened_at` | `sanctions[]` |
| `scripts/screen_aleph.py` ✅ | OCCRP Aleph entity search by ИНН, name fallback | `aleph_matches[]`, `aleph_screened_at` | `sanctions[]` / `litigation[]` |
| `scripts/screen_wb.py` **(new, see Phase 3.5)** | local `wb_watch.db` — `sellers.inn`, `sellers.trademark`, `items.brand`, item-title text | `wb_matches[]`, `wb_screened_at` | `wb_overlap` |
| `scripts/screen_fns.py` ⛔ | api-fns.ru — quota exhausted; `egrul.nalog.ru` open API used instead | — | — |
| `scripts/screen_press.py` ⛔ | dropped by user decision | — | — |
| (manual, no key needed) | EU Council Decision annexes under 2014/145/CFSP and similar Western designation documents (see Phase 1.5a — `OJ_L_202600504_EN_TXT.pdf` already on file, richer per-individual detail than a raw API match) | — | `sanctions[]` entries with DOB/passport/associated-entity detail where a name matches |

**Triage rule that proved its worth: verify by identifier, never by score.** A
match score of 1.0 does not mean correct identity. The only reliable check is
comparing the match record's own `innCode`/`ogrnCode`/`idNumber` against the
query's identifier. This caught 11 entity false positives and a Дмитрий Песков
name collision with Putin's press secretary that a score threshold would have
waved through. Apply the same rule to every future sweep.

### 2b. Intellectual property — a full sweep, not an afterthought

**Status (2026-08-24): trademarks DONE full-roster; patents DONE full-roster
via a second, better source, triaged, not yet promoted.** The thesis below was
borne out on first contact — every predicted signal type actually appeared:

- ✅ **A live, better patent-search API found and reverse-engineered
  (2026-08-24).** `searchplatform.rospatent.gov.ru` exposes a plain
  unauthenticated JSON `POST /search` endpoint (confirmed via two user-supplied
  HAR captures, reproduced with bare curl/urllib) — materially better coverage
  than the bulk CSV dump used below, because it supports a `patent_holders`
  substring filter (catches wordmarks the CSV's bibliographic-only fields
  can't) alongside an exact `IN_RU="<ФИО>"` inventor-field query. New script
  `scripts/rospatent_searchplatform_search.py` covers all 93 manufacturer-tier
  entities by both name and director, tagging every hit with which method
  found it. Full-roster `--force` sweep run 2026-08-24: **51/93 entities
  returned at least one candidate hit.** Fully triaged the same day —
  ~14 entities carry genuinely new, exact-name-matched, on-topic UAV/
  counter-drone patents (standouts: АО «НИИ «Вектор» — an interceptor-UAV +
  anti-UAV-jamming portfolio, 15+ patents, the largest new find of the whole
  IP sweep; НПЦ «ЭЛВИС» — UAV detection system + an anti-drone capture gun;
  АО «НИИ СТТ» — 9 UAV-specific patents incl. de-icing sensors and low-light
  aerial photography; ООО «Тримикс» — a UAV-detection device, on-brand for a
  company whose only other confirmed WB listing is counter-drone gear). Common
  false-positive collisions correctly rejected on sight (Гермес, Логос,
  Площадь, Росс, Прайм, Проммаш, Покров — all common Russian words/names
  hitting unrelated companies — plus a subtler ИНФОТЕКС collision: "Информационные
  системы и технологии" vs. the real crypto company "Информационные технологии
  и коммуникационные системы", same words reversed). **Promotion into
  `patents[]` + `corrections.json`, with each patent individually archived, is
  the next concrete step and has not started** — this is real work (~14
  entities, ~40 records) — see the open item below.

- ✅ **Inception dating confirmed.** UralDronZavod's brand was filed by two prior
  holders (АО ХК «Абсолют» 2018, ООО «СМАРТ» 2022) before the current entity
  began filing in 2023. Neither prior holder has been researched — open question.
- ✅ **EGRUL-redaction workaround confirmed.** АО «АУРИН» and ООО «НПО
  Рустехдрон» — both founder-access-restricted — share one patent attorney
  (ООО ЮФ «АЙ ПИ ПРО», Леонов А.В., same Moscow office). Worth checking whether
  that firm represents other network entities.
- ✅ **Intra-group holding structure surfaced.** «Капюшон» is registered to the
  Kilovatt sister entity, not the one marketing it.
- ⚠️ **Name discrepancy on an OFAC-designated entity** — ЦБС Тула's trademark
  names a fuller legal name than either OFAC or EGRUL use. Unresolved; flagged
  rather than folded into `name_ru`.
- ✅ **Patents access RESOLVED, full-roster sweep DONE, zero relevant hits.**
  What looked like geoblocking wasn't: `www1.fips.ru` returns a DDoS-Guard
  block over **HTTP** but **HTTPS works and returns real content**
  (`fips_patent_lookup.py` already used the right URL — confirmed unmodified
  against `RUPM 218475` and `RUPAT 220486`, both resolve cleanly). Single-number
  lookups are fine again. `patents[]` remains **1 of 148** because the bulk
  sweep, run and reviewed, found nothing to add — not because access is still
  blocked.
  <br>`scripts/rospatent_patent_search.py --sweep-registry` was run (user, per
  crawling-jobs policy) and returned 64 records across 15 entity/person name
  matches. **Every single one reviewed and rejected**: all 64 predate 2010
  (max reg. no. 2341453, vs. this network's own confirmed patents in the 2020s
  range) and cover unrelated subject matter (Soviet-era medicine, agriculture,
  radioactive-waste treatment, grinding/machining) — common-name collisions
  (Орион, Гермес, Леонов, Гусев, etc.) on a name-only dataset, exactly the
  false-positive risk this script's own docstring flagged in advance. Archived
  as `s0952`; rejection recorded on all 15 records so the same dead end isn't
  re-walked. Google Patents remains the fallback for any specific number a
  primary source names directly.
- ⚠️ **Dump limitation to remember**: the Rospatent bulk CSV is bibliographic
  only — no wordmark text — so brand names cannot be read out of it directly.

Original rationale, retained because it still governs the patent half:

- A trademark or patent filing **dates a project's real inception**, often years
  before the entity that now sells the product was registered.
- It **names the filing entity and its representative**, which routinely differs
  from the current owner of record — a way around EGRUL redaction. Two entities
  in the brief already have access-restricted founders (`АО «АУРИН»`,
  `ООО «Тримикс»`, `ООО «НПО Рустехдрон»`); IP filings are one of the few
  registries that don't honour those restrictions.
- Co-inventor names map informal engineering teams that no corporate filing
  shows. The brief already has one worked example — Дзема Вадим Вадимович as
  co-inventor on Рустехдрон's `RU218475U1` and `RU220486`.

Output lands in `trademarks[]` / `patents[]` with filing date, number,
applicant, representative and inventors.

### 2c. Foreign components — the load-bearing sanctions evidence

**Status (2026-08-24): DONE, full-roster, across TWO distinct GUR sections.**
`foreign_components[]` now has its first entry (`npts-ushkuynik`, 12 parts —
see below); still empty on the other 147 entities, so this remains the
evidence type most worth returning to as new documents surface, but the
screening pipeline itself is complete.

**Second GUR section found and swept this session, after being missed on the
first pass.** The user pointed out a URL (`war-sanctions.gur.gov.ua/ru/
components?f[title_uk]=witem-4751`) belonging to a *different* GUR catalogue
than the one `screen_gur.py` already covered: a 5,851-record teardown database
of individual foreign electronic parts, each tied to a named weapon platform —
titled by **weapon platform**, not by manufacturer/brand, so a company-name
search (which is how `screen_gur.py`'s existing sweep works) finds nothing even
when the entity's own product is directly listed. New script
`scripts/screen_gur_components.py` builds per-significant-word queries from
every registry product/brand name (GUR's search is literal substring, not
fuzzy — a whole-phrase transliterated query missed the known-good hit by one
letter before this was fixed) and was swept full-roster. One confirmed real
hit: `npts-ushkuynik`'s own flagship UAV, "Князь Вандал Новгородский", named
directly by GUR with **12 foreign components** (Sigmastar/Purui/Hangzhou
Zhongke — China; Unisonic/Realtek/Winbond/CapXon — Taiwan/China; Semtech — US;
an STM32F405RGT6 microcontroller — Switzerland/STMicroelectronics, with a
traceable production week). Archived and promoted into `foreign_components[]`
via `corrections.json`. All other candidates (16 on the first full sweep, 4
after adding a stopword filter for generic words that had produced false
positives) were reviewed and rejected as name collisions with unrelated GUR-
catalogued platforms. One adjacent finding — a "Delta (CBTS.611000)" weapon
item — was investigated for a possible ЦБСТ tie and **explicitly rejected**:
CBTS is not a plausible transliteration of ЦБСТ (Ц → "Ts", not "C"); logged as
a correction on the entity's `open_questions[]` rather than silently dropped,
per project discipline.

The original first-section sweep (below) remains the source of the
Рустехдрон/Алёшин findings and is unaffected by the above.

**Status 2026-08-24: UNBLOCKED.** Same lesson as FIPS: `war-sanctions.gur.gov.ua`
returns 403 to a bare request with no `User-Agent` header, but works fine over
plain HTTPS with a real browser UA — no special client, no proxy, nothing
exotic. Confirmed inline against two records:

- **ALYOSHIN Boris Sergeevich** (`/en/sanctions/persons/5316`) — GUR's own page
  gives a DOB (03.03.1955) that OpenSanctions' aggregation of this same person
  didn't carry, and states his role as UAC board member. Notably, GUR's own
  "Date of entry and reference to the document" field reads **"The country has
  not yet applied sanctions"** for all nine jurisdictions it lists as
  monitoring him — GUR tracks candidates for sanction, it does not itself
  confirm a designation has been made. Don't read GUR's jurisdiction list the
  way an OFAC/EU listing is read.
- **НПО Рустехдрон** (`/en/uav/companies/14300`) — ИНН/ОГРН match this
  registry's own values exactly. Surfaced 3 previously-unrecorded product names
  (RTD-K10, RTD-K8, RTD-4M, all explicitly labelled "FPV kamikaze" by GUR
  itself) and a "related company" listing for Concern Kalashnikov JSC — **not**
  independently verified as a real corporate tie (GUR's own site doesn't
  explain that widget's basis), recorded as an open question, not a fact.

**`scripts/screen_gur.py` built and tested** (same crawling-jobs-policy
template as `screen_opensanctions.py`/`screen_aleph.py`): searches
`/en/search?q=<name>`, fetches each profile-card hit, and cross-checks the
profile's own stated ИНН/ОГРН against the query entity's — verified end-to-end
on a live entity, correctly ID-confirming Рустехдрон while correctly rejecting
a same-industry, different-company false lead (NPO Aviabas, mismatched
identifiers) that the same search surfaced. Writes `gur_matches[]` +
`gur_screened_at`, both added to `extract_registry.py`'s carry-forward list
immediately (per the Phase 2 lesson — a new screening field left off that list
is silently wiped on the next regeneration).

**Full-roster sweep — hand this to the user, per crawling-jobs policy:**
```
python3 scripts/screen_gur.py
python3 scripts/scan_sources.py --out data/sources/MANIFEST.md
python3 scripts/inventory_sources.py
python3 scripts/extract_registry.py
python3 scripts/check_registry.py
```
Site search is free-text, not identity-scored — expect the same false-positive
discipline as OpenSanctions/Aleph (ID-cross-check every hit, never trust a name
match alone; the Aviabas case above is exactly that trap).

**Fallback sources, if GUR coverage turns out thin for a given manufacturer**
(most won't be individually profiled — GUR's UAV-companies section is
selective, not exhaustive), in order of expected yield per unit effort:
- **The manufacturers' own material**, already on disk. Spec sheets,
  `@`-channel build posts and marketplace listings routinely name controllers,
  flight stacks, optics, radio modules and thermal cores outright. This project
  already has ~98,700 scraped Telegram posts in `data/roymarket.db` and a
  working extraction pipeline — local text-mining, not a network job, and
  exactly the "own" self-incrimination pattern `STYLE_GUIDE.md` marks.
- Teardown reporting: Conflict Armament Research, RUSI, Trap Aggressor,
  StateWatch/NAKO.
- Ukrainian and allied component-traceability publications.

Recorded as `foreign_components[]` on the entity — `{part, manufacturer,
country, found_in_product, source_id, confidence}` — and rendered as a dedicated
profile block, since this is what a sanctions desk reads first.

**Crawling policy.** All of the above are live network jobs at scale. Per
`CLAUDE.md` I write and test each script on 2–3 records inline (ordinary
reconnaissance), then **hand you the exact commands** for the full sweep rather
than running them. Every result lands in the registry with a query date, so
re-screening later is a diff rather than a redo.

---

## Phase 3 — Imagery

**Status (2026-08-24, later in this session): STARTED — a first small batch of
real assets collected from already-harvested data, not a fresh scrape.**
`scripts/tg_media.py` still doesn't exist. The 24 files pre-dating this plan in
`docs/images/` were user-supplied ground/satellite/portrait shots (staged in git
per Phase 0), not output of this phase's tooling — but 6 new files this session
*are* real Phase-3 output, pulled programmatically from two sources already on
file:

- **POI headshots from leader-id.ru** (`docs/images/<slug>_portrait_leaderid.jpg`,
  `people[].photo`). Checked all 7 people whose leader-id `user_id` had already
  been ID-confirmed by the earlier `screen_leader_id.py` sweep — 3 of 7 actually
  had a photo set on their profile (`GET /api/v4/users/<id>`, field `photo` /
  `photo_520` / `photo_180`, no extra auth beyond the existing session token):
  Барахтин Артём Владимирович (GD, «Аркодим»), Соловьев Константин Юрьевич (GD,
  «Аркодим-Про»), Лысенко Андрей Олегович (project lead, «Визионеро»). The other
  4 confirmed accounts have `photo: null` — nothing to pull. **Gating rule
  applied and worth keeping**: only fetch/attach a photo for a person whose
  leader-id account is already independently confirmed (matched employer/role
  against something already documented) — never for a raw candidate match, since
  leader-id search is name-only with no identifier to cross-check.
- **Company logos from rk.2035.university** (`docs/images/<name>_logo_rk2035.{jpg,png}`,
  `entities[].images[]`). Of the 5 entities already corroborated against the
  70-company БАС-showcase dataset (`s1168` — `ooo-npo-rustekhdron`,
  `npp-radar-mms`, `ooo-kleverkopter`, `ao-aeromaks`, `ao-ekolibri`), 3 had a
  `cover` image set (base URL `https://s3.objstor.cloud4u.com/`, no auth
  needed — public object storage): НПП «Радар ммс», «Клеверкоптер», АО
  «Эколибри». `ooo-npo-rustekhdron` and `ao-aeromaks` have `cover: null`.
  Product-model `avatar` fields (the 274-model dataset, `s1169`) were checked
  too and are **null on every single record** — no product images available
  from this source at all, despite the field existing in the schema.
- **Not yet done**: VK avatar pulls via the existing `scripts/vk_fetch.py` for
  entities with a `web.vk[]` handle on file — the script exists and has never
  been pointed at imagery specifically. A lead not run down: the Химера
  dossier on Барашков А.С. (see findings above) named a *third*, unconfirmed
  leader-id account with a photo file (`145752.jpg`) but no `user_id` to
  cross-check — logged as an open lead, not fetched.
- **`scripts/tg_media.py`** (new, not built) — Telethon `download_media` over a
  given channel and message-id range, or over posts whose text matches
  product/field-test/handover keywords. Writes
  `docs/images/tg/<channel>_<msgid>.<ext>` plus a sidecar JSON recording channel,
  `msg_id`, date, full post text and the `t.me` permalink, so every image carries
  its own chain of custody. **Live network job → hand the user the command.**
  Note the `«Благодарственное письмо»/«Почетная грамота»` genre marker
  (`military_thankyou_letter_genre`) as a high-yield keyword for handover
  evidence — it identifies receiving units by name.
- **Curation pass**: for each manufacturer, select product / field-test /
  frontline-handover images; write captions to `entities[].images[]`.
- **User supplies** satellite and ground views of offices and production sites,
  and press portraits — the pattern already used for the existing 24 files.
- Person photographs per the Phase 0 bound — the 3 pulled this session are
  professional leader-id.ru profile photos, consistent with that bound (not
  private/family imagery).

---

## Phase 3.5 — Registry hardening (NEW, blocks Phase 4)

The registry was designed once and has since accreted fields from five screening
scripts and dozens of correction batches. A Jinja template consuming it today
would break, render duplicates, or silently omit blocks. This is the cleanup
that makes the data generator-safe. All of it is local, verifiable work.

**1. Fix the `wb_overlap` regression and split raw from curated** *(user
decision: raw + curated)*

- Restore `ooo-trimiks-bulat-3mx` to `confirmed` — with the reseller evidence
  attached, not despite it.
- Move the machine sweep into `scripts/screen_wb.py` writing `wb_matches[]` +
  `wb_screened_at`; `wb_overlap` becomes a **human-set conclusion only**.
- Values: `confirmed_direct` (own ИНН is a WB seller — ООО «ГАСКАР», ООО «АСЕЛ
  ЛАБС»), `confirmed_reseller` (brand on WB via reseller accounts, maker's ИНН
  absent — Тримикс/«Булат»), `none_found`, `not_checked`.
- Add the field to the carry-forward block (`extract_registry.py:1279-1330`) in
  the same change, or the next regeneration wipes it.

**2. Guard against machine-overwrites-human generally.** `check_registry.py`
gains a check that fails, not warns, when a curated conclusion field
(`wb_overlap`, `sanctions[]`, `cbst_tie`, `tier`) is downgraded from a
human-verified value by a bulk write without an explicit override. This class of
bug has now happened once and is silent by construction.

**3. Normalize type instabilities** — each of these will break a template:

| Field | Problem |
|---|---|
| `charter_capital` | 29 int, 1 float, **1 string** |
| `okved_mismatch` | 7 booleans and 15 long free-text explanations under one key |
| entity `open_questions[]` | 79 dicts `{question, source_id}` + **4 bare strings**; 3 also carry `status` |
| people `_corrected` | list on 39, **bare string on 2**, null on 4 (always a list on entities) |
| `_verified_against` vs `verified_against` | accidental key split — 147 records vs 5 |
| `sanctions[].regime` | free text, ~20 distinct spellings incl. `(program code not returned)`. Needs a `regime` enum + a `regime_raw` passthrough if the site is to group by jurisdiction |

Encode each as a `check_registry.py` assertion afterwards so it cannot regress.

**4. Make `_merged_into` real.** 3 entities (`kb-germes`, `ooo-sibnk`,
`ooo-kb-sinergiya`) and 1 person (`brovchenko-aleksandr-rufinovich`) are
tombstones. **Nothing in the codebase reads the key** — it is purely
documentary, so a generator will emit them as real, duplicate entities.
`check_registry.py` must validate the target slug exists; `build_site.py` must
filter them; counts reported to readers should say 145 live entities / 152 live
people, not 148 / 153.

**5. Build the reverse source index.** `entities[].sources[]` is **empty on all
148** — provenance actually runs the other way, via `sources.json.inns`. Phase
4's per-entity §14 "Sources" block and `check_citations.py` both assume forward
linkage. Build the reverse map at build time from `sources.json.inns` rather
than duplicating data. Also: `sources[].url` is empty on all 951, so nothing
links out to an original document yet.

**6. Unify the three open-question stores** into one shape (see Phase 1
status) so the build renders a single list per entity plus a global set.

**7. Generalize `check_tag_balance.py`.** It hardcodes
`docs/index.html` (`scripts/check_tag_balance.py:12`) and hard-exits unless the
file contains literal `<div class="wrap">` and `</body>` markers. Phase 4 needs
it to accept paths/globs and to not assume that wrapper.

**8. Commit everything.** `data/` is untracked; the entire registry exists only
in the working tree. Do this first, not last.

---

## Phase 4 — The generator and the site

**Status: not started.** No `scripts/build_site.py`, no `docs/_templates/`, no
`docs/_prose/`. `docs/index.html` is still the single hand-edited file from
before this plan. `requirements.txt` has 3 entries (telethon, python-dotenv,
openpyxl) — **jinja2 is not among them and appears nowhere in the repo**.
`docs/assets/ownership-graph.svg` now exists (Phase 0).

**Render only what the data supports.** Every profile block is conditional, and
the current coverage says several would be near-empty: `facility_type` 3/148
(§8), `patents` 1/148 (§11), `foreign_components` 0/148 (§10), `images` 0/148,
`litigation` 0/148, `financials` 52/148 (§5), `cbst_tie` 15/148. Decide per
block whether to render-if-present, show an explicit "not established" state, or
drop it — an empty block that looks like an answer is worse than an absent one.

Add `jinja2` to `requirements.txt`. New `scripts/build_site.py` renders
`data/registry/*.json` + prose partials into `docs/`.

```
docs/
  index.html / index-ru.html          narrative recap, general audience
  dossier.html / dossier-ru.html      full data layer: entity map, tables, network
  companies/<slug>.html / -ru.html    ~40 profile pages
  people.html / people-ru.html        person index, per-person anchors
  methodology.html / -ru.html         how this was built, what is not established
  sources.html / -ru.html             provenance catalogue (replaces the 15k-char footnote)
  assets/site.css                     extracted from the current inline <style>
  assets/ownership-graph.svg          static render of the dead Mermaid diagram
  images/                             existing 24 + tg/ + supplied
  _templates/*.html.j2
  _prose/<section>.{en,ru}.md         hand-written narrative, not generated
  _archive/index-2026-08-21.html
```

**Design language:** adapt the palette and components the user already owns in
`mariupol-property-seizures/docs/index.html` — dark forensic ground, mono
eyebrows, stat band, card grid, `--evidence`/`--stamp`/`--testimony` accents.
Reusing it means the two investigations read as one body of work. Keep the
current file's `prefers-color-scheme` + `[data-theme]` token structure.

**Company profile layout** — the user asked what else could go in. Proposed
blocks, each rendering only when the registry has data:

1. **Identity** — brand (Cyrillic + Latin) over legal name (Cyrillic + Latin),
   ИНН / ОГРН / registration date / address.
2. **Officially X, in fact Y** — declared ОКВЭД against actual product. This is
   the strongest recurring pattern in the material and
   `notes/okved_mismatches.md` already holds it, unpublished (Архангел registered
   as "professional training"; СКБ Пиранья as software; Кольская верфь as *sport*
   shipbuilding). It becomes a standing profile block, not a buried aside.
3. **People** — full ФИО + Latin + role + photo, linked to the person index.
   **Gated on Phase 1b.** Do not render this block from the current data: 148 of
   153 people are unverified and 120 of 153 role links are `_candidate: true`.
   Only 1 person has a photo.
4. **Products** — name, description, imagery, and **which units received them**.
5. **Money** — multi-year revenue/profit/headcount from БФО, charter capital,
   and the scale-mismatch flag where reach and revenue contradict (СуперХроно's
   ₽3.38m revenue against 810th Naval Infantry Brigade deployment).
6. **Ownership chain** — up to ultimate beneficial owner; state/Rostec proximity;
   EGRUL redaction and founder-disavowal flags.
7. **Corporate history** — renames and predecessor entities (Рационы питания →
   Боевые технологии is the model case).
8. **Physical footprint** — registered address vs actual production site, ground
   and satellite imagery, mass-registration-address flag.
9. **Sanctions** — every regime, with listing date and package number. Now the
    best-populated evidence block: **58 entities and 28 people** carry entries.
    But most cite an *aggregator*, not the underlying instrument, and their own
    notes say so — render the distinction (see Phase 1.5c), don't flatten it.
10. **Foreign components** — Western parts identified in this maker's products,
    with source and confidence. The block a sanctions desk reads first.
11. **Legal and IP** — licences, arbitration, patents and trademarks, with
    filing dates, applicants, representatives and co-inventors.
12. **Digital footprint** — websites (with WHOIS and hosting), Telegram channels
    with subscriber and post counts, VK pages, YouTube, marketplace listings.
13. **Open questions** — what is not established about this entity, per-entity,
    replacing the single global catch-all that
    `roymarket_tracking_discipline` records as having rotted before.
14. **Sources** — every document backing the above, linked to `sources.html`.

**Adjacent-not-core entities** (`roymarket_adjacent_networks`) get a registry
`tier: adjacent` and render as a short disambiguation list only — the policy
stays, it just becomes structural instead of remembered.

---

## Phase 5 — The prose

**Status: not started.** No `docs/_prose/` directory; narrative rewrite hasn't
begun. Depends on Phase 4's templates existing first.

Written by hand into `docs/_prose/`, EN and RU independently, per the Phase 0
mode table.

### The preamble — how the reader gets here

The narrative opens by explaining where this investigation came from, and the
origin is also the hook. This project began as `wb_watch`, a tracker of military
goods sold on Russian consumer marketplaces. The reason it turned into this is
that **РОЙ.МАРКЕТ's own landing page names Wildberries and Ozon outright**,
recruiting their sellers. The investigation didn't go looking for a connection to
the earlier work; the target announced one.

That is a proper cold open in the investigative register — the subject
self-incriminates in its own marketing copy, and the writer just quotes it. It is
already sourced in the current brief and needs no new research: finding 06
("supplier-recruitment target is Wildberries and Ozon sellers"), the Kommersant
13 August report on a 10,000-SKU catalogue extending into body armour, optics and
field uniform — "categories that overlap almost exactly with this project's
existing Wildberries dataset" — and the observed callback that the whole platform
is built without warehouses **because** Ukrainian drones hit Wildberries'.

### The framing this creates for everything after it

The manufacturer roster then stops being an inventory and becomes a prediction,
stated plainly up front: **these are the most likely suppliers to appear on
РОЙ.МАРКЕТ, because they are already residents of the platform owner's parent
body — and the overlap is not hypothetical, it has already been identified.**

`ООО «Тримикс»` / «Булат» / 3mx is the worked example and should be given room
rather than left in a table cell: the first confirmed WB ↔ РОЙ.МАРКЕТ overlap,
64 Wildberries listings of which 63 classify as strictly military, and shown at
ЦБСТ's own Дронница 2025 showcase.

**Updated 2026-08-24 — the thesis has now been tested against the whole roster,
and the result is better than "one crossover".** 86 of 93 manufacturers were
checked against `wb_watch`'s own seller data (the remaining 7 have no ИНН to key
on). Three confirmed overlaps, and they fall into **two structurally different
kinds** — which is itself the finding:

- **Direct**: the manufacturer sells under its own ИНН. ООО «ГАСКАР» (8
  listings, all military-flagged) and ООО «АСЕЛ ЛАБС» (5 listings, all
  military-flagged, its own drone detectors under its own name). Гаскар is
  independently sanctioned, which sharpens the point considerably.
- **Reseller-mediated**: the brand reaches Wildberries through intermediaries
  while the manufacturer's own ИНН never appears. Тримикс/«Булат» is this case —
  four separate ИП seller accounts, and the ИНН-keyed sweep found *nothing*.

**That second category is the methodological point, and it should be stated in
the prose, not buried in a schema note.** An analyst screening only for
manufacturer-owned storefronts would conclude Тримикс has no marketplace
presence — the exact opposite of the truth, and the flagship finding of the
entire investigation. The absence of a maker's ИНН from a marketplace is not
evidence of absence from the marketplace. For a document arguing that sanctions
screening should reach these companies, a demonstrated blind spot in the obvious
screening method is a substantive argument, not an aside.

Three things follow structurally from this framing:

- The registry's **`wb_overlap`** field distinguishes `confirmed_direct` from
  `confirmed_reseller` (see Phase 3.5), so the prediction is falsifiable and its
  status visible per company rather than asserted once in the introduction. It
  also gives the `wb_watch` dataset a defined join key back into this work.
- **State the 84 negatives honestly.** `none_found` means "no seller carries this
  ИНН", not "absent from Wildberries" — the Тримикс case proves the difference.
  Any published count must be worded to survive that distinction.
- The recap should say plainly what would confirm or refute the thesis, in the
  expert-witness register: a resident appearing in the РОЙ.МАРКЕТ catalogue is
  confirmation; the catalogue filling with entities from outside the ЦБСТ
  roster is not.

### The body

The existing "Eighteen findings" list is the right backbone for the recap — it is
the strongest material in the document — but it is written as numbered research
notes and needs rewriting as narrative: deadpan accumulation, the regime's own
documents doing the convicting, no explaining the irony.

RU is not a translation. Per the style guide's RU register: long periodic
sentences on colon-then-elaboration and chained тире, anaphora at the climax,
first-person «мы» permitted, and the engine is dry registry lexis («ОКВЭД
26.11», «учредитель», «уставный капитал») colliding with plain moral nouns.

---

## Verification

- `python3 scripts/check_registry.py` — schema, ИНН checksums, duplicates, orphan
  source ids. Must pass before a build.
- `python3 scripts/build_site.py` then `python3 scripts/check_tag_balance.py` over
  **every** generated file (extend it from its current single hardcoded path).
- `scripts/check_citations.py` (new) — every factual claim block in generated HTML
  carries a `source_id` resolving to `sources.json`; fails the build otherwise.
  This is what makes the output survive a hostile reader.
- Link check across all generated pages, including the EN↔RU language toggles.
- No `<pre class="mermaid">` ships without something to render it; the ownership
  graph appears as an image in a browser with JavaScript disabled.
- Every `<img>` referenced by a generated page exists on disk **and is tracked by
  git** — the current tree fails this today.
- EN/RU parity: every section present in both; report any missing.
- `python3 scripts/mine_leads.py` still runs and still dedupes correctly against
  the registry rather than the old HTML.
- Open `docs/index.html`, `docs/dossier.html` and three profile pages in a
  browser, light and dark, desktop and narrow viewport.
- Spot-check five entity records back to their primary documents in
  `data/sources/` — the registry must not have drifted from the source during
  extraction.
- **No `_merged_into` tombstone renders as a live entity or person**, and
  reader-facing counts say 145/152, not 148/153.
- **No curated conclusion field has been overwritten by a bulk write** — run the
  Phase 3.5 guard, and specifically assert `ooo-trimiks-bulat-3mx` is
  `confirmed_reseller`, not `none_found`.
- `python3 scripts/extract_registry.py` twice in a row leaves screening fields
  intact (`opensanctions_screened_at`, `aleph_screened_at`, `wb_screened_at`,
  `securing_measures_checked_at`) — the carry-forward regression test.

## Sequencing note

This is a multi-session program, not one pass. **Revised order as of
2026-08-24 (later in this session)**, given that Phases 0–2 are essentially
closed and Phase 3.5's commit step is now done:

1. **Fix the Тримикс `wb_overlap` regression first — still the single
   outstanding blocker.** Everything else in Phase 3.5 (item 8, commit) is
   done; this one (item 1) is not. Small, and it protects the project's
   headline claim from self-contradiction.
2. **The rest of Phase 3.5** — the overwrite guard, type-instability
   normalization, `_merged_into`, the reverse source index, unifying the three
   open-question stores, generalizing `check_tag_balance.py`.
3. **Phase 1b** — the people-verification gate (user-chosen). This is the
   largest remaining research pass and the one that most constrains what Phase 4
   may publish. (Barashkov's PII enrichment this session is one data point
   inside this phase, not a substitute for the bulk `_candidate`-role-link
   resolution work Phase 1b still needs.)
4. **Phase 2c probe** — time-boxed GUR access retry, then either the sweep or
   the documented fallback. Independent of the above; can interleave.
5. **Phase 3** (imagery) and **Phase 4** (generator) — Phase 3 has started
   (a first small batch of leader-id/rk.2035.university assets, see above) and
   enriches profiles but does not block the build, so Phase 4 can start once
   3.5 and 1b are done.
6. **Phase 5** (prose) last, as designed.

Checkpoints to stop for review: **after the Тримикс fix** (the registry and
brief agree again), **after the rest of Phase 3.5** (data is generator-safe),
**after Phase 1b** (the publish gate for person data), and at **first build**
in Phase 4.

**Artifact cutoff.** Per `roymarket_no_per_fold_publish` the Artifact only
republishes at an explicit user-called cutoff. A great deal has landed since the
last one — 58 sanctioned entities, 28 sanctioned people, a new OFAC-designated
entity, the full trademark sweep, the wb_overlap results, the full registry now
committed to git, and a first batch of real imagery. Worth calling a cutoff once
the Тримикс regression is fixed and the brief and registry agree again. **Do not
publish before that fix** — the live brief and the registry currently contradict
each other on the project's headline claim.
