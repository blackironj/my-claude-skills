---
name: save-doc
description: Use when user asks to save, export, or store session content (analysis results, benchmarks, specs, designs) to their Obsidian vault. Also when the user wants a handoff for the next session. Triggers on "저장해줘", "vault에 넣어줘", "정리해서 저장", "save this", "export to vault", "/save-doc", "핸드오프", "handoff", "다음 세션에서 이어서", "세션 정리해서 기록".
---

# Save Doc

Save session content to the Obsidian vault workspace as structured markdown.

## Step 1: Identify Content

Determine what to save from the session: analysis or benchmark results, designs and specs,
investigation findings, or other structured output the user wants kept. If unclear, ask: "어떤 내용을 저장할까요?"

**Handoff:** if the user asks for a handoff, or to record where to pick up next session, read
[handoff.md](handoff.md) and follow it alongside the steps below.

## Step 2: Infer Save Path

**Base directory:** `$DOCS_DIR/`

Run the ranking script from the session's working directory:

```bash
. ~/.claude/env && python3 ~/.claude/skills/save-doc/scripts/suggest-path.py
```

It matches the current repo against each folder's `project:` frontmatter and path names, and
prints ranked candidates (with recent filenames), the full folder map, or a proposed new folder.

**Choose the folder — the script ranks by repo, you decide by content:**

1. **Content is about the current repo** — take the top candidate. When several sibling
   subfolders tie (e.g. `cochl/SDK/<topic>/`), the parent is the project folder: pick the
   sibling whose recent filenames share the topic, or propose a new `<parent>/<topic-slug>/`
2. **Content is about another project** (the session ran elsewhere) — ignore the ranking and
   pick from the folder map by project and topic
3. **No candidate** — use the proposed new folder, or a new topic subfolder under the closest
   existing project folder; say it is new in Step 3
4. Read one recent doc in the chosen folder to match its style before writing

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

When the folder is new, add a line such as `새 폴더: cochl/payment-v2/ (기존 매칭 없음)`.

Wait for confirmation; use a different path if the user gives one.

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
- Frontmatter is required, as above. **`tags` MUST be a YAML list, one tag per line**:
  `tags: a,b,c` parses as one string that Obsidian shows as a single invalid tag. Tag
  characters are letters, digits, `_`, `-`, `/`, and a tag cannot be all digits

Resolve the full path first, then save with the Write tool:

```bash
. ~/.claude/env && mkdir -p "$DOCS_DIR/PARENT_DIR" && echo "$DOCS_DIR/PATH"
```

Then use the Write tool to create the file at the resolved absolute path.

## Step 5: Confirm Save

After saving, report:

```
저장 완료: workspace/cochl/security/benchmark/2026-03-20-onnx-vs-trt-cosine.md
```
