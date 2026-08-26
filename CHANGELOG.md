## v0.1.6 — shared guards identify their owner

The eval and social-preview validators now declare their umbrella-owned shared
mechanisms, making their family provenance explicit and machine-checkable.

## v0.1.5 — three Telegram surfaces, one public review contract

The pack now carries a root skill card, positive and near-miss routing cases,
three behavioral scenarios and an explicit unexecuted-results ledger. The README
opens with one install and a duplicate-update request, the generated social
preview is committed, and CI runs the pinned house audit plus a planted eval
schema failure. Bot API, MTProto and Mini App behavior are unchanged.

## v0.1.4 — a first publish takes longer to propagate than the check allowed

`@ssheleg/telegram-dev@0.1.3` published correctly — `npm publish` printed
`+ @ssheleg/telegram-dev@0.1.3` and signed provenance into the transparency log —
and the release still went red, on the step that polls the registry for three
minutes. A **first** publish creates the package document, which propagates more
slowly than a new version of one that already exists; the replica served nothing
for over three minutes and then served it.

So the poll runs for ten minutes, and it now tells the two cases apart: *the
registry does not know this package at all* and *it knows the package and not this
version* are different problems, and the first one is worth saying is a
propagation check rather than a publish check — because the publish had already
succeeded when this fired.

Also in this release: the README records that DeepSeek Harness loads this pack
with no plugin to write.

## v0.1.3 — the coordination snapshot exists, and something links it

`agent-sync check` wants two things beyond a parsed config: a setup snapshot, and
an agent instruction file that links it — because an agent that cannot find the
snapshot infers the pipeline instead. The umbrella runs that check across every
repository declaring coordination, and this one was the ninth and the only one
failing it.

`docs/AGENT_SYNC.md` is now generated rather than written, and `CLAUDE.md` links
it beside the four invariants this repository holds and the date every Telegram
fact in the skills was read.

## v0.1.2 — the gate now refuses a dropped routing trigger

The family's routing hook fires on phrases these descriptions have to keep, and a
member releases BEFORE the umbrella re-pins — so a member that drops one ships
green and the umbrella finds out minutes after the tag. This gate now asks the
umbrella's own checker, reading the module the hook itself calls, and discloses
rather than passing when no umbrella sits above the checkout.

Adding it exposed a hole in the umbrella's plant sweep, fixed there: the plant
removed the phrase case-sensitively, and this pack's description says *"auditing a
Telegram bot"* in prose while listing `"telegram bot"` as a trigger. The quoted
one went, the prose one stayed, the guard correctly reported the phrase as still
advertised — and the sweep read that as the guard failing to fire. Nine of nine
members refuse the drop now.

## v0.1.1 — the coordination config ships with the clone, and CI stopped lying about installers

`.claude/agent-sync.json` existed only on the machine that wrote it, which
protects nobody who clones the repository; the umbrella's validator refuses a
member without one, and it was right to.

Two CI steps were adapted from `sheleg-dev` and still asserted that pack's files.
The installer step passed `--no-claude`, a flag belonging to the umbrella
launcher, so the first run exited 2 on a step about installers with nothing wrong
with the installer. The release smoke test looked for
`crypto-payments/references/heleket-provider.md`. Both now derive their list from
this tree and run the shipped `initData` fixture from the installed copy — a
skill whose references did not travel arrives as a body full of links to nothing.

And the version plant in the validator's own self-test named a literal `0.1.0`,
so it stopped planting anything the moment the version moved. It reported itself
`BROKEN` rather than passing, which is the behaviour that found it; it now
derives the number it bumps.

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
