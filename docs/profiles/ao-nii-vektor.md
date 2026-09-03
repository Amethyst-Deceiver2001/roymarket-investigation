# АО «НИИ «Вектор»»

`sanctioned` `manufacturer` 

ИНН 7813491943 · ОГРН 1117847020400

## At a glance

- **Legal form:** AO (joint-stock company)
- **ОКВЭД:** 26.30.13 — Производство средств связи, выполняющих функцию систем управления и мониторинга
- **Wildberries overlap:** none_found

## Government contracts

- customer: Министерство обороны Российской Федерации; reg_number: 1770425226115000509; date: 2015; value_rub: 92000000; items: Largest of 7 direct МО/Минпромторг contracts found (out of 154 total zakupki hits, ₽437.06m aggregate, mostly routine/municipal); this is the mil-relevant subset — ₽338.92m across МО (₽232.87m) and Минпромторг (₽75m ОКР-style) contracts. [s3214]
- customer: Министерство обороны Российской Федерации; reg_number: 1770425226117000583; date: 2017; value_rub: 67633097; items: Second-largest direct МО contract for this entity. [s3217]
- customer: Министерство обороны Российской Федерации; reg_number: 0173100004511002671; date: 2011; value_rub: 31260000; items: Third direct МО contract; entity also has 4 smaller МО contracts (₽20.2m, ₽15.9m, ₽11.87m, ₽6.25m) and one ₽75m Минпромторг contract not itemized here — see mine_zakupki.py --inn 7813491943 for the full breakdown. [s3146]
- customer: Министерство обороны Российской Федерации; date: 2013-2016 (9 contracts, 28.03.2013-14.10.2014); value_rub: 73028219; items: AGGREGATE -- 9 Минобороны contracts, 2013-2016, ₽73,028,219 combined, distinct from the already-itemized 7-contract/₽338.92m mil-relevant subset above. CORRECTED 2026-09-01: this entry was previously duplicated (two near-identical rows, one with reg_number null and one with reg_number 0173100004511002669) -- merged into one. The 0173100004511002669 reg_number was also wrong: that specific contract card is a real but unrelated 2011 Минобороны contract (₽15,900,000, "Модернизация стационарного автоматизированного комплекса контроля безопасности связи радиолиний КВ диапазона Р-452С"), already covered by the "4 smaller МО contracts" note on the 7-contract subset entry below -- its date (17.03.2011) never matched this aggregate's own claimed 2013-2016 range, which should have been caught at the time. A follow-up zakupki_customer_clusters.py re-scan (2026-09-01) found an 8-contract/₽57,128,219 unwired Минобороны cluster (14.10.2014-28.03.2013) that sums, to the ruble, with the mis-cited ₽15,900,000 contract to this entry's own total (57,128,219 + 15,900,000 = 73,028,219 exactly) -- strong evidence the "8 new" contracts are actually 8 of this same already-counted 9-contract cluster, not new money, and were not wired again to avoid double-counting. reg_number left null since no single contract represents the aggregate; the true 9-member reg-number list is not separately recorded. [s3144]
- customer: АО «Концерн «Моринформсистема-Агат»»; reg_number: 1772054420822000003; date: 2022-03-28; value_rub: 54900000; items: Аппаратно-программный комплекс, моделирующий функционирование автоматизированного канала радиотехнической разведки (АПК) -- a hardware/software complex simulating an automated radio-technical reconnaissance (SIGINT) channel, supplied to Концерн «Моринформсистема-Агат», Russia's principal naval C4I/combat-systems integrator (part of the naval defence-electronics cluster) -- a defence-prime customer relationship, distinct from the routine regional/municipal government supply that makes up most of this entity's zakupki footprint. Found 2026-09-01 via zakupki_customer_clusters.py non-recurring-tail review. [s3218]

## State-program participation

- name_ru: Атлас промышленности ГИСП (Государственная информационная система промышленности); name_en: GISP (State Industrial Information System) Industrial Atlas — federal company-registry map layer; role: Company listed in the Ministry of Industry and Trade's official industrial-facility geodatabase, classified under industry '(unclassified)' with primary ОКВЭД 26.30.13 — independently corroborates the entity's ИНН/ОГРН/address/ОКВЭД via a second, unrelated federal data source (matches EGRUL exactly).; as_of: 2026-09-03 [s5346]

