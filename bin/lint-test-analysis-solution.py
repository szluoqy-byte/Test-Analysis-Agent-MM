#!/usr/bin/env python3
"""Lint a Markdown test analysis solution file."""

from __future__ import annotations

import re
import sys
from pathlib import Path


REQUIRED_SECTIONS = [
    "## 1. 需求范围",
    "## 2. 测试场景与测试点",
]

INFO_HEADER = "| 字段 | 内容 |"
EXPECTED_FALLBACK = "待人工分析确认"
DETAIL_PREFIX = "- 测试点详情："
EXPECTED_PREFIX = "- 预期结果："
E2E_POINT_TITLE = "E2E场景测试"
NON_SUCCESS_DETAIL_TERMS = (
    "失败",
    "拒绝",
    "不允许",
    "不能",
    "不可用",
    "不满足",
    "非法",
    "无效",
    "异常",
    "错误",
    "超时",
    "越权",
    "权限限制",
    "鉴权失败",
    "鉴权拒绝",
    "拦截",
    "为零",
    "依赖失败",
    "状态不允许",
    "重复提交失败",
    "重复请求失败",
)

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
    "测试设计项",
    "测试设计项 ID",
    "测试用例标题大纲",
    "测试用例标题项",
    "标题项 ID",
    "测试用例标题",
    "覆盖意图",
    "级别",
    "输入条件与数据依赖",
    "判定关注",
    "待确认信息",
    "TDI-",
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
    "<测试点>",
    "<测试点明细>",
    "<测试点详情>",
    "<测试场景名称>",
    "<明确预期结果或待人工分析确认>",
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


def is_non_success_detail(title: str, block_lines: list[str] | None = None) -> bool:
    return any(term in title for term in NON_SUCCESS_DETAIL_TERMS)


def collect_scenario_points(lines: list[str]) -> tuple[dict[str, list[tuple[int, str, str]]], dict[str, tuple[int, str]]]:
    scenario_points: dict[str, list[tuple[int, str, str]]] = {}
    point_titles: dict[str, tuple[int, str]] = {}
    current_scenario: str | None = None

    for line_number, line in enumerate(lines, start=1):
        scenario_match = re.match(r"^### (SC-\d{3})\s+(.+)", line)
        if scenario_match:
            current_scenario = scenario_match.group(1)
            scenario_points.setdefault(current_scenario, [])
            continue

        point_match = re.match(r"^#### (TP-\d{3})\s+(.+)", line)
        if point_match:
            point_id = point_match.group(1)
            point_title = point_match.group(2).strip()
            point_titles[point_id] = (line_number, point_title)
            if current_scenario is not None:
                scenario_points.setdefault(current_scenario, []).append((line_number, point_id, point_title))

    return scenario_points, point_titles


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
            if (
                next_line.startswith("###### ")
                or next_line.startswith("##### ")
                or next_line.startswith("#### ")
                or next_line.startswith("### ")
            ):
                break
            block_lines.append(next_line)
        blocks.append((index + 1, match.group(1), block_lines))
    return blocks


def collect_failure_type_blocks(lines: list[str]) -> list[tuple[int, str, list[str]]]:
    blocks: list[tuple[int, str, list[str]]] = []
    for index, line in enumerate(lines):
        match = re.match(r"^###### (TP-\d{3}-\d{3}-\d{3})\s+(.+)", line)
        if not match:
            continue
        block_lines: list[str] = []
        for next_line in lines[index + 1 :]:
            if next_line.startswith("#"):
                break
            block_lines.append(next_line)
        blocks.append((index + 1, match.group(1), block_lines))
    return blocks


