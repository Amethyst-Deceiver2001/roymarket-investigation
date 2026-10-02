# ЦБСТ residency and accelerator roster derived from the archive (2026-10-02)

No official list exists. `python3 scripts/cbst_roster_derive.py --kind resident|accelerator --out x.json` (local, about a minute) reruns the sweep of `cbst_resident_sweep.py` over 503,714 posts and splits the evidence per registry entity into **company-named** (the post names the company beside «резидент…») and **product-only** (a product name in a list of residents' goods; a lead, never a membership). Every wired passage below was read in the post itself; hits are a reading aid.

Result: 329 posts with «резидент» in ЦБСТ context, 46 registry entities resolved (33 by company, 13 by product only); accelerator wording: 356 posts, 33 entities (23 by company).

## Wired as `memberships[]` (corrections_entities.json)

- **doc, ЦБСТ's own channel (14):** АО «Площадь» (post 305), ООО «Смарт Текнолоджис» (487), ООО «ИНТЭК промышленные системы» (447), ГК «Логос» (878), АО «Нейрореволюция»/Neiry (1572), АО «Стратолинк» (1956), ООО «Кравт» (2067), ООО «Аркодим» (2134), ООО «КоптерЛаб» (2198), ООО «ВИЛЛИС»/Wheelies (2186), ООО «Уралдронзавод» (2116), and from the New Year list of 31.12.2025 (post 1701) ООО «Авирон», ООО «Визионеро», «Аляска» (`alyaska`); АО «Стратим» from post 1074 (brand-level). Already wired before: НПП «ЭЛВО», НПЦ «Ушкуйник».
- **doc, company's own channel:** ООО «КРАМС» (krams_pro 133), self-declared.
- **press, other channels only (3):** ООО «СуперХроно», ООО «Титан Северо-Запад» (mil_hub), ООО «КИНГПРО» (evgeniy_lisitsyn). ЦБСТ edits posts after publication, so these need the original.
- **Accelerator, first stream:** ООО «Интел Дрон» (winner), ООО «Ментастеп» (finalist). Residency not stated for either.

## Not wired (leads, with the reason)

- «Овод»: named in the 1701 list, but two entities carry it (`ovod` ООО «РЛВТ», `ooo-vozdushnyy-traktat`): needs a decision on which holds the status.
- АО «НПП» (1701): abbreviation is generic; `ao-npp-real` is t-open only.
- «Рустехдрон», «Скворец» (post 1074): brand-level, two Рустехдрон entities, Скворец is a product.
- ООО «Боевые технологии» (post 1135): «Владимира Потехина, резидента ЦБСТ» is grammatically the person, not clearly the company.
- ООО «Пиранья», ООО «Тримикс» («Булат»): named only through products at the Дронница 2025 exhibit (post 1193); Тримикс's tie stays two statements.
- «Мобил-груп» etc. from Дронница 2023 are a different question (see `ushkuynik_family_and_programs.md` §7).
- `kolskaya-verf` is not a resident: the post calls it «резидент Арктической зоны».
- ООО «Ментастеп», «Пехтра» as residents: the 04.06.2025 post says winners «станут резидентами» (future).

## Scale

ЦБСТ's own counts (now claims on `cbst-residency`): 50+ (14.12.2024), 100+ (09.01.2025), 350+ (06.11.2025), 400+ supported (29.12.2025), 525 (Aug 2026). 21 derived memberships are a small part of that; residents ЦБСТ does not name in public posts cannot be derived. Derivable next: the rest of the NEW list in `cbst_resident_triage_20261002.md`, and the product-only leads once a post names the maker.
