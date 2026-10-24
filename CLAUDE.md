# Working rules for roymarket-investigation

Rewritten 24.10.2026 as a short rulebook. The detail behind each rule is in `notes/reference/` (index at the end), moved there word for word; the pre-rewrite file is in git history (`8582f21`).

## What this is for

An OSINT evidence base on ЦБСТ (АНО «Центр беспилотных систем», a Moscow defence-tech body) and РОЙ.МАРКЕТ, the login-only "military marketplace" its circle runs (operator ООО «МПТМ»). The investigation's purpose is sanctions lobbying, so **every claim has to survive a hostile lawyer**. It is a standalone spin-off of `wb_watch` (since 18.08.2026), with its own scraper and mining.

Two readers:
- **A lay reader** (press, policy staff), who gets a story: the landing page's opening and story 1. These follow the chain from ЦБСТ and its programmes to the maker, the product, the sellers and state buyers, and the front-line recipients, with every line graded doc / rep / open.
- **A specialist** (sanctions desk, lawyer), who needs to check each claim and reach the identifiers.

Current work (24.10.2026):
- the landing page opening and the story (private previews);
- chain views per product («Булат», «Капюшон»);
- the delivery record (`deliveries.json`);
- media triage of Telegram pictures;
- registry corrections from documents read in full.

`notes/rebuild_plan.md` is the live plan (direction, ordered work, decisions waiting on the user); read it first. `data/watch/brief_items.json` and `scripts/morning_brief.py` give the short list of what is ready, stuck or waiting on a decision.

## Settled facts: never raise these as open work

- **ROY.MARKET has no public catalogue.** It is behind a login; its public pages are the legal terms, offer, payment, delivery, returns and contacts. That is the premise of the investigation. What is "on the platform" is known only from the operator's posts, the supplier offer, vendors' own posts and the press. Never write "check the catalogue" or "not yet checked" on a page, in a brief or in a note. Say the catalogue is not public and grade the listing by who claims it. Ask before assuming any access.
- **GitHub Actions is abandoned** (no minutes since 10.10). The checks, Wayback and sanctions workflows do not run. A red or missing run means nothing: do not report, fix, re-run or schedule it. `.github/workflows/` stays in the tree; nothing depends on it.
- **The daily round is retired** (24.10.2026). There is no launch agent and no 09:15 job; the last round report is 06.10. `daily_mac.py`, `status_board.py --pull-queue` and `first_reading.py` run by hand when the user asks. `ops/launchd/` stays in the tree, not installed. A missed day is not a fault to report.
- **Retired, kept by hand only:**
  - the sanctions watch: `sanctions_watch.py` runs by hand, and `watch/sanctions` is a frozen snapshot of 05.10.2026, so EU/US/UK/CH status is as of that date;
  - the Wayback batch: `archive_sources.py run` by hand, with the 442 captures kept;
  - the cloud first-reading routine and the `pull-inbox` branch;
  - the cloud weekly scan: on request only;
  - the status-board artifact: view it locally.
- **Telegram posts are not web-archived.** They are preserved by our own record (`data/roymarket.db`), the RFC 3161 stamps and per-post media bundles.
- **The old site is archived, not retrofitted.** That covers the case pages, profiles, graph explorer and `story.html` (`exhibits/archive/site_2026-10-02/`, generators in `scripts/archive/`). Do not run or extend them. The old brief (`notes/dossier_draft.html`) is never linked or published; its unregistered facts are a migration backlog.
- **The infrastructure freeze is lifted** (22.10). The media-law and PII review of the story is still not started until the user says so.

## Machines and data

- **The working Mac** (`~/Projects/roymarket-investigation`, Intel, macOS 12, disk nearly full):
  - `data/roymarket.db` holds 23.10.2025–23.10.2026 only;
  - **no sNNNN source ids are assigned here**, so a new post is cited by its public link until it is catalogued;
  - venvs: `~/.venvs/roymarket311` (page builders, bs4) and `~/.venvs/roymarket-media` (CLIP, torch with numpy<2);
  - Chrome headless does not run; Firefox headless screenshots work.
