# Founding-document (Устав) gap list

Generated 2026-09-07, updated same day after a 6-entity ФНС pull batch.
Reviews every live entity in `entities.json` (excludes 3 tombstoned
duplicates and 14 `tier: adjacent` out-of-scope entities) for whether a
founding-document primary source has actually been pulled and archived,
rather than relying on recall.

**"Has a founding doc" means one of:**
- a bespoke `UD_<OGRN>_*.zip` bundle in `data/sources/` (ФНС founding-document
  export — original устав text, amendments, founding-decision protocols), or
- a confirmed adoption of one of the 36 government-issued generic Типовые
  уставы (`data/registry/ustav_templates.json` `known_users[]`) — in this case
  we already know no entity-specific document exists to pull, so it is
  excluded from the gap list below rather than left as an open item.

**Update 2026-09-07 (same day):** the original pass matched a bundle to its
entity only via `MANIFEST.md`'s auto-extracted ОГРН column, which fails
silently when an `Opis.pdf`'s ОГРН is OCR'd as spaced-out digits ("1 1 6 7
..."). Matching now falls back to the ОГРН embedded in the filename itself
(`UD_<OGRN>_<date>_<slug>.zip`, the standing archiving convention) when the
manifest column comes back empty — this recovered 2 bundles that were
already sitting in `data/sources/` since 19.08.2026 but had been miscounted
as gaps (`ooo-npo-nebo`, `ooo-arkhangel`).

**29 entities now have a founding doc** — excluded from the gap list below (3 added 2026-09-08: АО «Проминвест», ООО «Гаскар», ООО «Центр беспилотных систем» (Tula) — not yet read/wired in, just archived):

- АНО «ЦБСТ» | Centre for Unmanned Systems & Technologies (`ano-tsbst-centre-for-unmanned-systems-technologies`) — bespoke UD zip
- АО «Площадь» (`ao-ploshchad`) — bespoke UD zip
- АО «Эколибри» (`ao-ekolibri`) — bespoke UD zip
- АО УК «Азимут» | formerly «Аэронавигационные и информационные системы» (`ao-uk-azimut-formerly-aeronavigatsionnye-i-informatsionnye-s`) — bespoke UD zip
- Акционерное общество «Научно-производственное предприятие» (`ao-npp-real`) — bespoke UD zip
- ООО «4ГНСС» (`ooo-4gnss`) — bespoke UD zip
- ООО «АСЕЛ ЛАБС» (`ooo-asel-labs`) — bespoke UD zip
- ООО «Архангел» (`ooo-arkhangel`) — bespoke UD zip
- ООО «БПР ЯРЛ» (`yarl`) — bespoke UD zip
- ООО «Гагаринг» (`ooo-gagaring`) — bespoke UD zip
- ООО «Гарант Клуб» (`ooo-garant-klub`) — bespoke UD zip
- ООО «Группа компаний «Логос»» (`ooo-gk-logos`) — bespoke UD zip
- ООО «Заволжское» (`ooo-zavolzhskoe`) — template #20
- ООО «КИНГПРО» (`ooo-kingpro`) — bespoke UD zip
- ООО «НПО НЕБО» (`ooo-npo-nebo`) — bespoke UD zip
- ООО «НПЦ БАСИРТК» (`ooo-npts-basirtk`) — bespoke UD zip
- ООО «ПРОММАШ» (`ooo-prommash`) — bespoke UD zip
- ООО «РТД-Защита» (`ooo-rtd-zashchita`) — bespoke UD zip
- ООО «СКБ Пиранья» (`ooo-skb-piranya`) — bespoke UD zip
- ООО «Системный интегратор» (`ooo-sistemnyy-integrator`) — bespoke UD zip
- ООО «ТИ ЭС ДЖИ ГРУПП» (`ooo-ti-es-dzhi-grupp`) — bespoke UD zip
- ООО «ТИТАН - СЕВЕРО-ЗАПАД» (`ooo-titan-severo-zapad`) — template #20
- ООО «Финконсалтингк» (ФКК) (`ooo-finkonsaltingk-fkk`) — bespoke UD zip (re-pulled 2026-09-14, `UD_1117746033052_20260914_ooo-finkonsaltingk-fkk.zip`, s7407 — one new filing since the 16.08.2026 pull: Изменения №7, charter capital raised ₽12m→₽14m, registered 09.09.2026)
- ООО «Центр Динарус» (`ooo-tsentr-dinarus`) — bespoke UD zip
- ООО НПК «Герон» (`ooo-npk-geron`) — bespoke UD zip
- Общество с ограниченной ответственностью «Кронштадт Беспилотные Системы» (`ooo-kronshtadt-bespilotnye-sistemy`) — bespoke UD zip
- АО «Проминвест» (`ao-prominvest`) — bespoke UD zip, `UD_1237700148180_20260908_ao-prominvest.zip`
- ООО «Гаскар» (`ooo-gaskar`) — bespoke UD zip, `UD_1237700273744_20260908_ooo-gaskar.zip`
- ООО «Центр беспилотных систем» (Tula) (`ooo-tsentr-bespilotnykh-sistem-tula`) — bespoke UD zip, `UD_1237100001467_20260908_ooo-tsentr-bespilotnykh-sistem-tula.zip`
- ООО «Архангел Щит» (`ooo-arkhangel-shchit`) — bespoke UD zip, `UD_1255000059533_20260910_ooo-arkhangel-shchit.zip` (added 2026-09-13, PDF, read in full — sole-founder boilerplate, confirms Лыткарино address; founder identity is not named in the charter body, already covered by the separate full ЕГРЮЛ выписка s5517)
- ООО «Архангел Групп» (`ooo-arkhangel-grupp`) — bespoke UD zip, `UD_1267700086081_20260910_ooo-arkhangel-grupp.zip` (added 2026-09-13, scanned TIF, not yet OCR'd/read)
- ООО «Винград» (`ooo-vingrad`) — bespoke UD zip, `UD_1177746217879_20260910_ooo-vingrad.zip` (added 2026-09-13; user's earlier "docs found" annotation was correct, the file just hadn't been located yet — see the retracted flag below). Bundle contains 3 filings: the 2017 original charter (OCR'd, no founder named in the body — standard pattern; declared purpose is виноградарство/винодельческая деятельность and real estate, unrelated to UAV work, consistent with its money-layer tier), a full 2022 charter restatement (OCR'd, revealed a real gap-filling fact: charter capital was ₽200,000 as of 18.05.2022, now in `charter_capital_history`), and the 2024 capital-increase amendment (read directly, corroborates the ₽2,000,000 figure already on file from the EGRUL выписка). Wired via `corrections_entities.json`, source `s7373`.

**2 more entities confirmed as generic-template users, same exclusion rule as the two above** — added to `data/registry/ustav_templates.json` template #20's `known_users[]` 2026-09-13, per the user's own pasted egrul.nalog.ru lookup text (not yet independently archived as a source file):
- ООО «Архангел» / Zaporizhzhia (`ooo-arkhangel-zaporizhzhie`, ОГРН 1249500004181) — template #20 since 21.08.2024
- ООО «Архангел» / Melitopol-2 (`ooo-arkhangel-melitopol-2`, ОГРН 1249000005517) — template #20 since 09.06.2024

**2 more template users found 2026-09-13 by reading the "Номер типового устава" field of an EGRUL extract already sitting in `data/sources/`** — same exclusion rule, added to `ustav_templates.json`:
- ООО «ДРОНОМИР» (`ooo-dronomir`, ОГРН 1264200005530) — template #20 since 05.06.2026
- ООО «Зетакс» (`ooo-zetaks`, ОГРН 1225300003983) — template #32 since 25.10.2022 (first entity on file using this template — template #32's own text hasn't been separately archived, only the adoption fact)

**A distinct annotation pattern surfaced this same pass, worth flagging for future reads of this file:** several entities got a "got docs"/"docs found" note that on inspection meant *an EGRUL выписка exists*, not a `UD_*` founding-document bundle — a different document type per this file's own opening definition. Checked individually against `data/sources/` at the time and left in the gap list (ГОУДРОН, Герон [`ooo-geron`, ИНН 7802893898 — distinct from the already-closed `ooo-npk-geron`], ЗИТ.ЦИ, Инвестментс, Интел Дрон, Информационные системы и технологии, КРАВТ, КРАВТ УДМУРТИЯ). Винград was the one exception where a real `UD_*` bundle did exist and just hadn't been located yet (see the "already have" list above) — so the annotation itself isn't unreliable, but it needs the same file-existence check every time rather than being taken as closing the gap on its own. **Update, same day, later pass:** 7 of those 8 — all but Герон — now DO have real bundles (see the new closure entry directly below), pulled and dropped into `data/sources/` after the check above ran. So the annotations were accurate all along, just ahead of the file landing; Герон remains the one genuinely still open.

**7 more entities closed 2026-09-13 (a later pass, same day) — real `UD_*` bundles now on file and read in full:**
- ООО «ГОУДРОН» (`ooo-goudron`) — `UD_1237700265846_20260913_ooo-goudron.zip`, source `s7377`. Single sole-founder filing (04.04.2023), generic boilerplate purpose, ₽10,000 capital — corroborates what was already on file, no new fact.
- ООО «ЗИТ.ЦИ» (`ooo-zit-tsi-otraslevoy-tsentr-importozameshcheniya`) — `UD_1227700802878_20260913_...zip`, source `s7376`. **Real finding**: the original 2022 charter's own purpose clause explicitly authorizes work involving state-secret information, cryptographic/secure telecom systems, and information-security services — a direct self-declaration, consistent with (not a new tie beyond) its ФГУП «ЗащитаИнфoТранс»/Transport Ministry sole ownership already on file. A 2024 amendment added two more activity codes and governance procedure changes only. Wired into `corrections_entities.json`.
- ООО «Инвестментс» (`ooo-investments`) — `UD_1237700523895_20260913_...zip`, source `s7378`. **Real finding**: the 2026 charter restatement's own preamble states this entity absorbed АО «Борей» (`ao-borey-absorbed-no-longer-exists`) via присоединение, joint meeting 17.11.2025 — resolving that entity's own slug note ("absorbed, no longer exists") which had no mechanism or date on file before. Wired onto both entities.
- ООО «Интел Дрон» (`ooo-intel-dron`) — `UD_1247400026246_20260913_...zip`, source `s7380`. Single filing (approved by general meeting, not sole founder, 10.09.2024), generic boilerplate purpose, ₽10,000 capital — corroborates the existing 3-way founder split (Воронин/Февралев/Гагаринг), no new fact.
- ООО «Информационные системы и технологии» (`ooo-instekh`) — `UD_1207800035079_20260913_...zip`, source `s7375`. OCR'd (scanned). Mild find: the original 2020 charter's declared activity was OKVED 43.21 (electrical installation work), not information systems despite the company name — a name/declared-activity mismatch, not wired as a structured fact (too weak on its own), noted here for awareness. ₽10,000 capital, sole founder — corroborates existing record.
- ООО «КРАВТ Удмуртия» (`ooo-kravt-udmurtiya`) — `UD_1241800012222_20260913_...zip`, source `s7379`. Single filing (04.09.2024), captioned "Общим собранием учредителей" (plural-founder meeting language) against a single Королев Д.М. founder currently on file with no share% — the same pattern that flagged a real open question at СКБ Пиранья; not independently resolved here, worth a light open-question flag if this thread continues. Generic purpose, ₽50,000 capital confirmed.
- ООО «КРАВТ» (`ooo-kravt`) — `UD_1197847166560_20260913_...zip`, source `s7374`. Richest bundle: 4 charter revisions spanning 2021-04-21 to 2026-08-25 (one OCR'd), all sole-founder (Королев Д.М.), all ₽10,000 capital, generic boilerplate purpose throughout — confirms ownership/capital stability across nearly 5 years, no substantive change to wire in.

Verification: `check_registry.py` 0 errors, 41 warnings (baseline unchanged); full housekeeping bundle (`inventory_sources.py` → `scan_sources.py` → `extract_registry.py` → `check_registry.py`) run clean after each batch.

## Attempted at ФНС, deprioritized (15 entities)

Attempted via the ФНС portal 2026-09-07 but not obtainable — ФНС returned a
"документ формируется" (document is being digitized) response rather than
the bundle itself. **Decision 2026-09-07: treat as effectively unavailable
and stop retrying** — after the initial attempt, the user judged these
unlikely to ever actually digitize. Kept here (rather than folded back into
the plain gap list) purely as a record that the attempt was made and
deliberately not pursued further, so a future session doesn't re-attempt
them under the impression they're an untried gap. Revisit only if there's
a specific reason to believe ФНС has since processed one of these ОГРН.

| Entity | ОГРН | ИНН | Note |
|---|---|---|---|
| АНО Военно-технической поддержки защитников Отечества и патриотического воспитания населения «Архангел» (`ano-arkhangel`) | 1242300005640 | 2315233718 | 2026-09-07: "документ формируется" at ФНС. Deprioritized same day, not expected to digitize. |
| АНО ДПО «Образовательный центр Гагаринг» (`ano-dpo-obrazovatelny-tsentr-gagaring`) | 1252300026208 | 2310240630 | 2026-09-07: "документ формируется" at ФНС. Deprioritized same day, not expected to digitize. |
| АО «Технодрон» (`ao-tekhnodron`) | 1247700354175 | 9704241986 | 2026-09-07: "документ формируется" at ФНС. Deprioritized same day, not expected to digitize. |
| АО ПК «Азимут» (`ao-pk-azimut`) | 1057746261605 | 7701583410 | 2026-09-07: "документ формируется" at ФНС. Deprioritized same day, not expected to digitize. |
| АО «НИИ СТТ» (`ao-nii-stt`) | 1026701461160 | 6730046954 | **Found 2026-09-08, previously untracked here**: hit "not digitized" pre-2026-08-20 (undated attempt, recorded only in prose — docs/index.html's АО «НИИ СТТ» section). A primary EGRUL extract (not the founding doc itself) was separately obtained via nalog.gov.ru, user-supplied, 20.08.2026 — that's a different document type and doesn't resolve this gap. |
| ООО «Ушкуйник-СП» (`ooo-ushkuynik-sp`) | 1245300003827 | 5300015906 | **Found 2026-09-08, previously untracked here**: same undated "not digitized" wall, per the same АО «НИИ СТТ» prose ("the same wall as Ушкуйник-СП и Атлант Аэро"). |
| ООО «Атлант Аэро» (`ooo-atlant-aero`) | 1236100025633 | 6154165878 | **Found 2026-09-08, previously untracked here**: same undated "not digitized" wall — the largest single manufacturer in this brief (854 employees, ₽59.08bn income), so worth a retry later even though deprioritized for now; flagging here specifically so it isn't recommended for a fresh pull attempt by mistake, as it nearly was on 2026-09-08. |
| АО «НИИ «Вектор»» (`ao-nii-vektor`) | 1117847020400 | 7813491943 | 2026-09-08: "документ формируется" at ФНС — user attempted, part of that day's 12-entity pull batch. Deprioritized. |
| АО «Спецтех Первый» (`ao-spetstekh-perviy`) | 1267700128376 | 9703244871 | 2026-09-08: "документ формируется" at ФНС. Deprioritized. |
| Фонд «Наша Правда» (`fond-nasha-pravda`) | 1237700218612 | 9705196180 | 2026-09-08: "документ формируется" at ФНС. Deprioritized. |
| ООО «МПТМ» (`ooo-mptm`) | 1257700021468 | 9714068459 | 2026-09-08: "документ формируется" at ФНС. Deprioritized. |
| АО «Стратим» (`ao-stratim`) | 1237700447324 | 7720901379 | 2026-09-08: "документ формируется" at ФНС. Deprioritized. |
| АО «Котлин-Новатор» (`ao-kotlin-novator`) | 1027806064571 | 7811075899 | 2026-09-08: "документ формируется" at ФНС. Deprioritized. |
| ООО «Тримикс» (`ooo-trimiks`) | 1237800084235 | 7802942873 | 2026-09-08: "документ формируется" at ФНС (re-attempted; the entity's EGRUL identity was separately already resolved via a different pull, see docs/index.html's footnote — that's a different document type). Deprioritized. |

**2026-09-14 audit finding:** a check of `data/sources/` for unprocessed founding-doc bundles turned up 17 files still under their original bare-numeric `UD_<n>.zip` names (per the standing "existing files are NOT renamed" convention — MANIFEST.md is the lookup layer, not the filename). All 17 turned out to already be archived and source-registered (`s0189`-`s0203`, `s0542`, `s0550`) — a first pass mistakenly treated them as never-processed and began renaming them, but `sources.json`'s `path` fields point at the original bare names, so this was reverted immediately (no lasting change to `data/sources/`). Of the 17: 9 were confirmed genuine duplicates of already-closed entities' bundles (same ОГРН, same content) and needed nothing further; 3 (**АО «АУРИН»**, **ООО «КоптерЛаб»**, **ООО «Ориент Системс»**) were fully wired already, just not reflected in this file's gap list — corrected below; **АО «Спецтех Инвестиции»**'s bundle actually digitized (16.08.2026, per its own Opis.pdf) despite being logged "документ формируется"/deprioritized on 2026-09-08 — moved out of the deprioritized table above, its 100% ЦБСТ-ownership already on file is now also corroborated directly from the устав's own text (see `corrections_entities.json` why[]); ООО «КРАМС» corroborated (already ruled out as unrelated to the `krams-brand-unresolved` brand); ООО «Решение» (ОГРН 1151001003230, `s0550`) is not in the registry at all and has no apparent tie to this investigation — flagged, not pursued. КоптерЛаб's устав yielded a real new self-declaration: its purpose clause explicitly names "производство летательных аппаратов, в том числе беспилотных комплексов" (UAV-complex production), consistent with its existing drone-kit product line.

**8 more entities closed 2026-09-14 — freshly pulled `UD_*` bundles (ФНС ОГРН-suffixed IDs 2062902-2062913), archived and read in full:**
- ООО «Авиационно-космические разработки «Бегак»» (`ooo-akr-begak`) — `UD_1202600009919_20260914_ooo-akr-begak.zip`, source `s7421`. OCR'd (20-page scanned appendix). **Real finding**: the устав's own purpose clause self-declares UAV/optionally-manned aircraft development, UAV-system services to МВД/ФСБ/МЧС/ФТК/ФПС, and flight-training aimed at candidates for military aviation училища and conscription into the ВС РФ — far richer than the thin web footprint found earlier, and consistent with the founder's own patent for a transforming flying-amphibious vehicle already on file.
- АО «МИКЦ» (`ao-mikts`) — `UD_1227700322410_20260914_ao-mikts.zip`, source `s7424`. ₽1,000,000 charter capital confirmed directly. Generic AO boilerplate, no founder named (standard), no UAV-specific language. Corroborates existing record.
- ООО «Аэроплатформы» (`ooo-aeroplatformy`) — `UD_1215000018650_20260914_ooo-aeroplatformy.zip`, source `s7423`. Generic boilerplate, corroborates existing record.
- ООО «Воздушный трактат» (`ooo-vozdushnyy-traktat`) — `UD_1237100015767_20260914_ooo-vozdushnyy-traktat.zip`, source `s7425`. Generic "any lawful activity" clause despite the aviation-suggestive name — no UAV self-declaration. Corroborates existing record.
- ООО «Гаскар Технологии» (`ooo-gaskar-tekhnologii`) — `UD_1207700344037_20260914_ooo-gaskar-tekhnologii.zip`, source `s7422`. **Real finding**: устав §3.1 restricts the entity's entire activity to Сколково-project research/commercialisation under 244-ФЗ — a formal Сколково resident, not just a claimed affiliate. New `state_programs[]` entry.
- ООО «Конструкторское бюро «Синергия»» (`ooo-konstruktorskoe-byuro-sinergiya`) — `UD_1237800134835_20260914_...zip`, source `s7426`. OCR'd. ₽10,000 capital confirmed. Generic boilerplate despite the "design bureau" name — no UAV-specific language. Corroborates existing record.
- ООО «Стратим» (`ooo-stratim`) — `UD_1245200009075_20260914_ooo-stratim.zip`, source `s7427`. OCR'd (17-page scanned). Generic boilerplate. Confirmed distinct from the already-deprioritized АО «Стратим» (different ИНН, same brand name, no relationship established).
- ООО «Скай авиа групп» (`ooo-skay-avia-grupp`) — `UD_1147847241464_20260914_ooo-skay-avia-grupp.zip`, source `s7420`. Archived (32-page scanned TIFF original) but not deep-read beyond the Opis.pdf inventory — director/founder/capital already confirmed via EGRUL. Flagged as archived-not-fully-read.

## Gap list: live entities with an ОГРН, no founding doc on file

**84 entities** (down from 109 as of the 2026-09-07 count — 25 closed: 14 on 2026-09-13 across three passes [3 bespoke bundles found: Архангел Щит, Архангел Групп, Винград; 4 confirmed generic-template users: both Архангел Zaporizhzhia/Melitopol-2, ДРОНОМИР, Зетакс; 7 more bespoke bundles: ГОУДРОН, ЗИТ.ЦИ, Инвестментс, Интел Дрон, Информационные системы и технологии, КРАВТ, КРАВТ Удмуртия — see the closure log above for what each turned up], 3 more found 2026-09-14 [АУРИН, КоптерЛаб, Ориент Системс], plus 8 more closed 2026-09-14 in a fresh ФНС pull batch — see the closure log directly above). Pull candidates for a manual ФНС founding-document request
(egrul.nalog.ru / nalog.gov.ru portal — no scriptable open-API route exists
for this document type, confirmed 2026-09-07, see `notes/SOURCE_REGISTER.md`).
Sorted alphabetically by name. `tier` shown for prioritization.

| Entity | ОГРН | ИНН | Tier |
|---|---|---|---|
| АНО «Платформа НТИ» (`ano-platforma-nti`) | 1197700000376 | 7703469180 | plumbing | - no docs 
| АНО «ЦСАСД» (`ano-tsasd-demyansk`) | 1235300001947 | 5300008970 | plumbing | no docs
| АНО «Центр развития транспортных технологий» (`ano-tsentr-razvitiya-transportnykh-tekhnologiy`) | 1217700636306 | 9724066980 | plumbing | - no docs
| АО «Борей» | absorbed, no longer exists (`ao-borey-absorbed-no-longer-exists`) | 1247700237663 | 9701280698 | money-layer |
| АО «Главтехконструкция» (`ao-glavtekhkonstruktsiya`) | 1174632000190 | 4611014597 | money-layer | docs found
| АО «Корпорация «Синергия»» (`ao-korporatsiya-sinergiya`) | 1237700250182 | 7743414861 | plumbing | got docs
| АО «НПП «Радар ММС»» (`npp-radar-mms`) | 1027807560186 | 7814027653 | manufacturer | no docs
| АО «НПЦ «Электронные вычислительно-информационные системы»» (ЭЛВИС) (`npts-elvis`) | 1127746073510 | 7735582816 | manufacturer | no docs
| АО «Научно-производственное предприятие Беспилотные авиационные технологии» (`ao-npp-bat`) | 1237700769701 | 9718238013 | manufacturer |
| АО «ПМЦ «Авангард»» (`ao-pmts-avangard`) | 1047855051892 | 7804302798 | manufacturer | no docs
| АО «РОСС» (`ao-ross`) | 1027700135957 | 7704097425 | manufacturer | no docs
| АО «Сейм-Агро» (`ao-seym-agro`) | 1114611000283 | 4611011596 | money-layer | got docs
| АО «Технодинамика» (`ao-tekhnodinamika`) | 1037719005873 | 7719265496 | plumbing | no docs
| АО «УК СМАРТ» (`ao-uk-smart`) | 1237700557050 | 7751264401 | plumbing | got docs
| АО «Фабрика им. Советской Армии» (`ao-fabrika-im-sovetskoy-armii`) | 1027739157401 | 7709278792 | money-layer | got docs
| АО «ХК Гумич» (`ao-khk-gumich`) | 1237700537788 | 9726051114 | money-layer | - no docs
| АО «Центр-Телко» (`ao-tsentr-telko`) | 1027739038590 | 7729150663 | plumbing | got docs
| Ассоциация благотворительной помощи «Взаимопомощь» (`assotsiatsiya-vzaimopomoshch`) | 1164700050734 | 4707039070 | money-layer | no docs
| Ассоциация разработчиков перспективных систем радиоэлектронной разведки, радиоэлектронной борьбы и связи (РЭР, РЭБ и связи) (`ano-arrs-krasnodar`) | 1242300011469 | 2312325336 | plumbing |
| Благотворительный фонд «КЦПН» (`bf-ktspn-barnaul`) | 1152225001114 | 2224171246 | plumbing |
| ГК «Ростех» (`gk-rostekh`) | 1077799030847 | 7704274402 | plumbing |
| ЗАО «Курскпромтеплица» (`zao-kurskpromteplitsa`) | 1117746195214 | 7705944272 | money-layer |
| ИП Кузнецов Руслан Николаевич (`ip-kuznetsov-ruslan-nikolaevich`) | 320631300042842 | 637592279701 | manufacturer |
| ИП Цыганов Вадим Борисович (`ip-tsyganov-vadim-borisovich`) | 318500700040208 | 504405055721 | manufacturer |
| ИП Шандобыло Сергей Сергеевич (`ip-shandobylo-sergey-sergeevich`) | 320784700272511 | 781154619843 | manufacturer |
| НЕКОММЕРЧЕСКОЕ ПАРТНЕРСТВО «ДИСКРЕТНО-ИННОВАЦИОННЫЙ КЛАСТЕР МАЛОЙ АВИАЦИИ» (`np-diskretno-innovatsionny-klaster-maloy-aviatsii`) | 1142651011788 | 2632811832 | plumbing |
| НПП «ЭЛВО» (`npp-elvo-kolskaya-verf`) | 1217800070509 | 7810918592 | manufacturer | типовой 23
| ООО «АС-КАМ» (`ooo-as-kam`) | 1166196114083 | 6165205064 | — |
| ООО «Аркодим» (`ooo-arkodim`) | 1101690020959 | 1659101884 | manufacturer |
| ООО «Аэро-Хит» (`ooo-aero-khit`) | 1232700009398 | 2700012608 | manufacturer | no docs (reconfirmed)
| ООО «Аэромакс» (`ooo-aeromaks`) | 1177746007900 | 7725347482 | manufacturer | no docs (reconfirmed)
| ООО «Аэротехальянс» (`ooo-aerotekhalyans`) | 1237700640660 | 9714020721 | money-layer | got docs
| ООО «Беспилотные технологические решения» (БТР) (`ooo-btr-bespilotnye-tekhnologicheskie-resheniya`) | 1247800059980 | 7813680637 | manufacturer | got docs
| ООО «Визионеро» (`ooo-vizionero`) | 1195958038902 | 5902056314 | manufacturer |
| ООО «Восточные ворота Забайкальск-Маньчжурия» (`ooo-vostochnye-vorota-zabaykalsk-manchzhuriya`) | 5167746405481 | 7703420474 | manufacturer |
| ООО «ГЭС-2» (`ooo-ges-2`) | 1147746575767 | 7706809928 | money-layer |
| ООО «Гаскар Интеграция» (`ooo-gaskar-integratsiya`) | 5147746074196 | 7733894200 | manufacturer |
| ООО «Герон» (`ooo-geron`) | 1217800073545 | 7802893898 | manufacturer | distinct from the already-closed `ooo-npk-geron` (ИНН 7814748285). Only EGRUL/БФО/Aleph/Федресурс files on file as of 2026-09-13, no `UD_*` bundle — the one entity from that day's "got docs" batch that hasn't since turned up a real bundle.
| ООО «Группа компаний «Аэромакс»» (`ooo-gk-aeromaks`) | 1147748024269 | 7710974353 | manufacturer |
| ООО «ДИАМ-АЭРО» (`ooo-diam-aero`) | 1187847091079 | 7811687549 | — |
| ООО «ДРОН-РЕЙСИНГ» (`ooo-dron-reysing`) | 1187746574696 | 7728432295 | manufacturer | got docs but Деятельность прекращена
| ООО «ДСГ» (`ooo-dsg`) | 1207700030493 | 9724002908 | manufacturer | got docs
| ООО «ИНТЭК БЕСПИЛОТНЫЕ СИСТЕМЫ» (`ooo-intek-bespilotnye-sistemy`) | 1247000000488 | 7000013316 | manufacturer | got docs
| ООО «Клеверкоптер» (`ooo-kleverkopter`) | 1185275047176 | 5257183517 | manufacturer | got docs
| ООО «Кольская верфь» (`kolskaya-verf`) | 1245100006799 | 5190102381 | manufacturer | got docs
| ООО «Конструкторское бюро СОВА» (`va-technologies`) | 1252300058515 | 2378001237 | manufacturer | типовой устав № 24
| ООО «Левит» (`ooo-levit`) | 1066330007798 | 6330030244 | money-layer |got docs 
| ООО «Ментастеп» (`ooo-mentastep`) | 1247700255208 | 9715478320 | manufacturer | got docs
| ООО «Метаскан» (`ooo-metaskan`) | 1201600057097 | 1660349248 | manufacturer | got docs
| ООО «НОВА» (`ooo-nova`) | 1086330002549 | 6330037352 | money-layer | got docs
| ООО «НПК «Центр перспективных технологий»» (ЦПТ) (`ooo-npk-tspt-tsentr-perspektivnykh-tekhnologiy`) | 1265300000470 | 5300022741 | manufacturer | got docs
| ООО «НПО Рустехдрон» (`ooo-npo-rustekhdron`) | 1235000022179 | 5003155499 | manufacturer | no docs
| ООО «НПО Эйлер» (Научно-производственное объединение «Эйлер») (`ooo-npo-eyler`) | 1257100008560 | 7100069249 | manufacturer | got docs
| ООО «Научно-производственное объединение «Киловатт»» (`ooo-npo-kilovatt`) | 1244800001820 | 4800013729 | manufacturer |
| ООО «Научно-производственное объединение «Киловатт»» (Шестопалов) (`ooo-npo-kilovatt-shestopalov`) | 1244800005240 | 4800016776 | manufacturer | got docs
| ООО «ОПКБ Экспломет» (`ooo-opkb-eksplomet`) | 1211200001650 | 1215235283 | manufacturer | got docs
| ООО «Оржицкие артезианские воды» (`ooo-orzhitskie-artezianskie-vody`) | 1197746619950 | 9709055542 | money-layer | got docs
| ООО «Орион» (`ooo-orion`) | 1077758220451 | 7706664648 | money-layer | got docs
| ООО «Оупен Лоджистикс» (`ooo-oupen-lodzhistiks`) | 1237700483976 | 9714015016 | money-layer |
| ООО «ПОКРОВ» (`ooo-pokrov`) | 1245000068774 | 5038189259 | manufacturer | got docs
| ООО «Пехтра» (`ooo-pekhtra`) | 1245200032406 | 5261138034 | manufacturer | got docs
| ООО «Прайм» (`ooo-praym`) | 1097746825945 | 7735565264 | manufacturer | no docs
| ООО «Промсинтез» (`ooo-promsintez`) | 1073435002013 | 3435084957 | manufacturer | got docs
| ООО «РТ-Развитие бизнеса» (`ooo-rt-razvitie-biznesa`) | 1147746392200 | 7704861136 | money-layer | no docs
| ООО «Рокот Тех» (`ooo-rokot-tekh`) | 1247600010954 | 7606140961 | manufacturer | got docs
| ООО «Русская лаборатория воздушного транспорта» (`ovod`) | 1227100012369 | 7100027464 | manufacturer | got docs
| ООО «СПДББК» (`ooo-spdbbk`) | 1157847359273 | 7838044584 | manufacturer |
| ООО «СУПЕРХРОНО» (`ooo-superkhrono`) | 1163525102619 | 3525389520 | manufacturer |
| ООО «Сибирская навигационная компания» (`ooo-sibirskaya-navigatsionnaya-kompaniya`) | 1184205024849 | 4205376019 | manufacturer |
| ООО «Смарт Текнолоджис» (`ooo-smart-teknolodzhis`) | 1127746712752 | 7715934509 | manufacturer |
| ООО «Специальные материалы» (Спецмат) (`ooo-spetsmat-spetsialnye-materialy`) | 1247800116464 | 7801738089 | manufacturer |
| ООО «Специальные полезные технологии» (`ooo-spetsialnye-poleznye-tekhnologii`) | 1247700253668 | 9715478264 | manufacturer |
| ООО «Стройстандарт» (`ooo-stroystandart`) | 1077762402992 | 7733629755 | money-layer |
| ООО «Ушкуйник» (`npts-ushkuynik`) | 1245300001650 | 5300013923 | manufacturer |
| ООО «ЦТП» (Цифровая транспортная платформа) (`ooo-tstp-tsifrovaya-transportnaya-platforma`) | 1247700498660 | 9714054618 | plumbing |
| ООО «ЦЮС» (`ooo-tsyus`) | 1181215007192 | 1215226708 | plumbing |
| ООО «Центр управления городской аэромобильностью» (`ooo-tsugam`) | 1227700378553 | 9731094770 | manufacturer |
| ООО «ЭйАрТэк» (`ooo-eyartek`) | 1227300004282 | 7300000540 | manufacturer |
| ООО «Эколибри-Беспилотные технологии» (`ooo-ekolibri-bt`) | 1237700545191 | 9713001941 | manufacturer |
| ПАО «Банк ПСБ» (`pao-bank-psb`) | 1027739019142 | 7744000912 | cbst-core |
| Фонд «Градислава» | historic & cultural heritage preservation (`fond-gradislava-historic-cultural-heritage-preservation`) | 1117799007050 | 7704278421 | money-layer |
| Фонд «ДАР» | Фонд региональных некоммерческих проектов (`fond-dar-fond-regionalnykh-nekommercheskikh-proektov`) | 1067799028923 | 7705517400 | money-layer |
| Фонд поддержки зимних олимпийских видов спорта (`fond-podderzhki-zimnikh-olimpiyskikh-vidov-sporta`) | 1117799016851 | 7706470191 | money-layer |
| Фонд поддержки национальных морских программ (`fond-podderzhki-natsionalnykh-morskikh-programm`) | 1167700057447 | 7714389530 | money-layer |

## No ОГРН on file at all

**17 entities** — a founding-document request needs an ОГРН
(or at minimum a confirmed ИНН to look one up first); these are a prerequisite
gap, not yet a founding-doc gap as such.

| Entity | ИНН | Tier |
|---|---|---|
| «Аляска» (`alyaska`) | — | manufacturer |
| «Архангел спецназа» (Telegram-канал) (`tg-arkhangel-spetsnaza`) | — | — |
| «Булат» / 3mx (`bulat-3mx`) | — | manufacturer |
| «Кулибин-клуб» (`kulibin-klub`) | 7725229200 | manufacturer |
| «Уралдронзавод» (`uraldronzavod`) | — | manufacturer |
| АНО «НПЦ «Ушкуйник»» (`ano-npts-ushkuynik`) | 5300010714 | manufacturer |
| ГК «Логос» (`gk-logos`) | 7839303129 | manufacturer |
| ИП Сидоров Андрей Сергеевич (`ip-sidorov-andrey-sergeevich`) | — | manufacturer |
| КРАМС (бренд, юрлицо не установлено) (`krams-brand-unresolved`) | — | manufacturer |
| НПО «КАЙСАНТ» (`npo-kaysant`) | 7733393203 | manufacturer |
| ООО «Авирон» (`ooo-aviron`) | 7743451768 | manufacturer |
| ООО «Боевые технологии» (Военторг «ИРПТОРГ») (`ooo-boevye-tekhnologii`) | 5262393781 | money-layer |
| ООО «Радиофид Системы» (`ooo-radiofid-sistemy`) | 7802491148 | manufacturer | - ogrn 1107847000084
| ООО «Статус 53» (`ooo-status-53`) | 5300006098 | plumbing |
| ООО «ЦКБР» (`ooo-tskbr`) | — | manufacturer |
| ООО «Элиарс» (`ooo-eliars`) | 7735140825 | manufacturer |
| Проект КБ «Архангел» (`proekt-kb-arkhangel`) | — | manufacturer |

## Not reviewed (excluded from this pass)

- 3 tombstoned duplicate records (`_merged_into` set) — not live entities.
- 14 `tier: adjacent` entities — confirmed to lack a ЦБСТ/РОЙ.МАРКЕТ tie, out of
  scope for further primary-document collection per `CLAUDE.md`'s
  adjacent-networks policy.

## Note on EGRUL access-restricted entities

A handful of entities in the gap list above also carry an `egrul_flags`
129-ФЗ access-restriction marker on their директор/учредители section. This
does NOT mean their founding doc is unobtainable — a Устав pull is a separate
document type from the EGRUL disclosure record, and an entity can still have a
requestable founding-document bundle even when its current EGRUL
participant/director fields read "Доступ ограничен". Not pre-filtered out here;
worth attempting regardless, per the standing no-guessing/verify-directly rule.

## 2026-09-07 pull batch: what was found

6 bundles pulled and read in full (OCR'd where scanned, cp866 nested-zip
filenames fixed per the standing technique) for ООО «Кронштадт Беспилотные
Системы», ООО НПК «Герон», ООО «СКБ Пиранья», АО «Эколибри», АО УК
«Азимут» (formerly АО «АИС»), and АО «Научно-производственное предприятие».
Notable findings, all wired into `entities.json`/`people.json` via
`corrections_entities.json`/`corrections_people.json`:

- **Kronshtadt БПЛА's own устав self-declares military purpose.** §3.2.4
  explicitly lists development/production/testing/repair/modernization of
  dual-use and military-purpose aircraft "including unmanned aerial vehicles
  and UAV simulators", work in the interests of the Ministry of Defence
  (Navy, Air Force), FSB Border Service, MVD, FTS and military intelligence,
  and state-secrets handling — a direct self-declaration in the company's own
  founding legal document, not an inference from other sources.
- **New founder identity recovered: Ткач Кирилл Владимирович**, ООО НПК
  «Герон»'s sole founder — full name, passport number, and registered
  address recovered from the устав's own founder-disclosure clause (§6.2),
  added to `people.json` as `tkach-kirill-vladimirovich`. Also recovered:
  the company was formed via реорганизация (share exchange) from a prior
  ЗАО НПК «ГЕРОН», not a fresh incorporation.
- **АО УК «Азимут»'s charter-capital history corrected and completed.** A
  prior EGRUL-выписка-sourced entry had mis-dated the current ₽12,806,700,000
  capital to 2017-12-15 — the устав bundle shows the real 2017 capital was
  ₽100,000, four orders of magnitude smaller. Corrected timeline: ₽100,000
  (2017) → ₽12,806,600,000 (2021) → ₽12,806,700,000 (2025) — confirming a
  ~128,000× capital jump in 2021 while still named АО «АИС». Every edition
  2017-2025 explicitly declares "обслуживание, ремонт, утилизация и
  реализация вооружения и военной техники" (arms/military-equipment
  service/repair/disposal/sale) plus state-secrets handling as core purpose.
- **АО «Эколибри» became a formal resident of ИНТЦ «Аэрокосмическая
  инновационная долина»** (Aerospace Innovation Valley innovation
  science-technology center, under 216-ФЗ), per Изменения №4 к уставу
  (09.12.2025) — new `state_programs[]` entry, beyond the existing
  gisp.gov.ru/rk.2035.university catalogue listings. Also recovered an
  intermediate ₽50,000 charter-capital step (Sept 2024) between the prior
  history's gap and the current ₽76,336.
- ООО «СКБ Пиранья»: original устав was approved by a founders' MEETING
  (plural), not a sole founder — flagged as an open question against the
  single confirmed founder currently on file.
- АО «Научно-производственное предприятие»: corroborates existing capital/
  founder data, no new identity detail (устав doesn't name the founder,
  standard post-2009 pattern) and no aviation/military language found in
  its purpose clause.

Verification: `check_registry.py` 0 errors, 39 warnings (baseline
unchanged); full field-size diff against pre-change git HEAD showed 0
shrinkages after fixing a self-inflicted overwrite bug (an in-place
`state_programs[]` assignment on АО «Эколибри» initially clobbered its 2
pre-existing entries — caught by the diff, fixed by merging instead of
replacing); 182/182 profiles tag-balance clean.

## 2026-09-29 pull batch: what was found

8 bundles pulled and read in full for the 7 "money-layer"/"manufacturer"
entities already flagged "got docs" in the table above — ООО «ДСГ», ООО
«ИНТЭК беспилотные системы», ООО «Клеверкоптер», ООО «Кольская верфь», ООО
«Левит», ООО «Ментастеп», and ООО «Метаскан» — plus ООО «НОВА» (source
`s8109`, `UD_2103373.zip`; MANIFEST's auto-extracted ОГРН column came back
blank for this one so it initially looked unmatched, resolved by reading
the charter's own name/ОГРН block directly rather than trusting the
column).

**Every one of the 8 corroborates data already on file — no new founder,
director, or charter-capital fact for any of them.** All 8 entities
already had fully sourced `founders_history`/`director_history`/
`charter_capital_history` from prior full ЕГРЮЛ выписка pulls (s6726,
s6810, etc.) before this batch landed, and — consistent with the standard
pattern already noted several times above — a Устав's own body text does
not name founders or the sitting director (that's a separate Решение/
Протокол document not included in these bundles), so even the newly-read
text couldn't have closed the one real remaining gap on file (ИНТЭК
беспилотные системы's director-history entry, `value: null`, name never
captured — `Калиновский Никита Владиславович` does not appear anywhere in
its charter text either). Capital figures cross-checked digit-for-digit
against the registry: ДСГ ₽10,000, ИНТЭК ₽100,000, Метаскан ₽40,000 (its
2020 original-filing OCR read "19 000" at one point — an OCR misread
against its own written-out "десять тысяч"/ten-thousand, confirmed ₽10,000
like the rest of that entity's own filing history), all others unchanged.

One incidental historical fact, not wired as a structured field (the
absorbed entity has no registry record of its own and no further
ЦБСТ-relevant connection): ООО «Нова»'s 2017 charter amendment shows it
absorbed ООО «Новафининвест» via a joint-meeting протокол о присоединении
dated 01.03.2017 — same pattern as the earlier Инвестментс/АО «Борей»
finding, just with no live registry entity on the absorbed side to wire it
onto.

Verification: `check_registry.py` 0 errors, 18 warnings (baseline
unchanged) — no `corrections_entities.json` edits made this batch, since
nothing surfaced that wasn't already sourced.
