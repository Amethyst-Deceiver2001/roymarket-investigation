# The "Архангел" brand family — entities NOT tied to Гагаринг

Split out of `notes/gagaring_network_map.md` on 2026-09-03 at the user's
direction: that document is Гагаринг's own network only (persons, related
companies) as a draft for a future company-profile/presentation page, so
everything below — real leads, but not established as connected to
Гагаринг — gets parked here instead, for separate research later.

Two "Архангел"-branded organizations DO tie to Гагаринг and stay documented
in `gagaring_network_map.md`, not here: **Архангел Легион** (`ano-arkhangel`,
ИНН 2315233718, Новороссийск — co-runs Гагаринг's 51st Army training
relationship) and **Архангел Спецназа** (@arx_spn — informal joint
drone-retraining project, mask branding on a Гагаринг graduation video).
Full historical/forensic detail on all six entities also lives in the
seeded memory `roymarket_archangel_adjacent_network` — this file is the
git-tracked, repo-local summary for anyone picking the adjacent thread back
up; it deliberately does not repeat the ~9-person non-principal PII roster
from the InformNapalm/OSINT Bees dossier below (same "doxxing-scale
apparatus" discipline this project applies elsewhere — see
`smolin_source_catalogue.md`).

## Family map (rebuilt 2026-09-30; the registry is authoritative, this is the index)

Eleven registry records carry the name. **Three have a ЦБСТ tie**, each on its
own evidence; the shared brand is not evidence of a shared owner.

| Record | ИНН | What it is | ЦБСТ tie | Evidence |
|---|---|---|---|---|
| `ooo-arkhangel` | 9714079108 | Moscow interceptor-drone maker, GD Шатракова | **t-doc** | ЦБСТ post 1976, II accelerator finalist [s8652]. Not the EU-listed entity |
| `ooo-arkhangel-tsentr` | 5032379630 | Odintsovo combat school, "ветераны ЧВК Вагнер"; ЕГРЮЛ: pending exclusion | **t-doc** | ЦБСТ post 2095 → links Decision 2026/504, entry 702 [s7588, s0168]. **The only EU-listed «Архангел»**; also UA-NSDC |
| `proekt-kb-arkhangel` | — | Филиппов's Telegram network, Туапсе school, interceptor, B2B | **t-open** | ЦБСТ post 1562 names the «учебный центр БПЛА «Архангел» в Туапсе» as a user of resident Квадросим's simulator [s8651]. A user, not a resident |
| `ooo-arkhangel-grupp` | 9702081286 | Project's B2B vehicle; Филиппов founder; GD Крючков | none | — |
| `ooo-arkhangel-shchit` | 5027339008 | Лыткарино; project's PVO-training entity; GD Хабибулин, founder Кулемин | none | — |
| `ooo-hab-svo` | 9722102248 | Not named Архангел; shares director Хабибулин with Щит | none | Director match only |
| `ooo-arkhangel-zaporizhzhie` | 9500026652 | Мелитополь/Запорожье, Kalashnikov link; GD Тимофеев, owner Кусумов | not established | — |
| `ooo-arkhangel-crimea` | 9108131213 | Судак; director/50% Тимофеев (same as Запорожье) | not established | — |
| `ooo-arkhangel-melitopol-2` | 9001027869 | Dormant sibling of Запорожье, owner Кусумов; UA-NSDC | not established | — |
| `ano-arkhangel` | 2315233718 | «Архангел Легион», Новороссийск; Гагаринг-tied | none recorded | Гагаринг path, see `gagaring_network_map.md` |
| `ooo-arkhangel-istra` | 5017140245 | Law/IT namesake, trademark collision | none | Resolved as unrelated |
| `tg-arkhangel-spetsnaza` | — | @arx_spn, no legal entity | none | Гагаринг path |

**Clusters.** (A) Drone project: `proekt-kb-arkhangel`, `-grupp`, `-shchit`, with
`ooo-hab-svo` by shared director. (B) Запорожье/Крым: three entities tied by
Тимофеев and Кусумов. (C) Two standalone ЦБСТ-named companies: `ooo-arkhangel` and
`ooo-arkhangel-tsentr`, with no documented link to each other or to A/B. (D) Гагаринг
side and namesakes: `ano-arkhangel`, `tg-arkhangel-spetsnaza`, `-istra`.

