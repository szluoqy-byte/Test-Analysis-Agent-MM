#!/usr/bin/env python3
"""Lint a Markdown test point report or standalone test point detail file."""

from __future__ import annotations

import re
import sys
from pathlib import Path


REQUIRED_SECTIONS = [
    "# ",
    "## 1. 分析范围",
    "## 2. 记忆上下文包摘要",
    "## 3. 需求结构化摘要",
    "## 4. 输入不足摘要",
    "## 5. 测试技术路由",
    "## 6. 方法分析证据摘要",
    "## 7. 输入不足说明",
    "## 8. 测试点明细",
    "## 9. 覆盖审查结果",
    "## 10. 质量门禁结果",
    "## 11. 专家评审评分",
    "## 12. 建议沉淀的记忆更新",
]

MODERN_REQUIRED_SECTIONS = [
    "# ",
    "## 1. 分析范围",
    "## 2. 任务清单摘要",
    "## 3. 记忆上下文包摘要",
    "## 4. Project/Personal 上下文使用情况",
    "## 5. 需求结构化摘要",
    "## 6. 输入不足摘要",
    "## 7. 测试分析维度与测试技术路由",
    "## 8. 方法分析证据摘要",
    "## 9. 输入不足说明",
    "## 10. 测试点明细",
    "## 11. 覆盖审查结果",
    "## 12. 质量门禁结果",
    "## 13. 专家评审评分",
    "## 14. 建议沉淀的记忆更新",
]

LEGACY_REQUIRED_SECTIONS = [
    "# ",
    "## 1. 分析范围",
    "## 2. 记忆上下文包摘要",
    "## 3. 需求结构化摘要",
    "## 4. 测试技术路由",
    "## 5. 方法分析证据摘要",
    "## 6. 输入不足说明",
    "## 7. 测试点明细",
    "## 8. 覆盖审查结果",
    "## 9. 质量门禁结果",
    "## 10. 专家评审评分",
    "## 11. 建议沉淀的记忆更新",
]

LIGHTWEIGHT_REQUIRED_SECTIONS = [
    "# ",
    "## 1. 分析范围",
    "## 2. 方法证据摘要",
    "## 3. 测试点明细摘要",
    "## 4. 覆盖审查结果",
]

DETAIL_REQUIRED_SECTIONS = [
    "# ",
    "## 测试点明细",
]

TESTPOINT_HEADER = "| ID | 模块 | 测试点 | 类型 | 方法 | 需求依据 | 级别 | 风险/备注 |"
DETAIL_SUMMARY_HEADER = "| 测试点明细 ID | 关联测试点 | 测试点明细 | 预期结果 |"
EVIDENCE_HEADERS = {
    "| 证据ID | 方法 | 需求片段 | 分析结论 | 关联测试点/说明 |",
    "| 证据ID | 方法 | 需求片段 | 分析结论 | 关联测试点/缺口 |",
}

BANNED_COLUMNS = {"前置条件", "操作步骤", "测试数据"}
HARD_STEP_WORDS = ("点击", "然后", "步骤", "断言", "执行用例")
SOFT_STEP_WORDS = ("输入", "选择", "调用接口")
VAGUE_TESTPOINTS = {
    "验证功能正常",
    "验证流程正常",
    "验证规则正确",
    "验证页面正常",
    "验证接口正常",
}

ROUTE_SECTION_ALIASES = {
    "## 5. 测试技术路由": [
        "## 5. 测试分析维度与测试技术路由",
        "## 5. 测试方法路由",
        "## 5. 测试分析维度与方法路由",
    ],
    "## 4. 测试技术路由": [
        "## 4. 测试分析维度与测试技术路由",
        "## 4. 测试方法路由",
        "## 4. 测试分析维度与方法路由",
    ],
    "## 7. 测试分析维度与测试技术路由": ["## 7. 测试分析维度与方法路由"],
    "## 4. 输入不足摘要": [],
}


def split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def parse_bullet_section(path: Path, heading: str) -> set[str]:
    values: set[str] = set()
    in_section = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() == heading:
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section and line.startswith("- "):
            values.add(line[2:].strip(" 。"))
    return values


