#!/usr/bin/env python3
"""Recall sessions by date from the Obsidian vault session archive.

Usage:
    recall-day.py list DATE_EXPR [--name PROJECT] [--min-msgs N]
    recall-day.py expand SESSION_ID [--max-msgs N]
    recall-day.py projects
    recall-day.py handoffs [--name TEXT] [--limit N]

DATE_EXPR examples: yesterday, today, 2026-02-25, "last tuesday", "this week",
                    "last week", "3 days ago", "last 3 days"

Reads $VAULT_SESSIONS_DIR recursively (top level and YYYY/MM archive folders),
so sessions from every synced machine and beyond local JSONL retention are visible.
`handoffs` lists save-doc session handoffs under $DOCS_DIR/**/_session-handoff/, newest first.
"""

import argparse
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add scripts dir to path for common module
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import local_tz as _local_tz, parse_frontmatter, parse_frontmatter_file, parse_iso_timestamp

VAULT_SESSIONS_DIR = os.environ.get('VAULT_SESSIONS_DIR', '')
VAULT_DIR = os.environ.get('VAULT_DIR', '')
SESSIONS_DIR = Path(VAULT_SESSIONS_DIR) if VAULT_SESSIONS_DIR else (Path(VAULT_DIR) / "Claude-Sessions" if VAULT_DIR else None)
SESSION_FILE_RE = re.compile(r'^(\d{4}-\d{2}-\d{2})-[0-9a-f]+$')


def iter_session_files():
    """Yield (date_str, path) for every session markdown file in the vault."""
    if not SESSIONS_DIR or not SESSIONS_DIR.is_dir():
        print("Error: VAULT_SESSIONS_DIR is not set or missing. Run '. ~/.claude/env' first.", file=sys.stderr)
        sys.exit(1)
    for md_file in SESSIONS_DIR.rglob("*.md"):
        m = SESSION_FILE_RE.match(md_file.stem)
        if m:
            yield m.group(1), md_file


def projects_of(fm: dict) -> list[str]:
    projects = fm.get('projects', [])
    return projects if isinstance(projects, list) else []


def scan_sessions(date_start: datetime, date_end: datetime, project_name: str | None) -> list[dict]:
    """Collect session metadata whose filename date falls in [date_start, date_end)."""
    first, last = date_start.strftime('%Y-%m-%d'), (date_end - timedelta(days=1)).strftime('%Y-%m-%d')
    sessions = []
    for date_str, md_file in iter_session_files():
        if not first <= date_str <= last:
            continue
        try:
            content = md_file.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            continue
        fm = parse_frontmatter(content)
        if not fm:
            continue
        projects = projects_of(fm)
        if project_name and not any(project_name.lower() in p.lower() for p in projects):
            continue

        last_activity = None
        if fm.get('last_activity'):
            try:
                last_activity = parse_iso_timestamp(str(fm['last_activity']), _local_tz())
            except (ValueError, TypeError):
                pass
        sessions.append({
            'session_id': str(fm.get('session_id') or md_file.stem.split('-')[-1]),
            'date': date_str,
            'last_activity': last_activity,
            # frontmatter `messages` also counts tool results; user turns are the `### User` headings
            'user_msg_count': content.count('\n### User\n'),
            'title': str(fm.get('title') or 'Untitled')[:80],
            'projects': projects,
            'machine': str(fm.get('machine') or ''),
        })
    return sessions


DAY_NAMES = {
    'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
    'friday': 4, 'saturday': 5, 'sunday': 6,
}


