---
name: setup-pstack
description: Configure pstack for Codex, choose models and reasoning budgets, and offer project verification skills. Use for setup-pstack, pstack setup, model choices, or session routing.
---

# Set up pstack on Codex

Read [the Codex adapter](../../docs/harness/codex.md) first. `<pstack>` is this skill's plugin root, two directories above this file.

1. Detect the actual models and reasoning levels offered by the current host's native subagent tool schema or documented model list. Do not treat saved config as entitlement. If detection is unavailable, ask which model IDs are available. Aliases `auto` and `inherit-parent` are always valid. Confirm that native `spawn_agent` and `wait_agent` are offered before promising fan-out.
2. Read `${CODEX_HOME:-~/.codex}/pstack-models.md` and existing instructions if present. Show existing choices. Defaults and roles are in the adapter. Preserve custom roles. `hardest tasks` and `strongest judgment` denote the same role.
3. Ask for a reasoning budget, using the current choice as context. Offer unlimited with max reasoning, large with xhigh, medium with high, small with medium, or session with no effort override. Show every role, all panel entries, and any unavailable model. The default four-agent Sol panels vary effort and have reduced model diversity. Explain that cost grows with panel size. Ask whether to keep the table or change specific roles. If the user has already supplied choices, use those without another approval question.
4. Validate selected real models against the detected set. Model IDs and reasoning effort are separate. Do not append Cursor effort suffixes or silently substitute models. Keep four independent reviewers unless the user chooses a different panel size.
5. Run the bundled CLI `python3 <pstack>/tools/setup.py --check` with the chosen `--budget` and `--available-model` arguments. For explicit role changes, write a temporary JSON role-to-string-or-list file and pass `--models-file`. Inspect the proposed changes. Run again without `--check` to apply within the user's authorized setup scope. Use `--codex-home` for a custom home. Preserve unrelated TOML and AGENTS.md instructions. Host permission requirements still apply.
6. Report the sheet and managed loader locations. Start a new chat for global instructions and multi-agent configuration to load. Test a read-only native child before promising model availability if the tool schema did not establish it. State any blocked capability explicitly.
7. Offer once to generate a project verification skill with [create-verification-skill](../create-verification-skill/SKILL.md) when no driver skill or equivalent real-app verification exists. On yes, write it under `.agents/skills/` and prove it works. On no, move on.
8. Offer once to generate a formal verification skill with [create-formal-verification-skill](../create-formal-verification-skill/SKILL.md) when none exists. Explain that it suits costly concurrency, retries, parsers, or state invariants. Respect the answer.

For persistent session routing, offer `--session-hook on`; `off` disables hook output. Do not claim the hook is active until trusted through the host's `/hooks` interface. Explicit `$pstack:poteto-mode` works without a hook.
