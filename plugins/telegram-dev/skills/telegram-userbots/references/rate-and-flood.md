# FloodWait, pacing, and takeout

**Load this when** anything iterates over chats, users, messages or media.

*Read against Telethon 1.44.0 on 2026-08-25.*

## FloodWait is a number, not a condition

`FloodWaitError.seconds` is how long Telegram wants you to wait. It is exact, and
it is the only number in the situation that is not a guess.

```python
async def call_with_flood(fn, *a, cap=300, **kw):
    while True:
        try:
            return await fn(*a, **kw)
        except FloodWaitError as e:
            if e.seconds > cap:
                log.error("flood_wait_too_long", seconds=e.seconds)
                raise                      # a limit this long is a decision, not a sleep
            await asyncio.sleep(e.seconds + 1)
```

- **The `+1` matters**: sleeping exactly `seconds` lands on the boundary and
  earns a second wait.
- **The cap matters more.** Seconds mean pacing; minutes mean the account is
  being limited; hours mean stop and look. Sleeping through an hour-long wait is
  how a limited account becomes a banned one.
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
