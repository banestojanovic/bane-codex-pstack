# pstack for Codex

Lauren Tan's [pstack](https://github.com/cursor/plugins/tree/main/pstack), adapted for Codex CLI and desktop. It preserves the 56 upstream skills, 23 playbooks, guide, agent briefs, scripts, and resources at Cursor pstack **0.15.29**, commit `190d28736eff128ec94f502a22c7fe0c4b56cd37`.

The port uses native Codex skills and `spawn_agent` / `wait_agent`. It includes setup, configurable model roles, four independent review panel entries, and an optional session routing hook. Source preservation is verified by hashes and a deterministic build. [Local validation](docs/parity.md) passed 28 port tests, 68 upstream tests, strict TypeScript checks, and native installation and discovery of all 59 packaged skills. It is a community port under MIT, not an official Cursor or OpenAI plugin.

## Install

Use a current Codex client with plugin marketplace support. Python 3.11+ is required for setup and the routing hook. In a terminal, run:

```sh
codex plugin marketplace add banestojanovic/bane-codex-pstack
codex plugin add pstack@bane-codex-pstack
```

Open a new Codex chat, use `/skills` or the skill picker, and choose `setup-pstack`. You can also type:

```text
$pstack:setup-pstack
```

Setup detects the models your current host offers, asks for a budget and role choices, enables native multi-agent support, and preserves unrelated settings. It writes `$CODEX_HOME/pstack-models.md` and a managed loader block in `$CODEX_HOME/AGENTS.md`, using `~/.codex` when `CODEX_HOME` is unset. It backs up existing files when they change. Restart Codex or start a new chat after setup.

For desktop clients without the CLI install commands, add this repository as a marketplace source in the plugin browser, install **pstack for Codex**, and start a new chat. The exact browser labels depend on the client. A local checkout also works:

```sh
git clone https://github.com/banestojanovic/bane-codex-pstack.git
cd bane-codex-pstack
codex plugin marketplace add .
codex plugin add pstack@bane-codex-pstack
```

An older Codex client without native plugins can discover the skill tree through a project symlink. This is skills-only and has no plugin hook:

```sh
mkdir -p /path/to/project/.agents/skills
ln -s /absolute/path/to/bane-codex-pstack/plugins/pstack/skills /path/to/project/.agents/skills/pstack
```

Keep the checkout available so relative resources resolve. Avoid installing two pstack distributions at once. Disable or remove the older `pstack@pstack-claude` plugin before relying on this port, since both expose the same skill names. This repository does not modify existing installations for you.

## Use the same workflow names

Start a task with its goal and a concrete check:

```text
$pstack:poteto-mode add a --json flag. Existing text output must stay byte-identical. Verify both.
$pstack:how explain how this project's job queue works
$pstack:architect design retries without duplicate execution
$pstack:interrogate review the current branch for correctness
$pstack:poteto-help which workflow should I use?
```

[All commands](docs/commands.md) retain their upstream names. The native loader exposes `pstack:name`, so `$pstack:poteto-mode` is the unambiguous plugin reference. Skills-only installs use `$poteto-mode`. Codex's supported invocation is a skill reference or picker. A plugin cannot add arbitrary built-in `/name` commands to Codex's parser, so Cursor's literal `/poteto-mode` syntax is not guaranteed. There is no claim of exact slash-menu parity.

Read the [Codex guide](docs/guide.md), [runtime adapter](plugins/pstack/docs/harness/codex.md), or the complete [upstream guide](plugins/pstack/docs/guide/README.md). The upstream guide remains intact and describes Cursor examples. The Codex adapter overrides its runtime-specific instructions.

## Models and budgets

The defaults use `gpt-6.1-sol` for coordination, architecture, judgment, difficult implementation, and review. `gpt-6-luna` handles scoped implementation and exploration. Arena, architect, and interrogate each use four independent Sol agents at medium, high, xhigh, and max effort. This has reduced model diversity compared with upstream's mixed-model panels, which verdicts must disclose.

Model availability depends on your account and host. Setup validates selected IDs against the models exposed by that host. It never silently substitutes a model. With no model listing, it asks you for available choices. A saved model sheet alone does not prove entitlement.

