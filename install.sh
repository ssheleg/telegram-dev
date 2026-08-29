#!/usr/bin/env bash
# Install every telegram-dev skill into ~/.claude/skills/<name>.
# Idempotent: rerun to overwrite. Zero dependencies beyond coreutils.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$ROOT/plugins/telegram-dev/skills"
DEST_ROOT="${HOME}/.claude/skills"

FORCE=0
if [[ "${1:-}" == "--force" ]]; then
  FORCE=1
elif [[ -n "${1:-}" ]]; then
  echo "usage: $0 [--force]" >&2
  exit 2
fi

if [ ! -d "$SRC" ]; then
  echo "error: skill sources missing at $SRC" >&2
  exit 1
fi

# One channel per agent: plain copies beside an installed plugin are two
# listings of every skill in this pack, and the stale copies win. Refuse rather
# than create that, and refuse loudly — reproduced live 2026-08-29 on this very
# pack: a bare `npx @ssheleg/telegram-dev` shipped all three skills as plain
# copies into the operator's ~/.claude/skills/ while the telegram-dev plugin
# was enabled, because nothing here looked. installed_plugins.json is the
# record of what is installed and is read first; the marketplaces/ dir alone
# under-reports (a directory-sourced marketplace has no dir there, and plugin
# names differ from marketplace names), so it is kept only as the fallback
# signal. A missing or unparsable JSON reads as "no plugin" — fail open.
INSTALLED_JSON="${HOME}/.claude/plugins/installed_plugins.json"
MARKETPLACE="${HOME}/.claude/plugins/marketplaces/telegram-dev"
SPEC=""
if [[ -f "$INSTALLED_JSON" ]]; then
  SPEC="$(sed -n 's/.*"\(telegram-dev@[^"]*\)".*/\1/p' "$INSTALLED_JSON" 2>/dev/null | head -n 1)" || true
fi
if [[ ( -n "$SPEC" || -e "$MARKETPLACE" ) && "$FORCE" -eq 0 ]]; then
  {
    if [[ -n "$SPEC" ]]; then
      echo "refused: telegram-dev is already installed as the Claude Code plugin $SPEC"
      echo "         (declared in ~/.claude/plugins/installed_plugins.json)."
    else
      echo "refused: telegram-dev is already registered as a Claude Code marketplace"
      echo "         ($MARKETPLACE)."
    fi
    echo "         Plain copies in ~/.claude/skills/ would shadow the plugin's skills"
    echo "         and serve this frozen version forever. Update the plugin channel"
    echo "         instead:"
    echo "           claude plugin marketplace update telegram-dev"
    echo "           claude plugin update ${SPEC:-telegram-dev@telegram-dev}"
    echo "         Family launcher: npx --yes sshlg-skills@latest update"
    echo "         Pass --force to write the plain copies anyway."
  } >&2
  exit 3
fi

count=0
for dir in "$SRC"/*/; do
  [ -d "$dir" ] || continue
  name="$(basename "$dir")"
  dest="$DEST_ROOT/$name"
  mkdir -p "$DEST_ROOT"
  rm -rf "$dest"
  cp -R "$dir" "$dest"
  echo "Installed $name -> $dest"
  count=$((count + 1))
done

if [ "$count" -eq 0 ]; then
  echo "error: no skills found under $SRC" >&2
  exit 1
fi

echo "Installed $count skill(s). Restart your agent — skills load at session start."
# The last line says how the next version arrives.
echo "Updates: git pull && ./install.sh --force, or npx --yes sshlg-skills@latest update"
