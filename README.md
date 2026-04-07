# my-claude-skills

Claude Code skills for session memory and recall with Obsidian integration.

## Skills

### sync-claude-sessions

Export Claude Code conversations to Obsidian markdown with live sync via hooks.

- Real-time session sync to `Claude-Sessions/` in your Obsidian vault
- Frontmatter with metadata (date, title, skills, messages, status, tags, rating)
- Korean + English keyword extraction for tags (via ir's Korean preprocessor)
- `## My Notes` section preserved across syncs
- Commands: `sync`, `export`, `resume`, `note`, `close`, `list`, `log`

### recall

Load context from previous sessions. Four modes:

- **Temporal** (date-based): `/recall yesterday`, `/recall last week`
- **Project** (filter by project): `/recall project triton yesterday`, `/recall projects`
- **Topic** (BM25 search): `/recall authentication`, `/recall 인증 작업` (requires [ir](https://github.com/vlwkaos/ir))
- **Graph** (visualization): `/recall graph last week` (requires networkx, pyvis)

Ends every recall with **One Thing** — the single highest-leverage next action.

### ideate

Lightweight collaborative ideation. Alternative to superpowers:brainstorming for open-ended exploration.

- Natural dialogue, not process checklist
- Triggers: `/ideate`, "같이 생각해보자", "이건 어때", "explore ideas"

### save-doc

Save session content (analysis, specs, designs) to Obsidian vault.

## Requirements

- Python 3.10+
- Claude Code with hooks support
- Obsidian vault
- (Optional) [ir](https://github.com/vlwkaos/ir) + Rust 1.80+ for topic search
- (Optional) networkx + pyvis for graph visualization

## Installation

### Step 1: Install skills

```bash
git clone https://github.com/blackironj/my-claude-skills.git
cd my-claude-skills

# Symlink (recommended — edits apply immediately)
ln -s "$(pwd)/skills/"* ~/.claude/skills/

# Or copy
cp -r skills/recall ~/.claude/skills/
cp -r skills/sync-claude-sessions ~/.claude/skills/
cp -r skills/save-doc ~/.claude/skills/
cp -r skills/ideate ~/.claude/skills/
cp skills/shared_utils.py ~/.claude/skills/
```

### Step 2: Create `~/.claude/env` (per machine)

```bash
cat > ~/.claude/env << 'EOF'
export VAULT_DIR="/path/to/your/obsidian-vault"
export VAULT_SESSIONS_DIR="$VAULT_DIR/ai-agent/Claude-Sessions"
export DOCS_DIR="$VAULT_DIR/workspace"
export CLAUDE_SESSIONS_TZ="Asia/Seoul"
export MACHINE_NAME="home-pc"
EOF
```

| Variable | Description |
|----------|-------------|
| `VAULT_DIR` | Obsidian vault root |
| `VAULT_SESSIONS_DIR` | Where Claude session markdown files are synced |
| `DOCS_DIR` | Where `/save-doc` writes documents |
| `CLAUDE_SESSIONS_TZ` | Timezone for session timestamps (default: `Asia/Seoul`) |
| `MACHINE_NAME` | Machine identifier in session frontmatter (optional) |

### Step 3: Add hooks to `~/.claude/settings.json`

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

### Step 4: (Optional) Install ir for topic search

[ir](https://github.com/vlwkaos/ir) enables BM25-based topic search with Korean support. Skip if you only need temporal recall.

```bash
cd ~/workspace
git clone https://github.com/vlwkaos/ir.git && cd ir
cargo install --path . --no-default-features --features llama-openmp  # Linux
# cargo install --path .  # macOS (Metal auto-detected)

# Korean preprocessor
cd preprocessors/ko/lindera-tokenize
cargo install --path .
ir preprocessor add ko lindera-tokenize

# Register collection and build index
source ~/.claude/env
ir collection add sessions "$VAULT_SESSIONS_DIR/"
ir preprocessor bind ko sessions
ir update
```

## License

MIT
