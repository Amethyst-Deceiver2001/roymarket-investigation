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

## Current state (queried 2026-09-19)

238 entities, 435 people, 7,699 sources, 23 quotes, 44 open questions.
67 entities and 35 people carry `sanctions[]`. 162 people are still
`_verified: false`. `facility_type` is set on 4 entities. `check_registry.py`:
0 errors, 16 warnings.

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
- **Гагаринг/Архангел**: Кулемин/Хабибулин DOB/address; «Открытое небо» candidate resolution; «Ворон-оптоволокно» entity; `tg-arkhangel-spetsnaza` legal entity; Одесская 48/3, Курская/Севастополь, НПО Эйлер threads (archive 3028-3044, 2610-2616).
- **ЦБСТ residents**: КРАМС and TSG Group identity resolution (archive ~3703); `ooo-npo-nebo` deliberately not wired as a ЦБСТ tie.
- **Never-screened manufacturers, EGRUL pulls, ФНС cross-references**: archive ~3970 and ~3497. The screening backlog has moved since; query `*_screened_at` instead of trusting those lists.
- **Pospekhov / «Системы Безопасности»**: one unwired lead from the bridge-figure triage (archive 4231-4286).

## Site structure (agreed 2026-09-20)

Direction chosen by the user with the peer sessions' input: a case-led front door.

- `docs/index.html`: generated landing page, five routes (Cases, Graph, Profiles, Guided read, Registry dossier).
- `docs/cases/`: one page per case, from `notes/case_study_<slug>.md`, built by `scripts/build_case_pages.py`. Built, unpublished until pushed: Архангел, Гагаринг. Planned (not started): ГОУДРОН, Овод/Черезов, Пиранья, Цыганов/Булат (the five excerpts in `~/.claude/plans/spicy-beaming-kite.md`) plus НПЦ БАСиРТК as a seventh, currently a paragraph in the dossier.
- `docs/dossier.html`: the former index.html, linked, not deleted.
- The live network-graph Artifact split in `~/.claude/plans/spicy-beaming-kite.md` (overview-first default) is still unexecuted; its case-excerpt list overlaps the cases above and its graph tokens are reused by `build_case_pages.py`.
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
