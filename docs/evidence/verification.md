# Verification evidence — telegram-dev

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
