# Contributing

## The gate

<!-- commands-run-in: a clone -->
Both commands run in a clone; the published package ships `bin/` and `plugins/`
only, so neither resolves from an install.

```bash
npm test               # test/validate.py, then both fixtures (one with its mutant matrix)
npm run test:negatives # plant each defect and require the validator to refuse it
```

A change that does not keep both green does not land. `test/validate.py
--self-test` is the half that matters: it copies the tree, breaks exactly the
thing each check exists for, and fails if the validator still passes.

## What a change owes

- **A claim carries its receipt.** A version, a limit, a parameter name — quote
  where it was read and when. "Bot API 10.3, read 2026-08-25" ages well; "the
  current version" does not.
- **A number is computed or compared, never typed.** The README's skill count is
  checked against the tree by the validator, and anything else countable should
  be too.
- **A fixture beats a paragraph.** If a rule can be executed, execute it — and
  give it a mutant, so somebody has watched it fail.
- **The three skills stay separate.** A fact true of the Bot API does not belong
  in the userbot skill because it is convenient; the boundary is the product.
- **Budgets:** a `SKILL.md` body stays under 4750 tokens and 500 lines, and a
  description under 970 characters. Past either, the answer is a split into
  `references/`, not a trim.

## Versioning

`package.json`, `plugins/telegram-dev/.claude-plugin/plugin.json`,
`.claude-plugin/marketplace.json` and the top `CHANGELOG.md` entry carry the same
semver and move together. The validator refuses a tree where they disagree.