## Patents

| Title | Reg. no. | Filed | Inventors |
|---|---|---|---|
| Широкополосная антенна | RU203165U1 | 2020.10.20 | Антонов Юрий Геннадьевич (RU), Сугак Михаил Иванович (RU), Костиков Григорий Александрович (RU), Балландович Святослав Владимирович (RU), Любина Любовь Михайловна (RU) |
| ИЗМЕРИТЕЛЬ СПЕКТРАЛЬНЫХ ПАРАМЕТРОВ РАДИОСИГНАЛОВ | RU2279098C1 | 2005.01.11 | Кирюхин Александр Максимович (RU), Минин Владимир Иванович (RU) |
| Радиоприемное устройство с управляемым преселектором | RU234467U1 | 2025.01.09 | Казаринов Андрей Сергеевич (RU), Шмырин Михаил Сергеевич (RU), Боровиков Сергей Геннадьевич (RU), Воскресенский Дмитрий Михайлович (RU) |
| Способ регулирования задержки СВЧ-сигнала и реализующая его линия задержки | RU2716283C2 | 2019.07.19 | Галичина Алина Андреевна (RU), Лукиянов Александр Сергеевич (RU), Подстригаев Алексей Сергеевич (RU) |
| Беспилотный летательный аппарат-перехватчик | RU2741142C2 | 2020.08.17 | Щеголев Игорь Николаевич (RU), Морозова Елена Владимировна (RU), Борисов Евгений Геннадьевич (RU), Сидоров Николай Михайлович (RU), Кострома Екатерина Ильинична (RU) |
| Отказоустойчивая система электропитания с возможностью гибкой настройки параметров | RU2746221C2 | 2020.08.19 | Федоров Андрей Викторович (RU), Орел Евгений Александрович (RU) |
| Многоканальный пеленгатор радиосигналов ВЧ диапазона | RU2752249C2 | 2020.12.08 | Петряевский Михаил Михайлович (RU), Бубневич Ирина Владимировна (RU), Румянцев Александр Иванович (RU), Понкратьев Алексей Иванович (RU) |
| Способ определения частот множества сигналов в приемнике с субдискретизацией | RU2761983C2 | 2021.04.16 | Шабанов Марат Фарадович (RU), Смоляков Андрей Владимирович (RU), Шпаков Илья Игоревич (RU), Подстригаев Алексей Сергеевич (RU) |
| Способ определения частоты в приемнике с субдискретизацией | RU2763583C2 | 2021.04.14 | Галичина Алина Андреевна (RU), Подстригаев Алексей Сергеевич (RU), Смоляков Андрей Владимирович (RU), Тюрнин Алексей Михайлович (RU), Алёшина Екатерина Андреевна (RU), Шабанов Марат Фарадович (RU), Чукалин Сергей Львович (RU), Шпаков Илья Игоревич (RU), Рябуха Юрий Викторович (RU) |
| Устройство аэродинамического подъема полезной нагрузки | RU2765196C2 | 2021.04.16 | Кострома Екатерина Ильинична (RU), Борисов Евгений Геннадьевич (RU), Морозова Елена Владимировна (RU), Полковников Сергей Петрович (RU), Сидоров Николай Михайлович (RU) |
| Способ пеленгования и реализующее его устройство | RU2765484C2 | 2021.04.13 | Подстригаев Алексей Сергеевич (RU) |
| Способ сопровождения траектории цели в активно-пассивной радиолокационной системе | RU2769566C2 | 2021.04.15 | Сидоров Николай Михайлович (RU), Николаев Олег Алексеевич (RU), Скорых Сергей Валерьевич (RU), Громов Александр Владимирович (RU), Чукалин Сергей Львович (RU), Петкау Олег Гергардович (RU), Белов Евгений Сергеевич (RU), Борисов Евгений Геннадьевич (RU), Полковников Сергей Петрович (RU) |
| Способ поисковых и спасательных операций с помощью беспилотного воздушного судна | RU2818393C1 | 2023.10.23 | Казаринов Андрей Сергеевич (RU), Стенюков Николай Сергеевич (RU), Григорьев Дмитрий Васильевич (RU), Шмырин Михаил Сергеевич (RU) |
| Способ пространственной локализации радиомолчащих объектов в полуактивной радиолокационной системе | RU2820521C1 | 2023.10.23 | Козлов Александр Сергеевич (RU), Григорьев Дмитрий Васильевич (RU), Шмырин Михаил Сергеевич (RU), Бархатов Алексей Владимирович (RU) |
| Способ радиопротиводействия беспилотному воздушному судну | RU2839399C1 | 2024.11.18 | Григорьев Дмитрий Васильевич (RU), Стенюков Николай Сергеевич (RU), Шмырин Михаил Сергеевич (RU) |
| Способ обнаружения сигналов и реализующее его устройство | RU2845089C1 | 2024.09.18 | Калинин Дмитрий Андреевич (RU), Подстригаев Алексей Сергеевич (RU) |
| Способ противодействия беспилотным летательным аппаратам | RU2858409C1 | 2025.05.29 | Гоцко Иван Иванович (RU), Пименов Глеб Андреевич (RU), Сидоров Николай Михайлович (RU) |
| Способ пеленгации радиосигналов | RU2859188C1 | 2025.09.30 | Казаринов Андрей Сергеевич (RU), Григорьев Дмитрий Васильевич (RU), Шмырин Михаил Сергеевич (RU), Стенюков Николай Сергеевич (RU) |
| Беспилотный летательный аппарат-перехватчик | RU2860540C1 | 2025.12.04 | Анкудинова Вероника Сергеевна (RU), Петкау Олег Гергардович (RU), Гоцко Иван Иванович (RU), Кондратьев Алексей Дмитриевич (RU), Борисов Евгений Геннадьевич (RU) |
| Способ и устройство пеленгования источников радиоизлучений беспилотными летательными аппаратами, совершающими согласованный полет по окружности | RU2861850C1 | 2025.10.02 | Борисов Евгений Геннадьевич (RU), Гоцко Иван Иванович (RU), Белов Евгений Сергеевич (RU), Петкау Олег Гергардович (RU) |

