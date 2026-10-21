#!/usr/bin/env python3
"""Read-only Codex worktree audit. Unknown chat ownership always needs review."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time


def git(repo, *args, check=True):
    return subprocess.run(['git', '-C', str(repo), *args], text=True, capture_output=True, check=check).stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-b', '--base')
    parser.add_argument('repo', nargs='?', default='.')
    args = parser.parse_args()
    repo = Path(git(args.repo, 'rev-parse', '--show-toplevel'))
    base = args.base
    if not base:
        default = git(repo, 'symbolic-ref', '--short', 'refs/remotes/origin/HEAD', check=False)
        for candidate in (default, 'origin/main', 'origin/master'):
            if candidate and git(repo, 'rev-parse', '--verify', candidate + '^{commit}', check=False):
                base = candidate
                break
    if not base or not git(repo, 'rev-parse', '--verify', base + '^{commit}', check=False):
        parser.error('no valid base ref; pass -b <ref>')
    output = git(repo, 'worktree', 'list', '--porcelain', '-z')
    entries = [entry for entry in output.split('\0\0') if entry]
    print(f'# base: {base}; chat ownership unknown; confirm native chat state before cleanup')
    print('SIZE\tAGE\tMERGED\tDIRTY\tREMOTE\tPR\tLAST_CHAT\tBUCKET\tWORKTREE')
    for entry in entries[1:]:
        values = dict(field.split(' ', 1) for field in entry.split('\0') if ' ' in field)
        wt = Path(values['worktree'])
        head = values['HEAD']
        state = git(wt, 'status', '--porcelain')
        merged = subprocess.run(['git', '-C', str(repo), 'merge-base', '--is-ancestor', head, base], capture_output=True).returncode == 0
        dirty = 'wip' if any(not line.startswith('??') for line in state.splitlines()) else 'scratch' if state else 'clean'
        bucket = 'hold-wip' if dirty == 'wip' else 'review'
        stamp = git(wt, 'log', '-1', '--format=%ct', check=False)
        age = f'{max(0, int((time.time() - int(stamp)) / 86400))}d' if stamp.isdigit() else '?'
        size = subprocess.run(['du', '-sh', str(wt)], text=True, capture_output=True).stdout.split('\t')[0].strip() or '?'
        branch = values.get('branch', '').removeprefix('refs/heads/')
        remote_head = git(wt, 'rev-parse', '--verify', 'refs/remotes/origin/' + branch, check=False) if branch else ''
        remote = 'detached' if not branch else 'no-remote' if not remote_head else 'pushed' if remote_head == head else 'diverged'
        print('\t'.join((size, age, 'YES' if merged else 'no', dirty, remote, 'unknown', 'unknown', bucket, str(wt))))


if __name__ == '__main__':
    try:
        main()
    except (OSError, subprocess.CalledProcessError, ValueError) as exc:
        print(f'worktree-audit: {exc}', file=sys.stderr)
        sys.exit(1)
