# smolin.info source catalogue (Ushkuynik network, 2 articles)

Built 2026-09-02 after the user flagged that the initial retrace only pulled
the 17 embedded downloadable primary documents (`kg-file-card` blocks) and
missed the much larger apparatus of secondary/corroborating links both
articles cite inline. This file catalogues everything else found in the two
archived pages so it doesn't get lost again.

Source pages: `s5288` (TRANSCRIPT_20260608_smolin-info-ushkuynik-investigation.html)
and `s5291` (TRANSCRIPT_20260608_smolin-info-dronovaya-tsepochka-rashizma.html).

## Primary documents (kg-file-card downloads) — all now archived

17 total, all pulled and wired into `data/registry/`:
- Article 1 (`s5288`): 12 files — s5292–s5303 (Minpromtorg BAS program, Demyansk
  decree 838, SDM tender notice+protocol, 5 EGRN extracts, 3 EGRUL extracts
  incl. ooo-btr-donetsk).
- Article 2 (`s5291`): 5 files, **initially missed, pulled 2026-09-02** —
  s5304 (Христюк Е.В. EGRN), s5305 (Христюк В.В. EGRN), s5306 (Прокофьев М.В.
  EGRN), s5307 (ООО «Скай авиа групп» EGRUL — precise address ул.
  Константиновская 8 г. Петергоф, wired into `ooo-skay-avia-grupp`), s5308
  (ООО «Герон» EGRUL — precise address ул. Красноармейская 71 г. Боровичи,
  wired into `ooo-geron`).

## Corporate/legal-registry cross-references — worth checking directly

| Link | Article | Context |
|---|---|---|
| checko.ru/company/npk-cpt-1265300000470 | s5288 | ООО «НПК ЦПТ» — matches our registry ИНН |
| checko.ru/company/btr-1247800059980 | s5288 | ООО «БТР» — matches |
| checko.ru/person/531501307291/timeline | s5288 | a Живова-adjacent ИНН (531501...) — check against зhivova-elena-vyacheslavovna (531501384786) |
| checko.ru/company/1147847241464/timeline | s5291 | ООО «Скай авиа групп» — matches OGRN |
| checko.ru/company/1217800073545/timeline | s5291 | ООО «Герон» — matches OGRN |
| checko.ru/company/1197847033218/timeline | s5291 | **not yet identified** — unlinked OGRN, needs lookup |
| fedresurs.ru/sfactmessages/6E1ADA1909794B6E9F5B048E505D2729 | s5291 | bankruptcy/insolvency fact message — unread |
| fedresurs.ru/sfactmessages/9C5449018C274B47A14635AD4E65801E | s5291 | bankruptcy/insolvency fact message — unread |
| kad.arbitr.ru/Card/2d9eda64-518a-45b8-a762-000e25a82904 | s5291 | arbitration case card (kad.arbitr.ru itself is DDoS-Guard-blocked to scripts — see memory `kad_arbitr_ru_ddos_guard_blocked`, manual browser check only) |
| novgorod.arbitr.ru/material/369364 | s5291 | **regional arbitr.ru subdomain — may not be DDoS-Guard-blocked like kad.arbitr.ru itself; worth testing scripted access separately** |
| 1zovs--spb.sudrf.ru case (case_id=1884603) | s5291 | a St. Petersburg district court case — general-jurisdiction courts (sudrf.ru), different portal than arbitr.ru, not yet tested for scriptability |

## Named individuals surfaced via myrotvorets.center links — not yet in registry

myrotvorets («Миротворец») is a Ukrainian crowdsourced database of alleged
Russian-military/occupation-linked individuals — a lead source, not a
primary source; anyone pulled from here needs independent EGRUL/EGRN
corroboration before being added with PII per project policy.

New names appearing in these links that are **not yet people.json entries**:
- **Пегов Семён Владимирович** (founder of WarGonzo, cited in s5291 — likely
  cited as a media/context reference, not necessarily an Ushkuynik-network
  principal; check the actual paragraph before adding)
- **Аширов Ярослав Олегович** (s5291, context unread)
- **Басюк Константин Владимирович** — a sitting senator per TASS
  (tass.ru/encyclopedia/person/basyuk-konstantin-vladimirovich), cited s5291,
  context unread — could be a name-collision/comparison reference rather
  than a direct tie
- **Заяц Светлана Степановна** (s5291, context unread)
- **Стриж Ульяна Валерьевна** (s5291, context unread)
- **Орлов Евгений Вячеславович** (s5291, context unread)
- **Бильченко Евгения Витальевна** (s5288, context unread — appears near
  Владимирский family cluster)
- **Владимирская Нина Леонидовна** (s5288 — likely a relative of
  Владимирский М.Ю., same surname cluster)
- **Владимирский Александр Юрьевич** (s5288 — likely a relative of
  Владимирский М.Ю., same surname cluster, possibly a brother given shared
  patronymic)

Already-registered names also cross-referenced via myrotvorets in these
articles (no action needed): Чадаев А.В., Владимирский М.Ю., Елисеев Д.Н.,
Малевич П.В., Руденко Д.А., Живова Е.В., Виноградов Ю.А., Прокофьев М.В.,
Христюк Е.В., Христюк В.В., Яценко В.В., Жигулин А.М.

**Before adding any of the 9 new names**: re-read the actual surrounding
paragraph in `s5288`/`s5291` to establish the claimed relationship to the
Ushkuynik network (family member, business associate, unrelated
comparison/reference) — myrotvorets link presence alone doesn't establish
relevance, only that the author flagged the name somewhere in the piece.

## Press citations (secondary corroboration, not primary)

- t.me/wargonzo/30716, t.me/novgorod_tv/21018, t.me/sotavisionmedia/56127 —
  Telegram press channel posts
