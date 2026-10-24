# Political-intermediary / bridge-figure triage — 2026-09-15

> **Archived 24.10.2026.** The leads that were still open were moved into the records' `open_questions` (the two officials known only by initials). The registry has since backfilled the role sources for Якушев, Безруков and Песков. **One error here:** item 4 calls Дмитрий Песков the Kremlin press secretary; the record is Дмитрий Николаевич Песков, the presidential special representative and head of Платформа НТИ, a different person. Not a source.

Local-data triage only (people.json, entities.json, roymarket.db — no live network
calls made). Not a source in itself; every candidate below still needs the usual
primary-source verification before being wired into `sanctions[]`/`roles[]`/a new
`political_intermediary` field via `corrections_people.json`. This file follows the
same non-authoritative-triage pattern as `_informal_ties_leads.md`/`_scaffold_leads.json`.

Method: scanned every person's `roles[]` titles/body, `notes`, and (where the ФНС
director/founder sweep has run) `other_entities[]` for political/state-apparatus
keywords (Госдума/Совет Федерации/Единая Россия/ФСБ/администрация/министр/генерал
[excluding "Генеральный директор"]/полпред/etc.), cross-referenced against formal
business ties (a `roles[]` entry with `entity_slug` pointing at a registry entity, or
a confirmed `other_entities[]` hit). Tiers pulled live from `entities.json.tier`.

## Part 1 — Political affiliation + formal registry-entity tie (11 candidates)

Every claim below cites the exact `source_id` on file, or is flagged "no source_id"
where the registry record itself carries none yet — that is itself a sourcing gap,
not a verified fact, and should be closed before use.

1. **saidov-adil-abukovich** (Саидов Адиль Абукович) — STRONGEST FINDING, see summary.
   Political: "Советник генерального директора", ГК «Ростех» [s3664]; "Член Бюро
   Правления", ОООР «СоюзМаш России» [s3664]; "Член Бюро", Ассоциация «Лига
   содействия оборонным предприятиям» [s3664]. Business: board member,
   `ao-uk-azimut-formerly-aeronavigatsionnye-i-informatsionnye-s` (manufacturer
   tier, source not yet pinned down — "which Azimut entity not fully confirmed");
   23.48% shareholder, АО «НИИ «Сапфир»» since Dec 2014 [s3664].
   **Assessment: genuine intermediary** — a named Rostech advisor and defense-
   industry-association board member who simultaneously holds an equity/board stake
   in a manufacturer-tier entity, all on one well-sourced record.

2. **vladimir-vadimovich-yakushev** (Якушев В.В.) — Chairman of ЦБСТ's own
   Supervisory Board, concurrently Secretary of United Russia's General Council and
   First Deputy Chairman of the Federation Council. **Data-quality gap**: this
   `roles[]` entry has `entity_slug: null` and `source_id: null` — the free-text
   `notes` field cites er.ru's own site confirming the ЦБСТ tie independently, but
   that citation was never formalized into the structured role record, so he did not
   surface in the strict entity-tie scan and is not counted among the 11. Flagging
   here because he is, on the numbers alone, the single most senior sitting
   political figure with a documented governance seat at the network's core body —
   **this record needs `entity_slug`/`source_id` backfilled onto the existing role
   before it can be cited as a formal intermediary tie.**

3. **andrey-bezrukov** — Chairman of the Board, ЦБСТ itself [role has `entity_slug`
   but `source_id: null`]; "Federation Council" hit came from his notes text (ex-
   illegal/SVR background, publicly reported). Business tie is to ЦБСТ core itself.
   Needs source_id backfilled; strong candidate pending that.

4. **dmitriy-peskov** — Kremlin press secretary/presidential special representative
   for digital and tech development; CEO + director, АНО «Платформа НТИ»
   (`ano-platforma-nti`, INN 7703469180, confirmed via ФНС director cross-check).
   Role source_id also null on the primary role entry. Platforma NTI is adjacent-tier
   infrastructure, not manufacturer-tier — genuine political name, but the business
   tie here is to a state-innovation vehicle, not obviously ЦБСТ-specific; treat as
   national-innovation-ecosystem overlap pending a clearer ЦБСТ link.

5. **dmitriy-vladimirovich-rubinshteyn** — General Director, ЦБСТ itself (Jul 2024–
   late 2025) [s6919]; also headed the Rudnevo UAV-technopark cluster pre-ЦБСТ
   [s6919]; concurrently director/founder of several personal LLCs (Техномост,
   Момент[о], Беркут) confirmed via ФНС cross-check. Flagged here as "генерал"
   pattern hit came from an unrelated notes string, not a real rank claim — **false
   positive on the political-keyword side**, kept in list for completeness but not
   a political intermediary; he is however the strongest **cross-tier bridge**
   figure (see Part 2).

6. **ustratov-dmitriy-vladimirovich** — General Director, Фонд поддержки
   национальных морских программ, since 30.04.2021 (role source_id null); "Ministry"
   keyword hit is generic/unconfirmed — needs a real citation before treating as a
   political tie. Low confidence.

