# РОЙ.МАРКЕТ: sanctions-gap report (internal draft, 05.10.2026; supersedes the 04.10.2026 draft)

**Status: draft for Alexey's review. Not sent anywhere.** Built on the five evidence packets in `notes/packets/` for the companies below
(a sixth, ООО «СТИМС», is kept as the packet for the listed company that the
registry had confused with Гаскар; see §3). The packets went through a
`claim-verifier` read-only pass on 03.10.2026 (≈330 claims checked), every
finding from that pass was fixed in the registry, and on 05.10.2026 the gap
table and all packets were regenerated from the current registry and the
sanctions watch of 05.10.2026. **Changes since the 04.10.2026 draft:** the
ЦБСТ tie of ООО «Гаскар» was withdrawn on 04.10.2026 (§3), so Гаскар is no longer
part of the set and the headline total falls from ≈₽18.6bn to ≈₽8.8bn; and on
05.10.2026 the registry's sanctions claims were read against the official US,
EU, Swiss and UK lists (§1). This document does not make the legal case: each
packet's §7 leaves the conclusion and statutory criterion for whoever submits it.

## 1. The finding

The registry ties 74 organisations to ЦБСТ (Центр беспилотных систем и
технологий) / РОЙ.МАРКЕТ, Russia's state-linked drone-industry marketplace
and its parent body. Checked against the EU, US (OFAC), UK and Swiss
sanctions lists by ИНН/ОГРН as of the 05.10.2026 weekly watch run:

- **22 listed** on at least one of the four regimes by identifier.
- **52 carry no identifier match on any of the four**: not proof of
  absence (a list can name a company without its tax/registration number,
  and only four regimes were checked this way), but the gap the project
  exists to surface.

Of those 52, **five have real, filed revenue large enough to matter and no
Western designation at all**. These are the five packets:

| Company | ИНН | FY2025 revenue (₽m) | ЦБСТ tie grade |
|---|---|---|---|
| ООО «Смарт Текнолоджис» | 7715934509 | 3,929.6 | Documented |
| ООО «Гагаринг» | 2312321660 | 2,159.0 | Documented |
| ООО НПО «Киловатт» (Шестопалов) | 4800016776 | 1,158.6 | Documented |
| ООО «ОПКБ Экспломет» | 1215235283 | 782.4 | Documented |
| ООО «Метаскан» | 1660349248 | 764.7 | Documented |

Next in line by revenue, with a documented tie and no match: ООО «БПР ЯРЛ»
(₽488.0m, one state contract), ООО «КРАВТ» (₽300.6m). Фонд «Наша Правда»
(₽984.9m of non-profit funds, not revenue) is outside the revenue ranking.

Total unlisted revenue across the five: **≈₽8.8bn** in FY2025 filed accounts,
all read from the signed БФО filings in `data/sources/`, not estimates.

**How firm the "listed" side is.** On 05.10.2026 the four official lists were
downloaded once each and searched by ИНН/ОГРН for every record whose sanctions
claim had rested on an aggregator. 21 records now cite their own official list
entries (59 entry files saved; the US listing dates come from OFAC's
recent-actions notices; the Ukrainian decrees cited by the GUR portal were read on
the Rada site, but the annex naming each entity could not be fetched, so those
Ukrainian entries rest on the portal's statement). The registry now reads 51 of
73 sanctions claims against an official list. For the other 22 records no official
US/EU/Swiss/UK entry prints their identifiers and the registry's claim is an
OpenSanctions match with no regime (topics «sanction.linked/control») or
Ukraine-only; they are recorded as unproven, not as designated. The public landing
page's count of sanctioned ЦБСТ-tied organisations was corrected from 35 to 27
for the same reason.

## 2. What "Documented" means here

Every ЦБСТ tie in the five-company table above is **t-doc** confidence in the registry's own
vocabulary: a primary document — not a press report, not an aggregator
snippet — states the relationship. The ties, in brief (full exhibits in each
packet):

- **Гаскар / СТИМС**: no longer in this table. See §3.
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

## 3. Two corrections about Гаскар (04.10.2026)

**First, the listing belongs to ООО «СТИМС», not ООО «Гаскар».** The registry had
attributed an EU/Swiss sanctions listing for "Gaskar Group" to **ООО «Гаскар»**
(ИНН 9710112989), when the listing's own printed identifiers (registration
number, tax ID, KPP, Skolkovo address) match **ООО «СТИМС»** (ИНН 7734436058), a
company renamed from Гаскар Групп on 19.11.2024. The two are separate legal
entities; a third, ООО «Гаскар Интеграция», is itself unlisted and its only link
to СТИМС so far is a name match (one of СТИМС's participants, Саитов Ренат
Фаритович, 20% since 07.07.2026, shares a full name with Гаскар Интеграция's
2019 general director; the registry treats that as an open question, not a fact).
ООО «СТИМС» now carries the EU (Council Implementing Regulation 2026/509,
entry 704) and Swiss (SECO, 21.05.2026, SSID 104739) listings with their own
printed identifiers.

