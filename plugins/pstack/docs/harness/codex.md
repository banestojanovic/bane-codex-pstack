# pstack in Codex

Read this adapter before following a bundled workflow. It overrides Cursor-specific tool names, model defaults, filesystem paths, and host features in the preserved upstream text. Follow the same workflow steps and evidence requirements. User instructions and the host's permission rules take precedence over this adapter and upstream's autonomy wording. `<pstack>` means this installed plugin's root.

## Invoke skills

All 56 upstream skill names are retained. Select a skill through `/skills` or the host's skill picker, reference `$poteto-mode`, `$setup-pstack`, `$how`, or another `$name`, or ask for the skill by name. Slash examples such as `/arena` in the upstream text mean the same skill on Codex. Native plugin discovery qualifies names as `pstack:name`, so use `$pstack:poteto-mode` or `$pstack:setup-pstack` when naming the installed plugin explicitly. Short `$name` references are suitable for skills-only copies or hosts that resolve unqualified names. A plugin cannot register arbitrary built-in `/name` parser commands. Do not claim that typing a raw Cursor slash command works in every Codex client. For a workflow calling another skill, read `<pstack>/skills/<name>/SKILL.md` and follow it in the current chat.

Before dispatching any subagent, read `${CODEX_HOME:-~/.codex}/pstack-models.md` if it exists. The setup tool writes that sheet and a managed loader block in the global `AGENTS.md`. Project instructions override global choices. A missing role uses the Codex defaults below, never an upstream Claude or Grok slug.

## Tools and fields

| Cursor term | Codex behavior |
| --- | --- |
| `Task`, `Agent`, Task tool, Task subagent, Task call | Native `spawn_agent`, then collect completion through `wait_agent`. Never use detached processes or a separate orchestration adapter to emulate delegation. |
| `generalPurpose`, `general-purpose`, `poteto-agent` | No type field. Put the role and scope in the brief. For a poteto-agent, instruct it to read `<pstack>/skills/poteto-mode/SKILL.md` in full first. |
| `comment-sicko` | Fresh independent subagent reading `<pstack>/agents/comment-sicko.md` and this adapter first. |
| `readonly: true` or `readonly: false` | Do not pass a readonly field. For read-only work say "do not edit files" and inspect the tree afterward. Tool access is the host's. |
| `environment: "cloud"` | Local isolated Git worktree, created before dispatch. Tell the worker its absolute path and base revision. This is not an isolated VM. |
| `environment: "local"` | Native subagent in the current environment. |
| `cloud_base_branch` | Check out the specified branch or commit in the worker's worktree. |
| `run_in_background: true` | Native spawn is asynchronous. Omit the field. |
| `resume` | Fresh agent with consolidated brief and previous result by default. Reuse only for costly live state as upstream specifies and only through a native follow-up tool. |
| `file_attachments` | Include absolute file pointers in the brief. |
| `AskQuestion`, `AskUserQuestion` | Use the host's question tool if offered, otherwise ask in ordinary text. Do not wait for a preference that experiments can settle. |
| Todolist, todo list | Native plan tool when available, otherwise `.audit/<task>.todo.md`. Preserve skipped steps with their reasons. |
| `Read`, `Grep`, `Glob`, `Bash` | The host's file and shell tools, `rg` for search. |
| Built-in PR tool | A connected forge tool if available, otherwise the resolved `gh` or `origin` CLI. Attach created PRs with the Codex app artifact tool if provided. |

Writing workers each own a worktree or output directory. `spawn_agent` may require `fork_turns: "none"` when selecting a model. In that case provide a self-contained brief, constraints, base revision, file pointers, and absolute poteto-mode path. Pass the role's model explicitly. Collect every child completion before claiming the parent phase complete.

Capacity is a host limit. Four panel entries mean four independent agents, even on a host with fewer simultaneous slots. Schedule them in waves if slots can be reclaimed. Do not count one agent four times. If the host cannot provide all reviewers, report the partial panel and block a required verdict. A required independent review never becomes self-review. For exploration only, a labelled sequential pass is acceptable if native agents are unavailable. Enable `[features] multi_agent = true` through setup where the host supports it.

Discover MCPs through the tools and metadata exposed by this session. Do not infer connected capabilities from Cursor's `mcps/` directory, `.mcp.json`, or another client's cache. Query only actually available tools.

## Models and reasoning

Never pass upstream `claude-*`, `grok-*`, Cursor `gpt-*` defaults, or `-fast` variants to Codex. Model entitlement comes from the current host's tool schema or a documented model list. A configuration file is a choice, not evidence of entitlement. If a configured model is unavailable, report it and keep the affected gate open. Do not silently substitute a model.

| Role | Codex default |
| --- | --- |
| feature, refactoring | gpt-6-luna |
| bug-fix, perf-issue, hillclimb | gpt-6.1-sol |
| judgment and prose, hardest tasks, strongest judgment | gpt-6.1-sol |
| how explorer, why investigators, reflect tooling, swarm workers | gpt-6-luna |
| how explainer, why synthesizer, reflect judgment, divergent, synthesizer | gpt-6.1-sol |
| arena runners, architect runners, interrogate reviewers | gpt-6.1-sol @medium, gpt-6.1-sol @high, gpt-6.1-sol @xhigh, gpt-6.1-sol @max |
| arena cross-judge pool | gpt-6.1-sol |

`hardest tasks` is upstream's label for `strongest judgment`. Treat them as the same role. Difficult implementation and ambiguous investigation use that role. Luna evidence informs Sol decisions. The panels have reduced model diversity. Disclose this in their verdicts.

