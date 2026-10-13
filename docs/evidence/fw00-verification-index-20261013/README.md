# FW00: navigable verification evidence

Status: FOCUSED PASS; independent audit and required broader owner gates pending.

## Objective and source contract

Expose this owner's existing verification evidence at the family reader's expected
path, without claiming a new historical run. The operator's autonomous completion
wave authorizes this docs-only packet. The selected canonical main is
[4ffb10ce1b92a599c2214327ea4d878ab514ed6b](https://github.com/ssheleg/telegram-dev/commit/4ffb10ce1b92a599c2214327ea4d878ab514ed6b),
manifest version 0.2.4; remote main was read before creating this isolated branch.

Read CLAUDE.md, CONTRIBUTING.md, .claude/agent-sync.json and the existing member-gate,
header-correction and published-readback packets. No docs/HANDOFF.md or
`docs/evidence/verification.md` exists at that base. Evidence already has an owner:
[release and readback](../releases/2026-10-13-member-gates/README.md), its adjacent
machine receipt and [source controls](../member-gates-20261013/README.md).
Do not copy their metrics or reinterpret historical passes as a current full run.

The hub's [actual ledger reader](https://github.com/ssheleg/sshlg-skills/blob/0016e058c86b3a39d0df1e06097b6c96de496c58/test/validate.py#L1878)
reads the newest semver in headings and compares package.json. Absence is disclosed;
lagging records are ratcheted. A matching heading proves navigation/version
alignment, not truth of the linked results or native quality.

The source-closure [central map](https://github.com/ssheleg/sshlg-skills/blob/0016e058c86b3a39d0df1e06097b6c96de496c58/docs/evidence/completion-1013/r30-eleven-owner-closure.md)
and [publication index](https://github.com/ssheleg/sshlg-skills/blob/0016e058c86b3a39d0df1e06097b6c96de496c58/docs/evidence/completion-1013/member-release-readback.md)
are cross-owner navigation; the local owner receipt remains the source of facts.

Contradictions: the missing family entry point was not missing verification work.
A new heading must not silently upgrade that work's source or acceptance scope.

## Requirements and sequence

1. Add a short versioned verification index linking existing evidence, with original
   source/run bounds and explicit installed/native/model limits. Add a handoff link.
2. Leave prior receipts, package/version surfaces, published content and runtime
   untouched. Take a local owner lease before edits; no board IDs are allocated.
3. Reproduce the missing-ledger disclosure with the actual extracted hub reader;
   verify current, absent, versionless and stale-heading behavior on owned fixtures.
4. Validate local links, compare all published-file hashes from the owner receipt,
   compare npm dry-run path set, and run the owner structural validator. Record
   commands/exit/disclosures and package parity. No provider/native calls.
5. Freeze and push a docs-only branch for independent audit. Required broader owner
   gates enter the coordinator's queue after Task Pipeline's full run; no broad
   invocation, tag, version bump or publication is performed in this slice.

## Handoff

Exact next task: create and check the pointer ledger, then obtain independent
source-bound acceptance. A later coordinator may integrate normally and update the
hub gitlink while retaining the published version only after package parity holds.
No mutable installed-profile or human verification claim is introduced.

Skills: task-pipeline (delivery), evidence-docs (source limits), agent-sync
(local advisory lease), make-skill (package preservation).

## Focused observations

[Current local receipt](focused.json) records the actual structural command,
output and exit 0, local link resolution and package parity. All 22
files from the existing published receipt match both SHA256 and size; the npm
`pack --dry-run --json --ignore-scripts` path set is identical. No tarball was
published or downloaded during this change. The owner structural disclosure for
an absent enclosing umbrella remains separate from native/model acceptance.

[Hub reader replay](hub-reader.json) records four cases using the actual extracted
hub function: absent entry discloses the baseline gap; the new current heading
is accepted; no version is disclosed; a stale heading triggers the existing lag
ratchet. Owned fixture directories were removed. These controls prove only the
reader's existing navigation contract, not the truth of historical outcomes.

All existing files, including prior receipts, are preserved byte-for-byte. The
new files are this packet and its check receipts, verification.md and HANDOFF.md.
No package version, installer, plugin, skill, validator or workflow changed.
The owner's broader commands from CLAUDE.md/CONTRIBUTING.md are **not rerun** in
this focused slice; their admission is queued after the coordinator's Task
Pipeline full run. Historical complete results remain bound to their own source.
Next: independent audit of the frozen docs and parity receipt before integration.

## Subsequent owner gates and independent acceptance

The initial focused snapshot above remains historical. After the coordinator
released the serial slot, the complete locally required command set ran at
`5d5ecbf4693bcb8c1fd279bb34d3e726127ecbcf` with owned scratch and a disk guard
(admit 400 MiB, stop below 200 MiB). [Process receipts](owner-gates.json)
and [exact command outputs](owner-gate-logs.json.gz) preserve each actual exit,
source identity, digest and disclosure. No disk stop occurred.

- `npm test`: exit 0.
- `npm run test:negatives`: exit 0.

The [independent navigation/payload peer](https://github.com/ssheleg/sshlg-skills/blob/a155725e46a0f11ddc4073fb9e337916c0194181/docs/evidence/completion-1013/fw00-navigation-peer.json)
accepted the initial three-owner index slice. It verified all 81 published files,
three npm path sets, 42 links and the actual hub reader; those family-wide counts
are not per-owner totals. This successor adds gate evidence and updates the current
handoff only. No payload or test implementation changed.

Next: freeze the evidence-only successor, verify its structural/link/package
conservation, then use one explicit ready-for-review candidate and genuine required
checks before normal integration. No version, tag or package release is needed.
