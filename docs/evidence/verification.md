# Verification evidence — telegram-dev

## v0.5.4: the 0.5.1 content confirmed against the shipped artifact (2026-10-25)

descriptions within a 300-character budget. Evidence: the repository gate exits 0 on the candidate tree; the PR CI run
and the tag release run are named in docs/HANDOFF.md.

## v0.5.3: the 0.5.1 content confirmed against the shipped artifact (2026-10-24)

| Evidence needed | Owning source | Scope and limits |
|---|---|---|
| The structure of the new reference and the routing rows | `test/validate.py` (`npm test`, `npm run test:negatives`, both exit 0 on the candidate) | Structure only. No model routing quality is claimed. |
| The nine delivery invariants of `fixtures/update_pump.py` | `python3 plugins/telegram-dev/skills/telegram-bots/fixtures/update_pump.py --self-test` (part of `npm test`): every invariant holds with all rules on, and each goes red when its own rule is removed | A simulation on a virtual clock. It shows what each rule protects; it is not a measurement of any live bot. |
| The telegraf behaviour `references/high-load.md` describes | telegraf 4.16.3 source read on 2026-10-23: `polling.js` awaits `Promise.all` over the batch before the next `getUpdates`; `handlerTimeout` 90 000 ms with `p-timeout`; the client sets `timeout = 500000` after its options are merged | Pinned to that release. A later telegraf may differ. |
| The package that installs is the one described | npm `@ssheleg/telegram-dev@0.5.1` and GitHub release `v0.5.1` published by the release workflow on tag `v0.5.1` (merge commit `3683720`) | 0.5.3 changes only this ledger and the version fields. |

## v0.4.0: short router descriptions (2026-10-20)

| Evidence needed | Owning source | Scope and limits |
|---|---|---|
| Description lengths and the 500-char cap | `test/validate.py` (`npm test`, `npm run test:negatives`, both exit 0 on the candidate) | Structure only. No model routing quality is claimed. |
| Every routed trigger still in the skill text | A scratch check over the umbrella's routing table: 32 triggers, 0 missing from the SKILL.md text, 8 now only in a body `## Triggers` section | Until the umbrella's own check reads the whole SKILL.md, it reports those 8 as unadvertised. |

## v0.3.0: content sources (2026-10-19)

| Evidence needed | Owning source | Scope and limits |
|---|---|---|
| Every added claim and its primary source; leads left out | [Feed packet](feed-1019/README.md) | Sources fetched on 2026-10-19. No model-quality or live-account test is claimed. |

## v0.2.4 — published-source evidence index (2026-10-13)

This index makes existing owner evidence discoverable. It does not re-run or
re-stamp historical checks. The version identifies the artifact in the linked
publication receipt; the repository also contains documented, payload-preserving
successors. A matching family-ledger heading is not a new acceptance result.

| Evidence needed | Owning source | Scope and limits |
|---|---|---|
| Release and publication | [Release packet](releases/2026-10-13-member-gates/README.md#published-readback) and [machine readback](releases/2026-10-13-member-gates/published-readback.json) | Exact original tag/source, release run, registry integrity and packaged-file hashes. Preserve the receipt's date and source. |
| Board and release safeguards | [Implementation and witnessed controls](member-gates-20261013/README.md) | Bounded source/process validation, including its intermediate failures; not a general YAML/Bash proof. |
| Repository-only successor | [Shared-header correction](member-gates-headers-20261013.md) and [owner board](backlog.md) | Declared source/payload preservation and publication reconciliation; no new package release. |
| This index change | [FW00 packet](fw00-verification-index-20261013/README.md) | Link/version discovery and unchanged package evidence only; current checks are recorded separately from historical receipts. |

Installed host discovery, native hooks, model task quality and live provider/device
behavior are **not established by this index**. Read their own source-bound receipts
if needed; package equality does not imply them. Older runs keep their original
confirmation state. No human confirmation or completed pipeline run is invented.

[Current handoff](../HANDOFF.md) names the next task.
