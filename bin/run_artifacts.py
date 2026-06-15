#!/usr/bin/env python3
"""Shared helpers for run JSON artifacts and Markdown rendering."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


STATUS_VALUES = {"pending", "in_progress", "done", "blocked", "skipped"}
APPLICATION_STATUS_VALUES = {
    "applied",
    "not_applicable",
    "insufficient_evidence",
    "conflict_with_requirement",
    "deferred_to_review",
}
EXPECTED_FALLBACK = "待人工分析确认"
ANALYSIS_REQUIRED_STAGES = [
    "固定 PROJECT_ROOT 与运行目录",
    "构建上下文包",
    "输入事实建模",
    "待确认治理",
    "测试技术路由",
    "专项分析",
    "按源补读",
    "测试分析方案生成",
    "确定性校验",
    "独立评审",
    "覆盖审查",
    "输出收口",
]
DESIGN_REQUIRED_STAGES = [
    "固定 PROJECT_ROOT 与运行目录",
    "测试分析方案校验",
    "构建上下文包",
    "设计依据补读",
    "测试设计方案生成",
    "确定性校验",
    "独立评审",
    "覆盖审查",
    "输出收口",
]
OPTIONAL_STAGES = {"按源补读", "设计依据补读"}
STAGE_ALIASES = {
    "方法路由": "测试技术路由",
    "专项方法分析": "专项分析",
    "场景化测试点生成": "测试分析方案生成",
    "需求可测性分析": "输入事实建模",
    "设计方案提取": "输入事实建模",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def markdown_table(columns: list[str], rows: list[list[str]]) -> list[str]:
    lines = [
        "| " + " | ".join(columns) + " |",
        "|" + "|".join("---" for _ in columns) + "|",
    ]
    for row in rows:
        padded = [str(row[index]) if index < len(row) else "" for index in range(len(columns))]
        lines.append("| " + " | ".join(padded) + " |")
    return lines


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def expected_json_path_for_markdown(markdown_path: Path) -> Path:
    return markdown_path.with_suffix(".json")


def render_task_list(data: dict[str, Any]) -> str:
    metadata = data.get("metadata", {})
    lines = ["# 测试分析方案任务清单", "", "## 运行标识", ""]
    for label, key in [
        ("需求文档", "requirementDocument"),
        ("设计方案文档", "designDocument"),
        ("run-id", "runId"),
        ("PROJECT_ROOT", "projectRoot"),
        ("生成时间", "generatedAt"),
    ]:
        lines.append(f"- {label}：{normalize_text(metadata.get(key, '未记录'))}")
    lines.extend(["", "## 任务列表", ""])
    rows = []
    for stage in data.get("stages", []):
        rows.append(
            [
                normalize_text(stage.get("order")),
                normalize_text(stage.get("stage")),
                normalize_text(stage.get("owner")),
                normalize_text(stage.get("checkpoint")),
                normalize_text(stage.get("status")),
                normalize_text(stage.get("evidence")),
            ]
        )
    lines.extend(markdown_table(["序号", "阶段", "负责 skill", "必须产物/检查点", "状态", "证据/路径"], rows))
    return "\n".join(lines).rstrip() + "\n"


def render_generic_document(data: dict[str, Any]) -> str:
    lines = [f"# {data.get('title', '未命名产物')}", ""]
    for section in data.get("sections", []):
        level = int(section.get("level", 2))
        heading = normalize_text(section.get("heading"))
        lines.extend([f"{'#' * level} {heading}", ""])
        for block in section.get("content", []):
            block_type = block.get("type")
            if block_type == "items":
                for item in block.get("items", []):
                    label = normalize_text(item.get("label"))
                    value = normalize_text(item.get("value"))
                    lines.append(f"- {label}：{value}" if label else f"- {value}")
                lines.append("")
            elif block_type == "bullets":
                for item in block.get("items", []):
                    lines.append(f"- {normalize_text(item)}")
                lines.append("")
            elif block_type == "table":
                lines.extend(markdown_table(block.get("columns", []), block.get("rows", [])))
                lines.append("")
            elif block_type == "paragraph":
                text = normalize_text(block.get("text")).rstrip()
                if text:
                    lines.append(text)
                    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_solution_fields(fields: list[dict[str, Any]]) -> list[str]:
    rows = [[normalize_text(field.get("field")), normalize_text(field.get("content"))] for field in fields]
    return markdown_table(["字段", "内容"], rows)


def render_analysis_solution(data: dict[str, Any]) -> str:
    lines = [f"# {data.get('title', '测试分析方案')}", "", "## 1. 需求范围", ""]
    lines.extend(render_solution_fields(data.get("scope", [])))
    lines.extend(["", "## 2. 测试场景与测试点", ""])
    for scenario in data.get("scenarios", []):
        lines.extend([f"### {scenario.get('id')} {scenario.get('title')}", ""])
        lines.extend(render_solution_fields(scenario.get("fields", [])))
        lines.append("")
        for point in scenario.get("testPoints", []):
            lines.extend([f"#### {point.get('id')} {point.get('title')}", ""])
            for detail in point.get("details", []):
                lines.append(f"##### {detail.get('id')} {detail.get('title')}")
                failure_details = detail.get("failureDetails", [])
                if failure_details:
                    lines.append("")
                    for failure in failure_details:
                        lines.append(f"###### {failure.get('id')} {failure.get('title')}")
                        lines.extend(["", f"- 测试点详情：{failure.get('description', '')}", ""])
                        lines.append(f"- 预期结果：{failure.get('expectedResult', '')}")
                        lines.append("")
                else:
                    lines.extend(["", f"- 测试点详情：{detail.get('description', '')}", ""])
                    lines.append(f"- 预期结果：{detail.get('expectedResult', '')}")
                    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_design_items(items: list[dict[str, Any]]) -> list[str]:
    return [f"- {item.get('id')} {item.get('content', '')}" for item in items]


def render_design_solution(data: dict[str, Any]) -> str:
    lines = [f"# {data.get('title', '测试设计方案')}", "", "## 1. 设计输入", ""]
    lines.extend(render_solution_fields(data.get("inputs", [])))
    lines.extend(["", "## 2. 测试场景与测试设计", ""])
    for scenario in data.get("scenarios", []):
        lines.extend([f"### {scenario.get('id')} {scenario.get('title')}", ""])
        lines.extend(render_solution_fields(scenario.get("fields", [])))
        lines.append("")
        for point in scenario.get("testPoints", []):
            lines.extend([f"#### {point.get('id')} {point.get('title')}", ""])
            for detail in point.get("details", []):
                lines.append(f"##### {detail.get('id')} {detail.get('title')}")
                failure_details = detail.get("failureDetails", [])
                if failure_details:
                    lines.append("")
                    for failure in failure_details:
                        lines.append(f"###### {failure.get('id')} {failure.get('title')}")
                        lines.extend(["", f"- 测试点详情：{failure.get('description', '')}", ""])
                        lines.append(f"- 预期结果：{failure.get('expectedResult', '')}")
                        items = render_design_items(failure.get("designItems", []))
                        if items:
                            lines.extend(["", *items])
                        lines.append("")
                else:
                    lines.extend(["", f"- 测试点详情：{detail.get('description', '')}", ""])
                    lines.append(f"- 预期结果：{detail.get('expectedResult', '')}")
                    items = render_design_items(detail.get("designItems", []))
                    if items:
                        lines.extend(["", *items])
                    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_review_report(data: dict[str, Any]) -> str:
    title = data.get("title") or data.get("artifactType", "review-report")
    lines = [f"# {title}", "", "## 1. 结论", ""]
    lines.append(f"- result：{data.get('result', '未记录')}")
    summary = data.get("summary")
    if summary:
        lines.append(f"- summary：{summary}")
    lines.append("")
    for heading, key in [
        ("## 2. Findings", "findings"),
        ("## 3. Blocking Issues", "blockingIssues"),
        ("## 4. Recommendations", "recommendations"),
        ("## 5. Evidence Refs", "evidenceRefs"),
    ]:
        lines.extend([heading, ""])
        values = data.get(key, [])
        if not values:
            lines.append("- 无")
        else:
            for value in values:
                if isinstance(value, dict):
                    label = value.get("id") or value.get("title") or value.get("location") or "item"
                    detail = value.get("description") or value.get("detail") or value.get("evidence") or value
                    lines.append(f"- {label}：{detail}")
                else:
                    lines.append(f"- {value}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


RENDERERS = {
    "task-list": render_task_list,
    "context-pack": render_generic_document,
    "input-fact-model": render_generic_document,
    "clarification-session": render_generic_document,
    "test-analysis-solution": render_analysis_solution,
    "test-design-solution": render_design_solution,
    "test-analysis-solution-review": render_review_report,
    "test-design-solution-review": render_review_report,
    "coverage-review": render_review_report,
}


def render_json_artifact(data: dict[str, Any]) -> str:
    artifact_type = data.get("artifactType")
    renderer = RENDERERS.get(artifact_type)
    if renderer is None:
        raise ValueError(f"unsupported artifactType: {artifact_type}")
    return renderer(data)


def collect_renderable_json_files(run_dir: Path) -> list[tuple[Path, Path]]:
    pairs = [
        (run_dir / "process" / "task-list.json", run_dir / "process" / "task-list.md"),
        (run_dir / "process" / "context-pack.json", run_dir / "process" / "context-pack.md"),
        (run_dir / "process" / "input-fact-model.json", run_dir / "process" / "input-fact-model.md"),
        (run_dir / "process" / "clarification-session.json", run_dir / "process" / "clarification-session.md"),
        (run_dir / "deliverables" / "test-analysis-solution.json", run_dir / "deliverables" / "test-analysis-solution.md"),
        (run_dir / "deliverables" / "test-design-solution.json", run_dir / "deliverables" / "test-design-solution.md"),
        (run_dir / "reports" / "test-analysis-solution-review.json", run_dir / "reports" / "test-analysis-solution-review.md"),
        (run_dir / "reports" / "test-design-solution-review.json", run_dir / "reports" / "test-design-solution-review.md"),
        (run_dir / "reports" / "coverage-review.json", run_dir / "reports" / "coverage-review.md"),
    ]
    return [(json_path, markdown_path) for json_path, markdown_path in pairs if json_path.exists()]


def validate_task_list(data: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    stages = data.get("stages")
    if not isinstance(stages, list) or not stages:
        return ["task-list.json 缺少 stages"], warnings

    seen_stages: list[str] = []
    statuses: dict[str, str] = {}
    in_progress: list[str] = []
    for index, stage in enumerate(stages, start=1):
        if not isinstance(stage, dict):
            errors.append(f"task-list.json stages[{index}] 不是对象")
            continue
        order = stage.get("order")
        name = STAGE_ALIASES.get(normalize_text(stage.get("stage")), normalize_text(stage.get("stage")))
        status = normalize_text(stage.get("status"))
        if order != index:
            errors.append(f"task-list.json 阶段 `{name}` 序号应为 {index}，实际为 {order}")
        if status not in STATUS_VALUES:
            errors.append(f"task-list.json 阶段 `{name}` 状态非法: {status}")
        if status in {"done", "blocked", "skipped"} and not stage.get("evidence"):
            errors.append(f"task-list.json 阶段 `{name}` 状态为 {status} 但 evidence 为空")
        if status == "in_progress":
            in_progress.append(name)
        seen_stages.append(name)
        statuses[name] = status

    if len(in_progress) > 1:
        errors.append("task-list.json 同时存在多个 in_progress 阶段: " + "、".join(in_progress))

    matched = None
    for flow_name, required in [("测试分析", ANALYSIS_REQUIRED_STAGES), ("测试设计", DESIGN_REQUIRED_STAGES)]:
        if all(stage in statuses for stage in required):
            matched = (flow_name, required)
            break
    if matched is None:
        warnings.append("task-list.json 未完整匹配测试分析或测试设计固定阶段")
        return errors, warnings

    flow_name, required = matched
    positions = [seen_stages.index(stage) for stage in required if stage in seen_stages]
    if positions != sorted(positions):
        errors.append(f"task-list.json {flow_name}固定阶段顺序不正确")
    for stage in required:
        status = statuses.get(stage)
        if stage in OPTIONAL_STAGES:
            if status not in {"done", "skipped"}:
                errors.append(f"task-list.json 可选阶段 `{stage}` 最终状态应为 done 或 skipped，当前为 {status}")
        elif status != "done":
            errors.append(f"task-list.json 必选阶段 `{stage}` 最终状态应为 done，当前为 {status}")
    return errors, warnings


def validate_generic_document(data: dict[str, Any], artifact_type: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not data.get("title"):
        errors.append(f"{artifact_type}.json 缺少 title")
    if not data.get("sections"):
        errors.append(f"{artifact_type}.json 缺少 sections")
    rendered = render_generic_document(data)
    if artifact_type == "context-pack":
        for marker in ("project-key", "personal-key", "项目知识阶段绑定", "补读"):
            if marker not in rendered:
                warnings.append(f"context-pack.json 未显式记录: {marker}")
    if artifact_type == "clarification-session":
        for marker in ("候选问题总表", "候选问题详情", "去重与降级结果", "预期结果兜底清单"):
            if marker not in rendered:
                errors.append(f"clarification-session.json 缺少固定章节: {marker}")
        if "无待确认候选" not in rendered and "CQ-" not in rendered:
            warnings.append("clarification-session.json 未记录候选问题，也未声明无待确认候选")
    return errors, warnings


def validate_solution_ids(data: dict[str, Any], is_design: bool) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    scenarios = data.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        return ["主交付件 JSON 缺少 scenarios"], warnings

    tp_index = 1
    tdi_index = 1
    for sc_index, scenario in enumerate(scenarios, start=1):
        expected_sc = f"SC-{sc_index:03d}"
        if scenario.get("id") != expected_sc:
            errors.append(f"场景序号应为 {expected_sc}，实际为 {scenario.get('id')}")
        points = scenario.get("testPoints")
        if not isinstance(points, list) or not points:
            errors.append(f"{expected_sc} 缺少 testPoints")
            continue
        if not any(point.get("title") == "E2E场景测试" for point in points):
            errors.append(f"{scenario.get('id')} 缺少 E2E场景测试")
        for point in points:
            expected_tp = f"TP-{tp_index:03d}"
            point_id = point.get("id")
            if point_id != expected_tp:
                errors.append(f"测试点序号应为 {expected_tp}，实际为 {point_id}")
            details = point.get("details")
            if not isinstance(details, list) or not details:
                errors.append(f"{point_id} 缺少 details")
                tp_index += 1
                continue
            for detail_index, detail in enumerate(details, start=1):
                expected_detail = f"{point_id}-{detail_index:03d}"
                detail_id = detail.get("id")
                if detail_id != expected_detail:
                    errors.append(f"测试点明细序号应为 {expected_detail}，实际为 {detail_id}")
                failures = detail.get("failureDetails", [])
                if failures:
                    for failure_index, failure in enumerate(failures, start=1):
                        expected_failure = f"{detail_id}-{failure_index:03d}"
                        if failure.get("id") != expected_failure:
                            errors.append(f"失败类型明细序号应为 {expected_failure}，实际为 {failure.get('id')}")
                        if not failure.get("description") or not failure.get("expectedResult"):
                            errors.append(f"{failure.get('id')} 缺少 description 或 expectedResult")
                        if is_design:
                            tdi_index, tdi_errors = validate_design_items(failure.get("designItems", []), tdi_index, failure.get("id"))
                            errors.extend(tdi_errors)
                else:
                    if not detail.get("description") or not detail.get("expectedResult"):
                        errors.append(f"{detail_id} 缺少 description 或 expectedResult")
                    if is_design:
                        tdi_index, tdi_errors = validate_design_items(detail.get("designItems", []), tdi_index, detail_id)
                        errors.extend(tdi_errors)
                if not is_design and (detail.get("designItems") or "TDI-" in json.dumps(detail, ensure_ascii=False)):
                    errors.append(f"{detail_id} 是分析方案节点，不得包含 TDI-* 或 designItems")
            tp_index += 1
    return errors, warnings


def validate_design_items(items: Any, start_index: int, parent_id: str | None) -> tuple[int, list[str]]:
    errors: list[str] = []
    if not isinstance(items, list) or not items:
        errors.append(f"{parent_id} 缺少 designItems")
        return start_index, errors
    for item in items:
        expected_id = f"TDI-{start_index:03d}"
        if item.get("id") != expected_id:
            errors.append(f"测试设计项序号应为 {expected_id}，实际为 {item.get('id')}")
        content = normalize_text(item.get("content"))
        if not content:
            errors.append(f"{item.get('id')} content 为空")
        if re.search(r"https?://\S+", content, re.IGNORECASE):
            errors.append(f"{item.get('id')} 不得包含完整裸 URL")
        if any(term in content for term in ("处理成功", "处理失败", "显示提示", "发送通知", "接口调用正确")):
            errors.append(f"{item.get('id')} 疑似写成结果或动作表达")
        start_index += 1
    return start_index, errors


def validate_review_json(data: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    result = data.get("result")
    if result not in {"通过", "需修正", "失败", "警告", "不适用"}:
        errors.append("review/coverage JSON result 必须为 通过/需修正/失败/警告/不适用")
    for key in ("findings", "blockingIssues", "recommendations", "evidenceRefs"):
        if key not in data:
            warnings.append(f"{data.get('artifactType')} 缺少 {key}")
        elif not isinstance(data.get(key), list):
            errors.append(f"{data.get('artifactType')} 的 {key} 必须是数组")
    return errors, warnings


def validate_artifact(data: dict[str, Any]) -> tuple[list[str], list[str]]:
    artifact_type = data.get("artifactType")
    errors: list[str] = []
    warnings: list[str] = []
    if not artifact_type:
        return ["JSON 缺少 artifactType"], warnings
    if data.get("schemaVersion") != "1.0":
        errors.append(f"{artifact_type}.json schemaVersion 必须为 1.0")
    if artifact_type == "task-list":
        task_errors, task_warnings = validate_task_list(data)
        errors.extend(task_errors)
        warnings.extend(task_warnings)
    elif artifact_type in {"context-pack", "input-fact-model", "clarification-session"}:
        doc_errors, doc_warnings = validate_generic_document(data, artifact_type)
        errors.extend(doc_errors)
        warnings.extend(doc_warnings)
    elif artifact_type == "test-analysis-solution":
        solution_errors, solution_warnings = validate_solution_ids(data, is_design=False)
        errors.extend(solution_errors)
        warnings.extend(solution_warnings)
    elif artifact_type == "test-design-solution":
        solution_errors, solution_warnings = validate_solution_ids(data, is_design=True)
        errors.extend(solution_errors)
        warnings.extend(solution_warnings)
    elif artifact_type in {"test-analysis-solution-review", "test-design-solution-review", "coverage-review"}:
        review_errors, review_warnings = validate_review_json(data)
        errors.extend(review_errors)
        warnings.extend(review_warnings)
    else:
        errors.append(f"不支持的 artifactType: {artifact_type}")
    return errors, warnings
