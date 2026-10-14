---
name: recall
description: Use when the user wants past Claude Code session context loaded from the vault, by date, topic, or project, or wants to resume work from an earlier session's handoff. Triggers on "recall", "what did we work on", "load context about", "remember when we", "prime context", "yesterday", "what was I doing", "last week", "session history", "어제 뭐 했지", "지난주 작업", "이전 세션", "그때 그 작업", "핸드오프 읽고 이어서", "지난 세션 이어서", "이어서 할 거 뭐 있지".
argument-hint: [yesterday|today|last week|this week|TOPIC|project NAME [DATE_EXPR]|projects|handoff [NAME]]
allowed-tools: Bash(ir:*), Bash(python3:*)
---

# Recall

Every command needs `. ~/.claude/env &&` first. Use only the flags shown here; do not add `2>/dev/null`.
`R` below is `python3 ~/.claude/skills/recall/scripts/recall-day.py`.

## 1. Route the query

| Query | Mode |
|---|---|
| Date only: "yesterday", "last week", "2026-09-30" | Temporal |
| Subject: "inspector", "인증 작업" | Topic |
| Subject + date or project: "auth last week", "auth in triton" | Topic with filters |
| "project NAME [DATE_EXPR]", "projects" | Project |
| Resuming earlier work: "handoff", "spec-auth 이어서 할 거 뭐 있지" | Handoff |

## 2. Run it

**Temporal** — `R list DATE_EXPR [--min-msgs N]` (default 3). DATE_EXPR: `today`, `yesterday`,
`YYYY-MM-DD`, `N days ago`, `last N days`, `this week`, `last week`, `last monday`…`last sunday`.

**Project** — `R list [DATE_EXPR] --name NAME` (default last 14 days; `--full-history` for all).
`R projects` lists project names when the user's name doesn't match.

**Expand a session** — `R expand ID8 [--max-msgs N]` prints its synced markdown (artifacts,
notes, conversation). To resume or study it deeply, Read the path on its `File:` line in full.

**Topic** — BM25 only matches exact words, so write 3-4 variants in the query's language and in
English (sessions mix both), e.g. "디스크 정리" → `"디스크 정리 용량"`, `"disk cleanup free space"`,
`"대용량 파일 삭제"`. Run them in parallel, dedupe by path, keep the top 5, Read the top 3:
```bash
ir search "VARIANT" -c sessions -n 5 --mode bm25 --md [-f "meta.projects~NAME"] [-f "meta.date>=YYYY-MM-DD"]
```
If ir is missing, returns under 3 hits, or the target is non-session notes, also search the whole
vault (Korean and English query; paths are relative to `$VAULT_DIR`):
```bash
cd /mnt/c && "$OBSIDIAN_CLI" search query="QUERY" limit=10
```

**Handoff** — `R handoffs [--name NAME] [--limit N]` lists save-doc session handoffs, newest
first. Read the newest match in full, then report its 지금 상태 briefly and its 다음 할 일 as the plan.
Start with item 1 of 다음 할 일 (usually syncing repos) unless the user only asked what is left.
If nothing matches, fall back to Project mode for the same name.

## 3. Present

- Temporal / Project: show the script table as-is (no re-tabulating, no per-session summaries),
  then one line: "번호 선택 → 타임라인 / 깊은 컨텍스트 로딩 가능"
- Topic: the search results, then the top 3 matches with file paths
- No results: suggest other terms, a wider date range, or `--min-msgs 1`

End with one bold sentence, skipped when there is too little signal; no reasoning, no alternatives:

> **One Thing: [the single next action with the most momentum or closest to done]**

ir setup and auto-indexing: see the repo README.
