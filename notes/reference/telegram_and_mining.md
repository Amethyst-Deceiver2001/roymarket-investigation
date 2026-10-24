# Telegram pipeline, lead mining and text search

Moved verbatim from CLAUDE.md on 24.10.2026, when CLAUDE.md was cut to a short rulebook; stale facts corrected where marked. CLAUDE.md keeps the rule in one line and points here for the detail.

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
- `config/channels.txt` — this repo's own watchlist (171 lines on 24.10.2026 [corrected from "the 11
  channels" when moved]; add new ones as research finds them).
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
content), and cross-checks every candidate against the registry and `notes/dossier_draft.html` (`id_patterns.load_known_text`; corrected from `docs/index.html` when moved) so
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

## Searching Telegram text: use `scripts/tg_post_coverage.py`, never SQL `LIKE`/`lower()`

Added 2026-10-01 after ЦБСТ posts 1562, 1976 and 2095 (all naming «Архангел») sat in `data/roymarket.db` while the registry said "no ЦБСТ tie". SQLite's `lower()` and `LIKE` do **not** fold Cyrillic (`lower(text) LIKE '%архангел%'` returned 0 where `LIKE '%Архангел%'` returned 5), and a hit list sliced to `[:3]` with no text printed hid the rest. Rules:

- "Does the channel say X?" is answered by `python3 scripts/tg_post_coverage.py --term "X"` (every hit, folded for case and ё, case endings tolerated, each hit's `links` field shown, archived-or-not flagged; `--all-channels` for the whole scrape, ~1 minute, say so first). It runs a positive control first and aborts (exit 2) if the matcher cannot find known words.
- Search the **bare brand word**, not the legal-name variant; then narrow.
- Never slice an evidence list. A cap (`--max`) must say how many hits it hides.
- Read a post's `links` field. A post can carry its primary document (an EU act, a patent) as a link.
- Never write "not found in this search" into the registry without naming the exact query and its hit count.
- `python3 scripts/tg_post_coverage.py` (no args) lists ЦБСТ posts that name a registry entity and are not archived, cited or reviewed. `check_registry.py` §6b turns the no-tie class into warnings. Close one by reading the posts and recording either a tie or a dated `cbst_channel_review` (`{as_of, outcome: namesake|named_no_tie|tie_wired|lead_open, posts_read: [msg ids actually read], note}`) via `corrections_entities.json`; never by deleting the warning. `tests/test_tg_post_coverage.py` holds the regression fixtures.
- **Residents and edits (added 2026-10-01).** `python3 scripts/cbst_resident_sweep.py` finds companies the archive calls «резидент ЦБСТ» that the registry lacks (NEW), holds without a tie (TIE-GAP), or mentions only in prose (MENTIONED); `--kind accelerator` does the same for accelerator finalists; `--watchlist` lists forwarding source channels not on `config/channels.txt`. ЦБСТ misspells itself in its own channel («резидент ЦСБТ», post 2041), so never search for «ЦБСТ» alone. A company name is resolved to a legal entity only by an identifier printed on the company's own site or a matching named person, never by an ЕГРЮЛ name search alone (Neiry is АО «Нейрореволюция», Wheelies is ООО «ВИЛЛИС»). `python3 scripts/tg_forward_diff.py` compares a channel's posts with forwards of them: DB text is the latest scrape, ЦБСТ edits posts after publication (10% of posts have a forward to compare against; three name removals found, e.g. «Титан Северо-Запад» in post 2080), so archive a forward when it names a company the origin no longer does.

