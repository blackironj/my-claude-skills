#!/usr/bin/env python3
"""Recall sessions by date from native Claude Code JSONL files.

Usage:
    recall-day.py list DATE_EXPR [--project PATH] [--all-projects] [--min-msgs N]
    recall-day.py expand SESSION_ID [--project PATH] [--all-projects] [--max-msgs N]

DATE_EXPR examples: yesterday, today, 2026-02-25, "last tuesday", "this week",
                    "last week", "3 days ago", "last 3 days"

Every Claude Code user has JSONL session files in ~/.claude/projects/.
No custom setup needed.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add scripts dir to path for common module
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import STRIP_PATTERNS, clean_content, extract_text, local_tz as _local_tz, parse_frontmatter_file, parse_iso_timestamp, derive_title

CLAUDE_PROJECTS = Path.home() / ".claude" / "projects"
VAULT_SESSIONS_DIR = os.environ.get('VAULT_SESSIONS_DIR', '')
VAULT_DIR = os.environ.get('VAULT_DIR', '')
OBSIDIAN_SESSIONS = Path(VAULT_SESSIONS_DIR) if VAULT_SESSIONS_DIR else (Path(VAULT_DIR) / "Claude-Sessions" if VAULT_DIR else None)


def build_project_index() -> dict[Path, str]:
    """Build project_dir -> project_name mapping from JSONL cwd fields.

    Reads the first record of the most recent JSONL in each project directory
    to extract the cwd, then uses Path(cwd).name as the project name.
    """
    index = {}
    if not CLAUDE_PROJECTS.is_dir():
        return index
    for proj_dir in CLAUDE_PROJECTS.iterdir():
        if not proj_dir.is_dir():
            continue
        jsonl_files = sorted(proj_dir.glob("*.jsonl"),
                           key=lambda f: f.stat().st_mtime, reverse=True)
        for jf in jsonl_files[:1]:
            try:
                with open(jf) as f:
                    for line in f:
                        obj = json.loads(line)
                        cwd = obj.get("cwd")
                        if cwd:
                            index[proj_dir] = Path(cwd).name
                            break
            except (OSError, json.JSONDecodeError):
                continue
    return index


def scan_obsidian_sessions(date_start: datetime, date_end: datetime, project_name: str | None = None) -> list[dict]:
    """Scan Obsidian Claude-Sessions for the given date range. Returns session metadata list."""
    if not OBSIDIAN_SESSIONS or not OBSIDIAN_SESSIONS.exists():
        return []

    sessions = []
    # Generate date patterns for the range
    current = date_start.date() if hasattr(date_start, 'date') else date_start
    end = date_end.date() if hasattr(date_end, 'date') else date_end

    while current < end:
        date_str = current.strftime('%Y-%m-%d')
        for md_file in OBSIDIAN_SESSIONS.glob(f"{date_str}-*.md"):
            fm = parse_frontmatter_file(md_file)
            if not fm:
                continue

            # Project name filter
            if project_name:
                fm_projects = fm.get('projects', [])
                if not isinstance(fm_projects, list):
                    fm_projects = []
                if not any(project_name.lower() in p.lower() for p in fm_projects):
                    continue

            session_id = fm.get('session_id', md_file.stem.split('-', 3)[-1] if '-' in md_file.stem else md_file.stem)
            title = fm.get('title', 'Untitled')
            messages = fm.get('messages', 0)
            last_activity = fm.get('last_activity', '')

            # Parse time from last_activity or filename date
            start_time = None
            if last_activity:
                try:
                    start_time = parse_iso_timestamp(last_activity, _local_tz())
                except (ValueError, TypeError):
                    pass
            if not start_time:
                start_time = datetime(current.year, current.month, current.day, tzinfo=_local_tz())

            sessions.append({
                'session_id': session_id,
                'start_time': start_time,
                'user_msg_count': messages if isinstance(messages, int) else 0,
                'file_size': md_file.stat().st_size,
                'title': title[:80] if title else 'Untitled',
                'filepath': str(md_file),
                'source': 'remote',
            })

        current += timedelta(days=1)

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


def get_project_dirs(project_path: str | None, all_projects: bool, name: str | None = None) -> list[Path]:
    """Get list of project directories to scan.

    Args:
        project_path: Exact project path (existing --project flag)
        all_projects: Scan all projects
        name: Project name substring filter (new --name flag)
    """
    if project_path and name:
        print("Error: --project and --name cannot be used together.", file=sys.stderr)
        sys.exit(1)

    if project_path:
        encoded = project_path.replace('/', '-')
        p = CLAUDE_PROJECTS / encoded
        if p.exists():
            return [p]
        # Try as-is
        p = Path(project_path)
        if p.exists():
            return [p]
        print(f"Error: Project path not found: {project_path}", file=sys.stderr)
        sys.exit(1)

    if name:
        index = build_project_index()
        matched = [d for d, pname in index.items() if name.lower() in pname.lower()]
        if not matched:
            print(f"Error: No project matching '{name}'.", file=sys.stderr)
            print("Run 'recall-day.py projects' to see available projects.", file=sys.stderr)
            sys.exit(1)
        return matched

    # Default: scan all projects
    return [d for d in CLAUDE_PROJECTS.iterdir() if d.is_dir()]


def scan_session_metadata(filepath: Path, date_start: datetime, date_end: datetime) -> dict | None:
    """Fast scan: read first ~30 lines for metadata, count user messages."""
    session_id = filepath.stem
    start_time = None
    first_user_msg = None
    user_msg_count = 0
    file_size = filepath.stat().st_size

    try:
        with open(filepath) as f:
            for i, line in enumerate(f):
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Get session ID from data if available
                if obj.get('sessionId'):
                    session_id = obj['sessionId']

                ts_str = obj.get('timestamp')
                if ts_str and not start_time:
                    try:
                        start_time = parse_iso_timestamp(ts_str, _local_tz())
                    except (ValueError, TypeError):
                        pass

                # Count user messages and capture first
                if obj.get('type') == 'user' and obj.get('message', {}).get('role') == 'user':
                    user_msg_count += 1
                    if first_user_msg is None:
                        raw = extract_text(obj['message'].get('content', ''))
                        cleaned = clean_content(raw)
                        if cleaned and len(cleaned) >= 5:
                            # Skip pure slash commands and skill instructions
                            if re.match(r'^/\w+\s*$', cleaned):
                                continue
                            if cleaned.startswith('Base directory for this skill:'):
                                continue
                            first_user_msg = cleaned

                # Early exit: if we have start_time and it's outside range, skip
                if start_time and i < 5:
                    if start_time >= date_end or start_time < date_start - timedelta(days=1):
                        return None

    except (OSError, UnicodeDecodeError):
        return None

    if not start_time:
        return None

    # Final date check
    if start_time < date_start or start_time >= date_end:
        return None

    # Derive title from first message
    title = derive_title([first_user_msg] if first_user_msg else [])

    return {
        'session_id': session_id,
        'start_time': start_time,
        'user_msg_count': user_msg_count,
        'file_size': file_size,
        'title': title,
        'filepath': str(filepath),
    }


def format_size(size_bytes: int) -> str:
    """Format file size human-readable."""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.0f}KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f}MB"


def cmd_list(args):
    """List sessions for a date range."""
    date_start, date_end = parse_date_expr(args.date_expr)
    if getattr(args, 'full_history', False):
        date_start = datetime(2020, 1, 1, tzinfo=_local_tz())
        date_end = datetime.now(_local_tz()) + timedelta(days=1)
    project_dirs = get_project_dirs(args.project, args.all_projects, getattr(args, 'name', None))

    sessions = []
    noise_count = 0
    total_scanned = 0

    # 1. Local JSONL scan (primary, fast)
    for proj_dir in project_dirs:
        jsonl_files = list(proj_dir.glob("*.jsonl"))
        total_scanned += len(jsonl_files)

        for filepath in jsonl_files:
            # Coarse filter: mtime must be within range (with 1 day buffer)
            try:
                mtime = datetime.fromtimestamp(filepath.stat().st_mtime, tz=_local_tz())
                if mtime < date_start - timedelta(days=1):
                    continue
            except OSError:
                continue

            meta = scan_session_metadata(filepath, date_start, date_end)
            if meta is None:
                continue

            meta['source'] = 'local'

            if meta['user_msg_count'] < args.min_msgs:
                noise_count += 1
                continue

            sessions.append(meta)

    # 2. Obsidian scan (supplementary — catches sessions from other computers)
    local_ids = {s['session_id'][:8] for s in sessions}
    obsidian_sessions = scan_obsidian_sessions(date_start, date_end, getattr(args, 'name', None))
    remote_count = 0
    for obs in obsidian_sessions:
        obs_id_short = obs['session_id'][:8]
        if obs_id_short not in local_ids:
            if obs['user_msg_count'] >= args.min_msgs:
                sessions.append(obs)
                remote_count += 1

    sessions.sort(key=lambda s: s['start_time'])

    # Format date range for header
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

    # Print table
    has_remote = any(s.get('source') == 'remote' for s in sessions)
    if has_remote:
        print(f" {'#':>2}  {'Time':5}  {'Msgs':>4}  {'Size':>6}  {'Src':6}  First Message")
        print(f" {'--':>2}  {'-----':5}  {'----':>4}  {'------':>6}  {'------':6}  -------------")
    else:
        print(f" {'#':>2}  {'Time':5}  {'Msgs':>4}  {'Size':>6}  First Message")
        print(f" {'--':>2}  {'-----':5}  {'----':>4}  {'------':>6}  -------------")

    for i, s in enumerate(sessions, 1):
        time_str = s['start_time'].strftime('%H:%M')
        size_str = format_size(s['file_size'])
        title = s['title'][:60]
        if has_remote:
            src = 'remote' if s.get('source') == 'remote' else 'local'
            print(f" {i:2}  {time_str}  {s['user_msg_count']:4}  {size_str:>6}  {src:6}  {title}")
        else:
            print(f" {i:2}  {time_str}  {s['user_msg_count']:4}  {size_str:>6}  {title}")

    print(f"\n{len(sessions)} sessions", end="")
    if remote_count:
        print(f" ({remote_count} remote)", end="")
    if noise_count:
        print(f" ({noise_count} filtered as noise)", end="")
    print()

    # Print session IDs for expand
    print(f"\nSession IDs (for expand):")
    for i, s in enumerate(sessions, 1):
        print(f"  {i:2}. {s['session_id'][:8]}")


def find_obsidian_session(session_id_prefix: str) -> Path | None:
    """Find an Obsidian session markdown file by session ID prefix."""
    if not OBSIDIAN_SESSIONS or not OBSIDIAN_SESSIONS.exists():
        return None
    for md_file in OBSIDIAN_SESSIONS.glob(f"*-{session_id_prefix}*.md"):
        return md_file
    # Also try broader match
    for md_file in OBSIDIAN_SESSIONS.glob("*.md"):
        if session_id_prefix in md_file.stem:
            return md_file
    return None


def cmd_expand(args):
    """Expand a session by ID - show conversation summary."""
    project_dirs = get_project_dirs(args.project, args.all_projects)
    target_id = args.session_id.lower()

    # Find the JSONL file
    target_file = None
    for proj_dir in project_dirs:
        for filepath in proj_dir.glob("*.jsonl"):
            if filepath.stem.lower().startswith(target_id):
                target_file = filepath
                break
        if target_file:
            break

    # Fallback to Obsidian if no local JSONL
    if not target_file:
        obs_file = find_obsidian_session(target_id)
        if obs_file:
            print(f"\nSession: {obs_file.stem} (remote — from Obsidian)")
            print(f"File: {obs_file}")
            print()
            # Print markdown content (skip frontmatter)
            in_frontmatter = False
            with open(obs_file, encoding='utf-8') as f:
                for line in f:
                    if line.strip() == '---' and not in_frontmatter:
                        in_frontmatter = True
                        continue
                    if line.strip() == '---' and in_frontmatter:
                        in_frontmatter = False
                        continue
                    if not in_frontmatter:
                        print(line, end='')
            return
        print(f"Error: No session found matching '{args.session_id}'", file=sys.stderr)
        sys.exit(1)

    print(f"\nSession: {target_file.stem}")
    print(f"File: {target_file}")
    print()

    msg_count = 0
    max_msgs = args.max_msgs

    with open(target_file) as f:
        for line in f:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            msg_type = obj.get('type')
            msg = obj.get('message', {})
            role = msg.get('role')
            ts_str = obj.get('timestamp', '')

            # Format timestamp
            ts_label = ''
            if ts_str:
                try:
                    dt = parse_iso_timestamp(ts_str, _local_tz())
                    ts_label = dt.strftime('%H:%M')
                except (ValueError, TypeError):
                    pass

            if msg_type == 'user' and role == 'user':
                raw = extract_text(msg.get('content', ''))
                cleaned = clean_content(raw)
                if not cleaned or len(cleaned) < 5:
                    continue
                if re.match(r'^/\w+\s*$', cleaned):
                    continue

                msg_count += 1
                if max_msgs and msg_count > max_msgs:
                    print(f"\n... truncated at {max_msgs} messages (use --max-msgs to show more)")
                    break

                # Truncate long messages
                display = cleaned
                if len(display) > 200:
                    display = display[:197] + '...'
                display = display.replace('\n', '\n    ')

                print(f"[{ts_label}] USER: {display}")

            elif msg_type == 'assistant' and role == 'assistant':
                content = msg.get('content', [])
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict):
                            if block.get('type') == 'text':
                                text = block.get('text', '')
                                first_line = text.split('\n')[0][:120]
                                if first_line.strip():
                                    print(f"  [{ts_label}] ASST: {first_line}")
                                break
                            elif block.get('type') == 'tool_use':
                                tool_name = block.get('name', '?')
                                print(f"  [{ts_label}] TOOL: {tool_name}")

    print(f"\n{msg_count} user messages total")


def cmd_projects(args):
    """List all known projects with session counts."""
    # Local projects from JSONL
    index = build_project_index()
    counts: dict[str, int] = {}
    for proj_dir, pname in index.items():
        jsonl_count = len(list(proj_dir.glob("*.jsonl")))
        counts[pname] = counts.get(pname, 0) + jsonl_count

    # Supplement with Obsidian (remote-only projects)
    if OBSIDIAN_SESSIONS and OBSIDIAN_SESSIONS.exists():
        local_projects = set(counts.keys())
        for md_file in OBSIDIAN_SESSIONS.glob("*.md"):
            fm = parse_frontmatter_file(md_file)
            if not fm:
                continue
            fm_projects = fm.get('projects', [])
            if not isinstance(fm_projects, list):
                continue
            for p in fm_projects:
                if p not in local_projects:
                    counts[p] = counts.get(p, 0) + 1

    if not counts:
        print("No projects found.")
        return

    print("\nProjects:\n")
    for pname, count in sorted(counts.items(), key=lambda x: -x[1]):
        print(f" {count:3}  {pname}")
    print(f"\n{len(counts)} projects total")


def main():
    parser = argparse.ArgumentParser(
        description='Recall sessions by date from Claude Code JSONL files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest='command', required=True)

    # list
    p_list = sub.add_parser('list', help='List sessions for a date')
    p_list.add_argument('date_expr', nargs='*', help='Date expression (e.g. yesterday, today, 2026-02-25)')
    p_list.add_argument('--project', help='Project path to scan')
    p_list.add_argument('--all-projects', action='store_true', help='Scan all projects')
    p_list.add_argument('--min-msgs', type=int, default=3, help='Min user messages (default: 3)')
    p_list.add_argument('--name', help='Filter by project name (substring match)')
    p_list.add_argument('--full-history', action='store_true', dest='full_history', help='Show full history (use with --name)')

    # expand
    p_expand = sub.add_parser('expand', help='Expand a session by ID')
    p_expand.add_argument('session_id', help='Session ID (prefix match)')
    p_expand.add_argument('--project', help='Project path to scan')
    p_expand.add_argument('--all-projects', action='store_true', help='Scan all projects')
    p_expand.add_argument('--max-msgs', type=int, default=50, help='Max messages to show (default: 50)')

    # projects
    sub.add_parser('projects', help='List all projects with session counts')

    args = parser.parse_args()

    if args.command == 'list':
        # Join multi-word date expressions
        if args.date_expr:
            args.date_expr = ' '.join(args.date_expr)
        elif args.name:
            # --name without date_expr defaults to last 14 days
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


if __name__ == '__main__':
    main()
