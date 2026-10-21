#!/usr/bin/env python3
"""Safely configure pstack's Codex model sheet and native multi-agent support."""
from __future__ import annotations

import argparse
import copy
import json
import os
import re
import shutil
import stat
import sys
import tempfile
import tomllib
from pathlib import Path

EFFORTS = ("low", "medium", "high", "xhigh", "max")
BUDGET_EFFORT = {
    "unlimited": "max",
    "large": "xhigh",
    "medium": "high",
    "small": "medium",
    "session": "session",
}
ROLE_DEFAULTS = {
    "feature, refactoring": "gpt-6-luna",
    "bug-fix": "gpt-6.1-sol",
    "perf-issue": "gpt-6.1-sol",
    "hillclimb": "gpt-6.1-sol",
    "judgment and prose": "gpt-6.1-sol",
    "strongest judgment": "gpt-6.1-sol",
    "how explorer": "gpt-6-luna",
    "how explainer": "gpt-6.1-sol",
    "why investigators": "gpt-6-luna",
    "why synthesizer": "gpt-6.1-sol",
    "reflect tooling": "gpt-6-luna",
    "reflect judgment, divergent, synthesizer": "gpt-6.1-sol",
    "arena runners": ["gpt-6.1-sol @medium", "gpt-6.1-sol @high", "gpt-6.1-sol @xhigh", "gpt-6.1-sol @max"],
    "arena cross-judge pool": ["gpt-6.1-sol"],
    "swarm workers": "gpt-6-luna",
    "architect runners": ["gpt-6.1-sol @medium", "gpt-6.1-sol @high", "gpt-6.1-sol @xhigh", "gpt-6.1-sol @max"],
    "interrogate reviewers": ["gpt-6.1-sol @medium", "gpt-6.1-sol @high", "gpt-6.1-sol @xhigh", "gpt-6.1-sol @max"],
}
KNOWN_ROLES = set(ROLE_DEFAULTS) | {"hardest tasks"}
BEGIN = "<!-- pstack-codex-setup:begin -->"
END = "<!-- pstack-codex-setup:end -->"
MANAGED_INSTRUCTIONS = """<!-- pstack-codex-setup:begin -->
For pstack work, read `pstack-models.md` in this Codex home before choosing agent models or reasoning effort. Use Codex native `spawn_agent` and `wait_agent` tools for pstack delegation. Do not use Scripts/vaelen-agents, OpenCode, detached agent processes, or another orchestration adapter.
<!-- pstack-codex-setup:end -->"""
VALUE_RE = re.compile(r"^(?:[A-Za-z0-9][A-Za-z0-9._/-]*|inherit-parent|auto)(?: @(?:low|medium|high|xhigh|max))?$")


class SetupError(Exception):
    pass


def role_value(value: object, role: str) -> str:
    values = value if isinstance(value, list) else [value]
    if not values or not all(isinstance(v, str) for v in values):
        raise SetupError(f"models file role {role!r} must be a model string or non-empty list of strings")
    for item in values:
        if not VALUE_RE.fullmatch(item.strip()):
            raise SetupError(f"invalid model/effort value for {role!r}: {item!r}")
    return ", ".join(v.strip() for v in values)


def parse_models(path: Path | None, available: set[str] | None) -> dict[str, str]:
    result = {role: role_value(value, role) for role, value in ROLE_DEFAULTS.items()}
    if path is not None:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SetupError(f"cannot read models file {path}: {exc}") from exc
        if not isinstance(payload, dict):
            raise SetupError("models file must be a JSON object mapping role names to strings or lists")
        for role, value in payload.items():
            if role not in KNOWN_ROLES:
                raise SetupError(f"unknown role in models file: {role!r}")
            result["strongest judgment" if role == "hardest tasks" else role] = role_value(value, role)
    return result


