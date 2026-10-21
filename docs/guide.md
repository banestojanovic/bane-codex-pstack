# Use pstack in Codex

Install the marketplace and plugin using the [README](../README.md#install). Start a new chat and invoke `$pstack:setup-pstack`. Pick a reasoning budget, review the model roles, and keep or change the offered choices. Setup uses native question controls when usable in the current mode. Otherwise it explicitly asks for a typed answer, one decision at a time. Optional verification offers follow completed model configuration. For normal work, send `$pstack:poteto-mode` followed by a goal and a check that can pass or fail.

The workflow copies the selected playbook into its todo list. A skipped step stays visible with a reason. The parent gathers evidence, chooses a design, delegates through native Codex agents, and collects their results. Writing agents work in separate worktrees. Required independent review remains blocked when the host cannot provide reviewers.

Use `$pstack:how` to understand current behavior, `$pstack:why` for rationale and history, `$pstack:architect` for types and module structure, `$pstack:arena` for competing attempts, `$pstack:swarm` for divided coverage, and `$pstack:interrogate` for adversarial review. `$pstack:poteto-help` reads the installed guide and recommends a workflow without starting expensive work.

Setup offers a real-app verification skill and a formal verification skill once each when the project lacks them. Accept the first when agents need a way to exercise your app. Formal verification suits races, retries, parsers, and expensive state invariants. Generated project skills live in `.agents/skills/`.

The [upstream guide](../plugins/pstack/docs/guide/README.md) provides all ten chapters and worked examples. Interpret slash commands as Codex skill names, `.cursor/skills` as `.agents/skills`, and task delegation through the [Codex adapter](../plugins/pstack/docs/harness/codex.md). The adapter explicitly records host-only limitations.

Codex hooks require host trust. To opt into session routing, run `python3 tools/setup.py --session-hook on` from a checkout and trust this plugin through `/hooks`. A skills-only installation does not carry hooks. Explicit invocation remains available.

To change role choices later, run `$pstack:setup-pstack` again. It preserves saved choices unless you explicitly replace them. Budget changes affect entries without their own effort suffix. Four-agent panels use separate Sol agents with different effort levels, so their reduced model diversity must appear in the verdict.
