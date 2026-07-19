#!/usr/bin/env python3
"""Validate the static stage contract used by multi-step skills."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from encoding_utils import configure_stdio


STEP_CONTRACT_SKILLS = {
    "coverage-review": "审查阶段",
    "final-report-generation": "报告生成阶段",
    "normalize-input-documents": "归一化阶段",
    "test-analysis-design-workflow": "执行阶段",
    "test-analysis-solution-generation": "生成阶段",
    "test-analysis-workflow": "执行阶段",
    "test-case-writing": "写作阶段",
    "test-design-solution-generation": "生成阶段",
    "test-design-workflow": "执行阶段",
}
INDEX_STEP_RE = re.compile(r"^- \[ \] Step ([1-9][0-9]*): (.+?)\s*$")
DETAIL_STEP_RE = re.compile(r"^### Step ([1-9][0-9]*): (.+?)\s*$")
RETIRED_MARKERS = (
    "Progress:",
    "## 计划-校验-执行模式",
    "## 执行步骤与生成原则",
)


def h2_section(lines: list[str], heading: str) -> list[str] | None:
    target = f"## {heading}"
    try:
        start = lines.index(target)
    except ValueError:
        return None

    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    return lines[start + 1 : end]


def parse_steps(lines: list[str], pattern: re.Pattern[str]) -> list[tuple[int, str]]:
    steps: list[tuple[int, str]] = []
    for line in lines:
        match = pattern.fullmatch(line)
        if match:
            steps.append((int(match.group(1)), match.group(2)))
    return steps


def validate_steps(label: str, steps: list[tuple[int, str]], issues: list[str]) -> None:
    if not steps:
        issues.append(f"{label} must declare at least one Step")
        return

    numbers = [number for number, _ in steps]
    expected = list(range(1, len(steps) + 1))
    if numbers != expected:
        issues.append(f"{label} Step numbers must be continuous from 1, got {numbers}")

    titles = [title for _, title in steps]
    if len(titles) != len(set(titles)):
        issues.append(f"{label} Step titles must be unique")


def validate_skill(root: Path, skill_name: str, stage_heading: str) -> list[str]:
    skill_path = root / "skills" / skill_name / "SKILL.md"
    label = skill_path.relative_to(root).as_posix()
    if not skill_path.exists():
        return [f"{label} is missing"]

    text = skill_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    issues: list[str] = []
    for marker in RETIRED_MARKERS:
        if marker in text:
            issues.append(f"{label} must not contain retired stage marker {marker!r}")

    if lines.count(f"## {stage_heading}") != 1:
        issues.append(f"{label} must contain exactly one ## {stage_heading}")
    if lines.count("## 各阶段执行要求") != 1:
        issues.append(f"{label} must contain exactly one ## 各阶段执行要求")

    index_section = h2_section(lines, stage_heading)
    if index_section is None:
        return [*issues, f"{label} is missing ## {stage_heading}"]
    detail_section = h2_section(lines, "各阶段执行要求")
    if detail_section is None:
        return [*issues, f"{label} is missing ## 各阶段执行要求"]

    index_steps = parse_steps(index_section, INDEX_STEP_RE)
    detail_steps = parse_steps(detail_section, DETAIL_STEP_RE)
    validate_steps(f"{label} static stage index", index_steps, issues)
    validate_steps(f"{label} detailed stage requirements", detail_steps, issues)
    if index_steps != detail_steps:
        issues.append(
            f"{label} static stage index and detailed requirements must use the same Step numbers and titles"
        )
    for index, line in enumerate(detail_section):
        if not DETAIL_STEP_RE.fullmatch(line):
            continue
        end = len(detail_section)
        for candidate in range(index + 1, len(detail_section)):
            if DETAIL_STEP_RE.fullmatch(detail_section[candidate]):
                end = candidate
                break
        if not any(candidate.strip() for candidate in detail_section[index + 1 : end]):
            issues.append(f"{label} {line} must include detailed execution requirements")
    return issues


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="校验多步骤 skill 的阶段索引契约")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="仓库根目录，默认使用当前脚本所在仓库",
    )
    args = parser.parse_args()
    root = args.root.resolve()

    issues: list[str] = []
    for skill_name, stage_heading in STEP_CONTRACT_SKILLS.items():
        issues.extend(validate_skill(root, skill_name, stage_heading))

    if issues:
        print("Skill stage contract validation failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("Skill stage contract validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
