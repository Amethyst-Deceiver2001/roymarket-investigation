# Working rules for roymarket-investigation

This repo is a standalone spin-off of a ЦБСТ/РОЙ.МАРКЕТ (Russian "military
marketplace" and its parent defence-tech body) OSINT investigation, migrated
out of the `wb_watch` project on 2026-08-18 once it outgrew "annex to a WB
tracker" scope. Read `HANDOFF.md` first in any new session — it has full
context, current state, and pending work that this file doesn't repeat.

## Data collection stays in wb_watch — this repo does analysis + publication

Telegram scraping (`wb-watch tg-scan`) requires an authenticated Telegram
session that lives in the `wb_watch` repo (`~/Downloads/wb_watch`), and that
repo's `config/channels.txt` already has every channel this investigation
uses. Don't set up a second scraping pipeline here. Instead:

1. New channels/full-history pulls happen in `wb_watch` (add to its
   `config/channels.txt`, hand the user the `tg-scan` command per *its*
   CLAUDE.md rules — full crawls are never run directly by Claude there
   either).
2. After a scan lands in `wb_watch/data/wb_watch.db`, run
   `scripts/export_from_wb_watch.py` here to pull the relevant channels'
   posts into this repo's own `data/roymarket.db` (gitignored — it's a local
   working copy regenerated on demand, not committed history).
3. Analyze/query `data/roymarket.db` directly here.

If a channel is genuinely new to this investigation, add its ID to
`CHANNEL_IDS` in `scripts/export_from_wb_watch.py` too.

## Same crawling-jobs discipline as wb_watch

Inline reconnaissance (single post lookups, one-off WebFetch/curl checks,
EGRUL/БФО document reads) is fine to run directly. Anything that does real
work at scale against a live third-party service must be handed to the user
as an exact command to run themselves, never run in the background — this
applies to `tg-scan` in `wb_watch` (see above) and to EGRUL/БФО pulls, which
are user's own manual downloads due to daily rate limits.

## Quotes: never paraphrase or invent

Any review, post, testimonial, or other quoted material in `docs/index.html`
must be the original text only — verbatim, punctuation and typos preserved.
If a quote can't be verified against a primary source, don't use it.

## Publishing

`docs/index.html` is the GitHub Pages source (repo Settings → Pages →
`/docs`) and the standalone Artifact companion
(https://claude.ai/code/artifact/5450bf7e-7f7b-4788-93c0-761503dd5ea4). Edit
the local file freely; only republish the Artifact when the user calls an
explicit investigation cutoff — see `HANDOFF.md` for why (the Artifact
intentionally lags the local file between cutoffs).

## Tag-balance check before any publish

Run the scoped tag-count script (in `HANDOFF.md` and the seeded memory) after
every `docs/index.html` edit, before publishing.

## PII handling

Default to the brief's existing standard: named individuals get name + role,
sourced from EGRUL/official filings, no personal addresses/ID numbers. The
one exception on record (an InformNapalm OSINT dossier with full addresses/
passport numbers) was included at explicit user direction for that specific
case — don't treat it as the default; ask if a similar case comes up.

## Adjacent-but-not-ЦБСТ networks

Entities/networks that turn out to lack a confirmed ЦБСТ/РОЙ.МАРКЕТ tie
(same industry, physical proximity, name collision — but no institutional
link) get a one-line disambiguation in `docs/index.html` at most, with full
detail parked in memory instead. See the seeded `roymarket_adjacent_networks`
memory file — check it before starting a fresh deep-dive on something that
smells adjacent-not-core.
