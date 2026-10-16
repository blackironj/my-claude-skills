# Setup: Live Session Sync

## Prerequisites

- Python 3.10+
- Obsidian vault (target for session exports)
- (Optional) [ir](https://github.com/vlwkaos/ir) for topic search via recall skill

## 1. Install Skills

Copy skills to `~/.claude/skills/`:

```bash
cp -r skills/recall ~/.claude/skills/
cp -r skills/sync-claude-sessions ~/.claude/skills/
```

## 2. Create `~/.claude/env`

This is the only file that differs per machine:

```bash
cat > ~/.claude/env << 'EOF'
# Claude Code environment — sourced by all hooks
export VAULT_DIR="/path/to/your/obsidian-vault"
export VAULT_SESSIONS_DIR="$VAULT_DIR/ai-agent/Claude-Sessions"
export DOCS_DIR="$VAULT_DIR/workspace"
EOF
```

## 3. Configure Hooks

Edit `~/.claude/settings.json` and add the hooks:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": ". ~/.claude/env && python ~/.claude/skills/sync-claude-sessions/scripts/claude-sessions sync --daily-append",
            "timeout": 30,
            "async": true
          }
        ]
      }
    ],
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "in=$(cat); printf '%s' \"$in\" | nohup bash ~/.claude/hooks/index-sessions.sh >> ~/.claude/hooks/index-sessions.log 2>&1 &",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

## 4. Install SessionEnd Hook Script

```bash
cp hooks/index-sessions.sh ~/.claude/hooks/
chmod +x ~/.claude/hooks/index-sessions.sh
```

### Step 5: ir for topic search (optional)

Install [ir](https://github.com/vlwkaos/ir) for keyword search across sessions. ir is installed locally per machine — the Obsidian vault (with `Claude-Sessions/`) syncs across PCs via Obsidian Sync, but ir and its index must be set up on each machine.

```bash
# Install ir (Rust 1.80+ required)
cargo install --git https://github.com/vlwkaos/ir --tag v0.11.0

# Korean preprocessor (cross-platform since v0.11.0)
ir preprocessor install ko

# Register collection
ir collection add sessions "$VAULT_SESSIONS_DIR/"

# Bind preprocessor + build index
ir preprocessor bind ko sessions
ir update
```

## 6. Shell Alias (Optional)

```bash
# Add to ~/.zshrc
alias cs="python ~/.claude/skills/sync-claude-sessions/scripts/claude-sessions"
```

Then:
- `cs list` — list active sessions
- `cs note "got it working"` — add note
- `cs close "done"` — mark done
- `cs resume --pick` — resume session

## 7. Verify

```bash
# Test sync hook (should print "Synced: ..." or exit silently)
echo '{}' | python ~/.claude/skills/sync-claude-sessions/scripts/claude-sessions sync

# Test SessionEnd hook (final sync + ir index update)
echo '{}' | bash ~/.claude/hooks/index-sessions.sh
```

## What Gets Synced

- **After every response (Stop):** Session metadata, skills used, artifacts created/modified, conversation
- **On session end (SessionEnd):** final sync (covers an interrupted last turn), then ir index update for topic search via recall
- **Preserved across syncs:** `## My Notes` section, `status`, `tags`, `rating`, `comments` fields
