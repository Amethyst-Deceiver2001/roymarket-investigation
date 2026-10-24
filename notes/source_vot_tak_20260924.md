# Source note: Вот Так, «Все дороги ведут в Кремль» (24.09.2026)

Logged 24.10.2026 at the user's request: what the article is, what it says about РОЙ.МАРКЕТ and ЦБСТ, how each claim stands against our record, and what we do not have. Everything here is the outlet's claim unless a second column says otherwise. The article is a press source (graded rep at best); nothing below was entered in the registry as a fact.

## The source

- **Title:** «Все дороги ведут в Кремль: кто стоит за Wildberries и Ozon — маркетплейсами под атакой ВСУ» (page title «Маркетплейсы военного времени. Кто стоит за Wildberries и Ozon»).
- **Publisher and author:** «Вот Так» (vot-tak.tv), «Редакция «Вот Так»», no individual byline.
- **Published:** 24.09.2026 06:00 (+02:00); modified 14:39 the same day.
- **URL:** https://vot-tak.tv/95546179/wildberries-ozon-kreml
- **Captured:** 24.10.2026 on this Mac. The page's visible markup carries only the lede; the full text (14,667 characters) is in the page's own structured data (`articleBody`) and was read in full in Russian. A summarising fetch tool was not used as the source.
- **Files** (`data/sources/`, gitignored, not yet catalogued because source ids are assigned on the archive Mac):
  - `PRESS_20260924_vot-tak-wildberries-ozon-kreml.html` (480,438 bytes, sha-256 starts `cd2d5556b8458a11`)
  - `PRESS_20260924_vot-tak-wildberries-ozon-kreml-articlebody.txt` (26,487 bytes, sha-256 starts `065dae8ceadf554c`)
- **Not done:** no Wayback capture (user rule: web archiving is run by hand), no RFC 3161 stamp yet (`timestamp_sources.py` after the next batch).

## What it says about РОЙ.МАРКЕТ and ЦБСТ, against our record

Quotations are verbatim from the article.

