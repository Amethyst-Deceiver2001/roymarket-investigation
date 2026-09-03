# Source-expansion methodology (started 2026-09-02)

Origin: the smolin.info retrace showed that checking a document's *actual
originating platform* (zakupki.gov.ru's own ЕИС, a district's own official
site) instead of trusting a re-hosted copy both confirms authenticity and
sometimes surfaces more detail than the copy carried. The user asked to
generalize this beyond Ushkuynik and beyond zakupki.gov.ru to the whole
registry: other procurement portals, federal/regional program founding
docs, local government decree archives, and court portals.

This file tracks portal-by-portal accessibility findings (so nobody
re-discovers the same block/workaround twice) and the prioritized entity
backlog for applying the practice.

## Portal accessibility findings

| Portal | Status | Notes |
|---|---|---|
| **zakupki.gov.ru** (ЕИС, both 44-ФЗ and 223-ФЗ) | **WORKS** | See `zakupki_gov_ru_contract_search_api` memory for 44-ФЗ `supplierTitle` search. For a known 223-ФЗ `regNumber`: `/223/purchase/public/purchase/info/common-info.html?regNumber=N` 301-redirects to `/epz/order/notice/notice223/common-info.html?regNumber=N` (SPA shell — has the reg number but not much else server-rendered); the real content is the print form, found via a `href` in the SPA-shell HTML matching `printForm/view.html?purchaseNoticeGuid=<GUID>&purchaseNoticeNumber=N` — that page IS server-rendered and gives customer name/address/contact/price/subject in full. Needs a real Chrome UA; plain curl UA 404s. |
| **utp.sberbank-ast.ru / www.sberbank-ast.ru** (the commercial 223-ФЗ trading platform itself) | **SOLVED via HAR capture 2026-09-02, more powerful than zakupki for this** | Real search API: `POST https://www.sberbank-ast.ru/api/Processing/main` with JSON body `{"windowCode":"/EsOpenUnitedPurchaseList","actionType":"MONITOR","actionCode":"default","documentBody":"","parm":"es","filterBody":"<query>...<mainInput>SEARCHTERM</mainInput>...</query>","options":{}}` — an Elasticsearch-backed full-text search. **No auth/cookies needed** — just `Content-Type: application/json`, `Origin: https://www.sberbank-ast.ru`, `Referer: https://www.sberbank-ast.ru/UnitedPurchaseList.html`, a real UA. Confirmed live outside the HAR capture session (i.e. reusable, not session-bound). **Important**: `mainInput` matches free text (purchase name / org name) and an exact ЕИС `regNumber`, but does **NOT** match a plain ИНН — searching an org's ИНН alone returns 0 hits even for known-positive cases; search by the org's **name text** instead. First real use: searching "Ушкуйник" surfaced **11 procurement notices totalling ~₽200.17M (Aug–Dec 2025)**, of which only 1 (the already-known SDM equipment purchase) had been documented — the other 10 (~₽193.8M) were a completely new find, describing a full manufacturing-facility buildout (CNC machining, injection molding, waterjet, EDM, laser cutting/welding, paint-drying, a materials-testing lab). See the `ano-npts-ushkuynik` `government_contracts[]` `why[]` note (source `s5313`) for full details. **This is now a standing check to run against every priority entity's name** — it found more in one search than the entire prior zakupki-based pass for this one entity. The `filterBody` XML's `<publicDate>` range should be widened (e.g. `startPublicDate=01.01.2015`) since the captured example defaulted to a narrow recent window. |
| **kad.arbitr.ru** (arbitration case database) | **Partially unblocked via WireGuard RU tunnel (2026-09-02)** | Originally confirmed dead (DDoS-Guard reject, see memory `kad_arbitr_ru_ddos_guard_blocked`). After routing through a Russian-exit WireGuard tunnel (`AllowedIPs` extended with `185.129.103.0/24`), the IP-level DDoS-Guard block clears — a case-card URL now returns the *site's own* "pravocaptcha" challenge page instead of a DDoS-Guard rejection. This is real progress (reachable at all) but the captcha itself is interactive (image/audio, has a lockout timer on repeated failures) and not scriptable — still needs a human in an actual browser to solve it per lookup. Not a path to batch/automated case lookups; usable for one-off manual verification of a specific case now, which it wasn't before. |
| **ras.arbitr.ru** (Банк решений арбитражных судов — full-text decision bank) | **BLOCKED at the API level even over the RU tunnel** | Homepage (`GET /`) returns HTTP 200 with real HTML. Its search backend (`POST /Ras/Search`) returns **HTTP 451 "Доступ заблокирован"** both with and without the WireGuard tunnel — confirms this block is behavioral/fingerprint-based, not geo-IP, so a VPN alone doesn't fix it. Don't retest this via IP-routing changes again; a different approach (real browser automation, or a request-signature match) would be needed. |
| **\<region\>.arbitr.ru** (a regional court's own site, e.g. novgorod.arbitr.ru) | **WORKS, but it's not the case database** | `novgorod.arbitr.ru/material/NNNNNN` (news/press-release URLs) return real HTML directly, no JS needed. Useful only for the court's own news/announcements (new judge appointments, etc.), NOT for looking up a specific case — the "Картотека арбитражных дел" link on these regional sites points straight back to the blocked kad.arbitr.ru. |
| **torgi.gov.ru** (official state/municipal property & asset sales register) | **Reachable but SPA shell** | `GET /new/public` returns HTTP 200, `<title>Торги</title>`, no server-rendered listing content. Needs its backend API found — likely via a HAR capture the way zakupki's `supplierTitle` param was found (see `zakupki_gov_ru_contract_search_api` memory for that precedent). Not yet attempted. |
| **bus.gov.ru** (budget-institution financial/procurement disclosure portal) | **Reachable (301), untested past that** | `/pub/agency` redirects (301), not yet followed through to confirm real content or find its API. Likely only relevant for state/municipal budgetary institutions (ФГУП/ГБУ/etc.) — most registry entities are ООО/АО/АНО, so check applicability per-entity before spending effort here. |
| **fedresurs.ru** (Федресурс — bankruptcy/corporate-fact disclosure register) | **SOLVED via HAR capture 2026-09-02 — two API layers found, second is much more powerful** | **Layer 1** (single-message lookup): `GET https://fedresurs.ru/backend/sfact-messages/<GUID>` — plain JSON, no auth, just a `Referer: https://fedresurs.ru/sfactmessages/<GUID>` header and a real UA. GUID works dashless-uppercase or hyphenated-lowercase. A `/signature` sub-path exists, not yet explored. **Layer 2** (full company lookup, found via a second HAR capture searching fedresurs.ru's own UI for an ИНН): `GET /backend/companies?searchString=<ИНН>&limit=15&offset=0&isActive=true` → returns a company **GUID**, then `GET /backend/companies/<GUID>/{main,bankruptcy,publications,networth,licenses,encumbrances,reorganizations,sro,act-type-groups,ieb}` — each a structured endpoint (`bankruptcy` lists every intent/filing message with its own GUID+date+type; `encumbrances` lists leases/pledges by group; `publications` is the full chronological feed of every fact-message touching the company). **No auth needed for any of these either.** This is a genuine universal company-lookup tool, not just a bankruptcy-notice reader — worth running against every priority-backlog entity's ИНН, not only ones already known to be in distress. First real use (ООО «Герон», ИНН 7802893898) found: 2 more Sberbank-initiated bankruptcy-intent notices beyond the already-known УФНС filing (3 creditors circling within 10 weeks), an EGRUL "Недостоверность сведений" (unreliable-information) flag from 11.03.2026, and a 2024 vehicle-lease record naming the lessee as **«ООО «Герон-Авиа»»** (same ИНН/ОГРН — confirms the geronavia.ru site tie) whose **lessor's identity is redacted under Постановление Правительства РФ №5 от 12.01.2018** (the decree shielding defense-industry/gosoboronzakaz entities from public disclosure), with Fedresurs's own system flagging both parties `isPublisherInSanctionList`/`isParticipantInSanctionList: true` (flagged as Fedresurs's own classification in the registry note — not independently verified against a specific primary sanctions list). All wired into `ooo-geron` (sources `s5314`–`s5324`). |
| **navigator.sk.ru** (Сколково resident directory) | **BLOCKED by a JS challenge, unaffected by the RU tunnel** | Tested both without and with the WireGuard RU tunnel — identical `servicepipe.tech` JS-challenge response both times (same byte size). Confirms this specific block is a browser-fingerprint/JS-execution check, not geography. Same category as ras.arbitr.ru: don't retry via IP-routing again. |

| **rts-tender.ru** (official 44/223/615-ПП platform, and — importantly — a cross-platform aggregator) | **SOLVED via HAR capture 2026-09-02, best organizer-search yet** | Hits its own "Anti-DDoS защита" JS-challenge page on a plain fetch (unaffected by IP/VPN routing, confirmed), but **a real browser session captured in a HAR gets through it** and the resulting cookies/requests are what matter. Real organizer search: the search POST body supports a direct `"innOrganizers":"<ИНН>"` filter field (unlike Sberbank-AST, which only matches free text) — found via `www.rts-tender.ru/poisk/organizator/<ИНН>-<КПП>/`. Crucially, **RTS-Tender indexes tenders run on OTHER platforms too** (confirmed: it lists Ushkuynik's Sberbank-AST-hosted 223-ФЗ procedures) — it's a cross-platform aggregator, not just its own listings, making it possibly the single best one-stop organizer-lookup tool of everything tried so far. First real use (Ushkuynik, ИНН 5300010714) returned a 10-result organizer page giving the **actual signed contract price** for 9 of the 11 equipment purchases already found via Sberbank-AST — each lower than the opening NMC (competitive-bidding discount, up to ₽15.7M less on the largest purchase) — plus the real ЕИС closing-notice numbers and 20-digit EIS contract registration numbers. List appears paginated at 10 (`skip`/`top` in the filter body) and date-sorted descending; a page-2 capture (`skip:10`) would likely surface anything older. All wired into `ano-npts-ushkuynik`'s `government_contracts[]` as enrichment (source `s5325`). **This is now a standing check to run against the whole priority backlog** — probably before Roseltorg, since it already proved itself and directly supports ИНН search rather than requiring name-text guessing. |

### WireGuard RU-tunnel split-routing (added 2026-09-02)

The user already runs a WireGuard app with a Russian-exit tunnel (used
previously to reach zakupki.gov.ru). Extended its split-tunnel
`AllowedIPs` with three more /24s for the sites above:
`193.104.207.0/24` (utp.sberbank-ast.ru), `185.129.103.0/24`
(kad.arbitr.ru / ras.arbitr.ru — same host), `194.190.0.0/24`
(navigator.sk.ru). Result: **this fixes pure connectivity/geo-IP blocks
(utp.sberbank-ast.ru went from timeout to fully reachable; kad.arbitr.ru's
DDoS-Guard reject cleared to the site's own interactive captcha) but does
nothing for behavioral/fingerprint-based blocks** (ras.arbitr.ru's search
API still 451s, navigator.sk.ru's JS challenge is byte-identical
before/after). Useful lesson for triaging any future "unreachable" site:
check whether the failure mode is a connection timeout/geo-redirect
(VPN candidate) versus a captcha/JS-challenge/behavioral 4xx (VPN won't
help; needs either manual browser solving or a different automation
approach entirely).
| **rosreestr.gov.ru** / **nspd.gov.ru** | **WORKS** | Already in active use this session (cadastral/ownership lookups) — see the nspd.gov.ru API details in the prior conversation summary. Not re-tested here, just noting it belongs in this same "confirmed working" list. |
| **demadmin.gosuslugi.ru** (a single municipal district's own site, generalizes to any `<name>.gosuslugi.ru`-hosted local government) | **WORKS for browsing, pagination not yet scripted** | Real per-district site pattern: `/ofitsialno/dokumenty/postanovleniya/postanovleniya-<YYYY>-goda/` lists that year's decrees, organized reverse-chronologically. A `?page=N` query param did not change the WebFetch-rendered result — pagination is likely JS-driven (real click interaction), not a plain GET param. Generalizes: any entity/person tied to a specific municipality's decree should be checked against that municipality's own `<slug>.gosuslugi.ru` site using this URL pattern, not just accepted from a secondary source. |

## Not yet tested this pass (from the "additional sources" research ask)

- Other 223-ФЗ commercial trading platforms besides Sberbank-AST (B2B-Center,
  RTS-tender, Fabrikant) — only relevant if a specific entity's tender turns
  out to be hosted on one of these instead; no need to test blind.
- **Реестр аккредитованных ИТ-компаний** (Minsvyaz/Минцифры IT-company
  accreditation registry, `www.gosuslugi.ru`-based) — relevant for any
  entity claiming IT-accreditation tax benefits.
- **Реестр резидентов Сколково** (sk.ru / navigator.sk.ru) — relevant if any
  entity's `state_programs[]` or marketing claims cite Сколково residency;
  should be checked against sk.ru's own public resident directory rather
  than taken on the entity's word. **Tested 2026-09-02**:
  `navigator.sk.ru/orn/<id>` is reachable (HTTP 200 with `-k`, contrary to
  an existing `ooo-aeroplatformy` open-question note claiming it's
  unreachable due to an "expired SSL cert") but gated by a JS bot-challenge
  (servicepipe.tech) — no server-rendered profile content, needs either a
  JS-executing fetch or a HAR-based API discovery. The existing open-
  question's stated reason (expired cert) is stale/wrong; the real current
  blocker is the JS challenge. 6 registry entities mention Сколково in some
  field (`ooo-gaskar-integratsiya`, `npo-kaysant`, `ano-platforma-nti`,
  `ooo-orient-sistems`, `ooo-4gnss`, `ooo-aeroplatformy`) — worth a batch
  check once the navigator.sk.ru access question is solved.
- **Фонд содействия инновациям (ФСИ / "Бортника")**, **РНФ (Российский
  научный фонд)**, **НТИ (Национальная технологическая инициатива)** grant
  registries — each publishes its own grantee list; relevant wherever a
  `state_programs[]` entry claims a grant from one of these without a
  primary-source citation.
- **pravo.gov.ru** (official federal legal-acts publication portal) — the
  authoritative source for any cited Постановление Правительства РФ (e.g.
  the experimental-legal-regime decree found in the BAS program document
  this session) — worth checking whenever a federal-level (not municipal)
  decree is cited, as distinct from the gosuslugi-hosted municipal pattern
  above.
- **rk.2035.university** — already in active use (see memory
  `rk_2035_university_bas_registry`), belongs in this same toolkit.
- **АЭРОНЕКСТ catalog API** — already in active use (see memory
  `aeronext_catalog_api`).

## Prioritized entity backlog for a deeper originating-source pass

Ranked by `government_contracts[]` count, `litigation[]` count, and
multi-value `*_history[]` fields (signal that something changed and might
be independently verifiable) — computed 2026-09-02 from the live registry:

| Rank | slug | Name | Why prioritized |
|---|---|---|---|
| 1 | `npp-radar-mms` | АО «НПП «Радар ММС»» | 72 govt_contracts, multi-director history, 3 litigation — already this session's other carried-over thread |
| 2 | `ao-nii-stt` | АО «НИИ СТТ» | 7 govt_contracts, multi-director history, **10 litigation** — highest litigation count in the registry, strong candidate for court-portal-adjacent verification once available |
| 3 | `ao-pmts-avangard` | АО «ПМЦ «Авангард»» | 13 govt_contracts |
| 4 | `npts-elvis` | АО «НПЦ «ЭЛВИС»» | 11 govt_contracts, 1 litigation |
| 5 | `ao-tsentr-telko` | АО «Центр-Телко» | 10 govt_contracts, multi-director history |
| 6 | `ao-nii-vektor` | АО «НИИ «Вектор»» | 5 govt_contracts |
| 7 | `ovod` | ООО «Русская лаборатория воздушного транспорта» | 4 govt_contracts |
| 8 | `ano-npts-ushkuynik` | АНО «НПЦ «Ушкуйник»» | already deep-dived this session; state_programs+litigation+address history all touched |
| 9 | `ip-tsyganov-vadim-borisovich` | ИП Цыганов В.Б. | 3 govt_contracts |
| 10 | `ooo-gaskar-integratsiya` | ООО «Гаскар Интеграция» | 2 govt_contracts, multi-director history |

Full scored list (25 entities with any signal) is reproducible via the
one-off scoring script used to build this table — not checked in as a
script since it's a one-time registry query, re-run against `entities.json`
whenever a fresh prioritization is needed:
```python
# score = 3*len(government_contracts) + 2*len(state_programs) + 2*len(litigation)
#         + 1 if multi-value director_history/address_history/founders_history
```

## Pattern noticed: sanctions-shielded vehicle-lease lessors (2026-09-03)

Checking `ooo-trimiks-bulat-3mx` and `ooo-gagaring` against fedresurs.ru's
company-lookup API (see above) found Тримикс clean, but Гагаринг has **4
vehicle-leasing fact-messages (2024-2025)**, and in every single one the
lessor's identity is redacted citing Постановление Правительства РФ №5 от
12.01.2018, with Fedresurs's own system flagging both parties
`isPublisherInSanctionList`/`isParticipantInSanctionList: true` — the
*exact same signature* as `ooo-geron`'s single leasing record found the
same session. Two independent ЦБСТ-adjacent entities both routing vehicle
leases through the same category of sanctions-shielded lessor, on
different dates, is worth treating as a real pattern rather than
coincidence — **the fedresurs `encumbrances` endpoint is now a standing
check worth running against every priority-backlog entity**, not just
ones already suspected of financial distress. If a third or fourth entity
shows the same shielded-lessor signature, that's worth writing up as its
own finding (a specific defense-sector leasing company is a real,
identifiable counterparty even if Fedresurs currently hides its name to
us — the lessor itself might be identifiable through other means, e.g. the
contract-number prefix format like "КРД"/"РНД" which look like regional
codes, or by cross-referencing against known state-linked leasing firms
such as GTLK).

Also worth noting: `ooo-gagaring` underwent a **mandatory statutory audit
for FY2025** (clean opinion, `ООО «БСК Аудит»`) — a mandatory-audit
requirement under Russian law implies the company crosses a revenue/asset
threshold, so this alone is informative about scale even before pulling
the actual attached financials. The audited financial statements are
attached as a downloadable PDF on Fedresurs (`docs[].guid`) — not yet
pulled; would need a fresh HAR of the publication page in a real browser
to find the document-download endpoint (same shape as the sfact-message
API, likely `/backend/sfact-messages/<guid>/docs/<doc-guid>` or similar,
not yet confirmed).

## Production-facility identification methodology (started 2026-09-03)

Triggered by `ooo-gagaring`'s FY2025 audit report (`s5333`) disclosing a
second physical address — 350020, Краснодар, ул. Одесская, д.48/3, an
"обособленное подразделение без выделения на отдельный баланс" registered
01.12.2023 — separate from the registered legal (HQ/mailing) address. The
user flagged this as high-priority: an entity's registered legal address is
routinely a mailbox/accountant's office, but a *second, industrial-zone*
address disclosed only in an internal accounting document is a much
stronger signal of an actual production site — especially for entities
that are cagey about physical presence (Тримикс is the named comparison
case). This is the same category of document as the founding
Устав/EGRN/EGRUL extracts smolin.info cited for Ushkuynik — an official
filing that incidentally reveals ground truth the entity wouldn't
volunteer in marketing copy. **Standing instruction: whenever a
subdivision/КПП/second address turns up in *any* future БФО filing, audit
report, or founding document (not just Гагаринг), treat it the same way —
log it explicitly, don't let it get buried in a citation note.**

Sources to identify/confirm a facility once an address is in hand, roughly
in order of how much they reveal vs. how hard they are to reach:

1. **Публичная кадастровая карта** (`pkk.rosreestr.ru`) — free, no login,
   satellite + cadastral-boundary view. Given an address (or approximate
   coordinates), shows the cadastral number, plot area, and **land
   category** (e.g. "земли промышленности" vs. residential/mixed) —
   confirms "industrial area" claims visually and administratively rather
   than by inference from the street name. Not yet tested this session for
   scripted access; likely has its own tile/API layer worth a HAR capture
   if the plain UI is JS-heavy.
2. **EGRN extract (выписка из ЕГРН) for the specific plot/building** — the
   authoritative registered-owner/lessee record for a piece of real estate,
   same document type already used for Христюк/Прокофьев/etc. in the
   Ushkuynik network (see `smolin_source_catalogue.md`). Pulled the same
   way: `rosreestr.gov.ru`'s paid extract order, or a Ковристов-style
   citizen-facing portal. Confirms *who legally holds* the building at
   Одесская 48/3 — could be Гагаринг itself, a landlord entity, or a third
   party the facility is shared with.
3. **Company-search-by-address** (rusprofile.ru, checko.ru, list-org.com,
   СБИС, DaData) — the single most useful cross-check for a shared
   industrial site: lists *every* legal entity registered at a given
   street address, which is exactly how a facility shared between Гагаринг,
   Тримикс, and others (if that's the case) would surface. **Tested
   2026-09-03: rusprofile.ru's search endpoint doesn't accept a plain query
   param (404/no results via curl), list-org.com 403s a bare curl request**
   — both look like the JS-challenge/session-cookie pattern already solved
   for Sberbank-AST/RTS-Tender/Fedresurs this session, not a hard block.
   **Needs a DevTools HAR capture of an address search on one of these
   sites** (rusprofile.ru's "поиск по адресу" or checko.ru's equivalent) to
   find the real API — same recipe as `zakupki_gov_ru_contract_search_api`.
   This is the highest-value next capture: one working address-search API
   would let every registry entity's known address be swept for
   co-located, currently-undiscovered entities in one pass, not just
   Тримикс.
4. **2ГИС / Яндекс.Карты организации** — business-directory listings tied
   to a street address; often surfaces companies operating from a location
   without being registered there (a common gap company-registry lookups
   alone miss — a production line can run under a landlord's or a
   different legal entity's roof). Worth checking directly in a browser;
   not yet tested for scripted access.
5. **Krasnodar city/krai government decrees** — `krd.ru` (Краснодар city
   administration's own portal, not gosuslugi-hosted) and
   `admkrai.krasnodar.ru`/regional equivalents publish normative acts on
   industrial-park/technopark designation, land allocation, and investment-
   zone status — the krai-level analogue of the Demyansk district decree
   smolin cited for the Ushkuynik network. Relevant if Одесская 48/3 turns
   out to sit inside a designated industrial/technopark zone (would also
   explain any subsidy/state_programs eligibility, like the 3DLAM Mid
   equipment subsidy already found).
6. **proverki.gov.ru** (реестр проверок — inspections registry) — logs
   Rostrud/Rospozharnadzor/etc. inspections by legal entity and address;
   an active production site is more likely to show up here than a mailbox
   address, since safety/labor inspections target actual workplaces.
7. Historical satellite imagery (Yandex/Google) for the coordinates, once
   pinned via the cadastral map — useful for dating when a building
   appeared/expanded, cross-checkable against `workforce_history[]` growth
   (Гагаринг's own headcount jumped 34→105 in 2025, which a facility
   expansion timeline could corroborate or contradict).

**Immediate next action recommended**: a DevTools HAR of rusprofile.ru or
checko.ru's address search (item 3) is the highest-leverage single capture
— unlocks facility-colocation checks for every address already in the
registry, not just this one.

## Recommended next steps (not yet started)

1. **HAR-capture torgi.gov.ru and fedresurs.ru** the same way zakupki's
   `supplierTitle` param was found (see `zakupki_gov_ru_contract_search_api`
   memory for that precedent) — these are real, reachable portals blocked
   only by not knowing the API, not by anti-bot measures, so a HAR unlocks
   them cleanly. fedresurs.ru is especially worth it since 2 real fact-
   message GUIDs are already sitting unread in the smolin catalogue.
2. Work down the prioritized entity backlog above, starting with
   `ao-nii-stt` (highest litigation count) once a court-portal option
   exists, or `npp-radar-mms` (already the other active thread this
   session) for its zakupki-based government_contracts.
3. For any entity with a `state_programs[]` claim not yet backed by a
   `source_id` pointing to the *program's own* registry (Сколково residents
   list, НТИ/ФСИ/РНФ grantee list), check that program's own public
   directory rather than trusting the entity's self-report.
