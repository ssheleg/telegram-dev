# Evaluation results

**Status: executed 2026-08-31 against two models.** The dated rows below are the
first behavioral measurements of this pack; before them this file said
"authored, never executed" — and said so on purpose, because CI proves shape,
not behavior.

| Date | Version | Model | Trigger pass rate (train / validation) | Scenario lines passed | Installed alongside | Notes |
|---|---|---|---|---|---|---|
| 2026-08-31 | 0.1.10 | claude-haiku | 17/18 / 18/18 (35/36 cases) | 6/12 (s01 1/4, s02 2/4, s03 3/4) | ssheleg family, 28 skills (see Method) | Never loaded a skill in the scenarios (0 tool calls each) — missed exactly the seams the pack documents |
| 2026-08-31 | 0.1.10 | claude-sonnet | 15/18 / 15/18 (30/36 cases) | 12/12 (s01 4/4, s02 4/4, s03 4/4) | ssheleg family, 28 skills (see Method) | Loaded the matching skill in all 3 scenarios (3–4 tool calls each); over-fires on near-miss negatives |

## Trigger detail (each query asked 3×, fresh session each time)

All six positives fired the **intended surface** 3/3 on both models
(q01/q04/q06 → `telegram-bots`, q02/q05 → `telegram-userbots`,
q03 → `telegram-miniapps`). Every dropped case is a near-miss negative that
pulled a telegram-dev skill when it should not have:

| Query (should NOT fire) | claude-haiku fired | claude-sonnet fired |
|---|---|---|
| q07 one HTTP alert to a bot | 1/3 (`telegram-bots`) | 1/3 (`telegram-bots`) |
| q08 сценарии онбординга для бота | 0/3 | 2/3 (`telegram-bots`) |
| q09 Stripe behind the Mini App | 0/3 | 0/3 |
| q10 visual style of the Mini App | 0/3 | 2/3 (`telegram-miniapps`) |
| q11 текст приветственного сообщения | 0/3 | 0/3 |
| q12 same workflow as a Slack bot | 0/3 | 1/3 (`telegram-bots`) |

Correct routes taken instead: q08 → `ux-flows`/`ux-scenarios`,
q09 → `stripe-billing`, q10 → `sheleg-design`, q11 → `copywriting`,
q12 → none/`agent-orchestrator`. The asymmetry is the finding: the stronger
model resolves near-misses toward the pack, so the "Not for" clauses in the
three descriptions are carrying real weight and any trim to them should
re-run this table first.

## Scenario detail (per expected_behavior line)

| Scenario line | haiku | sonnet |
|---|---|---|
| s01 uses `update_id` as idempotency key | pass | pass |
| s01 claims the update before side effects | **fail** (recorded after processing; its own race test would not hold) | pass |
| s01 validates the webhook secret header | **fail** (never mentioned) | pass |
| s01 retries and rate limits as normal delivery | **fail** (retries yes, rate limits absent) | pass |
| s02 first checks whether a user account is required | **fail** | pass |
| s02 treats the session file as a logged-in credential | pass | pass |
| s02 handles FloodWaitError for the exact duration | pass (`e.seconds + 1`) | pass |
| s02 names revocation, ban and library-version risks | **fail** (ban yes, revocation partial, pinning absent) | pass |
| s03 verifies the signed query string server-side | pass | pass |
| s03 does not trust initDataUnsafe | pass (implicit — never names it) | pass (explicit) |
| s03 checks auth_date against an explicit window | pass | pass |
| s03 correct bot-token / Ed25519 verification path | **fail** (HMAC keyed on the raw bot token — the missing-`WebAppData`-derivation defect the fixture exists for) | pass (correct derivation, `signature` field excluded knowingly) |

## Method (2026-08-31 run)

- **Harness**: Claude Code Agent tool from an automated wave-3 session on the
  author's machine; one fresh `general-purpose` sub-agent per probe, model
  forced per row (`haiku`, `sonnet`). No other models are claimed by this
  suite, so no others were probed.
- **Triggers**: each of the 12 queries asked verbatim, 3 repetitions per
  model (72 probes). The prompt carried the query plus an instruction to read
  a roster file of the installed family — 28 skill names with descriptions,
  extracted from the nine family repositories' `SKILL.md` front matters
  (make-skill, evidence-docs, project-audit, task-pipeline, brand-voice,
  copywriting, ux-audit, ux-flows, ux-foundation, ux-scenarios, vision,
  sheleg-design, seo-aeo-audit, agent-sync, ad-tracking, crypto-payments,
  error-tracking, frontend-performance, google-auth, google-signin,
  stripe-billing, agent-evals, agent-harness, agent-interop,
  agent-orchestrator, telegram-bots, telegram-miniapps, telegram-userbots) —
  and to answer with one skill name or "none". A positive passes when one of
  the three telegram-dev skills is named; a negative passes when none is.
- **Scenarios**: each scenario query sent verbatim to a fresh sub-agent per
  model with the pack installed as a plugin on the machine; the reply was
  scored line by line by the coordinating agent. Lines were scoreable from a
  single reply, so nothing is recorded as `not reproducible from this
  harness` this run.
- **Limits, stated**: (1) several sonnet trigger probes answered from the
  machine's native installed-skill listing without reading the roster file
  (0 tool calls) — same information, counted as valid; (2) a sub-agent is not
  a top-level session: the operator's SessionStart routing hooks were not in
  the path, so this measures description-driven selection only; (3) scenario
  scoring is one judge reading one reply, not an interactive multi-turn run.
- **Headline**: whether the skill gets loaded is worth 6 lines out of 12 —
  haiku answering from memory reproduced the exact defects the fixtures plant
  (claim-after-work, missing secret header, HMAC keyed on the raw token),
  and sonnet with the skill loaded shipped none of them.
