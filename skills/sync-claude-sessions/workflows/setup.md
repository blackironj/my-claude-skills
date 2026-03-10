# Setup: Live Session Sync

## Prerequisites

- Python 3.10+
- Obsidian vault (target for session exports)
- (Optional) [QMD](https://github.com/ArtemXTech/qmd) for topic search via recall skill

## 1. Install Skills

Copy skills to `~/.claude/skills/`:

```bash
cp -r skills/recall ~/.claude/skills/
cp -r skills/sync-claude-sessions ~/.claude/skills/
```

## 2. Set VAULT_DIR

Add to your shell profile (`~/.zshrc` or `~/.bashrc`):

```bash
export VAULT_DIR="/path/to/your/obsidian-vault"
```

This keeps `~/.claude/settings.json` portable across machines — only the shell profile differs per PC.

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
            "command": "python ~/.claude/skills/sync-claude-sessions/scripts/claude-sessions sync",
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
            "command": "python ~/.claude/skills/sync-claude-sessions/scripts/claude-sessions sync",
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

## 5. (Optional) QMD Topic Search

Set up QMD collections for recall topic search:

```bash
cd "$VAULT_DIR"
qmd collection add Claude-Sessions --name sessions
qmd collection add Notes --name notes
qmd update
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

# Test extract (should find and extract sessions)
python ~/.claude/skills/recall/scripts/extract-sessions.py --days 1 --source ~/.claude/projects

# Test QMD indexing
bash ~/.claude/hooks/index-sessions.sh
```

## What Gets Synced

- **On every message (UserPromptSubmit/Stop):** Session metadata, skills used, artifacts created/modified, conversation
- **On session end (SessionEnd):** QMD index update for topic search via recall
- **Preserved across syncs:** `## My Notes` section, `status`, `tags`, `rating`, `comments` fields
