# Rebuild the РОЙ.МАРКЕТ brief as a two-tier, data-driven publication

> **This is the canonical, live copy of this plan** — moved here 2026-08-24
> (later in this session) from `~/.claude/plans/spicy-beaming-kite.md` (a
> per-session, not-git-tracked location outside the repo) so it survives
> alongside the investigation it governs and doesn't depend on any one
> session's local Claude state. Read and update *this* file going forward.
> `CLAUDE.md` points here directly. The old `HANDOFF.md` redirect stub
> this note used to mention no longer exists in the repo (confirmed
> 2026-09-08) — `CLAUDE.md` was updated the same day to stop referencing
> it. If anything still points at `HANDOFF.md`, that's stale; this file is
> the actual live status doc.

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
| 1 — Registry (people) | **Not done — the neglected half.** Re-counted 2026-08-24 (later session) against the now-305-person roster: 146 `_verified: false`, 83 role links still `_candidate: true` (down from 111 earlier this session via a bulk EGRUL cross-check). Raw fractions against the grown roster are misleading — see Phase 1b's reframing: the real gap is a specific 147-person legacy cohort, not the roster as a whole. See **Phase 1b**. |
| **1b — People verification** | **NEW.** Gates Phase 4's People block. User-chosen over shipping hedged person data. |
| 1.5 — Source triage / typology | **Partial.** Files typed, but `facility_type` is populated on **3 of 148** entities — 1.5b is effectively unstarted. |
| 2 — Screening | **Substantially done**, 4 blockers documented below. OpenSanctions, Aleph and Rospatent trademarks all swept full-roster. **People-side OpenSanctions cross-reference now also done** (2026-08-24) — see below. |
| 2b — IP sweep | **Bulk-CSV pass done and superseded by a better source.** The `rospatent_tm_search.py`/`rospatent_patent_search.py` bulk-CSV sweep (`s0945`/`s0952`) is complete, but a live, unauthenticated JSON API at `searchplatform.rospatent.gov.ru` was reverse-engineered this session (see new findings below) and is materially more capable — full-text `patent_holders` substring search plus exact-field inventor search, vs. the CSV's bibliographic-only, no-wordmark-text limitation. `scripts/rospatent_searchplatform_search.py` full-roster `--force` sweep is **done**: 51/93 manufacturer-tier entities returned at least one candidate hit. **Triaged (2026-08-24), not yet promoted**: ~14 entities carry genuinely new, exact-name-matched, on-topic UAV/counter-drone patents (АО «НИИ «Вектор» — interceptor UAV + jamming, largest new find; НПЦ «ЭЛВИС» — UAV detection + anti-drone gun; АО «НИИ СТТ» — 9 UAV-specific patents; Тримикс — UAV detection device; plus ЦКБР, Клеверкоптер, Котлин-Новатор, ЭйАрТэк, Аэроплатформы, Сибирская навигационная компания, Центр Динарус, КРАВТ Удмуртия, НПП Радар ммс, Аркодим). Common-word/surname false positives correctly rejected (Гермес, Логос, Площадь, Росс, Прайм, Проммаш, Покров, and a Информационные-системы/ИНФОТЕКС word-order collision). One ambiguous case flagged for individual verification (ao-npp-bat's RU233454U1, truncated patentee string). **Promotion into `patents[]`/`corrections.json` with proper archiving is the next concrete step — not yet done.** |
| 2c — Foreign components | **Done, full-roster.** `screen_gur.py` (sanctions/uav-companies sections) swept full-roster earlier. **New this session**: a second, previously-missed GUR section — the `/components` foreign-parts teardown catalogue (5,851 records, no ИНН/ОГРН) — was identified (user-flagged), built into `screen_gur_components.py`, and swept full-roster. One confirmed real hit: `npts-ushkuynik`'s own flagship UAV ("Князь Вандал Новгородский") named directly by GUR with 12 foreign components (China/Taiwan/US/Switzerland), archived and promoted into `foreign_components[]`. All other candidate hits (16 on the first pass, 4 after adding a stopword filter) reviewed and rejected as generic-word or unrelated-platform collisions. A same-session "CBTS.611000" naming coincidence was investigated and explicitly rejected as a ЦБСТ tie (Ц transliterates as "Ts", not "C") — logged as a correction, not silently dropped. |
| 3 — Imagery | **Started (2026-08-24, later in this session).** First small batch of real assets collected from data already harvested (not a fresh scrape): 3 POI headshots pulled from leader-id.ru profile photos (only for people with an already ID-confirmed `user_id` — Барахтин, Соловьев, Лысенко) and 3 company logos pulled from the rk.2035.university БАС-showcase dataset (`s1168`, only for entities already corroborated against it — Радар ммс, Клеверкоптер, Эколибри). Linked via `people[].photo` / `entities[].images[]`. Coverage is thin — most people have no leader-id photo set, most entities have no rk.2035.university listing at all. `scripts/tg_media.py` (Telegram media download) still doesn't exist; VK avatar pulls via the existing `scripts/vk_fetch.py` haven't been run for imagery specifically. See updated Phase 3 below. |
| **3.5 — Registry hardening** | **Partially done.** Item 8 (commit everything) is **DONE** — see "Two things to fix," now three, below. Items 1 (fix the `wb_overlap` regression) and 2–7 (overwrite guard, type normalization, `_merged_into`, reverse source index, open-question unification, generalize `check_tag_balance.py`) are **still open** — the registry is safe (committed) but not yet generator-safe. |
| 4 — Generator | Not started. New prerequisites identified — see **Phase 3.5**. |
| 5 — Prose | Not started. Thesis framing has changed — see revised Phase 5. |

