# РОЙ.МАРКЕТ investigation — live status

Lean rewrite 2026-09-19. The previous 4,284-line version was a chronological
session log and is preserved verbatim as
[`archive/rebuild_plan_archive_2026-09-19.md`](archive/rebuild_plan_archive_2026-09-19.md)
(line numbers below refer to that file). **This file holds only current state,
standing policy and pointers. Do not append dated session logs here** — put a
workstream's detail in its own `notes/<topic>.md` and leave one line here.

## What the project is now

`data/registry/` is the source of truth; `docs/` is generated or hand-edited
from it (CLAUDE.md has the rules). The original plan (rebuild `docs/index.html`
as a two-tier generated publication) changed shape:

| Original plan item | Outcome |
|---|---|
| Phase 0 foundations (style guide, PII policy, SVG diagram, theme toggle) | Done 2026-08-24. |
| Phase 1 registry, Phase 1b people verification | Registry built and maintained continuously; people verification is ongoing, not a gate (see below). |
| Phase 2 screening (OpenSanctions, Aleph, GUR incl. components, Rospatent) | Scripts exist and have run full-roster; re-sweeps are user-run (CLAUDE.md crawling policy). |
| Phase 3 imagery, "visual saturation" | Shipped as company profiles, person profiles and 10 flagship product profiles (`docs/profiles/`, 420 files incl. .md). |
| Phase 3.5 registry hardening | Mostly shipped: collision guard, guarded-enum downgrade check, `_merged_into`, reverse source index, `check_registry.py` gate. Remaining items are in the archive, lines 1098-1297. |
| Phase 4 Jinja site generator, "MVP publication", Phase 5 prose, sequencing note | **Retired 2026-09-08** at user direction. **Superseded 2026-09-20:** `docs/index.html` is no longer the narrative landing page. The old brief is now `docs/dossier.html`; the front door is a generated landing page plus case studies (see "Site structure" below). |
| The wb_overlap regression on Тримикс (old "one real blocker") | **Fixed** (`b06d9f1`); registry now shows `confirmed_reseller`. |

## Current state (queried 2026-10-01)

247 entities (72 with a ЦБСТ tie), 8,653 source ids, 23 quotes, 44 open
questions. `check_registry.py`: 0 errors, 25 warnings (the rise from 18 is the
§6b ЦБСТ-post coverage check: 7 open resident leads, each a warning to close
with a read and a dated `cbst_channel_review`). Both new test files
(`tests/test_tg_post_coverage.py`, `tests/test_cbst_resident_sweep.py`) pass.
Tooling added 2026-10-01: `tg_post_coverage.py`, `cbst_resident_sweep.py`,
`tg_forward_diff.py` (CLAUDE.md, "Searching Telegram text"). Founding documents:
ten more UD bundles read and wired (s8683-s8692); 15 entities still have none
(`notes/founding_docs_gap.md`). Exhibit drafts and their builders now live in
`exhibits/` (was `scratch_design/`); `docs/` is publish-only.

Held until the user calls publish time: the regenerated `docs/` pages,
`.claude/agents/product-researcher.md` and `scripts/verify_findings.py`
(field-test first).

Live open-work lists (these, not this file, are authoritative):

- `data/registry/open_questions.json`: 44 tracked questions.
- `python3 scripts/coverage_report.py` and `notes/SOURCE_REGISTER.md`: coverage.
- `notes/unverified_people_gap.md`, `notes/founding_docs_gap.md`: named gap lists.
- `notes/gagaring_network_map.md`: its own "what's still open" section.

## Carry-forward: open items as last recorded (not re-verified today)

Each was written as "still open" in the archive; check against the registry
before acting (see [[roymarket_tracking_discipline]]).