## Foreign components

- Patent's own description lists this as one of several 'currently available devices' ('доступных на данный момент устройств') the proposed device can be built from -- an explicit reference implementation, not a prior-art citation. [s1051]
- Same patent, same 'currently available devices' list. [s1051]
- Same patent, same 'currently available devices' list. [s1051]
- Same patent, same 'currently available devices' list. [s1051]
- Same patent, same 'currently available devices' list. [s1051]
- Description names this specific part as having the needed dynamic range for the patented sub-sampling receiver method. [s1026]

## Sanctions & screening

**Ukraine (war-sanctions.gur.gov.ua, military-industry listing), Australia (Autonomous Sanctions, Russia), Switzerland (SECO, Ukraine-related measures), US (OFAC, Russia Harmful Foreign Activities Sanctions), GB-RUS, US-BIS-EL, EU (Ukraine-related restrictive measures), NZ-RSA2022, Ukraine (Presidential sanctions decree/list)** [s0797]

- Listed on Ukraine's GUR war-sanctions UAV-industry registry (screened 2026-08-24).
- 2 OpenSanctions match(es) (screened 2026-08-24).
- 5 OCCRP Aleph match(es) (screened 2026-08-26).

## Principals & persons of interest

### Alyoshina Ekaterina Andreevna — Алёшина Екатерина Андреевна

- co-inventor (patent RU2763583C2)

### Ankudinova Veronika Sergeevna — Анкудинова Вероника Сергеевна

- co-inventor (patent RU2860540C1)

### Antonov Yuriy Gennadevich — Антонов Юрий Геннадьевич

- **ИНН:** 781401290281
- co-inventor (patent RU203165U1)

### Ballandovich Svyatoslav Vladimirovich — Балландович Святослав Владимирович

- co-inventor (patent RU203165U1)

### Barkhatov Aleksey Vladimirovich — Бархатов Алексей Владимирович

- **ИНН:** 662913536174
- co-inventor (patent RU2820521C1)

### Belov Evgeniy Sergeevich — Белов Евгений Сергеевич

- co-inventor (patent RU2769566C2)
- co-inventor (patent RU2861850C1)

### Borisov Evgeniy Gennadevich — Борисов Евгений Геннадьевич

