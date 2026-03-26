"""Shared utilities for Claude Code skills.

Single source of truth for text cleaning, message extraction, and timezone helpers.
Used by: recall, sync-claude-sessions, update-title.

Import from any script:
    sys.path.insert(0, str(Path(__file__).resolve().parent / ".." / ".."))
    from skills.common import clean_content, extract_text, STRIP_PATTERNS
"""

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Patterns to strip from user messages.
# Order matters: combined pattern first, then individual fallbacks for
# when tags appear in a different order than expected.
STRIP_PATTERNS = [
    re.compile(r'<system-reminder>.*?</system-reminder>', re.DOTALL),
    re.compile(r'<local-command-caveat>.*?</local-command-caveat>', re.DOTALL),
    re.compile(r'<local-command-stdout>.*?</local-command-stdout>', re.DOTALL),
    re.compile(r'<command-name>.*?</command-name>\s*<command-message>.*?</command-message>\s*(?:<command-args>.*?</command-args>)?', re.DOTALL),
    re.compile(r'<command-message>.*?</command-message>', re.DOTALL),
    re.compile(r'<command-name>.*?</command-name>', re.DOTALL),
    re.compile(r'<command-args>.*?</command-args>', re.DOTALL),
    re.compile(r'<task-notification>.*?</task-notification>', re.DOTALL),
    re.compile(r'<teammate-message[^>]*>.*?</teammate-message>', re.DOTALL),
    re.compile(r'<ide_opened_file>.*?</ide_opened_file>', re.DOTALL),
]


def clean_content(text: str) -> str:
    """Strip system tags, keep only human-written content."""
    if not isinstance(text, str):
        return ""
    for pat in STRIP_PATTERNS:
        text = pat.sub('', text)
    return text.strip()


# Alias for backward compatibility (sync-claude-sessions uses clean_text)
clean_text = clean_content


def extract_text(content) -> str:
    """Extract text from message content (string or list of content blocks)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get('type') == 'text':
                parts.append(block.get('text', ''))
            elif isinstance(block, str):
                parts.append(block)
        return '\n'.join(parts)
    return ""


def local_tz() -> timezone:
    """Get local timezone offset (DST-aware)."""
    import time as _time
    # tm_isdst > 0 means DST is currently active; use altzone in that case
    is_dst = _time.localtime().tm_isdst > 0
    offset = timedelta(seconds=-(_time.altzone if is_dst else _time.timezone))
    return timezone(offset)


def parse_iso_timestamp(ts: str, tz=None) -> datetime:
    """Parse ISO timestamp, handling 'Z' suffix. Optionally convert to tz."""
    dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
    if tz:
        dt = dt.astimezone(tz)
    return dt


def parse_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter from markdown content string.
    Supports: key-value pairs, arrays (  - item), multiline strings (|).
    """
    frontmatter = {}
    match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not match:
        return frontmatter

    fm_text = match.group(1)
    current_key = None
    current_array = None
    multiline_value = []
    in_multiline = False

    for line in fm_text.split("\n"):
        if in_multiline:
            if line.startswith("  ") or line == "":
                multiline_value.append(line[2:] if line.startswith("  ") else "")
                continue
            else:
                frontmatter[current_key] = "\n".join(multiline_value).rstrip()
                in_multiline = False
                multiline_value = []
                current_array = None

        if line.startswith("  - "):
            if current_array:
                if current_array not in frontmatter:
                    frontmatter[current_array] = []
                elif not isinstance(frontmatter[current_array], list):
                    frontmatter[current_array] = []
                frontmatter[current_array].append(line[4:].strip())
            continue

        if ":" in line and not line.startswith("  "):
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            current_key = key

            if value == "|":
                in_multiline = True
                multiline_value = []
                current_array = None
            elif value == "" or value == "[]":
                current_array = key
                frontmatter[key] = []
            else:
                current_array = None
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                frontmatter[key] = value

    if in_multiline:
        frontmatter[current_key] = "\n".join(multiline_value).rstrip()

    return frontmatter


def parse_frontmatter_file(filepath) -> dict | None:
    """Parse frontmatter from a markdown file path. Returns None on error."""
    try:
        content = Path(filepath).read_text(encoding='utf-8')
        result = parse_frontmatter(content)
        return result if result else None
    except (OSError, UnicodeDecodeError):
        return None


def parse_jsonl(file_path) -> list[dict]:
    """Parse a JSONL file into a list of records. Skips invalid lines."""
    records = []
    path = Path(file_path)
    if not path.exists():
        return records
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records


def derive_title(user_messages: list[str], max_len: int = 80) -> str:
    """Derive session title from first meaningful user message.
    Skips skill instructions and short messages. Returns 'Untitled' if none found.
    """
    for msg in user_messages:
        candidate = msg.replace("\n", " ").strip()
        candidate = re.sub(r'^#+\s*', '', candidate)
        if candidate.startswith("Base directory for this skill:"):
            continue
        if candidate.startswith("## Continue:"):
            m = re.match(r'## Continue:\s*(.+?)(?:\n|$)', msg)
            if m:
                candidate = m.group(1).strip()
        if len(candidate) < 3:
            continue
        if len(candidate) > max_len:
            candidate = candidate[:max_len - 3] + '...'
        return candidate
    return "Untitled"


SHORT_ID_LEN = 8


def short_id(session_id: str) -> str:
    """Get the short form of a session ID."""
    return session_id[:SHORT_ID_LEN]
