# Member board and release gates: bounded delivery packet

Objective: enforce the member's own board grammar and release ancestry contract
through its existing offline validator. Authorized by the 2026-10-13 autonomous
family completion wave; no release, installation or hub pin update is in scope.

Baseline: canonical `ssheleg/telegram-dev` main `3f9d1d1538090b7ac443b1c38faba946c3f4f7b9`.
The hub's [B-108/B-109 source](https://github.com/ssheleg/sshlg-skills/blob/ab377787/docs/evidence/backlog.md)
requires owner gates and plants. This member has no `docs/evidence/backlog.md`;
`test/validate.py` does not check board rows, `fetch-depth` or `merge-base`.
The release workflow already carries the ancestry check; this task protects it.

## Requirements and sequence

| Requirement | Implementation/check |
|---|---|
| GATE-01: own board must exist, declare rows, use its own header width and unique IDs | Shared helper called from `test/validate.py`; malformed pipe, duplicate, missing board/header and normal escaped/bold/link controls |
| GATE-02: active release job must retain full-history checkout and ancestry failure branch | Shared helper, actual validator plants removing/commenting ancestry and changing/misplacing depth; no provider calls |
| GATE-03: check the mechanism independently of this document | Real subprocess validator baseline and mutation runs; every plant proves bytes changed and the expected failure is new |
| GATE-04: maintainable sibling propagation | Prove Telegram first, copy identical helper and regression script to XR/Web3D, adapt only validator integration; parent indexes exact commits |

Use task-pipeline for delivery, make-skill for the plugin's offline gate contract,
agent-sync for local advisory ownership and evidence-docs for receipts. Existing
user authorization resolves scope and autonomy; no new operator choice is needed.
No skill bodies, manifests or versions change. The release
check is a bounded structural contract for the current workflow, not a general
YAML/Bash interpreter or proof of every possible release bypass.

## Source ledger and resume

Read `CLAUDE.md`, `.claude/agent-sync.json`, `docs/AGENT_SYNC.md`, `package.json`,
`test/validate.py`, `.github/workflows/release.yml`, and the hub's
`check_board_is_parseable`/`_one_board` implementation. Canonical remote head was
verified before branching; local main was left untouched. Agent-sync reports
local advisory arbitration, not enforced or cross-machine protection. Fabric
whoami identifies the hub project, but no com.status/list/submit tools are exposed;
the cross-project board cannot be used through this connector.

Next: independent exact-SHA review of the pushed implementation, then one
draft-to-ready candidate transition. The common helper has been propagated to
the two siblings from their canonical main heads.
Do not call a planted failure or source pass a native/runtime or release
acceptance result. Release/installation and hub pin updates remain out of scope.

## Observed verification

- Initial real-validator plants: 12 hostile defects survived the unchanged
  validator, exit 1 for the test harness; three valid controls passed.
- Expanded replay with `git show 3f9d1d1:test/validate.py` in an owned temporary
  checkout: 18 process controls, 15 failures (every hostile defect survived).
- Initial corrected `python3 test/member_gates_test.py`: 19 process controls, 0 failures,
  exit 0. Sixteen hostile plants and three valid controls exercise the real
  validator, not a stand-in parser. The final additional plant came from a
  self-review counterexample: moving `fetch-depth` from checkout `with` to `env`
  was accepted; the corrected gate scopes the value to checkout options.
- `npm test`: exit 0, including structural validator, Telegram fixtures,
  installer (11 created/removed scratch homes) and audit regressions.
- `npm run test:negatives`: exit 0, original 15 plants plus the then-current
  18 member controls. After the isolated checkout-options correction, the
  complete member-controls script was rerun with all 19 passing; unchanged
  Telegram fixture suites were not duplicated.
- `claude plugin validate . --strict` and
  `claude plugin validate plugins/telegram-dev --strict`: both exit 0.
- `git diff --check` and Python compilation: exit 0.

The member validator discloses routed-trigger checking as unlooked because this
isolated worktree has no umbrella ancestor. Hosted CI, release, real Telegram
credentials/provider execution and installed/native model behavior were NOT_RUN.
The coordinator subsequently authorized alignment of validation triggers with
the standing operator policy: schedule at 23:00 Europe/Warsaw, workflow_call for
release, and workflow_dispatch requiring a recorded candidate_reason. Automatic push and PR opened/synchronize triggers are removed; the explicit
ready_for_review candidate transition remains. The final candidate commit does not use a CI skip marker. No full hosted suite was manually dispatched at this
local verification point; a single explicit frozen-candidate run is the allowed
exception, not a new per-push policy.

