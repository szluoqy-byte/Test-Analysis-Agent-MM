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
    "rules-pack": "强制规则索引",
    "context-pack": "上下文来源索引",
    "input-fact-model": "输入事实模型",
    "scenario-tree": "冻结 SC 场景树",
    "test-point-work-items": "测试点生成工作项索引",
    "test-point-slice": "测试点切片",
    "test-case-work-items": "测试用例生成工作项索引",
    "test-case-slice": "测试用例切片",
    "test-analysis-solution": "测试分析方案",
    "test-design-solution": "测试设计方案",
    "test-analysis-solution-review": "测试分析方案语义评审结果",
    "test-design-solution-review": "测试设计方案语义评审结果",
    "scenario-tree-review": "SC 场景树评审结果",
    "test-point-review": "测试点评审结果",
    "test-case-review": "测试用例评审结果",
    "coverage-review": "覆盖审查结果",
    "fact-coverage-map": "FACT 覆盖证据图",
    "final-report": "最终审阅报告",
}
GENERIC_METADATA_KEYS = {"artifactType", "alternateArtifactTypes", "schemaVersion", "title", "sections", "generationContext"}
ANALYSIS_REQUIRED_STAGES = [
    "固定 PROJECT_ROOT 与运行目录",
    "强制规则加载",
    "上下文来源索引",
    "输入事实建模",
    "测试技术路由",
    "专项分析",
    "按源补读",
    "测试分析方案生成",
    "确定性校验",
    "独立评审",
    "覆盖审查",
    "最终报告生成",
    "输出收口",
]
DESIGN_REQUIRED_STAGES = [
    "固定 PROJECT_ROOT 与运行目录",
    "测试分析方案校验",
    "强制规则加载",
    "上下文来源索引",
    "设计依据补读",
    "测试设计方案生成",
    "确定性校验",
    "独立评审",
    "覆盖审查",
    "最终报告生成",
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
SYSTEM_ACTION_ACTOR_RE = re.compile(
    r"^(?!系统管理员)"
    r"(?:MM系统|系统|平台|服务端|后端|后台|定时任务|批处理|数据库|消息队列|网关|核心系统|风控系统|第三方系统|下游系统)\s*"
    r"(?:判断|根据|校验|验证|检查|处理|执行|生成|创建|更新|写入|发送|返回|通知|计算|匹配|查询|读取|调用|取消|拒绝|受理|释放|记录|落库|推送|触发|同步|异步|扣减|回滚|补偿|提交|发起|展示|显示|保存|删除|拦截)"
)
HTTP_ACTION_RE = re.compile(r"\b(GET|POST|PUT|PATCH|DELETE)\s+(/[A-Za-z0-9_./{}:-]+)")
ANGLE_TOKEN_RE = re.compile(r"<(?!/?br\s*/?\s*>)([^<>\r\n]{1,120})>", re.IGNORECASE)
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


def sanitize_markdown_angle_tokens(text: str) -> str:
    return ANGLE_TOKEN_RE.sub(lambda match: "{" + match.group(1).strip() + "}", text)


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


def render_rules_pack(data: dict[str, Any]) -> str:
    if data.get("artifactType") != "rules-pack":
        return render_generic_document(data, "强制规则索引")

    lines = [f"# {artifact_title(data, '强制规则索引')}", ""]

    policy = data.get("priorityPolicy") if isinstance(data.get("priorityPolicy"), dict) else {}
    lines.extend(["## 优先级策略", ""])
    policy_rows = [[key, normalize_text(value)] for key, value in policy.items()]
    if policy_rows:
        lines.extend(markdown_table(["策略项", "说明"], policy_rows))
    else:
        lines.append("未声明优先级策略。")
    lines.append("")

    loading = data.get("loadingPolicy") if isinstance(data.get("loadingPolicy"), dict) else {}
    lines.extend(["## 加载策略", ""])
    loading_rows = [[key, normalize_text(value)] for key, value in loading.items()]
    if loading_rows:
        lines.extend(markdown_table(["策略项", "说明"], loading_rows))
    else:
        lines.append("未声明加载策略。")
    lines.append("")

    rows: list[list[str]] = []
    for rule in data.get("ruleSources", []):
        if not isinstance(rule, dict):
            continue
        stages = rule.get("availableStages", [])
        stage_text = "、".join(stages) if isinstance(stages, list) else normalize_text(stages)
        rows.append(
            [
                rule.get("layer", ""),
                rule.get("path", ""),
                rule.get("name", ""),
                rule.get("description", ""),
                stage_text,
                rule.get("availability", ""),
                "是" if rule.get("mandatory") is True else normalize_text(rule.get("mandatory")),
                rule.get("loadPolicy", ""),
            ]
        )
    lines.extend(["## 规则来源索引", ""])
    if rows:
        lines.extend(markdown_table(["层级", "路径", "名称", "描述", "可用阶段", "可见性", "强制", "加载策略"], rows))
    else:
        lines.append("无。")
    lines.append("")

    unscanned_rows: list[list[str]] = []
    for item in data.get("unscannedProjectRules", []):
        if isinstance(item, dict):
            unscanned_rows.append([item.get("path", ""), item.get("reason", "")])
        else:
            unscanned_rows.append([normalize_text(item), ""])
    lines.extend(["## 未扫描项目规则", ""])
    if unscanned_rows:
        lines.extend(markdown_table(["路径", "原因"], unscanned_rows))
    else:
        lines.append("无未扫描项目规则。")
    lines.append("")

    warning_rows = [[normalize_text(item)] for item in data.get("warnings", [])]
    lines.extend(["## 告警", ""])
    if warning_rows:
        lines.extend(markdown_table(["说明"], warning_rows))
    else:
        lines.append("无告警。")

    return "\n".join(lines).rstrip() + "\n"


def render_input_fact_model(data: dict[str, Any]) -> str:
    if data.get("sections"):
        fact_blocks = table_blocks_for_heading(data, "事实清单")
        if fact_blocks:
            return render_grouped_input_fact_model(data)
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


def table_blocks_for_heading(data: dict[str, Any], heading_keyword: str) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for section in data.get("sections", []):
        if not isinstance(section, dict) or heading_keyword not in normalize_text(section.get("heading")):
            continue
        for block in section.get("content", []):
            if isinstance(block, dict) and block.get("type") == "table":
                blocks.append(block)
    return blocks


def table_rows_as_dicts(block: dict[str, Any]) -> list[dict[str, str]]:
    columns = [normalize_text(column) for column in block.get("columns", [])]
    rows: list[dict[str, str]] = []
    for raw_row in block.get("rows", []):
        if not isinstance(raw_row, list):
            continue
        rows.append({columns[index]: normalize_text(raw_row[index]) for index in range(min(len(columns), len(raw_row)))})
    return rows


def input_source_lookup_from_model(data: dict[str, Any]) -> dict[str, dict[str, str]]:
    lookup: dict[str, dict[str, str]] = {}
    for block in table_blocks_for_heading(data, "输入来源"):
        for row in table_rows_as_dicts(block):
            source_type = row.get("来源类型") or row.get("类型") or ""
            if not source_type:
                continue
            lookup[source_type] = {
                "type": source_type,
                "source": row.get("文件/来源") or row.get("来源") or "未记录",
                "location": row.get("位置/章节") or row.get("范围") or "未记录",
                "description": row.get("说明") or "",
            }
    return lookup


def fact_input_source_from_row(row: dict[str, str], lookup: dict[str, dict[str, str]] | None = None) -> dict[str, str]:
    lookup = lookup or {}
    source_text = row.get("来源", "")
    source_type = row.get("来源类型", "")
    source_file = row.get("文件/来源", "")
    location = row.get("位置/章节", "")
    if not source_type and "：" in source_text:
        source_type, _, inferred_location = source_text.partition("：")
        location = location or inferred_location
    if not source_file and source_type in lookup:
        source_file = lookup[source_type].get("source", "")
    if not source_file:
        source_file = source_text if source_text and "：" not in source_text else ""
    if (not location or location == "未记录") and source_type in lookup:
        location = lookup[source_type].get("location", "")
    return {
        "type": source_type or "未记录",
        "source": source_file or "未记录",
        "location": location or "未记录",
        "description": source_text,
    }


def fact_rows_from_input_model(data: dict[str, Any]) -> list[dict[str, Any]]:
    facts: list[dict[str, Any]] = []
    source_lookup = input_source_lookup_from_model(data)
    for block in table_blocks_for_heading(data, "事实清单"):
        for row in table_rows_as_dicts(block):
            fact_id = row.get("事实ID", "")
            if not fact_id:
                continue
            facts.append(
                {
                    "factId": fact_id,
                    "inputSource": fact_input_source_from_row(row, source_lookup),
                    "factSummary": row.get("事实内容", ""),
                    "condition": row.get("约束/条件", ""),
                    "observableResult": row.get("可观察结果", ""),
                    "objectScope": row.get("对象/范围", ""),
                }
            )
    return facts


def render_grouped_input_fact_model(data: dict[str, Any]) -> str:
    lines = [f"# {artifact_title(data, '输入事实模型')}", ""]
    input_blocks = table_blocks_for_heading(data, "输入来源")
    if input_blocks:
        lines.extend(["## 1. 输入来源", ""])
        for block in input_blocks:
            lines.extend(markdown_table(block.get("columns", []), block.get("rows", [])))
            lines.append("")

    facts = fact_rows_from_input_model(data)
    lines.extend(["## 2. 事实清单", ""])
    if not facts:
        lines.append("- 无事实记录")
        lines.append("")
    else:
        grouped: dict[tuple[str, str], dict[str, list[dict[str, Any]]]] = {}
        for fact in facts:
            source = fact["inputSource"]
            source_key = (source.get("type", "未记录"), source.get("source", "未记录"))
            grouped.setdefault(source_key, {}).setdefault(source.get("location", "未记录"), []).append(fact)
        for (source_type, source), by_location in grouped.items():
            lines.extend([f"### {source_type}：{source}", ""])
            for location, location_facts in by_location.items():
                lines.extend([f"#### {location}", ""])
                rows = [
                    [
                        fact.get("factId", ""),
                        fact.get("objectScope", ""),
                        fact.get("factSummary", ""),
                        fact.get("condition", ""),
                        fact.get("observableResult", ""),
                    ]
                    for fact in location_facts
                ]
                lines.extend(markdown_table(["事实ID", "对象/范围", "事实内容", "约束/条件", "可观察结果"], rows))
                lines.append("")

    for keyword, title in (("需求-设计映射", "## 3. 需求-设计映射"), ("来源与应用说明", "## 4. 来源与应用说明")):
        blocks = table_blocks_for_heading(data, keyword)
        if not blocks:
            continue
        lines.extend([title, ""])
        for block in blocks:
            lines.extend(markdown_table(block.get("columns", []), block.get("rows", [])))
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_process_artifact(data: dict[str, Any]) -> str:
    artifact_type = normalize_text(data.get("artifactType"))
    return render_structured_sections(
        data,
        ARTIFACT_TITLES.get(artifact_type, artifact_type or "过程产物"),
        [
            "runDir",
            "scenarioTreeSource",
            "analysisSource",
            "workItemsSource",
            "scope",
            "scenarioPath",
            "leafScenarioId",
            "leafScenarioTitle",
            "testPoint",
            "scenario",
            "scenarios",
            "workItems",
            "instructions",
            "rulesApplications",
            "dynamicSourceApplications",
        ],
        {
            "runDir": "运行目录",
            "scenarioTreeSource": "场景树来源",
            "analysisSource": "分析方案来源",
            "workItemsSource": "工作项来源",
            "scope": "范围",
            "scenarioPath": "场景路径",
            "leafScenarioId": "叶子 SC",
            "leafScenarioTitle": "叶子 SC 标题",
            "testPoint": "测试点",
            "scenario": "场景切片",
            "scenarios": "场景树",
            "workItems": "工作项",
            "instructions": "填写约束",
            "rulesApplications": "Rules 应用记录",
            "dynamicSourceApplications": "动态来源应用记录",
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
    if data.get("targetArtifact"):
        lines.append(f"- targetArtifact：{data.get('targetArtifact')}")
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
    if data.get("coverageScope"):
        lines.append(f"- coverageScope：{data.get('coverageScope')}")
    if data.get("targetArtifact"):
        lines.append(f"- targetArtifact：{data.get('targetArtifact')}")
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


def final_report_input_source_key(item: dict[str, Any]) -> tuple[str, str, str]:
    input_source = item.get("inputSource") if isinstance(item.get("inputSource"), dict) else {}
    source_type = normalize_text(input_source.get("type") or "未记录")
    source = normalize_text(input_source.get("source") or "未记录")
    location = normalize_text(input_source.get("location") or "未记录")
    return source_type, source, location


def _solution_label_maps(source_path: Path | None) -> dict[str, dict[str, str]]:
    maps: dict[str, dict[str, str]] = {
        "scenario_paths": {},
        "test_points": {},
        "test_cases": {},
    }
    if source_path is None:
        return maps
    try:
        run_dir = source_path.resolve().parents[1]
    except IndexError:
        return maps
    solution_path = run_dir / "deliverables" / "test-design-solution.json"
    if not solution_path.exists():
        solution_path = run_dir / "deliverables" / "test-analysis-solution.json"
    if not solution_path.exists():
        return maps
    try:
        solution = load_json(solution_path)
    except Exception:
        return maps

    def walk_scenarios(scenarios: list[Any], parent_labels: list[str]) -> None:
        for scenario in scenarios:
            if not isinstance(scenario, dict):
                continue
            scenario_id = normalize_text(scenario.get("id"))
            title = normalize_text(scenario.get("title"))
            current_label = f"{scenario_id} {title}".strip()
            current_path = parent_labels + ([current_label] if current_label else [])
            if scenario_id:
                maps["scenario_paths"][scenario_id] = " > ".join(current_path) or scenario_id
            children = scenario.get("children")
            if isinstance(children, list) and children:
                walk_scenarios(children, current_path)
            for test_point in scenario.get("testPoints", []):
                if not isinstance(test_point, dict):
                    continue
                tp_id = normalize_text(test_point.get("id"))
                tp_title = normalize_text(test_point.get("title"))
                if tp_id:
                    maps["test_points"][tp_id] = f"{tp_id} {tp_title}".strip()
                for test_case in test_point.get("testCases", []):
                    if not isinstance(test_case, dict):
                        continue
                    tc_id = normalize_text(test_case.get("id"))
                    tc_title = normalize_text(test_case.get("title"))
                    if tc_id:
                        maps["test_cases"][tc_id] = f"{tc_id} {tc_title}".strip()

    scenarios = solution.get("scenarios")
    if isinstance(scenarios, list):
        walk_scenarios(scenarios, [])
    return maps


def _coverage_tree_lines(item: dict[str, Any], include_cases: bool, label_maps: dict[str, dict[str, str]]) -> list[str]:
    tree = item.get("coverageTree")
    if not isinstance(tree, list):
        return []
    lines: list[str] = []
    scenario_labels = label_maps.get("scenario_paths", {})
    tp_labels = label_maps.get("test_points", {})
    tc_labels = label_maps.get("test_cases", {})
    for scenario_ref in tree:
        if not isinstance(scenario_ref, dict):
            continue
        leaf_id = normalize_text(scenario_ref.get("leafScenarioId"))
        if not leaf_id:
            continue
        scenario_label = scenario_labels.get(leaf_id, leaf_id)
        test_points = scenario_ref.get("testPoints")
        if not isinstance(test_points, list) or not test_points:
            lines.append(scenario_label)
            continue
        for test_point_ref in test_points:
            if not isinstance(test_point_ref, dict):
                continue
            tp_id = normalize_text(test_point_ref.get("testPointId"))
            if not tp_id:
                continue
            tp_label = tp_labels.get(tp_id, tp_id)
            prefix = f"{scenario_label} / {tp_label}"
            test_cases = test_point_ref.get("testCases")
            case_ids = [normalize_text(value) for value in test_cases] if isinstance(test_cases, list) else []
            case_ids = [value for value in case_ids if value]
            if include_cases:
                if case_ids:
                    for tc_id in case_ids:
                        lines.append(f"{prefix} / {tc_labels.get(tc_id, tc_id)}")
                else:
                    lines.append(f"{prefix} / 未覆盖 TC")
            else:
                lines.append(prefix)
    return lines


def _append_unique(values: list[str], value: str) -> None:
    if value and value not in values:
        values.append(value)


def _coverage_tree_aggregates(
    item: dict[str, Any], include_cases: bool, label_maps: dict[str, dict[str, str]]
) -> list[str]:
    tree = item.get("coverageTree")
    if not isinstance(tree, list):
        return []
    scenarios: list[str] = []
    tp_values: list[str] = []
    tc_values: list[str] = []
    scenario_labels = label_maps.get("scenario_paths", {})
    tp_labels = label_maps.get("test_points", {})
    tc_labels = label_maps.get("test_cases", {})
    for scenario_ref in tree:
        if not isinstance(scenario_ref, dict):
            continue
        leaf_id = normalize_text(scenario_ref.get("leafScenarioId"))
        if not leaf_id:
            continue
        scenario_label = scenario_labels.get(leaf_id, leaf_id)
        _append_unique(scenarios, scenario_label)
        tp_refs = scenario_ref.get("testPoints")
        if not isinstance(tp_refs, list):
            continue
        for test_point_ref in tp_refs:
            if not isinstance(test_point_ref, dict):
                continue
            tp_id = normalize_text(test_point_ref.get("testPointId"))
            if not tp_id:
                continue
            tp_label = tp_labels.get(tp_id, tp_id)
            _append_unique(tp_values, tp_label)
            case_refs = test_point_ref.get("testCases")
            case_ids = [normalize_text(value) for value in case_refs] if isinstance(case_refs, list) else []
            case_ids = [value for value in case_ids if value]
            if include_cases:
                for tc_id in case_ids:
                    _append_unique(tc_values, tc_labels.get(tc_id, tc_id))
    aggregates = ["<br>".join(scenarios), "<br>".join(tp_values)]
    if include_cases:
        aggregates.append("<br>".join(tc_values))
    return aggregates


def render_final_report(data: dict[str, Any], source_path: Path | None = None) -> str:
    title = data.get("title") or "最终审阅报告"
    scope = normalize_text(data.get("reportScope") or "analysis")
    include_cases = scope == "design"
    label_maps = _solution_label_maps(source_path)
    lines = [f"# {title}", "", "## 1. 汇总", ""]
    summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
    summary_rows = [
        ["totalFacts", summary.get("totalFacts", 0)],
        ["coveredFacts", summary.get("coveredFacts", 0)],
        ["partialFacts", summary.get("partialFacts", 0)],
        ["missingFacts", summary.get("missingFacts", 0)],
        ["notApplicableFacts", summary.get("notApplicableFacts", 0)],
    ]
    lines.extend(markdown_table(["指标", "数量"], summary_rows))
    lines.append("")

    fact_coverage = data.get("factCoverage") if isinstance(data.get("factCoverage"), list) else []
    attention_rows: list[list[str]] = []
    for item in fact_coverage:
        if not isinstance(item, dict):
            continue
        status = normalize_text(item.get("coverageStatus"))
        if status == "covered":
            continue
        input_source = item.get("inputSource") if isinstance(item.get("inputSource"), dict) else {}
        attention_rows.append(
            [
                item.get("factId", ""),
                normalize_text(input_source.get("description") or ""),
                item.get("factSummary", ""),
                status,
                item.get("coverageReason", ""),
            ]
        )
    if attention_rows:
        lines.extend(["## 2. 需关注项", ""])
        lines.extend(markdown_table(["FACT", "输入来源", "事实内容", "覆盖状态", "原因"], attention_rows))
        lines.append("")
        detail_heading = "## 3. FACT 覆盖明细"
    else:
        detail_heading = "## 2. FACT 覆盖明细"

    lines.extend([detail_heading, ""])
    grouped: dict[tuple[str, str], dict[str, list[dict[str, Any]]]] = {}
    for item in fact_coverage:
        if not isinstance(item, dict):
            continue
        source_type, source, location = final_report_input_source_key(item)
        grouped.setdefault((source_type, source), {}).setdefault(location, []).append(item)

    if not grouped:
        lines.append("无 FACT 覆盖记录。")
        return "\n".join(lines).rstrip() + "\n"

    for (source_type, source), by_location in grouped.items():
        lines.extend([f"### {source_type}：{source}", ""])
        for location, items in by_location.items():
            lines.extend([f"#### {location}", ""])
            coverage_columns = ["覆盖SC", "覆盖TP", "覆盖TC"] if include_cases else ["覆盖SC", "覆盖TP"]
            columns = ["FACT", "输入来源", "事实内容", "约束/条件", "可观察结果", *coverage_columns, "覆盖状态"]
            rows: list[list[str]] = []
            for item in items:
                input_source = item.get("inputSource") if isinstance(item.get("inputSource"), dict) else {}
                source_desc = normalize_text(input_source.get("description") or "")
                status = normalize_text(item.get("coverageStatus"))
                empty_links = "不适用" if status == "not_applicable" else "未覆盖"
                coverage_columns = _coverage_tree_aggregates(item, include_cases, label_maps)
                if not any(coverage_columns):
                    coverage_columns = [empty_links, ""] if not include_cases else [empty_links, "", ""]
                rows.append(
                    [
                    item.get("factId", ""),
                    source_desc or f"{source_type} / {source} / {location}",
                    item.get("factSummary", ""),
                    item.get("condition", ""),
                    item.get("observableResult", ""),
                    *coverage_columns,
                    item.get("coverageStatus", ""),
                    ]
                )
            lines.extend(markdown_table(columns, rows))
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_fact_coverage_map(data: dict[str, Any], source_path: Path | None = None) -> str:
    title = data.get("title") or "FACT 覆盖证据图"
    scope = normalize_text(data.get("coverageScope") or "analysis")
    include_cases = scope == "design"
    label_maps = _solution_label_maps(source_path)
    lines = [f"# {title}", "", "## 1. 汇总", ""]
    summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
    summary_rows = [
        ["totalFacts", summary.get("totalFacts", 0)],
        ["coveredFacts", summary.get("coveredFacts", 0)],
        ["partialFacts", summary.get("partialFacts", 0)],
        ["gapFacts", summary.get("gapFacts", 0)],
        ["notApplicableFacts", summary.get("notApplicableFacts", 0)],
    ]
    lines.extend(markdown_table(["指标", "数量"], summary_rows))
    lines.append("")

    fact_coverage = data.get("factCoverage") if isinstance(data.get("factCoverage"), list) else []
    gap_rows: list[list[str]] = []
    for item in fact_coverage:
        if not isinstance(item, dict):
            continue
        status = normalize_text(item.get("coverageStatus"))
        if status not in {"partial", "gap"}:
            continue
        input_source = item.get("inputSource") if isinstance(item.get("inputSource"), dict) else {}
        gap_rows.append(
            [
                item.get("factId", ""),
                normalize_text(input_source.get("description") or ""),
                item.get("factSummary", ""),
                status,
                item.get("coverageReason", ""),
            ]
        )
    if gap_rows:
        lines.extend(["## 2. 门禁关注项", ""])
        lines.extend(markdown_table(["FACT", "输入来源", "事实内容", "覆盖状态", "原因"], gap_rows))
        lines.append("")
        detail_heading = "## 3. FACT 覆盖证据"
    else:
        detail_heading = "## 2. FACT 覆盖证据"

    lines.extend([detail_heading, ""])
    grouped: dict[tuple[str, str], dict[str, list[dict[str, Any]]]] = {}
    for item in fact_coverage:
        if not isinstance(item, dict):
            continue
        source_type, source, location = final_report_input_source_key(item)
        grouped.setdefault((source_type, source), {}).setdefault(location, []).append(item)

    if not grouped:
        lines.append("无 FACT 覆盖证据记录。")
        return "\n".join(lines).rstrip() + "\n"

    for (source_type, source), by_location in grouped.items():
        lines.extend([f"### {source_type}：{source}", ""])
        for location, items in by_location.items():
            lines.extend([f"#### {location}", ""])
            rows: list[list[str]] = []
            for item in items:
                input_source = item.get("inputSource") if isinstance(item.get("inputSource"), dict) else {}
                source_desc = normalize_text(input_source.get("description") or "")
                link_lines = _coverage_tree_lines(item, include_cases, label_maps)
                status = normalize_text(item.get("coverageStatus"))
                empty_links = "不适用" if status == "not_applicable" else "无覆盖证据"
                rows.append(
                    [
                        item.get("factId", ""),
                        source_desc or f"{source_type} / {source} / {location}",
                        item.get("factSummary", ""),
                        item.get("condition", ""),
                        item.get("observableResult", ""),
                        "<br>".join(link_lines) if link_lines else empty_links,
                        status,
                        item.get("coverageReason", ""),
                    ]
                )
            lines.extend(markdown_table(["FACT", "输入来源", "事实内容", "约束/条件", "可观察结果", "覆盖证据链路", "覆盖状态", "原因"], rows))
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


RENDERERS = {
    "task-list": render_task_list,
    "rules-pack": render_rules_pack,
    "context-pack": render_context_pack,
    "input-fact-model": render_input_fact_model,
    "scenario-tree": render_process_artifact,
    "test-point-work-items": render_process_artifact,
    "test-point-slice": render_process_artifact,
    "test-case-work-items": render_process_artifact,
    "test-case-slice": render_process_artifact,
    "test-analysis-solution": render_analysis_solution,
    "test-design-solution": render_design_solution,
    "test-analysis-solution-review": render_review_report,
    "test-design-solution-review": render_review_report,
    "scenario-tree-review": render_review_report,
    "test-point-review": render_review_report,
    "test-case-review": render_review_report,
    "coverage-review": render_coverage_report,
    "fact-coverage-map": render_fact_coverage_map,
    "final-report": render_final_report,
}


def render_json_artifact(data: dict[str, Any], source_path: Path | None = None) -> str:
    artifact_type = data.get("artifactType")
    if artifact_type == "final-report":
        return sanitize_markdown_angle_tokens(render_final_report(data, source_path))
    if artifact_type == "fact-coverage-map":
        return sanitize_markdown_angle_tokens(render_fact_coverage_map(data, source_path))
    renderer = RENDERERS.get(artifact_type)
    if renderer is None:
        raise ValueError(f"unsupported artifactType: {artifact_type}")
    return sanitize_markdown_angle_tokens(renderer(data))


def collect_renderable_json_files(run_dir: Path) -> list[tuple[Path, Path]]:
    pairs = [
        (run_dir / "process" / "analysis-task-list.json", run_dir / "process" / "analysis-task-list.md"),
        (run_dir / "process" / "design-task-list.json", run_dir / "process" / "design-task-list.md"),
        (run_dir / "process" / "task-list.json", run_dir / "process" / "task-list.md"),
        (run_dir / "process" / "rules-pack.json", run_dir / "process" / "rules-pack.md"),
        (run_dir / "process" / "context-pack.json", run_dir / "process" / "context-pack.md"),
        (run_dir / "process" / "input-fact-model.json", run_dir / "process" / "input-fact-model.md"),
        (run_dir / "process" / "scenario-tree.json", run_dir / "process" / "scenario-tree.md"),
        (run_dir / "process" / "test-point-work-items.json", run_dir / "process" / "test-point-work-items.md"),
        (run_dir / "process" / "test-case-work-items.json", run_dir / "process" / "test-case-work-items.md"),
        (run_dir / "process" / "analysis-fact-coverage-map.json", run_dir / "process" / "analysis-fact-coverage-map.md"),
        (run_dir / "process" / "design-fact-coverage-map.json", run_dir / "process" / "design-fact-coverage-map.md"),
        (run_dir / "deliverables" / "test-analysis-solution.json", run_dir / "deliverables" / "test-analysis-solution.md"),
        (run_dir / "deliverables" / "test-design-solution.json", run_dir / "deliverables" / "test-design-solution.md"),
        (run_dir / "process" / "reviews" / "scenario-tree-review.json", run_dir / "process" / "reviews" / "scenario-tree-review.md"),
        (run_dir / "process" / "reviews" / "test-point-review.json", run_dir / "process" / "reviews" / "test-point-review.md"),
        (run_dir / "process" / "reviews" / "test-case-review.json", run_dir / "process" / "reviews" / "test-case-review.md"),
        (
            run_dir / "process" / "reviews" / "test-analysis-solution-review.json",
            run_dir / "process" / "reviews" / "test-analysis-solution-review.md",
        ),
        (
            run_dir / "process" / "reviews" / "test-design-solution-review.json",
            run_dir / "process" / "reviews" / "test-design-solution-review.md",
        ),
        (run_dir / "process" / "reviews" / "analysis-coverage-review.json", run_dir / "process" / "reviews" / "analysis-coverage-review.md"),
        (run_dir / "process" / "reviews" / "design-coverage-review.json", run_dir / "process" / "reviews" / "design-coverage-review.md"),
        (run_dir / "process" / "reviews" / "coverage-review.json", run_dir / "process" / "reviews" / "coverage-review.md"),
        (run_dir / "reports" / "analysis-final-report.json", run_dir / "reports" / "analysis-final-report.md"),
        (run_dir / "reports" / "design-final-report.json", run_dir / "reports" / "design-final-report.md"),
    ]
    for directory in (
        run_dir / "process" / "test-point-slices",
        run_dir / "process" / "test-case-slices",
    ):
        if directory.is_dir():
            for json_path in sorted(directory.glob("*.json")):
                pairs.append((json_path, json_path.with_suffix(".md")))
    for directory in (
        run_dir / "process" / "reviews" / "test-point-reviews",
        run_dir / "process" / "reviews" / "test-case-reviews",
    ):
        if directory.is_dir():
            for json_path in sorted(directory.glob("*.json")):
                pairs.append((json_path, json_path.with_suffix(".md")))
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


def validate_rules_pack_json(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(data.get("priorityPolicy"), dict):
        errors.append("rules-pack.json 缺少对象字段: priorityPolicy")
    if not isinstance(data.get("loadingPolicy"), dict):
        errors.append("rules-pack.json 缺少对象字段: loadingPolicy")
    rules = data.get("ruleSources")
    if not isinstance(rules, list):
        errors.append("rules-pack.json 缺少数组字段: ruleSources")
        rules = []
    for index, rule in enumerate(rules, start=1):
        if not isinstance(rule, dict):
            errors.append(f"rules-pack.json ruleSources[{index}] 必须是对象")
            continue
        for required in (
            "path",
            "layer",
            "name",
            "description",
            "availableStages",
            "availability",
            "mandatory",
            "loadPolicy",
        ):
            if is_empty_value(rule.get(required)):
                errors.append(f"rules-pack.json ruleSources[{index}] 缺少字段: {required}")
        if rule.get("mandatory") is not True:
            errors.append(f"rules-pack.json ruleSources[{index}].mandatory 必须为 true")
        if rule.get("loadPolicy") != "stage_required":
            errors.append(f"rules-pack.json ruleSources[{index}].loadPolicy 必须为 stage_required")
        if "content" in rule:
            errors.append(f"rules-pack.json ruleSources[{index}] 不得内联 content，后续阶段按 path 读取规则正文")
        if rule.get("layer") not in {"core", "project", "user"}:
            errors.append(f"rules-pack.json ruleSources[{index}].layer 必须为 core/project/user")
        stages = rule.get("availableStages")
        if not isinstance(stages, list) or not all(isinstance(stage, str) and stage for stage in stages):
            errors.append(f"rules-pack.json ruleSources[{index}].availableStages 必须是非空字符串数组")
        path = normalize_text(rule.get("path")).replace("\\", "/")
        if re.match(r"^[A-Za-z]:/", path) or path.startswith("/"):
            errors.append(f"rules-pack.json ruleSources[{index}].path 必须是仓库相对路径")
        if path and not path.startswith("rules/"):
            errors.append(f"rules-pack.json ruleSources[{index}].path 必须位于 rules/ 目录: {path}")
    if "unscannedProjectRules" in data and not isinstance(data.get("unscannedProjectRules"), list):
        errors.append("rules-pack.json unscannedProjectRules 必须是数组")
    if "warnings" in data and not isinstance(data.get("warnings"), list):
        errors.append("rules-pack.json warnings 必须是数组")
    return errors


def validate_scenario_tree_json(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(data.get("scope", []), list):
        errors.append("scenario-tree.json scope 必须是数组")
    scenarios = data.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        errors.append("scenario-tree.json scenarios 必须是非空数组")
        return errors

    def walk(nodes: list[Any], parent_id: str = "", depth: int = 1) -> None:
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
            if not scenario.get("title"):
                errors.append(f"{scenario_id or expected_sc} 缺少 title")
            extra_keys = sorted(set(scenario) - {"id", "title", "fields", "children"})
            if extra_keys:
                errors.append(f"{scenario_id or expected_sc} 包含 scenario-tree 未定义字段: {', '.join(extra_keys)}")
            if "testPoints" in scenario:
                errors.append(f"{scenario_id or expected_sc} 在 scenario-tree 阶段不得包含 testPoints")
            children = scenario.get("children", [])
            if children is None:
                children = []
            if not isinstance(children, list):
                errors.append(f"{scenario_id or expected_sc} children 必须是数组")
                continue
            if children:
                walk(children, scenario_id, depth + 1)

    walk(scenarios)
    return errors


def validate_work_items_json(data: dict[str, Any], id_key: str, label: str) -> list[str]:
    errors: list[str] = []
    items = data.get("workItems")
    if not isinstance(items, list):
        errors.append(f"{label} workItems 必须是数组")
        return errors
    seen: set[str] = set()
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            errors.append(f"{label} workItems[{index}] 不是对象")
            continue
        item_id = normalize_text(item.get(id_key))
        if not item_id:
            errors.append(f"{label} workItems[{index}] 缺少 {id_key}")
        elif item_id in seen:
            errors.append(f"{label} workItems[{index}] {id_key} 重复: {item_id}")
        seen.add(item_id)
        if item.get("status") not in STATUS_VALUES:
            errors.append(f"{label} workItems[{index}].status 非法: {item.get('status')}")
        if not isinstance(item.get("scenarioPath", []), list):
            errors.append(f"{label} workItems[{index}].scenarioPath 必须是数组")
    return errors


def validate_test_point_slice_json(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    leaf_id = normalize_text(data.get("leafScenarioId"))
    scenario = data.get("scenario")
    if not leaf_id:
        errors.append("test-point-slice 缺少 leafScenarioId")
    if not isinstance(scenario, dict):
        errors.append("test-point-slice 缺少 scenario 对象")
        return errors
    if scenario.get("id") != leaf_id:
        errors.append("test-point-slice scenario.id 必须等于 leafScenarioId")
    if scenario.get("children") not in ([], None):
        errors.append(f"{leaf_id} 是叶子 SC 切片，不得包含 children")
    points = scenario.get("testPoints")
    if points is not None:
        if not isinstance(points, list):
            errors.append("test-point-slice scenario.testPoints 必须是数组")
        else:
            for index, point in enumerate(points, start=1):
                if not isinstance(point, dict):
                    errors.append(f"test-point-slice testPoints[{index}] 不是对象")
                    continue
                extra = sorted(set(point) - {"id", "title", "objective", "basisRefs", "note"})
                if extra:
                    errors.append(f"test-point-slice testPoints[{index}] 包含未定义字段: {', '.join(extra)}")
                if not point.get("title") or not point.get("objective"):
                    errors.append(f"test-point-slice testPoints[{index}] 缺少 title 或 objective")
                if "basisRefs" in point and not isinstance(point.get("basisRefs"), list):
                    errors.append(f"test-point-slice testPoints[{index}].basisRefs 必须是数组")
    return errors


def validate_test_case_slice_json(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    point = data.get("testPoint")
    if not isinstance(point, dict):
        return ["test-case-slice 缺少 testPoint 对象"]
    if not point.get("id"):
        errors.append("test-case-slice testPoint 缺少 id")
    cases = point.get("testCases")
    if cases is not None:
        if not isinstance(cases, list):
            errors.append("test-case-slice testPoint.testCases 必须是数组")
        else:
            for index, case in enumerate(cases, start=1):
                if not isinstance(case, dict):
                    errors.append(f"test-case-slice testCases[{index}] 不是对象")
                    continue
                extra_keys = sorted(
                    set(case)
                    - {"id", "title", "level", "preconditions", "testData", "steps", "expectedResult", "sourceRefs"}
                )
                if extra_keys:
                    errors.append(f"test-case-slice testCases[{index}] 包含未定义字段: {', '.join(extra_keys)}")
                if case.get("id") and not re.fullmatch(r"TC-\d{3}", normalize_text(case.get("id"))):
                    errors.append(f"test-case-slice testCases[{index}].id 不是合法 TC 编号")
                if case.get("level") not in TEST_CASE_LEVEL_VALUES:
                    errors.append(f"test-case-slice testCases[{index}].level 必须为 Level 0 到 Level 4")
                for key in ("title", "preconditions", "testData", "steps", "expectedResult", "sourceRefs"):
                    if key not in case:
                        errors.append(f"test-case-slice testCases[{index}] 缺少字段: {key}")
    return errors


def validate_generation_context(data: dict[str, Any], artifact_type: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    context = data.get("generationContext")
    required_artifacts = {
        "scenario-tree",
        "test-point-slice",
        "test-case-slice",
        "scenario-tree-review",
        "test-point-review",
        "test-case-review",
        "test-analysis-solution-review",
        "test-design-solution-review",
        "coverage-review",
    }
    if context is None:
        if artifact_type in required_artifacts:
            errors.append(f"{artifact_type}.json 缺少 generationContext")
        return errors, warnings
    if not isinstance(context, dict):
        return [f"{artifact_type}.json generationContext 必须是对象"], warnings
    required_keys = (
        "stage",
        "targetType",
        "targetId",
        "inputArtifacts",
        "applicableRules",
        "visibleSources",
        "relevantFacts",
        "constraints",
        "readPlan",
    )
    for key in required_keys:
        if key not in context:
            errors.append(f"{artifact_type}.json generationContext 缺少字段: {key}")
    for key in ("inputArtifacts", "applicableRules", "visibleSources", "relevantFacts", "constraints", "readPlan"):
        if key in context and not isinstance(context.get(key), list):
            errors.append(f"{artifact_type}.json generationContext.{key} 必须是数组")
    for index, rule in enumerate(context.get("applicableRules", []), start=1):
        if not isinstance(rule, dict):
            errors.append(f"{artifact_type}.json generationContext.applicableRules[{index}] 必须是对象")
            continue
        for key in ("path", "name", "description", "content"):
            if key not in rule:
                errors.append(f"{artifact_type}.json generationContext.applicableRules[{index}] 缺少 {key}")
        if not rule.get("content"):
            warnings.append(f"{artifact_type}.json generationContext.applicableRules[{index}] 未内联规则正文")
    for index, source in enumerate(context.get("visibleSources", []), start=1):
        if not isinstance(source, dict):
            errors.append(f"{artifact_type}.json generationContext.visibleSources[{index}] 必须是对象")
            continue
        for key in ("path", "name", "description", "availableStages"):
            if key not in source:
                errors.append(f"{artifact_type}.json generationContext.visibleSources[{index}] 缺少 {key}")
    return errors, warnings


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


def validate_executable_step_action(case_id: str, step_index: int, action: str, errors: list[str]) -> None:
    if action.startswith(ASSERTION_ACTION_PREFIXES):
        errors.append(
            f"{case_id} steps[{step_index}].action 不应单独写检查项 `{action}`；"
            "请把字段、状态、记录或事件检查要求写入同一步 expected"
        )
    if SYSTEM_ACTION_ACTOR_RE.search(action):
        errors.append(
            f"{case_id} steps[{step_index}].action 不应写系统行为 `{action}`；"
            "action 只写用户、测试人员、外部调用方可执行的操作或取数动作，系统判断、处理、返回、取消、释放等写入 expected"
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
                validate_executable_step_action(case_id, step_index, action, errors)
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
    blocking_issues = data.get("blockingIssues", [])
    findings = data.get("findings", [])
    has_blocking = bool(blocking_issues) or any(
        isinstance(item, dict) and item.get("severity") == "blocking"
        for item in findings
        if isinstance(findings, list)
    )
    if result == "通过" and has_blocking:
        errors.append("review/coverage JSON result 为通过时不得包含 blocking issue 或 blocking finding")
    if result in {"失败", "需修正"} and not has_blocking and data.get("artifactType") != "coverage-review":
        warnings.append("review JSON result 为失败/需修正但没有 blocking issue")
    if "targetArtifact" in data and not isinstance(data.get("targetArtifact"), str):
        errors.append("review/coverage JSON targetArtifact 必须是字符串")
    if data.get("artifactType") == "coverage-review":
        for key in ("qualityGates", "rulesApplications", "projectKnowledgeApplications", "coverageGaps"):
            if key not in data:
                warnings.append(f"coverage-review 缺少 {key}")
            elif not isinstance(data.get(key), list):
                errors.append(f"coverage-review 的 {key} 必须是数组")
        for index, gap in enumerate(data.get("coverageGaps", []), start=1):
            if not isinstance(gap, dict):
                errors.append(f"coverage-review coverageGaps[{index}] 必须是对象")
                continue
            for key in ("id", "requirementRef", "artifactLocation", "description", "suggestedFix"):
                if not gap.get(key):
                    errors.append(f"coverage-review coverageGaps[{index}] 缺少 {key}")
            location = normalize_text(gap.get("artifactLocation")).replace("\\", "/")
            if location and not (
                location.startswith("process/test-point-slices/") or location.startswith("process/test-case-slices/")
            ):
                errors.append(
                    f"coverage-review coverageGaps[{index}].artifactLocation 必须指向 process/test-point-slices/ 或 process/test-case-slices/: {location}"
                )
    return errors, warnings


def validate_final_report_json(data: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if data.get("reportScope") not in {"analysis", "design"}:
        errors.append("final-report reportScope 必须为 analysis 或 design")
    summary = data.get("summary")
    if not isinstance(summary, dict):
        errors.append("final-report 缺少 summary 对象")
    else:
        for key in ("totalFacts", "coveredFacts", "partialFacts", "missingFacts", "notApplicableFacts"):
            if key not in summary:
                errors.append(f"final-report summary 缺少 {key}")
            elif not isinstance(summary.get(key), int):
                errors.append(f"final-report summary.{key} 必须是整数")
    fact_coverage = data.get("factCoverage")
    if not isinstance(fact_coverage, list):
        return errors + ["final-report factCoverage 必须是数组"], warnings
    status_values = {"covered", "partial", "missing", "not_applicable"}
    seen_fact_ids: set[str] = set()
    for index, item in enumerate(fact_coverage, start=1):
        if not isinstance(item, dict):
            errors.append(f"final-report factCoverage[{index}] 必须是对象")
            continue
        fact_id = normalize_text(item.get("factId"))
        if not re.fullmatch(r"FACT-\d{3}", fact_id):
            errors.append(f"final-report factCoverage[{index}].factId 不是合法 FACT 编号")
        if fact_id in seen_fact_ids:
            errors.append(f"final-report factCoverage 重复 FACT: {fact_id}")
        seen_fact_ids.add(fact_id)
        input_source = item.get("inputSource")
        if not isinstance(input_source, dict):
            errors.append(f"final-report {fact_id or index} inputSource 必须是对象")
        else:
            for key in ("type", "source", "location", "description"):
                if key not in input_source:
                    errors.append(f"final-report {fact_id or index} inputSource 缺少 {key}")
        for key in ("factSummary", "condition", "observableResult", "coverageStatus", "coverageTree", "coverageReason"):
            if key not in item:
                errors.append(f"final-report {fact_id or index} 缺少 {key}")
        for legacy_key in ("coveredScenarios", "coveredTestPoints", "coveredTestCases", "reviewNote"):
            if legacy_key in item:
                errors.append(f"final-report {fact_id or index} 不再允许旧字段 {legacy_key}，请使用 coverageTree/coverageReason")
        coverage_tree = item.get("coverageTree")
        if not isinstance(coverage_tree, list):
            errors.append(f"final-report {fact_id or index} coverageTree 必须是数组")
            coverage_tree = []
        link_count = 0
        case_count = 0
        for tree_index, scenario_ref in enumerate(coverage_tree, start=1):
            if not isinstance(scenario_ref, dict):
                errors.append(f"final-report {fact_id or index} coverageTree[{tree_index}] 必须是对象")
                continue
            leaf_scenario_id = normalize_text(scenario_ref.get("leafScenarioId"))
            if not re.fullmatch(r"SC-\d{3}(?:-\d{3}){0,2}", leaf_scenario_id):
                errors.append(f"final-report {fact_id or index} coverageTree[{tree_index}].leafScenarioId 不是合法叶子 SC 编号")
            test_points = scenario_ref.get("testPoints")
            if not isinstance(test_points, list):
                errors.append(f"final-report {fact_id or index} coverageTree[{tree_index}].testPoints 必须是数组")
                continue
            if not test_points:
                errors.append(f"final-report {fact_id or index} coverageTree[{tree_index}].testPoints 不能为空")
            for tp_index, test_point_ref in enumerate(test_points, start=1):
                if not isinstance(test_point_ref, dict):
                    errors.append(f"final-report {fact_id or index} coverageTree[{tree_index}].testPoints[{tp_index}] 必须是对象")
                    continue
                test_point_id = normalize_text(test_point_ref.get("testPointId"))
                if not re.fullmatch(r"TP-\d{3}", test_point_id):
                    errors.append(
                        f"final-report {fact_id or index} coverageTree[{tree_index}].testPoints[{tp_index}].testPointId 不是合法 TP 编号"
                    )
                test_cases = test_point_ref.get("testCases")
                if not isinstance(test_cases, list):
                    errors.append(f"final-report {fact_id or index} coverageTree[{tree_index}].testPoints[{tp_index}].testCases 必须是数组")
                    continue
                link_count += 1
                normalized_cases = [normalize_text(value) for value in test_cases if normalize_text(value)]
                case_count += len(normalized_cases)
                for tc_id in normalized_cases:
                    if not re.fullmatch(r"TC-\d{3}", tc_id):
                        errors.append(f"final-report {fact_id or index} testCases 包含非法 TC 编号: {tc_id}")
        status = item.get("coverageStatus")
        if status not in status_values:
            errors.append(f"final-report {fact_id or index} coverageStatus 非法: {status}")
        reason = normalize_text(item.get("coverageReason"))
        if status == "covered":
            if link_count == 0:
                errors.append(f"final-report {fact_id or index} coverageStatus=covered 时 coverageTree 必须至少包含一条 SC/TP 链路")
            if data.get("reportScope") == "design" and case_count == 0:
                errors.append(f"final-report {fact_id or index} reportScope=design 且 covered 时必须至少包含一个 TC")
        elif status in {"partial", "missing", "not_applicable"}:
            if not reason or "待最终审阅" in reason:
                errors.append(f"final-report {fact_id or index} coverageStatus={status} 时 coverageReason 必须填写明确原因")
            if status in {"missing", "not_applicable"} and link_count:
                errors.append(f"final-report {fact_id or index} coverageStatus={status} 时 coverageTree 必须为空")
    if isinstance(summary, dict) and isinstance(fact_coverage, list):
        total = len(fact_coverage)
        counted = {
            "totalFacts": total,
            "coveredFacts": sum(1 for item in fact_coverage if isinstance(item, dict) and item.get("coverageStatus") == "covered"),
            "partialFacts": sum(1 for item in fact_coverage if isinstance(item, dict) and item.get("coverageStatus") == "partial"),
            "missingFacts": sum(1 for item in fact_coverage if isinstance(item, dict) and item.get("coverageStatus") == "missing"),
            "notApplicableFacts": sum(1 for item in fact_coverage if isinstance(item, dict) and item.get("coverageStatus") == "not_applicable"),
        }
        for key, expected in counted.items():
            if summary.get(key) != expected:
                errors.append(f"final-report summary.{key} 应为 {expected}，实际为 {summary.get(key)}")
    if not fact_coverage:
        warnings.append("final-report factCoverage 为空")
    return errors, warnings


def validate_fact_coverage_map_json(data: dict[str, Any]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if data.get("coverageScope") not in {"analysis", "design"}:
        errors.append("fact-coverage-map coverageScope 必须为 analysis 或 design")
    summary = data.get("summary")
    if not isinstance(summary, dict):
        errors.append("fact-coverage-map 缺少 summary 对象")
    else:
        for key in ("totalFacts", "coveredFacts", "partialFacts", "gapFacts", "notApplicableFacts"):
            if key not in summary:
                errors.append(f"fact-coverage-map summary 缺少 {key}")
            elif not isinstance(summary.get(key), int):
                errors.append(f"fact-coverage-map summary.{key} 必须是整数")
    fact_coverage = data.get("factCoverage")
    if not isinstance(fact_coverage, list):
        return errors + ["fact-coverage-map factCoverage 必须是数组"], warnings
    status_values = {"covered", "partial", "gap", "not_applicable"}
    seen_fact_ids: set[str] = set()
    for index, item in enumerate(fact_coverage, start=1):
        if not isinstance(item, dict):
            errors.append(f"fact-coverage-map factCoverage[{index}] 必须是对象")
            continue
        fact_id = normalize_text(item.get("factId"))
        if not re.fullmatch(r"FACT-\d{3}", fact_id):
            errors.append(f"fact-coverage-map factCoverage[{index}].factId 不是合法 FACT 编号")
        if fact_id in seen_fact_ids:
            errors.append(f"fact-coverage-map 重复 FACT: {fact_id}")
        seen_fact_ids.add(fact_id)
        input_source = item.get("inputSource")
        if not isinstance(input_source, dict):
            errors.append(f"fact-coverage-map {fact_id or index} inputSource 必须是对象")
        else:
            for key in ("type", "source", "location", "description"):
                if key not in input_source:
                    errors.append(f"fact-coverage-map {fact_id or index} inputSource 缺少 {key}")
        for key in ("factSummary", "condition", "observableResult", "coverageStatus", "coverageTree", "coverageReason"):
            if key not in item:
                errors.append(f"fact-coverage-map {fact_id or index} 缺少 {key}")
        coverage_tree = item.get("coverageTree")
        if not isinstance(coverage_tree, list):
            errors.append(f"fact-coverage-map {fact_id or index} coverageTree 必须是数组")
            coverage_tree = []
        link_count = 0
        case_count = 0
        for tree_index, scenario_ref in enumerate(coverage_tree, start=1):
            if not isinstance(scenario_ref, dict):
                errors.append(f"fact-coverage-map {fact_id or index} coverageTree[{tree_index}] 必须是对象")
                continue
            leaf_scenario_id = normalize_text(scenario_ref.get("leafScenarioId"))
            if not re.fullmatch(r"SC-\d{3}(?:-\d{3}){0,2}", leaf_scenario_id):
                errors.append(f"fact-coverage-map {fact_id or index} coverageTree[{tree_index}].leafScenarioId 不是合法叶子 SC 编号")
            test_points = scenario_ref.get("testPoints")
            if not isinstance(test_points, list):
                errors.append(f"fact-coverage-map {fact_id or index} coverageTree[{tree_index}].testPoints 必须是数组")
                continue
            if not test_points:
                errors.append(f"fact-coverage-map {fact_id or index} coverageTree[{tree_index}].testPoints 不能为空")
            for tp_index, test_point_ref in enumerate(test_points, start=1):
                if not isinstance(test_point_ref, dict):
                    errors.append(f"fact-coverage-map {fact_id or index} coverageTree[{tree_index}].testPoints[{tp_index}] 必须是对象")
                    continue
                test_point_id = normalize_text(test_point_ref.get("testPointId"))
                if not re.fullmatch(r"TP-\d{3}", test_point_id):
                    errors.append(
                        f"fact-coverage-map {fact_id or index} coverageTree[{tree_index}].testPoints[{tp_index}].testPointId 不是合法 TP 编号"
                    )
                test_cases = test_point_ref.get("testCases")
                if not isinstance(test_cases, list):
                    errors.append(f"fact-coverage-map {fact_id or index} coverageTree[{tree_index}].testPoints[{tp_index}].testCases 必须是数组")
                    continue
                link_count += 1
                normalized_cases = [normalize_text(value) for value in test_cases if normalize_text(value)]
                case_count += len(normalized_cases)
                for tc_id in normalized_cases:
                    if not re.fullmatch(r"TC-\d{3}", tc_id):
                        errors.append(f"fact-coverage-map {fact_id or index} testCases 包含非法 TC 编号: {tc_id}")
        status = item.get("coverageStatus")
        if status not in status_values:
            errors.append(f"fact-coverage-map {fact_id or index} coverageStatus 非法: {status}")
        reason = normalize_text(item.get("coverageReason"))
        if status == "covered":
            if link_count == 0:
                errors.append(f"fact-coverage-map {fact_id or index} coverageStatus=covered 时 coverageTree 必须至少包含一条 SC/TP 链路")
            if data.get("coverageScope") == "design" and case_count == 0:
                errors.append(f"fact-coverage-map {fact_id or index} coverageScope=design 且 covered 时必须至少包含一个 TC")
        elif status in {"partial", "gap", "not_applicable"}:
            if not reason or "待覆盖审查" in reason:
                errors.append(f"fact-coverage-map {fact_id or index} coverageStatus={status} 时 coverageReason 必须填写明确原因")
            if status in {"gap", "not_applicable"} and link_count:
                errors.append(f"fact-coverage-map {fact_id or index} coverageStatus={status} 时 coverageTree 必须为空")
    if isinstance(summary, dict) and isinstance(fact_coverage, list):
        counted = {
            "totalFacts": len(fact_coverage),
            "coveredFacts": sum(1 for item in fact_coverage if isinstance(item, dict) and item.get("coverageStatus") == "covered"),
            "partialFacts": sum(1 for item in fact_coverage if isinstance(item, dict) and item.get("coverageStatus") == "partial"),
            "gapFacts": sum(1 for item in fact_coverage if isinstance(item, dict) and item.get("coverageStatus") == "gap"),
            "notApplicableFacts": sum(1 for item in fact_coverage if isinstance(item, dict) and item.get("coverageStatus") == "not_applicable"),
        }
        for key, expected in counted.items():
            if summary.get(key) != expected:
                errors.append(f"fact-coverage-map summary.{key} 应为 {expected}，实际为 {summary.get(key)}")
    if not fact_coverage:
        warnings.append("fact-coverage-map factCoverage 为空")
    return errors, warnings


def validate_artifact(data: dict[str, Any]) -> tuple[list[str], list[str]]:
    artifact_type = data.get("artifactType")
    errors: list[str] = []
    warnings: list[str] = []
    if not artifact_type:
        return ["JSON 缺少 artifactType"], warnings
    expected_schema_version = "2.0" if artifact_type in {"test-analysis-solution", "test-design-solution"} else "1.0"
    if artifact_type == "rules-pack":
        expected_schema_version = "1.1"
    if data.get("schemaVersion") != expected_schema_version:
        errors.append(f"{artifact_type}.json schemaVersion 必须为 {expected_schema_version}")
    if artifact_type == "task-list":
        task_errors, task_warnings = validate_task_list(data)
        errors.extend(task_errors)
        warnings.extend(task_warnings)
    elif artifact_type == "rules-pack":
        doc_errors, doc_warnings = validate_generic_document(data, artifact_type)
        errors.extend(doc_errors)
        warnings.extend(doc_warnings)
        errors.extend(validate_rules_pack_json(data))
    elif artifact_type in {"context-pack", "input-fact-model"}:
        doc_errors, doc_warnings = validate_generic_document(data, artifact_type)
        errors.extend(doc_errors)
        warnings.extend(doc_warnings)
    elif artifact_type == "scenario-tree":
        doc_errors, doc_warnings = validate_generic_document(data, artifact_type)
        errors.extend(doc_errors)
        warnings.extend(doc_warnings)
        errors.extend(validate_scenario_tree_json(data))
    elif artifact_type == "test-point-work-items":
        doc_errors, doc_warnings = validate_generic_document(data, artifact_type)
        errors.extend(doc_errors)
        warnings.extend(doc_warnings)
        errors.extend(validate_work_items_json(data, "leafScenarioId", "test-point-work-items"))
    elif artifact_type == "test-case-work-items":
        doc_errors, doc_warnings = validate_generic_document(data, artifact_type)
        errors.extend(doc_errors)
        warnings.extend(doc_warnings)
        errors.extend(validate_work_items_json(data, "testPointId", "test-case-work-items"))
    elif artifact_type == "test-point-slice":
        doc_errors, doc_warnings = validate_generic_document(data, artifact_type)
        errors.extend(doc_errors)
        warnings.extend(doc_warnings)
        errors.extend(validate_test_point_slice_json(data))
    elif artifact_type == "test-case-slice":
        doc_errors, doc_warnings = validate_generic_document(data, artifact_type)
        errors.extend(doc_errors)
        warnings.extend(doc_warnings)
        errors.extend(validate_test_case_slice_json(data))
    elif artifact_type == "test-analysis-solution":
        solution_errors, solution_warnings = validate_solution_ids(data, is_design=False)
        errors.extend(solution_errors)
        warnings.extend(solution_warnings)
    elif artifact_type == "test-design-solution":
        solution_errors, solution_warnings = validate_solution_ids(data, is_design=True)
        errors.extend(solution_errors)
        warnings.extend(solution_warnings)
    elif artifact_type in {
        "test-analysis-solution-review",
        "test-design-solution-review",
        "scenario-tree-review",
        "test-point-review",
        "test-case-review",
        "coverage-review",
    }:
        review_errors, review_warnings = validate_review_json(data)
        errors.extend(review_errors)
        warnings.extend(review_warnings)
    elif artifact_type == "final-report":
        final_errors, final_warnings = validate_final_report_json(data)
        errors.extend(final_errors)
        warnings.extend(final_warnings)
    elif artifact_type == "fact-coverage-map":
        map_errors, map_warnings = validate_fact_coverage_map_json(data)
        errors.extend(map_errors)
        warnings.extend(map_warnings)
    else:
        errors.append(f"不支持的 artifactType: {artifact_type}")
    context_errors, context_warnings = validate_generation_context(data, artifact_type)
    errors.extend(context_errors)
    warnings.extend(context_warnings)
    return errors, warnings
