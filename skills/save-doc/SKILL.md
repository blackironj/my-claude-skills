---
name: save-doc
description: Use when user asks to save, export, or store session content (analysis results, benchmarks, specs, designs) to their Obsidian vault. Triggers on "저장해줘", "vault에 넣어줘", "정리해서 저장", "save this", "export to vault", "/save-doc".
---

# Save Doc

Save session content to the Obsidian vault workspace as structured markdown.

## Step 1: Identify Content

Determine what to save from the current session:
- Analysis results, benchmark data, performance measurements
- Design documents, specs, architecture decisions
- Investigation findings, debugging conclusions
- Any structured output the user wants to persist

If unclear, ask: "어떤 내용을 저장할까요?"

## Step 2: Infer Save Path

**Base directory:** `$DOCS_DIR/`

Load env and scan existing structure:

```bash
. ~/.claude/env && find "$DOCS_DIR/" -maxdepth 4 -type d 2>/dev/null
```

Also scan existing files in the likely target folder to match their style:

```bash
. ~/.claude/env && ls "$DOCS_DIR/TARGET_FOLDER/" 2>/dev/null
```

**Path inference — scan existing structure, don't hardcode:**

1. **Scan folders and files** to understand the current organization
2. **Read a few existing files** in candidate folders to understand naming/grouping conventions
3. **Match by similarity** — find the folder whose existing docs are most related to the content being saved (same project domain, same type of output)
4. **If no folder fits**, propose a new one that follows the existing naming pattern
5. **If base directory is missing**, create it (`mkdir -p`)

**Filename:** `YYYY-MM-DD-short-descriptive-title.md` (lowercase, hyphens)
- Date-prefixed for chronological sorting
- Exception: timeless docs (runbooks, guides) skip the date prefix

## Step 3: Propose and Confirm

**ALWAYS confirm before saving. Never save without explicit approval.**

Present to user:

```
저장 경로: workspace/cochl/security/benchmark/2026-03-20-onnx-vs-trt-cosine.md
내용: ONNX vs TRT-FP16 cosine similarity 비교 결과 (120 파일, 114-dim)

이대로 저장할까요?
```

Wait for user confirmation. If user says different path, use that.

## Step 4: Format and Save

Follow the existing document pattern:

```markdown
---
date: YYYY-MM-DD
type: doc
project: PROJECT_NAME
tags:
  - one-per-line
  - kebab-case
---
# Title

**Date:** YYYY-MM-DD
**Key metadata fields relevant to content**

## Section headers matching content structure

Content organized with tables, code blocks as appropriate
```

**Formatting rules:**
- Match existing docs' style in the same folder
- Use tables for structured data (benchmarks, comparisons)
- Include environment/setup info when relevant
- Korean or English — match whatever the session used
- Frontmatter: `date`, `type: doc`, `project`, and `tags` — every existing doc has it
- **`tags` MUST be a YAML list, one tag per line.** `tags: a,b,c` parses as a single
  string, and Obsidian renders it as one invalid tag (commas and spaces are not legal
  tag characters) — it shows underlined in red. Legal characters are letters, digits,
  `_`, `-`, `/`; a tag cannot be all digits

Resolve the full path first, then save with the Write tool:

```bash
. ~/.claude/env && mkdir -p "$DOCS_DIR/PARENT_DIR" && echo "$DOCS_DIR/PATH"
```

Then use the Write tool to create the file at the resolved absolute path.

## Step 5: Set Obsidian Properties (if OBSIDIAN_CLI is available)

After writing the file, tag it with Obsidian properties for discoverability:

```bash
. ~/.claude/env && cd /mnt/c && "$OBSIDIAN_CLI" property:set name="type" value="doc" path="VAULT_RELATIVE_PATH"
. ~/.claude/env && cd /mnt/c && "$OBSIDIAN_CLI" property:set name="date" value="YYYY-MM-DD" path="VAULT_RELATIVE_PATH"
. ~/.claude/env && cd /mnt/c && "$OBSIDIAN_CLI" property:set name="project" value="PROJECT_NAME" path="VAULT_RELATIVE_PATH"
```

`VAULT_RELATIVE_PATH` = path relative to vault root (e.g., `workspace/cochl/benchmark/file.md`).
`PROJECT_NAME` = infer from folder structure or session context.

**Property rules:**
- `type`: always `doc`
- `date`: the document date (YYYY-MM-DD)
- `project`: project name if identifiable from path or context (skip if unclear)
- `tags`: content categories — only if clearly applicable. In the file itself these are a
  YAML list (see Step 4); the CLI takes them comma-separated and splits them itself

If `$OBSIDIAN_CLI` is not set or Obsidian is not running, skip this step silently.

## Step 6: Confirm Save

After saving, report:

```
저장 완료: workspace/cochl/security/benchmark/2026-03-20-onnx-vs-trt-cosine.md
```
