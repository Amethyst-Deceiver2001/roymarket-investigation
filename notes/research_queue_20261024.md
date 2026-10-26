# Research queue (24.10.2026)

Built from `data/registry/open_questions.json` (44 entries: oq001–oq027, src001–src017), the open `brief_items.json` entries, and the FBK exhibit read (`notes/fbk_images_analysis_20261024.md`). **A work list, not a fact file; nothing here is registered.** Ranked by what it does for the sanctions case (a claim a hostile lawyer can test) and by whether it can be done now, from here.

Rules applied: no catalogue checks (ROI.MARKET is login-only), no warehouse hunt (oq001 stays a caveat), no CI or daily-round items. "User" means the user runs the job (live third-party work at scale).

## What the 44 entries really are

| Kind | Entries | Treatment |
|---|---|---|
| **Guards** (a "do not say X" for the writer, not a task) | oq001, 003, 004, 009 (motive), 020, 021, 022, 024, 025, 026, 027 | Keep as page-check caveats. No research. |
| **Identity traps** (can wrongly merge or accuse) | oq002, oq023 | Research, tier 1. |
| **Unknowns in the funds network** | oq005–008, 010–018 | Research, tiers 1–3. |
| **Unmined sources** | src001–017 | Fold into the items they serve, below. |
| **Possibly stale** | oq006, oq012, oq013, oq010 (their text already says "now confirmed" or "partly disclosed") | Re-read, then close or reword with a `status` + `note`. |

## Tier 1: do first (identity, and the core ДАР / Градислава / Наша Правда chain)

1. **oq002, which Azimut entity is sanctioned.** Two same-named companies share a director. Resolve by ИНН/ОГРН against the EU/US/UK listing text, not by name (frozen snapshot 05.10.2026). Blocks any page that says "sanctioned" next to Azimut. A wrong flag here is the worst error available.
2. **oq023, Осадчук.** ЦБСТ's MoD innovation-directorate head versus the US-designated unit 74455 commander. Compare patronymic and DOB from the US listing with anything ЦБСТ prints. If neither is available, the answer stays "two possible people".
3. **Градислава director history** (new from FBK, brief b015). Our `director_history` starts Карабинский on 17.12.2021 (ГРН 2217711641585). The SPARK screen (gallery n=2) shows him with last ЕГРЮЛ change 05.09.2013, and Жменя is recorded as director on 16.04.2013 (n=37). Needs the ЕГРЮЛ history of ИНН 7704278421 (ГРН list 2011–2021) to settle who was director when. Single lookup, can run inline.
4. **src015, ДАР identification (the item the brief called the single highest-value one).** ЛЕВИТ is documented as founder from ДАР's own extract, so the open part is the charter: Наша Правда's устав, and ДАР's, from the ЕГРЮЛ document archive. Names the founding foundations and shows what the supervisory board is. Also gives ДАР's supervisory board in a primary document (no FBK image shows it).
5. **oq005 / b015, the Медведев attribution.** Not a research task for the registry. It needs a rule check on every page: FBK 2017 allegation, the denial recorded, never a finding. Separately, **read the Western listing reasons** that supposedly describe Елисеев as Медведев's nominal asset-holder (ДАР has no `sanctions[]` entry; see the unsourced-line note in `source_fbk_dimon_2017.md`). Read the official text or drop the phrase.
6. **oq006 + src016 + FBK A1, the Миловка and Котельническая title chain.** Росреестр extracts (paid): Миловка 2014 transfer ДАР → Градислава (the FBK image n=4 shows only the owner entry, 19.09.2014, «Договор пожертвования», no object or transferor), and office 18 at Котельническая наб. 25 (lease №18/25-22). Needs user approval to buy.

## Tier 2: strengthens named claims (do after tier 1)

