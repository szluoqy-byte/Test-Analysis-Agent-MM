#!/usr/bin/env python3
"""Mirror root skills and agent facades into .opencode for OpenCode discovery."""

from __future__ import annotations

import argparse
import filecmp
import re
import shutil
import sys
from pathlib import Path


NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{path}: missing YAML frontmatter")

    data: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return data
        if not line.strip() or line.startswith(" "):
            continue
        key, sep, value = line.partition(":")
        if sep:
            data[key.strip()] = value.strip()

    raise ValueError(f"{path}: unterminated YAML frontmatter")


def validate_skill_dir(skill_dir: Path) -> None:
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.exists():
        raise ValueError(f"{skill_dir}: missing SKILL.md")

    meta = parse_frontmatter(skill_file)
    name = meta.get("name", "")
    description = meta.get("description", "")
    if name != skill_dir.name:
        raise ValueError(f"{skill_file}: name must match directory name {skill_dir.name!r}")
    if not NAME_RE.fullmatch(name):
        raise ValueError(f"{skill_file}: invalid OpenCode skill name {name!r}")
    if not (1 <= len(description) <= 1024):
        raise ValueError(f"{skill_file}: description must be 1-1024 characters")


def validate_agent_file(agent_file: Path) -> None:
    meta = parse_frontmatter(agent_file)
    name = meta.get("name", "")
    description = meta.get("description", "")
    if name != agent_file.stem:
        raise ValueError(f"{agent_file}: name must match file stem {agent_file.stem!r}")
    if not NAME_RE.fullmatch(name):
        raise ValueError(f"{agent_file}: invalid agent name {name!r}")
    if not (1 <= len(description) <= 1024):
        raise ValueError(f"{agent_file}: description must be 1-1024 characters")


def read_agent_body(agent_file: Path) -> tuple[dict[str, str], str]:
    text = agent_file.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{agent_file}: missing YAML frontmatter")

    data: dict[str, str] = {}
    end_index: int | None = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = index
            break
        if not line.strip() or line.startswith(" "):
            continue
        key, sep, value = line.partition(":")
        if sep:
            data[key.strip()] = value.strip()

    if end_index is None:
        raise ValueError(f"{agent_file}: unterminated YAML frontmatter")

    body = "\n".join(lines[end_index + 1 :]).lstrip("\n")
    return data, body


def yaml_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def render_opencode_agent(agent_file: Path) -> str:
    meta, body = read_agent_body(agent_file)
    description = meta["description"]
    rendered = [
        "---",
        f"description: {yaml_quote(description)}",
        "mode: subagent",
        "permission:",
        "  read: allow",
        "  edit: allow",
        "  glob: allow",
        "  grep: allow",
        "  list: allow",
        "  bash: allow",
        "  skill: allow",
        "---",
        "",
        body.rstrip(),
        "",
    ]
    return "\n".join(rendered)


def compare_dirs(left: Path, right: Path) -> list[str]:
    issues: list[str] = []
    comparison = filecmp.dircmp(left, right)
    for name in comparison.left_only:
        if name == "README.md":
            continue
        issues.append(f"missing in mirror: {right / name}")
    for name in comparison.right_only:
        if name == "README.md":
            continue
        issues.append(f"stale in mirror: {right / name}")
    for name in comparison.diff_files:
        issues.append(f"differs: {right / name}")
    for name in comparison.common_dirs:
        issues.extend(compare_dirs(left / name, right / name))
    return issues


def mirror_skills(root: Path, check: bool) -> int:
    source = root / "skills"
    destination = root / ".opencode" / "skills"
    readme = destination / "README.md"

    if not source.is_dir():
        print("skills/ directory not found", file=sys.stderr)
        return 1

    skill_dirs = sorted(path for path in source.iterdir() if path.is_dir())
    for skill_dir in skill_dirs:
        validate_skill_dir(skill_dir)

    if check:
        if not destination.is_dir():
            print(".opencode/skills directory not found", file=sys.stderr)
            return 1
        issues = compare_dirs(source, destination)
        if issues:
            print("OpenCode skill mirror is out of sync:")
            for issue in issues:
                print(f"- {issue}")
            return 1
        print("OpenCode skill mirror is in sync")
        return 0

    destination.mkdir(parents=True, exist_ok=True)
    if readme.exists():
        readme_text = readme.read_text(encoding="utf-8")
    else:
        readme_text = ""

    for child in destination.iterdir():
        if child.name == "README.md":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()

    for skill_dir in skill_dirs:
        shutil.copytree(skill_dir, destination / skill_dir.name)

    if readme_text:
        readme.write_text(readme_text, encoding="utf-8", newline="\n")

    print(f"Mirrored {len(skill_dirs)} skills to {destination.relative_to(root)}")
    return 0


def mirror_agents(root: Path, check: bool) -> int:
    source = root / "agents"
    destination = root / ".opencode" / "agents"
    readme = destination / "README.md"

    if not source.is_dir():
        print("agents/ directory not found", file=sys.stderr)
        return 1

    agent_files = sorted(path for path in source.glob("*.md") if path.is_file())
    for agent_file in agent_files:
        validate_agent_file(agent_file)

    if check:
        if not destination.is_dir():
            print(".opencode/agents directory not found", file=sys.stderr)
            return 1

        issues: list[str] = []
        expected_names = {agent_file.name for agent_file in agent_files}
        actual_names = {
            path.name
            for path in destination.glob("*.md")
            if path.is_file() and path.name != "README.md"
        }
        for name in sorted(expected_names - actual_names):
            issues.append(f"missing in mirror: {destination / name}")
        for name in sorted(actual_names - expected_names):
            issues.append(f"stale in mirror: {destination / name}")
        for agent_file in agent_files:
            target = destination / agent_file.name
            if target.exists() and target.read_text(encoding="utf-8") != render_opencode_agent(agent_file):
                issues.append(f"differs: {target}")

        if issues:
            print("OpenCode agent mirror is out of sync:")
            for issue in issues:
                print(f"- {issue}")
            return 1
        print("OpenCode agent mirror is in sync")
        return 0

    destination.mkdir(parents=True, exist_ok=True)
    if readme.exists():
        readme_text = readme.read_text(encoding="utf-8")
    else:
        readme_text = ""

    for child in destination.iterdir():
        if child.name == "README.md":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()

    for agent_file in agent_files:
        (destination / agent_file.name).write_text(
            render_opencode_agent(agent_file),
            encoding="utf-8",
            newline="\n",
        )

    if readme_text:
        readme.write_text(readme_text, encoding="utf-8", newline="\n")

    print(f"Mirrored {len(agent_files)} agents to {destination.relative_to(root)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if mirror is stale")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    try:
        skill_status = mirror_skills(root, args.check)
        agent_status = mirror_agents(root, args.check)
        return 0 if skill_status == 0 and agent_status == 0 else 1
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
