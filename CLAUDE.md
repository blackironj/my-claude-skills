# my-claude-skills

Personal Claude Code skills for session memory, recall, and ideation with Obsidian integration.

## Structure

```
skills/
  ideate/SKILL.md                        — Lightweight collaborative ideation (markdown-only)
  recall/
    SKILL.md                             — Session recall skill
    scripts/recall-day.py                — Temporal/project recall from the vault session archive
    scripts/common.py                    — Shared recall utilities
  save-doc/
    SKILL.md                             — Save content to Obsidian vault
    handoff.md                           — Session handoff mode: <folder>/_session-handoff/ + resume prompt
    scripts/suggest-path.py              — Rank $DOCS_DIR folders for the current repo
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
  fluent-korean-subagent.py              — PreToolUse(Agent) hook: append fluent-korean rules to Korean subagent prompts
```

## Installation

Skills are installed by copying to `~/.claude/skills/`. Symlink recommended for development:

```bash
ln -s "$(pwd)/skills/"* ~/.claude/skills/
```

## Skill Types

| Type | Example | Contains |
|------|---------|----------|
| Markdown-only | ideate | `SKILL.md` only |
| Script-based | recall, save-doc, sync-claude-sessions | `SKILL.md` + `scripts/` (+ `workflows/` or reference `.md`) |

## CLI Commands

All scripts are invoked from their installed path: `. ~/.claude/env && python ~/.claude/skills/<skill>/scripts/<script>`

- `claude-sessions {sync|export|resume|note|close|list|log}` — session management (`sync --daily-append` appends to Obsidian daily note)
- `backfill-daily.py [--dry-run] [--date YYYY-MM-DD]` — backfill sessions into Obsidian daily notes
- `recall-day.py {list|expand|projects|handoffs}` — date/project recall from `$VAULT_SESSIONS_DIR` (recursive, includes `YYYY/MM/` archives); `handoffs` lists `$DOCS_DIR/**/_session-handoff/`
- `suggest-path.py [--cwd PATH]` — rank `$DOCS_DIR` folders as save-doc targets for the current repo
- Recall modes: temporal / project / topic (BM25 via `ir`, Obsidian search fallback) / handoff

## Skill Conventions

- Each skill lives in `skills/<name>/SKILL.md`
- Frontmatter: `name`, `description` required; optional fields: `argument-hint`, `allowed-tools`, `when_to_use`, `disable-model-invocation`, `user-invocable`, `model`, `effort`, `context`, `agent`, `hooks`, `paths`, `shell`
- `description` + `when_to_use` combined: max 1536 chars (truncated by Claude Code for context budget)
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

- **Stop**: `claude-sessions sync --daily-append` (30s timeout, async) — session sync + daily note append after every response
- **SessionEnd**: `index-sessions.sh` (5s timeout, backgrounded) — final sync for an interrupted last turn, then ir index update if available. The hook JSON is piped in explicitly because `&` detaches stdin
- **PreToolUse** (matcher `Agent`): `fluent-korean-subagent.py` (5s timeout) — when the subagent prompt is mostly Hangul, returns `updatedInput` with the body of `~/.claude/output-styles/fluent-korean.md` appended. Output styles never reach subagents; this hook is the only way the rules do. Fails open (exit 0, no output) on any error.

## Obsidian Integration

- **Daily Notes**: Stop hook appends session summary to `Daily Notes/YYYY-MM-DD.md` under `## Claude Sessions` section
- **Obsidian Search**: Recall topic queries fall back to `$OBSIDIAN_CLI search` when ir is unavailable or results are sparse
- **Properties**: save-doc writes Obsidian properties as YAML frontmatter (`tags` must be a list)
- **Sessions Dashboard**: `sessions-dashboard.base` in Claude-Sessions folder provides database views (All / Active / By Project)

## Gotchas

- **`docs/` is gitignored**: `docs/superpowers/`, `docs/specs/`, `docs/plans/` are local superpowers artifacts, not tracked.
- **Sync must not scan the vault**: `claude-sessions sync` runs after every response, and the vault (`/mnt/c` under WSL, slow) grows by ~100 notes a month. Keep per-sync work bounded by the current session; get vault-wide data from the ir index instead of re-reading notes. A vault-wide TF-IDF keyword pass was removed for this reason.
- **ir is optional but indexed via SessionEnd hook**: `hooks/index-sessions.sh` runs `ir update` only if `ir` is on PATH. Topic recall falls back to Obsidian search, then temporal mode.
- **Daily note format**: `_daily_append()` writes directly to filesystem (not via Obsidian CLI) under `## Claude Sessions` heading. Same format as `backfill-daily.py`. Multi-project days are grouped by project.
- **Session classification**: `session_type` frontmatter field auto-classifies as `interactive` or `automated` (regex on first user message).
- **No test suite**: unit tests were removed (commit `ac22317`) — verify changes by running the scripts directly against a live vault.

## Roadmap

- **Wiki layer**: Distill repeated session topics into consolidated `wiki/` docs (3-phase: takeaways → topic pages → auto-update). Inspired by Karpathy's llm-wiki pattern. See memory for detailed roadmap.