7. **oq007, Градислава's ₽12.95bn 2024 "целевые мероприятия".** Re-read the FY2024 notes for itemisation; the Milovka line items are FY2023 and far smaller. Ties to the FBK Миловка story.
8. **oq014, who benefits from the winter-sports fund (ИНН 7706470191).** FBK n=63 puts the fund as owner of a Псехако object from 25.09.2014 (after ДАР from 10.12.2013). Read the object and its address; check whether a rights holder before ДАР is shown.
9. **oq016, Заволжское's 1% holder.** Request the founding documents; the 2013 Устав shows more than one founder. Possible link to the ФБК-era names (Жменя).
10. **oq010, oq011, oq017, Инвестментс loans and the stake fall from 100% to 90.91%.** Read FY2025 notes for the new holder (ЕГРЮЛ, ГИР БО). Counterparties are unnamed across the network; record that as a pattern only.
11. **oq012, oq013, Сейм-Агро / Фонд морских программ.** Re-read, then close or reword: both texts are already "now confirmed". Росагролизинг as pledgee is a lead for the ДАР ₽2.1bn tranche.
12. **oq018, ДАР securities (~₽11.6bn).** Note-by-note read of the БФО; the issuers are not named, so likely stays an open question. Low yield.
13. **oq019, Наша Правда FY2024 equipment inventory.** Check the large line items against the source PDF before citing any per-item figure. A pure verification task and cheap.

## Tier 3: МПТМ and ЦБСТ people and sites (steady but slower)

14. **b013 / oq009, МПТМ.** Former director Иван Коптенко (until May 2026 per Вот Так) is not on file. Pull the ЕГРЮЛ history (ГРН) first; do not file him as a person record until a primary document names him. The 15.07.2026 sealed founder register is a fact to cite with the date, with no motive.
15. **src002, src005, src007, src008, src011, МПТМ's footprint.** ГИР БО 2025 turnover, РКН operator registry (data-processing sites), Роспатент «РОЙ» filings (inception date and filing entity), Прозрачный бизнес (mass-address flag for Нарышкинская 5с2), job boards. Each is a single lookup. Do them together as one МПТМ pass. Record misses in `_pull_misses.json`.
16. **src003, src006, Инвестментс and МПТМ in the courts and Федресурс.** kad.arbitr.ru: one open case for ₽83.27m (real estate). Lease and landlord cases show real premises; this is the best legitimate route towards oq001 without asserting a warehouse.
17. **src001, src004, src009, state buyers and sanctions cross-checks.** ЕИС by the four ИНН listed in the entry; the GUR UAV-companies list; the Минпромторг licence registry for the Azimut licence Л008-00102-77/00006787. Batch sweeps go to the user as an exact command.
18. **oq020, РТ-Регистратор.** Stays a structural signal. One line unless a primary document appears.

## Tier 4: needs the archive Mac, a user run, or a user decision

- **b010 / b011**, delivery events with no unit link (bulat-d05, kapyushon-d02) and four 2024–25 leads: older posts live on the archive Mac.
- **b005**, no source ids assigned on this Mac.
- **src014**, `@roy_market` and the ЦБСТ MAX channel unscanned: user runs `scripts/run scripts/tg_scan.py …`.
- **src017**, Лисицын video archive for the Наша Правда deliveries: find the channel, then media triage.
- **src010, src013**, crt.sh and street-level imagery: low yield, retry only if the landing page needs them.
- **b016 / b017**, Kherson units: wait for the unit-name rules and a read.
- **b014**, source ids for the Вот Так and ФБК captures: archive Mac.

## Not research (close with a note, do not queue)

- **b012, "no warehouses to hit" has no document.** The settled position is that none is claimed; the intro line has to be reworded as a statement of what is not established, not searched for.
- oq001, 003, 004, 020–022, 024–027 stay as guards.

## FBK additions that belong in the queue

Items 3, 6, 8 above come from the FBK read. Two others stay open there and need no new work until a primary document turns up: ФКК = ФинКонсалтингК (name history, no ИНН in the crop, image n=19) and the ₽33 639 050 thousand "Уставный капитал" (image n=162, entity not printed).
