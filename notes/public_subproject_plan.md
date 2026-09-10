# Public open-API sub-project plan (parked 2026-09-08)

**Status: parked for a future session — design/decisions only, not yet
executed.** No `scripts/export_public_dataset.py`, no `public/` directory,
and no `.github/workflows/` exist yet. This note is the reference for
whoever (human or a future Claude session) picks this up next; read it in
full before starting Deliverable 1.

## Context

The private investigation (`data/registry/*.json`, `docs/index.html`) mixes
open-government sourcing with paid/gated tools (Kontur.Focus Pro, checko.ru,
экг-рейтинг.рф, rusprofile.ru) and privileged research access (an OCCRP
Aleph key issued to the user personally as a project member, an OpenSanctions
journalist key granted on trust). None of that is reproducible by an outside
reader, which weakens the investigation's credibility as a public artifact —
a hostile reader can wave away any claim they can't independently re-derive.

The user wants a second, slimmer sub-project: same registry shape, same
entity/person universe, but its factual claims traceable ONLY to sources
anyone can freely re-check — official Russian government open-data
registries (ЕСИА-gated is fine), no paid aggregators, no privileged-access
data. Deployed publicly as a static site on GitHub Pages, built from a
`public/` subdirectory of this repo.

Decisions already made by the user (2026-09-08):
- **Location**: `public/` folder in *this* (private) repo — source stays
  colocated with the registry data it's built from.
- **Aleph**: excluded entirely — the API key is a personal OCCRP grant, out
  of remit for a public redistribution.
- **OpenSanctions**: excluded from the public export — even though its
  underlying match logic could in principle be reverse-engineered from open
  registries, the user was given privileged access on trust and won't use
  that access to backdoor a public product.
- **GUR war-sanctions** (war-sanctions.gur.gov.ua): kept as OPEN — this is a
  no-login public Ukrainian government website, not a personal grant like
  Aleph/OpenSanctions, so it stays in the open-source bucket on its own
  merits.
- **Scope**: v1 publishes a **curated subset** — highest-tier / most
  newsworthy entities and their directly-linked people — not the full
  207/428-record roster.

## Source classification (from the 2026-09-08 pipeline survey)

**OPEN — usable directly, official/no-login/ЕСИА-gated government sources:**
egrul.nalog.ru + full-выписка flow, bo.nalog.gov.ru (БФО filings),
zakupki.gov.ru (44-ФЗ/223-ФЗ + РНП), pb.nalog.ru + nalog.gov.ru (disqualified
directors, subsidiary-liability, director/founder, ROМ), rmsp.nalog.ru,
Federal Notary Chamber pledge registry, ФССП open-data bulk CSV, ФСТЭК,
Rosgvardia's 5 registries, МЧС fire licenses, favt.gov.ru, Roscosmos,
RKN (comms + frequency), pub.fsa.gov.ru, reestr.digital.gov.ru, br.fas.gov.ru,
proverki.gov.ru, Rospatent (searchplatform + fips.ru, raw-curl/windows-1251
caveat noted), rk.2035.university, Rosreestr НСПД, war-sanctions.gur.gov.ua.
Plus all local derivation code (`mine_leads.py`, `extract_registry.py`,
`build_relationship_graph.py`, etc.) — no data-source restriction, it's our
own logic.

**EXCLUDED from the public export:** Kontur.Focus Pro, checko.ru,
rusprofile.ru, экг-рейтинг.рф, gisp.gov.ru (WAF/browser-only), leader-id.ru,
kad.arbitr.ru, rupep.org, reveng.ee (needs its own key), VK/Telegram API
data (token-gated, ToS concerns for redistribution), OCCRP Aleph,
OpenSanctions.

This list becomes a literal allow-list keyed on how each `sources.json`
entry was captured (see Deliverable 1).

## Platform constraint — resolved: separate hosting repo

GitHub Pages serves exactly one live site per repo (one source: a branch +
folder). This repo's Pages is already configured to `/docs` on `main` for
the *existing* private brief, so the public sub-project cannot also go live
under this same repo's Pages without displacing that site.

**Resolution (user decision, 2026-09-08):** the sub-project's *source*
stays in `public/` on `main` of this (private) investigation repo, but its
*build output* gets pushed to a **separate, dedicated hosting repo** — slug
TBD, user will supply it — whose sole purpose is serving the built static
site via its own Pages. This keeps the current `/docs` Pages site fully
untouched, keeps the public sub-project's source colocated with the
registry data it's built from, and gives the public site its own
independent URL. The GitHub Actions workflow (Deliverable 3) builds from
`public/` on this repo and pushes the output to that hosting repo (e.g. via
a deploy key / `peaceiris/actions-gh-pages`-style cross-repo push) once the
slug is known — this is a "hand the user an exact command / confirm the repo
exists" step, not something to guess a name for and create unprompted.

