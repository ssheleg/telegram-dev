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
    # `offset` is advanced only after the work committed. Without it a crash
    # between the two loses the update for good — the API keeps it 24 hours and
    # the bot has already said it was taken.
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

    def deliver(self, update: dict, crash_on: int | None = None) -> None:
        """One webhook delivery, or one update out of a polled batch."""
        uid = update["update_id"]
        if self.has("claim") and not self.store.claim(uid):
            self.store.log.append(f"{uid}: duplicate")
            return
        if not self.has("claim"):
            self.store.processed.add(uid)
        if crash_on is not None and uid == crash_on:
            raise SystemError("killed mid-work")
        self._work(update)

    def poll_batch(self, updates: list[dict], crash_on: int | None = None) -> None:
        """A getUpdates batch.

        `crash_on` raises DURING the work for that update_id — a deploy, an OOM
        kill, a database blip. That is the only moment where the two orderings
        differ, so it is the only scenario that measures them.
        """
        for u in updates:
            if self.has("confirm-after-work"):
                self.deliver(u, crash_on=crash_on)
                self.store.offset = u["update_id"] + 1      # confirm what is DONE
            else:
                self.store.offset = u["update_id"] + 1      # confirmed before the work
                self.deliver(u, crash_on=crash_on)

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


@invariant("a crash mid-work redelivers rather than loses", breaks=("confirm-after-work",))
def _(store, handler):
    # Killed while working on A. Nothing about A was finished.
    try:
        handler.poll_batch([UPDATE_A, UPDATE_B], crash_on=UPDATE_A["update_id"])
    except SystemError:
        pass
    assert store.work == [], "the fixture did not actually interrupt the work"

    # The bot restarts and asks Telegram for everything from its stored offset.
    stored = store.offset or 0
    still_delivered = [u for u in (UPDATE_A, UPDATE_B) if u["update_id"] >= stored]
    assert UPDATE_A in still_delivered, (
        "the offset was advanced past an update whose work never happened — Telegram "
        "keeps it 24 hours and the bot has already said it was taken, so it is gone"
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
