#!/usr/bin/env python3
"""FIX-TG-05.01 — one FloodWait cap does not bound an infinite retry (sherlock
audit, TG-05).

The finding: call_with_flood looped `while True` checking only `e.seconds >
cap`, so an infinite stream of SHORT flood waits (100 × 1s, each under the
cap) never stopped, though the body forbade unbounded sleeping. And the
quickstart client block used StringSession/os without importing them.

The fix under test: the retry has a BOUNDED envelope — wall-clock deadline,
cumulative-wait budget, attempt budget, cancellation, and a checkpoint/defer;
the cap is backpressure. The documented retry is re-implemented and driven by
a fake client raising 100 × 1s waits: it defers with a checkpoint, cancels on
demand, and does not retry a dead session. And the SKILL.md quickstart imports
os and StringSession (module parses via stubs, no Telegram login).

Standard library only.
"""
import asyncio
import os
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
UB = os.path.join(ROOT, "plugins", "telegram-dev", "skills", "telegram-userbots")

failures = []


def case(name, fn):
    try:
        fn()
        print(f"  ok  {name}")
    except AssertionError as e:
        failures.append(f"{name}: {e}")
        print(f"FAIL  {name}: {e}")


def t_doctrine_states_the_envelope():
    flat = " ".join(open(os.path.join(UB, "references", "rate-and-flood.md"),
                         encoding="utf-8").read().split())
    for needle in ("is NOT a stop condition",
                   "a wall-clock deadline,\na cumulative-wait budget, an attempt budget, and a "
                   "cancellation token".replace("\n", " "),
                   "The envelope is what stops the loop",
                   "DEFER with a\ncheckpoint".replace("\n", " "),
                   "The cap is backpressure"):
        assert needle in flat, f"rate-and-flood.md no longer states {needle!r}"


def t_quickstart_imports_os_and_stringsession():
    sk = open(os.path.join(UB, "SKILL.md"), encoding="utf-8").read()
    assert "import os\nfrom telethon import TelegramClient\nfrom telethon.sessions import StringSession" in sk, \
        "the quickstart client block still uses os/StringSession without importing them"


# ---------------- the bounded retry, re-implemented and driven


class FloodWaitError(Exception):
    def __init__(self, seconds):
        self.seconds = seconds
        super().__init__(f"flood {seconds}s")


class DeadSession(Exception):
    pass


async def call_with_flood(fn, *a, cap=300, deadline_s=1800, max_cumulative_s=900,
                          max_attempts=50, cancel=None, on_defer=None, clock=None, **kw):
    clock = clock or (lambda: 0.0)
    started = clock()
    cumulative = 0.0
    for attempt in range(max_attempts):
        if cancel is not None and cancel.is_set():
            raise asyncio.CancelledError("flood retry cancelled")
        try:
            return await fn(*a, **kw)
        except FloodWaitError as e:
            wait = e.seconds + 1
            over = (e.seconds > cap or clock() - started + wait > deadline_s
                    or cumulative + wait > max_cumulative_s)
            if over:
                if on_defer:
                    on_defer(cumulative=cumulative, attempt=attempt)
                raise
            cumulative += wait
            # no real sleep in the test
    raise RuntimeError("flood retry exhausted")


def run(coro):
    return asyncio.run(coro)


def t_infinite_short_floods_are_bounded():
    calls = {"n": 0}

    async def always_floods():
        calls["n"] += 1
        raise FloodWaitError(1)                    # always 1s, under the cap

    checkpoint = {}
    def defer(**kw):
        checkpoint.update(kw)

    # virtual clock advances 1s per call so the deadline also bounds it
    ticks = {"t": 0.0}
    def clock():
        ticks["t"] += 1
        return ticks["t"]

    try:
        run(call_with_flood(always_floods, cap=300, max_cumulative_s=10,
                            max_attempts=1000, on_defer=defer, clock=clock))
        raise AssertionError("an infinite stream of short floods never stopped")
    except FloodWaitError:
        pass
    assert checkpoint, "no checkpoint was saved on defer"
    assert calls["n"] < 1000, "the retry did not defer early — it exhausted attempts instead"


def t_cancellation_works():
    ev = asyncio.Event()
    ev.set()

    async def never_called():
        raise AssertionError("fn ran despite a set cancel token")

    try:
        run(call_with_flood(never_called, cancel=ev))
        raise AssertionError("cancellation did not raise")
    except asyncio.CancelledError:
        pass


def t_dead_session_is_not_retried():
    calls = {"n": 0}

    async def dead():
        calls["n"] += 1
        raise DeadSession("revoked")

    try:
        run(call_with_flood(dead))
        raise AssertionError("a dead session did not surface")
    except DeadSession:
        pass
    assert calls["n"] == 1, "a dead session was retried — only FloodWait is retried"


def t_success_returns_immediately():
    async def ok():
        return "done"
    assert run(call_with_flood(ok)) == "done"


def main():
    case("the doctrine states the bounded envelope", t_doctrine_states_the_envelope)
    case("the quickstart imports os and StringSession",
         t_quickstart_imports_os_and_stringsession)
    case("an infinite stream of short floods is bounded and checkpointed",
         t_infinite_short_floods_are_bounded)
    case("cancellation works", t_cancellation_works)
    case("a dead session is not retried", t_dead_session_is_not_retried)
    case("a success returns immediately", t_success_returns_immediately)
    if failures:
        print(f"\n{len(failures)} failure(s)")
        return 1
    print("\nall green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
