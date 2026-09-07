# Founding-document (Устав) gap list

Generated 2026-09-07. Reviews every live entity in `entities.json` (excludes
3 tombstoned duplicates and 14 `tier: adjacent` out-of-scope entities) for
whether a founding-document primary source has actually been pulled and
archived, rather than relying on recall.

**"Has a founding doc" means one of:**
- a bespoke `UD_<OGRN>_*.zip` bundle in `data/sources/` (ФНС founding-document
  export — original устав text, amendments, founding-decision protocols), or
- a confirmed adoption of one of the 36 government-issued generic Типовые
  уставы (`data/registry/ustav_templates.json` `known_users[]`) — in this case
  we already know no entity-specific document exists to pull, so it is
  excluded from the gap list below rather than left as an open item.

**18 entities already have one** (16 bespoke bundles cover 18 slugs — some
OGRNs map to more than one historical filename — plus 2 confirmed generic-
template adopters) — excluded from the gap list below:

- АНО «ЦБСТ» | Centre for Unmanned Systems & Technologies (`ano-tsbst-centre-for-unmanned-systems-technologies`) — bespoke UD zip
- ООО «Заволжское» (`ooo-zavolzhskoe`) — template #20
- ООО «Гарант Клуб» (`ooo-garant-klub`) — bespoke UD zip
- ООО «Финконсалтингк» (ФКК) (`ooo-finkonsaltingk-fkk`) — bespoke UD zip
- ООО «Системный интегратор» (`ooo-sistemnyy-integrator`) — bespoke UD zip
- АО «Площадь» (`ao-ploshchad`) — bespoke UD zip
- ООО «БПР ЯРЛ» (`yarl`) — bespoke UD zip
- ООО «ТИТАН - СЕВЕРО-ЗАПАД» (`ooo-titan-severo-zapad`) — template #20
- ООО «КИНГПРО» (`ooo-kingpro`) — bespoke UD zip
- ООО «Центр Динарус» (`ooo-tsentr-dinarus`) — bespoke UD zip
- ООО «4ГНСС» (`ooo-4gnss`) — bespoke UD zip
- ООО «ПРОММАШ» (`ooo-prommash`) — bespoke UD zip
- ООО «АСЕЛ ЛАБС» (`ooo-asel-labs`) — bespoke UD zip
- ООО «Гагаринг» (`ooo-gagaring`) — bespoke UD zip
- ООО «ТИ ЭС ДЖИ ГРУПП» (`ooo-ti-es-dzhi-grupp`) — bespoke UD zip
- ООО «НПЦ БАСИРТК» (`ooo-npts-basirtk`) — bespoke UD zip
- ООО «Группа компаний «Логос»» (`ooo-gk-logos`) — bespoke UD zip
- ООО «РТД-Защита» (`ooo-rtd-zashchita`) — bespoke UD zip

## Gap list: live entities with an ОГРН, no founding doc on file

**135 entities.** Pull candidates for a manual ФНС founding-document request
(egrul.nalog.ru / nalog.gov.ru portal — no scriptable open-API route exists
for this document type, confirmed 2026-09-07, see `notes/SOURCE_REGISTER.md`).
Sorted alphabetically by name. `tier` shown for prioritization.