**Second, ООО «Гаскар»'s own ЦБСТ tie is withdrawn.** It had been held as
documented on the assumption that «Гаскар Групп» in ЦБСТ's post 2095 (24.04.2026)
meant this company. The post prints no ИНН; a search for «Гаскар» in 2,474
@ANO_CBST posts on 04.10.2026 returned that one hit. The tie is now
"not established", so ООО «Гаскар» drops out of the table above (its ₽9.8bn
revenue is no longer counted), and СТИМС's own tie is graded t-open (ЦБСТ's post
names «Гаскар Групп» among the contour's EU-listed organisations, without
identifiers). The Гаскар packet is kept only as the record of that correction. Its
Canada entry (an OpenSanctions record under the name "EVR") has not been read
against Canada's list.

**Why this matters for submission**: naming the wrong legal entity in a
sanctions submission is the kind of error that gets a whole filing discounted.

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
- **Гагаринг, second pass (05.10.2026).** A read-only `claim-verifier` pass on the parts the first pass skipped (about 60 claims) returned 11 claims it could not confirm; the most serious were checked by the main session and fixed in the registry: the personal ИНН of Александров was a same-name Уфа namesake (ИНН 027313454520 from an Aleph match) and is replaced by the one the ЕГРЮЛ extract prints (231015713057); Барашков's birthplace has no source and is removed (his date of birth rests on one compiled report, a leak-database printout, and is reported, not documented); a 2023 welding patent attributed to him by name only is removed from the record; one press quote spliced a wire sentence with reported speech and is now two verbatim sentences; a thank-you quote is a forward of @RuFront, not Гагаринг's words; «член ассоциации» is not what the audit report says; the ГИСП record's address is not an exact match. The FY2024 restatement is now printed under the accounts table.
  **Still open from that pass:** the 36.8% holding in ООО «Авирон» rests on the company's own audit report (no register extract for Авирон is cited); the packet's "two live hh.ru postings" cites one exhibit; E1's date is the capture date (03.09.2026), while the audit opinion is dated 04.06.2026; the website, Telegram handle and Latin form in §1 carry no exhibit. The Гагаринг packet is still not fully verified.
- Several generator-level bugs (truncated exhibit descriptions, wrong
  document-type titles, an address wrongly flagged "no dated source") were
  fixed in `exhibits/build_evidence_packet.py` and all packets regenerated.

## 5. What is still open, stated plainly

A submission that hides its own gaps is worse than one that states them.

- **Same-name risk elsewhere.** The Гаскар case came from reading a printed
  identifier against a brand name. The 05.10.2026 official-list reading matched
  only on identifiers, never on names, for that reason; an official entry that
  prints no ИНН/ОГРН would not have been found.
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
  person-level sanctions matches more than on the five company packets above
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

- [ООО «Смарт Текнолоджис»](packets/ooo-smart-teknolodzhis.md)
- [ООО «Гагаринг»](packets/ooo-gagaring.md)
- [ООО НПО «Киловатт» (Шестопалов)](packets/ooo-npo-kilovatt-shestopalov.md)
- [ООО «ОПКБ Экспломет»](packets/ooo-opkb-eksplomet.md)
- [ООО «Метаскан»](packets/ooo-metaskan.md)
- [ООО «СТИМС»](packets/ooo-stims.md): listed (EU, Switzerland); tie graded t-open
- [ООО «Гаскар»](packets/ooo-gaskar.md): withdrawn from the set (§3); kept as the record of the correction

## 7. Recommended next step (not acted on — for Alexey to decide)

The cloud session's 03.10.2026 assessment proposed submitting this package
through proper channels: the EU, UK and US sanctions desks directly, plus
one partner organisation experienced in this kind of submission (OpenSanctions,
the KSE Institute, or B4Ukraine were named as examples). That is an
external-distribution decision this document does not make on its own —
flagging it here as the logical next step once:
1. Alexey has read and can stand behind every line in the five (six)
   packets, and
2. the media-law/PII review (§5) has actually happened for anything beyond
   the corporate facts in these packets specifically.

Nothing in this report or the packets has been sent anywhere. All
packets, this cover note, and the underlying registry corrections are on
`main`.