**Every ЦБСТ post that contains «Архангел»** (5 of 2,308 in `data/roymarket.db`,
channel_id 2159491523): 120 and 123 (2024-09, news digest repeating a third-party
analysis that cites "проект «Архангел» 2023" as a volunteer example; not a tie,
not wired), 1562, 1976, 2095 (wired as above). Query with a capital А or fold case in
Python: SQLite `lower()`/`LIKE` do not fold Cyrillic.

**Not established:** any link between cluster C's two companies and the Проект
(same brand word only); whether the post-2095 «Архангел» is the school, the
drone maker or both (the linked act names only the school); Квадросим's legal
entity.

## Entity: ООО «Архангел» (Moscow), ИНН 9714079108

`ooo-arkhangel` — Moscow interceptor-drone maker, director Шатракова Анастасия
Артёмовна. **ЦБСТ tie `t-doc`**: ЦБСТ's own channel (post 1976, 17.03.2026, s8652)
lists «производитель дронов-перехватчиков «Архангел»» among the 11 finalists of the
II accelerator stream and quotes its general director by name. **It is not the
EU-listed «Архангел»**: the only «Архангел» entry in the EU acts is ООО «Архангел-Центр»
(below). An earlier version of this note called this ООО "an EU-sanctioned ЦБСТ
resident" — that conflated the two and was wrong. No ownership or director tie to
the other Архангел records is on file, so "pure brand-name collision" stays
the working reading of the other clusters, not a finding.

## Entity: ООО «Архангел» (Мелитополь/occupied Zaporizhzhia), ИНН 9500026652

`ooo-arkhangel-zaporizhzhie` — registered 22.08.2024 (Kherson oblast
originally, relocated to Melitopol 04.03.2026). GD Тимофеев Владимир
Сергеевич, sole owner Кусумов Вахид Абдулович. OKVED 30.30.6 (UAS
production) but 100% of disclosed revenue booked as "образовательные
услуги": ₽12.96m (2024) → ₽55.77m (2025).

- **Kalashnikov tie**: CNews (27.08.2025) reports Концерн «Калашников»
  beginning serial production of this project's hybrid VTOL/fixed-wing
  drone at its own plants, with a joint training center planned "в
  Запорожской области."
- **GUR profile** (independently, exact ИНН match): a training network
  across 20 cities in Russia/occupied Ukraine, a Sevastopol branch funded
  by "Putin's fund for the Young UAV Operator course," direct training of
  BARS-32/"Sudoplatov's battalion" from July 2023.
