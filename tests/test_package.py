import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pstack_build', ROOT / 'tools/build.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class PackageTests(unittest.TestCase):
    def test_generated_tree_matches_locked_source_and_modes(self):
        result = subprocess.run([sys.executable, str(ROOT / 'tools/build.py'), '--check'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_all_source_commands_and_playbooks_survive(self):
        lock = json.loads((ROOT / 'upstream.lock.json').read_text())
        package = ROOT / 'plugins/pstack'
        self.assertEqual(len(lock['skills']), 56)
        self.assertEqual(len(lock['playbooks']), 23)
        for skill in lock['skills']:
            text = (package / 'skills' / skill / 'SKILL.md').read_text()
            self.assertIn(f'name: {skill}\n', text)
            self.assertIn('Codex adapter', text)
        for name in lock['playbooks']:
            relative = f'skills/poteto-mode/playbooks/{name}.md'
            self.assertEqual((package / relative).read_bytes(), (ROOT / 'vendor/pstack' / relative).read_bytes())

    def test_explicit_only_skills_preserve_native_invocation_policy(self):
        source = ROOT / 'vendor/pstack/skills'
        for skill in source.iterdir():
            if not (skill / 'SKILL.md').exists():
                continue
            if 'disable-model-invocation: true' in (skill / 'SKILL.md').read_text().split('\n---\n', 1)[0]:
                metadata = ROOT / 'plugins/pstack/skills' / skill.name / 'agents/openai.yaml'
                self.assertEqual(metadata.read_text(), 'policy:\n  allow_implicit_invocation: false\n')

    def test_provenance_accounts_for_every_source_and_dependency(self):
        lock = json.loads((ROOT / 'upstream.lock.json').read_text())
        ledger = json.loads((ROOT / 'plugins/pstack/provenance.json').read_text())
        self.assertEqual(set(lock['files']), set(ledger))
        for name, expected in lock['files'].items():
            self.assertEqual(build.digest((ROOT / 'vendor/pstack' / name).read_bytes()), expected)
        for name, expected in lock['dependencies'].items():
            self.assertEqual(build.digest((ROOT / 'vendor/cursor-team-kit' / name).read_bytes()), expected)

    def test_generator_detects_content_missing_extra_and_executable_drift(self):
        old = build.OUTPUT
        with tempfile.TemporaryDirectory() as temp:
            build.OUTPUT = Path(temp) / 'package'
            files, _ = build.render()
            for name, (data, mode) in files.items():
                path = build.OUTPUT / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
                path.chmod(mode)
            argv = sys.argv
            sys.argv = ['build.py', '--check']
            try:
                self.assertEqual(build.main(), 0)
                target = build.OUTPUT / 'skills/bro/SKILL.md'
                raw = target.read_bytes()
                target.write_bytes(raw + b'bad change')
                self.assertEqual(build.main(), 1)
                target.write_bytes(raw)
                target.unlink()
                self.assertEqual(build.main(), 1)
                target.write_bytes(raw)
                extra = build.OUTPUT / 'extra.txt'
                extra.write_text('extra')
                self.assertEqual(build.main(), 1)
                extra.unlink()
                executable = build.OUTPUT / 'skills/poteto-mode/scripts/worktree-audit.sh'
                executable.chmod(0o644)
                self.assertEqual(build.main(), 1)
            finally:
                sys.argv = argv
                build.OUTPUT = old

    def test_packaged_markdown_links_resolve(self):
        import re
        from urllib.parse import unquote
        root = ROOT / 'plugins/pstack'
        for path in root.rglob('*.md'):
            for href in re.findall(r'\]\(([^)\s]+)\)', path.read_text()):
                target = href.split('#')[0].split('?')[0]
                if not target or re.match(r'[a-zA-Z][a-zA-Z0-9+.-]*:', target) or any(c in target for c in '<>{}'):
                    continue
                if path.relative_to(root).as_posix() == 'skills/why/references/synthesizer-prompt.md' and target == 'url':
                    continue
                self.assertTrue((path.parent / unquote(target)).exists(), f'{path}: {href}')

    def test_manifests_resolve_and_both_formats_agree(self):
        root = ROOT / 'plugins/pstack'
        native = json.loads((root / 'plugin.json').read_text())
        compat = json.loads((root / '.codex-plugin/plugin.json').read_text())
        extension = native['extensions']['com.openai']
        for key in ('skills', 'hooks', 'onboardingSkill'):
            self.assertTrue((root / extension[key]).exists(), key)
            self.assertEqual(extension[key], compat[key])
        self.assertEqual(native['version'], compat['version'])
        marketplace = json.loads((ROOT / '.agents/plugins/marketplace.json').read_text())
        self.assertTrue((ROOT / marketplace['plugins'][0]['source']['path'] / 'plugin.json').exists())

    def test_hook_is_opt_in_and_reports_correct_protocol(self):
        with tempfile.TemporaryDirectory() as temp:
            env = {**os.environ, 'CODEX_HOME': temp}
            command = [sys.executable, str(ROOT / 'plugins/pstack/hooks/session_start.py')]
            self.assertEqual(subprocess.check_output(command, env=env, text=True), '')
            sheet = Path(temp) / 'pstack-models.md'
            sheet.write_text('session hook: off\n')
            self.assertEqual(subprocess.check_output(command, env=env, text=True), '')
            sheet.write_text('session hook: on\n')
            response = json.loads(subprocess.check_output(command, env=env, text=True))['hookSpecificOutput']
            self.assertEqual(response['hookEventName'], 'SessionStart')
            self.assertIn('spawn_agent and wait_agent', response['additionalContext'])
            self.assertIn(str(ROOT / 'plugins/pstack/skills/poteto-mode/SKILL.md'), response['additionalContext'])

    def test_transcripts_scope_by_metadata_never_message_text(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            sessions = root / 'sessions/2026/10/21'
            sessions.mkdir(parents=True)
            workspace = root / 'project'
            workspace.mkdir()
            matching = sessions / 'match.jsonl'
            matching.write_text(json.dumps({'type': 'session_meta', 'payload': {'id': 'match', 'cwd': str(workspace)}}) + '\nSECRET_MESSAGE_BODY')
            unrelated = sessions / 'unrelated.jsonl'
            unrelated.write_text(json.dumps({'type': 'session_meta', 'payload': {'id': 'other', 'cwd': str(root / 'other')}}) + '\n' + str(workspace))
            (sessions / 'malformed.jsonl').write_text('{broken')
            (sessions / 'link.jsonl').symlink_to(matching)
            (sessions / 'badtype.jsonl').write_text('[]\n')
            command = [sys.executable, str(ROOT / 'plugins/pstack/tools/transcripts.py'), '--workspace', str(workspace), '--codex-home', temp]
            output = subprocess.check_output(command, text=True)
            result = json.loads(output)
            self.assertEqual([item['id'] for item in result], ['match'])
            self.assertNotIn('SECRET', output)
            self.assertNotIn('other', output)

    def test_worktree_audit_preserves_spaces_and_never_assumes_safe(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / 'repo with spaces'
            repo.mkdir()
            def git(*args):
                return subprocess.run(['git', '-C', str(repo), *args], capture_output=True, text=True, check=True)
            git('init', '-b', 'main')
            git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', 'commit', '--allow-empty', '-m', 'base')
            wt = Path(temp) / 'worker with spaces'
            git('worktree', 'add', '-b', 'worker', str(wt))
            command = ['bash', str(ROOT / 'plugins/pstack/skills/poteto-mode/scripts/worktree-audit.sh'), '-b', 'main', str(repo)]
            result = subprocess.check_output(command, text=True)
            self.assertIn('\tunknown\tunknown\treview\t' + str(wt.resolve()), result)
            self.assertNotIn('\tsafe\t', result)
            (wt / 'tracked').write_text('first')
            subprocess.run(['git', '-C', str(wt), 'add', 'tracked'], check=True)
            result = subprocess.check_output(command, text=True)
            self.assertIn('\thold-wip\t' + str(wt.resolve()), result)


if __name__ == '__main__':
    unittest.main()
