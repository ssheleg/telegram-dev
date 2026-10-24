# A bot under load: one slow update must not hold everyone

The failure this page is about is quiet. Telegram answers slowly for a few
minutes (502s, sends that hang), one handler waits on it, and the whole bot stops
answering every user, because the dispatcher was waiting for that one handler
before it asked Telegram for anything else. Nothing crashes and nothing is
logged as an error until the sends start timing out.

*Read against the Telegraf 4.16.3 source on 2026-10-23
(`lib/core/network/polling.js`, `lib/telegraf.js`, `lib/core/network/client.js`).
The rules are library-independent; the Telegraf lines are the measured example.
Every rule below has a mutant in [`fixtures/update_pump.py`](../fixtures/update_pump.py).*

- [Check whether your poll waits for handlers](#check-whether-your-poll-waits-for-handlers)
- [A queue per chat, a ceiling across chats](#a-queue-per-chat-a-ceiling-across-chats)
- [Payments run outside the ceiling](#payments-run-outside-the-ceiling)
- [Guards keyed on "now" move when work is queued](#guards-keyed-on-now-move-when-work-is-queued)
- [Decide at the step that knows](#decide-at-the-step-that-knows)
- [Timeouts that free the caller, not the work](#timeouts-that-free-the-caller-not-the-work)
- [Stopping a process that holds acknowledged updates](#stopping-a-process-that-holds-acknowledged-updates)
- [Measure it, and alarm without flapping](#measure-it-and-alarm-without-flapping)
- [Before you ship](#before-you-ship)

## Check whether your poll waits for handlers

Read your library's polling loop, not its README. Telegraf 4.16.3:

```js
for await (const updates of this)
    await Promise.all(updates.map(handleUpdate));   // next getUpdates waits for ALL of them
```

The next `getUpdates` is sent only after every handler of the batch has settled,
and `handleUpdate` races the middleware against `handlerTimeout` (90 000 ms by
default). So a single handler that waits on a stalled Telegram holds every other
chat for up to 90 seconds, and a busy batch holds it for the slowest handler in
it. Concurrent within a batch, serial between batches: under load that is the
worst of both.

The fix does not need a new poller. Replace `bot.handleUpdate` on the instance
with a dispatcher that puts the update on a queue and returns at once; the
library's own loop then asks for the next batch immediately and still owns the
offset, the 409 handling and the webhook path. Call the original `handleUpdate`
from the queue.

## A queue per chat, a ceiling across chats

| Rule | Why |
|---|---|
| updates of one chat run **one at a time, in arrival order** | two taps of one chat racing on the same state is the bug the old serial loop hid |
| chats run **in parallel up to a ceiling** (tens, not thousands) | an unbounded burst exhausts the database pool and the sockets every other part of the process shares |
| one chat may queue a **bounded** number of updates; the rest are dropped and counted | a chat that floods must cost itself, not memory and not other chats |
| a repeated `update_id` is handled once (an in-memory window is enough for the poll; the durable inbox is still the guarantee across a crash) | the dispatcher must not undo the dedup the inbox gives you |
| the queue key is the chat for messages and callbacks, the sender for chatless updates, and its own lane for anything with neither | otherwise unrelated chatless updates serialise behind each other |

A key detail: count a dropped update and **answer it if it is a callback**, or its
button keeps spinning until the client gives up.

## Payments run outside the ceiling

`pre_checkout_query` must be answered within ten seconds. A dispatcher with a
global ceiling puts it in line behind whatever holds the slots, and the slots are
held precisely when Telegram is slow. Give payment updates (`pre_checkout_query`,
`successful_payment`) their own lane that starts at once and still counts in the
drain on shutdown. Payments are few, so the ceiling is exceeded by at most the
payments in flight.

## Guards keyed on "now" move when work is queued

Moving from concurrent to queued changes what every time-based guard measures.
A flood window of one second, checked when the handler STARTS, lets a second tap
through as soon as it waited behind a first handler that took longer than the
window: a double action the concurrent loop used to drop. Measure such windows
from the update's **arrival**, stamped by the dispatcher, and compare in both
directions: updates of one user queued in two chats can be judged out of
arrival order. The stamp itself must never move backwards.

## Decide at the step that knows

A tempting optimisation: when a newer tap queues behind a screen still being
drawn, mark the older screen superseded so it is never sent. It empties the chat.
Whether the queued update will draw anything is unknown when it queues: the flood
gate may drop it (a double tap), its handler may draw nothing (a page-indicator
button), the entry gate may refuse it. Let the older screen finish and the newer
one replace it, as it did before the queue. The general rule: **a decision that
needs the outcome of a later step is made at that step, or not at all.**

What IS safe at queue time: answering the waiting callback (`answerCallbackQuery`
with no text), because it draws nothing and deletes nothing. Answer it whether it
waits behind its chat or for a free slot, and skip the handler's own up-front
answer for that update only once the early answer succeeded, so a failed early
answer still gets its second chance.

## Timeouts that free the caller, not the work

- Telegraf sets the HTTP timeout of every Bot API call to 500 000 ms in the client
  itself (`config.timeout = 500000`), after the options are merged, so no option
  moves it. The long poll shares that client, so you cannot shorten it globally
  without breaking `getUpdates`. Bound **your wait** per send instead (a
  `Promise.race` with your own timer and an error code of your own, not
  `ETIMEDOUT`), knowing the request may still complete in the background.
- `handlerTimeout` releases the dispatcher, not the handler: the middleware keeps
  running after the timeout, so the chat's next update can start beside it. A
  per-handler send budget (a cap on total time spent sending inside one update) is
  what actually bounds a handler; a framework timeout only hides it.
- A retry loop on 429 sleeps `retry_after` and retries the same call; a retry loop
  on a timeout should be bounded in attempts AND in total time, or one stalled chat
  owns a slot for minutes.

## Stopping a process that holds acknowledged updates

Once the poll has advanced the offset, Telegram will not send those updates
again. On SIGTERM:

1. Stop the poll **first**, before anything else closes.
2. Drain the queue for a bounded time (seconds, not the whole shutdown budget:
   the inbound webhooks and other drains run after it inside the same budget).
3. Refuse to START the poll once stopping has begun. A launch that is still
   awaiting `deleteWebhook` when the signal arrives has no poll to stop yet
   (Telegraf's `stop()` throws "Bot is not running!"), and will start one in the
   middle of the drain unless `startPolling` itself checks the flag.
4. Stop anything a late handler could arm (timers, listening sessions) after the
   drain, and make it refuse to re-arm.

Updates still queued after the drain are lost until you have a durable inbox
([`updates-and-delivery.md`](updates-and-delivery.md)). Say so in your docs rather
than implying the drain is lossless.

## Measure it, and alarm without flapping

What to record per process, over a rolling five-minute window:

| Signal | How | Note |
|---|---|---|
| handling time p50/p95/max | dispatcher, start to settle | |
| lag from Telegram p95 | start minus the update's `date` (use `edit_date` for edits) | callback queries carry no `date`, so a tap-driven bot has few samples |
| wait in queue p95 | start minus arrival | the number the user feels |
| queue depth, active, dropped in window | dispatcher counters | report drops in the window, not since boot |
| event-loop delay p99 and max | `perf_hooks.monitorEventLoopDelay` | subtract the timer resolution, discard the first window after start; one long freeze barely moves p99, so alarm on max separately |

Alarm rules that do not flap:

- Read only fresh readings; a process that stopped reporting is its own alarm.
- **Fire** only with enough samples on one process (tens), so one slow update at
  night is not an outage.
- **Clear** only when every fresh reading is under the threshold; a reading over
  it on too few samples gives no verdict, so the standing alert is kept and can
  escalate.
- For one-minute signals (the event loop), clear after several clean readings in
  a row, or a stall that recurs every few minutes fires and clears forever and
  never escalates.

## Before you ship

1. **The poll does not wait for handlers** (§ *Check whether your poll waits*).
2. **Per-chat order, a ceiling across chats, a per-chat cap** (§ *A queue per chat*).
3. **Payments start at once**, outside the ceiling (§ *Payments*).
4. **Time-based guards measure from arrival** (§ *Guards keyed on "now"*).
5. **Nothing is superseded at queue time**; waiting callbacks are answered (§ *Decide at the step that knows*).
6. **Sends are bounded by your own timer**, handlers by a send budget (§ *Timeouts*).
7. **Shutdown stops the poll first and refuses to restart it** (§ *Stopping*).
8. **Lag, wait, drops and event-loop delay are measured and alarmed** (§ *Measure it*).

`python3 fixtures/update_pump.py --self-test` removes each of these rules in turn
and watches the matching invariant fail.
