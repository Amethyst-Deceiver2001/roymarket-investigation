# Methodology and provenance — DRAFT

> **Status 24.10.2026:** The live draft of the reader-facing methodology page; its open gaps are listed at the end. Not published.

**Status: draft for the author to rewrite, 02.10.2026.** Written in the expert-witness register (STYLE_GUIDE §1.4, flattest). Numbers are as of the date above and come from the registry; regenerate them before publishing. The reader-facing text runs to the "Drafting notes" section, which is internal and goes before publication.

Structure follows the six phases of the *Berkeley Protocol on Digital Open Source Investigations* (OHCHR and the Human Rights Center, UC Berkeley, 2022): online inquiry, preliminary assessment, collection, preservation, verification, investigative analysis. Each section says what is done, and where it applies, what is not done.

---

## What this investigation records

This investigation documents the companies, people and money around АНО «Центр беспилотных систем и технологий» (ЦБСТ), a Moscow non-profit that convenes Russian drone and electronic-warfare makers, and РОЙ.МАРКЕТ, the closed marketplace through which its «резиденты» sell to the military. It records who owns and runs each company, what it makes, who buys it, and what reaches the front.

Every fact sits in one structured registry. Published pages are generated from it and never edited by hand. A fact corrected in the registry is corrected on every page at once.

## 1. Online inquiry: where material comes from

Material comes from six classes of source.

| Class | Examples | What it can show |
|---|---|---|
| Russian state registers | Company register extracts (ЕГРЮЛ) and sole-trader extracts (ЕГРИП) from the Federal Tax Service; founding documents filed with the register; annual accounts from the state register of accounting statements (ГИР БО); state procurement records (zakupki.gov.ru); arbitration court rulings; Rospatent patent and trademark records; the industry ministry's product catalogue (ГИСП) | Identity, ownership, directors, revenue, contracts, products, as the state records them |
| The parties' own channels | ЦБСТ's Telegram channel; makers' and donors' channels, websites and marketplace listings | What each party says about itself and the others |
| Press | Named Russian and international outlets | Reported claims, attributed to the outlet |
| Official sanctions lists | EU consolidated list, US OFAC SDN list, UK Sanctions List, Swiss SECO list, Ukraine's state register and defence intelligence portal | Whether, when and under which act a company or person is listed |
| Aggregators | OpenSanctions, OCCRP Aleph, commercial company-data sites | Leads to a primary document; never the document itself |
| Investigator's own captures | Satellite and street-level views, screenshots | What a place or page looked like on a stated date |

Telegram is monitored with the investigation's own collection tool, across 57 channels as of this writing. Register documents are downloaded from the state services themselves. Sanctions lists are downloaded weekly in full from the four official publishers and matched by identifier.

## 2. Preliminary assessment: a lead is not a fact

Searches, text-mining passes, screening tools and aggregator hits produce leads. A lead enters the record only as an open question that names what is unverified. It becomes a fact only through the steps in §3 and §5.

Three rules apply at this stage:

- **A name is not an identity.** A company name in a post is resolved to a registered legal entity only through an identifier the company prints itself (on its own site, in its own filing) or through a named person the register confirms. A name search in the company register alone does not resolve it: several unrelated companies often share a name.
- **A sanctions match needs an identifier.** A list entry counts only if it carries the company's ИНН or ОГРН, or the person's date of birth or personal ИНН. Name similarity alone never counts.
- **An absence is reported with its search.** "Not found" is written only with the exact query and the number of results it returned.

## 3. Collection: the original document, in its own language, read in full

A fact enters the record only from the original document, normally in Russian, read in full: the register extract, the filed accounts, the charter, the court ruling, the Telegram post and the documents it links. English summaries, search snippets, machine translations and third-party paraphrases are leads only.

Scanned documents are run through text recognition, and where a fact depends on the scan, the recognised text is checked against the image.

Each document is saved with a name that states what it is, the identifier it concerns and the date it was obtained. Two dates are kept apart: the date the document was obtained, and the date it speaks to (a 2026 download of 2024 accounts speaks to 2024). Only a person who has read the document records the second date.

## 4. Preservation: copies, hashes, public snapshots

- **Local copies.** Every source is kept as a file. Each of the 8,935 source records carries the SHA-256 hash of its file, computed when the file was catalogued. A later copy can be checked against that hash.
- **Public snapshots.** Telegram posts and web pages that a record cites are submitted to the Internet Archive's Wayback Machine. The capture date and the hash of the archived bytes are recorded. A reader can open the public snapshot even if the original is deleted.
- **Edited posts.** ЦБСТ edits its own posts after publication; company names have been removed from posts that once carried them. Where a forward of a post preserves the earlier text, the forward is archived as a separate source and the difference is recorded.
- **Register documents** carry no public link. They can be requested again from the Federal Tax Service by the identifier given, and the result compared with the hash on file.

