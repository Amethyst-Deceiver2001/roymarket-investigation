# Informal-cooperation / co-mention leads (Part 2 of 2026-09-15 connectivity audit)

> **Archived 24.10.2026.** Its open leads were moved into the records' `open_questions` (ООО «Тримикс», НПО «КАЙСАНТ», АО «Площадь»); the rest were already closed in the registry: КИНГПРО carries a documented ЦБСТ tie, `kb-germes` is merged into `npo-kaysant`. Not a source.

**Status: triage list, not a source.** Every candidate below still needs the
same primary-source verification discipline as `mine_leads.py`'s output
before anything here goes into `corrections_entities.json`/
`corrections_people.json`. Nothing in this file has been wired into the
registry.

## Method

Local text mining over `data/roymarket.db` (192,582 posts with text length
> 20, no live scraping). For every already-registered entity (`name_ru`/
`brand_ru`) and person (`fio_ru`) in `data/registry/entities.json`/
`people.json`, built a normalized name index (reusing `scripts/id_patterns
.norm()`), then re-used `id_patterns.RE_ENTITY_QUOTED`/`RE_ENTITY_BARE`/
`RE_QUOTED_NAME` to extract candidate entity mentions per post. A post
scored as a candidate when it named **2 or more distinct already-registered
entities/people** in the same text. 635 normalized names loaded; 1,721 raw
co-mention posts found across 191 distinct entity/person pairs.

Two known-noise clusters were filtered out before triage (documented here
so the count is reproducible, not silently dropped):
- The «Архангел» name-collision cluster (`ooo-arkhangel*`, `proekt-kb-
  arkhangel` — 7 separate registry slugs for name-colliding, mostly
  unrelated "Архангел"-branded entities/projects) dominates raw counts
  (1,603 "co-mentions" per pair) purely because every post naming any
  "Архангел" matches all 7 slugs at once — an artifact of the name
  collision this project already tracks (`roymarket_archangel_adjacent_
  network` memory), not a real connection.
- Three pairs are the same real-world company recorded under two registry
  slugs (`ao-stratim`/`ooo-stratim`, `ao-aeromaks`/`ooo-aeromaks`, `ano-
  npts-ushkuynik`/`npts-ushkuynik`) — co-mentions between them are just the
  duplicate name matching itself, not a cooperation signal.

After excluding those, **27 distinct entity/person pairs** remain as real
candidate signal, backed by 1-9 posts each. Full raw data (all 1,721 posts,
all pairs) is at `/private/tmp/claude-501/-Users-ak-Downloads-roymarket-
investigation/f2a0c6cb-5635-40da-ac73-3c3d3f9f5370/scratchpad/comention_
raw.json` if a deeper pass is wanted later (not copied into the repo —
scratchpad only).

Per CLAUDE.md's proportionality guidance, this is a sampling/triage pass,
not an exhaustive sweep — training-course and dual-sweep techniques already
documented in `notes/tg_channel_dual_sweep.md`/`military_thankyou_letter_
genre.md` were reused rather than reinvented, but a full separate pass
using ROLE_TITLES/training-cohort vocabulary was not run this session; that
remains open work if a future session wants to extend this file.

## Verification-grade finding (recommend review/wire)

### ООО «КИНГПРО» carries no `cbst_tie` despite being named a ЦБСТ resident in a primary, dated, named source — this looks like a real registry gap, not just an informal-cooperation lead

`ooo-kingpro` currently has `cbst_tie: null` in `entities.json`. But three
independent postings from named, identifiable channels explicitly call it
a "резидент ЦБСТ" (ЦБСТ resident) in the same sentence as `ao-stratim`
(which DOES already carry a `cbst_tie`):

- `evgeniy_lisitsyn` (channel), msg 15599, 2025-04-09: *"Беспилотники
  резидентов ЦБСТ «Стратим» и «КингПро» поступили в 58-ю армию,
  группировку «Центр», 76-ю гвардейскую десантно-штурмовую и 9-ю
  мотострелковую бригады."*
- `asidyakin` (Александр Сидякин's own channel — already a named, sourced
  figure in this registry), msg 6, 2025-05-19: identical text, re-posted.
- `asidyakin`, msg 145, 2025-05-20: a paraphrased re-statement of the same
  event, again pairing «Стратим» and «КингПро» as delivered equipment,
  again in the ЦБСТ/Единая Россия/фонд «Наша Правда» joint-delivery frame.

This clears the same bar as the Цыганов fix — an unambiguous, dated,
named primary statement, not a suggestive mention — but it's a different
kind of gap: not a missing multi-hop path, but a missing direct
`cbst_tie` record on an entity that evidently should have one. Recommend
the main session review `ooo-kingpro` and add a `cbst_tie` (confidence
`t-doc`, these three posts as evidence) the same way `ao-stratim`'s own
was recorded, per CLAUDE.md's corrections mechanism — not done here per
this task's scope (Part 2 write-up only, no corrections-file edits).

## Probable duplicate-record lead (data-quality, not a new tie)

### `kb-germes` (КБ «Гермес», no ИНН, unresolved stub) may be the same real entity as `npo-kaysant` (НПО «КАЙСАНТ», ИНН 7733393203)

