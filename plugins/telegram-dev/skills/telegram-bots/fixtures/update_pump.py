#!/usr/bin/env python3
"""The rules that keep one slow handler from holding a Telegram bot for everyone,
and the proof that each one can fail.

    python3 update_pump.py              # run the invariants against the reference pump
    python3 update_pump.py --self-test  # remove one rule at a time; each MUST go red

The model is a discrete-event simulation on a virtual clock: updates arrive at
given times, handlers take given durations, and the pump decides when each one
starts. No threads, no sleeps, no network, so a run is exact and repeatable.

`--self-test` is the half that makes this evidence. For every invariant it names
the rule whose removal must turn it red, removes exactly that rule, and fails if
the assertion still passes. A check nobody has watched failing is
indistinguishable from one that cannot fail.

Point it at YOUR bot by reading each rule as a question about your dispatcher:
does the poll wait for handlers, are a chat's updates ordered, is there a
ceiling, does a payment wait behind it, where is the flood window measured from.
Standard library only.
"""
from __future__ import annotations

import heapq
import sys

RULES = (
    # The poll hands an update to a queue and asks Telegram for the next batch at
    # once. Without it the poll waits for every handler of the batch before the
    # next getUpdates (the shape of a library that awaits Promise.all over the
    # batch), so one slow handler holds every chat.
    "free-poll",
    # One chat's updates run one at a time, in arrival order. Without it two taps
    # of one chat run side by side and race on the same state.
    "per-chat-order",
    # At most `ceiling` handlers run at once across chats. Without it a burst
    # starts every handler together and exhausts the database pool and the
    # outbound sockets it shares with everything else.
    "global-ceiling",
    # A payment update (pre_checkout_query, successful_payment) runs at once,
    # outside the ceiling. Without it a pre-checkout waits for a free slot while
    # every slot is held by a slow handler, and misses its ten-second window.
    "payment-lane",
    # The flood window is measured from the update's ARRIVAL. Without it a second
    # tap queued behind a slow first one is judged when it starts, which is after
    # the window, and the double tap acts twice.
    "flood-from-arrival",
    # The screen being drawn is NOT superseded when a newer update of the chat
    # queues. Without it a double tap supersedes the first screen, the flood gate
    # then drops the second tap, and the chat is left with no screen at all.
    "no-supersede-at-queue",
    # A callback that has to wait (behind its chat, or for a free slot) is
    # answered at once. Without it the button spins for as long as it waits.
    "answer-waiting-callback",
    # An update_id already seen is not handled again. Without it a redelivered
    # update runs twice.
    "dedupe",
    # One chat may queue at most `per_chat` updates; the rest are dropped and
    # their callbacks answered. Without it one chat that floods grows a queue
    # without bound.
    "per-chat-cap",
)

PAYMENT_KINDS = ("pre_checkout_query", "successful_payment")


class Update:
    def __init__(self, uid, at, chat, kind="message", takes=0.1, user=None):
        self.uid, self.at, self.chat, self.kind, self.takes = uid, at, chat, kind, takes
        self.user = chat if user is None else user
        self.started = None
        self.ended = None
        self.answered = None     # when a callback stopped spinning
        self.outcome = None      # 'handled' | 'flood' | 'dropped' | 'dedup'


