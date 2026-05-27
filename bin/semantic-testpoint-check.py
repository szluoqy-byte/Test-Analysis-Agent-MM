#!/usr/bin/env python3
"""Heuristic semantic checks for a Markdown test point report."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


TESTPOINT_HEADER = "| ID | 模块 | 测试点 | 类型 | 方法 | 需求依据 | 级别 | 风险/备注 |"
ROUTE_HEADER = "| 需求片段 | 触发信号 | 适用方法 | 调用 skill | 必要性 | 置信度 | 说明 |"
ROUTE_HEADER_WITH_DIMENSION = "| 需求片段 | 分析维度 | 触发信号 | 适用方法 | 调用 skill | 必要性 | 置信度 | 说明 |"
QUESTION_HEADER = "| ID | 问题 | 影响 | 关联需求依据 |"
EVIDENCE_HEADER = "| 证据ID | 方法 | 需求片段 | 分析结论 | 关联测试点/待确认 |"
GATE_HEADER = "| 门禁 | 结果 | 失败/警告项 | 修正建议 |"
SCORE_HEADER = "| 维度 | 得分 | 说明 |"

GENERIC_BASIS = {"需求文档", "需求说明", "PRD", "原始需求"}
GENERIC_RISK_NOTES = {"无", "需要关注", "风险较高", "高风险", "重点关注"}
HIGH_LEVELS = {"Level 0", "Level 1"}

TYPE_METHOD_HINTS = {
    "边界值": {"边界值", "等价类"},
    "状态迁移": {"状态迁移"},
    "权限角色": {"权限矩阵"},
    "接口契约": {"接口契约"},
    "数据一致性": {"数据一致性", "状态迁移", "接口契约"},
    "兼容性": {"组合兼容"},
}


def split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_testpoint_id(value: str) -> bool:
    return bool(re.fullmatch(r"(?:TP|ITP)-\d{3}", value))


def collect_table(lines: list[str], header: str) -> list[tuple[int, list[str]]]:
    rows: list[tuple[int, list[str]]] = []
    try:
        start = lines.index(header)
    except ValueError:
        return rows

    for index in range(start + 2, len(lines)):
        line = lines[index]
        if not line.startswith("|"):
            break
        rows.append((index + 1, split_row(line)))
    return rows


def parse_bullet_section(path: Path, heading: str) -> set[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    values: set[str] = set()
    in_section = False
    for line in lines:
        if line.strip() == heading:
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section and line.startswith("- "):
            values.add(line[2:].strip(" 。"))
    return values


def split_methods(value: str, allowed_methods: set[str]) -> set[str]:
    methods: set[str] = set()
    for method in allowed_methods:
        if method in value:
            methods.add(method)
    if methods:
        return methods
    for part in re.split(r"[、,，/ ]+", value):
        part = part.strip()
        if part:
            methods.add(part)
    return methods


def risk_driven_covered(testpoint_rows: list[tuple[int, list[str]]]) -> bool:
    for _, cells in testpoint_rows:
        if len(cells) != 8:
            continue
        _, _, _, _, _, _, level, risk_note = cells
        if level in HIGH_LEVELS and risk_note and risk_note not in GENERIC_RISK_NOTES:
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="检查测试点报告的语义质量启发式规则")
    parser.add_argument("report", type=Path)
    parser.add_argument("--strict", action="store_true", help="将警告也视为失败")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    standard_path = repo_root / "knowledge" / "testpoint-standard.md"
    allowed_types = parse_bullet_section(standard_path, "## 标准类型")
    allowed_methods = parse_bullet_section(standard_path, "## 标准方法")

    text = args.report.read_text(encoding="utf-8")
    lines = text.splitlines()
    errors: list[str] = []
    warnings: list[str] = []

    testpoint_rows = collect_table(lines, TESTPOINT_HEADER)
    route_rows = collect_table(lines, ROUTE_HEADER)
    route_has_dimension = False
    if not route_rows:
        route_rows = collect_table(lines, ROUTE_HEADER_WITH_DIMENSION)
        route_has_dimension = bool(route_rows)
    question_rows = collect_table(lines, QUESTION_HEADER)
    evidence_rows = collect_table(lines, EVIDENCE_HEADER)
    gate_rows = collect_table(lines, GATE_HEADER)
    score_rows = collect_table(lines, SCORE_HEADER)

    if not testpoint_rows:
        errors.append("未找到测试点明细表")
    has_route_section = "测试方法路由" in text or "测试分析维度与方法路由" in text
    has_evidence_section = "方法分析证据摘要" in text
    has_gate_section = "质量门禁结果" in text
    has_score_section = "专家评审评分" in text

    if has_route_section and not route_rows:
        errors.append("存在测试方法路由章节，但未找到路由表")
    if not has_evidence_section:
        errors.append("缺少方法分析证据摘要章节")
    if has_evidence_section and not evidence_rows:
        errors.append("存在方法分析证据摘要章节，但未找到方法证据表")
    if has_gate_section and not gate_rows:
        errors.append("存在质量门禁结果章节，但未找到质量门禁表")
    if has_score_section and not score_rows:
        errors.append("存在专家评审评分章节，但未找到专家评分表")

    covered_methods: set[str] = set()
    evidenced_methods: set[str] = set()
    seen_testpoints: dict[str, int] = {}
    level_count: dict[str, int] = {}

    expected_evidence_id = 1
    for line_number, cells in evidence_rows:
        if len(cells) != 5 or not cells[0].startswith("ME-"):
            continue
        evidence_id, method, fragment, conclusion, links = cells
        expected = f"ME-{expected_evidence_id:03d}"
        if evidence_id != expected:
            errors.append(f"第 {line_number} 行：期望证据 ID {expected}，实际 {evidence_id}")
        expected_evidence_id += 1
        evidenced_methods.add(method)
        if method not in allowed_methods:
            warnings.append(f"第 {line_number} 行：方法证据中的方法 `{method}` 未出现在知识标准方法中")
        if not fragment or not conclusion or not links:
            errors.append(f"第 {line_number} 行：方法证据存在空字段")
        if "TP-" not in links and "ITP-" not in links and "Q-" not in links:
            warnings.append(f"第 {line_number} 行：方法证据未关联 TP-*、ITP-* 或 Q-*")

    for line_number, cells in testpoint_rows:
        if len(cells) != 8 or not is_testpoint_id(cells[0]):
            continue
        test_id, module, testpoint, test_type, method, basis, level, risk_note = cells
        covered_methods.add(method)
        level_count[level] = level_count.get(level, 0) + 1

        if test_type not in allowed_types:
            errors.append(f"第 {line_number} 行：类型 `{test_type}` 不在知识标准中")
        if method not in allowed_methods:
            warnings.append(f"第 {line_number} 行：方法 `{method}` 未出现在知识标准方法中")
        if basis in GENERIC_BASIS:
            warnings.append(f"第 {line_number} 行：需求依据过宽泛，建议指向标题、规则或段落摘要")
        if risk_note in GENERIC_RISK_NOTES:
            warnings.append(f"第 {line_number} 行：风险/备注过于泛化，建议说明风险原因")

        previous_line = seen_testpoints.get(testpoint)
        if previous_line:
            warnings.append(f"第 {line_number} 行：测试点与第 {previous_line} 行重复")
        seen_testpoints[testpoint] = line_number

        expected_methods = TYPE_METHOD_HINTS.get(test_type)
        if expected_methods and method not in expected_methods:
            warnings.append(
                f"第 {line_number} 行：类型 `{test_type}` 与方法 `{method}` 可能不匹配"
            )

        if level in HIGH_LEVELS and not risk_note:
            warnings.append(f"第 {line_number} 行：高等级测试点缺少风险备注")

    required_methods: set[str] = set()
    for line_number, cells in route_rows:
        expected_columns = 8 if route_has_dimension else 7
        if len(cells) != expected_columns:
            warnings.append(f"第 {line_number} 行：方法路由表列数异常")
            continue
        if route_has_dimension:
            _, dimension, _, methods, _, necessity, confidence, _ = cells
            if not dimension:
                warnings.append(f"第 {line_number} 行：方法路由表缺少分析维度")
        else:
            _, _, methods, _, necessity, confidence, _ = cells
        if confidence not in {"高", "中", "低"}:
            warnings.append(f"第 {line_number} 行：方法路由置信度建议使用 高/中/低")
        if "必选" not in necessity:
            continue
        required_methods.update(split_methods(methods, allowed_methods))

    missing_methods = sorted(method for method in required_methods if method not in covered_methods)
    if "风险驱动" in missing_methods and risk_driven_covered(testpoint_rows):
        missing_methods.remove("风险驱动")
    if missing_methods:
        has_questions = any(cells and cells[0].startswith("Q-") for _, cells in question_rows)
        message = "必选方法未在测试点方法列中体现: " + "、".join(missing_methods)
        if has_questions:
            warnings.append(message + "；报告存在待确认问题，请确认是否已解释缺口")
        else:
            errors.append(message)

    missing_evidence_methods = sorted(method for method in required_methods if method not in evidenced_methods)
    if missing_evidence_methods:
        has_questions = any(cells and cells[0].startswith("Q-") for _, cells in question_rows)
        message = "必选方法未在方法证据中体现: " + "、".join(missing_evidence_methods)
        if has_questions:
            warnings.append(message + "；报告存在待确认问题，请确认是否已解释证据缺口")
        else:
            errors.append(message)

    if testpoint_rows and len(level_count) == 1 and len(testpoint_rows) >= 5:
        warnings.append("测试点级别全部相同，建议确认风险分层是否充分")

    for line_number, cells in gate_rows:
        if len(cells) != 4:
            warnings.append(f"第 {line_number} 行：质量门禁表列数异常")
            continue
        gate, result, issue, _ = cells
        if result == "失败":
            errors.append(f"第 {line_number} 行：质量门禁 `{gate}` 存在失败项: {issue}")
        elif result == "警告":
            warnings.append(f"第 {line_number} 行：质量门禁 `{gate}` 存在警告项: {issue}")

    score_total = 0
    score_count = 0
    for line_number, cells in score_rows:
        if len(cells) != 3:
            warnings.append(f"第 {line_number} 行：专家评分表列数异常")
            continue
        dimension, score_text, _ = cells
        try:
            score = int(score_text)
        except ValueError:
            errors.append(f"第 {line_number} 行：专家评分 `{dimension}` 不是整数: {score_text}")
            continue
        score_total += score
        score_count += 1
        if score == 0:
            errors.append(f"第 {line_number} 行：专家评分 `{dimension}` 为 0")
    if score_count and score_total < 10:
        errors.append(f"专家评分总分 {score_total}/12 低于通过线 10/12")

    for warning in warnings:
        print(f"警告: {warning}")
    for error in errors:
        print(f"失败: {error}")

    if errors or (args.strict and warnings):
        return 1
    print(f"通过: {args.report} 已通过语义启发式检查")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
