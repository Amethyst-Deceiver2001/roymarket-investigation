# Name check of the ЦБСТ-tied organisations against the official lists, 04.10.2026

Why: the weekly watch matches ИНН and ОГРН only. The Гаскар case (issue #20) showed the gap: a list can name a company under another identifier, or by name alone. Method: all 73 organisations with a ЦБСТ tie (`t-doc`, `t-open`, `press`), their Russian and Latin names and brands, searched as whole-word name matches (and by a consonant skeleton for Latin-only entries) in the US, EU, Swiss and UK files of 02.10.2026 and Canada's SEMA list of 04.10.2026. Every hit was read in the entry itself; most were generic words («научно-производственное предприятие», «Архангел») and are not recorded. The search script was a one-off and is not in the repo.

## What was found
- **ООО «Гаскар» was not the EU-listed «Гаскар Групп»** (now ООО «СТИМС», new record `ooo-stims`); see `notes/packet_verification_20261003.md`.
- **Name-only listings of a registered company:**
  - Уралдронзавод: EU entry EU.12595.62 (16.12.2024) and Swiss SSID 86586 name it with no identifier, at the Sakharov-avenue address that the OFAC entry (which carries the ИНН and ОГРН) also prints.
  - Кронштадт: the EU entry EU.8300.17 («JSC Kronshtadt Tekhnologii», a group) and UK RUS1078 («Kronshtadt») carry no identifier; both print the Descartes Business Center address on the OFAC entry. Which legal entity the EU and UK mean is not established.
  - Canada items 833 (EVR LLC, our ООО «Гаскар» under its old name), 837 (Atlant Aero), 838 (Ushkuynik): all listed 12.06.2026, none with an identifier. Item 838's alias «ООО НПЦ Ушкуйник» matches the separate ООО «Ушкуйник» (no list carries its ИНН).
  - UK RUS0237 (Промсвязьбанк): no identifier in the UK file; the bank is recorded.
- **EU Annex IV is not an asset freeze.** ООО «Стратим» (entry 765, Decision 2025/931), ООО «СПДББК» (entry 699, Decision 2024/3187) and ООО «Радиофид Системы» (entry 832, Regulation 2025/2033) are in Annex IV of Regulation 833/2014 (export restrictions) and not in the EU consolidated asset-freeze file. Their registry entries now say so.
- **The EU consolidated file (FSF) of 22.09.2026 lacks the whole batch of Decision 2026/1364 of 15.06.2026** (44 entries, among them entry 801 ООО «ИОНОС»). The Decision's own text matches our ИОНОС record. The weekly check therefore shows ИОНОС as "no identifier match" and would miss any other company in that batch. Only ИОНОС is in the registry from it; other 2026 batches have not been checked this way.
- **"US-BIS-EL" is the Commerce Department's Entity List, not an OFAC listing** (АО «НИИ СТТ», АО ПК «Азимут»); relabelled.
- **Listed on the official lists but missing from `sanctions[]` (issue #9):** 10 organisation entries recorded (ИОНОС CH; Кайсант US; Элиарс CH, EU, US; Радиофид CH; ЦКБР CH, EU, US; Уралдронзавод US). 8 entries for people remain: Турчак (US), Анцев (CH, EU), Чернышов (EU), Косолапов (CH, EU), Соколова (CH, EU); a person's entry needs date and place of birth checked before it is recorded.

## Not done
- Names of the 73 were searched; the registry's other organisations and its people were not.
- The EU FSF gap: a second EU source (the Official Journal acts) in the weekly watch is a proposal, not built (infrastructure freeze).
- Canada: item numbers are from the file of 04.10.2026; the watch does not read it.

## People entries of #9, recorded 04.10.2026

Five people with a personal ИНН on the official lists, read in the original entries and matched by that ИНН: Турчак (US SDN, s9109), Анцев (EU Reg. 2024/753 entry 1732, s9125; CH, s9106), Чернышов (EU Decision 2026/1845 entry 2099, s9124), Косолапов (EU Reg. 2026/509 entry 2005, s9114; CH), Соколова (EU Reg. 2026/509 entry 1994; CH). Dates of birth match the registry for Турчак, Чернышов and Соколова. Анцев's 29.01.1961 is new (both lists); his birthplace is left null because the act's wording is unclear. Косолапов: no date or place of birth is printed anywhere. The Swiss first-listing date for Анцев and the OFAC designation date for Турчак were not read. Соколова's company is named 'UAMOC' in both entries with no identifier; the link to ООО «ЦУГАМ» rests on the person.
