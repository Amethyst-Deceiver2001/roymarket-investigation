# Script and parser reference (moved verbatim from CLAUDE.md, 2026-09-20)

CLAUDE.md keeps the standing rules and one-line pointers; the per-script detail lives here.

---

**`scripts/tg_media_pull.py`** (added 2026-08-25, generalized from a manual
pull done for СКБ «Пиранья»/`@piranhafpv`) pulls photo/video-still evidence
out of posts a channel scrape already found, in two steps:

- `candidates --channel <username> [--top N] [--min-score N]` — LOCAL scan
  over `data/roymarket.db`, scoring each post by UAV/battlefield-language
  density (reuses `id_patterns.uav_score` plus its own
  `BATTLEFIELD_TERMS` list — уничтож/поражен/сбит/боевое применение/
  благодарствен/etc). No network call, safe to run directly/repeatedly like
  `mine_leads.py`.
- `fetch --channel <username> --inn <ИНН> --msg-ids 300,355,384 [--out FILE]`
  — for a human-picked msg_id list, fetches each post's public
  `t.me/s/<channel>/<id>` preview (no auth), parses any photo/video-thumb
  URLs out of the grouped-album HTML, downloads them to `data/sources/` as
  `TGMEDIA_<ИНН>_<YYYYMMDD>_<channel>-post<id>-<n>.jpg`, and prints a JSON
  scaffold (Russian text verbatim from the DB, English/context/`source_id`
  left `TODO` for a human) ready to hand-paste into `corrections.json`'s
  `battlefield_evidence[]`. Capped at 15 posts per invocation — these are
  single-post lookups (same category as a one-off WebFetch, fine to run
  directly per the policy above), not a scripted loop at scale; a bigger
  batch should be split into multiple runs rather than raising the cap.
  After `fetch`, still run `inventory_sources.py` → `extract_registry.py`
  to get real `sNNNN` source ids for the new files (set `as_of` on the new
  cache entries by hand — see the dated-history convention above), then fill
  the scaffold's `TODO` fields before adding it to `corrections.json`.

Does not do a live Telegram scrape itself — that's still `tg_scan.py`'s job,
handed to the user per the policy above. This script only re-fetches public
preview HTML for posts a scrape already found in the local DB.

**`scripts/zakupki_batch_pull.py`** (added 2026-08-25, generalized from the
manual pull that confirmed ИП Цыганов's ₽28.176m «Булат»/«Покров» government
contracts) searches zakupki.gov.ru's contract registry for every ИНН already
in `entities.json`/`people.json`, using the `supplierTitle` param
reverse-engineered from a user-supplied DevTools HAR capture — see the
seeded memory `zakupki_gov_ru_contract_search_api`. Three steps:

- `scan [--limit N] [--inn X] [--kind entity|person] [--force]` — one search
  per ИНН (186 as of 2026-08-25: 146 entity + 40 personal), paginated
  (50/page) until every `regNumber` the hit count promises is collected —
  the first version only ever fetched page 1 (silently truncating a
  160-contract ИНН to ~10) and extracted reg numbers with a blanket
  `№ \d+` regex that also matched unrelated ИКЗ/plan-position codes on the
  page; fixed to read only each result card's own `common-info.html` link.
  A hit count above 5000 is treated as a broken filter (the
  `customerInn`/`supplierInn` trap documented in the memory file silently
  returns the whole ~42M-record registry), not a finding — large state
  defense primes legitimately run into the hundreds (confirmed against a
  real 160-contract ИНН), so the ceiling sits well above that. Zero-hit
  ИНН are logged to `data/registry/_zakupki_scan_log.json` (bookkeeping,
  not `data/sources/`) so a re-run skips them by default; any real hit
  gets its raw search page archived as `data/sources/ZAKUPKI_<ИНН>_
  <YYYYMMDD>_supplier-search.html` and printed with its `regNumber`(s).
- `fetch-contracts --inn X` / `--reg-numbers A,B,C` / `--all-hits` — pulls
  each contract's full `common-info.html` card live, archived as
  `data/sources/ZAKUPKI_contract_<regNumber>_<YYYYMMDD>.html`. Capped at
  50 regNumbers per invocation; skips a regNumber already archived.
