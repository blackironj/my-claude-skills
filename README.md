# my-claude-skills

Claude Code skills for session memory, recall, and Obsidian integration — with daily note sync, vault search, and session dashboards.

## Skills

### sync-claude-sessions

Export Claude Code conversations to Obsidian markdown with live sync via hooks.

- Real-time session sync to `Claude-Sessions/` in your Obsidian vault
- Frontmatter with metadata (date, title, skills, messages, status, tags, rating)
- Korean + English keyword extraction for tags (via ir's Korean preprocessor)
- `## My Notes` section preserved across syncs
- Auto-appends session summary to Obsidian daily notes (`Daily Notes/YYYY-MM-DD.md`)
- Backfill tool to populate daily notes from existing sessions
- Sessions dashboard (`.base` file) with All / Active / By Project views
- Commands: `sync`, `export`, `resume`, `note`, `close`, `list`, `log`

### recall

Load context from previous sessions. Four modes:

- **Temporal** (date-based): `/recall yesterday`, `/recall last week`
- **Project** (filter by project): `/recall project triton yesterday`, `/recall projects`
- **Topic** (BM25 search + Obsidian search fallback): `/recall authentication`, `/recall 인증 작업` ([ir](https://github.com/vlwkaos/ir) optional — falls back to Obsidian search)
- **Handoff** (resume from a save-doc session handoff): `/recall handoff spec-auth`, "spec-auth 이어서 할 거 뭐 있지"

Ends every recall with **One Thing** — the single highest-leverage next action.

### ideate

Lightweight collaborative ideation for open-ended exploration.

- Natural dialogue, not process checklist
- Triggers: `/ideate`, "같이 생각해보자", "이건 어때", "어떻게 생각해", "explore ideas"

### save-doc

Save session content (analysis, specs, designs) to Obsidian vault under `$DOCS_DIR`.

- Ranks target folders by matching the current repo to docs `project` frontmatter and folder names (`scripts/suggest-path.py`); proposes a new folder when nothing matches
- Session handoff mode (`handoff.md`): saves next-session state to `<folder>/_session-handoff/` with a fixed structure and a paste-ready resume prompt
- Writes Obsidian properties (`date`, `type`, `project`, `tags`) as YAML frontmatter
- Triggers: `/save-doc`, "저장해줘", "vault에 넣어줘", "save this", "export to vault"

### fluent-korean-subagent hook

`hooks/fluent-korean-subagent.py` is a `PreToolUse` hook for the `Agent` tool. Output styles live in the parent session's system prompt and never reach subagents, so a Korean subagent prompt loses the fluent-korean rules on hand-off. The hook appends the body of `~/.claude/output-styles/fluent-korean.md` to prompts that are mostly Hangul (about 7 KB per Korean subagent call) and leaves English prompts alone.

```bash
ln -s "$(pwd)/hooks/fluent-korean-subagent.py" ~/.claude/hooks/
```

Register it in `~/.claude/settings.json` as shown in Step 3 below.

## Requirements

- Python 3.10+
- Claude Code with hooks support
- Obsidian vault (with Daily Notes core plugin enabled for daily note sync)
- (Optional) Obsidian desktop with CLI enabled — for vault search fallback and property tagging
- (Optional) [ir](https://github.com/vlwkaos/ir) for BM25 topic search — needs Rust 1.80+, `libclang-dev`, `cmake`

## Installation

### Step 1: Install skills

```bash
git clone https://github.com/blackironj/my-claude-code.git
cd my-claude-code

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
export OBSIDIAN_CLI="/path/to/Obsidian.com"  # optional, enables daily notes and vault search
EOF
```

| Variable | Description |
|----------|-------------|
| `VAULT_DIR` | Obsidian vault root |
| `VAULT_SESSIONS_DIR` | Where Claude session markdown files are synced |
| `DOCS_DIR` | Where `/save-doc` writes documents |
| `CLAUDE_SESSIONS_TZ` | Timezone for session timestamps (default: `Asia/Seoul`) |
| `MACHINE_NAME` | Machine identifier in session frontmatter (optional) |
| `OBSIDIAN_CLI` | Path to Obsidian desktop CLI (optional — enables daily notes, vault search) |

### Step 3: Add hooks to `~/.claude/settings.json`

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Agent",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/fluent-korean-subagent.py",
            "timeout": 5
          }
        ]
      }
    ],
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
            "command": ". ~/.claude/env && python ~/.claude/skills/sync-claude-sessions/scripts/claude-sessions sync --daily-append",
            "timeout": 15,
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
            "command": "nohup bash ~/.claude/hooks/index-sessions.sh >> ~/.claude/hooks/index-sessions.log 2>&1 &",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### Step 4: (Optional) Install ir for topic search

[ir](https://github.com/vlwkaos/ir) enables BM25-based topic search with Korean support. Skip if you only need temporal, project, and handoff recall.

```bash
cargo install --git https://github.com/vlwkaos/ir --no-default-features --features llama-openmp  # Linux
# cargo install --git https://github.com/vlwkaos/ir  # macOS (Metal auto-detected)

# Korean preprocessor (optional, for CJK search)
ir preprocessor install ko

# Register collection and build index
source ~/.claude/env
ir collection add sessions "$VAULT_SESSIONS_DIR/"
ir preprocessor bind ko sessions
ir update
```

## Roadmap

- **Wiki layer** — Auto-distill repeated session topics into consolidated knowledge docs (`wiki/`). Three phases: session takeaways in daily notes → semi-auto topic pages when 3+ sessions overlap → full auto wiki maintenance. Inspired by [Karpathy's llm-wiki](https://gist.github.com/karpathy) pattern.
- **Session canvas** — Generate `.canvas` files for native Obsidian visualization of session-file relationships.
- **defuddle web clipper** — Web page → clean markdown → vault via [defuddle](https://github.com/kepano/defuddle).

## License

MIT
