# Archived profile generator: how it worked (moved out of CLAUDE.md, 21.10.2026)

The generator and templates are in `scripts/archive/` and must not be run or extended (see CLAUDE.md, "Company profiles and case pages"). Kept for its rules on images and display.


`docs/profiles/<slug>.{html,md}` are per-entity profile pages, generated from
`data/registry/` by `scripts/build_company_profile.py` — not edited by hand
(a regeneration would silently discard hand edits, the same reason
`corrections.json` exists for `entities.json`/`people.json`). Run it after
any registry change that touches a profiled entity:

```
python3 scripts/build_company_profile.py --slug ooo-skb-piranya
python3 scripts/build_company_profile.py --inn 7300024069   # equivalent
python3 scripts/build_company_profile.py --all              # every non-adjacent entity
```

Local file processing over `data/registry/*.json` — no network calls, safe to
run directly/repeatedly. Always follow with
`python3 scripts/check_tag_balance.py docs/profiles/<slug>.html`.

`templates/company_profile.{html,md}.jinja2` are the two Jinja2 templates
(one script, two outputs — the section order and field coverage are kept in
sync between them by construction, not by hand). The HTML page links
`docs/assets/profile.css`, a standalone copy of `docs/index.html`'s design
tokens/classes (same `--paper`/`--ink`/`.tag`/`.t-doc` etc. — kept in sync by
hand since profile pages didn't exist when `index.html`'s `<style>` block was
written) plus profile-specific additions (`.person-card`, `.meta-grid`, …).

Follows `STYLE_GUIDE.md`'s expert-witness/forensic register by construction:
Latin name primary with the Cyrillic ФИО/name shown alongside (never hidden
in a tooltip), legal-form abbreviation transliterated not translated, ИНН/
ОГРН as bare digits, and — the important one — **no internal notation in
visible prose**. A claim is cited by a short bracketed `[sNNNN]` id resolved
in the page's own "Sources cited" table (locator + captured/as-of dates, no
sha256 — the hash belongs on a site-wide provenance page this project
doesn't have yet, not repeated on every profile), never by printing a raw
`source_id`/registry-field name. A person's freeform `notes` field is **not**
dumped into the page — it's an internal working note (often containing
passport/phone numbers alongside research-process commentary); only the
structured PII fields already vetted under the PII policy below (`dob`,
`birthplace`, `address`, `inn_personal`) render on the page.

**Images**: `entities.json`'s `images[]` and `people.json`'s `photo` already
point at `docs/images/<file>` (the publish-ready copy) — `data/sources/` is
the gitignored raw archive, not part of the published site. The HTML output
only embeds an `<img>` when a `docs/images/` copy actually exists (checked at
build time); otherwise it falls back to a text citation so a photo that's
only in `data/sources/` doesn't render as a broken image. The Markdown
output isn't published, so it links `data/sources/` paths directly. This
means a fresh `battlefield_evidence[]`/`images[]` entry (e.g. from
`scripts/tg_media_pull.py`) needs its file copied into `docs/images/` before
it'll actually appear in the HTML profile — pulling the media isn't enough
on its own.

Ground/satellite views of a facility are just `images[]` entries distinguished
by caption text (e.g. `_ground.jpg`/`_satellite.jpg` naming, already used at
`ooo-aeromaks`) — there's no separate schema field for them.

## From CLAUDE.md (moved 24.10.2026)

## Company profiles and case pages: archived 2026-10-02

**Withdrawn at user direction, not retrofitted.** The case pages, the company/person/product profiles, the profile index, the old landing page and `story.html` moved from `docs/` to `exhibits/archive/site_2026-10-02/`; their generators (`build_case_pages.py`, `build_company_profile.py`, `build_person_profile.py`, `build_product_profile.py`, `build_profile_index.py`) and `templates/` moved to `scripts/archive/`. Do not run or extend them. New reader pages are built after the design system redo and a new landing page (`notes/rebuild_plan.md`, track A), and carry no internal notation: no source ids, slugs, field names or file names; sources are cited in plain words with a public link. Shared display helpers (`ru_date`, `source_type_label`) are in `scripts/display_helpers.py`. The text below describes the archived generator and is kept for its rules on images and PII fields, which still apply to new pages.

