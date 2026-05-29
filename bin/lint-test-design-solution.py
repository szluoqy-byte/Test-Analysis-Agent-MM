#!/usr/bin/env python3
"""Lint a Markdown test design solution file."""

from __future__ import annotations

import re
import sys
from pathlib import Path


REQUIRED_SECTIONS = [
    "## 1. 设计输入",
    "## 2. 测试场景与测试设计",
]

INFO_HEADER = "| 字段 | 内容 |"
DESIGN_ITEM_HEADER = "| 测试设计项 ID | 条件/数据/状态/组合 | 预期结果 |"
EXPECTED_FALLBACK = "待人工分析确认"
DETAIL_PREFIX = "**测试点详情**："

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
EMPTY_MARKERS = {
    "",
    "<代表性条件、数据、状态或组合>",
    "<明确预期结果或待人工分析确认>",
    "<测试点>",
    "<测试点明细>",
    "<测试场景名称>",
}


def split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def has_generic_reference(value: str) -> bool:
    if value == EXPECTED_FALLBACK:
        return False
    return any(word in value for word in GENERIC_REFERENCE_WORDS)


def parse_id_sequence(lines: list[str], pattern: str) -> list[tuple[int, str]]:
    ids: list[tuple[int, str]] = []
    for line_number, line in enumerate(lines, start=1):
        match = re.match(pattern, line)
        if match:
            ids.append((line_number, match.group(1)))
    return ids


def check_global_sequence(ids: list[tuple[int, str]], prefix: str, errors: list[str]) -> None:
    for expected_index, (line_number, actual_id) in enumerate(ids, start=1):
        expected_id = f"{prefix}-{expected_index:03d}"
        if actual_id != expected_id:
            errors.append(f"第 {line_number} 行：期望 {expected_id}，实际 {actual_id}")


def collect_detail_blocks(lines: list[str]) -> list[tuple[int, str, list[str]]]:
    blocks: list[tuple[int, str, list[str]]] = []
    for index, line in enumerate(lines):
        match = re.match(r"^##### (TP-\d{3}-\d{3})\s+(.+)", line)
        if not match:
            continue
        block_lines: list[str] = []
        for next_line in lines[index + 1 :]:
            if next_line.startswith("##### ") or next_line.startswith("#### ") or next_line.startswith("### "):
                break
            block_lines.append(next_line)
        blocks.append((index + 1, match.group(1), block_lines))
    return blocks


def collect_design_rows(block_lines: list[str]) -> list[tuple[int, list[str]]]:
    rows: list[tuple[int, list[str]]] = []
    for index, line in enumerate(block_lines):
        if line != DESIGN_ITEM_HEADER:
            continue
        for row_index in range(index + 2, len(block_lines)):
            row = block_lines[row_index]
            if not row.startswith("|"):
                break
            cells = split_row(row)
            if cells and cells[0].startswith("TDI-"):
                rows.append((row_index + 1, cells))
    return rows


def main() -> int:
    if len(sys.argv) != 2:
        print("用法: lint-test-design-solution.py <测试设计方案.md>", file=sys.stderr)
        return 2

    solution_path = Path(sys.argv[1])
    text = solution_path.read_text(encoding="utf-8-sig")
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
        errors.append(f"缺少输入/场景信息表头: {INFO_HEADER}")
    if DESIGN_ITEM_HEADER not in text:
        errors.append(f"缺少测试设计项表头: {DESIGN_ITEM_HEADER}")

    scenario_ids = parse_id_sequence(lines, r"^### (SC-\d{3})\s+.+")
    if not scenario_ids:
        errors.append("未找到 `### SC-* <测试场景名称>` 场景标题")
    else:
        check_global_sequence(scenario_ids, "SC", errors)

    point_ids = parse_id_sequence(lines, r"^#### (TP-\d{3})\s+.+")
    if not point_ids:
        errors.append("未找到 `#### TP-* <测试点>` 测试点标题")
    else:
        check_global_sequence(point_ids, "TP", errors)

    detail_blocks = collect_detail_blocks(lines)
    if not detail_blocks:
        errors.append("未找到 `##### TP-*-* <测试点明细>` 测试点明细标题")

    details_by_point: dict[str, list[tuple[int, str]]] = {}
    all_design_rows: list[tuple[int, list[str]]] = []
    for line_number, detail_id, block_lines in detail_blocks:
        parent_id = "-".join(detail_id.split("-")[:2])
        details_by_point.setdefault(parent_id, []).append((line_number, detail_id))

        title_line = lines[line_number - 1]
        detail_title = re.sub(r"^##### TP-\d{3}-\d{3}\s+", "", title_line).strip()
        if detail_title in EMPTY_MARKERS:
            errors.append(f"第 {line_number} 行：测试点明细标题不能为空或模板占位")
        if any(word in detail_title for word in BANNED_STEP_WORDS):
            errors.append(f"第 {line_number} 行：测试点明细标题包含步骤化或脚本化表达: {detail_title}")

        detail_line = next((line for line in block_lines if line.startswith(DETAIL_PREFIX)), "")
        if not detail_line:
            errors.append(f"第 {line_number} 行：测试点明细缺少 `{DETAIL_PREFIX}`")
        elif detail_line.removeprefix(DETAIL_PREFIX).strip() in EMPTY_MARKERS:
            errors.append(f"第 {line_number} 行：测试点详情不能为空或模板占位")

        design_rows = collect_design_rows(block_lines)
        if not design_rows:
            errors.append(f"第 {line_number} 行：测试点明细下缺少 TDI-* 测试设计项表")
        all_design_rows.extend((line_number + offset, cells) for offset, cells in design_rows)

    for _, point_id in point_ids:
        if point_id not in details_by_point:
            errors.append(f"测试点 {point_id} 下缺少测试点明细")

    for parent_id, details in details_by_point.items():
        for expected_index, (line_number, actual_id) in enumerate(details, start=1):
            expected_id = f"{parent_id}-{expected_index:03d}"
            if actual_id != expected_id:
                errors.append(f"第 {line_number} 行：期望测试点明细 ID {expected_id}，实际 {actual_id}")

    if not all_design_rows:
        errors.append("未找到 TDI-* 测试设计项")

    seen_items: set[tuple[str, str]] = set()
    for expected_index, (line_number, cells) in enumerate(all_design_rows, start=1):
        if len(cells) != 3:
            errors.append(f"第 {line_number} 行：测试设计项期望 3 列，实际 {len(cells)} 列")
            continue

        design_id, item, expected_result = cells
        expected_id = f"TDI-{expected_index:03d}"
        if design_id != expected_id:
            errors.append(f"第 {line_number} 行：期望测试设计项 ID {expected_id}，实际 {design_id}")

        if item in EMPTY_MARKERS:
            errors.append(f"第 {line_number} 行：条件/数据/状态/组合不能为空或模板占位")
        if expected_result in EMPTY_MARKERS:
            errors.append(f"第 {line_number} 行：预期结果不能为空或模板占位")
        if has_generic_reference(item):
            errors.append(f"第 {line_number} 行：条件/数据/状态/组合使用了非自包含占位表达: {item}")
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