| Entity | ОГРН | ИНН | Tier |
|---|---|---|---|
| АНО «Платформа НТИ» (`ano-platforma-nti`) | 1197700000376 | 7703469180 | plumbing |
| АНО «ЦСАСД» (`ano-tsasd-demyansk`) | 1235300001947 | 5300008970 | plumbing |
| АНО «Центр развития транспортных технологий» (`ano-tsentr-razvitiya-transportnykh-tekhnologiy`) | 1217700636306 | 9724066980 | plumbing |
| АНО Военно-технической поддержки защитников Отечества и патриотического воспитания населения «Архангел» (`ano-arkhangel`) | 1242300005640 | 2315233718 | — |
| АНО ДПО «Образовательный центр Гагаринг» (`ano-dpo-obrazovatelny-tsentr-gagaring`) | 1252300026208 | 2310240630 | — |
| АО «АУРИН» (`ao-aurin`) | 1237700898786 | 9705214590 | plumbing |
| АО «Борей» | absorbed, no longer exists (`ao-borey-absorbed-no-longer-exists`) | 1247700237663 | 9701280698 | money-layer |
| АО «Главтехконструкция» (`ao-glavtekhkonstruktsiya`) | 1174632000190 | 4611014597 | money-layer |
| АО «Корпорация «Синергия»» (`ao-korporatsiya-sinergiya`) | 1237700250182 | 7743414861 | plumbing |
| АО «Котлин-Новатор» (`ao-kotlin-novator`) | 1027806064571 | 7811075899 | manufacturer |
| АО «МИКЦ» (`ao-mikts`) | 1227700322410 | 7714486438 | manufacturer |
| АО «НИИ «Вектор»» (`ao-nii-vektor`) | 1117847020400 | 7813491943 | manufacturer |
| АО «НИИ СТТ» (`ao-nii-stt`) | 1026701461160 | 6730046954 | manufacturer |
| АО «НПП «Радар ММС»» (`npp-radar-mms`) | 1027807560186 | 7814027653 | manufacturer |
| АО «НПЦ «Электронные вычислительно-информационные системы»» (ЭЛВИС) (`npts-elvis`) | 1127746073510 | 7735582816 | manufacturer |
| АО «Научно-производственное предприятие Беспилотные авиационные технологии» (`ao-npp-bat`) | 1237700769701 | 9718238013 | manufacturer |
| АО «ПМЦ «Авангард»» (`ao-pmts-avangard`) | 1047855051892 | 7804302798 | manufacturer |
| АО «Проминвест» (`ao-prominvest`) | 1237700148180 | 9714004945 | plumbing |
| АО «РОСС» (`ao-ross`) | 1027700135957 | 7704097425 | manufacturer |
| АО «Сейм-Агро» (`ao-seym-agro`) | 1114611000283 | 4611011596 | money-layer |
| АО «Спецтех Инвестиции» (`ao-spetstekh-investitsii-ao-spetstekh-pervyy`) | 1257700523079 | 9703232234 | cbst-core |
| АО «Спецтех Первый» (`ao-spetstekh-perviy`) | 1267700128376 | 9703244871 | cbst-core |
| АО «Стратим» (`ao-stratim`) | 1237700447324 | 7720901379 | manufacturer |
| АО «Технодинамика» (`ao-tekhnodinamika`) | 1037719005873 | 7719265496 | plumbing |
| АО «Технодрон» (`ao-tekhnodron`) | 1247700354175 | 9704241986 | manufacturer |
| АО «УК СМАРТ» (`ao-uk-smart`) | 1237700557050 | 7751264401 | plumbing |
| АО «Фабрика им. Советской Армии» (`ao-fabrika-im-sovetskoy-armii`) | 1027739157401 | 7709278792 | money-layer |
| АО «ХК Гумич» (`ao-khk-gumich`) | 1237700537788 | 9726051114 | money-layer |
| АО «Центр-Телко» (`ao-tsentr-telko`) | 1027739038590 | 7729150663 | plumbing |
| АО «Эколибри» (`ao-ekolibri`) | 1217700279103 | 7714473012 | manufacturer |
| АО ПК «Азимут» (`ao-pk-azimut`) | 1057746261605 | 7701583410 | money-layer |
| АО УК «Азимут» | formerly «Аэронавигационные и информационные системы» (`ao-uk-azimut-formerly-aeronavigatsionnye-i-informatsionnye-s`) | 1167746513967 | 7714390623 | money-layer |
| Акционерное общество «Научно-производственное предприятие» (`ao-npp-real`) | 1237700409121 | 9722048270 | manufacturer |
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
| ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "АРХАНГЕЛ ГРУПП" (`ooo-arkhangel-grupp`) | 1267700086081 | 9702081286 | manufacturer |
| ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "АРХАНГЕЛ ЩИТ" (`ooo-arkhangel-shchit`) | 1255000059533 | 5027339008 | manufacturer |
| ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "АРХАНГЕЛ" (`ooo-arkhangel-zaporizhzhie`) | 1249500004181 | 9500026652 | manufacturer |
| ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ "АРХАНГЕЛ" (`ooo-arkhangel-melitopol-2`) | 1249000005517 | 9001027869 | manufacturer |
| ООО «АС-КАМ» (`ooo-as-kam`) | 1166196114083 | 6165205064 | — |
| ООО «Авиационно-космические разработки «Бегак»» (`ooo-akr-begak`) | 1202600009919 | 2632116476 | manufacturer |
| ООО «Аркодим» (`ooo-arkodim`) | 1101690020959 | 1659101884 | manufacturer |
| ООО «Архангел» (`ooo-arkhangel`) | 1257700345407 | 9714079108 | manufacturer |
| ООО «Атлант Аэро» (`ooo-atlant-aero`) | 1236100025633 | 6154165878 | manufacturer |
| ООО «Аэро-Хит» (`ooo-aero-khit`) | 1232700009398 | 2700012608 | manufacturer |
| ООО «Аэромакс» (`ooo-aeromaks`) | 1177746007900 | 7725347482 | manufacturer |
| ООО «Аэроплатформы» (`ooo-aeroplatformy`) | 1215000018650 | 5027293811 | manufacturer |
| ООО «Аэротехальянс» (`ooo-aerotekhalyans`) | 1237700640660 | 9714020721 | money-layer |
| ООО «Беспилотные технологические решения» (БТР) (`ooo-btr-bespilotnye-tekhnologicheskie-resheniya`) | 1247800059980 | 7813680637 | manufacturer |
| ООО «Визионеро» (`ooo-vizionero`) | 1195958038902 | 5902056314 | manufacturer |
| ООО «Винград» (`ooo-vingrad`) | 1177746217879 | 9701066447 | money-layer |
| ООО «Воздушный трактат» (`ooo-vozdushnyy-traktat`) | 1237100015767 | 7100046925 | manufacturer |
| ООО «Восточные ворота Забайкальск-Маньчжурия» (`ooo-vostochnye-vorota-zabaykalsk-manchzhuriya`) | 5167746405481 | 7703420474 | manufacturer |
| ООО «ГОУДРОН» (`ooo-goudron`) | 1237700265846 | 9721203814 | manufacturer |
| ООО «ГЭС-2» (`ooo-ges-2`) | 1147746575767 | 7706809928 | money-layer |
| ООО «Гаскар Интеграция» (`ooo-gaskar-integratsiya`) | 5147746074196 | 7733894200 | manufacturer |
| ООО «Гаскар Технологии» (`ooo-gaskar-tekhnologii`) | 1207700344037 | 9731070264 | manufacturer |
| ООО «Гаскар» (`ooo-gaskar`) | 1237700273744 | 9710112989 | manufacturer |
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
| ООО «МПТМ» (`ooo-mptm`) | 1257700021468 | 9714068459 | cbst-core |
| ООО «Ментастеп» (`ooo-mentastep`) | 1247700255208 | 9715478320 | manufacturer |
| ООО «Метаскан» (`ooo-metaskan`) | 1201600057097 | 1660349248 | manufacturer |
| ООО «НОВА» (`ooo-nova`) | 1086330002549 | 6330037352 | money-layer |
| ООО «НПК «Центр перспективных технологий»» (ЦПТ) (`ooo-npk-tspt-tsentr-perspektivnykh-tekhnologiy`) | 1265300000470 | 5300022741 | manufacturer |
| ООО «НПО НЕБО» (`ooo-npo-nebo`) | 1254800002786 | 4800023371 | manufacturer |
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
| ООО «СКБ Пиранья» (`ooo-skb-piranya`) | 1237300010430 | 7300024069 | manufacturer |
| ООО «СПДББК» (`ooo-spdbbk`) | 1157847359273 | 7838044584 | manufacturer |
| ООО «СУПЕРХРОНО» (`ooo-superkhrono`) | 1163525102619 | 3525389520 | manufacturer |
| ООО «Сибирская навигационная компания» (`ooo-sibirskaya-navigatsionnaya-kompaniya`) | 1184205024849 | 4205376019 | manufacturer |
| ООО «Скай авиа групп» (`ooo-skay-avia-grupp`) | 1147847241464 | 7802865058 | manufacturer |
| ООО «Смарт Текнолоджис» (`ooo-smart-teknolodzhis`) | 1127746712752 | 7715934509 | manufacturer |
| ООО «Специальные материалы» (Спецмат) (`ooo-spetsmat-spetsialnye-materialy`) | 1247800116464 | 7801738089 | manufacturer |
| ООО «Специальные полезные технологии» (`ooo-spetsialnye-poleznye-tekhnologii`) | 1247700253668 | 9715478264 | manufacturer |
| ООО «Стратим» (`ooo-stratim`) | 1245200009075 | 5260494520 | manufacturer |
| ООО «Стройстандарт» (`ooo-stroystandart`) | 1077762402992 | 7733629755 | money-layer |
| ООО «Тримикс» (`ooo-trimiks-bulat-3mx`) | 1237800084235 | 7802942873 | manufacturer |
| ООО «Ушкуйник-СП» (`ooo-ushkuynik-sp`) | 1245300003827 | 5300015906 | manufacturer |
| ООО «Ушкуйник» (`npts-ushkuynik`) | 1245300001650 | 5300013923 | manufacturer |
| ООО «ЦТП» (Цифровая транспортная платформа) (`ooo-tstp-tsifrovaya-transportnaya-platforma`) | 1247700498660 | 9714054618 | plumbing |
| ООО «ЦЮС» (`ooo-tsyus`) | 1181215007192 | 1215226708 | plumbing |
| ООО «Центр беспилотных систем» (`ooo-tsentr-bespilotnykh-sistem-tula`) | 1237100001467 | 7100032961 | cbst-core |
| ООО «Центр управления городской аэромобильностью» (`ooo-tsugam`) | 1227700378553 | 9731094770 | manufacturer |
| ООО «ЭйАрТэк» (`ooo-eyartek`) | 1227300004282 | 7300000540 | manufacturer |
| ООО «Эколибри-Беспилотные технологии» (`ooo-ekolibri-bt`) | 1237700545191 | 9713001941 | manufacturer |
| ООО НПК «Герон» (`ooo-npk-geron`) | 1187847365750 | 7814748285 | manufacturer |
| Общество с ограниченной ответственностью «Кронштадт Беспилотные Системы» (`ooo-kronshtadt-bespilotnye-sistemy`) | 1167847402898 | 7801320277 | manufacturer |
| ПАО «Банк ПСБ» (`pao-bank-psb`) | 1027739019142 | 7744000912 | cbst-core |
| Фонд «Градислава» | historic & cultural heritage preservation (`fond-gradislava-historic-cultural-heritage-preservation`) | 1117799007050 | 7704278421 | money-layer |
| Фонд «ДАР» | Фонд региональных некоммерческих проектов (`fond-dar-fond-regionalnykh-nekommercheskikh-proektov`) | 1067799028923 | 7705517400 | money-layer |
| Фонд «Наша Правда» (`fond-nasha-pravda`) | 1237700218612 | 9705196180 | cbst-core |
| Фонд поддержки зимних олимпийских видов спорта (`fond-podderzhki-zimnikh-olimpiyskikh-vidov-sporta`) | 1117799016851 | 7706470191 | money-layer |
| Фонд поддержки национальных морских программ (`fond-podderzhki-natsionalnykh-morskikh-programm`) | 1167700057447 | 7714389530 | money-layer |

## No ОГРН on file at all

**17 entities** — a founding-document request needs an ОГРН (or at minimum a
confirmed ИНН to look one up first); these are a prerequisite gap, not yet a
founding-doc gap as such.

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
  scope for further primary-document collection per CLAUDE.md's
  adjacent-networks policy.

## Note on EGRUL access-restricted entities

A handful of entities in the gap list above also carry an `egrul_flags`
129-ФЗ access-restriction marker on their директор/учредители section. This
does NOT mean their founding doc is unobtainable — a Устав pull is a separate
document type from the EGRUL disclosure record, and an entity can still have a
requestable founding-document bundle even when its current EGRUL
participant/director fields read "Доступ ограничен". Not pre-filtered out here;
worth attempting regardless, per the standing no-guessing/verify-directly rule.
