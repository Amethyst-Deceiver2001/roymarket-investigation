# Source register — every registry/database an entity should be checked against

**Created 2026-09-05.** Companion to `scripts/coverage_report.py`. That script
answers *"which entities have we checked?"*; this file answers *"checked against
**what**, and can we do it ourselves?"*

**Why this exists.** Three times in one session (2026-09-05) an entity already
fully covered in `data/registry/` was reported as an uncovered gap, because
"have we checked X?" was answered from memory instead of from data. The
registry itself fixes the per-entity half of that. This file fixes the other
half: the set of sources is now written down with an explicit access tier, so a
source is never silently forgotten, and "the user has to do this one" is a
recorded property rather than a thing rediscovered each session.

## Access tiers

| Tier | Meaning | Policy |
|---|---|---|
| **A** | Plain `curl`/`requests`, no captcha, no session | Scriptable. Single lookups inline; full-roster sweeps handed to the user per CLAUDE.md's crawling-jobs policy. |
| **B** | Needs a real browser (WAF/Qrator/JS-rendered); works via chrome-devtools | Inline reconnaissance only. Not batch-scriptable — one entity at a time. |
| **C** | Captcha-gated, login-gated, or legally blocked | **User-only.** Do not attempt to automate; put it on the manual-task list. |
| **D** | No route found from this environment | Note and move on; user should re-test from their own network before we call it dead. |

Probe date for every "confirmed" status below: **2026-09-05**, from this
sandbox. Tier D especially is environment-dependent — a timeout here is not
proof the site is down for the user (cf. `kad_arbitr_ru_ddos_guard_blocked`,
which *was* confirmed from both sides and is genuinely dead).

---

## Tier A — scripted, already integrated

| # | Source | What it gives | Tool | Coverage field |
|---|---|---|---|---|
| 1 | egrul.nalog.ru (open lookup) | name/ИНН/ОГРН/director/region | `egrul_batch_pull.py` | `inn`,`ogrn`,`director` |
| 2 | egrul.nalog.ru (full выписка) | founders+shares, capital, ОКВЭД list, address, ГРН history | `egrul_vypiska_pull.py` | `founders`,`capital`,`okved` |
| 3 | egrul.nalog.ru ЕГРИП | individual-entrepreneur registrations (people) | `screen_egrip_ip.py` | people-side |
| 4 | bo.nalog.gov.ru (ГИР БО) | signed annual accounts (balance, P&L) | `bfo_pull.py` | `bfo` |
| 5 | ФНС дисквалифицированные лица | director disqualification | `screen_disqualified.py` | people-side |
| 6 | ФНС субсидиарная ответственность | subsidiary-liability findings | `screen_subsidiary.py` | people-side |
| 7 | ФНС упр./учр. cross-reference | other directorships/foundings | `screen_upr_uchr.py` | `other_entities` |
| 8 | ФНС обеспечительные меры | tax-security measures | `screen_rom.py` | `securing` |
| 9 | zakupki.gov.ru (44-ФЗ contracts) | state contracts + attachments | `zakupki_batch_pull.py` | `zakupki` |
| 10 | OpenSanctions API | consolidated sanctions/PEP | `screen_opensanctions.py` | `opensanctions` |
| 11 | war-sanctions.gur.gov.ua | GUR war-sanctions (3 sections) | `screen_gur.py`, `screen_gur_components.py` | `gur`,`gur_components` |
| 12 | searchplatform.rospatent.gov.ru | patents | `rospatent_patent_search.py` et al. | `ip` |
| 13 | Rospatent trademarks | trademarks | `rospatent_tm_search.py` | `ip` |
| 14 | rk.2035.university | national БАС-industry company registry | `screen_rk2035_bas_registry.py` | `rk2035` |
| 15 | Aleph (OCCRP) | leaked/aggregated corporate data | `screen_aleph.py` | `aleph` |
| 16 | Wildberries/Ozon | marketplace listings | `screen_wb.py` | `wb` |
| 17 | Telegram | posts + membership | `tg_scan.py`, `tg_scan_users.py` | `web` |
| 18 | component.aeronext.aero | АЭРОНЕКСТ member catalogue | (memory recipe, no script) | `state_programs` |

## Tier A — confirmed reachable 2026-09-05, NOT yet integrated

