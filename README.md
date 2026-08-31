# telegram-dev

[![validate](https://github.com/ssheleg/telegram-dev/actions/workflows/validate.yml/badge.svg)](https://github.com/ssheleg/telegram-dev/actions/workflows/validate.yml)
[![npm](https://img.shields.io/npm/v/%40ssheleg%2Ftelegram-dev)](https://www.npmjs.com/package/@ssheleg/telegram-dev)
[![license](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![site](https://img.shields.io/badge/docs-skills.sshlg.me-8ab0ff)](https://skills.sshlg.me/skills/telegram-dev/)
[![skills.sh](https://skills.sh/b/ssheleg/telegram-dev)](https://skills.sh/ssheleg/telegram-dev)

**Build Telegram bots, userbots and Mini Apps on the right API, with their delivery and authentication risks explicit.**

```bash
npx skills add ssheleg/telegram-dev
```

Ask: `Build a Bot API webhook that safely handles duplicate updates.`

**[Detailed docs →](https://skills.sshlg.me/skills/telegram-dev/)**

**[Docs, and every skill →](https://skills.sshlg.me/)** · [this skill's page](https://skills.sshlg.me/skills/telegram-dev/) · [follow @sshlg93 on X](https://x.com/intent/follow?screen_name=sshlg93)

Loads in **DeepSeek Harness** (`dsh`) with **no plugin to write**: it reads the
Agent Skills standard directly, scanning `~/.agents/skills` — where `npx skills
add` puts this pack — at rank 500.

**Telegram is three products behind one brand.** A bot token, a user account and
a web page in a WebView have different capabilities, different limits and very
different ways of losing money or an account. **Three skills**, one per surface,
so an agent picks the right one before it writes anything.

Part of the [ssheleg skill family](https://skills.sshlg.me/).

---

## The three, and the line between them

| Skill | The API it speaks | Reach for it when |
|---|---|---|
| **`telegram-bots`** | official HTTP **Bot API** | a bot users add to chats — no phone number, no ban risk |
| **`telegram-userbots`** | **MTProto** via Telethon | the job needs a user account, and you have written down why |
| **`telegram-miniapps`** | the **Mini App** web layer | a page inside Telegram, whose whole auth is one signed blob |

The boundary is not stylistic. A bot cannot read history from before it joined,
act on behalf of a person, or download a file over 20 MB — and a user account can
be limited or banned in a way a token cannot. `telegram-userbots` opens with the
decision of whether you need one at all, because the cheapest answer is usually a
local Bot API server.

## What each one owns

- **`telegram-bots`** — `update_id` as the only idempotency key; the
  `allowed_updates` default that silently drops three update types; the webhook
  secret header; rate limits as a design constraint; Telegram Stars, the
  ten-second pre-checkout window, and granting on `successful_payment`.
- **`telegram-userbots`** — the session file as a credential equal to the
  password; `FloodWaitError` as a number rather than a condition; pinning across
  minor releases that move session and entity-cache behaviour; `takeout` for bulk
  export; the ban risk, stated plainly.
- **`telegram-miniapps`** — verifying `initData` with HMAC-SHA256 and the
  `WebAppData` derivation, the `auth_date` window, the Ed25519 path for a third
  party, exchanging the blob for your own session, and the SDK package whose name
  moved.

## What loads on demand

**Ten reference files** ship beside the three skills. Each `SKILL.md` stays
inside its token budget and pulls these in only when the work reaches them —
this table is what actually arrives in your repository, and the validator
compares it to the tree both ways:

| Skill | Reference | Load it when |
|---|---|---|
| `telegram-bots` | `references/updates-and-delivery.md` | wiring `getUpdates` or `setWebhook`, or explaining why an update arrived twice or not at all |
| `telegram-bots` | `references/payments-stars.md` | the bot sells anything — Stars, the ten-second pre-checkout window, refunds |
| `telegram-bots` | `references/limits-and-files.md` | sending at volume, broadcasting, or moving anything larger than a photo |
| `telegram-bots` | `references/frameworks.md` | choosing a library, or auditing one somebody else chose |
| `telegram-miniapps` | `references/initdata-verification.md` | implementing or reviewing `initData` verification — both algorithms, every known wrong turn |
| `telegram-miniapps` | `references/app-to-bot.md` | the app has to return a result, open an inline result, or take money |
| `telegram-miniapps` | `references/viewport-and-platform.md` | the app looks wrong on a real device — safe areas, the jumping viewport |
| `telegram-userbots` | `references/sessions-and-auth.md` | creating, storing or moving a session, or a process that ran yesterday asks for a code |
| `telegram-userbots` | `references/rate-and-flood.md` | anything iterates over chats, users, messages or media — FloodWait, pacing, takeout |
| `telegram-userbots` | `references/entities-and-history.md` | resolving users or chats, iterating messages, downloading at scale |

## Runnable, not described

```bash
python3 plugins/telegram-dev/skills/telegram-miniapps/fixtures/verify_initdata.py
python3 plugins/telegram-dev/skills/telegram-bots/fixtures/update_delivery.py --self-test
```

Standard library only, no network. The first is the `initData` verifier to copy,
with nine checks watching it refuse a tampered user id, a stale `auth_date`, a
re-serialised `user` field and a reversed key derivation. The second holds four
delivery invariants and, under `--self-test`, removes one rule at a time and
requires each invariant to go red.

## Install

```bash
npx skills add ssheleg/telegram-dev
```

```bash
claude plugin marketplace add ssheleg/telegram-dev && claude plugin install telegram-dev@telegram-dev
```

The whole family in one command:

```bash
npx sshlg-skills install
```

## Development

<!-- commands-run-in: a clone -->
These run in a clone of this repository; the published package ships `bin/` and
`plugins/` only.

```bash
npm test              # the validator, then both fixtures including the mutant matrix
npm run test:negatives # plant each defect and require the validator to refuse it
```

Both are offline and stdlib-only, which is why the `$schema` guard inside them can
only pin the two addresses rather than resolve them. The half that fetches is kept
separate, because `npm test` has to keep working with no network:

```bash
pip install jsonschema && python3 test/check_schemas.py
```

It resolves every `$schema` the manifests declare and validates each document
against what that address actually serves. It exits 2, not 0, when SchemaStore is
unreachable — a check that could not look must not read as one that looked.

Contributions welcome — see [CONTRIBUTING.md](CONTRIBUTING.md). To report a
vulnerability, see [SECURITY.md](SECURITY.md).

## Author

Built by ssheleg — [sshlg.me](https://sshlg.me)

- X / Twitter — [@sshlg93](https://x.com/sshlg93) ·
  [follow in one click](https://x.com/intent/follow?screen_name=sshlg93)

## License

MIT © 2026 ssheleg.
