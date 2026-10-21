#!/usr/bin/env python3
"""Render the pinned upstream tree with explicit Codex adapters."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'vendor/pstack'
OUTPUT = ROOT / 'plugins/pstack'
DEPENDENCIES = ('deslop', 'control-cli', 'control-ui')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def upstream_files():
    return {p.relative_to(SOURCE).as_posix(): p for p in sorted(SOURCE.rglob('*')) if p.is_file()}


def render():
    files = {name: (path.read_bytes(), path.stat().st_mode & 0o777) for name, path in upstream_files().items()}
    files.pop('.cursor-plugin/plugin.json')
    for name in list(files):
        if name.endswith('/SKILL.md'):
            raw = files[name][0].decode()
            target = '../../docs/harness/codex.md' if name.startswith('skills/') else os.path.relpath('docs/harness/codex.md', str(Path(name).parent))
            header = f'On Codex, read [the Codex adapter]({target}) before following this skill. Its runtime mappings override the Cursor-specific instructions below.\n\n'
            front, body = raw.split('\n---\n', 1)
            if 'disable-model-invocation: true' in front:
                metadata = name.removesuffix('SKILL.md') + 'agents/openai.yaml'
                files[metadata] = (b'policy:\n  allow_implicit_invocation: false\n', 0o644)
            front = '\n'.join(line for line in front.split('\n') if not line.startswith(('disable-model-invocation:', 'icon:', 'color:')))
            files[name] = ((front + '\n---\n\n' + header + body.lstrip()).encode(), files[name][1])
    for dep in DEPENDENCIES:
        base = ROOT / 'vendor/cursor-team-kit/skills' / dep
        for path in sorted(base.rglob('*')):
            if path.is_file():
                name = f'skills/{dep}/{path.relative_to(base).as_posix()}'
                data = path.read_bytes()
                if path.name == 'SKILL.md':
                    front, body = data.decode().split('\n---\n', 1)
                    data = (front + '\n---\n\nOn Codex, read [the Codex adapter](../../docs/harness/codex.md) before following this dependency skill.\n\n' + body.lstrip()).encode()
                files[name] = (data, path.stat().st_mode & 0o777)
    files['DEPENDENCY-LICENSE'] = ((ROOT / 'vendor/cursor-team-kit/LICENSE').read_bytes(), 0o644)
    for path in sorted((ROOT / 'adapters').rglob('*')):
        if path.is_file():
            files[path.relative_to(ROOT / 'adapters').as_posix()] = (path.read_bytes(), path.stat().st_mode & 0o777)
    if (ROOT / 'tools/setup.py').exists():
        files['tools/setup.py'] = ((ROOT / 'tools/setup.py').read_bytes(), 0o644)
    manifest = {
        '$schema': 'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json',
        'name': 'pstack', 'version': '0.15.29-codex.2',
        'description': 'Lauren Tan\'s pstack workflows adapted for native Codex skills and subagents.',
        'author': {'name': 'Bane Stojanovic (Codex port); Lauren Tan (upstream)'},
        'homepage': 'https://github.com/banestojanovic/bane-codex-pstack',
        'repository': 'https://github.com/banestojanovic/bane-codex-pstack', 'license': 'MIT',
        'extensions': {'com.openai': {
            'skills': './skills/', 'hooks': './hooks/hooks.json',
            'onboardingSkill': './skills/setup-pstack/SKILL.md',
            'interface': {'displayName': 'pstack for Codex', 'shortDescription': 'Rigorous workflows with native Codex delegation',
                          'developerName': 'Bane Stojanovic', 'category': 'Developer Tools',
                          'capabilities': ['Read', 'Write', 'Interactive'],
                          'websiteURL': 'https://github.com/banestojanovic/bane-codex-pstack',
                          'logo': './assets/logo.png', 'composerIcon': './assets/logo.png',
                          'defaultPrompt': ['Use $pstack:poteto-mode for this task.', 'Run $pstack:setup-pstack.']}}}
    }
    files['plugin.json'] = ((json.dumps(manifest, indent=2) + '\n').encode(), 0o644)
    compatibility = {key: value for key, value in manifest.items() if key not in ('$schema', 'extensions')}
    compatibility.update(manifest['extensions']['com.openai'])
    files['.codex-plugin/plugin.json'] = ((json.dumps(compatibility, indent=2) + '\n').encode(), 0o644)
    skills = sorted(path.name for path in (SOURCE / 'skills').iterdir() if (path / 'SKILL.md').is_file())
    playbooks = sorted(p.stem for p in (SOURCE / 'skills/poteto-mode/playbooks').glob('*.md'))
    lock = {'repository': 'https://github.com/cursor/plugins', 'commit': '190d28736eff128ec94f502a22c7fe0c4b56cd37',
            'version': '0.15.29', 'skills': skills, 'playbooks': playbooks,
            'files': {name: digest(path.read_bytes()) for name, path in upstream_files().items()},
            'dependencies': {p.relative_to(ROOT / 'vendor/cursor-team-kit').as_posix(): digest(p.read_bytes())
                             for p in sorted((ROOT / 'vendor/cursor-team-kit').rglob('*')) if p.is_file()}}
    ledger = {name: {'upstream': digest(path.read_bytes()),
                     'generated': digest(files[name][0]) if name in files else None,
                     'status': 'omitted Cursor manifest' if name not in files else
                               'unchanged' if files[name][0] == path.read_bytes() else
                               'Codex overlay' if (ROOT / 'adapters' / name).exists() else
                               'Codex adapter header and supported frontmatter' if name.endswith('/SKILL.md') else 'Codex overlay'}
              for name, path in upstream_files().items()}
    files['provenance.json'] = ((json.dumps(ledger, indent=2) + '\n').encode(), 0o644)
    return files, lock


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    files, lock = render()
    lock_bytes = (json.dumps(lock, indent=2) + '\n').encode()
    if args.check:
        have = {p.relative_to(OUTPUT).as_posix(): p for p in OUTPUT.rglob('*') if p.is_file() and 'node_modules' not in p.parts and '__pycache__' not in p.parts}
        drift = sorted(set(files) ^ set(have))
        drift += [name for name in files.keys() & have.keys()
                  if files[name][0] != have[name].read_bytes() or bool(files[name][1] & 0o111) != bool(have[name].stat().st_mode & 0o111)]
        if not (ROOT / 'upstream.lock.json').exists() or (ROOT / 'upstream.lock.json').read_bytes() != lock_bytes:
            drift.append('upstream.lock.json')
        if drift:
            print('Generated files differ. Run python3 tools/build.py\n' + '\n'.join(drift[:30]), file=sys.stderr)
            return 1
    else:
        if OUTPUT.exists():
            shutil.rmtree(OUTPUT)
        for name, (data, mode) in files.items():
            target = OUTPUT / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            target.chmod(mode)
        (ROOT / 'upstream.lock.json').write_bytes(lock_bytes)
    print(f'OK: {len(lock["skills"])} upstream skills, {len(lock["playbooks"])} playbooks, {len(DEPENDENCIES)} dependency skills; {len(files)} packaged files')
    return 0


if __name__ == '__main__':
    sys.exit(main())
