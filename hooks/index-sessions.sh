#!/bin/bash
# index-sessions.sh — SessionEnd hook
# Extracts recent sessions to QMD-friendly markdown and updates QMD index.
# Requires: VAULT_DIR env var (set in ~/.zshrc)

if [ -z "$VAULT_DIR" ]; then
    echo "Error: VAULT_DIR not set" >&2
    exit 1
fi

cd "$VAULT_DIR"
python ~/.claude/skills/recall/scripts/extract-sessions.py --days 3 --source ~/.claude/projects
qmd update
