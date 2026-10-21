# Register closures and two packet outlines (internal, 21.10.2026)

Made from `data/registry/` alone (cloud session, no source files). Every date
below is already in the registry with its `source_id`; nothing here was read
from a document again. This is analysis and a work list, not a finding.

## 1. When shareholder sections closed, set beside listings

ЕГРЮЛ extracts of these entities print «Доступ к сведениям ограничен» for the
participants/founders. The legal basis is not read here and is not assumed to be
anything but the register's own mechanism. **A pattern in timing is a question to
ask, not proof of motive**: the closures are as likely to follow a general change
in practice as a specific event.

| Entity (ИНН) | Closure date in the extract | Official listing dates on file | Gap |
|---|---|---|---|
| ООО «Тримикс» (7802942873) | 01.11.2024 (GRN 2247802369637; all three participants; owners recorded to 31.10.2024) | EU 24.02.2025 | closure 115 days before EU listing |
| ООО НПО «Рустехдрон» (5003155499) | 12.03.2025 and 03.04.2026 (two founder rows) | Ukraine NSDC 02.12.2024; EU 20.05.2025 | first closure 100 days after Ukraine, 69 before EU; second 318 after EU |
| ООО «Уралдронзавод» (6671284030) | 16.06.2026 (GRN 2269600747590); share-transfer agreement noted 28.09.2026 | EU 16.12.2024 | 547 days after EU listing |
| АНО «ЦАСД Демянск» (5300008970) | 04.07.2025 | none | n/a |
| АНО «НПЦ «Ушкуйник»» (5300013923) | 15.09.2025 | none on file | n/a |
| ООО «МПТМ» (9714068459), the РОЙ.МАРКЕТ operator | 15.07.2026 (GRN 2267706073688) | none | n/a |
| ООО «ГК Аэромакс» (7710974353) | 19.08.2026 (three founder rows) | none; the previous split (49.659% / 49.659% / 0.682%) is dated 14.12.2025 | n/a |
| ООО «РТ-Развитие бизнеса» (7704861136) | 12.12.2022 (director, not founders) | OFAC/NZ/Ukraine entries, undated | n/a |

Closed, date unknown: first recorded as restricted at the 07.09.2026 pull (that
date is the **pull**, not the closure): АО «Спецтех Инвестиции» (registered
27.11.2025), АО «Спецтех Первый» (registered 10.04.2026), НПО «Кайсант» (OFAC,
undated), ООО «Ушкуйник-СП», ООО «Радиофид Системы» (Swiss listing 12.12.2025).
The two Спецтех companies are ЦБСТ's own 100%-owned subsidiaries; the registry
holds a readable ЦБСТ 100% entry for each at registration (27.11.2025,
10.04.2026) and a restricted section by 07.09.2026, so the closure fell within
284 and 150 days of registration respectively.

Also closed, but the **director** section, not the participants: АО
«Технодинамика» (EU 16.12.2022, UK 12.09.2025), АО «ХК Гумич» and
ООО «РТ-Развитие бизнеса» (12.12.2022); all three recorded at the 07.09.2026
pull except the last, dated in the extract.

What the table can and cannot say:
- Said: the closure dates are documented; four entities closed or re-closed within
  months of a listing, two (Уралдронзавод, Рустехдрон's second row) long after.
  Only Тримикс closed **before** its listing, and it is the one with the
  best-documented ЦБСТ tie.
- Not said: that any closure was a reaction. Seven of the twelve entities with a
  closed participants' section have no listing at all (МПТМ, both Спецтех,
  Ушкуйник, Аэромакс, Ушкуйник-СП, Демянск). Counting method: a strict match of
  the extract's own wording in `founders_history`, `egrul_flags` and
  `director_history`; a loose match on «ограничен» also catches «общество с
  ограниченной ответственностью» and gave a false hit on Фонд «ДАР».

