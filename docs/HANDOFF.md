# telegram-dev: handoff

## 2026-10-20: v0.4.0, short router descriptions

Objective: free Claude Code's shared skill-listing budget (about 30,000 chars; 81 of
134 skills showed no description on 2026-10-20). The three descriptions are now
419-461 chars (2,671 to 1,322 in total); removed trigger phrases moved verbatim into
each body's `## Triggers`. `test/validate.py` caps a description at 500 chars. Checks:
`npm test` and `npm run test:negatives` exit 0. Open: the umbrella's advertised-trigger
check still reads descriptions only and reports 8 body-only triggers until its
context-diet change lands; the umbrella re-pin is the umbrella's task. Exact next
task: none in this repository for this change.

## 2026-10-19: v0.3.0, primary-sourced feed content (FEED-SEO-1019 wave 6)

Objective: add verified content on user sessions, Mini App host trust and
storage, TON Connect 5.0, the official Markdown Bot API docs, gift offers and a
second-channel practice. Sources and left-out leads:
[feed packet](evidence/feed-1019/README.md). Open work: board rows FEED-01 to
FEED-03 (each waits on a primary source). Checks: `npm test` and
`npm run test:negatives` on the branch and on the merge commit; release receipts
are the tag's release run and the npm readback named in the PR.

Exact next task: when a primary source appears for a FEED row, add it in its
own change; otherwise re-check the Bot API changelog at the next release.

## Earlier: evidence navigation

The [verification index](evidence/verification.md) routes to existing evidence for
published version 0.2.4. The [FW00 packet](evidence/fw00-verification-index-20261013/README.md)
owns this docs-only change, its source ledger, checks and remaining gates.

Completed in the earlier source/publication wave: the [release packet](evidence/releases/2026-10-13-member-gates/README.md#published-readback)
records the original tag, successful run and package readback. This navigation
change does not rerun those historical events or assert installed/native quality.

Exact next task: integrate the frozen docs-only candidate through genuine required
checks and normal merge. Independent navigation/payload review and the owner's
local command set passed; the [subsequent gate receipt](evidence/fw00-verification-index-20261013/owner-gates.json)
preserves their exact sources. A successor containing only these receipts receives
final structural, link and package-conservation checks before promotion. No new
version, tag, publication, provider call or host-profile update belongs here.