def render_sheet(existing: str | None, models: dict[str, str], budget: str, hook: str, overrides: set[str] | None = None) -> str:
    lines = existing.splitlines() if existing else ["# pstack model configuration", ""]
    role_pattern = re.compile(r"^\s*([^:#][^:]*):\s*(.*?)\s*$")
    overrides = overrides or set()
    seen: set[str] = set()
    output: list[str] = []
    for line in lines:
        match = role_pattern.match(line)
        if match and match.group(1).strip() in KNOWN_ROLES:
            role = match.group(1).strip()
            role = "strongest judgment" if role == "hardest tasks" else role
            if role in seen:
                raise SetupError(f"duplicate model role in sheet: {role}")
            seen.add(role)
            current = match.group(2)
            if role in models and role not in {"default effort", "session hook"}:
                if role in overrides or current == "" or current.startswith("<!-- generated defaults"):
                    current = models[role]
            if role == "default effort":
                current = BUDGET_EFFORT[budget]
            elif role == "session hook":
                current = hook
            output.append(f"{role}: {current}")
        elif line.startswith("default effort:"):
            seen.add("default effort")
            output.append(f"default effort: {BUDGET_EFFORT[budget]}")
        elif line.startswith("session hook:"):
            seen.add("session hook")
            output.append(f"session hook: {hook}")
        else:
            output.append(line)
    if output and output[-1].strip():
        output.append("")
    for role, value in models.items():
        if role not in seen:
            output.append(f"{role}: {value}")
    if "default effort" not in seen:
        output.append(f"default effort: {BUDGET_EFFORT[budget]}")
    if "session hook" not in seen:
        output.append(f"session hook: {hook}")
    return "\n".join(output).rstrip() + "\n"


def managed_instructions(existing: str | None) -> str:
    text = existing or ""
    begin, end = text.find(BEGIN), text.find(END)
    if begin >= 0 and end >= begin:
        end += len(END)
        return text[:begin] + MANAGED_INSTRUCTIONS + text[end:]
    if begin >= 0 or end >= 0:
        raise SetupError("global AGENTS.md has an unmatched pstack managed-block marker; repair it before setup")
    return text.rstrip() + ("\n\n" if text.strip() else "") + MANAGED_INSTRUCTIONS + "\n"


def update_config(text: str | None) -> str:
    original = text or ""
    try:
        parsed = tomllib.loads(original)
    except tomllib.TOMLDecodeError as exc:
        raise SetupError(f"config.toml is malformed; no files were changed: {exc}") from exc
    features = parsed.get("features", {})
    if not isinstance(features, dict):
        raise SetupError("config.toml [features] must be a table; refusing to rewrite unsupported structure")
    if features.get("multi_agent") is True:
        return original
    if isinstance(features.get("multi_agent"), (dict, list)):
        raise SetupError("config.toml uses a nested multi_agent value; refusing to rewrite unsupported structure")
    lines = original.splitlines(keepends=True)
    table_start = None
    table_end = len(lines)
    for i, line in enumerate(lines):
        header = re.match(r"^\s*(\[\[[^\]]+\]\]|\[[^\]]+\])\s*(?:#.*)?(?:\r?\n)?$", line)
        if header:
            name = header.group(1)[1:-1].strip()
            if name == "features":
                table_start = i
                continue
            if table_start is not None:
                table_end = i
                break
    if table_start is None:
        if re.search(r"^\s*features\s*=", original, re.MULTILINE):
            raise SetupError("config.toml defines features as an inline value; convert it to [features] before setup")
        suffix = "" if not original or original.endswith("\n") else "\n"
        return original + suffix + ("\n" if original.strip() else "") + "[features]\nmulti_agent = true\n"
    for i in range(table_start + 1, table_end):
        match = re.match(r"^(\s*)multi_agent\s*=\s*(.*?)(\s*(?:#.*)?)\r?\n?$", lines[i])
        if match:
            lines[i] = f"{match.group(1)}multi_agent = true{match.group(3)}\n"
            return "".join(lines)
    insertion = f"multi_agent = true\n"
    if table_end and not lines[table_end - 1].endswith("\n"):
        lines[table_end - 1] += "\n"
    lines.insert(table_end, insertion)
    return "".join(lines)


