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
ARTIFACT_TITLES = {
    "task-list": "测试分析方案任务清单",
    "context-pack": "上下文来源索引",
    "input-fact-model": "输入事实模型",
    "clarification-session": "待确认治理记录",
    "test-analysis-solution": "测试分析方案",
    "test-design-solution": "测试设计方案",
    "test-analysis-solution-review": "测试分析方案语义评审结果",
    "test-design-solution-review": "测试设计方案语义评审结果",
    "coverage-review": "覆盖审查结果",
}
GENERIC_METADATA_KEYS = {"artifactType", "alternateArtifactTypes", "schemaVersion", "title", "sections"}
ANALYSIS_REQUIRED_STAGES = [
    "固定 PROJECT_ROOT 与运行目录",
    "上下文来源索引",
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
    "上下文来源索引",
    "设计依据补读",
    "测试设计方案生成",
    "确定性校验",
    "独立评审",
    "覆盖审查",
    "输出收口",
]
OPTIONAL_STAGES = {"按源补读", "设计依据补读"}
STAGE_ALIASES = {
    "构建上下文包": "上下文来源索引",
    "记忆上下文构建": "上下文来源索引",
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
    safe_columns = [format_table_cell(column) for column in columns]
    lines = [
        "| " + " | ".join(safe_columns) + " |",
        "|" + "|".join("---" for _ in safe_columns) + "|",
    ]
    for row in rows:
        padded = [format_table_cell(row[index]) if index < len(row) else "" for index in range(len(columns))]
        lines.append("| " + " | ".join(padded) + " |")
    return lines


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def format_table_cell(value: Any) -> str:
    return normalize_text(value).replace("\n", "<br>").replace("|", "\\|")


def artifact_title(data: dict[str, Any], fallback: str | None = None) -> str:
    artifact_type = normalize_text(data.get("artifactType"))
    return normalize_text(data.get("title") or fallback or ARTIFACT_TITLES.get(artifact_type) or artifact_type or "运行产物")


def is_empty_value(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def labelize_key(key: str) -> str:
    labels = {
        "id": "ID",
        "project-key": "project-key",
        "personal-key": "personal-key",
        "projectKey": "project-key",
        "personalKey": "personal-key",
        "runId": "运行 ID",
        "reason": "原因",
        "result": "结论",
        "summary": "摘要",
        "severity": "级别",
        "dimension": "维度",
        "gate": "门禁",
        "location": "位置",
        "description": "说明",
        "detail": "详情",
        "evidence": "证据",
        "recommendation": "建议",
        "source": "来源",
        "sourceFile": "来源文件",
        "sourceType": "来源类型",
        "stage": "阶段",
        "status": "状态",
        "note": "说明",
        "ruleId": "规则 ID",
        "requirementRef": "需求引用",
        "artifactLocation": "产物位置",
        "suggestedFix": "修复建议",
    }
    if key in labels:
        return labels[key]
    words = re.sub(r"(?<!^)([A-Z])", r" \1", key).replace("_", " ").replace("-", " ")
    return words[:1].upper() + words[1:] if words else key


def inline_value(value: Any) -> str:
    if isinstance(value, dict):
        parts = [f"{labelize_key(str(key))}={inline_value(item)}" for key, item in value.items() if not is_empty_value(item)]
        return "；".join(parts)
    if isinstance(value, list):
        return "；".join(inline_value(item) for item in value if not is_empty_value(item))
    return normalize_text(value)


def preferred_columns(items: list[dict[str, Any]], preferred_keys: list[str] | None = None) -> list[str]:
    columns: list[str] = []
    for key in preferred_keys or []:
        if any(key in item for item in items):
            columns.append(key)
    for item in items:
        for key in item:
            if key not in columns:
                columns.append(key)
    return columns


def render_value(value: Any, preferred_keys: list[str] | None = None, empty_text: str = "无记录") -> list[str]:
    if is_empty_value(value):
        return [f"- {empty_text}"]
    if isinstance(value, list):
        dict_items = [item for item in value if isinstance(item, dict)]
        if dict_items and len(dict_items) == len(value):
            columns = preferred_columns(dict_items, preferred_keys)
            return markdown_table([labelize_key(column) for column in columns], [[inline_value(item.get(column)) for column in columns] for item in dict_items])
        lines: list[str] = []
        for item in value:
            if isinstance(item, dict):
                lines.append(f"- {inline_value(item)}")
            else:
                lines.append(f"- {normalize_text(item)}")
        return lines or [f"- {empty_text}"]
    if isinstance(value, dict):
        rows = [[labelize_key(str(key)), inline_value(item)] for key, item in value.items()]
        return markdown_table(["字段", "内容"], rows) if rows else [f"- {empty_text}"]
    return [normalize_text(value)]


def render_structured_sections(data: dict[str, Any], fallback_title: str, ordered_keys: list[str], key_labels: dict[str, str]) -> str:
    if data.get("sections"):
        return render_generic_document(data, fallback_title)
    lines = [f"# {artifact_title(data, fallback_title)}", ""]
    keys = [key for key in ordered_keys if key in data]
    keys.extend(key for key in data if key not in GENERIC_METADATA_KEYS and key not in keys)
    for key in keys:
        value = data.get(key)
        if is_empty_value(value):
            continue
        lines.extend([f"## {key_labels.get(key, labelize_key(key))}", ""])
        lines.extend(render_value(value))
        lines.append("")
    if len(lines) == 2:
        lines.append("- 无记录")
    return "\n".join(lines).rstrip() + "\n"


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


def render_generic_document(data: dict[str, Any], fallback_title: str | None = None) -> str:
    lines = [f"# {artifact_title(data, fallback_title)}", ""]
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


def render_context_pack(data: dict[str, Any]) -> str:
    if data.get("sections"):
        return render_generic_document(data, "上下文来源索引")

    lines = [f"# {artifact_title(data, '上下文来源索引')}", ""]

    requirement = data.get("requirement") if isinstance(data.get("requirement"), dict) else {}
    lines.extend(["## 本次需求", ""])
    lines.extend(
        markdown_table(
            ["字段", "值"],
            [
                ["path", requirement.get("path", "")],
                ["title", requirement.get("title", "")],
                ["keywords", "、".join(requirement.get("keywords", [])) if isinstance(requirement.get("keywords"), list) else requirement.get("keywords", "")],
            ],
        )
    )
    lines.append("")

    project_binding = data.get("projectBinding") if isinstance(data.get("projectBinding"), dict) else {}
    personal_binding = data.get("personalBinding") if isinstance(data.get("personalBinding"), dict) else {}
    lines.extend(["## 绑定结果", ""])
    lines.extend(
        markdown_table(
            ["绑定", "状态", "标识", "说明"],
            [
                ["projectBinding", project_binding.get("status", ""), project_binding.get("projectKey", ""), project_binding.get("reason", "")],
                ["personalBinding", personal_binding.get("status", ""), personal_binding.get("personalKey", ""), personal_binding.get("reason", "")],
            ],
        )
    )
    lines.append("")

    source_rows: list[list[str]] = []
    for source in data.get("sources", []):
        if not isinstance(source, dict):
            continue
        stages = source.get("availableStages", [])
        stage_text = "、".join(stages) if isinstance(stages, list) else normalize_text(stages)
        source_rows.append(
            [
                source.get("path", ""),
                source.get("name", ""),
                source.get("description", ""),
                stage_text,
                source.get("availability", ""),
            ]
        )
    lines.extend(["## 动态来源索引", ""])
    if source_rows:
        lines.extend(markdown_table(["路径", "名称", "描述", "可用阶段", "可见性"], source_rows))
    else:
        lines.append("无动态 project/personal 来源。")
    lines.append("")

    unscanned_rows: list[list[str]] = []
    for item in data.get("unscannedProjectSources", []):
        if isinstance(item, dict):
            unscanned_rows.append([item.get("path", ""), item.get("reason", "")])
        else:
            unscanned_rows.append([normalize_text(item), ""])
    lines.extend(["## 未扫描项目来源", ""])
    if unscanned_rows:
        lines.extend(markdown_table(["路径", "原因"], unscanned_rows))
    else:
        lines.append("无未扫描项目来源。")
    lines.append("")

    warning_rows = [[normalize_text(item)] for item in data.get("warnings", [])]
    lines.extend(["## 告警", ""])
    if warning_rows:
        lines.extend(markdown_table(["说明"], warning_rows))
    else:
        lines.append("无告警。")

    return "\n".join(lines).rstrip() + "\n"


def render_input_fact_model(data: dict[str, Any]) -> str:
    return render_structured_sections(
        data,
        "输入事实模型",
        [
            "inputSources",
            "sources",
            "facts",
            "factList",
            "requirementDesignMappings",
            "mappings",
            "clarificationItems",
            "clarifications",
            "sourceApplications",
            "applications",
        ],
        {
            "inputSources": "输入来源",
            "sources": "输入来源",
            "facts": "事实清单",
            "factList": "事实清单",
            "requirementDesignMappings": "需求-设计映射",
            "mappings": "需求-设计映射",
            "clarificationItems": "待确认事项",
            "clarifications": "待确认事项",
            "sourceApplications": "来源与应用说明",
            "applications": "来源与应用说明",
        },
    )


def render_clarification_session(data: dict[str, Any]) -> str:
    return render_structured_sections(
        data,
        "待确认治理记录",
        [
            "status",
            "runStatus",
            "candidates",
            "candidateSummary",
            "candidateDetails",
            "deduplicationResults",
            "deduplication",
            "expectedResultFallbacks",
            "fallbacks",
            "rules",
        ],
        {
            "status": "运行状态",
            "runStatus": "运行状态",
            "candidates": "候选问题总表",
            "candidateSummary": "候选问题总表",
            "candidateDetails": "候选问题详情",
            "deduplicationResults": "去重与降级结果",
            "deduplication": "去重与降级结果",
            "expectedResultFallbacks": "预期结果兜底清单",
            "fallbacks": "预期结果兜底清单",
            "rules": "治理规则",
        },
    )


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


def render_report_collection(
    lines: list[str],
    heading: str,
    data: dict[str, Any],
    key: str,
    preferred_keys: list[str] | None = None,
) -> None:
    lines.extend([heading, ""])
    lines.extend(render_value(data.get(key, []), preferred_keys))
    lines.append("")


def render_review_report(data: dict[str, Any]) -> str:
    title = data.get("title") or data.get("artifactType", "review-report")
    lines = [f"# {title}", "", "## 1. 结论", ""]
    lines.append(f"- result：{data.get('result', '未记录')}")
    summary = data.get("summary")
    if summary:
        lines.append(f"- summary：{summary}")
    lines.append("")
    render_report_collection(lines, "## 2. Findings", data, "findings", ["id", "severity", "dimension", "location", "description", "evidence", "recommendation"])
    render_report_collection(lines, "## 3. Blocking Issues", data, "blockingIssues", ["id", "severity", "location", "description", "evidence", "recommendation"])
    render_report_collection(lines, "## 4. Recommendations", data, "recommendations", ["id", "location", "description", "recommendation"])
    render_report_collection(lines, "## 5. Evidence Refs", data, "evidenceRefs", ["source", "location", "description"])
    render_report_collection(lines, "## 6. Knowledge Applications", data, "knowledgeApplications", ["sourceFile", "stage", "status", "location", "note"])
    return "\n".join(lines).rstrip() + "\n"


def render_coverage_report(data: dict[str, Any]) -> str:
    title = data.get("title") or "覆盖审查结果"
    lines = [f"# {title}", "", "## 1. 结论", ""]
    lines.append(f"- result：{data.get('result', '未记录')}")
    summary = data.get("summary")
    if summary:
        lines.append(f"- summary：{summary}")
    lines.append("")
    render_report_collection(lines, "## 2. Findings", data, "findings", ["id", "severity", "gate", "location", "description", "evidence", "recommendation"])
    render_report_collection(lines, "## 3. Blocking Issues", data, "blockingIssues", ["id", "severity", "gate", "location", "description", "evidence", "recommendation"])
    render_report_collection(lines, "## 4. Recommendations", data, "recommendations", ["id", "gate", "location", "description", "recommendation"])
    render_report_collection(lines, "## 5. Evidence Refs", data, "evidenceRefs", ["source", "location", "description"])
    render_report_collection(lines, "## 6. Quality Gates", data, "qualityGates", ["gate", "result", "description", "recommendation"])
    render_report_collection(lines, "## 7. Rules Applications", data, "rulesApplications", ["ruleId", "sourceFile", "stage", "status", "location", "note"])
    render_report_collection(lines, "## 8. Dynamic Source Applications", data, "projectKnowledgeApplications", ["sourceType", "sourceFile", "stage", "status", "location", "note"])
    render_report_collection(lines, "## 9. Coverage Gaps", data, "coverageGaps", ["id", "requirementRef", "artifactLocation", "description", "suggestedFix"])
    return "\n".join(lines).rstrip() + "\n"


RENDERERS = {
    "task-list": render_task_list,
    "context-pack": render_context_pack,
    "input-fact-model": render_input_fact_model,
    "clarification-session": render_clarification_session,
    "test-analysis-solution": render_analysis_solution,
    "test-design-solution": render_design_solution,
    "test-analysis-solution-review": render_review_report,
    "test-design-solution-review": render_review_report,
    "coverage-review": render_coverage_report,
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
        warnings.append(f"{artifact_type}.json 缺少 title，渲染时将使用 artifactType 默认标题")
    has_sections = bool(data.get("sections"))
    has_structured_fields = any(
        key not in GENERIC_METADATA_KEYS and not is_empty_value(value)
        for key, value in data.items()
    )
    if not has_sections and not has_structured_fields:
        errors.append(f"{artifact_type}.json 缺少 sections 或可渲染结构化字段")
    rendered = RENDERERS.get(artifact_type, render_generic_document)(data)
    if artifact_type == "context-pack":
        errors.extend(validate_context_pack_json(data))
    if artifact_type == "clarification-session":
        for marker in ("候选问题总表", "候选问题详情", "去重与降级结果", "预期结果兜底清单"):
            if marker not in rendered:
                errors.append(f"clarification-session.json 缺少固定章节: {marker}")
        if "无待确认候选" not in rendered and "CQ-" not in rendered:
            warnings.append("clarification-session.json 未记录候选问题，也未声明无待确认候选")
    return errors, warnings


def validate_context_pack_json(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    project_binding = data.get("projectBinding")
    personal_binding = data.get("personalBinding")
    if not isinstance(project_binding, dict):
        errors.append("context-pack.json 缺少对象字段: projectBinding")
    elif project_binding.get("status") not in {"resolved", "unresolved"}:
        errors.append("context-pack.json projectBinding.status 必须为 resolved 或 unresolved")
    if not isinstance(personal_binding, dict):
        errors.append("context-pack.json 缺少对象字段: personalBinding")
    elif personal_binding.get("status") not in {"default", "resolved"}:
        errors.append("context-pack.json personalBinding.status 必须为 default 或 resolved")

    allowed_source_prefixes = (
        "rules/projects/",
        "rules/user/",
        "knowledge/projects/",
        "knowledge/user/",
        "memory/projects/",
        "memory/user/",
    )
    forbidden_source_keys = {"sourceType", "layer", "projectKey", "stages", "applied"}
    forbidden_core_prefixes = (
        "rules/core/",
        "knowledge/core/",
        "rules/",
        "knowledge/",
        "templates/",
        "skills/",
        ".opencode/",
    )

    sources = data.get("sources")
    if not isinstance(sources, list):
        errors.append("context-pack.json 缺少数组字段: sources")
        return errors

    for index, source in enumerate(sources, start=1):
        if not isinstance(source, dict):
            errors.append(f"context-pack.json sources[{index}] 必须是对象")
            continue
        for key in ("path", "name", "description", "availableStages"):
            if is_empty_value(source.get(key)):
                errors.append(f"context-pack.json sources[{index}] 缺少字段: {key}")
        unexpected_keys = sorted(key for key in forbidden_source_keys if key in source)
        if unexpected_keys:
            errors.append(
                f"context-pack.json sources[{index}] 不应写入字段: {', '.join(unexpected_keys)}；"
                "context pack 只记录动态来源索引，应用状态写入后续阶段产物"
            )
        source_path = normalize_text(source.get("path")).replace("\\", "/")
        if re.match(r"^[A-Za-z]:/", source_path) or source_path.startswith("/"):
            errors.append(f"context-pack.json sources[{index}].path 必须是仓库相对路径，不得使用绝对路径")
        if any(source_path.startswith(prefix) for prefix in forbidden_core_prefixes) and not any(
            source_path.startswith(prefix) for prefix in allowed_source_prefixes
        ):
            errors.append(f"context-pack.json sources[{index}] 不得索引 core 层或 skill/template 路径: {source_path}")
        if source_path and not any(source_path.startswith(prefix) for prefix in allowed_source_prefixes):
            errors.append(
                f"context-pack.json sources[{index}].path 必须位于 project/personal 动态来源目录: {source_path}"
            )
        stages = source.get("availableStages")
        if not isinstance(stages, list) or not all(isinstance(stage, str) and stage for stage in stages):
            errors.append(f"context-pack.json sources[{index}].availableStages 必须是非空字符串数组")

    if "unscannedProjectSources" in data and not isinstance(data.get("unscannedProjectSources"), list):
        errors.append("context-pack.json unscannedProjectSources 必须是数组")
    if "warnings" in data and not isinstance(data.get("warnings"), list):
        errors.append("context-pack.json warnings 必须是数组")
    return errors


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
