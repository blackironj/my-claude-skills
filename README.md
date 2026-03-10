# claude-code-skills

Two [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skills for session memory and recall. Adapted from [ArtemXTech/personal-os-skills](https://github.com/ArtemXTech/personal-os-skills).

## Skills

### sync-claude-sessions

Export Claude Code conversations to Obsidian markdown with live sync via hooks. Auto-syncs on every prompt submission and response completion.

Features:
- Real-time session sync to `Claude-Sessions/` in your Obsidian vault
- Frontmatter with metadata (date, title, skills, messages, status, tags, rating)
- `## My Notes` section preserved across syncs
- Commands: `sync`, `export`, `resume`, `note`, `close`, `list`, `log`

### recall

Load context from previous sessions. Three modes:

- **Temporal** (date-based): `/recall yesterday`, `/recall last week`
- **Topic** (BM25 search): `/recall authentication` (requires [QMD](https://github.com/ArtemXTech/qmd))
- **Graph** (visualization): `/recall graph last week` (requires networkx, pyvis)

Ends every recall with **One Thing** — the single highest-leverage next action.

## Installation

```bash
# Clone
git clone https://github.com/blackironj/claude-code-skills.git
cd claude-code-skills

# Install skills
cp -r skills/recall ~/.claude/skills/
cp -r skills/sync-claude-sessions ~/.claude/skills/

# Install SessionEnd hook
mkdir -p ~/.claude/hooks
cp hooks/index-sessions.sh ~/.claude/hooks/
chmod +x ~/.claude/hooks/index-sessions.sh
```

## Configuration

### 1. Set VAULT_DIR (per machine)

Add to `~/.zshrc` or `~/.bashrc`:

```bash
export VAULT_DIR="/path/to/your/obsidian-vault"
```

### 2. Add hooks to `~/.claude/settings.json`

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

### 3. (Optional) QMD for topic search

```bash
cd "$VAULT_DIR"
qmd collection add Claude-Sessions --name sessions
qmd update
```

See [setup guide](skills/sync-claude-sessions/workflows/setup.md) for full details.

## Requirements

- Python 3.10+
- Claude Code with hooks support
- Obsidian vault
- (Optional) QMD for topic search
- (Optional) networkx + pyvis for graph visualization

## License

MIT
