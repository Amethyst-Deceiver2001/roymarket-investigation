# OKVED/branding mismatches

Running list of entities in this network whose registered OKVED (economic-
activity code) doesn't match their actual product/branding. `docs/index.html`
already flags this as a recurring pattern across the network; this file
makes the pattern itself queryable instead of leaving it scattered across
prose paragraphs. Not published — internal tracking only.

Add a row whenever a new mismatch surfaces during entity resolution. Each
row should be traceable back to a specific claim in `docs/index.html` (or
flag here first if it hasn't been folded into the brief yet).

| Entity | ИНН | Registered OKVED | Actual branding/product | Source |
|---|---|---|---|---|
| ООО «Архангел» | 9714079108 | 85.30 «Обучение профессиональное» (professional training) | Interceptor drones, ЦБСТ-accelerator finalist | docs/index.html, EU-sanctions/АО «Архангел» section |
| ООО «СКБ Пиранья» | 7300024069 | Software development | «Пиранья 15»/«20» cargo-capable strike drones | docs/index.html, 20th-package sanctions section |
| ООО «Группа компаний «Логос»» | 3435149330 | «Торговля оптовая химическими продуктами» (wholesale chemical products) | EW/RF jammers, drone detectors, «Дрон-Таран» interceptor | docs/index.html, ГК «Логос» section |
| ООО «Винград» | 9701066447 | «Выращивание винограда» (grape cultivation) | Central-Moscow commercial building, ФКК-owned holding entity | docs/index.html, ФКК/Гарант Клуб section |
| ООО «Гарант Клуб» | 7729610279 | «Деятельность гостиниц» (hotel operations, until 08.12.2025) | Property/financial vehicle under ФКК, no hotel activity described | docs/index.html, ФКК/Гарант Клуб section |
| «Кольская верфь» | 5190102381 | Recreational/sport shipbuilding | Hydrofoil unmanned surface vessel (БЭК) project with НПП «ЭЛВО» | docs/index.html, НПП «ЭЛВО»/«Кольская верфь» row |
| ООО «Боевые технологии» | 5262393781 | 46.52 (electronics/telecom wholesale) + ration-pack production + textile wholesale | Automatic detect-and-jam counter-drone device | docs/index.html, «Боевые технологии» row |
| Фонд поддержки национальных морских программ | 7714389530 | 88.10 (social services for elderly/disabled) | Pass-through war-supply funder, structurally identical to ДАР | docs/index.html, fourth-foundation section |

## Weaker/unconfirmed cases — not yet added as rows

- КБ «Горизонт» / УЦ «Искра» — EGRUL names carry OKVEDs (snow removal,
  architecture) that look like an unrelated name-collision rather than a
  branding mismatch on the real entity. Brief explicitly treats these as
  probably-not-the-same-entity, not a mismatch case — don't add without
  further confirmation.
- ООО «КИНГПРО» — unusually broad *secondary* OKVED list (integrated
  circuits, radio/TV transmitting, space-vehicle production, wholesale
  software) alongside a correctly-matching primary drone-manufacturing
  code. This is a "kitchen-sink registration" pattern, not a mismatch —
  the primary code is right. Different phenomenon, don't conflate.
