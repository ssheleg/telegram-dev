# From the Mini App back to the bot

**Load this when** the app has to return a result, open an inline result, or take
money.

*Read against Bot API 10.3 on 2026-08-25.*

## Two ways back, and the button decides which

| Opened from | Return with | Shape |
|---|---|---|
| A **keyboard** button (`web_app` in `ReplyKeyboardMarkup`) | `WebApp.sendData(data)` | closes the app, delivers `message.web_app_data` to the bot |
| An **inline** button (`web_app` in `InlineKeyboardMarkup`) or an inline query | `answerWebAppQuery(query_id, result)` | the bot posts the result on the user's behalf |
| A direct link / menu button | neither — talk to your own backend | the app has no query to answer |

Choosing the wrong one is not a style question: `sendData` is unavailable from an
inline context, and `query_id` is absent from `initData` when the app was opened
from a keyboard button.

## `sendData` is user input

The string arrives as `message.web_app_data.data`, attributed to the user, in a
service message. **It is not signed and not privileged.** A user can craft the
same message. Validate it exactly as you would validate a typed command, and
never carry an amount, a price or an entitlement in it — carry an id your server
can look up.

`sendData` is limited to a few kilobytes and closes the app immediately; anything
larger or anything you need a response to belongs on your own HTTP API, with the
session minted from verified `initData`.

## `answerWebAppQuery` expires

`query_id` from the verified `initData` is short-lived. A handler that verifies,
then calls a payment provider, then answers, will find the query gone. Answer
first with something honest, or do the slow work before you open the app.

## Money inside a Mini App

The app is where the button is; the bot is where the money is confirmed.

1. The app asks your server for an invoice link.
2. Your server calls **`createInvoiceLink`** (currency `XTR`, empty
   `provider_token` for digital goods) and returns the link.
3. The app opens it with `WebApp.openInvoice(link, callback)`.
4. The **bot** receives `pre_checkout_query` — answer within **10 seconds** — and
   then `successful_payment`.
5. **Grant on `successful_payment`, in the bot's handler**, keyed on the charge
   id.

The callback in step 3 tells the app what the user saw. It is not proof of
payment: it runs on the user's device. Treating `status === 'paid'` from that
callback as the grant signal is the Mini App version of granting on a redirect,
and `telegram-bots` covers the general form.

## Deep links carry state

`start_param` in `initData` is the `startapp` parameter from the link that opened
the app. It is attacker-controlled like any query string — use it to route, not
to authorise.
