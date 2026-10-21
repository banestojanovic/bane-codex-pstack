# pstack for Codex

This installed plugin ports Lauren Tan's pstack 0.15.29 to native Codex skills. It retains all 56 upstream skill names and 23 playbooks, plus the dependency skills `deslop`, `control-cli`, and `control-ui`.

## Install and set up

```sh
codex plugin marketplace add banestojanovic/bane-codex-pstack
codex plugin add pstack@bane-codex-pstack
```

Start a new chat. Choose `setup-pstack` in `/skills` or invoke `$pstack:setup-pstack`. Setup detects models, asks for a budget and role choices, then writes a model sheet and managed instructions under `$CODEX_HOME`, defaulting to `~/.codex`. Existing unrelated configuration and instructions are preserved. Start a new chat after setup.

## Start work

```text
$pstack:poteto-mode add a --json flag. Existing text output stays byte-identical. Verify both.
$pstack:how explain the queue's runtime flow
$pstack:interrogate review the current diff for correctness
$pstack:poteto-help which workflow should I use?
```

Read [all command names](docs/commands.md), [the full upstream guide](docs/guide/README.md), and [the Codex adapter](docs/harness/codex.md). The adapter overrides Cursor-specific names in the preserved guide. Codex uses `$name` or the skill picker. Plugins cannot guarantee Cursor's literal `/name` command syntax.

The default models are Sol for coordination and judgment, Luna for scoped implementation and evidence, and four independent Sol panel agents at medium, high, xhigh, and max effort. Availability depends on the host. Saved choices do not prove entitlement. Native subagents require host support. Required review stays blocked if reviewers cannot run.

For optional session routing, use `python3 <this-plugin-root>/tools/setup.py --session-hook on` and trust the plugin through `/hooks`. Hook output defaults to off. `--session-hook off` disables it. Explicit `$pstack:poteto-mode` needs no hook.

Cursor Custom Modes, isolated cloud VMs, cloud video, and Cursor webhook/secret services do not have exact equivalents in this plugin. `make-bot-ui` and Benny retain their source but their hosted backend is unsupported. The adapter names the limits and prevents fake-success reports.

The watcher and orchestration tools require Bun and install pinned dependencies on first use. Forge workflows need authenticated `gh` or supported Origin tooling. Drivers and model checkers depend on the project. Setup and hooks require Python 3.11+.

For source, tests, and update instructions, see [the repository](https://github.com/banestojanovic/bane-codex-pstack). Original source is pinned in `vendor/pstack` there. The installed `provenance.json` accounts for every source file. Original [MIT license](LICENSE) and [dependency license](DEPENDENCY-LICENSE) are retained.