7. **kiselev-gleb-dmitrievich** — "представитель на круглом столе Народного
   фронта" [s0560], tied to `kulibin-klub`. Weak/single-event political tie, not a
   standing post — low-priority lead.

8. **vladimirskiy-mikhail-yurevich** / **vinogradov-yuriy-aleksandrovich** — both
   Заместитель генерального директора, АНО НПЦ «Ушкуйник» [s5288]; "генерал" hit is
   a substring of a different word each time (checked — false positive, not a real
   rank claim). **Not political intermediaries; drop from this list**, kept only for
   audit-trail transparency on why the keyword scan flagged them.

9. **filippov-mikhail-gennadevich** — "Ministry" keyword hit is unconfirmed/generic
   in source text; heads `proekt-kb-arkhangel` [s5454] and is 80% founder of
   `ooo-arkhangel-grupp` [s5474], both manufacturer-tier Архангел-network entities.
   Political claim not solid enough to cite yet — needs a real source before use.

10. **rogozin-dmitriy-olegovich** — self-described "флагман движения" for
    `ooo-hab-svo` (Проект «Архангел»), and personally cross-posted an Архангел
    recruitment announcement with endorsement framing [s6912, s6915]. "Federation
    Council" keyword is a false positive (matched an unrelated string, not a real
    seat claim — verify before use). Business tie is real and sourced; political
    claim is not — do not cite him as a Federation Council figure without new
    sourcing.

11. **nikiforov-anton-sergeevich** — First Deputy General Director, `ooo-aeromaks`
    [s4571]. "генерал" hit is a substring false positive (part of "генеральный"
    somewhere in text) — **not a political tie**, drop.

**Net read on Part 1**: after discounting substring false positives (items 5, 8,
11) and unconfirmed keyword hits (6, 7, 9, 10), only **items 1–4 are real,
sourceable political-affiliation-plus-business-tie candidates**, and only #1
(Saidov) currently has a fully source_id-backed claim on both sides. #2–4 (Yakushev,
Bezrukov, Peskov) are genuine, well-known political figures with a real ЦБСТ-network
tie, but their own registry role records are missing `source_id` — a data-quality
fix, not a new-lead problem, and should be the first thing done before any of them
is written up as a formal "political intermediary."

## Part 2 — Cross-tier bridge figures (from the 102 people with a completed ФНС
other_entities sweep; not necessarily political)

13 people hold roles or ФНС-confirmed director/founder ties spanning two or more
different registry `tier` values. Full list (entity/tier pairs from live registry
data, no missing sourcing on the tie itself since these come from `other_entities[]`
or a sourced `roles[]` entry):

- **dmitriy-vladimirovich-rubinshteyn** — cbst-core (ЦБСТ itself, two Спецтех
  subsidiaries) + unverified-tier personal LLCs (Беркут, Техномост, Момент[о]).
  **Strongest bridge figure in the dataset**: simultaneously ran ЦБСТ's own
  operating apparatus and a cluster of personally-held LLCs.
- **barashkov-aleksandr-sergeevich** — manufacturer (`ooo-gagaring`) + plumbing
  (`ano-arrs-krasnodar`) — Гагаринг/АРРС Краснодар network, already flagged in
  prior PII-amendment work on Архангел-adjacent training networks.
- **garkusha-vladimir-vladimirovich** — manufacturer (`ooo-promsintez`) + plumbing
  (`ooo-gk-logos`), plus a wide personal LLC footprint (Атаман, Логос Холдинг,
  Логос-Ярославль, Новатор, Протон Холдинг, Сармат, Эластохим, Легион, НПП Эталон)
  — largest personal-entity footprint of anyone in this scan; worth a dedicated
  look regardless of political status.
- **sokolov-german-olegovich** — manufacturer (`ooo-npo-rustekhdron`) + plumbing
  (`ooo-rtd-zashchita`).
- **pospekhov-ivan-aleksandrovich** — manufacturer (`ooo-metaskan`) + plumbing
  (`ooo-tsyus`).
- **khuteshen-aleksey-aleksandrovich** — manufacturer (Атлант Аэро cluster, 3
  entities) + adjacent-tier (8 entities: Оптические системы, Аметист, Атлант
  Логистик, Атлант Сервис, Эверест, НПК Зевс, ПК Стальной Купол, Пром-Тех) —
  largest cross-tier entity count of anyone in this scan (11 total).
- **begak-aleksandr-arkadevich** — plumbing (НП «Дискретно-инновационный кластер
  малой авиации») + manufacturer (`ooo-akr-begak`).
- **rogozin-aleksey-dmitrievich** — manufacturer (`ao-ekolibri`, chairman of
  advisory council) + plumbing (`ano-tsentr-razvitiya-transportnykh-tekhnologiy`,
  director) — also director, Союз авиапроизводителей России (industry-association
  tie, not in registry).
- **galaev-ilya-viktorovich** — manufacturer (РусТехДрон/РТД-Защита, per iStories,
  not yet EGRUL-confirmed for current filing) + plumbing + adjacent (ФГДР —
  Федерация гонок дронов России, EGRUL-confirmed presidency).