- **The archive Mac** holds the older posts, the `TGPOST_`/`TGMEDIA_` originals and the source catalogue run (`inventory_sources.py` → `extract_registry.py`). Work that needs them waits there (brief items b005, b010, b011).
- **Python 3.11 parity.** Never put a backslash or a reused quote inside an f-string expression; build the string first. Byte-compile staged `.py` files with `python3.11` before committing.
- **Pre-commit hook:** `ops/git-hooks/pre-commit` runs the checker and refreshes `data/watch/status/board.json` on a fact-file commit, and does the 3.11 compile. It is not installed on this Mac (`git config core.hooksPath ops/git-hooks`), so do those steps by hand.

## Hard rules

- **Facts come from the original document, read in full, in its own language** (normally Russian). That means the charter, the ЕГРЮЛ extract, the Telegram post with its `links`, the court filing, the press article. English summaries, snippets, machine translations, the month read and a subagent's paraphrase are **leads only**: record one as an `open_questions` entry `{text, source_id}` naming what is unverified, never as a fact, tie or identity. OCR is checked against the image where it matters. Say which document and passage a fact rests on.
- **Quotes are verbatim**, typos included; if one can't be verified, don't use it (STYLE_GUIDE §3.1).
- **Search Telegram text with `scripts/tg_post_coverage.py --term "X"`, never SQL `LIKE`/`lower()`**, which do not fold Cyrillic. Search the bare brand word. Never slice a hit list; a cap says how many it hides. Read each post's `links`. "Not found" goes in the registry only with the exact query and its hit count. ЦБСТ misspells itself («ЦСБТ») and edits posts after publishing. → `notes/reference/telegram_and_mining.md`
- **Look a name up with `scripts/registry_lookup.py` before calling it unrecorded.** Its `contains`/`fuzzy`/`initials` tiers are leads, never merges.
- **"Connected to ЦБСТ" means multi-hop reachability.** Run `scripts/graph_query.py` (undirected BFS, `--between A B`) before saying two records are or aren't connected.
- **An identity is resolved by an identifier, not a name.** Use an ИНН/ОГРН printed on the company's own site, or a matching named person; never an ЕГРЮЛ name search alone. A same-name namesake goes in `candidate_identities[]`, never into the record's `inn`. Take an ИНН/ОГРН checksum failure from `check_registry.py` seriously.
- **Never overwrite a file in `data/sources/`.** Write through `source_files.write_new()` (a changed re-fetch becomes `-r2`). Hand-made notes there are fixed once catalogued: add a new dated file. Check `data/sources/MANIFEST.md` before asking the user to re-download anything. → `notes/reference/sources_and_naming.md`
- **A tool's output is a work item, never a fact.** That covers screening hits, mining leads, OCR matches, CLIP ranks, the status board's flags and first-reading worksheets. A pulled document is read before anything from it enters the registry.
- **ё:** spell it where a source for that person gives it; match with ё folded to е on both sides; never edit quoted text (`scripts/yo_audit.py`, STYLE_GUIDE §2.5).
- **Adjacent networks** (same industry or name, no institutional tie) get one line at most. Check the `roymarket_adjacent_networks` memory before deep-diving something that smells adjacent.

## Where things live

| What | Where | Rule |
|---|---|---|
| Facts | `data/registry/*.json`: `entities`, `people`, `products`, `deliveries`, `media`, `programs`, `military_units`, `quotes`, `sources`, `open_questions` | The source of truth; every page is generated from it. |
| Hand fixes | `corrections_entities.json`, `corrections_people.json` | Each fix carries its reason and source. `extract_registry.py` applies them last. Raw screening fields (`ENTITY_/PEOPLE_CARRY_FORWARD_FIELDS`: `gur_matches`, `opensanctions_matches`…) are written onto the record, not via corrections. When a generated file is edited by hand here (no archive), mirror the edit in corrections. |
| Generated | `relationship_graph.json` (+ `_views`), from `build_relationship_graph.py`; schema in `scripts/graph_contract.py` | Rebuild after any change touching ownership, roles, products, contracts or `cbst_tie`; `check_registry.py` fails on a stale graph. Never hand-edit. Edge `grade` is derived, never set. |
| Deliveries | `data/registry/deliveries.json` (65 events: 23 name a product, 26 product items) | One event per post per recipient. Product views read it through `scripts/deliveries.py` `load_products()`. Ids are stable (`bulat-d05`, `h0025`); media records point at them. |
| Source files | `data/sources/` (gitignored), `MANIFEST.md`, `timestamps/` stamps | Naming `<TYPE>_<INN-or-OGRN>_<YYYYMMDD>_<slug>.<ext>`. `_`/`.` names are working files. |
| Telegram | `data/roymarket.db`, `tg/`, `config/channels.txt` (171) | `tg_scan.py` is a live job: the user runs it. |
| Watch | `data/watch/` (`brief_items.json`, `developments.json`, `status/board.json`, `daily/`, `brief/`) | An item closes with `status` + `note`, never by deletion. |
| Exhibits | `exhibits/` (builders, mockups, `images/`); `design/` (tokens) | Drafts never go in `docs/` or `notes/`. |
| Public | `docs/` (Pages serves it: landing, `images/`, `fonts/`) | Pushing `docs/` publishes. |
| Notes | `notes/` (plan, workstream notes, `reference/`, `archive/`) | Full transcripts go in `data/sources/`, not `notes/`. |

