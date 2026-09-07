# Unverified-people backlog (updated 2026-09-07, 4th screen_upr_uchr.py pass)

Generated 2026-09-07, updated same day after a 4th `screen_upr_uchr.py` run
(109 people checked) plus a bugfix to that script itself -- see
`notes/SOURCE_REGISTER.md`/commit history for full detail. This revision also
closes out a real data-loss bug found the same day: `screen_upr_uchr.py` was
silently overwriting a person's real prior `other_entities` hits with a false
"0 hits" whenever pb.nalog.ru's captcha wall fired mid-drill-down -- fixed, and
the three known-affected people (Ташматов И.С., Тимофеев В.С., Кусумов В.А.)
restored to their last-good state.

`_verified: true` means a primary-source document (EGRUL/founding-doc
extract, a full ЕГРЮЛ выписка, a signed government contract, an official
ФНС registry cross-reference, etc.) has actually confirmed this person
against a known identifier or entity -- not just that some data exists on
the record.

**Closure passes so far:**
1. **71 people** closed by cross-referencing director_history/
   founders_history entries already sitting on entities they held a role
   at (no new documents pulled -- pure cross-reference of already-collected
   primary evidence).
2. **6 more people** closed via `screen_upr_uchr.py`'s ФНС director/founder
   cross-reference (`pb.nalog.ru`): Ольга Соколова (`ooo-tsugam`), Ступников
   А.Г. (`ooo-sibirskaya-navigatsionnaya-kompaniya`), Лобов В.Г. and Федяева
   А.Ю. (both `ao-korporatsiya-sinergiya`), and Михельсон Л.В. (`ooo-levit`)
   / Михельсон В.Л. (`ooo-ges-2`).
