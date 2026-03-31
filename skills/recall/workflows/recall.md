# Recall Workflow

Load context from vault memory - temporal queries use native JSONL files, topic queries use ir search.

## Step 1: Classify Query

Parse the user's input after `/recall` and classify:

- **Graph** - starts with "graph": "graph last week", "graph yesterday", "graph today"
  -> Go to Step 2C
- **Temporal** - mentions time: "yesterday", "today", "last week", "this week", a date, "what was I doing", "session history"
  -> Go to Step 2A
- **Topic** - mentions a subject: "recall system", "authentication", "lab content"
  -> Go to Step 2B
- **Project** - starts with "project": "project triton yesterday", "project security last week"
  -> Go to Step 2D
- **Both** - temporal + topic: "what did I do with auth yesterday"
  -> Go to Step 2A first, then scan results for the topic

## Step 2A: Temporal Recall

The script automatically scans both local JSONL and Obsidian (if `VAULT_DIR` is set). Local sessions come first; Obsidian adds remote sessions from other computers. Deduplication by session ID is built-in.

**IMPORTANT: Always prefix with `. ~/.claude/env &&` to inject `VAULT_DIR`.**

### Step 2A.1: List Sessions

```bash
. ~/.claude/env && python3 ~/.claude/skills/recall/scripts/recall-day.py list DATE_EXPR
```

Supported DATE_EXPR: `yesterday`, `today`, `YYYY-MM-DD`, `last monday`..`last sunday`, `this week`, `last week`, `N days ago`, `last N days`

Options:
- `--min-msgs N` - filter noise (default: 3)
- `--project PATH` - limit to a specific project (default: scans all projects)

### Step 2A.2: Expand a Session

If the user picks a session to expand, offer two depth levels:

**Quick expand** — conversation timeline (user messages, assistant first lines, tool calls):

```bash
. ~/.claude/env && python3 ~/.claude/skills/recall/scripts/recall-day.py expand SESSION_ID
```

Options:
- `--max-msgs N` - limit messages shown (default: 50)
- `--project PATH` - limit to a specific project
- `--all-projects` - scan all projects

**IMPORTANT: These are the ONLY supported flags. Do NOT invent flags like `--summary`. Do NOT suppress stderr with `2>/dev/null`.**

For remote sessions (no local JSONL), expand automatically falls back to Obsidian markdown content.

**Deep context** — read the full synced session markdown from Obsidian vault:

```bash
. ~/.claude/env && ls "$VAULT_SESSIONS_DIR/"*SESSION_ID_PREFIX*
# Then Read the matched file
```

The Claude-Sessions markdown contains the full conversation, artifacts (created/modified files), and metadata. Use this when the user wants to resume or deeply understand a past session. Match by the 8-char session ID prefix from the list output.

If user says "컨텍스트 줘", "이어서 하고 싶어", "resume", or wants to continue past work → use deep context.
If user just wants to browse what happened → use quick expand.

## Step 2B: Topic Recall (ir BM25 with Korean Support)

BM25 is keyword-based - it only finds exact word matches. The user's recall of a topic often uses different words than the session itself. Fix: expand the query into 3-4 keyword variants covering synonyms and related phrasings.

**Step 2B.1: Expand query into variants.** Generate 3-4 alternative phrasings that someone might use for the same topic. Think: what other words describe this?

**Bilingual queries:** ir's Korean preprocessor handles Korean tokenization natively. For ALL queries, generate variants in both the query's original language and English. Sessions are Korean-English mixed, so bilingual variants maximize recall.

- Korean query example: "디스크 정리" → `"디스크 정리 용량"`, `"disk cleanup free space"`, `"대용량 파일 삭제"`
- English query example: "disk cleanup" → `"disk cleanup free space"`, `"디스크 정리"`, `"large files storage"`, `"delete cache bloat GB"`

**Step 2B.2: Run ALL variants in parallel** (fast, ~0.3s each):

```bash
ir search "VARIANT_1" -c sessions -n 5 --mode bm25 --md
ir search "VARIANT_2" -c sessions -n 5 --mode bm25 --md
ir search "VARIANT_3" -c sessions -n 5 --mode bm25 --md
```

