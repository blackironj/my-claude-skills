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

**Base directory:** `$VAULT_DIR/workspace/`

Load env and scan existing structure:

```bash
. ~/.claude/env && find "$VAULT_DIR/workspace/" -maxdepth 4 -type d 2>/dev/null
```

Also scan existing files in the likely target folder to match their style:

```bash
. ~/.claude/env && ls "$VAULT_DIR/workspace/TARGET_FOLDER/" 2>/dev/null
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
- No Obsidian frontmatter needed (plain markdown)

Resolve the full path first, then save with the Write tool:

```bash
. ~/.claude/env && mkdir -p "$VAULT_DIR/workspace/PARENT_DIR" && echo "$VAULT_DIR/workspace/PATH"
```

Then use the Write tool to create the file at the resolved absolute path.

## Step 5: Confirm Save

After saving, report:

```
저장 완료: workspace/cochl/security/benchmark/2026-03-20-onnx-vs-trt-cosine.md
```