**Registry now holds (re-counted 2026-08-24, later session):** 149 entities
(93 manufacturers, 28 money-layer, 15 plumbing, 9 cbst-core, 4 adjacent), 305
people (up sharply from 154 — see Phase 1b's reframing below for why this
isn't 151 new unverified records), 1168 sources, 19 quotes. 58 entities and
**33 people** now carry `sanctions[]` entries (27 → 33 this
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

**Status update (2026-08-24, later in this session): first real dent made in
the `_candidate` backlog, via exactly the bulk EGRUL-snapshot approach item 1
below recommends.** Cross-checked every `_candidate` role link's entity_name
against the linked entity's own already-sourced `director`/`founder` field
(local data only, no network calls) — 28 of 111 role links (27 people)
resolved cleanly on an exact name match, `_candidate` dropped, the entity's
own `source_id` reused (not fabricated). The other 83 stay unresolved,
correctly: 35 because the candidate's entity name doesn't normalize to a
unique registry entity (one-off holding companies never separately profiled,
ambiguous legal-form variants), 48 because the entity resolved but its
director/founder field names a *different* person — informative in its own
right (several people hold candidate roles at more than one company and only
one is usually real) but not something to guess at. Also, separately, a full
review of the ~123 previously-unreviewed leader-id.ru candidates against
entity director fields (not just prose role text, which the first promotion
pass had used) found: 1 real duplicate-person bug (a second Лысенко Андрей
Олегович record, tombstoned), 1 missing `entity_slug` filled on an existing
correct role (Андрей Безруков → ЦБСТ itself), 1 misattributed candidate role
corrected (Чадаев А.В. was pointed at the wrong «Ушкуйник» entity), several
corroboration-only notes where leader-id's self-report matches an existing
sourced director field, and 2 real director-field *conflicts* flagged as open
questions rather than resolved either way (ЭйАрТэк, Смарт Текнолоджис — see
their entity records). `check_registry.py`: 0 errors throughout both passes.
This closes a meaningful slice of item 1 below but does **not** close Phase
1b — most of the remaining `_candidate` links and most `_verified: false`
records still need individual research (EGRUL pulls, web search, primary
documents), not just cross-checking against data already in the registry.

The entity pass is done; people were never given the equivalent treatment, and
the registry has also grown (305 people now, up from the 153 these original
counts were taken against, following a broader ИНН/ОГРН/entity-extraction
pass earlier the same day) — so these are stale as exact fractions, but the
*shape* of the gap they describe is still accurate and worth keeping as the
baseline this phase is measured against:

| Measure | People (baseline, 153) | (Entities, for contrast) |
|---|---|---|
| `_verified: true` | **5 / 153** | 147 / 148 |
| Role links flagged `_candidate: true` | **120 / 153** (now 83, post-resolution, against a larger 305-person roster — not directly comparable) | — |
| Has `dob` | 23 / 153 | — |
| Has `inn_personal` | 17 / 153 | — |
| Has a photo | 1 / 153 (now 4, see Phase 3) | — |

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

**Dedup pass run, 2026-08-25 (start of Phase 1b work) — 3 more duplicates
found and merged**, on top of the 3 already fixed earlier (`lysenko-*`,
`barakhtin-*`, `brovchenko-aleksandr-rufinovich`/`aleksandr-rufinovich-
brovchenko`). Exact-ФИО-word-set comparison across all 302 then-live people
found: `sergey-rufinovich-brovchenko`/`brovchenko-sergey-rufinovich` (kept
the former — it carries a sourced notes field on Olympic Fund beneficial
ownership; the latter's 2 unresolved `_candidate` role links were folded
into the canonical record, not discarded), `ivan-igorevich-karabinskiy`/
`karabinskiy-ivan-igorevich` (kept the former, which has the sourced
General Director role; the latter was empty), `gorodnichin-dmitriy-
aleksandrovich`/`-2` (kept the unsuffixed slug per the naming convention
the two earlier merges already established; folded in the `-2` record's
co-inventor role). A looser first-name+patronymic-only check (deliberately
ignoring surname) turned up ~16 more coincidental groups — all confirmed as
genuinely different people who happen to share a common Russian given-name/
patronymic combination (e.g. several different "Дмитрий Александрович"s),
not duplicates; no action taken on those. Live people count: 302 → 299.
`check_registry.py`: 0 errors. This closes the "Watch for" prerequisite —
the roster is now clean going into the rest of Phase 1b's verification
work.

**Bulk `_candidate` resolution against `egrul_batch_pull.py`'s snapshot,
2026-08-25 — 6 role links resolved.** Cross-checked every remaining
`_candidate` role link's `entity_name` against the full-roster director
snapshot `egrul_batch_pull.py` already pulled (138 `EGRULAPI_*.json` files
on disk, each carrying the queried entity's own `ГЕНЕРАЛЬНЫЙ ДИРЕКТОР:`/
`ЛИКВИДАТОР:` field as of 2026-08-22) — a different, more current data
source than the "already-sourced director field on the registry entity"
check the first resolution pass used, and one that reaches entities whose
`director` field on `entities.json` was never separately populated. Of 81
candidate links: 38 didn't normalize-match to any registry entity slug
(one-off/ambiguous names, same shape as before), 3 matched an entity with
no batch-pull snapshot on file, 34 matched an entity with a known director
who is a **different person** than the candidate (left alone, per the
standing discipline — informative on its own, not something to guess at),
and **6 resolved on an exact full-ФИО match**: Бессонов С.Н. → ООО
«Аэромакс» (ГД), Некрасов А.В. → ООО «КБ «Синергия»» (ГД), Костюнин П.А. →
**both** АО «Стратим» (ГД) and ООО «Стратим» (Ликвидатор — a real, useful
finding: the same person holds different roles at the two same-named
Стратим entities), Чичков А.Ю. → ООО «ДРОНОМИР» (ГД), Баранова О.В. → ООО
«Прайм» (ГД). Each got its own `source_id` from the batch-pull snapshot,
`_candidate` dropped, other still-unresolved candidate roles on the same
people left untouched. `_candidate` count: 81 → 75. `check_registry.py`:
0 errors. The 34 director-mismatch cases are a natural next target — not
fixed here, since "which of two plausible people is the real one" needs
individual judgment, not a bulk pass — but worth a closer look, since a
meaningful fraction may be resolvable the same way the earlier session's
Чадаев/«Ушкуйник» correction was (candidate pointed at the wrong same-named
entity, fixable once the right one is identified).

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

**Broader source-catalogue health** (re-counted 2026-08-24, later session,
against 1168 sources — up from 951 when first measured): `type` null on
**589** (overwhelmingly the machine-harvested `ALEPH_*` / `OPENSANCTIONS_*`
JSON dumps the typing logic never covered — a known shape, not a random gap;
grew proportionally with source count, ~41-45% both times); `as_of` null on
**630**; `url` empty on **all 1168**; `entities` empty on **all 1168**;
`_verified: false` on **all 1168**. The percentages are essentially unchanged
from the original measurement — this is stalled at the same rate the count
has grown, not improving or worsening in relative terms. See Phase 3.5 §5
above for the same finding stated against `entities[].sources[]`.

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

## Phase 3 — Imagery (merged 2026-09-01 — see "Visual saturation" section below)

Merged into the "Visual saturation" plan's own `#### Phase 3 — new
standalone person/POI template + imagery` section, at the user's own
observation that this and that plan's differently-numbered Phase 3 were
doing overlapping work (imagery feeds the very page template that phase
builds). Full status/history preserved there, not deleted — read it there,
not here.

<!-- original content below, superseded by the merge above -->
<!--
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
- **2026-08-25 (later session, HAR-driven marketplace pass)**: a new source
  class for this phase — user-supplied HAR captures of Ozon/WB/Yandex Maps
  sessions, processed via `scripts/har_tools.py` (salvages truncated HAR
  JSON — promoted from a `/tmp` scratch file this session, later given a
  `list`/`grep`/`extract` CLI so large captures can be triaged/extracted to
  files by the user without routing full response bodies through the
  assistant's context — see the `roymarket_har_token_efficient_workflow`
  memory). Confirmed `ooo-gaskar`'s Ozon storefront
  via matching ОГРН (`s1385`); resolved `ooo-pokrov`'s site and the "Макс 911"
  Ozon dealer's real identity (ИП Коровкин, via egrul.nalog.ru open API,
  `s1387`/`s1388`); for `ooo-goudron`, confirmed/corrected two Ozon seller
  leads (one is actually a different legal entity, ООО «ИНВИЖН ТРЕЙД» —
  caught before misattribution), archived its own product site (набат.рф,
  `s1393`) including the self-incriminating "СВО" tagline, and pulled 4
  showroom photos + customer-review quotes from a Yandex Maps HAR (`s1396`)
  — most notably an official-account photo of wall signage reading "СВОих не
  бросаем" and a customer review confirming a combat-zone purchase. Two new
  standing rules came out of this pass, now in memory: VK/TG counts as a
  primary source when no official site exists
  (`roymarket_vk_tg_as_primary_source`), and marketing copy must be scanned
  for and quote verbatim any self-incriminating СВО/military language, not
  just paraphrased around (`roymarket_capture_self_incriminating_marketing_copy`).
  Open: only 50/120 Yandex reviews and 4/48 gallery photos pulled (more
  available on request); the smaller "GD" Ozon seller for `ooo-goudron`
  remains unresolved (legal-info modal never captured with content).
-->

---

## Phase 3.5 — Registry hardening (NEW, blocks Phase 4)

The registry was designed once and has since accreted fields from five screening
scripts and dozens of correction batches. A Jinja template consuming it today
would break, render duplicates, or silently omit blocks. This is the cleanup
that makes the data generator-safe. All of it is local, verifiable work.

**Data-shape re-audit, 2026-08-24 (later in this session).** Re-ran the counts
behind every item below directly against the live `data/registry/*.json` (149
entities, 305 people, 1168 sources now — up from 148/154/977 when this section
was first written) rather than trusting the numbers as last recorded. Headline:
**item 8 is done; items 3, 5, 6 and 7 have not moved AT ALL** despite a great
deal of other work landing in between — they've been consistently skipped in
favor of content work, not because anyone tried and failed. Item 1 turns out to
be a bigger gap than previously described (see below — the redesigned field
doesn't exist in code yet, not just the one regression). Item 4's tombstone
count has grown (more reason to fix it, not less). These are re-flagged here so
a future session doesn't have to re-derive current numbers from scratch again.

**1. Fix the `wb_overlap` regression and split raw from curated** *(user
decision: raw + curated)* — **DONE (2026-08-25).** `ooo-trimiks-bulat-3mx` was
already `confirmed_reseller` going into this pass (fixed in `b06d9f1`, an
earlier session). This pass closed the rest: wrote `scripts/screen_wb.py`
(reads the sibling `wb_watch` repo's already-scraped `sellers` table — 4385
sellers with an ИНН on file — and joins on each registry entity's own ИНН;
2 direct matches, both already known: ГАСКАР and АСЕЛ ЛАБС), which writes
`wb_matches[]` + `wb_screened_at` directly onto `entities.json` per the
carry-forward rule; added both fields to `ENTITY_CARRY_FORWARD_FIELDS` in
`extract_registry.py` (verified surviving a regen); reclassified ГАСКАР and
АСЕЛ ЛАБС's stale bare `"confirmed"` to `confirmed_direct` via
`corrections.json`, and cleaned up a third stale bare `"confirmed"` sitting
in an already-superseded ИНН-keyed correction block for Тримикс (harmless in
practice — a later slug-keyed correction already won — but an invalid enum
value nonetheless). Current distribution: `none_found` 83, `not_checked` 63,
`confirmed_direct` 2, `confirmed_reseller` 1. `wb_overlap` itself remains
**human-set only**, via `corrections.json` — `screen_wb.py` only finds a
seller trading under an entity's *own* ИНН; a reseller relationship (the
Тримикс/Макс 911 pattern) still needs the brand-name-search + primary-source
verification this project already does by hand.

**2. Guard against machine-overwrites-human generally.** **Partially done
(2026-08-25).** Added a `wb_overlap` enum validator to `check_registry.py`
(rejects any value outside `confirmed_direct`/`confirmed_reseller`/
`none_found`/`not_checked`) — this alone would have caught the ГАСКАР/АСЕЛ
ЛАБС bare-`"confirmed"` mislabeling immediately instead of it sitting
unnoticed for a session. `_merged_into` was already validated for referential
integrity (resolves to an existing slug) before this pass, just not flagged
as such here. What's still genuinely missing: neither check catches a
*silent regression* — a value that was correct, then got overwritten to
something else-but-still-valid by a bad bulk edit (the actual Тримикс
mechanism: a correction sweep set `none_found` over a previously-correct
`confirmed_reseller`, and both are valid enum members, so no validator alone
would have flagged it). Catching that class needs either a diff-against-
previous-run check or an explicit "downgrade requires justification" rule —
not built yet, and probably not worth building until it recurs; the
concrete fix this time was re-establishing the correct value, not tooling.

**3. Normalize type instabilities** — **DONE (2026-08-25).** All six rows
fixed and each now has a `check_registry.py` assertion guarding it (all
pass clean: 0 errors on full regeneration):

| Field | Fix applied |
|---|---|
| `charter_capital` | The 1 stray string (`ooo-npts-basirtk`, in its `add_entities` scaffold entry, both the flat field and its one `charter_capital_history` entry) cast to `int`. The 1 float (`pao-bank-psb`, kopeck-precision) left as-is — float is a legitimate numeric type, not a bug. New check: must be `int`/`float`/`null`. |
| `okved_mismatch` | Normalized all 22 non-null values (7 bools, 15 explanation strings) to one shape: `{"mismatch": bool, "note": str\|null}` — bools became `{mismatch: <bool>, note: null}`, strings became `{mismatch: true, note: "<original text>"}` (every string case was describing a confirmed mismatch). New check: must match that shape or be `null`. |
| entity `open_questions[]` | The 3 remaining bare strings converted to `{"question": "<text>", "source_id": null}`, matching the other 101 entries. New check: every entry must be a dict with a `question` key. |
| people `_corrected` | The 1 bare string (`lyubimov-aleksandr-sergeevich`, from a `"why"` field in `corrections.json` that had been written as a plain string instead of a list) wrapped in a 1-element list; confirmed no other bare-string `"why"` values exist anywhere in `corrections.json`. New check: must be a `list` or `null`. |
| `_verified_against` vs `verified_against` | **Already resolved before this pass** — direct count found 238 uses of `_verified_against` and zero of the bare typo'd key anywhere in `people.json`, so no migration was needed; a past session evidently already normalized this and the plan's own count had gone stale. |
| `sanctions[].regime` | The real bug turned out to be bigger than spelling drift: 16 entries (all on people, e.g. `andrey-bezrukov`, `andrey-turchak`, `mikhelson-leonid-viktorovich`) had an OpenSanctions **topic** code (`"sanction"`, `"role.pol"`, `"corp.disqual"`, etc.) sitting in the `regime` field, which isn't a jurisdiction at all — nulled `regime` on those and, where the topics value wasn't already stated in the entry's own `note`, prepended it there so the information wasn't lost. A further 21 entries used one of three placeholder-text spellings for "not known" (`"(see note)"`, `"(regime code not returned by OpenSanctions for this match)"`, etc.) — normalized to `null`, the registry's existing convention for "not known" elsewhere. The remaining 62 real, legitimate multi-jurisdiction semicolon-joined strings (`"US (OFAC...); Canada (...); EU (...)"`) were split into an actual `list[str]`, one element per jurisdiction, wording preserved exactly — no jurisdiction-name spelling was touched or harmonized, since that's a content-accuracy judgment call, not a type-shape bug, and collapsing e.g. "Canada (Special Economic Measures Act)" and "Canada (SEMA)" into one canonical spelling risks obscuring what a given source actually said. New check on both entities and people: `regime` must be `list[str]` or `null` — a bare string (semicolon-joined or not) now fails the build. |

All fixes applied directly in `data/registry/corrections.json` (the only
place any of these six fields originate — none are scaffolded by
`extract_registry.py`), each with a `why[]` note explaining the change was
a labeling/shape fix, not new evidence. Verified surviving a full
`extract_registry.py` regeneration.

**4. Make `_merged_into` real.** **Partially done (2026-08-25) — the
check_registry.py half is complete; the build-time filter is still blocked on
Phase 4 not existing yet.** Current tombstones unchanged: 3 entities
(`kb-germes`, `ooo-sibnk`, `ooo-kb-sinergiya`) and 3 people
(`brovchenko-aleksandr-rufinovich`, `barakhtin-artem-vladimirovich-2`,
`lysenko-andrey-olegovich-2`). `_merged_into` target resolution was already
validated (confirmed pre-existing, not new this pass); this pass added: (a)
a chain check — `_merged_into` erroring if it points at *another* tombstone
instead of the final live record (none found — all 6 existing tombstones
point directly at a live record); (b) a stale-incoming-reference warning —
any other record's `entity_slug`/`slug` pointing at an entity that is itself
tombstoned (none found — checked directly against the current registry,
zero stale refs exist today, so this is a regression guard for future
merges, not a fix for an existing problem); (c) the coverage report now
prints both raw and live counts (`149 raw / 146 live`, `305 raw / 302 live`)
instead of only the raw figure. **Still open**: nothing outside
`check_registry.py` reads `_merged_into` yet — `docs/index.html` itself and
any future generator still need to actually filter tombstones out, which
needs `build_site.py` (Phase 4) to exist first. Counts reported to readers
in prose should use the live numbers above.

**5. Build the reverse source index.** **Done, in the form the plan itself
specified (2026-08-25)** — "build the reverse map at build time... rather
than duplicating data" turned out to mean this doesn't need Phase 4 to
exist first. New `scripts/reverse_source_index.py`: a pure `build_index()`
function (importable by the eventual `build_site.py`) that derives
`entity_slug -> [source_id]`, `person_slug -> [source_id]` and
`source_id -> [(kind, slug)]` by matching each source's own `inns[]`
(every ИНН/ОГРН `inventory_sources.py` found in the document text) against
the registry's own `inn`/`inn_personal` fields — no static duplication
written into `entities.json`/`sources.json` at all. Run standalone for a
coverage report, or as of this pass it's wired into `check_registry.py`'s
own coverage output on every run. Actual coverage: **74/142 entities and
16/23 people reach at least one source this way** (249 of 1392 sources
have a matching ИНН) — a real result, not a placeholder, and a large jump
over the old static field's 1/149. The 68 entities-with-an-ИНН that still
resolve to zero sources are printed by the script as a work list (either
their backing sources haven't been ИНН-extracted yet, or their evidence is
prose-only with no ИНН-bearing document on file) — not fixed this pass,
since closing that gap is itself a sourcing task, not a normalization one.
`entities[].sources[]`/`sources[].entities` themselves were left as they
were (still ~unused) rather than backfilled, per the plan's own "don't
duplicate" instruction — the computed index is the reverse map now, full
stop. `sources[].url` (empty on all 1392) is a separate, still-open gap
this item was never actually about — most `data/sources/` files are PDFs/
zips with no meaningful single URL, so this field may simply not apply to
most rows; worth a decision, not a mechanical fix, if it's ever needed.

**6. Unify the three open-question stores.** **Done, in the form that
turned out to matter (2026-08-25).** Re-checking on the way in: the field
`scope` (`global` vs `unmined-source`) was already correctly distinguishing
the two kinds of item inside `open_questions.json` — an earlier reading of
this table item overstated that as unfixed. The two real defects were: (a)
the two embedded per-entity/per-person stores used key `question` where the
global store used `text` — now unified, all 116 embedded entries renamed to
`text` via `corrections.json` (`check_registry.py` now validates the `text`
key on all three, plus a `person_slug` shape check newly added for people);
(b) `entity_slug` was null on all 44 global rows with no `person_slug` field
at all. Added `attribute_open_questions()` to `extract_registry.py`, run
once entities/people are final: it sets `entity_slug`/`person_slug` ONLY on
an unambiguous match (a guillemet-quoted entity name or a full Cyrillic ФИО
appearing in the question text, and appearing in exactly one record —
«Азимут», which genuinely names two different entities, correctly stays
unset rather than guessed). Deliberately does not attempt transliterated
matching (English "Medvedev" vs Cyrillic "Медведев") — a surname-only
cross-script match is exactly the kind of guess this project's attribution
discipline exists to prevent. Result: **16 of 44 rows now resolve to a
specific entity or person**, up from 0, entirely from data already on file
(fully deterministic — re-running the scaffold reproduces the same 16 every
time, so this needed no hand-editing and nothing to maintain going forward).
`check_registry.py` now validates `open_questions.json`'s `scope` enum and
`entity_slug`/`person_slug` referential integrity, and reports the
attribution count in its coverage output.

**7. Generalize `check_tag_balance.py`.** **Done (2026-08-25).** Now accepts
zero or more file-path/glob arguments (`python3 scripts/check_tag_balance.py
"docs/companies/*.html"`), defaulting to `docs/index.html` alone when none
are given so the existing single-page workflow/instructions in `HANDOFF.md`
and the seeded memory keep working unchanged. Scoping is now a three-step
fallback instead of a hard requirement: `<div class="wrap">...</body>`
(the current file's own convention) → generic `<body>...</body>` (any other
page) → the whole file, printed as a loud warning rather than a silent
choice, since checking unscoped reopens the JS-literal false-positive risk
scoping exists to avoid. Multi-file runs print a per-file section plus a
summary line (`N/M file(s) OK`) and a non-zero exit if any file mismatches
or any requested path doesn't exist. Verified against `docs/index.html`
itself (identical 18/18 OK result to the pre-change version), a synthetic
`<body>`-only file (correctly used the fallback scope), and a synthetic
file with no wrapper at all and a real, deliberate `<p>` mismatch (correctly
fell back to whole-file scope and caught the mismatch).

**8. Commit everything.** ✅ **DONE** (see "Things to fix" §2 above,
2026-08-24) — `data/registry/`, `STYLE_GUIDE.md`, `docs/_archive/`,
`docs/assets/`, all screening scripts and the plan itself (this file) are now
tracked across five commits. The only item in this phase that's actually
closed.

**New finding this pass, not previously documented — orphan role links.** 20
of `people.json`'s non-`_candidate` role links (i.e., roles treated as
resolved/confirmed) have `entity_slug: null` — mostly high-profile named
figures whose role is described as free text without a formal entity link
(Медведев, Турчак, Песков, Фрадков, Осадчук, Рубинштейн, and others — a mix of
ЦБСТ-adjacent officials and money-layer figures). Some of these may be
correctly unlinked — a role like "associate of the ДАР fund network" doesn't
always map onto one legal entity — but the set has never been individually
triaged to confirm that, versus just being an extraction gap. Worth a pass
before Phase 4 renders per-entity People blocks, since a null `entity_slug` on
a *non-candidate* role currently reads as "resolved, nothing to link" rather
than "needs review."

**Reframing for Phase 1b, not a Phase 3.5 item but worth stating here since
it came out of the same audit:** the people roster has grown from 153 to 305
since Phase 1b's headline numbers were taken, and the growth is NOT uniform
unverified backlog — of the 158 people added via `corrections:add_entities`
(patent co-inventors, GUR/rk.2035.university/leader-id finds, EGRUL directors,
etc.), **154 are already `_verified: true`**, because they were added with
sourcing attached at creation time. The real unresolved gap is concentrated in
the original **147 prose/table-scaffolded records, of which only 5 are
verified** — a narrower, more specific target than "148/305 unverified" makes
it look. Phase 1b's actual job is verifying that legacy 147, not the newer
158, which are mostly already in good shape.

---

## Phase 4 — The generator and the site

**RETIRED 2026-09-08, at user direction.** The Jinja-generator approach
below is no longer the plan. It was deferred back in August specifically
to avoid automating the class of bug that caused the Тримикс `wb_overlap`
regression (a generator faithfully re-rendering whatever a bulk sweep
writes has the same blind spot, just automated) — and in the two weeks
since, it never got picked back up in favor of breadth-first investigative
work on other networks (see the session logs below this phase). Rather
than keep it on the books as a stalled prerequisite, it's retired outright.
What replaces it: direct iteration on `docs/index.html`/`docs/profiles/`
using data already in the registry — the same low-risk lever the MVP
publish below used, now the standing approach rather than a one-off
interim step. **Also retired, same direction, same date: the "MVP
publication" framing two sections below** — it was explicitly scoped as
an interim stand-in for Phase 4; with Phase 4 gone, there's no longer a
"real" version it's standing in for, so the distinction stops being
meaningful. Direct registry-to-page edits are simply how this project
publishes now.

**POI-verification gate relaxed, same date.** Phase 1b's "verify the
147-person legacy cohort before publishing People blocks" gate blocked
on a specific, well-defined worry: rendering unverified identities as
established fact in a sanctions-facing document. At user direction, that
gate is now scoped down rather than dropped — **the most important POIs
are treated as already verified where the underlying sourcing already
supports it**, not by blanket-flipping the `_verified` bool. Checked
2026-09-08: of the 12 people holding a role at a `cbst-core`-tier entity,
2 (`andrey-bezrukov`, `dmitriy-vladimirovich-rubinshteyn`) had exhaustive
sourcing (DOB, personal ИНН, multiple source-backed roles, sanctions
cross-references) sitting on file with `_verified` still `false` — a
bookkeeping gap, not a research one. Both flipped to `true` via
`corrections_people.json`. Two others in the same cohort
(`zamyatin-aleksandr-yurevich`, `borisov-aleksandr-sergeevich-tsbs-tula`)
were checked and genuinely don't clear the bar yet (one source each, no
DOB/ИНН) — left `false`, correctly. This is the model going forward:
check sourcing depth per person before flipping the flag, not a bulk
policy change. `check_registry.py`: 0 errors after the change.

**Headshot pulled the same pass**: Яныкина Нина Олеговна (sitting GD,
АНО «ЦБСТ») had no photo despite being `_verified` since before this
session. Found her own leader-id.ru profile photo (the same
identity-confirmed leader-id `user_id` already backing her role/ИНН
sourcing — not a fresh name-match), fetched, visually confirmed as a real
portrait, saved to `docs/images/nina-olegovna-yanykina_portrait_leader-id.png`,
wired via `corrections_people.json`. Other core-cohort people still
missing a photo (Бровченко, Рубинштейн, Замятин, Колударов, Байгутлина,
Борисов) were checked this pass — no clean bio-photo lead found for
Бровченко in the time spent; the rest weren't attempted. Real next step
if this continues, not done here.

**Design direction for any future site/publication work, same date.**
Whatever replaces the generator-and-rewrite approach should carry the
same aesthetic correction the Hub Insignia mockup thread worked out this
session (full reasoning and semiotics research in
`notes/hub_insignia_design_notes.md`): **no green-on-black terminal
skin, no space-movie-villain color scheme.** The subjects of this
investigation present themselves in techno-optimist, venture-deck
registers despite being arms producers — a menacing dark aesthetic
undersells that irony and reads as generated-AI-slop besides; a clean,
utilitarian, visually subtle treatment (paper-toned ground, one confident
accent color, flat functional signage rather than mood lighting) lets the
actual subject matter do the unsettling work on its own. This is a
standing instruction for `docs/index.html`/`docs/profiles/`, not just the
one mockup artifact it was worked out on.

---

**Everything below this line is the original Phase 4 plan, kept for
reference/ideas to recycle into direct-edit work — not an active
prerequisite queue.**

**Status: not started.** No `scripts/build_site.py`, no `docs/_templates/`, no
`docs/_prose/`. `docs/index.html` is still the single hand-edited file from
before this plan. `requirements.txt` has 3 entries (telethon, python-dotenv,
openpyxl) — **jinja2 is not among them and appears nowhere in the repo**.
`docs/assets/ownership-graph.svg` now exists (Phase 0).

**Render only what the data supports.** Every profile block is conditional.
Coverage re-counted directly 2026-08-24 (later session) against the current
149-entity registry, since several of these numbers had drifted a lot since
first written: `facility_type` still 3/149 (§8, unmoved), `patents` **25/149**
(§11 — up sharply from 1/148, this session's two patent-promotion passes),
`foreign_components` 3/149 (§10 — up from 1/148), `images` **3/149** (up from
0/148 — see Phase 3's first small imagery batch), `litigation` still 0/149
(§9, unmoved), `financials` 52/149 (§5, essentially unmoved), `cbst_tie`
16/149 (essentially unmoved), `confidence` 26/149 (§— unmoved, still ~83%
absent — see Phase 1's "Confidence" note, also stalled), `trademarks` 41/149,
`sanctions` 58/149 (well-populated now — see Phase 2 status). Decide per block
whether to render-if-present, show an explicit "not established" state, or
drop it — an empty block that looks like an answer is worse than an absent
one. The pattern worth noting: blocks fed by a *screening sweep* (patents,
sanctions, trademarks) have grown a lot; blocks that need *individual human
reading* per entity (facility_type, confidence tagging, litigation) haven't
moved at all across several sessions of otherwise-substantial progress — that
asymmetry is worth planning around rather than assuming steady progress on
everything.

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
   **Gated on Phase 1b.** Do not render this block from the current data.
   Re-counted 2026-08-24 (later session) against the now-305-person registry:
   146/305 people are unverified and 83/305 role links are `_candidate: true` —
   see Phase 1b's reframing above for why raw counts against the grown roster
   overstate the remaining gap (most of the growth is already-verified
   corrections-added records; the real target is a specific 147-person legacy
   cohort). 4 people have a photo (up from 1 — see Phase 3).
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

## MVP publication (2026-08-25) — a deliberate, scoped-down interim step

**RETIRED as a distinct concept 2026-09-08, same direction as Phase 4
above.** This was explicitly scoped as a stand-in for the "real" Phase 4
generator; with Phase 4 retired, there's no longer a more-real version
this is standing in for. The pattern it used — hand-edit `docs/index.html`
directly from evidence already sitting in the registry — is now just how
this project publishes, not an interim compromise. Kept below for the
record of what shipped and why.

Before the multi-session program below resumes, a bounded MVP shipped: the
Тримикс `wb_overlap` regression is **fixed** (`b06d9f1` — registry and brief
now agree; `docs/index.html`'s prose and summary-table row both state the
overlap is reseller-mediated, not a direct manufacturer storefront), and 5
new manufacturer profiles/supplements were hand-written into `docs/index.html`
from already-collected registry evidence that had never been published
(`d84c60c`): full new profiles for АО «НИИ «Вектор»» and АО «НПЦ «ЭЛВИС»»
(both Rostec/Роселектроника subsidiaries, sanctioned, with on-topic
counter-drone/anti-UAV patents), plus supplements to the existing Ushkuynik
(GUR teardown contradicting Chadaev's own "domestic components" claim),
КРАВТ (a newly-confirmed sanction, and clarifying that the parent's own IP
is water-treatment equipment while the UAV power-supply patent sits at the
subsidiary КРАВТ УДМУРТИЯ) and Экспломет (a 20-patent EOD/metal-detector
portfolio) sections. `check_tag_balance.py` and `check_registry.py` both
clean throughout.

**Decision behind this scoping** (full reasoning in the session that
produced it, condensed here): building the full Jinja generator
(`scripts/build_site.py`, Phase 4 below) was explicitly deferred rather than
started now, because standing it up before a narrow `check_registry.py`
overwrite-guard exists would risk automating a repeat of the exact Тримикс
bug — a generator that faithfully re-renders whatever a future bulk sweep
writes has the same blind spot that caused this regression, just automated.
The MVP instead used the lowest-risk lever available: hand-editing the
existing file with data that was already sitting, fully sourced, unused in
the registry (72% of manufacturers have at least one substantive evidence
block). This is explicitly an interim step, not a replacement for Phase 4 —
**Option B (the real generator) is still the eventual target**, gated on the
overwrite-guard, and should cover `wb_overlap`, `sanctions`, `trademarks`,
`patents`, `okved_mismatch` and `financials` at minimum once built.

**Not done by this MVP, still open**: the rest of Phase 3.5's hardening
backlog, Phase 1b people verification, and the other ~62 evidenced-but-
unwritten manufacturers beyond the 5 chosen here (a reasonable next batch,
once this round is reviewed).

## Sequencing note

**Superseded 2026-09-08** — this ordering exists to sequence toward Phase
4, which is now retired (see above). Direct registry-to-page edits don't
need a generator gate, and the POI-verification gate is now scoped to
"most important people already verified where sourcing supports it" (see
Phase 4's retirement note) rather than the full 147-person cohort. Kept
below for the record of the reasoning at the time.

This is a multi-session program, not one pass. **Revised order as of
2026-08-25**, given that the MVP above has now landed on top of the
2026-08-24 state (Phases 0–2 essentially closed, Phase 3.5's commit step
done, the Тримикс regression fixed):

1. **Review and, once satisfied, publish the MVP** — per
   `roymarket_no_per_fold_publish`, Artifact republishing is a user-called
   cutoff, not something to do unprompted even when a plan names it as a
   step. Confirm with the user before updating the live Artifact.
2. **The rest of Phase 3.5** — the overwrite guard (now the literal
   prerequisite for starting Phase 4's generator, not just good practice),
   type-instability normalization, `_merged_into`, the reverse source index,
   unifying the three open-question stores, generalizing
   `check_tag_balance.py`.
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
   3.5's overwrite-guard and Phase 1b are done. Phase 4 supersedes this MVP's
   hand-written content once it exists — the manual additions become a
   content draft the generator later formalizes, not wasted work.
6. **Phase 5** (prose) last, as designed.

Checkpoints to stop for review: **after MVP publish** (or the decision not
to, yet), **after the rest of Phase 3.5** (data is generator-safe),
**after Phase 1b** (the publish gate for person data), and at **first build**
in Phase 4.

**Artifact cutoff.** Per `roymarket_no_per_fold_publish` the Artifact only
republishes at an explicit user-called cutoff. A great deal has landed since the
last one — 58 sanctioned entities, 28 sanctioned people, a new OFAC-designated
entity, the full trademark sweep, the wb_overlap fix, the full registry now
committed to git, a first batch of real imagery, and now 5 new manufacturer
profiles/supplements. **The registry/brief contradiction that previously
blocked any publish is now resolved** — the remaining gate is just the
user's explicit go-ahead, not an outstanding correctness issue.

## zakupki.gov.ru mining workstream (started 2026-08-25, parallel to the phases above)

A separate track from the phased rebuild above — government-contract
mining, not registry-generator work. Status as of 2026-08-26:

- `scripts/zakupki_batch_pull.py` (scan/fetch-contracts/fetch-documents) and
  `scripts/mine_zakupki.py` (extraction pipeline) are both built and mature
  — contract-XML, payment-order (XML+HTML), contract-card HTML, docx,
  neustойка-PDF, and RAR-archive parsing, non-performance flagging,
  amendment tracking. See memory `zakupki_b2g_document_conventions` and
  `russian_b2g_legislation` for the domain-knowledge glossary this
  produced.
- `mine_zakupki.py` just gained `--depth {scan,deep}` and `--diff` (see
  memory `housekeeping_bundle_after_pulls` for the adjacent local-processing
  convention) — a cheap whole-corpus scan tier plus an incremental
  new-since-last-run diff, specifically to make bulk mining
  token-affordable instead of reading every contract's full detail every
  pass.
- **Deep-dived so far**: ИП Цыганов Вадим Борисович (17 files, full
  «Булат»/«Покров» war-emergency justification chain, 10 new named
  officials wired into the registry), ООО «Центр беспилотных систем»
  (Tula, the strongest confirmed `cbst-core` entity with a zakupki
  footprint — one fully-paid ₽3.072m contract, a director-field conflict
  surfaced and recorded as a dated `director_history` entry).
- **Done**: АО «Центр-Телко» (ИНН 7729150663, `ao-tsentr-telko`) — cap-table
  entity in the Аэромакс/Кронштадт holding restructuring. All 10 zakupki
  contracts (2012-2016, civilian radio-comms services for Moscow city
  bodies/ГФС России, unrelated to its UAV-holding-structure significance)
  identity-confirmed and wired into `government_contracts[]`; performance-
  flag hits hand-checked and found to be boilerplate, not real
  non-performance. Director Синельщиков А.В.'s passport (from a contract
  signature block) recorded on his person record per PEP policy. (This
  correction was originally filed under the raw ИНН as its
  `corrections_entities.json` key instead of the slug — found and merged
  into the canonical `ao-tsentr-telko` block 2026-08-26.)
- **Done (2026-08-26)**: `npp-radar-mms` (ИНН 7814027653) — full scan/
  fetch-contracts/fetch-documents pass, 75 contracts, top-10 by value
  fully document-verified (77 attachments, 42MB). 72-contract
  `government_contracts[]` wired (~₽1.37B total: 8 direct Минобороны
  contracts, 27 Минпромторг, scientific-institute customers, a confirmed
  БАС ВТ-ПСС maintenance contract for St. Petersburg SAR). A deep-mine
  re-pass over the 77 attachments afterward surfaced no new facts beyond
  the contract cards — confirms this is a fully-mined entity, not a gap.
  Two real bugs found and fixed along the way: `_zakupki_scan_log.json`
  contamination (25/38 entries had stale `reg_numbers` from before an
  already-documented regex fix — corrected via local re-parse) and
  `mine_zakupki.py` deep-mode's missing `card_fields` fallback (rendered
  near-blank reports for modern XML-less contracts — fixed, matching
  scan-mode's existing fallback). `zakupki_batch_pull.py`'s
  `fetch-documents` also crashed on `http.client.IncompleteRead` — fixed
  (commit bdf15db).
- **Done (2026-08-26)**: `ao-ross` (ИНН 7704097425) — full scan (19
  contracts) + one targeted fetch-documents pull on the standout ₽31.5M
  ФТС contract (IR-band surveillance system, fully executed with delivery
  act + payment order). Remaining 18 contracts triaged as sub-₽10M supply
  to ФСБ/Минобороны units — none individually warranting their own
  documents pass. Closes the long-standing "unresolved EGRUL lead" flag
  this entity carried since before the rebuild.
- **Done (2026-08-26)**: same pagination-contamination bug flagged 9 more
  registry ИНН with truncated `reg_numbers` (АО ПК «Азимут» 77, ООО
  «Смарт Технолоджис» 41, АО «Технодинамика» 44, АО «ПМЦ «Авангард»» 91,
  АО «НИИ «Вектор»» 160, АО «НПЦ «ЭЛВИС»» 33, АО «НИИ СТТ» 86, АО «Росс»
  19 — see above, «Радиофид Системы» 26) — all re-scanned clean.
  «Радиофид Системы» triaged at contract-card level: routine municipal/
  МВД telecom procurement (routers/modems), no UAV/ЦБСТ angle, not worth
  a documents pass. **Not yet triaged at contract-card level**: НПЦ
  «ЭЛВИС», «Смарт Технолоджис», «Технодинамика», and the two large primes
  «ПК Азимут»/«ПМЦ Авангард» (91 contracts, open industry-mismatch
  question — perimeter security vs UAV) — `fetch-contracts` not yet run
  for these five. АО «НИИ «Вектор»» (160 contracts) not yet even
  fetch-contracts'd — likely a large, already-well-documented state
  defense institute per the "don't over-invest in expected primes"
  caution below; scan first, triage before committing to a full pull.
- **Not started**: RNP (Реестр недобросовестных поставщиков) blacklist
  check for any entity with confirmed non-performance findings (Гаскар
  Интеграция is the current candidate, per `russian_b2g_legislation`'s
  ст.104 note) — parked, not yet requested by the user.

## Aleph screening + RuPEP identity enrichment workstream (2026-08-26)

Another parallel track — PEP/identity screening, not the registry-generator
work above.

- **`corrections.json` split** into `corrections_entities.json` /
  `corrections_people.json` (23k lines / 1.5MB had gotten unwieldy).
  `extract_registry.py`'s `load_corrections()` reads both and merges;
  verified byte-identical output before/after. `corrections.json` itself
  removed. See `CLAUDE.md`'s `data/registry/` section for the split.
- **`scripts/screen_aleph.py`** (Aleph/OCCRP free-text screening) ran its
  first full unscoped sweep this session — 419 of ~508 registry records
  came back with ≥1 hit, every one now carrying `aleph_matches[]` +
  `aleph_screened_at` directly on `entities.json`/`people.json` (a carry-
  forward field, not correction-settable — see `CLAUDE.md`).
- **`scripts/aleph_followup.py`** (new, this session) triages that noisy
  match list locally (name-token overlap, tier priority, dedup) and fetches
  full entity detail for hand-picked ids in batches (network job, ≤30
  ids/invocation, handed to the user each time per the crawling-jobs
  policy). Full triage of the post-sweep candidate pool (cbst-core through
  unclassified tiers) is now complete: **people with a personal ИНН went
  from 51 to 101** (checksum-valid, each with a `source_id` + `why[]` entry
  citing the specific Aleph EGRUL/OGRN record), plus 3 entity ИНН
  confirmed. Two recurring false-positive candidates
  (`gorodnichin-dmitriy-aleksandrovich-2` — a `_merged_into` duplicate,
  `kalinovskiy-nikita-vladislavovich` — caption-only match, not
  EGRUL-direct) were deliberately excluded from every wiring pass.
  `check_registry.py`: 0 errors throughout.
- **RuPEP.org** (Russian PEP biography database) added as a source this
  session — blocked for scripted access (Cloudflare JS challenge, see
  memory `rupep_org_cloudflare_blocked`) but works for the user's own
  browser; hybrid workflow (user downloads profile PDF → I extract text/
  headshot/dob/birthplace/ИНН, decline family-member detail per PII scope,
  wire via corrections). **11 people processed as of 2026-08-26**:
  Якушев (`s2452`), Сидякин (`s2535`, headshot at
  `docs/images/aleksandr-sidyakin_portrait_rupep.jpg`, flagged an
  unverified "Батальон «Дубай»" Navalny-team dossier link as an open
  question), Фрадков (ИНН dropped for checksum failure, logged as an open
  question instead), Лысогорский, Осадчук, Песков, Турчак, Рогозин,
  Алёшин, Медведев, оба Михельсона (Виктория checked-negative — no new
  network tie, just confirmed the family link), Соколова (DOB conflict
  vs. existing OpenSanctions value logged as an open question, not
  silently overwritten). Two standout results: **Кузякин Д.В.** (`s2788`)
  — RuPEP independently confirms his personal ИНН and lists him under
  active Ukraine/EU/Switzerland sanctions, upgrading his sanctions note
  from OpenSanctions-PLAUSIBLE to RuPEP-CONFIRMED; **Орджоникидзе А.Г.**
  (`s2789`, ИНН cross-corroborated via rusprofile.ru `s2790`) — RuPEP
  files him as family-of-PEP (mother is a serving MID ambassador-at-large
  and UNESCO-commission secretary), not wired as a network tie since the
  mother has no independent connection to this investigation.
  Checked-and-negative for **Безруков** (not on RuPEP — the correct
  1986-born ЦБСТ chairman, distinct from the 1960-born SVR-illegal
  namesake his DOB was originally misattributed from) and, as a full
  batch, for the fund-director/АНО cluster: Скорятин, Яныкина, Рубинштейн,
  Бровченко А.Р. and С.Р., Давыдов, Карабинский, Устратов, Маслак, Козлов
  — **none of these 9 are on RuPEP**. Combined with Безруков, this
  suggests RuPEP's coverage of this specific network is close to
  exhausted; further identity-enrichment candidates should come from a
  different signal (EGRUL, court filings, press) rather than more blind
  RuPEP tries against people with no independent government/political
  role in their existing role text.
- **налетай.рф marketplace mining (2026-08-26)** — user has a buyer ИП
  account; explored via a supplied HAR capture. Public catalog API
  (`api.xn--80aaorhk2b.xn--p1ai/api/v1/...`) is fully unauthenticated —
  `/catalog/listing` (per-seller products, plus a 302-manufacturer facet
  list when unfiltered) and `/products/<slug>` (full detail + gallery
  images). Cross-referenced the 302-name facet list against the registry
  by exact ИНН, confirming 9 sellers: ao-ekolibri, npo-kaysant,
  npp-radar-mms, ooo-aviron, ooo-gaskar, ooo-kleverkopter, ooo-kopterlab,
  ooo-kravt, ooo-rokot-tekh — each wired with a `web.marketplace_listings[]`
  entry (source_ids s2615-s2627), several with new `products[]`/
  `images[]` pulled from product-detail pages. No company/brand logos
  found on the platform for any of the 9. Standout: НПО «Кайсант»
  (confirmed `cbst_tie`, sanctioned) sells its kinetic FPV interceptor
  drone through a personal ИП storefront under its own founder/GD's name
  (Черепкова Н.С.) rather than the company's — flagged as a plausible
  deliberate visibility-reduction pattern, not yet proven. Two tempting
  false positives (ЗАО «Росси» vs `ao-ross`; a substring collision with
  `ooo-nova`) were checked and explicitly rejected rather than force-wired.
- **`notes/commands.md`** (new) — copy-paste reference for every recurring
  command in this project (housekeeping bundle, Aleph screen/triage/fetch,
  zakupki scan/mine/pull, profile rebuild, tag-balance check), so they
  don't need re-deriving each session.

---

## Visual saturation: landing page, company profiles, new POI profiles (started 2026-08-31)

> **Moved here 2026-08-31** from `~/.claude/plans/spicy-beaming-kite.md`
> (external, per-session, not git-tracked) for the same reason the phase-0-5
> registry rebuild plan above was moved here on 2026-08-24: that path is
> reused as a generic slug across unrelated planning sessions, which was
> causing confusion. Read and update *this* section going forward. The
> external file has been overwritten with a short redirect stub.

### Context

The investigation's data (`data/registry/*.json`) is far richer than what
either published surface currently shows visually. Two Explore passes over
`docs/index.html` and the profile-generation pipeline confirmed:

- **`docs/index.html`** (1,189 lines, hand-authored) has a mature design-token
  system (`--paper/--ink/--accent`, semantic `--ok/--mid/--low` confidence
  colors, serif/sans/mono type system) and real component classes
  (`.tag`, `.callout`, `.gallery`, `.cards`, `.scroll`+table, `.legend`), but
  exactly **one diagram in the whole site** (a pre-rendered Mermaid ownership
  graph) and **zero charts, zero maps, zero timelines** — despite the
  registry already holding chart-ready dated arrays (`financials[]`,
  `workforce_history[]`, `government_contracts[]`, `state_programs[]`). The
  densest, most consequential section (the ДАР/Градислава/Наша
  Правда/Olympic-Fund money-flow narrative) is pure prose plus one diagram.
  61 real evidence photos sit in `docs/images/` (facility ground/satellite
  pairs, product photos, portraits) with no unifying visual index.
- **Company profiles** (`templates/company_profile.{html,md}.jinja2` →
  `docs/profiles/*.{html,md}`, ~150 pages from one template) share the same
  token system via `docs/assets/profile.css`, but the numerically dominant
  sections — `government-contracts`, `state-programs`, litigation/licences/
  foreign-components, egrul-flags, open-questions — are flat
  `<ul class="plain">`, and financials/workforce/history are plain
  `<table>`. One template edit regenerates all ~150 pages, making this the
  highest-leverage surface to improve.
- **People (PEPs)** have no standalone page at all today — they only appear
  as `.person-card` blocks inside a company profile's `principals` section,
  unless separately registered as an ИП entity (which then borrows the
  company template). 359 people exist in `people.json` with no page of
  their own.

No chart/map JS library exists anywhere in the repo, and the user has
chosen to keep it that way: **all new visuals are build-time-generated
inline SVG/HTML+CSS**, matching the existing zero-runtime-dependency,
archival-friendly static-HTML approach (same pattern as the one hand-baked
Mermaid diagram) rather than a CDN-loaded chart library. The user also
chose to sequence **landing page first, then the profile template**, and to
add a **new standalone person/POI template** rather than only polishing the
existing `.person-card`.

The landing page scope grew through the planning conversation: the
underlying facts are current (no content-accuracy problem), but the page's
**visual structure, navigation, and prose delivery** are dated and need a
full rebuild — including a **complete copy rewrite** in `STYLE_GUIDE.md`'s
voice, and a **new opening**: a hook referencing the team's earlier
Wildberries investigation (https://amethyst-deceiver2001.github.io/wb-watcher/
— confirmed content: 7,666 military-item listings, 89% shipped through WB's
own warehouses, 802 sellers, the «Ganza» case study) as established
precedent, then the investigation's actual hypothesis stated flat: that
рой.маркет's most likely vendors are residents of its parent project,
ЦБСТ. The current "Eighteen findings" section is also confirmed too long
for what should be a quick recap for a general audience before the reader
descends into supporting detail — it needs tightening, not just restyling.
It keeps the current design tokens (shared with all profile pages) and
stays hand-authored rather than becoming registry-generated.

**Editorial pivot (2026-08-31, explicit user instruction, supersedes the
English-first drafting described below):** every section is now drafted in
**natural Russian first**, grounded in the user's own personal voice
examples — Alexey Kovalev's Noodleremover/Лапшеснималочная blog piece "Как
мэрия Собянина обманывает москвичей за их же деньги", and two Meduza
feature pieces — not translated from an English draft. This activates
STYLE_GUIDE §1.7's already-stated rule ("RU pages are written, never
translated from the EN") for the first time this project. Register notes
from the examples: more first-person «мы»/direct-reader-address than the
site's Investigative-mode restraint had been using, ironic/deflating
character and euphemism framing, systems-failure argument structure
(accumulated negligence over single-culprit blame), officials
characterized by silence/evasion rather than adjectives, forward momentum
over a hard kicker. **English translation happens only after the user
approves each Russian draft, section by section.** Drafting proceeds
section by section with a checkpoint (fully laid-out Artifact preview,
using the site's real design tokens) before moving to the next section —
first section drafted and previewed: the new hook + hypothesis opening
(RU draft published to Artifact `a8b6fdea-e869-432c-84e9-7cc547d91778`,
awaiting the user's review before being written into `docs/index.html` and
before the next section — the "Eighteen findings" → quick-recap rewrite —
is drafted).

**Added constraint (2026-08-31, explicit user instruction):** no new visual
element surfaces raw registry plumbing that carries no informational value
to a reader — entity/person `slug` strings, `_verified` boolean flags, CSS
custom-property/token names, or any other internal bookkeeping field.
Every badge/chip/label introduced below must earn its place by telling the
reader something substantive (a sourced fact, a confidence level, a count,
a date) — not expose implementation detail as decoration. This sharpens
STYLE_GUIDE §3.5's existing "no internal notation" rule rather than
replacing it; apply it specifically when designing the Phase 2 badge-row /
Phase 3 person-template chips, where registry fields like `_verified`
could otherwise tempt a checkmark that doesn't actually inform.

All work must respect existing hard constraints (already confirmed in
exploration): `data/registry/*.json` is the source of truth (visuals must
be data-driven, not hand-typed numbers); STYLE_GUIDE.md's confidence-chip
vocabulary (`t-doc`/`t-press`/`t-open` → `--ok`/`--mid`/`--low`) must be the
*only* semantic-status color system — new charts reuse it rather than
inventing a fourth color scheme; no internal notation (`source_id`, field
names) ever appears in visible prose/captions, only resolved `[sNNNN]`
citations; RU-is-evidence/EN-is-analysis and the Latin-name+Cyrillic-ФИО
dual format apply to any new labels; PII fields render only when
independently sourced, and a person's freeform `notes` never renders;
images render only when a `docs/images/` copy exists (graceful-degradation
pattern via `.person-photo.placeholder` already established); every
`docs/index.html` edit needs `scripts/check_tag_balance.py`; profile pages
are generated — edits land in the Jinja2 templates + `build_company_profile.py`
context, never on generated output; the HTML and `.md` outputs are one
script/two-templates kept in sync — every new visual needs a plain-text
equivalent in the `.md` template.

### Status

| Step | State |
|---|---|
| Phase 0 — palette sanity check | **Done.** `dataviz` skill's `validate_palette.js` found a real hard-fail (mid/low confidence-tag colors too close, ΔE 12 < the 15 normal-vision floor, in both light and dark mode). Fixed and reverified in both files: light `--ok` #1c6046→#0a7a53, `--mid` #7a5a10→#96700a (+ lighter `--mid-bg`/`--ok-bg` tints for contrast); dark `--mid` #d4b25f→#e0b23f, `--low` #e08c85→#ec7a95. Applied to `docs/index.html` and `docs/assets/profile.css` (6 blocks total — light `:root`, dark `@media`, dark `[data-theme]`, in each file). `check_tag_balance.py` clean. Profile pages link the stylesheet externally, so the fix reached all ~150 profiles with no regeneration needed. |
| Phase 1, §1 — Hook + hypothesis (new opening section) | **Drafted in Russian, in Artifact preview, awaiting user approval.** Not yet written into `docs/index.html`. |
| Phase 1, §2–12 | Not started — see "New section architecture" below. |
| Phase 2 (company profile template) | Not started — sequenced after Phase 1. |
| Phase 3 (new person/POI template) | Not started — sequenced after Phase 2. |
| Quick fix, unrelated but done same session | `scripts/zakupki_coverage.py`'s `DEFENSE_KEYWORD_RE` extended to also match the abbreviated `в/ч <digits>` form, not just spelled-out `войсковая часть` (user correction — в/ч is the more common form in practice). Verified against real and negative test strings. |

### Approach

#### Phase 0 — palette sanity check (once, before building anything)

**Done — see Status table.** Verification method for reference: run the
`dataviz` skill's `scripts/validate_palette.js` against the `--ok`/`--mid`/
`--low`/`--accent` hex values (light and dark), fix any FAIL before
building anything else on top of the palette.

#### Phase 1 — landing page (`docs/index.html`): full copy rewrite + structural redesign, hand-authored

The page's facts are current, but its prose, its structure, and its
navigation all need a full rebuild. This is one integrated pass — copy
rewrite and structural redesign are done together, section by section,
since the new architecture and the new voice are not separable (STYLE_GUIDE
mode selection depends on what each section is *for*, which is exactly
what the restructuring is also deciding). Design tokens
(`--paper/--ink/--accent`, `--ok/--mid/--low`, serif/sans/mono) stay as-is
— shared with ~150 profile pages, already confirmed solid — this phase
redesigns structure, navigation, and prose, not the base palette/type
system.

**Current structural problem, confirmed by direct inspection**: the page's
`<h2>`s are Eighteen findings → Defence Ministry origin → Physical
infrastructure → **The entity map** → Who actually makes the goods →
Digital/operational infrastructure → Data sources still unmined → Media
sources → What is not established. But "The entity map" `<h2>` alone spans
~400 lines (a third of the page) and, via nested `<h3>`s, actually contains
the ownership diagram *and* the entire ДАР/Градислава/Наша Правда/Olympic
Fund money narrative *and* the Legal entities table *and* the Supervisory
Board *and* Executives — four distinct subjects mis-nested under one
heading. Splitting these into their own top-level sections is itself a
major navigability fix, independent of any visual styling.

**New section architecture** (top-level, in order):

1. **Hook + hypothesis** (new). Opens on the team's earlier Wildberries
   investigation (wb-watcher: 7,666 military-item listings, 89% via WB's
   own warehouses, 802 sellers, the «Ganza» case) as established precedent
   — a marketplace already shown to enable military supply chains — then
   states this investigation's actual hypothesis flat: рой.маркет's most
   likely vendor base is residents of its parent project, ЦБСТ. **Drafted
   in Russian, in the Artifact preview, awaiting approval** — see Status.
   Real grounding used: of 155 ЦБСТ-linked entities mapped in the registry,
   3 are confirmed-overlapping against the earlier Wildberries dataset
   (ООО «Гаскар», ООО «АСЕЛ ЛАБС», ООО «Тримикс»), 69 not yet checked —
   hedged honestly as an early, structural finding, not a closed case.
2. **Quick findings recap** (rewrite of "Eighteen findings"). Confirmed too
   long for its job — tighten to genuinely skimmable, general-audience
   scope: deadpan accumulation, one fact-pair per item, no elaboration, no
   explained irony. Every item still links to the deeper section that
   substantiates it rather than trying to carry its own evidence inline.
3. **In-page navigation** (new) — anchor links to every section below, so
   the "quick recap → nitty gritty" structure the user asked for is
   actually navigable rather than requiring a scroll.
4. **"This was a Defence Ministry project from the start"** — kept, rewrite
   pass for voice/tightness.
5. **"Physical infrastructure"** — kept, rewrite pass; add the consolidated
   facilities index (ground/satellite image pairs currently scattered here
   and in "Who actually makes the goods", unified into one `.gallery` with
   consistent city/region captions).
6. **"The entity map"** — narrowed to just the diagram and the prose that
   directly explains it, moved earlier in the reading order since it's the
   page's one real piece of visual argument and the sections that follow
   should read as unpacking a diagram the reader has already seen.
7. **"The money behind the platform"** (new top-level section, split out
   of the old mis-nested content) — the ДАР/Градислава/Наша
   Правда/Olympic Fund narrative, rewritten for voice/tightness, plus a
   new build-time inline SVG chart aggregating `government_contracts[]`
   value-over-time (one hue, `--accent`, thin marks per the dataviz
   skill's mark spec), with a plain data table alongside for
   accessibility.
8. **"Legal entities"** — promoted to its own top-level section (was
   nested under "The entity map").
9. **"People"** (Supervisory Board + Executives) — promoted to its own
   top-level section, card/badge treatment consistent with the rest of the
   redesign.
10. **"Who actually makes the goods"** — kept, rewrite pass, `.cards`
    treatment for manufacturer sub-sections.
11. **"Digital and operational infrastructure"** — kept, rewrite pass.
12. **Appendices** — "Data sources still unmined", "Media sources", "What
    is not established" (this last one specifically Expert-witness/forensic
    mode — flattest register, every sentence quotable out of context) —
    made collapsible (`<details>`) to cut scroll fatigue without deleting
    content.

**Drafting discipline**: apply STYLE_GUIDE Part I's mode selection per
section, Part II naming (transliterated legal forms, Latin-name+Cyrillic-
ФИО, ИНН/ОГРН bare-digit format), Part III sourcing (confidence chips, no
internal notation, no research-process dates, quotes verbatim from Russian
originals), Part IV PII scope, and Part V (euphemism list,
bold-on-first-mention, cross-linking) — **written in Russian per the
editorial pivot above**, EN translation only after RU approval. Run the
document's own "Checklist before publishing" at the end of the rewrite.

New reusable low-level SVG/HTML component markup (bar chart, stat-tile,
sticky-nav, collapsible-appendix) is authored once here, then ported into
`docs/assets/profile.css` / the profile template in Phase 2.

Verify: `python3 scripts/check_tag_balance.py docs/index.html` after every
edit; a full browser read-through (light+dark, narrow+wide) for layout,
nav-anchor correctness, and voice consistency; every fact re-traced to its
existing registry source during the rewrite (a rewrite must not silently
drop or alter a sourced claim — STYLE_GUIDE §3.6 trace-before-correcting
applies to the rewrite itself); every new number in the chart/stat-tile
traced to an actual query, never hand-typed; the STYLE_GUIDE checklist run
once at the end of the phase.

#### Phase 2 — company profile template (`templates/company_profile.{html,md}.jinja2`, `scripts/build_company_profile.py`, `docs/assets/profile.css`)

One template/context change regenerates all ~150 pages, so land the
expanded component vocabulary (bar-list, timeline, sparkline, badge-row)
here once it's proven out on the landing page in Phase 1:

1. **Risk/evidence badge row** near the masthead: compact colored-badge
   summary (sanctions count, litigation count, foreign-components count,
   egrul-flags count) using the existing `--ok/--mid/--low` tokens, above
   the existing detail lists (which stay as lists for exact detail).
2. **Government-contracts → sorted value-bar list**: `build_company_profile.py`
   currently flattens `government_contracts[]` into `{text, source}` via
   `simple_list()` (`scripts/build_company_profile.py:275-282`), discarding
   `value_rub`/`date`/`customer`. Add a parallel context path that keeps
   `value_rub` as a number, sorts descending, and computes each row's bar
   width as a percentage of the entity's own max — rendered as a horizontal
   bar-list component (reuse `.card`/new `.bar-row` class) instead of
   `<ul class="plain">`. `state_programs`/litigation/licences/foreign-components
   stay as lists (no natural magnitude to bar-chart) but get the badge-row
   treatment from step 1 instead.
3. **Unified history timeline**: `history_tables` (director/founders/
   charter-capital/address/name histories) currently render as N separate
   flat tables. Replace with one horizontal/vertical timeline component
   (dated markers, each labeled with which field changed) built from the
   same `history_tables` context data.
4. **Financials/workforce sparkline**: when `financials[]` or
   `workforce_history[]` has ≥2 dated points, add a small inline SVG
   sparkline before the existing table (table stays for exact figures).
5. **Evidence-tier chips on products**: tag each `products[]` card with the
   same `t-doc`/`t-press`/`t-open` vocabulary reflecting its evidence tier
   (self-marketing vs. patent-description vs. battlefield-confirmed —
   consistent with the existing `rospatent_patent_description_evidence_tier`
   distinction).
6. Update `templates/company_profile.md.jinja2` in lockstep with every
   change above — plain-text equivalents. Hard requirement, per the
   one-script-two-templates invariant.
7. Regenerate everything: `python3 scripts/build_company_profile.py --all`,
   then `check_tag_balance.py` across all of `docs/profiles/*.html`.

Verify: spot-check 3 real pages spanning the data-richness spectrum —
`ao-nii-stt` (rich), `npp-radar-mms` (image-heavy, sparse contracts),
`ip-tsyganov-vadim-borisovich` (sparsest, ИП-as-company) — for visual
correctness and graceful degradation on missing data; confirm the `.md`
output still reads sensibly as plain text.

#### Phase 3 — new standalone person/POI template + imagery (merged 2026-09-01)

**Merged with the original registry-rebuild "Phase 3 — Imagery" section**
(previously tracked separately, further up this file) — the user's own
observation, and correct: one gathers the photo/logo assets, the other
builds the page template whose header field is specifically `people[].photo`
/ `entities[].images[]`. Tracking them as two differently-numbered,
differently-located "Phase 3"s was itself a source of confusion (the same
class of problem as the external-plan-file slug collision fixed earlier)
— now one phase, one status line. The original section's full work log
(leader-id.ru headshots, rk.2035.university logos, the HAR-driven
Ozon/WB/Yandex Maps imagery pass, the still-open `scripts/tg_media.py`
build) is preserved below under "Imagery status/history" rather than
rewritten — nothing lost, just relocated and no longer double-tracked.

New `templates/person_profile.{html,md}.jinja2` + a `build_person_profile`
mode (either a new script `scripts/build_person_profile.py` mirroring
`ProfileBuilder`'s structure, or a second `Builder` class added alongside
it — reuse `humanize_item`/`source_label`/`load_json` rather than
duplicating them). Output goes to `docs/profiles/<person-slug>.html`/`.md`
— confirmed zero slug collisions between `entities.json` (155 slugs) and
`people.json` (359 slugs), so no path-clash risk.

Content, following the same PII/sourcing rules already enforced in
`.person-card` today (full detail only when independently sourced,
`notes` never rendered raw):

- Header: photo (or `.person-photo.placeholder` fallback), Latin name +
  Cyrillic ФИО, DOB/birthplace/address/ИНН as a badge/meta-grid row (reuse
  `.meta-grid`), sanctions status chip if applicable.
- **Roles across entities**: every `roles[]` entry, cross-linked to that
  entity's own profile page (`{{ entity_slug }}.html`) — this is the one
  genuinely new piece of information a standalone page can show that a
  `.person-card` snippet can't.
- Quotes attributed to them (cross-reference `quotes.json`).
- Screening evidence (`opensanctions_matches`, `aleph_matches`, etc.)
  rendered as resolved, human-readable summary rows (count + top matches),
  never a raw dump of the match JSON.
- Sources-cited table, same pattern as company profiles.
- Every company profile's `.person-card` gets a link to the person's new
  standalone page (small addition to Phase 2's principals-section markup).

Verify: build for 3 people spanning the range — a sitting officer with
rich sourcing (Яныкина), a co-inventor with minimal data (Городничин), and
someone with `sanctions`/`opensanctions_matches` populated — confirm PII
fields only render when sourced, `notes` never leaks, and
`check_tag_balance.py` passes.

##### Imagery status/history (the former standalone "Phase 3 — Imagery")

**Status as of 2026-08-25: STARTED — a small first batch of real assets,
not a fresh scrape.** `scripts/tg_media.py` still doesn't exist. Current
coverage (checked 2026-09-01): 7/155 entities have `images[]`, 23/361
people have a `photo` — low in absolute terms, but not every entity/person
needs one to be "done" (PII policy scopes full imagery to principals/PEPs,
not every name in the registry).

Sources already pulled from (all local reprocessing of already-harvested
data, not new live scrapes):
- **leader-id.ru POI headshots** (`docs/images/<slug>_portrait_leaderid.jpg`)
  — gated to people whose leader-id account was already independently
  ID-confirmed (never a raw name-only candidate match). 3 pulled this way:
  Барахтин А.В., Соловьев К.Ю. (both «Аркодим»), Лысенко А.О. («Визионеро»).
- **rk.2035.university company logos** (`docs/images/<name>_logo_rk2035.{jpg,png}`)
  — 3 pulled (НПП «Радар ммс», «Клеверкоптер», АО «Эколибри») from the 5
  entities already corroborated against that dataset; product-model
  `avatar` fields are null on every record in that source, confirmed dead
  end.
- **HAR-driven Ozon/WB/Yandex Maps pass** (2026-08-25) — resolved several
  seller identities (ООО «Гаскар»'s Ozon storefront, ООО «Покров»'s site,
  the "Макс 911" Ozon dealer's real ИП owner), caught one misattribution
  before it happened (a "GD" Ozon seller lead for `ooo-goudron` that turned
  out to be a different legal entity), and pulled self-incriminating
  marketing copy + showroom photos for `ooo-goudron` (a Yandex Maps HAR,
  including an official photo of "СВОих не бросаем" wall signage). Two
  standing rules came out of this: VK/TG counts as a primary source when no
  official site exists, and marketing copy must be scanned for verbatim
  self-incriminating СВО/military language, not paraphrased around (both
  now in memory). Left incomplete: only 50/120 Yandex reviews and 4/48
  gallery photos pulled for that one HAR; a smaller "GD" Ozon seller lead
  remains unresolved.

Still not built: **`scripts/tg_media.py`** — Telethon `download_media` over
a channel/message-id range or a product/handover-keyword text match,
writing `docs/images/tg/<channel>_<msgid>.<ext>` plus a sidecar JSON
(channel, msg_id, date, post text, permalink) for chain-of-custody. **Live
network job → hand the user the exact command**, same as every other
scraping job in this project. The `«Благодарственное письмо»/«Почетная
грамота»` genre marker is a high-yield keyword for handover-evidence posts
that name the receiving unit. Also not yet run: VK avatar pulls via the
existing `scripts/vk_fetch.py` for entities with a `web.vk[]` handle (script
exists, never pointed at imagery specifically).

The curation/user-supply conventions stand as before: for each manufacturer,
select product/field-test/frontline-handover images and write captions to
`entities[].images[]`; the user supplies satellite/ground facility views and
press portraits (the pattern already used for the 24 pre-existing files);
person photographs stay bounded to professional/public-presence sources
(leader-id.ru profile photos, company sites, press), never private/family
imagery, per the Phase 0 PII rule.

### Critical files

- `docs/index.html` — hand-authored landing page; `<style>` block holds the
  design tokens (kept in sync with `docs/assets/profile.css` by hand).
- `STYLE_GUIDE.md` — authoritative voice/naming/sourcing rules; read in
  full before drafting any section.
- https://amethyst-deceiver2001.github.io/wb-watcher/ — the prior
  Wildberries investigation referenced in the new hook.
- `docs/assets/profile.css` — shared token/component stylesheet for all
  profile pages; new bar/timeline/sparkline/badge-row classes land here.
- `templates/company_profile.html.jinja2` / `.md.jinja2` — sections to
  convert: `#government-contracts` (line ~90), `#ownership-history`
  (line ~44), `#financials`/`#workforce` (line ~76/108), `#products`
  (line ~61).
- `scripts/build_company_profile.py` — `ProfileBuilder.build_context()`,
  `simple_list()` (line 275), `humanize_item()`, `source_label()`.
- `templates/person_profile.html.jinja2` / `.md.jinja2` — new files.
- `scripts/build_person_profile.py` (or an added class in
  `build_company_profile.py`) — new.
- `scripts/compute_landing_stats.py` — new, for Phase 1's stat strip.
- `scripts/check_tag_balance.py` — run after every HTML edit/regeneration.

### Verification

- Phase 0: `node <dataviz-skill-path>/scripts/validate_palette.js
  "<hex,hex,...>" --mode light` and `--mode dark` against the current
  token values — done, see Status.
- After Phase 1: `check_tag_balance.py docs/index.html`; full manual
  browser read-through (light + dark, narrow + wide) for layout/overflow/
  nav-anchor correctness and voice; every new stat/chart number traced to a
  real `compute_landing_stats.py` query output, not typed by hand; every
  rewritten claim re-traced to its existing registry source; STYLE_GUIDE.md's
  own "Checklist before publishing" run against the finished page.
- After Phase 2: `python3 scripts/build_company_profile.py --all`, then
  `check_tag_balance.py` over all of `docs/profiles/*.html`; spot-check the
  three data-richness-spectrum pages named above in both `.html` and `.md`.
- After Phase 3: build the three named test people; confirm PII-sourcing
  and `notes`-never-renders rules hold; `check_tag_balance.py` on the new
  pages.
- Throughout: no new visual introduces a source_id/internal field name into
  visible text, no chart series color reuses the reserved `--ok/--mid/--low`
  triad for a non-status purpose, and RU-evidence/EN-analysis + Latin+ФИО
  formatting is preserved in every new label/caption.

## zakupki mining: signatory disambiguation + extraction gap-fills (2026-08-31/09-01)

### Context

Follow-on to the "zakupki.gov.ru mining workstream" section above — this is
a specific session's worth of parser hardening and gap-filling done via the
existing `mine_zakupki.py` → `zakupki_coverage.py` / `zakupki_customer_clusters.py`
/ `zakupki_signatory_diff.py` housekeeping chain, not a new phase. Triggered
by trying to trust `zakupki_signatory_diff.py`'s "по Уставу" hits as
director_history candidates and finding a real methodological gap:
`docx_signatories` didn't distinguish which contract party (customer vs.
supplier) a signatory belonged to, so a customer-side official (e.g. a
"Войсковая часть 35533" commanding officer) could read as a plausible new
director of the supplier entity.

### What shipped

- **`find_signatories()`** (new, `scripts/mine_zakupki.py`) labels every
  `docx_signatories` entry `customer`/`supplier`/`unknown` by tracking the
  "именуемое в дальнейшем «Роль»" preamble label nearest each signatory's
  own clause. Five real regex gaps found and fixed by stress-testing against
  the full ~1600-file `.docx` attachment corpus, each now covered by a
  fixture in `tests/test_zakupki_parser.py` (16/16 pass):
  1. Missing party disambiguation entirely (the original gap).
  2. An individual-entrepreneur supplier's role label sits *after* its
     authority clause ("...ОГРНИП <n>, именуемое в дальнейшем «Поставщик»"),
     not before it like every legal-entity case.
  3. A missing comma before "с одной/другой стороны" broke the clause-
     boundary check, leaking one party's label into the other's window.
  4. Compound role labels ("Головной исполнитель") and lowercase labels
     («поставщик») weren't matched by the original exact-phrase list —
     fixed by classifying on the label's last word instead.
  5. A joint "совместно именуемые «Стороны»" label was short-circuiting the
     real per-side label search; a reversed connector word order ("далее
     именуемое «Роль»"); and a parenthetical gender-suffix blob
     ("именуемое(ая,ый)") that broke the regex match entirely, costing
     *both* signatories in an affected document.
  - End state on the full corpus: 427 signatories, 8 `unknown` (1.9%), 1
    residual same-party collision (a rare docx-glue text corruption,
    documented not chased further).
- **`zakupki_signatory_diff.py`** now reports two separate sections —
  "supplier side" (real director_history candidates) vs. "customer side or
  unresolved" (never officer evidence) — instead of one undifferentiated
  list.
- **New extracted-but-never-surfaced fields wired into the deep report**
  (same class of bug as the pre-existing `fact_address` fix): supplier
  `delivery_place` (the contract's actual delivery/install destination,
  distinct from both parties' registered addresses) and supplier
  `email`/`phone`.

### What got wired from this pass

- `director_history`: `ao-nii-stt` (Галкин В.С., 2014-10-29 — new earliest
  director on record), `ooo-aeromaks` (a clean 4-name succession chain,
  2021–2024, filling the gap before the existing 2025-09 entry), `npts-elvis`
  (Семилетов А.Д., 2024-12-03 — this entity's **first-ever** director_history
  entry, filling a real gap).
- Flagged, not wired (documented in `notes` instead): two same-surname/
  given-name-but-different-patronymic collisions (`ao-nii-stt`,
  `ooo-zit-tsi-otraslevoy-tsentr-importozameshcheniya`) read as likely
  transcription/OCR errors, not new people — per this project's standing
  OCR-consistency discipline; and one `npp-radar-mms` доверенность-holder
  correctly excluded as a non-officer representative.
- `government_contracts[]`: ₽620.85M across 4 previously-unwired contracts
  found via the new `delivery_place` field — 2 civilian regional-government
  IT contracts (`ooo-gaskar-integratsiya`, `ooo-gaskar-tekhnologii`,
  Krasnogorsk) and 2 notable ones: `ooo-zit-tsi-otraslevoy-tsentr-importozameshcheniya`
  doing vehicle-queue/border-crossing security infrastructure at Верхний
  Ларс (the Georgia crossing) for ФГКУ «Дирекция по строительству и
  эксплуатации объектов Росграницы» — the same federal customer that
  already has a confirmed ₽2.97bn contract with `ao-pmts-avangard` at the
  Хасан crossing (China/NK border). Worth a cross-entity note if this
  pattern (ЦБСТ-network entities separately contracted by Росгранстрой at
  different border crossings) gets pursued further.

### Still open

1. **The three big unreviewed institutes** in `clusters_new.md`:
   `ao-nii-vektor` (157 unwired cards), `ao-pmts-avangard` (87),
   `ao-nii-stt` (85). Not started — this is a real session's worth of work
   on its own, not a quick pass.
2. **A clean final housekeeping re-mine is still needed** to get the true
   post-fix signatory-diff/clusters report. The 2026-09-01 attempt
   (`python3 scripts/mine_zakupki.py --json --out /tmp/zakupki_report.md`)
   was run in the background here and got stuck — only 116/3076 files in
   1h43m before being killed — almost certainly OCR-fallback (`tesseract`)
   bottlenecking on a run of PDFs without a text layer. Per this project's
   own crawling-jobs/long-local-job discipline, this needs to run in the
   user's own terminal, watched live, not backgrounded again. If it's still
   crawling after a few minutes, interrupt it and note the last
   `[N/3076] <filename>` line — that pinpoints whether one specific file is
   the bottleneck (worth a targeted fix) or it's just broadly OCR-heavy
   (worth a `--depth scan`-only pass instead, or accepting the runtime).
3. `gk-rostekh` / `ao-tekhnodinamika` / `pao-bank-psb` clusters remain
   explicitly out of scope per the user's standing call (Rostec's own
   footprint only matters via specific resident ties, already covered).

## Full pipeline/evidence review + autonomous fixes (2026-09-02)

Full review requested and delivered (methods/sources/claims/evidence-strength
audit, plan status, index.html calibration). Findings and fixes below; see
chat log for the full review text.

**Findings, ranked:**
1. **PII sourcing gap (critical)** — CLAUDE.md's own PII policy requires a
   source_id on every identifying field; measured reality was DOB 6% sourced,
   birthplace 12%, address 24%, inn_personal 38%, 96/140 PII-carrying people
   with NO source at all. Evidence exists (18 RuPEP, 853 Aleph, 145
   OpenSanctions files archived) — this was a linkage failure, not a research
   gap.
2. **litigation[] empty except npts-elvis** despite 10 arbitration case
   numbers cited in index.html prose (all archived, s0014-s0042) — a Phase-4
   generator would have silently dropped all 10.
3. **73 uncommitted files**, 4 days since last commit.
4. **8 orphan entities** (manufacturer-tier) with neither `cbst_tie` nor
   `tier_basis` recorded, despite carrying real evidence elsewhere in their
   own record.
5. Checklist fields added 2026-08-25 never populated: `state_programs` (0),
   `domain_history` (0), `marketing_claims` (1 entity/3 items despite a
   standing memory instruction to capture this).

**Fixed autonomously this session (no user input needed):**
- Border-crossing count corrected 4→5 in index.html (Росморпорт maritime
  crossing was already documented in prose but the summary sentence still
  said four).
- `litigation[]` backfilled for ao-nii-stt: all 10 arbitration cases
  structured with case number/court/parties/amount/status/source_id, two
  correctly flagged as unconfirmed-parties (А40-168087/2019, А40-209485/2024)
  rather than asserted as FSB links.
- `tier_basis` written for all 8 orphan entities (alyaska, va-technologies,
  ooo-npo-kilovatt, ooo-radiofid-sistemy, 3 Тримикс-network ИП records,
  krams-brand-unresolved), grounded in each entity's own already-sourced
  data (sanctions designations, dossier citations, trademark records) — no
  new research, just distilling what was already on file.
- PII source-linkage pass (RuPEP batch): 13 people linked to their archived
  rupep.org profile (s2452-s2710) after verifying DOB/birthplace/ИНН match
  before linking. Caught and fixed one wrong unsourced DOB (olga-sokolova,
  1973-01-23 → corrected 1976-01-03, same person confirmed via exact
  personal-ИНН match to the RuPEP record). Correctly REJECTED linking a
  same-surname RuPEP record to mikhail-kuznetsov (different person — an MSU
  economist, not this registry's ОНФ executive — role/sanctions-regime
  mismatch caught before linking). DOB-sourced 6%→26%, birthplace 12%→81%,
  inn_personal 38%→48%. ~70 people remain PII-unsourced, mostly needing
  per-person verification against already-recorded `aleph_matches` (can't be
  bulk-linked — those matches are procurement/asset-declaration records, not
  necessarily documents that state DOB/address, so each needs its underlying
  document checked before linking, same discipline as the RuPEP batch).
- **Root-cause bug fixed in `extract_registry.py`**: the `people_add_entities`
  correction path unconditionally appended a new record and only repointed
  the lookup dict, leaving the original prose-derived record in the output
  list too — caused the two duplicate-person-slug warnings
  (sinelshchikov-andrey-valentinovich, saidov-adil-abukovich). Fixed to merge
  into the existing record (list fields concatenated without duplicating,
  notes appended, scalar/dict fields filled only where blank) instead of
  appending a second record. Verified: people count correctly dropped
  361→359 live, both merged records retain all data from both sources.
- **`check_registry.py` warning-noise fix**: 546 of 549 total warnings were
  the same "identical file content" class, almost all zakupki.gov.ru serving
  one attachment under multiple filenames (expected, benign) — this was
  burying the 3 warnings that actually needed a human look. Collapsed the
  zakupki-attachment case to one summary line (full path list still
  included, just not one warning line each) and kept non-zakupki duplicates
  as individually-flagged warnings. Total warning count: 549 → 9, of which 7
  are now real (small, genuinely worth a glance) non-zakupki duplicate-file
  cases and 27 (now visible instead of buried) unsourced history-entry
  placeholders.

**Left for user judgment, not attempted autonomously:**
- Committing the 73 uncommitted files — CLAUDE.md's own git policy requires
  an explicit user request, not inferred from "fix what you can."
- Remaining ~70 PII-unsourced people (Aleph-match verification, one person
  at a time — real work, not mechanical).
- Whether to restructure index.html's opening around the Ushkuynik SVO
  contract (currently documented in full but mid-paragraph, not in an
  opening/hook position) — blocked on the still-undecided Phase 1 §1 hook
  section (Russian draft sitting in an Artifact preview, not yet approved).
- `state_programs[]`/`domain_history[]`/`marketing_claims[]` population —
  needs actual research passes, not just registry hygiene.

---

## Гагаринг network deep-dive (started 2026-09-03)

User request: apply the same wide-net rigor just used on the Ushkuynik
network (via smolin.info's dossiers) to Гагаринг — explore all connections,
all linked companies/POI, identify what other sources/methods to bring to
bear. Full plan drafted in plan mode and approved 2026-09-03; kept in full
at `~/.claude/plans/spicy-beaming-kite.md` per the redirect note at the top
of this file (that external path is where plan-mode drafts land — this
section is the durable summary/tracker).

**Pre-existing state (survey, 2026-09-03):** Гагаринг itself is not thin —
`ooo-gagaring` (ИНН 2312321660) has a 55-page audited FY2025 financials
filing, Fedresurs corroboration, ~₽2.16bn revenue, and the training center
(`ano-dpo-obrazovatelny-tsentr-gagaring`, ИНН 2310240630) has a
licence-registry-confirmed address (ул. Цезаря Куникова 24к2, Краснодар).
~73 sources already wired. The real gap is the network around it:

- **The "Архангел" brand-name collision problem** — at least 6 distinct
  orgs now on record sharing the name, only 2 with registry entries:
  `ano-arkhangel` (Архангел Легион, ИНН 2315233718, rusprofile-only so
  far), «Архангел Спецназа» (@arx_spn, no legal entity ID'd), «проект
  Архангel»/Филиппов М.Г. (parked in memory), `ooo-arkhangel` (EU-sanctioned
  ЦБСТ resident, ИНН 9714079108, already confirmed unrelated to the
  others), ООО «Архангел» ИНН 9500026652 (Zaporizhzhia/Kalashnikov, sources
  exist, no entity record), ООО «Архангел» ИНН 5032379630 (Odintsovo/
  Wagner, barely developed). Disambiguating this is the single highest-
  value task.
- Two open training-center-location sub-threads: which building/unit at
  Гагаринг's own Одесская 48/3, Краснодар обособленное подразделение
  (23-building industrial complex, one candidate "Производственный
  корпус" 1972), and whether Туапсе's «школа Архангел» is the same site as
  the 51st Army training-center relationship or separate.
- Named individuals never promoted to `people.json`: Безроднова А.С.
  (training-center director), Архангельский Г.Е. + Ташматов И.С. (Архангел
  Легион), Филиппов М.Г. (проект Архангел), Сиразатдинов Н.В. + Климов
  М.А. (АРРС co-founders), Шатракова А.А. (sanctioned ooo-arkhangel).
- Unmined local Telegram DB leads: a second training-center operator
  («Пианист»/УЦ «Шершень»), a possible Kursk-region lab distinct from the
  Krasnodar HQ, a Sevastopol training trip, named 51st Army recruitment
  contacts (Галушко/Dark_GAA), and a `potapov_npp` video interview with
  Барашков.
- EGRUL/БФО gaps: `ano-arkhangel` and the training center both rest on
  open-API/aggregator sourcing only; two archived-but-unread устав zips;
  the OSINT Bees «проект Архангел» capture (s0234/s0235) is still
  underexploited; НПО Эйлер (Tula, 50%-owned by Гагаринг) already flagged
  in its own record as high-priority for a deeper pull.

No `smolin.info`-equivalent dossier source exists for Гагаринг in this
repo — unlike Ushkuynik, that specific technique is new ground here.
checko.ru, myrotvorets.center and sudrf.ru are likewise not yet integrated
anywhere in this project; worth trying as single inline lookups.

**Execution discipline**: single EGRUL/checko.ru/myrotvorets/sudrf.ru
lookups, single Telegram post reads, and single `screen_*.py --slug X`
calls run inline; any full-roster batch pull is handed to the user as an
exact command, never backgrounded — same split as every prior session.
New entities via `corrections_entities.json`, new people via
`corrections_people.json`; PII stays null without a source; disambiguation
between same-named entities gets written explicitly, never silently
merged.

**Deliverable**: a `notes/gagaring_network_map.md` sibling to
`notes/smolin_source_catalogue.md`, summarizing the resolved Архангел-
family relationship map — this is the concrete "same wide-net rigor" ask.

**Status (2026-09-03): substantially DONE.** All threads worked:

- **Архангел-family disambiguation (A)**: 2 of 6 orgs promoted to full
  entity records (`ooo-arkhangel-zaporizhzhie`, `ooo-arkhangel-tsentr`);
  fresh EGRUL confirmations on `ano-arkhangel`/training center; checko.ru
  and myrotvorets.center tried on the remaining 2 undocumented brands
  (both negative/blocked). **Headline finding**: `ooo-arkhangel-tsentr` is
  already sanctioned across 6 jurisdictions (EU/UA/FR/CH/BE/MC) — found via
  a single OpenSanctions batch call, previously only a thin
  Wagner-branding-unverified stub. GUR also confirmed
  `ooo-arkhangel-zaporizhzhie` is a 20-city national training network, not
  a single Melitopol operator.
- **Training-center location (B)**: Туапсе confirmed as a separate visited
  site, not the same facility. Одесская 48/3 building-pin attempt came back
  negative (public directory search, inconclusive).
- **Named individuals (C)**: 7 new people promoted (Безроднова, 2×
  Архангел-Легион founders, Филиппов, 2× 51st-Army recruitment contacts,
  Тимофеев+Кусумов for entity #5) + 2 misattributed АРРС founder roles
  fixed.
- **Telegram DB leads (D)**: Sevastopol training site, Kursk-lab open
  question, УЦ «Шершень» cooperation, personal Чадаев–Барашков tie.
- **EGRUL/устав gaps (E)**: fresh extracts pulled; устав OCR surfaced a
  sole-founder-at-inception fact and state-secret/education activity
  clauses; full-text-mined the previously-skimmed OSINT Bees dossier
  (resolved Филиппов's unsourced DOB).
- **НПО Эйлер (F)**: negative-result pull (no БФО yet, no zakupki hits) —
  documented, not left unchecked.
- **Screening (G)**: GUR + OpenSanctions run inline (single-lookup/small-
  batch, not full-roster) against the new roster.

Deliverable written: `notes/gagaring_network_map.md`. Not done: full EGRUL
extracts (vs. open-API summaries) for entities #5/#6, and no legal entity
ever identified for «Архангел Спецназа» (#2) or confirmed for «проект
Архангел» (#3) — left as genuinely open, not chased further this pass.

### Continuation (2026-09-04)

Four more sessions' worth of work on the same network, all folded into
`notes/gagaring_network_map.md` and `CLAUDE.md` rather than kept here:

- **Krasnodar-krai regional registries** — SME-registry exclusion event
  and a hackathon-sponsor tie found for Гагаринг (see the entity's own
  `open_questions[]`).
- **A fourth Гагаринг office** (ул. Красная 176/5, sales/legal) and a ГОЗ
  self-admission found via hh.ru job postings — a new source type for this
  project.
- **POI-wide ЕГРИП/ИП sweep** — every one of 126 people-of-interest with a
  personal ИНН checked against egrul.nalog.ru's open ЕГРИП search
  (`scripts/screen_egrip_ip.py`, new script). Caught and fixed a real
  undercount bug (filtering on `tot` instead of `k=="fl" and o`) that had
  silently dropped every 2nd+ ИП registration for anyone with multiple —
  re-ran with `--force` after the fix, recovering 13 registrations (53→66
  total across 53 people). Along the way, discovered and documented
  rusprofile.ru's anti-scraping decoy-content behavior (see the seeded
  memory `rusprofile_ru_decoy_content_anti_scraping`) — its gated
  procurement/status widgets return randomized OTHER people's data to
  repeat/bot traffic while the `<title>` tag stays accurate; nearly let a
  fabricated "3rd government contract" for an already-confirmed principal
  (Цыганов) into the registry before catching it.
- **Screening-gap closure** — audited every known screening mechanism
  (GUR, Aleph, OpenSanctions, rk2035, ФНС «Прозрачный бизнес») against the
  9 Гагаринг-network entities + 3 key principals, found and closed the
  real gaps (GUR had never been run against ANY person — no batch script
  exists, so this used `screen_gur.py`'s internal functions directly per-
  person). The ФНС director/founder cross-reference
  (`scripts/screen_upr_uchr.py`, new) was the productive one: surfaced
  pre-Гагаринг СДЭК ties (ООО «СДЭК Рекоммерс», ООО «СДЭК-Европа») and a
  charitable fund (Игры вдолгую) for Барашков, and a new entity for Бегак
  (НП «Дискретно-инновационный кластер малой авиации», added to
  `entities.json`). Куртеев came back clean everywhere — reinforces the
  existing suspicion his Гагаринг-role attribution is spurious.
- **Open web search + postal-code verification** — a TASS-quoted
  Volkswagen-engineer recruitment episode and Гагаринг's own Telegram
  posts on the same campaign (explicit "sanctions backfired" framing)
  captured into `marketing_claims[]`; a self-submitted press release
  (re-port.ru) claims Барашков is assistant to State Duma deputy Vladislav
  Даванков — recorded as an open question, NOT independently confirmed.
  Resolved a standing postal-code discrepancy for the legal HQ (350912 is
  correct per public index directories; 350312 was a Роскомнадзор filing
  typo, not a competing valid code) and confirmed the new Красная 176/5
  office's own postal code (350020).

Still open from the original pass: full EGRUL for Архангел entities #5/#6,
«Архангел Спецназа»/«проект Архангел» legal-entity ID, Barashkov's
`screen_disqualified.py` check (returned HTTP 400, inconclusive — retry),
the private Archangel chat (zero scraped message content, only 3/many
members catalogued — commands handed to user, not yet run), НПО Эйлер deep
dive, the Одесская 48/3 building pin.

## New licensing-registry screeners + NSPD reliability finding (2026-09-06/07)

Six new registries reverse-engineered and scripted this pass, all now
tracked in `notes/SOURCE_REGISTER.md` (#59-65): RKN comms-license and
frequency-assignment registries (`screen_rkn_comms_license.py`,
`screen_rkn_frequency_registry.py` — both needed the full param set a real
form submit sends, not just the obvious fields, or the server silently
returns the unchanged default page instead of erroring), a fixed
`screen_mchs_fire_licenses.py` (HTML-entity decode bug), Roscosmos
licences, favt.gov.ru aviation operators, and all 5 Rosgvardia licence
registries. Full-roster sweeps run clean: 5 RKN comms-license hits + 5 RKN
frequency hits wired into `licences[]` via `corrections_entities.json`
(large batches condensed with a note rather than itemized in full, same
precedent as `npp-radar-mms`'s earlier 24-record RKN batch); МЧС/Roscosmos/
favt/Rosgvardia hits reviewed and found to be either already-known/wired
duplicates or clean negatives — no new leads. Ten company profiles rebuilt
and tag-balance-checked for the entities touched by the wiring.

**NSPD (nspd.gov.ru) downgraded from "promote toward Tier B" to a firm,
documented Tier B with an honest reliability caveat.** A single curl with a
full browser-header set got one real 200 (confirmed the exact building
inventory at Гагаринг's Одесская 48/3 production site — already documented
2026-09-03/04, not a new finding, just re-confirmed), but every retry
after that 403'd, from both this sandbox's egress AND the user's own home
network (confirmed running a 152-entity address sweep). This is a strictly
worse case than fedresurs.ru's sandbox-only block — no network tested so
far reliably passes NSPD's WAF via curl, only a real chrome-devtools
browser session has never failed. `scripts/nspd_lookup.py` (single-query)
and `scripts/screen_nspd_addresses.py` (batch, built but should not be
handed to the user again as a full sweep) both exist for when curl does
work.

**Process notes, both now saved as feedback memories:**
- The NSPD reverse-engineering above was **largely redundant** — the same
  endpoint, the same WAF-vs-browser finding, and the same Одесская 48/3
  building inventory were already fully documented in
  `notes/gagaring_network_map.md` (2026-09-03/04). Grep `notes/*.md` for a
  target before starting a fresh registry/facility dive.
- The `/deep-research` Workflow was invoked twice this session and both
  times cost far more than the direct alternative (WebSearch/WebFetch/curl)
  would have — one run hit the account's monthly spend limit mid-flight,
  the other's final synthesis step returned literal `"test"` placeholder
  content instead of a real report (findings had to be reconstructed by
  hand from the workflow's own journal, written up in
  `notes/deep_research_registries_20260906.md`). Default to direct research
  tools for this kind of open-ended discovery question going forward.

## Registry hardening: correction-key collision now a build check (2026-09-07)

Closed the open item from the 2026-09-07 БФО/EGRUL-выписка session
("a full audit of `corrections_entities.json` for ИНН/slug key pairs
targeting the same entity is still open, not done this pass") by making
`check_registry.py` detect the class directly instead of relying on
someone noticing by hand next time. For every `entities{}`/`people{}` key
in `corrections_entities.json`/`corrections_people.json`, it resolves the
key (slug or ИНН/inn_personal) to the live record it targets and flags any
record with more than one correction key pointing at it. **ERROR** (fails
the build) if the two `set` blocks share an overlapping field — that's the
mechanism that silently drops one side's value, "whichever key is
processed last wins" — versus **warning** (dormant risk, not yet
corrupting anything) when the keys collide but don't yet overlap on a
field.

First run found 43 colliding pairs. 6 had an active field overlap and were
genuinely dropping data — merged (union for array fields by content,
gap-fill for everything else, both `why[]` histories preserved) and
re-verified with a full before/after field-size diff (0 shrinkages). The
biggest recovery: `ano-arkhangel`'s ИНН-keyed correction entry had been
silently overwritten and was carrying address, director_history, founders,
founders_history, financials and ОКВЭД that the live registry hadn't had
since whenever the collision was introduced — all recovered. The other 37
pairs have no field overlap today (dormant — safe until a future edit to
either key introduces one) and are left as `check_registry.py` warnings, a
concrete work list rather than a vague "should audit sometime":

```
ooo-tsyus, ooo-opkb-eksplomet, ooo-akr-begak, ooo-aero-khit,
ooo-sibirskaya-navigatsionnaya-kompaniya, ooo-prommash,
ooo-sistemnyy-integrator, kolskaya-verf, ooo-stratim, ooo-atlant-aero,
ooo-vozdushnyy-traktat, ooo-skb-piranya, ano-platforma-nti, ao-ross,
gk-rostekh, zao-kurskpromteplitsa, ao-aeromaks, ao-ekolibri,
ao-tekhnodinamika, ao-stratim, ooo-gaskar-integratsiya,
ao-korporatsiya-sinergiya, ao-uk-smart, ooo-trimiks-bulat-3mx,
ooo-ayaks-tekhnologii, npp-elvo-kolskaya-verf, ao-kotlin-novator,
npp-radar-mms, ooo-spdbbk, ooo-krams,
ano-tsbst-centre-for-unmanned-systems-technologies, ao-tekhnodron,
ao-aurin, ao-prominvest, ao-ploshchad, ooo-kingpro, ooo-tsugam
```

Merge these opportunistically whenever touching one of these records for
other reasons, or in a dedicated pass — not urgent (no active data loss),
but each is one bad future edit away from becoming one, and the merge
itself is cheap (the pattern above, or reuse `resolve_key()` from either
of this session's `apply_bfo.py`/`apply_egrul_vypiska.py` scratch scripts
for any future correction-writing script instead of introducing a new
colliding key).

## Phase 3.5 item 2, second half closed: guarded-enum downgrade check (2026-09-07)

Closed the part of item 2 explicitly left open in its original write-up:
"Catching that class needs either a diff-against-previous-run check or an
explicit 'downgrade requires justification' rule — not built yet." Added
to `check_registry.py`: for a small `GUARDED_ENUM_RANK` table (currently
just `wb_overlap`, the field the original Тримикс regression happened on;
extend it if another field earns the same treatment), every entity's
current value is compared against the last **committed** value (`git show
HEAD:data/registry/entities.json`) and any transition ranked as a downgrade
(`confirmed_direct`/`confirmed_reseller` -> `none_found` -> `not_checked`)
is flagged.

First attempt tried to auto-suppress the warning when a correction's
`why[]` note already mentions the field name — tested against a simulated
re-injection of the actual Тримикс bug (`wb_overlap` flipped back to
`none_found`) and it **failed to fire**, because this exact entity already
carries a `why` note mentioning `wb_overlap` from the *original* 2026-08-25
fix, which the naive substring search matched and treated as blanket
permission forever. That's worse than not having the check — a guard that
can be silently defeated by an old, unrelated note is a false sense of
safety. Simplified to always warn on a guarded-field downgrade and let a
human eyeball the one line above it; re-tested against the same simulated
regression and it now fires correctly, and is silent against the real
current (clean) state. Restored `entities.json` after the test — no
lasting change from the simulation, only the check itself is new.

## Dormant correction-key collisions closed (2026-09-07)

Merged all 37 (36 distinct) dormant pairs listed above, same union/
gap-fill pattern used on the 6 active ones. `check_registry.py`'s
correction-key-collision detector now finds zero instances of any kind
(active or dormant) — the whole bug class flagged this session is fully
closed, not just the urgent half of it. Notable recoveries where the
dormant ИНН-keyed twin had real data the live slug had never surfaced:
`ao-stratim` (director/financials/name_ru/ogrn/products/registered/
related_entities/tier), `ooo-sistemnyy-integrator` (`_verified`/address/
charter_capital+history/director+history/financials/founders+history/
ogrn/okved/parents/registered/tier+basis), `ano-tsbst-centre-for-
unmanned-systems-technologies` (`_verified`/address+history/
director+history/founders+history/name_latin/okved/tier+basis). 0
field-size shrinkages verified against pre-merge git HEAD; 37 profiles
rebuilt, 182/182 tag-balance clean. This closes Phase 3.5 item covering
correction-key integrity entirely.

## Founding-document coverage audit + small-batch screening sweeps (2026-09-07)

Separate thread from the registry-hardening work above — see
`notes/SOURCE_REGISTER.md`'s matching 2026-09-07 entry for full detail:
`notes/founding_docs_gap.md` (135-entity founding-doc gap list with
ОГРН/ИНН, for manual ФНС pulls), plus zakupki/RNP/Aleph/GUR/WB catch-up
sweeps on every small (single-digit to low-double-digit) still-unscreened
record, and the orphan-role-link review closing 2 of 33 remaining gaps
(Бровченко, Устратов). Two new leads surfaced needing further research,
not yet promoted: Богатиков С.А. (ГК Аэромакс director) is also director
of АО «ГосМКБ «Радуга» им. А.Я. Березняка» (state missile design bureau);
Шестопалов С.А. founds/directs 3 newly-registered Липецк electronics/
antenna R&D firms.

## Plan: НСПД facility investigation for proverki-discovered addresses (2026-09-07)

`notes/proverki_findings.md` (this session) surfaced several physical
facilities not previously on file, via proverki.gov.ru's
`object_address` field on inspection records. `scripts/nspd_lookup.py` +
`scripts/screen_nspd_addresses.py` (built 2026-09-06, see
`notes/gagaring_network_map.md` for the technique's first real use on
Гагаринг's own addresses) are the right tool to corroborate these:
existence, scale, declared building use, construction year, and
ownership/right type (not owner identity — Rosreestr redacts that
post-2017). Each single-address lookup is ordinary inline reconnaissance
under CLAUDE.md's crawling-jobs policy — fine to run directly; only a
full-roster batch needs handing to the user.

**Reliability caveat already documented in the scripts**: nspd.gov.ru's
WAF 403s this sandbox's curl in bursts even with full browser headers,
while a chrome-devtools browser session has not failed once on the same
queries. Treat an ERROR run as "retry later or fall back to
chrome-devtools," not proof of no record.

### Priority queue (highest-signal first)

1. **npp-radar-mms — дер. Хаболово cadastral parcels (КН
   47:20:0442001:212, КН 47:20:0442001:209)**. Exact cadastral numbers
   already in hand — this is a precise single-record lookup, not a
   fuzzy address geocode, so should return a clean building/parcel record
   if the WAF cooperates. Top priority: this is the one open question
   explicitly flagged on the entity record (radar company, unexplained
   land far from its SPb HQ). Command:
   `python3 scripts/nspd_lookup.py --query "47:20:0442001:212"` (and
   `:209`).
2. **npp-radar-mms — Новосельковская ул., д.46, лит.А**
   (the "Строительство производственно-складского корпуса" record) —
   confirm current construction status/declared purpose against НСПД's
   own building-name field, same technique that identified Гагаринг's
   Краснодар "Производственный корпус."
3. **ao-nii-vektor — ул. Маршала Новикова, д.40, лит.А** (also an active-
   construction record) and **Кантемировская ул., д.10** (the record's
   own "фактического осуществления деятельности" address) — corroborate
   both against НСПД, since the source itself already distinguishes
   registered vs. operating address here.
4. **ooo-aeromaks's three non-matching facility addresses** (Милютинский
   13, Андропова 18к9, Малый пр. В.О. 54к5) — lower priority than the
   above (no defense-radar/land-use ambiguity), but worth a quick batch
   since none match the registered legal address at all.
5. **npts-elvis's second Zeleongrad site** (проезд 4922-й, д.4, стр.2)
   and **ao-kotlin-novator's two SPb clusters** (Глиняная 5/11, Обводного
   канала 14) — lowest priority of this batch, routine corroboration.

**Explicitly out of scope for now**: ao-pmts-avangard's Волгоград site —
per `notes/proverki_findings.md`, this entity has no confirmed ЦБСТ/UAV
tie, so an НСПД pull isn't worth the turn unless that changes.

### Execution discipline

Same as every prior registry write this session: any real НСПД hit gets
wired to the entity's `facility_type`/`facility_type_history` (not
`address_history`, which already holds the address itself) via
`corrections_entities.json`, with the actual `source_id` from an archived
`NSPD_<cadastral-or-address-slug>_<YYYYMMDD>_<slug>.json` (or `.txt` for a
chrome-devtools capture) file in `data/sources/` — never a placeholder.
Run `inventory_sources.py` → `scan_sources.py` → `extract_registry.py` →
`check_registry.py` (0 errors) → the field-size-shrinkage diff before
committing, same as every other write this session. Update
`notes/proverki_findings.md`'s per-entity sections to note НСПД
corroboration once done, so the two logs stay in sync.

**Done 2026-09-07.** Ran 16 lookups via chrome-devtools fetch (curl 403'd
as expected from this sandbox's IP). Headline result: the Хаболово
cadastral parcel (КН :212) that looked like a possible undisclosed
test-range/antenna-field lead turned out to be a 1,530 m² private
RESIDENTIAL land plot — deflates that open question rather than
resolving it toward something notable; recorded as RESOLVED on the
entity record rather than left open. Second finding: ООО «Гаскар»'s
Пехорская 1Д facility ("Корпус 9", 15,506.8 m², built 2022) sits in the
same Косино-Ухтомский municipal district as ООО «НПО «Рустехдрон»»'s
Пехорская 1/3 site — upgrades the "possible shared-cluster" note on both
entities to a confirmed same-district finding. Everything else was
routine corroboration (real building exists / matches "actual operating
address" claim) or a clean non-find (address not yet in Rosreestr,
consistent with active-construction status already noted from proverki).
No further facility_type changes warranted — none of the corroborated
buildings changed an entity's existing facility_type classification, so
this closed as notes-only additions rather than facility_type_history
entries. See `notes/proverki_findings.md` for the per-entity detail.

## Хутешен А.А. / Атлант Аэро network expansion (2026-09-07)

`screen_upr_uchr.py` on Хутешен Алексей Александрович (ЦКБР's sanctioned
chief designer, already known as ООО «Атлант Аэро»'s director) returned 14
director/founder ties, not just the one Атлант Аэро role already on file.
Pulled full EGRUL выписки (not just the ФНС search-proc summary) for every
new ИНН, and added the whole cluster to the registry:

- **ooo-prometey** (manufacturer tier) — a second, brand-new (05.06.2026)
  Таганрог aircraft manufacturer. Shares founder Шевченко К.И. with Атлант
  Аэро — a real corporate link between two same-city aircraft makers.
- **ooo-npk-atlant-aero** (manufacturer tier) — a direct sibling to Атлант
  Аэро, registered 12 days earlier, same Хутешен/Шевченко ownership,
  ОКВЭД "Ремонт металлоизделий" (plausible airframe-repair adjunct).
- **7 supporting entities** (adjacent tier): ооо Атлант Сервис/Атлант
  Логистик/Пром-Тех/НПК Зевс, АО Оптические Системы, ООО Аметист/Эверест,
  ООО ПК Стальной Купол, plus ООО «ДС-БАРС-Т» (Прометей's pre-existing
  24% corporate founder). Two structural patterns worth flagging: three
  entities share one registered mail-drop address (б-р Яна Райниса 41,
  Южное Тушино) — a mass-registration signature — and Аметист/Эверест
  share the same director (Беленкова А.Е.), a nominee-director pattern.
  Пром-Тех carries an unexplained ФНС "недостоверность сведений" flag
  (05.06.2025).
- 8 new named individuals added to `people.json` (Призов, Филатов,
  Русецкий, Лымарь, Савченко, Беленкова, Коцеруба, Степанов) — all
  disqualification-screened, 0 hits. Director/founder cross-reference,
  subsidiary-liability, and ЕГРИП screens NOT yet run on any of them
  (only the disqualification check ran this pass) — do that next before
  calling this network's screening complete.

**Update 2026-09-08.** Ran `screen_upr_uchr.py`/`screen_subsidiary.py`/
`screen_egrip_ip.py` on all 8. Subsidiary-liability: 0 hits across the
board. Director/founder cross-reference mostly just confirmed the
already-known tie, EXCEPT **Степанов Валерий Юрьевич** (ДС-БАРС-Т's
director), who turned up 4 more companies: ООО «ДС-Проект» and ООО
«Проектное бюро 74» (both generic real-estate holding, not added) and —
the real find — **ООО ИК «АВИАОК»** (ИНН 6154569246), which he directs
and wholly owns. Unlike everything else in this cluster, АВИАОК declares
a genuine communications/radio-electronics-equipment OKVED block
(26.30.11–26.30.19), not just real-estate/wholesale codes — added to the
registry as `ooo-ik-aviaok` (manufacturer tier). Long-standing entity
(founded 2011), no EGRUL restriction flags. ЕГРИП found active ИП
registrations for Филатов, Лымарь, and Коцеруба (not detail-checked —
low priority, proportionality).

**Still not done, next steps if this thread continues:**
1. OpenSanctions/Aleph screen the now-9 new people (never run).
2. zakupki scan on the three manufacturer-tier additions (Прометей, НПК
   Атлант Аэро, АВИАОК) — АВИАОК is old enough (2011) to plausibly have
   government-contract history, worth checking first.
3. АВИАОК needs the standard verification pass this registry requires
   before treating it as more than a lead: БФО pull (old enough to have
   filings, unlike the other new entities), a press/website/VK/TG check
   for an actual product line, zakupki.
4. A БФО pull on the rest of the cluster will find nothing yet (all
   <3 years old, most founded within the last year) — skip until a
   filing is actually due.
5. НСПД check on the shared Южное Тушино mail-drop address (б-р Яна
   Райниса 41), to confirm/characterize what that address actually is.
6. Consider whether Пром-Тех's недостоверность flag is worth a closer
   EGRUL record-history read to identify which field was flagged.

**Update 2026-09-08 — items 1-6 above all closed.** НСПД confirmed б-р
Яна Райниса 41 (АО Оптические Системы/ООО Аметист/ООО ПК Стальной Купол)
is an ordinary residential building, not a distinct commercial mail-drop
of interest — noted on all three, no further action. Read Пром-Тех's full
EGRUL change-log sequence and resolved the недостоверность flag to its
registered-address field specifically (already re-confirmed current by a
later filing). OpenSanctions/Aleph screened all 9 cluster people: only
generic EGRUL-derived `ru-inn-` entries, no sanction/PEP topics on any of
them. zakupki scans: 0 hits across Прометей, НПК Атлант Аэро and АВИАОК
(all `zakupki_review: closed`, recorded per-entity). АВИАОК's БФО pull
found no filings on record despite its 2011 founding — flagged, not yet
explained (possible lapsed disclosure, same pattern seen elsewhere in this
network, or a filing that predates bo.nalog.gov.ru's coverage window).

Two further leads surfaced from a fresh `screen_upr_uchr.py` pass over
the whole ~155-person unverified-people roster with a personal ИНН
(started 2026-09-07, ran to 131/149 before the pb.nalog.ru captcha wall,
resumed 2026-09-08 for the remaining 24 — every record with an ИНН is now
checked at least once, no backlog remains):

- **ООО «Сельскохозяйственные беспилотные системы «МИРА»»**
  (`ooo-selskohozyaystvennye-bespilotnye-sistemy-mira`, ИНН 7804712459) —
  a 3rd corporate tie for Кобзев Виктор Викторович (35% founder,
  23.07.2026), already known via Прометей/РИБЭКС. Registered as generic
  agricultural-equipment wholesale (ОКВЭД 46.61) in Dec 2024, then added
  ОКВЭД 30.30.6 "Производство беспилотных авиационных систем" seven
  months later (17.07.2026) — the same declared-purpose-drift pattern
  already documented elsewhere in this registry. НСПД-confirmed real
  small office suite (not another mail-drop). zakupki: 0 hits, too young
  to plausibly have contract history yet (`zakupki_review: closed`).
- **АО «РТИ-Радио»** (`ao-rti-radio`, ИНН 7713133550) — surfaced via
  Бессонов Сергей Николаевич (already known as ООО «Аэромакс»'s
  director), installed as this entity's GD 19.02.2026, six days after
  ООО «Группа компаний «Аэромакс»» acquired 100% (13.02.2025). Initially
  characterized as a real manufacturer (long-established 1997, genuine
  radar/radionavigation OKVED matching АО «НПП «Радар ММС»») — **corrected
  same day** after pulling and reading all 5 available БФО filings
  (FY2021–2025): fixed assets have shrunk to ₽16,000, inventory is zero
  in every year, real product-sales revenue peaked at ~₽1m in FY2021, and
  net losses since FY2023 run into the billions of rubles (-₽8.04bn
  FY2025), driven by non-cash provisioning charges, not operating costs
  — this is a dormant financial shell wearing an old manufacturing OKVED,
  not evidence of active production. The Аэромакс-acquisition fact
  itself still stands. Also ruled out a name-collision tie to the much
  larger Ростех/АФК «Система»-adjacent «Концерн «РТИ Системы»» group
  (separate ИНН, no ownership link found) and confirmed no subsidiaries
  of its own.
- Киселёв Глеб Дмитриевич — not a new corporate tie, but a
  characterization fix at the user's direction: he's both PEP-adjacent
  (son of Дмитрий Киселёв) AND a defense-industry figure in his own
  right via «Кулибин-клуб» (835 designs tested, 195 accepted by MoD,
  220,000+ units delivered per his own ONF-roundtable statements,
  s0560), plus a since-exited 2016-2019 10% stake in ООО «Агрофирма
  «Таврида»» (RuPEP, s7344).
- ЦКБР scaffold gap closed 2026-09-08: the entity existed in the
  registry (table-scaffolded from prose) but had no ИНН/founders/director
  filled in. Pulled a full EGRUL выписка directly — confirms the founders
  list already on file for co-founder/chief-designer Кузякин Д.В. (25%,
  individually EU/UA/CH-sanctioned) and adds a GD succession not
  previously recorded (Кузякин -> Косолапов О.Ю., 20.05.2025).

Group-1 unverified-people refresh (`other_entities_checked_at`) is now
fully current for every person carrying a personal ИНН — no backlog
remains from this thread.

## Гагаринг wide-net deep-dive (started 2026-09-08)

Picking up the parked plan at `~/.claude/plans/spicy-beaming-kite.md` at
the user's direction. **Finding on opening this thread: the plan itself is
largely stale.** `notes/gagaring_network_map.md` (604 lines) and
`notes/archangel_adjacent_network.md` (now ~230 lines) already document an
enormous amount of work done 2026-09-03 through -07 — full-corpus channel
reads (65k+ posts scanned across the Архангел-family channels alone),
independent press corroboration of the Kalashnikov MOU/serial-production
tie, EGRUL pulls for nearly every entity in the family (now 11 distinct
«Архангел»-branded records, not the plan's estimated 6), and most of
threads A/D/E/G already substantially closed. Rather than re-executing the
stale plan, spent this pass closing the concrete gaps that were still
genuinely open on top of that existing work:

- **`ooo-arkhangel-melitopol-2`**: the "why do two Архангел entities share
  one Melitopol address" open question had a БФО pull sitting unread in
  `data/sources/` since 2026-09-05 (s5532/s5533) — read it: zero revenue
  both FY2024 and FY2025, confirming the dormant-second-vehicle
  hypothesis. Question closed.
- **`ooo-arkhangel-crimea`**: same situation, one unread БФО filing
  (s5534) — zero revenue in its first (FY2025) filing, ₽3.1m charter
  capital paid in kind not cash. Doesn't fully resolve the
  agriculture-vs-training question (no revenue exists yet to tag either
  way) but rules out "currently operating" as the state — noted.
- **Черезов Андрей Павлович** (director of `ovod`/`ooo-vozdushnyy-traktat`,
  the Tula «Овод» maker who survived a 2026-07-29 assassination attempt,
  already extensively documented in `gagaring_network_map.md`'s own
  "ovod" section) had no personal ИНН despite an EGRUL extract for `ovod`
  already on file since 2026-09-07 — found there (712802968839),
  unexploited. Now on his people.json record.
- **«Открытое небо»** (Lytkarino cert-issuing front company for Проект
  Архангел's pilot school, per iStories) — attempted an EGRUL name search;
  20 same-named candidates nationwide, none clearly identifiable as the
  Lytkarino one by region field alone. Genuinely unresolved, left open —
  would need a per-candidate address check.
- Reconciled `notes/archangel_adjacent_network.md`, which only documented
  6 of the now-11 «Архангел»-branded entities — added a summary section
  for the 5 it was missing (`ooo-arkhangel-shchit/-grupp/-istra/
  -melitopol-2/-crimea`, `proekt-kb-arkhangel`) pointing to each entity's
  own much more detailed `open_questions[]` rather than re-deriving it.

**Genuinely still open, not attempted this pass** (real next steps if this
thread continues, roughly in order of tractability):
1. Кулемин Игорь Александрович / Хабибулин Владимир Игоревич
   (`ooo-arkhangel-shchit`'s owner/director) — both have an ИНН but no
   DOB/address; would need a RuPEP or similar deep-dive.
2. «Открытое небо» — resolve which of the 20 same-named candidates is the
   Lytkarino one (per-candidate EGRUL address pull).
3. «Ворон-оптоволокно» — no ИНН/entity resolved yet despite a confirmed
   direct founder-to-founder relationship with Проект «Архангел».
4. `tg-arkhangel-spetsnaza` (@arx_spn, 1.02M subs) — still no legal
   entity identified; checko.ru/myrotvorets untried per the original
   plan.
5. The plan's threads B/C/F (Одесская 48/3 building ID, Курская/Sevastopol
   location confirmation, НПО Эйлер deep-dive) — not touched this pass,
   still open per `gagaring_network_map.md`'s own "what's still open"
   section.

## Hub Insignia — presentation-layer design exploration (2026-09-08)

**Not part of the registry rebuild above** — flagged here only so a future
session doesn't rediscover it from scratch or mistake it for registry work.
A standalone mockup artifact, built and iterated in-session at user
direction, exploring a classification-mark/icon system for the live
Network Graph's cluster hubs (offensive/defensive/dual-use manufacturer
type, plus hub-site type and drone-platform-type variants). Full revision
log and visual-semiotics research (Peirce icon/index/symbol, Neurath's
Isotype, ISO 7001, ANSI Z535/GHS) in `notes/hub_insignia_design_notes.md`.
Published at https://claude.ai/code/artifact/8bed5183-6ced-4df0-8c2d-8a4352ceaacd.

**Update 2026-09-08, same day: wired into the live Network Graph**, at
user direction. The dagger/shield/shield+dagger glyph system now renders
on hub nodes in https://claude.ai/code/artifact/0e402553-a22e-4427-a3a9-c5b0251bdaa2 —
`build_relationship_graph.py` gained a `classify_variant()` keyword
heuristic over `products[]` text (24/207 entities classified: 14
defensive, 7 offensive, 3 dual), logged as a presentation read, not a
sourced registry field, same caveat the mockup carried, now surfaced in
the graph's own sidebar legend too. Full detail in
`notes/hub_insignia_design_notes.md`'s "v3" entry. Nothing here touches
`entities.json`'s schema or gates any phase above — the `variant` field
lives only in the derived `data/registry/relationship_graph.json`, not
the source-of-truth registry files.

**Update 2026-09-08, later same day: extended to all node/edge types
("v4")**, at user direction to keep researching visual semiotics and
apply it beyond hubs. Researched Bertin's visual variables and POLE/
link-analysis link-chart conventions (i2 Analyst's Notebook genre — the
one this graph actually belongs to); full citations in
`notes/hub_insignia_design_notes.md`'s "v4" entry. Two changes landed in
the live graph: (1) node **shape** now encodes kind — circle=entity,
diamond=person, square=product — closing a gap where the sidebar legend
already promised a person diamond the canvas never rendered; (2)
`products[]` entries are promoted to their own graph node kind (477
product nodes/edges from 72 entities, off by default via a toggle) with
directed arrowheads added to the inherently directional edge types
(owns/founded/directs/produces). Same presentation-not-sourced discipline
as v3 — no `entities.json` schema change.

**Update 2026-09-08, still later same day ("v4.1"): grouping made
explicit.** User feedback on a full-graph screenshot: with 1408 nodes
on screen, everything outside the labeled hub clusters read as "a
sparse cluster of loosely if at all connected galaxies... grouped by an
uncertain principle." Cause: components of size 1–2 (the majority of
the graph — most entities have exactly one director/founder) all
shared one weak central anchor point instead of getting their own
layout space. Fixed by replacing the uniform-grid clustering with a
size-aware shelf pack (cell size ∝ √component-size) and adding an
explicit soft convex-hull halo around every component so grouping is
drawn, not inferred from proximity. Full writeup in
`notes/hub_insignia_design_notes.md`'s "v4.1" entry. Republished to the
same graph URL.

Touches the same registry data the phases above track (pulled 5 real
entities' names/ИНН/products for test cards) but only as read-only input —
no entity record was modified. Two live-fetched brand assets (site
favicons, a Telegram channel avatar, one product photo) were embedded in
the mockup artifact as base64 but were **not** archived into
`data/sources/`, added to `entities.json`'s `images[]`, or run through the
`inventory_sources.py`/`extract_registry.py`/`check_registry.py`
housekeeping bundle — per CLAUDE.md's own imagery convention, that would be
a separate follow-up if these assets are wanted as permanent registry
assets rather than mockup-only decoration.

**Update 2026-09-09 ("v5"): hub badge glyph replaced with a hex/pattern
family.** A second standalone mockup ("Hub Icon Schema",
https://claude.ai/code/artifact/8bed5183-6ced-4df0-8c2d-8a4352ceaacd)
redesigned the v3 dagger/shield badge as one fixed hex glyph whose *fill
pattern* — solid/hollow-ring/split — carries offensive/defensive/dual,
instead of two different shape families, tested against real imagery for
«Овод», ГОУДРОН, and БАСИРТК. User approved it and asked to wire it in;
only `hubGlyphInner()`'s rendering and the `.hub-badge` CSS changed in
the live graph — `classify_variant()`'s existing full-graph classification
logic was untouched. Full writeup, including a caught-before-publish
debug-script DOM mutation (never reached the saved file), in
`notes/hub_insignia_design_notes.md`'s "v5" entry. Republished to the
same graph URL.

**Update 2026-09-13 ("v7"): merged a parallel hardening pass; product
icon set cut from 15 categories to 2.** A separate working copy of this
repo (same machine, user-confirmed) had independently built a stricter
graph contract (`graph_contract.py`, schema_version 2, exact-equality
validation now wired into `check_registry.py`), fixed a real founder-
share-parsing bug, excluded `_merged_into` tombstones from the graph, and
replaced `classify_product()`'s broad keyword heuristic with a
deliberately conservative 2-signal version (explicit "multirotor" or
"vehicle-mounted" wording only — 462 of 474 products now read
`unclassified`, up from 32%). User reviewed both classifiers and chose
the conservative one everywhere, consistent with this project's own
"never present inference as fact" standard, while keeping
`classify_variant()` (the hub badge) as a separate, already-approved
feature not covered by that decision — re-added on top of the merge.
Merged via `git merge` after committing this session's own uncommitted
work as a checkpoint first; one real code conflict
(`build_relationship_graph.py`), resolved by taking the incoming rewrite
and re-adding `classify_variant()`. `relationship_graph.json`/`_views
.json` regenerated from the merged code (1308 nodes, 1637 edges, 208
unresolved). New artifact from the same merge: `docs/relationship-graph
.html`, a table-first evidence-only explorer (cited/current/core/
evidence-gap views), deliberately not force-directed. Full writeup,
including the merge-review process and what was verified, in
`notes/hub_insignia_design_notes.md`'s "v7" entry. Live D3 graph updated
to match (product icons cut to 2 categories) and republished to the same
URL.

**Same day, follow-on: fixed a `sources.json` date-parsing bug the new
explorer surfaced.** Actually reading `docs/relationship-graph.html`
(not just testing it) turned up 43 sources with a nonsense
`captured_date` (e.g. `"1708-20-26"`, `"3396-34-34"`) — pre-existing,
invisible until this new page started rendering `captured_date` directly
in its source-detail panel. Root cause in `extract_registry.py`'s
`infer_source_type_and_dates()`: it blindly slices any 8-digit filename
stamp as YYYYMMDD, but a small pre-convention batch of `<ИНН>_
<8digits>.pdf` EGRUL pulls used DD-MM-YYYY, and `ZAKUPKI_ATTACH_*`
filenames end in an 8-digit upload UID that isn't a date in either
order. Fixed to accept the YYYYMMDD reading only if it's a real calendar
date, fall back to DD-MM-YYYY only if that's also a real date AND its
year falls in a plausible pull window (2020–2027), and set `None`
otherwise rather than keep guessing — 4 sources got a real corrected
date, 39 correctly became `null` (an honest gap, not a wrong date).
Regenerated `sources.json` via the normal `extract_registry.py` pipeline
(confirmed `entities.json`/`people.json`/everything else byte-identical
— only `captured_date` values changed) and `docs/relationship-graph
.html`. Verified: full test suite, `check_registry.py --quiet` (0
errors, matching pre-fix), tag-balance.

**Update 2026-09-09 ("v6"): product nodes gained 15 subtype icons.** User
asked for more varied/intuitive icons distinguishing quadcopters, FPV,
parts, and EW-setup subtypes, plus more researched categories. A third
mockup ("Product Icon Set",
https://claude.ai/code/artifact/fa4295ea-cef5-4fa0-ab0b-27cd92407a93)
surveyed the registry's 477 `products[]` entries by keyword, designed 15
monoline pictograms (FPV strike, multirotor, fixed-wing, helicopter,
three EW-jammer variants, detector, antenna, battery, motor, video-link,
ground-control, munition, repeater, plus a fiber-optic modifier tag)
grounded in MIL-STD-2525's frame/icon orthogonality and ISO 7000's
symbol-family consistency, and iterated on six icons that read poorly at
first pass. Approved and wired in: `build_relationship_graph.py` gained
`classify_product()` (same keyword-heuristic, non-registry-field
discipline as `classify_variant()`) — 153 of 477 products matched a
category, the rest genuinely fall outside the UAV/EW vocabulary (GISP-
catalogue office/IT hardware, not a classifier miss). `network_graph.html`
renders the matched icon directly on the product's own square (a new
`--product-icon-ink` token, no separate backing) and gave product nodes a
7px size floor so the icon has room to draw. Full writeup in
`notes/hub_insignia_design_notes.md`'s "v6" entry. Republished to the
same graph URL.
