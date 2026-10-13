# telegram-dev evidence board

This board starts with the 2026-10-13 owner-gate propagation. It does not invent
verdicts for earlier releases or replace their source evidence. IDs are local to
this board; the source requests are the hub's B-108 and B-109.

| ID | Finding and acceptance | State | Evidence |
|---|---|---|---|
| GATE-01 | Own validator must reject missing boards, shifted columns and duplicate IDs using each table's header. | closed: verified, merged and published | [Task packet](member-gates-20261013/README.md), `test/member_gates_test.py` |
| GATE-02 | Own validator must reject removal of the release job's full-history checkout or unconditional ancestry failure guard. | closed: verified, merged and published | [Task packet](member-gates-20261013/README.md), `test/member_gates_test.py` |

Source review and owner integration are complete; exact merge and eligible-run
receipts are in the [release packet](releases/2026-10-13-member-gates/README.md).
Patch `0.2.4` is published; exact tag, run and npm byte-readback are in
the [published receipt](releases/2026-10-13-member-gates/README.md#published-readback).
The coordinator's family-pin/install wave is separate. No native/provider or past
release verdict is claimed.