Schema rules (dated `_history` arrays, `cbst_tie` confidence vocabulary, `graph_tier`, sellers and `sells_for`, products and listings, delivery and unit-name rules, media, brands, programs, citations) are in `notes/reference/registry_schema.md`. **Read the relevant part before adding or changing a field.** Key points:
- A time-variant fact is a dated history entry `{value, as_of, source_id, note}`. One without a source is a placeholder.
- `captured_date` and `as_of` are never collapsed. `as_of` is filled only by someone who read the document.
- A `cbst_tie` needs `confidence` from `{t-doc, t-open, press}` or no edge is drawn.
- A delivery records the recipient as the post names it, defaults to `asserted_by: self`, `credibility: single`, and never implies combat use.
- A bare unit number never identifies a unit (`scripts/unit_lookup.py`).
- A product name is never a company brand. A brand never merges entities.
- Participation is not residency. Counts are claims, not edges.
- Citation fields (`title`, `public_url`) come only from `scripts/source_citation.py`.

## Working loop

1. A correction goes in `corrections_*.json` (or `deliveries.json`, `media.json`, `programs.json`, `military_units.json`, which are hand-held).
2. Run `python3 scripts/build_relationship_graph.py`, then `python3 scripts/check_registry.py` (`--no-local-files` where `data/sources/` is absent), which must show **0 errors**.
3. Run the `tests/test_*.py` files the change touches (all of them for a schema or helper change), the 3.11 byte-compile, and `scripts/check_tag_balance.py` on any page touched.
4. For a refactor, snapshot the built pages before and after and show they are byte-identical, or explain each difference.

**Commits (user, 04.10 and 24.10.2026).** Commit and push without a per-commit go-ahead when **all** of these hold:
- only these paths are staged: `data/registry/`, `notes/`, `exhibits/` generators and their tests, `scripts/` and their tests (bug fixes, new tools, archive moves), and the timestamp folders;
- the checker shows 0 errors;
- the touched tests pass.

**Needs an explicit go-ahead:**
- anything under `docs/`;
- `CLAUDE.md` and `STYLE_GUIDE.md`;
- anything sent outside the project (exports, packets, emails, sharing an artifact);
- a change to what a job runs, when, or its cap;
- deleting an artifact.

Never stage the held files listed in `notes/rebuild_plan.md` ("Held, never committed").

**Jobs:**
- Live third-party work at scale (`tg_scan.py`, `tg_scan_users.py`, `tg_media_pull.py download`, batch ЕГРЮЛ/БФО/zakupki/ЕГРИП/ФНС sweeps) is handed to the user as an exact command, never run or backgrounded.
- Single lookups are fine inline.
- A local job over ~100 files or ~2 minutes: say so, run it in the background, report when it ends.
- Read `notes/reference/script_notes.md` before running or changing a pull or screening script. It covers the parser lessons: sample before a full run; an all-null field is a parser bug; non-profit `funds_*` is never revenue.

Only the main session writes facts into the registry. Something that needs the user goes in a GitHub issue or a brief item. A registry "not found" is remembered in `_pull_misses.json` for 30 days.

## Reader pages and writing

