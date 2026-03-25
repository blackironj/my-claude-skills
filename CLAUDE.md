# my-claude-skills

Personal Claude Code skills for session memory, recall, and ideation with Obsidian integration.

## Structure

```
skills/
  ideate/           — Lightweight collaborative ideation skill
  recall/           — Session recall with temporal, topic, and graph modes
  save-doc/         — Save content to Obsidian vault
  sync-claude-sessions/ — Export sessions to Obsidian markdown
  shared_utils.py   — Shared Python utilities
hooks/              — SessionEnd hook for ir auto-indexing
docs/               — Spec and plan documents from superpowers workflows
```

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

## Installation

Skills in this repo are copied to `~/.claude/skills/` for use. After editing a skill here, copy it to the installed location to apply changes.

## Python Scripts

- Use `shared_utils.py` for common utilities
- Scripts are invoked via `. ~/.claude/env && python ~/.claude/skills/<name>/scripts/<script>`
- Python 3.10+ required
