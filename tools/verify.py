#!/usr/bin/env python3
"""Run port and upstream checks and save their actual results."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--with-install', action='store_true')
    parser.add_argument('--output', type=Path, default=ROOT / '.audit/verification')
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    scripts = ROOT / 'plugins/pstack/skills/poteto-mode/scripts'
    commands = [([sys.executable, 'tools/build.py', '--check'], ROOT),
                ([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'], ROOT),
                (['bun', 'install', '--frozen-lockfile'], scripts),
                (['bun', 'test', 'orch', 'watch-pr', 'check-plan.test.ts'], scripts),
                (['bun', 'run', 'typecheck'], scripts)]
    if args.with_install:
        commands.append(([sys.executable, 'tools/smoke_install.py'], ROOT))
    results = []
    with args.output.with_suffix('.txt').open('w') as log:
        for command, cwd in commands:
            start = datetime.now(timezone.utc).isoformat()
            print('Running ' + ' '.join(command), flush=True)
            log.write(f'\n{start}\n$ {" ".join(command)}\ncwd: {cwd}\n')
            log.flush()
            result = subprocess.run(command, cwd=cwd, stdout=log, stderr=subprocess.STDOUT, timeout=180)
            results.append({'startedAt': start, 'command': command, 'cwd': str(cwd.relative_to(ROOT)) or '.', 'exitCode': result.returncode})
            log.write(f'\nexitCode: {result.returncode}\n')
            log.flush()
            if result.returncode:
                break
    passed = len(results) == len(commands) and all(item['exitCode'] == 0 for item in results)
    report = {'status': 'PASS' if passed else 'FAIL', 'finishedAt': datetime.now(timezone.utc).isoformat(),
              'includeInstall': args.with_install, 'results': results}
    args.output.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n')
    print(report['status'] + '. Receipts in ' + str(args.output.with_suffix('.json')))
    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main())
