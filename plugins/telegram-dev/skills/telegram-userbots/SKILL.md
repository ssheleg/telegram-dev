---
name: telegram-userbots
description: >-
  Use when a Telegram job needs a user account rather than a bot token — reading
  history a bot cannot see, acting as a person, exporting at scale, or
  downloading past the Bot API ceiling — with Telethon or another MTProto
  client. Covers the decision of whether a user account is needed at all, the
  session file as a credential equal to the password, api_id and api_hash,
  FloodWaitError as the API working rather than failing, entity resolution and
  its cache, pinning across minor releases that move session and cache
  behaviour, two-factor login, takeout for bulk export, and the account-ban
  risk a bot token does not carry. Triggers - "telethon", "pyrogram", "mtproto",
  "userbot", "user account", "read channel history", "FloodWaitError",
  "api_hash", "юзербот", "телетон", "мтпрото", "сессия телеграм". Not for
  ordinary bots (telegram-bots) or the web layer (telegram-miniapps).
license: MIT
---

# Telegram userbots — MTProto, and what it costs

A bot token is issued to software. **An MTProto session is a logged-in human
being** — the same authority the person has, held in a file, with none of the
protections a token has. Everything in this skill follows from that one
difference.

*Read against Telethon **1.44.0** and `core.telegram.org` on 2026-08-25. Telethon
minor releases change session and entity-cache behaviour; the version you are on
is a fact to check, not to assume.*

Deep material, loaded on demand:

| Read | When |
|---|---|
| [`references/sessions-and-auth.md`](references/sessions-and-auth.md) | logging in, storing a session, rotating one, or moving between machines |
| [`references/rate-and-flood.md`](references/rate-and-flood.md) | anything that loops over chats, users or messages — FloodWait, pacing, takeout |
| [`references/entities-and-history.md`](references/entities-and-history.md) | resolving peers, iterating history, downloading media at scale |

---

## First: do you actually need one?

Answer this before writing a line, and write the answer down.

| The job | Bot API can | Verdict |
|---|---|---|
| React to messages in chats the bot is in | yes | **use a bot** |
| Send to users who started the bot | yes | **use a bot** |
| Read a public channel it is admin of | yes | **use a bot** |
| Read history of a channel it does not administer | no | userbot |
| Read a chat's past, from before it joined | no | userbot |
| Act as a specific person | no | userbot |
| Download a file over 20 MB | no | userbot, **or a local Bot API server** |
| Enumerate a group's members at scale | no | userbot, and see the risk below |

**The local Bot API server closes the file ceiling without an account.** Reaching
for a user session because of a 21 MB video is trading a permanent liability for
an infrastructure task you were going to have anyway.

**The refusal, and it is not a formality:** a user account can be limited or
banned, and Telegram does not explain, appeal quickly, or restore what was in it.
If the account is a real person's, the blast radius is their messages, their
groups and their logins. Automating a personal account is a decision with a
named owner or it is not a decision.

## The session file is the credential

```python
from telethon import TelegramClient

client = TelegramClient(
    session=StringSession(os.environ["TG_SESSION"]),   # from the secret store
    api_id=int(os.environ["TG_API_ID"]),
    api_hash=os.environ["TG_API_HASH"],
)
```

- **A `.session` file grants full access to the account, without the password and
  without the 2FA prompt.** Copying one to another machine logs that machine in.
  It belongs in `.gitignore`, in a secret store, in backups you would give a
  password the same treatment — and never in an image layer or a log.
- **`api_id`/`api_hash` come from `my.telegram.org`** and identify the
  *application*, not the account. They are not a session and not a secret of the
  same weight, but they are still not public.
- **Losing a session is recoverable; leaking one is an incident.** Revoke from
  the account's own *Devices* screen, which ends that session everywhere.
- Verified on this machine on 2026-08-25: five of five Telethon projects
  gitignore the session and **none has one tracked in git** — the one trap this
  estate has actually closed. Keep it closed.

## `FloodWaitError` is the API working

```python
from telethon.errors import FloodWaitError

try:
    await client.send_message(peer, text)
except FloodWaitError as e:
    if e.seconds > MAX_ACCEPTABLE:      # a decision, not a sleep
        raise
    await asyncio.sleep(e.seconds + 1)
    await client.send_message(peer, text)
```

- **It is not a failure to swallow and not a signal to retry blindly.** It names
  exactly how long to wait; anything else is guessing at a number Telegram
  already told you.
- **A very large `seconds` is a different event.** Minutes mean you are pacing
  too hard; hours mean the account is being limited, and continuing is how a
  limit becomes a ban. Cap it, alert, stop.
- **Sleeping inside a request handler is how one flood becomes an outage.** The
  wait belongs in a worker with a queue, not in the path a user is waiting on.
- Measured across six Telethon projects here on 2026-08-25: **three of six handle
  `FloodWaitError` at all.** The other three run until the first limit and then
  stop, in whatever state they were in.

## Pin the minor, and know why

Four bots in this estate pin `telethon==1.37.0` while a fifth runs `1.44.0`, and
the pin carries its reason in `requirements.txt`: *minor releases change session
and entity-cache behaviour, and a jump of seven minors on a live bot needs its own
change with its own verification.*

That is the right shape and it is worth stating as doctrine. **A userbot's
dependency is not a library, it is a protocol client holding a login.** An
upgrade can invalidate a session format, change what `get_entity` costs, or move
an exception's module. Upgrade deliberately, one bot at a time, with a session
you can recreate.

## Entities are resolved, and resolution is not free

`get_entity` may hit the network, and doing it in a loop is the most common way
to earn a FloodWait that looks unexplained.

- **Prefer ids you already have.** A cached `InputPeer` costs nothing; a username
  costs a request.
- **`PeerIdInvalidError` usually means the account has never seen that peer**, not
  that the id is wrong. A user account can only address what it has encountered.
- **Iterate with the library's own iterators** (`iter_messages`, `iter_dialogs`)
  and let them page; hand-rolled offsets re-request and re-trip the limits.
- For a bulk export, **`takeout` exists and is the sanctioned path** — it raises
  the limits for exactly this and tells Telegram what you are doing.

Detail in [`references/entities-and-history.md`](references/entities-and-history.md).

## Two accounts, two lifetimes

A userbot has a second failure mode a bot does not: **the human logs in
somewhere, changes the password, or terminates sessions**, and your process dies
holding a session that is no longer valid. Treat it as an expected event —
surface it as an alert with the account named, not as a crash loop — and never
put a userbot on the critical path of something a bot could serve.

## Before you ship

1. **The reason a user account is required is written down**, and the bot-API
   alternative was checked (§ *First: do you actually need one?*).
2. **The session is in a secret store, gitignored, and revocable** (§ *The
   session file is the credential*).
3. **`FloodWaitError` is caught, capped and alerted on** — never slept off
   unbounded (§ *`FloodWaitError` is the API working*).
4. **The client version is pinned**, and the upgrade is its own change (§ *Pin
   the minor*).
5. **A dead session pages a human** rather than restarting forever (§ *Two
   accounts, two lifetimes*).
