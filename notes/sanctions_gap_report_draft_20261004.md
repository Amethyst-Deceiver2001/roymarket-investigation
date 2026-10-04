# РОЙ.МАРКЕТ: sanctions-gap report (internal draft, 04.10.2026)

**Status: draft for Alexey's review. Not sent anywhere.** Built on the six
evidence packets in `notes/packets/`, each of which went through a
`claim-verifier` read-only pass on 03.10.2026 (≈330 claims checked) and had
every finding from that pass fixed in the registry — re-verified today
(04.10.2026) by regenerating all seven packets and confirming the output is
byte-identical to what's on `main`. This document is the cover note the
cloud session recommended shipping as the project's first real output; it
does not itself make the legal case — each packet's §7 leaves the
conclusion and statutory criterion for whoever submits it.

## 1. The finding

The registry ties 73 organisations to ЦБСТ (Центр беспилотных систем и
технологий) / РОЙ.МАРКЕТ, Russia's state-linked drone-industry marketplace
and its parent body. Checked against the EU, US (OFAC), UK and Swiss
sanctions lists by ИНН/ОГРН as of the 02.10.2026 weekly watch run:

- **21 already listed** on at least one of the four regimes by identifier.
- **52 carry no identifier match on any of the four** — not proof of
  absence (a list can name a company without its tax/registration number,
  and only four regimes were checked this way), but the gap the project
  exists to surface.

Of those 52, **six have real, filed revenue large enough to matter and no
Western designation at all**. These are the six packets:

| Company | ИНН | FY2025 revenue (₽m) | ЦБСТ tie grade |
|---|---|---|---|
| ООО «Гаскар» | 9710112989 | 9,824.7 | Documented |
| ООО «Смарт Текнолоджис» | 7715934509 | 3,929.6 | Documented |
| ООО «Гагаринг» | 2312321660 | 2,159.0 | Documented |
| ООО НПО «Киловатт» (Шестопалов) | 4800016776 | 1,158.6 | Documented |
| ООО «ОПКБ Экспломет» | 1215235283 | 782.4 | Documented |
| ООО «Метаскан» | 1660349248 | 764.7 | Documented |

(ООО «СТИМС», ИНН 7734436058, is a seventh packet — included because it
turned out to be the real identity behind an EU/Swiss listing that the
registry had been attributing to a different, similarly-named company; see
§3.)

Total unlisted revenue across the six: **≈₽18.6bn** in FY2025 filed accounts,
all read from the signed БФО filings in `data/sources/`, not estimates.

## 2. What "Documented" means here

Every ЦБСТ tie in this table is **t-doc** confidence in the registry's own
vocabulary: a primary document — not a press report, not an aggregator
snippet — states the relationship. The ties, in brief (full exhibits in each
packet):

- **Гаскар / СТИМС**: see §3 — the group's products are shown at ЦБСТ events
  and listed under rk.2035.university's ГИСП БАС catalogue.
- **Смарт Текнолоджис**: ЦБСТ's own channel names it a resident (post 487).
- **Гагаринг**: ЦБСТ association membership (01.03.2024) plus its training
  arm (АНО ДПО «Образовательный центр Гагаринг»).
- **Киловатт (Шестопалов)**: products («Капюшон» jammers) shown at
  Дронница 2024/2025, handed over to the front via Фонд «Наша Правда»
  (8 recorded deliveries).
- **Экспломет**: a signed strategic-cooperation agreement with ЦБСТ
  (12.08.2025, ЦБСТ's own channel), general directors named on both sides.
- **Метаскан**: ЦБСТ's own channel names its demining product among goods
  handed to Kursk-direction units (12.05.2025).

## 3. The one real correction this pass made: Гаскар ≠ СТИМС

The most serious defect the claim-verifier pass found was a conflation: the
registry had attributed an EU/Swiss sanctions listing for "Gaskar Group" to
**ООО «Гаскар»** (ИНН 9710112989), when the listing's own printed
identifiers (registration number, tax ID, KPP, Skolkovo address) match
**ООО «СТИМС»** (ИНН 7734436058) — a company renamed from Гаскар Групп on
19.11.2024. The two are separate legal entities; a third, ООО «Гаскар
Интеграция», is itself unlisted and its only link to СТИМС so far is a name
match — one of СТИМС's participants (Саитов Ренат Фаритович, 20% since
07.07.2026) shares a full name with Гаскар Интеграция's 2019 general
director, but the registry does not treat that as a confirmed link; it is
an open question, not a fact in this report.

This is now fixed: ООО «СТИМС» carries the EU (Council Implementing
Regulation 2026/509, entry 704) and Swiss (SECO, 21.05.2026, SSID 104739)
listings with their own printed identifiers checked against its ЕГРЮЛ
extract; ООО «Гаскар» (9710112989) correctly shows "no ID match" on all
four regimes in the table above and is listed on Canada's SEMA list only
(Schedule 1 Part 2, item 833).

**Why this matters for submission**: naming the wrong legal entity in a
sanctions submission is the kind of error that gets a whole filing
discounted. The fix means a submitter working from this packet set won't
repeat the registry's own earlier mistake.

## 4. What else the verification pass fixed (no longer open)

