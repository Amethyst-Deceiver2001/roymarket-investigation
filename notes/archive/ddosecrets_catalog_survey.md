# DDoSecrets catalog survey (2026-09-08, one-time reconnaissance)

One-time reverse-engineering pass on data.ddosecrets.org/.com and
ddosecrets.org for the "Data Access Request" (Reserved-collection library
card) application in progress. Not a recurring scrape — bot-blocked on
almost every direct fetch (data.ddosecrets.org/.com 403 or empty,
tickets.ddosecrets.org 403, ddosecrets.com/wiki/Contact empty to WebFetch).
Catalog content below came from Wikipedia's "List of material published by
Distributed Denial of Secrets" and their Substack archive instead.

## Access model

Two tiers: **Public** (their main searchable "Library of Leaks" index, open
to all) and **Reserved** (PII-heavy datasets, gated behind a vetted
"library card" — the thing our application form is for). Vetting criteria
per their own public statements: journalists/researchers who've "proved
with their previous work that they can respect the privacy of individuals
caught up in a data breach." Contact/apply via press@ddosecrets.com or their
ticket system (both blocked to automated fetch, use a real browser).

`xray.ddosecrets.com` ("Project X-Ray") is **not** the full-text search —
it's a separate crowdsourced tool for manually transcribing scanned offshore
corporate-registry filings (PHP/MySQL, volunteers fill in officer/director
data OCR can't read). The actual full-text "Library of Leaks" search over
the whole corpus is a different, client-rendered interface not reachable via
static fetch — worth trying once library-card access exists, since that's
what would let a name/ИНН search across every leak at once before deciding
which specific dataset(s) to formally request.

## Russia-relevant holdings (March–April 2022 "Russian Leaks" batch, plus a few others)

Highest relevance to ЦБСТ/РОЙ.МАРКЕТ (defense/UAV network, sanctions
evidentiary work):
- **General Department of Troops (Ministry of Defense)** — 9.5 GB emails,
  April 2022. Direct MoD internal correspondence.
- **Tetraedr** (Belarus, missile testing footage/weapons schematics),
  Feb 2022 — defense-manufacturer emails.
- **Synesis** (Belarus surveillance-system vendor), 1.2 GB, April 2022.
- **Central Bank of Russia** — 22.5 GB, March 2022 — cross-check candidate
  for financial/beneficial-ownership claims where БФО filings are thin.
- **Rosatom** (15.3 GB), **Marathon Group** (51.9 GB, investment),
  **Gazprom Linde Engineering** (728 GB) — large state/investment-corp
  email caches, worth a name/ИНН search inside if access is granted.
- Regional-government caches: Tver Oblast (116 GB), Strezhevoy (221 GB),
  Blagoveshchensk (150 GB) — only relevant if a tracked entity's registered
  address falls in one of those regions (not yet checked).

Needs a specific tie before requesting:
- **Cyprus Confidential** (~3.6M docs, Nov 2023, joint ICIJ) — Putin
  financial network / Russian billionaire offshore & sanctions-evasion
  records, 67 of 105 tracked Russian billionaires. Relevant only if a
  specific network principal has Cyprus exposure — not yet established.
- **Roskomnadzor** (820 GB, March 2022 + April 2023 update) — censorship/
  surveillance monitoring, low relevance unless tracking suppression of
  coverage about our own targets specifically.

Full March–April 2022 batch also includes (lower/unclear relevance, listed
for completeness): Omega Co./Transneft R&D (79 GB), Thozis Corp (5.9 GB),
MashOil (110 GB), RostProekt (2.5 GB), Mosekspertiza (483 GB), VGTRK state
media (900k+ emails), Ministry of Education (250k emails), Ministry of
Culture (200k+ emails), Capital Legal Services (65 GB), Aerogas (154 GB),
Technotec (440 GB), Gazregion (222 GB), Continent Express (339 GB),
Neocom Geoservice (107 GB), Tendertech (160 GB), Worldwide Invest (130 GB),
Sawatzky (432 GB), Accent Capital (221 GB), Enerpred (342 GB), Russian
Orthodox Church (15 GB, limited distribution).

## Next step once library-card access is granted

Search the full-text "Library of Leaks" index (not xray.ddosecrets.com) for
every core entity/person name and ИНН already in `data/registry/*.json`
before requesting specific bulk datasets — a targeted hit list is a much
stronger basis for the "which dataset(s)" field than guessing from the
catalog metadata alone.