def parse_date_expr(expr: str) -> tuple[datetime, datetime]:
    """Parse a date expression into (start, end) date range (local time, day boundaries).

    Returns start of day (inclusive) and end of day (exclusive) in local timezone.
    """
    expr = expr.strip().lower()
    local_tz = _local_tz()
    now = datetime.now(local_tz)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    if expr == 'today':
        return today_start, today_start + timedelta(days=1)

    if expr == 'yesterday':
        start = today_start - timedelta(days=1)
        return start, today_start

    # YYYY-MM-DD — use local timezone (consistent with other date expressions)
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', expr)
    if m:
        d = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=local_tz)
        return d, d + timedelta(days=1)

    # "N days ago"
    m = re.match(r'^(\d+)\s+days?\s+ago$', expr)
    if m:
        n = int(m.group(1))
        start = today_start - timedelta(days=n)
        return start, start + timedelta(days=1)

    # "last N days"
    m = re.match(r'^last\s+(\d+)\s+days?$', expr)
    if m:
        n = int(m.group(1))
        start = today_start - timedelta(days=n)
        return start, today_start + timedelta(days=1)

    # "this week" (Monday-based)
    if expr == 'this week':
        monday = today_start - timedelta(days=today_start.weekday())
        return monday, today_start + timedelta(days=1)

    # "last week"
    if expr == 'last week':
        this_monday = today_start - timedelta(days=today_start.weekday())
        last_monday = this_monday - timedelta(days=7)
        return last_monday, this_monday

    # "last monday" .. "last sunday"
    m = re.match(r'^last\s+(\w+)$', expr)
    if m and m.group(1) in DAY_NAMES:
        target_dow = DAY_NAMES[m.group(1)]
        current_dow = today_start.weekday()
        days_back = (current_dow - target_dow) % 7
        if days_back == 0:
            days_back = 7
        start = today_start - timedelta(days=days_back)
        return start, start + timedelta(days=1)

    print(f"Error: Can't parse date expression: '{expr}'", file=sys.stderr)
    print("Supported: today, yesterday, YYYY-MM-DD, 'N days ago', 'last N days',", file=sys.stderr)
    print("           'this week', 'last week', 'last monday'...'last sunday'", file=sys.stderr)
    sys.exit(1)


def cmd_list(args):
    """List sessions for a date range."""
    date_start, date_end = parse_date_expr(args.date_expr)
    if args.full_history:
        date_start = datetime(2020, 1, 1, tzinfo=_local_tz())
        date_end = datetime.now(_local_tz()) + timedelta(days=1)

    sessions = scan_sessions(date_start, date_end, args.name)
    noise_count = sum(1 for s in sessions if s['user_msg_count'] < args.min_msgs)
    sessions = [s for s in sessions if s['user_msg_count'] >= args.min_msgs]
    sessions.sort(key=lambda s: (s['date'], s['last_activity'] or datetime.min.replace(tzinfo=_local_tz())))

    if date_end - date_start <= timedelta(days=1):
        header_date = date_start.strftime('%Y-%m-%d (%A)')
    else:
        header_date = f"{date_start.strftime('%Y-%m-%d')} to {(date_end - timedelta(days=1)).strftime('%Y-%m-%d')}"

    print(f"\nSessions for {header_date}\n")

    if not sessions:
        print("No sessions found.")
        if noise_count:
            print(f"({noise_count} filtered as noise, try --min-msgs 1)")
        return

    print(f" {'#':>3}  {'Date':10}  {'Last':5}  {'Msgs':>4}  {'Machine':12}  {'Project':18}  Title")
    print(f" {'---':>3}  {'-' * 10}  {'-----':5}  {'----':>4}  {'-' * 12}  {'-' * 18}  -----")
    for i, s in enumerate(sessions, 1):
        last = s['last_activity'].strftime('%H:%M') if s['last_activity'] else '--:--'
        project = ','.join(s['projects'])[:18]
        print(f" {i:3}  {s['date']}  {last}  {s['user_msg_count']:4}  {s['machine'][:12]:12}  {project:18}  {s['title'][:60]}")

    print(f"\n{len(sessions)} sessions", end="")
    if noise_count:
        print(f" ({noise_count} filtered as noise)", end="")
    print()

    print("\nSession IDs (for expand):")
    for i, s in enumerate(sessions, 1):
        print(f"  {i:3}. {s['session_id'][:8]}")


def cmd_expand(args):
    """Print a session's markdown body (frontmatter stripped), capped at --max-msgs user turns."""
    target_id = args.session_id.lower()
    target = next((f for _, f in iter_session_files() if f.stem.split('-')[-1].startswith(target_id[:8])), None)
    if not target:
        print(f"Error: No session found matching '{args.session_id}'", file=sys.stderr)
        sys.exit(1)

    print(f"\nSession: {target.stem}")
    print(f"File: {target}\n")

    text = target.read_text(encoding='utf-8')
    if text.startswith('---'):
        end = text.find('\n---', 3)
        if end != -1:
            text = text[end + 4:]

    user_turns = 0
    for line in text.splitlines():
        if line.startswith('### User'):
            user_turns += 1
            if args.max_msgs and user_turns > args.max_msgs:
                print(f"\n... truncated at {args.max_msgs} user messages (use --max-msgs to show more)")
                break
        print(line)


