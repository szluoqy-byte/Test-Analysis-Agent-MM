#!/usr/bin/env python3
"""Lint a rendered Markdown test design solution file."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from encoding_utils import configure_stdio

REQUIRED_SECTIONS = (
    "## 设计输入",
)
FORBIDDEN_METHOD_TERMS = ("方法引用", "methodRefs")

SC_RE = re.compile(r"^(#{2,4}) (SC-\d{3}(?:-\d{3}){0,2})\s+(.+)")
TP_RE = re.compile(r"^(#{3,5}) (TP-\d{3})\s+(.+)")
TC_RE = re.compile(r"^(#{4,5}) (TC-\d{3})\s+(.+)")
TC_BULLET_RE = re.compile(r"^\s*-\s+(TC-\d{3})\s+(.+)")
NUMBERED_ITEM_RE = re.compile(r"^\s*(?:-\s+)?\d+[.、]\s*.+")
INLINE_NUMBERED_ITEM_RE = re.compile(r"(?:^|[；;]\s*|<br/?>\s*|\\n\s*)(\d+)[.、]\s*")


def has_markdown_bold_marker(line: str) -> str | None:
    if "**" in line:
        return "**"
    if re.search(r"__[^_\s][^_\n]*?__", line):
        return "__"
    return None


def scenario_depth(scenario_id: str) -> int:
    return len(scenario_id.split("-")) - 1


def numbered_item_count(text: str) -> int:
    return len(INLINE_NUMBERED_ITEM_RE.findall(text.strip()))


def main() -> int:
    configure_stdio()
    if len(sys.argv) != 2:
        print("用法: lint-test-design-solution.py <test-design-solution.md>", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"失败: 文件不存在: {path}")
        return 1

    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    errors: list[str] = []

    for section in REQUIRED_SECTIONS:
        if section not in text:
            errors.append(f"缺少固定章节: {section}")

    for line_number, line in enumerate(lines, start=1):
        marker = has_markdown_bold_marker(line)
        if marker:
            errors.append(f"第 {line_number} 行：不得使用 Markdown 加粗标记 {marker}")
        for term in FORBIDDEN_METHOD_TERMS:
            if term in line:
                errors.append(f"第 {line_number} 行：测试设计方案不得包含方法引用字段 `{term}`")

    scenario_ids: list[str] = []
    point_ids: list[str] = []
    case_ids: list[str] = []
    current_scenario_level: int | None = None
    current_point_level: int | None = None
    for line_number, line in enumerate(lines, start=1):
        if match := SC_RE.match(line):
            level = len(match.group(1))
            scenario_id = match.group(2)
            scenario_ids.append(scenario_id)
            expected_level = 1 + scenario_depth(scenario_id)
            if level != expected_level:
                errors.append(f"第 {line_number} 行：{scenario_id} 标题层级应为 {'#' * expected_level}")
            current_scenario_level = level
            current_point_level = None
            continue
        if match := TP_RE.match(line):
            level = len(match.group(1))
            point_id = match.group(2)
            point_ids.append(point_id)
            if current_scenario_level is None:
                errors.append(f"第 {line_number} 行：{point_id} 前缺少父级 SC")
            elif level != current_scenario_level + 1:
                errors.append(f"第 {line_number} 行：{point_id} 标题层级应比父级 SC 低一层")
            current_point_level = level
            continue
        if match := TC_RE.match(line):
            level = len(match.group(1))
            case_id = match.group(2)
            case_ids.append(case_id)
            if current_point_level is None:
                errors.append(f"第 {line_number} 行：{case_id} 前缺少父级 TP")
            elif current_point_level < 5 and level != current_point_level + 1:
                errors.append(f"第 {line_number} 行：{case_id} 标题层级应比父级 TP 低一层")
            continue
        if match := TC_BULLET_RE.match(line):
            case_id = match.group(1)
            case_ids.append(case_id)
            if current_point_level is None:
                errors.append(f"第 {line_number} 行：{case_id} 前缺少父级 TP")
            elif current_point_level != 5:
                errors.append(f"第 {line_number} 行：{case_id} 只有在父级 TP 已是 5 级标题时才使用列表节点")
    if not scenario_ids:
        errors.append("未找到 SC-* 测试场景标题")
    if not point_ids:
        errors.append("未找到 TP-* 测试点标题")
    if not case_ids:
        errors.append("未找到 TC-* 测试用例")

    duplicate_points = sorted({point_id for point_id in point_ids if point_ids.count(point_id) > 1})
    duplicate_cases = sorted({case_id for case_id in case_ids if case_ids.count(case_id) > 1})
    if duplicate_points:
        errors.append(f"测试点编号重复: {', '.join(duplicate_points)}")
    if duplicate_cases:
        errors.append(f"测试用例编号重复: {', '.join(duplicate_cases)}")

    required_markers = ("- 前置条件：", "- 测试数据：", "- 测试步骤：", "- 预期结果：", "- 用例级别：", "- 最终预期：", "- 来源引用：")
    for marker in required_markers:
        if marker not in text:
            errors.append(f"缺少 TC 固定字段: {marker}")

    step_items = [line for line in lines if NUMBERED_ITEM_RE.match(line) or numbered_item_count(line) > 0]
    if not step_items:
        errors.append("未找到有效编号项")

    current_case: str | None = None
    step_count = 0
    expected_count = 0
    mode: str | None = None
    for line in lines + ["#### END"]:
        case_match = TC_RE.match(line) or TC_BULLET_RE.match(line)
        if case_match or line == "#### END":
            if current_case and step_count != expected_count:
                errors.append(f"{current_case} 测试步骤数量({step_count})与预期结果数量({expected_count})不一致")
            current_case = case_match.group(2) if case_match and line.startswith("#") else case_match.group(1) if case_match else None
            step_count = 0
            expected_count = 0
            mode = None
            continue
        stripped = line.strip()
        if stripped.startswith("- 测试步骤：") or stripped.startswith("测试步骤："):
            mode = "steps"
            step_count += numbered_item_count(stripped.split("：", 1)[1] if "：" in stripped else "")
            continue
        if stripped.startswith("- 预期结果：") or stripped.startswith("预期结果："):
            mode = "expected"
            expected_count += numbered_item_count(stripped.split("：", 1)[1] if "：" in stripped else "")
            continue
        if (
            stripped.startswith("|")
            or stripped.startswith("- 前置条件：")
            or stripped.startswith("前置条件：")
            or stripped.startswith("- 测试数据：")
            or stripped.startswith("测试数据：")
        ):
            mode = None
            continue
        if NUMBERED_ITEM_RE.match(line):
            if mode == "steps":
                step_count += 1
            elif mode == "expected":
                expected_count += 1

    if "E2E场景测试" not in text:
        errors.append("未找到 E2E场景测试")

    for error in errors:
        print(f"失败: {error}")
    if errors:
        return 1
    print(f"通过: {path} 测试设计方案 Markdown 校验通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
