# Verification evidence — telegram-dev

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
