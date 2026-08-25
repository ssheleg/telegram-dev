---
name: telegram-miniapps
description: >-
  Use when building or auditing a Telegram Mini App — a web page opened inside
  Telegram — where the whole security model is one signed blob. Covers verifying
  initData on the server with HMAC-SHA256 and the "WebAppData" key derivation,
  why initDataUnsafe is named that, the auth_date freshness window, the Ed25519
  signature path for a third party with no bot token, session exchange, sending
  results back to the bot with sendData and answerWebAppQuery, Stars payments
  inside the app, the viewport and safe-area fields a real device needs, and the
  SDK package whose name moved. Triggers - "mini app", "miniapp", "telegram web
  app", "initData", "initDataUnsafe", "WebAppData", "tma.js",
  "@telegram-apps/sdk", "мини-апп", "телеграм веб-апп", "валидация initData".
  Not for the bot behind it (telegram-bots) or user accounts
  (telegram-userbots).
license: MIT
---

# Telegram Mini Apps — one signed blob is the whole model

A Mini App is a web page in a WebView with a query string attached. **That query
string is the only proof of who the user is, and it is signed with your bot
token.** Verify it on your server and you have authentication as strong as the
bot itself; trust the parsed object the SDK hands you and you have none.

*Read against `core.telegram.org/bots/webapps` on 2026-08-25, Bot API **10.3**.*

Deep material, loaded on demand:

| Read | When |
|---|---|
| [`references/initdata-verification.md`](references/initdata-verification.md) | implementing or reviewing verification — both algorithms, in three languages, with the failure cases |
| [`references/app-to-bot.md`](references/app-to-bot.md) | returning a result to the bot, inline queries, and paying inside the app |
| [`references/viewport-and-platform.md`](references/viewport-and-platform.md) | the app looks wrong on a real phone — viewport, safe areas, fullscreen, themes |

**Runnable, and shipped beside this file:**
[`fixtures/verify_initdata.py`](fixtures/verify_initdata.py) — the verifier to copy,
plus nine checks that watch it refuse a tampered user id, a stale `auth_date`, a
re-serialised `user` field and a reversed key derivation. `python3
fixtures/verify_initdata.py` needs nothing but the standard library.

---

## `initDataUnsafe` is named that on purpose

```js
// The client hands you both. One is evidence, the other is a convenience.
const raw    = window.Telegram.WebApp.initData;        // the signed string — SEND THIS
const unsafe = window.Telegram.WebApp.initDataUnsafe;  // already parsed — display only
```

`initDataUnsafe.user.id` is a number a user can set to anything, because it comes
from a page running on their device. **Anything it decides — who you are, what
you own, what you may see — must be decided again on the server from the raw
string.** Send `initData` to your backend, verify it there, and derive the
identity from what you verified.

The single defect this skill exists to prevent: an endpoint that takes
`{ userId }` from the client. It works, it demos, and it lets anyone read anyone.

## Verifying it, exactly

```python
import hashlib, hmac, time
from urllib.parse import parse_qsl

MAX_AGE = 300  # seconds; a decision, not a constant handed down

def verify(init_data: str, bot_token: str) -> dict:
    pairs = dict(parse_qsl(init_data, strict_parsing=True))   # already url-decoded
    received = pairs.pop("hash", None)
    if not received:
        raise ValueError("no hash")
    pairs.pop("signature", None)                              # third-party field, not in the HMAC

    check = "\n".join(f"{k}={pairs[k]}" for k in sorted(pairs))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, received):
        raise ValueError("bad signature")
    if time.time() - int(pairs["auth_date"]) > MAX_AGE:
        raise ValueError("stale")
    return pairs
```

Five ways this goes wrong, each of which still returns "valid" for somebody:

- **The key derivation is backwards in half the snippets on the internet.** The
  secret is `HMAC_SHA256(key="WebAppData", msg=bot_token)` — the constant is the
  *key* and the token is the *message*. Swapped, it produces a stable hash that
  never matches, and the usual fix is to stop checking.
- **Sort by key, join with `\n`, and use the values as received** — url-decoded
  once, not re-encoded, not re-serialised. `user` is a JSON string and must stay
  the exact string that arrived; parsing and re-dumping it changes key order and
  breaks the hash.
