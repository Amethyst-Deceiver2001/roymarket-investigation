# Presentation review: data, narrative, audiences (2026-09-30)

An internal review of how the investigation is presented now, and how it should
be presented to two audiences: general readers and specialists. It covers the
published `docs/` site, the seven case notes, `STYLE_GUIDE.md` and
`data/registry/`. **Aggregate figures in §1 come from one quick pass over
`entities.json` on 2026-09-30. They are for planning only and must be
re-derived by a script before anything is published.**

## 0. Bottom line

The evidence is strong and the case pages are well built. What the site lacks
is the middle layer: one page that says **what the network is and why it
matters**, backed by the aggregate numbers only the registry can give.
Right now a general reader lands on a routing page with no thesis, and a
specialist lands on prose with no download. Both audiences need one new thing
each:

- **General readers:** a single lead story, one curated network picture (not
  the 1,136-node graph), and a Russian edition.
- **Specialists:** a sanctions-gap table, a per-entity evidence packet, and
  machine-readable exports (CSV and FollowTheMoney), with a
  methodology/provenance page to cite.

Fix §4's defects first. Some of them would hand a hostile lawyer an easy
opening.

## 1. What the data says in aggregate (not yet on any page)

From live records (239 entities, 437 people, 8,506 sources in `sources.json`):

| Measure | Value | Caveat |
|---|---|---|
| Entities with a ЦБСТ tie at `doc`/`open`/`press` grade | 61 (52 at `doc`) | `cbst_tie` is unset on 160 records, which is not the same as "no tie" |
| …of which carry any sanctions entry | 31 | |
| …listed by the EU, US or UK | about 28 | Regime strings were matched by crude text search; rebuild with a structured field |
| FY2025 revenue of ЦБСТ-tied entities that filed | ₽91.8bn across 37 filers | **₽59.6bn of it is one company, ООО «Центр управления городской аэромобильностью».** Without it, about ₽32bn. Always show that split. |
| Largest ЦБСТ-tied (`doc`) filers with **no** sanctions entry in the registry | ООО «Смарт Текнолоджис» ₽3.93bn, ООО «Гагаринг» ₽2.16bn, НПО «Киловатт» (Шестопалов) ₽1.16bn, ОПКБ Экспломет ₽0.78bn, Метаскан ₽0.77bn, ЦКБР ₽0.55bn, Авирон ₽0.27bn | Each must be checked against current EU/UK/US/UA/CH/JP lists before being called undesignated |
| Entities with `government_contracts[]` | 25 of 239 | The recurring "no public contract" finding across cases is itself a pattern worth stating |
| Entities with `battlefield_evidence[]` | 7 | The thinnest layer. It is also the one general readers care about most |

Two stories sit in these numbers and appear on no page yet:

1. **The sanctions gap.** ЦБСТ's own channel names its residents, and EU
   package 20 hit several of them. The network then points to others with
   billions in revenue that no Western list names. For specialists this is the
   most useful output the project can make.
2. **Money without contracts.** Billions in filed revenue, and almost no
   zakupki trail. The same gap shows up in Гагаринг, Пиранья and Архангел, and
   in aggregate it suggests the money runs through closed ГОЗ (state defence
   order) channels, «народный ОПК» fundraising or intermediaries. State it as
   a pattern with its own calibrated hedge, not seven times as a footnote.

## 2. Who the audiences are and what each needs

