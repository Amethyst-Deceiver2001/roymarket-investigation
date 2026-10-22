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
