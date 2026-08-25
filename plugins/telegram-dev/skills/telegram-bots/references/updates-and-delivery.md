# Updates: polling, webhooks, and the delivery contract

**Load this when** wiring `getUpdates` or `setWebhook`, migrating between them,
or explaining why an update arrived twice or not at all.

*Read from `core.telegram.org/bots/api` on 2026-08-25, Bot API 10.3.*

## Contents

- [The contract, in five sentences](#the-contract-in-five-sentences)
- [Long polling](#long-polling)
- [Webhook](#webhook)
- [`allowed_updates`](#allowed_updates)
- [Migrating between them](#migrating-between-them)
- [Ordering, and what it is not](#ordering-and-what-it-is-not)

## The contract, in five sentences

1. `update_id` is sequential and increasing, and it is the same across
   redeliveries of one event.
2. An update is stored **at most 24 hours**, until the bot takes it.
3. `getUpdates` **will not work while a webhook is set**.
4. A webhook delivery that does not get a 2xx quickly is retried — with the same
   `update_id`.
5. `allowed_updates` decides what you are subscribed to, and its default is not
   "everything".

Everything below follows from those.

## Long polling

```python
offset = None
while True:
    updates = await bot.get_updates(offset=offset, timeout=30,
                                    allowed_updates=WANTED)
    for u in updates:
        await handle(u)                 # claim on update_id INSIDE handle
        offset = u.update_id + 1        # confirm only what is done
```

- **`offset` must be the highest id seen plus one.** Sending it is what
  acknowledges the batch; until you do, the same updates come back.
- **Confirm after the work, not before.** Advancing `offset` first turns a crash
  into silent data loss; advancing after turns it into a redelivery, which the
  claim absorbs. Redelivery is the failure you want.
- `timeout` is long polling proper — the request hangs until an update or the
  timeout. A `timeout=0` loop is a busy poll and will earn 429.
- **One consumer per token.** Two pollers steal batches from each other, each
  seeing half the traffic, and nothing errors.

## Webhook

```python
await bot.set_webhook(
    url=f"https://{host}/tg/{random_path}",
    secret_token=SECRET,                    # 1-256 chars
    allowed_updates=WANTED,
    max_connections=40,                     # 1-100
    drop_pending_updates=False,
)
```

- The endpoint must be **HTTPS** with a valid certificate.
- **Verify `X-Telegram-Bot-Api-Secret-Token`** against `SECRET` in constant time
  and answer 401 on mismatch. A random path is obscurity; the header is the
  check.
- **`max_connections` is concurrency**, defaulting to 40. Whatever number you
  choose, two deliveries of one update can overlap — the claim is not optional.
- Answer 2xx **fast**. Long work belongs in a queue; a slow handler produces
  retries, and retries produce duplicates.
- `getWebhookInfo` reports `pending_update_count` and `last_error_message`. It is
  the first thing to read when a bot "stopped receiving messages", and it usually
  answers the question outright.

## `allowed_updates`

Passing nothing, or an empty list, subscribes to **all types except
`chat_member`, `message_reaction` and `message_reaction_count`**. Those three are
the ones a moderation or analytics bot most wants, and their absence is silent.

- The list is fixed **at subscription time**. Adding a handler does not add a
  subscription; re-run `setWebhook`/`getUpdates` with the new list.
- Name every type explicitly, including the ones in the default. A written list
  is a diff when it changes; an omitted parameter is not.
- `my_chat_member` (the bot's own status) is in the default. `chat_member`
  (everyone else's) is not — a pair that is very easy to conflate.

## Migrating between them

```
poll → webhook:   setWebhook(...)                      # polling stops working immediately
webhook → poll:   deleteWebhook(drop_pending_updates=False) → getUpdates(...)
```

`drop_pending_updates=True` on either call **discards the queue**, payments and
all. Use it when you deliberately want a clean start, never as hygiene.

A local `getUpdates` against a production token that has a webhook set just fails;
a local `setWebhook` against it silently redirects production traffic to a laptop.
**Separate tokens for separate environments** is the only safe arrangement — bots
are free.

## Ordering, and what it is not

`update_id` increases, so it orders **delivery**. It does not order **events** in
any way you can act on: two chats are independent, an edit can arrive after a
later message, and a webhook with `max_connections` above 1 processes out of
order by design.

Derive state from the update's own contents and your stored row, never from the
order two updates happened to arrive in. Where order genuinely matters — a
payment against the invoice that produced it — the ids in the payload are what
connect them.
