# Source register — every registry/database an entity should be checked against

**Created 2026-09-05.** Companion to `scripts/coverage_report.py`. That script
answers *"which entities have we checked?"*; this file answers *"checked against
**what**, and can we do it ourselves?"*

The 2026-09-05 coverage audit that produced both — including case-study
candidates, the manual-task queue and a staged cutoff plan — is published at
https://claude.ai/code/artifact/8957e376-c07c-4c06-bddf-13bead303b99
(a working document, not the `docs/index.html` brief companion, which still
republishes only at an explicit investigation cutoff).

**Why this exists.** Three times in one session (2026-09-05) an entity already
fully covered in `data/registry/` was reported as an uncovered gap, because
"have we checked X?" was answered from memory instead of from data. The
registry itself fixes the per-entity half of that. This file fixes the other
half: the set of sources is now written down with an explicit access tier, so a
source is never silently forgotten, and "the user has to do this one" is a
recorded property rather than a thing rediscovered each session.

## Access tiers

| Tier | Meaning | Policy |
|---|---|---|
| **A** | Plain `curl`/`requests`, no captcha, no session | Scriptable. Single lookups inline; full-roster sweeps handed to the user per CLAUDE.md's crawling-jobs policy. |
| **B** | Needs a real browser (WAF/Qrator/JS-rendered); works via chrome-devtools | Inline reconnaissance only. Not batch-scriptable — one entity at a time. |
| **C** | Captcha-gated, login-gated, or legally blocked | **User-only.** Do not attempt to automate; put it on the manual-task list. |
| **D** | No route found from this environment | Note and move on; user should re-test from their own network before we call it dead. |

Probe date for every "confirmed" status below: **2026-09-05**, from this
sandbox. Tier D especially is environment-dependent — a timeout here is not
proof the site is down for the user (cf. `kad_arbitr_ru_ddos_guard_blocked`,
which *was* confirmed from both sides and is genuinely dead).

**Full sweep re-run 2026-09-05 (later same day), after the user put this
sandbox's egress behind a WireGuard tunnel.** Network-layer reachability
changed for most former Tier D entries; captcha/WAF-layer blocks (the actual
Tier C boundary) did not, because a tunnel changes the IP a request comes
from, not whether a site's bot-defense or login wall lets that request
through. One exception cuts the other way: **fedresurs.ru still hard-403s
this sandbox specifically** (`IP: 94.242.50.158` in its own error page) even
though the user's own browser opens it fine — my chrome-devtools browser
runs on this sandbox's network, not through the user's tunnel, so a
site-specific IP-reputation block on this exact address is not something a
tunnel on the user's device can fix from here.

---

## Tier A — scripted, already integrated

