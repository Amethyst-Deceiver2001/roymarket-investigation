# @osvedomitell_alex scan: what it adds to the Kherson note (24.10.2026)

Scan of 24.10.2026 (user-run): 16,074 posts, 24.10.2024 to 24.10.2026, in `data/roymarket.db` (channel id 1763867870, «От Мариуполя до Карпат», Kherson-direction war blogger; the page footer lists an author handle and an RKN personal-page registration). Searched in Python with case folding (not SQL LIKE); hit counts are over post text only. Companion to `notes/kherson_human_safari_20261024.md`. **Posts are the channel's own claims (grade rep), mostly reposts of unit channels; nothing here is a registry fact yet.** Post ids are this DB's msg_id.

## Hit counts (post text)
205th brigade 41 · Берислав 73 · Каховк 121 · Судоплатов 85 · «Судный День» 60+ · Хабр 93 · 404th 6 · БАРС-33 4 · Рубикон 7 · сафари 4 · Архангел 8 (all "Архангел Спецназа", an unrelated channel signature or the church, none our project) · ЦБСТ / РОЙ.МАРКЕТ / «Наша Правда» **0**. «Херсон» 6,299 and «Днепр» 2,125 are boilerplate-heavy and not counted as evidence.

## 1. The 205th brigade sits in the Beryslav sector, under the 49th Army (closes to-close item 3, at channel-claim level)
- **27702, 23.07.2025** (repost of t.me/official_49_army): «Бериславский отрезок фронта. Работают мужчины из стали 205 бригада 49 ОА ГВ "Днепр" … удары дронами по ПВД противника». The same post: «Любое передвижение автотранспорта будет считаться законной целью. Все объекты критической инфраструктуры являются законной целью. Гражданским быть предельно внимательными и осторожными.»
- Other posts name the brigade at Beryslav (24075, 03.02.2025; 24546, 26.02.2025), Казацкое (27081, 33291) and in «ГВ "Днепр"» (24206, 25759). 34195 (03.05.2026) gives «205-я отдельная мотострелковая казачья бригада (в/ч 74814, Будённовск)»; 22984 (13.12.2024) the presidential honorific.
- **What this changes:** the fund's 07.05.2024 delivery to «49-й армии» (h0018) and the 205th are now linked **by the channel's own wording, not Wikipedia**. Still a formation-level overlap; the 100 drones are not shown to reach the 205th.

## 2. Sudoplatov VT-40 is used by 205th crews, per this channel
- **24195 (09.02.2025), 24206, 22582 (25.11.2024):** «операторами ударных БПЛа из состава 205 бригады … Расчёт fpv работает дронами ВТ-40 проекта "Судный День"»; the channel also credits «Судный День» for parcels (25110, 25373). Links to t.me/sudoplatov_official.
- With HRW's identification of a VT-40 in one Kherson attack and the registry's open lead on Архангел's «судоплатовских комплектующих (ВТ 40)», the three now join: **Архангел recruits for the 205th; the 205th's crews are shown with VT-40; Sudoplatov's component is on Архангел's list.** Each is a separate claim by a different party; none says an Архангел graduate flew a VT-40 at a civilian.

## 3. Direct use of «сафари»
- **38581, 19.10.2026 (video):** «Хохлы часто пишут, что наши расчеты устроили в Херсоне сафари на людей. Мы практически не показываем, как происходит заход на цель и что было до... … оператор никогда не будет атаковать цель, если не убедится, что прохожие в безопасности. … Все цели подтверждены и определены.» **So a Russian war blogger, in October 2026, answers the accusation by name.** It corrects the earlier note's "no Russian source engages with it" and the user's observation that none call it that: this one denies the label, it does not adopt it. No unit is named in the post.
- Other «сафари»: 24718 (07.03.2025, repost of AirlinesVDV, «Славное сафари выдалось у одного из расчетов … подбиты транспортное средство с лс и два петушка»: the hunting-vehicles-and-personnel sense, right bank of the Dnipro); 27993 (a boat hunt); 34424 (a complaint about Ukrainian "safari" on locals).

## 4. Other units
- **404th regiment:** 24631 (03.03.2025) «Бойцы Волгоградского 404-го мотострелкового полка сражаются … от Алешек до Казачьих Лагерей», plus greetings (28453: «404 полк 126 бр»). The unit named in the SBU notices operates in the same sector; no post links it to civilian targets.
- **БАРС-33:** 21969 (01.11.2024), 26541 (31.05.2025), 32160 (17.01.2026: award ceremony, group «Днепр»). **Рубикон** appears for Black Sea and Pokrovsk work, not Kherson.
- **Kakhovka:** 121 hits, not yet read; the 205th greeting from Новая Каховка (23230) is one.

## Not found
No ЦБСТ, РОЙ.МАРКЕТ, «Наша Правда», Архангел-project or Kherson-ООО mention. The channel does not link to our network.

## To do
1. Read the 121 Каховка and the Berislav posts for civilian-vehicle wording; list posts that show strikes on vehicles or "ПВД" in settlements.
2. Pull the media of 27702, 24195, 38581 only if the user wants them (user-run download).
3. Registry: record the 205th brigade as a unit only after `scripts/unit_lookup.py` and a unit-name source; add the 49 ОА pairing from 27702 as the cited basis. Add Sudoplatov-VT-40 ↔ 205th as an open-question update on `proekt-kb-arkhangel`.
4. The VK post the user cited was not in the scrape; still needs its text.