- co-inventor (patent RU2741142C2)
- co-inventor (patent RU2765196C2)
- co-inventor (patent RU2769566C2)
- co-inventor (patent RU2860540C1)
- co-inventor (patent RU2861850C1)

### Borovikov Sergey Gennadevich — Боровиков Сергей Геннадьевич

- **ИНН:** 661200622870
- co-inventor (patent RU234467U1)

### Bubnevich Irina Vladimirovna — Бубневич Ирина Владимировна

- co-inventor (patent RU2752249C2)

### Voskresenskiy Dmitriy Mikhaylovich — Воскресенский Дмитрий Михайлович

- co-inventor (patent RU234467U1)

### Galichina Alina Andreevna — Галичина Алина Андреевна

- co-inventor (patent RU2716283C2)
- co-inventor (patent RU2763583C2)

### Gotsko Ivan Ivanovich — Гоцко Иван Иванович

- co-inventor (patent RU2858409C1)
- co-inventor (patent RU2860540C1)
- co-inventor (patent RU2861850C1)

### Grigorev Dmitriy Vasilevich — Григорьев Дмитрий Васильевич

- **ИНН:** 143505949570
- co-inventor (patent RU2818393C1)
- co-inventor (patent RU2820521C1)
- co-inventor (patent RU2839399C1)
- co-inventor (patent RU2859188C1)

### Gromov Aleksandr Vladimirovich — Громов Александр Владимирович

- co-inventor (patent RU2769566C2)

### Kazarinov Andrey Sergeevich — Казаринов Андрей Сергеевич

- co-inventor (patent RU234467U1)
- co-inventor (patent RU2818393C1)
- co-inventor (patent RU2859188C1)

### Kalinin Dmitriy Andreevich — Калинин Дмитрий Андреевич

- co-inventor (patent RU2845089C1)

### Kiryukhin Aleksandr Maksimovich — Кирюхин Александр Максимович

- **ИНН:** 301807242706
- co-inventor (patent RU2279098C1)

### Kozlov Aleksandr Sergeevich — Козлов Александр Сергеевич

- co-inventor (patent RU2820521C1)

### Kondratev Aleksey Dmitrievich — Кондратьев Алексей Дмитриевич

- **ИНН:** 772024389337
- co-inventor (patent RU2860540C1)

### Kostikov Grigoriy Aleksandrovich — Костиков Григорий Александрович

- co-inventor (patent RU203165U1)

### Kostroma Ekaterina Ilinichna — Кострома Екатерина Ильинична

- co-inventor (patent RU2741142C2)
- co-inventor (patent RU2765196C2)

### Lukiyanov Aleksandr Sergeevich — Лукиянов Александр Сергеевич

- co-inventor (patent RU2716283C2)

### Lyubina Lyubov Mikhaylovna — Любина Любовь Михайловна

- co-inventor (patent RU203165U1)

### Minin Vladimir Ivanovich — Минин Владимир Иванович

- **ИНН:** 780622665530
- co-inventor (patent RU2279098C1)

### Morozova Elena Vladimirovna — Морозова Елена Владимировна

- co-inventor (patent RU2741142C2)
- co-inventor (patent RU2765196C2)

### Nikolaev Oleg Alekseevich — Николаев Олег Алексеевич

- co-inventor (patent RU2769566C2)

### Orel Evgeniy Aleksandrovich — Орел Евгений Александрович

- **ИНН:** 420532903800
- co-inventor (patent RU2746221C2)

### Petkau Oleg Gergardovich — Петкау Олег Гергардович

- **ИНН:** 780512742566
- co-inventor (patent RU2769566C2)
- co-inventor (patent RU2860540C1)
- co-inventor (patent RU2861850C1)

### Petryaevskiy Mikhail Mikhaylovich — Петряевский Михаил Михайлович

- co-inventor (patent RU2752249C2)

### Pimenov Gleb Andreevich — Пименов Глеб Андреевич

- co-inventor (patent RU2858409C1)

### Podstrigaev Aleksey Sergeevich — Подстригаев Алексей Сергеевич

- co-inventor (patent RU2716283C2)
- co-inventor (patent RU2761983C2)
- co-inventor (patent RU2763583C2)
- co-inventor (patent RU2765484C2)
- co-inventor (patent RU2845089C1)

### Polkovnikov Sergey Petrovich — Полковников Сергей Петрович

