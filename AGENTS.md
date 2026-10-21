# Work on the Codex port

`vendor/pstack/` and the three `vendor/cursor-team-kit/skills/` dependencies are pinned upstream source. Do not edit them to fix Codex behavior. Put deliberate differences in `adapters/` and regenerate with `python3 tools/build.py`.

`plugins/pstack/` is generated and installed by Codex. Keep source and generated changes in the same commit. Run `python3 tools/build.py --check`, `python3 -m unittest discover -s tests -v`, and the upstream Bun tests plus typecheck before publishing changes. Run `python3 tools/smoke_install.py` on a host with the Codex plugin CLI to verify the actual installed package and skill parser.

Use native Codex `spawn_agent` and `wait_agent` for delegation. Do not introduce detached agent processes, another orchestration adapter, model proxies, or shell-launched inference in this plugin. Preserve workflow gates. Never count self-review as independent review.

Keep the compatibility matrix honest. Cursor-hosted webhooks, secret cards, cloud VMs, cloud videos, and Custom Modes are not implemented by this plugin. Source preservation, successful installation, and successful workflow execution are distinct claims.

Do not mutate a user's real Codex home in tests. Use temporary homes and workspace fixtures. Setup must validate proposed TOML semantics, preserve unrelated instructions and configuration, and refuse unsupported syntax before mutation.
