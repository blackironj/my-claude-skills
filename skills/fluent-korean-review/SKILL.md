---
name: fluent-korean-review
description: Use when the user wants existing Korean prose checked or corrected against the fluent-korean rules (dropped particles and endings, sentences ending in noun phrases or connective endings, metaphor swapped for plain vocabulary, em dashes) in a document, note, spec, README, or pasted text. Triggers on "/fluent-korean-review", "fluent-korean 규칙으로 검토", "한국어 문장 점검해줘", "조사 빠진 데 고쳐줘", "명사구로 끝나는 문장 고쳐줘", "이 문서 한국어 다듬어줘", and when the user asks to review the Korean of a long document Claude just wrote. Not for AI-tell removal, 번역투, or spelling (im-not-ai, korean-skills), and not for code, comments, or commit messages.
argument-hint: [FILE_PATH | 텍스트]
---

# Fluent Korean Review

Apply the fluent-korean output-style rules to Korean prose that already exists. The output style shapes replies as they are written; this skill catches what slipped through in documents.

## 1. Load the rules in full

Read `~/.claude/output-styles/fluent-korean.md` (fallback: `~/workspace/my/fluent-korean/plugins/fluent-korean/output-styles/fluent-korean.md`). If neither exists, stop and tell the user.

Work from the whole file. Do not paraphrase the rules: each clause carries the examples that show what it means, and a summary turns the review into keyword matching (the file says so itself in 상황과 목표).

Which sections apply to a document:
- 문장 단위 and 구 단위 are the checks.
- 동작 범위 says what to leave alone: code-like text, proper nouns and terms with an established translation or transliteration, foreign words that belong.
- 응답 단위 and 추가 사항 govern live replies and subagent prompts. Skip them; a document may legitimately open with context and close with a summary.

## 2. Resolve the input

- The argument is an existing path: file mode.
- Otherwise: text mode. Review the argument text, or the Korean text in the user's message.

Out of scope in both modes: frontmatter, code blocks, inline code, URLs, identifiers, direct quotations. Headers, list items, and table cells are exempt from the complete-sentence rule (문장 단위 2) but not from the other rules.

## 3. Review

Work paragraph by paragraph. For each violation record the location, the original span, the fix, and the clause (for example 구 단위 1). Fix only that span.

Keep the document's register and tense: a text in 해라체 stays in 해라체 even though the rule file's examples use 합쇼체. Facts, numbers, proper nouns, terms, and quotations stay exactly as written; if a fix would change what a sentence claims, leave it and note it in the report. Do not restyle prose the rules do not cover. This is a rules check, not a rewrite.

## 4. Apply

File mode:
1. Keep a copy of the original: `orig=$(mktemp) && cp <file> "$orig"`.
2. Apply each fix with Edit.
3. Run the change-rate gate: `python3 ~/.claude/skills/fluent-korean-review/scripts/change_rate.py "$orig" <file>`.
   - exit 0: at most 30% changed. Done.
   - exit 1: over 30%. Keep the edits and flag the rate in the report.
   - exit 2: over 50%. Save the revision with `cp <file> "$orig.revised"`, restore the original with `cp "$orig" <file>`, and report the path. A review that rewrites half the text has stopped being a review; the user should see it as a diff.

Text mode: print the revised text in full, then the report. No gate, since the user sees both versions.

## 5. Report

```
검토 대상: <path 또는 "입력 텍스트"> · 변경률 12% · 위반 5건
- 14행 구 단위 1: "컨텍스트 압축 전 신중 반영한다" → "컨텍스트가 압축되기 전에 신중히 반영한다"
- 22행 문장 단위 2: "다음 단계는 배포 스크립트 점검." → "다음 단계는 배포 스크립트를 점검하는 것이다."
```

If nothing violates the rules, say so and change nothing.