## Deliverables

**1. `scripts/export_public_dataset.py`** (new, local-only, no network).
Reads `entities.json`, `people.json`, `sources.json`, `relationship_graph.json`.
For each entity/person, walks every field that carries a `source_id`, resolves
it against `sources.json`, and keeps the field only if at least one supporting
source is OPEN-tagged (per the allow-list above) — a fact resourced solely
from Kontur/checko/экг-рейтинг/rusprofile/Aleph/OpenSanctions gets dropped
from the public copy, not fabricated a fake open citation. Strips wholesale:
`_raw`, `_corrected`, `_verified*`, `_origin`, all `*_checked_at`/
`*_screened_at` bookkeeping, `notes` (internal working commentary), and any
carry-forward match field sourced from an excluded screener
(`opensanctions_matches`, `aleph_matches`, `kontur_focus_matches`,
`ekg_rating_matches`, `rusprofile_*`). Person PII (`dob`, `birthplace`,
`address`, `inn_personal`, `photo`) defaults to excluded unless the
supporting source is itself OPEN (e.g. an ЕГРИП entry) — same logic as the
entity-field filter, not a blanket carve-out.
Curation filter (v1 scope): keep only entities meeting an explicit
newsworthiness bar to be finalized against the real `tier`/`sanctions[]`
values when writing the script (e.g. `tier <= 1` or `sanctions` non-empty
or flagged `tier_basis`), plus every person directly linked to a kept entity
via `roles[]`/`director`/`founders`.
Output: `public/data/entities.json`, `public/data/people.json`,
`public/data/relationship_graph.json` (edges' `source_id` replaced with a
public-safe citation string or dropped), `public/data/sources.json`
(OPEN-tagged entries only, with live URLs — no local `sha256`/file paths),
and a `public/data/methodology.json` stats summary (counts kept/dropped per
category, for the About page).

**2. `public/` static site.** Vanilla JS + D3 (reuse the force-graph code
already built for the 2026-09-08 Artifact/`build_relationship_graph.py`
output, adapted to fetch `data/relationship_graph.json` at runtime instead
of baking data into the HTML at generation time — a deliberate divergence
from `docs/index.html`'s all-baked-in approach, since the public site needs
to regenerate from a script, not be hand-edited).
- `index.html` — landing/overview + methodology summary.
- `explorer.html` — searchable/filterable entity table + the relationship
  graph viz.
- `entity.html?slug=X` — client-rendered detail view sourced from the JSON
  (avoids needing a per-entity static-file build step; can add static
  per-entity pages later via `build_company_profile.py`'s Jinja2 pattern if
  needed for SEO/shareability).
- `about.html` — the OPEN/EXCLUDED source breakdown itself, published as a
  transparency page: exactly what this site does and doesn't draw on, and
  why (the Aleph/OpenSanctions restraint is worth stating plainly — it's a
  credibility asset, not just an internal policy).
Apply the `dataviz`/`artifact-design` skill conventions already used for the
relationship-graph Artifact (categorical palette, dark/light theme tokens,
D3 force-sim + zoom/drag), styled as a real public-facing site rather than
a raw Artifact.

**3. `.github/workflows/`** — a build workflow (triggered on push to
`main` touching `public/` or `data/registry/`, or manual dispatch) that runs
`export_public_dataset.py` and pushes the resulting `public/` tree to the
hosting repo (see platform-constraint resolution above).

## Execution order (for the future session that picks this up)

1. Get the hosting-repo slug from the user (still outstanding).
2. Read actual `tier`/`sanctions[]` values in `entities.json` to fix the
   curation cutoff concretely (currently a placeholder rule above).
3. Build `scripts/export_public_dataset.py`, run it, hand-inspect the output
   for leaks (grep for `sha256`, `data/sources`, `dob`, `inn_personal`,
   `_raw`, any excluded-source string) before it ever touches `public/`.
4. Scaffold `public/` site against the exported JSON; test locally
   (`python3 -m http.server` from `public/`) in a real browser — golden
   path (load explorer, click an entity, view the graph) and an edge case
   (an entity with only 1-2 open-sourced fields renders sanely, not blank).
5. Add the GitHub Actions workflow that builds from `public/` and pushes to
   the hosting repo once its slug is known.

## Verification

- `export_public_dataset.py`'s output hand-audited for the four leak classes
  above before first publish.
- Local browser test of `public/` (golden path + thin-record edge case) —
  per CLAUDE.md's UI-testing rule, not just "the script ran."
- `check_tag_balance.py` (or an equivalent scoped check) on any generated
  static HTML.
- The About/methodology page's OPEN-source list cross-checked once more
  against `notes/full_pipeline_catalogue.md` before publish, since that
  catalogue may have grown since this session's snapshot.