- **Self-description** (rk.2035.university org profile): states a direct
  contractual relationship with the Russian MoD's own combat-training
  directorate ("Главное управление боевой подготовки группировок войск...
  для нужд специальной военной операции") — the strongest primary-source
  admission on this thread.
- OpenSanctions carries a match, but graph-inferred (`ann_graph_topics` +
  `ext_ru_egrul`), not a direct-designation dataset — flagged, not treated
  as a sanction.
- No sanctions currently applied by any of the 9 jurisdictions GUR lists it
  against — a live gap.

Behind @projectArchangel (21.3K subs, full history scanned back to
21.10.2022; launched as a grassroots FPV-assembly volunteer channel,
"развитие проекта началось с Твери"). By Aug 2024, paid recruitment running
jointly with «Союз Ветеранов СВО по Краснодарскому краю» — weeks before
this entity's incorporation.

**Two loose threads, not yet chased:**
- «Ассоциация Народный ВПК» (announced 02.08.2024) names a fellow member,
  "«Компания Гагаринг»" (t.me/my_el_lab) — a primary-source hit worth
  cross-checking against Гагаринг's own network if this thread reopens,
  but not itself evidence of an Архангел↔Гагаринг tie (an association
  membership list, not a direct relationship).
- «Гермес» comms system (msg 4977, 02.08.2024): claims serial production
  across 5 cities, denies supplying a rival network "«проект
  Судоплатов»/НСУ 2.0." Possibly unrelated to the *different*, already-
  verified `npo-kaysant` (ИНН 7733393203) "Гермес" tactical-comms line —
  unresolved, not asserted as a link.

## Entity: ООО «Архангел-Центр» (Odintsovo), ИНН 5032379630

`ooo-arkhangel-tsentr` — registered 17.05.2024. Commercial paid combat-
training school (archangel-center.ru, Wayback capture 18.11.2024, s8650, footer
prints the ИНН/ОГРН), ₽28,000–48,000 courses (UAV operator, sniper, artillery,
tactical medicine), self-branded "под руководством ветеранов ЧВК Вагнер." ЕГРЮЛ
now shows a pending exclusion as a недействующее юридическое лицо. **Listed by the
EU** (entry 702; Council Decision (CFSP) 2026/504 and Implementing Regulation
2026/509, both 23.04.2026) and by UA-NSDC; FR/CH/BE/MC listings rest on an
OpenSanctions match (Open grade). **ЦБСТ tie `t-doc`**: post 2095 (24.04.2026,
s7588) calls «Архангел» a ЦБСТ resident in the EU's 20th package and links
Decision 2026/504 — whose only «Архангел» entry is this company. The post itself
prints the bare name; the identification rests on the act it links. No
drone-manufacturing OKVED, no documented tie to any other Архангел entity or
to Гагаринг.

## «Проект Архангел» / Филиппов Михаил Геннадьевич

Predates all the legal entities above. An 02.08.2023 InformNapalm/OSINT
Bees dossier named its coordinator (TG @arhangel76), Филиппов Михаил
Геннадиевич — now a `people.json` record (properly sourced to that
dossier), the only individual from that dossier promoted per the doxxing-
scale discipline noted above.

Turns out to be an actively operating **multi-city training network**, not
just Телеграм presence: a Туапсе node (mountain/river-side camp, Krasnodar
krai foothills, recurring free 3-week residential courses, contact callsign
"Покров"), a node "в Запорожье," and the project's own description of
itself as "не просто школа... это целая сеть центров подготовки,
разбросанная по многим регионам России." That decentralized structure
echoes GUR's independent "20 cities" description of the *unrelated* entity
above (ИНН 9500026652) — an unconfirmed structural-similarity lead worth
checking, not an established connection.

Филиппов separately co-presented at a Rostov industry round table
(26.05.2026) alongside an active-duty EW officer and «ГК Логос» — a
materially stronger signal than a brand mention, still not a confirmed
ЦБСТ or Гагаринг tie. «ГК Логос»'s own presentation deck also lists
«проект Архангел» as a partner (third independent surfacing of the name in
this investigation's orbit).

## «Архангел Спецназа» — resolved as NOT part of this parked group

@arx_spn (1.02M subs) is the org behind the branded masks seen on a
Гагаринг training-center graduation video, with a confirmed joint
drone-retraining project. No legal entity has ever been identified for it
(generic checko.ru name search too noisy; channel's own about page has no
external link) — but because the Гагаринг tie itself IS confirmed, this
entity's summary lives in `gagaring_network_map.md`, not here.

## Disambiguation discipline

Eleven "Архангел"-branded records are on file (see the family map at the top);
the count of six here predates them. All cross-checks were done by ИНН/ОГРН, never by name — see
`roymarket_fuzzy_dedup` memory. Before treating any new "Архангел" mention
as connected to Гагаринг (or to any other entity in this family), confirm
via identifier first.

## Entities added since this doc was last written (2026-09-05 to -08)

Five more legal entities surfaced after the "six distinct organizations"
count above was fixed — this doc's own count is now stale; the registry
(`entities.json`) is authoritative, not this list. Kept brief here since
the full forensic detail (dozens of open_questions per entity) lives on
each entity's own record, not duplicated into prose:

- **`ooo-arkhangel-shchit`** (ИНН 5027339008, Лыткарино) — CONFIRMS a
  press photo-credit lead: proekt_arhangel's own channel (msg 623,
  2025-10-11) states Проект «Архангел» created this entity mid-2025 for
  civilian PVO/security-staff training. 100% owner Кулемин Игорь
  Александрович, director Хабибулин Владимир Игоревич — both thin
  records (ИНН only, no DOB/address). Registered address is a private
  flat; no БФО filed yet (first FY 2025).
- **`ooo-arkhangel-grupp`** (ИНН 9702081286, Moscow, registered
  12.03.2026) — named as @projectArchangel's own B2B contracting vehicle
  for the interceptor-drone facility-defense business. Director Крючков
  Дмитрий Александрович, no cross-reference to anyone else on file.
  Full screening battery (OpenSanctions/Aleph/GUR/rk2035/ФНС РОМ) clean.
- **`ooo-arkhangel-istra`** (ИНН 5017140245, Павловская Слобода) —
  RESOLVED to a namesake, not part of the network: sole owner/director
  Аристархов Владимир Вячеславович runs a Moscow law/IT firm (ОКВЭД
  69.10) with no aerospace/UAV/training codes and no personal tie to
  anyone else in this family. A trademark collision (Rospatent reg.
  1183435), not a corporate one. Tiered `adjacent` deliberately, so this
  doesn't get re-flagged as a fresh lead.
- **`ooo-arkhangel-melitopol-2`** (ИНН 9001027869, same Мелитополь
  address as `ooo-arkhangel-zaporizhzhie` but a distinct, earlier
  registration) — sole owner/director Кусумов Вахид Абдулович, also
  100% founder of the sibling entity. UA-NSDC sanctioned (confirmed
  exact-identifier OpenSanctions match). БФО filings (FY2024-25, read
  2026-09-08) show zero revenue both years — a dormant vehicle, distinct
  from the sibling that books the real ₽55.77m education revenue.
- **`ooo-arkhangel-crimea`** (ИНН 9108131213, Судак) — director/50%
  owner Тимофеев Владимир Сергеевич, the SAME person who directs
  `ooo-arkhangel-zaporizhzhie`, appointed there 3 days before this
  entity's registration. Declared ОКВЭД mixes grain cultivation with a
  full aviation-training-school code block. FY2025 БФО (read 2026-09-08)
  books zero revenue — pre-operational as of its first filing, so the
  agriculture-vs-training question stays open pending a later filing.
  Unique in the family for a non-minimum ₽3.1m charter capital, paid in
  kind (booked as fixed assets, not cash).
- **`proekt-kb-arkhangel`** — Филиппов's own informal project/channel
  operation, no single ИНН of its own (see the entities above, which are
  its formal vehicles). Has by far the largest open_questions[] list of
  any record in this registry — full multi-city 2023 network history,
  Kalashnikov MOU/serial-production escalation, Putin/Мулино exhibition
  claim (unconfirmed by name in independent press), a documented
  ЧВК-Вагнер ideological throughline, and dozens of named but
  unresolved partner/vendor leads (Ворон-оптоволокно, Открытое небо,
  ООО «Воздушный тракт»/«Овод», КБ «Перит», GoDrone, and others) — read
  the entity's own record directly rather than this summary if picking
  this thread back up.

Also closed 2026-09-08: Черезов Андрей Павлович (director of `ovod` and
`ooo-vozdushnyy-traktat`, the Tula «Овод» drone maker who survived an
assassination attempt) had no personal ИНН on file despite an EGRUL
extract for `ovod` already sitting in `data/sources/` since 2026-09-07 —
found there (712802968839), unexploited. «Открытое небо» (the Lytkarino
cert-issuing front company for Проект Архангел's pilot school, per
iStories) was searched by name on egrul.nalog.ru — 20 same-named
candidates nationwide, none clearly identifiable as the Lytkarino one by
region field alone; genuinely unresolved, would need a per-candidate
address check to close.

## Sources

Fully cited in each entity's own `data/registry/entities.json` /
`people.json` record (`ooo-arkhangel`, `ooo-arkhangel-zaporizhzhie`,
`ooo-arkhangel-tsentr`, `filippov-mikhail-gennadevich`,
`timofeev-vladimir-sergeevich`, `kusumov-vakhid-abdulovich`,
`shatrakova-anastasiya-artemovna`) and `open_questions[]` fields. See also
memory `roymarket_archangel_adjacent_network` for the full forensic history
of each surfacing.