def backup_path(path: Path) -> Path:
    candidate = path.with_name(path.name + ".bak")
    n = 1
    while candidate.exists():
        candidate = path.with_name(path.name + f".bak.{n}")
        n += 1
    return candidate


def atomic_write(path: Path, content: str) -> Path | None:
    path.parent.mkdir(parents=True, exist_ok=True)
    old = path.read_text(encoding="utf-8") if path.exists() else None
    if old == content:
        return None
    saved_backup = None
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o644
    if path.exists():
        saved_backup = backup_path(path)
        shutil.copy2(path, saved_backup)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temp_name, mode)
        os.replace(temp_name, path)
    except BaseException:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        if saved_backup is not None:
            saved_backup.unlink(missing_ok=True)
        raise
    return saved_backup


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-home", type=Path, default=Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")))
    parser.add_argument("--budget", choices=BUDGET_EFFORT, default=None)
    parser.add_argument("--models-file", type=Path)
    parser.add_argument("--available-model", action="append", dest="available_models")
    parser.add_argument("--session-hook", choices=("on", "off"), default=None)
    parser.add_argument("--check", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    home = args.codex_home.expanduser().resolve()
    try:
        models = parse_models(args.models_file, set(args.available_models) if args.available_models is not None else None)
        sheet_path, agents_path, config_path = home / "pstack-models.md", home / "AGENTS.md", home / "config.toml"
        for managed_path in (sheet_path, agents_path, config_path):
            if managed_path.is_symlink():
                raise SetupError(f"{managed_path} is a symlink; configure its target explicitly or replace it before setup")
        old_sheet = sheet_path.read_text(encoding="utf-8") if sheet_path.exists() else None
        old_agents = agents_path.read_text(encoding="utf-8") if agents_path.exists() else None
        old_config = config_path.read_text(encoding="utf-8") if config_path.exists() else None
        old_values = dict(line.split(": ", 1) for line in (old_sheet or "").splitlines() if ": " in line and not line.startswith("#"))
        budget = args.budget or next((key for key, value in BUDGET_EFFORT.items() if value == old_values.get("default effort")), "session")
        hook = args.session_hook or old_values.get("session hook", "off")
        overrides = set(json.loads(args.models_file.read_text())) if args.models_file else set()
        if "hardest tasks" in overrides:
            overrides.remove("hardest tasks")
            overrides.add("strongest judgment")
        new_config = update_config(old_config)
        expected_config = copy.deepcopy(tomllib.loads(old_config or ""))
        expected_config.setdefault("features", {})["multi_agent"] = True
        if tomllib.loads(new_config) != expected_config:
            raise SetupError("could not safely change only features.multi_agent; convert the features table to [features] before setup")
        proposed = {
            sheet_path: render_sheet(old_sheet, models, budget, hook, overrides),
            agents_path: managed_instructions(old_agents),
            config_path: new_config,
        }
        for line in proposed[sheet_path].splitlines():
            if ": " not in line or line.startswith("#"):
                continue
            role, value = line.split(": ", 1)
            if role not in KNOWN_ROLES:
                continue
            for entry in value.split(","):
                role_value(entry.strip(), role)
                model = entry.strip().split(" @", 1)[0]
                if args.available_models and model not in {"auto", "inherit-parent"} and model not in args.available_models:
                    raise SetupError(f"saved model {model!r} for {role!r} is unavailable; choose an explicit override")
        plan = [{"path": str(path), "change": content != (path.read_text(encoding="utf-8") if path.exists() else None)} for path, content in proposed.items()]
        if args.check:
            print(json.dumps({"check": True, "changes": [item for item in plan if item["change"]]}, indent=2))
            return 0
        backups = []
        for path, content in proposed.items():
            backup = atomic_write(path, content)
            if backup:
                backups.append(str(backup))
        print(json.dumps({"check": False, "changes": [item for item in plan if item["change"]], "backups": backups}, indent=2))
        return 0
    except (SetupError, OSError, ValueError) as exc:
        print(f"setup: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