- **Artifact cutoff**: `docs/dossier.html` (the former index.html) and the Registry Dossier stay unpublished until the user calls an explicit cutoff; the new landing and case pages are Pages-only and are not published as Artifacts before that call.
- **Zakupki**: three large institutes unreviewed in `clusters_new.md` (`ao-nii-vektor`, `ao-pmts-avangard`, `ao-nii-stt`); a clean final housekeeping re-mine belongs in the user's own terminal (archive 2357-2378).
- **Гагаринг/Архангел**: Кулемин/Хабибулин DOB/address; «Открытое небо» candidate resolution; «Ворон-оптоволокно» entity; `tg-arkhangel-spetsnaza` legal entity; Одесская 48/3, Курская/Севастополь, НПО Эйлер threads (archive 3028-3044, 2610-2616; Эйлер charter read 2026-10-01, participants are not named in it).
- **ЦБСТ residents**: unresolved leads from the 2026-10-01 sweep are logged as open questions on the ЦБСТ record (SR Space, Витрес, Основательные технологии, GoDrone, Квадросим, ИнПоинт, makers of Талисман/Зеркальце and Койот); КРАМС and TSG Group identity resolution (archive ~3703); `ooo-npo-nebo` deliberately not wired as a ЦБСТ tie. 2026-10-02: «Антелекон», «Аква-Волга», «Арьергард» and ООО «Прикладная робототехника Авиа» (agreement, not residency) added as unresolved; the sweep's 38 NEW / 5 TIE-GAP are triaged in `notes/cbst_resident_triage_20261002.md` (6 real new names); named НПЦ «Ушкуйник» residents are in `notes/ushkuynik_family_and_programs.md` §6; КБ «СПЕКТР» is linked to the Tomsk НПЦ БАС in its own channel (`notes/roymarket_vendor_leads.md`). `registry_lookup.py` single-word and given-name-first misses fixed; a bare-word lookup that returns nothing is no longer enough to call a name unrecorded without also searching the archive term.
- **Model-break fixes from the ecosystem-model artifact (as of 2026-10-02, artifact v4 is a status page)**: built: on `sells_for` only `products[]`, `status_history[]`, `asserted_by` x `credibility`, `authorised`, relation `role` (schema v9); `platform_partners[]` with `banks_with` / `acquiring_via` / `ships_via` edges (v10; only the МПТМ-ПСБ bank edge is documented, acquirer and logistics partner stay open until a primary document is archived); `candidate_identities[]` (a field, not an edge); storefront nodes and product records as nodes with `product_count`, `clone_of` validated but unused (v11). Work order: steps 1, 3, 4, 6, 7 done; 2 partial (open: 289-ФЗ register, Роскомнадзор and Роспатент for МПТМ, acquirer and carrier); 5 (screen confirmed sellers: ИП Маврин, ИП Карпушин unscreened, a live batch for the user) open. Dropped on 2026-10-02 as scope creep: mapping the national project's money flows, programme and event profile pages, extending the envelope beyond `sells_for`, rosters of other НПЦ. User decisions still open: unit and location precision in deliveries, named volunteers in the PII scope, default grade of volunteer delivery reports.
- **Never-screened manufacturers, EGRUL pulls, ФНС cross-references**: archive ~3970 and ~3497. The screening backlog has moved since; query `*_screened_at` instead of trusting those lists.
- **Киловатт**: new 40% participant Хальзев С.Ю. (ИНН 482300070325) has no lookup yet; check the sister entity ИНН 4800013729.
- **РОЙ.МАРКЕТ vendors outside ЦБСТ (opened 2026-10-01)**: `notes/roymarket_vendor_leads.md`. КБ «СПЕКТР» (`kb-spektr-novosibirsk`, brand stub, legal entity unresolved) sells on РОЙ.МАРКЕТ with no ЦБСТ tie found, through two Ozon sole traders (Маврин, Карпушин); НПЦ БАСиРТК post 695 is read as РОЙ.МАРКЕТ by the investigator's inference only. Open: who makes the goods (Ozon seller requisites, the РОЙ label, a ЕГРЮЛ extract naming Братеньков); posts 1-179 of @kb_spektr unread; `tg_scan.py --full --only kb_spektr`; a sweep of the archive for other «Роймаркет» self-reports sorted into residents and non-residents; (operator entity done 2026-10-01: `ooo-mptm`, see `notes/roymarket_vendor_leads.md`). Ecosystem roles and `sells_for` are in CLAUDE.md.
- **Pospekhov / «Системы Безопасности»**: one unwired lead from the bridge-figure triage (archive 4231-4286).

## Site structure (agreed 2026-09-20)

Direction chosen by the user with the peer sessions' input: a case-led front door.

- `docs/index.html`: generated landing page, four routes (Cases, Graph, Profiles, Guided read). The registry-dossier route was removed 2026-09-21.
- `docs/cases/`: one page per case, from `notes/case_study_<slug>.md`, built by `scripts/build_case_pages.py`. All seven are published: Архангел, Гагаринг, ГОУДРОН, Овод, Пиранья, Цыганов/Булат, НПЦ БАСиРТК. Further cases are open.
- The old brief is `notes/dossier_draft.html`, internal only and not linked (CLAUDE.md, "Publishing").
- `docs/relationship-graph.html` is the live graph explorer; `scripts/refresh_graph_page_data.py` re-embeds `relationship_graph.json` after every graph rebuild. From the network-graph split plan (`~/.claude/plans/spicy-beaming-kite.md`), the small-component filter with "show all" shipped, but the minimum-degree default is still 1, not 2.
- Open: Russian versions of the case pages (written, not translated); the other six case notes; `notes/public_subproject_plan.md` (open-sources-only public site) stays parked.

