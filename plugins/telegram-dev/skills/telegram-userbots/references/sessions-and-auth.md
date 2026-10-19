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
- [What logging out ends, and the session that is not yours](#what-logging-out-ends-and-the-session-that-is-not-yours)
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

- **Detect and alert, naming the account.** This is the TERMINAL auth state:
  the process may be live, but readiness is false and it stays false until a
  fresh login. Do not retry, and **do not let a supervisor restart it** — a
  supervisor restart is for the `recoverable` policy only; a revoked session is
  `terminal` and lands on the STOP-and-alert row of the shared recovery
  contract (error-tracking states the table). A bounded retry that keeps
  hitting the same `AuthKeyUnregisteredError` is terminal, not "try harder".
  (A transient `401` a fresh CONNECT fixes — a rotated token elsewhere — is the
  other branch, where a bounded retry or a restart is legitimate.)
- **Have the recreation procedure written down** and runnable by whoever is on
  call, because it needs the phone.

## What logging out ends, and the session that is not yours

*Read against `core.telegram.org` (`/api/auth`, `/api/qr-login`, `/api/links`,
`/api/config` and the method pages named below) and `fragment.com/about` on
2026-10-19; Telethon names checked in the 1.44.0 wheel the same day.*

**Log Out is not a lockout.** `auth.logOut` may return a `future_auth_token`,
and a client is told to keep up to 20 of them. When that client later calls
`auth.sendCode` with them in `codeSettings.logout_tokens` for the same account,
an unexpired token skips the login code: with no two-step password the call
answers "authorized" outright, with one it asks only for the password. A device
that logged out cleanly can therefore come back without a code, and **the
two-step password is what still stands in its way.** (The Telethon 1.44.0
client neither stores nor sends these tokens; an official app is a different
client.)

**Terminating a session is the revocation, and it is done from another one.**

| Call (Telethon class) | Effect |
|---|---|
| `account.getAuthorizations` (`account.GetAuthorizationsRequest`) | every logged-in session: `hash`, `current`, `official_app`, `api_id`, `app_name`, `device_model`, `ip`, `country`, `date_active`, `unconfirmed`, `password_pending` |
| `account.resetAuthorization(hash)` (`account.ResetAuthorizationRequest`) | logs out that one session |
| `auth.resetAuthorizations` (`auth.ResetAuthorizationsRequest`) | terminates every session except the current one |

Both reset calls refuse with `FRESH_RESET_AUTHORISATION_FORBIDDEN` when the
session making the call is less than 24 hours old, so **a session an attacker
just created cannot evict the owner's older one, and a fresh one of yours cannot
evict theirs either**: keep an old, trusted session (the owner's phone) as the
one that terminates. The human path is the same operation: Telegram's FAQ sends
a user to *Settings > Devices* (or *Privacy & Security > Active Sessions*) to
terminate a session on a lost device.

**A new login announces itself to the other sessions.** They receive
`updateNewAuthorization` (`types.UpdateNewAuthorization`); when its `unconfirmed`
flag is set, the client is expected to ask whether the user recognises it, then
confirm (`account.changeAuthorizationSettings` with `confirmed`) or log it out
(`account.resetAuthorization` with its `hash`). Unanswered, it confirms itself
after the server's `authorization_autoconfirm_period` (604800 seconds, seven
days, in the documented example config). An owner-side monitor is a userbot
doing exactly this: alert a human on every `UpdateNewAuthorization`, and treat a
session with an unfamiliar `api_id` or country as one to terminate.

**Two links hand over a login.**

- **`tg://login?token=<base64url>`** is the QR login. The app that wants in
  calls `auth.exportLoginToken` (the token usually lives 30 seconds); any
  already logged-in app that calls `auth.acceptLoginToken` on it **logs in the
  app that generated it.** The flow has no code step. Accepting a login token
  someone else sent you hands them a session; a userbot must never accept one it
  did not generate itself.
- **`t.me/login/<code>`** (`tg://login?code=<code>`) carries the login code
  itself. Forwarding it is giving the code away.

**A `+888` number gets its code on Fragment, not by SMS.** Collectible numbers
receive login codes on `fragment.com`, read by connecting the TON wallet that
holds the number (the API reports `auth.sentCodeTypeFragmentSms` with the URL).
For such an account the wallet is the code channel: guard it as the SIM, and set
a two-step password so the code alone is not the account.

## Version pinning

Telethon minor releases have changed session format and entity-cache behaviour.
Four bots in this estate pin `telethon==1.37.0` deliberately while a fifth runs
`1.44.0`, and the pin's reason is in the requirements file beside it.

Pin the exact version. Upgrade one bot at a time, with a session you can
recreate, and verify the two things a minor release touches: that the existing
session still opens, and that peer resolution still finds what it used to.
