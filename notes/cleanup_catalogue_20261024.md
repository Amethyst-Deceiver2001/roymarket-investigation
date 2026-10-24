# Cleanup catalogue: duplicates, conflicting versions, abandoned angles (24.10.2026)

Internal. Written for the user, to decide what to move, merge or delete. Nothing was deleted or moved in making it. The review covered the working tree on this machine: the full repo, the scrape database and the media working folder, but not the `data/sources/` archive, which is not here. The 21.10 review (`repo_review_20261021.md` §3) found some of the same things; each item says whether it is still open from there or new.

Proposed action tags: **archive** = `git mv` into an `archive/` folder (history kept), **delete** = remove (git history keeps it), **merge** = fold into the live file, **go-ahead** = touches `docs/`, branches or a job, so it needs the user.

## 1. Public exposure (do first)

**Done 24.10.2026 (user go-ahead):** the 109 files moved to `exhibits/images/profiles/` (commit 53e30f3), with registry paths repointed and the people matrix reading either place. Checked afterwards: the GitHub Pages API returns 404 for this repo (it is private, and Pages is not enabled), so `docs/` was not being served at the time. The move matters for when Pages is switched back on.

| What | Detail | Action |
|---|---|---|
| `docs/images/`: 109 of 111 files are used by no page | 18 MB. Pages serves them at guessable URLs: 31 portraits (RuPEP, Leader-ID, Wikimedia, press), Barashkov's portrait, a Gagaring graduation crop, an Arkhangel recruitment poster, Arkhangel course material. The pages that showed them were withdrawn on 02.10. *Still open from 21.10.* | go-ahead: move out of `docs/` into `exhibits/images/` (or a gitignored folder), repoint the `photo`/`image` paths in `people.json` and `entities.json` |
| `docs/index.html` is the 05.10 build | The builder has moved on 18 days and four versions since (the new opening, the people, company and Arkhangel cards). The public page shows 05.10 numbers. That is correct until the go-ahead, but the three copies (`docs/index.html`, `exhibits/landing.html`, untracked `exhibits/landing_preview.html`) drift. | keep; regenerate the public copy only on go-ahead |
| `docs/fonts/`: the IBM Plex Sans 600 files are byte-identical to the 400 ones | four pairs (latin, latin-ext, cyrillic, cyrillic-ext). Google serves Plex Sans as one variable font, so both weights render correctly; a reader downloads the same file twice under two names. Plex Mono's two weights differ. | low: point both `@font-face` weights at one file (`font-weight: 400 600`) |

## 2. Exact duplicates

- **Images in both `docs/images/` and `exhibits/images/media/`**: 13 pairs, 4.7 MB (Arkhangel course images m0046–m0054, the Eksplomet, GK Logos and Trimiks logos, m0001). They go away with the move in §1.
- **`sources.json`: 617 groups of records with byte-identical files** (1,415 records; only 15 carry `duplicate_of`). Mostly the same zakupki attachment saved under two to six names (531 groups, typeless), plus 63 charter bundles and 15 court files. Only **3 groups** have two or more records cited separately, so readers rarely see a double citation. *New.* Action: a one-off pass that sets `duplicate_of` on the later record of each group (the citation code already follows it). It needs the archive machine, because the hash is checked against the file.
- `tests/fixtures/zakupki_object_absent.html` and `zakupki_no_price.html` are identical (both empty). That is harmless and probably deliberate.

## 3. Conflicting or parallel versions

