#!/usr/bin/env python3
"""Convert legacy Markdown run artifacts into JSON canonical files."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

from run_artifacts import dump_json, split_row


def parse_table(lines: list[str], start: int) -> tuple[list[str], list[list[str]], int]:
    columns = split_row(lines[start])
    rows: list[list[str]] = []
    index = start + 2
    while index < len(lines) and lines[index].startswith("|"):
        rows.append(split_row(lines[index]))
        index += 1
    return columns, rows, index


def parse_generic_markdown(path: Path, artifact_type: str) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8").splitlines()
    title = lines[0].removeprefix("# ").strip() if lines else path.stem
    sections: list[dict[str, Any]] = []
    index = 1
    while index < len(lines):
        line = lines[index]
        heading_match = re.match(r"^(#{2,6})\s+(.+)$", line)
        if not heading_match:
            index += 1
            continue
        level = len(heading_match.group(1))
        section = {"heading": heading_match.group(2).strip(), "level": level, "content": []}
        index += 1
        while index < len(lines):
            line = lines[index]
            if re.match(r"^#{2,6}\s+", line):
                break
            if not line.strip():
                index += 1
                continue
            if line.startswith("|") and index + 1 < len(lines) and lines[index + 1].startswith("|"):
                columns, rows, index = parse_table(lines, index)
                section["content"].append({"type": "table", "columns": columns, "rows": rows})
                continue
            if line.startswith("- "):
                items: list[dict[str, str]] = []
                bullets: list[str] = []
                while index < len(lines) and lines[index].startswith("- "):
                    value = lines[index][2:].strip()
                    label, sep, item_value = value.partition("：")
                    if sep:
                        items.append({"label": label, "value": item_value})
                    else:
                        bullets.append(value)
                    index += 1
                if items and not bullets:
                    section["content"].append({"type": "items", "items": items})
                else:
                    if items:
                        bullets.extend(f"{item['label']}：{item['value']}" for item in items)
                    section["content"].append({"type": "bullets", "items": bullets})
                continue
            paragraph_lines: list[str] = []
            while index < len(lines):
                line = lines[index]
                if not line.strip() or line.startswith("|") or line.startswith("- ") or re.match(r"^#{2,6}\s+", line):
                    break
                paragraph_lines.append(line)
                index += 1
            if paragraph_lines:
                section["content"].append({"type": "paragraph", "text": "\n".join(paragraph_lines)})
                continue
            index += 1
        sections.append(section)
    return {"artifactType": artifact_type, "schemaVersion": "1.0", "title": title, "sections": sections}


def parse_task_list(path: Path) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8").splitlines()
    metadata: dict[str, str] = {}
    stages: list[dict[str, Any]] = []
    for line in lines:
        if line.startswith("- "):
            label, sep, value = line[2:].partition("：")
            if sep:
                key = {
                    "需求文档": "requirementDocument",
                    "设计方案文档": "designDocument",
                    "run-id": "runId",
                    "PROJECT_ROOT": "projectRoot",
                    "生成时间": "generatedAt",
                }.get(label)
                if key:
                    metadata[key] = value
    for index, line in enumerate(lines):
        if line.startswith("| 序号 | 阶段 | 负责 skill |"):
            _columns, rows, _end = parse_table(lines, index)
            for row in rows:
                if len(row) >= 6:
                    stages.append(
                        {
                            "order": int(row[0]) if row[0].isdigit() else len(stages) + 1,
                            "stage": row[1],
                            "owner": row[2],
                            "checkpoint": row[3],
                            "status": row[4],
                            "evidence": row[5],
                        }
                    )
            break
    return {"artifactType": "task-list", "schemaVersion": "1.0", "metadata": metadata, "stages": stages}


def parse_fields_table(lines: list[str], start: int) -> tuple[list[dict[str, str]], int]:
    columns, rows, end = parse_table(lines, start)
    fields: list[dict[str, str]] = []
    if columns[:2] == ["字段", "内容"]:
        fields = [{"field": row[0], "content": row[1]} for row in rows if len(row) >= 2]
    return fields, end


def find_block_end(lines: list[str], start: int, heading_prefixes: tuple[str, ...]) -> int:
    for index in range(start, len(lines)):
        if lines[index].startswith(heading_prefixes):
            return index
    return len(lines)


def parse_leaf(lines: list[str], start: int, end: int) -> tuple[str, str, list[dict[str, str]]]:
    description = ""
    expected = ""
    design_items: list[dict[str, str]] = []
    for line in lines[start:end]:
        stripped = line.strip()
        if stripped.startswith("- 测试点详情："):
            description = stripped.removeprefix("- 测试点详情：")
        elif stripped.startswith("- 预期结果："):
            expected = stripped.removeprefix("- 预期结果：")
        else:
            match = re.match(r"^-\s+(TDI-\d{3})\s+(.+)$", stripped)
            if match:
                design_items.append({"id": match.group(1), "content": match.group(2)})
    return description, expected, design_items


def parse_solution(path: Path, artifact_type: str) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8").splitlines()
    title = lines[0].removeprefix("# ").strip()
    scope_heading = "## 1. 需求范围" if artifact_type == "test-analysis-solution" else "## 1. 设计输入"
    scope_key = "scope" if artifact_type == "test-analysis-solution" else "inputs"
    scope: list[dict[str, str]] = []
    for index, line in enumerate(lines):
        if line == scope_heading:
            table_index = next((i for i in range(index + 1, len(lines)) if lines[i].startswith("| 字段 | 内容 |")), None)
            if table_index is not None:
                scope, _end = parse_fields_table(lines, table_index)
            break

    scenarios: list[dict[str, Any]] = []
    scenario_indices = [
        (index, match.group(1), match.group(2).strip())
        for index, line in enumerate(lines)
        if (match := re.match(r"^### (SC-\d{3})\s+(.+)$", line))
    ]
    for scenario_position, (scenario_start, scenario_id, scenario_title) in enumerate(scenario_indices):
        scenario_end = scenario_indices[scenario_position + 1][0] if scenario_position + 1 < len(scenario_indices) else len(lines)
        fields: list[dict[str, str]] = []
        table_index = next(
            (i for i in range(scenario_start + 1, scenario_end) if lines[i].startswith("| 字段 | 内容 |")),
            None,
        )
        if table_index is not None:
            fields, _end = parse_fields_table(lines, table_index)
        points: list[dict[str, Any]] = []
        point_indices = [
            (index, match.group(1), match.group(2).strip())
            for index in range(scenario_start + 1, scenario_end)
            if (match := re.match(r"^#### (TP-\d{3})\s+(.+)$", lines[index]))
        ]
        for point_position, (point_start, point_id, point_title) in enumerate(point_indices):
            point_end = point_indices[point_position + 1][0] if point_position + 1 < len(point_indices) else scenario_end
            details: list[dict[str, Any]] = []
            detail_indices = [
                (index, match.group(1), match.group(2).strip())
                for index in range(point_start + 1, point_end)
                if (match := re.match(r"^##### (TP-\d{3}-\d{3})\s+(.+)$", lines[index]))
            ]
            for detail_position, (detail_start, detail_id, detail_title) in enumerate(detail_indices):
                detail_end = detail_indices[detail_position + 1][0] if detail_position + 1 < len(detail_indices) else point_end
                failures: list[dict[str, Any]] = []
                failure_indices = [
                    (index, match.group(1), match.group(2).strip())
                    for index in range(detail_start + 1, detail_end)
                    if (match := re.match(r"^###### (TP-\d{3}-\d{3}-\d{3})\s+(.+)$", lines[index]))
                ]
                if failure_indices:
                    for failure_position, (failure_start, failure_id, failure_title) in enumerate(failure_indices):
                        failure_end = (
                            failure_indices[failure_position + 1][0]
                            if failure_position + 1 < len(failure_indices)
                            else detail_end
                        )
                        description, expected, design_items = parse_leaf(lines, failure_start + 1, failure_end)
                        failure: dict[str, Any] = {
                            "id": failure_id,
                            "title": failure_title,
                            "description": description,
                            "expectedResult": expected,
                        }
                        if artifact_type == "test-design-solution":
                            failure["designItems"] = design_items
                        failures.append(failure)
                    details.append({"id": detail_id, "title": detail_title, "failureDetails": failures})
                else:
                    description, expected, design_items = parse_leaf(lines, detail_start + 1, detail_end)
                    detail: dict[str, Any] = {
                        "id": detail_id,
                        "title": detail_title,
                        "description": description,
                        "expectedResult": expected,
                        "failureDetails": [],
                    }
                    if artifact_type == "test-design-solution":
                        detail["designItems"] = design_items
                    details.append(detail)
            points.append({"id": point_id, "title": point_title, "details": details})
        scenarios.append({"id": scenario_id, "title": scenario_title, "fields": fields, "testPoints": points})

    data: dict[str, Any] = {"artifactType": artifact_type, "schemaVersion": "1.0", "title": title, scope_key: scope, "scenarios": scenarios}
    return data


def convert_run(run_dir: Path) -> list[Path]:
    written: list[Path] = []
    conversions = [
        (run_dir / "process" / "task-list.md", "task-list", parse_task_list),
        (run_dir / "process" / "context-pack.md", "context-pack", parse_generic_markdown),
        (run_dir / "process" / "input-fact-model.md", "input-fact-model", parse_generic_markdown),
        (run_dir / "deliverables" / "test-analysis-solution.md", "test-analysis-solution", parse_solution),
        (run_dir / "deliverables" / "test-design-solution.md", "test-design-solution", parse_solution),
    ]
    for markdown_path, artifact_type, parser in conversions:
        if not markdown_path.exists():
            continue
        if parser is parse_task_list:
            data = parser(markdown_path)
        else:
            data = parser(markdown_path, artifact_type)
        json_path = markdown_path.with_suffix(".json")
        if artifact_type == "coverage-review" and markdown_path.name == "test-analysis-report.md":
            json_path = run_dir / "reports" / "coverage-review.json"
        dump_json(json_path, data)
        written.append(json_path)
    legacy_report = run_dir / "reports" / "test-analysis-report.md"
    if legacy_report.exists():
        data = {
            "artifactType": "coverage-review",
            "schemaVersion": "1.0",
            "title": "覆盖审查结果",
            "result": "通过",
            "summary": "由旧版 test-analysis-report.md 迁移生成；详细过程报告保留原 Markdown。",
            "findings": [],
            "blockingIssues": [],
            "recommendations": [],
            "evidenceRefs": [str(legacy_report.relative_to(run_dir))],
        }
        json_path = run_dir / "reports" / "coverage-review.json"
        dump_json(json_path, data)
        written.append(json_path)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="将旧 Markdown run 产物迁移为 JSON canonical")
    parser.add_argument("run_dir", type=Path, help="outputs/runs/<run-id>")
    args = parser.parse_args()
    if not args.run_dir.is_dir():
        print(f"失败: 运行目录不存在: {args.run_dir}")
        return 1
    written = convert_run(args.run_dir)
    if not written:
        print(f"失败: 未找到可迁移 Markdown 产物: {args.run_dir}")
        return 1
    for path in written:
        print(f"生成: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
