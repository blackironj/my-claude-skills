#!/usr/bin/env python3
"""Backfill existing session markdown files into Obsidian daily notes.

Scans $VAULT_SESSIONS_DIR for session .md files, groups them by date,
and writes/updates a ## Claude Sessions section in the corresponding
daily note at $VAULT_DIR/Daily Notes/YYYY-MM-DD.md.

Usage:
    backfill-daily.py [--dry-run] [--date YYYY-MM-DD]
"""

import argparse
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from shared_utils import parse_frontmatter  # noqa: E402

SECTION_HEADING = "## Claude Sessions"


def get_tz() -> timezone:
    """Get Asia/Seoul timezone (UTC+9)."""
    return timezone(timedelta(hours=9))


def parse_last_activity(value: str) -> str:
    """Parse ISO timestamp to HH:MM in Asia/Seoul timezone.

    Returns '00:00' if parsing fails or value is empty.
    """
    if not value:
        return "00:00"
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        dt_local = dt.astimezone(get_tz())
        return dt_local.strftime("%H:%M")
    except (ValueError, TypeError):
        return "00:00"


def format_session_line(stem: str, title: str, time_str: str, project: str | None) -> str:
    """Format a single session line for the daily note.

    Format: - HH:MM [[stem]] — title ([[project]])
    """
    line = f"- {time_str} [[{stem}]] — {title}"
    if project:
        line += f" ([[{project}]])"
    return line


def scan_sessions(sessions_dir: Path) -> list[dict]:
    """Scan all session .md files and extract metadata."""
    sessions = []
    for md_file in sorted(sessions_dir.rglob("*.md")):
        try:
            content = md_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue

        fm = parse_frontmatter(content)
        if not fm:
            continue

        date_str = fm.get("date", "")
        if not date_str:
            continue

        title = fm.get("title", "Untitled")
        # Strip surrounding quotes if present
        if len(title) >= 2 and title[0] == '"' and title[-1] == '"':
            title = title[1:-1]

        last_activity = fm.get("last_activity", "")
        time_str = parse_last_activity(last_activity)

        projects = fm.get("projects", [])
        project = projects[0] if isinstance(projects, list) and projects else None

        sessions.append({
            "date": date_str,
            "stem": md_file.stem,
            "title": title,
            "time": time_str,
            "project": project,
        })

    return sessions


def group_by_date(sessions: list[dict]) -> dict[str, list[dict]]:
    """Group sessions by date, sorted by time within each group."""
    groups: dict[str, list[dict]] = {}
    for s in sessions:
        groups.setdefault(s["date"], []).append(s)

    # Sort each group by time
    for date in groups:
        groups[date].sort(key=lambda s: s["time"])

    return groups


def build_section(sessions: list[dict]) -> str:
    """Build the ## Claude Sessions section, grouped by project."""
    lines = [SECTION_HEADING]

    # Group by project
    by_project: dict[str, list[dict]] = {}
    for s in sessions:
        proj = s["project"] or "other"
        by_project.setdefault(proj, []).append(s)

    if len(by_project) <= 1:
        # Single project or no project — flat list
        for s in sessions:
            lines.append(format_session_line(s["stem"], s["title"], s["time"], s["project"]))
    else:
        # Multiple projects — group with subheadings
        for proj in sorted(by_project.keys()):
            proj_sessions = by_project[proj]
            lines.append(f"**[[{proj}]]**")
            for s in proj_sessions:
                lines.append(format_session_line(s["stem"], s["title"], s["time"], None))

    return "\n".join(lines)


def update_daily_note(daily_path: Path, section: str, dry_run: bool) -> str:
    """Update or create a daily note with the sessions section.

    Returns a status string: 'created', 'replaced', or 'appended'.
    """
    if not daily_path.exists():
        if dry_run:
            return "would create"
        daily_path.parent.mkdir(parents=True, exist_ok=True)
        daily_path.write_text(section + "\n", encoding="utf-8")
        return "created"

    content = daily_path.read_text(encoding="utf-8")

    # Check if section already exists — replace it
    # Matches heading + any mix of list items, bold project headers, and blank lines
    pattern = re.compile(
        r"^## Claude Sessions\n(?:(?:- .+|\*\*.+\*\*)\n?)*",
        re.MULTILINE,
    )
    if pattern.search(content):
        if dry_run:
            return "would replace"
        new_content = pattern.sub(section + "\n", content)
        daily_path.write_text(new_content, encoding="utf-8")
        return "replaced"

    # Append section
    if dry_run:
        return "would append"
    separator = "\n" if content and not content.endswith("\n") else ""
    extra_newline = "" if content.endswith("\n\n") or not content.strip() else "\n"
    daily_path.write_text(
        content + separator + extra_newline + section + "\n",
        encoding="utf-8",
    )
    return "appended"


def main():
    parser = argparse.ArgumentParser(
        description="Backfill session markdown files into Obsidian daily notes",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be written without writing",
    )
    parser.add_argument(
        "--date",
        help="Backfill only a specific date (YYYY-MM-DD)",
    )
    args = parser.parse_args()

    vault_dir = os.environ.get("VAULT_DIR", "")
    sessions_dir = os.environ.get("VAULT_SESSIONS_DIR", "")

    if not vault_dir:
        print("Error: VAULT_DIR not set. Source ~/.claude/env first.", file=sys.stderr)
        return 1
    if not sessions_dir:
        print("Error: VAULT_SESSIONS_DIR not set. Source ~/.claude/env first.", file=sys.stderr)
        return 1

    vault_path = Path(vault_dir)
    sessions_path = Path(sessions_dir)
    daily_dir = vault_path / "Daily Notes"

    if not sessions_path.is_dir():
        print(f"Error: Sessions directory not found: {sessions_path}", file=sys.stderr)
        return 1

    # Scan and group sessions
    all_sessions = scan_sessions(sessions_path)

    if args.date:
        # Validate date format
        try:
            datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            print(f"Error: Invalid date format: {args.date} (expected YYYY-MM-DD)", file=sys.stderr)
            return 1
        all_sessions = [s for s in all_sessions if s["date"] == args.date]

    if not all_sessions:
        print("No sessions found.")
        return 0

    grouped = group_by_date(all_sessions)

    # Process each date
    dates_processed = 0
    for date_str in sorted(grouped.keys()):
        sessions = grouped[date_str]
        section = build_section(sessions)
        daily_path = daily_dir / f"{date_str}.md"

        status = update_daily_note(daily_path, section, args.dry_run)
        dates_processed += 1

        prefix = "[dry-run] " if args.dry_run else ""
        print(f"{prefix}{date_str}: {len(sessions)} sessions — {status}")

        if args.dry_run:
            for s in sessions:
                line = format_session_line(s["stem"], s["title"], s["time"], s["project"])
                print(f"  {line}")

    print(f"\nTotal: {len(all_sessions)} sessions across {dates_processed} dates")
    return 0


if __name__ == "__main__":
    sys.exit(main())
