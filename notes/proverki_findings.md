# proverki.gov.ru screening — findings log

Started 2026-09-07. Tracks every entity screened against proverki.gov.ru's
ФГИС «Единый реестр контрольных (надзорных) мероприятий» via
`scripts/screen_proverki.py` (captcha-gated, run interactively by the user
one entity at a time — see the script's own docstring and CLAUDE.md's
crawling-jobs policy). This note exists so physical-facility and other
notable findings don't stay buried in raw `proverki_inspections[]` JSON —
every entry below has a matching registry write (address_history, cbst_tie,
notes) with a real `source_id`, not just a mention here.

**Convention**: object_address values on inspection records are extremely
noisy (OCR/manual-entry variants of the same address, e.g. 15+ spelling
variants of "Академика Павлова, д.14" for one entity) — read them as raw
signal, cluster by hand, and only wire a genuinely distinct physical site
into `address_history`, not every formatting variant.

## Entities screened so far: 54

0-hit (genuine "no inspection history" result, not a failed lookup):
ano-npts-ushkuynik / npts-ushkuynik, ao-ekolibri, ao-mikts, ao-npp-bat,
ao-npp-real, ao-tekhnodron, gk-logos, ip-kuznetsov-ruslan-nikolaevich,
kolskaya-verf, kulibin-klub, npo-kaysant, npp-elvo-kolskaya-verf,
ooo-4gnss, ooo-akr-begak, ooo-aeroplatformy, ooo-arkhangel,
ooo-arkhangel-grupp, ooo-aviron, ooo-arkodim, ooo-dron-reysing,
ooo-dronomir, ooo-asel-labs, ooo-btr-bespilotnye-tekhnologicheskie-resheniya,
ooo-arkhangel-zaporizhzhie, ooo-arkhangel-shchit, ooo-arkhangel-melitopol-2,
ooo-eyartek, ooo-gk-aeromaks, ooo-gaskar-integratsiya, ooo-gaskar-tekhnologii,
ooo-ekolibri-bt, ooo-eliars, ooo-goudron, ooo-hab-svo, ooo-instekh,
ooo-intek-bespilotnye-sistemy, ooo-kingpro, ooo-kleverkopter,
ooo-konstruktorskoe-byuro-sinergiya, ooo-kravt.

Hits, routine (labor/fire/environmental/consumer-protection history,
confirms continuous legitimate operation, no new facility or notable
regulator beyond what's already on file): ao-ploshchad (1), ao-ross (2),
ip-shandobylo-sergey-sergeevich (1, s6929), ip-tsyganov-vadim-borisovich
(1, s6926, confirms known Солнечногорск/Мышецкое 3MX-network location),
ooo-aero-khit (1, no address on the record), ooo-gagaring (1, s6932, no
new address), ooo-geron (2, s6933, no new address beyond precise Боровичи
address already on file), ooo-intel-dron (1, coarse "обл. Челябинская"
only, no new precision), ooo-kopterlab (1, repeats "г. Москва" only, no
new precision).

Hits with real findings — all wired below: ao-nii-stt (15), ao-kotlin-novator
(25), ao-stratim (8), ao-pmts-avangard (31), ao-nii-vektor (46), npp-radar-mms
(50), npts-elvis (13), ooo-aeromaks (17), ooo-atlant-aero (4), ooo-gaskar (5,
s6934), ooo-dsg (2, s6935).

## Physical facilities discovered — all wired into address_history

### АО «НПП «Радар ММС»» (npp-radar-mms, ИНН 7814027653) — 50 records, s6930
The single biggest facility finding of this sweep. Wired 3 new
`address_history` entries beyond the main Новосельковская 37 site already
on file:
- **Новосельковская ул., д.46, лит.А** — second corpus at the main site;
  one record explicitly names ongoing **"Строительство производственно-
  складского корпуса"** (construction of a new production/warehouse
  building) — active expansion, not a static footprint.
- **Ленинградская область, Кингисеппский район, дер. Хаболово** — TWO
  separate records citing cadastral numbers (КН 47:20:0442001:212 and
  :209). A defense-radar manufacturer holding land under cadastral
  reference far from its SPb HQ is a real open lead (test range? antenna
  field? undisclosed site?) — **not yet identified further, flagged as an
  open question on the entity record**.
- **Курортный район Санкт-Петербурга** (Сестрорецк/Белоостров/Песочный,
  incl. the Сестрорецкое болото nature reserve) — one record covers this
  whole area as an inspected zone; specific activity not identified.
- "Архангельская обл" (bare regional mention, no further detail) — not
  wired, too thin to act on.

### ООО «Аэромакс» (ooo-aeromaks, ИНН 7725347482) — 17 records, s6927
Wired 3 new `address_history` entries — **none of the three match the
entity's own registered legal address** (1-й Волоколамский пр-д, д.10,
стр.1, Москва):
- пер. Милютинский, д.13, стр.1, Москва
- пр-т Андропова, д.18, к.9, Москва
- Малый пр. В.О., д.54, корп.5, лит.Р, Санкт-Петербург
A materially larger and more dispersed operational footprint than the
registered address alone would suggest.

