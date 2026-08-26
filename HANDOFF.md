# Handoff: ЦБСТ/РОЙ.МАРКЕТ investigation

Read this first in a new session. It's the entry point — detail lives in the
files it points to, not duplicated here.

## ⚠ A rebuild is in progress (started 2026-08-22)

`docs/index.html` is being replaced by a **generated multi-page publication**
built from a structured registry. Much of the "Current state" and "Structure
of the brief itself" sections below describe the single-file brief as it was
before that started — treat them as describing the frozen snapshot at
`docs/_archive/index-2026-08-21.html`, not as the target state.

**The plan lives at [`notes/rebuild_plan.md`](notes/rebuild_plan.md) — read
that file for current phase status, not the summary that used to be here.**
(Moved 2026-08-24 from `~/.claude/plans/spicy-beaming-kite.md`, a per-session
location outside the repo, specifically so it can't go stale relative to a
Claude session and can't disappear between sessions. That old external path
now just holds a redirect stub — if a future session surfaces it via
plan-mode tooling, treat `notes/rebuild_plan.md` as authoritative and update
it, not the stub.) The phase-by-phase summary that used to be duplicated here
was removed because it drifted out of sync with the real plan more than once;
don't recreate it — link, don't copy.

As of 2026-08-24 (end of that day's session): Phases 0–2 are essentially
closed (registry built, 147/148 entities verified, screening swept
full-roster), the entire `data/registry/` tree is now committed to git (it
was untracked before — see the plan's "Things to fix" §2), and Phase 3
(imagery) has a first small batch of real assets. **One real blocker remains
before any publish**: a regression left `ooo-trimiks-bulat-3mx`'s
`wb_overlap` at `none_found` when it should be `confirmed_reseller` — the
registry and the live brief currently contradict each other on the project's
headline claim. See the plan's "Things to fix" §1.

Two known defects in the old file, both fixed by the rebuild rather than in
place: the manufacturers table is malformed (an unclosed `<td colspan="3">`
spanning lines 1026–1051 with galleries and a 51,007-character unclosed
paragraph inside it — do not DOM- or regex-edit that region), and the Mermaid
ownership diagram at lines 500–568 has never rendered on Pages because the
document loads no JavaScript.

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
evidence and source table — so it moved to this standalone repo.

**Data collection is now fully independent of `wb_watch` too** (a same-day
correction to the original migration design — see `CLAUDE.md`'s "This repo
has its own Telegram scraping pipeline" section for the full story). This
repo has its own Telethon client/scraper/session (`tg/`), own
`config/channels.txt`, and its own purpose-built lead-mining pass
(`scripts/mine_leads.py`) that has nothing to do with wb_watch's WB/Ozon-
link matching. `scripts/export_from_wb_watch.py` only did the one-time
historical bootstrap at migration time and isn't the ongoing method.

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
- **`data/sources/`** — primary-source documents backing the brief's EGRUL/
  БФО claims: `ul-*.pdf` (EGRUL extracts), `РЕСУРС_БФО_*.zip` (annual
  accounts filings), `UD_*.zip` (founding Устав bundles), plus a handful of
  one-off press/OSINT captures (ТАСС Безруков interview HTML, the
  InformNapalm Архангел dossier html/mhtml). Gitignored (424MB, well past
  GitHub's 100MB single-file limit for some bundles) — local working copy
  only, not committed history. Populated 2026-08-18 from everything the
  user had downloaded to `~/Downloads` from 2026-08-14 onward; going
  forward, save new EGRUL/БФО pulls directly here rather than leaving them
  in `~/Downloads`. **Check here before re-downloading or re-requesting a
  document from the user** — most of what's cited in the brief already has
  its source file sitting in this folder.
- **`data/roymarket.db`** — this repo's own SQLite DB (gitignored — it's a
  local working copy, not committed history), currently holding the ~98,700
  Telegram posts across the 11 channels this investigation uses. Seeded at
  migration time from wb_watch's archive, now grown/refreshed via this
  repo's own scraper (`scripts/tg_scan.py`) going forward.
- **`tg/`** — this repo's own Telethon client/scraper/storage layer
  (`client.py`, `scraper.py`, `db.py`) — independent auth session from
  wb_watch, no WB/Ozon-item-matching logic (irrelevant here).
- **`config/channels.txt`** — this repo's own watchlist.
- **`scripts/tg_login.py`** — one-time interactive Telegram auth; prints a
  session string to paste into `.env`.
- **`scripts/tg_scan.py`** — the scraper entry point. **Live network job —
  hand the exact command to the user, don't run it directly/in the
  background**, same discipline as wb_watch always required for its
  `tg-scan`.
- **`scripts/check_tag_balance.py`** — run after every `docs/index.html`
  edit, before publishing. The file is large hand-edited HTML; a missing
  closing tag from a string-replace edit won't error, it'll just silently
  break rendering somewhere downstream.
- **`scripts/export_from_wb_watch.py`** — historical bootstrap only, not
  the ongoing collection method (see above).
- **`scripts/mine_leads.py`** — this investigation's own entity/product/
  person extraction pass over `data/roymarket.db` (corporate-prefix regex,
  «quoted names», ИНН/ОГРН, role+name), UAV-relevance-scored and cross-
  checked against `docs/index.html` so it only surfaces genuinely new
  candidates. Purpose-built — does not reuse wb_watch's WB/Ozon-link
  matcher. See `CLAUDE.md` for the full design rationale. First run (2026-
  08-18) already surfaced real candidates worth checking: named ЦБСТ
  personnel not yet in the brief (Нина Яныкина, Дмитрий Рубинштейн — msg
  refs in the tool's own output), and corporate leads like АО «ГЛОНАСС»,
  АО «Обуховский завод», АО «Фазотрон-ВМЗ», НПЦ «Крылья Сахалина». Treat
  all of it as a triage list — every candidate still needs EGRUL/БФО/
  primary-source verification before going in the brief.

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
- **PII discipline (revised 2026-08-22 — supersedes the old default)**:
  named individuals get **full identifying detail** (DOB, place of birth,
  address, personal ИНН, photo) where sourced — this investigation feeds
  sanctions screening, where DOB is often what makes a match legally usable.
  Every field still needs its own `source_id`; never inferred or filled from
  a plausible namesake. Only applies to PEPs/network principals (owners,
  directors, officials) — not to incidental resellers or people mentioned in
  passing. See `CLAUDE.md`'s "PII handling" section for the full rule.
- **Adjacent-not-core networks** (same industry/event/name, no confirmed
  ЦБСТ tie) get one disambiguation line in the brief, full detail parked in
  memory. On record: the national НПЦ БАС/Технопарк program, two of the
  three «Архангел»-branded entities, and (2026-08-25) unrelated Chinese
  resellers surfacing under the "Набат" brand name on WB/Ozon.
- **VK/TG as primary source, marketing copy scanned verbatim (2026-08-25)**:
  no official site is not a dead end for `products[]` — a VK/TG catalog is a
  valid primary source in its place. Any marketing copy scan (site, listing,
  brochure) must be grepped for and quote verbatim any self-incriminating
  СВО/military-use language, not just note the adjacent commercial fact (a
  discount tier, a spec sheet). See the seeded
  `roymarket_vk_tg_as_primary_source` and
  `roymarket_capture_self_incriminating_marketing_copy` memory files.

## Pending / open work

The single most current source for this is the seeded
`roymarket_tracking_discipline` memory file's "Current open threads"
section — read that directly rather than trusting this list to stay fresh.
Highlights as of migration:

- Long tail of unresolved EGRUL/БФО leads (АО «Росс», «Динарус», «Инстех»+
  Asel Labs, «Аэроплатформы», several bare product names with no
  manufacturer yet, etc.) — see the memory file for the full list and why
  each is stuck (no EGRUL match, ambiguous OKVED, quota exhaustion).
- TSG's bot-linked webshop catalog — JS-rendered SPA, not yet successfully
  extracted.
- A pending `python3 scripts/tg_scan.py --full --days 1500 --only
  projectArchangel`-style extension may still be relevant if any other
  channel's history looks truncated by the 730-day default lookback window
  (see "technique notes" below) — check each channel's earliest
  `tg_posts.date` against when you'd actually expect it to start. Needs a
  working `.env` (`scripts/tg_login.py` run once) — this repo's own
  session, not wb_watch's.
- The investigator.org.ua YouTube video (flagged, never watched) — still
  outstanding if the «Архангел» adjacent-network thread gets revisited.
- **Aleph screening/RuPEP enrichment (2026-08-26)** — full-roster
  `screen_aleph.py` sweep done (419/508 hits) and fully triaged via the new
  `scripts/aleph_followup.py`; personal ИНН coverage went 51→101 people.
  RuPEP.org added as a source (blocked for scripts, works for the user's
  browser — see memory `rupep_org_cloudflare_blocked`); Якушев and Сидякин
  done, Безруков checked-negative, a downloaded Песков PDF still
  unprocessed, 6 more candidates (Фрадков, Лысогорский, Кузнецов, Осадчук,
  Турчак, Рогозин) not yet looked up. Full detail: `notes/rebuild_plan.md`'s
  "Aleph screening + RuPEP identity enrichment workstream" section.

## Technique notes worth knowing before you hit the same wall

- **`scripts/tg_scan.py --full` caps history at `--days` back (default 730
  = 2 years), not the channel's actual creation date** — inherited
  deliberately from wb_watch's identical gotcha. A scan that stops at a
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
- **Telethon**: `tg/client.py`'s `make_client()` returns a `TelegramClient`
  synchronously — don't `await` the constructor itself, use `async with
  client:`. Useful beyond message fetching: bot metadata via
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
