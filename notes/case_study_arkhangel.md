# Проект «Архангел»: interceptor drones, combat-drone training and state-format diplomas from one Telegram network, with no public contract behind any of it

2026-09-20. Every claim carries a `[sNNNN]` source id, resolved in the table at the end. Russian is quoted verbatim from archived posts; English is analysis. **Registry position: tier manufacturer, ЦБСТ tie none found. The project is treated as adjacent to the core network, not part of it.**

## The finding

Проект «Архангел» sells three things through one set of Telegram channels: an interceptor drone it calls a rocket, training for combat-drone operators, and diplomas for the graduates. The project itself is not a registered legal entity. Its head, Михаил Филиппов, owns 80% of one Moscow company created in March 2026 [s5474]. Its training credentials come from an Omsk-registered education institute that has sold job-centre retraining to Russian regional governments since 2017 [s7907]. Its interceptor is announced as produced with the state arms concern «Калашников» [s5476–s5483], and its radio comms brand, ГЕРМЕС, is named a resident of the ЦБСТ network by ЦБСТ's own channel [s7597]. No procurement record links any of these to a state customer.

## Officially X, actually Y

| Officially | Actually |
|---|---|
| «в рамках всероссийского добровольческого проекта "Архангел"», in a TASS report of 06.06.2023 [s5485] | No legal-entity registration found for the project itself; the record is held separately from the same-brand companies so the two are not conflated [s5454] |
| «КБ» (design bureau) | Runs entirely through Telegram: `@projectArchangel` (10,064 posts scraped), `Archangel_Forum` (86,291), `proekt_arhangel` (1,073), counts from the local scrape of 20.09.2026 |
| Education institute АНО «НИИ ДПО» (ОКВЭД 85.42.9) | The issuing body of the «Школа внешних пилотов (операторов) БПЛА «Архангел»»: ten specimen diplomas and certificates bear the Архангел logo [s7897–s7906, s7907] |
| ООО «Архангел» (Мелитополь / Запорожье), ОКВЭД production of unmanned aircraft | FY2025 revenue ₽55.77m, all tagged «Образовательные услуги» (educational services) [s0381]; Rosobrnadzor licence for professional training issued 09.10.2024 [s1166]; Ukrainian military intelligence describes a network of training centres in 20 cities [s5412] |
| A charity fund «Сармат» | Founded 15.10.2024 in Таганрог; the founders include Алексей Рогозин, son of Дмитрий Рогозин, whose unit the project names as a partner [s7870, s7693] |

## The product: an interceptor with two spec sheets

**What it is.** The channel calls it «по сути, управляемая ракета с вертикальным взлётом, или возможностью размещения на самолете-матке» and published the drawings and assembly diagrams free on 31.05.2025 [s5475]. The kit is a 3D-printed airframe on a Betaflight controller with a public bill of materials [s5454, s5452]. A B2B integration channel for aircraft, radar and vehicle makers is offered through `@arhangel_channel_bot` [s5454].

**Two spec sheets.** The channel's own figures conflict, even within one file. Its build post of 26.06.2026 gives a range of up to 50 km, a maximum of 340 km/h and a cruise of 100–120 km/h, and a later part of the same file gives «пиковая скорость 315кмч» and economy flight at «140кмч» [s5454]; the post of 06.09.2026 repeats 315 and 140 [s7653]. CNews, reporting the Kalashnikov tie, says the drone reaches «до 280 км/ч» at a range of up to 50 km, with a payload «от 700 гр до 7 кг» [s5477]. No independent test data is on file. Which figure is true, and whether they describe different variants, is not established.

**Production tie:** {press} «Калашников» and «Архангел» signed a memorandum on 27.08.2025 under which Архангел selects, verifies and combat-tests developments from independent engineers and small teams, and «Калашников» provides industrial production (press paraphrase, not a quotation). Independent outlets report it (aviation21.ru, CNews, TASS syndication, EADaily) [s5476–s5483]; CNews, vpk.name and www1.ru name Филиппов [s5477, s5478, s5482, s5483].