def check_leaf_block(
    line_number: int,
    block_id: str,
    block_lines: list[str],
    lines: list[str],
    errors: list[str],
    warnings: list[str],
    seen_details: set[tuple[str, str]],
    label: str,
) -> None:
    title_line = lines[line_number - 1]
    title = re.sub(r"^#{5,6} TP-\d{3}-\d{3}(?:-\d{3})?\s+", "", title_line).strip()
    if title in EMPTY_MARKERS:
        errors.append(f"第 {line_number} 行：{label}标题不能为空或模板占位")
    if title in {"验证功能正常", "异常场景覆盖", "正常场景", "异常场景", "功能正确"}:
        errors.append(f"第 {line_number} 行：{label}过于泛化: {title}")
    if any(word in title for word in BANNED_STEP_WORDS):
        errors.append(f"第 {line_number} 行：{label}标题包含步骤化或脚本化表达: {title}")

    detail_text = "\n".join(block_lines)
    detail_line = next((line for line in block_lines if line.startswith(DETAIL_PREFIX)), "")
    expected_line = next((line for line in block_lines if line.startswith(EXPECTED_PREFIX)), "")
    if not detail_line:
        errors.append(f"第 {line_number} 行：{label}缺少 `{DETAIL_PREFIX}`")
    if not expected_line:
        errors.append(f"第 {line_number} 行：{label}缺少 `{EXPECTED_PREFIX}`")

    detail_value = detail_line.removeprefix(DETAIL_PREFIX).strip() if detail_line else ""
    expected_value = expected_line.removeprefix(EXPECTED_PREFIX).strip() if expected_line else ""
    for field_label, value in (("测试点详情", detail_value), ("预期结果", expected_value)):
        if value in EMPTY_MARKERS:
            errors.append(f"第 {line_number} 行：{field_label}不能为空或模板占位")
        if has_generic_reference(value):
            errors.append(f"第 {line_number} 行：{field_label}使用了非自包含占位表达: {value}")
        if any(word in value for word in BANNED_STEP_WORDS):
            errors.append(f"第 {line_number} 行：{field_label}包含步骤化或脚本化表达: {value}")

    key = (title, expected_value)
    if key in seen_details:
        warnings.append(f"第 {line_number} 行：{label}与前文重复: {title}")
    seen_details.add(key)

    if "|" in detail_text and "预期结果" in detail_text:
        errors.append(f"第 {line_number} 行：{label}不得使用表格承载")