- **ИНН:** 720303327007
- co-inventor (patent RU2765196C2)
- co-inventor (patent RU2769566C2)

### Ponkratev Aleksey Ivanovich — Понкратьев Алексей Иванович

- co-inventor (patent RU2752249C2)

### Rumyantsev Aleksandr Ivanovich — Румянцев Александр Иванович

- co-inventor (patent RU2752249C2)

### Ryabukha Yuriy Viktorovich — Рябуха Юрий Викторович

- co-inventor (patent RU2763583C2)

### Sidorov Nikolay Mikhaylovich — Сидоров Николай Михайлович

- co-inventor (patent RU2741142C2)
- co-inventor (patent RU2765196C2)
- co-inventor (patent RU2769566C2)
- co-inventor (patent RU2858409C1)

### Skorykh Sergey Valerevich — Скорых Сергей Валерьевич

- **ИНН:** 780212544531
- co-inventor (patent RU2769566C2)

### Smolyakov Andrey Vladimirovich — Смоляков Андрей Владимирович

- co-inventor (patent RU2761983C2)
- co-inventor (patent RU2763583C2)

### Stenyukov Nikolay Sergeevich — Стенюков Николай Сергеевич

- co-inventor (patent RU2818393C1)
- co-inventor (patent RU2839399C1)
- co-inventor (patent RU2859188C1)

### Sugak Mikhail Ivanovich — Сугак Михаил Иванович

- co-inventor (patent RU203165U1)

### Tyurnin Aleksey Mikhaylovich — Тюрнин Алексей Михайлович

- co-inventor (patent RU2763583C2)

### Fedorov Andrey Viktorovich — Федоров Андрей Викторович

- co-inventor (patent RU2746221C2)

### Chukalin Sergey Lvovich — Чукалин Сергей Львович

- co-inventor (patent RU2763583C2)
- co-inventor (patent RU2769566C2)

### Shabanov Marat Faradovich — Шабанов Марат Фарадович

- co-inventor (patent RU2761983C2)
- co-inventor (patent RU2763583C2)

### Shmyrin Mikhail Sergeevich — Шмырин Михаил Сергеевич

- co-inventor (patent RU234467U1)
- co-inventor (patent RU2818393C1)
- co-inventor (patent RU2820521C1)
- co-inventor (patent RU2839399C1)
- co-inventor (patent RU2859188C1)

### Shpakov Ilya Igorevich — Шпаков Илья Игоревич

- co-inventor (patent RU2761983C2)
- co-inventor (patent RU2763583C2)

### Shchegolev Igor Nikolaevich — Щеголев Игорь Николаевич

- co-inventor (patent RU2741142C2)

## Sources cited in this profile

| ID | Type | Locator | Captured | As of |
|---|---|---|---|---|
| s0797 | OpenSanctions screening record | OpenSanctions screening record (OPENSANCTIONS_7813491943_20260824_ao-nii-vektor.json) | 2026-08-24 | — |
| s1026 | Rospatent patent record | Rospatent patent record (PATENT_RU2763583C2_2026-08-24_ao-nii-vektor.json) | — | — |
| s1051 | Rospatent patent record | Rospatent patent record (PATENT_RU2861850C1_2026-08-24_ao-nii-vektor.json) | — | — |
| s3144 | Zakupki | Zakupki (ZAKUPKI_contract_0173100004511002669_20260829.html) | 2026-08-29 | — |
| s3146 | Zakupki | Zakupki (ZAKUPKI_contract_0173100004511002671_20260829.html) | 2026-08-29 | — |
| s3214 | Zakupki | Zakupki (ZAKUPKI_contract_1770425226115000509_20260829.html) | 2026-08-29 | — |
| s3217 | Zakupki | Zakupki (ZAKUPKI_contract_1770425226117000583_20260829.html) | 2026-08-29 | — |
| s3218 | Zakupki | Zakupki (ZAKUPKI_contract_1772054420822000003_20260829.html) | 2026-08-29 | — |
| s5346 | Gisp | Gisp (GISP_20260903_atlas-promyshlennosti-full-dump-40281-companies.json) | 2026-09-03 | 2026-09-03 |

---
_Generated from this investigation's registry (`data/registry/`) by `scripts/build_company_profile.py`. Not a substitute for reading the underlying primary sources listed above._