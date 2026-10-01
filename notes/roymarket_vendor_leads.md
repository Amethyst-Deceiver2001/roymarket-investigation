# РОЙ.МАРКЕТ vendors outside the registry: self-reports and what they show

Opened 2026-10-01. Working note, not published. Source ids resolve in `data/registry/sources.json`. Nothing here is a registry fact about an entity: the one vendor below has no established legal identity yet.

## Why this note exists

The working hypothesis was that РОЙ.МАРКЕТ vendors are, by default, ЦБСТ residents. Two Telegram channels now report onboarding or selling through the marketplace. One of them has no ЦБСТ tie on file and no registry record.

## 1. КБ «СПЕКТР» (Новосибирск): reports onboarding, shipping goods with a РОЙ label, no ЦБСТ tie found

**Own channel, @kb_spektr** (1 161 subscribers on 2026-10-01; bio «Все виды НИОКР, реверсинжиниринг, аддитивные технологии … вакуумная формовка … металлообработка», s8736):

- Post 321, 06.07.2026: «По заявкам трудящихся масс осваиваем Роймаркет. Теперь ТЭЧ могут сами закупать наши пропеллеры напрямую в Роймаркет.» The attached photo shows a cardboard carton with a label carrying the «РОЙ» logo and QR code, article «А0-13805373», «Лопасти для дрона 8 дюймов, 100 шт (25 комплектов по 4 шт (2Л+2П)), КБ Спектр», and tape printed «КБ «СПЕКТР»» (s8737 page, s8734 image). The label is the strongest item: it shows goods packed and labelled in РОЙ's system, not only an intention.
- Post 322, 07.07.2026: «Скоро на Роймаркет можно будет приобрести лучшие новосибирские АКБ 6S 10000 mah 15C» (s8737). Video; its thumbnail shows only a box on a pallet. Batteries are "soon", not yet listed, on the post's own wording.

**What the same channel says about its other sales** (s8737, read in the preview; not archived post by post): Ozon seller page `ozon.ru/seller/4015246` (post 240, 09.02.2026), a retail warehouse in Донецк (post 262, 11.03.2026), «отзывы с фронта» behind a 15-inch propeller (post 263, 13.03.2026). So РОЙ.МАРКЕТ is one of at least three channels for this vendor.

**Press** (read in full, original Russian; TASS text as carried by www1.ru): «Новосибирское конструкторское бюро (КБ) «Спектр» начало серийное производство складных пропеллеров для БПЛА самолетного и мультироторного типа», up to 20 thousand items a month, per executive director Андрей Братеньков (12.07.2025, s8733). Earlier: production of propellers for the captured heavy drone «Баба-Яга», 1 000 sets a month (06.01.2025, s8732). Neither article names a legal entity or ИНН.

**ЦБСТ tie: none found, with limits.** Query «КБ Спектр» (0 hits) and «kb_spektr» (0 hits) over the 2 308 posts of @ANO_CBST in the local scrape, with the matcher's positive control passing. ЦБСТ post 58 (22.08.2024) says Russian FPV propellers beat HQProp but names no maker; not attributed. Of @kb_spektr I read posts 180-346 (148 posts) in the public preview: none names ЦБСТ. Posts 1-179 are unread and the channel is not in the local DB. Absence of a tie is not shown; it is "not found in what was searched".

**Legal identity: not established, so no entity record.** The user supplied ИНН 5445029638 on 2026-10-01. The ЕГРЮЛ extract pulled that day (s8739) is for ООО «КОНСТРУКТОРСКОЕ БЮРО «СПЕКТР»», ОГРН 1195476049196, Новосибирск, ул. Троллейная 87/1, registered 02.07.2019, director and 100% participant Детинов Максим Борисович, capital ₽10 000. It was **struck off on 30.06.2022** («Исключение из ЕГРЮЛ недействующего юридического лица», ГРН 2225400672286). The vendor was selling in 2026 and TASS named a different executive director (Братеньков) in 2025, so this ИНН does not show who runs the vendor today.