Work to make it a finding (Mac or network needed):
1. Get the **first** date each of the five "date unknown" sections closed: the
   ЕГРЮЛ history (earlier extracts, or ФНС's records of changes by GRN).
2. Read what the extracts say about the **basis** of the closure on each date,
   then check it against the decree it cites.
3. Count the same event across the entities with an extract that were not
   screened for it. The comparison needs a base rate, otherwise "12 closed"
   means nothing.

## 2. Packet outline A: "core" (not built; needs a go-ahead before the generator is touched)

Purpose: the direct ask. The five revenue packets skip the centre because
non-profits have no revenue.

| Record | ИНН | What is on file | Sanctions status (as registered) |
|---|---|---|---|
| АНО «ЦБСТ» | 9702064851 | founders Наша Правда (27.02.2024) and ПСБ (01.04.2025); GD Яныкина Н.О. since 16.12.2025, Рубинштейн Д.В. July 2024 to late 2025; БФО 2024: ₽269.8m received, ₽98.0m used | Ukraine only (GUR page read 30.09.2026); the OFAC entry names the Tula ООО |
| АО «Спецтех Инвестиции» | 9703232234 | 100% ЦБСТ (27.11.2025); GD Рубинштейн; no accounts | OpenSanctions match, regime null: **lead only** |
| АО «Спецтех Первый» | 9703244871 | 100% ЦБСТ (10.04.2026); GD Рубинштейн; no accounts | OpenSanctions match, regime null: **lead only** |
| ООО «МПТМ» | 9714068459 | РОЙ.МАРКЕТ operator, participants hidden since 15.07.2026; 2025 revenue ₽1.0m | none |
| Фонд «Наша Правда» | 9705196180 | ₽1.23bn received 2024, ₽0.98bn 2025 | Ukraine only |
| ПАО «Банк ПСБ» | 7744000912 | ЦБСТ co-founder since 01.04.2025 | listed (EU, US, UK, CH and others) |

Reading list before any claim: ЦБСТ's БФО 2025 (the notes name the receipts under
«Прочие поступления»), both Спецтех's first accounts, the ЕГРЮЛ history for the
two Спецтех (who the participants were while readable), ПСБ's 2025 decision to
join (ЦБСТ post). Open question from the packet's point of view: the ask is about
**ЦБСТ and its subsidiaries**, not the Tula company, and the registry must keep
saying so (the Tula ООО has `graph_tier: held-off` for this reason).

## 3. Packet outline B: "funders" (not built)

Purpose: the sources of money, one tier up.

| Record | ИНН | Figures on file (БФО) | Ties on file |
|---|---|---|---|
| Фонд «Градислава» | 7704278421 | received ₽11.86bn (2023), used ₽15.07bn (2024), received ₽1.14bn (2025) | co-founder of Наша Правда (per its own site); no ЦБСТ edge |
| Фонд «ДАР» | 7705517400 | received ₽8.30bn (2024), ₽1.83bn (2025) | co-founder of Наша Правда; founder ООО «Левит» (БФО FY2023 notes; Ведомости 18.04.2023) |
| ООО «Левит» | 6330030244 | revenue ₽15.9bn (2025) | owners Михельсон and Симановский (record-grade, oq021) |
| ООО «Инвестментс» | 9707004743 | ~₽133m loans out 2023-25; stake of Наша Правда 100% → 90.91% (oq011) | Наша Правда subsidiary |

What must not be said: that the funders directed the foundation's activity
(oq021), that Левит controls ПСБ (oq022, a widespread error), or that any
political figure owns the funds (oq005: investigative attribution only).

Questions a read of the notes to the accounts could close: oq007 (what the
₽15bn «целевые мероприятия» bought), oq008, oq017, oq018, oq014; src015 (the
Наша Правда charter, which names who may nominate its board).

Status: none of the three funds carries a listing, and the registry says so; a
packet would be a **funding map**, not a sanctions-gap submission, until a
designation criterion is argued for each.