`npo-kaysant`'s own `cbst_tie.claim` text already states: *"КБ «Гермес»,
резидент ЦБСТ, представило новый высокоскоростной перехватчик..."* and
notes *"this entity trades under the «Гермес» brand (kaysant.ru/
germesfpv.ru)"* — i.e. the registry's own npo-kaysant record already
identifies «Гермес» as its own trade brand. `kb-germes` nonetheless exists
as a separate, ИНН-less stub slug. The 8 co-mention posts found here (all
duplicates of the same educational-post genre reposted across `mil_hub`/
`projectArchangel`/etc.) are not a cooperation signal between two entities
— they're the same underlying "Гермес" name being matched twice because it
resolves to two different registry slugs. Recommend the main session check
whether `kb-germes` should be merged/redirected into `npo-kaysant` rather
than treated as a distinct entity. Not done here — this is a registry-
hygiene observation, not a corrections-file edit.

## Real informal-cooperation signals (triage — verify before use)

### АО «Площадь» × ООО «Гагаринг» — joint exhibitor listing at "Народный ВПК" forum, organized by the (ЦБСТ-adjacent, not ЦБСТ-core) «Архангел» project

Channel `projectArchangel`, msg 4504, 2024-06-05 (also cross-posted to
`Archangel_Forum`, msg 95633, 2024-06-11): a forum-slyot announcement for
"Народный ВПК" (14-16 June 2024, Nizhny Novgorod) lists АО «Площадь»
("разработка бортовых решений для разведывательных и ударных БЛА на
основе ИИ") alongside ООО «Гагаринг» as separate exhibitors, each with its
own invite link. `ao-ploshchad` currently has no `cbst_tie`; `ooo-gagaring`
does. This is a genuine joint-appearance signal, but it runs through the
«Архангел» adjacent-network's own event, not a ЦБСТ event — worth noting
as a cross-network touchpoint (one more data point for the `roymarket_
archangel_adjacent_network` memory file) rather than a ЦБСТ-internal tie.
Characterization: **shared exhibition appearance, cross-network**.

### НПО «КАЙСАНТ» × АНО «НПЦ «Ушкуйник»» — shared Дронница-2025 exhibition tent, reported in a press digest

Channels `tsg_group71` (msg 168) and `nponebo` (msg 95), both 2025-09-09,
identical "Что показывали на Дроннице" digest text: both entities' products
are described in the same round-up of what was shown at Дронница. This is
the same shared-exhibition-space genre CLAUDE.md already documents for
`tsg_group71`/`nponebo` (тент-neighbours). Characterization: **shared
exhibition appearance** — both entities already carry `cbst_tie` records
independently, so this doesn't establish a new ЦБСТ link, but does
document a direct physical/promotional co-appearance between the two.

### АО «Технодрон» × АНО «НПЦ «Ушкуйник»» — co-mention in an RT-sourced press repost about «Технодрон»'s fiber-optic FPV line

Channels `mil_hub` (msg 97962) and `ANO_CBST` (msg 509), both 2025-03-04,
identical RT-sourced text about «Технодрон»'s optical-fiber FPV drone
«Скворец». «Ушкуйник» appears only because the digest/repost format
co-lists multiple ЦБСТ residents' names in surrounding text, not because
of a described cooperative act between the two specifically —
**low-confidence, likely just shared-channel co-listing, not a real tie**.
Flagged for completeness but not recommended for further chase.

### АНО «НПЦ «Ушкуйник»» × ООО «Тримикс» (3mx/«Булат») — joint anti-drone-detection conference

Channel `chadayevru`, msg 3627, 2025-03-06: *"4–5 марта 2025 года на базе
научно-производственного центра «Ушкуйник» в Великом Новгороде состоялось
второе совещание разработчиков средств противодронной борьбы. Организаторы:
АНО «НПЦ «Ушкуйник», компания «RuDrones. Беспилотные технологии» и
коммуникационная площадка ExpoUAV."* «Тримикс»/«Булат» is not named as a
co-organizer in this specific post (matched via a separate April-2024
chadayevru post, msg 2722, about a related anti-drone conference series at
the same venue) — the cross-year conference-series link is suggestive but
not a single-document confirmation that «Тримикс» attended *this specific*
March 2025 session. Characterization: **plausible shared-conference-series
signal, needs a direct per-event confirmation before treating as
established**.

## Lower-confidence signal, logged not chased further

### «Аляска» (ООО «ИОНОС», slug `alyaska`) × ООО «Визионеро» × «Овод» (РЛВТ) × АНО «НПЦ «Ушкуйник»» × ООО «Авирон» — recurring ЦБСТ resident-roundup co-listings

Multiple `ANO_CBST` posts (e.g. msg 1734, 2026-01-11; msg 1701,
2025-12-31) are ЦБСТ's own New Year/news-digest posts naming several
resident companies together in one sentence ("...руководители наших
компаний-резидентов: «Авирон», «Овод», АО «НПП», НПЦ «Ушкуйник», «Аляска»
и «Визионеро»"). This is co-residency, already independently documented
via each entity's own `cbst_tie` record — not a new pairwise cooperation
finding, just confirms the resident cohort ЦБСТ itself already lists
together repeatedly. Logged for completeness; no individual pair here rises
above "same resident list," so none is broken out as its own lead.

## Not pursued (out of proportional scope this pass)

Joint-training-course and instructor/student cohort mining (the PII-scope
category added 2026-09-04) was not run as a separate pass this session —
the co-mention scan above is keyed on already-registered entities/people
only, per this task's brief ("connection discovery among what's already
documented," not new-name discovery). A dedicated training-cohort sweep
using `ROLE_TITLES`/course-genre vocabulary against channels already
flagged as training-adjacent (e.g. `ano-dpo-obrazovatelny-tsentr-gagaring`
-affiliated channels) remains open work for a future session if wanted.
