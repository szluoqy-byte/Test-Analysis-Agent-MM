#!/usr/bin/env python3
"""Lint a rendered Markdown test design solution file."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REQUIRED_SECTIONS = (
    "## 1. 设计输入",
    "## 2. 测试场景与测试设计",
)

SC_RE = re.compile(r"^### (SC-\d{3}(?:-\d{3}){0,2})\s+(.+)")
TP_RE = re.compile(r"^#### (TP-\d{3})\s+(.+)")
TC_RE = re.compile(r"^##### (TC-\d{3})\s+(.+)")
STEP_ROW_RE = re.compile(r"^\|\s*(\d+)\s*\|\s*([^|]+)\|\s*([^|]+)\|")


def has_markdown_bold_marker(line: str) -> str | None:
    if "**" in line:
        return "**"
    if re.search(r"__[^_\s][^_\n]*?__", line):
        return "__"
    return None


def main() -> int:
    if len(sys.argv) != 2:
        print("用法: lint-test-design-solution.py <test-design-solution.md>", file=sys.stderr)
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

    scenario_ids = [match.group(1) for line in lines if (match := SC_RE.match(line))]
    point_ids = [match.group(1) for line in lines if (match := TP_RE.match(line))]
    case_ids = [match.group(1) for line in lines if (match := TC_RE.match(line))]
    if not scenario_ids:
        errors.append("未找到 SC-* 测试场景标题")
    if not point_ids:
        errors.append("未找到 TP-* 测试点标题")
    if not case_ids:
        errors.append("未找到 TC-* 测试用例标题")

    for point_index, point_id in enumerate(point_ids, start=1):
        expected = f"TP-{point_index:03d}"
        if point_id != expected:
            errors.append(f"测试点序号应为 {expected}，实际为 {point_id}")
    for case_index, case_id in enumerate(case_ids, start=1):
        expected = f"TC-{case_index:03d}"
        if case_id != expected:
            errors.append(f"测试用例序号应为 {expected}，实际为 {case_id}")

    required_markers = ("- 前置条件：", "- 测试数据：", "- 测试步骤：", "- 最终预期：")
    for marker in required_markers:
        if marker not in text:
            errors.append(f"缺少 TC 固定字段: {marker}")

    step_rows = [line for line in lines if STEP_ROW_RE.match(line)]
    if not step_rows:
        errors.append("未找到测试步骤表格中的有效步骤行")

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