| # | Source | What it gives | Tool | Coverage field |
|---|---|---|---|---|
| 1 | egrul.nalog.ru (open lookup) | name/ИНН/ОГРН/director/region | `egrul_batch_pull.py` | `inn`,`ogrn`,`director` |
| 2 | egrul.nalog.ru (full выписка) | founders+shares, capital, ОКВЭД list, address, ГРН history | `egrul_vypiska_pull.py` | `founders`,`capital`,`okved` |
| 3 | egrul.nalog.ru ЕГРИП | individual-entrepreneur registrations (people) | `screen_egrip_ip.py` | people-side |
| 4 | bo.nalog.gov.ru (ГИР БО) | signed annual accounts (balance, P&L) | `bfo_pull.py` | `bfo` |
| 5 | ФНС дисквалифицированные лица | director disqualification | `screen_disqualified.py` | people-side |
| 6 | ФНС субсидиарная ответственность | subsidiary-liability findings | `screen_subsidiary.py` | people-side |
| 7 | ФНС упр./учр. cross-reference | other directorships/foundings | `screen_upr_uchr.py` | `other_entities` |
| 8 | ФНС обеспечительные меры | tax-security measures | `screen_rom.py` | `securing` |
| 9 | zakupki.gov.ru (44-ФЗ contracts) | state contracts + attachments | `zakupki_batch_pull.py` | `zakupki` |
| 10 | OpenSanctions API | consolidated sanctions/PEP | `screen_opensanctions.py` | `opensanctions` |
| 11 | war-sanctions.gur.gov.ua | GUR war-sanctions (3 sections) | `screen_gur.py`, `screen_gur_components.py` | `gur`,`gur_components` |
| 12 | searchplatform.rospatent.gov.ru | patents | `rospatent_patent_search.py` et al. | `ip` |
| 13 | Rospatent trademarks | trademarks | `rospatent_tm_search.py` | `ip` |
| 14 | rk.2035.university | national БАС-industry company registry | `screen_rk2035_bas_registry.py` | `rk2035` |
| 15 | Aleph (OCCRP) | leaked/aggregated corporate data | `screen_aleph.py` | `aleph` |
| 16 | Wildberries/Ozon | marketplace listings | `screen_wb.py` | `wb` |
| 17 | Telegram | posts + membership | `tg_scan.py`, `tg_scan_users.py` | `web` |
| 18 | component.aeronext.aero | АЭРОНЕКСТ member catalogue | (memory recipe, no script) | `state_programs` |
| 59 | rkn.gov.ru — Реестр лицензий в области связи | Comms-service licence records (number/status/activity), keyed by ИНН or org name | **Scripted 2026-09-06 — `scripts/screen_rkn_comms_license.py`.** Real endpoint needs the FULL param set the live form submits (`lic_status_id=0&service_id=0&region_id=0&searchBtn=Найти` in addition to the obvious ones) — an earlier attempt wrongly concluded this was JS-gated because a partial param set silently returns the untouched default page (same byte count regardless of query) rather than erroring. Confirmed clean full-176-roster run: 5 hits. | `licences` |
| 60 | rkn.gov.ru — Единый реестр частотных присвоений | Radio-frequency assignment records (record number/validity/order/status), keyed by ИНН or org name | **Scripted 2026-09-06 — `scripts/screen_rkn_frequency_registry.py`.** Same domain/pattern as #59 (plain POST, urlencoded body works, no multipart needed). Confirmed clean full-176-roster run: 5 hits, all consistent with already-documented profiles (telecom operator, radar-equipment manufacturer, bank) — no new leads. | `licences` |
| 61 | pb.nalog.ru МЧС fire-safety licence search | Fire-safety licence records, keyed by ИНН | **Scripted (prior session) — `scripts/screen_mchs_fire_licenses.py`.** Fixed an HTML-entity-decoding bug 2026-09-06 (raw `&quot;` in org names). Confirmed clean full-176-roster run: 6 hits, 5 wired (1 confirmed duplicate of an existing EGRUL-sourced licence). | `licences` |
| 62 | licenses.roscosmos.ru/api/public/licenses | Roscosmos space-activity licences, bulk JSON (548 records) | **Scripted 2026-09-06 — `scripts/screen_roscosmos_licenses.py`.** Single bulk fetch (needs a browser-like User-Agent or 403s), matched locally by `inn` field — same "bulk dataset, not a per-entity loop" class as `fstec_pull.py`, safe to re-run directly. Confirmed: 3 hits, all already known/wired. | `licences` |
| 63 | favt.gov.ru aviation-operators page | Civil-aviation operator certificates + registered aircraft, keyed loosely by ИНН in table rows | **Scripted 2026-09-06 — `scripts/screen_favt_aviation_operators.py`.** Single bulk fetch, regex-parsed. Confirmed: 2 hits (`ooo-aeromaks`, `ao-aeromaks`), both already known/wired. | `licences` |
| 64 | Rosgvardia licence registries (th/tgso/tgsp/choop/chd) | Private-security/detective/weapons-related licences, daily-snapshot CSVs | **Scripted 2026-09-06 — `scripts/screen_rosgvardia_licenses.py`.** All 5 registries in one script via `LOOKBACK_DAYS` snapshot auto-detect; matches by searching every field of every row for an exact ИНН (robust to differing column layouts). Confirmed: 0 hits across the full roster + personal ИНН — a clean negative, not a gap. | `licences` |
| 65 | rospatent.gov.ru/opendata (bulk CSV: `-tz` trademarks, `-otz` well-known marks, `-po` industrial designs) | Full-registry bulk dumps with `right holder name/ogrn/inn` columns, monthly snapshots back to 2017 | **Confirmed 2026-09-06 via direct curl** — no auth, no captcha; downloaded a real 93MB trademark CSV and verified the ИНН/ОГРН columns. Bulk-file complement to the already-used `searchplatform.rospatent.gov.ru` live API (same owning body, ФИПС) — not yet wired into a script, but trivially scriptable when needed. | `ip` (not yet wired) |
| 68 | **opendata.fssp.gov.ru** — dataset `7709576929-iplegallist`, "Общедоступные сведения банка данных исполнительных производств в отношении юридических лиц" | Legal-entity enforcement-proceedings/debt records: debtor name+address, proceeding number/date, executive-document type, debt amount + remaining balance, bailiff department, and critically **Debtor TIN (ИНН)** | **Found and confirmed real 2026-09-07 — a completely separate, unauthenticated route into the same data the captcha-gated `fssp.gov.ru/iss/ip` UI blocks (#28/#67).** The SPA's own API (`GET /api/ssp-open_data/data-sets?perPage=N`, no auth/captcha) lists 33 published datasets; this one is published DAILY (confirmed 3 consecutive days of versions), keyed by ИНН, verified via a byte-range sample download showing real legal-entity debt rows. **Scale**: the full CSV is ~1.95GB (this sandbox's throughput, ~420KB/s, makes a full pull take 80+ minutes) — `scripts/screen_fssp_opendata.py` streams it via curl piped into a CSV parser rather than saving to disk, but the full run is handed to the user per the crawling-jobs/long-job policy, not run from here. No individuals (физлица) equivalent exists in this catalogue — personal debt data stays genuinely unreachable, consistent with privacy protections elsewhere. | `litigation` or a new field (not yet wired — pending the user's full run) |

## Tier A — confirmed reachable, NOT yet integrated

| # | Source | What it gives | Status | Priority |
|---|---|---|---|---|
| 19 | **zakupki.gov.ru РНП (44-ФЗ)** — реестр недобросовестных поставщиков | debarment record; a clean check is a **citable negative** | **Confirmed working via plain curl.** No-hit marker: `Поиск не дал результатов`. Now scripted — `screen_rnp.py`. | Done |
| 20 | zakupki.gov.ru РНП (223-ФЗ) and РНП ПП РФ 615 | same, other two sub-registries | Same page, query flags (`fz223=on`, `ppRf615=on`); same script | Done |
| 21 | sudact.ru | court decisions (general jurisdiction + arbitration text) | **Correction 2026-09-05**: the earlier "plain curl HTTP 200" check only verified the static page loads — the actual search is client-side, requiring JS (`У Вас отключен JavaScript, который необходим для работы поиска`). Attempted the real AJAX endpoint anyway (`/arbitral/doc_ajax/?arbitral-txt=...`, found via live devtools capture) both via curl and via an actual browser click — **both got HTTP 500 from the site itself**, on both `/arbitral/` and `/regular/` sections, with a plain single-word query. This reads as a genuine site-side outage/bug right now, not a bot-block or a technique failure — worth re-testing later rather than building a puller against a currently-broken endpoint. | **High** — litigation is a real gap (`litigation[]` populated on 5/182), but blocked on the site's own current 500s |
| 22 | checko.ru | aggregator company card | **Scripted 2026-09-05 — `scripts/checko_pull.py`.** `GET /search?query=<ИНН>` 301-redirects straight to the company card on an exact match (precise, not a name-collision-prone free-text search). The card's sidebar nav gives per-section item counts (Арбитражные дела, ФССП, Федресурс, Связи, etc) without needing to parse each section's own content — cheap cross-check against this registry's own arrays. Already productive on the first real run: caught `ooo-gagaring` (1 arbitration case on checko, 0 in `litigation[]`) and `fond-dar-fond-regionalnykh-nekommercheskikh-proektov` (4 vs 0) as real gaps. **Rate-limits hard** — a short burst drew HTTP 429 for several minutes; the script retries with backoff but a full sweep needs patience. | Medium — aggregator, corroboration only, but now genuinely gap-finding |
| 23 | audit-it.ru (→ www.audit-it.ru) / sbis.ru (→ saby.ru, rebranded) | aggregator financials | HTTP 200 after redirect (re-confirmed 2026-09-05) | Low — БФО is better and primary |
| 40 | **pub.fsa.gov.ru (Росаккредитация)** | Certificates/declarations of conformity — hard evidence of what a manufacturer actually makes | **Scripted 2026-09-05 — `scripts/pub_fsa_pull.py`.** Corrects the earlier "Tier A" call below: this site sits behind a JS anti-bot challenge (obfuscated per-load endpoints, enciphered bodies) that gates minting an "anonymous" JWT — a bare `curl` to any real API path 403s with no way to get a token from scratch. **But the JWT itself is fully portable once minted** (confirmed: lift it from a live browser's `localStorage.fgis_token`, then reuse via plain `curl` with zero cookies/session for its ~8h lifetime) — a Tier A/B hybrid, same shape as fedresurs.ru's backend API. Two endpoints confirmed: `POST /api/v1/rss/common/certificates/get` and `POST /api/v1/rds/common/declarations/get` (note: different date-filter key names and a different `columnsSearch` item shape between the two — see the script's own docstring, cost one 500 error before being caught). Free-text applicant/manufacturer name search, not ИНН-keyed. | **High — now closed** |
| 41 | reestr.digital.gov.ru (реестр российского ПО) | Russian-software registry — relevant to control-software claims | **Scripted 2026-09-05 — `scripts/reestr_digital_pull.py`.** The listing page is server-rendered (Bitrix), takes a plain GET with an `OWNER_INN` filter param (found via live devtools capture of the actual filter form), and needs an unverified TLS context (same class as zakupki.gov.ru's cert chain) but no captcha/JS. Confirmed against a real ИНН with 28 live registrations during reconnaissance. The homepage's own "тестовые испытания"/"технические работы" banner text turned out to be permanent boilerplate, not a real outage warning. | Medium — now closed |
| 42 | fstec.ru | ФСТЭК licence registry (defence-info-security licensing) | **Scripted 2026-09-05 — `scripts/fstec_pull.py`.** The actual registry lives on the separate `reestr.fstec.ru` (Joomla `com_ajax`/DataTables, `/reg1` = ТЗИ licences, `/reg2` = СЗИ development licences). Per-column server-side filtering never worked no matter which parameter shape was tried — every variant silently returned the full unfiltered table. Worked around it: `length=-1` returns the ENTIRE table in one request (3755 rows reg1, 1685 reg2), so this pulls both once and matches every entity's ИНН locally, rather than querying per-entity. Productive immediately: 11 real active-licence hits across the roster on the first run, including two entities (`ao-pk-azimut`, `ooo-smart-teknolodzhis`) holding BOTH licence types. | Medium — now closed |
| 43 | list-org.com | aggregator company card | **Moved from Tier D 2026-09-05** — bare domain still 403s, **use `https://www.list-org.com/`**, which loads clean | Low — aggregator, tier A primary sources exist |
| 44 | zachestnyibiznes.ru | aggregator company card | **Moved from Tier D 2026-09-05** — real content confirmed post-tunnel, DDoS-Guard no longer triggering | Low — aggregator |

## Tier B — browser-assisted (chrome-devtools), one entity at a time

| # | Source | What it gives | Notes |
|---|---|---|---|
| 24 | **fedresurs.ru** (company card) | **charter capital, current ЕГРЮЛ address, status, ОКВЭД, reg. date** | Qrator 401s plain curl; passes in a real browser — **except this sandbox specifically still hard-403s even post-tunnel** (re-confirmed 2026-09-05, `IP: 94.242.50.158` in Qrator's own error page — the tunnel is on the user's device, not this sandbox's browser, so it doesn't change my egress IP here). Works fine in the user's own browser. Backend API confirmed: `GET /backend/companies?searchString=<ИНН>&limit=5&offset=0` → guid; `GET /backend/companies/<guid>` → full card. **`offset` is mandatory** or it 400s. **Correction 2026-09-06**: this is `fedresurs.ru` (company-card lookup), distinct from `bankrot.fedresurs.ru` (ЕФРСБ bankruptcy notices, item #29 below) — don't conflate the two domains. A separately-cited "open JSON `fedresurs.ru/backend/companies?code=<ИНН>`" claim (from a 2022 Habr article) was re-tested directly and 404s on the `bankrot.` domain — Федресурс's actual official bulk API (per `github.com/Smolevich/fedresurs-sdk`) is a PHP **SOAP client requiring registration**, not an open anonymous endpoint; don't trust old blog posts describing a `/backend/` REST shape without re-testing first. |
| 25 | gisp.gov.ru (ГИСП) | industrial-product + company registries (ПП 719 / ПП 878) | WAF-blocks curl (403, re-confirmed 2026-09-05); browser loads real content fine. Company search is by legal name only, not director. |
| 26 | rupep.org | PEP dossiers: DOB, birthplace, ИНН, family | **Cloudflare "Just a moment..." challenge confirmed still active 2026-09-05** even via devtools browser+tunnel (interstitial held after 6s wait) — this one may need an actual human solve, not just a browser context. Re-test with more wait time or the user's own browser before relying on it. |
| 27 | **vestnik-gosreg.ru** (use `www.` — bare domain 502s) | Liquidation/reorganisation/bankruptcy notices; homepage news feed itself is a live source (`novosti_kompaniy`) | Re-tested 2026-09-05 via WireGuard tunnel — was Tier D (network timeout), now loads real content. Homepage/news feed readable directly, no gate. The ИНН/ОГРН **search box** is behind a Yandex SmartCaptcha checkbox — still Tier B, not scriptable. |

## Tier C — user-only (do not automate)

| # | Source | Blocker | What we'd get |
|---|---|---|---|
| 28 | **fssp.gov.ru** (исполнительные производства) | **Captcha confirmed still present 2026-09-05** on `/iss/ip` even with the tunnel — page loads, `captcha` string present in the page itself, application-layer not network | Enforcement proceedings = unpaid judgments/debts. **Superseded 2026-09-07 for legal entities** — see #68 below, a genuinely open bulk-CSV route into the same underlying data via `opendata.fssp.gov.ru`, no captcha at all. This interactive-UI entry stays relevant only for individuals, where no open-data equivalent exists. |
| 29 | fedresurs.ru **publications** | **HTTP 451** (legal block) on `/backend/companies/<guid>/publications` — a legal block is jurisdictional, not IP-based, so no tunnel fixes this one | Bankruptcy/lien/pledge/net-asset notices. The company card (tier B) still works. |
| 30 | kad.arbitr.ru | **Re-tested 2026-09-05**: page itself now loads (DDoS-Guard no longer blocking at network level), but the search form's own captcha (`captcha` string present) still gates results — moved from "network-dead" to "app-layer captcha," net effect for us is the same: user-only | Arbitration case records — use `sudact.ru` (Tier A) as the scriptable substitute |
| 31 | mos-gorsud.ru | **Re-tested 2026-09-05**: same pattern as kad.arbitr.ru — page loads now, `captcha` string confirmed present | Moscow court records |
| 32 | leader-id.ru | **Re-tested 2026-09-05**: homepage loads real content now, but the actual user-directory function is still login-gated (401 confirmed on the API) — homepage reachability is not the same as the directory being usable | 412k-user event-participant directory |
| 33 | reveng.ee | **Struck off the active queue 2026-09-07 at user direction** — API key must be requested by the user (media/journalist tier); homepage itself loads fine (HTTP 200, re-confirmed) but the search API needs the key. Not pursuing for now; re-open if the user decides to request the key later. | Leaked Russian DB search |
| 34 | rusprofile.ru | **Serves decoy data to automated traffic** — only `<title>` trustworthy | Nothing safely; avoid |

## Tier D — no route found from this sandbox (user should re-test)

All prior Tier D entries were re-tested 2026-09-05 once the sandbox's egress
went through the user's WireGuard tunnel — **every one of them became
reachable** (moved to Tier A/B above). Nothing remains in Tier D as a pure
network-unreachability case as of this sweep, **except** the NAZK item below,
whose problem isn't network routing at all:

| # | Source | Status |
|---|---|---|
| 35 | sanctions.nazk.gov.ua (NAZK "War & Sanctions") | **Not a network problem — this hostname doesn't exist.** DNS lookup returns NXDOMAIN (confirmed via both Google and Cloudflare DoH, `Status:3`, no `Answer` section). The base domain `nazk.gov.ua` resolves fine (91.142.175.20). The subdomain was this investigation's own guess, never verified against NAZK's actual site structure — still needs the real current URL for their sanctions tool before this can be re-tried at all. Do not guess further subdomains; find the real one from NAZK's own navigation or ask the user. |

---

## Regional/lower-level registries and permit sources — surveyed 2026-09-05

Prompted by the question "where else could our entities plausibly file for
permits" — a different axis from the federal registries above. None of these
were previously in this file.

### New Tier A — reachable, real content, no captcha

| # | Source | What it gives | Notes |
|---|---|---|---|
| 45 | **rmsp.nalog.ru** (Реестр МСП) | SME category (micro/small/medium), `is_active`, `is_hitech` flag, `has_licenses`/`has_contracts` booleans, headcount, registry in/out dates, self-reported product line (`СВЕДЕНИЯ О ПРОИЗВОДИМОЙ ПРОДУКЦИИ`) | **Confirmed scriptable.** `GET /search-proc.json?query=<ИНН>` — plain JSON, no captcha, no key. `is_hitech` is a genuinely new, unused data point for a UAV-industry investigation. No script yet — worth one. |
| 46 | statreg.gks.ru (Росстат registry) | Would corroborate ГИР БО financials from a second body | **Reachable but useless as tested** — root URL just serves nginx's default page, meaning this is the wrong subdomain/path for the actual public lookup. Needs the real endpoint identified before this is actually Tier A. |

### New Tier B — browser-only

| # | Source | What it gives | Notes |
|---|---|---|---|
| 47 | rpn.gov.ru (Росприроднадзор) | Environmental permits / negative-impact-object registry (НВОС) — relevant for any entity with a physical production facility | Homepage loads fine, but the actual permit function lives on a separate login-gated sub-application (`lk.fsrpn.ru`), not a public per-entity search — this looks like an application portal, not a lookup registry. Needs more digging to find (or confirm the absence of) a public NVOS object search before this is worth wiring up. |

### New Tier C — app-layer blocked

| # | Source | Blocker | What we'd get |
|---|---|---|---|
| 48 | nostroy.ru (СРО builders registry — construction self-regulating org membership) | **DDoS-Guard confirmed** (devtools browser shows the DDoS-Guard interstitial directly, not real content) | SRO membership for any entity doing construction/installation work under a government contract (relevant — ГАСКАР Интеграция's construction-IT-services contracts, above) |
| 49 | rosrid.ru (ЕГИСУ НИОКР — state R&D-results registry) | **TLS certificate mismatch** (`ERR_CERT_COMMON_NAME_INVALID` in a real browser) on top of an HTTP 401 via curl — this reads as a misconfigured or wrong-hostname server, not a clean app-layer gate like a captcha. Needs the real current hostname before ruling in or out. | Would show state-funded R&D contract results — relevant for any entity claiming government R&D grants |

### New — wrong/dead hostnames (not network problems)

| # | Source | Status |
|---|---|---|
| 50 | reestr.mchs.gov.ru (fire-safety declarations registry, guessed) | NXDOMAIN — guessed hostname, never verified. `www.mchs.gov.ru` itself resolves and redirects fine; the actual declarations-registry subdomain still needs to be found from MCHS's own site nav. |
| 51 | rosakkreditatsiya.gov.ru (guessed) | NXDOMAIN — **this is just the wrong name for pub.fsa.gov.ru**, already Tier A (source #40 above). Do not re-add as a separate source. |

### New Tier D — genuinely network-unreachable, confirmed even from the sandbox (not just untested)

**Re-tested 2026-09-05 (second pass, curl-only).** These four (#52-55) still
time out via plain `curl` (`000` after a 12s timeout) — the tunnel fix that
resolved every other Tier D entry does NOT reach these **via curl**.

**Third pass, same day, via the chrome-devtools browser: 2 of the 4 DO load
real content in a real browser, even though curl still can't reach them.**
This is a genuinely new distinction for this file — not "reachable vs not"
but "reachable to a full browser client vs not to a bare TCP/TLS client,"
plausibly a TLS-fingerprint or SNI/ALPN check rather than an IP-level block
(consistent with the fedresurs.ru pattern above, where the browser and curl
diverge for a different reason). Re-verify via curl from a real browser's
network path before assuming these need Tier B treatment specifically:

| # | Source | curl result | Browser result | What it gives |
|---|---|---|---|---|
| 52 | data.mos.ru (Moscow city open-data portal) | Still times out (`000`) | **Loads real content in browser** — homepage shows "1246 наборов" (datasets), including "Адресный реестр объектов недвижимости города Москвы" and a "ТОП-30 предприятий по объемам выставленных штрафных санкций" (top-30 firms by fines) dataset. **API-docs read done 2026-09-05, resolved to Tier C — login-gated, not scriptable.** The documented API (`apidata.mos.ru/v1/...`) requires an `api_key` issued only via a registered user profile (confirmed live: `GET https://apidata.mos.ru/version` returns 200 with no key, but `GET /v1/datasets` 401s with `"Необходимо указать api_key"` — the version-check endpoint is open, the actual data endpoints are not). Same login-gated shape as `leader-id.ru`. `apidata.mos.ru` also only answers a browser `fetch`, not `curl` (`000` even from behind the tunnel) — a third confirmed instance of the browser-vs-curl split, on top of `nspd.gov.ru`. If the user wants this pursued, it needs their own free registration + API key, then it's a normal Tier A JSON API. |
| 53 | rosreestr.gov.ru | Still times out (`000`) | Browser tab also shows `chrome-error` — genuinely dead in the browser too | Property/ЕГРН — facility ownership, the long-flagged Rosreestr gap (see "Known gaps" section below) |
| 54 | lk.rosreestr.ru | Still times out (`000`) | Browser tab also shows `chrome-error` — genuinely dead in the browser too | Rosreestr personal-cabinet subdomain |
| 55 | nspd.gov.ru (Национальная система пространственных данных — Rosreestr's modern public cadastral-map portal) | Still times out (`000`) | **Confirmed Tier B, 2026-09-06/07 — NOT reliably curl-scriptable, despite one early success.** Real endpoint found: `GET /api/geoportal/v2/search/geoportal?query=<address-or-cadastral-number>&thematicSearchId=1`, returns cadastral number/address/area/year-built/purpose/ownership_type/right_type/cost_value per matched building (owner/tenant identity is never exposed — Rosreestr redacted that from public output post-2017). A curl with a full browser-like header set (Referer + `sec-ch-ua*`/`sec-fetch-*` family) got one real 200 — but every retry after that 403'd, from **both this sandbox's egress AND the user's own home network** (confirmed 2026-09-07 running `scripts/screen_nspd_addresses.py` against 152 entities — 403 on every request from the user's machine too). This is a materially different/worse case than fedresurs.ru's sandbox-only IP block above: nspd.gov.ru's WAF is not reliably passable from ANY network tested so far. A chrome-devtools browser session has never failed on the same queries. **`scripts/nspd_lookup.py`** (single-query) and **`scripts/screen_nspd_addresses.py`** (batch, exists but do not hand this one to the user again as a batch job — it will just 403) exist for the case curl does work; when it doesn't, redo the specific query via chrome-devtools instead. Do not re-attempt a full-roster curl sweep of this source without a genuinely different network path (e.g. a residential proxy) to test first. |

**#56/57 corrected, merged, and upgraded to Tier A — re-tested 2026-09-05.**
These are **the same site**, not two: `solutions.fas.gov.ru` 302-redirects
straight to `br.fas.gov.ru`. The original description of #56 ("реестр
банковских гарантий") was also wrong — the page's own title is «База
решений и правовых актов» (FAS decisions & legal-acts database, antitrust
rulings), matching what #57 described. **Confirmed scriptable via plain
curl** (devtools capture done, then independently reproduced with bare
curl — see `scripts/screen_fas_br.py`, added same day): `GET /?text=<name>&
type=0` is a server-rendered full-text case search, no JS/cookies/session
needed; the result page's "Всего: N" line gives a real hit count (tested:
"Ростелеком" → 136, a small no-history entity → 0, identical in curl and
browser). The org-ID-based filter (`/ajax/organizations/?term=...`) that
looked more precise turned out to ignore its own `term` param entirely
(returns an identical unfiltered page regardless of query) — abandoned in
favor of the working free-text path. One entry, corrected and promoted:

| # | Source | What it gives | Notes |
|---|---|---|---|
| 56 | **br.fas.gov.ru** (= solutions.fas.gov.ru, redirects here) — ФАС «База решений и правовых актов» | Antitrust-violation decisions/rulings — a citable negative (or a real hit) distinct from the debarment registry (RNP) already integrated | **Tier A, scripted** — `scripts/screen_fas_br.py`. Free-text name search only (a bare ИНН as `text` returns 0 even for entities with real cases — this indexes case prose, not a structured ИНН field), so every hit needs a human read of the actual case before use — a generic name ("Орион," tested, 78 hits) will pull in unrelated same-named companies. |
| 58 | www.gost.ru / gost.ru (Росстандарт — GOST certification body) | Product standard certification — same evidentiary category as Rosakkreditatsiya's declarations-of-conformity registry (#40), different body | **Reachable, redirects to the real site**: `www.gost.ru` → `www.rst.gov.ru/portal/gost` (HTTP 200, confirmed 2026-09-05 via both curl and browser). Not yet checked for a per-company/per-product search function — homepage reachability only so far. |

---

## Still unresolved — reverse-engineering started, not finished

| # | Source | Status |
|---|---|---|
| 66 | **reestrs.minjust.gov.ru** | A generic registries platform underlying multiple Минюст registries (its foreign-agents page loads via `ExternalApi.setBaseUrl('https://reestrs.minjust.gov.ru')` + a table UUID, e.g. `39b95df9-9a68-6b6d-e1e3-e6388507067e`). A single probe of `GET /api/registers/<uuid>` was interrupted mid-attempt 2026-09-06 and never completed — genuinely open, not confirmed dead. Worth a proper chrome-devtools session (same technique that cracked #59/#60 above) before writing this off. |
| 67 | ФССП Bank of Enforcement Proceedings (`fssp.gov.ru/iss/ip`) | Already Tier C (#28, captcha on the public page) but note from 2026-09-06 research: the **official** API (`api-ip.fssp.gov.ru`) requires a token issued by ФССП itself and is asynchronous (submit task → poll for result) — not just captcha-gated, genuinely not an anonymous-access API even with a token workaround. Third-party wrappers (`github.com/TalismanFR/fssp`) confirm the same shape. Not worth further automation attempts without the user obtaining credentials directly from ФССП. |

## Known gaps in the source set itself (nothing checks these yet)

- **Customs/import data.** Russia has hidden company-level import data since
  2022; the best open lead remains The Insider's exporter CSV (sellers only, no
  Russian buyer field) plus China/Kazakhstan/Kyrgyzstan mirror data. See the
  `sanctions_evasion_tracker_and_mirror_trade_data` memory. No tooling.
- **Property/Rosreestr (ЕГРН).** Facility ownership. Referenced in the Гагаринг
  plan (pinning a specific литер at Одесская 48/3) but never actually wired up.
- **Non-OpenSanctions primary designation lists** — OFAC SDN, EU consolidated,
  UK OFSI, CA/JP/AU/CH read directly rather than through the aggregator.
  `sanctions[]` notes already flag several entries as "ID-confirmed aggregator
  match, one level short of a primary-source read".
