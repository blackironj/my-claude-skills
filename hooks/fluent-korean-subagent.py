#!/usr/bin/env python3
"""PreToolUse hook (matcher: Agent) that carries the fluent-korean rules into subagents.

Output styles are part of the parent session's system prompt and never reach a
subagent, so a Korean prompt written under fluent-korean loses the rules the moment
it is handed off. This hook reads the Agent tool input from stdin and, when the prompt
is mostly Korean, returns ``updatedInput`` with the style body appended. English
prompts and prompts that already carry the body pass through untouched.

The full body is appended rather than a summary because the style file itself asks
not to be summarized: the examples attached to each clause are what make the clauses
actionable. Any failure exits 0 without output so a broken hook never blocks agents.
"""

import json
import os
import re
import sys

STYLE_FILE = os.path.expanduser("~/.claude/output-styles/fluent-korean.md")
HANGUL = re.compile(r"[가-힣]")
LETTERS = re.compile(r"[A-Za-z가-힣]")
MIN_HANGUL_RATIO = 0.3


def style_body(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        text = f.read()
    parts = text.split("---\n", 2)
    if len(parts) == 3 and parts[0] == "":
        return parts[2].strip()
    return text.strip()


def is_korean(text: str) -> bool:
    letters = LETTERS.findall(text)
    if not letters:
        return False
    return len(HANGUL.findall(text)) / len(letters) >= MIN_HANGUL_RATIO


def main() -> int:
    data = json.load(sys.stdin)
    if data.get("tool_name") != "Agent":
        return 0
    tool_input = data.get("tool_input") or {}
    prompt = tool_input.get("prompt")
    if not isinstance(prompt, str) or not is_korean(prompt):
        return 0
    rules = style_body(STYLE_FILE)
    if rules[:120] in prompt:  # already carries the body (e.g. a re-run of the same call)
        return 0

    updated = dict(tool_input)
    updated["prompt"] = prompt.rstrip() + "\n\n---\n\n" + rules
    json.dump(
        {"hookSpecificOutput": {"hookEventName": "PreToolUse", "updatedInput": updated}},
        sys.stdout,
        ensure_ascii=False,
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001 - fail open, never block the Agent call
        print(f"fluent-korean-subagent hook: {exc}", file=sys.stderr)
        sys.exit(0)
