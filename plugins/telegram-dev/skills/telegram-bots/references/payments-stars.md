# Telegram Stars, and the ten-second window

**Load this when** a bot sells anything.

*Read from `core.telegram.org/bots/payments-stars` on 2026-08-25, Bot API 10.3.*

## Digital goods are Stars, and only Stars

All sales of **digital goods and services** through bots are carried out in
Telegram Stars: currency `XTR`, and `provider_token` left **empty**. Physical
goods go through a payment provider and are a different flow with different
rules — if the thing is shipped, this file is the wrong one.

## The flow

```
createInvoiceLink / sendInvoice
        │
        ▼
pre_checkout_query ──► answerPreCheckoutQuery(ok=True|False)   ≤ 10 seconds
        │
        ▼
successful_payment ──► grant the thing, keyed on the charge id
```

| Step | Handler | Rule |
|---|---|---|
| `pre_checkout_query` | fast, local | validate against **your own** state only. No provider calls, no slow lookups |
| `successful_payment` | idempotent | this is the money. Grant here, exactly once |
| `refundStarPayment` | your admin path | claw back what you granted |

- **Ten seconds is the whole budget** for the pre-checkout answer, and missing it
  cancels the transaction. Anything that could block belongs after the payment.
- **Answer `ok=False` with a message the user can act on**: an out-of-stock item,
  a closed account. A silent `False` looks like a Telegram fault.
- `successful_payment` carries `telegram_payment_charge_id` and
  `provider_payment_charge_id`, `invoice_payload`, `total_amount` and `currency`.
  **`invoice_payload` is yours** — put the order id in it, because it is the only
  field that comes back unchanged and it is how the payment finds the row.

## Idempotency, and why this is the same problem as a card

`successful_payment` can arrive twice: a webhook retry, a poller redelivery, a
restart between the grant and the offset confirmation. Claim on `update_id` at
the transport layer **and** guard the grant on the charge id at the business
layer. The transport claim protects the handler; the charge-id guard protects the
grant when the handler is reached from anywhere else — a reconciliation job, an
admin replay, a support tool.

## Refunds

`refundStarPayment(user_id, telegram_payment_charge_id)` returns the Stars. Your
side must reverse whatever was granted, and clamp at zero rather than going
negative when the user already spent it. A refund that only moves Stars and
leaves the entitlement in place is a paid product given away.

`getStarTransactions` lists the account's Star movements and is the reconciliation
source: run it on a schedule and compare against your own rows, because a payment
whose update never arrived looks exactly like a payment that never happened.

## Subscriptions

An invoice may carry a **`subscription_period`**, which makes it recurring.
Recurring means `successful_payment` arrives again on each renewal, with the same
`invoice_payload` and a new charge id. Grant per **charge id**, never per payload
— keying on the payload grants the first renewal and silently drops the rest.

## What not to trust

- **Not the `openInvoice` callback in a Mini App.** It runs on the user's device
  and reports what they saw.
- **Not the message the user sends afterwards.** "I paid" is input.
- **Only `successful_payment`, reaching your server, over the transport you
  verified.**
