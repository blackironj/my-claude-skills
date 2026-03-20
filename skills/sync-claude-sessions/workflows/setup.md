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
EOF
```

## 3. Configure Hooks

Edit `~/.claude/settings.json` and add the hooks:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": ". ~/.claude/env && python ~/.claude/skills/sync-claude-sessions/scripts/claude-sessions sync",
            "timeout": 10
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": ". ~/.claude/env && python ~/.claude/skills/sync-claude-sessions/scripts/claude-sessions sync",
            "timeout": 10
          }
        ]
      }
    ],
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash ~/.claude/hooks/index-sessions.sh >> ~/.claude/hooks/index-sessions.log 2>&1",
            "timeout": 30
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

Install [ir](https://github.com/vlwkaos/ir) for keyword search across sessions and notes. ir is installed locally per machine — the Obsidian vault (with `Claude-Sessions/` and `Notes/`) syncs across PCs via Obsidian Sync, but ir and its index must be set up on each machine.

```bash
# Build from source (Rust 1.80+ required)
cd ~/workspace/ir
cargo install --path .

# Korean preprocessor (build from source on Linux)
cd ~/workspace/ir/preprocessors/ko/lindera-tokenize
cargo install --path .
ir preprocessor add ko lindera-tokenize

# Register collections
ir collection add sessions "$VAULT_DIR/Claude-Sessions/"
ir collection add notes "$VAULT_DIR/Notes/"

# Bind preprocessor + build index
ir preprocessor bind ko sessions
ir preprocessor bind ko notes
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

# Test ir indexing (should update search index)
bash ~/.claude/hooks/index-sessions.sh
```

## What Gets Synced

- **On every message (UserPromptSubmit/Stop):** Session metadata, skills used, artifacts created/modified, conversation
- **On session end (SessionEnd):** ir index update for topic search via recall
- **Preserved across syncs:** `## My Notes` section, `status`, `tags`, `rating`, `comments` fields
