# Source-type coverage audit — 2026-09-15

Read-only audit. No registry file was modified. Ground-truth commands run:
`.venv/bin/python3 scripts/check_registry.py` (0 errors, 43 warnings — all
pre-existing/cosmetic, see raw output), `scripts/coverage_report.py`,
`scripts/zakupki_coverage.py --gaps-only`, plus local ad-hoc queries against
`entities.json`/`people.json` for fields `coverage_report.py` doesn't break
out (disqualification/subsidiary/upr-uchr/opensanctions/aleph/leader_id
checked-at markers).

## Summary table

### Entities (216 raw / 214 live)

| source-type | checked-and-found | checked-and-clear | never-checked |
|---|---|---|---|
| EGRUL identity (ИНН/ОГРН/director/founders) | see coverage_report: 208/197/188/149 of 216 have the field | — (blank identity fields are mostly genuine "not yet resolved," not a reviewed-clear state) | remainder, concentrated in the bottom-tier/thin-lead rows (#186–216) |
| БФО financials | 159/216 have `financials[]`/`funds_*` | not separately tracked as "reviewed, no filings" | 57/216 — some legitimately pre-revenue/shell, not distinguished from unreviewed |
| zakupki | 34 `zakupki_review`-closed + more with real `government_contracts[]` hits (23/216 activity field populated) | 34 explicitly `zakupki_review: closed/partial/wired` | **60 entities never scanned at all** (see list below) — real gap |
| GUR war-sanctions | 184/216 | included in the 184 | 32/216 |
| GUR components | 76/216 | included | 140/216 — large gap, but this list is inherently narrower-scope (only entities with a plausible parts-teardown tie) |
| OpenSanctions | 183/216 | included | 33/216 |
| Aleph/OCCRP | 183/216 | included | 33/216 |
| Rospatent (director) | 93/216 | included | 123/216 |
| rk.2035.university БАС registry | 113/216 | included | 103/216 — expected; most entities aren't UAV-industry-registry members by nature |
| WB/marketplace overlap | 209/216 | included | 7/216 |
| ФНС обеспечительные меры | 174/216 | included | 42/216 |
| founding docs / Устав | not broken out by coverage_report.py; `notes/rebuild_plan.md`'s 2026-09-07 "Founding-document coverage audit" (`notes/founding_docs_gap.md`) already ran this sweep — **treat as recently closed, not re-audited here** | | |

### People (432 raw / 426 live)

| source-type | checked-and-found | checked-and-clear | never-checked |
|---|---|---|---|
| ФНС disqualification (`screen_disqualified.py`) | 1 hit | 154 checked-clear | **277 never checked** — largest people-side gap |
| ФНС subsidiary liability (`screen_subsidiary.py`) | 0 hits | 153 checked-clear | **279 never checked** |
| ФНС director/founder cross-ref (`screen_upr_uchr.py`, `other_entities`) | 99 with hits | 72 checked-clear | **261 never checked** |
| OpenSanctions | 146 hits | 273 checked-clear | 13 never checked — near-complete |
| Aleph/OCCRP | 367 hits | 44 checked-clear | 21 never checked — near-complete |
| leader-id.ru | 136 hits | 172 checked-clear | 124 never checked |
| ЕГРИП (`screen_egrip_ip.py`) | **no structural field exists on any person record at all** (`egrip`/`ogrnip` not present as keys anywhere in `people.json`) | — | effectively **175/432 people have `inn_personal` and none carry any ЕГРИП check marker** — this looks like a real tooling/recording gap, not "reviewed and clear" |
| rupep.org PEP check | no dedicated structured field; ad hoc, prose-only per `notes/rebuild_plan.md` | — | not systematically tracked; can't distinguish reviewed-clear from unchecked from the data alone |

## Zakupki: NOT a repeat of the 2026-09-05 false-positive incident

`zakupki_coverage.py --gaps-only` already respects `zakupki_review` — its
own summary line separates **60 never-scanned** from **34 already reviewed
(zakupki_review)** and **3 partial fetch-contracts**. The 60 "UNSCANNED" ИНН
it lists (23 entities + 37 people) are genuinely never queried against the
zakupki search API at all — no `zakupki_review` marker, no scan-log entry.
This is a real, not false-positive, gap list — reproduced in full in the
tool's own output; representative entity rows: `ooo-hab-svo` (9722102248),
`ao-opticheskie-sistemy` (7733486867), `ooo-laboratoriya-yangelya`
(2373028450), plus the `Аркодим`-family cluster (6 entities, ИНН prefix
165x) and the `Атлант`/`Аметист`/`ДС-Барс-Т`/`НПК Зевс`/`Прометей`-family
cluster (Дагестан/Кавказ ИП/ООО, ИНН prefix 6154x/6161x/6163x/9717x/9704x) —
these look like a single unscanned regional sub-network, not scattered
individuals.

## Prioritized real-gap list (top candidates for a human's next pull)

1. **ЕГРИП check on people with `inn_personal` and a role at a manufacturer/
   cbst-core tier entity** — this is the single cleanest structural gap:
   the tool (`screen_egrip_ip.py`) exists, the ИНН exist (175 people), and
   there is literally no marker field showing it was ever run project-wide,
   vs. the disciplined checked-at pattern every other screen_*.py leaves.
   Worth running `screen_egrip_ip.py --slug` on directors/founders of the
   highest-tier entities first (ЦБСТ core, manufacturer tier) rather than
   the full 175.
2. **zakupki UNSCANNED entity cluster, Аркодим family** (`ooo-arkodim-2`,
   `ooo-arkodim-pro`, `ooo-ntc-arkodim`, `ooo-zemstroyregistr`,
   `ooo-ekspoket`, plus `ooo-arkodim` itself at 12/27 dimension coverage) —
   manufacturer-tier, six related ИНН never zakupki-scanned as a group.
3. **zakupki UNSCANNED entity `ooo-laboratoriya-yangelya`** (2373028450,
   `network` tier, only 1/8 БФО-adjacent dims but full identity coverage) —
   highest-tier label among the unscanned entity list.
4. **ФНС disqualification/subsidiary check, 277/279 people never run** —
   the biggest raw count in this audit, but proportionality applies per
   CLAUDE.md's PII policy: triage to directors/founders of manufacturer and
   cbst-core tier entities (cross-reference `people.json` `roles[]` against
   `entities.json` `tier`) rather than running all 277 blind.
5. **zakupki UNSCANNED regional cluster** (Дагестан/Кавказ ИП/ООО group,
   ~10 entities/people, ИНН prefixes 6154x/6161x/6163x/9704x/9717x/9722x) —
   worth one batch scan given it reads as a coherent sub-network rather than
   isolated small-supplier noise.
6. **GUR components teardown check, 140/216 entities never checked** — large
   in raw count but expected-scope-limited (only relevant to entities with a
   plausible parts/component tie); not flagged as urgent without further
   triage of which of the 140 are actually manufacturer-tier.

## Dimensions confirmed fully/near-fully closed — do not re-flag

- **Founding-document / Устав coverage** — swept in the documented
  2026-09-07 "Founding-document coverage audit" session
  (`notes/founding_docs_gap.md`); not re-audited here per the
  grep-notes-first discipline.
- **OpenSanctions (both entities 183/216 and people 419/432)** and
  **Aleph/OCCRP (both entities 183/216 and people 411/432)** — both close
  to full coverage; residual gaps are single-digit-percent and not worth a
  dedicated pass on their own.
- **WB/marketplace overlap** — 209/216 entities, effectively closed.
- **zakupki** — the coverage tool's own review-outcome discipline is intact
  and working as designed (34 correctly excluded as reviewed); the 60
  UNSCANNED is the only real remaining zakupki gap, not a re-run of the
  2026-09-05 false-positive pattern.

## Caveats on this audit

- "Never-checked" counts for БФО, EGRUL identity fields, and GUR/Rospatent/
  rk2035 mix genuine gaps with legitimately-inapplicable records (shells
  with no filings, adjacent-not-core entities that were never expected to
  register with rk.2035.university, etc.) — `coverage_report.py` does not
  itself carry a review-outcome marker for these dimensions the way
  `zakupki_review`/`sanctions_review` do, so these counts should be read as
  upper bounds on real gaps, not confirmed gap counts.
- rupep.org PEP screening and founding-doc screening have no structured
  per-record marker at all in the schema (unlike zakupki_review/
  disqualification_checked_at/etc.) — this audit could not distinguish
  reviewed-clear from unchecked for either dimension from the data alone;
  flagging this as a tooling gap worth a structured field, not a content
  gap.
