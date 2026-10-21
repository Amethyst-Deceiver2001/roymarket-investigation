# Repo review and course of action (21.10.2026, cloud session, no local sources)

Written for the user. Read from the remote repo only: no `data/sources/`, no
`data/roymarket.db`, and this cloud environment's network policy refuses every
source host (ЕГРЮЛ, БФО, zakupki, t.me, web.archive.org, OpenSanctions, OFAC,
GUR, kad.arbitr, Rospatent, roimarket.ru). Nothing below is a registry fact;
each item names what it rests on.

Health at a glance: tests 23/23 pass; `check_registry.py --no-local-files` 0
errors, 26 warnings; last commit on main 09.10.2026; last daily round report
06.10; newest scraped post 04.10; last sanctions watch 05.10.

## 1. Broken: fix first

### 1.1 GitHub Actions has run nothing since 10.10 (most likely the minutes quota)

Every scheduled run since 10.10 failed in 3-4 seconds with no runner assigned
(`runner_id: 0`, no log): wayback runs 9-20 (10.10-21.10) and sanctions-watch
runs 11-12 (12.10 and 19.10). Cause, inferred from the run history: each
nightly wayback run from 04.10 to 09.10 lasted about 5 h 15 min (it runs into
its own 315-minute `timeout`), so six runs used ≈1,890 runner-minutes, plus
≈160 one-minute `checks` runs. A private repo on GitHub Free gets 2,000
minutes a month. The failures began the day after that total was crossed.
To confirm: Settings → Billing → Usage (Actions minutes, spending limit).

Consequences:
- **Two weekly sanctions watches missed** (12.10, 19.10). Any new EU/US/UK/Swiss
  listing of a registry ИНН since 05.10 is undetected.
- **CI is off.** The next push to main will show red for want of a runner, not
  because of the code.
- Wayback captures have stopped (low cost: the archive is a nice-to-have next
  to the RFC 3161 stamps).

