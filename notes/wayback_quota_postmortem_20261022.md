# Wayback workflow and the Actions quota: what the run history shows (22.10.2026)

Internal. Complements `notes/repo_review_20261021.md` §1.1 (which has the cause and the cap change already applied in `334c98e`). This note holds the measured numbers and the remaining gap. Source: the GitHub Actions run history of 04.10 to 21.10 and `source_archives.json` at each nightly commit. The billing page was not readable from the cloud, so the quota figure is inferred.

## What it cost and what it bought

| | |
|---|---|
| Scheduled wayback runs 04.10-09.10 | 6, each 312-315 min (the `timeout 315m` ended every one) |
| Runner minutes, all wayback runs | about 1,913 (20 runs) |
| Other workflows in the same period | about 200 (checks 164, Copilot agent 22, sanctions-watch 15) |
| Free-tier allowance assumed for a private repo | 2,000 min a month |
| Captures in `source_archives.json`, first to last nightly commit | 654 to 660 (+6) |
| Error entries in the same file | 56 to 429 (+373) |
| Dominant errors | lookup timed out, SSL handshake timed out, CDX HTTP 503 |
| After 09.10 | every run (12 wayback, 2 sanctions-watch) failed in 3-4 s with no runner and no log |

The anonymous archive.org endpoint, called from GitHub's shared runner addresses, mostly timed out. The script kept retrying until the 315-minute ceiling.

## Why nothing flagged it

The step ends `... | tee log.txt || echo "batch ended early ..."`, so a run that captured nothing exits 0 and shows green. The commit step then records the error entries as a change to `source_archives.json`, so even the commit history looked like activity.

## Remaining gap (not fixed; a workflow change needs the user's go-ahead)

The caps (weekly, 40 URLs, 60 min) bound the damage but the run can still be green and empty. Cheap hardening, in order of value:

1. Fail the step when a run captured zero new URLs, so it shows red.
2. Stop after 10 consecutive errors instead of running to the ceiling.
3. Set the repo secrets `WAYBACK_S3_ACCESS` and `WAYBACK_S3_SECRET` (open since 02.10): the keyed endpoint is the real speed-up.
4. Treat any workflow that fails in under 10 seconds as "no runner or quota", not as a code failure.
