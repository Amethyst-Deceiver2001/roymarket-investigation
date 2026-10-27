# The 13 "registry says listed, no identifier match" cells, read on the 25.10.2026 lists

Read in the downloaded list files themselves (`SANCTIONS_EU/US/UK/CH_20261025.xml`, `SANCTIONS_CSL_20261025.csv`), not in OpenSanctions. Lists: EU generated 2026-10-23, US 10/21/2026, UK 16/10/2026, CH 2026-10-20. No registry change follows from any of them.

Three causes: seven cells are regimes the watcher does not scan (the watcher compares only the EU consolidated financial sanctions (FSF) list, the OFAC SDN list, the UK list and the Swiss list, while the registry also records EU Regulation 833/2014 Annex IV and the US Commerce Entity List); one is the EU FSF file lagging a June 2026 decision (ИОНОС); five are name-and-address entries that print no identifier (Kronshtadt EU and UK, Bank PSB UK, Uraldronzavod EU and CH).

| Record | Cell | What the 25.10 list shows | Reading |
|---|---|---|---|
| ООО «ИОНОС» (alyaska) | EU | No EU FSF entry (no ИНН, ОГРН, «IONOS», «ИОНОС»). Swiss entry SSID 107260 prints ОГРН 1146196001621, ИНН 6168719068, listed 10.8.2026. | EU listing is Council Decision 2026/1364 of 15.6.2026, entry 801; the FSF file still does not carry that Decision's entries (registry note of 04.10 says the same). Swiss entry read in full. |
| АО «Кронштадт» (ao-kronshtadt) | EU | EU.8300.17, «JSC Kronshtadt Tekhnologii Group of Companies», designated 3.6.2022, no identifier; Moscow address Andropov Ave. 18 bldg. 9 (Descartes Business Center) and St Petersburg Maly pr. V.O. 54/4. | Name and address only, as the registry already records. The US entry (uid 35854) prints the same address and the record's ИНН and ОГРН. |
| АО «Кронштадт» | UK | RUS1078 «Kronshtadt», designated 24.3.2022, no identifier; Andropov Ave. 18k9, Moscow. | Name and address only, as recorded. |
| АО «НИИ СТТ» (ao-nii-stt) | US | No SDN entry for it. The CSL carries it on the **Entity List** (BIS), «Joint Stock Company Scientific Research Institute of Modern Telecommunication Technologies», 23.2.2024, 10 Novo-Leningradskaya St, Smolensk. | The registry regime is the Entity List, which is not an OFAC listing. EU.13366.27 (ИНН and ОГРН printed) is already recorded. |
| АО ПК «Азимут» (ao-pk-azimut) | EU | No EU FSF entry. | Registry regime is Annex IV (trade restriction), not on the FSF file. |
| АО ПК «Азимут» | US | No SDN entry; the SDN «Azimut Photonics» (ИНН 7706724914) and «AZIMUT LLC» (Internet Research Agency) are other companies. CSL: **Entity List** «Rostekh – Azimuth», 3.3.2022, Narishkinskaya Alleya, Moscow. | Entity List, not OFAC. Do not read the SDN hits as this company. |
| ГК «Ростех» (gk-rostekh) | EU | No FSF entry for the corporation itself (only subsidiaries naming it as parent, and S. V. and S. S. Chemezov). | Registry regime is Annex IV. US SDN uid 17260 and UK RUS0238 are recorded already. |
| ООО «Радиофид Системы» (ooo-radiofid-sistemy) | EU | No EU FSF entry. US SDN uid 50359 prints ОГРН 1107847000084 and ИНН 7802491148. | EU regime is Annex IV entry 832 (Regulation 2025/2033), not on the FSF file. |
| ООО «СПДББК» (ooo-spdbbk) | EU | No EU FSF entry. | Registry regime is Annex IV. Swiss entry 86958 is recorded. |
| ООО «Стратим» (ooo-stratim) | EU | The EU FSF entry EU.13073.69 is «JSC Stratim», Moscow, ОГРН 1237700447324 (ao-stratim), not this Nizhny Novgorod company. US SDN «Stratim Limited Liability Company» is the record. | EU regime is Annex IV. Do not read EU.13073.69 as ООО «Стратим». |
| ПАО «Банк ПСБ» (pao-bank-psb) | UK | RUS0237 «Public Joint Stock Company Promsvyazbank», designated 22.2.2022, Building 22, Moscow, no identifier. | Name and address only, as recorded. |
| ООО «Уралдронзавод» (uraldronzavod) | EU | EU.12595.62, designated 16.12.2024 (Regulation 2024/3183), no identifier; Yekaterinburg, Akademika Sakharova 41-118. | Name and address only, as recorded. The address is the one on the OFAC entry that prints this ИНН. |
| ООО «Уралдронзавод» | CH | SSID 86586, listed 20.12.2024, amended 18.2.2025, no identifier; postcode 620105. | Name and address only, as recorded. |

## Found while reading: АО «Стратим», ИНН printed wrongly on the EU entry (resolved 27.10.2026)

EU.13073.69 prints ОГРН 1237700447324 (ao-stratim's) and «National fiscal code» 7726030449; the record's ИНН is 7720901379. Read in the Official Journal text of Implementing Regulation (EU) 2025/933, entry 572: the act itself prints 7726030449. The ЕГРЮЛ open search of 27.10.2026 returns 7726030449 for АО «НРК-Р.О.С.Т.» (a registrar, ОГРН 1027739216757) and 7720901379 for ОГРН 1237700447324. So the ИНН on the EU entry is an error in the act; Annex IV entry 763 prints the correct one. Recorded in `ao-stratim` `sanctions[]`.
