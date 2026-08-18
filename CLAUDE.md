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

## Same crawling-jobs discipline as wb_watch

Inline reconnaissance (single post lookups, one-off WebFetch/curl checks,
EGRUL/БФО document reads) is fine to run directly. Anything that does real
work at scale against a live third-party service must be handed to the user
as an exact command to run themselves, never run in the background — this
applies to `scripts/tg_scan.py` here (see above) and to EGRUL/БФО pulls,
which are the user's own manual downloads due to daily rate limits.
`scripts/mine_leads.py` is NOT covered by this — it's local processing over
already-scraped data, no live network call, fine to run directly/repeatedly.

## Quotes: never paraphrase or invent

Any review, post, testimonial, or other quoted material in `docs/index.html`
must be the original text only — verbatim, punctuation and typos preserved.
If a quote can't be verified against a primary source, don't use it.

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

Default to the brief's existing standard: named individuals get name + role,
sourced from EGRUL/official filings, no personal addresses/ID numbers. The
one exception on record (an InformNapalm OSINT dossier with full addresses/
passport numbers) was included at explicit user direction for that specific
case — don't treat it as the default; ask if a similar case comes up.

## Adjacent-but-not-ЦБСТ networks

Entities/networks that turn out to lack a confirmed ЦБСТ/РОЙ.МАРКЕТ tie
(same industry, physical proximity, name collision — but no institutional
link) get a one-line disambiguation in `docs/index.html` at most, with full
detail parked in memory instead. See the seeded `roymarket_adjacent_networks`
memory file — check it before starting a fresh deep-dive on something that
smells adjacent-not-core.
