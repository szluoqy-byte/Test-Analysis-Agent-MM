#!/usr/bin/env python3
"""Build or refresh final human-review fact coverage reports."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

from encoding_utils import configure_stdio
from run_artifacts import dump_json, load_json, normalize_text
from staged_workflow import render_markdown_for_json


MAP_TO_FINAL_STATUS = {
    "covered": "covered",
    "partial": "partial",
    "gap": "missing",
    "missing": "missing",
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


def report_paths(run_dir: Path, scope: str) -> tuple[Path, Path]:
    return run_dir / "reports" / f"{scope}-final-report.json", run_dir / "reports" / f"{scope}-final-report.md"


def coverage_map_path(run_dir: Path, scope: str) -> Path:
    return run_dir / "process" / f"{scope}-fact-coverage-map.json"


def target_artifacts(run_dir: Path, scope: str) -> dict[str, str]:
    artifacts = {"inputFactModel": "process/input-fact-model.json"}
    analysis_path = run_dir / "deliverables" / "test-analysis-solution.json"
    design_path = run_dir / "deliverables" / "test-design-solution.json"
    coverage_relative = f"process/reviews/{scope}-coverage-review.json"
    coverage_path = run_dir / coverage_relative
    map_relative = f"process/{scope}-fact-coverage-map.json"
    map_path = run_dir / map_relative
    if analysis_path.exists():
        artifacts["analysisSolution"] = "deliverables/test-analysis-solution.json"
    if scope == "design" and design_path.exists():
        artifacts["designSolution"] = "deliverables/test-design-solution.json"
    if map_path.exists():
        artifacts["factCoverageMap"] = map_relative
    if coverage_path.exists():
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


def build_summary(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "totalFacts": len(rows),
        "coveredFacts": sum(1 for row in rows if row.get("coverageStatus") == "covered"),
        "partialFacts": sum(1 for row in rows if row.get("coverageStatus") == "partial"),
        "missingFacts": sum(1 for row in rows if row.get("coverageStatus") == "missing"),
        "notApplicableFacts": sum(1 for row in rows if row.get("coverageStatus") == "not_applicable"),
    }


def rows_from_coverage_map(run_dir: Path, scope: str) -> list[dict[str, Any]]:
    path = coverage_map_path(run_dir, scope)
    if not path.exists():
        raise FileNotFoundError(f"缺少 FACT 覆盖证据图: {path}")
    data = load_json(path)
    if data.get("artifactType") != "fact-coverage-map":
        raise ValueError(f"不是 FACT 覆盖证据图: {path}")
    if data.get("coverageScope") != scope:
        raise ValueError(f"{path} coverageScope 应为 {scope}")
    coverage = data.get("factCoverage")
    if not isinstance(coverage, list):
        raise ValueError(f"{path} factCoverage 必须是数组")
    rows: list[dict[str, Any]] = []
    for item in coverage:
        if not isinstance(item, dict):
            continue
        raw_status = normalize_text(item.get("coverageStatus"))
        status = MAP_TO_FINAL_STATUS.get(raw_status, "missing")
        reason = normalize_text(item.get("coverageReason"))
        if status == "missing" and not reason:
            reason = "coverage-review 阶段记录为 gap。"
        rows.append(
            {
                "factId": normalize_text(item.get("factId")),
                "inputSource": item.get("inputSource") if isinstance(item.get("inputSource"), dict) else {},
                "factSummary": normalize_text(item.get("factSummary")),
                "condition": normalize_text(item.get("condition")),
                "observableResult": normalize_text(item.get("observableResult")),
                "coverageTree": normalize_coverage_tree(item.get("coverageTree")),
                "coverageStatus": status,
                "coverageReason": "" if status == "covered" else reason,
            }
        )
    return rows


def build_report(run_dir: Path, scope: str) -> Path:
    input_fact_path = run_dir / "process" / "input-fact-model.json"
    if not input_fact_path.exists():
        raise FileNotFoundError(f"缺少输入事实模型: {input_fact_path}")
    if scope == "analysis" and not (run_dir / "deliverables" / "test-analysis-solution.json").exists():
        raise FileNotFoundError("缺少分析方案: deliverables/test-analysis-solution.json")
    if scope == "design" and not (run_dir / "deliverables" / "test-design-solution.json").exists():
        raise FileNotFoundError("缺少设计方案: deliverables/test-design-solution.json")

    report_path, _ = report_paths(run_dir, scope)
    rows = rows_from_coverage_map(run_dir, scope)
    report = {
        "artifactType": "final-report",
        "schemaVersion": "1.0",
        "title": "测试分析最终报告" if scope == "analysis" else "测试设计最终报告",
        "reportScope": scope,
        "targetArtifacts": target_artifacts(run_dir, scope),
        "summary": build_summary(rows),
        "factCoverage": rows,
    }
    dump_json(report_path, report)
    render_markdown_for_json(report_path)
    return report_path


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="生成或刷新最终人审报告骨架，并渲染 Markdown")
    parser.add_argument("run_dir", type=Path, help="outputs/runs/<run-id>")
    parser.add_argument("--scope", choices=("analysis", "design"), required=True, help="最终报告范围")
    args = parser.parse_args()

    try:
        report_path = build_report(args.run_dir, args.scope)
    except Exception as exc:
        print(f"失败: {exc}")
        return 1
    print(f"通过: 已刷新 {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
