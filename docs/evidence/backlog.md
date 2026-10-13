# telegram-dev evidence board

This board starts with the 2026-10-13 owner-gate propagation. It does not invent
verdicts for earlier releases or replace their source evidence. IDs are local to
this board; the source requests are the hub's B-108 and B-109.

| ID | Finding and acceptance | State | Evidence |
|---|---|---|---|
| GATE-01 | Own validator must reject missing boards, shifted columns and duplicate IDs using each table's header. | implemented on branch; independent review pending | [Task packet](member-gates-20261013/README.md), `test/member_gates_test.py` |
| GATE-02 | Own validator must reject removal of the release job's full-history checkout or unconditional ancestry failure guard. | implemented on branch; independent review pending | [Task packet](member-gates-20261013/README.md), `test/member_gates_test.py` |

Remaining: independent review, owner integration, then the coordinator's separate
release and family-pin wave. No native/provider or past release verdict is claimed.
