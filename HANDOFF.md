# Handoff: ЦБСТ/РОЙ.МАРКЕТ investigation

Read this first in a new session. It's the entry point — detail lives in the
files it points to, not duplicated here.

## What this is

An OSINT corporate-genealogy investigation into ЦБСТ (Центр беспилотных
систем и технологий — a Russian defence-tech body) and РОЙ.МАРКЕТ (the
"military marketplace" its subsidiary МПТМ runs). It's a companion piece to
Alexey Kovalev's Foreign Policy article, AND — per explicit user direction —
exists to **inform sanctions lobbying**, not just journalism. That second
purpose sets the evidentiary bar: every claim needs to survive scrutiny from
lawyers/advocacy orgs/government staff who might act on it. Read the seeded
memory file `roymarket_project_goal` for the full statement of this; it
governs almost every judgment call in this investigation (corroborate from
primary sources, tag confidence levels, don't fold in unconfirmed leads).

## Migrated from wb_watch, 2026-08-18

This was previously `wb_watch/research/roymarket-brief.html`, an "annex" to
a separate Wildberries product-tracking project. It outgrew that framing —
~1,200 lines of narrative, 50+ resolved corporate entities, its own image
evidence and source table — so it moved to this standalone repo. See
`CLAUDE.md` for why data collection (Telegram scraping) still happens in
`wb_watch` rather than being duplicated here.

## Current state

- **`docs/index.html`** — the brief itself. GitHub Pages source once this
  repo has a remote (Settings → Pages → `/docs`) and also published as a
  standalone Artifact:
  https://claude.ai/code/artifact/5450bf7e-7f7b-4788-93c0-761503dd5ea4
  **The Artifact lags the local file** — it's only republished at an
  explicit user-called investigation cutoff, never per-edit. See the seeded
  `roymarket_no_per_fold_publish` memory. **When checking "is X already in
  the brief," always read `docs/index.html` directly — never the Artifact
  URL**, which will be stale and produce false "new finding" claims.
- **`docs/images/`** — evidence photos (satellite views, production-floor
  frame grabs, screenshots) referenced by the brief.
- **`data/roymarket.db`** — local SQLite copy of the ~98,700 Telegram posts
  across the 11 channels this investigation actually uses (gitignored,
  regenerate with `scripts/export_from_wb_watch.py` — source of truth is
  `wb_watch`'s own DB).
- **`scripts/check_tag_balance.py`** — run after every `docs/index.html`
  edit, before publishing. The file is large hand-edited HTML; a missing
  closing tag from a string-replace edit won't error, it'll just silently
  break rendering somewhere downstream.
- **`scripts/export_from_wb_watch.py`** — regenerates `data/roymarket.db`.

## Structure of the brief itself

Roughly, in reading order: hero stats → thesis → MoD-payment-integration
finding (Sidyakin quote) → ЦБСТ org chart/history → EU sanctions traced to
EGRUL entities (Технодрон, Гаскар, СКБ Пиранья, Аэро-Хит, Архангел, Атлант
Аэро + the Технодинамика/Ростех trust-management chain) → a big
"Company/Principal/Products" table (50+ rows) → per-entity prose sections
for the more complex cases (НПЦ БАСиРТК physical-facility case study, TSG
Group, etc.) → Наша Правда fund / delivery-partnership timeline →
Telegram-source table → limitations → data-download table. The
"still open — not yet resolved" catch-all table row is the live todo list
inside the document itself — grep it for what's still unnamed.

## Standing working discipline (all seeded into memory — see below)

- **Fuzzy-dedup before adding a table row** — normalize company names
  (strip ООО/АО prefixes, case-fold) before treating something as new; a
  plain grep misses variants. Caught 4 real duplicates in one pass.
- **Verbatim quotes only** — never paraphrase or clean up a quote. If it
  can't be verified against a primary source, don't use it.
- **Tag-balance check** (above) after every edit.
- **Check the local file, not the Artifact**, before claiming anything is
  "new" or "already covered."
- **Check the local Telegram DB before web-searching** — often the source
  for a claim is already sitting in the scraped corpus.
- **Don't call a source "fully scanned" until every page/section has
  actually been opened** — a homepage-only pass on TSG Group's site missed
  a real brand-name collision («Стрибог») that only surfaced on a full
  re-scan.
- **PII discipline**: default to name+role only (EGRUL-sourced), no
  addresses/passport numbers, *unless* the user explicitly asks for full
  detail on a specific case (happened once, for the InformNapalm
  «Архангел» dossier — treat as an exception, not the default).
- **Adjacent-not-core networks** (same industry/event/name, no confirmed
  ЦБСТ tie) get one disambiguation line in the brief, full detail parked in
  memory. Two on record already: the national НПЦ БАС/Технопарк program,
  and two of the three «Архангел»-branded entities.

## Pending / open work

The single most current source for this is the seeded
`roymarket_tracking_discipline` memory file's "Current open threads"
section — read that directly rather than trusting this list to stay fresh.
Highlights as of migration:

- Long tail of unresolved EGRUL/БФО leads (АО «Росс», «Динарус», «Инстех»+
  Asel Labs, «Аэроплатформы», several bare product names with no
  manufacturer yet, etc.) — see the memory file for the full list and why
  each is stuck (no EGRUL match, ambiguous OKVED, quota exhaustion).
- НПЦ БАСиРТК founding docs (Устав) — blocked on the user's daily EGRUL
  quota.
- TSG's bot-linked webshop catalog — JS-rendered SPA, not yet successfully
  extracted.
- A pending `tg-scan --full --days 1500 --only projectArchangel`-style
  extension may still be relevant if any other channel's history looks
  truncated by the 730-day default lookback window (see "technique notes"
  below) — check each channel's earliest `tg_posts.date` against when you'd
  actually expect it to start.
- The investigator.org.ua YouTube video (flagged, never watched) — still
  outstanding if the «Архангел» adjacent-network thread gets revisited.

## Technique notes worth knowing before you hit the same wall

- **`tg-scan --full` caps history at `--days` back (default 730 = 2
  years), not the channel's actual creation date.** A scan that stops at a
  suspiciously round "N years ago" date is hitting this default, not the
  channel's real start — rerun with a larger `--days` and `--only <handle>`
  to extend just that channel.
- **БФО zip files**: unzip to get an `.xlsx` (balance sheet + P&L, parse via
  `openpyxl.load_workbook(path, data_only=True)`, sheets named
  `Бухгалтерский баланс` / `Отчет о финансовых результатах`) plus sometimes
  a `NO_BUHPZ_*.pdf` explanatory-notes doc — the PDF is where related-party
  and beneficiary detail actually lives, the xlsx alone often isn't enough.
  Figures are in тыс. руб. (thousands) — always cross-check against a known
  figure (charter capital, an EGRUL-disclosed number) before trusting scale.
- **EGRUL founding-doc (Устав) zips** sometimes have cp866-encoded
  filenames that break plain `unzip` — decode with
  `info.filename.encode('cp437').decode('cp866')` via Python's `zipfile`,
  or extract by reading `z.read(info.filename)` directly and writing under
  a clean name if `unzip` still chokes on the raw bytes.
- **Headless Chrome for JS-rendered/blocked content**: `Google Chrome
  --headless --disable-gpu --dump-dom --virtual-time-budget=Nms <url>`
  bypasses WebFetch's static-HTML-only limitation for VK posts, Telegram
  channel previews (`t.me/s/<handle>`), and JS-rendered sites. Doesn't
  bypass Cloudflare Turnstile challenges (informnapalm.org is behind one) —
  those need the user's own browser session, saved as `.mhtml` if you need
  the content badly enough to ask for it.
- **Telethon**: `wb_watch/wb_watch/tg/client.py`'s `make_client()` returns a
  `TelegramClient` synchronously — don't `await` the constructor itself,
  use `async with client:`. Useful beyond message fetching: bot metadata via
  `client(GetFullUserRequest(bot))` can surface a real URL hidden behind a
  bot's menu button that a plain landing-page fetch won't show.

## Memory

This session seeded `~/.claude/projects/<escaped-this-repo-path>/memory/`
with every ЦБСТ/РОЙ.МАРКЕТ-relevant memory file from the `wb_watch` project
(the WB-tracker-specific ones were left behind — irrelevant here). Check
`MEMORY.md` there for the full index. If that seeding didn't survive (new
machine, fresh Claude Code install, whatever) — this HANDOFF.md plus the
brief itself are still the durable record; the memory files are an
accelerant, not the only copy of anything.
