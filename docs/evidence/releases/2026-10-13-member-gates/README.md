# telegram-dev 0.2.4: release packet

Objective: publish the already merged FW02 board and release-ancestry gates as
an exact patch version. The operator authorized this release wave on 2026-10-13.
Hub pins and global installation belong to the coordinating hub wave.

## Source and acceptance

- Source main: `85a5a5f13e2c7b24fddda5c53bb05f1634d969ed`; [PR 12](https://github.com/ssheleg/telegram-dev/pull/12).
- Eligible source check: [run 38336371814](https://github.com/ssheleg/telegram-dev/actions/runs/38336371814), success.
- [Implementation packet](../../member-gates-20261013/README.md): 42 process controls,
  including 38 hostile plants and four valid shapes. The coordinator independently
  replayed the final Telegram controls and verified identical sibling helper/harness hashes.
- This release changes version metadata and evidence only; the source gate implementation
  and CI job bodies remain the merged, reviewed ones.

## Requirements and sequence

1. Synchronize package, marketplace, plugin, existing skill metadata and skill card
   to `0.2.4`; add the exact changelog section, preserving historical versions.
2. Run the owner's required local gate sequentially; strict manifest validation and
   payload dry-run supplement it. Record actual outcomes below.
3. Independently review the frozen diff, push a draft PR, then promote it once for
   eligible `ready_for_review` checks. Ordinary exact-head squash merge only.
4. Create a new annotated `v0.2.4` at merged canonical main, after confirming the
   tag and npm version are absent. Watch the existing release workflow, then verify
   the exact registry version and GitHub release. Never rewrite an old tag.
5. Hand source/tag/run receipts to the hub coordinator for pins and installation.

## Current state and next task

Plan committed before the metadata change. Local release-candidate checks, PR
admission, tag creation, publication and installation are **NOT_RUN** here.
Next: synchronize version metadata, then perform step 2 after the current FW04
full gate finishes. No model/provider/native-runtime acceptance is inferred.

Skills used: make-skill (release construction), task-pipeline (delivery),
agent-sync (local advisory ownership), evidence-docs (source and check receipts).
