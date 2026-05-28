#!/usr/bin/env python3
"""Validate Claude Code and OpenCode runtime wiring."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
PROJECT_KEY_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
MAIN_SKILL = "analyze-requirement-test-design-solution"
MAIN_AGENT = "test-analysis-agent"
OPENCODE_COMMAND = ".opencode/commands/analyze-requirement-test-design-solution.md"
OPENCODE_AGENT = f".opencode/agents/{MAIN_AGENT}.md"


def fail(message: str, issues: list[str]) -> None:
    issues.append(message)


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("missing YAML frontmatter")

    data: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return data
        if not line.strip() or line.startswith(" "):
            continue
        key, sep, value = line.partition(":")
        if sep:
            data[key.strip()] = value.strip()

    raise ValueError("unterminated YAML frontmatter")


def validate_plugin(root: Path, issues: list[str]) -> None:
    manifest_path = root / ".claude-plugin" / "plugin.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"{manifest_path.relative_to(root)} is not valid JSON: {exc}", issues)
        return

    if manifest.get("skills") != "./skills/":
        fail(".claude-plugin/plugin.json must point skills to ./skills/", issues)
    if manifest.get("agents") != "./agents/":
        fail(".claude-plugin/plugin.json must point agents to ./agents/", issues)

    if (root / ".claude-plugin" / "agents").exists():
        fail(".claude-plugin/agents must not exist; Claude plugin agents are sourced from root agents/", issues)


def validate_skills(root: Path, issues: list[str]) -> None:
    skills_dir = root / "skills"
    if not skills_dir.is_dir():
        fail("skills/ directory is missing", issues)
        return

    for skill_dir in sorted(path for path in skills_dir.iterdir() if path.is_dir()):
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            fail(f"{skill_dir.relative_to(root)} is missing SKILL.md", issues)
            continue
        try:
            meta = parse_frontmatter(skill_file)
        except ValueError as exc:
            fail(f"{skill_file.relative_to(root)}: {exc}", issues)
            continue

        name = meta.get("name", "")
        description = meta.get("description", "")
        if name != skill_dir.name:
            fail(f"{skill_file.relative_to(root)} name must match directory name", issues)
        if not NAME_RE.fullmatch(name):
            fail(f"{skill_file.relative_to(root)} has invalid skill name {name!r}", issues)
        if not (1 <= len(description) <= 1024):
            fail(f"{skill_file.relative_to(root)} description must be 1-1024 characters", issues)

    if not (skills_dir / MAIN_SKILL / "SKILL.md").exists():
        fail(f"main skill {MAIN_SKILL!r} is missing", issues)


def validate_agents(root: Path, issues: list[str]) -> None:
    agents_dir = root / "agents"
    if not agents_dir.is_dir():
        fail("agents/ directory is missing", issues)
        return

    for agent_file in sorted(path for path in agents_dir.glob("*.md") if path.is_file()):
        try:
            meta = parse_frontmatter(agent_file)
        except ValueError as exc:
            fail(f"{agent_file.relative_to(root)}: {exc}", issues)
            continue

        name = meta.get("name", "")
        description = meta.get("description", "")
        if name != agent_file.stem:
            fail(f"{agent_file.relative_to(root)} name must match file stem", issues)
        if not NAME_RE.fullmatch(name):
            fail(f"{agent_file.relative_to(root)} has invalid agent name {name!r}", issues)
        if not (1 <= len(description) <= 1024):
            fail(f"{agent_file.relative_to(root)} description must be 1-1024 characters", issues)

    if not (agents_dir / f"{MAIN_AGENT}.md").exists():
        fail(f"main agent {MAIN_AGENT!r} is missing", issues)


def validate_opencode(root: Path, issues: list[str]) -> None:
    config_path = root / "opencode.json"
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"opencode.json is not valid JSON: {exc}", issues)
        return

    if config.get("$schema") != "https://opencode.ai/config.json":
        fail("opencode.json must declare the OpenCode schema", issues)
    skill_permission = config.get("permission", {}).get("skill", {})
    if skill_permission.get("*") != "allow":
        fail('opencode.json should allow project skills with permission.skill."*"', issues)

    command_path = root / OPENCODE_COMMAND
    if not command_path.exists():
        fail(f"{OPENCODE_COMMAND} is missing", issues)
    else:
        command_text = command_path.read_text(encoding="utf-8")
        if MAIN_SKILL not in command_text:
            fail(f"{OPENCODE_COMMAND} must invoke the main skill", issues)
        if "$ARGUMENTS" not in command_text:
            fail(f"{OPENCODE_COMMAND} must pass $ARGUMENTS", issues)

    opencode_agent_path = root / OPENCODE_AGENT
    if not opencode_agent_path.exists():
        fail(f"{OPENCODE_AGENT} is missing", issues)
    else:
        agent_text = opencode_agent_path.read_text(encoding="utf-8")
        if "mode: subagent" not in agent_text:
            fail(f"{OPENCODE_AGENT} must be an OpenCode subagent", issues)
        if MAIN_SKILL not in agent_text:
            fail(f"{OPENCODE_AGENT} must route generation work to the main skill", issues)
        if "context-capture" not in agent_text:
            fail(f"{OPENCODE_AGENT} must route memory/knowledge capture work to context-capture", issues)

    for rules_file in ("AGENTS.md", "CLAUDE.md"):
        if not (root / rules_file).exists():
            fail(f"{rules_file} is missing", issues)


def validate_sync(root: Path, issues: list[str]) -> None:
    script = root / "bin" / "sync-opencode-skills.py"
    result = subprocess.run(
        [sys.executable, str(script), "--check"],
        cwd=root,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        detail = (result.stdout + result.stderr).strip()
        fail(f"OpenCode skill mirror is out of sync: {detail}", issues)


def validate_markdown_files(root: Path, files: list[Path], issues: list[str]) -> None:
    for markdown_file in files:
        try:
            text = markdown_file.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            fail(f"{markdown_file.relative_to(root)} is not valid UTF-8: {exc}", issues)
            continue
        if not text.strip():
            fail(f"{markdown_file.relative_to(root)} must not be empty", issues)


def validate_project_extension_dirs(root: Path, issues: list[str]) -> None:
    for relative in (
        "memory/projects",
        "knowledge/projects",
        "templates/projects",
        "quality-gates/projects",
    ):
        projects_dir = root / relative
        if not projects_dir.exists():
            continue
        if not projects_dir.is_dir():
            fail(f"{relative} must be a directory", issues)
            continue

        for project_dir in sorted(path for path in projects_dir.iterdir() if path.is_dir()):
            if not PROJECT_KEY_RE.fullmatch(project_dir.name):
                fail(
                    f"{project_dir.relative_to(root)} has invalid project-key; "
                    "use lowercase letters, digits, '-' or '_'",
                    issues,
                )
                continue

            markdown_files = sorted(
                path
                for path in project_dir.rglob("*.md")
                if path.is_file() and path.name != "README.md"
            )
            if not markdown_files:
                fail(f"{project_dir.relative_to(root)} should contain at least one project Markdown file", issues)
                continue

            validate_markdown_files(root, markdown_files, issues)


def validate_user_extension_dirs(root: Path, issues: list[str]) -> None:
    for relative in ("memory/user", "knowledge/user", "templates/user", "quality-gates/user"):
        user_dir = root / relative
        if not user_dir.exists():
            continue
        if not user_dir.is_dir():
            fail(f"{relative} must be a directory", issues)
            continue

        markdown_files = sorted(
            path
            for path in user_dir.rglob("*.md")
            if path.is_file() and path.name != "README.md"
        )
        validate_markdown_files(root, markdown_files, issues)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    issues: list[str] = []

    validate_plugin(root, issues)
    validate_agents(root, issues)
    validate_skills(root, issues)
    validate_opencode(root, issues)
    validate_sync(root, issues)
    validate_project_extension_dirs(root, issues)
    validate_user_extension_dirs(root, issues)

    if issues:
        print("Runtime validation failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("Runtime validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