Budget selects the default effort for role entries with no explicit `@effort`. Explicit panel efforts and saved custom suffixes remain intact. To change those, choose explicit role entries during setup. `session` sets no default override. `auto` and `inherit-parent` omit the child model and inherit the parent. Setup does not change the parent chat model.

For a scriptable dry run:

```sh
python3 tools/setup.py --check --budget session
python3 tools/setup.py --budget session --available-model gpt-6.1-sol --available-model gpt-6-luna
```

For persistent routing, pass `--session-hook on` and trust the plugin hook through `/hooks` if your host offers it. It routes nontrivial work through poteto-mode on startup, resume, clear, compact, and fork. Default hook output is off. `--session-hook off` disables it. A standing instruction in project `AGENTS.md` is another option. Explicit `$pstack:poteto-mode` needs neither.

## Compatibility limits

| Upstream feature | Codex behavior |
| --- | --- |
| Skills, principles, playbooks, model roles | Preserved, with native runtime mappings. |
| Parallel workers | Native subagents in local worktrees. Shared host, no isolated cloud VM. |
| Independent review | Same gate. Blocked when reviewers cannot run. Never replaced by self-review. |
| Cursor Custom Modes | Explicit skill invocation, standing instructions, or optional trusted hook. |
| `/loop` and unattended wakes | Active-session native waits, or user-authorized Codex heartbeat when available. No persistent process guarantee. |
| Bugbot | Existing forge review threads can be triaged. Cursor's review service is not bundled. |
| CLI and UI verification | Dependency skills included. Actual drivers and app access depend on the host. |
| `make-bot-ui` | Name and workflow source retained. Cursor webhook/secret backend is unsupported on Codex. |
| Benny automation | Source and templates retained. Cursor routines cannot run on Codex without a separately built backend. |

These limitations mean this is a workflow port, **not an exact behavioral replica of Cursor's hosted services**. See [parity and validation](docs/parity.md) for what has actually been tested.

The upstream watcher and orchestration CLIs require Bun. They install their pinned dependencies on first use. GitHub operations require authenticated `gh`, or use Origin where the upstream workflow supports it. Some shell workflows require `jq`. Drivers, browsers, deployment tools, and model checkers are project-specific and are not installed automatically. The Codex worktree audit is conservative and always asks for ownership review before cleanup.

## Verify and maintain

Python 3.11+, Node.js, and Bun are needed for the full test suite. The port's Python tests have no third-party dependencies.

```sh
python3 tools/build.py --check
python3 -m unittest discover -s tests -v
python3 tools/smoke_install.py
cd plugins/pstack/skills/poteto-mode/scripts
bun install --frozen-lockfile
bun test orch watch-pr check-plan.test.ts
```

`tools/smoke_install.py` uses a temporary `CODEX_HOME` and the actual Codex marketplace/install CLI. It does not change your real installation or authenticate accounts. Behavioral model probes are separate from package/install checks because model output is not deterministic.

`vendor/pstack/` is untouched source. `adapters/` holds deliberate Codex differences. `tools/build.py` generates `plugins/pstack/` and `upstream.lock.json`. Never edit generated files directly. `provenance.json` accounts for every upstream file, including the removed Cursor manifest. Three dependency skills are vendored from `cursor-team-kit` at the same commit, with its MIT license retained. See [architecture](docs/architecture.md) for the port design.

After updating adapters, run `python3 tools/build.py`, verify, and commit both source and generated output. For an upstream update, review a new pinned commit, replace the vendor snapshot deliberately, update the generator pin, regenerate, inspect the provenance differences, and rerun all checks. Marketplace updates are explicit:

```sh
codex plugin marketplace upgrade bane-codex-pstack
codex plugin add pstack@bane-codex-pstack
```

Remove this plugin with `codex plugin remove pstack@bane-codex-pstack`. Setup files remain yours. Remove only the managed loader block and model sheet if you no longer use them; do not delete unrelated global instructions or configuration.

Original pstack copyright 2026 Lauren Tan. The original [MIT license](LICENSE) is preserved. Codex adapter changes are also MIT. [Cursor team kit license](vendor/cursor-team-kit/LICENSE) covers the bundled dependency skills.