Run all variants in parallel for fast response.

**Step 2B.3: Deduplicate results** by document path. If same doc appears in multiple searches, keep the highest score. Present top 5 unique results.

**Project filter:** If the user specifies both a topic and a project (e.g., "recall auth in triton"), run `ir search` normally, then filter results by reading the frontmatter `projects` field of matched files. Only present results where the project name matches.

## Step 3: Fetch Full Documents (Topic path only)

For the top 3 most relevant results, read the files directly using the Read tool. File paths are included in `ir search --md` output. No separate fetch command needed — the files are local markdown in the Obsidian vault.

If you need the path programmatically, use `ir search --json` which returns structured output with document paths.

## Step 4: Present Results (Speed First)

**IMPORTANT: Minimize LLM processing. Show script output directly, don't reformat into tables.**

**For temporal queries:**
1. Show the script output as-is (it's already a formatted table)
2. Add one line: "번호 선택 → 타임라인 / 깊은 컨텍스트 로딩 가능"
3. Add One Thing (one sentence, see below)

That's it. Do NOT re-create the table in markdown, summarize each session, or add commentary.

**For topic queries:** Show search results directly, then briefly note top 3 matches with file paths.

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
. ~/.claude/env && python3 ~/.claude/skills/recall/scripts/session-graph.py DATE_EXPR
```

Options:
- `--min-files N` - only show sessions touching N+ files (default: 2, use 5+ for cleaner graphs)
- `--min-msgs N` - filter noise (default: 3)
- `--project PATH` - limit to a specific project (default: all)
- `-o PATH` - custom output path (default: /tmp/session-graph.html)
- `--no-open` - don't auto-open browser

Opens interactive HTML in browser. Session nodes colored by day, file nodes colored by folder.
Tell the user the node/edge counts and what to look for (clusters, shared files).

## Step 2D: Project Recall

Recall sessions filtered by project name.

### Step 2D.1: Parse project query

Strip "project" prefix. First word = project name, remaining = date expression.
If no date expression, default to "last 14 days".

To see available projects:
```bash
. ~/.claude/env && python3 ~/.claude/skills/recall/scripts/recall-day.py projects
```

### Step 2D.2: List project sessions

```bash
. ~/.claude/env && python3 ~/.claude/skills/recall/scripts/recall-day.py list DATE_EXPR --name PROJECT_NAME
```

For full history (no date limit):
```bash
. ~/.claude/env && python3 ~/.claude/skills/recall/scripts/recall-day.py list --name PROJECT_NAME --full-history
```

### Step 2D.3: Present results

Same as Step 4 (temporal). Show script output as-is, add expand option, add One Thing.

## CLI Reference (Exact Supported Flags)

**Do NOT invent or guess flags. Only use flags listed below.**

**All commands MUST be prefixed with `. ~/.claude/env &&`**

### `recall-day.py projects`
No flags. Lists all projects with session counts.

### `recall-day.py list DATE_EXPR`
| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--min-msgs N` | int | 3 | Filter noise by minimum user messages |
| `--project PATH` | str | (all) | Limit to specific project path |
| `--all-projects` | flag | false | Scan all projects |
| `--name NAME` | str | (all) | Filter by project name (substring match) |
| `--full-history` | flag | false | Show full history (no date limit, use with --name) |

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

- **Always prefix commands with `. ~/.claude/env &&`** — this injects `VAULT_DIR`, `VAULT_SESSIONS_DIR` for Obsidian access
- `recall-day.py` scans local JSONL first, then Obsidian for remote sessions (auto-dedup by session ID)
- Graph queries go through `session-graph.py` (NetworkX + pyvis)
- Topic queries use BM25 (`ir search --mode bm25`) - fast keyword search with Korean support
- Run all search variants in parallel to keep response time fast
- If a result is truncated or you need more context, Read the full file from the Obsidian vault
- **Never suppress stderr with `2>/dev/null`** — let argparse errors surface so you can see what's wrong
