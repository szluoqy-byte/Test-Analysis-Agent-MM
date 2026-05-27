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
    "## 4. 待确认治理摘要",
    "## 5. 测试方法路由",
    "## 6. 方法分析证据摘要",
    "## 7. 待确认问题",
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
    "## 6. 待确认治理摘要",
    "## 7. 测试分析维度与方法路由",
    "## 8. 方法分析证据摘要",
    "## 9. 待确认问题",
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
    "## 4. 测试方法路由",
    "## 5. 方法分析证据摘要",
    "## 6. 待确认问题",
    "## 7. 测试点明细",
    "## 8. 覆盖审查结果",
    "## 9. 质量门禁结果",
    "## 10. 专家评审评分",
    "## 11. 建议沉淀的记忆更新",
]

DETAIL_REQUIRED_SECTIONS = [
    "# ",
    "## 测试点明细",
]

TESTPOINT_HEADER = "| ID | 模块 | 测试点 | 类型 | 方法 | 需求依据 | 级别 | 风险/备注 |"
EVIDENCE_HEADER = "| 证据ID | 方法 | 需求片段 | 分析结论 | 关联测试点/待确认 |"

BANNED_COLUMNS = {"前置条件", "操作步骤", "测试数据", "预期结果"}
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
    "## 5. 测试方法路由": "## 5. 测试分析维度与方法路由",
    "## 4. 测试方法路由": "## 4. 测试分析维度与方法路由",
    "## 4. 待确认治理摘要": "## 4. 交互澄清摘要",
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
    return bool(re.fullmatch(r"(?:TP|ITP)-\d{3}", value))


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
    try:
        header_index = lines.index(EVIDENCE_HEADER)
    except ValueError:
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


def has_required_section(text: str, section: str) -> bool:
    return section in text or ROUTE_SECTION_ALIASES.get(section, "") in text


def main() -> int:
    if len(sys.argv) != 2:
        print("用法: lint-testpoint-report.py <报告.md>", file=sys.stderr)
        return 2

    report_path = Path(sys.argv[1])
    repo_root = Path(__file__).resolve().parents[1]
    allowed_types = parse_bullet_section(repo_root / "knowledge" / "testpoint-standard.md", "## 标准类型")
    text = report_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    errors: list[str] = []
    warnings: list[str] = []

    is_full_report = "## 1. 分析范围" in text
    required_sections = DETAIL_REQUIRED_SECTIONS
    if is_full_report:
        if "## 4. Project/Personal 上下文使用情况" in text:
            required_sections = MODERN_REQUIRED_SECTIONS
        elif "## 4. 交互澄清摘要" in text or "## 4. 待确认治理摘要" in text:
            required_sections = REQUIRED_SECTIONS
        else:
            required_sections = LEGACY_REQUIRED_SECTIONS

    for section in required_sections:
        if section == "# ":
            if not lines or not lines[0].startswith("# "):
                errors.append("缺少 Markdown 一级标题")
        elif not has_required_section(text, section):
            errors.append(f"缺少必需章节: {section}")

    if TESTPOINT_HEADER not in text:
        errors.append("缺少带 `方法` 列的测试点表头")
    if is_full_report and EVIDENCE_HEADER not in text:
        errors.append("缺少方法分析证据表头")

    for line_number, line in enumerate(lines, start=1):
        if not line.startswith("|"):
            continue
        cells = set(split_row(line))
        for column in BANNED_COLUMNS:
            if column in cells:
                errors.append(f"第 {line_number} 行：出现禁止的用例化列名: {column}")

    rows = collect_testpoint_rows(lines)
    if not rows:
        errors.append("测试点表中未找到 TP-* 或 ITP-* 行")

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
            ("关联测试点/待确认", links),
        ]:
            if not value:
                errors.append(f"第 {line_number} 行：方法证据必填字段为空: {name}")
        if not ("TP-" in links or "ITP-" in links or "Q-" in links):
            warnings.append(f"第 {line_number} 行：方法证据建议关联 TP-*、ITP-* 或 Q-*: {links}")

    expected_tp_id = 1
    expected_itp_id = 1
    for line_number, cells in rows:
        if len(cells) != 8:
            errors.append(f"第 {line_number} 行：期望 8 列，实际 {len(cells)} 列")
            continue

        test_id, module, testpoint, test_type, method, basis, level, risk_note = cells

        if test_id.startswith("ITP-"):
            expected = f"ITP-{expected_itp_id:03d}"
            expected_itp_id += 1
        else:
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
    target_name = "完整报告" if is_full_report else "测试点明细文件"
    print(f"通过: {report_path} 已通过{target_name}确定性校验")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
