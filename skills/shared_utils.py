"""Shared utilities for Claude Code skills.

Single source of truth for text cleaning, message extraction, and timezone helpers.
Used by: recall, sync-claude-sessions, update-title.

Import from any script:
    sys.path.insert(0, str(Path(__file__).resolve().parent / ".." / ".."))
    from skills.common import clean_content, extract_text, STRIP_PATTERNS
"""

import re
from datetime import timedelta, timezone

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
    """Get local timezone offset."""
    import time as _time
    offset = timedelta(seconds=-_time.timezone if _time.daylight == 0 else -_time.altzone)
    return timezone(offset)
