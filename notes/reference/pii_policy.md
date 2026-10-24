# PII handling: the full policy and its amendments

Moved verbatim from CLAUDE.md on 24.10.2026, when CLAUDE.md was cut to a short rulebook; stale facts corrected where marked. CLAUDE.md keeps the rule in one line and points here for the detail.

## PII handling

**Policy changed 2026-08-22 at explicit user direction. The former name+role
default no longer applies — do not restore it.**

Named individuals in this investigation are recorded with **full identifying
detail**: name (ФИО and Latin), date of birth, place of birth, address,
personal ИНН, and any other identifier that supports a match. The rationale
the user gave: these are public PEPs, and the output feeds sanctions
screening, where a date of birth is frequently the field that makes a match
legally usable rather than merely suggestive. The user supplies this data
where available.

Rules that still hold:

- **Every identifying field carries its own source.** A DOB or address with
  no `source_id` is left null, never inferred, never filled from a
  plausible-looking namesake. The scale-up in what gets published is a
  reason for more sourcing discipline, not less — see
  [[roymarket_project_goal]]: this material has to survive a hostile lawyer.
- **Photographs** are sourced from the subject's public or professional
  presence — their own channel, their company's site, press coverage, an
  official event. Not private or family imagery.
- **Individuals who are not PEPs, network principals, or affiliated
  participants** — a resident mentioned in passing, a private person named
  in a court filing unrelated to this network — are not in scope for this
  treatment. Ask before extending it to anyone who doesn't fit an already-
  established category below.

**Policy amended 2026-09-04 at explicit user direction, to add a second
in-scope category: confirmed participants of a network's own recruitment/
training/operational apparatus** — course students, instructors, chat
admins/moderators, named contacts — not just its owners/directors/officials.
Rationale the user gave: for an operation like Проект «Архангел» that trains
and equips people for combat drone operations feeding the war, a documented
participant is not a bystander — they are plausibly someone who goes on to
serve in the operations this investigation exists to document (see
[[roymarket_project_goal]]), and identifying them is itself a legitimate
finding, not incidental collateral. This is DISTINCT from indiscriminately
cataloguing every name that surfaces near the network — the bar is a
**confirmed** participation link (posted in the network's own chat, listed
as a course student/instructor, tagged admin, etc.), sourced the same way
any other identifying field is (see the sourcing-discipline bullet above).
A name that only appears as a stray mention, forwarded content, or someone
else's contact reference does NOT clear this bar on its own.

**Photographs**, for this category specifically, may be sourced from a
self-published Telegram/social profile picture in the network's own
chat/channel — this is the person's own chosen public-facing image on a
platform where the group itself has 1,000+ members, not private or family
imagery, even though it isn't press-sourced. The existing rule (own
channel/company site/press/official event) still governs PEPs and
principals; this paragraph only widens what counts as "public presence"
for confirmed affiliated participants.

**Policy amended 2026-10-02 at explicit user direction: everyone involved is a person of interest.** Anyone who takes part in the network's activity (a donor or volunteer who hands over equipment, a carrier, a seller, a signatory, a course participant) is in scope, with the same sourcing rule for every identifying field. A person who is merely connected (a family member with no stake or role in a company) is not; record such a person only as `graph_tier: "reference"` where a record is needed at all.

**Proportionality still applies.** Finding 500+ names in a single chat scan
does not mean 500+ full person records — triage for a real signal (exposed
phone number, distinctive photo, a named role/title in their own bio,
cross-referenced elsewhere in the network) before promoting someone to
people.json, the same judgment call already used for zakupki
vendor-mention triage and press-lead triage elsewhere in this file. When in
doubt on a specific name, it's fine to ask.

The earlier logged exception (an InformNapalm OSINT dossier carrying full
addresses and passport numbers) is no longer an exception; it is now
consistent with the standard.


- **PII scope, third category:** a seller (usually a sole trader) gets an entity record, and its owner a person record only on user direction, when it has a **documented link to a registry manufacturer or to РОЙ.МАРКЕТ**. A marketplace listing alone is not enough. (2026-10-02: an owner who is involved in the trade is a person of interest under the PII section's amended rule.) Same sourcing rule as every identifying field: the ИП's ИНН comes from its ЕГРИП extract, never from a plausible namesake, and no date of birth or address is filled without a source. Individuals recorded under this category so far: Братеньков, Маврин (person of interest, user, 2026-10-01). ИП Карпушин has an entity record but no person record.

