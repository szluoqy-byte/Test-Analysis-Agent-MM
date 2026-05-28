#!/usr/bin/env python3
"""Lint a Markdown test design solution file."""

from __future__ import annotations

import re
import sys
from pathlib import Path


REQUIRED_SECTIONS = [
    "## 1. 需求范围",
    "## 2. 测试场景与测试设计",
]

INFO_HEADER = "| 字段 | 内容 |"
DESIGN_ITEM_HEADER = "| 测试设计项 ID | 测试设计项 | 预期结果 |"
EXPECTED_FALLBACK = "待人工分析确认"

BANNED_MAIN_SECTIONS = (
    "## 3. 未明确规则",
    "## 未明确规则",
    "## 待确认信息",
    "## 3. 待确认信息",
)
BANNED_TERMS = (
    "Test Scenario",
    "Test Point",
    "Test Design Item",
    "测试用例标题大纲",
    "测试用例标题项",
    "标题项 ID",
    "测试用例标题",
    "覆盖意图",
    "级别",
    "输入条件与数据依赖",
    "判定关注",
    "待确认信息",
    "TD-",
    "TC-",
    "TCT-",
    "TI-",
    "ITP-",
    "ITDI-",
)
BANNED_COLUMNS = {
    "前置步骤",
    "测试步骤",
    "操作步骤",
    "执行数据",
    "自动化脚本",
}
BANNED_STEP_WORDS = (
    "点击",
    "然后",
    "步骤",
    "执行用例",
    "输入以下",
    "断言",
    "curl ",
    "SELECT ",
    "UPDATE ",
)
GENERIC_REFERENCE_WORDS = (
    "见原始需求",
    "见需求",
    "见设计方案",
    "详见原始需求",
    "详见设计方案",
    "参考需求",
    "参考设计",
    "按需求",
    "同上",
    "TBD",
    "待补充",
    "待确认",
)
EMPTY_MARKERS = {"", "<代表性条件、数据、状态或组合>", "<明确预期结果或待人工分析确认>", "<测试点>", "<测试场景名称>"}


def split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def collect_all_tables(lines: list[str], header: str) -> list[list[tuple[int, list[str]]]]:
    tables: list[list[tuple[int, list[str]]]] = []
    for start, line in enumerate(lines):
        if line != header:
            continue
        rows: list[tuple[int, list[str]]] = []
        for index in range(start + 2, len(lines)):
            row = lines[index]
            if not row.startswith("|"):
                break
            rows.append((index + 1, split_row(row)))
        tables.append(rows)
    return tables


def has_generic_reference(value: str) -> bool:
    if value == EXPECTED_FALLBACK:
        return False
    return any(word in value for word in GENERIC_REFERENCE_WORDS)


def main() -> int:
    if len(sys.argv) != 2:
        print("用法: lint-test-design-solution.py <测试设计方案.md>", file=sys.stderr)
        return 2

    solution_path = Path(sys.argv[1])
    text = solution_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    errors: list[str] = []
    warnings: list[str] = []

    if not lines or not lines[0].startswith("# ") or "测试设计方案" not in lines[0]:
        errors.append("缺少 Markdown 一级标题，或标题未声明“测试设计方案”")

    for section in REQUIRED_SECTIONS:
        if section not in text:
            errors.append(f"缺少必需章节: {section}")

    for section in BANNED_MAIN_SECTIONS:
        if section in text:
            errors.append(f"主交付件不应包含章节: {section}")

    for line_number, line in enumerate(lines, start=1):
        if re.match(r"^## 3\.", line):
            errors.append(f"第 {line_number} 行：主交付件不应设置第三章，请把缺口沉淀到预期结果的“{EXPECTED_FALLBACK}”")
        for term in BANNED_TERMS:
            if term in line:
                errors.append(f"第 {line_number} 行：出现旧版字段或术语: {term}")
        if line.startswith("|"):
            cells = set(split_row(line))
            for column in BANNED_COLUMNS:
                if column in cells:
                    errors.append(f"第 {line_number} 行：出现完整测试用例字段: {column}")

    if INFO_HEADER not in text:
        errors.append(f"缺少需求范围表头: {INFO_HEADER}")
    if DESIGN_ITEM_HEADER not in text:
        errors.append(f"缺少测试设计项表头: {DESIGN_ITEM_HEADER}")

    scenario_headings = [line for line in lines if re.match(r"^### 场景 SC-\d{3}：", line)]
    if not scenario_headings:
        errors.append("未找到 `### 场景 SC-*：` 场景标题")

    point_headings = [line for line in lines if re.match(r"^#### 测试点 TP-\d{3}：", line)]
    if not point_headings:
        errors.append("未找到 `#### 测试点 TP-*：` 测试点标题")

    design_tables = collect_all_tables(lines, DESIGN_ITEM_HEADER)
    design_rows = [
        (line_number, cells)
        for rows in design_tables
        for line_number, cells in rows
        if cells and cells[0].startswith("TDI-")
    ]
    if not design_rows:
        errors.append("未找到 TDI-* 测试设计项")

    expected_tdi_id = 1
    seen_items: set[tuple[str, str]] = set()
    for line_number, cells in design_rows:
        if len(cells) != 3:
            errors.append(f"第 {line_number} 行：测试设计项期望 3 列，实际 {len(cells)} 列")
            continue
        design_id, item, expected_result = cells
        expected_id = f"TDI-{expected_tdi_id:03d}"
        if design_id != expected_id:
            errors.append(f"第 {line_number} 行：期望测试设计项 ID {expected_id}，实际 {design_id}")
        expected_tdi_id += 1

        if item in EMPTY_MARKERS:
            errors.append(f"第 {line_number} 行：测试设计项不能为空或模板占位")
        if expected_result in EMPTY_MARKERS:
            errors.append(f"第 {line_number} 行：预期结果不能为空或模板占位")
        if has_generic_reference(item):
            errors.append(f"第 {line_number} 行：测试设计项使用了非自包含占位表达: {item}")
        if has_generic_reference(expected_result):
            errors.append(f"第 {line_number} 行：预期结果必须写明确结果或“{EXPECTED_FALLBACK}”，当前为: {expected_result}")
        if any(word in item for word in BANNED_STEP_WORDS):
            errors.append(f"第 {line_number} 行：测试设计项包含步骤化或脚本化表达: {item}")
        if any(word in expected_result for word in BANNED_STEP_WORDS):
            errors.append(f"第 {line_number} 行：预期结果包含步骤化或脚本化表达: {expected_result}")
        if item in {"验证功能正常", "异常场景覆盖", "正常场景", "异常场景", "功能正确"}:
            errors.append(f"第 {line_number} 行：测试设计项过于泛化: {item}")

        key = (item, expected_result)
        if key in seen_items:
            warnings.append(f"第 {line_number} 行：测试设计项与前文重复: {item}")
        seen_items.add(key)

    if len(design_tables) < len(point_headings):
        errors.append(f"测试设计项表数量少于测试点数量：测试点 {len(point_headings)} 个，设计项表 {len(design_tables)} 个")

    for warning in warnings:
        print(f"警告: {warning}")
    for error in errors:
        print(f"失败: {error}")

    if errors:
        return 1
    print(f"通过: {solution_path} 已通过测试设计方案确定性校验")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