## 5. Verification

- **Identifiers are checked arithmetically.** Every ИНН and ОГРН is validated against its control digits. This has caught a transposed ОГРН in a published text and two personal ИНН wrongly attributed to companies.
- **Quotations are verbatim.** Quotes are taken from the original Russian, character for character, with typos kept and marked [так в оригинале]. A quote that cannot be checked against its source is not used.
- **Self-reports stay self-reports.** A donor's or volunteer's post about a delivery is recorded as that party's own claim. It is upgraded only when an independent second source confirms it, such as the receiving unit's letter of thanks.
- **Faces do not identify.** A person in a photograph is named only where a source names them.
- **Each identifying detail about a person** (date of birth, address, personal ИНН) carries its own source, or is left empty.

## 6. Analysis: grades and what a link does not prove

Every link in the record carries one of three grades:

| Grade | Means |
|---|---|
| **Documented** | A primary document shows it: a register extract, a state contract, filed accounts, a trademark or patent record, an official list entry |
| **Reported** | One party's own word (its posts, website or listings), or the press |
| **Not documented** | Drawn to complete the picture, with no document on file; the record says what is missing |

As of this writing, the network's 2,182 links grade 1,793 documented, 355 reported and 34 not documented.

The grade belongs to the evidence, not to the conclusion. Three limits follow:

- A delivery to a unit does not show the equipment was used in combat. Units in the rear, and inside Russia, receive equipment too.
- A seller of a maker's goods is not thereby an authorised dealer, unless a document says so.
- Two entities are called unconnected only after a search of every path between them in the network, not only direct links.

## 7. Corrections

Corrections are made in the registry, with the reasoning and the document checked against, and are applied on every page at once. A correction is never made by deleting the warning that flagged it.

[A public, dated corrections log does not exist yet. See drafting notes.]

---

## Drafting notes (internal — delete before publishing)

**Facts this draft rests on, and where they come from.**
- 57 channels: non-comment lines in `config/channels.txt`, 02.10.2026.
- 8,935 source records, all with `sha256`: `data/registry/sources.json`.
- 2,182 links, 1,793 / 355 / 34: `relationship_graph.json` edge `grade`, schema v12.
- Checksum catches (Стратим ОГРН, two personal ИНН): CLAUDE.md, `check_registry.py` section.
- ЦБСТ post edits («Титан Северо-Запад», post 2080): CLAUDE.md, `tg_forward_diff.py`.
- Sanctions identifier-only matching: `scripts/sanctions_watch.py`.

**Gaps to close before this page can be published, or the text must change:**
1. **Wayback coverage is close to nil.** `source_archives.json` lists 2,408 URLs; 11 have a capture (tier 1: 5 of 637). §4 describes the practice, not the state. Either run `archive_sources.py run` batches on the Mac until tier 1 is covered, or say plainly how much is covered.
2. **Source titles are weak in places.** 80 sources are titled "Archived document" and 37 "Web page". Гагаринг's FY2025 audit report (s5333) is titled "Fedresurs register record". The evidence packets cite these titles, so fix the rules in `scripts/source_citation.py`.
3. **People's date and place of birth carry no field-level source** in `people.json` (only a per-person `sources` list). §5's last bullet claims more than the data shows. Either add `dob_source_id` and its kin, or soften the line.
4. **No public corrections log.** `corrections_*.json` hold 228 entity and 252 person corrections with reasons, but as internal records. A dated public log (what changed, when, why, without internal ids) is the credibility asset the review asked for.
5. **No hash catalogue for readers.** STYLE_GUIDE §3.4 promises a provenance page with hash, URL and capture date per artefact. `exports/csv/sources.csv` is most of it; decide whether it is published.
6. **The source-class table** should be checked against `graph_contract.SOURCE_PREFIX_GRADE`, which is what actually grades a link; aggregators grade "reported" there.
7. **Collection tooling and access.** The draft does not describe how blocked Russian sites are reached (tunnels, human-solved captchas) or which leaked datasets, if any, are used. Decide what the page says on both; a court will ask.
8. **The Berkeley Protocol citation.** Confirm the edition and wording you want to cite. The mapping to its six phases is ours, not the Protocol's.
