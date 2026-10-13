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

Next: add the negative plants and run them against the unchanged validator;
then implement the common helper, rerun targeted checks, obtain independent
review and push a handoff branch. Whole member gates wait until the parent hub
aggregate finishes. Do not call a planted failure or source pass a native/runtime
or release acceptance result.
