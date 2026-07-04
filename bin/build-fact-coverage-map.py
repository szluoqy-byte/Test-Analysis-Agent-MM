#!/usr/bin/env python3
"""Build or refresh process fact coverage maps for coverage-review."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

from encoding_utils import configure_stdio
from run_artifacts import dump_json, load_json, normalize_text
from staged_workflow import render_markdown_for_json


STATUS_VALUES = {"covered", "partial", "gap", "not_applicable"}
FINAL_TO_MAP_STATUS = {
    "covered": "covered",
    "partial": "partial",
    "missing": "gap",
    "not_applicable": "not_applicable",
}


ID_PATTERNS = {
    "scenario": re.compile(r"SC-\d{3}(?:-\d{3}){0,2}"),
    "testPoint": re.compile(r"TP-\d{3}"),
    "testCase": re.compile(r"TC-\d{3}"),
}


def extract_id(value: Any, kind: str) -> str:
    text = normalize_text(value)
    match = ID_PATTERNS[kind].search(text)
    return match.group(0) if match else ""


def table_rows(data: dict[str, Any], heading_keyword: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for section in data.get("sections", []):
        if not isinstance(section, dict) or heading_keyword not in normalize_text(section.get("heading")):
            continue
        for block in section.get("content", []):
            if not isinstance(block, dict) or block.get("type") != "table":
                continue
            columns = [normalize_text(column) for column in block.get("columns", [])]
            for raw_row in block.get("rows", []):
                if not isinstance(raw_row, list):
                    continue
                rows.append({columns[index]: normalize_text(raw_row[index]) for index in range(min(len(columns), len(raw_row)))})
    return rows


def source_lookup(data: dict[str, Any]) -> dict[str, dict[str, str]]:
    lookup: dict[str, dict[str, str]] = {}
    for row in table_rows(data, "输入来源"):
        source_type = row.get("类型") or row.get("来源类型") or row.get("sourceType") or ""
        source = row.get("来源") or row.get("文件/来源") or row.get("source") or ""
        if not source_type and not source:
            continue
        lookup[source_type] = {
            "type": source_type,
            "source": source or "未记录",
            "location": row.get("范围") or row.get("位置/章节") or "未记录",
            "description": row.get("说明") or row.get("description") or "",
        }
    return lookup


def input_source_from_fact(row: dict[str, str], lookup: dict[str, dict[str, str]]) -> dict[str, str]:
    source_type = row.get("来源类型", "")
    source = row.get("文件/来源", "")
    location = row.get("位置/章节", "")
    description = row.get("来源", "")
    old_source = row.get("来源", "")
    if not source_type and "：" in old_source:
        source_type, _, inferred_location = old_source.partition("：")
        location = location or inferred_location
    if not source and source_type in lookup:
        source = lookup[source_type].get("source", "")
    if not source and old_source and "：" not in old_source:
        source = old_source
    if not description:
        parts = [part for part in (source_type, source, location) if part]
        description = " / ".join(parts)
    return {
        "type": source_type or "未记录",
        "source": source or "未记录",
        "location": location or "未记录",
        "description": description or "未记录",
    }


def collect_facts(input_fact_model: dict[str, Any]) -> list[dict[str, Any]]:
    lookup = source_lookup(input_fact_model)
    facts: list[dict[str, Any]] = []
    for row in table_rows(input_fact_model, "事实清单"):
        fact_id = row.get("事实ID", "")
        if not fact_id.startswith("FACT-"):
            continue
        facts.append(
            {
                "factId": fact_id,
                "inputSource": input_source_from_fact(row, lookup),
                "factSummary": row.get("事实内容", ""),
                "condition": row.get("约束/条件", ""),
                "observableResult": row.get("可观察结果", ""),
            }
        )
    return facts


def map_paths(run_dir: Path, scope: str) -> tuple[Path, Path]:
    return run_dir / "process" / f"{scope}-fact-coverage-map.json", run_dir / "process" / f"{scope}-fact-coverage-map.md"


def final_report_path(run_dir: Path, scope: str) -> Path:
    return run_dir / "reports" / f"{scope}-final-report.json"


def target_artifacts(run_dir: Path, scope: str) -> dict[str, str]:
    artifacts = {"inputFactModel": "process/input-fact-model.json"}
    analysis_path = run_dir / "deliverables" / "test-analysis-solution.json"
    design_path = run_dir / "deliverables" / "test-design-solution.json"
    coverage_relative = f"process/reviews/{scope}-coverage-review.json"
    if analysis_path.exists():
        artifacts["analysisSolution"] = "deliverables/test-analysis-solution.json"
    if scope == "design" and design_path.exists():
        artifacts["designSolution"] = "deliverables/test-design-solution.json"
    if (run_dir / coverage_relative).exists():
        artifacts["coverageReview"] = coverage_relative
    return artifacts


def normalize_coverage_tree(tree: Any) -> list[dict[str, Any]]:
    if not isinstance(tree, list):
        return []
    grouped: dict[str, dict[str, set[str]]] = {}
    for scenario_ref in tree:
        if not isinstance(scenario_ref, dict):
            continue
        leaf_id = extract_id(scenario_ref.get("leafScenarioId"), "scenario")
        if not leaf_id:
            continue
        grouped.setdefault(leaf_id, {})
        test_points = scenario_ref.get("testPoints")
        if not isinstance(test_points, list):
            continue
        for test_point_ref in test_points:
            if not isinstance(test_point_ref, dict):
                continue
            tp_id = extract_id(test_point_ref.get("testPointId"), "testPoint")
            if not tp_id:
                continue
            cases = test_point_ref.get("testCases")
            case_ids = {extract_id(value, "testCase") for value in cases} if isinstance(cases, list) else set()
            grouped[leaf_id].setdefault(tp_id, set()).update(value for value in case_ids if value)
    return [
        {
            "leafScenarioId": leaf_id,
            "testPoints": [
                {"testPointId": tp_id, "testCases": sorted(case_ids)}
                for tp_id, case_ids in sorted(test_points.items())
            ],
        }
        for leaf_id, test_points in sorted(grouped.items())
        if test_points
    ]


def existing_coverage(run_dir: Path, scope: str) -> dict[str, dict[str, Any]]:
    map_path, _ = map_paths(run_dir, scope)
    path = map_path if map_path.exists() else final_report_path(run_dir, scope)
    if not path.exists():
        return {}
    data = load_json(path)
    coverage = data.get("factCoverage", [])
    if not isinstance(coverage, list):
        return {}
    return {
        normalize_text(item.get("factId")): item
        for item in coverage
        if isinstance(item, dict) and item.get("factId")
    }


def coverage_row(fact: dict[str, Any], existing: dict[str, Any] | None) -> dict[str, Any]:
    existing = existing or {}
    raw_status = normalize_text(existing.get("coverageStatus"))
    status = FINAL_TO_MAP_STATUS.get(raw_status, raw_status)
    if status not in STATUS_VALUES:
        status = "gap"
    reason = normalize_text(existing.get("coverageReason") or existing.get("reviewNote"))
    if not reason and status != "covered":
        reason = "待覆盖审查确认。"
    return {
        "factId": fact["factId"],
        "inputSource": fact["inputSource"],
        "factSummary": fact.get("factSummary", ""),
        "condition": fact.get("condition", ""),
        "observableResult": fact.get("observableResult", ""),
        "coverageTree": normalize_coverage_tree(existing.get("coverageTree")),
        "coverageStatus": status,
        "coverageReason": "" if status == "covered" else reason,
    }


def build_summary(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "totalFacts": len(rows),
        "coveredFacts": sum(1 for row in rows if row.get("coverageStatus") == "covered"),
        "partialFacts": sum(1 for row in rows if row.get("coverageStatus") == "partial"),
        "gapFacts": sum(1 for row in rows if row.get("coverageStatus") == "gap"),
        "notApplicableFacts": sum(1 for row in rows if row.get("coverageStatus") == "not_applicable"),
    }


def build_map(run_dir: Path, scope: str) -> Path:
    input_fact_path = run_dir / "process" / "input-fact-model.json"
    if not input_fact_path.exists():
        raise FileNotFoundError(f"缺少输入事实模型: {input_fact_path}")
    if scope == "analysis" and not (run_dir / "deliverables" / "test-analysis-solution.json").exists():
        raise FileNotFoundError("缺少分析方案: deliverables/test-analysis-solution.json")
    if scope == "design" and not (run_dir / "deliverables" / "test-design-solution.json").exists():
        raise FileNotFoundError("缺少设计方案: deliverables/test-design-solution.json")

    facts = collect_facts(load_json(input_fact_path))
    existing = existing_coverage(run_dir, scope)
    rows = [coverage_row(fact, existing.get(fact["factId"], {})) for fact in facts]
    data = {
        "artifactType": "fact-coverage-map",
        "schemaVersion": "1.0",
        "title": "测试分析 FACT 覆盖证据图" if scope == "analysis" else "测试设计 FACT 覆盖证据图",
        "coverageScope": scope,
        "targetArtifacts": target_artifacts(run_dir, scope),
        "summary": build_summary(rows),
        "factCoverage": rows,
    }
    map_path, _ = map_paths(run_dir, scope)
    dump_json(map_path, data)
    render_markdown_for_json(map_path)
    return map_path


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="生成或刷新 coverage-review 使用的 FACT 覆盖证据图")
    parser.add_argument("run_dir", type=Path, help="outputs/runs/<run-id>")
    parser.add_argument("--scope", choices=("analysis", "design"), required=True, help="覆盖证据图范围")
    args = parser.parse_args()

    try:
        map_path = build_map(args.run_dir, args.scope)
    except Exception as exc:
        print(f"失败: {exc}")
        return 1
    print(f"通过: 已刷新 {map_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
