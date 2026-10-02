# Retired branch: `recovery/original-working-tree-2026-09-10`

Retired 2026-10-02 at user direction. The branch came from an experimental
GitHub Copilot session. It is preserved as a git bundle,
`copilot-recovery-2026-09-10.bundle` (20 MB, verified, tip `94635f4`), kept
offline in `data/sources/`, and optionally as the annotated tag
**`archive/copilot-recovery-2026-09-10`**. The cloud session's git proxy
refused the tag push, so the tag has to be pushed from a local clone. The
branch is deleted once the bundle is safe.

Restore with: `git fetch copilot-recovery-2026-09-10.bundle
archive/copilot-recovery-2026-09-10:refs/tags/archive/copilot-recovery-2026-09-10`.

## What it held

- **The pre-reroot history.** 323 commits by AK, 18.08.2026 (`92bc852`,
  migration out of wb_watch) to 08.09.2026 (`21c6aae`). Main's history now
  begins on 24.09.2026 with no parent, so this tag is the only place in the
  repo where the dated commit record from 18.08 to 08.09 survives. Read it
  with `git log archive/copilot-recovery-2026-09-10`.
- **One snapshot commit** (`94635f4`, 10.09.2026, "Recover original working
  tree snapshot", co-authored by Copilot App). It holds the uncommitted
  working tree as of that day, verbatim and not rebuilt: 20 files.

## Checked against main (`cb248c3`) on 2026-10-02

Every added line of the snapshot was compared with main:

| Snapshot content | State on main |
|---|---|
| АО «РОСС» `battlefield_evidence` from @nashapravdafond post 240 (21.02.2024), naming it maker of «Взгляд»/«Наблюдатель» | Present (`ao-ross`, as_of 2024-02-21); only the note wording differs |
| Фонд «ДАР», Фонд «Градислава» entries; ДАР's ₽1.213bn to Наша Правда | Present in `entities.json` and `notes/dossier_draft.html` |
| `corrections_people.json`, `people.json`, `_source_ids.json` additions | Present |
| `sources.json` additions | Present, except one `"_origin": "manifest"` bookkeeping flag |
| `notes/ddosecrets_catalog_survey.md`, `notes/public_subproject_plan.md`, `docs/images/nina-olegovna-yanykina_portrait_leader-id.png` | Identical on main |
| `notes/hub_insignia_design_notes.md`, `scripts/id_patterns.py` | Main is a superset |
| `notes/rebuild_plan.md` (+173 lines) | All lines are in `notes/archive/rebuild_plan_archive_2026-09-19.md` |
| `notes/founding_docs_gap.md` (Архангел rows) | Superseded by main's later regeneration |
| `CLAUDE.md`, `docs/index.html` edits | Superseded (the brief is now `notes/dossier_draft.html`; CLAUDE.md rewritten since) |
| `relationship_graph.json`, `scripts/build_relationship_graph.py` | Superseded: generated output, and the builder is now at schema v12 |
| `docs/profiles/ano-npts-ushkuynik.pdf` | In `exhibits/archive/site_2026-10-02/profiles/` |
| `_scan_sources_cache.json` (2.7 MB), `_source_content_cache.json` (6.3 MB) | Gitignored on main, regenerated locally by `scan_sources.py` / `inventory_sources.py` |

Files that exist only on the branch tip (401 in all) are the 389 retired
`docs/profiles/` pages, the old profile templates and generator (now in
`scripts/archive/`), the 21.08 brief snapshot (now in `notes/archive/`), the
`docs/assets/` ownership graph and profile CSS, and five gitignored caches.

**Conclusion: no registry fact exists only on this branch.** Nothing was
carried over.

## Caution

The tag contains `_kontur_focus_cache.json` (Kontur.Focus Pro, a paid
aggregator) and the old brief as a public `docs/` page. The repo is private.
Delete the tag, or move it to an offline bundle (`git bundle create
copilot-recovery.bundle archive/copilot-recovery-2026-09-10`), before the
repo is ever made public.
