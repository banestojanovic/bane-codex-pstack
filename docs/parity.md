# Parity and validation

The source baseline is Cursor pstack 0.15.29 at commit `190d28736eff128ec94f502a22c7fe0c4b56cd37`. The fetched checkout's commit receipt is in [upstream.txt](../.audit/upstream.txt). `upstream.lock.json` hashes every vendored file and lists all 56 skills and 23 playbooks. Three dependency skills come from the same commit's `cursor-team-kit` directory.

## What is verified

| Check | Evidence |
| --- | --- |
| Every upstream skill name and playbook retained | Python package tests and `upstream.lock.json`. |
| Unchanged playbooks match source bytes | Python package tests compare all 23 files. |
| Every upstream file accounted for | Installed `provenance.json` and locked vendor hashes. |
| Generated package matches sources, bytes, and executable flags | `tools/build.py --check`, with known-bad content, missing-file, extra-file, and executable-mode controls. |
| Explicit-only skills retain invocation policy | Native `agents/openai.yaml` policy tests. |
| Installed Markdown references resolve | Local-link test, excluding the upstream prompt's literal `url` example. |
| Setup preserves custom roles and unrelated configuration | Subprocess tests cover fresh setup, reruns, explicit overrides, aliases, budgets, dry-run, backups, malformed TOML, newline boundaries, array tables, multiline strings, and symlinks. |
| Transcript discovery stays scoped | Fixtures verify exact workspace metadata matching and no message bodies in output. |
| Worktree audit remains conservative | Real Git worktree fixture with spaces, clean state, and staged work. |
| Session hook emits correct opt-in JSON | Fixture runs for missing, off, and on states. |
| Native marketplace installation succeeds | Real Codex marketplace/add calls under a temporary `CODEX_HOME`. |
| Native skill parser discovers the plugin | Real Codex app-server `skills/list` reports all 59 qualified skills without package errors. No model request is made. |
| Upstream watcher, store, and plan checks pass | 68 Bun tests and strict TypeScript check. Forge responses are faked in upstream unit tests. |
| Representative instruction behavior | Native agents exercised help, bro, unsupported bot behavior, and a simple how workflow. See the [behavioral probe record](../.audit/behavioral-probes.md). |

The recorded local run passed 28 port tests and 68 upstream tests, strict TypeScript checks, and native installation and discovery. The [verification JSON](../.audit/verification.json) records commands, timestamps, and exit codes. The [complete output](../.audit/verification.txt) records the actual test output. Rerun `python3 tools/verify.py --with-install` to replace these receipts with a new measurement. Codex CLI 0.163.0-alpha.10.2 was used for local installation and discovery checks. The automated CI job runs structural, setup, Bun, and TypeScript checks, but its hosted GitHub result is separate from these local receipts.

## What remains unverified

No claim is made that every model follows every workflow perfectly. The full four-agent panel, all 23 playbook executions, actual trusted SessionStart injection, desktop picker rendering, Windows, authenticated forge operations, remote deployments, app-specific live verification, and installed formal verifiers were not exercised end to end here. The native instruction probes are small behavioral checks, not a complete agent evaluation suite.

Literal Cursor `/name` syntax is not implemented as Codex parser commands. Native installed skills are qualified as `pstack:name`; use `$pstack:poteto-mode` and the skill picker. Skills-only installs retain their unqualified names.

Cursor cloud VMs, video capture, Custom Modes, and webhook/secret services are host capabilities. `make-bot-ui` and Benny cannot execute their Cursor backend on Codex. The adapter blocks claims of success for those dependencies. This port preserves the workflow source and offers explicit native mappings where possible, not behavioral parity for hosted services.

Default panels preserve four independent agents but use one Sol model at different effort levels, so model diversity is reduced. Model choices are defaults, not a guarantee of account access. Missing models, capacity, or drivers keep their required gates open.
