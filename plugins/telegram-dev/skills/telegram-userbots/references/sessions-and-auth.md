# Sessions, credentials, and logging in

**Load this when** creating a session, storing one, moving one between machines,
or working out why a process that ran yesterday is asking for a code.

*Read against Telethon 1.44.0 on 2026-08-25.*

## Contents

- [What each secret is](#what-each-secret-is)
- [Creating a session, once, by a human](#creating-a-session-once-by-a-human)
- [Storing it](#storing-it)
- [Two-factor, and the login that hangs](#two-factor-and-the-login-that-hangs)
- [Revocation and rotation](#revocation-and-rotation)
- [Version pinning](#version-pinning)

## What each secret is

| Secret | From | Weight |
|---|---|---|
| `api_id` / `api_hash` | `my.telegram.org` | identifies the **application**. Not public, not the account |
| The session | produced by logging in | **is the account**: full access, no password, no 2FA prompt |
| The phone number | the human | the recovery path, and the thing an attacker needs next |

A leaked `api_hash` lets someone build an app that looks like yours. A leaked
session lets them *be the user*. They are not in the same class and should not be
in the same secret store entry.

## Creating a session, once, by a human

Interactive login is a human step, and pretending otherwise produces code that
blocks forever in CI:

```python
# scripts/login.py — run by a person, on a laptop, once
from telethon import TelegramClient
from telethon.sessions import StringSession

with TelegramClient(StringSession(), API_ID, API_HASH) as client:
    print(client.session.save())        # paste into the secret store
```

`StringSession` produces a portable string; the default file session produces a
`.session` SQLite file that is equally sensitive and much easier to commit by
accident. **Prefer the string** in anything deployed: it lives in the secret
store next to every other credential and never lands in the working tree.

## Storing it

- **Secret store, not the repository.** A `.session` file in `.gitignore` is the
  minimum, not the plan.
- **Not in the image.** Baking one into a container ships the account to whoever
  can pull it.
- **Not in logs, not in error reports.** A crash handler that dumps config dumps
  the account. This is the same rule `error-tracking` states for database URLs,
  with a higher blast radius.
- **One session per process.** Two processes on one session fight over the
  connection and produce errors that look like network faults.

## Two-factor, and the login that hangs

If the account has a password, login needs it after the code. Telethon raises
`SessionPasswordNeededError`; a script that does not handle it appears to hang.
The password is a third secret, needed only at session creation — do not store it
beside a session that no longer needs it.

## Revocation and rotation

A session ends when the user terminates it in Telegram's **Devices** screen, when
the password changes, or when Telegram decides. All three look identical to your
code: an `AuthKeyUnregisteredError` or an unauthorised state on the next call.

- **Detect and alert, naming the account.** Do not retry: reconnecting with a
  dead session in a loop is a good way to draw attention to the account.
- **Have the recreation procedure written down** and runnable by whoever is on
  call, because it needs the phone.

## Version pinning

Telethon minor releases have changed session format and entity-cache behaviour.
Four bots in this estate pin `telethon==1.37.0` deliberately while a fifth runs
`1.44.0`, and the pin's reason is in the requirements file beside it.

Pin the exact version. Upgrade one bot at a time, with a session you can
recreate, and verify the two things a minor release touches: that the existing
session still opens, and that peer resolution still finds what it used to.
