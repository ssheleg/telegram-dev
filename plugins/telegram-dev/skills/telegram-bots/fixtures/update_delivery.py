#!/usr/bin/env python3
"""The update-delivery invariants a correct Telegram bot holds, and the proof
that each one can fail.

    python3 update_delivery.py              # run them against the reference handler
    python3 update_delivery.py --self-test  # break one rule at a time; each MUST go red

`--self-test` is the half that makes this evidence. For every invariant it names
the rule whose removal must turn that invariant red, deletes exactly that rule,
and fails if the assertion still passes. A check nobody has watched failing is
indistinguishable from one that cannot fail.

Point it at YOUR handler by replacing `Store` and `Handler` below and keeping the
three entry points: `deliver(update)`, `poll_batch(updates)`, and a store you can
read counts off. Standard library only, no network, no clock.
"""
from __future__ import annotations

import sys

RULES = (
    # The claim: an INSERT on a primary key, before any work. Without it a
    # redelivered update is processed a second time.
    "claim",
    # The claim row is a durable INBOX row, written before the ack (the webhook's
    # 200, or the offset advance). Without it the work runs inside the request:
    # a crash mid-work leaves the claim standing, the redelivery reads
    # "duplicate", and the update is lost — the crash fixture stays green while
    # the real redelivery loses the event.
    "inbox-before-ack",
    # A crashed work attempt leaves its inbox row pending, and the sweep retries
    # it. Without it the row is marked done at take-time, so receipt quietly
    # becomes completion and a crash after the ack loses the update.
    "worker-retry",
    # The ack is sent only after the durable write. Without it a crash between
    # the two loses the update for good — the API keeps it 24 hours and the bot
    # has already said it was taken.
    "confirm-after-work",
    # 429 sleeps for exactly `retry_after` and retries the SAME call. Without it
    # the send is dropped and the user never hears back.
    "retry-after",
    # The grant is guarded on the payment's own charge id, not only on the
    # transport claim — a reconciliation replay reaches the handler with no
    # update at all.
    "charge-id-guard",
)


class Store:
    def __init__(self) -> None:
        self.processed: set[int] = set()
        self.inbox: dict[int, dict] = {}   # update_id -> {"state": 'pending'|'done', "update": …}
        self.acked: list[int] = []         # every 200 the transport saw (or offset advance)
        self.work: list[int] = []          # one entry per unit of work actually done
        self.offset: int | None = None
        self.granted: list[str] = []       # charge ids granted
        self.sent: list[str] = []
        self.log: list[str] = []

    def claim(self, update_id: int) -> bool:
        """INSERT on a primary key: atomic, and the only thing that survives a race."""
        if update_id in self.processed:
            return False
        self.processed.add(update_id)
        return True

    def inbox_put(self, update: dict) -> bool:
        """The same INSERT, but the row it writes is durable state, not a boolean:
        'pending' until a worker finishes, 'done' after. False means the row exists —
        a redelivery — and existing is an answer about RECEIPT, never about work."""
        uid = update["update_id"]
        if uid in self.inbox:
            return False
        self.inbox[uid] = {"state": "pending", "update": update}
        return True


class Transport:
    """Stands in for Telegram: refuses once with a retry_after, then accepts."""

    def __init__(self, refuse_times: int = 1, retry_after: int = 3) -> None:
        self.refuse_times = refuse_times
        self.retry_after = retry_after
        self.slept: list[int] = []

    def send(self, text: str) -> str:
        if self.refuse_times > 0:
            self.refuse_times -= 1
            raise RetryAfter(self.retry_after)
        return text


class RetryAfter(Exception):
    def __init__(self, seconds: int) -> None:
        super().__init__(f"retry after {seconds}")
        self.seconds = seconds


