#!/usr/bin/env python3
import json
import os
from pathlib import Path
import shutil
import select
import time
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def discover_skills(env, workspace):
    with tempfile.TemporaryFile() as errors:
        process = subprocess.Popen(['codex', 'app-server', '--stdio'], env=env,
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=errors)
        buffer = b''
        def request(identifier, method, params):
            nonlocal buffer
            process.stdin.write((json.dumps({'id': identifier, 'method': method, 'params': params}) + '\n').encode())
            process.stdin.flush()
            deadline = time.monotonic() + 45
            while time.monotonic() < deadline:
                if b'\n' in buffer:
                    line, buffer = buffer.split(b'\n', 1)
                    message = json.loads(line)
                    if message.get('id') == identifier:
                        if 'error' in message:
                            raise RuntimeError(message['error'])
                        return message['result']
                    continue
                readable, _, _ = select.select([process.stdout], [], [], max(0, deadline - time.monotonic()))
                if not readable:
                    break
                chunk = os.read(process.stdout.fileno(), 65536)
                if not chunk:
                    break
                buffer += chunk
            raise RuntimeError('Codex app-server skill discovery did not respond')
        try:
            request(1, 'initialize', {'clientInfo': {'name': 'pstack-smoke', 'version': '1.0'}, 'capabilities': {'experimentalApi': True}})
            process.stdin.write(b'{"method":"initialized"}\n')
            process.stdin.flush()
            result = request(2, 'skills/list', {'cwds': [str(workspace)], 'forceReload': True})
            return result
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            process.stdin.close()
            process.stdout.close()


def main():
    if not shutil.which('codex'):
        raise SystemExit('codex CLI is required for the installation smoke test')
    with tempfile.TemporaryDirectory(prefix='pstack-install-') as temp:
        env = {**os.environ, 'CODEX_HOME': temp}
        def run(*args):
            result = subprocess.run(['codex', 'plugin', *args, '--json'], env=env, text=True, capture_output=True, check=True, timeout=60)
            return json.loads(result.stdout)
        added = run('marketplace', 'add', str(ROOT))
        assert added['marketplaceName'] == 'bane-codex-pstack', added
        installed = run('add', 'pstack@bane-codex-pstack')
        path = Path(installed['installedPath'])
        manifest = json.loads((path / 'plugin.json').read_text())
        assert manifest['name'] == 'pstack'
        assert (path / 'tools/setup.py').is_file()
        skills = sorted(p.parent.name for p in (path / 'skills').glob('*/SKILL.md'))
        lock = json.loads((ROOT / 'upstream.lock.json').read_text())
        assert set(lock['skills']) <= set(skills), skills
        for name in skills:
            assert 'Codex adapter' in (path / 'skills' / name / 'SKILL.md').read_text(), name
        setup = subprocess.run(['python3', str(path / 'tools/setup.py'), '--codex-home', str(Path(temp) / 'setup-home'), '--check'], text=True, capture_output=True, check=True)
        assert json.loads(setup.stdout)['check'] is True
        discovery = discover_skills(env, ROOT)
        entries = discovery['data']
        discovered = [skill for entry in entries for skill in entry['skills'] if str(path) in skill['path']]
        errors = [error for entry in entries for error in entry['errors'] if str(path) in error['path']]
        assert not errors, errors
        assert {skill['name'].removeprefix('pstack:') for skill in discovered} == set(skills), [skill['name'] for skill in discovered]
        print(json.dumps({'nativeDiscovery': len(discovered), 'status': 'PASS' , 'version': installed['version'], 'skills': len(skills), 'isolated': True}, indent=2))


if __name__ == '__main__':
    main()