def cmd_projects(args):
    """List all projects found in session frontmatter with session counts."""
    counts: dict[str, int] = {}
    for _, md_file in iter_session_files():
        fm = parse_frontmatter_file(md_file)
        for p in projects_of(fm or {}):
            counts[p] = counts.get(p, 0) + 1

    if not counts:
        print("No projects found.")
        return

    print("\nProjects:\n")
    for pname, count in sorted(counts.items(), key=lambda x: -x[1]):
        print(f" {count:3}  {pname}")
    print(f"\n{len(counts)} projects total")


def cmd_handoffs(args):
    """List session handoffs, newest first, optionally filtered by folder/file/topic/project substring."""
    docs_env = os.environ.get('DOCS_DIR')
    if not docs_env or not Path(docs_env).is_dir():
        print("Error: DOCS_DIR is not set or missing. Run '. ~/.claude/env' first.", file=sys.stderr)
        sys.exit(1)
    docs_dir = Path(docs_env)

    rows = []
    for md in docs_dir.rglob('_session-handoff/*-handoff.md'):
        fm = parse_frontmatter_file(md) or {}
        rel = md.relative_to(docs_dir).as_posix()
        topic, project = str(fm.get('topic') or ''), str(fm.get('project') or '')
        if args.name and not any(args.name.lower() in v.lower() for v in (rel, topic, project)):
            continue
        rows.append((md.name[:10], md.stat().st_mtime, rel, topic))

    if not rows:
        print("No session handoffs found." + (f" (filter: {args.name})" if args.name else ""))
        return

    rows.sort(key=lambda r: (r[0], r[1]), reverse=True)
    print(f"\nSession handoffs in {docs_dir} (newest first)\n")
    for date, _, rel, topic in rows[:args.limit]:
        print(f" {date}  {rel}" + (f"  [topic: {topic}]" if topic else ""))
    if len(rows) > args.limit:
        print(f"\n... {len(rows) - args.limit} older (use --limit)")


def main():
    parser = argparse.ArgumentParser(
        description='Recall sessions by date from the Obsidian vault',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest='command', required=True)

    p_list = sub.add_parser('list', help='List sessions for a date')
    p_list.add_argument('date_expr', nargs='*', help='Date expression (e.g. yesterday, today, 2026-02-25)')
    p_list.add_argument('--min-msgs', type=int, default=3, help='Min user messages (default: 3)')
    p_list.add_argument('--name', help='Filter by project name (substring match)')
    p_list.add_argument('--full-history', action='store_true', dest='full_history', help='Show full history (use with --name)')

    p_expand = sub.add_parser('expand', help='Expand a session by ID')
    p_expand.add_argument('session_id', help='Session ID (prefix match)')
    p_expand.add_argument('--max-msgs', type=int, default=50, help='Max user messages to show (default: 50)')

    sub.add_parser('projects', help='List all projects with session counts')

    p_handoffs = sub.add_parser('handoffs', help='List session handoffs, newest first')
    p_handoffs.add_argument('--name', help='Filter by folder, filename, topic, or project (substring)')
    p_handoffs.add_argument('--limit', type=int, default=10, help='Max handoffs to show (default: 10)')

    args = parser.parse_args()

    if args.command == 'list':
        if args.date_expr:
            args.date_expr = ' '.join(args.date_expr)
        elif args.name:
            args.date_expr = 'last 14 days'
        elif args.full_history:
            args.date_expr = 'last 3650 days'
        else:
            parser.error("date_expr is required (or use --name for project filtering)")
        cmd_list(args)
    elif args.command == 'expand':
        cmd_expand(args)
    elif args.command == 'projects':
        cmd_projects(args)
    elif args.command == 'handoffs':
        cmd_handoffs(args)


if __name__ == '__main__':
    main()