- **Киловатт (Шестопалов)**: the dealer named on a product certificate was
  wrong (a namesake, ИП Пинимасова Е.А., instead of the actual signatory ИП
  Пинимасов А.В.); a participant's role was overstated as "founder" when he
  bought in later (31.03.2026, not at incorporation); the «Капюшон»
  trademark is correctly attributed to the sister entity that actually holds
  it, not this one.
- **Метаскан**: a second 50% participant (ООО «Централизованная юридическая
  служба») was missing from the ownership table; a paraphrase had been
  rendered as a direct quote.
- **Гагаринг**: an ownership-history row carried the wrong date for when the
  49.5% holder's stake began; a since-restated FY2024 profit figure now
  carries the restatement note.
- **Экспломет**: a FY2023 profit restatement now carries its note; the
  ЦБСТ-tie wording was softened to match what the source post actually
  says ("envisages" joint development, not "joint development" as an
  accomplished fact).
- Several generator-level bugs (truncated exhibit descriptions, wrong
  document-type titles, an address wrongly flagged "no dated source") were
  fixed in `exhibits/build_evidence_packet.py` and all packets regenerated.

## 5. What is still open, stated plainly

A submission that hides its own gaps is worse than one that states them.

- **Гагаринг's ownership split is unreconciled by design, not oversight.**
  The company register shows 50.5%/49.5% (ГРН 2262300538091, 15.04.2026,
  re-confirmed on a fresh extract pulled 04.10.2026); its own FY2025 audit
  report says 50/50 as of 31.12.2025. Alexey decided (04.10.2026) to leave
  this open rather than guess; resolving it needs either the register's
  entry history for that ГРН or an earlier version of the audit report,
  neither pulled yet. The packet states both figures and the conflict.
- **Delivery evidence is self-reported.** The 25 recorded equipment
  deliveries (Булат, Капюшон) all trace to the donor's own posts (Фонд
  «Наша Правда», ЦБСТ's channel), `asserted_by: self`, `credibility:
  single` by default. This is adequate to show a product reaches the front,
  not to prove combat use of a specific unit's equipment — the registry's
  own rule is that a delivery never implies combat use.
- **Wayback coverage of web pages is decent (148 of 157 cited tier-1 web
  pages captured, per `archive_sources.py report`); Telegram is a separate,
  deliberate gap.** The project stopped submitting Telegram posts to the
  Wayback Machine on 03.10.2026 (Alexey's decision); 442 captures made
  before that date stay on file but no new ones are added. Primary-source
  preservation for Telegram instead rests on the project's own scrape
  (`data/roymarket.db`), RFC 3161 timestamping of the archived bytes
  (`data/registry/timestamps/`), and a per-cited-post evidence bundle with
  media — a public third-party mirror, not our own record, which is the
  thing a hostile reviewer would ideally also be able to check independently.
- **DOB/PII coverage is partial.** Most people in the registry do not carry
  a date of birth; where one is recorded it has its own source, but the
  coverage is not systematic. This affects identity confidence on
  person-level sanctions matches more than on the six company packets above
  (which rest on corporate ИНН/ОГРН, not personal identifiers).
- **No media-law or PII-policy legal review has been done.** Explicitly not
  started per Alexey's own "not yet" (04.10.2026); this report and the
  packets stay internal until that review happens.
- **Second-person verification.** Every check in this pass was done by one
  Claude session working from the registry; no independent human or second
  reviewer has checked the packets against the underlying documents yet.

## 6. The packets themselves

Each packet (`notes/packets/<slug>.md`) is self-contained: identification,
sanctions status, owners/directors, filed accounts, the ЦБСТ tie with its
own evidence, products and what's said about their use, a draft statement
of reasons (facts only — the legal conclusion is left for the submitter),
and a numbered exhibit list with public links where they exist and SHA-256
hashes for everything else. An internal appendix on each (dropped before
sending) lists the open research questions still sitting against that
company, so a submitter or a second reviewer can see what was checked and
what wasn't.

- [ООО «Гаскар»](packets/ooo-gaskar.md)
- [ООО «Смарт Текнолоджис»](packets/ooo-smart-teknolodzhis.md)
- [ООО «Гагаринг»](packets/ooo-gagaring.md)
- [ООО НПО «Киловатт» (Шестопалов)](packets/ooo-npo-kilovatt-shestopalov.md)
- [ООО «ОПКБ Экспломет»](packets/ooo-opkb-eksplomet.md)
- [ООО «Метаскан»](packets/ooo-metaskan.md)
- [ООО «СТИМС»](packets/ooo-stims.md)

## 7. Recommended next step (not acted on — for Alexey to decide)

The cloud session's 03.10.2026 assessment proposed submitting this package
through proper channels: the EU, UK and US sanctions desks directly, plus
one partner organisation experienced in this kind of submission (OpenSanctions,
the KSE Institute, or B4Ukraine were named as examples). That is an
external-distribution decision this document does not make on its own —
flagging it here as the logical next step once:
1. Alexey has read and can stand behind every line in the six (seven)
   packets, and
2. the media-law/PII review (§5) has actually happened for anything beyond
   the corporate facts in these packets specifically.

Nothing in this report or the packets has been sent anywhere. All six
packets, this cover note, and the underlying registry corrections are on
`main`.