def is_testpoint_id(value: str) -> bool:
    return bool(re.fullmatch(r"TP-\d{3}", value))


def collect_testpoint_rows(lines: list[str]) -> list[tuple[int, list[str]]]:
    rows: list[tuple[int, list[str]]] = []
    try:
        header_index = lines.index(TESTPOINT_HEADER)
    except ValueError:
        return rows

    for index in range(header_index + 2, len(lines)):
        line = lines[index]
        if not line.startswith("|"):
            break
        cells = split_row(line)
        if len(cells) != 8:
            rows.append((index + 1, cells))
            continue
        if is_testpoint_id(cells[0]):
            rows.append((index + 1, cells))
    return rows


def collect_evidence_rows(lines: list[str]) -> list[tuple[int, list[str]]]:
    rows: list[tuple[int, list[str]]] = []
    header_index = next((index for index, line in enumerate(lines) if line in EVIDENCE_HEADERS), None)
    if header_index is None:
        return rows

    for index in range(header_index + 2, len(lines)):
        line = lines[index]
        if not line.startswith("|"):
            break
        cells = split_row(line)
        if len(cells) != 5:
            rows.append((index + 1, cells))
            continue
        if cells[0].startswith("ME-"):
            rows.append((index + 1, cells))
    return rows


def collect_detail_summary_rows(lines: list[str]) -> list[tuple[int, list[str]]]:
    rows: list[tuple[int, list[str]]] = []
    try:
        header_index = lines.index(DETAIL_SUMMARY_HEADER)
    except ValueError:
        return rows

    for index in range(header_index + 2, len(lines)):
        line = lines[index]
        if not line.startswith("|"):
            break
        cells = split_row(line)
        if len(cells) != 4:
            rows.append((index + 1, cells))
            continue
        if re.fullmatch(r"TP-\d{3}-\d{3}(?:-\d{3})?", cells[0]):
            rows.append((index + 1, cells))
    return rows


def has_required_section(text: str, section: str) -> bool:
    return section in text or any(alias in text for alias in ROUTE_SECTION_ALIASES.get(section, []))


