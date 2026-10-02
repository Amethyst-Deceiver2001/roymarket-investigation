# What the August 2026 «Infrastructure & Entity Brief» held that the registry does not (2026-10-02)

The brief (Artifact 5450bf7e, 26.08.2026, 18 findings) is retired. Local copy: `data/sources/ARTIFACT_20260826_infrastructure-entity-brief.html`. Audit method: every ИНН/ОГРН (156 and 67 in the text), every «quoted» name (481), every unit number, and 35 headline facts were checked against `data/registry/*.json` and `notes/`, then the unmatched names were run through `scripts/registry_lookup.py` (bare-word misses are not proof, so a lookup came first).

## Result

- **Identifiers and figures:** all but three of the identifiers are already in the registry or notes (the three are a URL id, a pair of map coordinates and one ОГРН, below). The headline figures (ДАР ₽1.213bn to Наша Правда, Левит's НОВАТЭК shares, Наша Правда's ~10,400 units and ₽900.96m, Атлант Аэро's 854 staff and ₽59.08bn, the technopark plan, МПТМ's sealed register, the 20th-package names, the 525 residents) are all present. The Олимпийский фонд ₽42.9bn and the Первобанк ₽1.65bn write-off (from Левит's own FY2025 filing) are both on file in the entity records; nothing is lost with the artifact.
- **Facts only the brief held:** the live site's HTTP headers (a CSP naming `3ds.payment.ru` and `widget.metaship.ru`). The brief's recon was never archived. Re-fetched on 2026-10-02 and archived (`WEBCAPTURE_20261002_roimarket-ru-http-headers.txt`, `WEBCAPTURE_20261002_roimarket-ru-login-page.html`); the МПТМ open question now cites them.
- **Leads, not facts.** Everything below is unresolved in the registry. None is a finding until a primary document is read.

## Names with no registry record (lookup 2026-10-02: no candidate)

| Name | What the brief says | Next check |
|---|---|---|
| ГК «МВС» («Мир высокотехнологичных систем») with «VIRA» | Production partner shown at Дронница 2025: electronics arm, component supplier, IT firm, FPV range | Own site for an ИНН; Дронница channel posts |
| НПО «Милитех» | Maker of equipment itemised in Наша Правда's audited accounts; «not previously identified» | The БФО note text in `data/sources/`; ИНН from the filing or its site |
| АО «ФТК Интеграция» (ФТК) | Listed with the ExpoUAV-linked firms; Чадаев calls ФТК the centre's key integrator partner («Контроль неба» at «Архипелаг», s8935) | ЕГРЮЛ by ИНН once the site prints one |
| ООО «Лассард», ООО «Скайгард», ООО «Хелиор» | Named beside «Элиарс» (on file) among ExpoUAV-listed companies | ExpoUAV programme; own sites |
| ООО «Цифровая платформа», ООО «Лабиринт», ООО «СТ СОФТ», ООО «ЦФА Информационная система», ООО «ЦФА система», СНТ «Усадьба Бергов» | Same ultimate control as ООО «Смарт Текнолоджис» (Ефремов А.В. / Кот О.П., 50/50); none pulled | ЕГРЮЛ by name of the two controllers |
| ООО «Машаудит» | The auditor named in the audits of ДАР, Наша Правда and Орион: a common auditor | Name and ИНН from the audit reports already on file |
| ООО «ПРОМТЕХНОПАРК «МУРОММАШ»» (ОГРН 1043302407169) | Managing company of the Муром technopark; НПЦ БАСиРТК became its resident on 04.06.2026 (UAS_development/620) | ИНН from the park's site; check the ОГРН checksum first |
| АО «Проектмашприбор» | The building at Звёздный бульвар 19/1 where АО «Площадь» is registered | Only an address fact; low value |
| «Опора России» / «Сделано для фронта» | ОНФ campaign with 100+ SMEs | Programme record only if it matters |

## Product names with no owner in the registry

«МГЛА-СТ.10», «МГЛА-СТ.12», «ПАК «МГЛА» СК 2», «СПК 26», «НСУ» (a counter-drone jammer family sold with an «Asel»-branded detector; the brief suspects ООО «АСЕЛ ЛАБС»); «ЛЮСТРА-10», «САЯН-30», «КРАМС-34», «Колун», «Дуплет», «ЛЕГО» (КРАМС lineup); «Д-20»/«Д-20К» (Аэромакс); «Наблюдатель»/«-Н»/«-ДР»/«-Н-ДР» (an optical-reconnaissance family of the АО «НИИ СТТ» record); «Караван» (ООО «НПО НЕБО»); the «Локтар» lineup («Дымка», «Туман», «Шорох-У», «Скрежет», «Фрактал», «Узор»; Локтар is a volunteer collective, no entity). The delivery post 611 (s8925) names «Грань» and «Шорох» as Локтар systems.

## Units and formations

The brief names в/ч 11051 (letter from «Ахмат-Россия»), в/ч 12676 (Херсонская обл.), в/ч 25953, в/ч 33000, «БАРС-Курск», «БАРС-11», батальон «Сомали», «СИГМА Запад», отряд «Яким». `military_units.json` lacks 11051, 12676 and 25953; 25953 appears nowhere else. Add them only with the thank-you letter or post that names them (see the thank-you-letter genre note in memory).

## Not recorded, checked

«Налетай» (налетай.рф, built by АО «ГТЛК», run by ООО «ЦТП», ИНН 9714054618) and the nine manufacturers listing on it are already in the registry (`ooo-tstp-tsifrovaya-transportnaya-platforma`, «Налетай» listing or sales records on six entities). The brief's `info@roy-market.ru` and Telegram `t.me/roy_market` observations (4 subscribers) are stale: the site now prints `info@roimarket.ru`.