class Handler:
    def __init__(self, store: Store, transport: Transport, without: tuple[str, ...] = ()) -> None:
        for rule in without:
            if rule not in RULES:
                raise ValueError(f"unknown rule: {rule}")
        self.store = store
        self.transport = transport
        self.without = set(without)

    def has(self, rule: str) -> bool:
        return rule not in self.without

    # ------------------------------------------------------------------ entry points

    def deliver(self, update: dict, crash: str | None = None) -> None:
        """One webhook request. The ack is the HTTP 200; the work is not.

        `crash` names the moment the process dies: "before-ack" (the durable
        write happened, the 200 never left) or "in-worker" (the 200 left, the
        worker was killed mid-work). A crash is a raise with nothing released —
        that is what makes it a crash.
        """
        uid = update["update_id"]
        if not self.has("inbox-before-ack"):
            # The pre-inbox shape: claim, then work, inside the request. The claim
            # is already durable when the crash lands, so the redelivery reads
            # "duplicate" and the update is lost. Kept as the mutant.
            if self.has("claim") and not self.store.claim(uid):
                self.store.log.append(f"{uid}: duplicate")
                self.store.acked.append(uid)
                return
            if not self.has("claim"):
                self.store.processed.add(uid)
            if crash is not None:
                raise SystemError("killed mid-work")        # no 200 left this process
            self._work(update)
            self.store.acked.append(uid)
            return
        fresh = self.store.inbox_put(update)
        if not self.has("claim") and not fresh:
            self.store.inbox[uid] = {"state": "pending", "update": update}
            fresh = True
        if crash == "before-ack":
            raise SystemError("killed after the durable write, before the 200")
        self.store.acked.append(uid)                        # received, durably — not done
        if not fresh:
            self.store.log.append(f"{uid}: duplicate delivery")
            return
        self.run_worker(uid, crash=(crash == "in-worker"))

    def run_worker(self, uid: int, crash: bool = False) -> None:
        """One work attempt against a pending inbox row. Off the request path in
        production; inline here so every invariant stays deterministic."""
        row = self.store.inbox.get(uid)
        if row is None or row["state"] != "pending":
            return
        if not self.has("worker-retry"):
            row["state"] = "done"        # done at take-time: a crash now loses the row
        if crash:
            raise SystemError("worker killed mid-work")
        self._work(row["update"])
        row["state"] = "done"

    def run_workers(self) -> None:
        """The sweep: every pending row gets another attempt. In production this is
        the worker loop under a lease; a row a crashed worker held comes back here."""
        for uid in sorted(self.store.inbox):
            self.run_worker(uid)

    def poll_batch(self, updates: list[dict], crash_on: int | None = None) -> None:
        """A getUpdates batch.

        `crash_on` raises at that update's seam — between the durable write and
        the offset advance, whichever order the rules put them in. That is the
        only moment where the two orderings differ, so it is the only scenario
        that measures them.
        """
        for u in updates:
            uid = u["update_id"]
            if not self.has("inbox-before-ack"):
                # the pre-inbox shape: the work itself sits inside the batch loop
                if self.has("confirm-after-work"):
                    self.deliver(u, crash="mid-work" if crash_on == uid else None)
                    self.store.offset = uid + 1              # confirm what is DONE
                else:
                    self.store.offset = uid + 1              # confirmed before the work
                    self.deliver(u, crash="mid-work" if crash_on == uid else None)
                continue
            if self.has("confirm-after-work"):
                self.store.inbox_put(u)                      # durable first
                if crash_on == uid:
                    raise SystemError("killed before the offset advanced")
                self.store.offset = uid + 1                  # confirm what is HELD
            else:
                self.store.offset = uid + 1                  # confirmed before the write
                if crash_on == uid:
                    raise SystemError("killed after the offset, before the write")
                self.store.inbox_put(u)
            self.run_worker(uid)

    # ---------------------------------------------------------------------- the work

    def _work(self, update: dict) -> None:
        if "successful_payment" in update:
            charge = update["successful_payment"]["telegram_payment_charge_id"]
            if self.has("charge-id-guard") and charge in self.store.granted:
                self.store.log.append(f"{charge}: already granted")
                return
            self.store.granted.append(charge)
            self.store.work.append(update["update_id"])
            return
        self.store.work.append(update["update_id"])
        self._send(f"reply to {update['update_id']}")

    def _send(self, text: str) -> None:
        while True:
            try:
                self.store.sent.append(self.transport.send(text))
                return
            except RetryAfter as e:
                if not self.has("retry-after"):
                    self.store.log.append("dropped on 429")
                    return
                self.transport.slept.append(e.seconds)      # sleep(e.seconds) in production


# ------------------------------------------------------------------------ invariants

def harness(without=(), refuse_times=0):
    store = Store()
    return store, Handler(store, Transport(refuse_times=refuse_times), without)


UPDATE_A = {"update_id": 1001, "message": {"text": "hello"}}
UPDATE_B = {"update_id": 1002, "message": {"text": "again"}}
PAYMENT = {
    "update_id": 1003,
    "successful_payment": {
        "telegram_payment_charge_id": "chg_PLACEHOLDER_1",
        "invoice_payload": "order-42",
        "currency": "XTR",
        "total_amount": 250,
    },
}

INVARIANTS = []


def invariant(id_, breaks):
    def deco(fn):
        INVARIANTS.append((id_, breaks, fn))
        return fn
    return deco


@invariant("redelivered-update-works-once", breaks=("claim",))
def _(store, handler):
    handler.deliver(UPDATE_A)
    handler.deliver(dict(UPDATE_A))                 # the same update_id, delivered again
    assert len(store.work) == 1, (
        "the same update_id was processed twice — a webhook retry, a poller redelivery "
        "or a restart is enough to produce this"
    )


