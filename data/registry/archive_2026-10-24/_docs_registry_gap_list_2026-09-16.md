# docs/index.html → registry structured-field gap list (2026-09-16)

Fresh re-derivation per peer session's recommendation (their remembered "~15 people"
list was explicitly unreliable — not used as a starting point here). Method: stripped
`docs/index.html` to plain text, grepped for role-keyword contexts
(учредитель/директор/президент/владелец/бенефициар/основатель) across the whole
document, then cross-checked every named individual against `people.json` `roles[]`
(source_id present/absent) and the corresponding entity's `director_history`/
`founders_history` in `entities.json`. Excludes everything fixed in b47ea74
(ao-stratim UBOs: Ястребов/Бежанов/Махнёв/Назаров; ooo-zavolzhskoe/Рубцов Л.В.).

**This is a triage list only** — nothing wired, no corrections.json/extract_registry.py
touched. Every item below still needs a human to pull/read the actual primary source
(mostly: the specific БФО filing note or Minjust filing already cited in the docs.html
prose) before wiring a `source_id`.

---

## (a) High-confidence gaps — real, specific, sourced-in-prose tie with NO matching
structured field, ready for a human to verify + wire

1. **Елисеев Илья Владимирович** (`eliseev-ilya-vladimirovich`) — Фонд «ДАР» /
   Фонд «Наша Правда». `people.json` roles = `[]` (empty). docs/index.html: *"Илья
   Владимирович Елисеев (no employer listed — the same sanctioned individual who
   chairs ДАР's board, here holding a direct seat one level closer to the fund
   that actually procures and transfers equipment)"* — named in Наша Правда's own
   FY2024 ГИР БО filing (tagged "Primary doc" in the brief) as a Наблюдательный
   совет member, and separately as chairing ДАР's own supervisory board (per the
   entity's own `_raw.role` note: "Supervisory board chaired by Ilya Eliseev").
   Neither seat is in his `roles[]`. His existing `sanctions[]` entry already notes
   the ДАР-chairmanship claim (OpenSanctions corroboration) but with `source_id:
   null` — the primary FY2024 filing that would source it directly is apparently
   already in this project's hands (cited elsewhere as "Primary doc").

