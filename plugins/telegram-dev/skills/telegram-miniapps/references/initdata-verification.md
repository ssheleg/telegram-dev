# Verifying `initData` — both algorithms, and every way they are got wrong

**Load this when** implementing or reviewing verification, or when a correct-looking
implementation rejects everything (or accepts everything).

*Read from `core.telegram.org/bots/webapps` on 2026-08-25. The runnable version of
everything below is [`../fixtures/verify_initdata.py`](../fixtures/verify_initdata.py),
whose nine checks watch each rule refuse its own defect.*

## Contents

- [What arrives](#what-arrives)
- [The bot-token algorithm](#the-bot-token-algorithm)
- [Node and Go](#node-and-go)
- [The Ed25519 third-party algorithm](#the-ed25519-third-party-algorithm)
- [Failure cases, and which of them still return "valid"](#failure-cases-and-which-of-them-still-return-valid)
- [Turning a verified blob into a session](#turning-a-verified-blob-into-a-session)

## What arrives

`window.Telegram.WebApp.initData` is a **url-encoded query string**, not JSON:

```
query_id=AAH…&user=%7B%22id%22%3A100200300%2C…%7D&auth_date=1756100000&signature=…&hash=…
```

| Field | Note |
|---|---|
| `user` | a **JSON string**. Keep it as the string that arrived — see the trap below |
| `auth_date` | unix seconds; the freshness check has nothing else to use |
| `query_id` | present when the app was opened from an inline button; needed by `answerWebAppQuery` |
| `hash` | the HMAC. Removed before building the check string |
| `signature` | the Ed25519 signature for third parties. **Also removed** before the HMAC check string |
| `start_param`, `chat_type`, `chat_instance`, `receiver`, `chat` | present depending on how the app was opened |

## The bot-token algorithm

1. Parse the query string **once**. Values are now decoded.
2. Take out `hash`. Take out `signature`.
3. Sort the remaining keys alphabetically.
4. Build `key=value` lines joined with `\n` (0x0A).
5. `secret = HMAC_SHA256(key=b"WebAppData", msg=bot_token)`.
6. `expected = hex(HMAC_SHA256(key=secret, msg=check_string))`.
7. Compare with `hash` in **constant time**.
8. Reject when `now - auth_date` exceeds your window.

The Python implementation is in the fixture. It is short enough to read in full
before copying, which is the point of shipping it rather than describing it.

## Node and Go

```js
import crypto from 'node:crypto';

export function verify(initData, botToken, maxAgeSeconds = 300) {
  const params = new URLSearchParams(initData);
  const hash = params.get('hash');
  if (!hash) throw new Error('no hash');
  params.delete('hash');
  params.delete('signature');

  const check = [...params.entries()]
    .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))
    .map(([k, v]) => `${k}=${v}`)
    .join('\n');

  const secret = crypto.createHmac('sha256', 'WebAppData').update(botToken).digest();
  const expected = crypto.createHmac('sha256', secret).update(check).digest('hex');

  const a = Buffer.from(expected, 'hex');
  const b = Buffer.from(hash, 'hex');
  if (a.length !== b.length || !crypto.timingSafeEqual(a, b)) throw new Error('bad signature');

  const authDate = Number(params.get('auth_date'));
  if (!authDate || Date.now() / 1000 - authDate > maxAgeSeconds) throw new Error('stale');
  return Object.fromEntries(params);
}
```

`URLSearchParams` decodes on read, which is what step 1 wants. Do not call
`decodeURIComponent` again on the values — double-decoding a `%2B` turns a plus
sign in a name into a space and the hash stops matching for exactly those users.

For Go, the organisation's own
[`init-data-golang`](https://github.com/Telegram-Mini-Apps/init-data-golang) does
this correctly and is worth using rather than re-deriving.

## The Ed25519 third-party algorithm

For a service that must not hold the bot token:

1. Take out `hash` **and** `signature`.
2. Sort the rest, `key=value`, joined with `\n`.
3. Prepend `<bot_id>:WebAppData` and a `\n`.
4. Verify the base64url-decoded `signature` against Telegram's Ed25519 public key.

Production and test environments use **different public keys**, so a staging
build that verifies against production keys fails every login and looks like a
signing bug.

Use this only when the verifier genuinely cannot hold the token. If it can, the
HMAC path has one fewer key to distribute and one fewer environment to get wrong.

## Failure cases, and which of them still return "valid"

| Mistake | Symptom |
|---|---|
| Key and message swapped in the derivation | never matches; the usual "fix" is to delete the check |
| `signature` left in the check string | fails only for newer clients — a partial outage that looks random |
| `user` re-serialised (`json.dumps(json.loads(...))`) | fails for every user, immediately |
| Values decoded twice | fails only for users whose name or username contains `+` or `%` |
| `hash` compared with `==` | works, and leaks the digest a byte at a time |
| `auth_date` unchecked | **works forever** — the captured blob is a permanent bearer token |
| Identity read from `initDataUnsafe` on the server | **works, for everybody, as anybody** |

The last two are the dangerous rows: nothing errors, no test fails, and the app
is fully functional while being fully open.

## Turning a verified blob into a session

Verify once, at a single endpoint, then issue your own credential:

```
POST /auth/telegram  { initData }
  → verify(initData, BOT_TOKEN, max_age=300)
  → upsert the user by the verified telegram id
  → return a short-lived token of your own
```

Every other endpoint takes your token. This keeps `max_age` small — it only has
to cover the moment of login, not the length of a session — and it means the bot
token is used in one place, which is the place you can audit.
