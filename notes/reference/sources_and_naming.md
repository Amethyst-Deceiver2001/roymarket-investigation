# Primary sources: where they live and how they are named

Moved verbatim from CLAUDE.md on 24.10.2026, when CLAUDE.md was cut to a short rulebook; stale facts corrected where marked. CLAUDE.md keeps the rule in one line and points here for the detail.

## Hard rule: facts come from the original document, read in full, in its own language

Added 2026-10-01 at user direction. A fact enters the registry only from the original-language (normally Russian) document, read in full: the charter, the ЕГРЮЛ extract, the Telegram post and its `links`, the court filing, the press article. English summaries, search-result snippets, machine translations and a subagent's paraphrase are **leads only**. A lead from one of them is recorded as an `open_questions` entry naming what is unverified, never as a fact, a tie or an identity match. Scanned documents are OCR'd and the OCR is checked against the image where it matters (a one-page amendment can be an image the text layer misses). Say in the record which document and passage a fact rests on.

## Primary-source documents: check `data/sources/` before re-downloading

`data/sources/` (gitignored — local working copy; 1.6 GB on the working Mac on 24.10.2026, corrected from ~424MB when moved) holds the EGRUL
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
report is a triage list of candidates not yet in the registry (corrected from `docs/index.html` when moved), same
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

**Workflow**: `python3 scripts/inventory_sources.py` (reads every file in
`data/sources/` once — pdftotext/zip/xlsx — and caches its type and `as_of`
date to `data/registry/_source_content_cache.json`; only processes files not
already cached, so re-run it after adding new sources rather than every
session) → `python3 scripts/extract_registry.py` (one-time scaffold from the
frozen brief snapshot `notes/archive/brief_snapshot_2026-08-21.html` (moved out of `docs/` 2026-10-02), consuming that cache; re-runnable while
Phase 1 continues) → `python3 scripts/check_registry.py` before trusting or
building from anything. All three are local file processing — no network,
safe to run repeatedly.

**Cloud sessions and tests (added 2026-10-02, reworded 24.10.2026).** `data/sources/` and `data/roymarket.db` exist only on the user's machine. Where they are absent, run `python3 scripts/check_registry.py --no-local-files`: it skips existence checks for `data/sources/` paths only, says how many it skipped, and still checks everything committed. `pip install -r requirements.txt` covers the tests, the checker and the page builders. Run every `tests/test_*.py`, that check and `check_tag_balance.py docs/index.html` yourself before a commit; the workflow that used to run them on each push (`.github/workflows/checks.yml`) is abandoned with the rest of GitHub Actions.

`check_registry.py` validates ИНН and ОГРН control digits. **Take a checksum
failure seriously**: it caught a transposed ОГРН for АО «Стратим» that had
been sitting in the brief, and two personal ИНН that had been mis-attributed
to organisations. A wrong identifier in a sanctions submission is a serious
defect, not a typo.

