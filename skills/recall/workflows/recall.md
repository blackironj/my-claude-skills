# Recall Workflow

Load context from vault memory - temporal queries use native JSONL files, topic queries use QMD search.

## Step 1: Classify Query

Parse the user's input after `/recall` and classify:

- **Graph** - starts with "graph": "graph last week", "graph yesterday", "graph today"
  -> Go to Step 2C
- **Temporal** - mentions time: "yesterday", "today", "last week", "this week", a date, "what was I doing", "session history"
  -> Go to Step 2A
- **Topic** - mentions a subject: "QMD video", "authentication", "lab content"
  -> Go to Step 2B
- **Both** - temporal + topic: "what did I do with QMD yesterday"
  -> Go to Step 2A first, then scan results for the topic

## Step 2A: Temporal Recall (Obsidian First, then Local JSONL)

Obsidian sessions include work from ALL computers (synced), so check there first. Local JSONL catches any unsynced sessions.

### Step 2A.1: Scan Obsidian Sessions by Date (Primary)

Convert DATE_EXPR to date pattern(s) (YYYY-MM-DD), then list matching session files:

```bash
. ~/.claude/env && ls "$VAULT_DIR/Claude-Sessions/"DATE_PATTERN-* 2>/dev/null
```

Examples:
- `yesterday` (2026-03-16) → `ls "$VAULT_DIR/Claude-Sessions/"2026-03-16-*`
- `this week` → `ls "$VAULT_DIR/Claude-Sessions/"2026-03-{10,11,12,13,14,15,16,17}-*` (expand to each date in range)
- `last week` → similar expansion for the prior week's dates
- `2026-03-15` → `ls "$VAULT_DIR/Claude-Sessions/"2026-03-15-*`

For each matched file, read the YAML frontmatter to extract: date, title, messages count, skills, tags, status, projects.

Present as a table:
| # | Time | Session ID | Title | Msgs | Skills/Tags |
|---|------|-----------|-------|------|-------------|

### Step 2A.2: Scan Local JSONL (Supplementary)

Also run the local script to catch unsynced sessions:

```bash
python3 ~/.claude/skills/recall/scripts/recall-day.py list DATE_EXPR
```

Replace `DATE_EXPR` with the parsed date expression. Supported:
- `yesterday`, `today`
- `YYYY-MM-DD`
- `last monday` .. `last sunday`
- `this week`, `last week`
- `N days ago`, `last N days`

Options:
- `--min-msgs N` - filter noise (default: 3)
- `--project PATH` - limit to a specific project (default: scans all projects)

### Step 2A.3: Merge & Deduplicate

Match sessions by the 8-char session ID prefix. If a session appears in both Obsidian and local JSONL, prefer the Obsidian version (richer metadata). Show any local-only sessions separately marked as "(unsynced)".

### Step 2A.4: Expand a Session

If the user picks a session to expand, offer two depth levels:

**Quick expand** — conversation timeline (user messages, assistant first lines, tool calls):

```bash
python3 ~/.claude/skills/recall/scripts/recall-day.py expand SESSION_ID
```

Options:
- `--max-msgs N` - limit messages shown (default: 50)
- `--project PATH` - limit to a specific project
- `--all-projects` - scan all projects

**IMPORTANT: These are the ONLY supported flags. Do NOT invent flags like `--summary`. Do NOT suppress stderr with `2>/dev/null`.**

**Deep context** — read the full synced session markdown from Obsidian vault:

```bash
. ~/.claude/env && ls "$VAULT_DIR/Claude-Sessions/"*SESSION_ID_PREFIX*
# Then Read the matched file
```

The Claude-Sessions markdown contains the full conversation, artifacts (created/modified files), and metadata. Use this when the user wants to resume or deeply understand a past session. Match by the 8-char session ID prefix from the list output.

If user says "컨텍스트 줘", "이어서 하고 싶어", "resume", or wants to continue past work → use deep context.
If user just wants to browse what happened → use quick expand.

## Step 2B: Topic Recall (QMD BM25 with Query Expansion)

BM25 is keyword-based - it only finds exact word matches. The user's recall of a topic often uses different words than the session itself (e.g. "disk clean up" vs "large files on computer"). Fix: expand the query into 3-4 keyword variants covering synonyms and related phrasings.

**Step 2B.1: Expand query into variants.** Generate 3-4 alternative phrasings that someone might use for the same topic. Think: what other words describe this?