The generator's description (Jinja templates, `[sNNNN]` citation style, image handling) moved to `notes/reference/archived_profile_generator.md`. Rules from it that still apply elsewhere: a person's free-text `notes` field is never put on a page (it holds passport and phone numbers); only the structured PII fields vetted under the PII section render; an image is embedded only if a `docs/images/` copy exists, and `docs/images/` is public (see Media).

### Product profiles and `relationship_type`

Product profiles (`build_product_profile.py`, `FLAGSHIP_PRODUCTS`; archived 2026-10-02) and the `related_entities[].relationship_type` vocabulary are documented in `notes/reference/script_notes.md`. Standing rules: extend `FLAGSHIP_PRODUCTS` one real product at a time; set `relationship_type` from `graph_contract.RELATED_ENTITY_RELATIONSHIP_TYPES` whenever adding a `related_entities[]` entry; never populate `competitor` without a sourced claim.



### Publishing history

**Changed 2026-10-02 at user direction: the site is withdrawn pending a redesign.** `docs/` (repo Settings → Pages → `/docs`) now holds the generated landing page (`docs/index.html`, from `python3 exhibits/build_landing.py --out docs/index.html`, live since 02.10.2026 at user direction; it replaced the holding page), and `docs/images/`. The graph explorer (`relationship-graph.html`) was retired in its current form on 02.10.2026 at user direction: the page is in `exhibits/archive/site_2026-10-02/`, its refresh script and test in `scripts/archive/`; do not restore it. A replacement is B6 in `notes/rebuild_plan.md` (neighbourhood on demand, v12 grades). The seven case studies (case notes still in `notes/case_study_<slug>.md`) and all profiles are archived (see "Company profiles and case pages"). Order of work: design system redo, new landing page, then new pages. Until the public cutoff, new reader pages (chain views first) go out as **private Artifacts for preview** only. The landing page is generated by `exhibits/build_landing.py` (`--preview` for the artifact, which links chain views to their preview artifacts); add a product to its `CHAINS` table when its chain view is published. Every number on it is computed from the registry. The public build links a chain view only once `docs/chain_<slug>.html` exists, and copies only the logos it shows into `docs/images/media/`; a chain's own pictures (faces included) never reach `docs/` through it.

**Changed 2026-09-21 at user direction: the old written brief is no longer public at all.** `docs/dossier.html` (the former `docs/index.html`) is moved to `notes/dossier_draft.html` and is **not** linked from any published page — the user's stated reason: it's a first-draft prose document whose facts should have been migrated into `data/registry/*.json` rather than kept as free text, and it must not ship as a public file. Treat it as an internal working note:
- No page links `dossier.html` or the draft; don't add one. Its frozen 2026-08-21 snapshot (which `extract_registry.py` reads) moved from `docs/_archive/` to `notes/archive/` on 2026-10-02, because `docs/` is public.
- `scripts/id_patterns.py`'s "already documented?" cross-check and `scripts/check_tag_balance.py`'s default target were repointed to the new path (the former, `docs/index.html` the latter) — keep them pointed at `notes/dossier_draft.html`, not a `docs/` path, if this file is touched again.
- The standalone Artifact companion to the old brief (5450bf7e) was retired on 2026-10-02 at user direction after an audit (`notes/brief_leftovers_20261002.md`); a local copy is `data/sources/ARTIFACT_20260826_infrastructure-entity-brief.html`. Other Artifact pages are a separate publish channel from `docs/`; ask before deleting one.
- Real, still-unregistered facts in `notes/dossier_draft.html` are a backlog, not something to re-publish: migrate them into `corrections_entities.json`/`corrections_people.json` like any other correction, the same as the rest of this project's registry-is-truth discipline.