def main() -> int:
    if len(sys.argv) != 2:
        print("用法: skills/coverage-review/scripts/lint-testpoint-report.py <报告.md>", file=sys.stderr)
        return 2

    report_path = Path(sys.argv[1])
    repo_root = Path(__file__).resolve().parents[3]
    allowed_types = parse_bullet_section(repo_root / "knowledge" / "testpoint-standard.md", "## 标准类型")
    text = report_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    errors: list[str] = []
    warnings: list[str] = []

    is_full_report = "## 1. 分析范围" in text
    required_sections = DETAIL_REQUIRED_SECTIONS
    if is_full_report:
        if "## 2. 方法证据摘要" in text and "## 3. 测试点明细摘要" in text:
            required_sections = LIGHTWEIGHT_REQUIRED_SECTIONS
        elif "## 4. Project/Personal 上下文使用情况" in text:
            required_sections = MODERN_REQUIRED_SECTIONS
        elif "## 4. 输入不足摘要" in text:
            required_sections = REQUIRED_SECTIONS
        else:
            required_sections = LEGACY_REQUIRED_SECTIONS

    for section in required_sections:
        if section == "# ":
            if not lines or not lines[0].startswith("# "):
                errors.append("缺少 Markdown 一级标题")
        elif not has_required_section(text, section):
            errors.append(f"缺少必需章节: {section}")

    is_lightweight_report = required_sections == LIGHTWEIGHT_REQUIRED_SECTIONS
    if not is_lightweight_report and TESTPOINT_HEADER not in text:
        errors.append("缺少带 `方法` 列的测试点表头")
    if is_lightweight_report and DETAIL_SUMMARY_HEADER not in text:
        errors.append("缺少测试点明细摘要表头")
    if is_full_report and not any(header in text for header in EVIDENCE_HEADERS):
        errors.append("缺少方法分析证据表头")

    for line_number, line in enumerate(lines, start=1):
        if not line.startswith("|"):
            continue
        cells = set(split_row(line))
        for column in BANNED_COLUMNS:
            if column in cells:
                errors.append(f"第 {line_number} 行：出现禁止的用例化列名: {column}")

    rows = collect_detail_summary_rows(lines) if is_lightweight_report else collect_testpoint_rows(lines)
    if not rows:
        errors.append("测试点表中未找到 TP-* 行")

    evidence_rows = collect_evidence_rows(lines) if is_full_report else []
    if is_full_report and not evidence_rows:
        errors.append("方法分析证据表中未找到 ME-* 行")

    expected_evidence_id = 1
    for line_number, cells in evidence_rows:
        if len(cells) != 5:
            errors.append(f"第 {line_number} 行：期望 5 列方法证据，实际 {len(cells)} 列")
            continue
        evidence_id, method, fragment, conclusion, links = cells
        expected = f"ME-{expected_evidence_id:03d}"
        if evidence_id != expected:
            errors.append(f"第 {line_number} 行：期望证据 ID {expected}，实际 {evidence_id}")
        expected_evidence_id += 1
        for name, value in [
            ("方法", method),
            ("需求片段", fragment),
            ("分析结论", conclusion),
            ("关联测试点", links),
        ]:
            if not value:
                errors.append(f"第 {line_number} 行：方法证据必填字段为空: {name}")
        if "TP-" not in links:
            warnings.append(f"第 {line_number} 行：方法证据建议关联 TP-*: {links}")

    expected_tp_id = 1
    for line_number, cells in rows:
        if is_lightweight_report:
            if len(cells) != 4:
                errors.append(f"第 {line_number} 行：期望 4 列测试点明细摘要，实际 {len(cells)} 列")
                continue
            detail_id, parent_id, detail, expected_result = cells
            if not re.fullmatch(r"TP-\d{3}-\d{3}(?:-\d{3})?", detail_id):
                errors.append(f"第 {line_number} 行：测试点明细 ID 格式错误: {detail_id}")
            if not is_testpoint_id(parent_id):
                errors.append(f"第 {line_number} 行：关联测试点 ID 格式错误: {parent_id}")
            if not detail or not expected_result:
                errors.append(f"第 {line_number} 行：测试点明细摘要存在空字段")
            continue

        if len(cells) != 8:
            errors.append(f"第 {line_number} 行：期望 8 列，实际 {len(cells)} 列")
            continue

        test_id, module, testpoint, test_type, method, basis, level, risk_note = cells

        expected = f"TP-{expected_tp_id:03d}"
        expected_tp_id += 1
        if test_id != expected:
            errors.append(f"第 {line_number} 行：期望 ID {expected}，实际 {test_id}")

        if test_type not in allowed_types:
            errors.append(f"第 {line_number} 行：非法类型 {test_type}")
        if level not in {"Level 0", "Level 1", "Level 2", "Level 3", "Level 4"}:
            errors.append(f"第 {line_number} 行：非法级别 {level}")

        for name, value in [
            ("模块", module),
            ("测试点", testpoint),
            ("方法", method),
            ("需求依据", basis),
            ("风险/备注", risk_note),
        ]:
            if not value:
                errors.append(f"第 {line_number} 行：必填字段为空: {name}")

        if any(word in testpoint for word in HARD_STEP_WORDS):
            errors.append(f"第 {line_number} 行：测试点存在用例化表达: {testpoint}")
        if any(word in testpoint for word in SOFT_STEP_WORDS):
            warnings.append(f"第 {line_number} 行：请检查疑似步骤化表达: {testpoint}")
        if testpoint in VAGUE_TESTPOINTS or len(testpoint) < 12:
            warnings.append(f"第 {line_number} 行：测试点描述可能过于空泛，需体现被测对象、场景和验证特性: {testpoint}")

    for warning in warnings:
        print(f"警告: {warning}")
    for error in errors:
        print(f"失败: {error}")

    if errors:
        return 1
    target_name = "轻量过程报告" if is_lightweight_report else "完整报告" if is_full_report else "测试点明细文件"
    print(f"通过: {report_path} 已通过{target_name}确定性校验")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