The open ЕГРЮЛ search (name queries, 2026-10-01) shows two sibling entities created the same day by the same person with consecutive ИНН: ООО «КБ «СПЕКТР-ВМ»» (ИНН 5445029652, struck off 27.05.2022) and ООО «КБ «СПЕКТР-ИНЖИНИРИНГ»» (ИНН 5445029645, ОГРН 1195476049185, still active, now in Бердск, director and 100% participant Детинов; extract s8740). The last is the only live member of the trio. Its ОКВЭД list is a broad mix (it includes meat processing and grain growing next to engineering), nothing that reads as propeller manufacture, and its extract has no link to the Telegram vendor. A name search on «Братеньков Андрей» is capped at 20 rows and returned mostly other people; the ИНН search above is the reliable one. Name queries for other «КБ Спектр» entities returned Moscow, St Petersburg, Rostov and Orenburg entities, none checked against this vendor.

So, as of now: the vendor's name and region match a family of Детинов entities, one of which is active, but nothing printed in the archived documents says that any of them is the vendor. Settling it needs one of: the requisites on the vendor's Ozon seller page or a РОЙ label/invoice, a site or older channel post that prints an ИНН, or a named link between Братеньков and an entity.

**Hypothesis tested 2026-10-01: Братеньков sells under his own ИП.** The Новосибирск business-support portal partner.nso.ru lists «ИП Братеньков Андрей Алексеевич», ИНН 540787849136, Новосибирск, site kbspektr.ru, trading as «КОНСТРУКТОРСКОЕ БЮРО "СПЕКТР"» (listing dated 09.06.2022, s8743). Its description is word for word the bio of the @kb_spektr channel (s8736: «Все виды НИОКР, реверсинжиниринг, аддитивные технологии (3D сканирование/моделирование/печать пластиками, композитом и металлом) …»), so this is the same business, and the surname matches the executive director in the TASS articles. What the documents say about it:

- **The ИП is closed.** ЕГРИП extract of 01.10.2026 (s8741): ОГРНИП 307540721400012, registered 02.08.2007, «Прекратил деятельность в связи с принятием судом решения о признании его несостоятельным (банкротом)», 23.04.2020 (ГРН 420547600422151). A search by that ИНН returns this one registration only: no later ИП under the same ИНН. So the 2022 portal listing was already stale when it was made, and an ИП registration cannot be what sells in 2026.
- **The listed site is gone.** `kbspektr.ru` now renders a reg.ru page offering the domain for sale (headless render, 01.10.2026, s8742).
- **Same-name legal entities came afterwards.** The three «Спектр» ООО of Детинов were all registered on 02.07.2019, nine months before the ИП's bankruptcy ended it; two were struck off in 2022 and «СПЕКТР-ИНЖИНИРИНГ» is live (see above). The documents show the dates and no link between Братеньков and Детинов. Why the business was split across entities is not established and is not inferred here.

So the hypothesis is half-right: the business was Братеньков's own ИП until 2020 and the vendor presents the same business and bio, but a closed ИП is not the 2026 seller, and no document names the entity that is. The question stays open. The next documents that would answer it are the Ozon seller's requisites, a РОЙ label or invoice for the carton in post 321, a ФНС check of Братеньков's participation in юрлица, or a ЕГРЮЛ extract naming him as director or participant of any entity.

**Second lead, supplied by the user 2026-10-01: the Ozon seller for «Спектр» is ИП Маврин Олег Владимирович (ОГРНИП 320547600022326).** The Ozon seller page itself was not read by us (it returns HTTP 307 to a plain request), so the Ozon-to-Маврин link rests on the user's reading of it. What the documents we hold say:

- **ЕГРИП extract of 01.10.2026 (s8744):** ИП МАВРИН ОЛЕГ ВЛАДИМИРОВИЧ, ИНН 540316596357, ОГРНИП 320547600022326, registered **18.02.2020** by МИФНС № 16 по Новосибирской области, active (no termination entry), e-mail INFO@ARM-PNT.RU. Main ОКВЭД 20.30.2 (paints, lacquers, enamels); others 20.12, 20.30, 20.30.1, 32.40 (games and toys), 32.99.7 (demonstration models), 46.73.4 (wholesale paints), 46.74.1 (hardware). Nothing in the list covers plastic parts or aircraft components, so the declared activity does not match propeller sales. That is the registry's usual declared-versus-actual observation, not a finding of wrongdoing: sole traders often register broadly.
- **The e-mail domain is his own paint brand.** The Wayback capture of arm-pnt.ru of 28.06.2022 (s8810) is a template site of «ARM.PNT», «Краски и химия для масштабного моделирования», Новосибирск, with placeholder text; it matches his ОКВЭД. The domain no longer resolves.
- **No document we hold links Маврин to Спектр**: the Dec 2023 site of kbspektr.ru (below) never names him, and the user-reported ФНС «Прозрачный бизнес» check found Братеньков in no юрлицо.

