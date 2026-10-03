# Weekly scan, trial findings: what to record and what the Mac must capture first

03.10.2026. Four findings from the 02.10.2026 trial scan (`/mnt/project-files/watch/reports/2026-10-02_trial.md`, items in `developments.json`) checked against the registry. None of them can be recorded from the cloud. The posts were read only through a fetch tool, which is a lead under the hard rule. They also need `TGPOST_` capture files and source ids, and `data/sources/` exists only on the Mac. This note gives the order of work and drafts each correction, with placeholders for the source ids.

## 1. Capture the posts (Mac)

```
python3 scripts/tg_scan.py --only @ANO_CBST,@nashapravdafond,@ru3mx,@kb_spektr   # bring the posts into data/roymarket.db
# channel ids: sqlite3 data/roymarket.db "select id, username from tg_channels where username in ('ANO_CBST','nashapravdafond','ru3mx','kb_spektr')"
python3 scripts/archive_tg_posts.py --channel-id <ANO_CBST id> --msg-ids 2565 --slug sidyakin-duma-committee-digital-ai
python3 scripts/archive_tg_posts.py --channel-id <nashapravdafond id> --msg-ids 686 --slug sidyakin-committee-congratulation
python3 scripts/archive_tg_posts.py --channel-id <ru3mx id> --msg-ids 741,742 --slug bulat-v6-announcement
python3 scripts/archive_tg_posts.py --channel-id <kb_spektr id> --msg-ids 337 --slug armamid-propeller-roimarket-ozon
python3 scripts/inventory_sources.py && python3 scripts/extract_registry.py
```

(Handles as written in `config/channels.txt`.) Read each post in full in its `TGPOST_` file before applying anything below.

## 2. Draft corrections (apply after reading)

**Сидякин, Duma committee chair.** `corrections_people.json` → `people.aleksandr-sidyakin.set.roles`: append (keep the three ЦБСТ roles):

```json
{"entity_slug": null, "body": "Государственная Дума IX созыва",
 "title": "Chair, State Duma Committee on Digital Development and Artificial Intelligence",
 "from": "<date of the Duma vote; ЦБСТ 2565 (~24.09) reports only Medvedev's proposal>",
 "to": null, "source_id": "<sid of TGPOST ano_cbst-2565, or a duma.gov.ru record of the vote>"}
```

Settle what the sources actually say first. ЦБСТ post 2565 says Medvedev «предложил кандидатуру». Наша Правда post 686 congratulates him «с назначением на пост председателя комитета». Zona.media (24.09.2026) gives the committee's remit as «маркетплейсы, БПЛА и креативными индустриями». A Duma record of the vote is the better source for `from`. Наша Правда's line «Мы давно сотрудничаем с Александром» is a candidate for `quotes.json`.

**«Булат» в.6.** `products.json` → `bulat.versions`: append

```json
{"slug": "bulat-v6", "name_ru": "«Булат» в.6", "firmware": null,
 "description": "Announced by the maker as «новый стандарт обнаружения»; limited version for those who supplied trophies, 4th quarter 2026. Not yet released.",
 "source_id": "<sid of TGPOST ru3mx-741>"}
```

Post 742 restates firmware 1.71 for в.4, which matches the record; it adds nothing unless the record wants a dated firmware history.

**КБ «СПЕКТР» on РОЙ.МАРКЕТ.** Correction to the trial report: the registry already has this seller as `listed` since 06.07.2026 (post 321, s8737), not onboarding. Post 337 adds a new product announced for the platform: «Спец серия пропеллера 14х10 для Молния-2 из Армамида. Через неделю будет доступна на РОЙ. МАРКЕТ и OZON». Record it as a `products[]` entry on the `kb-spektr-novosibirsk` → `ooo-mptm` `sells_for` record, plus a `status_history` entry `{status: "announced", as_of: <post date>, source_id: <sid>}`, but only if the envelope rules allow a per-product status. Otherwise put it in `note` and leave the edge at `listed`.

**Ткачук / Уралдронзавод.** Correction to the trial report: the car-bomb attack (05.08.2026) is already recorded on `uraldronzavod` from ЦБСТ post 2383 (s6911). The @bayraktar1070 forward added nothing new, and that item is dismissed in `developments.json`. A person record for Владимир Ткачук is still missing. The ЕГРЮЛ director field is restricted (`_egrul_vypiska.json`), so the patronymic needs another primary source. Until one is found, a minimal record would rest on ЦБСТ posts 2383 (s6911) and 2116 (s8927). Make it only if a record without a patronymic is wanted.

## 3. Then

`python3 scripts/build_relationship_graph.py && python3 scripts/check_registry.py`, then set the matching `developments.json` items to `recorded` with a note naming the source id.
