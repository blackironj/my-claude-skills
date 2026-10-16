#!/bin/bash
set -euo pipefail

# SessionEnd: final sync (Stop misses a last turn that was interrupted), then
# refresh the ir index so it includes that final state.
# The hook JSON must be piped in by the caller: a backgrounded command (`&`)
# otherwise gets /dev/null as stdin and sync cannot find the session.
. ~/.claude/env
python ~/.claude/skills/sync-claude-sessions/scripts/claude-sessions sync --daily-append

if command -v ir >/dev/null 2>&1; then
    ir update
fi
