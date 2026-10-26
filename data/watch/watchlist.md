# Weekly scan: watch list and method

Built 02.10.2026 from `config/channels.txt` and the channels most cited in `data/registry/sources.json`. Edit this file to change what the Monday scan reads; the routine reads it fresh each run.

## Channels read in full every week (core network)

| Channel | Why |
|---|---|
| @ANO_CBST | ЦБСТ's own channel (87 cited posts) |
| @nashapravdafond | Фонд «Наша Правда», ЦБСТ co-founder, donor deliveries |
| @asidyakin | Сидякин, secretary of ЦБСТ's supervisory board |
| @chadayevru | Чадаев, НПЦ «Ушкуйник» |
| @nvgushkuynik | АНО «НПЦ «Ушкуйник»» |
| @dronnitsa | Дронница event, exhibitor rosters |
| @UAS_development | НПЦ БАСиРТК, a РОЙ.МАРКЕТ seller |
| @potapov_npp | cited 7 times |
| @kb_spektr | КБ «СПЕКТР», self-reported РОЙ.МАРКЕТ vendor |
| @ru3mx | 3mx / ООО «Тримикс», «Булат» |
| @tulaovod | «Овод», ЦБСТ's flagship resident, sanctioned |

## Channels scanned for registry names only (makers, residents, adjacent)

@projectArchangel, @my_el_lab, @mil_hub, @krams_pro, @evgeniy_lisitsyn, @Rus_Piranha, @piranhafpv, @GoDrone, @aeromax_group, @stratim_drones, @alaskadron, @KBinteldron, @kotlin_novator, @gaskargroup, @bpryarl, @germesfpv, @arkhangelfront, @russian_shock_volunteer_brigade, @rogozin_do, @droneracingfederation, @asel_labs, @orient4gnss, @rostecru (ЦБСТ items only).

Not readable from the cloud: the two private invite chats (Архангел members, 3mx users). Those stay with the local `tg_scan.py` run.

## News search terms (Russian first, then English)

- «Рой.Маркет» / «РОЙ.МАРКЕТ» / «Роймаркет» / «военный маркетплейс»
- «ЦБСТ» / «Центр беспилотных систем и технологий» / «Безруков ЦБСТ» (also «ЦСБТ», the channel's own misspelling)
- «Сидякин» + беспилотники / ЦБСТ / комитет по цифровому развитию
- «фонд Наша Правда»
- «ПСБ» + беспилотники / ЦБСТ / маркетплейс
- «МПТМ», «Спецтех Инвестиции», «Системный интегратор» + ЦБСТ
- «Ушкуйник», «Дронница», «Акселератор спецтехпроектов»
- Sanctions: new EU / UK / US (OFAC) / Ukraine (РНБО, war-sanctions.gur.gov.ua) packages naming any registry entity or person
- English: "Roy.Market" OR "ROY.MARKET" OR "ROI.MARKET" OR "roimarket" drone marketplace; "Center for Unmanned Systems and Technologies"

## Method (what the routine does)

1. Read each channel with WebFetch on `https://t.me/s/<channel>?after=<last seen>`. The plain `t.me/s/<channel>` URL can return a weeks-old cached copy (seen for @ANO_CBST on 02.10.2026); the `after=` form returned current posts. Direct curl to t.me is blocked by this environment's network policy.
2. A post counts as new only if its number is above `weekly_scan_state.json`. Telegram previews do not give reliable dates through WebFetch, so dates are taken from the post text or a news report, or left out.
3. Every name is checked with `python3 scripts/registry_lookup.py "<name>"` and every post against `tg_post` in `data/registry/sources.json`, so already-recorded material is not reported as new.
4. Report only items that touch a registry entity or person, or a lead that plainly bears on ЦБСТ / РОЙ.МАРКЕТ. Flag anything that updates or contradicts a published claim. Quote Russian verbatim; a WebFetch summary is a lead, not a fact (CLAUDE.md hard rule).
5. Never edit the repo, the registry or published pages. Update only `weekly_scan_state.json`, add the report to `reports/`, and append each reported item to `developments.json`.
6. **`developments.json`** feeds the Investigation Status Board (`scripts/status_board.py`). For every item in the report, append `{id: "<run date>-NN", found, report, url, channel, post, also: [other urls], about: [registry slugs from registry_lookup.py, or "@channel"], kind: update|contradicts|new|lead, status: "open", summary}` (summary: one plain English line saying what the record lacks). `about: []` for a lead with no registry match. Never change an existing item's status; people and threads close items (`recorded` or `dismissed`, with a `note`). Skip a post already present as an open item.

## Wider context (added 02.10.2026 at user request)

Reported in a separate "Industry and law" section of each report. The bar is lower than for the core scan: an item qualifies if it changes the conditions the network operates in (money, rules, sanctions, attacks on its people), even if it names no registry entity. Still one line on why it matters to this investigation.

### Industry Telegram channels (read for БАС industry news)

| Channel | What it is | Tested 02.10 |
|---|---|---|
| @bayraktar1070 | «Свидетели Байрактара», Шилов (РИА) and Харченко (RT) | yes, reads |
| @uavdev | «Разработчик БПЛА», developer channel | yes, reads |
| @zas_svo | drone teardown analysis, cited 42 times in mil_hub | not yet |
| @xronikabpla | «Хроника БПЛА», cited in mil_hub / Архангел | not yet |

Tried and dropped: @kcpn2014 (no public preview; КЦПН is covered through @dronnitsa), @rusengineer (general politics, not industry).

### Industry sites

- АвиаПорт news, https://www.aviaport.ru/news/ (aggregates TASS / www1.ru БАС items, dated; reads well)
- roimarket.ru (the platform itself: new sections, rules, partners)
- vpk.name, www1.ru, kommersant.ru (via news search on the terms above)
- cbst.ru/news renders empty to the fetch tool; ЦБСТ is covered through its channel.

### Law and regulation

- Official publication portal, http://publication.pravo.gov.ru/documents/block/president and the `government` block, plus the Минпромторг, Минобороны, Минтранс and Минцифры blocks: new decrees, government resolutions and ministry orders on БАС, localisation (ПП №719), dual-use goods, marketplaces, export control, the national project «Беспилотные авиационные системы».
- State Duma news, http://duma.gov.ru/news/ (bills, first readings, committee work; watch Сидякин's committee on digital development and AI, which covers marketplaces and БПЛА).
- The Duma bill database (sozd.duma.gov.ru) and regulation.gov.ru time out from here; use a news search for «законопроект» / «проект постановления» + беспилотн / маркетплейс / двойного назначения instead.
- Budget: national project «Беспилотные авиационные системы» lines in the 2027-2029 budget (first reading 29.10.2026).

### Sanctions

- OFAC recent actions, https://ofac.treasury.gov/recent-actions (reads; Russia-related entries only)
- EU Council press releases, https://www.consilium.europa.eu/en/press/press-releases/ (reads; the 21st package was trailed with ~30 drone-related companies)
- UK: the old OFSI collection page is withdrawn; use a news search for "UK sanctions Russia drones" until a working list URL is found.
- Ukraine: presidential sanctions decrees and https://war-sanctions.gur.gov.ua (already the registry's most-cited sanctions source).
- Any new listing is checked against every registry entity and person by name and ИНН; a hit is a top item.
