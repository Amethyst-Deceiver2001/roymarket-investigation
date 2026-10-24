# Units named for the Kherson drone campaign: what our other channels say (24.10.2026)

Search of `data/roymarket.db` (117,382 posts, 57 channels; this Mac holds 23.10.2025 to 23.10.2026 for every channel except @osvedomitell_alex, which now runs back to 07.05.2024), excluding @osvedomitell_alex, in Python with case folding. Units searched: the three CIR/DW units, the SBU's regiment, the UN's formations, «Хабр», Teplinsky. **Every line is a channel's own statement, read in the post text; none is a registry fact yet.** Companion to `notes/kherson_human_safari_20261024.md`, `notes/osvedomitell_alex_scan_20261024.md`, `notes/un_coi_kherson_drones_20261024.md`.

## Counts (posts outside @osvedomitell_alex)
| Unit or formation | Posts | Where |
|---|---|---|
| 205th brigade | 44 | Архангел channels only (projectArchangel 33, Archangel_Forum 7, proekt_arhangel 2, one unnamed) |
| 18th Army (18 ОА) | 10 | mil_hub 4, rogozin_do 3, **nashapravdafond 1**, arx_spn, projectArchangel |
| 49th Army | 6 | mil_hub 5, **my_el_lab 1** |
| «Днепр» Group of Forces | 44 | mil_hub 20, rogozin_do 11, russian_shock_volunteer_brigade 6, evgeniy_lisitsyn, sudoplatov, arx_spn, tehnofrontrv |
| 10th Special Purpose Brigade («10 обрспн») | 16 | **tehnofrontrv 13**, mil_hub 2, projectArchangel 1 |
| 404th regiment, БАРС-33, «Хабр» (the unit), Скорпионы-328 | **0** | (two «Хабр» hits are the website habr.com) |
| «Рубикон» | 1,204 | sudoplatov 1,014; elsewhere only 5 posts also name Kherson-area places; no Kherson civilian link |

## 1. Our network touches the UN's «Днепр» group three ways (strongest to weakest)
**a. Архангел is inside Барс-Сармат, and Барс-Сармат is inside «Днепр».**
- Registry (case study, {doc}): Рогозин's own channel, 22.04.2025: «Теперь — в составе военно-учебного центра Центра специального назначения беспилотных систем "Барс-Сармат". Присоединяйтесь!» [s6915]; joint agreement of 17.10.2024 [s7693, s7694].
- **rogozin_do 8057, 19.01.2026:** «Жёсткие кадры боевой работы операторов боевых расчётов беспилотных систем ВДВ и Группировки войск "Днепр". … Центр специального назначения беспилотных систем "Барс-Сармат", командиром которого я являюсь, выполняет боевые задачи командующего ВДВ и Генерального штаба.»
- **rogozin_do 7780, 12.11.2025:** «многие наши союзники — армейские подразделения Группировки войск "Днепр" и части ВДВ предпочитают использовать в качестве боевой части штурмовых дронов боеприпасы, разработанные инженерами ЦСН "Барс-Сармат"».
- **russian_shock_volunteer_brigade 4237, 02.10.2026:** «Барс-Сармат, который входит в Группировку войск «Днепр» … численность … не менее 3 тыс. … входит в состав ВДВ». A channel's report quoting «источники»; weaker than Рогозин's own words.
- So: a ЦБСТ-tied training project says it is part of a centre whose commander says it fights for the group the UN names (A/80/497 para 40), and which supplies warhead munitions for assault drones to that group's units. **A group-level link on the entities' own words**, stronger than the 205th link because it rests on the head of the centre. It does not connect either to the Beryslav attacks or to any civilian target. The registry has Барс-Сармат (`csn-bars-sarmat`) with `cbst_tie: none`; the tie runs through Архангел, not directly.
- **«БАРС-33»** (CIR/DW) is a volunteer detachment of the «Днепр» group, per osvedomitell_alex 32160 (17.01.2026) and russian_shock 3457/3547 for «БАРС-37». Whether «БАРС» detachments relate to Барс-Сармат is **not** established; the name is not evidence.

**b. «Наша Правда» to the 18th Army.** **nashapravdafond 580, 05.03.2026:** «Автомобиль, который ранее Фонд «Наша Правда» передал участникам спецоперации, бойцы 18 армии дооборудовали РЭБ и успешно используют для доставки грузов на ЛБС и переброски личного состава.» The 18th Army is the formation the UN names (CRP.2 para 49). **A vehicle, not a drone**, and a feedback post by the fund itself. Add to the fund's earlier delivery to the 49th Army (h0018, 07.05.2024).

**c. Gagaring's «Сова» to the 49th Army.** **my_el_lab 2811, 23.12.2025:** «Воины 49-й Армии на страже неба Днепра … Без Совы перехватывать видео было бы на много тяжелее, Спасибо большое Александру и его команде. @PD_BpLA_KRAB». That is **counter-drone use** (intercepting enemy FPV video), signed by an air-defence channel. With the 205th under the 49th Army (osvedomitell_alex 27702): a ЦБСТ resident's component is at the army that includes the 205th, in a defensive role. The same company's Кузнечик is marketed for strike drones (ЦБСТ 2677); no post puts it in a 205th or 49th Army strike drone.

