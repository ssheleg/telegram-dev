# Limits, and files

**Load this when** sending at volume, broadcasting, or moving anything larger
than a photo.

*Rate limits from `core.telegram.org/bots/faq`, file limits from the Bot API
reference, read 2026-08-25.*

## The published rates

| Scope | Limit |
|---|---|
| One chat | ~1 message per second; short bursts tolerated, then 429 |
| One group | 20 messages per minute |
| Bulk, across users | ~30 messages per second |
| With paid broadcasts | up to 1000 per second, 0.1 Stars per message past the free 30/s |

Telegram's own advice for bulk notifications is to spread them over **8–12
hours** rather than to send as fast as the limit allows.

## 429 is data, not an error

```python
except TelegramRetryAfter as e:       # aiogram; grammY: e.parameters.retry_after
    await asyncio.sleep(e.retry_after)
    # retry the SAME call — the message was not sent
```

`parameters.retry_after` is in seconds and is exact. A fixed backoff is either
slower than necessary or trips the next limit; exponential backoff on top of a
number the server gave you is guessing over a fact.

## A broadcast is a job

A `for` loop over 100 000 users is wrong in four ways: it exceeds 30/s, it cannot
resume, it retries the whole list after a crash, and it blocks whatever process
it runs in for hours.

The shape that works:

- a **queue** with the recipient list materialised up front,
- a **rate limiter** at 25–30/s, leaving headroom,
- a **per-recipient status** written before the next send, so a restart resumes
  instead of starting over,
- **removal on `403 Forbidden: bot was blocked by the user`** — that user is gone
  and every future send to them is wasted quota,
- a **stop switch** an operator can hit without a deploy.

## Files

| Operation | Ceiling |
|---|---|
| `getFile` download | **20 MB** |
| Upload through the cloud API | **50 MB** |
| Upload via a **local Bot API server** | 2 GB |

- **`file_id` is per-bot and not a URL.** It is valid for the bot that received
  it, it is stable enough to resend cheaply, and it is not an archival reference —
  store the bytes if you need them later.
- **`file_path` from `getFile` expires** (about an hour) and the download URL
  contains the bot token. Never log it, never hand it to a client.
- **The 20 MB download ceiling is the usual reason people reach for a userbot.**
  A local Bot API server removes it without an account and without ban risk, and
  is almost always the cheaper answer — `telegram-userbots` states the trade
  explicitly.

## Message sizes

Text is capped at 4096 characters and a caption at 1024. A bot that formats a
report has to paginate, and the failure mode of not doing so is a `400` in
production on the one message that mattered. Split on a boundary you control,
not on the cap.
