# Handoff Mode

A handoff is working state for the next session to pick up, not knowledge to keep. The next
handoff on the same topic replaces it. Write it so a fresh session can resume without
re-deriving anything or asking the user what was going on.

This mode is for session-to-session handoffs only. A handoff to another person (an API spec,
an onboarding guide for a teammate) is a regular doc: skip this file.

## Path and filename

- First look for earlier handoffs of this work, by topic or project name:
  ```bash
  . ~/.claude/env && python3 ~/.claude/skills/recall/scripts/recall-day.py handoffs --name NAME
  ```
- Continuing work: save in the same `_session-handoff/` folder as the newest match and reuse its
  topic slug (`spec-auth`, not a new name each time). This overrides Step 2's ranking
- New work: `<folder>/_session-handoff/`, where `<folder>` is what Step 2 picks; create it if
  missing. The `_` prefix keeps `suggest-path.py` from offering it for regular docs
- Filename: `YYYY-MM-DD-<topic>[-<focus>]-handoff.md`. Add `-<focus>` only when another
  handoff on the same topic already exists for that date

## Frontmatter

Step 4 frontmatter plus:

```yaml
topic: spec-auth
previous: "[[2026-10-07-spec-auth-session-handoff]]"   # latest earlier handoff on this topic; omit if none
tags:
  - handoff
```

Do not edit the previous handoff; the `previous` link is the chain.

## Sections

Write in the session's language. Every section is required; write "없음" rather than drop one.

1. **지금 상태** — table per repo: branch, HEAD commit, PR (number + draft/open/merged),
   what is pushed vs local only. Then deployed envs, running local stacks, and the last
   verification run with its result (tests passed/failed, and which failures pre-existed)
2. **이번 세션 결정 (사용자)** — table: topic | decision. Only what the user decided or
   confirmed, including "the agent must not do X" rules
3. **다음 할 일** — numbered, in execution order. First item is what to run before anything
   else (e.g. `git fetch` and rebase the three repos). Mark items blocked on the user
4. **함정·메모** — facts that cost time to find this session and must not be re-derived:
   environment quirks, wrong turns, commands that look right but fail
5. **재개 프롬프트** — one code block the user pastes to start the next session:
   ```
   <topic> 이어서 진행해. vault의 workspace/<folder>/_session-handoff/<file>.md 핸드오프를 먼저 읽고, <first step>.
   ```

## Before writing

Collect facts, don't recall them: run `git -C <repo> status -sb`, `git -C <repo> log -1 --oneline`,
and `gh pr list --head <branch>` for each repo touched this session.

Then continue with Step 3 (confirm) and Step 4 (save). Step 3 shows the `previous` handoff too.

## After saving

If this project's auto-memory has an entry pointing at an earlier handoff of this topic (a
"start here" line, a handoff path), update that entry to the new path. Do not create a new memory
just to point at the handoff; `recall handoff <topic>` finds it.
