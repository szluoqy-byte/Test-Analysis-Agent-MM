#!/usr/bin/env python3
"""Check fixed run artifact layout and cross-artifact test point consistency."""

from __future__ import annotations

import re
import sys
from pathlib import Path


TITLE_ITEM_HEADER = "| 标题项 ID | 测试用例标题 | 覆盖意图 | 级别 | 输入条件与数据依赖 | 判定关注 | 待确认信息 |"
REPORT_TESTPOINT_HEADER = "| ID | 模块 | 测试点 | 类型 | 方法 | 需求依据 | 级别 | 风险/备注 |"
EVIDENCE_HEADER = "| 证据ID | 方法 | 需求片段 | 分析结论 | 关联测试点/待确认 |"
TASK_LIST_HEADER = "| 序号 | 阶段 | 负责 skill | 必须产物/检查点 | 状态 | 证据/路径 |"
TASK_STATUS_VALUES = {"pending", "in_progress", "done", "blocked", "skipped"}
REQUIRED_TASK_STAGES = [
    "固定 PROJECT_ROOT 与运行目录",
    "构建上下文包",
    "需求可测性分析",
    "设计方案提取",
    "待确认治理",
    "方法路由",
    "专项方法分析",
    "按源补读",
    "场景化测试点生成",
    "测试用例标题大纲生成",
    "覆盖审查",
    "确定性校验",
    "输出收口",
]
OPTIONAL_TASK_STAGES = {"按源补读", "设计方案提取"}
QUESTION_HEADERS = {
    "| ID | 问题 | 影响 | 关联需求依据 |",
    "| 问题 ID | 问题 | 影响场景/测试点 | 当前处理 |",
    "| 问题 ID | 问题 | 影响场景/测试点/标题项 | 当前处理 |",
}
CONTEXT_REQUIRED_SECTIONS = [
    "## 项目标识",
    "## 个人配置标识",
    "## 已扫描来源",
    "## 命中摘要",
    "## Project/Personal 使用摘要",
    "## 相关项目事实",
    "## 相关项目知识补充",
    "## 相关个人补充",
    "## 大文件来源与后续补读建议",
]


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


def is_point_id(value: str) -> bool:
    return bool(re.fullmatch(r"(?:TP|ITP)-\d{3}", value))