| Pair | Detail | Proposal |
|---|---|---|
| `data/registry/handovers.json` (42 handovers, 2023–2026, three channels) vs `products.json` `deliveries[]` (26, «Булат» and «Капюшон») | Two delivery models with no overlap by channel and post. `handovers.json` is read by the status board, `daily_mac.py` and `unit_lookup.py`; the chain views and the story read `deliveries[]`. A reader page built from one will miss the other. | decide which is the record; probably move product-specific rows into `deliveries[]` and keep `handovers.json` for handovers that name no registry product |
| `scripts/run_pipeline.py` + `notes/full_pipeline_catalogue.md` (08.09) vs `scripts/daily_mac.py` (05.10) | Two "run everything" entry points. The daily round is the live one; `run_pipeline.py` was last touched 02.10. | archive `run_pipeline.py` and the catalogue, or rewrite the catalogue as a map of `daily_mac.py` |
| Three methodology documents: `notes/methodology_draft.md` (the reader-facing draft), `source_expansion_methodology.md` (68 KB, 30.09), `SOURCE_REGISTER.md` (48 KB, 02.10), plus `deep_research_registries_20260906.md` | They overlap on which registries to check and how. | keep `methodology_draft.md` and `SOURCE_REGISTER.md`; archive the other two once anything live is moved over |
| Sanctions gap: `exhibits/sanctions_gap.md`/`.csv` (06.10), `notes/sanctions_gap_report_draft_20261005.md`, `notes/sanctions_name_check_20261004.md` | All are frozen as of the last watch run (05.10), which has since been retired. The draft says it supersedes the 04.10 draft, which is no longer in `notes/`. | keep the 05.10 draft as the live text; archive the 04.10 name check |
| Presence lists: `notes/entities_without_telegram.md` and `notes/entity_presence_inventory.md` (both 01.10), script `entity_presence_inventory.py` (nothing calls it) | They report the same data from two angles. | merge into one, or archive both: the status board now flags a missing channel |
| Gap lists: `unverified_people_gap.md` (07.09), `founding_docs_gap.md` (01.10), `okved_mismatches.md` (18.08), `data/registry/_docs_registry_gap_list_2026-09-16.md`, `_source_coverage_audit_2026-09-15.md` | Point-in-time snapshots. The status board computes the same gaps live. | archive |
| Case notes `notes/case_study_{bulat,goudron,ovod,piranya}.md` vs company pages `exhibits/company_{ooo-trimiks,ooo-goudron,ovod,ooo-skb-piranya}.html` | The case pages were withdrawn on 02.10. The new company pages are built from the registry and can now state things the hand-written notes say differently (for example, a revenue headline from an older filing). | keep the notes as background, mark them "superseded by the company page" in their first line, and check the headlines against the registry before anyone quotes them |
| `exhibits/arkhangel_exhibit.html` (hand-made, 21.09) vs `exhibits/arkhangel.html` (generated) | The builder says it replaces the hand-made page. | archive `arkhangel_exhibit.html` |
| `exhibits/affiliation_matrix.html` + `scripts/build_affiliation_matrix.py` vs `exhibits/people_matrix.html` + `build_people_matrix.py` | The same: the new builder replaces the old one. | archive the old pair |
| CLAUDE.md vs the machine | It says the repo is in `~/Downloads`, and the launchd plist's `WorkingDirectory` is `/Users/ak/Downloads/roymarket-investigation`. This Mac has it at `~/Projects`, and no launch agent is installed. It also says `data/sources/` is "~424MB" and `config/channels.txt` holds "the 11 channels" (171 lines now). | correct the facts once you say which machine is main |

## 4. Abandoned angles and retired builds still in the live folders

**Exhibits** (nothing in code or notes refers to these):
- `exhibits/cbst_orbit.html` + `cbst_orbit_build_svg.py`: the hub-and-satellites picture of the first hypothesis, retired 02.10.
- `exhibits/case_study_excerpts.html`, `case_study_build_page.py`, `case_study_build_svgs.py`, `case_study_extract.py`, plus `scripts/build_case_studies.py`: the case-page build, archived 02.10. CLAUDE.md says its generators moved to `scripts/archive/`, but these were left behind.
- `exhibits/cbst_chain.html`, `evidence_ledger.html` + `scripts/build_evidence_ledger.py`: early chain and ledger mockups (01.10), replaced by the chain views.
- `exhibits/coverage_audit.html`, `data_to_ink_system.html`, `roymarket-supply-demand-cycle.html`, `demand_side_icon_set.html`, `product_icon_set.html`: design studies from before the design system. `classify_product_icon.py` still uses the 17-category icon set, so keep `product_icon_set.html` if those icons come back.
- `exhibits/Main.dc.html`: an export from an external design tool that needs a `support.js` that isn't in the repo, so it cannot render.
- `exhibits/build_explainer_video.py` (07.10): the draft video for Story 1, which nothing calls. Keep if the video is still planned.

**Scripts.** These are one-off migrations or finished passes:
- `profile_text.py` is used only by the archived generators, so it belongs in `scripts/archive/`.
- One-off migrations: `wire_role_edges_from_entity_history.py`, `wire_upr_uchr_sources.py`.
- Single passes, each with output already on file: `mine_components.py`, `scan_source_video_links.py`, `promo_video_sources.py`, `extract_products.py`, `find_patent_mentions.py`, `enrich_egrip_hits.py`, `har_tools.py`, `parse_kontur_focus.py`, `cbst_roster_derive.py`, `aleph_followup.py`, `screen_leader_id.py`, `zakupki_customer_clusters.py`.
- Rospatent has six scripts: `rospatent_patent_search`, `_searchplatform_search`, `_tm_search`, `_tm_ws_search`, `_archive_patents`, `_download_pdfs`. Before archiving any of them, find out which ones still work against the live site.

