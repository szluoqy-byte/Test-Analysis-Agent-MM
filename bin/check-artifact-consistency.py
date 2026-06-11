#!/usr/bin/env python3
"""Check fixed run artifact layout and basic solution consistency."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from deliverable_markdown import normalize_deliverable_markdown_files


TASK_LIST_HEADER = "| 序号 | 阶段 | 负责 skill | 必须产物/检查点 | 状态 | 证据/路径 |"
TASK_STATUS_VALUES = {"pending", "in_progress", "done", "blocked", "skipped"}
ANALYSIS_REQUIRED_TASK_STAGES = [
    "固定 PROJECT_ROOT 与运行目录",
    "构建上下文包",
    "需求可测性分析",
    "设计方案提取",
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
DESIGN_REQUIRED_TASK_STAGES = [
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
OPTIONAL_TASK_STAGES = {"按源补读", "设计方案提取", "设计依据补读"}
TASK_STAGE_ALIASES = {
    "方法路由": "测试技术路由",
    "专项方法分析": "专项分析",
    "场景化测试点生成": "测试分析方案生成",
}


def split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


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


def collect_first_table(lines: list[str], header: str) -> list[tuple[int, list[str]]]:
    tables = collect_all_tables(lines, header)
    return tables[0] if tables else []


def collect_solution_points(path: Path) -> set[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    points: set[str] = set()
    for line in lines:
        match = re.match(r"^#### (TP-\d{3})\s+", line)
        if match:
            points.add(match.group(1))
    return points


def collect_solution_details(path: Path) -> set[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    details: set[str] = set()
    for line in lines:
        match = re.match(r"^##### (TP-\d{3}-\d{3})\s+", line)
        if match:
            details.add(match.group(1))
    return details


def collect_design_items(path: Path) -> set[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    items: set[str] = set()
    for line in lines:
        list_match = re.match(r"^\s*-\s+(TDI-\d{3})\s+", line)
        if list_match:
            items.add(list_match.group(1))
            continue
        if line.startswith("|"):
            cells = split_row(line)
            if cells and re.fullmatch(r"TDI-\d{3}", cells[0]):
                items.add(cells[0])
    return items


def collect_task_rows(path: Path) -> list[tuple[int, list[str]]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return collect_first_table(lines, TASK_LIST_HEADER)


def validate_task_list(path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    rows = collect_task_rows(path)
    if not rows:
        errors.append("任务清单缺少固定任务表")
        return errors, warnings

    stages: list[str] = []
    statuses: dict[str, str] = {}
    in_progress: list[str] = []

    for line_number, cells in rows:
        if len(cells) != 6:
            errors.append(f"任务清单第 {line_number} 行列数不正确")
            continue
        order, stage, _owner, _artifact, status, evidence = cells
        if not re.fullmatch(r"\d+", order):
            errors.append(f"任务清单第 {line_number} 行序号不是数字: {order}")
        if status not in TASK_STATUS_VALUES:
            errors.append(f"任务清单第 {line_number} 行状态非法: {status}")
        canonical_stage = TASK_STAGE_ALIASES.get(stage, stage)
        if status == "in_progress":
            in_progress.append(canonical_stage)
        if status in {"done", "blocked", "skipped"} and not evidence:
            errors.append(f"任务清单阶段 `{stage}` 状态为 {status} 但证据/路径为空")
        stages.append(canonical_stage)
        statuses[canonical_stage] = status

    if len(in_progress) > 1:
        errors.append("任务清单同时存在多个 in_progress 阶段: " + "、".join(in_progress))

    candidate_flows = [
        ("测试分析", ANALYSIS_REQUIRED_TASK_STAGES),
        ("测试设计", DESIGN_REQUIRED_TASK_STAGES),
    ]
    matched_flow = next(
        ((flow_name, required_stages) for flow_name, required_stages in candidate_flows if all(stage in statuses for stage in required_stages)),
        None,
    )
    if matched_flow is None:
        analysis_missing = [stage for stage in ANALYSIS_REQUIRED_TASK_STAGES if stage not in statuses]
        design_missing = [stage for stage in DESIGN_REQUIRED_TASK_STAGES if stage not in statuses]
        errors.append(
            "任务清单未匹配测试分析或测试设计固定阶段；"
            "分析缺少: "
            + "、".join(analysis_missing)
            + "；设计缺少: "
            + "、".join(design_missing)
        )
        return errors, warnings

    flow_name, required_stages = matched_flow
    positions = [stages.index(stage) for stage in required_stages if stage in stages]
    if positions != sorted(positions):
        errors.append(f"任务清单{flow_name}固定阶段顺序不正确")

    for stage in required_stages:
        status = statuses.get(stage)
        if stage in OPTIONAL_TASK_STAGES:
            if status not in {"done", "skipped"}:
                errors.append(f"任务清单可选阶段 `{stage}` 最终状态应为 done 或 skipped，当前为 {status}")
        elif status != "done":
            errors.append(f"任务清单必选阶段 `{stage}` 最终状态应为 done，当前为 {status}")

    return errors, warnings


def validate_context_pack(path: Path) -> tuple[list[str], list[str]]:
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    warnings: list[str] = []

    if not text.strip():
        errors.append("context-pack 为空")
        return errors, warnings
    for marker in ["project-key", "personal-key"]:
        if marker not in text:
            warnings.append(f"context-pack 未显式记录绑定字段: {marker}")
    if "项目知识阶段绑定" not in text:
        warnings.append("context-pack 未记录项目知识阶段绑定")
    if "补读" not in text:
        warnings.append("context-pack 未记录后续补读建议或无需补读原因")

    return errors, warnings


def validate_clarification_session(path: Path) -> tuple[list[str], list[str]]:
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    warnings: list[str] = []

    if not text.strip():
        errors.append("clarification-session 为空")
        return errors, warnings
    required_markers = [
        "# 待确认治理记录",
        "## 1. 候选问题总表",
        "## 2. 去重与降级结果",
        "## 3. 预期结果兜底清单",
    ]
    for marker in required_markers:
        if marker not in text:
            errors.append(f"clarification-session 缺少固定章节: {marker}")
    if "无待确认候选" not in text and "CQ-" not in text:
        warnings.append("clarification-session 未记录候选问题，也未声明无待确认候选")

    return errors, warnings


def main() -> int:
    if len(sys.argv) != 2:
        print("用法: check-artifact-consistency.py <outputs/runs/<run-id>>", file=sys.stderr)
        return 2

    run_dir = Path(sys.argv[1])
    errors: list[str] = []
    warnings: list[str] = []

    if not run_dir.is_dir():
        print(f"失败: 运行目录不存在: {run_dir}")
        return 1

    required_paths = [
        run_dir / "process" / "task-list.md",
        run_dir / "process" / "context-pack.md",
        run_dir / "process" / "clarification-session.md",
    ]
    for required in required_paths:
        if not required.exists():
            errors.append(f"缺少固定运行产物: {required.relative_to(run_dir)}")

    solution_path = run_dir / "deliverables" / "test-analysis-solution.md"
    design_solution_path = run_dir / "deliverables" / "test-design-solution.md"
    normalize_deliverable_markdown_files(run_dir / "deliverables")
    task_list_path = run_dir / "process" / "task-list.md"
    context_pack_path = run_dir / "process" / "context-pack.md"
    clarification_session_path = run_dir / "process" / "clarification-session.md"

    if not solution_path.exists() and not design_solution_path.exists():
        errors.append("缺少主交付件: deliverables/test-analysis-solution.md 或 deliverables/test-design-solution.md")

    if task_list_path.exists():
        task_errors, task_warnings = validate_task_list(task_list_path)
        errors.extend(task_errors)
        warnings.extend(task_warnings)
        rows = collect_task_rows(task_list_path)
        normalize_done = any(
            len(cells) == 6 and cells[1] == "输入文档归一化" and cells[4] == "done"
            for _line_number, cells in rows
        )
        if normalize_done:
            manifest_path = run_dir / "inputs" / "input-normalization-manifest.json"
            if not manifest_path.exists():
                errors.append("输入文档归一化已完成，但缺少 inputs/input-normalization-manifest.json")

    if context_pack_path.exists():
        context_errors, context_warnings = validate_context_pack(context_pack_path)
        errors.extend(context_errors)
        warnings.extend(context_warnings)

    if clarification_session_path.exists():
        clarification_errors, clarification_warnings = validate_clarification_session(clarification_session_path)
        errors.extend(clarification_errors)
        warnings.extend(clarification_warnings)

    if solution_path.exists():
        points = collect_solution_points(solution_path)
        details = collect_solution_details(solution_path)
        if not points:
            errors.append("测试分析方案未找到 TP-* 测试点标题")
        if not details:
            errors.append("测试分析方案未找到 TP-*-* 测试点明细")

    if design_solution_path.exists():
        points = collect_solution_points(design_solution_path)
        details = collect_solution_details(design_solution_path)
        design_items = collect_design_items(design_solution_path)
        if not points:
            errors.append("测试设计方案未找到 TP-* 测试点标题")
        if not details:
            errors.append("测试设计方案未找到 TP-*-* 测试点明细")
        if not design_items:
            errors.append("测试设计方案未找到 TDI-* 测试设计项")

    for warning in warnings:
        print(f"警告: {warning}")
    for error in errors:
        print(f"失败: {error}")

    if errors:
        return 1
    print(f"通过: {run_dir} 运行产物路径和基础一致性校验通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
