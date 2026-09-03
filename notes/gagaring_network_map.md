# Гагаринг network map — the "Архангел" collision problem, resolved

Built 2026-09-03 in response to the user's request to apply the same
wide-net rigor used on the Ushkuynik network (via smolin.info's dossiers,
see `notes/smolin_source_catalogue.md`) to Гагаринг: explore all
connections, all linked companies/POI, and identify what other sources/
methods to bring to bear. Unlike the Ushkuynik push, no single dossier
source did the work here — this was built from `egrul.nalog.ru`, GUR,
OpenSanctions, checko.ru, myrotvorets.center, the local Telegram DB, two
founding-устав OCR passes, and one already-archived-but-unmined OSINT Bees
dossier.

## The core finding: "Архангел" is reused by at least 6 unrelated organizations

A recurring failure mode in this investigation (see `roymarket_fuzzy_dedup`,
`roymarket_archangel_adjacent_network`) is generic patriotic brand names
getting reused independently across the Russian military-industrial/
training space. "Архангел" ("Archangel") is the worst case found so far:

| # | Name | Legal entity | Status | Tie to Гагаринг |
|---|------|-------------|--------|------------------|
| 1 | Архангел Легион | `ano-arkhangel`, ИНН 2315233718, Новороссийск | Confirmed, EGRUL-corroborated | **CONFIRMED** — co-runs Гагаринг's 51st Guards Combined Arms Army training-center relationship |
| 2 | Архангел Спецназа | @arx_spn (1.02M subs) — no legal entity found | Unresolved | **CONFIRMED (informal)** — joint drone-retraining project with Гагаринг, mask branding on a Гагаринг graduation video |
| 3 | проект Архангел | Филиппов М.Г. (coordinator) — legal-entity status unclear | Parked/adjacent | Not established |
| 4 | ООО «Архангел» (Moscow) | `ooo-arkhangel`, ИНН 9714079108 | EU-sanctioned ЦБСТ resident | **Confirmed unrelated** |
| 5 | ООО «Архангел» (Мелитополь) | `ooo-arkhangel-zaporizhzhie`, ИНН 9500026652 | Full entity record; GUR: 20-city training network | Not established |
| 6 | ООО «Архангел-Центр» (Одинцово) | `ooo-arkhangel-tsentr`, ИНН 5032379630 | **Multi-jurisdiction sanctioned (EU/UA/FR/CH/BE/MC)** | Not established |