class Pump:
    def __init__(self, without=(), ceiling=32, per_chat=50, flood_window=1.0):
        for rule in without:
            if rule not in RULES:
                raise ValueError(f"unknown rule {rule!r}")
        self.without = set(without)
        self.ceiling, self.per_chat, self.flood_window = ceiling, per_chat, flood_window
        self.events = []         # (time, seq, kind, payload)
        self.seq = 0
        self.now = 0.0
        self.queues = {}         # chat -> list of waiting updates
        self.running = set()     # chats with a handler in flight
        self.ready = []          # chats ready to start, in order
        self.active = 0
        self.max_active = 0
        self.max_depth = 0
        self.seen = set()
        self.last_ts = {}        # user -> flood stamp
        self.screen = {}         # chat -> update whose screen is current
        self.superseded = set()  # updates whose screen was superseded
        self.drawn = []          # (chat, uid) screens actually drawn
        self.batch_pending = 0   # batch mode: handlers of the current batch
        self.backlog = []        # batch mode: arrived, not yet polled

    def has(self, rule):
        return rule not in self.without

    def _push(self, t, kind, payload):
        self.seq += 1
        heapq.heappush(self.events, (t, self.seq, kind, payload))

    def run(self, updates):
        for u in updates:
            self._push(u.at, "arrive", u)
        if not self.has("free-poll"):
            self._push(0.0, "poll", None)
        while self.events:
            self.now, _, kind, payload = heapq.heappop(self.events)
            getattr(self, "_on_" + kind)(payload)
        return updates

    # -- the poll ----------------------------------------------------------
    def _on_arrive(self, u):
        if self.has("free-poll"):
            self.dispatch(u)
        else:
            self.backlog.append(u)

    def _on_poll(self, _):
        # Batch mode: take what arrived, run it all, poll again only when every
        # handler of the batch is done.
        if not self.backlog:
            if any(k == "arrive" for _, _, k, _ in self.events):
                nxt = min(t for t, _, k, _ in self.events if k == "arrive")
                self._push(nxt, "poll", None)
            return
        batch, self.backlog = self.backlog, []
        self.batch_pending = len(batch)
        for u in batch:
            self._start(u)

    # -- the pump ----------------------------------------------------------
    def dispatch(self, u):
        if self.has("dedupe"):
            if u.uid in self.seen:
                u.outcome = "dedup"
                return
            self.seen.add(u.uid)
        if u.kind in PAYMENT_KINDS and self.has("payment-lane"):
            self._start(u)
            return
        if not self.has("per-chat-order"):
            self._enqueue_global(u)
            return
        q = self.queues.setdefault(u.chat, [])
        depth = len(q) + (1 if u.chat in self.running else 0)
        if self.has("per-chat-cap") and depth >= self.per_chat + 1:
            u.outcome = "dropped"
            if u.kind == "callback_query" and self.has("answer-waiting-callback"):
                u.answered = self.now
            return
        q.append(u)
        self.max_depth = max(self.max_depth, depth + 1)
        if depth > 0:
            self._waiting(u)
            if not self.has("no-supersede-at-queue") and self.screen.get(u.chat) is not None:
                self.superseded.add(self.screen[u.chat].uid)
        self._mark_ready(u.chat)
        self._pump()
        if depth == 0 and u in q:
            self._waiting(u)   # its chat is idle, every slot is taken

    def _waiting(self, u):
        if u.kind == "callback_query" and self.has("answer-waiting-callback") and u.answered is None:
            u.answered = self.now

    def _enqueue_global(self, u):
        # No per-chat queue: one global line under the ceiling.
        self.queues.setdefault(None, []).append(u)
        if self.active >= self._ceiling():
            self._waiting(u)
        self._mark_ready(None)
        self._pump()

    def _ceiling(self):
        return self.ceiling if self.has("global-ceiling") else 10 ** 9

    def _mark_ready(self, chat):
        if chat not in self.ready and (chat is None or chat not in self.running):
            self.ready.append(chat)

    def _pump(self):
        while self.ready and self.active < self._ceiling():
            chat = self.ready[0]
            q = self.queues.get(chat) or []
            if not q:
                self.ready.pop(0)
                continue
            if chat is not None:
                self.ready.pop(0)
            u = q.pop(0)
            if chat is not None:
                self.running.add(chat)
            self._start(u)

    def _start(self, u):
        u.started = self.now
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        if u.kind == "callback_query" and u.answered is None:
            u.answered = self.now   # the up-front ack every handler gets
        # flood middleware
        if u.kind not in PAYMENT_KINDS:
            stamp_at = u.at if self.has("flood-from-arrival") else self.now
            last = self.last_ts.get(u.user)
            if last is not None and abs(stamp_at - last) < self.flood_window:
                u.outcome = "flood"
                self._push(self.now, "end", u)
                return
            self.last_ts[u.user] = max(last or stamp_at, stamp_at)
            self.screen[u.chat] = u
        u.outcome = "handled"
        self._push(self.now + u.takes, "end", u)

    def _on_end(self, u):
        u.ended = self.now
        self.active -= 1
        if u.outcome == "handled" and u.kind not in PAYMENT_KINDS:
            if self.screen.get(u.chat) is u and u.uid not in self.superseded:
                self.drawn.append((u.chat, u.uid))
        if not self.has("free-poll"):
            self.batch_pending -= 1
            if self.batch_pending == 0:
                self._push(self.now, "poll", None)
            return
        if u.kind in PAYMENT_KINDS and self.has("payment-lane"):
            self._pump()
            return
        if self.has("per-chat-order"):
            self.running.discard(u.chat)
            if self.queues.get(u.chat):
                self._mark_ready(u.chat)
        self._pump()


# -- invariants ------------------------------------------------------------
INVARIANTS = []


def invariant(name, breaks):
    def deco(fn):
        INVARIANTS.append((name, breaks, fn))
        return fn
    return deco


@invariant("one handler held for 60 s does not hold the other chats", "free-poll")
def _(without):
    slow = Update(1, 0.0, chat="a", takes=60.0)
    others = [Update(100 + i, 0.5 + i * 0.01, chat=f"c{i}") for i in range(200)]
    Pump(without).run([slow] + others)
    worst = max(u.started - u.at for u in others)
    assert worst < 2.0, f"another chat waited {worst:.1f} s behind one slow handler"


