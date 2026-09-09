# FloodWait, pacing, and takeout

**Load this when** anything iterates over chats, users, messages or media.

*Read against Telethon 1.44.0 on 2026-08-25.*

## Contents

- [FloodWait is a number, not a condition](#floodwait-is-a-number-not-a-condition)
- [Pacing that avoids it](#pacing-that-avoids-it)
- [`takeout` is the sanctioned path for bulk](#takeout-is-the-sanctioned-path-for-bulk)
- [Errors worth handling by name](#errors-worth-handling-by-name)

## FloodWait is a number, not a condition

`FloodWaitError.seconds` is how long Telegram wants you to wait. It is exact, and
it is the only number in the situation that is not a guess.

`e.seconds > cap` alone is NOT a stop condition: a stream of SHORT flood
waits — 100 × 1s, each under the cap — loops forever while the body forbids
unbounded sleeping. The retry needs a BOUNDED envelope: a wall-clock deadline,
a cumulative-wait budget, an attempt budget, and a cancellation token; the
per-call `cap` is backpressure (one wait too long to sit through), the budgets
are the policy choice about the whole operation.

```python
import time

async def call_with_flood(fn, *a, cap=300, deadline_s=1800,
                          max_cumulative_s=900, max_attempts=50,
                          cancel=None, on_defer=None, **kw):
    started = time.monotonic()
    cumulative = 0.0
    for attempt in range(max_attempts):
        if cancel is not None and cancel.is_set():
            raise asyncio.CancelledError("flood retry cancelled")
        try:
            return await fn(*a, **kw)
        except FloodWaitError as e:
            wait = e.seconds + 1                 # +1: exact `seconds` lands on the boundary
            over_cap = e.seconds > cap
            over_deadline = time.monotonic() - started + wait > deadline_s
            over_budget = cumulative + wait > max_cumulative_s
            if over_cap or over_deadline or over_budget:
                # Bounded: checkpoint the work so it can resume, and DEFER —
                # do not keep sleeping. A long wait is a policy decision, not a loop.
                if on_defer is not None:
                    on_defer(reason="flood", seconds=e.seconds,
                             cumulative=cumulative, attempt=attempt)
                log.warning("flood_deferred", seconds=e.seconds, cumulative=cumulative)
                raise                            # let the caller re-enqueue from the checkpoint
            cumulative += wait
            await asyncio.sleep(wait)
    raise RuntimeError(f"flood retry exhausted {max_attempts} attempts")
```

- **The envelope is what stops the loop**, not the single `cap`. 100 × 1s waits
  hit the cumulative-wait budget (or the attempt budget) and DEFER with a
  checkpoint — they do not sleep forever.
- **The `+1` matters**: sleeping exactly `seconds` lands on the boundary and
  earns a second wait.
- **The cap is backpressure.** Seconds mean pacing; minutes mean the account is
  being limited; hours mean stop and look. Sleeping through an hour-long wait is
  how a limited account becomes a banned one — so a wait over the cap defers to
  the checkpoint queue rather than blocking.
- **Never sleep inside a request handler.** A flood wait in a web request is an
  outage; in a worker it is a delay.

## Pacing that avoids it

There is no published rate table for MTProto, which is precisely why the wait is
the signal. What holds in practice:

- **Space out writes.** Sending, joining, inviting and reading many different
  peers are the expensive operations.
- **Reads of things you already have are cheap.** Iterating messages in a chat
  you are in is much cheaper than resolving a hundred usernames.
- **A fresh account has a much lower ceiling than an old one**, and a fresh
  account doing bulk work is the classic ban shape.
- **Random jitter beats a fixed interval** — a perfectly regular request train is
  the most identifiable thing an automated client can do.

## `takeout` is the sanctioned path for bulk

For exporting history at volume, Telethon exposes a takeout session:

```python
async with client.takeout(finalize=True) as takeout:
    async for message in takeout.iter_messages(peer):
        ...
```

It tells Telegram what you are doing, raises the limits for it, and can be
resumed. Using it is both faster and less likely to end the account than the same
loop outside it. It requires the user to approve the takeout in their client the
first time — another human step.

## Errors worth handling by name

| Error | Means |
|---|---|
| `FloodWaitError` | wait exactly `seconds` |
| `AuthKeyUnregisteredError` | the session is dead — alert, do not retry |
| `PeerIdInvalidError` | this account has never encountered that peer |
| `ChannelPrivateError` | not a member, or removed |
| `UserDeactivatedBanError` | **the account is banned**. Stop everything |
| `RPCError` | the base class; catching only this hides all of the above |

`UserDeactivatedBanError` is the one that must page a human rather than restart.