| Claim in the article | Our record | Standing |
|---|---|---|
| «Рой.Маркет», «в отличие от Wildberries и Ozon, не планирует открывать собственные склады — на этот раз товары для участников вторжения будут хранить сами продавцы». No document or speaker is named for it. | ЦБСТ's own wording (posts 2386 of 05.08 and 2392 of 06.08.2026, read in full): the platform moves to «модель распределённой логистики, самостоятельной работой поставщиков», and a network of «защищённых технопарков» (over 100 thousand m², over ₽25 billion) is planned. Neither post says "no warehouses". | **The press's reading of a documented plan.** Say "the platform is moving to distributed logistics with suppliers working independently (ЦБСТ, 05.08.2026); the press reads this as sellers holding the stock themselves (Вот Так, 24.09.2026)". Never put "no warehouses" in ЦБСТ's mouth. |
| «доступ на сайт «Рой.Маркет» как продавцу, так и покупателю открывается по запросу»; «Проверить, как именно сейчас выглядит ассортимент, затруднительно». | Matches the settled fact: the platform is login-gated; operator texts masked after 22.08. | **Independent press agreement that the catalogue is not open.** Access is "on request", a wording we did not have. Fits the "no public catalogue" line on the pages. |
| «защищенный канал продаж товаров двойного назначения»; «к следующему году в каталоге площадки будет больше 10 тыс. позиций». | Quoted as the creators' promise; the source is not named. | **Lead.** Find the ЦБСТ post or statement that says it (likely 2392 or the Наблюдательный совет release). |
| Reports of a full launch came «через месяц после первых атак по Wildberries» (first strikes on 18.07.2026, per the article's seller); development since 2025. | Our launch dating comes from ЦБСТ posts, not yet laid against this. | **Lead.** Not used on a page. |
| ЦБСТ was founded by «Единая Россия», Промсвязьбанк («опорная финансовая организация Министерства обороны») and Фонд «Наша правда»; Медведев is called «вдохновителем» «Рой.Маркета» by «представители ЦБСТ». | Registered founders: Фонд «Наша Правда» and ПАО «Банк ПСБ»; «Единая Россия» is a founder by ЦБСТ's own release of 13.08.2026 (shown beside the registered two on the landing page). | **Agrees with our record.** The «вдохновитель» line has no named speaker: find the ЦБСТ statement before using it. |
| Operator: Колударов Антон Валерьевич last director; «с конца августа» director data hidden in ЕГРЮЛ; **Иван Коптенко led the company until May 2026**, described as a friend of Илья Медведев and found in a leaked list of ФБК donors. | `ooo-mptm`: Колударов as director on 04.08.2026; director field restricted in the 07.09 pull. **No earlier director on file and no Коптенко record.** | **Registry gap, logged** as an open question on `ooo-mptm`. The friendship and donor-leak statements are the outlet's, not repeated as fact. |
| «В феврале 2025 года Медведев-младший совместно с «Нашей правдой» и другими членами «Единой России» передал участникам вторжения аппаратуру для борьбы с БПЛА.» | `deliveries.json` has «Наша Правда» handovers on 11, 17 and 19.02.2025; none names Илья Медведев. 17.02.2025 (`bulat-d02`, post 397) names Сидякин and a party project lead. | **Lead, unmatched.** Read the three February posts again for his name before linking. |
| Context on Wildberries and Ozon: at least 48 strikes in the summer, 14 victims, Data Insight losses ₽507.8bn, the owners' ties (Керимов, Тимченко and others). | Outside this investigation's scope. | Not recorded. The strikes are why "no warehouses" matters; they are not our evidence. |

## What we do not have

1. **A document or speaker for "no own warehouses".** The article names none. ЦБСТ's own text says "distributed logistics". Needed: the Наблюдательный совет release or a platform page that says suppliers hold the stock. The supplier offer (s8817, archive Mac only) may state who stores and ships; read it for «склад», «хранение» and «отгрузка» before the intro leans on this.
2. **A catalogue.** There is none public, and the article confirms access is on request. Nothing to check; do not list as work.
3. **The former director of ООО «МПТМ».** Need an ЕГРЮЛ extract or history before 05.2026 naming him. All pulls on file postdate the 15.07.2026 access restriction.
4. **The article's own sources.** It cites ФБК, «Проект», РБК, «Коммерсантъ», a seller, and leaked flight and donor data.
   - **ФБК, «Он вам не Димон» (2017), now read in full: see `notes/source_fbk_dimon_2017.md`.** We do know it; it is the origin of the Медведев attribution for ДАР and Градислава in the frozen brief (`notes/archive/brief_snapshot_2026-08-21.html`, lines 248 and 669). It had **no source record and no capture** until now. Captured 24.10.2026 from https://dimon.navalny.com/ (`WEBCAPTURE_20261024_navalny-dimon-on-vam-ne-dimon.html`, 302,947 bytes, sha-256 starts `a5ca3387deb54a98`, and the extracted text, 90,738 characters). Located, not yet read in full: the passages saying «Дар» gave Миловка to «Градислава» in 2014, that «Градислава» is a "дублёр" with Леонид Рубцов as founder and Иван Карабинский, a «Дар» employee, as director, and the property-register extract it cites. The text does not mention «Наша правда» or ЦБСТ (it predates both). The Медведев ownership is FBK's allegation, which the article records him denying through his press secretary; our own link from the two funds to the «Наша Правда» founding rests on the registry (sources s7370, s7521), not on FBK.
   - The rest («Проект», РБК, «Коммерсантъ», the seller, the leaks): we hold none. Anything we take from the article stays a lead until read in the original.
5. **An archived copy.** Only our local capture exists; no public archive or timestamp yet.
6. **A source id** for either capture (Вот Так or ФБК). Catalogue on the archive Mac (`inventory_sources.py`, then `extract_registry.py`), then cite the article by that id; until then cite it by URL and date.
7. **The locations.** The article says nothing about where the sellers or ЦБСТ sit. The address half of the intro rests entirely on registry addresses (58 of 70 tied entities have one) and on imagery we have not built (5 facility pictures of 88 media records).

## How this feeds the intro

- The strikes on the big marketplaces' warehouses are the reader's way in: why a marketplace "without warehouses" is a stated design choice.
- The "no warehouses" line is the **press's** and has to be worded that way; ЦБСТ's own documented wording is "distributed logistics" and "protected technoparks".
- The traceability argument stands on our own evidence: the register addresses of the operator, makers and sellers, graded by their extracts.