**Korean queries:** QMD's BM25 tokenizer (`porter unicode61`) cannot segment Korean text. If the user's query is in Korean, translate it to English keywords before searching. Include both English variants and any English terms that appeared in the original Korean query. Example:
- User says "디스크 정리" -> variants: `"disk cleanup free space"`, `"large files storage"`, `"delete cache bloat"`
- User says "인증 작업" -> variants: `"authentication"`, `"auth login token"`, `"credential session"`

English example:
- User says "disk clean up" -> variants: `"disk cleanup free space"`, `"large files storage"`, `"delete cache bloat GB"`, `"free up computer space"`

**Step 2B.2: Run ALL variants across ALL collections in parallel** (fast, ~0.3s each):

```bash
qmd search "VARIANT_1" -c sessions -n 5
qmd search "VARIANT_2" -c sessions -n 5
qmd search "VARIANT_3" -c sessions -n 5
qmd search "VARIANT_1" -c notes -n 5
qmd search "VARIANT_2" -c notes -n 5
qmd search "VARIANT_1" -c daily -n 3
```

Run sessions variants in parallel. Notes/daily can use fewer variants (prioritize sessions for recall).

**Step 2B.3: Deduplicate results** by document path. If same doc appears in multiple searches, keep the highest score. Present top 5 unique results.

## Step 3: Fetch Full Documents (Topic path only)

For the top 3 most relevant results across all collections, get the full document:

```bash
qmd get "qmd://collection/path/to/file.md" -l 50
```

Use the paths returned from Step 2B searches. The `-l 50` flag limits to 50 lines (adjust if needed for very large files).

## Step 4: Present Results (Speed First)

**IMPORTANT: Minimize LLM processing. Show script output directly, don't reformat into tables.**

**For temporal queries:**
1. Show the script output as-is (it's already a formatted table)
2. Add one line: "번호 선택 → 타임라인 / 깊은 컨텍스트 로딩 가능"
3. Add One Thing (one sentence, see below)

That's it. Do NOT re-create the table in markdown, summarize each session, or add commentary.

**For topic queries:** Show QMD search results directly, then briefly note top 3 matches with file paths.

## Step 5: One Thing (One Sentence)

Append one bold sentence based on what has momentum or is closest to done. Skip if not enough signal.

> **One Thing: [specific action]**

Do NOT explain reasoning, list criteria, or provide multiple options.

## Fallback: No Results Found

If no results are found:

```
No results found for "QUERY". Try:
- Different search terms
- Broader keywords / different date range
- --min-msgs 1 to include short sessions
```

## Step 2C: Graph Visualization

Strip "graph" prefix from query to get the date expression. Run:

```bash
python3 ~/.claude/skills/recall/scripts/session-graph.py DATE_EXPR
```

Options:
- `--min-files N` - only show sessions touching N+ files (default: 2, use 5+ for cleaner graphs)
- `--min-msgs N` - filter noise (default: 3)
- `--project PATH` - limit to a specific project (default: all)
- `-o PATH` - custom output path (default: /tmp/session-graph.html)
- `--no-open` - don't auto-open browser

Opens interactive HTML in browser. Session nodes colored by day, file nodes colored by folder.
Tell the user the node/edge counts and what to look for (clusters, shared files).

## CLI Reference (Exact Supported Flags)

**Do NOT invent or guess flags. Only use flags listed below.**

### `recall-day.py list DATE_EXPR`
| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--min-msgs N` | int | 3 | Filter noise by minimum user messages |
| `--project PATH` | str | (all) | Limit to specific project path |
| `--all-projects` | flag | false | Scan all projects |

### `recall-day.py expand SESSION_ID`
| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--max-msgs N` | int | 50 | Maximum messages to display |
| `--project PATH` | str | (all) | Limit to specific project path |
| `--all-projects` | flag | false | Scan all projects |

### `session-graph.py DATE_EXPR`
| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--min-files N` | int | 2 | Only show sessions touching N+ files |
| `--min-msgs N` | int | 3 | Filter noise |
| `--project PATH` | str | (all) | Limit to specific project |
| `-o PATH` | str | /tmp/session-graph.html | Custom output path |
| `--no-open` | flag | false | Don't auto-open browser |

## Notes

- Temporal queries check Obsidian Claude-Sessions first (includes all synced computers), then local JSONL for unsynced sessions
- Graph queries go through `session-graph.py` (NetworkX + pyvis)
- Topic queries use BM25 (`qmd search`) NOT hybrid (`qmd query`) - 53x faster
- Run all 3 collection searches in parallel to keep response time fast
- If a result is truncated or you need more context, fetch with `-l 100` or higher
- **Never suppress stderr with `2>/dev/null`** — let argparse errors surface so you can see what's wrong
