# Deep-research: additional public/ЕСИА-gated registries (2026-09-06)

Workflow run `wf_e7a50cec-fa9` completed with real search/fetch/verify results
(19 sources fetched, 61 claims extracted, 25 verified: 16 confirmed / 9
refuted), but its final synthesis step returned broken placeholder output
("test") instead of a real report — a bug in that run, not a real finding.
This note reconstructs the real findings by hand from the run's own
journal (`subagents/workflows/wf_e7a50cec-fa9/journal.jsonl`) plus direct
curl verification of the most promising leads. Confirmed/refuted status
below reflects the workflow's own 3-vote adversarial check, and (for the
top candidates) an independent curl test done afterward.

## New, verified, genuinely scriptable

### Роспатент open-data bulk CSV dumps (rospatent.gov.ru/opendata)
**Verified directly** (curl, 2026-09-06): `rospatent.gov.ru/opendata/7730176088-tz`
(and sibling pages `-otz` well-known marks, `-po` industrial designs) list
dated CSV download links with no auth, no CAPTCHA, no JS challenge —
e.g. `rospatent.gov.ru/opendata/7730176088-tz/data-20260902-structure-20180828.csv`
downloaded clean as a 93MB CSV. Header confirms **`right holder name`,
`right holder ogrn`, `right holder inn`, `right holder address`** columns
alongside registration/application/priority dates — directly usable to
cross-reference an entity's ИНН/ОГРН against its full trademark portfolio.
This is a **bulk-file complement**, not a replacement, to the
already-used live `searchplatform.rospatent.gov.ru` API — same owning body
(ФИПС), but updated monthly (not real-time) and covering the full registry
in one pull rather than one query per name. Snapshots archived back to
2017 (industrial designs) / 19 Oct 2017 (trademarks), so a specific
`as_of` date can be pinned to a snapshot file for provenance.
- Trademarks: `rospatent.gov.ru/opendata/7730176088-tz`
- Well-known trademarks: `rospatent.gov.ru/opendata/7730176088-otz`
- Industrial designs: `rospatent.gov.ru/opendata/7730176088-po`

### NSPD / Rosreestr Публичная кадастровая карта (nspd.gov.ru)
**Confirmed 3-0** by the workflow's own verification: the standalone
Публичная кадастровая карта has migrated to the unified НСПД platform
(`nspd.gov.ru/map`, canonical domain `nspd.rosreestr.gov.ru`), browsable
without login. It supports requesting official ЕГРН extracts from the same
interface. Not yet reverse-engineered for a scriptable query API — this is
a browse confirmation only, same caveat as the earlier `favt.gov.ru`-style
"no-registration-required" claims that turned out to gate the actual data
behind a request form. Worth a chrome-devtools pass the same way the RKN
registries were cracked, but not yet done.

## Re-tested and found weaker than the workflow initially reported

### Федресурс (bankrot.fedresurs.ru) — official API needs SOAP + registration
The workflow surfaced a claim (from a 2022 Habr article) that
`fedresurs.ru/backend/companies?code=<ИНН>` is an open JSON endpoint
needing only a Referer header. **This claim was refuted 0-3 by the
workflow's own verifiers, and independently refuted again just now**: a
direct curl to `bankrot.fedresurs.ru/backend/companies?...` with a proper
Referer returns a plain 404 — the endpoint/domain from the 2022 article no
longer exists. A more recent lead, `github.com/Smolevich/fedresurs-sdk`,
documents Федресурс's actual official API as a **PHP SOAP client**
requiring registration per Федресурс's own connection-docs PDF — i.e. this
is not an open, anonymously-scriptable registry the way EGRUL or the RKN
registries are. The public search UI at `bankrot.fedresurs.ru/search`
likely has its own AJAX endpoint, but it hasn't been reverse-engineered
(a chrome-devtools session, same technique used for RKN, would be the next
step if this registry becomes a priority).

### egrul.itsoft.ru bulk EGRUL mirror — refuted
A claim that the full EGRUL registry is available as an open bulk XML
mirror at `egrul.itsoft.ru` was **refuted 0-3** — treat as unconfirmed/
likely stale; this project already has better EGRUL access via
`scripts/egrul_batch_pull.py` and the full-выписка flow, so not worth
chasing further.

