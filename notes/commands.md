# Recurring commands

Copy-paste reference for commands that come up repeatedly. Not documentation
of what they do (see CLAUDE.md for that) — just the exact invocations so
they don't have to be re-typed or re-derived each session.

## Housekeeping bundle (run after any new data/sources/ files land)

Local file processing only — no network calls, safe to run directly/
repeatedly.

```
python3 scripts/mine_zakupki.py --json data/registry/_zakupki_mined.json --out /tmp/zakupki_mine.md && python3 scripts/zakupki_coverage.py --gaps-only && python3 scripts/zakupki_signatory_diff.py

python3 scripts/mine_zakupki.py --json data/registry/_zakupki_mined.json --out /tmp/zakupki_mine.md && python3 scripts/zakupki_coverage.py --gaps-only && python3 scripts/zakupki_customer_clusters.py --all && python3 scripts/zakupki_signatory_diff.py

```

## Aleph full-roster re-screen (live network job — run this yourself)

Screens every entity/person not already screened today against Aleph's
free-text search; writes `aleph_matches[]` + `aleph_screened_at` directly
onto entities.json/people.json. ~1s/record.

```
python3 scripts/screen_aleph.py
```

Diagnostic probe (3 records only, useful to confirm the API key/pipeline
still works before a full run):

```
python3 scripts/screen_aleph.py --limit 3
```

## Aleph follow-up triage (local, no network — safe to run directly)

Ranks every `aleph_matches[]` entry already on file by name-match quality,
filters out collision noise, prints candidate `entity_id`s to fetch.

```
python3 scripts/aleph_followup.py triage --limit 250
```

## Aleph follow-up fetch (live network job — hand to user in batches of ≤30 ids)

Pulls full entity detail for a comma-separated list of Aleph entity_ids,
archives each to `data/sources/ALEPH_DETAIL_*.json`, prints a schema-aware
extraction. Cap at 30 ids per invocation.

```
python3 scripts/aleph_followup.py fetch --entity-ids <id1>,<id2>,...
```

Add `--target-name "ФИО"` when checking a Mention/HyperText hit for
noise (flags CONFIRMED NOISE if the name doesn't actually appear in the
document's own mention list). Add `--slug <slug>` to label the archived
filename instead of the default `unknown`.

## zakupki.gov.ru mining (local — safe to run directly/repeatedly)

Two-tier report over already-pulled zakupki documents in `data/sources/`.

```
python3 scripts/mine_zakupki.py --depth scan --diff --json data/registry/_zakupki_mined.json --out /tmp/zakupki_scan.md
```

Deep single-ИНН dive:

```
python3 scripts/mine_zakupki.py --inn <ИНН> --out /tmp/zakupki_deep.md
```

## zakupki.gov.ru live pulls (live network jobs — run these yourself)

```
python3 scripts/zakupki_batch_pull.py scan --limit 20
python3 scripts/zakupki_batch_pull.py fetch-contracts --inn <ИНН>
python3 scripts/zakupki_batch_pull.py fetch-documents --inn <ИНН>
```

## Company profile rebuild (local — safe to run directly)

```
python3 scripts/build_company_profile.py --slug <slug>
python3 scripts/build_company_profile.py --all
python3 scripts/check_tag_balance.py docs/profiles/<slug>.html
```

## docs/index.html tag balance (run before any publish)

```
python3 scripts/check_tag_balance.py docs/index.html
```
