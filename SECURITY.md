# Security

## Reporting

Report privately: [@sshlg93 on X](https://x.com/sshlg93), or a
[private security advisory](https://github.com/ssheleg/telegram-dev/security/advisories/new)
on this repository. Please do not open a public issue for a vulnerability.

## What ships, and what of it executes

This package is **documentation plus two test fixtures**. It contains no service,
no telemetry and no key. Two files execute, and only when you run them:

| File | Runtime behaviour |
|---|---|
| `plugins/telegram-dev/skills/*/SKILL.md` and `references/*.md` | text; read by the agent, executes nothing |
| `plugins/telegram-dev/skills/telegram-miniapps/fixtures/verify_initdata.py` | standard library only — `hashlib`, `hmac`, `json`, `time`, `urllib.parse`. No network, no filesystem write |
| `plugins/telegram-dev/skills/telegram-bots/fixtures/update_delivery.py` | standard library only. No imports beyond `sys`. No network, no filesystem write |
| `bin/telegram-dev.js` — the npm installer | runs only when you invoke it. Node built-ins only: `fs`, `path`, `os` |
| `install.sh` — the shell installer | **not in the tarball**; reaches you only through a clone. It is the destructive channel: `rm -rf` per skill, then `cp -R` |

## The secrets this pack talks about

The skills describe handling three Telegram credentials. **None of them appears
in this repository**, and the validator refuses a payload containing anything
shaped like one — a bot token, an `api_hash`, or a private key:

- a **bot token** (`123456:ABC…`) — identifies the bot;
- **`api_id` / `api_hash`** from `my.telegram.org` — identify an application;
- a **user session** (`.session` file or `StringSession`) — **is the account**:
  full access without the password and without the 2FA prompt.

The third is the one this pack keeps returning to. A leaked session is an
incident, not a rotation.

## Verifying for yourself

```bash
# Nothing key-shaped in the shipped payload, and the plants that prove the guard.
python3 test/validate.py
python3 test/validate.py --self-test

# What the fixtures can reach: NO OUTPUT, and grep exits 1 because it matched nothing.
grep -rnE "subprocess|socket|requests|urlopen|open\(|os\.system" \
  plugins/telegram-dev/skills/*/fixtures/*.py

# The whole I/O surface of the only other executable file.
grep -nE "require|child_process|exec|spawn|fetch|rm -rf|cp -R" bin/telegram-dev.js install.sh
```