| # | Source | What it gives | Status | Priority |
|---|---|---|---|---|
| 19 | **zakupki.gov.ru РНП (44-ФЗ)** — реестр недобросовестных поставщиков | debarment record; a clean check is a **citable negative** | **Confirmed working via plain curl.** No-hit marker: `Поиск не дал результатов`. No script yet. | **High** — cheap, and debarment is directly material to a sanctions case |
| 20 | zakupki.gov.ru РНП (223-ФЗ) and РНП ПП РФ 615 | same, other two sub-registries | Same page, separate tabs; same access | High |
| 21 | sudact.ru | court decisions (general jurisdiction + arbitration text) | HTTP 200. Viable **substitute for the DDoS-Guard-blocked kad.arbitr.ru** | **High** — litigation is a real gap (`litigation[]` populated on 5/182) |
| 22 | checko.ru | aggregator company card | HTTP 200 | Medium — aggregator, corroboration only |
| 23 | audit-it.ru / sbis.ru | aggregator financials | HTTP 200 | Low — БФО is better and primary |

## Tier B — browser-assisted (chrome-devtools), one entity at a time

| # | Source | What it gives | Notes |
|---|---|---|---|
| 24 | **fedresurs.ru** (company card) | **charter capital, current ЕГРЮЛ address, status, ОКВЭД, reg. date** | Qrator 401s plain curl; passes in a real browser. Backend API confirmed: `GET /backend/companies?searchString=<ИНН>&limit=5&offset=0` → guid; `GET /backend/companies/<guid>` → full card. **`offset` is mandatory** or it 400s. |
| 25 | gisp.gov.ru (ГИСП) | industrial-product + company registries (ПП 719 / ПП 878) | WAF-blocks curl; browser fine. Company search is by legal name only, not director. |
| 26 | rupep.org | PEP dossiers: DOB, birthplace, ИНН, family | Cloudflare-blocks scripts; browser fine. Cheap first check for PEP gaps. |

## Tier C — user-only (do not automate)

| # | Source | Blocker | What we'd get |
|---|---|---|---|
| 27 | **fssp.gov.ru** (исполнительные производства) | **Captcha on search submit** — confirmed 2026-09-05 (page loads in browser, `captcha` present in the search response) | Enforcement proceedings = unpaid judgments/debts. Genuinely useful; needs the user. |
| 28 | fedresurs.ru **publications** | **HTTP 451** (legal block) on `/backend/companies/<guid>/publications` | Bankruptcy/lien/pledge/net-asset notices. The company card (tier B) still works. |
| 29 | kad.arbitr.ru | DDoS-Guard; confirmed dead from sandbox **and** user's own network | Arbitration case records |
| 30 | vestnik-gosreg.ru | Captcha | Liquidation/reorganisation notices |
| 31 | leader-id.ru | Login-gated (401 confirmed) | 412k-user event-participant directory |
| 32 | reveng.ee | API key must be requested by the user (media/journalist tier) | Leaked Russian DB search |
| 33 | rusprofile.ru | **Serves decoy data to automated traffic** — only `<title>` trustworthy | Nothing safely; avoid |

## Tier D — no route found from this sandbox (user should re-test)

| # | Source | Symptom | Why we want it |
|---|---|---|---|
| 34 | **pub.fsa.gov.ru (Росаккредитация)** | Connection timeout — curl **and** browser | **Certificates/declarations of conformity.** High value: a drone/RЭБ manufacturer's certification record is hard evidence of what hardware it actually makes. Top of the re-test list. |
| 35 | sanctions.nazk.gov.ua (NAZK "War & Sanctions") | Connection timeout | Ukrainian sanctions list **distinct from** GUR's — a separate designation source we currently don't check at all |
| 36 | reestr.digital.gov.ru | Read timeout | Russian-software registry (relevant to control-software claims) |
| 37 | fstec.ru | Connection timeout | ФСТЭК licence registry (defence-information-security licensing) |
| 38 | list-org.com / zachestnyibiznes.ru | 403 / DDoS-Guard | Aggregators — low priority, tier A alternatives exist |
| 39 | mos-gorsud.ru | Read timeout | Moscow court records |

---

## Known gaps in the source set itself (nothing checks these yet)

- **Customs/import data.** Russia has hidden company-level import data since
  2022; the best open lead remains The Insider's exporter CSV (sellers only, no
  Russian buyer field) plus China/Kazakhstan/Kyrgyzstan mirror data. See the
  `sanctions_evasion_tracker_and_mirror_trade_data` memory. No tooling.
- **Property/Rosreestr (ЕГРН).** Facility ownership. Referenced in the Гагаринг
  plan (pinning a specific литер at Одесская 48/3) but never actually wired up.
- **Non-OpenSanctions primary designation lists** — OFAC SDN, EU consolidated,
  UK OFSI, CA/JP/AU/CH read directly rather than through the aggregator.
  `sanctions[]` notes already flag several entries as "ID-confirmed aggregator
  match, one level short of a primary-source read".
