# telegram-dev evidence board

This board starts with the 2026-10-13 owner-gate propagation. It does not invent
verdicts for earlier releases or replace their source evidence. IDs are local to
this board; the source requests are the hub's B-108 and B-109.

| ID | Finding and acceptance | State | Evidence |
|---|---|---|---|
| GATE-01 | Own validator must reject missing boards, shifted columns and duplicate IDs using each table's header. | verified and merged; patch release pending | [Task packet](member-gates-20261013/README.md), `test/member_gates_test.py` |
| GATE-02 | Own validator must reject removal of the release job's full-history checkout or unconditional ancestry failure guard. | verified and merged; patch release pending | [Task packet](member-gates-20261013/README.md), `test/member_gates_test.py` |

Source review and owner integration are complete; exact merge and eligible-run
receipts are in the [release packet](releases/2026-10-13-member-gates/README.md).
Remaining: patch publication and the coordinator's family-pin/install wave. No native/provider or past release verdict is claimed.