2. **Карабинский Иван Игоревич** — Фонд «Градислава» GD. **Two duplicate person
   records exist**: `ivan-igorevich-karabinskiy` (has one role, `entity_slug: null`,
   `source_id: null`) and `karabinskiy-ivan-igorevich` (zero roles at all) — likely
   a dedup bug in addition to the sourcing gap. Meanwhile `entities.json`'s
   `fond-gradislava-historic-cultural-heritage-preservation` already has a fully
   sourced `director_history` entry for him (`source_id: s0216`, ГРН
   2217711641585, 17.12.2021). The entity side is fine; the person side is
   split across two stub records, neither carrying the reciprocal sourced role.
   Also his separate Наша Правда Наблюдательный совет seat ("Иван Игоревич
   Карабинский (Градислава)") is unrecorded on either record.

3. **Устратов Дмитрий Владимирович** (`ustratov-dmitriy-vladimirovich`) — Фонд
   поддержки национальных морских программ, GD since 30.04.2021. His one role
   entry has `entity_slug: null`, `source_id: null` — even though
   `entities.json`'s `fond-podderzhki-natsionalnykh-morskikh-programm` already
   carries two sourced `director_history` entries for the same fact (`s6703`,
   `s0105`). Also unrecorded: his separate Наша Правда Наблюдательный совет seat.

4. **Давыдов Виктор Ильич** (`viktor-ilich-davydov`) — Фонд «ДАР» GD since 2008.
   Same pattern: role entry `entity_slug: null`, `source_id: null`, while
   `entities.json`'s `fond-dar-...` has a fully sourced `director_history`
   (`source_id: s0214`). Also his separately-disclosed role as ООО «Орион»'s
   "бенефициарный владелец" (named explicitly in that entity's own FY2023–25
   filings, per docs.html prose) is not reflected in his roles.

5. **Антонова Татьяна Сергеевна** (`antonova-tatyana-sergeevna`) — Наша Правда
   Наблюдательный совет member, named in the same FY2024 filing ("Primary doc").
   `roles[]` = `[]`.

6. **Тихонов Сергей Юрьевич** (`tikhonov-sergey-yurevich`) — Фонд «ДАР»
   Попечительский совет member (distinct from ООО «Прайм»'s GD Баранова — see
   ruled-out item in section (c)). `roles[]` = `[]`.

7. **Манецкий Роман Каллистратович** (`manetskiy-roman-kallistratovich`) — Фонд
   «Градислава» Попечительский совет member. `roles[]` = `[]`.

8. **Дукал Марина Александровна** (`dukal-marina-aleksandrovna`) — Фонд «ДАР»
   Попечительский совет member. `roles[]` = `[]`.

9. **Семилетов Антон Дмитриевич** (`semiletov-anton-dmitrievich`) — АО НПЦ
   «ЭЛВИС», Генеральный директор as of 03.12.2024. `entities.json`'s `npts-elvis`
   already carries this fully sourced (`director_history`, `source_id: s3702`,
   explicitly noted as "First director_history entry for this entity"). His
   `people.json` roles list only 4 unrelated patent co-inventor credits for
   ЭЛВИС — the actual GD role is entirely missing from his record, despite
   being sourced and present on the entity side. Pure backfill, source already
   in hand.

10. **Басов Алексей Николаевич** and **Исаенко Сергей Васильевич** — both
    currently carry only unsourced (`source_id: null`) roles at "ООО «ДЕДАЛ»"
    and "ООО «АИТК»". docs/index.html's actual claim, per АО «Эколибри»'s own
    FY2025 БФО filing notes (governance disclosure), is that both sit on
    **Эколибри's Совет директоров** — ДЕДАЛ/АИТК are shareholders in Эколибри
    (13.1%/12.5%), not entities these two people direct. The Эколибри board
    seat itself is entirely missing from both records, and is sourced (FY2025
    БФО filing, already pulled per the prose). `ao-ekolibri`'s own
    `director_history` only has Павлова — no board-seat field exists on the
    entity at all for Жук/Басов/Исаенко/Rogozin.

11. **Жук Виталий Александрович** (`zhuk-vitaliy-aleksandrovich`) — same
    Эколибри Совет директоров seat as #10, missing from both his record (only
    Котлин-Новатор GD + Клеверкоптер are recorded) and the entity's structured
    fields. Note docs.html itself flags this Жук as *possibly* the same person
    as Котлин-Новатор's Жук — "not independently confirmed as the same person"
    — so this should be verified as same-vs-different person before wiring,
    not assumed.