def main() -> int:
    if len(sys.argv) != 2:
        print("用法: lint-test-analysis-solution.py <测试分析方案.md>", file=sys.stderr)
        return 2

    solution_path = Path(sys.argv[1])
    text = solution_path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    errors: list[str] = []
    warnings: list[str] = []

    if not lines or not lines[0].startswith("# ") or "测试分析方案" not in lines[0]:
        errors.append("缺少 Markdown 一级标题，或标题未声明“测试分析方案”")

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
                errors.append(f"第 {line_number} 行：出现禁止字段或术语: {term}")
        if line.startswith("|"):
            cells = set(split_row(line))
            for column in BANNED_COLUMNS:
                if column in cells:
                    errors.append(f"第 {line_number} 行：出现完整测试用例字段: {column}")
            if {"测试设计项 ID", "测试设计项", "预期结果"}.issubset(cells):
                errors.append(f"第 {line_number} 行：测试分析方案不得使用测试设计项表格")

    if INFO_HEADER not in text:
        errors.append(f"缺少需求范围/场景信息表头: {INFO_HEADER}")

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

    scenario_points, point_titles = collect_scenario_points(lines)
    for line_number, scenario_id in scenario_ids:
        points = scenario_points.get(scenario_id, [])
        if not any(E2E_POINT_TITLE in point_title for _point_line, _point_id, point_title in points):
            errors.append(f"第 {line_number} 行：测试场景 {scenario_id} 下缺少 `{E2E_POINT_TITLE}` 测试点")

    detail_blocks = collect_detail_blocks(lines)
    failure_type_blocks = collect_failure_type_blocks(lines)
    if not detail_blocks:
        errors.append("未找到 `##### TP-*-* <测试点明细>` 测试点明细标题")

    details_by_point: dict[str, list[tuple[int, str]]] = {}
    detail_ids: set[str] = set()
    detail_titles: dict[str, tuple[int, str, list[str]]] = {}
    failure_types_by_detail: dict[str, list[tuple[int, str]]] = {}
    seen_details: set[tuple[str, str]] = set()
    for line_number, detail_id, block_lines in detail_blocks:
        parent_id = "-".join(detail_id.split("-")[:2])
        details_by_point.setdefault(parent_id, []).append((line_number, detail_id))
        detail_ids.add(detail_id)

        title_line = lines[line_number - 1]
        detail_title = re.sub(r"^##### TP-\d{3}-\d{3}\s+", "", title_line).strip()
        detail_titles[detail_id] = (line_number, detail_title, block_lines)
        if detail_title in EMPTY_MARKERS:
            errors.append(f"第 {line_number} 行：测试点明细标题不能为空或模板占位")
        if detail_title in {"验证功能正常", "异常场景覆盖", "正常场景", "异常场景", "功能正确"}:
            errors.append(f"第 {line_number} 行：测试点明细过于泛化: {detail_title}")
        if any(word in detail_title for word in BANNED_STEP_WORDS):
            errors.append(f"第 {line_number} 行：测试点明细标题包含步骤化或脚本化表达: {detail_title}")

    for line_number, failure_type_id, block_lines in failure_type_blocks:
        parent_detail_id = "-".join(failure_type_id.split("-")[:3])
        if parent_detail_id not in detail_ids:
            errors.append(f"第 {line_number} 行：失败类型明细 {failure_type_id} 缺少父级测试点明细 {parent_detail_id}")
        failure_types_by_detail.setdefault(parent_detail_id, []).append((line_number, failure_type_id))

    leaf_blocks: list[tuple[int, str, list[str], str]] = []
    for line_number, detail_id, block_lines in detail_blocks:
        detail_line_number, detail_title, detail_block_lines = detail_titles[detail_id]
        has_failure_types = detail_id in failure_types_by_detail
        is_non_success = is_non_success_detail(detail_title, detail_block_lines)
        if is_non_success and not has_failure_types:
            errors.append(
                f"第 {detail_line_number} 行：非成功测试点明细 `{detail_title}` 必须新增 `TP-*-*-*` 第四层，"
                "用于拆分失败类型"
            )
        if has_failure_types and not is_non_success:
            errors.append(
                f"第 {detail_line_number} 行：只有非成功测试点明细才应新增 `TP-*-*-*` 第四层，"
                f"当前明细 `{detail_title}` 未体现失败、拒绝、异常或非法分支"
            )
        if not has_failure_types:
            leaf_blocks.append((line_number, detail_id, block_lines, "测试点明细"))

    for line_number, failure_type_id, block_lines in failure_type_blocks:
        leaf_blocks.append((line_number, failure_type_id, block_lines, "失败类型明细"))

    for line_number, block_id, block_lines, label in sorted(leaf_blocks, key=lambda item: item[0]):
        check_leaf_block(
            line_number,
            block_id,
            block_lines,
            lines,
            errors,
            warnings,
            seen_details,
            label,
        )

    for _, point_id in point_ids:
        if point_id not in details_by_point:
            errors.append(f"测试点 {point_id} 下缺少测试点明细")

    for parent_id, details in details_by_point.items():
        for expected_index, (line_number, actual_id) in enumerate(details, start=1):
            expected_id = f"{parent_id}-{expected_index:03d}"
            if actual_id != expected_id:
                errors.append(f"第 {line_number} 行：期望测试点明细 ID {expected_id}，实际 {actual_id}")

    for parent_detail_id, failure_types in failure_types_by_detail.items():
        for expected_index, (line_number, actual_id) in enumerate(failure_types, start=1):
            expected_id = f"{parent_detail_id}-{expected_index:03d}"
            if actual_id != expected_id:
                errors.append(f"第 {line_number} 行：期望失败类型明细 ID {expected_id}，实际 {actual_id}")

    for warning in warnings:
        print(f"警告: {warning}")
    for error in errors:
        print(f"失败: {error}")

    if errors:
        return 1
    print(f"通过: {solution_path} 已通过测试分析方案确定性校验")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