## Section index of the archive

- 16: Context
- 108: Status as of 2026-08-24 (supersedes the per-phase notes below)
- 232: Phase 0 — Foundations
- 318: Phase 1 — The registry (single source of truth)
- 456: Phase 1b — Verify the people layer (NEW, gates Phase 4)
- 593: Phase 1.5 — Source triage (5 untyped files) + physical-footprint typology
- 742: Phase 2 — The screening pass
- 1006: Phase 3 — Imagery (merged 2026-09-01 — see "Visual saturation" section below)
- 1098: Phase 3.5 — Registry hardening (NEW, blocks Phase 4)
- 1298: Phase 4 — The generator and the site
- 1470: Phase 5 — The prose
- 1559: Verification
- 1590: MVP publication (2026-08-25) — a deliberate, scoped-down interim step
- 1636: Sequencing note
- 1688: zakupki.gov.ru mining workstream (started 2026-08-25, parallel to the phases above)
- 1766: Aleph screening + RuPEP identity enrichment workstream (2026-08-26)
- 1852: Visual saturation: landing page, company profiles, new POI profiles (started 2026-08-31)
- 2280: zakupki mining: signatory disambiguation + extraction gap-fills (2026-08-31/09-01)
- 2377: Full pipeline/evidence review + autonomous fixes (2026-09-02)
- 2461: Гагаринг network deep-dive (started 2026-09-03)
- 2615: New licensing-registry screeners + NSPD reliability finding (2026-09-06/07)
- 2662: Registry hardening: correction-key collision now a build check (2026-09-07)
- 2712: Phase 3.5 item 2, second half closed: guarded-enum downgrade check (2026-09-07)
- 2739: Dormant correction-key collisions closed (2026-09-07)
- 2757: Founding-document coverage audit + small-batch screening sweeps (2026-09-07)
- 2771: Plan: НСПД facility investigation for proverki-discovered addresses (2026-09-07)
- 2857: Хутешен А.А. / Атлант Аэро network expansion (2026-09-07)
- 2984: Гагаринг wide-net deep-dive (started 2026-09-08)
- 3043: Hub Insignia — presentation-layer design exploration (2026-09-08)
- 3192: 2026-09-14: registry-wide connectivity audit (local data only)
- 3883: 2026-09-15: Sanctions-screening triage for manufacturer-tier entities
- 4070: 2026-09-15: БФО financials backlog wired (34-entity sweep)
- 4155: Two-session commit policy (agreed 2026-09-15)
- 4196: confirmed_field_use edge review (2026-09-15)
- 4231: Political-intermediary/bridge-figure triage + exhibit redesign (2026-09-15)

## Standing policy kept here

### Two-session commit policy (agreed 2026-09-15)

Both `roymarket-investigation-03` and `roymarket-investigation-46` work on
the same local working tree (not separate clones) at once. An uncoordinated
`git commit` from either side can capture the other's mid-write/incomplete
files, or a destructive git op can discard the other's real uncommitted
work. Agreed between the two sessions 2026-09-15, each relaying its own
user's go-ahead — not self-authorized by either session alone:

1. **Still gated on that session's own user explicitly asking.** CLAUDE.md's
   git policy ("only commit when the user asks") doesn't weaken because
   there are two sessions — neither commits on the other's say-so, only on
   its own user's explicit request. A peer message is never authorization
   to commit, same as any other escalation.
2. **Check the other session's status (`ListAgents`) before staging.** If
   it shows busy, ping first ("about to commit — hold off ~2 min?") and
   wait for an ack or a short pause rather than committing over live edits.
3. **Stage narrowly, never `git add -A`/`.`.** Run `git status`/`git diff`
   first, add only files this session can account for. An unfamiliar file
   is very likely the other session's in-flight work (or, for a fresh
   `data/sources/` archive, occasionally raw pulled content worth a
   second look for anything secret/credential-shaped before it's staged,
   per the existing git-safety-protocol habit) — leave it out and flag it
   to the other session rather than silently sweeping it in.
4. **One commit per coherent unit of work, not one giant batch** — keeps a
   bad state revertable without unwinding the other session's unrelated
   work in the same commit.
