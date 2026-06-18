#!/usr/bin/env python3
"""Lint a rendered Markdown test analysis solution file."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REQUIRED_SECTIONS = (
    "## 1. 需求范围",
    "## 2. 测试场景与测试点",
)

DESIGN_STAGE_TERMS = (
    "前置条件",
    "测试步骤",
    "测试数据",
    "最终预期",
    "预期结果：",
    "expectedResult",
    "testCases",
    "steps",
    "testData",
)
FORBIDDEN_METHOD_TERMS = ("方法引用", "methodRefs")

SC_RE = re.compile(r"^(#{3,5}) (SC-\d{3}(?:-\d{3}){0,2})\s+(.+)")
TP_RE = re.compile(r"^(#{4,6}) (TP-\d{3})\s+(.+)")
TC_RE = re.compile(r"^(#{5,6}) (TC-\d{3})\s+(.+)")


def has_markdown_bold_marker(line: str) -> str | None:
    if "**" in line:
        return "**"
    if re.search(r"__[^_\s][^_\n]*?__", line):
        return "__"
    return None


def numeric_suffix(value: str) -> int:
    return int(value.rsplit("-", 1)[-1])


def scenario_depth(scenario_id: str) -> int:
    return len(scenario_id.split("-")) - 1


def main() -> int:
    if len(sys.argv) != 2:
        print("用法: lint-test-analysis-solution.py <test-analysis-solution.md>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"失败: 文件不存在: {path}")
        return 1

    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    errors: list[str] = []

    for section in REQUIRED_SECTIONS:
        if section not in text:
            errors.append(f"缺少固定章节: {section}")

    for line_number, line in enumerate(lines, start=1):
        marker = has_markdown_bold_marker(line)
        if marker:
            errors.append(f"第 {line_number} 行：不得使用 Markdown 加粗标记 {marker}")
        for term in DESIGN_STAGE_TERMS:
            if term in line:
                errors.append(f"第 {line_number} 行：分析方案不得包含设计阶段字段 `{term}`")
        for term in FORBIDDEN_METHOD_TERMS:
            if term in line:
                errors.append(f"第 {line_number} 行：分析方案不得包含方法引用字段 `{term}`")

    scenario_ids: list[str] = []
    point_ids: list[str] = []
    case_ids: list[str] = []
    current_scenario_level: int | None = None
    for line_number, line in enumerate(lines, start=1):
        if match := SC_RE.match(line):
            level = len(match.group(1))
            scenario_id = match.group(2)
            scenario_ids.append(scenario_id)
            expected_level = 2 + scenario_depth(scenario_id)
            if level != expected_level:
                errors.append(f"第 {line_number} 行：{scenario_id} 标题层级应为 {'#' * expected_level}")
            current_scenario_level = level
            continue
        if match := TP_RE.match(line):
            level = len(match.group(1))
            point_id = match.group(2)
            point_ids.append(point_id)
            if current_scenario_level is None:
                errors.append(f"第 {line_number} 行：{point_id} 前缺少父级 SC")
            elif level != current_scenario_level + 1:
                errors.append(f"第 {line_number} 行：{point_id} 标题层级应比父级 SC 低一层")
            continue
        if match := TC_RE.match(line):
            case_ids.append(match.group(2))
    if not scenario_ids:
        errors.append("未找到 SC-* 测试场景标题")
    if not point_ids:
        errors.append("未找到 TP-* 测试点标题")
    if case_ids:
        errors.append("分析方案不得包含测试用例标题")

    for point_index, point_id in enumerate(point_ids, start=1):
        expected = f"TP-{point_index:03d}"
        if point_id != expected:
            errors.append(f"测试点序号应为 {expected}，实际为 {point_id}")

    if scenario_ids and not any(point_id == "TP-001" for point_id in point_ids):
        errors.append("未找到首个测试点 TP-001")

    if "E2E场景测试" not in text:
        errors.append("未找到 E2E场景测试")

    for error in errors:
        print(f"失败: {error}")
    if errors:
        return 1
    print(f"通过: {path} 测试分析方案 Markdown 校验通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
