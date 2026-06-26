#!/usr/bin/env python3
"""Run deterministic smoke checks for example test analysis solutions."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from encoding_utils import configure_stdio, utf8_env


EXAMPLE_RUN_SUFFIX = "-run"
REQUIRED_FILES = [
    ".editorconfig",
    ".gitattributes",
    "AGENTS.md",
    "CLAUDE.md",
    "opencode.json",
    "codearts.json",
    ".claude-plugin/plugin.json",
    "agents/file-normalization-agent.md",
    "agents/test-analysis-agent.md",
    "agents/test-design-agent.md",
    ".opencode/agents/file-normalization-agent.md",
    ".opencode/agents/test-analysis-agent.md",
    ".opencode/agents/test-design-agent.md",
    ".opencode/commands/test-analysis-workflow.md",
    ".opencode/commands/test-design-workflow.md",
    ".opencode/commands/normalize-input-documents.md",
    ".opencode/codearts.json",
    ".opencode/skills/README.md",
    ".testagent/agents/file-normalization-agent.md",
    ".testagent/agents/test-analysis-agent.md",
    ".testagent/agents/test-design-agent.md",
    ".testagent/commands/test-analysis-workflow.md",
    ".testagent/commands/test-design-workflow.md",
    ".testagent/commands/normalize-input-documents.md",
    ".testagent/codearts.json",
    ".testagent/kernel.json",
    ".testagent/skills/README.md",
    "docs/test-analysis-agent-design.md",
    "docs/test-design-agent-design.md",
    "docs/skills-architecture-optimization-analysis.md",
    "docs/output-artifact-contract.md",
    "docs/knowledge-skill-memory-boundaries.md",
    "knowledge/README.md",
    "skills/coverage-review/references/basic-test-types.md",
    "knowledge/test-workflow-boundaries.md",
    "knowledge/test-analysis-solution-standard.md",
    "knowledge/test-design-solution-standard.md",
    "knowledge/test-techniques/README.md",
    "rules/README.md",
    "rules/projects/README.md",
    "rules/user/README.md",
    "templates/test-analysis-solution-template.md",
    "templates/test-design-solution-template.md",
    "templates/coverage-review-template.md",
    "templates/context-pack-template.md",
    "templates/input-fact-model-template.md",
    "templates/test-analysis-solution-json-template.json",
    "templates/test-design-solution-json-template.json",
    "templates/context-pack-json-template.json",
    "templates/input-fact-model-json-template.json",
    "templates/review-report-json-template.json",
    "templates/coverage-review-json-template.json",
    "templates/process-artifacts-json-template.json",
    "skills/input-fact-modeling/SKILL.md",
    "skills/context-source-indexing/SKILL.md",
    "skills/context-source-indexing/scripts/build-context-source-index.py",
    "skills/context-capture/SKILL.md",
    "skills/test-analysis-workflow/SKILL.md",
    "skills/test-design-workflow/SKILL.md",
    "skills/test-analysis-solution-generation/SKILL.md",
    "skills/test-analysis-solution-review/SKILL.md",
    "skills/test-case-writing/SKILL.md",
    "skills/test-design-solution-generation/SKILL.md",
    "skills/test-design-solution-review/SKILL.md",
    "skills/coverage-review/references/coverage-check.md",
    "skills/coverage-review/references/review-gates.md",
    "skills/coverage-review/references/context-application-gates.md",
    "skills/coverage-review/references/deep-review-rubric.md",
    "outputs/runs/.gitkeep",
    "memory/README.md",
    "bin/lint-test-analysis-solution.py",
    "bin/lint-test-design-solution.py",
    "bin/init-scenario-tree.py",
    "bin/lint-scenario-tree.py",
    "bin/lint-run-json.py",
    "bin/render-run-markdown.py",
    "bin/run_artifacts.py",
    "bin/build-rules-pack.py",
    "bin/build-generation-context.py",
    "bin/generation_context.py",
    "bin/init-report-artifact.py",
    "bin/apply-coverage-gaps.py",
    "bin/update-run-task.py",
    "bin/extract-test-point-work-items.py",
    "bin/init-test-point-slice.py",
    "bin/merge-test-point-slice.py",
    "bin/extract-test-case-work-items.py",
    "bin/init-test-case-slice.py",
    "bin/merge-test-case-slice.py",
    "skills/normalize-input-documents/scripts/normalize-office-input.py",
    "bin/sync-opencode-skills.py",
    "bin/validate-agent-runtime.py",
    "skills/normalize-input-documents/SKILL.md",
    "skills/normalize-input-documents/references/docx-image-and-diagram-workflow.md",
    "skills/normalize-input-documents/references/xlsx-to-markdown.md",
    "skills/normalize-input-documents/references/xlsx-to-ai-knowledge-base.md",
]


def example_run_dir(repo_root: Path, stem: str) -> Path:
    return repo_root / "examples" / "outputs" / "runs" / f"{stem}{EXAMPLE_RUN_SUFFIX}"


def run_command(cmd: list[str], cwd: Path) -> bool:
    env = utf8_env()
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
    solution = run_dir / "deliverables" / "test-analysis-solution.md"
    solution_json = run_dir / "deliverables" / "test-analysis-solution.json"
    design_solution = run_dir / "deliverables" / "test-design-solution.md"

    print(f"\n== {requirement} ==")
    if not run_dir.is_dir():
        print(f"失败: 未找到固定示例运行目录 {run_dir}")
        return False
    if not solution.exists():
        print(f"失败: 未找到示例测试分析方案 {solution}")
        return False
    if not solution_json.exists():
        print(f"失败: 未找到示例测试分析方案 JSON {solution_json}")
        return False

    ok = run_command([sys.executable, "bin/lint-run-json.py", str(run_dir)], repo_root)
    ok &= run_command([sys.executable, "bin/render-run-markdown.py", str(run_dir), "--check"], repo_root)
    ok &= run_command([sys.executable, "bin/lint-test-analysis-solution.py", str(solution)], repo_root)
    if design_solution.exists():
        ok &= run_command([sys.executable, "bin/lint-test-design-solution.py", str(design_solution)], repo_root)
    ok &= run_command([sys.executable, "bin/check-artifact-consistency.py", str(run_dir)], repo_root)
    return ok


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="运行 Test Analysis Agent 的示例 smoke 检查")
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