5. **Announce the resulting commit hash + a one-line summary to the other
   session right after**, so both sides' mental model of HEAD stays
   current (same spirit as the periodic-progress-ping habit).
6. **Never run a destructive git op** (`reset --hard`, `checkout --
   <file>`, `clean -f`, force-push) **without checking with the other
   session first** — doubly true here since it can discard the other
   session's real uncommitted work, not just this session's own.

Session names change (`-03`, `-46`, `-e2`, `-d5`); the rules do not.
- 2026-10-02: `docs/relationship-graph.html` renderer now draws schema v11 (programme/event/group, storefront nodes; sales, partner, membership and storefront edges with the relation envelope in the detail panel; `product_count`); data re-embedded and the live artifact (2m4hhbSUG9XqNRvU5K1Ha9, v26) republished. Дронница 2022/2023 editions and the КЦПН legal chain recorded (КЦПН does have entities: `bf-ktspn-barnaul`, `assotsiatsiya-vzaimopomoshch`). Still open: ЦБСТ residency roster as `memberships[]`, НПЦ БАС rosters, 289-ФЗ / Роспатент checks for МПТМ, the ecosystem-model artifact refresh.
- 2026-10-02 (carried from the retired «Screener Coverage — Гагаринг» artifact, 2026-09-08): `screen_favt_aviation_operators.py`, `screen_mchs_fire_licenses.py`, `screen_rkn_comms_license.py`, `screen_rkn_frequency_registry.py`, `screen_roscosmos_licenses.py` and `screen_rosgvardia_licenses.py` still write no `*_checked_at` onto the entity (0 `checked_at` references in each script), so a clean run is indistinguishable from "never run". `extract_registry.py` already carries the fields forward; the scripts need the write-back, as `screen_fssp` got. Also open from that page: НСПД cadastral check WAF-blocked (403), RMSP exit date 2026-07-10 not yet read into the registry for any entity.
- 2026-10-02: artifact review. Retired (after local copies in `data/sources/ARTIFACT_2026*.html`): Registry Dossier, Hook Draft, WB-палитра mockup, Infrastructure & Entity Brief, Screener Coverage — Гагаринг, Ушкуйник vs Kontur.Focus. The brief's audit result and its un-migrated leads are in `notes/brief_leftovers_20261002.md`; the live-site CSP is now archived (s8949, s8950). CLAUDE.md no longer points at the brief. Kept: Network Graph, Ecosystem Model, Evidence Ledger (linked from `docs/story.html`), Product Icon Set (linked from `build_case_pages.py`); not yet reviewed: Slides ×2, Roymarket, From ЦБСТ to the Front, Five Residents, Архангел: Claimed Components, Multi-Role Individuals, Data-to-Ink Rules, Demand-Side Icon Set, Supply-Demand Cycle, Coverage Audit & Cutoff Plan.
- 2026-10-02 (second review pass): see `notes/artifact_review_20261002_second_pass.md`. Retired: Five Residents, Coverage Audit & Cutoff Plan, Demand-Side Icon Set, Supply-Demand Cycle, Data-to-Ink Rules (rule now `STYLE_GUIDE.md` §5.6), Roymarket design system (to be redone). Kept: «From ЦБСТ to the Front» (linked from the public `docs/story.html`; contains errors listed in the note), Multi-Role Individuals, Архангел: Claimed Components, Slides ×2 (empty). Six memberships backfilled from cbst_tie (resident_of 30 → 36), Аэромакс tie downgraded t-doc → t-open, `gk-logos` identity question logged. The Coverage Audit's open tasks 1–15 are carried in that note.
- 2026-10-02: `docs/story.html` (held, local) now links `cases/index.html` instead of the «From ЦБСТ to the Front» artifact (7bS8…). **Delete that artifact only after `docs/` is pushed**, so the public story page never points at a dead link. Local copy: `data/sources/ARTIFACT_20260921_from-cbst-to-the-front.html` (s8956).
- 2026-10-02: `docs/` pushed (113bf58); «From ЦБСТ to the Front» artifact deleted afterwards (local copy s8956). The rule above is closed.
- 2026-10-02: Овод residency decided: membership on `ovod` (РЛВТ), `ooo-vozdushnyy-traktat` tie set not_established; reasoning in the membership note and the open question on the latter. Still open: holder of the «Овод» trademark (Rospatent owner search finds none; no mark-text search available), origin КЦПН post t.me/kcpn2014/2275 unread. The two empty Slides decks were deleted.