- novvedomosti.ru/news/economy/106460/ — regional business press
- tass.ru/armiya-i-opk/26122579, tass.ru/ekonomika/26122897,
  tass.ru/ekonomika/24256169 — TASS wire pieces, context unread
- kp.ru/online/news/6759421/ — Komsomolskaya Pravda

## Other entity-adjacent links worth a look

- **geronavia.ru** (and /Courses.html) — ООО «Герон»'s own site, not yet
  scanned the way nvgushkuynik.ru was (site/marketing-copy scan pending)
- pd.rkn.gov.ru/operators-registry/operators-list/?id=78-24-066334 —
  Roskomnadzor personal-data-operator registry entry for one of the
  entities/individuals in article 2 — confirms formal registration as a
  PD operator, unread which entity it's for
- pureportal.spbu.ru profile — an SPbU academic publications page, likely
  tied to Чадаев or another academic-affiliated principal
- szgmu.ru/rus/m/3920/ — North-Western State Medical University page,
  context unread

## Deliberately not catalogued individually: the doxxing-scale apparatus

The two articles collectively cite **~223 social-media links (vk.com, ok.ru,
instagram, tiktok, my.mail.ru, telegram, whatsapp, phone numbers) and ~96
archive.is snapshots** of those profiles, plus ~15 employment/CV-site links
(superjob.ru, trudvsem.ru, novjob.ru, finder.work). This is smolin.info's
own person-identification methodology (matching phone numbers across
platforms to unmask real identities behind corporate front-people) — useful
as a *methodology reference* but not something to catalogue link-by-link
here: per the PII policy in CLAUDE.md, full contact-detail/social-profile
harvesting is reserved for confirmed PEPs/network principals, not applied
wholesale to every name that crosses a phone-number-matching pass. The raw
HTML (`s5288`, `s5291`) is archived in `data/sources/` and can be re-parsed
for a specific individual's social footprint if and when that person is
confirmed as a principal worth the fuller PII treatment.

## Originating-platform verification pass (2026-09-02)

The user flagged that we'd only checked smolin's re-hosted PDF copies, not
the actual originating platforms the SDM tender and the Demyansk decree
claim to have been published on. Checked directly:

- **zakupki.gov.ru ЕИС, извещение №32515497957** — CONFIRMED live and
  genuine. `https://zakupki.gov.ru/223/purchase/public/purchase/info/
  common-info.html?regNumber=32515497957` 301-redirects to
  `/epz/order/notice/notice223/common-info.html?regNumber=...` (an SPA
  shell); the server-rendered print form is at
  `/epz/order/notice/notice223/printForm/view.html?purchaseNoticeGuid=
  deb33584-184a-4db7-b26c-6f7de4be353f&purchaseNoticeNumber=32515497957`
  — full match on customer name/address (173003, Великий Новгород, ул.
  Лазаревская, д.11, помещ.105), contact (Владимирский М.Ю.,
  ushkuynick53@yandex.ru), price (₽6,332,500), and subject. Both pages
  archived: `data/sources/ZAKUPKI_5300010714_20260902_notice-32515497957-
  common-info.html` and `...-printform.html` (`s5309`/`s5310` range —
  check `sources.json` for exact ids after the next extract run).
  **Access notes for future zakupki.gov.ru work**: plain
  `curl -k` 404s on the `/223/purchase/...` path — it 301-redirects to
  `/epz/order/notice/notice223/...`; follow the redirect, don't treat the
  first 404 as a dead link. A real browser `User-Agent` is required (a
  bare curl UA also gets rejected).
- **utp.sberbank-ast.ru (the commercial trading platform itself)** —
  unreachable: `curl` times out connecting to 193.104.207.121:443 from
  this sandbox network. Same class of failure as kad.arbitr.ru (see memory
  `kad_arbitr_ru_ddos_guard_blocked`) — likely blocks non-Russian IPs
  outright rather than DDoS-Guard-style bot detection, but the practical
  effect is the same: no scripted access, manual browser check only if
  ever needed. Not fatal here since zakupki.gov.ru's ЕИС mirrors the same
  notice by law (223-ФЗ requires dual publication) and was independently
  confirmed above.
- **demadmin.gosuslugi.ru (Демянский район's actual official site)** —
  CONFIRMED to be the real, live district administration portal (a
  gosuslugi.ru-hosted municipal site), with a genuine normative-acts
  archive at `/ofitsialno/dokumenty/postanovleniya/postanovleniya-2023-
  goda/` (449 documents for 2023, organized by category/year, matching the
  decree's own self-citation: "Опубликовать постановление ... и разместить
  на официальном сайте"). **Could not pin the exact deep-link to
  постановление №838 within this pass** — the archive's listing is
  reverse-chronological and its pagination didn't respond to a `?page=N`
  query param through WebFetch (likely needs real click/JS interaction,
  not a plain GET). smolin.info's re-hosted copy (`s5300`) remains the
  working citation; the document's own digital signature (cert serial
  07FC71FBD0E958D12254F84B9CF62082, signer Сапогов А.Н., глава района,
  15.09.2023 09:58) already gives it strong authenticity independent of
  where it's hosted. A manual browser search of that archive page for
  №838 would close the loop if a direct government-hosted copy is wanted.

## Process note for future smolin.info (or similar Ghost-CMS) pieces

`div.kg-file-card` blocks are the *downloadable-primary-document* markers,
but a full retrace also needs the plain inline `<a href>` citations —
BeautifulSoup over the whole page, filtered to non-smolin/non-share-button
hosts, not just the file-card selector. The mismatch this time: 12 file-cards
were caught in article 1, but article 2's own 5 file-cards were skipped
entirely on the first pass — worth defaulting to "parse every kg-file-card
across every archived companion article," not just the first one opened.