- `fetch-documents` (same `--inn`/`--reg-numbers`/`--all-hits` selectors,
  plus `--max-contracts` to raise the default-50 cap) — the actual "incl.
  docs" pull: reuses the contract card (or fetches it), extracts
  `contractInfoId`, hits the card's "Вложения" tab, and downloads every
  attachment — the signed contract PDF, payment orders, delivery acts,
  sole-supplier justification — from zakupki's filestore
  (`44fz/filestore/public/1.0/download/rgk2/file.html?uid=...`), named
  `data/sources/ZAKUPKI_ATTACH_<ИНН-or-regNumber>_<regNumber>_<label-slug>_
  <uid8>.<ext>` with the real extension read off each response's
  `Content-Disposition` header (`resp.headers`, not a `dict()`-ified copy —
  the server sends lowercase `Content-disposition`, and a plain `dict()`
  lookup on the capitalized name silently misses it and everything falls
  back to `.bin`; caught on the first test run, see the script's own
  comment). Confirmed end-to-end against the two known Цыганов contracts:
  17 attachments, 42.1MB, correct pdf/xml/html/rar/docx/zip extensions.

All three steps are live network jobs at scale — handed to the user, not
run directly or in background, per the policy above (tested inline on a
handful of ИНН/contracts first, same as `egrul_batch_pull.py`'s
precedent). A hit is a lead, not yet a citable fact — hand-verify each
contract card (and its attachments, once pulled) and wire confirmed ones
into `government_contracts[]` via `corrections.json`, the same way the
Цыганов contracts were added, before treating it as established. Many
hits will belong to large, already-well-documented state defense primes
(Ростех, НИИ «Вектор», Технодинамика, ...) whose zakupki footprint is
enormous by nature — triage for what's actually new to this investigation
before spending a `fetch-documents` pass on it.

**Record every zakupki triage decision in the structured `zakupki_review`
field, not only in prose.** `scripts/zakupki_coverage.py` is the "are we
done with zakupki?" report, and its zero-wired heuristic cannot by itself
tell *nobody has read this* from *somebody read it and correctly decided
not to wire anything* — and the second case is the common one (a generic
small-supplier footprint; a state prime whose presence is enormous by
nature; an academic-fee-scale personal ИНН). On 2026-09-05 that made **10
of its 11 flagged "high-value candidates" false positives**, every one
already triaged on 2026-08-30/31 and recorded as such in the record's own
prose notes — an entire work session's worth of misdirection. So when a
review closes, set on the entity/person via `corrections.json`:

```json
"zakupki_review": {"as_of": "YYYY-MM-DD",
                   "outcome": "wired" | "partial" | "closed",
                   "note": "what was read and why it was/wasn't wired"}
```

`closed` = reviewed and deliberately not wired. `partial` = some wired, a
reviewed remainder deliberately left. The script treats this field as
authoritative and drops such records from the candidate list; it also
carries a prose backstop (`REVIEW_PROSE_RE`) that loudly flags a record
whose notes say it was reviewed but which has no structured field, so a
missing one fails visibly instead of silently re-flagging. Trust
`--gaps-only` output over your own file counts — a gap list derived from
counting files in `data/sources/` reproduces exactly this error.

**`scripts/tg_scan_users.py`** (added 2026-09-04, sibling to `tg_scan.py`)
catalogs a channel's member/participant list rather than its message
history — usernames, profile names, exposed phone numbers, and a flag for
profile photos with identifiable features. Same live-network-job class as
`tg_scan.py` — a full-channel member pull is handed to the user as an exact
command (`--only <handle>`), never run directly/in background. Distinct
from `tg_scan.py --full`, which only ever pulled message text/media, never
membership — for an invite-only chat in particular, a "did we scrape this"
question needs checking `tg_users` (membership) separately from `tg_posts`
(content); a channel can have one populated and not the other.