- **rudenko-dmitriy-aleksandrovich** — adjacent (АНО «Невский центр научного
  сотрудничества») + manufacturer (БТР — Беспилотные технологические решения,
  Спецмат).
- **timofeev-vladimir-sergeevich** — manufacturer (`ooo-arkhangel-zaporizhzhie`) +
  adjacent (`ooo-arkhangel-crimea`) — Архангел-network occupied-territories cluster.
- **filippov-mikhail-gennadevich** — manufacturer (Архангел Групп, КБ Архангел) +
  adjacent (`ooo-ml-konstrakshns`).
- **stepanov-valeriy-yurevich** — adjacent (`ooo-ds-bars-t`) + manufacturer
  (`ooo-ik-aviaok`).

## Part 3 — Telegram co-occurrence (informal corroboration only, local DB scan,
surname LIKE-matched against posts containing ЦБСТ/CBST/Единая Россия — NOT a
citable source, triage signal only)

Reliable hits (real distinct surnames, not patronymic false positives):
- **Безруков** (andrey-bezrukov) — 179 posts
- **Якушев** (vladimir-vadimovich-yakushev) — 35 posts
- **Рубинштейн** (dmitriy-vladimirovich-rubinshteyn) — 34 posts
- **Песков** (dmitriy-peskov) — 5 posts

All four are already-known, well-documented figures (items 1–4/5 above) — the TG
signal corroborates rather than surfaces anything new. Everyone else's "hits" were
patronymic-string false positives (e.g. "Александрович", "Сергеевич" matched as if
a surname) and are not reported as real corroboration.

## Part 4 — Not-yet-ФНС-checked people (258 total) worth prioritizing for a future
`screen_upr_uchr.py` run (that sweep itself is a live-network job, NOT run here —
hand to the user per the crawling-jobs policy)

Keyword-scanned the 258 unchecked records' existing `roles[]`/`notes` text only (no
network call). 5 look like plausible intermediary candidates worth running first:

1. **dmitriy-medvedev** — "Chairman, United Russia; Deputy Chairman, Security
   Council" (role has no entity_slug/source_id — top-tier political figure, no
   confirmed formal registry-entity tie yet; worth checking whether he has any
   personal director/founder footprint at all).
2. **rogozin-dmitriy-olegovich** — already has a sourced Архангел business tie
   (Part 1 #10); ФНС sweep would surface any other personal entities.
3. **nikiforov-anton-sergeevich** — already has a sourced Aeromaks tie; worth a
   check for completeness.
4. **ganysh-v-p** — "Начальник управления информационных технологий и связи,
   полковник внутренней службы, ГУ МЧС России по Курской области" — a named
   security-service-adjacent official with no business tie on file yet; worth
   checking if this is even a full ФИО (name field is null — identity may need
   resolving before a meaningful ФНС search is even possible).
5. **savvin-a-a** — "Начальник, генерал-майор, ФГКУ «Центр... «Лидер»»" — same
   caveat: no `fio_ru`, name field null, ФНС search not meaningfully possible until
   the identity is resolved.

Note: ganysh-v-p and savvin-a-a are effectively unusable for a name-based ФНС sweep
until someone resolves their full ФИО — flagging as a name-resolution gap, not a
screening-priority gap.

## Part 5 — Follow-up on Part 2's cross-tier bridge figures (main session, 2026-09-15)

Checked all 13 Part-2 candidates individually rather than trusting entity-count alone.
Result: most of the "extra" entities are generic personal-business diversification
(commercial chemical trading, courier/logistics franchises, real-estate holding,
legal services) with no UAV/defense/ЦБСТ relevance — not genuine ecosystem bridges.
Two concrete outcomes:

1. **dmitriy-vladimirovich-rubinshteyn** — his «Беркут» role note said "ИНН not yet
   identified, open lead," but the 2026-09-07 ФНС cross-check (other_entities[]) had
   already resolved it (ИНН 9709100837, matching the already-registered
   `ooo-berkut-dmv`). Stale-note fix applied via corrections_people.json.

2. **pospekhov-ivan-aleksandrovich** (director/founder, `ooo-metaskan` +
   `ooo-tsyus`, both already registered) — **RESOLVED 2026-09-15, closed, not
   wired.** ООО «Системы Безопасности» (ИНН 5001160158, OKVED 26.11) turned out
   to be a personal shell/holding vehicle: full EGRUL выписка pulled (s7520)
   shows Поспехов as 100% sole owner AND director, statutory-minimum charter
   capital, and 38 additional catch-all ОКВЭД codes spanning unrelated retail/
   IT/accounting/transport/construction activity — the same discount pattern
   as every other Part-2 bridge-figure candidate. No product/patent/UAV signal
   found. See the full reasoning in `corrections_people.json`'s
   `pospekhov-ivan-aleksandrovich` entry.

Everyone else's extra other_entities[] hits (Гагаринг's Барашков → СДЭК courier
franchise + a charity fund; Гаркуша's 9-entity chemical-trading cluster; Тимофеев's
trucking company; Степанов's real-estate holding companies) were checked and are
genuinely unrelated personal business activity — not wired, and not flagged for
further follow-up.
