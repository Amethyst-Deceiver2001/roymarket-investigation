# Working rules for roymarket-investigation

This repo is a standalone spin-off of a ЦБСТ/РОЙ.МАРКЕТ (Russian "military
marketplace" and its parent defence-tech body) OSINT investigation, migrated
out of the `wb_watch` project on 2026-08-18 once it outgrew "annex to a WB
tracker" scope. Read `HANDOFF.md` first in any new session — it has full
context, current state, and pending work that this file doesn't repeat.

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

Not yet wired up: `docs/index.html` doesn't link to `docs/profiles/` pages
yet (no nav, no cross-linking from the narrative). That's a separate task
from generating the profiles themselves.

## Publishing

`docs/index.html` is the GitHub Pages source (repo Settings → Pages →
`/docs`) and the standalone Artifact companion
(https://claude.ai/code/artifact/5450bf7e-7f7b-4788-93c0-761503dd5ea4). Edit
the local file freely; only republish the Artifact when the user calls an
explicit investigation cutoff — see `HANDOFF.md` for why (the Artifact
intentionally lags the local file between cutoffs).

## Tag-balance check before any publish

Run the scoped tag-count script (in `HANDOFF.md` and the seeded memory) after
every `docs/index.html` edit, before publishing.

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
- **Individuals who are not PEPs or network principals** — a resident
  mentioned in passing, a private person named in a court filing, a
  chat participant — are not in scope for this treatment. Ask before
  extending it to anyone who is not a principal, official, owner,
  director or comparable public actor in the network.

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