**Archived kbspektr.ru, 06.12.2023 (Wayback, s8811).** Title «kbspektr — Мы гарантируем, что ваши задачи импортозамещения будут решены качественно!». Phone +7 913 912-55-01 (the same number as on Братеньков's ИП portal listing, s8743), e-mail kbspektrnsk@gmail.com, contacts @andrey_bratenkov (Telegram, Instagram) and @kb_spektr. Content: a Marussia B1 car project, sports karts, hockey blades «RED STAR» («Технология разработана Конструкторским бюро «СПЕКТР» @kb_spektr», made with the support of «ОПОРА РОССИИ» НСО and Минпромторг НСО), and engineering services (3D scanning, reverse engineering). In the first person: «Я @andrey_bratenkov сам играю в хоккей … я и моя творческая команда @kb_spektr». No ИНН, ОГРН, ИП or ООО name is printed anywhere in the visible text. So in 2023 the business was run in Братеньков's name and phone with no legal entity shown, and propellers were not on the site yet.

**Timeline from the documents (dates only; no document says these events are connected):**

| Date | Event | Source |
|---|---|---|
| 02.07.2019 | Three «КБ «СПЕКТР»» ООО registered, Детинов Максим Борисович director and 100% participant | s8739, s8740 |
| 18.02.2020 | ИП Маврин Олег Владимирович registered | s8744 |
| 23.04.2020 | Братеньков's ИП ceases on a court bankruptcy decision (entry 14.05.2020) | s8741 |
| 30.06.2022 and 27.05.2022 | Two Детинов ООО struck off as inactive | s8739 |
| 09.06.2022 | Портал partner.nso.ru still lists Братеньков's closed ИП | s8743 |
| 06.12.2023 | kbspektr.ru, run in Братеньков's name | s8811 |
| 2025 | TASS names Братеньков executive director of КБ «Спектр» | s8732, s8733 |
| 06.07.2026 | Channel posts the РОЙ-labelled carton | s8737 |
| 14.08.2026 | ИП Карпушин Александр Александрович registered (UAV-manufacturing ОКВЭД) | s8812 |
| about mid-Sept 2026 | «Звезда Спектр» store opens on Ozon ("работает с Ozon 18 дней" on the user's screenshot; date of the screenshot not recorded) | s8814 |

**The label photo, read closely (user's 960×1280 copy, s8809; no EXIF).**
- The QR code decodes (checked with OpenCV) to `A0-13805373`, identical to the printed article: it carries the SKU only, with no seller, ИНН or URL.
- РОЙ logo at top left, a perforated divider, then the article and the item name in a serif, template-printed layout with a stray line break: «Лопасти для дрона 8 дюймов, 100 шт (25 комплектов по 4 шт (2Л+2П)), КБ Спектр». The vendor is named by brand only.
- Two cartons are stacked, both with the same article: at least 200 propellers in this shipment (2 × 100).
- The cartons are sealed with custom-printed tape reading «КБ «СПЕКТР»» with a globe-and-gear emblem, so the manufacturer packed them; the РОЙ label was stuck on afterwards (on the lower carton it overlaps the tape edge).
- The format `A0-` plus eight digits is a РОЙ item number. The string appears nowhere else in the Telegram archive or in our sources, so the listing cannot be located from our data.

**Two Ozon sellers for КБ «СПЕКТР» products (user screenshots of Ozon's «О магазине» panels, 2026-10-01; archived s8813, s8814).**

| Ozon storefront | Seller of record as printed | ОГРНИП | Notes on the screenshot |
|---|---|---|---|
| «СПЕКТР конструкторское бюро» (logo of the bureau) | ИП Маврин Олег Владимирович | 320547600022326 | seller card shows 1.7K orders (s8813) |
| «Звезда Спектр» | ИП Карпушин Александр Александрович | 326547600152216 | «Premium магазин», «Работает с Ozon 18 дней», 2% discount from ₽10 000; category Электроника / Квадрокоптеры и аксессуары; listings with the bureau's «СПЕКТР конструкторское бюро» logo, «10" пропеллеры», material «Армамид» (s8814) |

The ОГРНИП numbers on the screenshots match the extracts we pulled. The second store is new and the ИП behind it was registered only on 14.08.2026.

- **ИП Карпушин Александр Александрович** (ЕГРИП extract of 01.10.2026, s8812): ИНН 540863046567, ОГРНИП 326547600152216, registered **14.08.2026** by МИФНС № 16 по Новосибирской области (the same office as Маврин's ИП and the three Детинов ООО), active, e-mail 13KAMEN@MAIL.RU. Main ОКВЭД **30.30** (production of aircraft); additional codes include 25.40 (weapons and ammunition), 28.99.3 (launch devices for aircraft), 30.30.1, 30.30.3, 30.30.5, 30.30.6 (**unmanned aircraft systems**), 30.30.39, 26.51.2 (radar and radio-navigation equipment), 33.13, 52.23.13 (aviation work), 71.12, 71.20, 72.19. Unlike Маврин's paint-trade codes, this list is a UAV-manufacturing profile. A broad ОКВЭД list proves nothing about activity.
- **Reading the two together (observation, not a finding):** the bureau's products are sold on Ozon by two different sole traders, neither of them Братеньков. One has traded since 2020 on an ОКВЭД list of paints and toys; the other was registered five weeks after the 06.07.2026 post about joining РОЙ.МАРКЕТ and carries a UAV-manufacturing list. Nothing archived says who the manufacturer of record is, or whether either ИП produces anything.
- **Name echo, weak:** on his Dec 2023 site (s8811) Братеньков says he plays for the hockey team «Звезда Новосибирска»; the new store is «Звезда Спектр». «Звезда» is a common word and nothing links the two.

**Scope (user, 2026-10-01):** Братеньков and Маврин are persons of interest, and Братеньков is publicly associated with Спектр in the media. That settles the PII-scope question for those two. Карпушин is recorded here from his public ЕГРИП extract only; whether he gets a person record has not been decided.

## 2. НПЦ БАСиРТК (ООО, ИНН 3300009049): post 695, read as Роймаркет by the investigator's inference

@UAS_development post 695, 17.09.2026: «Начинаем работу через онлайн-маркетплейс для продукции двойного назначения. Специалисты были подготовлены заранее. #маркетплейс» (s8735 image; page capture s8738).

The photo is a certificate of the «Вайлдменеджер» (Wild Manager, wildmanager.ru) school, dated 29.01.2026, certifying that Ирина Байгутлина completed a 6-week programme «Востребованный менеджер маркетплейсов» (logos: Ozon, Яндекс Маркет, Wildberries). Ирина Байгутлина is the entity's owner and general director per its ЕГРЮЛ extract (s6782). Neither the text nor the image names Роймаркет, and the course is about three other marketplaces. Reading the post as a РОЙ.МАРКЕТ onboarding is an inference, not something the post says. **Investigator's decision, 2026-10-01 (user):** treat it as a РОЙ.МАРКЕТ onboarding, because «онлайн-маркетплейс для продукции двойного назначения» is taken to be a euphemism for it and no other online marketplace of that description is known. That is recorded as the investigator's reading with its basis, on the entity's open questions, and is not graded {doc}: the post itself never says it, so a published sentence must say «reported by the company as a dual-use online marketplace, understood by us to be РОЙ.МАРКЕТ», not «the company said it joined РОЙ.МАРКЕТ».

This entity is already a ЦБСТ accelerator participant (s7522), so even if post 695 is about Роймаркет it would not test the vendors-are-residents hypothesis.

## What this does to the hypothesis

- One vendor with documentary evidence of shipping under a РОЙ label (КБ «Спектр») shows no ЦБСТ tie in what was searched, though its legal identity is still open. If its identity and absence of a tie hold up, "vendors are residents by default" is wrong as a rule; Роймаркет sells to non-resident manufacturers too.
- It does not show the reverse: that Роймаркет and ЦБСТ are unconnected. Роймаркет's own ties to ЦБСТ are recorded elsewhere in the registry and are untouched by this.
- One example is not a rate. The question to answer next is how many of the vendors that name Роймаркет are residents, which needs a sweep of Telegram for self-reports like post 321, not more reading of this one channel.

## Handed to the user

- `@kb_spektr` added to `config/channels.txt`. Command: `python3 scripts/tg_scan.py --full --only kb_spektr`.
- `@UAS_development` is on the list but the scrape ends at message 672: `python3 scripts/tg_scan.py --only UAS_development`.

## РОЙ.МАРКЕТ operator: what the public site shows (read 2026-10-01)

Fetched from roimarket.ru (Russian originals, captures `data/sources/WEBCAPTURE_20261001_roimarket-ru-*.html`; not yet registered with source ids, held while another session edits `sources.json`). Pages: /legal, /legal/supplier-offer, /legal/buyer-offer, /legal/platform-rules, /contacts. The роймаркет.рф host did not answer from here; roimarket.ru did.

- /legal, last updated «29 июля 2026 года»: «Оферты для Покупателей и Поставщиков защищены: обезличенные редакции открыты всем, а полный текст с реквизитами доступен после входа». Supplier offer is «Редакция 3.0, вступает в силу 01.08.2026».
- The public texts print the operator's requisites masked: buyer offer §13 «Наименование: ООО «****» ИНН: **********»; supplier offer «Наименование Агента: ООО «****»»; platform rules §23 likewise. /contacts: «Оператор платформы», e-mail only.
- So the current public site does **not** name ООО «МПТМ». The brief's statement that МПТМ's address and its Банк ПСБ account are printed in the supplier offer rests on an earlier, unmasked view, with no archived copy; it is unverified here.
- Independent document: ЦБСТ's 2025 report to Минюст (s0207, section 2.2) lists ООО «МПТМ» ОГРН 1257700021468 as an LLC in which ЦБСТ participates since 22.01.2025. No share stated; the report does not say МПТМ runs the marketplace.
- **Resolved by the Wayback capture of 22.08.2026** (`data/sources/WAYBACK_20260822_roimarket-supplier-offer.html`, captured 22.08.2026 09:13:40 UTC, original read in Russian; plus the `sell-with-roy` page, `WAYBACK_20260822_roimarket-sell-with-roy.html`, from the user-supplied roимаркет.рф capture). The unmasked supplier offer, «Агентский договор-оферта для Поставщиков», редакция 3.0:
  - §1.1.1: «Агент / Оператор платформы / владелец агрегатора — Общество с ограниченной ответственностью «МПТМ», ИНН 9714068459, КПП 771401001, ОГРН 1257700021468», address 125167, Москва, … ал. Нарышкинская, д. 5, стр. 2, помещ. 1/1; it acts «от имени и за счёт Поставщика».
  - §17 «Реквизиты Агента»: «Платформа: роймаркет.рф»; account at ПАО «БАНК ПСБ», БИК 044525555.
  - The site header in that capture reads «ООО «МПТМ» · ИНН 9714068459». By 01.10.2026 the live pages show «ООО «****»» instead: the operator's name was masked between those dates.
  - The offer's counterparties are «Поставщики» (юрлица and ИП) selling through the platform; the platform is their agent, not the seller of record. That is the structure the registry's `sells_for` edges should point at.
  - `sell-with-roy` (same day): «РОЙ.МАРКЕТ - защищённый канал продаж товаров двойного назначения»; «Ваши товары могут продаваться не только на Wildberries и Ozon». ЦБСТ's own phrase, used by the operator's seller page.
- Still not established: the ЦБСТ share in МПТМ (s0207 gives participation since 22.01.2025, no percentage; ЕГРЮЛ participants restricted since 15.07.2026).

## Self-report sweep over the rescanned archive (2026-10-01)

Archive: 503,714 posts, 56 channels, after the full rescan (`tg_scan.py --full --days 1680`, aborted once and finished with `--only kb_spektr`). Matcher: `tg_post_coverage.py --all-channels --include-archived --term …` (folded for case and ё, positive control 8/8 passed on every run). Every hit was read; none is sliced.

| Query | Hits |
|---|---|
| «роймаркет» | 3: asidyakin/618; kb_spektr/321, /322 |
| «рой.маркет» | 13, all ЦБСТ's own posts or reposts of them (2386, 2392, 2398, 2413, 2414, 2415, 2420, 2433, 2440; mil_hub and asidyakin copies) |
| «рой маркет» | 3: my_el_lab/2076 (12.06.2025, a question list: «Почему не взлетел маркет дронов? (Рой маркет - что с ним не так)»); two customer messages in the 3mx chat (below) |
| «стать селлером» | 1: ЦБСТ 2413 (a heading) |
| «онлайн-маркетплейс» | 6, one of them a vendor channel: UAS_development/695 |
| «#маркетплейс» | 1: UAS_development/695 |
| «защищённый канал продаж» | 4, all ЦБСТ (2413, 2415, 2420, 2433) |
| «поставщиком рой» | 1: ЦБСТ 2433 |
| «двойного назначения маркетплейс», «селлер роймаркет», «маркетплейс двойного» | 0 |

**Result.** Two vendor channels name the platform or its generic description: `@kb_spektr` (posts 321–322, names «Роймаркет», `doc`) and `@UAS_development` (post 695, generic phrase, inference). No third vendor self-report is in the archive. The sweep reads post text only; captions on media and channels not on the watchlist are outside it. The deterministic route works: the phrase «онлайн-маркетплейс» plus «двойного назначения» finds post 695 by itself, so it is a usable codeword for the next rescan.

**New findings, each from a post read in full (archived s8847–s8864):**
1. **3mx is not documented as a РОЙ.МАРКЕТ seller.** In 3mx's customer chat on 02.09.2026 a customer asks (msg 42145) «Новая версия булата будет выставлена к продаже на рой маркет?» and the next message from the maker's side (msg 42146, 13 minutes later) says «Всю нашу продукцию можно приобрести только у нас на сайте 3mx.ru или у наших дилеров.» Another customer (msg 42151): «Очень нужно что бы Вашим дилером стал рой маркет». Limits: the DB does not store reply-to links, so the pairing is by adjacency; the responder is unnamed. This is the maker of a ЦБСТ-resident product (shown at Дронница 2025, s8842) saying it is not selling through the platform, while a non-resident (КБ «СПЕКТР») is.
2. **Launch attribution.** Сидякин (head of the Центральный исполком «Единой России»), 15.12.2025: «Вместе с партией и ПСБ запустили военный маркетплейс «Роймаркет». Платформа протестирована.» (s8847). The post does not name МПТМ. Recorded on `ooo-mptm` as a claim.
3. **Pilot to open platform.** ЦБСТ 2386 (05.08.2026): «Ранее площадка функционировала в рамках пилота»; 2413–2433 (13–20.08): opening to «сторонних» sellers, including «юрлица, которые уже работают на Wildberries, Ozon», and «Небольшая команда или независимый разработчик». КБ «СПЕКТР»'s post (06.07.2026) falls in the pilot period. Whether Спектр was invited under the pilot is not stated anywhere.
4. **Scale claims, self-reported.** «десятки потребителей», «каталог … до нескольких сотен позиций» (asidyakin 1230, 05.08.2026); goal 10,000+ items by 2027 (2414); all ТЭЧ of Минобороны to be connected by 1 September (ЦБСТ 2392, a plan). Whether the ТЭЧ were connected is not recorded.
5. **Size of the ЦБСТ contour.** «Сегодня в нашем контуре 525 компаний», «более 850 разработчиков» supported (asidyakin 1230): the brief's 525 now has a source; the wording is «в контуре», not «резидентов».

**Still open:** the Kommersant article (doc/8878535) and cbst.ru's «Стать селлером» page unread; the registered Поставщик behind Спектр; whether any ЦБСТ resident lists on the platform (the 3mx statement is one data point); post 700 of UAS_development («Антидрон-предложение от наших китайских партнеров», 23.09.2026) names no partner.