The caller scan found only `release.yml` invoking `validate.yml`; there is no
Pages/deployment workflow indirectly running it on a branch push. The release
tag trigger and its dependency on the full validator remain unchanged. The
workflow was parsed with PyYAML locally (exit 0), asserting the exact four
events, ready-only PR event, timezone and required reason; PyYAML is not added to the offline gate.
GitHub documents [IANA timezone schedules](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)
and [dispatch refs](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow),
read 2026-10-13. Scheduled runs check the default branch, so they do not certify
this unmerged candidate. The coordinator must match the eligible candidate run to the frozen head or
its test merge commit, never manufacture a required status.


## Review correction and final bounded contract

Self-review reproduced an accepted duplicate release job and successful exit
before ancestry, then a successful exit inside the refusal branch. Independent
review by the hub coordinator reproduced quoted mapping keys overriding release,
run, fetch-depth and steps; a Row table silently escaped declaration uniqueness;
and missing/late Markdown separators passed. These accepting cases preceded
the corresponding correction. The first shell-override regression was also red
(26 process controls, 1 failure) before the step-leading shell property was fixed.

A final merge-key plant (`<<: {continue-on-error: true}`) initially survived
the real validator: 42 process controls, one failure. Merge keys now fail closed
before structural inspection.

The final common helper requires ID declaration tables and their immediate,
matching Markdown separator. Row reference ledgers are explicitly unsupported
in these new boards; they are not silently treated as declarations or ignored.
It reads each table's own width and rejects duplicate IDs across declarations.

Release validation is intentionally bounded to the current plain mapping keys,
two-space jobs and six-space steps. Quoted keys, YAML merge keys, duplicate jobs/steps/run/checkout
options and depths, unknown defaults, conditional or ignored ancestry, and
nonstandard shell setup fail closed. The supported setup is set-eu, resolve the
actual default branch, fetch it, then the ancestry condition; the refusal branch
permits diagnostic echo commands followed by exit 1. This is a maintainable
structural contract, not a general YAML parser or arbitrary shell verifier.
Changing that grammar requires explicit review and new controls. Valid escaped
pipes, bold/linked IDs, differing table widths and explicit false failure-ignore
flags remain accepted.

The final harness has **42 process controls: 38 hostile plants and four valid
controls**. All copies use the same helper and harness bytes. The last local
command results are recorded below; older 18/19/26-control results above are
intermediate observations, not the final result.

## Final candidate CI policy

Only `pull_request.types: [ready_for_review]` triggers a candidate suite. The PR
is created as draft, independently reviewed and locally gated, then moved to
ready once at its frozen head. No push/opened/reopened/synchronize trigger was
added. The 23:00 Europe/Warsaw schedule and release workflow_call remain.
workflow_dispatch with required candidate_reason is retained only for standalone
diagnostics; it does not satisfy PR required checks. This corrects the earlier
candidate-dispatch design above. Job bodies are unchanged.

GitHub's [required-check event contract](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks#checks-from-some-workflow-jobs-are-not-evaluated),
read 2026-10-13, explicitly excludes workflow_dispatch jobs from PR admission.
The coordinator verified that behavior during this wave. A check must be a real
eligible-event job at the candidate head or its matching test merge commit;
there is no synthetic status, branch-protection bypass or release authorization.

## Final local receipt

`npm test && npm run test:negatives && git diff --check` completed with
exit 0 after the merge-key correction, sequentially across the three members.
The negative gate refused 15 original defects and passed all 42 common
process controls (38 hostile plants, four valid controls). Workflow parsing
assertions also passed: exactly four events, ready_for_review only for PRs,
23:00 Europe/Warsaw, required candidate_reason, and job bodies equal to the
canonical-main baseline. Earlier installer and strict-manifest checks above
remain applicable: these files did not change during parser review.

Final source SHA-256:

- `test/member_gates.py`: `6d297aa8fe285e5aaaad67357829315e78ee014eb38ae6deec3d0753c8b94ff0`.
- `test/member_gates_test.py`: `b3ef7e6dc667f6b26b481c108443fdf1b6945a9133ab488a75b7fcd2e99c89e0`.

Independent final-commit approval and hosted PR admission remain pending at
this source receipt. Next: verify this exact commit, create or retain a draft
PR, then promote the frozen candidate once and watch the genuine check jobs.
No merge, release or hub pin update is authorized by this receipt.
