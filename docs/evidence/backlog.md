# telegram-dev evidence board

This board starts with the 2026-10-13 owner-gate propagation. It does not invent
verdicts for earlier releases or replace their source evidence. IDs are local to
this board; the source requests are the hub's B-108 and B-109.

| ID | Finding and acceptance | State | Evidence |
|---|---|---|---|
| GATE-01 | Own validator must reject missing boards, shifted columns and duplicate IDs using each table's header. | closed: verified, merged and published | [Task packet](member-gates-20261013/README.md), `test/member_gates_test.py` |
| GATE-02 | Own validator must reject removal of the release job's full-history checkout or unconditional ancestry failure guard. | closed: verified, merged and published | [Task packet](member-gates-20261013/README.md), `test/member_gates_test.py` |
| FEED-01 | Session leads from the 2026-10-19 review (auth key after Log Out, `+888` code flood and a code-reception switch): add to `sessions-and-auth.md` only with a Telegram or Fragment primary source. | open: waits on a primary source | [Packet](feed-1019/README.md#leads-left-out-no-primary-source-found) |
| FEED-02 | Gift scam tells and Stars refund losses: add to `payments-stars.md` only with a first-party description. | open: waits on a primary source | [Packet](feed-1019/README.md#leads-left-out-no-primary-source-found) |
| FEED-03 | Wallet rename, default wallet and a feed tab: re-check the Telegram blog and Bot API changelog at the next release; add only what they state. | open: re-check at next release | [Packet](feed-1019/README.md#leads-left-out-no-primary-source-found) |

Source review and owner integration are complete; exact merge and eligible-run
receipts are in the [release packet](releases/2026-10-13-member-gates/README.md).
Patch `0.2.4` is published; exact tag, run and npm byte-readback are in
the [published receipt](releases/2026-10-13-member-gates/README.md#published-readback).
The coordinator's family-pin/install wave is separate. Minor `0.3.0`
adds primary-sourced content; its sources and left-out leads are in the
[feed packet](feed-1019/README.md). No native/provider or past
release verdict is claimed.