Action: archive into `scripts/archive/` after one check per script that no doc tells a session to run it. `notes/commands.md` (02.09) still lists `zakupki_customer_clusters.py` in its housekeeping bundle; update it at the same time.

**Notes** (finished work logs or parked plans; move to `notes/archive/`):
- Parked plan: `public_subproject_plan.md` (parked 08.09; the `public/` folder it plans was never made).
- Work logs: `hub_insignia_design_notes.md` (marked historical), `artifact_review_20261002_second_pass.md`, `brief_leftovers_20261002.md`, `media_backfill_20261002.md`, `cbst_resident_triage_20261002.md`, `cbst_roster_derived_20261002.md`, `delivery_signal_scan_20261002.md`, `scan_wiring_20261003.md`, `packet_verification_20261003.md`, `presentation_review.md` (30.09; the story outline and the rebuild plan replace it), `ddosecrets_catalog_survey.md`, `wayback_quota_postmortem_20261022.md`.
- `needs_mac_20261022.md` and its branch: keep until the archive machine is back, then close.

**Registry side files** (outputs from passes that nothing reads now):
- Nothing reads: `video_observations.json` (20.09), `_components_mined_video.*` (19.09), `_informal_ties_leads.md`, `_political_intermediary_leads.md` (15.09).
- `_candidate_channels.md` (160 KB, 19.09) and `_product_scan.json` (1.2 MB) are each read by one script. Keep them if those scripts stay, otherwise archive them with the scripts.
- The two unread lead files still hold open leads (ООО «КИНГПРО» as a resident without a tie; `kb-germes` as a possible duplicate of `npo-kaysant`, from the 21.10 review). Move those into `open_questions` before archiving.

**Stalled pipelines.** These are not abandoned on purpose:
- The daily round wrote its last report on 06.10 (`data/watch/daily/`). Retired as a scheduled job 24.10.2026 (user); it runs by hand, and so do first reading and the exports.
- First reading stopped on 04.10 (`notes/first_reading/`).
- `exports/` is from 02.10.
- The status board's `board.json` updates only on commits that touch the registry.

These are the 21.10 review's §1.2, still open. They restart when the archive machine runs again.


**Step 2 done 24.10.2026 (user go-ahead): 38 files archived with `git mv`, so history follows them.**
- `exhibits/archive/retired_2026-10-24/` (15): the orbit picture and its builder, the five case-page pieces (`case_study_*`, excerpts page), `cbst_chain`, `evidence_ledger`, `coverage_audit`, `data_to_ink_system`, `roymarket-supply-demand-cycle`, `demand_side_icon_set`, `Main.dc.html`, `arkhangel_exhibit`, `affiliation_matrix`.
- `scripts/archive/` (15): `build_case_studies`, `build_evidence_ledger`, `build_affiliation_matrix`, `profile_text`, `wire_role_edges_from_entity_history`, `mine_components`, `scan_source_video_links`, `promo_video_sources`, `extract_products`, `find_patent_mentions`, `parse_kontur_focus`, `cbst_roster_derive`, `screen_leader_id`, `run_pipeline`, `entity_presence_inventory`.
- `notes/archive/` (8): `public_subproject_plan`, `ddosecrets_catalog_survey`, `deep_research_registries_20260906`, `sanctions_name_check_20261004`, `okved_mismatches`, `entities_without_telegram`, `entity_presence_inventory`, `full_pipeline_catalogue`.
- Archived scripts keep their old `REPO = parent.parent` paths and will not run from the archive without an edit; the existing `scripts/archive/` files are the same.
- Docstrings in `build_people_matrix.py` and `build_arkhangel_page.py` now point at the archived paths. Registry checker: 0 errors, same 26 warnings; all tests pass.

