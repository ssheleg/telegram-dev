---
name: telegram-bots
description: >-
  Use when building or auditing a Telegram bot on the official HTTP Bot API:
  receiving updates by polling or webhook, deduplicating them, keyboards and
  inline mode, Telegram Stars payments, files, rate limits, and the seam where
  an update becomes a row in your own database. Covers the pinned API version,
  update_id as the only idempotency key, the allowed_updates default that drops
  three update types in silence, the webhook secret header, the ten-second
  pre-checkout window, XTR and refunds, the 20MB download ceiling, and what a
  bot cannot do at all. Triggers - "telegram bot", "bot api", "aiogram",
  "grammy", "telegraf", "python-telegram-bot", "setWebhook", "getUpdates",
  "telegram stars", "pre_checkout_query", "телеграм бот", "бот апи", "вебхук
  телеграм", "звёзды телеграм". Not for user accounts or reading history a bot
  cannot see (telegram-userbots), and not for the web layer
  (telegram-miniapps).
license: MIT
compatibility: Fixtures run with python3 (standard library only)
---

# Telegram bots — the official Bot API

Telegram holds the chat. Your database holds everything you will act on later.
**Every serious bot defect is an update that was processed twice, or one that was
never delivered because nobody asked for it.**

The Bot API is not where bots fail. They fail at the seam: the update redelivered
after a crash, the member event that never arrives because of a default nobody
read, the payment confirmed from the wrong signal, the broadcast that trips 429
at user 31 and silently stops.

*Read against the Bot API on 2026-08-25, at version **10.3** (released
2026-08-24). Re-check `core.telegram.org/bots/api-changelog` before quoting a
version: this API ships roughly monthly.*

Deep material, loaded on demand:

| Read | When |
|---|---|
| [`references/updates-and-delivery.md`](references/updates-and-delivery.md) | wiring polling or a webhook — the delivery contract, ordering, dedup, and the migration between them |
| [`references/payments-stars.md`](references/payments-stars.md) | taking money — Stars, invoices, the pre-checkout window, refunds, subscriptions |
| [`references/limits-and-files.md`](references/limits-and-files.md) | sending at volume, or moving files — every published limit and what to do at each |
| [`references/frameworks.md`](references/frameworks.md) | choosing or auditing a library — aiogram, grammY, Telegraf, python-telegram-bot, and what each hides |

**Runnable, and shipped beside this file:**
[`fixtures/update_delivery.py`](fixtures/update_delivery.py) — four invariants a
correct handler holds, each with the mutant that makes it fail. `python3
fixtures/update_delivery.py --self-test` watches a redelivered update processed
twice, an update lost to a crash, a reply dropped on 429, and one payment granted
twice. Standard library only.

---

## Which API you are on, decided once

| You need | Use | Why |
|---|---|---|
| A bot users add, in chats it is in | **Bot API** — this skill | HTTP, a token, no phone number, no ban risk |
| To read history a bot cannot see, or act as a person | **MTProto** — `telegram-userbots` | a user account, with everything that costs |
| A web interface inside Telegram | **Mini App** — `telegram-miniapps` | a page plus `initData` you must verify |

**A bot cannot** read messages in a group without privacy mode off or a mention,
see a chat it was never added to, read history from before it joined, act on
behalf of a user, or download a file over 20 MB. Wanting any of those is the
signal to read `telegram-userbots` — and to read its refusal first, because a
user account is a liability a bot token is not.

## The update is the event, and it arrives at least once

```python
# aiogram 3.x — the shape, not the framework
async def handle(update: Update, db) -> None:
    if not await db.claim_update(update.update_id):   # INSERT on a primary key
        return                                        # already processed
    await do_the_work(update)
```

- **`update_id` is the only idempotency key you get.** It is sequential and it is
  stable across redeliveries. Nothing else in an update identifies it: two
  identical messages a second apart are two events, and the same event delivered
  twice is one.
- **Claim before working**, with an `INSERT` on a primary key, not a `SELECT`
  then an `INSERT`. Under a webhook Telegram may open up to `max_connections`
  (default 40) simultaneous connections, so two deliveries of one update can be
  in flight at once.
- **Updates are kept for 24 hours** and no longer. A bot that is down for a day
  has lost them, and nothing will say so — reconcile from your own state, never
  from the assumption that the queue drained.
- Measured across eight live Telegram bots on this machine on 2026-08-25:
  **zero of eight deduplicate on `update_id`.** Long polling hides it until the
  first crash between "work done" and "offset confirmed".

## `allowed_updates` drops three types by default

```python
await bot.set_webhook(
    url=f"{origin}/tg/{SECRET_PATH}",
    secret_token=WEBHOOK_SECRET,                 # 1-256 chars
    allowed_updates=["message", "callback_query", "chat_member",
                     "pre_checkout_query", "my_chat_member"],
    drop_pending_updates=False,
)
```

