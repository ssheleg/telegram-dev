# Frameworks, and what each one hides

**Load this when** choosing a library, or auditing one somebody else chose.

*Versions read from the registries on 2026-08-25.*

## The field

| Library | Language | Version | Notes |
|---|---|---|---|
| **aiogram** | Python | 3.30.0 | async, FSM, routers, middlewares. The default for new Python bots |
| **python-telegram-bot** | Python | 22.8 | async, older lineage, very large user base |
| **grammY** | TypeScript | 1.45.1 | small core plus plugins; first-class typing of the whole API |
| **Telegraf** | TypeScript | 4.16.3 | widely deployed, slower moving |

All four are wrappers over the same HTTP API. **None of them changes anything in
`SKILL.md`:** the update contract, the limits and the payment flow belong to
Telegram, and a framework that appears to solve one of them is usually deferring
it.

## What they do for you, and what they only appear to do

| Concern | Framework | Still yours |
|---|---|---|
| HTTP, retries, typed payloads | yes | — |
| Long polling loop and `offset` | yes | the crash window between work and confirmation |
| Webhook server and secret check | usually | verifying the header, and answering fast |
| **`update_id` deduplication** | **no** | all of it |
| 429 handling | partly — often a plugin | the pacing that avoids it |
| FSM / conversation state | yes | persistence across a restart |
| Payments | typed helpers | the ten-second window and the grant |

The row that matters is deduplication. No mainstream framework does it, because
it needs your database. A framework's built-in "retry" makes it worse: the
request is retried, the handler runs again.

## aiogram, briefly

Routers, `Dispatcher`, and middlewares that wrap every update — a middleware is
the natural place for the `update_id` claim, because it sits before every
handler:

```python
class ClaimUpdate(BaseMiddleware):
    async def __call__(self, handler, event, data):
        if not await data["db"].claim_update(event.update_id):
            return                      # already processed; drop silently
        return await handler(event, data)
```

FSM storage defaults to memory. **Memory storage loses every conversation on
deploy**, which reads as "the bot forgot me" to the user; move it to Redis or
your database before the first release, not after the first complaint.

## grammY, briefly

Plugins are explicit: `@grammyjs/auto-retry` handles `retry_after`,
`@grammyjs/runner` handles concurrency. Both are opt-in, so a default bot has
neither. The middleware signature makes the claim as natural as in aiogram:

```ts
bot.use(async (ctx, next) => {
  if (!(await db.claimUpdate(ctx.update.update_id))) return;
  await next();
});
```

## Choosing

Pick the one your team already reads. The differences between them are smaller
than the difference between a bot that dedups and one that does not — and the
audit questions in this pack are the same whichever is underneath.
