## v0.1.0 — three surfaces, and the line between them

Telegram is three different products behind one brand, and the most expensive
mistakes come from treating them as one. This pack draws the line and puts the
seams on the correct side of it.

**`telegram-bots` — the official HTTP Bot API.** `update_id` is the only
idempotency key an update carries, and a webhook retry, a poller redelivery or a
crash between "work done" and "offset confirmed" all produce the same event
twice. Measured across eight live Telegram bots on this machine on 2026-08-25:
**zero of eight deduplicate on it.** Also here: the `allowed_updates` default
that subscribes you to everything **except** `chat_member`, `message_reaction`
and `message_reaction_count` while returning `ok: true`; the
`X-Telegram-Bot-Api-Secret-Token` header that is the actual check on a webhook;
rate limits as a design constraint (1/sec per chat, 20/min per group, ~30/sec
bulk, and paid broadcasts to 1000/sec); and Telegram Stars, where
`answerPreCheckoutQuery` has **ten seconds** and the grant belongs to
`successful_payment`.

**`telegram-userbots` — MTProto and Telethon.** A bot token is issued to
software; a session is a logged-in human being. The file grants full access with
no password and no 2FA prompt, `FloodWaitError` is the API telling you exactly
how long to wait rather than a failure to swallow, and an account can be limited
or banned in a way a token cannot. The first section is the decision of whether a
user account is needed at all — a 21 MB file is a local Bot API server, not a
permanent liability. Measured here: **three of six** Telethon projects handle
`FloodWaitError`; five of five gitignore the session and none has one tracked,
which is the one trap this estate had already closed.

**`telegram-miniapps` — the web layer.** The entire security model is one signed
query string. `initDataUnsafe` is named that because it is parsed on the user's
device; anything decided from it must be decided again on the server from the raw
`initData`. The verification algorithm ships as a **runnable fixture** rather than
a paragraph — nine checks that watch it refuse a tampered user id, a stale
`auth_date`, a re-serialised `user` field and a key derivation applied backwards.
Also recorded: the SDK package name moved to `@telegram-apps/sdk` (3.11.8) while
the `Telegram-Mini-Apps` organisation still fronts `tma.js` (3.3.0), eight minors
behind, and four of its templates are archived and unsupported.

**Two fixtures, both with their mutants.** `update_delivery.py` holds four
invariants — a redelivered update worked once, a crash mid-work that redelivers
rather than loses, a 429 retried for exactly `retry_after`, and one payment
granted once from any entry point — and `--self-test` removes one rule at a time
and requires each to go red. The first draft of the crash invariant **survived
its own mutant**, because the scenario interrupted after the update rather than
during it; it measures the ordering now.

Read against Bot API **10.3** (released 2026-08-24), Telethon **1.44.0**, and
`core.telegram.org` on 2026-08-25.
