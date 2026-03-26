#!/usr/bin/env python3
"""Generate LLM title for a Claude session markdown file.

Called as background process by claude-sessions sync.

Usage:
    update-title.py --jsonl PATH --md PATH
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Import shared text cleaning utilities (single source of truth)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from shared_utils import clean_text, extract_text  # noqa: E402


def get_user_messages(jsonl_path: Path, max_messages: int = 30) -> list[str]:
    """Extract cleaned user messages from JSONL."""
    messages = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("type") != "user" or record.get("isMeta"):
                continue
            msg = record.get("message", {})
            text = extract_text(msg.get("content", ""))
            cleaned = clean_text(text)
            if cleaned and not cleaned.startswith("Base directory for this skill:"):
                messages.append(cleaned)
            if len(messages) >= max_messages:
                break
    return messages


def get_assistant_summaries(jsonl_path: Path, max_summaries: int = 5) -> list[str]:
    """Extract assistant's first lines for additional context."""
    summaries = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("type") != "assistant":
                continue
            msg = record.get("message", {})
            contents = msg.get("content", [])
            if isinstance(contents, list):
                for item in contents:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text = item.get("text", "").strip()
                        if text:
                            first_line = text.split("\n")[0][:200]
                            summaries.append(first_line)
                            break
            if len(summaries) >= max_summaries:
                break
    return summaries


def has_custom_title(jsonl_path: Path) -> bool:
    """Check if session has a custom-title record."""
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                record = json.loads(line.strip())
                if record.get("type") == "custom-title":
                    return True
            except (json.JSONDecodeError, AttributeError):
                continue
    return False


def generate_title(messages: list[str], assistant_lines: list[str]) -> str | None:
    """Call claude CLI to generate a concise title."""
    context_parts = []
    for msg in messages[:20]:
        truncated = msg[:300] + "..." if len(msg) > 300 else msg
        context_parts.append(f"User: {truncated}")

    for line in assistant_lines[:3]:
        context_parts.append(f"Assistant: {line}")

    context = "\n".join(context_parts)

    prompt = f"""Below is a Claude Code session's conversation snippets. Generate a concise title (max 60 chars) that captures the main topic/task. Write the title in the same language the user primarily uses. Output ONLY the title, nothing else.

{context}"""

    try:
        env = os.environ.copy()
        env.pop("CLAUDECODE", None)
        result = subprocess.run(
            ["claude", "-p", "--model", "haiku", "--no-session-persistence"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )
        if result.returncode == 0 and result.stdout.strip():
            title = result.stdout.strip()
            # Remove quotes if wrapped
            if (title.startswith('"') and title.endswith('"')) or \
               (title.startswith("'") and title.endswith("'")):
                title = title[1:-1]
            title = title.split("\n")[0].strip()
            return title[:80]
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"Title generation failed: {e}", file=sys.stderr)
    return None


def update_markdown_title(md_path: Path, new_title: str):
    """Update title, title_source, and H1 heading in markdown."""
    content = md_path.read_text(encoding="utf-8")

    escaped = new_title.replace('"', '\\"')
    content = re.sub(
        r'^title: ".*?"',
        f'title: "{escaped}"',
        content, count=1, flags=re.MULTILINE,
    )

    # Update title_source to llm
    if 'title_source:' in content:
        content = re.sub(
            r'^title_source: \w+',
            'title_source: llm',
            content, count=1, flags=re.MULTILINE,
        )
    else:
        content = re.sub(
            r'^(title: ".*?")',
            r'\1\ntitle_source: llm',
            content, count=1, flags=re.MULTILINE,
        )

    # Update H1 heading
    content = re.sub(
        r'^# .+$',
        f'# {new_title}',
        content, count=1, flags=re.MULTILINE,
    )

    md_path.write_text(content, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Generate LLM title for a session")
    parser.add_argument("--jsonl", required=True, help="Path to session JSONL")
    parser.add_argument("--md", required=True, help="Path to session markdown")
    args = parser.parse_args()

    jsonl_path = Path(args.jsonl)
    md_path = Path(args.md)

    if not jsonl_path.exists() or not md_path.exists():
        print(f"File not found: jsonl={jsonl_path.exists()} md={md_path.exists()}", file=sys.stderr)
        return 1

    if has_custom_title(jsonl_path):
        print(f"Skipping: has custom title")
        return 0

    messages = get_user_messages(jsonl_path)
    if len(messages) < 2:
        print(f"Skipping: too few messages ({len(messages)})")
        return 0

    assistant_lines = get_assistant_summaries(jsonl_path)
    new_title = generate_title(messages, assistant_lines)
    if not new_title:
        print("Failed to generate title")
        return 1

    update_markdown_title(md_path, new_title)
    print(f"Title: {new_title}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