- **Remove `hash` before building the string, and `signature` too.** Leaving
  `signature` in is the failure that appears only for clients new enough to send
  it.
- **`auth_date` is not optional.** Without a freshness window a captured
  `initData` is a permanent bearer token. Pick a window, state it, and treat
  anything older as unauthenticated — not as an error to log and continue past.
- **Compare in constant time.** `==` on a hex digest is a timing oracle; the
  language's `compare_digest` equivalent costs nothing.

## Do not verify on every request

`initData` is a login, not a session. Verify it once, mint your own short-lived
token, and let the rest of the API use that.

```
POST /auth/telegram   { initData }   →  verify → your session JWT (short TTL)
GET  /api/...         Authorization: Bearer <your token>
```

Re-verifying on each call forces `MAX_AGE` wide enough to cover a long session,
which is the same as not checking `auth_date` at all.

## The third-party path, when you have no bot token

An external service cannot hold the bot token, so Telegram signs `initData` a
second way: an **Ed25519 `signature`**, verifiable with Telegram's public key.
The signed string differs — it is prefixed with `<bot_id>:WebAppData` and a line
feed, then the same sorted `key=value` pairs with **both** `hash` and `signature`
removed. Public keys differ between test and production.

Use it when the verifier is not the bot's owner. Do not use it as a substitute
for the HMAC when you *do* hold the token — the HMAC path is simpler and has
fewer moving keys. Both, with code:
[`references/initdata-verification.md`](references/initdata-verification.md).

## The SDK's package name moved, and the org page still says the old one

- **Live package: `@telegram-apps/sdk`** (3.11.8 on 2026-08-25), with
  `@telegram-apps/sdk-react` beside it.
- The `Telegram-Mini-Apps` GitHub organisation still fronts **`tma.js`** and
  `@tma.js/sdk`, last at 3.3.0 — the earlier name, eight minors behind.
- The templates in that organisation (`reactjs-template`, `nextjs-template`,
  `vuejs-template`, `solidjs-template`) are worth reading; four others there are
  **archived and marked unsupported**, and an agent copying the first result gets
  one of those about half the time.

Neither library is required. The Mini App interface is
`window.Telegram.WebApp`, delivered by `telegram-web-app.js`; an SDK buys typed
access and platform shims, not capability.

## The device is not your laptop

A Mini App renders inside a WebView with a keyboard, a header and a home
indicator in the way. Read the viewport fields rather than assuming:
`viewportHeight`, `viewportStableHeight`, `safeAreaInset`,
`contentSafeAreaInset`, `isFullscreen`, `isActive`. `100vh` is wrong on both
platforms and wrong differently.

Themes come from `themeParams` and `colorScheme` and change under the user, not
under you — bind to them rather than hardcoding a palette.
[`references/viewport-and-platform.md`](references/viewport-and-platform.md).

## Getting the answer back to the bot

- **`sendData(data)`** — for an app opened from a **keyboard button**. It closes
  the app and delivers `web_app_data` to the bot. The bot must still treat it as
  input from the user, because it is.
- **`answerWebAppQuery`** — for an app opened from an **inline button**, using
  the `query_id` inside the verified `initData`. It has a short lifetime; a
  server that goes and does slow work first will find it expired.
- Payments run through the bot, in Stars, on the same
  `pre_checkout_query` → `successful_payment` path `telegram-bots` describes.
  **The Mini App is where the user clicks; it is not where the money is
  confirmed.**

## Before you ship

1. **The server derives identity from verified `initData`**, never from a
   client-supplied id (§ *`initDataUnsafe` is named that on purpose*).
2. **`auth_date` is checked against a stated window**, and `initData` is
   exchanged for your own session (§ *Verifying it, exactly*, § *Do not verify on
   every request*).
3. **The hash comparison is constant-time**, and `hash` and `signature` are both
   removed before the check string is built.
4. **The SDK is `@telegram-apps/*`**, and any template copied from the org is not
   one of the archived ones (§ *The SDK's package name moved*).
5. **Layout reads the safe-area and viewport fields** rather than `100vh`
   (§ *The device is not your laptop*).