### АО «НИИ «Вектор»» (ao-nii-vektor, ИНН 7813491943) — 46 records, s6922
Wired 2 new `address_history` entries beyond the registered Академика
Павлова 14а address:
- **ул. Маршала Новикова, д.40, лит.А, Приморский район, СПб** — one
  record explicitly: "Строительство производственно-складского корпуса:
  акционерное общество «Научно-исследовательский институт «Вектор»" — a
  second site under active construction.
- **Кантемировская ул., д.10, СПб** — one record explicitly labels this
  the "фактического осуществления деятельности" (actual place of
  operations) address, distinct from the "юридического лица" (legal)
  address at Академика Павлова — proverki's own data distinguishes
  registered vs. operating address here.

### АО «НПЦ «ЭЛВИС»» (npts-elvis, ИНН 7735582816) — 13 records, s6928
Wired 1 new `address_history` entry: **проезд 4922-й, д.4, стр.2,
Зеленоград** — a second Zelenograd facility beyond ул. Конструктора
Лукина 14 already on file.

### АО «Стратим» (ao-stratim, ИНН 7720901379) — 8 records, s6925
Second facility (ул. Электродная, д.2, стр.34, помещ.19/3, Москва) beyond
the registered Новогиреево address — wired to `address_history`, alongside
a labor-inspection warning cluster (6 "Объявление предостережения"
notices, June-July 2026) flagged as a plausible wartime-hiring-ramp signal
against a documented revenue surge (₽964k->₽27.8m->₽606.8m, 2023-2025).
Also closed a standing `cbst_tie` gap for this entity (see commit 914a189).

### АО «Котлин-Новатор» (ao-kotlin-novator, ИНН 7811075899) — 25 records, s6917
Wired 2 new `address_history` entries (entity had no `address` field set
at all before this): ул. Глиняная, д.5/д.11 (multiple corpuses) and наб.
Обводного канала, д.14 — both Санкт-Петербург. Also carries the
Роскосмос/Минпромторг/Роспатент inspections already reported in an
earlier session (commit f1261b8).

### АО «ПМЦ «Авангард»» (ao-pmts-avangard, ИНН 7804302798) — 31 records, s6921
**Not wired** — deliberately, low priority:
- Волгоградская область, Калачевский район — three 2019 Облстройнадзор
  construction-oversight records at a site far from the registered SPb
  address. Entity has no confirmed ЦБСТ/UAV tie (design/project-
  development firm, ОКВЭД 71.12.12) — flagged here, not written to the
  registry, since it's not clearly part of this investigation's network.
- Невский пр./наб. кан. Грибоедова intersection records read as separate
  retail/public-space inspections (Роспотребнадзор-style), not a company
  facility — likely noise.

### ООО «Атлант Аэро» (ooo-atlant-aero, ИНН 6154165878) — 4 records, s6931
Wired 1 new `address_history` entry: **ул. Инструментальная, земельный
участок 2в/7, Таганрог** — entity previously had no street-level address
at all (only city-level). One record is a construction-oversight
inspection (Региональная служба государственного строительного надзора
Ростовской области); other records in the same set cite slightly
different building numbers on the same street (2-7 стр.1, 4-54),
consistent with active construction/expansion at this site.

### ООО «Гаскар» (ooo-gaskar, ИНН 9710112989) — 5 records, s6934
Wired 1 new `address_history` entry: **ул. Пехорская, д.1Д, стр.1, Москва**
— entity previously had only "г. Москва" on file. Same street as ООО «НПО
«Рустехдрон»»'s Пехорская 1/3, стр.4 facility (Руднево technopark, wired
earlier this session) — possible shared-industrial-cluster overlap, not
yet confirmed as the same building. Also wired a discovered prior legal
name: records dated Oct 2024–Nov 2025 all carry faceName ООО «ЭВР» at this
same ИНН/ОГРН; only the most recent (Aug 2026) record shows «Гаскар» —
renamed sometime in that window.

### ООО «ДСГ» (ooo-dsg, ИНН 9724002908) — 2 records, s6935
Wired the entity's only two addresses on file (previously none): Москва,
Хлебозаводской пр-д, д.7, стр.9 and Москва, Вернадского пр-т, д.29.
Control body is Департамент образования и науки города Москвы — not a
standard labor/fire/tax inspector — suggesting an educational-licensing
or training-program angle worth checking.

## Remaining unscreened

~145 manufacturer-tier entities with an ИНН still lack `proverki_checked_at`
as of 2026-09-07. See CLAUDE.md/screen_proverki.py's own docstring for the
interactive-only run pattern (no full-roster batch mode by design).