| Audience | Question they bring | What serves them | Register (STYLE_GUIDE §1.1) |
|---|---|---|---|
| General EN reader | What is this and why should I care? | One story, one picture, three named people, one number | Investigative, FP-analysis for the frame |
| General RU reader (inside Russia and in exile) | Who near me is doing this, and who pays? | The same story, *written* in Russian, and regional hooks (Ульяновск, Тула, Краснодар) | RU register §1.7 |
| Other journalists and researchers | Can I reuse this and build on it? | Searchable profiles, an ego-network graph, bulk data, a methodology page to credit | Forensic |
| Sanctions analysts (EU EEAS/RELEX, OFSI, OFAC, Ukraine's NSDC and GUR, NGO submitters such as B4Ukraine and KSE Institute) | Is there a designation case, and can I match it? | Identifiers, a statement-of-reasons draft, primary-document exhibits, a list of who is not yet listed | Flattest forensic |
| Compliance and screening vendors (bank KYC, OpenSanctions, Dow Jones, LSEG) | Can I ingest it? | Stable IDs, FtM/CSV, aliases and transliterations, DOB, as-of dates | None: this audience needs data, not prose |
| Lawyers, courts, prosecutors | Does it hold up? | Chain of custody, hashes, capture dates, a stated methodology, a Berkeley Protocol-style account of collection and verification | Expert-witness |

The site now serves the third row reasonably, the first row partly, and the
others hardly at all.

## 3. What already works (keep it)

- **Case pages** (`docs/cases/*.html`). Each headline states the finding flat.
  The "Officially / Actually" table is the organising unit STYLE_GUIDE §1.4
  asks for. Every claim carries an `[sNNNN]` id and a grade. Each page ends
  with "What is not established". This is close to the house style of
  OCCRP and Bellingcat, and it is the project's strongest asset. Пиранья is
  the model case: the EU's text, the company's own shop copy and its own
  filings are set side by side, and the page stops without comment.
- **The three-grade vocabulary** (`doc`/`press`/`open`) with visible chips.
  Specialists need exactly this.
- **Registry-first generation.** Profiles and cases are rebuilt, not
  hand-edited. That makes versioning and exports cheap (§5.2).

## 4. Defects to fix before wider promotion

1. **Internal notation in published prose** (STYLE_GUIDE §3.5). Rendered case
   pages include "Registry position: tier manufacturer" (5 pages),
   "Registry record `ooo-…`" (7), "scan log" (5), "local scrape" (3). Visible
   `t-doc`/`t-open` labels appear in `docs/story.html` (12 times). Translate
   these into reader terms, for example "zakupki.gov.ru search by ИНН,
   05.09.2026" instead of "scan log", and remove slugs.
2. **Two different definitions of `open`.** The landing page says "unresolved:
   not published as fact". `story.html` says "open-source / social-media
   sourced, not yet document-confirmed". A specialist will notice. Keep one
   definition in one place (`scripts/build_case_pages.py`) and import it
   everywhere, `story.html` included.
3. **Grading a self-report as `press`.** In `story.html`, Story one grades
   Барашков's RT interview claim ("hundreds" of targets) `press`. The outlet
   is a named press source, but the claim is the founder's own. The case
   pages handle this correctly with wording such as "the company's posts about
   what others say". Apply the same distinction in `story.html`.
4. **OpenSanctions matches on the public site.** Four case pages cite an
   "OpenSanctions match" as the basis for an owner's or company's listing
   (Пиранья three times). This raises two problems. (a) The parked public-site
   plan (`notes/public_subproject_plan.md`) says OpenSanctions stays out of
   public output because access was granted on trust. It is worth deciding
   whether that rule applies to `docs/` too; the public OpenSanctions website
   is citable, but the API key is not. (b) For specialists, a match is not a
   listing. Where a case names a regulation (Пиранья's 60% owner, "EU
   Regulation 2026/1843"), get the Official Journal text and cite that as
   `doc`, or leave the claim out.
5. **Stale counts.** The landing page says 242 entities and 7,951 sources.
   The live registry has 239 or 240 live entities (242 raw) and 8,189 to 8,506
   sources, depending on what is counted. Generate these figures at build time
   and label them ("live records").
6. **Cases lack an "as of" line.** Each note opens with its drafting date.
   Specialists need "facts as of DD.MM.YYYY; last rebuilt DD.MM.YYYY" and a
   change log per case, so that a sanctions submission can cite a fixed
   version.

## 5. Recommendations

### 5.1 General audience

**A. Write one lead story, and make it the front door.** The landing page
routes but does not argue. The general reader needs 1,500–2,500 words in
FP-analysis mode (§1.5). Open cold on one named person. The founder of Овод,
Черезов, shot in July 2026, is the strongest human open the cases offer. Then
zoom out to the system: a state-convened body (ЦБСТ) calls its suppliers
«резиденты», they turn over billions, a handful of them got sanctioned, most
did not, and almost none of the money shows up in public procurement. Close
with the sanctions gap as the thesis. Every paragraph links down to a case;
every case links down to profiles. This is the three-layer model
(story → case → record) that ICIJ's Offshore Leaks and OCCRP's
Laundromat projects both use, and the site already has the bottom two layers.

**B. Replace the hairball as a first visual.** Research on network
visualisation is consistent: general readers do not read force-directed
graphs of more than a few dozen nodes. Narrative network work (Bach et al.,
*Narrating Networks*) points to fixed, annotated ego networks and
step-by-step reveals instead. Concretely:

- One hand-curated **hub-and-spoke diagram** of ЦБСТ, the seven case
  entities and perhaps five other named residents. Mark each spoke with its
  tie grade and each node with sanction status: EU/UK/US, Ukraine only, or
  none. The landing page's `net-motif` SVG already is this diagram without
  the data. Put the data in, and it becomes the sanctions-gap picture.
- On each case page, a **static ego network** (one hop, at most 15 nodes),
  generated with `graph_query.py`. `build_case_pages.py` already embeds a
  "graph excerpt", so check it stays inside that budget.
- Keep `relationship-graph.html` as the explorer for researchers, but open it
  on a single node's neighbourhood (for example, ЦБСТ at depth 1) with
  "show all" as an option. The plan notes say minimum degree is still 1. At
  1.86 MB the page is also slow on mobile, which is where most general
  readers are.

**C. A repeatable visual grammar.** Two card types, used everywhere: the
"Officially / Actually" pair (ОКВЭД versus product), and the "money without
a contract" strip (revenue bars against a zero for zakupki). Readers learn a
card once and then read seven cases faster. These make good social cards
too.

**D. A Russian edition, written, not translated.** This is the biggest reach
gap. The findings matter most to Russian readers: regional hooks, named
local companies, «народный ОПК» fundraising that uses their donations. The
style guide already describes the RU register. Start with the lead story and
Пиранья and Овод, the cases with the most local press value.

**E. Put the self-incriminating copy first.** «От 1 штуки, отправим в день
заказа», «Убийца Abrams», «Санкции не помогли». General readers remember a
company's own words longer than a regulation number. `marketing_claims[]`
exists on only 12 entities; filling it is cheap and pays off on both
audiences' pages.

### 5.2 Specialist audience

**F. A sanctions-gap table.** One generated page and one CSV: every entity
with a ЦБСТ tie of `doc` grade, its ИНН/ОГРН, latest revenue, tie source, and
a column per regime (EU, UK, US, CH, JP, CA, AU, UA/NSDC, UA/GUR), each cell
set to *listed (regulation, date)*, *not listed (checked DD.MM.YYYY)* or
*not checked*. This needs a structured `regime` code on `sanctions[]` in place
of free text. §1 shows the free text cannot be counted reliably. This table
is what EEAS desk officers, OFSI and NGO submitters actually use.

**G. A per-entity evidence packet** (PDF plus a folder), modelled on the EU
Official Journal's own "statement of reasons" layout, which is the form a
designating authority has to write anyway:

1. Identifiers: every name form, Latin transliterations as screeners search
   them, ИНН, ОГРН, address, and every director and owner with DOB.
2. A draft statement of reasons in three or four sentences, forensic register,
   every sentence footnoted.
3. Numbered exhibits: the EGRUL extract, БФО filings, archived posts, with
   capture date and SHA-256 per exhibit.
4. What is not established.

`build_company_profile.py` already holds most of this. A PDF of
`ano-npts-ushkuynik` exists, so part of the pipeline is already there. Start
with the seven unsanctioned `doc`-tied filers in §1.

**H. Machine-readable exports.** Specialists and screening vendors do not
parse HTML. Publish:

- **FollowTheMoney (FtM) JSON lines**: `Company`, `Person`, `Ownership`,
  `Directorship`, `Sanction` and `Documentation` entities. This is the format
  OpenSanctions and OCCRP Aleph ingest natively, so the registry can be
  loaded into their tools and cross-matched with no custom work. The
  `followthemoney` Python library validates the output.
- **Flat CSVs** of entities, people, ties and sources for everyone else.
- The same filters as the parked public-site plan: no `notes`, no internal
  fields, PII only where the source allows it.

**I. Methodology and provenance pages.** STYLE_GUIDE §3.4 promises a
provenance page, and it does not exist. Courts and designating authorities
need an account of how material was collected, preserved and verified. The
Berkeley Protocol (OHCHR/UC Berkeley, 2020/2022) is the reference framework
that international tribunals recognise. Map the project's practice onto its
stages (online inquiry, preliminary assessment, collection, preservation,
verification, analysis) on one page. Add the source-class table
(government registries, own channels, press, aggregators), the confidence
vocabulary, the hash catalogue and a correction policy. A dated corrections
log is itself a credibility asset.

**J. Stable citation.** Keep `sNNNN` and slugs permanent (the registry
already guarantees this with `_merged_into`). Add a versioned snapshot per
release (a git tag plus a dated `data/` export), so that "RoyMarket registry
v2026-10-01, entity `ooo-skb-piranya`" is a citation that cannot change
underneath a submission.

## 6. Suggested order

1. Fix the §4 defects (a day's work, all in generators).
2. Add structured `regime` codes to `sanctions[]`, then build the
   sanctions-gap table and CSV (F).
3. Build the methodology/provenance page (I). The evidence packets and the
   lead story both need it to link to.
4. Write the lead story (A) and the curated hub diagram (B). Get the user's
   explicit go-ahead before pushing, per CLAUDE.md "Publishing".
5. Build evidence packets for the undesignated `doc`-tied filers (G) and the
   FtM/CSV export (H). Decide whether this reuses `public/`
   (`notes/public_subproject_plan.md`) or lives under `docs/data/`.
6. Russian edition (D), starting with the lead story.

## Sources consulted

- FollowTheMoney data model:
  https://docs.aleph.occrp.org/developers/explanation/followthemoney and
  https://www.opensanctions.org/docs/bulk/json
- Berkeley Protocol on Digital Open Source Investigations:
  https://humanrights.berkeley.edu/programs/investigations/berkeley-protocol
- Bach, Riche, Carpendale, Pfister, *Narrating Networks* (2018):
  https://arxiv.org/pdf/1801.01322
- Yoghourdjian et al., *Exploring the Limits of Complexity: A Survey of
  Empirical Studies on Graph Visualisation*: https://arxiv.org/pdf/1809.00270
- B4Ukraine, sanctions submissions and document intake:
  https://b4ukraine.org/what-we-do/whistleblower

---

## Addendum 2026-10-02: after the reader-layer rebuild (main at `cb248c3`)

The 09-30 review above is partly overtaken. The case pages, profiles and
`story.html` it critiqued are archived. §4 defects 1–3 and 5 went with them.
The direction now in `notes/rebuild_plan.md` (chain views as the main exhibit,
one design system, B4 citations with no internal notation, a graph explorer
for neighbourhoods only) answers §5 B, C and E. What follows is only what is
still open or new.

### Checked and sound

- The landing page counts match the registry: 73 ЦБСТ ties (60 doc, 13 rep),
  35 of them sanctioned.
- The Сидякин post-618 opening is the best self-incrimination open the project
  has had.
- The «Булат» chain view prices contracts per unit and puts the donor's
  audited stock (50 units) beside 17 handover posts. Specialists can use this
  as it stands.
- `check_registry.py` raises 29 errors in a cloud checkout. All are `media[]`
  files missing because `data/sources/` is not in the clone. Two test files
  fail only on missing packages (openpyxl, bs4). Neither is a data defect.

### Still open, in priority order

1. **The hero product's sanctions rest on an aggregator.** On the landing page
   and in both chain views, Тримикс's "Switzerland, EU, US, Ukraine" is
   sourced to "Sanctions-list entries compiled by OpenSanctions". The work
   exists to support sanctions lobbying, so each regime should cite its own
   primary entry: OJ regulation and entry number, OFAC SDN entry, SECO
   annex, GUR page. Coverage Audit task 1 already covers this. Do it for
   every entity on a reader page before chain views go public.
2. **The public graph explorer contradicts the new reader rules.**
   `docs/relationship-graph.html` is still public at its URL, although the
   landing page no longer links it. It embeds schema v11, the old
   `t-doc`/`tier` vocabulary and raw `sNNNN` ids, and weighs 1.9 MB. Either
   take it off Pages until B6, or regenerate it from v12 with
   `reader_grade()`.
3. **The sanctions gap still has no page.** Of the 73 ЦБСТ-tied
   organisations, **38 carry no sanctions entry; 31 of those ties are
   doc-graded.** The largest by latest revenue are Смарт Текнолоджис
   ₽3.93bn, Гагаринг ₽2.16bn, ОПКБ Экспломет ₽0.78bn, Метаскан ₽0.77bn and
   Авирон ₽0.27bn. (Each needs re-screening against current lists before
   being called unlisted.) That is the lobbying deliverable. It belongs in
   A6 entity pages as a regime-by-regime table that includes "not listed,
   checked DD.MM.YYYY", plus one gap list.
4. **The definition of "Not documented" reads badly.** "The link must exist,
   but no document on file shows it" asserts what it admits it cannot show.
   Suggested: "Not documented: inferred from [what], with no document on file
   that shows it."
5. **Recipients are printed with unmarked euphemisms.** The chain view's
   handover list prints «участники спецоперации» and similar strings with no
   guillemets. They read as the page's own words (STYLE_GUIDE §5.1). Quote
   them and gloss them, or attribute the line ("as the donor puts it").
6. **"Reported" merges self-report and press.** That is fine for lay
   readers. Specialists need the distinction, so state the publisher type in
   each source note ("the company's own post", "press: Kommersant"). Most
   notes already do; make it a rule in `describe_source()`.
7. **Choose the next chain views by lobbying value.** The best candidates are
   products of unlisted, doc-tied makers that have contracts or handovers:
   Гагаринг «Кузнечик» (case note already written), then a Смарт Текнолоджис
   or Экспломет product once its record is read. «Пиранья» is already
   EU-listed, so it is lower priority for lobbying but strong for lay readers.
8. **Machine-readable output** (§5.2 H) and **a methodology page** (§5.2 I)
   are still absent. The landing page's "How this is made" paragraph is a
   start; the provenance and hash catalogue is not yet public.
9. **Russian edition.** It is still listed as "later". The landing page is
   generated and short, so a written RU landing page is the cheapest first
   step.

### Housekeeping

- Add a flag to `check_registry.py` that skips file-existence checks, and add a
  `requirements.txt` (pytest, openpyxl, bs4, jinja2), so cloud sessions can
  validate.
- The `claude/project-thread-v1pj0k` branch (status board, `--diff`,
  `--pull-queue`) is unmerged.
- Decisions waiting on the user: unit naming (the proposal in
  `rebuild_plan.md` is sound) and the graphic-content default (stills only,
  content warning).
