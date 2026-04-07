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
ln -s ~/workspace/my/claude-code-skills/skills/* ~/.claude/skills/
```

## Skill Types

| Type | Example | Contains |
|------|---------|----------|
| Markdown-only | ideate, save-doc | `SKILL.md` only |
| Script-based | recall, sync-claude-sessions | `SKILL.md` + `scripts/` + `workflows/` |

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
- `MACHINE_NAME` — Machine identifier in session frontmatter

## Python Scripts

- Use `shared_utils.py` for common utilities
- Scripts are invoked via `. ~/.claude/env && python ~/.claude/skills/<name>/scripts/<script>`
- Python 3.10+ required

## Gotchas

- **`docs/` is gitignored**: `docs/superpowers/`, `docs/specs/`, `docs/plans/` are local superpowers artifacts, not tracked.