3. **Симановский Леонид Яковлевич** (Левит's 21.71% co-owner) added as a new
   person record, sourced directly against Левит's own full ЕГРЮЛ выписка.
4. A 2nd `screen_upr_uchr.py` pass (15 people) -- 4 hits, all peripheral/
   unrelated (a furniture-repair LLC, a plumbing/heating cluster, a name-only
   collision), none cleared the bar.
5. A 3rd `screen_upr_uchr.py` pass (21 people) closed **Елисеев Д.Н.** and
   **Владимирский М.Ю.** (both АНО «НПЦ «Ушкуйник»» staff) as confirmed 50/50
   co-founders of `ooo-npk-tspt-tsentr-perspektivnykh-tekhnologiy` (ЦПТ) --
   corroborated by that entity's own full ЕГРЮЛ выписка.
6. A 4th `screen_upr_uchr.py` pass (109 people) closed **Чичков А.Ю.**
   (second directorship at `ooo-prommash`, same Кемерово drone-manufacturing
   cluster as his known `ooo-dronomir` role) and **Руденко Д.А.** (previously
   on file with zero roles -- now director of `ano-ntsns-nevskiy-tsentr-
   nauchnogo-sotrudnichestva` plus 50%% co-founder of both `ooo-btr-bespilotnye-
   tekhnologicheskie-resheniya` and `ooo-spetsmat-spetsialnye-materialy`;
   notably co-founds БТР with Владимирский М.Ю., a second cross-link between
   those two people, not yet chased further).

**165 people remain unverified**, split below by what each actually needs.

## Group 1: has a personal ИНН, ready for a ФНС screen (37 people)

`screen_upr_uchr.py` is captcha-gated on `pb.nalog.ru` -- confirmed 2026-09-07
to be a count/session-based gate, not a request-rate one (bumping the
per-request delay from 2s to 15s did not avoid it; roughly the same ~35-
request budget before the wall fires either way). **Wait hours, not
minutes, between attempts.** It skips anyone already checked today, so
repeated runs make incremental progress. A silent data-loss bug in this
script (captcha-wall drill-down failures were overwriting real prior hits
with a false "0 hits") was fixed 2026-09-07 -- a failed drill-down now
leaves that person's prior result untouched instead of erasing it.
`screen_disqualified.py` and `screen_subsidiary.py` share the roster but not
necessarily the same wall (`screen_subsidiary.py` uses a different
`nalog.gov.ru` endpoint with no captcha observed so far -- a full run
against all 138 completed cleanly 2026-09-07 with 0 hits).

```
python3 scripts/screen_upr_uchr.py
python3 scripts/screen_disqualified.py
python3 scripts/screen_subsidiary.py   # already run clean, 0 hits -- rerun only for new people
```

A hit against an entity already in the registry is an instant
verification (see the closure passes above); a hit against an unlisted
entity is a new lead, not yet a citable fact until hand-checked -- most
hits so far have turned out to be unrelated peripheral businesses or
name collisions, not real ties.

| Person | ИНН | upr_uchr checked (hits) | disqual. checked | subsidiary checked | Known role |
|---|---|---|---|---|---|
| Александр Геннадьевич Сидякин (`aleksandr-sidyakin`) | 690900262387 | 2026-09-07 (0 hits) | — | 2026-09-07 | Secretary of the Supervisory Board; Head of United Russia’s Central Executive Committee @ ЦБСТ Supervisory Board |
| Александр Осадчук (`aleksandr-osadchuk`) | 772027207786 | 2026-09-07 (0 hits) | — | 2026-09-07 | Head of the Main Directorate for Innovative Development (ГУИР), Ministry of Defence @ ЦБСТ Supervisory Board |
| Александров Алексей Витальевич (`aleksandrov-aleksey-vitalevich`) | 027313454520 | 2026-09-07 (0 hits) | — | 2026-09-07 | — |
| Алёшин Борис Сергеевич (`aleshin-boris-sergeevich`) | 770802770590 | 2026-09-07 (6 hits) | — | 2026-09-07 | Chairman of the Board of Directors (until 2023 departure) @ ГК «Кронштадт» / Кронштадт industrial complex |
| Андрей Анатольевич Безруков (`andrey-bezrukov`) | 519031542137 | 2026-09-07 (0 hits) | — | 2026-09-07 | Chairman of the Board (правление), ЦБСТ @ ЦБСТ Supervisory Board |
| Андрей Турчак (`andrey-turchak`) | 781002279818 | 2026-09-07 (0 hits) | — | 2026-09-07 | Then Secretary of United Russia’s General Council; later Head of the Altai Republic |
| Арутюнов Николай Владимирович (`arutyunov-nikolay-vladimirovich`) | 100119009162 | 2026-09-07 (6 hits) | — | 2026-09-07 | директор по развитию @ ООО «Решение» ГК «Логос» |
| Белоглазова Людмила Александровна (`beloglazova-lyudmila-aleksandrovna`) | 636501893256 | 2026-09-07 (0 hits) | — | 2026-09-07 | — |
| Виноградов Юрий Александрович (`vinogradov-yuriy-aleksandrovich`) | 532115324671 | 2026-09-07 (0 hits) | — | 2026-09-07 | Заместитель генерального директора @ АНО «НПЦ «Ушкуйник»» |
| Владимир Владимирович Якушев (`vladimir-vadimovich-yakushev`) | 890304549930 | 2026-09-07 (1 hit) | — | 2026-09-07 | Chairman of the Supervisory Board; Secretary of United Russia’s General Council; First Deputy Chairman of the Federation Council @ ЦБСТ Supervisory Board |
| Живова Елена Вячеславовна (`zhivova-elena-vyacheslavovna`) | 531501384786 | 2026-09-07 (1 hit) | — | 2026-09-07 | Главный бухгалтер @ АНО «НПЦ «Ушкуйник»» |
| Кирилл Лысогорский (`kirill-lysogorskiy`) | 772705212594 | 2026-09-07 (0 hits) | — | 2026-09-07 | Deputy Minister of Industry and Trade @ ЦБСТ Supervisory Board |
| Кирток Александр Сергеевич (`kirtok-aleksandr-sergeevich`) | 511500997610 | 2026-09-07 (0 hits) | — | 2026-09-07 | Сотрудник @ ООО «Тримикс» |
| Киселёв Глеб Дмитриевич (`kiselev-gleb-dmitrievich`) | 772883561589 | 2026-09-07 (0 hits) | — | 2026-09-07 | представитель на круглом столе Народного фронта @ «Кулибин-клуб» (Народный фронт) |
| Королев Алексей Александрович (`korolev-aleksey-aleksandrovich`) | 761103199274 | 2026-09-07 (0 hits) | — | 2026-09-07 | — |
| Кузнецов Павел Владиславович (`kuznetsov-pavel-vladislavovich`) | 583502178630 | 2026-09-07 (1 hit) | 2026-09-06 | 2026-09-07 | — |
| Кузнецов Руслан Николаевич (`kuznetsov-ruslan-nikolaevich`) | 637592279701 | 2026-09-07 (0 hits) | — | 2026-09-07 | Сотрудник @ ООО «Тримикс»; Индивидуальный предприниматель @ ИП Кузнецов Руслан Николаевич |
| Кузякин Дмитрий Васильевич (`kuzyakin-dmitriy-vasilevich`) | 501306766736 | 2026-09-07 (1 hit) | — | 2026-09-07 | — @ АО «Котлин-Новатор»; co-inventor (patent RU236504U1) @ ООО «ЦКБР» |
| Куртеев Александр Сергеевич (`kurteev-aleksandr-sergeevich`) | 434540800305 | 2026-09-07 (0 hits) | 2026-09-06 | 2026-09-07 | — @ ООО «Гагаринг» |
| Ляшенко Игорь Владимирович (`lyashenko-igor-vladimirovich`) | 100122155290 | 2026-09-07 (2 hits) | — | 2026-09-07 | Генеральный директор и единственный учредитель (100%) @ ООО «Решение» ГК «Логос» |
| Михайлов Константин Денисович (`mikhaylov-konstantin-denisovich`) | 772032838410 | 2026-09-07 (1 hit) | — | 2026-09-07 | Дилер (Москва, Мариуполь) @ ООО «Тримикс» |
| Павлова Татьяна Викторовна (`pavlova-tatyana-viktorovna`) | 781409856219 | 2026-09-07 (0 hits) | — | 2026-09-07 | — |
| Петров Александр Витальевич (`petrov-aleksandr-vitalevich`) | 810702450538 | 2026-09-07 (0 hits) | — | 2026-09-07 | — |
| Петров Алексей Александрович (`petrov-aleksey-aleksandrovich`) | 290140368319 | 2026-09-07 (0 hits) | — | — | Сотрудник (не окончательно подтверждено) @ ООО «Тримикс» |
| Петров Виктор Витальевич (`petrov-viktor-vitalevich`) | 292700110340 | 2026-09-07 (0 hits) | — | 2026-09-07 | — |
| Петрова Дарья Александровна (`petrova-darya-aleksandrovna`) | 710680000353 | 2026-09-07 (0 hits) | — | 2026-09-07 | — |
| Потапов Игорь Владимирович (`potapov-igor-vladimirovich`) | 772578663993 | 2026-09-07 (0 hits) | — | 2026-09-07 | — |
| Потехина Светлана Алексеевна (`potekhina-svetlana-alekseevna`) | 526220591645 | 2026-09-07 (0 hits) | 2026-09-06 | 2026-09-07 | — @ ООО «Рационы питания» |
| Прокофьев Михаил Васильевич (`prokofev-mikhail-vasilevich`) | 532120471505 | 2026-09-07 (0 hits) | — | 2026-09-07 | сборщик (assembler) @ ООО «Скай авиа групп» |
| Саидов Адиль Абукович (`saidov-adil-abukovich`) | 772428159554 | 2026-09-07 (0 hits) | — | 2026-09-07 | Член совета директоров (board member) — which Azimut entity not fully confirmed @ АО УК «Азимут»; Советник генерального директора @ Государственная корпорация «Ростех»; Член Бюро Правления @ ОООР «СоюзМаш России»; Член Бюро @ Ассоциация «Лига содействия оборонным предприятиям»; Акционер (23.48%), с декабря 2014 @ АО «НИИ «Сапфир»» (0541016738) |
| Симановский Леонид Яковлевич (`simanovskiy-leonid-yakovlevich`) | 770100058167 | — | — | — | Участник (21.7098%, номинал ₽25,698,196) @ ООО «Левит» |
| Федорова Полина Геннадьевна (`fedorova-polina-gennadevna`) | 470200877524 | 2026-09-07 (0 hits) | — | 2026-09-07 | — |
| Царьков Даниил Дмитриевич (`tsarkov-daniil-dmitrievich`) | 501214513380 | 2026-09-07 (0 hits) | — | 2026-09-07 | Руководитель отдела (Department Head) @ АО «Стратим» |
| Шандобыло Милослава Игоревна (`shandobylo-miloslava-igorevna`) | 781152210830 | 2026-09-07 (0 hits) | — | 2026-09-07 | — |
| Шандобыло Сергей Сергеевич (`shandobylo-sergey-sergeevich`) | 781154619843 | 2026-09-07 (0 hits) | — | 2026-09-07 | Директор по развитию @ ООО «Тримикс»; Индивидуальный предприниматель @ ИП Шандобыло Сергей Сергеевич |
| Шахматов Иван Анатольевич (`shakhmatov-ivan-anatolevich`) | 471010513778 | 2026-09-07 (0 hits) | — | 2026-09-07 | — |
| Шветов Артемий Андреевич (`shvetov-artemiy-andreevich`) | 531500409942 | 2026-09-07 (0 hits) | — | 2026-09-07 | Сотрудник @ ООО «Тримикс» |

## Group 2: has a DOB but no ИНН (26 people)

A DOB is often the field that makes a rupep.org / press / EGRUL match
legally usable rather than merely suggestive (see the PII-policy
rationale in `CLAUDE.md`) -- these are worth a targeted rupep.org or
press search by name+DOB rather than a registry screen, since most lack
a personal ИНН to screen against.

| Person | DOB | Birthplace | Known role |
|---|---|---|---|
| Батанова Ольга Геннадьевна (`batanova-olga-gennadevna`) | 1955-07-06 | — | — |
| Гаврилов Александр Валерьевич (`gavrilov-aleksandr-valerevich`) | 1984-02-01 | — | — @ ООО «РТ-Развитие бизнеса»; — @ ГК «Ростех» |
| Дмитрий Владимирович Рубинштейн (`dmitriy-vladimirovich-rubinshteyn`) | 1975-04-13 | — | General Director, АНО «ЦБСТ», until late 2025 |
| Дмитрий Медведев (`dmitriy-medvedev`) | 1965-09-14 | Санкт-Петербург (Saint Petersburg, then Leningrad) | Chairman, United Russia; Deputy Chairman, Security Council |
| Елисеев Илья Владимирович (`eliseev-ilya-vladimirovich`) | 1965-12-19 | — | — |
| Жулидов Евгений (`zhulidov-evgeniy`) | 1998-07-14 | — | — |
| Корчагина Ольга Александровна (`korchagina-olga-aleksandrovna`) | 1972-04-25 | — | — |
| Кузнецова Менижеган Хантимировна (`kuznetsova-menizhegan-khantimirovna`) | 1966-08-01 | — | — |
| Мешков Александр Петрович (`meshkov-aleksandr-petrovich`) | 1957-12-11 | — | — |
| Мешкова Кристина Андреевна (`meshkova-kristina-andreevna`) | 2005-03-29 | — | — |
| Мешкова Надежда Филипповна (`meshkova-nadezhda-filippovna`) | 1954-10-08 | — | — |
| Незнамов Василий Александрович (`neznamov-vasiliy-aleksandrovich`) | 1959-02-08 | — | — |
| Незнамова Анастасия Васильевна (`neznamova-anastasiya-vasilevna`) | 1982-06-07 | — | — |
| Незнамова Людмила Викторовна (`neznamova-lyudmila-viktorovna`) | 1956-08-20 | — | — |
| Незнамова Ольга Викторовна (`neznamova-olga-viktorovna`) | 1977-08-22 | — | — |
| Петров Виталий Павлинович (`petrov-vitaliy-pavlinovich`) | 1931-05-01 | — | — |
| Петрова Марина Владимировна (`petrova-marina-vladimirovna`) | 1961-08-17 | — | — |
| Петрова Наталья Викторовна (`petrova-natalya-viktorovna`) | 1975-10-19 | — | — |
| Сафиева Виктория Зуфаровна (`safieva-viktoriya-zufarovna`) | 1985-01-28 | — | Сотрудник @ ООО «Тримикс» |
| Федоров Павел Романович (`fedorov-pavel-romanovich`) | 1998-08-31 | — | Сотрудник @ ООО «Тримикс» |
| Хутешен Алексей Александрович (`khuteshen-aleksey-aleksandrovich`) | 1983-10-02 | — | — @ ООО «ЦКБР» |
| Цыганова Виктория Юрьевна (`tsyganova-viktoriya-yurevna`) | 1963-10-28 | — | — |
| Шагиахметова Алиса Айратовна (`shagiakhmetova-alisa-ayratovna`) | 2015-04-05 | — | — |
| Шахматов Анатолий Александрович (`shakhmatov-anatoliy-aleksandrovich`) | 1963-10-20 | — | — |
| Шахматова Ольга Петровна (`shakhmatova-olga-petrovna`) | 1960-08-28 | — | — |
| Шахматова Татьяна Анатольевна (`shakhmatova-tatyana-anatolevna`) | 1989-03-28 | — | — |

## Group 3: named, no ИНН, no DOB (89 people)

The largest group and the hardest to close cheaply -- no structured
identifier to screen against. Verification for these needs an actual
name+role web/press search, an EGRUL open-lookup by name (accepting the
namesake-collision risk that comes with a name-only search), or a
primary document not yet pulled (a government contract signature block,
a founding-document bundle, a court filing). Sorted alphabetically;
triage by the `roles[]` significance (an entity director/founder is a
better use of research time than a passing mention).

| Person | Known role |
|---|---|
| Andrew (фамилия не установлена) (`andrew-first-pathfinder`) | Course participant (posted in the private chat, also member of Archangel_Forum) @ Проект КБ «Архангел» |
| Алейник Евгений (`aleynik-evgeniy`) | — |
| Александр (фамилия не установлена) (`alexandr-alex-bbggt`) | Course participant (posted in the private chat, also member of Archangel_Forum) @ Проект КБ «Архангел» |
| Александр Галушко (`galushko-aleksandr`) | Named recruitment contact for the UAV-systems training center's intake @ Учебный центр Беспилотных Систем (51-я Гвардейская Общевойсковая Армия / Архангел Легион / Гагаринг) |
| Александр Смородин (`smorodin-aleksandr`) | Named among the four counter-drone instructors (with Толстоусов, Толстоусова, Иванкин) training soldiers in aerial-target shooting for the «Последний рубеж» project @ Учебный центр «Гагаринг» (АНО ДПО «Образовательный центр Гагаринг») |
| Анна Толстоусова (Тараносова) (`tolstousova-anna-saiga`) | Старший инструктор (senior instructor), callsign «Сайга»; champion of Russia and Мастер спорта (Master of Sport) in practical shooting; trains soldiers in counter-drone aerial-target shooting under the «Последний рубеж» project @ Учебный центр «Гагаринг» (АНО ДПО «Образовательный центр Гагаринг») |
| Антонова Татьяна Сергеевна (`antonova-tatyana-sergeevna`) | — |
| Артём (позывной/контакт Dark_GAA) (`artem-dark-gaa`) | Named recruitment contact for the UAV-systems training center's intake @ Учебный центр Беспилотных Систем (51-я Гвардейская Общевойсковая Армия / Архангел Легион / Гагаринг) |
| Артём Толстоусов (`tolstousov-artem`) | Инструктор по тактико-огневой подготовке (tactical-firearms instructor); part of the «Последний рубеж» ("Last Frontier") counter-drone training team under Сергей «Лыня» Паршиков @ Учебный центр «Гагаринг» (АНО ДПО «Образовательный центр Гагаринг»); Named among the four counter-drone instructors (with Толстоусова, Смородин, Иванкин) training soldiers in aerial-target shooting for the «Последний рубеж» project @ Учебный центр «Гагаринг» (АНО ДПО «Образовательный центр Гагаринг») |
| Архангельский Геннадий (patronymic unconfirmed) (`arkhangelskiy-gennadiy-weapons-engineer`) | Contributor — weapons/mount engineering (self-described) @ Проект КБ «Архангел» |
| Атливанчик Сергей Николаевич (`atlivanchik-sergey-nikolaevich`) | — |
| Барило Денис Александрович (`barilo-denis-aleksandrovich`) | — |
| Басов Алексей Николаевич (`basov-aleksey-nikolaevich`) | — @ ООО «ДЕДАЛ»; — @ ООО «АИТК» |
| Бежанов Иван Валериевич (`bezhanov-ivan-valerievich`) | — @ АО «Хоук Холдинг»; — @ АО «АИН» |
| Бурлака Павел Анатольевич (`burlaka-pavel-anatolevich`) | — |
| Бэлла (фамилия не установлена) (`belissimo-bella-academy-admin`) | Admin, «Академия Противодействия БПЛА» chat (3,256 members) @ Проект КБ «Архангел» |
| Власов Артём Аркадьевич (`vlasov-artem-arkadevich`) | — @ АО «Стратолинк» |
| Военкор Евгений Лисицын (`voenkor-evgeniy-lisitsyn`) | Embedded war correspondent |
| Гагарин (имя/фамилия не установлены, позывной/юзернейм) (`gagarin-gagapih`) | Course participant (posted in the private chat, also member of Archangel_Forum) @ Проект КБ «Архангел» |
| Геха (фамилия не установлена, позывной/юзернейм) (`geha-geha125ru`) | Course participant (posted in the private chat, also member of Archangel_Forum) @ Проект КБ «Архангел» |
| Головачёв Виталий Юрьевич (`golovachev-vitaliy-yurevich`) | — |
| Гончаренко Антон Александрович (`goncharenko-anton-aleksandrovich`) | — @ АО «УК СМАРТ» |
| Данилин Виктор Сергеевич (`danilin-viktor-sergeevich`) | Сотрудник (Leader-ID org staff listing, role/title not specified) @ АО «Стратим» |
| Долгушевский Алексей Михайлович (`dolgushevskiy-aleksey-mikhaylovich`) | — |
| Дробаха Инга Сергеевна (`drobakha-inga-sergeevna`) | — |
| Дубровский Александр (`dubrovskiy-aleksandr`) | Course participant (posted in the private chat, also member of Archangel_Forum); self-stated external role below @ Проект КБ «Архангел» |
| Дукал Марина Александровна (`dukal-marina-aleksandrovna`) | — |
| Евгений Сергеевич (фамилия не установлена) (`evgeniy-sergeevich-ieto-yal`) | Course participant (posted in the private chat, also member of Archangel_Forum) @ Проект КБ «Архангел» |
| Ефремов Антон Вениаминович (`efremov-anton-veniaminovich`) | — @ АО «УК СМАРТ» |
| Жуков Дмитрий (`zhukov-dmitriy`) | Course participant (posted in the private chat, also member of Archangel_Forum) @ Проект КБ «Архангел» |
| Замятин Александр Юрьевич (`zamyatin-aleksandr-yurevich`) | технический директор — главный конструктор |
| Иванов Евгений Андреевич (`ivanov-evgeniy-andreevich-logos`) | эксперт Университета НТИ 2035 @ ГК «Логос» |
| Ивлев Артём Юрьевич (`ivlev-artem-yurevich`) | — |
| Исаенко Сергей Васильевич (`isaenko-sergey-vasilevich`) | — @ ООО «ДЕДАЛ»; — @ ООО «АИТК» |
| Калиновский Никита Владиславович (`kalinovskiy-nikita-vladislavovich`) | — @ ООО «ИНТЭК БЕСПИЛОТНЫЕ СИСТЕМЫ» |
| Капустин Павел Евгеньевич (`kapustin-pavel-evgenevich`) | — @ ООО «Визионеро» |
| Киндяков Андрей Андреевич (`kindyakov-andrey-andreevich`) | — @ ООО «КРАВТ» |
| Константинов Евгений Александрович (`konstantinov-evgeniy-aleksandrovich`) | — |
| Королев Дмитрий Алексеевич (`korolev-dmitriy-alekseevich`) | — |
| Кот Олег Петрович (`kot-oleg-petrovich`) | — @ АО «УК СМАРТ» |
| Крылов Андрей Олегович (`krylov-andrey-olegovich`) | — @ ООО «Стройстандарт»; — @ ООО «Винград» |
| Леонов Александр Владимирович (`leonov-aleksandr-vladimirovich`) | — @ ЮФ «АЙ ПИ ПРО» |
| Малевич Павел Владимирович (`malevich-pavel-vladimirovich`) | — |
| Малышева Наталья Викторовна (`malysheva-natalya-viktorovna`) | — @ УК «Азимут» |
| Манецкий Роман Каллистратович (`manetskiy-roman-kallistratovich`) | — |
| Махнёв Александр Игоревич (`makhnev-aleksandr-igorevich`) | — @ АО «Хоук Холдинг»; — @ АО «АИН» |
| Медисова Татьяна Николаевна (`medisova-tatyana-nikolaevna`) | — |
| Михаил Кузнецов (`mikhail-kuznetsov`) | Head of the Executive Committee, ОНФ (Popular Front) @ ЦБСТ Supervisory Board |
| Михайлова Ирина Валериевна (`mikhaylova-irina-valerievna`) | — @ АО «АУРИН»; — @ ООО «МПТМ» |
| Назаров Олег Рамилевич (`nazarov-oleg-ramilevich`) | — @ АО «АИН» |
| Настенков Виталий Геннадьевич (`nastenkov-vitaliy-gennadevich`) | — |
| Настя (фамилия не установлена) (`anlunegova-nastya-academy-admin`) | Admin, «Академия Противодействия БПЛА» chat (3,256 members) @ Проект КБ «Архангел» |
| Некрасов Александр Викторович (`nekrasov-aleksandr-viktorovich`) | Генеральный директор @ ООО «Конструкторское бюро «Синергия»»; — @ ООО «Визионеро»; — @ ООО «КБ «Синергия»»; — @ ООО «Метаскан» |
| Никифоров Антон Сергеевич (`nikiforov-anton-sergeevich`) | Первый заместитель генерального директора @ ООО «Аэромакс» |
| Обрезанова Ирина Вадимовна (`obrezanova-irina-vadimovna`) | — |
| Оксман Николас Николаевич (`oksman-nikolas-nikolaevich`) | — @ АО «Стратолинк» |
| Перекатов Сергей Сергеевич (`perekatov-sergey-sergeevich`) | — @ ООО «ЭйАрТэк» |
| Петрович (фамилия не установлена, позывной/юзернейм) (`petrovich-sapfpv`) | Course participant (posted in the private chat, also member of Archangel_Forum) @ Проект КБ «Архангел» |
| Попов Григорий Сергеевич (`popov-grigoriy-sergeevich`) | CV-инженер (computer-vision engineer) @ АО «Стратим» |
| Проценко Артём Витальевич (`protsenko-artem-vitalevich`) | — |
| Роман (фамилия не установлена) (`roman-academy-chat-79168352900`) | Course participant (posted in the private chat, also member of Archangel_Forum) @ Проект КБ «Архангел» |
| Рубцов Леонид Викторович (`rubtsov-leonid-viktorovich`) | — |
| СКИФ (фамилия не установлена, позывной/юзернейм) (`skif-wozmezdiye`) | Course participant (posted in the private chat, also member of Archangel_Forum) @ Проект КБ «Архангел» |
| Сергей Иванкин (`ivankin-sergey`) | Named among the four counter-drone instructors (with Толстоусов, Толстоусова, Смородин) training soldiers in aerial-target shooting for the «Последний рубеж» project @ Учебный центр «Гагаринг» (АНО ДПО «Образовательный центр Гагаринг») |
| Сергей Паршиков (`parshikov-sergey-lynya`) | Руководитель проекта «Последний рубеж» (head of the "Last Frontier" counter-drone training project run under Гагаринг), callsign «Лыня»; ветеран боевых действий 2014 года (combat veteran since 2014), волонтёр @ Учебный центр «Гагаринг» (АНО ДПО «Образовательный центр Гагаринг») |
| Сиразатдинов Никита Вадимович (`sirazatdinov-nikita-vadimovich`) | Учредитель @ АРРС (Ассоциация разработчиков перспективных систем РЭР/РЭБ/связи) |
| Скорятин Георгий Андреевич (`skoryatin-georgiy-andreevich`) | — @ ГК «Аэромакс» |
| Суховерхий Владимир Андреевич (`sukhoverkhiy-vladimir-andreevich`) | — @ ООО «Пехтра»; — @ ООО «Стартап-студия университета Лобачевского» |
| Сухоненкова Надежда Андреевна (`sukhonenkova-nadezhda-andreevna`) | — |
| Тарасенко Ирина Анатольевна (`tarasenko-irina-anatolevna`) | — |
| Тихонов Сергей Юрьевич (`tikhonov-sergey-yurevich`) | — |
| Ткач Кирилл Владимирович (`tkach-kirill-vladimirovich`) | Единственный учредитель (100%) @ ООО НПК «ГЕРОН» |
| Трубина Екатерина Святославовна (`trubina-ekaterina-svyatoslavovna`) | — |
| Федукович Кирилл Олегович (`fedukovich-kirill-olegovich`) | — @ АО «АУРИН» |
| Фомин Александр Николаевич (`fomin-aleksandr-nikolaevich`) | — @ ООО «ЭйАрТэк» |
| Фоминых Алексей Михайлович (`fominykh-aleksey-mikhaylovich`) | — |
| Фёдоров Павел Вячеславович (`fedorov-pavel-vyacheslavovich`) | — |
| Черезов Андрей Павлович (`cherezov-andrey-pavlovich`) | — |
| Четвертков Алексей Владимирович (`chetvertkov-aleksey-vladimirovich`) | — |
| Шандобыло Александр (`shandobylo-aleksandr-otets`) | — |
| Шандобыло Людмила Александровна (`shandobylo-lyudmila-aleksandrovna-mat`) | — |
| Шандобыло Татьяна (`shandobylo-tatyana-rodstvennitsa`) | — |
| Шандобыло Юлия (`shandobylo-yuliya-rodstvennitsa`) | — |
| Шацких Александр Владимирович (`shatskikh-aleksandr-vladimirovich`) | — @ ООО «НПО НЕБО» |
| Швецов Алексей Александрович (`shvetsov-aleksey-aleksandrovich`) | — @ ООО «Винград» |
| Шелаев Денис Владимирович (`shelaev-denis-vladimirovich`) | — |
| Штрек Игорь Александрович (`shtrek-igor-aleksandrovich`) | Инженер (Engineer), с 2021 @ АО «Стратим» |
| Шуликин Николай Константинович (`shulikin-nikolay-konstantinovich`) | — |
| Ястребов Сергей Владимирович (`yastrebov-sergey-vladimirovich`) | — @ АО «Хоук Холдинг»; — @ АО «АИН» |

## Group 4: no name recovered at all — Telegram handle/callsign only (13 people)

These are chat participants identified only by a Telegram username or
callsign (e.g. `@Dark_GAA`, `SKIF`) -- no surname was ever recoverable
from the source post. Cleared for inclusion under the 2026-09-04 PII
policy amendment (confirmed affiliated participants) on the strength of
their own chat activity, not an identity document. **These are
structurally unverifiable with the tooling this project has** -- there is
no primary-source document to cross-reference a bare handle against.
Leave `_verified: false` rather than force a citation; only remove from
this list if a real name is ever recovered (e.g. the handle posts a
selfie with a name tag, or another source ties the handle to a ФИО).

| Slug | Known role/context |
|---|---|
| `akhezin-a-n` | Заместитель руководителя, Главное управление МЧС России по Курской области |
| `borisov-aleksandr-sergeevich-tsbs-tula` | Генеральный директор, ООО «Центр беспилотных систем» (Тула, ИНН 7100032961) |
| `ganysh-v-p` | Начальник управления информационных технологий и связи, полковник внутренней службы, Главное управление МЧС России по Курской области |
| `grebenkova-k-yu` | Начальник отдела (организации контрактной работы), капитан, ФГКУ «ЦСООР «Лидер»» |
| `grigoryan-e-a` | Член приемочной комиссии, капитан, ФГКУ «ЦСООР «Лидер»» |
| `kulagin-s-a` | Член приемочной комиссии, майор, ФГКУ «ЦСООР «Лидер»» |
| `kuznetsov-v-s-fgku-lider` | Член приемочной комиссии, майор, ФГКУ «ЦСООР «Лидер»» |
| `lunev-ivan-ivanovich` | Начальник Главного управления МЧС России по Курской области |
| `saitov-renat-faritovich` | Генеральный директор ООО «Гаскар Интеграция» (2019) |
| `savvin-a-a` | Начальник, генерал-майор, ФГКУ «Центр по проведению спасательных операций особого риска «Лидер»» |
| `skabelin-s-n` | Материально-ответственное лицо, ФГКУ «ЦСООР «Лидер»» |
| `ustimov-r-s` | Член приемочной комиссии, капитан, ФГКУ «ЦСООР «Лидер»» |
| `zaytsev-e-d` | Член приемочной комиссии, майор, ФГКУ «ЦСООР «Лидер»» |

