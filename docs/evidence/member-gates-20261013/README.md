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
No skill bodies, manifests, versions or workflow triggers change. The release
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

Next: independent review of the frozen implementation, then commit/push and
propagate the same helper to the two siblings from their canonical main heads.
Do not call a planted failure or source pass a native/runtime or release
acceptance result. Release/installation and hub pin updates remain out of scope.

## Observed verification

- Initial real-validator plants: 12 hostile defects survived the unchanged
  validator, exit 1 for the test harness; three valid controls passed.
- Expanded replay with `git show 3f9d1d1:test/validate.py` in an owned temporary
  checkout: 18 process controls, 15 failures (every hostile defect survived).
- Final `python3 test/member_gates_test.py`: 19 process controls, 0 failures,
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
Owner workflow triggers are unchanged; branch commits use `[skip ci]` while the
coordinator reconciles the repository's older all-push/PR workflow with the
operator's nightly-check policy. No full hosted suite was manually dispatched.