## 2. The 10th Special Purpose Brigade
**tehnofrontrv** (a volunteer print workshop; not in the registry; in `config/channels.txt` as «supplies tail sections/hulls to units per mil_hub posts») prints parts «для бойцов 10 обрспн» in 13 posts (08.11.2025 to 04.07.2026), including a catapult seal for the «Молния» (4757, 14.02.2026) and spools for cables. **Whether «10 обрспн» is CIR/DW's «10th Special Purpose Brigade» is not stated; the unit-number rule applies (bare numbers do not identify; `scripts/unit_lookup.py`).** No tie to ЦБСТ for tehnofrontrv. Lead.

## 3. Nothing
- **404th regiment, БАРС-33 (as «БАРС-33» by name), «Хабр», Скорпионы-328: no mention in any channel except @osvedomitell_alex.**
- Beryslav, Kakhovka and civilian-area posts: only the Kherson channel carries them. The other channels (mil_hub, arx_spn, rogozin_do) post combat video of the group but nothing we read states a civilian target; I did not search them for ambulance or civilian-vehicle wording. That search is still to do.

## 4. What we can say, and what we cannot
Can say (attributed): ЦБСТ's resident Архангел says it trains within Барс-Сармат; Барс-Сармат's commander says it fights in and for ГВ «Днепр» and equips its units' strike drones; the UN Commission found that drone units of that group are among those that attacked civilians in Kherson (A/80/497 para 40, 51–54); «Наша Правда» and Gagaring record deliveries to the 18th and 49th Armies.
Cannot say: that Барс-Сармат, Архангел, «Наша Правда», Gagaring or their donors took part in an attack on civilians; that any delivered item reached a unit or an incident; or that the UN named any of them.

## 5. To do
1. **Search the other channels for ambulance, civilian-vehicle and «двойного назначения» wording** that touches «Днепр», 18 ОА, 49 ОА, Барс-Сармат (local, quick).
2. Read **rogozin_do** and **mil_hub** around the Kherson sector for the group's own claims, to see whether Рогозин names Kherson or Beryslav.
3. Registry (main session): open questions on `csn-bars-sarmat` (Dnepr-group membership per Рогозин; tie via Архангел) and on `proekt-kb-arkhangel`; Gagaring ↔ 49th Army (my_el_lab 2811) and fund ↔ 18th Army (nashapravdafond 580) as delivery-record leads, **after** each post is read with its `links` (done here for the four above).
4. Get the unit-name sources for 18 ОА, 49 ОА, 205 омсбр before any unit record.

## 6. Follow-up search (24.10.2026): civilian-object wording in the Барс-Сармат channels, and the open questions now in the registry
Search of the same 57 channels for the unit names with ambulance, civilian-vehicle, infrastructure and «двойного назначения» wording (34 posts) and with Kherson-area place names (80 posts). **No post outside @osvedomitell_alex ties «Днепр», 18 ОА, 49 ОА or Барс-Сармат to ambulances or hearses**; the ambulance mentions in Рогозин's and the volunteer-brigade channels are accusations against Ukraine (rogozin_do 8511, 27.05.2026; russian_shock 3569, 16.02.2026), and a description of Барс-Сармат crews escorting civilian transport and helping civilians hit by Ukrainian drones (7977, 8675, 8820; russian_shock 3419).
What does bear on the UN's categories, in the centre commander's own words (rogozin_do):
- **7901, 18.12.2025:** «Херсонский фронт, обычное утро. Сапёры и бойцы роты охраны и сопровождения ЦСН "Барс-Сармат"…»: the centre has crews in the Kherson sector (left bank; 3527, 14.01.2026: «Херсонский участок фронта, левый берег Днепра»).
- **8017, 12.01.2026, Nikopol (Dnipropetrovsk Oblast, the right bank of the Dnipro, in A/80/497's area):** «В ходе съёмок пострадали здания фашистского гауляйтера Никополя, фуры, перевозившие лаборатории БпЛА ВСУ и другое военное имущество, а также объекты газо- и электроэнергетики. Ни один мирный житель при съёмках фильма не пострадал.» A claim of strikes on gas and electric installations in a city the UN names (A/80/497 para 34, 41, 35).
- **8257, 25.03.2026:** «Приносим вам свои извинения за временные неудобства в связи с началом процесса закрытия нами всех отделений Приватбанка в вашем городе … Закрытие Приватбанка было осуществлено нами рано утром — в 5.45. с целью ненанесения ущерба здоровью гражданского населения. Однако, впредь мы не можем гарантировать, что череда закрытий банковских отделений в гг. Никополь и Марганец … а затем и в гг. Запорожье и Херсоне будет проходить в столь раннее время или в выходные дни … прошу посещение данных банковских отделений гражданскими лицами немедленно прекратить.» On the photo: «отделение "Приватбанка" до и после его закрытия боевым расчётом "Барс-Сармат"». A stated policy of striking bank branches in civilian cities, with a warning to civilians. Irony in the text; whether the strikes happened is unchecked.
- **Why it matters:** the commander of the centre that hosts Архангел's training centre states in his own channel that the centre strikes civilian-city targets (bank branches, gas and power installations) and gives the warning pattern the UN describes. These are claims about **the centre**, not about Архангел. Not an attack on a person is claimed. Attribute only.

Registry (24.10.2026, from the posts quoted above): one open question each on `csn-bars-sarmat`, `ooo-gagaring`, `fond-nasha-pravda` (`corrections_entities.json` and `entities.json`); the checker shows 0 errors.
Still open: the Nikopol and bank-branch claims checked against Ukrainian reports of the same dates; a source outside channels for Барс-Сармат's place in «Днепр».