**`scripts/screen_egrip_ip.py`** (added 2026-09-04) checks a person's
personal ИНН against egrul.nalog.ru's open ЕГРИП (individual-entrepreneur)
search — the same no-captcha API `egrul_batch_pull.py` already uses, just
keyed on people instead of entities. `--slug <person-slug>` is ordinary
inline reconnaissance; a full-roster sweep (no `--slug`/`--limit`) is
handed to the user. A real ИП hit is any row with `k=="fl"` carrying an
`o` (ОГРНИП) field — NOT a check on `tot`/`cnt`, which are pagination
metadata attached inconsistently and silently drop a person's 2nd+
registration if used as the filter (bug found and fixed 2026-09-04, see
the script's own docstring). **`scripts/enrich_egrip_hits.py`** takes the
resulting ОГРНИП list to rusprofile.ru for status/OKVED/procurement
detail — see the seeded memory `rusprofile_ru_decoy_content_anti_scraping`
before trusting anything this script returns beyond the `<title>` tag;
rusprofile serves randomized other-people's data in its gated widgets to
repeat/automated traffic, confirmed by re-fetching the same URL three
times and getting three different unrelated procurement summaries while
the title stayed correct every time.

**ФНС «Прозрачный бизнес» (pb.nalog.ru / nalog.gov.ru), added 2026-09-04**
— three distinct person-level (not entity-level) cross-checks, all keyed
on a person's `inn_personal`, each `--slug`-scoped for inline
reconnaissance and hand-the-user'd for a full-roster sweep:
`scripts/screen_disqualified.py` (реестр дисквалифицированных лиц —
disqualified-director registry, via `pb.nalog.ru/search-proc.json`
search-rdl mode), `scripts/screen_subsidiary.py` (subsidiary/liability
cross-check by ИНН and ФИО, via `nalog.gov.ru/rn77/rso/Ajax.html` — no DOB
field, so a namesake collision can't be fully ruled out by this registry
alone), and `scripts/screen_upr_uchr.py` (director/founder cross-reference,
same `search-proc.json` endpoint, different query mode — writes results to
a person's `other_entities`/`other_entities_checked_at` fields, not a
field named `upr_uchr_matches`). Genuinely productive on the first real
run: surfaced business ties for the Гагаринг network's Барашков/Бегак that
ФНС's own director/founder records had but nothing else in this project's
toolkit had checked.

## Local extraction jobs: sample before a full corpus run, don't background a slow one

"No network call" (`mine_leads.py`, `scan_sources.py`, `mine_zakupki.py`,
`extract_registry.py`) means safe to *run*, not safe to run *blind* — two
failure modes this project has actually hit:

- **A parser bug can survive a full run silently.** The 2026-08-29
  `mine_zakupki.py` price-parsing bug (an older zakupki.gov.ru contract-card
  layout puts "Цена контракта" in a `<div class="price">` block, a different
  DOM shape from the `section__title`/`section__info` blocks the parser
  otherwise read) went undetected through 32 contracts (₽1.72bn) across two
  full corpus mines before a human-noticed "why is this null" question
  caught it. After changing anything in a parser
  (`mine_zakupki.py`/`mine_leads.py`/`scan_sources.py`), run
  `python3 tests/test_zakupki_parser.py` (fixtures for both known contract-
  card layouts, plus a no-price-section case) before trusting a full re-run —
  it catches this class of regression in under a second instead of requiring
  a multi-minute full mine plus a human spotting the gap in the output.
  Extend that fixture file (or add a sibling one) when a new layout variant
  or extraction gotcha turns up, the same instinct that produced
  `docs/registry/ustav_templates.json` for charter-template variants.
- **A local job can still be slow enough to want the user's own terminal.**
  A full `mine_zakupki.py` re-mine of the ~1289-file `data/sources/` corpus
  (needed after any parser change, since its own file-mtime cache doesn't
  know the code changed) took long enough that a backgrounded run had to be
  killed and hand-restarted in 2026-08-29. Before backgrounding any local
  job touching 100+ files or expected to run past ~2 minutes, say so and
  either let the user run it in their own terminal instead, or make clear
  you're starting a background task they'll be notified about — don't
  silently launch it in the background and go quiet.
- **A field silently empty for every record, not just one, is still a
  parser bug** — same lesson as the all-null rule below, but corpus-wide.
  `mine_zakupki.py`'s `parse_contract_card_html` selected
  `span.cardMainInfo__title` only; "Объекты закупки" (the contract subject
  line) uses a `<div>` for that same title class on every one of 1498
  archived contract cards, so `government_contracts[].items`/`subject_ru`
  came back empty across the whole corpus — not because contracts lack a
  stated subject, but because the selector never matched it. Fixed
  2026-09-15 to select both tags, plus preferring a truncated span's
  `data-tooltip` for the full text and dropping a non-substantive
  "Этап N" stage label instead of reporting it as the subject. See
  `tests/test_zakupki_parser.py`'s `zakupki_object_*` fixtures — run them
  after touching this parser, same discipline as the price-parsing bug
  above.

**An all-null result for one entity is a parser signal, not a finding.** When
a parser returns nothing for *every* document belonging to a single record,
suspect the parser before concluding the entity has no figures. Two distinct
bugs in `parse_bfo_financials.py` were found this way on 2026-09-05, both
having silently corrupted or suppressed real data across the whole registry:

- **Non-profits file their money somewhere else.** An АНО/фонд filing form
  0710096 has an «Отчет о финансовых результатах» sheet that is empty *by
  construction* — an НКО reports no Выручка and no Чистая прибыль. The real
  numbers live in the «Отчет о целевом использовании средств» (ОЦИС, ОКУД
  0710003): line 6200 targeted funding received, 6300 used, 6100/6400
  opening and closing balances. The parser read only the P&L, so every
  non-profit in the registry came back `revenue=None profit=None`, which is
  indistinguishable from "nothing on file". That hid ₽269.8m of FY2024
  funding for АНО «ЦБСТ» — the investigation's own core entity — behind six
  filings that had been sitting in `data/sources/` the whole time. These
  figures are recorded under `funds_*` keys and **must never be presented as
  revenue or turnover**: targeted non-profit funding is a different thing and
  conflating them would be a factual error in a sanctions brief. Two gotchas
  worth keeping: the ОЦИС sheet name is truncated to 31 chars by Excel
  («Отчет о целевом использовании д»), so match a prefix; and line 6300 is
  printed both bare (`98 047`) and parenthesised (`(275 587)`), so it must be
  sign-normalised or the same quantity lands with opposite signs depending on
  the filing. Every parsed row is now checked against the sheet's own
  identity `6100 + 6200 − 6300 = 6400`.
- **A filing's `inns` list is not ordered filer-first.** It includes related
  parties, so picking the first entry that happens to be in the registry
  attributes the filing to whichever related party sorts first — it credited
  фонд «Градислава»'s FY2025 filing to ООО «Заволжское», a commercial LLC
  that would then have carried another organisation's non-profit funding as
  its own. The filename is authoritative (`РЕСУРС_БФО_<filer ИНН>_<year>_…`,
  `BFO_<filer ИНН>_<year>_…`); read the filer off it and fall back to `inns`
  only when the name carries none.

`tests/test_bfo_parser.py` locks down both, plus the commercial path, the
same way `tests/test_zakupki_parser.py` does for contract cards — run it
after any change to `parse_one()`. A cheap independent check that
attribution is right: consecutive filing years should chain, each year's
6100 equalling the previous year's 6400.


---

### Product profiles (added 2026-09-15) — flagship products only, not the full `products[]` corpus

`scripts/build_product_profile.py` generates `docs/profiles/products/
<slug>.{html,md}` the same generated-not-hand-written way company profiles
work, but there is no product-level registry file to drive it from —
`products[]` entries live nested under each entity, with no product-level
slug, and (as of this writing) only 25 of 489 entries across the whole
registry have a structured `specs{}` dict; the rest are name+description
only, and images/`battlefield_evidence[]` are captioned at the *entity*
level with no field linking them to one specific product when an entity
sells several. Building a real profile — not a mostly-empty stub — for
every one of 489 entries isn't achievable from what the registry currently
holds.

So this is scoped to a short, hand-maintained `FLAGSHIP_PRODUCTS` list in
the script itself (currently 5: Кузнечик, Набат, Овод, Пиранья, Булат/3MX —
the same flagship entities already central to the coverage audit and the
"From ЦБСТ to the Front" exhibit), each entry naming its maker entity_slug,
the exact `products[].name_ru` values that make up that flagship product
(often several registry entries — variants, sub-modules), and a short list
of distinct-proper-noun match keywords (e.g. `["кузнечик", "kuznechik"]`)
used to link images/`battlefield_evidence[]` from across the product's real
supply chain (maker + any reseller/distributor entity, e.g. Булат's
Тримикс → ПОКРОВ → ИП Цыганов chain) by substring match on the product's
own brand name — never a generic term, or unrelated evidence gets pulled
in. `government_contracts[]`-derived "handovers" are scoped to the
reseller/distributor entities specifically (a contract card rarely names
the product brand in a structured field, so keyword-matching it would be
unreliable — but a reseller/distributor's *only* registry-relevant
contracts already are for this product line, so no matching is needed
there). Every section that comes up empty is stated as such under "Not yet
sourced" rather than omitted silently, so a thin page still tells you what
hasn't been confirmed, not just what has.

Extend `FLAGSHIP_PRODUCTS` deliberately, one real product at a time, only
when a product actually has enough sourced specs/images/field-testing data
to justify a page — not as a mechanical sweep of the remaining ~484 entries.

Company profiles link to a product's profile page when one exists
(`PRODUCT_PROFILE_BY_NAME` in `build_company_profile.py`, keyed off the
exact `products[].name_ru` strings `FLAGSHIP_PRODUCTS` names) — a plain
description card otherwise, never a dead link to a page that doesn't
exist yet.

### `related_entities[].relationship_type` — a typed vocabulary, not free-text guessing

Every `related_entities[]` entry always had a free-text `relationship`
paragraph, but nothing categorized *what kind* of tie it was — a reader
(or a filter, or a future exhibit) couldn't tell "authorized dealer" from
"co-exhibited at one forum" from "same director, real corporate family"
without reading the whole paragraph. `relationship_type` (schema v5,
`graph_contract.RELATED_ENTITY_RELATIONSHIP_TYPES`) fixes that: `dealer`,
`co-exhibited`, `co-speaker`, `sister-entity`, `group-structure`,
`managed-by`, `external-registry-cross-listed`, `same-name-different-
entity`, `training-partnership`, `competitor`. **This vocabulary was
derived by reading every one of the registry's (then-)42 `related_entities[]`
entries and categorizing what each one actually documents — never invented
ahead of the data.** `competitor` is defined for future use; as of
2026-09-15 no entity carries a sourced competitor claim, and the category
existing is not licence to populate it without one. `build_relationship_
graph.py` uses it as the `related` edge's label when present, falling back
to the old generic "related (ambiguous)" only for an entry that predates
the taxonomy and hasn't been classified. Renders as a `.tag` chip on both
company profiles ("Corporate links") and product profiles ("Network
context" — pulled from every entity in the product's own supply chain,
labeled "via <entity>" so a reader sees whose relationship it actually is).

When adding a new `related_entities[]` entry, set `relationship_type` from
this vocabulary at the same time — don't leave it for a later backfill
pass, or the entry silently falls back to the generic label again.


## Product research: `product-researcher` agent + `verify_findings.py` (added 2026-09-30)

`.claude/agents/product-researcher.md` researches what listed entities make from Russian
primary sources and returns a findings JSON; it may write only raw captures into
`data/sources/` and that file. **`scripts/verify_findings.py <findings.json>`** (local, no
network) checks every `verbatim_ru`/`text_ru` fragment against the cited raw file (case, ё,
quote style and punctuation folded; `\uXXXX` page state decoded; fails on a missing file or
a quote not in it) and warns on `name_only` identity. The 2026-09-30 tranche needed it: 15
quotes cited the wrong capture, one spliced two patent sentences, two came from articles
that were only linked. The agent never wires the registry; the main session does, and
`claim-verifier` is the independent second pass on the wired slug.

## Telegram post coverage: `tg_post_coverage.py` (added 2026-10-01)

Local, no network. Modes: no args (ЦБСТ posts naming a registry entity, unarchived/uncited/unreviewed, grouped by term, no-tie-on-file first), `--slug`, `--term` (every hit plus `links`), `--all-channels`, `--include-archived`, `--max N`, `--check` (exit 1 on an unreviewed no-tie hit), `--out`. Terms come from `name_ru`, `brand_ru` and `name_history` with legal forms and quotes stripped; terms under 5 letters and a small stop list are dropped; a term hitting >=25 posts and >=1.5% of the channel is reported as generic (counts only). A hit is ARCHIVED (a TGPOST/TGWEB file for that exact channel+msg in `sources.json`), CITED (named in registry prose, no file), REVIEWED (msg id in the entity's `cbst_channel_review.posts_read`) or UNSEEN. One review on any candidate slug closes the post for that term, so keep `posts_read` to posts actually read and say in `note` what stays open. Lessons: SQLite does not fold Cyrillic; fold in Python. Ended at 3 seconds for the ЦБСТ channel after a substring prefilter (21 s without it, identical output). First run (2026-10-01) produced 42 no-tie hits across 16 terms; reading them closed 8 terms as namesakes and left 8 real leads (Ростех, Молот-ПВО, Элиарс, Сармат, Кольская верфь, Платформа НТИ, Азимут 716).

## Resident sweep and forward diff: `cbst_resident_sweep.py`, `tg_forward_diff.py` (added 2026-10-01)

`cbst_resident_sweep.py` (local, 3 s for all 328k posts): a «резидент…» word (anchored so «президент» does not match) within 300 characters of a ЦБСТ token (ЦБСТ, ЦСБТ, ЦБТС, «Центр беспилотных систем», #Резиденты_ЦБСТ), or anywhere in ЦБСТ's own channel. Names are taken from the sentence holding the word plus the next one (a headline «Резидент ЦБСТ представил…» names the company in the following sentence), dropping «…» after a preposition (events), bare acronyms and roman numerals. Matching is by `match_key`: legal forms stripped, punctuation ignored, Cyrillic transliterated, y folded to i (so Нейри meets Neiry, «ТИТАН - СЕВЕРО-ЗАПАД» meets «Титан Северо-Запад»). Classes: TIE-GAP, NEW, MENTIONED, known. `--kind accelerator` is noisy (184 NEW in ЦБСТ, most foreign news) and is better used by reading the announcement posts. First run (2026-10-01): 52 NEW / 6 TIE-GAP across all channels; reading them produced five new entities (Neiry, Wheelies, Школа БПЛА Октагон, Stratolink, ИНТЭК ПРОМЫШЛЕННЫЕ СИСТЕМЫ), two tie fixes (ИНТЭК БЕСПИЛОТНЫЕ СИСТЕМЫ, Титан Северо-Запад) and an open-lead list on the ЦБСТ record. Products and event names appear as candidates too; each needs a read.

`tg_forward_diff.py`: compares the «…» and Latin names in a channel's posts with those in forwards of them. The DB holds the text as last scraped; a forward keeps the wording at forward time. Flags names present in the forward and absent now (removed) and the reverse (added or shortened). Only 10% of ЦБСТ posts have a forward, so a clean result covers only those. Tests: `tests/test_cbst_resident_sweep.py`.


## Automated upkeep: status board, pull queue, first reading, sanctions watch, Wayback (added 2026-10-02)

Merged from cloud sessions (PRs #3–#6). The rules are in CLAUDE.md; the who-runs-what table is in `notes/rebuild_plan.md` §D. Practical notes:

- **`status_board.py`** reads only the repo plus, when present, the weekly scan's `weekly_scan_state.json` / `developments.json` in `/mnt/project-files/watch/` (cloud only; on the Mac those flags are skipped and the output says so). `--slug X` for one record, `--json` + `--diff old.json` for what changed. `screen_never` / `screen_hits_unreviewed` are listed but not queued: the screeners have no per-record selector.
- **`--pull-queue`** ranks by tier, caps 8 per registry, and prints the ingest chain after the pulls: `inventory_sources` → `scan_sources` → the matching parser → `extract_registry` → `build_relationship_graph` (added 02.10.2026; without it `check_registry` fails on a stale graph whenever a parser adds data) → `check_registry`. Run the lines as printed, then commit only after reading. Since 02.10.2026 it also queues re-screens for the board's `screen_never`/`screen_stale` flags (each flag's `due` names the screens): `screen_opensanctions.py --budget N --only …` (cap 4 a day), `screen_gur.py --only …` and `screen_aleph.py --only …` (cap 8 each). When there were pulls, the queue ends with `first_reading.py export --push --local-dir data/sources/_inbox` (user's go-ahead 02.10.2026), so the daily routine can write the first-reading worksheet the same morning.
- **`first_reading.py`**: `export` picks files named `EGRUL|EGRULAPI|EGRIP|BFO_<ИНН>_<date>_…` pulled on or after `--since` (БФО by file mtime, since its name carries the fiscal year). `--push` writes text to the private `pull-inbox` branch with git plumbing (the checkout is untouched); `--local-dir data/sources/_inbox` also writes the day's texts locally so `read --inbox data/sources/_inbox/<date>` runs on the Mac without the round trip. Exported hashes are remembered only after a push. A scanned PDF with no text layer is flagged, not read.
- **`sanctions_watch.py`** counts identifier matches only (ИНН/ОГРН in the list entry); names are context. Person listings rarely carry an ИНН, so a clean person result proves nothing. Offline test mode: `--from-file us=sdn.xml`.
- **`archive_sources.py`**: `plan`/`local`/`report` are local; `lookup` (read-only CDX) and `save` are network jobs for the Mac in batches. Captures are public but anonymous. Set `WAYBACK_S3_ACCESS`/`WAYBACK_S3_SECRET` in `.env` for SPN2. Per-post CDX lookups (1.5 s each) and anonymous saves (~20 s, throttled to ~45/hour by the second batch) were the bottleneck; since 03.10.2026 Telegram uses one prefix query per channel (`collapse=urlkey`, earliest capture) and preview-page saves. Many channels are already heavily captured by others (projectArchangel ~68k URLs).
- **`timestamp_sources.py`**: `build` (local), `stamp` (one RFC 3161 request per authority; only the manifest's hash leaves the machine), `verify`. First run 03.10.2026 found 121 files rewritten after cataloguing: trademark JSON regenerated by `fips_trademark_enrich.py`, re-fetched OpenSanctions/zakupki/ГУР/Aleph pages saved under the same name, and notes appended later. Scripts that overwrite a catalogued file in place are the cause; a re-fetch should get a new dated filename.
- **`daily_mac.py`** wraps the above: board before → queue lines run in order (a failed step is logged, later steps still run) → `first_reading export --push --local-dir` → `read` → board after and `sb.diff`. Report and log in `data/sources/_daily/<date>.md`. It never commits.
- **Lessons from the first run (02.10.2026).** (1) The local text copies under `data/sources/_inbox/` were inventoried as 27 new sources (s9019–s9045, duplicates of the БФО PDFs plus a log and the export state); the source scans now skip `_`/`.` names, and the ids were dropped before anything cited them. (2) Parsed БФО lands in `_bfo_financials.json`, not in `financials[]`, so the board kept re-queuing pulled filings; it now flags them `bfo_unread`. (3) A company that has not filed the latest year yet keeps its `bfo_behind` flag; it queues last so it cannot hold the day's slots. (4) A second run the same day (the user's terminal and this session) re-asks bo.nalog only for the years it lacks; `bfo_pull.py` skips files on disk.
- **CI** (`checks.yml`) runs on main pushes and PRs without `data/sources/`; locally run `check_registry.py` without `--no-local-files`.
