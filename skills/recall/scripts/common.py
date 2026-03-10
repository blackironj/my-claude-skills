"""Backward-compatible shim — re-exports from skills/shared_utils.py."""

import sys
from pathlib import Path

# Add skills/ dir to path so we can import shared_utils
_skills_dir = str(Path(__file__).resolve().parent.parent.parent)
if _skills_dir not in sys.path:
    sys.path.insert(0, _skills_dir)

from shared_utils import STRIP_PATTERNS, clean_content, clean_text, extract_text, local_tz  # noqa: F401, E402
