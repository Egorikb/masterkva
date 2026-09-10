#!/usr/bin/env bash
set -euo pipefail

# RED check: frontend must not parse text-embedded [VISUAL] protocol.
if rg -n "\\[VISUAL\\]|\\[/VISUAL\\]" components app lib --glob '*.{ts,tsx}' >/tmp/no-visual-protocol.matches 2>/dev/null; then
  echo "❌ Found legacy [VISUAL] protocol usage in frontend source:"
  cat /tmp/no-visual-protocol.matches
  exit 1
fi

echo "✅ No legacy [VISUAL] protocol markers found"