Two of these (#1, #2) are genuinely part of Гагаринг's own network. The
other four are independent organizations that happen to share the brand
name — confirmed via identifier cross-checks (ИНН/ОГРН), not name matching,
per this project's standing "verify by identifier, never by name"
discipline.

## What each entity actually is

**#1 — Архангел Легион (`ano-arkhangel`).** АНО founded 01.02.2024,
Новороссийск, director Архангельский Геннадий Евгеньевич (whose own
surname is plausibly the origin of the brand), co-founder Ташматов Илья
Сергеевич. Co-runs, alongside Гагаринг, a training relationship with the
51st Guards Combined Arms Army — recruitment posts name two individual
contacts (Артём/@Dark_GAA, Александр Галушко/@Alexande_galushko) offering
₽3.4M signing bonuses. A visit to a separate "школа «Архангел»" in Туапсе
(01.03.2026) was initially ambiguous but confirmed this session to be a
distinct site the group *visited*, not their own facility.

**#2 — Архангел Спецназа (@arx_spn).** The org behind the branded face
masks seen on a Гагаринг training-center graduation video — resolved this
investigation thread from a pure visual mystery to a sourced joint-project
announcement (10.08.2026). No legal entity has been identified for it; a
generic checko.ru name search returned only noise (dozens of unrelated
"Архангел" companies) and the channel's own public page carries no
external link.

**#3 — проект Архангел (Филиппов М.Г.).** A drone-training/production
group that predates all the legal entities above — an 02.08.2023 OSINT
Bees (InformNapalm-affiliated) doxxing dossier named its coordinator,
Филиппов Михаил Геннадиевич (b. 17.11.1976, Лыткарино), and ~9 more
channel admins/activists with full PII. Only Филиппов was promoted to
`people.json` (properly sourced this session, after an earlier attempt had
to strip his DOB for lack of a source_id) — the other ~9 were deliberately
left uncatalogued, same "doxxing-scale apparatus" discipline already
established for the Ushkuynik network. He separately co-presented at a
Rostov industry round table alongside an active-duty EW officer and
«ГК Логос» — a materially stronger signal than a brand mention, but still
not a confirmed ЦБСТ tie.

**#4 — ООО «Архангел» (`ooo-arkhangel`, Moscow).** Already a confirmed,
independently-verified EU-sanctioned ЦБСТ resident (20th sanctions
package). Genuinely unrelated to the rest of this family — its own record
already flagged this before this session began.

**#5 — ООО «Архангел» (`ooo-arkhangel-zaporizhzhie`, Мелитополь).**
Registered in Russian-occupied Zaporizhzhia oblast, 22.08.2024. Officially
a UAV-mechanic training operator (Rosobrnadzor licence
№ Л035-00115-95/01431042) — its own БФО filing books 100% of revenue as
"образовательные услуги." GUR's own profile (exact ИНН match) reveals it
is materially larger than the single legal entity suggests: a training
network across **20 cities** in Russia and occupied Ukraine, a Sevastopol
branch funded by "Putin's fund for the Young UAV Operator course," and
direct training of the BARS-32/"Sudoplatov's battalion" unit from July
2023. No sanctions currently applied by any of the 9 jurisdictions GUR
lists it against — a live gap. OpenSanctions carries it with
`sanction.linked`/`sanction.control` topics, but on a graph-inferred basis
(not a direct designation dataset) — flagged, not promoted to `sanctions[]`.

**#6 — ООО «Архангел-Центр» (`ooo-arkhangel-tsentr`, Одинцово).** The
single biggest finding of this whole push. Registered 17.05.2024,
self-branded a commercial combat-training school "под руководством
ветеранов ЧВК Вагнер" (₽28,000–48,000 courses: UAV operator, sniper,
artillery, tactical medicine). An OpenSanctions exact-identifier match
revealed it is **already sanctioned across six jurisdictions** — EU
(Council Regulation/Decision, CELEX 32026R0509/32026D0504), Ukraine NSDC,
France (Trésor gels d'avoirs), Switzerland (SECO), Belgium (FOD) and
Monaco, designated 2026-04-23. The full EU/UA designation narrative
confirms it trains Russian soldiers for combat in Ukraine and offers
discounts to war participants.

## What's still open

- No legal entity identified for «Архангел Спецназа» (#2).
- «проект Архангел»'s (#3) legal-entity status is still unclear — it may
  not be a formally incorporated organization at all, distinct from the
  incorporated entities #1/#4/#5/#6.
- No confirmed institutional tie found between any of #3/#4/#5/#6 and the
  Гагаринг-connected #1/#2, despite the shared brand and overlapping
  activity (UAV/combat training). A city-level coincidence (#5's Sevastopol
  branch vs. Гагаринг's own Sevastopol training-camp use) is flagged as a
  lead, not asserted as a connection.
- #5 and #6 both still rest on thin primary-source coverage (open-API
  summaries, not full signed EGRUL extracts) relative to Гагаринг's own
  55-page audited financials.
- Одесская 48/3 (Гагаринг's own production subdivision address) — which
  specific building in the 23-building industrial complex it occupies
  remains unidentified; a public business-directory check came back
  negative (expected for a defense-adjacent site).

## Sources and methods used this push

New to this project this session: GUR's `/uav/companies` single-lookup
search (already used for other entities, newly applied here), OpenSanctions
batch `/match/default` (targeted at the new roster, 1 request against
quota), checko.ru (tried, too noisy for a generic name), myrotvorets.center
(tried, Cloudflare-blocked to scripts — same as before). Local: the
Telegram DB (`data/roymarket.db`), устав OCR (`tesseract`), and a full
re-read of an already-archived-but-previously-skimmed OSINT Bees capture.

See also: `roymarket_archangel_adjacent_network` (memory, full historical
detail), `smolin_source_catalogue.md` (the model this follows), and each
entity's own `open_questions[]` in `data/registry/entities.json` for the
underlying source citations.
