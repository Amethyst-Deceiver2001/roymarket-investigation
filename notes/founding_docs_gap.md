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
- ООО «Финконсалтингк» (ФКК) (`ooo-finkonsaltingk-fkk`) — bespoke UD zip
- ООО «Центр Динарус» (`ooo-tsentr-dinarus`) — bespoke UD zip
- ООО НПК «Герон» (`ooo-npk-geron`) — bespoke UD zip
- Общество с ограниченной ответственностью «Кронштадт Беспилотные Системы» (`ooo-kronshtadt-bespilotnye-sistemy`) — bespoke UD zip
- АО «Проминвест» (`ao-prominvest`) — bespoke UD zip, `UD_1237700148180_20260908_ao-prominvest.zip`
- ООО «Гаскар» (`ooo-gaskar`) — bespoke UD zip, `UD_1237700273744_20260908_ooo-gaskar.zip`
- ООО «Центр беспилотных систем» (Tula) (`ooo-tsentr-bespilotnykh-sistem-tula`) — bespoke UD zip, `UD_1237100001467_20260908_ooo-tsentr-bespilotnykh-sistem-tula.zip`

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
| АО «Спецтех Инвестиции» (`ao-spetstekh-investitsii-ao-spetstekh-pervyy`) | 1257700523079 | 9703232234 | 2026-09-08: "документ формируется" at ФНС. Deprioritized. |
| АО «Спецтех Первый» (`ao-spetstekh-perviy`) | 1267700128376 | 9703244871 | 2026-09-08: "документ формируется" at ФНС. Deprioritized. |
| Фонд «Наша Правда» (`fond-nasha-pravda`) | 1237700218612 | 9705196180 | 2026-09-08: "документ формируется" at ФНС. Deprioritized. |
| ООО «МПТМ» (`ooo-mptm`) | 1257700021468 | 9714068459 | 2026-09-08: "документ формируется" at ФНС. Deprioritized. |
| АО «Стратим» (`ao-stratim`) | 1237700447324 | 7720901379 | 2026-09-08: "документ формируется" at ФНС. Deprioritized. |
| АО «Котлин-Новатор» (`ao-kotlin-novator`) | 1027806064571 | 7811075899 | 2026-09-08: "документ формируется" at ФНС. Deprioritized. |
| ООО «Тримикс» (`ooo-trimiks-bulat-3mx`) | 1237800084235 | 7802942873 | 2026-09-08: "документ формируется" at ФНС (re-attempted; the entity's EGRUL identity was separately already resolved via a different pull, see docs/index.html's footnote — that's a different document type). Deprioritized. |

## Gap list: live entities with an ОГРН, no founding doc on file

**109 entities.** Pull candidates for a manual ФНС founding-document request
(egrul.nalog.ru / nalog.gov.ru portal — no scriptable open-API route exists
for this document type, confirmed 2026-09-07, see `notes/SOURCE_REGISTER.md`).
Sorted alphabetically by name. `tier` shown for prioritization.

| Entity | ОГРН | ИНН | Tier |
|---|---|---|---|
| АНО «Платформа НТИ» (`ano-platforma-nti`) | 1197700000376 | 7703469180 | plumbing | - no docs 
| АНО «ЦСАСД» (`ano-tsasd-demyansk`) | 1235300001947 | 5300008970 | plumbing |
| АНО «Центр развития транспортных технологий» (`ano-tsentr-razvitiya-transportnykh-tekhnologiy`) | 1217700636306 | 9724066980 | plumbing | - no docs
| АО «АУРИН» (`ao-aurin`) | 1237700898786 | 9705214590 | plumbing |
| АО «Борей» | absorbed, no longer exists (`ao-borey-absorbed-no-longer-exists`) | 1247700237663 | 9701280698 | money-layer |
| АО «Главтехконструкция» (`ao-glavtekhkonstruktsiya`) | 1174632000190 | 4611014597 | money-layer |
| АО «Корпорация «Синергия»» (`ao-korporatsiya-sinergiya`) | 1237700250182 | 7743414861 | plumbing |
| АО «МИКЦ» (`ao-mikts`) | 1227700322410 | 7714486438 | manufacturer |
| АО «НПП «Радар ММС»» (`npp-radar-mms`) | 1027807560186 | 7814027653 | manufacturer |
| АО «НПЦ «Электронные вычислительно-информационные системы»» (ЭЛВИС) (`npts-elvis`) | 1127746073510 | 7735582816 | manufacturer |
| АО «Научно-производственное предприятие Беспилотные авиационные технологии» (`ao-npp-bat`) | 1237700769701 | 9718238013 | manufacturer |
| АО «ПМЦ «Авангард»» (`ao-pmts-avangard`) | 1047855051892 | 7804302798 | manufacturer |
| АО «РОСС» (`ao-ross`) | 1027700135957 | 7704097425 | manufacturer |
| АО «Сейм-Агро» (`ao-seym-agro`) | 1114611000283 | 4611011596 | money-layer |
| АО «Технодинамика» (`ao-tekhnodinamika`) | 1037719005873 | 7719265496 | plumbing |
| АО «УК СМАРТ» (`ao-uk-smart`) | 1237700557050 | 7751264401 | plumbing |
| АО «Фабрика им. Советской Армии» (`ao-fabrika-im-sovetskoy-armii`) | 1027739157401 | 7709278792 | money-layer |
| АО «ХК Гумич» (`ao-khk-gumich`) | 1237700537788 | 9726051114 | money-layer | - no docs
| АО «Центр-Телко» (`ao-tsentr-telko`) | 1027739038590 | 7729150663 | plumbing |
| Ассоциация благотворительной помощи «Взаимопомощь» (`assotsiatsiya-vzaimopomoshch`) | 1164700050734 | 4707039070 | money-layer |
| Ассоциация разработчиков перспективных систем радиоэлектронной разведки, радиоэлектронной борьбы и связи (РЭР, РЭБ и связи) (`ano-arrs-krasnodar`) | 1242300011469 | 2312325336 | plumbing |
| Благотворительный фонд «КЦПН» (`bf-ktspn-barnaul`) | 1152225001114 | 2224171246 | plumbing |
| ГК «Ростех» (`gk-rostekh`) | 1077799030847 | 7704274402 | plumbing |
| ЗАО «Курскпромтеплица» (`zao-kurskpromteplitsa`) | 1117746195214 | 7705944272 | money-layer |
| ИП Кузнецов Руслан Николаевич (`ip-kuznetsov-ruslan-nikolaevich`) | 320631300042842 | 637592279701 | manufacturer |
| ИП Цыганов Вадим Борисович (`ip-tsyganov-vadim-borisovich`) | 318500700040208 | 504405055721 | manufacturer |
| ИП Шандобыло Сергей Сергеевич (`ip-shandobylo-sergey-sergeevich`) | 320784700272511 | 781154619843 | manufacturer |
| НЕКОММЕРЧЕСКОЕ ПАРТНЕРСТВО «ДИСКРЕТНО-ИННОВАЦИОННЫЙ КЛАСТЕР МАЛОЙ АВИАЦИИ» (`np-diskretno-innovatsionny-klaster-maloy-aviatsii`) | 1142651011788 | 2632811832 | plumbing |
| НПП «ЭЛВО» (`npp-elvo-kolskaya-verf`) | 1217800070509 | 7810918592 | manufacturer |
| ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "АРХАНГЕЛ ГРУПП" (`ooo-arkhangel-grupp`) | 1267700086081 | 9702081286 | manufacturer | - founding docs found
| ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "АРХАНГЕЛ ЩИТ" (`ooo-arkhangel-shchit`) | 1255000059533 | 5027339008 | manufacturer | docs found
| ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "АРХАНГЕЛ" (`ooo-arkhangel-zaporizhzhie`) | 1249500004181 | 9500026652 | manufacturer | 

Действующая организация
ИНН:
9500026652
ОГРН:
1249500004181
Регион:
Запорожская область
Применяет типовой устав № 20 с 21.08.2024
| ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "АРХАНГЕЛ" (`ooo-arkhangel-melitopol-2`) | 1249000005517 | 9001027869 | manufacturer | Применяет типовой устав № 20 с 09.06.2024

| ООО «АС-КАМ» (`ooo-as-kam`) | 1166196114083 | 6165205064 | — |
| ООО «Авиационно-космические разработки «Бегак»» (`ooo-akr-begak`) | 1202600009919 | 2632116476 | manufacturer |
| ООО «Аркодим» (`ooo-arkodim`) | 1101690020959 | 1659101884 | manufacturer |
| ООО «Аэро-Хит» (`ooo-aero-khit`) | 1232700009398 | 2700012608 | manufacturer | no docs
| ООО «Аэромакс» (`ooo-aeromaks`) | 1177746007900 | 7725347482 | manufacturer | no docs
| ООО «Аэроплатформы» (`ooo-aeroplatformy`) | 1215000018650 | 5027293811 | manufacturer |
| ООО «Аэротехальянс» (`ooo-aerotekhalyans`) | 1237700640660 | 9714020721 | money-layer |
| ООО «Беспилотные технологические решения» (БТР) (`ooo-btr-bespilotnye-tekhnologicheskie-resheniya`) | 1247800059980 | 7813680637 | manufacturer |
| ООО «Визионеро» (`ooo-vizionero`) | 1195958038902 | 5902056314 | manufacturer |
| ООО «Винград» (`ooo-vingrad`) | 1177746217879 | 9701066447 | money-layer | docs found
| ООО «Воздушный трактат» (`ooo-vozdushnyy-traktat`) | 1237100015767 | 7100046925 | manufacturer |
| ООО «Восточные ворота Забайкальск-Маньчжурия» (`ooo-vostochnye-vorota-zabaykalsk-manchzhuriya`) | 5167746405481 | 7703420474 | manufacturer |
| ООО «ГОУДРОН» (`ooo-goudron`) | 1237700265846 | 9721203814 | manufacturer |
| ООО «ГЭС-2» (`ooo-ges-2`) | 1147746575767 | 7706809928 | money-layer |
| ООО «Гаскар Интеграция» (`ooo-gaskar-integratsiya`) | 5147746074196 | 7733894200 | manufacturer |
| ООО «Гаскар Технологии» (`ooo-gaskar-tekhnologii`) | 1207700344037 | 9731070264 | manufacturer |
| ООО «Герон» (`ooo-geron`) | 1217800073545 | 7802893898 | manufacturer |
| ООО «Группа компаний «Аэромакс»» (`ooo-gk-aeromaks`) | 1147748024269 | 7710974353 | manufacturer |
| ООО «ДИАМ-АЭРО» (`ooo-diam-aero`) | 1187847091079 | 7811687549 | — |
| ООО «ДРОН-РЕЙСИНГ» (`ooo-dron-reysing`) | 1187746574696 | 7728432295 | manufacturer |
| ООО «ДРОНОМИР» (`ooo-dronomir`) | 1264200005530 | 4214047363 | manufacturer |
| ООО «ДСГ» (`ooo-dsg`) | 1207700030493 | 9724002908 | manufacturer |
| ООО «ЗИТ.ЦИ» | Отраслевой центр импортозамещения (`ooo-zit-tsi-otraslevoy-tsentr-importozameshcheniya`) | 1227700802878 | 9726029133 | money-layer |
| ООО «Зетакс» (`ooo-zetaks`) | 1225300003983 | 5300006066 | manufacturer |
| ООО «ИНТЭК БЕСПИЛОТНЫЕ СИСТЕМЫ» (`ooo-intek-bespilotnye-sistemy`) | 1247000000488 | 7000013316 | manufacturer |
| ООО «Инвестментс» (`ooo-investments`) | 1237700523895 | 9707004743 | money-layer |
| ООО «Интел Дрон» (`ooo-intel-dron`) | 1247400026246 | 7448259249 | manufacturer |
| ООО «Информационные системы и технологии» (`ooo-instekh`) | 1207800035079 | 7842179810 | manufacturer |
| ООО «КРАВТ УДМУРТИЯ» (`ooo-kravt-udmurtiya`) | 1241800012222 | 1800023369 | manufacturer |
| ООО «КРАВТ» (`ooo-kravt`) | 1197847166560 | 7802693899 | manufacturer |
| ООО «Клеверкоптер» (`ooo-kleverkopter`) | 1185275047176 | 5257183517 | manufacturer |
| ООО «Кольская верфь» (`kolskaya-verf`) | 1245100006799 | 5190102381 | manufacturer |
| ООО «Конструкторское бюро «Синергия»» (`ooo-konstruktorskoe-byuro-sinergiya`) | 1237800134835 | 7842219445 | manufacturer |
| ООО «Конструкторское бюро СОВА» (`va-technologies`) | 1252300058515 | 2378001237 | manufacturer |
| ООО «КоптерЛаб» (`ooo-kopterlab`) | 1247700198734 | 7720925267 | manufacturer |
| ООО «Левит» (`ooo-levit`) | 1066330007798 | 6330030244 | money-layer |
| ООО «Ментастеп» (`ooo-mentastep`) | 1247700255208 | 9715478320 | manufacturer |
| ООО «Метаскан» (`ooo-metaskan`) | 1201600057097 | 1660349248 | manufacturer |
| ООО «НОВА» (`ooo-nova`) | 1086330002549 | 6330037352 | money-layer |
| ООО «НПК «Центр перспективных технологий»» (ЦПТ) (`ooo-npk-tspt-tsentr-perspektivnykh-tekhnologiy`) | 1265300000470 | 5300022741 | manufacturer |
| ООО «НПО Рустехдрон» (`ooo-npo-rustekhdron`) | 1235000022179 | 5003155499 | manufacturer |
| ООО «НПО Эйлер» (Научно-производственное объединение «Эйлер») (`ooo-npo-eyler`) | 1257100008560 | 7100069249 | manufacturer |
| ООО «Научно-производственное объединение «Киловатт»» (`ooo-npo-kilovatt`) | 1244800001820 | 4800013729 | manufacturer |
| ООО «Научно-производственное объединение «Киловатт»» (Шестопалов) (`ooo-npo-kilovatt-shestopalov`) | 1244800005240 | 4800016776 | manufacturer |
| ООО «ОПКБ Экспломет» (`ooo-opkb-eksplomet`) | 1211200001650 | 1215235283 | manufacturer |
| ООО «ОРИЕНТ СИСТЕМС» (`ooo-orient-sistems`) | 5147746083491 | 7743939185 | manufacturer |
| ООО «Оржицкие артезианские воды» (`ooo-orzhitskie-artezianskie-vody`) | 1197746619950 | 9709055542 | money-layer |
| ООО «Орион» (`ooo-orion`) | 1077758220451 | 7706664648 | money-layer |
| ООО «Оупен Лоджистикс» (`ooo-oupen-lodzhistiks`) | 1237700483976 | 9714015016 | money-layer |
| ООО «ПОКРОВ» (`ooo-pokrov`) | 1245000068774 | 5038189259 | manufacturer |
| ООО «Пехтра» (`ooo-pekhtra`) | 1245200032406 | 5261138034 | manufacturer |
| ООО «Прайм» (`ooo-praym`) | 1097746825945 | 7735565264 | manufacturer |
| ООО «Промсинтез» (`ooo-promsintez`) | 1073435002013 | 3435084957 | manufacturer |
| ООО «РТ-Развитие бизнеса» (`ooo-rt-razvitie-biznesa`) | 1147746392200 | 7704861136 | money-layer |
| ООО «Рокот Тех» (`ooo-rokot-tekh`) | 1247600010954 | 7606140961 | manufacturer |
| ООО «Русская лаборатория воздушного транспорта» (`ovod`) | 1227100012369 | 7100027464 | manufacturer |
| ООО «СПДББК» (`ooo-spdbbk`) | 1157847359273 | 7838044584 | manufacturer |
| ООО «СУПЕРХРОНО» (`ooo-superkhrono`) | 1163525102619 | 3525389520 | manufacturer |
| ООО «Сибирская навигационная компания» (`ooo-sibirskaya-navigatsionnaya-kompaniya`) | 1184205024849 | 4205376019 | manufacturer |
| ООО «Скай авиа групп» (`ooo-skay-avia-grupp`) | 1147847241464 | 7802865058 | manufacturer |
| ООО «Смарт Текнолоджис» (`ooo-smart-teknolodzhis`) | 1127746712752 | 7715934509 | manufacturer |
| ООО «Специальные материалы» (Спецмат) (`ooo-spetsmat-spetsialnye-materialy`) | 1247800116464 | 7801738089 | manufacturer |
| ООО «Специальные полезные технологии» (`ooo-spetsialnye-poleznye-tekhnologii`) | 1247700253668 | 9715478264 | manufacturer |
| ООО «Стратим» (`ooo-stratim`) | 1245200009075 | 5260494520 | manufacturer |
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
| ООО «Радиофид Системы» (`ooo-radiofid-sistemy`) | 7802491148 | manufacturer |
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
