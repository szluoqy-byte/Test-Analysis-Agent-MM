#!/usr/bin/env python3
"""Mirror root skills and agent facades into framework discovery directories."""

from __future__ import annotations

import argparse
import filecmp
import re
import shutil
import sys
from pathlib import Path

from encoding_utils import configure_stdio


NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MIRROR_DIRS = (".opencode", ".testagent")
PRIMARY_MIRROR = ".opencode"
SECONDARY_STATIC_SKIP = {"agents", "skills", "codearts.json", "logs"}
ROOT_CONFIG_MIRRORS = ("codearts.json",)


def write_text_lf(path: Path, text: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


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


def mirror_skills(root: Path, mirror_dir: str, check: bool) -> int:
    source = root / "skills"
    destination = root / mirror_dir / "skills"
    readme = destination / "README.md"

    if not source.is_dir():
        print("skills/ directory not found", file=sys.stderr)
        return 1

    skill_dirs = sorted(path for path in source.iterdir() if path.is_dir())
    for skill_dir in skill_dirs:
        validate_skill_dir(skill_dir)

    if check:
        if not destination.is_dir():
            print(f"{mirror_dir}/skills directory not found", file=sys.stderr)
            return 1
        issues = compare_dirs(source, destination)
        if issues:
            print(f"{mirror_dir} skill mirror is out of sync:")
            for issue in issues:
                print(f"- {issue}")
            return 1
        print(f"{mirror_dir} skill mirror is in sync")
        return 0

    destination.mkdir(parents=True, exist_ok=True)
    if readme.exists():
        readme_text = readme.read_text(encoding="utf-8")
    elif mirror_dir != PRIMARY_MIRROR and (root / PRIMARY_MIRROR / "skills" / "README.md").exists():
        readme_text = (root / PRIMARY_MIRROR / "skills" / "README.md").read_text(encoding="utf-8")
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
        write_text_lf(readme, readme_text)

    print(f"Mirrored {len(skill_dirs)} skills to {destination.relative_to(root)}")
    return 0


def mirror_agents(root: Path, mirror_dir: str, check: bool) -> int:
    source = root / "agents"
    destination = root / mirror_dir / "agents"
    readme = destination / "README.md"

    if not source.is_dir():
        print("agents/ directory not found", file=sys.stderr)
        return 1

    agent_files = sorted(path for path in source.glob("*.md") if path.is_file())
    for agent_file in agent_files:
        validate_agent_file(agent_file)

    if check:
        if not destination.is_dir():
            print(f"{mirror_dir}/agents directory not found", file=sys.stderr)
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
            print(f"{mirror_dir} agent mirror is out of sync:")
            for issue in issues:
                print(f"- {issue}")
            return 1
        print(f"{mirror_dir} agent mirror is in sync")
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
        write_text_lf(destination / agent_file.name, render_opencode_agent(agent_file))

    if readme_text:
        write_text_lf(readme, readme_text)

    print(f"Mirrored {len(agent_files)} agents to {destination.relative_to(root)}")
    return 0


def mirror_root_configs(root: Path, mirror_dir: str, check: bool) -> int:
    destination_dir = root / mirror_dir
    issues: list[str] = []
    for config_name in ROOT_CONFIG_MIRRORS:
        source = root / config_name
        destination = destination_dir / config_name
        if not source.exists():
            print(f"{config_name} not found", file=sys.stderr)
            return 1
        if check:
            if not destination.exists():
                issues.append(f"missing in mirror: {destination}")
            elif not filecmp.cmp(source, destination, shallow=False):
                issues.append(f"differs: {destination}")
            continue
        destination_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)

    if check:
        if issues:
            print(f"{mirror_dir} root config mirror is out of sync:")
            for issue in issues:
                print(f"- {issue}")
            return 1
        print(f"{mirror_dir} root config mirror is in sync")
    else:
        print(f"Mirrored {', '.join(ROOT_CONFIG_MIRRORS)} to {destination_dir.relative_to(root)}")
    return 0


def copy_tree_or_file(source: Path, destination: Path) -> None:
    if destination.exists():
        if destination.is_dir():
            shutil.rmtree(destination)
        else:
            destination.unlink()
    if source.is_dir():
        shutil.copytree(source, destination)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)


def compare_tree_or_file(source: Path, destination: Path) -> list[str]:
    if not destination.exists():
        return [f"missing in mirror: {destination}"]
    if source.is_dir():
        if not destination.is_dir():
            return [f"expected directory in mirror: {destination}"]
        return compare_dirs(source, destination)
    if destination.is_dir():
        return [f"expected file in mirror: {destination}"]
    if not filecmp.cmp(source, destination, shallow=False):
        return [f"differs: {destination}"]
    return []


def mirror_secondary_static(root: Path, check: bool) -> int:
    source_root = root / PRIMARY_MIRROR
    destination_root = root / ".testagent"
    if not source_root.is_dir():
        print(f"{PRIMARY_MIRROR} directory not found", file=sys.stderr)
        return 1

    source_entries = {
        child.name: child
        for child in source_root.iterdir()
        if child.name not in SECONDARY_STATIC_SKIP
    }

    if check:
        if not destination_root.is_dir():
            print(".testagent directory not found", file=sys.stderr)
            return 1
        issues: list[str] = []
        for name, source in sorted(source_entries.items()):
            issues.extend(compare_tree_or_file(source, destination_root / name))
        actual_static_names = {
            child.name
            for child in destination_root.iterdir()
            if child.name not in SECONDARY_STATIC_SKIP
        }
        for name in sorted(actual_static_names - set(source_entries)):
            issues.append(f"stale in mirror: {destination_root / name}")
        if issues:
            print(".testagent static mirror is out of sync:")
            for issue in issues:
                print(f"- {issue}")
            return 1
        print(".testagent static mirror is in sync")
        return 0

    destination_root.mkdir(parents=True, exist_ok=True)
    for child in list(destination_root.iterdir()):
        if child.name in SECONDARY_STATIC_SKIP:
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    for name, source in sorted(source_entries.items()):
        copy_tree_or_file(source, destination_root / name)
    print(f"Mirrored static {PRIMARY_MIRROR} entries to {destination_root.relative_to(root)}")
    return 0


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if mirror is stale")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    try:
        statuses: list[int] = []
        for mirror_dir in MIRROR_DIRS:
            statuses.append(mirror_skills(root, mirror_dir, args.check))
            statuses.append(mirror_agents(root, mirror_dir, args.check))
            statuses.append(mirror_root_configs(root, mirror_dir, args.check))
        statuses.append(mirror_secondary_static(root, args.check))
        return 0 if all(status == 0 for status in statuses) else 1
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
