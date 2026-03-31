---
name: recall
description: Load context from vault memory. Temporal queries (yesterday, last week, session history) use native JSONL timeline. Topic queries use ir BM25 search (with Korean tokenizer for CJK support). "recall graph" generates interactive temporal graph of sessions and files. Every recall ends with "One Thing" - the single highest-leverage next action synthesized from results. Use when user says "recall", "what did we work on", "load context about", "remember when we", "prime context", "yesterday", "what was I doing", "last week", "session history", "recall graph", "session graph".
argument-hint: [yesterday|today|last week|this week|TOPIC|graph DATE_EXPR|project NAME [DATE_EXPR]|projects]
allowed-tools: Bash(ir:*), Bash(python3:*)
---

# Recall Skill

Three modes: temporal (date-based session timeline), topic (BM25 search across ir collections), and graph (interactive visualization of session-file relationships). Every recall ends with the **One Thing** - a concrete, highest-leverage next action synthesized from the results.

## What It Does

- **Temporal queries** ("yesterday", "last week", "what was I doing"): Scans native Claude Code JSONL files by date. Shows a table of sessions with time, message count, and first message. Expand any session for conversation details.
- **Topic queries** ("authentication", "video work"): BM25 search across sessions in ir collections.
- **Graph queries** ("graph yesterday", "graph last week"): Generates an interactive HTML graph showing sessions as nodes connected to files they touched. Sessions colored by day, files colored by folder. Clusters reveal related work streams, shared files show cross-session dependencies.
- **Project queries** ("project triton", "project security last week"): Filters sessions by project name (substring match). Shows sessions from matching projects within a date range (default: last 14 days). Use `projects` subcommand to list all available projects.
- **One Thing synthesis**: After presenting results, synthesizes the single most impactful next action based on what has momentum, what's blocked, and what's closest to done. Not generic - specific and actionable.

No custom setup needed for temporal recall - every Claude Code user has JSONL files.

## Setup (for topic search)

Topic search requires [ir](https://github.com/vlwkaos/ir). If `ir` is not installed, topic queries will not work (temporal and graph still work).

```bash
# 1. Build ir from source (Rust 1.80+, libclang-dev, cmake)
cd ~/workspace
git clone https://github.com/vlwkaos/ir.git && cd ir
cargo install --path . --no-default-features --features llama-openmp  # Linux
# cargo install --path .  # macOS (Metal auto-detected)

# 2. Korean preprocessor (optional, for CJK search)
cd preprocessors/ko/lindera-tokenize  # Linux: build from source
cargo install --path .
ir preprocessor add ko lindera-tokenize
# macOS: ir preprocessor install ko

# 3. Register collection
ir collection add sessions "$VAULT_SESSIONS_DIR/"
ir preprocessor bind ko sessions  # skip if no ko preprocessor
ir update
```

ir is installed per machine. The Obsidian vault syncs across PCs; ir index is local.

## Auto-Indexing (Optional)

You can auto-index sessions into ir on every session end via a Claude Code hook. See AGENTS.md for setup instructions.

## Usage

```
/recall yesterday
/recall last week
/recall 2026-02-25
/recall video work
/recall authentication work
```

**Graph mode** - visualize session relationships over time:
```
/recall graph yesterday        # what you touched today
/recall graph last week        # week overview - find clusters
/recall graph this week        # current week so far
/recall graph last 3 days      # recent activity window
```

Graph options: `--min-files 5` for cleaner graphs (only sessions touching 5+ files), `--all-projects` to scan beyond current vault.

**Project mode** - filter sessions by project:
```
/recall project triton yesterday       # triton* sessions from yesterday
/recall project security last week     # security* sessions from last week
/recall project triton                 # default: last 14 days
```

List available projects:
```
/recall projects
```

## Commands (MUST use these scripts - do NOT craft raw bash commands)

**Temporal** (date queries → recall-day.py):
```bash
python3 ~/.claude/skills/recall/scripts/recall-day.py list DATE_EXPR
python3 ~/.claude/skills/recall/scripts/recall-day.py expand SESSION_ID
```

**Topic** (keyword queries → ir search with query expansion):
```bash
ir search "VARIANT_1" -c sessions -n 5 --mode bm25 --md
ir search "VARIANT_2" -c sessions -n 5 --mode bm25 --md
# Document fetch: use Read tool on file paths from search results
```

**Graph** (strip "graph" prefix, pass rest as DATE_EXPR):
```bash
python3 ~/.claude/skills/recall/scripts/session-graph.py DATE_EXPR
```

**Project** (project queries → recall-day.py with --name):
```bash
python3 ~/.claude/skills/recall/scripts/recall-day.py projects
python3 ~/.claude/skills/recall/scripts/recall-day.py list DATE_EXPR --name PROJECT_NAME
```

## Workflow

See `workflows/recall.md` for full routing logic, query classification, and presentation rules.
