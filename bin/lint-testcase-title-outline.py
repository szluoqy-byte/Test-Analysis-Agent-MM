#!/usr/bin/env python3
"""Lint a Markdown testcase title outline file."""

from __future__ import annotations

import re
import sys
from pathlib import Path


REQUIRED_SECTIONS = [
    "# ",
    "## 1. 需求与设计方案信息",
    "## 2. 测试场景清单",
    "## 3. 测试场景详情",
    "## 5. 待确认信息",
    "## 6. 完整性自检",
]

INFO_HEADER = "| 字段 | 内容 |"
SCENARIO_HEADER = "| 场景 ID | 场景名称 | 场景测试类型 | 场景目标 |"
CONDITION_HEADER = "| 条件项 | 内容 |"
POINT_FIELD_HEADER = "| 字段 | 内容 |"
TITLE_ITEM_HEADER = "| 标题项 ID | 测试用例标题 | 覆盖意图 | 级别 | 输入条件与数据依赖 | 判定关注 | 待确认信息 |"
QUESTION_HEADER = "| 问题 ID | 问题 | 影响场景/测试点/标题项 | 当前处理 |"
SELF_CHECK_HEADER = "| 检查项 | 是否满足 | 说明 |"

REQUIRED_INFO_FIELDS = {
    "需求名称",
    "需求来源",
    "需求摘要",
    "本次覆盖范围",
    "本次不覆盖内容",
}
REQUIRED_CONDITIONS = {
    "场景入口/触发方式",
    "执行用户/角色",
    "前置条件",
    "测试数据因子",
    "业务设计约束",
}
ALLOWED_LEVELS = {"Level 0", "Level 1", "Level 2", "Level 3", "Level 4"}
BANNED_COLUMNS = {"前置步骤", "测试步骤", "操作步骤", "测试数据", "预期结果", "自动化脚本"}
BANNED_STEP_WORDS = ("点击", "然后", "步骤", "执行用例", "输入以下", "预期结果", "断言")
GENERIC_REFERENCE_WORDS = (
    "见原始需求",
    "见设计方案",
    "详见原始需求",
    "详见设计方案",
    "参考需求",
    "参考设计",
    "按需求",
    "同上",
    "TBD",
    "待补充",
)
EMPTY_MARKERS = {"", "<需要确认的问题>", "<影响范围>", "<测试场景名称>"}


def split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def collect_table(lines: list[str], header: str) -> list[tuple[int, list[str]]]:
    try:
        start = lines.index(header)
    except ValueError:
        return []
    rows: list[tuple[int, list[str]]] = []
    for index in range(start + 2, len(lines)):
        line = lines[index]
        if not line.startswith("|"):
            break
        rows.append((index + 1, split_row(line)))
    return rows


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
    return any(word in value for word in GENERIC_REFERENCE_WORDS)


