#!/usr/bin/env python3
"""Run deterministic smoke checks for example testcase title outlines."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


EXAMPLE_RUN_SUFFIX = "-run"
REQUIRED_FILES = [
    ".editorconfig",
    ".gitattributes",
    "AGENTS.md",
    "CLAUDE.md",
    "opencode.json",
    ".claude-plugin/plugin.json",
    ".opencode/commands/analyze-requirement-testcase-outline.md",
    ".opencode/skills/README.md",
    "docs/testcase-title-outline-agent-design.md",
    "docs/skills-architecture-optimization-analysis.md",
    "docs/output-artifact-contract.md",
    "docs/knowledge-skill-memory-boundaries.md",
    "knowledge/README.md",
    "knowledge/basic-test-types.md",
    "knowledge/test-analysis-methodology.md",
    "knowledge/testcase-title-outline-standard.md",
    "knowledge/testcase-design-patterns/README.md",
    "templates/testcase-title-outline-template.md",
    "templates/task-list-template.md",
    "templates/context-pack-template.md",
    "templates/clarification-template.md",
    "templates/design-facts-template.md",
    "skills/design-solution-extraction/SKILL.md",
    "quality-gates/testcase-title-outline-check.md",
    "quality-gates/coverage-check.md",
    "quality-gates/expert-review-rubric.md",
    "quality-gates/traceability-check.md",
    "outputs/runs/.gitkeep",
    "memory/README.md",
    "examples/evaluation-matrix.md",
    "bin/lint-testcase-title-outline.py",
    "bin/sync-opencode-skills.py",
    "bin/validate-agent-runtime.py",
]


def example_run_dir(repo_root: Path, stem: str) -> Path:
    return repo_root / "examples" / "outputs" / "runs" / f"{stem}{EXAMPLE_RUN_SUFFIX}"


def run_command(cmd: list[str], cwd: Path) -> bool:
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    result = subprocess.run(
        cmd,
        cwd=cwd,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
        env=env,
    )
    if result.stdout:
        print(result.stdout.rstrip())
    if result.stderr:
        print(result.stderr.rstrip(), file=sys.stderr)
    return result.returncode == 0


def check_required_files(repo_root: Path) -> list[str]:
    missing: list[str] = []
    for relative in REQUIRED_FILES:
        if not (repo_root / relative).exists():
            missing.append(relative)
    return missing


def check_one_requirement(repo_root: Path, requirement: Path) -> bool:
    stem = requirement.stem
    run_dir = example_run_dir(repo_root, stem)
    outline = run_dir / "deliverables" / "testcase-title-outline.md"

    print(f"\n== {requirement} ==")
    if not run_dir.is_dir():
        print(f"失败: 未找到固定示例运行目录 {run_dir}")
        return False
    if not outline.exists():
        print(f"失败: 未找到示例标题大纲 {outline}")
        return False

    return run_command([sys.executable, "bin/lint-testcase-title-outline.py", str(outline)], repo_root)


def main() -> int:
    parser = argparse.ArgumentParser(description="运行 Testcase Title Outline Agent 的示例 smoke 检查")
    parser.add_argument("requirements", nargs="*", type=Path, help="需求 Markdown 路径，默认检查 examples/requirements/*.md")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    missing = check_required_files(repo_root)
    if missing:
        for relative in missing:
            print(f"失败: 缺少关键文件 {relative}")
        return 1
    print("通过: 关键项目文件存在")

    requirements = args.requirements
    if not requirements:
        requirements = sorted((repo_root / "examples" / "requirements").glob("*.md"))
    if not requirements:
        print("失败: 未找到可检查的示例需求")
        return 1

    ok = True
    for requirement in requirements:
        requirement = requirement if requirement.is_absolute() else repo_root / requirement
        if requirement.suffix != ".md" or not requirement.exists():
            print(f"失败: 非法需求文件 {requirement}")
            ok = False
            continue
        ok &= check_one_requirement(repo_root, requirement)

    if not ok:
        return 1
    print("\n通过: smoke 检查全部通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