- **Read `STYLE_GUIDE.md` before drafting any prose.** A draft in generic register needs rewriting, not editing.
- **English first** (23.10.2026): every quotation, printed line, address and recipient wording leads in English, with the verbatim Russian under a small RU control. Use `quote_html()`, `caption_html()`, `orig_line()`, `popup_originals()` and `latinize_gloss()` in `scripts/display_helpers.py`. Registered names stay visible in Russian beside the Latin.
- **No internal notation on a reader page:** no source or media ids, slugs, field or file names, or "msg N". Sources are cited in plain words with a public link.
- **Design system:**
  - colours, type and components come from `design/roymarket.css` via `display_helpers.design_head()`;
  - page CSS holds layout only;
  - grades come from `display_helpers.reader_grade()`;
  - red is only the Sanctioned flag;
  - names come from `display_name()`, brand first and legal name beneath.
  - After a CSS change, rebuild and republish the Reader System artifact (`design/README.md`).
- **Before any publish:**
  - run `scripts/check_reader_page.py <page>` (Russian outside RU controls, dead links, duplicate ids, internal notation, Sanctioned flags against `sanctions[]`, an unsourced DOB or personal ИНН);
  - run the tag-balance check;
  - add a new page to `tests/test_reader_pages.py` `PAGES`.
- **Story:** after changing the story's quotations, write `tests/fixtures/story_sources.json` with `build_story.py --export-fixture` on a machine that has the sources.
- **Publishing:**
  - new reader pages go out as **private Artifacts for preview** (landing W5m6W6w663RjwfqqTEjQ6z, chain views);
  - the public landing is `python3 exhibits/build_landing.py --out docs/index.html`, and every number on it is computed from the registry;
  - publishing to `docs/` and enabling Pages are the user's decisions (brief b006);
  - a chain's own pictures never reach `docs/`.

## People, faces and media

- **Everyone involved is a person of interest:** principals and PEPs, course participants and instructors, donors, volunteers, carriers, sellers and signatories. They are recorded with full identifying detail, and **every identifying field carries its own source**. A DOB or address with no source stays null and is never filled from a namesake.
- A merely connected person (family with no stake) is not in scope; use `graph_tier: "reference"` if a record is needed at all.
- **Proportionality:** triage names before promoting anyone to `people.json`, and ask when in doubt.
- A person's free-text `notes` never reaches a page.
- Full policy and its history → `notes/reference/pii_policy.md`.
- **Media** (`media.json`):
  - no source, no record;
  - `shows` and `redact` come only from a full-size look;
  - faces of the involved are shown, and only a clearly uninvolved bystander or child is blurred;
  - **nobody is named from a face**;
  - faces the publisher blurred stay blurred;
  - video is key frames plus a link to the archived original;
  - `docs/images/` is public, so nothing unblurred or unarchived goes there.
  - Triage runs `media_triage.py` `queue` → user-run download → `process` → `rank` → `sheets`, and nothing is looked at twice (`_media_looked.json`).

## Reference index

- `notes/rebuild_plan.md`: the live plan and decisions; read first.
- `notes/reference/registry_schema.md`: every registry field and modelling rule. Read it before changing the model or adding a record of a new kind.
- `notes/reference/telegram_and_mining.md`: the scraper, `mine_leads.py`, `extract_ids.py`, `tg_post_coverage.py`, resident sweep, forward diff.
- `notes/reference/jobs_and_screening.md`: status board, pull queue, first reading, sanctions watch, Wayback, timestamps, evidence packets and exports, and the history of the retired schedules.
- `notes/reference/script_notes.md`: per-script detail and parser lessons for the pull and screening scripts.
- `notes/reference/sources_and_naming.md`: `data/sources/` contents, naming, `scan_sources.py`, Устав templates, the inventory → extract → check workflow.
- `notes/reference/reader_pages.md`: design system, writing, quotes, publishing, page check and tag balance in full.
- `notes/reference/pii_policy.md`: the PII policy in full.
- `notes/reference/archived_profile_generator.md`: the archived profile generator, `relationship_type`, and the publishing history.
- `notes/reference/working_from_a_fresh_clone.md`: working without `data/sources/` or the full DB.
- `STYLE_GUIDE.md` (voice, transliteration, identifiers, confidence vocabulary, checklist) and `design/README.md` (tokens, grades).