**Radio link, and the one path to ЦБСТ:** {open} (each side names the other; no contract on file). ЦБСТ's own channel calls «КБ «Гермес»» a «резидент ЦБСТ» (14.11.2025) [s7597]; the registry identifies that brand as НПО «КАЙСАНТ», an identification the page does not re-derive. Архангел's channel carries 60 ГЕРМЕС video posts in the local scrape and its bill of materials lists «Связь: Гермес или аналоги» [s5452]. ГЕРМЕС's own channel writes: «Дроны-перехватчики проекта «Архангел» оснащены дальнобойной связью ГЕРМЕС.» (14.05.2026, forwarded into `mil_hub` msg 130001). This is the only path from the Архангел cluster to the core network in the registry. No supply contract or invoice is on file.

**Combat version:** {open} «В боевой версии «Архангела» используется цилиндр с боевой частью» and a civilian version «можно оснастить утяжелённой головкой и использовать как таран» [s5454].

**Partnerships claimed, not verified.** A signed agreement with Тульское ЦКБА to integrate the interceptor into its radar systems (proekt_arhangel msg 631/653) [s5475]; display to Путин at Мулино on 16.09.2025. The visit is confirmed by Interfax and RIA, but neither names Архангел, ЦБСТ or Безруков, so the exhibit itself rests on the project's own post [s5479, s5480].

## The service: a training funnel with a paper layer

1. **Free remote course.** «Запись на бесплатное обучение, и более подробная информация в боте» `@course_bpla_bot` (msg 7109, 02.04.2025).
2. **The accredited layer.** «Архангел» предлагает пройти дистанционное обучение и стать востребованным специалистом. Кафедра общественной безопасности АНО «Научно-исследовательский институт дополнительного профессионального образования» … «Выпускников после профессиональной подготовки ждут уже в «Архангеле», где к теории прибавится практика под руководством опытных инструкторов.» (msg 7130, 05.04.2025).
3. **The credentials.** On 07.02.2026 the channel and `Archangel_Forum` posted ten documents: pilot, mechanic, UAS-data-processing and pilot-instructor certificates and diplomas, plus an «Архангел ЩИТ» air-defence instructor diploma and an АНТИБПЛА certificate (msgs 9507–9516) [s7897–s7906]. They are specimens: the holders are «Сталин И.В.» and «Гагарин Ю.А.» with zeroed serials. Every one is signed «Еськов Н.Л., Ректор». They claim registration in the federal ФИС ФРДО register and print licence Л035-01273-55/00207746 of 18.02.2022.
4. **Placement.** The channel says graduates go to named units: 51-я армия (78-й полк, «две трети наших выпускников» (msg 10782, 13.09.2026), 205-я бригада, 1-я Славянская бригада), and to «Рубикон» [s7654, s7650, s7648]. «Главной целью нашего центра является подготовка специалистов для Министерства обороны. Это факт.» (msg 10573, 28.07.2026) [s7651]. All placements are the channel's own statements.

**The institute.** АНО «НИИ ДПО» (ИНН 5505057400) was registered in Omsk on 12.09.2017; Еськов Николай Леонидович has been rector since 25.08.2022 [s7907]. A second ООО «НИИ ДПО» (ИНН 7733462457) was registered in Moscow on 24.01.2025 with Еськов as rector and 100% owner [s7908]. Zakupki.gov.ru lists 81 supplier contracts for the АНО; 80 were read: 2017–2022 job-centre retraining (Омская обл., ХМАО, Мурманск, Красноярск), about ₽4.4m in total, none military [s7910]. The institute is an ordinary education vendor that the project uses as its accreditation. The certificates' licence number differs from the one in ЕГРЮЛ (55Л01 75-п, 31.10.2017) and has not been checked against the Rosobrnadzor register.