def main() -> int:
    if len(sys.argv) != 2:
        print("用法: lint-testcase-title-outline.py <测试用例标题大纲.md>", file=sys.stderr)
        return 2

    outline_path = Path(sys.argv[1])
    text = outline_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    errors: list[str] = []
    warnings: list[str] = []

    for section in REQUIRED_SECTIONS:
        if section == "# ":
            if not lines or not lines[0].startswith("# ") or "测试用例标题大纲" not in lines[0]:
                errors.append("缺少 Markdown 一级标题，或标题未声明“测试用例标题大纲”")
        elif section not in text:
            errors.append(f"缺少必需章节: {section}")

    for header in [INFO_HEADER, SCENARIO_HEADER, CONDITION_HEADER, TITLE_ITEM_HEADER, SELF_CHECK_HEADER]:
        if header not in text:
            errors.append(f"缺少必需表头: {header}")

    for line_number, line in enumerate(lines, start=1):
        if not line.startswith("|"):
            continue
        cells = set(split_row(line))
        for column in BANNED_COLUMNS:
            if column in cells:
                errors.append(f"第 {line_number} 行：出现完整测试用例字段: {column}")

    info_rows = collect_table(lines, INFO_HEADER)
    info_fields = {cells[0]: cells[1] for _, cells in info_rows if len(cells) == 2}
    for field in REQUIRED_INFO_FIELDS:
        value = info_fields.get(field, "")
        if not value:
            errors.append(f"需求与设计方案信息缺少内容: {field}")
        elif has_generic_reference(value):
            errors.append(f"需求与设计方案信息 `{field}` 使用了非自包含占位表达: {value}")

    scenario_rows = [
        (line_number, cells)
        for line_number, cells in collect_table(lines, SCENARIO_HEADER)
        if cells and re.fullmatch(r"SC-\d{3}", cells[0])
    ]
    if not scenario_rows:
        errors.append("测试场景清单未找到 SC-* 场景行")

    expected_scene_id = 1
    scenario_ids: list[str] = []
    for line_number, cells in scenario_rows:
        if len(cells) != 4:
            errors.append(f"第 {line_number} 行：场景清单期望 4 列，实际 {len(cells)} 列")
            continue
        scene_id, name, scene_type, goal = cells
        expected = f"SC-{expected_scene_id:03d}"
        if scene_id != expected:
            errors.append(f"第 {line_number} 行：期望场景 ID {expected}，实际 {scene_id}")
        expected_scene_id += 1
        scenario_ids.append(scene_id)
        for label, value in [("场景名称", name), ("场景测试类型", scene_type), ("场景目标", goal)]:
            if not value:
                errors.append(f"第 {line_number} 行：{label} 不能为空")
            elif has_generic_reference(value):
                errors.append(f"第 {line_number} 行：{label} 使用了非自包含占位表达: {value}")

    headings = {line.strip() for line in lines if line.startswith("### ")}
    for scene_id in scenario_ids:
        if not any(heading.startswith(f"### {scene_id} ") for heading in headings):
            errors.append(f"缺少场景详情标题: ### {scene_id} <场景名称>")

    condition_tables = collect_all_tables(lines, CONDITION_HEADER)
    if len(condition_tables) < len(scenario_ids):
        errors.append(f"场景测试条件表数量不足，场景 {len(scenario_ids)} 个，条件表 {len(condition_tables)} 个")
    for table_index, rows in enumerate(condition_tables[: len(scenario_ids)], start=1):
        condition_values = {cells[0]: cells[1] for _, cells in rows if len(cells) == 2}
        missing = sorted(REQUIRED_CONDITIONS - set(condition_values))
        if missing:
            errors.append(f"第 {table_index} 个场景缺少必填条件: {'、'.join(missing)}")
        for condition in REQUIRED_CONDITIONS:
            value = condition_values.get(condition, "")
            if not value:
                errors.append(f"第 {table_index} 个场景的条件 `{condition}` 内容为空")
            elif has_generic_reference(value):
                errors.append(f"第 {table_index} 个场景的条件 `{condition}` 使用了非自包含占位表达: {value}")

    point_headings = [line for line in lines if re.match(r"^##### (TP|ITP)-\d{3} ", line)]
    if not point_headings:
        errors.append("未找到 TP-* 或 ITP-* 测试点标题")

    title_tables = collect_all_tables(lines, TITLE_ITEM_HEADER)
    title_rows = [
        (line_number, cells)
        for rows in title_tables
        for line_number, cells in rows
        if cells and cells[0].startswith("TCT-")
    ]
    if not title_rows:
        errors.append("未找到 TCT-* 测试用例标题项")

    expected_tct_id = 1
    for line_number, cells in title_rows:
        if len(cells) != 7:
            errors.append(f"第 {line_number} 行：标题项期望 7 列，实际 {len(cells)} 列")
            continue
        title_id, title, intent, level, data_deps, oracle, question = cells
        expected = f"TCT-{expected_tct_id:03d}"
        if title_id != expected:
            errors.append(f"第 {line_number} 行：期望标题项 ID {expected}，实际 {title_id}")
        expected_tct_id += 1
        if not title.startswith("验证"):
            warnings.append(f"第 {line_number} 行：测试用例标题建议以“验证”开头: {title}")
        if level not in ALLOWED_LEVELS:
            errors.append(f"第 {line_number} 行：非法级别 {level}")
        for label, value in [
            ("测试用例标题", title),
            ("覆盖意图", intent),
            ("输入条件与数据依赖", data_deps),
            ("判定关注", oracle),
            ("待确认信息", question),
        ]:
            if value in EMPTY_MARKERS:
                errors.append(f"第 {line_number} 行：{label} 不能为空")
            elif has_generic_reference(value):
                errors.append(f"第 {line_number} 行：{label} 使用了非自包含占位表达: {value}")
        if any(word in title for word in BANNED_STEP_WORDS):
            errors.append(f"第 {line_number} 行：测试用例标题包含步骤化表达: {title}")
        if any(word in data_deps for word in ("步骤", "点击", "进入页面后")):
            errors.append(f"第 {line_number} 行：输入条件与数据依赖包含步骤化表达: {data_deps}")
        if any(word in oracle for word in ("预期结果如下", "步骤 1", "步骤1")):
            errors.append(f"第 {line_number} 行：判定关注疑似展开完整预期结果: {oracle}")
        if title in {"验证功能正常", "验证异常处理", "验证校验通过"}:
            errors.append(f"第 {line_number} 行：测试用例标题过于泛化: {title}")

    if QUESTION_HEADER in text:
        for line_number, cells in collect_table(lines, QUESTION_HEADER):
            if len(cells) != 4:
                errors.append(f"第 {line_number} 行：待确认信息期望 4 列，实际 {len(cells)} 列")
                continue
            question_id, question, impact, handling = cells
            if question_id.startswith("Q-"):
                if question in EMPTY_MARKERS or impact in EMPTY_MARKERS or not handling:
                    errors.append(f"第 {line_number} 行：待确认信息存在空问题行")
    elif "本次无待确认信息。" not in text:
        warnings.append("未找到待确认信息表，也未声明“本次无待确认信息。”")

    self_check_rows = collect_table(lines, SELF_CHECK_HEADER)
    if not self_check_rows:
        errors.append("完整性自检未找到检查项")
    for line_number, cells in self_check_rows:
        if len(cells) != 3:
            errors.append(f"第 {line_number} 行：自检表期望 3 列，实际 {len(cells)} 列")
            continue
        item, satisfied, note = cells
        if not item or not satisfied or not note:
            errors.append(f"第 {line_number} 行：自检表存在空字段")
        if satisfied not in {"是", "否", "不适用", "部分满足"}:
            warnings.append(f"第 {line_number} 行：自检结果建议使用 是/否/不适用/部分满足")

    for warning in warnings:
        print(f"警告: {warning}")
    for error in errors:
        print(f"失败: {error}")

    if errors:
        return 1
    print(f"通过: {outline_path} 已通过测试用例标题大纲确定性校验")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
