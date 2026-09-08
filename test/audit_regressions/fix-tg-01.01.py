#!/usr/bin/env python3
"""FIX-TG-01.01 — Durable inbox before ack (sherlock audit, finding TG-01).

The finding: the crash fixture was green while a real redelivery lost the
update. The doctrine's claim-then-work shape wrote a durable boolean claim
inside the request; a crash mid-work left the claim standing, Telegram's
redelivery read "duplicate", and the update was gone — the offset fixture only
ever measured the polling seam, never the claim's own lie.

The fix under test:

* the doctrine (SKILL.md, references/updates-and-delivery.md) states the split:
  a durable inbox row (pending → done) is written BEFORE the ack, work runs off
  the request under a worker whose crashed attempt is retried;
* the shipped fixture embodies it: rules `inbox-before-ack` and `worker-retry`,
  and invariants for both acceptance cases — a crash after the ack keeps the
  queued update, and a redelivery after a crash still completes the work;
* the fixture's --self-test watches every rule's removal go red, including the
  pre-inbox claim-then-work shape reproducing the original loss.

Acceptance: crash after ack keeps the queued update; redelivery does not lose
eventual completion.
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


UPDATE = {"update_id": 5001, "message": {"text": "hi"}}


def harness(without=()):
    store = F.Store()
    return store, F.Handler(store, F.Transport(refuse_times=0), without)


# ------------------------------------------------------------------ the doctrine


def t_docs_state_the_split():
    skill = open(os.path.join(BOTS, "SKILL.md"), encoding="utf-8").read()
    ref = open(os.path.join(BOTS, "references", "updates-and-delivery.md"),
               encoding="utf-8").read()
    for needle, doc, name in [
        ("Inbox before ack — a claim is a receipt, not completion", skill,
         "SKILL.md states the split"),
        ("durable BEFORE the ack", skill, "SKILL.md snippet writes before answering"),
        ("leaves the row pending", skill, "SKILL.md separates the worker retry"),
        ("confirm only what is HELD", ref, "the polling loop confirms the durable write"),
        ("The inbox row is the claim, and it has states", ref,
         "the reference names the states"),
        ("only after the durable write", ref, "the webhook answers after the write"),
    ]:
        assert needle in doc, f"{name}: {needle!r} is not in the document"


# --------------------------------------------------- acceptance, by behaviour


def t_crash_after_ack_keeps_the_queued_update():
    store, handler = harness()
    try:
        handler.deliver(dict(UPDATE), crash="in-worker")
    except SystemError:
        pass
    assert UPDATE["update_id"] in store.acked, "the 200 never left — not this scenario"
    assert store.work == [], "the crash did not interrupt the work"
    handler.run_workers()
    assert store.work == [UPDATE["update_id"]], \
        "the acked update was lost — Telegram will never resend an acknowledged update"


def t_redelivery_completes_after_crash():
    store, handler = harness()
    try:
        handler.deliver(dict(UPDATE), crash="before-ack")
    except SystemError:
        pass
    handler.deliver(dict(UPDATE))               # Telegram got no 200, so it retries
    handler.run_workers()
    assert store.work == [UPDATE["update_id"]], \
        "the redelivery was told 'duplicate' about work that never happened"


def t_original_shape_reproduces_the_loss():
    """The negative: the pre-inbox claim-then-work shape LOSES the update — the
    exact defect the finding describes, watched failing rather than asserted."""
    store, handler = harness(without=("inbox-before-ack",))
    try:
        handler.deliver(dict(UPDATE), crash="in-worker")
    except SystemError:
        pass
    handler.deliver(dict(UPDATE))               # the redelivery hits the standing claim
    handler.run_workers()
    assert store.work == [], \
        "the pre-inbox shape unexpectedly recovered — the mutant no longer measures the defect"
    assert any("duplicate" in line for line in store.log), \
        "the redelivery was not answered 'duplicate' — the mutant drifted from the finding"


def t_redelivered_update_still_works_once():
    store, handler = harness()
    handler.deliver(dict(UPDATE))
    handler.deliver(dict(UPDATE))
    handler.run_workers()
    assert store.work == [UPDATE["update_id"]], "a plain redelivery was processed twice"


# ------------------------------------------------- the shipped fixture, as run


def t_fixture_passes_both_modes():
    for args in ([], ["--self-test"]):
        r = subprocess.run([sys.executable, FIXTURE] + args,
                           capture_output=True, text=True, timeout=120)
        assert r.returncode == 0, \
            f"update_delivery.py {' '.join(args)} fails:\n{(r.stderr or r.stdout)[-400:]}"
    out = subprocess.run([sys.executable, FIXTURE, "--self-test"],
                         capture_output=True, text=True, timeout=120).stdout
    for rule in ("inbox-before-ack", "worker-retry"):
        assert rule in out, f"the self-test never exercised {rule!r}"


def main():
    case("the doctrine states inbox-before-ack", t_docs_state_the_split)
    case("crash after ack keeps the queued update", t_crash_after_ack_keeps_the_queued_update)
    case("redelivery still completes after a crash", t_redelivery_completes_after_crash)
    case("the pre-inbox shape reproduces the original loss", t_original_shape_reproduces_the_loss)
    case("a plain redelivery still works once", t_redelivered_update_still_works_once)
    case("the shipped fixture passes both modes", t_fixture_passes_both_modes)
    if failures:
        print(f"\n{len(failures)} failure(s)")
        return 1
    print("\nall green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
