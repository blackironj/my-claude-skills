# my-claude-skills

Personal Claude Code skills for session memory, recall, and ideation with Obsidian integration.

## Structure

```
skills/
  ideate/SKILL.md                        — Lightweight collaborative ideation (markdown-only)
  recall/
    SKILL.md                             — Session recall skill
    scripts/recall-day.py                — Temporal recall (date-based)
    scripts/session-graph.py             — Graph visualization
    scripts/common.py                    — Shared recall utilities
    workflows/recall.md                  — Routing logic and presentation rules
  save-doc/SKILL.md                      — Save content to Obsidian vault (markdown-only)
  sync-claude-sessions/
    SKILL.md                             — Session export skill
    scripts/update-title.py              — Title update script
    scripts/backfill-daily.py            — Backfill sessions into Obsidian daily notes
    scripts/claude-sessions              — Main sync script
    schema/tags.yaml                     — Tag schema
    workflows/setup.md                   — Setup guide
    workflows/log-session.md             — Session logging workflow
  shared_utils.py                        — Shared Python utilities across skills
hooks/
  index-sessions.sh                      — SessionEnd hook for ir auto-indexing
```

## Installation

Skills are installed by copying to `~/.claude/skills/`. Symlink recommended for development:

```bash
ln -s "$(pwd)/skills/"* ~/.claude/skills/
```

## Skill Types

| Type | Example | Contains |
|------|---------|----------|
| Markdown-only | ideate, save-doc | `SKILL.md` only |
| Script-based | recall, sync-claude-sessions | `SKILL.md` + `scripts/` + `workflows/` |

## CLI Commands

All scripts are invoked from their installed path: `. ~/.claude/env && python ~/.claude/skills/<skill>/scripts/<script>`

- `claude-sessions {sync|export|resume|note|close|list|log}` — session management (`sync --daily-append` appends to Obsidian daily note)
- `backfill-daily.py [--dry-run] [--date YYYY-MM-DD]` — backfill sessions into Obsidian daily notes
- `recall-day.py` — date-based temporal recall
- `session-graph.py` — graph visualization (needs `networkx`, `pyvis`)
- Recall modes: temporal / project / topic (BM25 via `ir`, Obsidian search fallback) / graph

## Skill Conventions

- Each skill lives in `skills/<name>/SKILL.md`
- Frontmatter: `name` and `description` only (max 1024 chars total)
- `description` starts with "Use when..." — trigger conditions only, no workflow summary
- Scripts go in `skills/<name>/scripts/`
- Keep skills under 500 words for token efficiency

## Environment

Skills depend on `~/.claude/env` for vault paths:
- `VAULT_DIR` — Obsidian vault root
- `VAULT_SESSIONS_DIR` — Session markdown output
- `DOCS_DIR` — Document output for save-doc
- `CLAUDE_SESSIONS_TZ` — Timezone for session timestamps (default: `Asia/Seoul`)
- `MACHINE_NAME` — Machine identifier in session frontmatter
- `OBSIDIAN_CLI` — Path to Obsidian desktop CLI (enables `--daily-append` in sync)

## Python Scripts

- Use `shared_utils.py` for common utilities
- Scripts are invoked via `. ~/.claude/env && python ~/.claude/skills/<name>/scripts/<script>`
- Python 3.10+ required

## Hooks

- **UserPromptSubmit**: `claude-sessions sync` (10s timeout) — live session sync
- **Stop**: `claude-sessions sync --daily-append` (15s timeout, async) — final sync + daily note append
- **SessionEnd**: `index-sessions.sh` (5s timeout) — ir index update if available

## Obsidian Integration

- **Daily Notes**: Stop hook appends session summary to `Daily Notes/YYYY-MM-DD.md` under `## Claude Sessions` section
- **Obsidian Search**: Recall topic queries fall back to `$OBSIDIAN_CLI search` when ir is unavailable or results are sparse
- **Properties**: save-doc can set Obsidian properties via `$OBSIDIAN_CLI property:set` after saving
- **Sessions Dashboard**: `sessions-dashboard.base` in Claude-Sessions folder provides database views (All / Active / By Project)

## Gotchas

- **`docs/` is gitignored**: `docs/superpowers/`, `docs/specs/`, `docs/plans/` are local superpowers artifacts, not tracked.
- **Sync hook timeout**: `UserPromptSubmit` + `Stop` hooks run `claude-sessions sync`. Lindera-tokenize calls are batched (commit `af7a5cf`) — don't reintroduce per-file subprocess loops.
- **ir is optional but indexed via SessionEnd hook**: `hooks/index-sessions.sh` runs `ir update` only if `ir` is on PATH. Topic recall falls back to Obsidian search, then temporal mode.
- **Daily note format**: `_daily_append()` writes directly to filesystem (not via Obsidian CLI) under `## Claude Sessions` heading. Same format as `backfill-daily.py`.
- **No test suite**: unit tests were removed (commit `ac22317`) — verify changes by running the scripts directly against a live vault.
