#!/usr/bin/env python3
"""Lint JSON canonical artifacts in a run directory."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from encoding_utils import configure_stdio
from run_artifacts import collect_renderable_json_files, load_json, normalize_text, validate_artifact


REQUIRED_PROCESS_JSON = [
    "process/rules-pack.json",
    "process/context-pack.json",
]


def has_any(run_dir: Path, relatives: list[str]) -> bool:
    return any((run_dir / relative).exists() for relative in relatives)


def coverage_review_path(run_dir: Path, scope: str) -> Path:
    return run_dir / "process" / "reviews" / f"{scope}-coverage-review.json"


def final_report_path(run_dir: Path, scope: str) -> Path:
    return run_dir / "reports" / f"{scope}-final-report.json"


def fact_coverage_map_path(run_dir: Path, scope: str) -> Path:
    return run_dir / "process" / f"{scope}-fact-coverage-map.json"


def coverage_review_result(run_dir: Path, scope: str) -> str:
    path = coverage_review_path(run_dir, scope)
    if not path.exists():
        return ""
    try:
        data = load_json(path)
    except Exception:
        return ""
    return normalize_text(data.get("result"))


def validate_coverage_gap_locations(run_dir: Path, relative: Path, data: dict) -> list[str]:
    if data.get("artifactType") != "coverage-review":
        return []
    errors: list[str] = []
    report_name = relative.as_posix()
    scope = data.get("coverageScope")
    if not scope:
        if report_name.endswith("analysis-coverage-review.json"):
            scope = "analysis"
        elif report_name.endswith("design-coverage-review.json"):
            scope = "design"
    allowed_prefixes = {
        "analysis": ("process/test-point-slices/",),
        "design": ("process/test-case-slices/",),
    }.get(scope, ("process/test-point-slices/", "process/test-case-slices/"))
    for index, gap in enumerate(data.get("coverageGaps", []), start=1):
        if not isinstance(gap, dict):
            continue
        location = str(gap.get("artifactLocation") or "").replace("\\", "/").strip()
        if not location:
            continue
        if location.startswith(str(run_dir).replace("\\", "/").rstrip("/") + "/"):
            location = location[len(str(run_dir).replace("\\", "/").rstrip("/") + "/") :]
        if not any(location.startswith(prefix) for prefix in allowed_prefixes):
            errors.append(f"{relative}: coverageGaps[{index}].artifactLocation 不符合 {scope or '未知'} 范围: {location}")
            continue
        if not (run_dir / location).exists():
            errors.append(f"{relative}: coverageGaps[{index}].artifactLocation 指向的切片不存在: {location}")
    return errors


def solution_index(run_dir: Path, scope: str) -> dict[str, Any]:
    solution_path = run_dir / "deliverables" / ("test-design-solution.json" if scope == "design" else "test-analysis-solution.json")
    if not solution_path.exists():
        return {
            "leafScenarios": set(),
            "testPointToLeaf": {},
            "testCaseToTestPoint": {},
        }
    solution = load_json(solution_path)
    index: dict[str, Any] = {
        "leafScenarios": set(),
        "testPointToLeaf": {},
        "testCaseToTestPoint": {},
    }

    def walk(scenarios: list[Any]) -> None:
        for scenario in scenarios:
            if not isinstance(scenario, dict):
                continue
            scenario_id = normalize_text(scenario.get("id"))
            children = scenario.get("children")
            if isinstance(children, list) and children:
                walk(children)
                continue
            if scenario_id:
                index["leafScenarios"].add(scenario_id)
            for test_point in scenario.get("testPoints", []):
                if not isinstance(test_point, dict):
                    continue
                tp_id = normalize_text(test_point.get("id"))
                if tp_id and scenario_id:
                    index["testPointToLeaf"][tp_id] = scenario_id
                for test_case in test_point.get("testCases", []):
                    if not isinstance(test_case, dict):
                        continue
                    tc_id = normalize_text(test_case.get("id"))
                    if tc_id and tp_id:
                        index["testCaseToTestPoint"][tc_id] = tp_id

    scenarios = solution.get("scenarios")
    if isinstance(scenarios, list):
        walk(scenarios)
    return index


def validate_final_report_links(run_dir: Path, relative: Path, data: dict) -> list[str]:
    if data.get("artifactType") != "final-report":
        return []
    errors: list[str] = []
    scope = normalize_text(data.get("reportScope") or "analysis")
    if scope not in {"analysis", "design"}:
        return errors
    index = solution_index(run_dir, scope)
    if not index["leafScenarios"]:
        errors.append(f"{relative}: 无法读取 {scope} 最终方案用于校验 coverageTree")
        return errors
    for row_index, row in enumerate(data.get("factCoverage", []), start=1):
        if not isinstance(row, dict):
            continue
        fact_id = normalize_text(row.get("factId")) or f"factCoverage[{row_index}]"
        status = normalize_text(row.get("coverageStatus"))
        tree = row.get("coverageTree") if isinstance(row.get("coverageTree"), list) else []
        tp_count = 0
        tc_count = 0
        for scenario_ref in tree:
            if not isinstance(scenario_ref, dict):
                continue
            leaf_id = normalize_text(scenario_ref.get("leafScenarioId"))
            if leaf_id and leaf_id not in index["leafScenarios"]:
                errors.append(f"{relative}: {fact_id} coverageTree 引用了不存在或非叶子的 SC: {leaf_id}")
            test_points = scenario_ref.get("testPoints") if isinstance(scenario_ref.get("testPoints"), list) else []
            for test_point_ref in test_points:
                if not isinstance(test_point_ref, dict):
                    continue
                tp_id = normalize_text(test_point_ref.get("testPointId"))
                if not tp_id:
                    continue
                tp_count += 1
                actual_leaf = index["testPointToLeaf"].get(tp_id)
                if not actual_leaf:
                    errors.append(f"{relative}: {fact_id} coverageTree 引用了不存在的 TP: {tp_id}")
                elif actual_leaf != leaf_id:
                    errors.append(f"{relative}: {fact_id} {tp_id} 属于 {actual_leaf}，不能挂在 {leaf_id}")
                test_cases = test_point_ref.get("testCases") if isinstance(test_point_ref.get("testCases"), list) else []
                for raw_tc in test_cases:
                    tc_id = normalize_text(raw_tc)
                    if not tc_id:
                        continue
                    tc_count += 1
                    actual_tp = index["testCaseToTestPoint"].get(tc_id)
                    if scope == "analysis":
                        errors.append(f"{relative}: {fact_id} analysis final-report 不应包含 TC: {tc_id}")
                    elif not actual_tp:
                        errors.append(f"{relative}: {fact_id} coverageTree 引用了不存在的 TC: {tc_id}")
                    elif actual_tp != tp_id:
                        errors.append(f"{relative}: {fact_id} {tc_id} 属于 {actual_tp}，不能挂在 {tp_id}")
        if status == "covered":
            if tp_count == 0:
                errors.append(f"{relative}: {fact_id} covered 状态必须至少有一条 SC/TP 覆盖链路")
            if scope == "design" and tc_count == 0:
                errors.append(f"{relative}: {fact_id} design covered 状态必须至少有一个 TC")
    return errors


def normalize_tree_for_compare(tree: Any) -> list[dict[str, Any]]:
    if not isinstance(tree, list):
        return []
    grouped: dict[str, dict[str, set[str]]] = {}
    for scenario_ref in tree:
        if not isinstance(scenario_ref, dict):
            continue
        leaf_id = normalize_text(scenario_ref.get("leafScenarioId"))
        if not leaf_id:
            continue
        grouped.setdefault(leaf_id, {})
        test_points = scenario_ref.get("testPoints") if isinstance(scenario_ref.get("testPoints"), list) else []
        for test_point_ref in test_points:
            if not isinstance(test_point_ref, dict):
                continue
            tp_id = normalize_text(test_point_ref.get("testPointId"))
            if not tp_id:
                continue
            test_cases = test_point_ref.get("testCases") if isinstance(test_point_ref.get("testCases"), list) else []
            grouped[leaf_id].setdefault(tp_id, set()).update(normalize_text(value) for value in test_cases if normalize_text(value))
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


def validate_final_report_matches_map(run_dir: Path, relative: Path, data: dict) -> list[str]:
    if data.get("artifactType") != "final-report":
        return []
    errors: list[str] = []
    scope = normalize_text(data.get("reportScope"))
    if scope not in {"analysis", "design"}:
        return errors
    map_path = fact_coverage_map_path(run_dir, scope)
    if not map_path.exists():
        errors.append(f"{relative}: 缺少对应 FACT 覆盖证据图: {map_path.relative_to(run_dir)}")
        return errors
    try:
        coverage_map = load_json(map_path)
    except Exception as exc:
        errors.append(f"{relative}: 无法读取对应 FACT 覆盖证据图: {exc}")
        return errors
    status_map = {"covered": "covered", "partial": "partial", "gap": "missing", "not_applicable": "not_applicable"}
    map_rows = {
        normalize_text(item.get("factId")): item
        for item in coverage_map.get("factCoverage", [])
        if isinstance(item, dict) and item.get("factId")
    }
    final_rows = {
        normalize_text(item.get("factId")): item
        for item in data.get("factCoverage", [])
        if isinstance(item, dict) and item.get("factId")
    }
    if set(final_rows) != set(map_rows):
        missing = sorted(set(map_rows) - set(final_rows))
        extra = sorted(set(final_rows) - set(map_rows))
        if missing:
            errors.append(f"{relative}: final-report 缺少 fact-coverage-map 中的 FACT: {', '.join(missing)}")
        if extra:
            errors.append(f"{relative}: final-report 包含 fact-coverage-map 中不存在的 FACT: {', '.join(extra)}")
    for fact_id, final_row in final_rows.items():
        map_row = map_rows.get(fact_id)
        if not isinstance(map_row, dict):
            continue
        expected_status = status_map.get(normalize_text(map_row.get("coverageStatus")), "missing")
        if final_row.get("coverageStatus") != expected_status:
            errors.append(f"{relative}: {fact_id} coverageStatus 应从 fact-coverage-map 映射为 {expected_status}，实际为 {final_row.get('coverageStatus')}")
        if normalize_tree_for_compare(final_row.get("coverageTree")) != normalize_tree_for_compare(map_row.get("coverageTree")):
            errors.append(f"{relative}: {fact_id} coverageTree 与 fact-coverage-map 不一致")
    return errors


def validate_fact_coverage_map_links(run_dir: Path, relative: Path, data: dict) -> list[str]:
    if data.get("artifactType") != "fact-coverage-map":
        return []
    errors: list[str] = []
    scope = normalize_text(data.get("coverageScope") or "analysis")
    if scope not in {"analysis", "design"}:
        return errors
    index = solution_index(run_dir, scope)
    if not index["leafScenarios"]:
        errors.append(f"{relative}: 无法读取 {scope} 最终方案用于校验 coverageTree")
        return errors
    for row_index, row in enumerate(data.get("factCoverage", []), start=1):
        if not isinstance(row, dict):
            continue
        fact_id = normalize_text(row.get("factId")) or f"factCoverage[{row_index}]"
        status = normalize_text(row.get("coverageStatus"))
        tree = row.get("coverageTree") if isinstance(row.get("coverageTree"), list) else []
        tp_count = 0
        tc_count = 0
        for scenario_ref in tree:
            if not isinstance(scenario_ref, dict):
                continue
            leaf_id = normalize_text(scenario_ref.get("leafScenarioId"))
            if leaf_id and leaf_id not in index["leafScenarios"]:
                errors.append(f"{relative}: {fact_id} coverageTree 引用了不存在或非叶子的 SC: {leaf_id}")
            test_points = scenario_ref.get("testPoints") if isinstance(scenario_ref.get("testPoints"), list) else []
            for test_point_ref in test_points:
                if not isinstance(test_point_ref, dict):
                    continue
                tp_id = normalize_text(test_point_ref.get("testPointId"))
                if not tp_id:
                    continue
                tp_count += 1
                actual_leaf = index["testPointToLeaf"].get(tp_id)
                if not actual_leaf:
                    errors.append(f"{relative}: {fact_id} coverageTree 引用了不存在的 TP: {tp_id}")
                elif actual_leaf != leaf_id:
                    errors.append(f"{relative}: {fact_id} {tp_id} 属于 {actual_leaf}，不能挂在 {leaf_id}")
                test_cases = test_point_ref.get("testCases") if isinstance(test_point_ref.get("testCases"), list) else []
                for raw_tc in test_cases:
                    tc_id = normalize_text(raw_tc)
                    if not tc_id:
                        continue
                    tc_count += 1
                    actual_tp = index["testCaseToTestPoint"].get(tc_id)
                    if scope == "analysis":
                        errors.append(f"{relative}: {fact_id} analysis fact-coverage-map 不应包含 TC: {tc_id}")
                    elif not actual_tp:
                        errors.append(f"{relative}: {fact_id} coverageTree 引用了不存在的 TC: {tc_id}")
                    elif actual_tp != tp_id:
                        errors.append(f"{relative}: {fact_id} {tc_id} 属于 {actual_tp}，不能挂在 {tp_id}")
        if status == "covered":
            if tp_count == 0:
                errors.append(f"{relative}: {fact_id} covered 状态必须至少有一条 SC/TP 覆盖链路")
            if scope == "design" and tc_count == 0:
                errors.append(f"{relative}: {fact_id} design covered 状态必须至少有一个 TC")
    return errors


def validate_coverage_review_consistency(run_dir: Path, relative: Path, data: dict) -> list[str]:
    if data.get("artifactType") != "coverage-review":
        return []
    errors: list[str] = []
    scope = normalize_text(data.get("coverageScope"))
    if scope not in {"analysis", "design"}:
        return errors
    result = normalize_text(data.get("result"))
    gaps = data.get("coverageGaps") if isinstance(data.get("coverageGaps"), list) else []
    map_path = fact_coverage_map_path(run_dir, scope)
    if not map_path.exists():
        errors.append(f"{relative}: 缺少对应 FACT 覆盖证据图: {map_path.relative_to(run_dir)}")
        return errors
    try:
        coverage_map = load_json(map_path)
    except Exception as exc:
        errors.append(f"{relative}: 无法读取对应 FACT 覆盖证据图: {exc}")
        return errors
    map_gaps = [
        normalize_text(item.get("factId"))
        for item in coverage_map.get("factCoverage", [])
        if isinstance(item, dict) and item.get("coverageStatus") == "gap"
    ]
    if result == "通过":
        if gaps:
            errors.append(f"{relative}: coverage-review result=通过 时 coverageGaps 必须为空")
        if map_gaps:
            errors.append(f"{relative}: coverage-review result=通过 时 fact-coverage-map 不得保留 gap: {', '.join(map_gaps)}")
    elif map_gaps and not gaps:
        errors.append(f"{relative}: fact-coverage-map 存在 gap 但 coverageGaps 为空: {', '.join(map_gaps)}")
    return errors


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="校验 run 目录内 JSON canonical 产物")
    parser.add_argument("run_dir", type=Path, help="outputs/runs/<run-id>")
    args = parser.parse_args()

    run_dir = args.run_dir
    if not run_dir.is_dir():
        print(f"失败: 运行目录不存在: {run_dir}")
        return 1

    errors: list[str] = []
    warnings: list[str] = []
    for relative in REQUIRED_PROCESS_JSON:
        if not (run_dir / relative).exists():
            errors.append(f"缺少固定 JSON 运行产物: {relative}")

    analysis_json = run_dir / "deliverables" / "test-analysis-solution.json"
    design_json = run_dir / "deliverables" / "test-design-solution.json"
    if not analysis_json.exists() and not design_json.exists():
        errors.append("缺少主交付件 JSON: deliverables/test-analysis-solution.json 或 deliverables/test-design-solution.json")
    if analysis_json.exists() and not has_any(run_dir, ["process/analysis-task-list.json", "process/task-list.json"]):
        errors.append("测试分析 run 缺少任务清单: process/analysis-task-list.json")
    if design_json.exists() and not has_any(run_dir, ["process/design-task-list.json", "process/task-list.json"]):
        errors.append("测试设计 run 缺少任务清单: process/design-task-list.json")
    if analysis_json.exists() and not (run_dir / "process" / "input-fact-model.json").exists():
        errors.append("测试分析 run 缺少固定 JSON 运行产物: process/input-fact-model.json")
    if analysis_json.exists() and not (run_dir / "process" / "scenario-tree.json").exists():
        errors.append("测试分析 run 缺少分层冻结产物: process/scenario-tree.json")
    if analysis_json.exists() and not (run_dir / "process" / "test-point-work-items.json").exists():
        errors.append("测试分析 run 缺少分层冻结产物: process/test-point-work-items.json")
    if design_json.exists() and not (run_dir / "process" / "test-case-work-items.json").exists():
        errors.append("测试设计 run 缺少分层冻结产物: process/test-case-work-items.json")
    for scope, solution_exists in (("analysis", analysis_json.exists()), ("design", design_json.exists())):
        if not solution_exists:
            continue
        review_path = coverage_review_path(run_dir, scope)
        report_path = final_report_path(run_dir, scope)
        map_path = fact_coverage_map_path(run_dir, scope)
        if (review_path.exists() or report_path.exists()) and not map_path.exists():
            errors.append(f"{scope} run 缺少覆盖证据过程件: {map_path.relative_to(run_dir)}")
        if coverage_review_result(run_dir, scope) == "通过" and not report_path.exists():
            errors.append(f"{scope} coverage-review 已通过，但缺少最终人审报告: {report_path.relative_to(run_dir)}")

    json_files = [json_path for json_path, _markdown_path in collect_renderable_json_files(run_dir)]
    seen = set(json_files)
    for required in REQUIRED_PROCESS_JSON:
        path = run_dir / required
        if path.exists() and path not in seen:
            json_files.append(path)
            seen.add(path)
    for path in (analysis_json, design_json):
        if path.exists() and path not in seen:
            json_files.append(path)
            seen.add(path)

    for path in sorted(json_files):
        try:
            data = load_json(path)
        except Exception as exc:
            errors.append(f"{path.relative_to(run_dir)} 不是合法 JSON: {exc}")
            continue
        artifact_errors, artifact_warnings = validate_artifact(data)
        errors.extend(f"{path.relative_to(run_dir)}: {error}" for error in artifact_errors)
        warnings.extend(f"{path.relative_to(run_dir)}: {warning}" for warning in artifact_warnings)
        errors.extend(validate_coverage_gap_locations(run_dir, path.relative_to(run_dir), data))
        errors.extend(validate_final_report_links(run_dir, path.relative_to(run_dir), data))
        errors.extend(validate_final_report_matches_map(run_dir, path.relative_to(run_dir), data))
        errors.extend(validate_fact_coverage_map_links(run_dir, path.relative_to(run_dir), data))
        errors.extend(validate_coverage_review_consistency(run_dir, path.relative_to(run_dir), data))

    task_json = (
        run_dir / "process" / "analysis-task-list.json"
        if (run_dir / "process" / "analysis-task-list.json").exists()
        else run_dir / "process" / "task-list.json"
    )
    if task_json.exists():
        try:
            task_data = load_json(task_json)
        except Exception:
            task_data = {}
        normalize_done = any(
            stage.get("stage") == "输入文档归一化" and stage.get("status") == "done"
            for stage in task_data.get("stages", [])
            if isinstance(stage, dict)
        )
        if normalize_done and not (run_dir / "inputs" / "input-normalization-manifest.json").exists():
            errors.append("输入文档归一化已完成，但缺少 inputs/input-normalization-manifest.json")

    for warning in warnings:
        print(f"警告: {warning}")
    for error in errors:
        print(f"失败: {error}")
    if errors:
        return 1
    print(f"通过: {run_dir} JSON canonical 产物校验通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
