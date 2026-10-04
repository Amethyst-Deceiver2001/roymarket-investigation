# 2026-10-04 pulls: corrections drafted for downstream application

Built from `notes/first_reading/2026-10-04.md` (cloud session's reading)
after spot-checking its figures against the raw filing text myself
(`ООО «Дроннет»` 2024/2025, lines 2110/2400 — exact match: revenue
31,159/2,453, net profit 1,646/9). Nothing below is in the registry yet;
these are ready-to-paste `corrections_entities.json` `set.financials`
blocks for the main session to apply after a final read-through, per the
hard rule (facts from the original document, read in full).

Units are тыс. руб. unless noted; `financials[]` stores whole rubles
(×1,000) to match the existing convention on these records.

## Ready to apply as-is (simple financials additions, no open conflict)

**ООО «Дроннет» (ИНН 3666267556, slug `ooo-dronnet`)** — verified against text myself.
```json
"financials": [
  {"year": "2023", "revenue": 0, "profit": 0, "source_id": "s9136", "note": "Nil filing."},
  {"year": "2024", "revenue": 31159000, "profit": 1646000, "source_id": "s9137"},
  {"year": "2025", "revenue": 2453000, "profit": 9000, "source_id": "s9138", "note": "Revenue down 92% on 2024; a one-year pass-through shape, worth flagging on the status board rather than closing."}
]
```

**ООО «Мобил-Груп» (ИНН 7839011447, slug `ooo-mobil-grup`)**
```json
"financials": [
  {"year": "2021", "revenue": 11255000, "profit": 1246000, "source_id": "s9155"},
  {"year": "2022", "revenue": 111800000, "profit": 36630000, "source_id": "s9156"},
  {"year": "2023", "revenue": 119582000, "profit": 24876000, "source_id": "s9157"},
  {"year": "2024", "revenue": 132042000, "profit": 26700000, "source_id": "s9158"},
  {"year": "2025", "revenue": 63411000, "profit": -7904000, "source_id": "s9159", "note": "Revenue down 52% on 2024, first loss year."}
]
```

**ФГУП «ЗащитаИнфоТранс» Минтранса России (ИНН 7708083600, slug `fgup-zashchitainfotrans`)**
```json
"financials": [
  {"year": "2021", "revenue": 1814938000, "profit": 31328000, "source_id": "s9150"},
  {"year": "2022", "revenue": 2416754000, "profit": 182736000, "source_id": "s9151"},
  {"year": "2023", "revenue": 2149562000, "profit": -287175000, "source_id": "s9152", "note": "Correction filing no. 1."},
  {"year": "2024", "revenue": 2201989000, "profit": -118701000, "source_id": "s9153"},
  {"year": "2025", "revenue": 3558488000, "profit": 8144000, "source_id": "s9154", "note": "Correction filing no. 1."}
]
```

**АНО «НИИ ДПО» (ИНН 5505057400, slug `ano-nii-dpo`)** — non-profit; funds_* lines are not revenue (CLAUDE.md rule). No 2022 filing was pulled.
```json
"financials": [
  {"year": "2021", "revenue": 2093000, "profit": 46000, "source_id": "s9141", "note": "Correction filing no. 1."},
  {"year": "2023", "revenue": 1242000, "profit": 163000, "source_id": "s9142"},
  {"year": "2024", "revenue": 1999000, "profit": 179000, "source_id": "s9143"},
  {"year": "2025", "revenue": 1426000, "profit": 190000, "source_id": "s9144"}
]
```

**АНО «Центр помощи военнослужащим «За Отважных Воинов — Армии Ангелов»» (ИНН 1651092483, slug `ano-tsvp-zov-aa`)** — 3 consecutive nil filings, itself a finding.
```json
"financials": [
  {"year": "2023", "revenue": 0, "profit": 0, "source_id": "s9133", "note": "Nil filing. Balance ~₽10 thousand, all cash (line 1250)."},
  {"year": "2024", "revenue": 0, "profit": 0, "source_id": "s9134", "note": "Nil filing."},
  {"year": "2025", "revenue": 0, "profit": 0, "source_id": "s9135", "note": "Nil filing."}
],
"open_questions": [
  {"source_id": "s9135", "status": "open", "text": "Registered 24.10.2022 as a charity aiding servicemen; three consecutive nil БФО filings (2023-2025) with a ~₽10,000 cash-only balance mean its stated activity's money does not pass through this legal entity -- a different entity, a personal card, or a platform may hold it. Unresolved: where this organisation's actual fundraising is accounted for."}
]
```

## Needs one more read before applying (do not paste as-is)

- **ООО «СТИМС» (ИНН 7734436058)** — existing registry already has financials with `profit: 3000` for 2024 (`s9130`). The filing text itself gives 2024 net profit as **2** (тыс. руб.) in the 2024 filing, but **3** in the 2025 filing's prior-year comparative column. Read: fix the 2024 entry's `profit` to `2000`, keep a `note` on the comparative discrepancy. Do not touch 2025 (confirmed: revenue 349,650,000 / profit 217,975,000 — matches registry).
- **ООО «Стартап-студия университета Лобачевского» (ИНН 5261135844)** — financials (loss -4,907,000 2024 corr.1, -6,781,000 2025) are safe to add, but the ₽101m/₽201m loans with no named lender need the PDF's notes section read before writing anything about the lender into `open_questions` as more than a bare question — the three participants (Фонд инфраструктурных и образовательных программ 45%, ННГУ 28%, «Группа ПРОМАВТО» 27%) are candidates, not confirmed.
- **ООО «Управляющая компания КОМАКС» (ИНН 7704790277)** — financials table above is safe; the ₽7.8bn loan / ₽6.86bn investment lines (1240/1410) and the restated-profit footnotes need the PDF's notes pages, not just the text layer, before any claim about the lender or investment target.
- **ООО «Гагаринг» EGRUL re-pull (s9126, 04.10.2026)** — confirms existing director/shares/capital/address, no change needed there. Proposal only: add `okved_additional` (13 codes; eight added 28.12.2024 incl. 26.51.2/26.51.7/30.30.39 — radar/control/aircraft-adjacent — two added 13.01.2026, rest at registration). Declared codes only, not evidence of actual output.
- **ИП Пинимасов Александр Вячеславович (ИНН 583680188519, s9119)** — registration moved from Пенза to Электросталь/Солнечногорск (20.06.2025); 14 additional ОКВЭД codes (media/PR/advertising/design alongside retail) found, none a tie to a registry entity on their own. An e-mail address is on the extract — do not copy it in without deciding whether this crosses into the PII identifying-field rule (he already has a person record, `ip-pinimasov-aleksandr-vyacheslavovich`).

## Not drafted here (already flagged as open, no new reading needed)

Kiselev Д.К. — 1 unreviewed OpenSanctions-type screening hit, no sanctions entry. Needs the actual hit read against the official list (same discipline as `sanctions_name_check`), not a financials read.
