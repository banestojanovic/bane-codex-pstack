# Setup question routing correction

The user reported that setup printed several groups of Markdown choices and asked them to select options, but created no interactive controls. The screenshot is the direct reproduction of the user-visible defect. No screenshot or project-specific attachment is published here.

The shared adapter only said to use the host's question tool if offered. It did not name the async tool, account for mode restrictions, or distinguish a text list from a question widget. Setup compounded that with five budgets and several unrelated decisions together. This applies Fix Root Causes at the runtime mapping and setup sequence.

Version 0.15.29-codex.2 prioritizes usable native async questions, then usable sync questions. It follows the actual tool schema, splits budget choices when needed, waits for a real answer, and defers optional verification offers until model configuration has been applied. If no question tool is usable, it explicitly says choices are unavailable and asks for a typed answer. It never implies that a Markdown list is clickable or treats a preselection as consent.

The local CLI reported `default_mode_request_user_input` as under development and false. A read-only launch-scoped probe with `codex --enable default_mode_request_user_input features list` reported true. The plugin does not persist that flag, change mode automatically, or promise that instruction text can expose an absent tool. The existing user's model sheet and config were not modified by this fix.

A fresh Luna instruction probe evaluated seven simulated host states from tests/evals/setup-questions.json. Async and sync payloads fit their supplied schemas. Pending preferences blocked writes. Already-supplied preferences did not trigger new questions. The initial probe omitted the explicit no-controls explanation in two fallback outputs, so the parent strengthened that fallback sentence and repeated those two cases with a fresh Luna agent. Both then explicitly told the user to type an answer and withheld writes. These are instruction-routing simulations, not actual UI rendering tests.

The first probe also claimed the user's model sheet was missing. The parent had read that sheet successfully; the unrelated source note is rejected and not used to establish behavior. The raw probe output is retained in setup-question-probe.json for auditability.

The fresh fallback probe returned the following user-facing text in both no-tool and Plan-only-in-Default cases:

> Interactive choices are unavailable in this session; please type your answer. What reasoning budget should pstack use? You can choose session, small, medium, large, or unlimited. For example, "Use session effort."

A fresh Sol reviewer found no blocking instruction defects. Its test rerun exposed a package-test bug after Bun installation: the Markdown check recursed into ignored runtime dependencies. The parent reproduced that failure, changed the test to use the generator's actual package inventory, and reran it. A second fresh Sol reviewer verified that adding a broken link to an actual packaged README still fails the test. All 28 Python tests then passed. Source and generated content agree, and native isolated installation discovers 59 skills at .2.

There were no changed code comments to remove. Review used the configured Sol model family; no four-member adversarial panel or diverse-model verdict is claimed. Actual CLI popup rendering remains NOT VERIFIED. The fix does not claim to enable interactive questions in a host or mode that does not provide the tool.

The full rerunnable command is `python3 tools/verify.py --with-install --output .audit/setup-questions-verification`. Its JSON and text receipts record structural checks, port tests, upstream tests, typecheck, and native installation. A final link-test pass after Bun installation checks that installed dependencies no longer contaminate package validation.
