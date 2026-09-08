#!/usr/bin/env python3
"""FIX-TG-01.02 — business and send dedup (sherlock audit, TG-01, second leaf;
depends on FIX-TG-01.01's durable inbox).

The contract under test: the grant is keyed on the BUSINESS charge id, never
the update id — one charge arriving in two updates is one payment; replies
leave through an outbox row whose key is the send's business identity, and the
consumer dedups on it, because both the work retry and the queue redeliver.

Acceptance: a repeated update never doubles the grant; a crash around the send
retried still yields exactly one delivered result.

Driven against the shipped fixture module and both its run modes as processes.
Standard library only.
"""
import importlib.util
import os
import subprocess
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BOTS = os.path.join(ROOT, "plugins", "telegram-dev", "skills", "telegram-bots")
FIXTURE = os.path.join(BOTS, "fixtures", "update_delivery.py")

_spec = importlib.util.spec_from_file_location("update_delivery", FIXTURE)
F = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(F)

failures = []


def case(name, fn):
    try:
        fn()
        print(f"  ok  {name}")
    except AssertionError as e:
        failures.append(f"{name}: {e}")
        print(f"FAIL  {name}: {e}")


def harness(without=()):
    store = F.Store()
    return store, F.Handler(store, F.Transport(refuse_times=0), without)


MSG = {"update_id": 7001, "message": {"text": "hi"}}
PAY = {
    "update_id": 7002,
    "successful_payment": {
        "telegram_payment_charge_id": "chg_PLACEHOLDER_9",
        "invoice_payload": "order-9", "currency": "XTR", "total_amount": 100,
    },
}


def t_docs_state_the_two_keys():
    ref = open(os.path.join(BOTS, "references", "updates-and-delivery.md"),
               encoding="utf-8").read()
    flat = " ".join(ref.split())
    for needle in ("Replies leave through an outbox, and the consumer holds its own key",
                   "business identity (`telegram_payment_charge_id`), never the `update_id`",
                   "one charge arriving in two updates is one payment"):
        assert needle in flat, f"the reference no longer states {needle!r}"
    skill = open(os.path.join(BOTS, "SKILL.md"), encoding="utf-8").read()
    assert "nine invariants" in skill, "SKILL.md invariant count is stale"


def t_repeated_update_never_doubles_the_grant():
    store, handler = harness()
    handler.deliver(dict(PAY))
    handler.deliver(dict(PAY))                                   # same update_id
    handler.deliver(dict(PAY, update_id=PAY["update_id"] + 1))   # same charge, new update
    handler.run_workers()
    assert store.granted == ["chg_PLACEHOLDER_9"], \
        f"one charge granted {len(store.granted)} times: {store.granted}"


def t_crashed_send_retry_yields_one_result():
    store, handler = harness()
    store.inbox[MSG["update_id"]] = {"state": "pending", "update": dict(MSG)}
    try:
        handler.run_worker(MSG["update_id"], crash_after_send=True)
    except SystemError:
        pass
    assert store.inbox[MSG["update_id"]]["state"] == "pending", "the crash missed its window"
    handler.run_workers()
    assert len(store.sent) == 1, f"the reply reached the user {len(store.sent)} times"
    # and a queue redelivery of the sent row changes nothing
    for row in store.outbox:
        row["state"] = "pending"
    handler.drain_outbox()
    assert len(store.sent) == 1, "a redelivered outbox row sent again"


def t_pre_outbox_shape_reproduces_the_double_send():
    """The negative: without the outbox, the same crash doubles the reply."""
    store, handler = harness(without=("send-outbox",))
    store.inbox[MSG["update_id"]] = {"state": "pending", "update": dict(MSG)}
    try:
        handler.run_worker(MSG["update_id"], crash_after_send=True)
    except SystemError:
        pass
    handler.run_workers()
    assert len(store.sent) == 2, \
        f"the pre-outbox shape sent {len(store.sent)} — the mutant no longer measures the defect"


def t_fixture_passes_both_modes():
    for args in ([], ["--self-test"]):
        r = subprocess.run([sys.executable, FIXTURE] + args,
                           capture_output=True, text=True, timeout=120)
        assert r.returncode == 0, \
            f"update_delivery.py {' '.join(args)} fails:\n{(r.stderr or r.stdout)[-300:]}"
    out = subprocess.run([sys.executable, FIXTURE, "--self-test"],
                         capture_output=True, text=True, timeout=120).stdout
    for rule in ("send-outbox", "send-consumer-key"):
        assert rule in out, f"the self-test never exercised {rule!r}"


def main():
    case("the doctrine states the two keys", t_docs_state_the_two_keys)
    case("a repeated update never doubles the grant", t_repeated_update_never_doubles_the_grant)
    case("a crashed send, retried, yields one result", t_crashed_send_retry_yields_one_result)
    case("the pre-outbox shape reproduces the double send", t_pre_outbox_shape_reproduces_the_double_send)
    case("the shipped fixture passes both modes", t_fixture_passes_both_modes)
    if failures:
        print(f"\n{len(failures)} failure(s)")
        return 1
    print("\nall green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
