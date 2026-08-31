# Skill Card — telegram-dev

## Identity

| Field | Value |
|---|---|
| Pack | `telegram-dev` |
| Version | `0.1.11` |
| Skills | `telegram-bots`, `telegram-userbots`, `telegram-miniapps` |
| License | MIT |
| Source | https://github.com/ssheleg/telegram-dev |

## Job and boundary

Build Telegram surfaces on the API they actually use: Bot API, MTProto user
accounts or Mini Apps. A one-off alert over HTTP is transport, not a Telegram
product. Product behavior, visual style, copy and card payments keep their own
owners.

## Inputs and outputs

Inputs are an existing application, chosen Telegram surface and credentials
provided through the product's secret store. Outputs are repository changes,
delivery/authentication handlers, tests and runnable fixtures.

## Runtime and trust

Bot tokens and Telethon sessions never ship with the pack. A session file is a
logged-in user credential. Mini App authentication verifies the original
`initData` server-side; `initDataUnsafe` is display data. Duplicate Bot API
updates and MTProto flood waits are normal protocol states.

## Distribution

Install from npm/GitHub, through the Agent Skills CLI, or as the
`telegram-dev` Claude Code plugin.

## Verification

- Repository validator and tests: `npm test`
- Protocol mutant fixtures: repository test suite
- House audit: pinned `make-skill` auditor in `validate.yml`
- Declared `$schema` addresses resolved and validated: `python3 test/check_schemas.py`
- Behavioral data: `test/evals/`
- Evaluation status: executed 2026-08-31 against claude-haiku and claude-sonnet;
  two dated rows with their method in `test/evals/RESULTS.md`

## Known limits

Telegram limits and SDK packages change. Production work must verify the current
official API contract. A userbot carries account-ban and session-compromise risk
that a bot token does not.