@invariant("one chat's updates run one at a time, in order", "per-chat-order")
def _(without):
    first = Update(1, 0.0, chat="a", takes=3.0)
    second = Update(2, 1.5, chat="a")          # outside the flood window
    Pump(without).run([first, second])
    assert second.started >= first.ended, (
        f"the second update of a chat started at {second.started} while the first ran until {first.ended}")


@invariant("no more than `ceiling` handlers run at once", "global-ceiling")
def _(without):
    burst = [Update(i, 0.0, chat=f"c{i}", takes=5.0) for i in range(100)]
    p = Pump(without, ceiling=32)
    p.run(burst)
    assert p.max_active <= 32, f"{p.max_active} handlers ran at once against a ceiling of 32"


@invariant("a pre-checkout is answered inside ten seconds while every slot is busy", "payment-lane")
def _(without):
    hogs = [Update(i, 0.0, chat=f"h{i}", takes=60.0) for i in range(2)]
    pay = Update(9, 1.0, chat="buyer", kind="pre_checkout_query")
    Pump(without, ceiling=2).run(hogs + [pay])
    assert pay.started - pay.at < 10.0, f"the pre-checkout waited {pay.started - pay.at:.0f} s for a slot"


@invariant("a double tap queued behind a slow first tap is still dropped", "flood-from-arrival")
def _(without):
    first = Update(1, 0.0, chat="a", kind="callback_query", takes=1.3)
    second = Update(2, 0.2, chat="a", kind="callback_query")
    Pump(without).run([first, second])
    acted = [u.uid for u in (first, second) if u.outcome == "handled"]
    assert acted == [1], f"a double tap inside the 1 s window acted {len(acted)} times"


@invariant("a double tap leaves the first screen drawn", "no-supersede-at-queue")
def _(without):
    first = Update(1, 0.0, chat="a", kind="callback_query", takes=0.3)
    second = Update(2, 0.15, chat="a", kind="callback_query")
    p = Pump(without)
    p.run([first, second])
    assert p.drawn == [("a", 1)], f"screens drawn: {p.drawn} (the chat was left empty)"


@invariant("a callback that waits stops spinning at once", "answer-waiting-callback")
def _(without):
    busy = Update(1, 0.0, chat="a", takes=5.0)
    tap = Update(2, 1.5, chat="a", kind="callback_query")
    hog = Update(3, 0.0, chat="h", takes=5.0)
    other = Update(4, 1.0, chat="b", kind="callback_query")   # idle chat, no free slot
    Pump(without).run([busy, tap])
    Pump(without, ceiling=1).run([hog, other])
    for u in (tap, other):
        assert u.answered - u.at < 1.0, f"a waiting button spun for {u.answered - u.at:.1f} s"


@invariant("a redelivered update_id is handled once", "dedupe")
def _(without):
    a, b = Update(7, 0.0, chat="a"), Update(7, 0.5, chat="b")   # same update_id twice
    Pump(without).run([a, b])
    handled = [u for u in (a, b) if u.outcome == "handled"]
    assert len(handled) == 1, f"update 7 was handled {len(handled)} times"


@invariant("a flooding chat is capped and the others are unaffected", "per-chat-cap")
def _(without):
    stuck = Update(1, 0.0, chat="a", takes=60.0)
    flood = [Update(10 + i, 0.1 + i * 0.001, chat="a", user=f"bot{i}") for i in range(500)]
    other = Update(9999, 1.0, chat="b")
    p = Pump(without, per_chat=50)
    p.run([stuck] + flood + [other])
    assert p.max_depth <= 51, f"one chat queued {p.max_depth} updates against a cap of 50"
    assert other.started - other.at < 2.0, "another chat waited behind the flood"


def run(without=()):
    failures = []
    for name, _breaks, fn in INVARIANTS:
        try:
            fn(without)
        except AssertionError as e:
            failures.append(f"{name}: {e}")
    return failures


def self_test():
    ok = True
    for name, breaks, fn in INVARIANTS:
        try:
            fn((breaks,))
        except AssertionError:
            print(f"  red as it must be without {breaks!r}: {name}")
            continue
        print(f"FAIL: removing {breaks!r} left this green: {name}")
        ok = False
    named = {b for _, b, _ in INVARIANTS}
    for rule in RULES:
        if rule not in named:
            print(f"FAIL: rule {rule!r} has no invariant that its removal turns red")
            ok = False
    return ok


def main():
    failures = run()
    if failures:
        for f in failures:
            print("FAIL:", f)
        return 1
    print(f"update_pump: {len(INVARIANTS)} invariants hold against the reference pump")
    if "--self-test" in sys.argv:
        if not self_test():
            return 1
        print(f"update_pump: every one of {len(RULES)} rules was watched failing")
    return 0


if __name__ == "__main__":
    sys.exit(main())
