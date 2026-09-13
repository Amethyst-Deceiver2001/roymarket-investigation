# Full pipeline catalogue (2026-09-08)

Written in response to a direct request to review the whole pipeline — every
source this investigation has ever used or reverse-engineered — and unify it
into one documented flow, plus a relationship-graph visualization. This is
the map; `scripts/run_pipeline.py` is the executable form of it.

The catalogue below is organized by what each source *is*, not by when it
was built. Every entry already exists as a script in `scripts/`; nothing here
is new collection, only new organization. Per CLAUDE.md's crawling-jobs
policy, each entry is tagged **[local]** (safe to run directly/repeatedly,
no network) or **[network — hand to user]** (a full-roster sweep must be
run in the user's own terminal, never backgrounded); a single `--slug`/`--inn`
lookup on a **[network]** script is still fine to run inline for spot-checks.

## Stage 0 — collection

| Script | Source | Class |
|---|---|---|
| `tg_scan.py` | This repo's own Telethon scraper over `config/channels.txt` | network — hand to user |
| `tg_scan_users.py` | Channel/chat membership roster (distinct from message history) | network — hand to user |
| `vk_fetch.py` | VK API wall/newsfeed pulls | network — hand to user |
| `tg_media_pull.py` | Photo/video-still evidence from already-scraped posts (`t.me/s/` previews, no auth) | network, capped at 15/run — inline-class |
| `export_from_wb_watch.py` | Historical bootstrap only — not ongoing collection | n/a |

## Stage 1 — local mining over already-collected data

| Script | What it extracts | Class |
|---|---|---|
| `mine_leads.py` | Entities/products/ИНН/ОГРН/role+name from Telegram post text | local |
| `mine_zakupki.py` | Structured contract data (price, subject, signatories, docx text) from `data/sources/ZAKUPKI_*` | local |
| `extract_products.py` | Product/brand catalog sweep over scraped channels | local |
| `find_patent_mentions.py` | Patent/UM/ID number sweep over `data/sources/` | local |
| `scan_sources.py` | ИНН/ОГРН/entity/person extraction over every file in `data/sources/` → `MANIFEST.md` | local |
| `extract_ids.py` | General-purpose CLI: pipe any text through it for the same pattern set | local |
| `check_egrul_flags.py` | EGRUL access-restriction/disavowal marker detection on pasted extract text | local |

## Stage 1.5 — Kontur.Focus Pro exports (recurring manual input, added 2026-09-08)

| Script | Source | Class |
|---|---|---|
| `parse_kontur_focus.py --pdf <path> --slug <slug> --source-id <sNNNN>` | Kontur.Focus Pro company-profile PDF, the user's own paid-subscription export, dropped into `data/sources/` | local |

Not a screener against a live third-party service — the user pulls these
themselves from their own Kontur.Focus Pro subscription and hands the PDF
over; this only parses an already-downloaded file. Confirmed on the first
real run (АНО «НПЦ «Ушкуйник»», `data/sources/CHECKO_5300010714_20260908_
ano-npts-ushkuynik.pdf`, source `s7369`): 19 ОКВЭД codes, 4 founders, 8
beneficial owners (Kontur's own computed chain), 2 litigation cases, 36
government contracts (participant + customer roles), full 4-year financials
across all 4 forms (matches `parse_bfo_financials.py`'s own numbers), the
ЭКГ rating (matches `screen_ekg_rating.py`'s live pull exactly — 83/15/32/
36 both ways), and 23 "Ближайшие связи" affiliated-network entities, 21 of
them not previously in this project's registry at all — sister АНО «НПЦ
БАС» centres in other regions, ФОНД НТИ, the founding ministry, and several
unrelated-looking commercial/political entities worth individual triage.

Writes a compact raw summary (`kontur_focus_matches[]` /
`kontur_focus_checked_at`) directly onto the matched entity in
`entities.json` (added to `ENTITY_CARRY_FORWARD_FIELDS`), and the full
parsed structure to `data/registry/_kontur_focus_cache.json` keyed by ИНН.
Does **not** auto-wire litigation/government_contracts/founders_history —
those need human dedup against what zakupki_batch_pull.py/kad.arbitr.ru
pulls may already have recorded; the script prints a review scaffold of
what looks new instead, the same discipline as `_scaffold_leads.json`.

## Stage 2 — registry identifiers & founding documents

| Script | Source | Class |
|---|---|---|
| `egrul_batch_pull.py` | egrul.nalog.ru open lookup (no captcha) — synchronized baseline snapshot | network — hand to user |
| `egrul_vypiska_pull.py` | Full signed ЕГРЮЛ/ЕГРИП выписка PDF (vyp-request/status/download flow) | network — hand to user |
| `parse_egrul_vypiska.py` | Parser for the signed выписка PDFs above | local |
| `crosscheck_egrul.py` | Phase-1 automated cross-check of every entity against fresh EGRUL | network — hand to user |
| `screen_egrip_ip.py` | egrul.nalog.ru ЕГРИП (individual entrepreneur) lookup, keyed on personal ИНН | network — hand to user |
| `enrich_egrip_hits.py` | rusprofile.ru enrichment of ИП hits — **decoy-content risk, see memory** | network — hand to user |
| `checko_pull.py` | checko.ru company-data aggregator | network — hand to user |

## Stage 3 — financials

| Script | Source | Class |
|---|---|---|
| `bfo_pull.py` | bo.nalog.gov.ru signed БФО filings (uncaptcha'd download endpoint) | network — hand to user |
| `parse_bfo_financials.py` | Parser: P&L for commercial entities, ОЦИС (0710003) for non-profits — see the all-null-is-a-parser-bug lesson in memory | local |

## Stage 4 — procurement (44-ФЗ / 223-ФЗ)

| Script | Source | Class |
|---|---|---|
| `zakupki_batch_pull.py` | zakupki.gov.ru contract search (`supplierTitle` param) + contract cards + attachment fetch | network — hand to user |
| `zakupki_coverage.py` | "Are we done with zakupki?" report — reads `zakupki_review` as authoritative | local |
| `zakupki_customer_clusters.py` | Clusters archived-but-unwired contracts by customer | local |
| `zakupki_signatory_diff.py` | Diffs docx-mined signatories/emails against registry `director`/contacts | local |
| `screen_rnp.py` | zakupki.gov.ru РНП (реестр недобросовестных поставщиков) | network — hand to user |

## Stage 5 — sanctions, PEP & watchlists

| Script | Source | Class |
|---|---|---|
| `screen_opensanctions.py` | OpenSanctions batch match (journalist API key) | network — hand to user |
| `screen_gur.py` | war-sanctions.gur.gov.ua — legal entities & UAV companies sections | network — hand to user |
| `screen_gur_components.py` | GUR's components-teardown catalogue, matched against product names | network — hand to user |
| `screen_aleph.py` / `aleph_followup.py` | OCCRP Aleph entity search + structured follow-up | network — hand to user |
| `screen_disqualified.py` | ФНС реестр дисквалифицированных лиц (pb.nalog.ru search-rdl) | network — hand to user |
| `screen_subsidiary.py` | ФНС subsidiary-liability cross-check by ИНН+ФИО (no DOB field) | network — hand to user |
| `screen_upr_uchr.py` | ФНС director/founder cross-reference | network — hand to user |
| `screen_rom.py` | ФНС Реестр обеспечительных мер | network — hand to user |
| `screen_pledge_registry.py` | Federal Notary Chamber pledge registry | network — hand to user |
| `screen_fssp_opendata.py` | ФССП open-data bulk debt CSV | network — hand to user |

## Stage 6 — sector licenses & regulatory registries

| Script | Source | Class |
|---|---|---|
| `fstec_pull.py` | ФСТЭК reg1/reg2 licence registries | network — hand to user |
| `screen_rosgvardia_licenses.py` | Rosgvardia's 5 open-data license registries | network — hand to user |
| `screen_mchs_fire_licenses.py` | МЧС fire-safety licenses | network — hand to user |
| `screen_favt_aviation_operators.py` | favt.gov.ru aviation-works operator registry | network — hand to user |
| `screen_roscosmos_licenses.py` | Roscosmos space-activity licenses | network — hand to user |
| `screen_rkn_comms_license.py` | RKN communications-license registry | network — hand to user |
| `screen_rkn_frequency_registry.py` | RKN Единый реестр частотных присвоений | network — hand to user |
| `pub_fsa_pull.py` | pub.fsa.gov.ru ФГИС Росаккредитация | network — hand to user |
| `reestr_digital_pull.py` | reestr.digital.gov.ru accredited-IT-company registry | network — hand to user |
| `screen_fas_br.py` | br.fas.gov.ru База решений и правовых актов ФАС | network — hand to user |
| `screen_proverki.py` | proverki.gov.ru ФГИС Единый реестр проверок | network — hand to user |
| `screen_rmsp.py` | rmsp.nalog.ru Единый реестр СМСП | network — hand to user |
| `screen_ekg_rating.py` | экг-рейтинг.рф — third-party ESG/reputation index (added 2026-09-08) | network — hand to user |

## Stage 7 — IP (patents & trademarks)

| Script | Source | Class |
|---|---|---|
| `rospatent_patent_search.py` | Rospatent open-data bulk patent export | local (bulk file, no live call) |
| `rospatent_searchplatform_search.py` | searchplatform.rospatent.gov.ru live JSON API | network — hand to user |
| `rospatent_tm_search.py` | Rospatent open-data bulk trademark export | local |
| `rospatent_tm_ws_search.py` | searchplatform.rospatent.gov.ru live trademark search (full-roster) | network — hand to user |
| `rospatent_archive_patents.py` / `rospatent_download_pdfs.py` | Archive full patent documents/PDFs | network — hand to user |
| `fips_patent_lookup.py` / `fips_trademark_enrich.py` | fips.ru direct lookups (raw curl + windows-1251 — **never trust WebFetch on fips.ru**, see memory) | network — inline single-lookup |

## Stage 8 — state-industry programs & directories

| Script | Source | Class |
|---|---|---|
| `screen_rk2035_bas_registry.py` | rk.2035.university open БАС industry directory | network — hand to user |
| `gisp_goods_pull.js` | gisp.gov.ru product catalog — **browser-console snippet, not a Python script** (WAF-gated) | network — browser, hand to user |
| `screen_leader_id.py` | leader-id.ru — **login-gated, blocked pending a proper session capture** | blocked |

## Stage 9 — property & geography

| Script | Source | Class |
|---|---|---|
| `nspd_lookup.py` | Rosreestr НСПД single property/building lookup | inline reconnaissance |
| `screen_nspd_addresses.py` | НСПД cross-check of every entity's known address(es) | network — hand to user |

## Stage 10 — marketplace overlap

| Script | Source | Class |
|---|---|---|
| `screen_wb.py` | Wildberries seller-record cross-check against entity ИНН | network — hand to user |

## Stage 11 — assembly, verification, and derived views

| Script | What it does | Class |
|---|---|---|
| `inventory_sources.py` | Types + dates every file in `data/sources/`, caches to `_source_content_cache.json` | local |
| `extract_registry.py` | Rebuilds `entities.json`/`people.json` from cache + `corrections_*.json` | local |
| `check_registry.py` | ИНН/ОГРН checksum validation, registry shape/carry-forward guard, and exact deterministic relationship-graph rebuild/contract validation | local |
| `reverse_source_index.py` | Derives entity/person ↔ source citation map | local |
| `coverage_report.py` | Per-entity coverage matrix across every screening dimension | local |
| `build_company_profile.py` | Generates `docs/profiles/<slug>.{html,md}` from the registry | local |
| `check_tag_balance.py` | HTML tag-balance check before publish | local |
| `build_relationship_graph.py` | Nodes/edges from ownership/directorship/founding/role/product fields; excludes tombstones and writes cited/current/core/evidence-gap derived views | local |
| `graph_quality_report.py` | Deterministic relationship-graph baseline (schema, parity, citation, temporal, stub, and view counts) | local |
| `build_graph_explorer.py` | Generates an accessible, evidence-first explorer from the validated canonical graph, derived views, and directly attached source metadata | local |

**Blocked/parked, for completeness**: `kad.arbitr.ru` (DDoS-Guard, no
scripting route — manual browser search only), `leader-id.ru` (session
capture had no usable cookie), `reveng.ee` (needs a user-requested API key
first), `rupep.org` (Cloudflare-blocks scripts, browser-only).

## What's genuinely new here vs. what already existed

Every individual source above was already reverse-engineered and scripted
before this session — the survey didn't find a new source. What was missing
was (a) a single document naming all ~45 of them in one place organized by
what they screen, and (b) the beneficial-ownership/affiliation graph layer
identified in the "what would bring us closer to Kontur's scope" discussion
— the one gap judged actually worth closing, since the data to build it
(`founders`/`founders_history`/`parents`/`subsidiaries`/`related_entities`/
`director`/`director_history`/`roles[]`/`other_entities[]`) was already
sitting in the registry, just never assembled into a graph.

`scripts/build_relationship_graph.py` closes that gap: it resolves those
free-text name fields against both live registries via normalized matching,
excludes `_merged_into` tombstones, and writes the canonical
`data/registry/relationship_graph.json` plus
`relationship_graph_views.json`.  The derived views are intentionally
evidence-first: `cited_only` uses only an edge's originating `source_id`;
`current_only` requires a directly cited, dated historical-record entry;
`core_network` is a one-hop ЦБСТ-core view; and `evidence_gaps` makes
uncited edges visible without assigning them a source. Product-node
classifications only use explicit multirotor or vehicle-mounted wording;
generic UAV/jammer text remains `unknown`/`unclassified`. Unresolved names
are retained as visible stub nodes rather than silently dropped, and
`graph_quality_report.py` provides a deterministic baseline for every run.
`check_registry.py` rebuilds the canonical graph from the live registry and
requires the serialized graph and each view to match exactly, so a
well-formed but stale edge or substituted known source_id cannot pass.
