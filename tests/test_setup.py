import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "tools/setup.py"


class SetupCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.home = self.root / "codex"

    def tearDown(self):
        self.temp.cleanup()

    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), "--codex-home", str(self.home), *map(str, args)], text=True, capture_output=True)

    def test_explicit_role_change_replaces_saved_choice_and_alias(self):
        self.home.mkdir(parents=True)
        (self.home / "pstack-models.md").write_text("hardest tasks: old-model @high\nfeature, refactoring: custom-model\n")
        choices = self.root / "models.json"
        choices.write_text(json.dumps({"hardest tasks": "gpt-6.1-sol @max", "feature, refactoring": "auto"}))
        result = self.run_cli("--models-file", choices)
        self.assertEqual(result.returncode, 0, result.stderr)
        sheet = (self.home / "pstack-models.md").read_text()
        self.assertIn("strongest judgment: gpt-6.1-sol @max", sheet)
        self.assertIn("feature, refactoring: auto", sheet)
        self.assertNotIn("old-model", sheet)

    def test_rerun_preserves_hook_and_default_effort(self):
        result = self.run_cli("--session-hook", "on", "--budget", "large")
        self.assertEqual(result.returncode, 0, result.stderr)
        before = (self.home / "pstack-models.md").read_text()
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.home / "pstack-models.md").read_text(), before)

    def test_quoted_features_table_refuses_without_writes(self):
        self.home.mkdir(parents=True)
        config = '["features"]\nmulti_agent = false\n'
        (self.home / "config.toml").write_text(config)
        result = self.run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertEqual((self.home / "config.toml").read_text(), config)
        self.assertEqual([p.name for p in self.home.iterdir()], ["config.toml"])

    def test_saved_unavailable_model_refuses_without_writes(self):
        self.home.mkdir(parents=True)
        sheet = "feature, refactoring: unavailable-model\n"
        (self.home / "pstack-models.md").write_text(sheet)
        result = self.run_cli("--available-model", "gpt-6.1-sol", "--available-model", "gpt-6-luna")
        self.assertEqual(result.returncode, 2)
        self.assertEqual((self.home / "pstack-models.md").read_text(), sheet)
        self.assertFalse((self.home / "config.toml").exists())

    def test_features_without_final_newline_are_enabled(self):
        import tomllib
        for source in ("[features]", "[features]\n# user note", "[features]\nother = true"):
            with self.subTest(source=source):
                self.home.mkdir(parents=True, exist_ok=True)
                (self.home / "config.toml").write_text(source)
                result = self.run_cli()
                self.assertEqual(result.returncode, 0, result.stderr)
                parsed = tomllib.loads((self.home / "config.toml").read_text())
                self.assertIs(parsed["features"]["multi_agent"], True)
                if "other" in source:
                    self.assertIs(parsed["features"]["other"], True)
                if "note" in source:
                    self.assertIn("# user note\n", (self.home / "config.toml").read_text())

    def test_final_saved_alias_roles_validate_against_host(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("pstack_setup", SCRIPT)
        setup = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(setup)
        self.home.mkdir(parents=True)
        sheet = "\n".join(role + ": auto" for role in setup.ROLE_DEFAULTS) + "\n"
        (self.home / "pstack-models.md").write_text(sheet)
        result = self.run_cli("--available-model", "other-entitled-model")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("gpt-6", (self.home / "pstack-models.md").read_text())

    def test_array_table_after_features_keeps_agent_flag_in_features(self):
        import tomllib
        self.home.mkdir(parents=True)
        config = '[features]\nother = true\n\n[[skills.config]]\npath = "/tmp/a"\nenabled = true\n'
        (self.home / "config.toml").write_text(config)
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        parsed = tomllib.loads((self.home / "config.toml").read_text())
        self.assertIs(parsed["features"]["multi_agent"], True)
        self.assertEqual(parsed["skills"]["config"], [{"path": "/tmp/a", "enabled": True}])

    def test_symlinked_managed_paths_are_rejected_before_any_write(self):
        for name in ("config.toml", "AGENTS.md", "pstack-models.md"):
            with self.subTest(name=name):
                for path in self.home.iterdir() if self.home.exists() else []:
                    path.unlink()
                self.home.mkdir(parents=True, exist_ok=True)
                target = self.root / (name + '.target')
                target.write_text('user content')
                (self.home / name).symlink_to(target)
                result = self.run_cli()
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn('symlink', result.stderr)
                self.assertTrue((self.home / name).is_symlink())
                self.assertEqual(target.read_text(), 'user content')
                self.assertEqual([p.name for p in self.home.iterdir()], [name])

    def test_table_like_multiline_string_never_changes_unrelated_values(self):
        self.home.mkdir(parents=True)
        config = '[features]\nnotes = """\n[other]\n"""\n'
        (self.home / "config.toml").write_text(config)
        result = self.run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertIn('safely change only', result.stderr)
        self.assertEqual((self.home / "config.toml").read_text(), config)
        self.assertEqual([p.name for p in self.home.iterdir()], ['config.toml'])

    def test_fresh_and_rerun_are_idempotent_and_enable_agents(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        config = (self.home / "config.toml").read_text()
        self.assertIn("[features]\nmulti_agent = true", config)
        sheet = (self.home / "pstack-models.md").read_text()
        self.assertIn("arena runners: gpt-6.1-sol @medium, gpt-6.1-sol @high, gpt-6.1-sol @xhigh, gpt-6.1-sol @max", sheet)
        self.assertIn("strongest judgment: gpt-6.1-sol", sheet)
        before = {p.name: p.read_bytes() for p in self.home.iterdir()}
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.home.iterdir()})
        self.assertNotIn(".bak", result.stdout)

    def test_preserves_unrelated_config_instructions_and_custom_role_value(self):
        self.home.mkdir(parents=True)
        config = '# user comment\n[other]\nvalue = 7\n\n[features]\ncustom = "keep"\nmulti_agent = false # explain\n\n[nested]\nvalue = "x"\n'
        (self.home / "config.toml").write_text(config)
        agents = "User rules stay.\n"
        (self.home / "AGENTS.md").write_text(agents)
        sheet = "# user notes\nfeature, refactoring: my-model @high\ncustom role: untouched\n"
        (self.home / "pstack-models.md").write_text(sheet)
        result = self.run_cli("--budget", "small")
        self.assertEqual(result.returncode, 0, result.stderr)
        new_config = (self.home / "config.toml").read_text()
        self.assertIn('# user comment\n[other]\nvalue = 7', new_config)
        self.assertIn('custom = "keep"\nmulti_agent = true # explain', new_config)
        self.assertIn('[nested]\nvalue = "x"', new_config)
        new_sheet = (self.home / "pstack-models.md").read_text()
        self.assertIn("feature, refactoring: my-model @high", new_sheet)
        self.assertIn("custom role: untouched", new_sheet)
        self.assertIn("default effort: medium", new_sheet)
        new_agents = (self.home / "AGENTS.md").read_text()
        self.assertTrue(new_agents.startswith(agents))
        self.assertIn("spawn_agent` and `wait_agent", new_agents)
        self.assertTrue((self.home / "config.toml.bak").exists())

    def test_budget_changes_default_effort_without_rewriting_explicit_roles(self):
        result = self.run_cli("--budget", "large", "--session-hook", "off")
        self.assertEqual(result.returncode, 0, result.stderr)
        sheet = (self.home / "pstack-models.md").read_text()
        self.assertIn("default effort: xhigh", sheet)
        self.assertIn("session hook: off", sheet)
        self.assertIn("gpt-6.1-sol @max", sheet)

    def test_check_reports_plan_without_creating_files(self):
        result = self.run_cli("--check", "--budget", "medium")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report["check"])
        self.assertEqual(len(report["changes"]), 3)
        self.assertFalse(self.home.exists())

    def test_malformed_config_rejects_before_any_write(self):
        self.home.mkdir(parents=True)
        (self.home / "config.toml").write_text("[bad\n")
        result = self.run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertIn("malformed", result.stderr)
        self.assertEqual({p.name for p in self.home.iterdir()}, {"config.toml"})

    def test_unsupported_inline_features_config_rejects_before_any_write(self):
        self.home.mkdir(parents=True)
        (self.home / "config.toml").write_text("features = { custom = true }\n")
        result = self.run_cli()
        self.assertEqual(result.returncode, 2)
        self.assertIn("inline value", result.stderr)
        self.assertEqual({p.name for p in self.home.iterdir()}, {"config.toml"})

    def test_available_models_checked_only_when_supplied(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        other_home = self.root / "other"
        result = subprocess.run([sys.executable, str(SCRIPT), "--codex-home", str(other_home), "--available-model", "gpt-6-luna"], text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("unavailable", result.stderr)
        self.assertFalse(other_home.exists())

    def test_models_file_validates_roles_values_and_aliases(self):
        path = self.root / "models.json"
        path.write_text(json.dumps({"bug-fix": "auto @high", "arena cross-judge pool": ["inherit-parent", "gpt-6-luna @max"]}))
        result = self.run_cli("--models-file", path, "--available-model", "gpt-6-luna", "--available-model", "gpt-6.1-sol")
        self.assertEqual(result.returncode, 0, result.stderr)
        sheet = (self.home / "pstack-models.md").read_text()
        self.assertIn("bug-fix: auto @high", sheet)
        self.assertIn("arena cross-judge pool: inherit-parent, gpt-6-luna @max", sheet)
        path.write_text('{"unknown role": "auto"}')
        bad_home = self.root / "bad"
        result = subprocess.run([sys.executable, str(SCRIPT), "--codex-home", str(bad_home), "--models-file", str(path)], text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertFalse(bad_home.exists())

    def test_existing_config_without_features_gets_table(self):
        self.home.mkdir(parents=True)
        (self.home / "config.toml").write_text('[model]\nname = "keep"\n')
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        parsed = __import__("tomllib").loads((self.home / "config.toml").read_text())
        self.assertEqual(parsed["model"]["name"], "keep")
        self.assertTrue(parsed["features"]["multi_agent"])


if __name__ == "__main__":
    unittest.main()
