"""Backward-compatible shim — re-exports from skills/shared_utils.py."""

import sys
from pathlib import Path

_skills_dir = str(Path(__file__).resolve().parent.parent.parent)
if _skills_dir not in sys.path:
    sys.path.insert(0, _skills_dir)

from shared_utils import (  # noqa: F401, E402
    local_tz, parse_iso_timestamp, parse_frontmatter, parse_frontmatter_file,
)