The default — an empty list, and the value you get by not passing the parameter —
means *"all update types **except** `chat_member`, `message_reaction` and
`message_reaction_count`"*. So a bot that tracks joins and leaves receives
nothing, the request returns `ok: true`, and the logs are clean. **Name every
type you handle, explicitly**, and re-run `setWebhook` when you add one:
`allowed_updates` is set at subscription time, not at handler time.

## Webhook or polling — and never both

`getUpdates` **will not work while a webhook is set**. That is the whole
migration hazard: a local `getUpdates` run against a production token silently
takes over, or fails, depending on which side moved last. One token, one
consumer.

- **The webhook is the callback, so it needs the same defences as a payment
  webhook**: verify `X-Telegram-Bot-Api-Secret-Token` against the value you set
  with `secret_token`, in constant time, and answer 401 with no detail when it
  fails. The URL is not a secret; the header is.
- **Answer fast, work later.** Telegram retries on non-2xx and on a slow reply,
  and a retry is a second delivery of the same `update_id`. Acknowledge, then
  process — the claim above is what makes that safe.
- **`drop_pending_updates=True` is a decision, not a cleanup.** It discards
  everything queued, including payments already made.
- Long polling is correct for development and for low-volume bots; a webhook is
  correct when you have a public HTTPS endpoint and care about latency. Both are
  in [`references/updates-and-delivery.md`](references/updates-and-delivery.md).

## Limits are a design constraint, not an error path

| Limit | Value | What it means for the design |
|---|---|---|
| One chat | ~**1 message/second** | bursts are tolerated, then refused |
| One group | **20 messages/minute** | a chatty group bot needs a queue |
| Bulk, all users | ~**30 messages/second** | a broadcast to 100k users is **hours**, not a loop |
| Paid broadcasts | up to **1000/second** | 0.1 Stars per message past the free 30/s |

On 429 the response carries `parameters.retry_after` in seconds. **Sleep exactly
that long and retry the same call** — a fixed backoff either wastes the window or
trips the next one. A broadcast is a job with a rate limiter and a resume point,
not a `for` loop; if it cannot resume, a crash at user 60 000 restarts at zero
and every earlier user is messaged twice.

## Money: the successful payment is the payment

Digital goods and services are sold **exclusively in Telegram Stars**, currency
code `XTR`, and `provider_token` is left empty for them.

```
sendInvoice / createInvoiceLink  →  pre_checkout_query  →  successful_payment
                                    answer within 10s        deliver here
```

- **`answerPreCheckoutQuery` has a ten-second window.** Miss it and the
  transaction is cancelled — so that handler validates against your own state and
  nothing slow. Anything that can take a second belongs after
  `successful_payment`.
- **Deliver on `successful_payment`, never on the pre-checkout.** Pre-checkout is
  a question; the payment has not happened yet.
- **`refundStarPayment` exists and a refund is not a deletion.** Claw back what
  you granted, keyed on the charge id, exactly the way a card refund is handled —
  the arithmetic and the ordering are the same problem `stripe-billing` covers.

Full flow, subscriptions and the transaction ledger:
[`references/payments-stars.md`](references/payments-stars.md).

## Files have a ceiling, and it is lower than you think

- **Download via `getFile`: 20 MB.** Above that the Bot API refuses, and no
  framework works around it.
- **Upload: 50 MB** through the cloud Bot API.
- A **local Bot API server** removes both ceilings and changes the file paths
  your code receives. That is an infrastructure decision, not a flag —
  [`references/limits-and-files.md`](references/limits-and-files.md).
- **`file_id` is not a URL and not stable across bots.** It is valid for your bot
  only; store it to resend cheaply, never as an archival reference.

## What belongs in your database

| Fact | Where it lives | Why |
|---|---|---|
| `update_id` seen | yours, unique | the only idempotency key |
| `chat_id`, `user_id` | yours | Telegram will not list your users for you |
| the message you sent | yours, with `message_id` | editing later needs both ids |
| entitlement bought with Stars | yours, keyed on the charge id | a refund must find it |
| `file_id` | yours, as a cache | cheap resend, not an archive |

Telegram is not a database and offers no way to enumerate the people who have
started your bot. If you did not write it down when it happened, it is gone.

## Before you ship

1. **Every handler is idempotent on `update_id`** (§ *The update is the event*).
2. **The webhook verifies the secret header** and answers 401 without detail
   (§ *Webhook or polling*).
3. **`allowed_updates` names every type you handle** — the default is not "all"
   (§ *`allowed_updates` drops three types*).
4. **429 sleeps for `retry_after`**, and a broadcast can resume (§ *Limits*).
5. **Goods are delivered on `successful_payment`**, not on pre-checkout
   (§ *Money*).
