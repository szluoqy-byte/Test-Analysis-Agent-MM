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
TEST_CASE_LEVEL_VALUES = {"Level 0", "Level 1", "Level 2", "Level 3", "Level 4"}
ARTIFACT_TITLES = {
    "task-list": "测试分析方案任务清单",
    "context-pack": "上下文来源索引",
    "input-fact-model": "输入事实模型",
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
ASSERTION_ACTION_PREFIXES = (
    "检查",
    "验证",
    "确认",
    "断言",
    "比对",
    "核对",
    "观察",
    "校验",
    "判断",
)
HTTP_ACTION_RE = re.compile(r"\b(GET|POST|PUT|PATCH|DELETE)\s+(/[A-Za-z0-9_./{}:-]+)")
ACTION_VARIANT_TERMS = (
    "不包含",
    "缺失",
    "未传",
    "为空",
    "空字符串",
    "非法",
    "无效",
    "错误",
    "超过",
    "小于",
    "大于",
    "边界",
    "最小",
    "最大",
    "重复",
    "不同",
    "过期",
    "不存在",
    "未登录",
    "无权限",
    "状态为",
    "返回成功",
    "返回失败",
    "超时",
    "乱序",
    "角色",
    "用户",
    "开关",
    "配置",
    "开启",
    "关闭",
    "启用",
    "禁用",
    "灰度",
    "回滚",
    "成功",
    "失败",
)
ACTION_PREFIX_RE = re.compile(r"^(发送|提交|调用|请求|发起|模拟|构造|输入|选择|切换|设置|使用|用户|角色|管理员|客服|系统|定时任务|批处理)")


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
        "projectKey": "project-key",
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
    stage_names = {normalize_text(stage.get("stage")) for stage in data.get("stages", []) if isinstance(stage, dict)}
    design_markers = {"测试分析方案校验", "设计依据补读", "测试设计方案生成"}
    title = "测试设计方案任务清单" if stage_names & design_markers else "测试分析方案任务清单"
    lines = [f"# {title}", "", "## 运行标识", ""]
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
    lines.extend(["## 绑定结果", ""])
    lines.extend(
        markdown_table(
            ["绑定", "状态", "标识", "说明"],
            [
                ["projectBinding", project_binding.get("status", ""), project_binding.get("projectKey", ""), project_binding.get("reason", "")],
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
            "sourceApplications": "来源与应用说明",
            "applications": "来源与应用说明",
        },
    )


def render_solution_fields(fields: list[dict[str, Any]]) -> list[str]:
    rows = [[normalize_text(field.get("field")), normalize_text(field.get("content"))] for field in fields]
    return markdown_table(["字段", "内容"], rows)


def render_solution_field_list(fields: Any) -> list[str]:
    if not isinstance(fields, list) or not fields:
        return ["- 无记录"]
    lines: list[str] = []
    for field in fields:
        if not isinstance(field, dict):
            continue
        name = normalize_text(field.get("field"))
        content = normalize_text(field.get("content"))
        if name or content:
            lines.append(f"- {name}：{content}" if name else f"- {content}")
    return lines if lines else ["- 无记录"]


def render_source_refs(refs: Any) -> str:
    if not isinstance(refs, list) or not refs:
        return "无记录"
    return "；".join(inline_value(ref) for ref in refs if not is_empty_value(ref)) or "无记录"


def scenario_children(scenario: dict[str, Any]) -> list[dict[str, Any]]:
    children = scenario.get("children", [])
    return children if isinstance(children, list) else []


def heading(level: int, text: str) -> str:
    return f"{'#' * min(max(level, 1), 6)} {text}"


def render_test_point(point: dict[str, Any], heading_level: int, *, table: bool = True) -> list[str]:
    lines = [heading(heading_level, f"{point.get('id')} {point.get('title')}"), ""]
    rows = [
        ["验证目标", point.get("objective", "")],
        ["依据引用", render_source_refs(point.get("basisRefs", []))],
    ]
    note = normalize_text(point.get("note"))
    if note:
        rows.append(["说明", note])
    if table:
        lines.extend(markdown_table(["字段", "内容"], rows))
    else:
        lines.extend(f"- {name}：{normalize_text(value)}" for name, value in rows)
    lines.append("")
    return lines


def render_analysis_scenario(scenario: dict[str, Any], depth: int) -> list[str]:
    scenario_level = 2 + depth
    lines = [heading(scenario_level, f"{scenario.get('id')} {scenario.get('title')}"), ""]
    lines.extend(render_solution_fields(scenario.get("fields", [])))
    lines.append("")
    children = scenario_children(scenario)
    if children:
        for child in children:
            lines.extend(render_analysis_scenario(child, depth + 1))
    else:
        for point in scenario.get("testPoints", []):
            lines.extend(render_test_point(point, scenario_level + 1))
    return lines


def render_analysis_solution(data: dict[str, Any]) -> str:
    lines = [f"# {data.get('title', '测试分析方案')}", "", "## 1. 需求范围", ""]
    lines.extend(render_solution_fields(data.get("scope", [])))
    lines.extend(["", "## 2. 测试场景与测试点", ""])
    for scenario in data.get("scenarios", []):
        if isinstance(scenario, dict):
            lines.extend(render_analysis_scenario(scenario, 1))
    return "\n".join(lines).rstrip() + "\n"


def render_test_data(items: Any) -> list[str]:
    if not isinstance(items, list) or not items:
        return ["- 无记录"]
    lines: list[str] = []
    for item in items:
        if isinstance(item, dict):
            name = normalize_text(item.get("name"))
            value = normalize_text(item.get("value"))
            description = normalize_text(item.get("description"))
            parts = [part for part in [f"{name}={value}" if value else name, f"说明={description}" if description else ""] if part]
            if parts:
                lines.append("- " + "；".join(parts))
    return lines if lines else ["- 无记录"]


def compact_lines(lines: list[str]) -> str:
    compacted = [line.strip().removeprefix("- ").strip() for line in lines if line.strip()]
    return "<br/>".join(compacted) if compacted else "无"


def render_compact_field(prefix: str, label: str, lines: list[str]) -> list[str]:
    compacted = compact_lines(lines)
    child_prefix = prefix + "  "
    return [f"{prefix}- {label}：", f"{child_prefix}- {compacted}"]


def render_numbered_items(items: Any) -> list[str]:
    if not isinstance(items, list) or not items:
        return ["1、无"]
    lines: list[str] = []
    for index, item in enumerate(items, start=1):
        text = normalize_text(item)
        if text:
            lines.append(f"{index}、{text}")
    return lines if lines else ["1、无"]


def render_test_actions(items: Any) -> list[str]:
    if not isinstance(items, list) or not items:
        return ["1、无"]
    lines: list[str] = []
    for index, item in enumerate(items, start=1):
        if isinstance(item, dict):
            action = normalize_text(item.get("action"))
            if action:
                lines.append(f"{index}、{action}")
    return lines if lines else ["1、无"]


def render_step_expectations(items: Any) -> list[str]:
    if not isinstance(items, list) or not items:
        return ["1、无"]
    lines: list[str] = []
    for index, item in enumerate(items, start=1):
        if isinstance(item, dict):
            expected = normalize_text(item.get("expected"))
            if expected:
                lines.append(f"{index}、{expected}")
    return lines if lines else ["1、无"]


def render_test_case(case: dict[str, Any], heading_level: int) -> list[str]:
    if heading_level <= 5:
        lines = [heading(heading_level, f"{case.get('id')} {case.get('title')}"), ""]
        prefix = ""
        separator = [""]
    else:
        lines = [f"- {case.get('id')} {case.get('title')}"]
        prefix = "  "
        separator = []
    preconditions = case.get("preconditions", [])
    lines.extend(render_compact_field(prefix, "前置条件", render_numbered_items(preconditions)))
    lines.extend(separator)
    lines.extend(render_compact_field(prefix, "测试数据", render_test_data(case.get("testData", []))))
    steps = case.get("steps", [])
    lines.extend(separator)
    lines.extend(render_compact_field(prefix, "测试步骤", render_test_actions(steps)))
    lines.extend(separator)
    lines.extend(render_compact_field(prefix, "预期结果", render_step_expectations(steps)))
    lines.extend(separator)
    lines.extend(render_compact_field(prefix, "用例级别", [normalize_text(case.get("level")) or "无记录"]))
    lines.extend(separator)
    lines.extend(render_compact_field(prefix, "最终预期", [normalize_text(case.get("expectedResult")) or "无记录"]))
    lines.extend(separator)
    lines.extend(render_compact_field(prefix, "来源引用", [render_source_refs(case.get("sourceRefs", []))]))
    lines.append("")
    return lines


def render_design_scenario(scenario: dict[str, Any], depth: int) -> list[str]:
    scenario_level = 1 + depth
    lines = [heading(scenario_level, f"{scenario.get('id')} {scenario.get('title')}"), ""]
    lines.extend(render_solution_fields(scenario.get("fields", [])))
    lines.append("")
    children = scenario_children(scenario)
    if children:
        for child in children:
            lines.extend(render_design_scenario(child, depth + 1))
    else:
        point_level = scenario_level + 1
        case_level = point_level + 1
        for point in scenario.get("testPoints", []):
            lines.extend(render_test_point(point, point_level, table=True))
            for case in point.get("testCases", []):
                lines.extend(render_test_case(case, case_level))
    return lines


def render_design_solution(data: dict[str, Any]) -> str:
    lines = [f"# {data.get('title', '测试设计方案')}", "", "## 设计输入", ""]
    lines.extend(render_solution_fields(data.get("inputs", [])))
    lines.append("")
    for scenario in data.get("scenarios", []):
        if isinstance(scenario, dict):
            lines.extend(render_design_scenario(scenario, 1))
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
        (run_dir / "process" / "analysis-task-list.json", run_dir / "process" / "analysis-task-list.md"),
        (run_dir / "process" / "design-task-list.json", run_dir / "process" / "design-task-list.md"),
        (run_dir / "process" / "task-list.json", run_dir / "process" / "task-list.md"),
        (run_dir / "process" / "context-pack.json", run_dir / "process" / "context-pack.md"),
        (run_dir / "process" / "input-fact-model.json", run_dir / "process" / "input-fact-model.md"),
        (run_dir / "deliverables" / "test-analysis-solution.json", run_dir / "deliverables" / "test-analysis-solution.md"),
        (run_dir / "deliverables" / "test-design-solution.json", run_dir / "deliverables" / "test-design-solution.md"),
        (run_dir / "reports" / "test-analysis-solution-review.json", run_dir / "reports" / "test-analysis-solution-review.md"),
        (run_dir / "reports" / "test-design-solution-review.json", run_dir / "reports" / "test-design-solution-review.md"),
        (run_dir / "reports" / "analysis-coverage-review.json", run_dir / "reports" / "analysis-coverage-review.md"),
        (run_dir / "reports" / "design-coverage-review.json", run_dir / "reports" / "design-coverage-review.md"),
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
    return errors, warnings


def validate_context_pack_json(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    project_binding = data.get("projectBinding")
    if not isinstance(project_binding, dict):
        errors.append("context-pack.json 缺少对象字段: projectBinding")
    elif project_binding.get("status") not in {"resolved", "unresolved"}:
        errors.append("context-pack.json projectBinding.status 必须为 resolved 或 unresolved")

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
    tc_index = 1
    scenario_keys = {"id", "title", "fields", "children", "testPoints"}
    analysis_point_keys = {"id", "title", "objective", "basisRefs", "note"}
    design_point_keys = analysis_point_keys | {"testCases"}

    def walk(nodes: list[Any], parent_id: str = "", depth: int = 1) -> None:
        nonlocal tp_index, tc_index
        if depth > 3:
            errors.append(f"{parent_id or 'scenarios'} 超过 3 层 SC 深度")
            return
        for index, scenario in enumerate(nodes, start=1):
            if not isinstance(scenario, dict):
                errors.append(f"{parent_id or 'scenarios'}[{index}] 不是对象")
                continue
            expected_sc = f"{parent_id}-{index:03d}" if parent_id else f"SC-{index:03d}"
            scenario_id = normalize_text(scenario.get("id"))
            if scenario_id != expected_sc:
                errors.append(f"场景序号应为 {expected_sc}，实际为 {scenario.get('id')}")
            extra_scenario_keys = sorted(set(scenario) - scenario_keys)
            if extra_scenario_keys:
                errors.append(f"{scenario_id} 包含 schemaVersion 2.0 未定义字段: {', '.join(extra_scenario_keys)}")
            children = scenario.get("children", [])
            if children is None:
                children = []
            if not isinstance(children, list):
                errors.append(f"{scenario_id} children 必须是数组")
                children = []
            points = scenario.get("testPoints", [])
            if children:
                if points:
                    errors.append(f"{scenario_id} 是非叶子场景，不得挂载 testPoints")
                walk(children, scenario_id, depth + 1)
                continue
            if not isinstance(points, list) or not points:
                errors.append(f"{scenario_id} 是叶子场景，必须包含 testPoints")
                continue
            if not any(point.get("title") == "E2E场景测试" for point in points if isinstance(point, dict)):
                errors.append(f"{scenario_id} 缺少 E2E场景测试")
            for point in points:
                if not isinstance(point, dict):
                    errors.append(f"{scenario_id} testPoints 中存在非对象节点")
                    continue
                expected_tp = f"TP-{tp_index:03d}"
                point_id = normalize_text(point.get("id"))
                if point_id != expected_tp:
                    errors.append(f"测试点序号应为 {expected_tp}，实际为 {point.get('id')}")
                if not point.get("title") or not point.get("objective"):
                    errors.append(f"{point_id} 缺少 title 或 objective")
                if not is_design:
                    extra_point_keys = sorted(set(point) - analysis_point_keys)
                    if extra_point_keys:
                        errors.append(f"{point_id} 包含 schemaVersion 2.0 分析节点未定义字段: {', '.join(extra_point_keys)}")
                else:
                    extra_point_keys = sorted(set(point) - design_point_keys)
                    if extra_point_keys:
                        errors.append(f"{point_id} 包含 schemaVersion 2.0 设计节点未定义字段: {', '.join(extra_point_keys)}")
                    cases = point.get("testCases")
                    if not isinstance(cases, list) or not cases:
                        errors.append(f"{point_id} 缺少 testCases")
                    else:
                        tc_index = validate_test_cases(cases, tc_index, point_id, errors)
                tp_index += 1

    walk(scenarios)
    return errors, warnings


def action_signature(action: str) -> str:
    match = HTTP_ACTION_RE.search(action)
    if match:
        return f"{match.group(1)} {match.group(2)}"
    normalized = re.sub(r"[，,；;].*$", "", action).strip()
    normalized = re.sub(r"\b[A-Z][A-Z0-9_-]*\b", "<值>", normalized)
    normalized = re.sub(r"\d+", "<数>", normalized)
    normalized = re.sub(r"用户\s*[A-Za-z0-9一二三四五六七八九甲乙丙丁]+", "用户<值>", normalized)
    normalized = re.sub(r"角色\s*[A-Za-z0-9一二三四五六七八九甲乙丙丁]+", "角色<值>", normalized)
    normalized = re.sub(r"(开启|关闭|启用|禁用)[^，,；; ]*", "<配置取值>", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized[:40]


def is_variant_action(action: str) -> bool:
    if not ACTION_PREFIX_RE.search(action):
        return False
    return any(term in action for term in ACTION_VARIANT_TERMS)


def validate_atomic_test_case(case_id: str, steps: list[Any], errors: list[str]) -> None:
    variant_groups: dict[str, list[int]] = {}
    for index, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            continue
        action = normalize_text(step.get("action"))
        if not is_variant_action(action):
            continue
        signature = action_signature(action)
        if signature:
            variant_groups.setdefault(signature, []).append(index)
    for signature, indexes in variant_groups.items():
        if len(indexes) >= 2:
            step_list = ", ".join(str(index) for index in indexes)
            errors.append(
                f"{case_id} 疑似将多个独立输入条件/数据组合合并为一个 TC: "
                f"步骤 {step_list} 都在枚举 `{signature}` 的不同变体；应拆成多个 TC"
            )


def validate_test_cases(cases: Any, start_index: int, parent_id: str, errors: list[str]) -> int:
    case_keys = {"id", "title", "level", "preconditions", "testData", "steps", "expectedResult", "sourceRefs"}
    for case in cases:
        if not isinstance(case, dict):
            errors.append(f"{parent_id} testCases 中存在非对象节点")
            continue
        expected_id = f"TC-{start_index:03d}"
        case_id = normalize_text(case.get("id"))
        if case_id != expected_id:
            errors.append(f"测试用例序号应为 {expected_id}，实际为 {case.get('id')}")
        extra_case_keys = sorted(set(case) - case_keys)
        if extra_case_keys:
            errors.append(f"{case_id} 包含 schemaVersion 2.0 测试用例未定义字段: {', '.join(extra_case_keys)}")
        if not case.get("title") or not case.get("expectedResult"):
            errors.append(f"{case_id} 缺少 title 或 expectedResult")
        if case.get("level") not in TEST_CASE_LEVEL_VALUES:
            errors.append(f"{case_id} level 必须为 Level 0/Level 1/Level 2/Level 3/Level 4")
        preconditions = case.get("preconditions")
        if not isinstance(preconditions, list):
            errors.append(f"{case_id} preconditions 必须是数组")
        test_data = case.get("testData")
        if not isinstance(test_data, list) or not test_data:
            errors.append(f"{case_id} testData 必须是非空数组")
        else:
            for item_index, item in enumerate(test_data, start=1):
                if not isinstance(item, dict) or any(is_empty_value(item.get(key)) for key in ("name", "value", "description")):
                    errors.append(f"{case_id} testData[{item_index}] 必须包含 name/value/description")
        steps = case.get("steps")
        if not isinstance(steps, list) or not steps:
            errors.append(f"{case_id} steps 必须是非空数组")
        else:
            for step_index, step in enumerate(steps, start=1):
                if not isinstance(step, dict):
                    errors.append(f"{case_id} steps[{step_index}] 不是对象")
                    continue
                if step.get("stepNo") != step_index:
                    errors.append(f"{case_id} steps[{step_index}] stepNo 应为 {step_index}")
                if not step.get("action") or not step.get("expected"):
                    errors.append(f"{case_id} steps[{step_index}] 缺少 action 或 expected")
                action = normalize_text(step.get("action")).strip()
                if action.startswith(ASSERTION_ACTION_PREFIXES):
                    errors.append(
                        f"{case_id} steps[{step_index}].action 不应单独写检查项 `{action}`；"
                        "请把字段、状态、记录或事件检查要求写入同一步 expected"
                    )
            validate_atomic_test_case(case_id, steps, errors)
        source_refs = case.get("sourceRefs")
        if source_refs is not None and not isinstance(source_refs, list):
            errors.append(f"{case_id} sourceRefs 必须是数组")
        start_index += 1
    return start_index


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
    expected_schema_version = "2.0" if artifact_type in {"test-analysis-solution", "test-design-solution"} else "1.0"
    if data.get("schemaVersion") != expected_schema_version:
        errors.append(f"{artifact_type}.json schemaVersion 必须为 {expected_schema_version}")
    if artifact_type == "task-list":
        task_errors, task_warnings = validate_task_list(data)
        errors.extend(task_errors)
        warnings.extend(task_warnings)
    elif artifact_type in {"context-pack", "input-fact-model"}:
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