def collect_outline_points(path: Path) -> dict[str, dict[str, str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    points: dict[str, dict[str, str]] = {}
    for line_number, line in enumerate(lines, start=1):
        match = re.match(r"^#{4,5} ((?:TP|ITP)-\d{3})\s+(.+)$", line)
        if not match:
            continue
        point_id, text = match.groups()
        points[point_id] = {
            "line": str(line_number),
            "text": text.strip(),
            "category": "",
            "subtype": "",
            "level": "",
            "risk": "",
        }
    return points


def collect_outline_title_ids(path: Path) -> set[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    title_ids: set[str] = set()
    for rows in collect_all_tables(lines, TITLE_ITEM_HEADER):
        for _, cells in rows:
            if cells and re.fullmatch(r"TCT-\d{3}", cells[0]):
                title_ids.add(cells[0])
    return title_ids


def collect_report_points(path: Path) -> dict[str, dict[str, str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    points: dict[str, dict[str, str]] = {}
    for line_number, cells in collect_first_table(lines, REPORT_TESTPOINT_HEADER):
        if len(cells) != 8 or not is_point_id(cells[0]):
            continue
        point_id, module, text, test_type, method, basis, level, risk = cells
        points[point_id] = {
            "line": str(line_number),
            "module": module,
            "text": text,
            "type": test_type,
            "method": method,
            "basis": basis,
            "level": level,
            "risk": risk,
        }
    return points


def collect_evidence_links(path: Path) -> set[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    links: set[str] = set()
    for _, cells in collect_first_table(lines, EVIDENCE_HEADER):
        if len(cells) != 5:
            continue
        for point_id in re.findall(r"(?:TP|ITP|Q)-\d{3}", cells[4]):
            links.add(point_id)
    return links


def collect_question_ids(path: Path) -> set[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    questions: set[str] = set()
    for header in QUESTION_HEADERS:
        for _, cells in collect_first_table(lines, header):
            if cells and re.fullmatch(r"Q-\d{3}", cells[0]):
                questions.add(cells[0])
    return questions


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
        if status == "in_progress":
            in_progress.append(stage)
        if status in {"done", "blocked", "skipped"} and not evidence:
            warnings.append(f"任务清单阶段 `{stage}` 状态为 {status} 但证据/路径为空")
        stages.append(stage)
        statuses[stage] = status

    if len(in_progress) > 1:
        errors.append("任务清单同时存在多个 in_progress 阶段: " + "、".join(in_progress))

    missing = [stage for stage in REQUIRED_TASK_STAGES if stage not in statuses]
    if missing:
        errors.append("任务清单缺少固定阶段: " + "、".join(missing))

    positions = [stages.index(stage) for stage in REQUIRED_TASK_STAGES if stage in stages]
    if positions != sorted(positions):
        errors.append("任务清单固定阶段顺序不正确")

    for stage in REQUIRED_TASK_STAGES:
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

    for section in CONTEXT_REQUIRED_SECTIONS:
        if section not in text:
            errors.append(f"context-pack 缺少必需章节: {section}")

    for marker in ["project-key", "personal-key"]:
        if marker not in text:
            errors.append(f"context-pack 缺少绑定字段: {marker}")

    if "未采用" not in text and "未注入" not in text:
        warnings.append("context-pack 未说明 project/personal 未采用或未注入来源")
    if "补读" not in text:
        warnings.append("context-pack 未记录后续补读建议或无需补读原因")

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
        run_dir / "deliverables" / "testcase-title-outline.md",
        run_dir / "process" / "task-list.md",
        run_dir / "process" / "context-pack.md",
    ]
    for required in required_paths:
        if not required.exists():
            errors.append(f"缺少固定运行产物: {required.relative_to(run_dir)}")

    outline_path = run_dir / "deliverables" / "testcase-title-outline.md"
    task_list_path = run_dir / "process" / "task-list.md"
    context_pack_path = run_dir / "process" / "context-pack.md"
    report_path = run_dir / "reports" / "test-analysis-report.md"

    if task_list_path.exists():
        task_errors, task_warnings = validate_task_list(task_list_path)
        errors.extend(task_errors)
        warnings.extend(task_warnings)

    if context_pack_path.exists():
        context_errors, context_warnings = validate_context_pack(context_pack_path)
        errors.extend(context_errors)
        warnings.extend(context_warnings)

    if outline_path.exists():
        outline_points = collect_outline_points(outline_path)
        title_ids = collect_outline_title_ids(outline_path)
        if not outline_points:
            errors.append("测试用例标题大纲未找到 TP-* 或 ITP-* 测试点标题")
        if not title_ids:
            errors.append("测试用例标题大纲未找到 TCT-* 标题项")

    if report_path.exists() and outline_path.exists():
        outline_points = collect_outline_points(outline_path)
        report_points = collect_report_points(report_path)

        missing_in_report = sorted(set(outline_points) - set(report_points))
        if missing_in_report:
            errors.append("过程报告缺少主交付件测试点: " + "、".join(missing_in_report))

        for point_id in sorted(set(outline_points) & set(report_points)):
            outline_point = outline_points[point_id]
            report_point = report_points[point_id]
            for field, label in [("text", "测试点")]:
                if outline_point[field] != report_point[field]:
                    errors.append(
                        f"{point_id} {label} 不一致: 主交付件 `{outline_point[field]}` / 过程报告 `{report_point[field]}`"
                    )
            if outline_point.get("level") and outline_point["level"] != report_point["level"]:
                errors.append(f"{point_id} 级别不一致: 主交付件 `{outline_point['level']}` / 过程报告 `{report_point['level']}`")

        evidence_links = collect_evidence_links(report_path)
        question_ids = collect_question_ids(report_path)
        valid_links = set(outline_points) | set(report_points) | question_ids
        unknown_links = sorted(link for link in evidence_links if link not in valid_links)
        missing_evidence = sorted(set(outline_points) - evidence_links)
        if unknown_links:
            errors.append("方法证据引用未知 ID: " + "、".join(unknown_links))
        if missing_evidence:
            warnings.append("以下测试点未被方法证据直接关联: " + "、".join(missing_evidence))

    for warning in warnings:
        print(f"警告: {warning}")
    for error in errors:
        print(f"失败: {error}")

    if errors:
        return 1
    print(f"通过: {run_dir} 运行产物路径和跨产物一致性校验通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