**Left in place on purpose, because live code or rules still cite them:** `wire_upr_uchr_sources.py` (named in `screen_upr_uchr.py`'s instructions), `zakupki_customer_clusters.py` (in the housekeeping bundle in `commands.md`), `aleph_followup.py` (README and two registry notes), `enrich_egrip_hits.py` (`script_notes.md`), `har_tools.py` (README), `presentation_review.md` (three scripts cite its sections as their origin), `source_expansion_methodology.md` (cited by `screen_proverki.py`), `hub_insignia_design_notes.md` (cited by `design/README.md`), and the notes CLAUDE.md, the plan or the registry point to (`brief_leftovers`, `media_backfill`, `cbst_resident_triage`, `cbst_roster_derived`, `scan_wiring`, `artifact_review_…second_pass`, `unverified_people_gap`, `founding_docs_gap`). The Rospatent scripts were not touched: they need a check against the live site first.


**Posts 382, 397 and 448 combined 24.10.2026 (user: "3 combine").** The three pairs of «Булат» and «Капюшон» rows are now one event each with two items (65 events), and the «Капюшон» item keeps its old id so its view and media are unchanged (`scripts/archive/combine_double_product_events_20261024.py`). Rebuilt every output before and after: the «Булат» chain, the company page, both landing pages and the story are byte-identical; the «Капюшон» page changes only in two English recipient glosses (now the «Булат» page's wording) and the board counts three recipients once, not twice. Where the two rows differed the fuller value was kept: the named carrier of the 17.02.2025 handover (fund representatives with Сидякин and a party project lead) instead of "not stated".

**Fonts deduplicated 24.10.2026 (user: "1 go"):** IBM Plex Sans is a variable font (wght 100–700), so `docs/fonts/` keeps one file per subset, `ibm-plex-sans-400-600-<subset>.woff2`, declared `font-weight: 400 600` (24 files → 20, 110 KB less). `design/fetch_fonts.py` merges weights that share a file the same way on a re-run. Checked in headless Firefox: 600 renders as the real weight with `font-synthesis: none`. The landing page itself is not republished (user: hold until the artifacts are polished).

**CLAUDE.md rewritten 24.10.2026 (user: "lean rulebook", commit 9325263):** 84 KB down to 18 KB; the detail moved word for word into six `notes/reference/` files. The §3 machine facts are fixed: ~/Downloads and launchd are now history, 171 channels, `data/sources` size per machine.

**Step 3a done 24.10.2026 (user: "merge deliveries into a single file"):** `handovers.json` (42 rows) and the `deliveries[]` on «Булат» and «Капюшон» (26 rows) are now `data/registry/deliveries.json`, 68 events, none duplicated (the two lists shared no post). `scripts/deliveries.py` holds the schema and `load_products()`, which gives every reader a product's deliveries in the shape it already used. Checked by rebuilding every page and printout before and after: both chain views, the company page, the story, both landing pages and the product printouts are byte-identical; evidence packets differ only by their generation date. Findings on the way: three ЦБСТ events pointed at a donor slug (`ano-cbst`) that no entity has (fixed to the real slug); posts 382, 397 and 448 each report both products to one recipient and are two rows (to combine later, which changes ids media point at); `bulat-d05` and `kapyushon-d02` name units that resolve to unit records but have no `recipient_unit_slug` yet (a decision for the reader of the posts, not set here); 33 of the 42 handover posts have no source record yet. The board's unit line now counts recipients that name a unit separately from those that name only a direction or a group (36 of 38 resolve; 30 name no unit). Migration script: `scripts/archive/migrate_deliveries_20261024.py`. Not combined, not renumbered, and no `asserted_by` upgraded: the 42 handover rows got the standing default (`self`, `single`) because the old file carried none.

## 5. Branches (all fully merged into main, 0 commits ahead)

**Done 24.10.2026 (user go-ahead):** all seven deleted locally and on origin; `main` and `watch/sanctions` remain.

`local/needs-mac-20261022`, `retire-sanctions-watch` (local and remote), `origin/claude/project-thread-{1w20sw,27kwn6,55iyhs,qtsqtj}`, `origin/fix/english-first-media-captions`. Keep `origin/watch/sanctions`: it holds the frozen 05.10 snapshot. *Partly open from 21.10*: the earlier `pull-inbox`, `copilot/…` and `laughing-brahmagupta` branches are already gone. Action: go-ahead, then delete; nothing is lost.

## 6. Registry identity checks (no problem found)

- No duplicate ИНН among the 252 live entities. No two live people share a full name.
- The four ООО «Архангел» records (Запорожье, Истра, Мелитополь, Крым) share a legal name and are separate companies.
- `dmitriy-peskov` has the role of the presidential special representative (Платформа НТИ), and its portrait file is named for Дмитрий **Николаевич**. The record's `fio_ru` is only «Дмитрий Песков», though, the same as the Kremlin spokesman Дмитрий Сергеевич. Add the patronymic, so that no reader or screening match confuses the two.

## Suggested order

1. §1 docs images and §5 branches: one go-ahead each, low effort.
2. §4 archive moves for exhibits, scripts and notes: one commit, inside the paths the main session may commit (`exhibits/`, `notes/`, `scripts/`). Each move is checked against code references first.
3. §3 decisions: handovers vs deliveries, run_pipeline vs daily_mac, the methodology documents. These need a call from the user before any merge.
4. §2 `duplicate_of` pass and the CLAUDE.md fact fixes: on the archive machine.