**Earlier tie to state officials:** {open} In July 2023 the channel says the Russian-installed governor of Запорожье, Евгений Балицкий, handed course certificates to BARS-32 graduates (msg 1358) and the Ministry of Defence assessed submitted drones at a range trial in August 2023 (msg 1483). These are early-archive samples not yet archived as sources [s5475].

## Who is in it

| Person / body | Role | Grade |
|---|---|---|
| Михаил Филиппов | Head; callsign «Архангел», `@arhangel76`; 80% of ООО «Архангел Групп» since 12.03.2026 | {doc} [s0234, s5465, s5474] |
| Еськов Н.Л. | Rector of both НИИ ДПО; signs every credential in the set | {doc} [s7907, s7908, s7897] |
| Дмитрий Рогозин | Commander of ЦСН «Барс-Сармат» per the unit's own site [s7687]; Архангел's channel writes «Флагманом движения является Д.О. Рогозин» (05.11.2024) [s6912]. On his own channel on 22.04.2025 he posts about Проект «Архангел»: «Теперь — в составе военно-учебного центра Центра специального назначения беспилотных систем "Барс-Сармат". Присоединяйтесь!» [s6915] | {doc} [s6912, s6915] |
| ЦСН «Барс-Сармат» (Рогозин's unit) | Joint approbation and a mutual «объединяем ресурсы» agreement, 17.10.2024 | {doc} [s7693, s7694] |
| Алексей Рогозин | Founder of Фонд «Сармат», the unit's donation fund; Гамируллин М.Д. directs it | {doc} [s7870] |
| АНО ЦПВ «ЗОВ-АА» (Прибылова К.А.) | Co-organiser of joint events with Архангел, 2024–2026 | {doc} [s7727, s7728] |
| НПО «КАЙСАНТ» | Supplier of ГЕРМЕС comms {open}; the ГЕРМЕС brand is named a ЦБСТ resident by ЦБСТ's own channel {doc} | [s7597] |
| Гагаринг | Its own storefront channel cross-posts Архангел at least five times, including a B2B pitch for interceptors and facility-defence contracts on 30.08.2026 | {doc} [s5539] |

## Same name, other entities

Nine companies carry the «Архангел» name. Only one, Архангел Групп, has a documented ownership tie to Филиппов. The rest are graded separately so the brand is not read as a corporate group: the Мелитополь, Запорожье and Крым companies are tied to one another by people, since Кусумов Вахид Абдулович owns 100% of both Мелитополь companies and Тимофеев Владимир Сергеевич directs the Запорожье and Крым ones [s0229, s5504, s5508], and Ukrainian military intelligence describes training centres in 20 cities [s5412]; «Архангел-ЦЕНТР» (ИНН 5032379630, Odintsovo) is listed by the EU as a military training organisation, in Council Implementing Regulation (EU) 2026/509 of 23 April 2026 {doc} [s7941]; an OpenSanctions match also lists Ukrainian, French, Swiss, Belgian and Monaco regimes {open} [s5413]; no tie to Филиппов is established; «Архангел-Щит» (ИНН 5027339008) is named as the interceptor's manufacturer in an archived summary of Mash's Expo.UAV coverage, a paraphrase and not the article {press} [s5458]; its director is Хабибулин Владимир Игоревич and its sole founder is Кулемин Игорь Александрович [s5517, s6797].

## B2B, B2G and the money

- **B2B:** {doc} as an offer only. «Руководителям предприятий критически значимой инфраструктуры … создание мобильных расчётов защиты объекта, оснащенных современными средствами обнаружения и дронами-перехватчиками» (msg 10668, 17.08.2026), and a service pitch through the Гагаринг channel [s5539]. No customer is named and no contract is on file.
- **B2G: not supported by any procurement record.** Every Архангел-named entity on file returned zero zakupki hits as buyer or supplier in the scan of 05.09.2026 (scan log). The only state-contract footprint in the cluster is the НИИ ДПО's job-centre retraining.
- **How it runs, on the project's own account.** A 2023 iStories interview has Филиппов saying the project lived on one unnamed patron and made «крайне мало» drones [s5484]. Two later claims point the other way: the channel says its two Херсон and Запорожье companies work «в интересах и по задачам ГУБП ВС РФ» (proekt_arhangel msg 623, 11.10.2025, local scrape), and on 07.07.2026 it recruits for its own private security firm, «У нас не будет контракта ни с Минобороны, ни с доброкором» (msg 10453). The stated pay is ₽200,000–400,000. The state relationship is asserted, not documented.

## Timeline

| Date | Event |
|---|---|
| 07.11.2022 | First posts on `@projectArchangel` [s5475] |
| Nov 2022 – 2023 | City-by-city hobbyist pilot teams (iStories) [s5484] |
| 06.06.2023 | TASS-sourced report of a project loitering-munition concept [s5485] |
| 25.08.2023 | iStories investigation «Народный ВПК» [s5484] |
| 17.10.2024 | Meeting with Дмитрий Рогозин; joint arrangement with «Барс-Сармат» [s7693, s7694] |
| 05.04.2025 | Kafedra of НИИ ДПО pitched as the remote course [msg 7130] |
| 22.04.2025 | Рогозин's channel says Проект «Архангел» is «в составе военно-учебного центра» of «Барс-Сармат» [s6915] |
| 31.05.2025 | Interceptor drawings published free [s5475] |
| 27.08.2025 | Kalashnikov memorandum [s5476–s5483] |
| 16.09.2025 | Putin visits Мулино; Архангел claims the exhibit [s5479, s5480] |
| 07.02.2026 | Ten specimen diplomas and certificates posted [s7897–s7906] |
| 12.03.2026 | ООО «Архангел Групп» registered, Филиппов 80% [s5474] |
| 07.07.2026 | Announces its own security firm [msg 10453] |
| 30.08.2026 | B2B pitch for interceptors through the Гагаринг channel [s5539] |

## What is not established

- Whether Проект «Архангел» is legally part of the «Барс-Сармат» training centre, as Рогозин's post of 22.04.2025 says [s6915]. No registration or agreement shows it; the tie may be a cooperation, not a corporate one.
- Which legal entity invoices for the interceptor or the courses. The channel names «Архангел Групп» as the contact for its «группа компаний» [msg 10668], but no sales record is on file.
- Whether the certificates were issued to real people, and whether ФИС ФРДО holds entries for them. The set on file is specimens only.
- Which НИИ ДПО entity (АНО or ООО) issues Архангел credentials since 2025, and the licence number discrepancy.
- Whether the interceptor's real speed is 280, 315 or 340 km/h.
- Whether the Мулино exhibit, the Тульское ЦКБА agreement and the «ГУБП ВС РФ» work are anything other than the project's own statements.
- Who owns АО «МИКЦ» (a co-founder of Фонд «Сармат») and who directed the Фонд before 09.07.2026.
- The 2023 Балицкий and Ministry of Defence claims: early-archive samples not yet archived as proper sources.
- One of the НИИ ДПО АНО's 81 zakupki contracts (2552300339718000005) was not read.

## Evidence base

Registry records: `proekt-kb-arkhangel`, `ano-nii-dpo`, `ooo-nii-dpo`, `fond-sarmat`, `csn-bars-sarmat`, `ano-tsvp-zov-aa`, `npo-kaysant`, `ooo-arkhangel-*`; people `filippov-mikhail-gennadevich`, `eskov-nikolay-leonidovich`, `rogozin-*`. Scrapes: `projectArchangel`, `Archangel_Forum`, `proekt_arhangel` in `data/roymarket.db`. Primary documents: ЕГРЮЛ выписки [s7870, s7907, s7908], the certificate set [s7897–s7906], zakupki scan [s7910], press [s5476–s5483, s5479, s5480, s5484]. The only sanctions statement on this page, for «Архангел-ЦЕНТР», is the EU listing in the Official Journal text on file [s7941]; the other regimes rest on an aggregator match [s5413] and are graded Open.
