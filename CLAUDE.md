# CLAUDE.md — telegram-dev

House rules for **this repository only**. Family doctrine (language, quality bar,
routing) loads from `~/.claude/CLAUDE.md` in the same session; a second copy here
would be a second source of truth that drifts.

## What this repo is

Three agent skills for Telegram, separated by **which API each surface actually
speaks**. That separation is the product: a bot token, a user session and a
signed query string have different capabilities, different limits and very
different ways of losing money or an account.

## The gate

```bash
npm test               # test/validate.py, then both fixtures (one with its mutant matrix)
npm run test:negatives # plant each defect and require the validator to refuse it
```

Both green or the change does not land.

## Invariants — each one has a check that has been watched failing

- **A rule that can be executed is executed.** The `initData` verifier and the
  update-delivery invariants ship as runnable fixtures with their mutants, not as
  paragraphs. The crash invariant survived its own mutant on the first draft —
  the scenario interrupted after the update rather than during it — which is
  exactly what a mutant matrix is for.
- **A number is derived, never typed.** The README's skill count is compared to
  the tree. The version plant in the self-test derives the number it bumps, after
  a literal `0.1.0` stopped planting anything at v0.1.1.
- **The description keeps the phrases the family's routing hook fires on.** This
  repository releases BEFORE the umbrella re-pins, so a dropped trigger ships
  green and the umbrella finds out after the tag. The check asks the umbrella's
  own checker rather than copying its table, and discloses when no umbrella sits
  above the checkout.
- **Nothing secret-shaped reaches the payload.** A bot token, an `api_hash` or a
  private key in a file that gets copied into other people's repositories is an
  incident. The validator refuses one, and the plant proves it.

## Coordination

`docs/AGENT_SYNC.md` — how coordination is wired here and what it does not
guarantee. Read it before editing a guarded file: `CHANGELOG.md`,
`package.json`, both manifests, the workflows, `test/validate.py`, `README.md`.

## Where the facts came from

Every version, limit and parameter name in the skills carries the date it was
read. Bot API **10.3** (2026-08-24), Telethon **1.44.0**, `core.telegram.org`
2026-08-25. The baseline the pack was written against is eight live Telegram bots
on the author's machine, measured the same day — not imagined problems.
