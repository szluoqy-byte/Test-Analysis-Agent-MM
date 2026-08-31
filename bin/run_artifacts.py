#!/usr/bin/env python3
"""Result-deliverable JSON helpers and Markdown rendering."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


TEST_CASE_LEVEL_VALUES = {"Level 0", "Level 1", "Level 2", "Level 3", "Level 4"}
ASSERTION_ACTION_PREFIXES = ("检查", "验证", "确认", "断言", "比对", "核对", "观察", "校验", "判断")
SYSTEM_ACTION_ACTOR_RE = re.compile(
    r"^(?!系统管理员)(?:MM系统|系统|平台|服务端|后端|后台|定时任务|批处理|数据库|消息队列|网关|核心系统|风控系统|第三方系统|下游系统)\s*"
    r"(?:判断|根据|校验|验证|检查|处理|执行|生成|创建|更新|写入|发送|返回|通知|计算|匹配|查询|读取|调用|取消|拒绝|受理|释放|记录|落库|推送|触发|同步|异步|扣减|回滚|补偿|提交|发起|展示|显示|保存|删除|拦截)"
)
ANGLE_TOKEN_RE = re.compile(r"<(?!/?br\s*/?\s*>)([^<>\r\n]{1,120})>", re.IGNORECASE)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def normalize_text(value: Any) -> str:
    return "" if value is None else str(value)


def is_empty_value(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def format_table_cell(value: Any) -> str:
    return normalize_text(value).replace("\n", "<br>").replace("|", "\\|")


def markdown_table(columns: list[str], rows: list[list[Any]]) -> list[str]:
    lines = [
        "| " + " | ".join(format_table_cell(column) for column in columns) + " |",
        "|" + "|".join("---" for _ in columns) + "|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(format_table_cell(row[index]) if index < len(row) else "" for index in range(len(columns))) + " |")
    return lines


def inline_value(value: Any) -> str:
    if isinstance(value, dict):
        return "；".join(f"{key}={inline_value(item)}" for key, item in value.items() if not is_empty_value(item))
    if isinstance(value, list):
        return "；".join(inline_value(item) for item in value if not is_empty_value(item))
    return normalize_text(value)


def sanitize_markdown_angle_tokens(text: str) -> str:
    return ANGLE_TOKEN_RE.sub(lambda match: "{" + match.group(1).strip() + "}", text)


def render_solution_fields(fields: Any) -> list[str]:
    if not isinstance(fields, list):
        return ["- 无记录"]
    rows = [[field.get("field", ""), field.get("content", "")] for field in fields if isinstance(field, dict)]
    return markdown_table(["字段", "内容"], rows)


def render_source_refs(refs: Any) -> str:
    if not isinstance(refs, list) or not refs:
        return "无记录"
    return "；".join(inline_value(ref) for ref in refs if not is_empty_value(ref)) or "无记录"


def scenario_children(scenario: dict[str, Any]) -> list[dict[str, Any]]:
    children = scenario.get("children", [])
    return children if isinstance(children, list) else []


def heading(level: int, text: str) -> str:
    return f"{'#' * min(max(level, 1), 6)} {text}"


def render_test_point(point: dict[str, Any], heading_level: int) -> list[str]:
    lines = [heading(heading_level, f"{point.get('id')} {point.get('title')}"), ""]
    rows = [["验证目标", point.get("objective", "")], ["依据引用", render_source_refs(point.get("basisRefs", []))]]
    if normalize_text(point.get("note")):
        rows.append(["说明", point.get("note", "")])
    lines.extend(markdown_table(["字段", "内容"], rows))
    lines.append("")
    return lines


def render_analysis_scenario(scenario: dict[str, Any], depth: int) -> list[str]:
    level = 2 + depth
    lines = [heading(level, f"{scenario.get('id')} {scenario.get('title')}"), ""]
    lines.extend(render_solution_fields(scenario.get("fields", [])))
    lines.append("")
    children = scenario_children(scenario)
    if children:
        for child in children:
            lines.extend(render_analysis_scenario(child, depth + 1))
    else:
        for point in scenario.get("testPoints", []):
            if isinstance(point, dict):
                lines.extend(render_test_point(point, level + 1))
    return lines


def render_analysis_solution(data: dict[str, Any]) -> str:
    lines = [f"# {data.get('title', '测试分析方案')}", "", "## 1. 需求范围", ""]
    lines.extend(render_solution_fields(data.get("scope", [])))
    lines.extend(["", "## 2. 测试场景与测试点", ""])
    for scenario in data.get("scenarios", []):
        if isinstance(scenario, dict):
            lines.extend(render_analysis_scenario(scenario, 1))
    return "\n".join(lines).rstrip() + "\n"


def numbered_lines(items: Any) -> str:
    if not isinstance(items, list) or not items:
        return "无"
    return "<br/>".join(f"{index}、{normalize_text(item)}" for index, item in enumerate(items, start=1))


def test_data_lines(items: Any) -> str:
    if not isinstance(items, list) or not items:
        return "无"
    rows = []
    for item in items:
        if isinstance(item, dict):
            rows.append(f"{item.get('name', '')}={item.get('value', '')}；说明={item.get('description', '')}")
    return "<br/>".join(rows) or "无"


def render_test_case(case: dict[str, Any], level: int) -> list[str]:
    if level <= 5:
        lines = [heading(level, f"{case.get('id')} {case.get('title')}"), ""]
        prefix = ""
    else:
        lines = [f"- {case.get('id')} {case.get('title')}"]
        prefix = "  "
    steps = case.get("steps", []) if isinstance(case.get("steps"), list) else []
    actions = "<br/>".join(f"{index}、{step.get('action', '')}" for index, step in enumerate(steps, start=1) if isinstance(step, dict)) or "无"
    expected = "<br/>".join(f"{index}、{step.get('expected', '')}" for index, step in enumerate(steps, start=1) if isinstance(step, dict)) or "无"
    fields = [
        ("前置条件", numbered_lines(case.get("preconditions", []))),
        ("测试数据", test_data_lines(case.get("testData", []))),
        ("测试步骤", actions),
        ("预期结果", expected),
        ("用例级别", case.get("level", "")),
        ("最终预期", case.get("expectedResult", "")),
        ("来源引用", render_source_refs(case.get("sourceRefs", []))),
    ]
    for label, value in fields:
        lines.extend([f"{prefix}- {label}：", f"{prefix}  - {value}"])
    lines.append("")
    return lines


def render_design_scenario(scenario: dict[str, Any], depth: int) -> list[str]:
    level = 1 + depth
    lines = [heading(level, f"{scenario.get('id')} {scenario.get('title')}"), ""]
    lines.extend(render_solution_fields(scenario.get("fields", [])))
    lines.append("")
    children = scenario_children(scenario)
    if children:
        for child in children:
            lines.extend(render_design_scenario(child, depth + 1))
    else:
        for point in scenario.get("testPoints", []):
            if not isinstance(point, dict):
                continue
            lines.extend(render_test_point(point, level + 1))
            for case in point.get("testCases", []):
                if isinstance(case, dict):
                    lines.extend(render_test_case(case, level + 2))
    return lines


def render_design_solution(data: dict[str, Any]) -> str:
    lines = [f"# {data.get('title', '测试设计方案')}", "", "## 设计输入", ""]
    lines.extend(render_solution_fields(data.get("inputs", [])))
    lines.append("")
    for scenario in data.get("scenarios", []):
        if isinstance(scenario, dict):
            lines.extend(render_design_scenario(scenario, 1))
    return "\n".join(lines).rstrip() + "\n"


def render_json_artifact(data: dict[str, Any], source_path: Path | None = None) -> str:
    artifact_type = data.get("artifactType")
    if artifact_type == "test-analysis-solution":
        return sanitize_markdown_angle_tokens(render_analysis_solution(data))
    if artifact_type == "test-design-solution":
        return sanitize_markdown_angle_tokens(render_design_solution(data))
    raise ValueError(f"只有结果交付件 JSON 可渲染 Markdown，当前 artifactType={artifact_type}")


def collect_renderable_json_files(run_dir: Path) -> list[tuple[Path, Path]]:
    pairs = [
        (run_dir / "deliverables" / "test-analysis-solution.json", run_dir / "deliverables" / "test-analysis-solution.md"),
        (run_dir / "deliverables" / "test-design-solution.json", run_dir / "deliverables" / "test-design-solution.md"),
    ]
    return [pair for pair in pairs if pair[0].is_file()]


def validate_test_cases(cases: Any, parent_id: str, errors: list[str], seen_ids: set[str]) -> None:
    allowed = {"id", "title", "level", "preconditions", "testData", "steps", "expectedResult", "sourceRefs"}
    if not isinstance(cases, list) or not cases:
        errors.append(f"{parent_id} 缺少 testCases")
        return
    for case in cases:
        if not isinstance(case, dict):
            errors.append(f"{parent_id} testCases 中存在非对象节点")
            continue
        case_id = normalize_text(case.get("id"))
        if not re.fullmatch(r"TC-\d{3}", case_id):
            errors.append(f"测试用例编号格式非法: {case.get('id')}")
        elif case_id in seen_ids:
            errors.append(f"测试用例编号重复: {case_id}")
        else:
            seen_ids.add(case_id)
        extra = sorted(set(case) - allowed)
        if extra:
            errors.append(f"{case_id} 包含 schemaVersion 2.0 未定义字段: {', '.join(extra)}")
        if not case.get("title") or not case.get("expectedResult"):
            errors.append(f"{case_id} 缺少 title 或 expectedResult")
        if case.get("level") not in TEST_CASE_LEVEL_VALUES:
            errors.append(f"{case_id} level 必须为 Level 0 到 Level 4")
        if not isinstance(case.get("preconditions"), list):
            errors.append(f"{case_id} preconditions 必须是数组")
        test_data = case.get("testData")
        if not isinstance(test_data, list) or not test_data:
            errors.append(f"{case_id} testData 必须是非空数组")
        else:
            for index, item in enumerate(test_data, start=1):
                if not isinstance(item, dict) or any(is_empty_value(item.get(key)) for key in ("name", "value", "description")):
                    errors.append(f"{case_id} testData[{index}] 必须包含 name/value/description")
        steps = case.get("steps")
        if not isinstance(steps, list) or not steps:
            errors.append(f"{case_id} steps 必须是非空数组")
        else:
            for index, step in enumerate(steps, start=1):
                if not isinstance(step, dict):
                    errors.append(f"{case_id} steps[{index}] 不是对象")
                    continue
                if step.get("stepNo") != index:
                    errors.append(f"{case_id} steps[{index}] stepNo 应为 {index}")
                action = normalize_text(step.get("action")).strip()
                if not action or not step.get("expected"):
                    errors.append(f"{case_id} steps[{index}] 缺少 action 或 expected")
                if action.startswith(ASSERTION_ACTION_PREFIXES):
                    errors.append(f"{case_id} steps[{index}].action 不应单独写检查项")
                if SYSTEM_ACTION_ACTOR_RE.search(action):
                    errors.append(f"{case_id} steps[{index}].action 不应写系统行为")
        if case.get("sourceRefs") is not None and not isinstance(case.get("sourceRefs"), list):
            errors.append(f"{case_id} sourceRefs 必须是数组")


def validate_solution(data: dict[str, Any], *, design: bool) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    expected_type = "test-design-solution" if design else "test-analysis-solution"
    if data.get("artifactType") != expected_type:
        errors.append(f"artifactType 必须为 {expected_type}")
    if data.get("schemaVersion") != "2.0":
        errors.append("schemaVersion 必须为 2.0")
    scenarios = data.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        return errors + ["主交付件 JSON 缺少 scenarios"], warnings
    seen_tp: set[str] = set()
    seen_tc: set[str] = set()
    scenario_keys = {"id", "title", "fields", "children", "testPoints"}
    point_keys = {"id", "title", "objective", "basisRefs", "note"} | ({"testCases"} if design else set())

    def walk(nodes: list[Any], parent: str = "", depth: int = 1) -> None:
        if depth > 3:
            errors.append(f"{parent or 'scenarios'} 超过 3 层 SC 深度")
            return
        for index, scenario in enumerate(nodes, start=1):
            if not isinstance(scenario, dict):
                errors.append(f"{parent or 'scenarios'}[{index}] 不是对象")
                continue
            expected = f"{parent}-{index:03d}" if parent else f"SC-{index:03d}"
            scenario_id = normalize_text(scenario.get("id"))
            if scenario_id != expected:
                errors.append(f"场景序号应为 {expected}，实际为 {scenario_id}")
            extra = sorted(set(scenario) - scenario_keys)
            if extra:
                errors.append(f"{scenario_id} 包含 schemaVersion 2.0 未定义字段: {', '.join(extra)}")
            children = scenario.get("children", []) or []
            points = scenario.get("testPoints", []) or []
            if not isinstance(children, list):
                errors.append(f"{scenario_id} children 必须是数组")
                children = []
            if children:
                if points:
                    errors.append(f"{scenario_id} 是非叶子场景，不得挂载 testPoints")
                walk(children, scenario_id, depth + 1)
                continue
            if not isinstance(points, list) or not points:
                errors.append(f"{scenario_id} 是叶子场景，必须包含 testPoints")
                continue
            if not any(isinstance(point, dict) and point.get("title") == "E2E场景测试" for point in points):
                errors.append(f"{scenario_id} 缺少 E2E场景测试")
            for point in points:
                if not isinstance(point, dict):
                    errors.append(f"{scenario_id} testPoints 中存在非对象节点")
                    continue
                tp_id = normalize_text(point.get("id"))
                if not re.fullmatch(r"TP-\d{3}", tp_id):
                    errors.append(f"测试点编号格式非法: {tp_id}")
                elif tp_id in seen_tp:
                    errors.append(f"测试点编号重复: {tp_id}")
                else:
                    seen_tp.add(tp_id)
                extra_point = sorted(set(point) - point_keys)
                if extra_point:
                    errors.append(f"{tp_id} 包含 schemaVersion 2.0 未定义字段: {', '.join(extra_point)}")
                if not point.get("title") or not point.get("objective"):
                    errors.append(f"{tp_id} 缺少 title 或 objective")
                if design:
                    validate_test_cases(point.get("testCases"), tp_id, errors, seen_tc)

    walk(scenarios)
    return errors, warnings


def validate_artifact(data: dict[str, Any]) -> tuple[list[str], list[str]]:
    artifact_type = data.get("artifactType")
    if artifact_type == "test-analysis-solution":
        return validate_solution(data, design=False)
    if artifact_type == "test-design-solution":
        return validate_solution(data, design=True)
    return [f"只有结果交付件允许使用 canonical JSON，当前 artifactType={artifact_type}"], []
