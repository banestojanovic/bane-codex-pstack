---
name: poteto-help
description: Guide users through pstack for Codex setup, commands, playbooks, and troubleshooting. Use for poteto-help or questions about using pstack.
---

# pstack help on Codex

Read [the Codex adapter](../../docs/harness/codex.md) before answering. Answer a help question without starting a costly workflow. An explicit request to do the work routes to [poteto-mode](../poteto-mode/SKILL.md).

Read the relevant bundled skill or guide page before explaining its behavior. All 32 upstream public skill names and 24 principles are installed. The guide in `docs/guide/` preserves the upstream explanation and examples; the adapter owns Codex differences. Give a runnable Codex prompt using `$name`, such as `$pstack:poteto-mode add a --json flag and verify text output remains identical.`

For installation, use the repository README's Codex marketplace instructions. For models and reasoning budgets, run `$pstack:setup-pstack`; its sheet lives at `${CODEX_HOME:-~/.codex}/pstack-models.md`. A missing sheet uses Codex defaults from the adapter. For a list of commands, read `docs/commands.md`. For persistent routing explain the optional trusted hook and standing AGENTS.md instructions. Codex does not have Cursor's Custom Mode UI.

For picking a workflow, read the relevant skill. `how` explains runtime flow, `why` investigates rationale, `architect` explores designs, `arena` compares candidates, `swarm` divides coverage, `interrogate` challenges a diff, and `reflect` proposes skill improvements with the upstream approval gate. Use `poteto-mode` when the user wants complete execution with the right playbook.

If a run stalls, inspect its todo list and evidence before suggesting a retry. Native subagent availability, model entitlement, capacity, forge authentication, and app drivers depend on the host. Keep required independent review blocked when no reviewer can run. Name Cursor-only dependencies explicitly. `make-bot-ui` and Benny's routine backend cannot execute on Codex without a separately implemented service.
