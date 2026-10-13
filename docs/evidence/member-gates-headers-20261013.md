# Shared member-gate declaration correction

Objective: make the two shared Python gate files discoverable by the hub's
existing divergence guard. Source base: `35bb98527884df798c4120957452ba37bae01e90` (telegram-dev 0.2.4).

The integration check found six missing declarations across telegram-dev, xr-dev
and web3d-dev: `test/member_gates.py` and `test/member_gates_test.py` are identical
copies, but did not carry machine-readable `shared-mechanism`/`diverges` headers.
Each now declares its stable mechanism ID, `diverges: none`, and all three owners.
No exemption or similarity-floor change was made in the hub.

Validation performed on this candidate:

- The real hub function `check_a_copied_mechanism_declares_its_divergence` was
  evaluated against isolated copies of these six files. Baseline: six missing
  declaration failures; corrected: zero. Adding an undeclared module constant to
  one copy still refused all three declarations in that file group.
- `npm test`: exit 0.
- `python3 test/member_gates_test.py`: 42 real process controls, zero failures.
- Python AST dumps excluding positions were identical before/after for both files.
  The only source edits are comments; existing execution and negative plants are
  unchanged. Hosted normal candidate validation remains required before merge.
- `npm pack --dry-run --json`: 22 files, version 0.2.4. Exact path set and
  every SHA-256 matched the previously downloaded and source-verified published
  0.2.4 tarball. Test files and this evidence are outside the npm payload.

Decision: this is a repository-only successor, not a new package release. Keep
version 0.2.4, its published payload, and historical tag untouched. The hub
may pin the merged successor while retaining the verified package version.

Next task: independent review, ordinary draft-to-ready candidate checks, then
normal exact-head merge; coordinator reruns the hub integration guard with all
three corrected owner commits. No installed skill or host setting changes.

Skills: task-pipeline (normal delivery), make-skill (unchanged package proof),
agent-sync (local advisory ownership), evidence-docs (bounded check receipts).