Proposed fix (a workflow cap change, so it needs the user's go-ahead):
- wayback: weekly instead of nightly, `timeout-minutes: 60` and a matching
  `timeout 50m`, or move it to the Mac. The anonymous endpoint does about one
  URL per 45 s, so the run always hits the ceiling; the S3 keys (waiting on the
  user since 02.10) are the real speed-up.
- When minutes are available: run `sanctions-watch` once by hand
  (workflow_dispatch) to cover the two missed Mondays.

### 1.2 The Mac round has been silent since 06.10

`data/watch/daily/` ends at 2026-10-06; `board.json` was generated 09.10; the
local scrape's newest post is 04.10. If the Mac is no longer available, the
whole pull, re-screen, ingest and scrape apparatus is offline, and this cloud
environment cannot replace it (all source hosts denied). Decision needed:
restore the Mac's launchd job, or allow the needed hosts in this environment's
network settings (Allowed domains), or accept a pause.

### 1.3 Stale coordination records

- CLAUDE.md's Coordination table lists a 10:05 status-board cloud routine and
  a Monday weekly-scan routine; this account has no scheduled tasks at all.
- `notes/rebuild_plan.md` "Current state (queried 2026-10-02)" is three weeks
  old (registry now 256 entities, 442 people, 9,229 sources).
- Issues: #9 (baseline), #27 (done in the 04.10 daily-round change) and #32
  (all five changes recorded: Атливанчик EU+CH, СТИМС EU+CH, Киселёв US) can
  be closed. #31 still waits for the user's call on the weekly scan.

## 2. Data quality: things a hostile lawyer would find

1. **40 `sanctions[]` entries with `regime: null`** (23 entities, 17 people),
   all OpenSanctions matches. Many carry only the topics `sanction.linked` /
   `sanction.control`: tied to a listed party, not listed. Examples:
   АО «Спецтех Инвестиции», АО «Спецтех Первый», ООО «Левит», ООО «Инвестментс»,
   Безруков, Фрадков, Яныкина, Бровченко, Михельсон. The landing count already
   excludes them (35 → 27, 05.10), but they still sit in the field a reader or
   an export treats as designation. Proposal: move them out of `sanctions[]`
   into the screening record (or mark them `linked_not_designated`) until an
   official entry is read. Check `export_data.py` and the packets for the
   same leak.
2. **86 people with a date of birth and no per-field source** (board check,
   status "act"). The PII rule says every identifying field carries its own
   source. A `dob_source` field is a schema change (the freeze), or the DOBs
   stay null until sourced.
3. **85 sources still cite as "Archived document"** (checker warning; they
   reach a reader page as an uninformative citation).
4. Leads from `_informal_ties_leads.md` (15.09) not re-checked here: ООО
   «КИНГПРО» named a resident without a `cbst_tie`; `kb-germes` as a possible
   duplicate of `npo-kaysant`.

## 3. Remove or tidy

- **`docs/images/`: 109 of 111 files are used by no page** (the live landing
  uses two). Pages still serves them at guessable URLs: Барашков's portrait,
  the Krasnodar residential HQ, a training-graduation photo, Архангел course
  material. The profiles that showed them were withdrawn on 02.10. Moving
  them out of `docs/` (and repointing `people.json` / `entities.json` image
  paths) takes them off the public site; git history keeps them. Needs the
  user's go-ahead (`docs/`).
- **CLAUDE.md is 80 KB** (roughly 20k tokens loaded by every session). About a
  third is history and archived-generator description (profiles, case pages,
  explorer). Moving that to `notes/reference/` would cut the per-session cost
  #31 worried about, without dropping a rule.
- **Branches:** `pull-inbox` (retired 05.10); `claude/project-thread-*` ×5 and
  `claude/status-board-copy-review` (merged or superseded, 61-169 behind);
  `copilot/look-at-repo-and-report-back` (an unreviewed B6 neighbourhood
  explorer, 884 lines: keep as a reference for B6 or delete);
  `claude/laughing-brahmagupta-b9cnwo` (a status-line mod; its CI fix is
  already on main as 1a4eb2e).
- `requirements.txt` pulls `telethon` (and `pyaes`, which does not build on
  Python 3.13) into CI, which needs neither; a `requirements-ci.txt` would
  separate the Mac's needs from CI's.

## 4. Overlooked threads, ranked for the sanctions purpose

1. **The money above Наша Правда.** Фонд «Наша Правда» (₽1.23bn received in
   2024) is the story's spine, but its founders are much larger and sit in no
   sanctions-gap packet. The gap set ranks ЦБСТ-tied organisations by revenue,
   and these are non-profits with no direct tie, so they are excluded twice.
   On file (БФО, already read): Фонд «Градислава» received ₽11.86bn in 2023 and
   used ₽15.07bn in 2024; Фонд «ДАР» received ₽8.30bn in 2024; ООО «Левит»,
   founder of ДАР, has revenue of about ₽15.9bn. Михельсон and Симановский are
   documented owners of Левит (oq021: ownership, not direction). No entry for
   any of the three funds on any list; Михельсон's own entry is an unread
   aggregator match. Open and answerable from documents: what Градислава's
   ₽15bn bought (oq007), loan counterparties (oq017), ДАР's ₽11.6bn securities
   (oq018), the Winter Olympic fund's flows (oq014), and the charters (src015).
   Next step: read the notes to the Градислава and ДАР accounts in full, as
   was done for Наша Правда on 07-08.10, then decide whether a "funders"
   packet is a second class beside the five revenue packets.
2. **The core itself is not listed in the West.** ЦБСТ (Ukraine only; the OFAC
   entry belongs to the Tula ООО), its two 100% subsidiaries АО «Спецтех
   Инвестиции» (27.11.2025) and АО «Спецтех Первый» (10.04.2026), the operator
   ООО «МПТМ» and Наша Правда (Ukraine only). The subsidiaries have no accounts
   or contracts on file; Спецтех Инвестиции's first БФО (FY2025) should exist.
   What do they invest in, and does РТ-Регистратор as registrar mean anything
   (oq020)? A "core" packet (ЦБСТ, the two Спецтех, МПТМ, Наша Правда) is the
   most direct ask the investigation can make, and the five-company set skips
   it because non-profits have no revenue.
3. **Concealment timeline.** 14 registry entities have their ЕГРЮЛ shareholder
   section closed, each with a dated record: Тримикс 01.11.2024, ЦАСД Демянск
   04.07.2025, Ушкуйник 15.09.2025, Уралдронзавод 16.06.2026, МПТМ 15.07.2026,
   both Спецтех and Кайсант, Рустехдрон and others by 07.09.2026. Set against
   listing dates, press coverage and ЦБСТ milestones, the dates may show
   companies closing their registers after attention. Each date is already
   read from a document; this is analysis over the registry, possible offline.
4. **State money to drone makers (the national БАС project).** Parked since
   01.10 with the documents identified but not pulled: НПЦ resident rosters
   (about 15 sites), Минпромторг subsidy-round recipients, Фонд НТИ protocols
   (applications by number only). Песков links it to ЦБСТ's supervisory
   board. A named list of state grantees, crossed with the registry and the
   lists, is a second sanctions-gap angle.
5. **ЦБСТ's leadership change.** Рубинштейн (Ukraine-listed) left the general
   directorship in late 2025; Яныкина Н.О. since 16.12.2025 (s0228). Her record
   has only an unread aggregator match; nothing else is known about her.
6. **The «Булат» seller to the foundation (B3)** is still open. АО «Технодрон»
   is the only supplier in Наша Правда's 31.12.2024 payables (its amount is
   unreadable in the scan); Технодрон also appears in the informal-ties leads
   as an FPV maker. A lead, nothing more.
7. **Leak corpora.** The DDoSecrets library-card application (08.09) has no
   recorded outcome. If granted, an ИНН search across the index comes before
   any bulk request.

## 5. Course of action

**User, about 30 minutes, unblocks everything else:**
1. Check Actions billing; approve the wayback cap; re-run the sanctions watch.
2. Say whether the Mac round is coming back. If not, decide which hosts this
   environment may reach.
3. Say whether the infrastructure freeze (04.10, "two to three weeks") has
   ended. Items 2.1, 2.2 and 3 depend on it.
4. Go-aheads: close #9, #27, #32; delete the stale branches; take the
   orphaned images off `docs/`.

**A cloud session can do without sources:** the sanctions-field
reclassification (2.1, once agreed), the concealment timeline (4.3), the
CLAUDE.md trim and coordination update, the stale plan numbers, and a "core"
and "funders" packet outline from registry data already on file.

**Needs the Mac or network:** the Градислава/ДАР notes read in full, the
Спецтех БФО, the НПЦ rosters, the Наша Правда scrape (post 688), Story 1's
second-person check against the source files, and the missed sanctions
watches.

Story 1 stays where the user left it on 09.10: all chapters drafted, waiting
on the second-person check, the personal-data review and right of reply.