### ФССП Bank of Enforcement Proceedings (debt registry) — real but token-gated
**Confirmed 3-0** that ФССП maintains a searchable "Банк данных
исполнительных производств" (debt-enforcement registry) at
`fssp.gov.ru/iss/ip`, but the only documented API access
(`api-ip.fssp.gov.ru`, and third-party wrappers like
`github.com/TalismanFR/fssp`) **requires a token issued by ФССП itself**
(confirmed 2-1) and is asynchronous (submit a task, poll for results) —
not an open anonymous endpoint. The public web UI itself may still be
scriptable via its own AJAX calls (same class of problem as RKN/Fedresurs
above); not yet attempted with chrome-devtools.

## Supporting leads, not yet tested (worth a look if time allows)

- **GAS Правосудие** — searchable database of Russian courts of general
  jurisdiction rulings, distinct from `kad.arbitr.ru` (arbitration courts,
  already known to be DDoS-Guard-blocked). Since this is a *different*
  court system (general jurisdiction, not commercial/arbitration), it may
  not share the same block.
- **Declarator** — repository of Russian public officials' income/asset
  declarations; useful for PEP cross-checks alongside `rupep.org`.
- **dom.gosuslugi.ru** (ГИС ЖКХ / Housing) — property/building-level
  lookups, distinct from Rosreestr/EGRN.
- **checko.ru** — independently re-confirmed by an OSINT catalog as a free
  corporate-lookup API; already covered by this project's own
  `checko_pull.py`, so this is corroboration, not a new lead.
- **OpenRegistry** (openregistry.io-style aggregator) — claims real-time
  access across 27 national corporate registries worldwide with a free
  tier (20-30 req/min); Russia-specific coverage/quality untested.
- **Минюст open-data page** (`minjust.gov.ru/ru/pages/opendata/`) — a
  dedicated open-data section distinct from the `reestrs.minjust.gov.ru`
  generic registries platform already flagged as unreverse-engineered;
  not yet checked for bulk NKO/foreign-agent dumps.
- **zakupki.gov.ru/epz/opendata** — ЕИС's own open-data section, distinct
  from the live contract-search API already used via
  `zakupki_batch_pull.py`; may carry bulk dataset dumps worth checking for
  completeness cross-checks.

## Leak repositories (flagged per the evidentiary-weight caveat — not equivalent to an official registry)

- **CyberPartisans** (Belarusian hacktivist group, `by.cpartisans.org`) —
  maintains a verification bot over a database of 8,600+ current/former
  KGB (Belarus) employees, and has published leaked material from
  Roskomnadzor-linked surveillance systems (SecureTower, Brand Analytics,
  "Oculus", "Vepr") and a ~40,000-entry KGB appeals/denunciation database.
  **Confirmed 2-1 as leak-sourced** (hacked internal government material,
  not an official registry) — any fact sourced here needs independent
  corroboration before it goes near the brief, same standard already
  applied to the InformNapalm dossier per the PII policy in CLAUDE.md.
  Relevant to Belarus-linked individuals, not directly to ЦБСТ/РОЙ.МАРКЕТ
  unless a specific cross-reference turns up.
- **"пробив" ecosystem** — Telegram-distributed lookup bots that resell
  insider access to official databases (ЕГРН, ЕГРЮЛ, MVD/GIBDD/PFR
  records) "через сотрудников" (via employees), not open scriptable
  endpoints. Explicitly **not** a registry substitute — mentioned here only
  because the research prompt asked about the ecosystem's existence, not
  as something to use.
- **DDoSecrets-style breach corpora** (e.g. the cited Yandex.Eats 2022
  breach, ~7M records with name/phone/address) — same caveat: leak-sourced
  personal data, different evidentiary tier than an official lookup,
  flagged not treated as equivalent.

## Not pursued further this round

`reestrs.minjust.gov.ru` (the generic Минюст registries platform found via
its foreign-agents page's `ExternalApi.setBaseUrl` call) was not
independently reverse-engineered in this workflow run — the interrupted
manual probe from earlier in this session (a guessed
`/api/registers/<table-uuid>` call) remains the most promising lead and is
worth resuming with a proper chrome-devtools session, the same technique
that cracked both RKN registries.