12. **Рогозин Алексей Дмитриевич** (`rogozin-aleksey-dmitrievich`) — same
    Эколибри Совет директоров seat (per FY2025 filing), distinct from his
    existing recorded "Chairman of the Advisory Council" role (`s0962`) which
    the same filing supersedes/updates ("Rogozin's own current role... is a
    seat on the Board of Directors... not merely an advisory-council
    chairmanship"). Also missing: his FY2025-disclosed position as a small
    long-term lender to Эколибри (₽302k at 6.5%). His existing advisory-council
    role entry should probably get an `to`/end-date or superseding note rather
    than being silently left alongside the new board-seat entry as if both are
    current.

13. **АО «Эколибри»** (`ao-ekolibri`) itself — `founders_history` is `[]`
    despite the FY2025 filing disclosing a full shareholder table (Павлова
    52.4%, ООО «ДЕДАЛ» 13.1%, ООО «АИТК» 12.5%, Жук 12.5%). This is an
    entity-side structural gap, not just a person-side one — flagging
    alongside the person gaps above since they'd likely get wired together.

---

## (b) Ambiguous / needs verification before wiring

- **Куртеев Александр Сергеевич** (`kurteev-aleksandr-sergeevich`) — has a role
  entry for ООО «Гагаринг» with `source_id: null`, but docs/index.html's own
  prose is explicit that this is an **unresolved, unconfirmed** link ("a name
  not otherwise connected to ООО «Гагаринг» or Барашков anywhere else in this
  brief... still flagged as unresolved, not a confirmed link"). The existing
  role entry may itself be a premature/incorrect wire — worth a human decision
  on whether to remove it (source doesn't exist) rather than add one.

- **Гарькуша Владимир Владимирович / Бурлака Павел Анатольевич** —
  docs/index.html states Гарькуша "had to amend the charter before he could
  formally install Бурлака as a distinct director four months after founding,"
  with the amendment "personally signed" — but the excerpt captured doesn't
  name which entity (context around index.html line ~1227, entity name is a
  few lines earlier than what was captured in this pass — needs re-reading
  that specific section to identify the entity slug). Бурлака has zero roles
  in `people.json`. Needs the entity identified before this can be called a
  clean gap vs. already covered under a different entity's `director_history`.

- **Сиразатдинов Никита Вадимович** and **Климов Максим Александрович** — both
  have a role at "АРРС (Ассоциация разработчиков перспективных систем
  РЭР/РЭБ/связи)" as "Учредитель" but `source_id: null`. docs/index.html's
  source for this is a list-org.com aggregator lookup, not a primary document
  — flagged by the brief's own prose as still needing better sourcing ("not
  yet established whether АРРС itself has any direct ЦБСТ tie... flagged for
  further research"). Verify whether a stronger source (EGRUL extract) exists
  before wiring a `source_id`, rather than citing the aggregator as-is.

- **Дробаха Инга Сергеевна**, **Тарасенко Ирина Анатольевна**, **Обрезанова
  Ирина Вадимовна** — АО «Росс» (financial director / unspecified roles per
  the company's own site listing). All three have person records but zero
  roles. Source would be the АО «Росс» site listing itself (ross-jsc.ru,
  JS-rendered) — a company's own self-published staff listing, weaker than a
  filing, but citable per this project's sourcing conventions. Low priority
  (roles are vague: "unspecified other roles" per the brief's own prose for
  two of the three).

- **Сухоненкова Надежда Андреевна** (`sukhonenkova-nadezhda-andreevna`) —
  НПЦ БАСиРТК Административный директор, per two dated letters (one
  05.04.2026, a repeat addressee 16 months later per the brief's own framing —
  check this date math, the excerpt is internally inconsistent as written).
  Zero roles on the person record. Needs the letter source_id(s) identified.

- **Максимов Юрий Алексеевич** (`maksimov-yuriy-alekseevich`) — role recorded
  with `source_id: s0009` but `title: null`. Likely just needs the title field
  filled ("Генеральный директор, АО «РОСС»") rather than a missing source —
  minor completeness gap, not a sourcing gap.

- **Замятин Александр Юрьевич** (`zamyatin-aleksandr-yurevich`) — role has
  `source_id: s0232` (sourced) but `entity_slug: null` and `entity_name: null`
  — an orphaned role, title only ("технический директор — главный
  конструктор") with no entity attached. The excerpt captured didn't retain
  which entity this was for (docs.html line ~1379) — needs re-reading that
  section to attach the entity_slug; the source itself already exists.

---

## (c) False leads ruled out

- **"ooo-praym / Тихонов"** — confirmed FALSE, matching the peer's own
  warning. `ooo-praym` (ИНН 7735565264) is correctly and fully sourced to
  **Баранова Ольга Владимировна** as GD (`source_id: s0120`/`s6828`) and
  **Степаева Мария Ивановна** as prior director/100% owner (`s0494`/`s6828`).
  Тихонов Сергей Юрьевич has no connection to ООО «Прайм» anywhere in
  docs/index.html — he's a Фонд «ДАР» Попечительский совет member (see (a)#6),
  an entirely different entity. No trace of any Тихонов↔Прайм claim was found
  in the text scan; whatever produced that false association in the peer's
  memory doesn't correspond to anything actually in docs/index.html or the
  registry.

- **Баранова Ольга Владимировна ↔ ООО «АКР «Бегак»»** — she has a role listed
  for this entity too (`source_id: null`), but docs/index.html itself only
  ever describes her in connection with ООО «Прайм» ("director Баранова Ольга
  Владимировна — no obvious defense/UAV tie by name alone, not yet otherwise
  researched"). No mention connects her to АКР «Бегак» in the prose scanned —
  this looks like a possible mis-wire (maybe from a shared-founders-list
  context around АРРС's five founding members, which lists both Бегак's
  company and Прайм as separate entries, not as connected to each other via
  Баранова). Flagged for a human to check, not confirmed false, but suspicious
  enough to not present as a confidence gap in section (a).

---

## Not re-checked in this pass (out of scope / already covered)

- ao-stratim UBOs, ooo-zavolzhskoe/Рубцов — excluded per instructions (done in
  b47ea74).
- Барашков Александр Сергеевич, Бегак Александр Аркадьевич, Загорский
  Александр Сергеевич, Максимов Юрий Алексеевич (АО «Росс» GD fact itself) —
  all already carry real sourced roles matching docs/index.html's claims, no
  gap found.
