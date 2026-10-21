#!/usr/bin/env python3
"""List Codex transcript paths matching exact first-line workspace metadata."""
import argparse
import json
import os
from pathlib import Path


def workspace_sessions(home, workspace):
    expected = workspace.resolve()
    for directory in ('sessions', 'archived_sessions'):
        root = home / directory
        if not root.is_dir():
            continue
        for path in sorted(root.rglob('*.jsonl')):
            if path.is_symlink():
                continue
            try:
                with path.open('r', encoding='utf-8') as stream:
                    line = stream.readline(262145)
                if len(line) > 262144:
                    continue
                record = json.loads(line)
                if record.get('type') != 'session_meta':
                    continue
                payload = record.get('payload', {})
                cwd = payload.get('cwd')
                if not isinstance(cwd, str) or not Path(cwd).is_absolute():
                    continue
                if Path(cwd).resolve() == expected:
                    yield {'path': str(path.resolve()), 'id': payload.get('id'), 'cwd': str(expected)}
            except (OSError, ValueError, AttributeError, TypeError):
                continue


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--codex-home', type=Path, default=Path(os.environ.get('CODEX_HOME', Path.home() / '.codex')))
    args = parser.parse_args()
    if not args.workspace.is_absolute():
        parser.error('--workspace must be absolute')
    print(json.dumps(list(workspace_sessions(args.codex_home, args.workspace)), indent=2))


if __name__ == '__main__':
    main()
