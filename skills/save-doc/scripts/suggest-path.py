#!/usr/bin/env python3
"""Rank $DOCS_DIR folders as save targets for the current project (git root, else cwd).

Usage:
    suggest-path.py [--cwd PATH]

Signals, strongest first:
  - docs in the folder carry `project:` frontmatter matching the repo name
  - folder path segments share name tokens with the repo (infra-clean ~ infra)
  - the docs top-level folder equals the repo's parent dir name (workspace/cochl/x -> cochl/)

Folders under an `_`-prefixed segment (e.g. _archive) are never candidates.
Ties go to the folder with the most recently modified doc.
Prints ranked candidates with recent titles, the full folder map for content-based
judgement, and a proposed new folder when nothing matches.
"""

import argparse
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from shared_utils import parse_frontmatter_file  # noqa: E402

TOKEN_SPLIT = re.compile(r'[-_./\s]+')
STOP_TOKENS = {'server', 'client', 'api', 'test', 'v2', 'prod', 'internal', 'kit', 'archive'}


def tokens(name: str) -> set[str]:
    return {t for t in TOKEN_SPLIT.split(name.lower()) if t and t not in STOP_TOKENS}


def project_root(cwd: Path) -> Path | None:
    """Git toplevel, else cwd itself; None when cwd is $HOME or above (no project context)."""
    out = subprocess.run(['git', '-C', str(cwd), 'rev-parse', '--show-toplevel'],
                         capture_output=True, text=True)
    if out.returncode == 0:
        return Path(out.stdout.strip())
    return None if cwd.resolve() in (Path.home(), *Path.home().parents) else cwd.resolve()


def scan_docs(docs_dir: Path) -> dict[str, dict]:
    """folder (relative) -> {count, projects, files: [(mtime, name)], recent: [name]}"""
    folders: dict[str, dict] = defaultdict(lambda: {'count': 0, 'projects': set(), 'files': []})
    for md in docs_dir.rglob('*.md'):
        rel = md.parent.relative_to(docs_dir).as_posix()
        if rel == '.' or '/.' in f'/{rel}':
            continue
        info = folders[rel]
        info['count'] += 1
        fm = parse_frontmatter_file(md) or {}
        if fm.get('project'):
            info['projects'].add(str(fm['project']))
            # _session-handoff/, _archive/ docs still identify the project folder above them
            parts = rel.split('/')
            hidden = next((i for i, seg in enumerate(parts) if seg.startswith('_')), None)
            if hidden:
                folders['/'.join(parts[:hidden])]['projects'].add(str(fm['project']))
        info['files'].append((md.stat().st_mtime, md.name))
    for d in docs_dir.rglob('*'):
        if d.is_dir() and not any(p.startswith('.') for p in d.relative_to(docs_dir).parts):
            folders[d.relative_to(docs_dir).as_posix()]  # include empty folders
    for info in folders.values():
        info['recent'] = [n for _, n in sorted(info['files'], reverse=True)[:3]]
    return folders


def score(folder: str, info: dict, repo: str, org: str) -> tuple[int, list[str]]:
    reasons = []
    s = 0
    repo_tokens = tokens(repo)
    if repo in info['projects']:
        s += 100
        reasons.append(f'project={repo}')
    elif any(repo_tokens & tokens(p) for p in info['projects']):
        s += 60
        reasons.append('project~' + ','.join(sorted(info['projects'])))
    seg_tokens = set().union(*(tokens(seg) for seg in folder.split('/')[1:])) if '/' in folder else set()
    overlap = repo_tokens & seg_tokens
    if overlap:
        s += 30 * len(overlap)
        reasons.append('path~' + ','.join(sorted(overlap)))
    if s and folder.split('/')[0] == org:
        s += 10
        reasons.append(f'org={org}')
    return s, reasons


def print_folder_map(folders: dict[str, dict]) -> None:
    print('## Folder map (folder  docs  projects)')
    for f in sorted(folders):
        info = folders[f]
        print(f'{f}/  {info["count"]}  {",".join(sorted(info["projects"]))}')


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--cwd', default=os.getcwd())
    args = parser.parse_args()

    docs_env = os.environ.get('DOCS_DIR')
    if not docs_env:
        print("Error: DOCS_DIR is not set. Run '. ~/.claude/env' first.", file=sys.stderr)
        sys.exit(1)
    docs_dir = Path(docs_env)
    docs_dir.mkdir(parents=True, exist_ok=True)

    folders = scan_docs(docs_dir)
    root = project_root(Path(args.cwd))
    if root is None:
        print(f'No project context ({args.cwd}); choose from the folder map by content.\n')
        print_folder_map(folders)
        return
    repo, org = root.name, root.parent.name

    def latest(f: str) -> float:
        return max((t for t, _ in folders[f]['files']), default=0)

    ranked = [(*score(f, i, repo, org), f) for f, i in folders.items()
              if not any(seg.startswith('_') for seg in f.split('/'))]
    ranked = sorted((r for r in ranked if r[0] > 0), key=lambda r: (-r[0], -latest(r[2])))

    print(f'Project: {repo} (parent: {org})  DOCS_DIR: {docs_dir}\n')
    if ranked:
        print('## Candidates')
        for s, reasons, f in ranked[:5]:
            info = folders[f]
            print(f'- {f}/  score={s} [{"; ".join(reasons)}] docs={info["count"]}')
            for name in info['recent']:
                print(f'    {name}')
    else:
        base = org if org in {f.split('/')[0] for f in folders} else ''
        print('## No matching folder')
        print(f'Proposed new folder: {base + "/" if base else ""}{repo}/')

    print()
    print_folder_map(folders)


if __name__ == '__main__':
    main()
