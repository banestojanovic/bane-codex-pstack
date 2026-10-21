import json
import os
from pathlib import Path

home = Path(os.environ.get('CODEX_HOME', Path.home() / '.codex'))
sheet = home / 'pstack-models.md'
try:
    enabled = any(line.strip() == 'session hook: on' for line in sheet.read_text().splitlines())
except (OSError, UnicodeError):
    enabled = False
if enabled:
    root = Path(__file__).resolve().parents[1]
    context = (f'For work touching multiple files, changing a called signature, making a design choice, '
               f'or investigating an unknown bug/performance issue, read {root}/skills/poteto-mode/SKILL.md '
               f'and {root}/docs/harness/codex.md first. Read model roles from {sheet}. '
               'Use native spawn_agent and wait_agent for delegation. For smaller tasks work directly '
               'and verify the real artifact. User instructions and host permissions take precedence.')
    print(json.dumps({'hookSpecificOutput': {'hookEventName': 'SessionStart', 'additionalContext': context}}))
