# ЦБСТ resident sweep: triage of 38 NEW and 5 TIE-GAP candidates (2026-10-02)

Input: `python3 scripts/cbst_resident_sweep.py` over the rescanned archive (503,714 posts, 56 channels), output kept in `/private/tmp/sw/res.txt` (not in the repo). Every row below was checked against `registry_lookup.py` (after the two fixes of 2026-10-02, below) and, where a fact is recorded, against the original post read in full. A product or company name matching another name is a lead, not a tie.

## Tool fixes made while triaging (2026-10-02)

- `registry_lookup.py` returned "no candidate" for a one-word brand inside a longer registry name («ЭЛВО» in НПП «ЭЛВО»; «ЗащитаИнфоТранс») and for «Алексей Чадаев» against «Чадаев Алексей Викторович». The first cause: the `contains` tier needs two words. The second: the Latin transliteration tokens of the query inflated its token set. A weak `word` tier now covers the first, the Cyrillic and Latin spellings are tested separately for the second, and `report()` no longer silently keeps only the first four hits. `tests/test_registry_lookup.py` holds the regression.
- A record made earlier the same week (the ЦБСТ open question and the Кольская верфь review) said ЭЛВО was not in the registry. It is (`npp-elvo-kolskaya-verf`, t-doc tie, s7604). Both notes are corrected in `corrections_entities.json`.

## The ЦБСТ post warnings closed

| Post | Reading | Recorded |
|---|---|---|
| 2474 (31.08.2026, s8871) | «Кронштадт» is the city where the ТНПА «Сахалин» of «Русская морская команда» is tested | `ao-kronshtadt` review: namesake |
| 2538 (17.09.2026, s8872) | A ЦБСТ resident project «Антелекон» tested an antenna complex at «полигоне ЦСН «БАРС-Сармат»» | `csn-bars-sarmat`, `fond-sarmat` reviews extended; «Антелекон» opened as an unresolved resident |
| 2037 | Airbus Bird of Prey article, does not name the БАРС-Сармат crew | read, noted on the review |

## TIE-GAP (5)

| Name | Disposition |
|---|---|
| «АНО «ЦБСТ»» | Self-match (ЦБСТ's own name). Not a candidate. |
| «Баба-яга» → `kb-spektr-novosibirsk` | False lead. Post 1509 (s7597): КБ «Гермес», резидент ЦБСТ, presents an interceptor against Ukrainian «Баба-яга» drones. The word is the name of the target. |
| «Кольская верфь» | Reviewed: ЦБСТ's tie is to НПП «ЭЛВО» (resident), not to Кольская верфь («резидент Арктической зоны»). |
| «Русак» → `ooo-stratim` | Review `lead_open` (post 1246): a product name in a list of residents' drones; ООО «Стратим» is 25% owned by АО «Стратим» (ЦБСТ tie). |
| «Сибирячок» → `ooo-gaskar-integratsiya` | Review `lead_open` (post 1557, s8889): a product name in a list of residents' drones; the company lists a «Сибирячок» on its own site (s8013). |

## NEW (38)

Real company or project names, none resolved to a legal entity (identity needs an identifier on the company's own site or a matching named person):

| Name | What the archive says | Status |
|---|---|---|
| «Антелекон» | Post 2538: «Резидент ЦБСТ», antenna АН5200-5800Ш17 | Open; antelecon.ru redirects to антелекон.рф, which did not answer; no Wayback copy |
| «Аква-Волга» | Posts 2463, 2541: Volgograd team, accelerator stream III, co-developer of the boat «Вектор» | Open |
| «Арьергард» | Post 457: «резиденты АНО ЦБСТ, к примеру, компания Арьергард» at NAIS 2025 | Open |
| ООО «Прикладная робототехника Авиа» | Post 1102: cooperation agreement with ЦБСТ at the forum of 15.08.2025; not called a resident | Open; the parent ООО «Прикладная робототехника» prints ИНН 7730697556 on its site (s8874), «…Авиа» is not shown to be that company |
| «Квадросим» | Already an open question (post 1562, simulator «АНТИ БПЛА») | Open |
| «Моторно», «Лаборатория разработок» | Post 1269 (s8581, read in full): winners of accelerator stream I, helped by ЦБСТ with a technical specification, a roadmap and an ФПИ application; residency not stated | Open as accelerator winners; ООО «Интел Дрон» (`ooo-intel-dron`, the third winner named) and ООО «Ментастеп» (a finalist, `ooo-mentastep`) are on file |

Already on file, listed as NEW by the sweep because the post shortens the name: АО «НПП» (`ao-npp-real`, t-open), «Аляска» (`alyaska`), КБ «Гермес» (`npo-kaysant`), Уралдронзавод (`uraldronzavod`), Школа БПЛА Октагон (`ao-shkola-bpla-oktagon`), Кольская верфь (`kolskaya-verf`), НПП «ЭЛВО» (`npp-elvo-kolskaya-verf`).

Products with no maker named (leave as product leads): «Матрёшки», «Рарог», «Гусь» (КБ «Гермес» product), «Буревестник», «ВИТ-1 М», «Болт», «Дикобразы», «Скворцы», «Упыри», «Тарелка» (the Антелекон antenna), «Небо-22» (simulator), «Яким» (system of the consortium «Интегра-С», post 1891: «продукт экосистемы ЦБСТ»; a consortium with no entity on file).

Events, programmes and noise (no entity): «TECH WEEK», «NAIS 2025», «Архипелаг», «Патриоты России», «Defence City» (an essay concept), «Эра» (военный технополис), «Сколково: 15 лет инноваций», «Другой ракурс» (TV programme), «Сомали» (a battalion), «малой технологической компании», «паспорта», «домашняя работа», «реальное взросление», «намного быстрее впитывают знания», «рейтинг дронификации», «свой – чужой», «граница России нигде не заканчивается» (the slogan of «Аляска»), «Единой Россией», «Лаборатория разработок», «Skydio».

Result: 6 genuinely new unresolved names out of 38, plus 7 name-shortening misses by the sweep. The sweep's NEW class is a prompt to read, not a list of companies.

## Archive scan for residents and БАС participants (2026-10-02)

Terms run over all 503,714 posts with `tg_post_coverage.py --all-channels` (hits shown in full; the NEW/duplicate reading above is of the deduplicated text): «НПЦ БАС» 44 hits, «резидент НПЦ» 33, «Фонд НТИ» 79, «Ушкуйник» 528 (not read one by one), «Росавиаци» 266 (not read, mostly unrelated), «Гранты по БАС» 0, «Колыбель БАС» 0.

Named by the sources, recorded in `programs.json` / on entities (see `ushkuynik_family_and_programs.md` §6 and `bas_program_leads.md` §6): the named residents of НПЦ «Ушкуйник», КБ «СПЕКТР» next to the Tomsk НПЦ БАС, and the Kommersant figures for the whole network. Named only through aggregator channels (leads, originals unread): the Фонд НТИ grantees «Дронко» (₽300m, engines, mil_hub 95638), «НьюЛинк» (₽300m, servo drives, mil_hub 119789 and 127389), a Mesh-network project (₽43.8m, mil_hub 123457), and «Лаборатория будущего» (Фонд НТИ owns 72% per mil_hub 135422; reports of a fraud case in August 2026, mil_hub 134218 and 135422, unread in the original).