@invariant("a crash mid-batch redelivers or holds rather than loses", breaks=("confirm-after-work",))
def _(store, handler):
    # Killed at A's seam — between the durable write and the offset advance.
    try:
        handler.poll_batch([UPDATE_A, UPDATE_B], crash_on=UPDATE_A["update_id"])
    except SystemError:
        pass
    assert store.work == [], "the fixture did not actually interrupt the work"

    # The bot restarts. The update survives one of two ways: Telegram redelivers it
    # (the offset never covered it), or the inbox already holds it pending.
    stored = store.offset or 0
    redelivered = [u for u in (UPDATE_A, UPDATE_B) if u["update_id"] >= stored]
    held = store.inbox.get(UPDATE_A["update_id"], {}).get("state") == "pending"
    assert UPDATE_A in redelivered or held, (
        "the offset was advanced past an update that is neither done nor held — Telegram "
        "keeps it 24 hours and the bot has already said it was taken, so it is gone"
    )


@invariant("a crash after the ack keeps the queued update", breaks=("inbox-before-ack", "worker-retry"))
def _(store, handler):
    # The 200 left; the worker died mid-work. Telegram will NOT redeliver an update it
    # saw acknowledged — only the inbox row brings this one back.
    try:
        handler.deliver(UPDATE_A, crash="in-worker")
    except SystemError:
        pass
    assert UPDATE_A["update_id"] in store.acked, (
        "the crash landed before the ack — with a durable inbox the 200 goes out once "
        "the row is written, and the work is not the request's problem"
    )
    handler.run_workers()                       # the sweep a lease expiry feeds in production
    assert store.work == [UPDATE_A["update_id"]], (
        "the update the bot already acknowledged was lost — receipt was read as completion"
    )


@invariant("a redelivery after a crash still completes the work", breaks=("inbox-before-ack",))
def _(store, handler):
    # The original finding: the crash fixture is green, and the REAL redelivery still
    # loses the update, because the claim written before the crash answers "duplicate"
    # about work that never happened.
    try:
        handler.deliver(UPDATE_A, crash="before-ack")
    except SystemError:
        pass
    handler.deliver(dict(UPDATE_A))             # no 200 left the process, so Telegram retries
    handler.run_workers()
    assert store.work == [UPDATE_A["update_id"]], (
        "the redelivery was answered 'duplicate' and nothing ever did the work — "
        "a duplicate is an answer about a done row, not about a receipt"
    )


@invariant("a 429 is retried, not dropped", breaks=("retry-after",))
def _(store, handler):
    handler.deliver(UPDATE_A)
    assert store.sent == ["reply to 1001"], "the reply was dropped on the first 429"
    assert handler.transport.slept == [3], "did not sleep for the retry_after Telegram gave"


@invariant("a payment grants once, from any entry point", breaks=("charge-id-guard",))
def _(store, handler):
    handler.deliver(PAYMENT)
    # A reconciliation replay reaches the same work with no update at all, so the
    # transport claim cannot protect it.
    handler._work(dict(PAYMENT, update_id=9999))
    assert store.granted == ["chg_PLACEHOLDER_1"], (
        "one payment granted twice — the transport claim protects the handler, and "
        "only the charge id protects the grant"
    )


# ---------------------------------------------------------------------------- runner

def run_one(id_, fn, without=()):
    store, handler = harness(without, refuse_times=1 if "429" in id_ else 0)
    fn(store, handler)


def main(argv):
    self_test = "--self-test" in argv
    failures = []

    for id_, _breaks, fn in INVARIANTS:
        try:
            run_one(id_, fn)
        except AssertionError as e:
            failures.append(f"{id_}: {e}")

    if failures:
        for f in failures:
            print(f"FAIL: {f}")
        return 1

    if not self_test:
        print(f"OK ({len(INVARIANTS)} checks — update delivery, 429 and the payment grant)")
        return 0

    print("mutant matrix — each invariant must go red when its own rule is removed\n")
    broken = []
    for id_, breaks, fn in INVARIANTS:
        for rule in breaks:
            try:
                run_one(id_, fn, without=(rule,))
            except AssertionError:
                print(f"  ok      {id_:<50} dies without {rule!r}")
                continue
            print(f"  BROKEN  {id_:<50} survives without {rule!r}")
            broken.append((id_, rule))
    if broken:
        print(f"\nFAIL: {len(broken)} invariant(s) cannot fail, so they prove nothing")
        return 1
    print(f"\nself-test OK — {len(INVARIANTS)} invariants, each watched failing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