A role value is `model @effort`, or `auto` or `inherit-parent`. Parse a panel as a list of such values. `@medium`, `@high`, `@xhigh`, and `@max` become `reasoning_effort` on `spawn_agent`, separate from `model`. `session` supplies no effort override. The global `default effort` applies when an entry has no suffix. Aliases omit the model argument and inherit the parent. Respect user-selected reasoning levels. Never infer availability by inventing a new slug. On a limited host, ask for an available model choice and leave the task state reviewable.

## Paths and transcript access

| Cursor path or behavior | Codex replacement |
| --- | --- |
| `~/.cursor/rules/pstack-models.mdc`, `pstack-models.mdc` | `${CODEX_HOME:-~/.codex}/pstack-models.md`. Read explicitly. This file is not automatically injected by Codex. |
| `.cursor/skills/` | `.agents/skills/`. Generated project skills belong here. |
| `~/.cursor/skills/` | `~/.agents/skills/`, or the host's documented user skill path. |
| `.cursor/rules/*.mdc`, always-applied rule | Project `AGENTS.md`, or `${CODEX_HOME:-~/.codex}/AGENTS.md` globally. Preserve existing instructions. |
| `.cursor-plugin/plugin.json`, `~/.cursor/plugins/` | Root `plugin.json` with `extensions.com.openai`, compatibility `.codex-plugin/plugin.json`, and the host-managed plugin cache. Resolve this installed plugin from its skill path. |
| `CLAUDE.md`, "your instructions file" | Project `AGENTS.md` on Codex. |
| Public upstream links | Read bundled local files first. Link the Codex repository for adapted instructions, upstream for original behavior. |
| `agent-transcripts`, `~/.cursor/projects/` | Native Codex chat tools where available. Otherwise use the current session path provided by the host or a user-authorized transcript. A tight session digest is allowed for reflect. |

Do not scan unrelated chats. Codex JSONL sessions can live under `$CODEX_HOME/sessions` and `$CODEX_HOME/archived_sessions`, but these are shared across projects. Do not glob and read their bodies to find a project. The bundled `tools/transcripts.py --workspace <absolute path>` only reads first-line session metadata and returns exact workspace matches; it never prints message bodies. Read only a returned workspace transcript relevant to the current task. If no authoritative session is available, say so and use a labelled current-session digest where permitted. Never pretend Cursor JSONL layouts apply to Codex.

The worktree audit overlay deliberately reports unknown chat state and never classifies a worktree as safe solely from missing history. Confirm ownership through native chat state before cleanup. The original source remains in `vendor/pstack` in the repository.

## Dependency skills and drivers

`deslop`, `control-cli`, and `control-ui` from the same pinned `cursor-team-kit` source are bundled alongside pstack. Read their local skills, with these mappings. `create-skill` and `plugin-dev:skill-development` mean the host's skill-creator skill if available, otherwise write a standard Agent Skill with `name` and `description` frontmatter, supporting resources, validation, and realistic forward tests. `agent-browser`, Cursor's browser, screenshot/video capture, and mobile drivers require actual installed tools. Select tools exposed by the host, observe the real artifact, and report unavailable verification as NOT VERIFIED. Do not invent a driver call or count a manual-check suggestion as a passed live lane.

## Host capabilities

| Upstream capability | Codex adaptation and limit |
| --- | --- |
| Cursor Custom Mode, Option+Enter | Explicit `$poteto-mode` for each task. Optional trusted session hook or standing `AGENTS.md` routing instruction for persistence. No matching Custom Mode UI. |
| `/loop`, `/loop 1h` | While the current turn remains active, use the host's bounded waits and native watcher agents. For later wakeups use a Codex heartbeat automation only when exposed and the user authorized recurring work. Preserve quiet-on-no-change behavior. No promise of an indefinitely running local agent after the session ends. |
| `/in-cloud`, cloud VM, parallel videos | Local worktrees share a machine and permissions. For a requirement that depends on VM isolation or cloud video, report it unsupported. Do not pass cloud fields to `spawn_agent`. |
| Cursor Projects, dashboard, coordinator, cross-chat messages | Native chat read/wait tools when offered. Send messages or create chats only with user authorization. Internal subtasks use native subagents. |
| Bugbot | Read existing review threads through the active forge. Starting or configuring Cursor's bot is unsupported. Use the independent Codex review panel and record that difference. |
| Cursor Automations and Benny routines | The source and templates are retained under `automations/benny`, but its routine webhooks and secret contract are Cursor-only. Codex scheduling alone is not equivalent. |
| `make-bot-ui`, `update_state target:routine trigger:webhook`, `SendToUser`, `api2.cursor.sh/automations` | The command is retained for source parity. On Codex first report UNSUPPORTED for its Cursor webhook/secret backend. Do not generate a fake endpoint, request secrets, or deploy a bot. A separately specified hosted Codex integration is required to execute this workflow. |
| Image generation | Use the host's actual image tool if available. Otherwise report the unavailable artifact. |

When a nonessential host-only step cannot run, record `Skipped in Codex: <step>. <reason>.` and continue independent work. When completion or a required review depends on it, report BLOCKED or NOT VERIFIED. Source presence is not behavioral parity.

## Setup and optional session routing

Run `$setup-pstack` and follow its Codex-specific instructions. The bundled setup CLI can configure an isolated home for validation. It preserves unrelated configuration and instructions, makes backups on change, and offers a dry run. It rejects symlinked managed files before writing so dotfiles links are never replaced. It does not change the parent model, authenticate accounts, or confirm model entitlement.

The optional SessionStart hook reads `session hook: on` from the model sheet. With no sheet or with `off` it emits nothing. A user must trust the plugin hook through `/hooks` before Codex executes it. The hook supplies routing instructions and the sheet path; it does not execute tasks or install dependencies. Skills-only copies have no plugin hook and need explicit invocation or a standing routing instruction.
