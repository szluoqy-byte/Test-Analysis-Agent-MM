#!/usr/bin/env python3
"""Check consistency between Markdown process evidence and result JSON deliverables."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from encoding_utils import configure_stdio
from markdown_process import ids_in_markdown, parse_scenario_headings, read_markdown, require_markdown, review_result
from run_artifacts import load_json, render_json_artifact


def flatten_scenarios(nodes: list[Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        result.append(node)
        children = node.get("children")
        if isinstance(children, list) and children:
            result.extend(flatten_scenarios(children))
    return result


def base_point(point: dict[str, Any]) -> dict[str, Any]:
    return {key: point.get(key) for key in ("id", "title", "objective", "basisRefs", "note") if key in point}


def check_render(run_dir: Path, json_path: Path, errors: list[str]) -> None:
    markdown = json_path.with_suffix(".md")
    if not markdown.is_file():
        errors.append(f"缺少结果人读版: {markdown.relative_to(run_dir).as_posix()}")
        return
    expected = render_json_artifact(load_json(json_path), json_path)
    if read_markdown(markdown) != expected:
        errors.append(f"结果 Markdown 与 JSON 不一致: {markdown.relative_to(run_dir).as_posix()}")


def check_work_items(run_dir: Path, scope: str, errors: list[str]) -> None:
    if scope == "analysis":
        work_path = run_dir / "process/test-point-work-items.json"
        id_key = "leafScenarioId"
        slice_dir = run_dir / "process/test-point-slices"
        review_dir = run_dir / "process/reviews/test-point-reviews"
    else:
        work_path = run_dir / "process/test-case-work-items.json"
        id_key = "testPointId"
        slice_dir = run_dir / "process/test-case-slices"
        review_dir = run_dir / "process/reviews/test-case-reviews"
    if not work_path.is_file():
        errors.append(f"缺少控制工作项: {work_path.relative_to(run_dir).as_posix()}")
        return
    data = load_json(work_path)
    for item in data.get("workItems", []):
        if not isinstance(item, dict):
            continue
        current_id = str(item.get(id_key) or "")
        if item.get("status") != "done":
            errors.append(f"{scope} 工作项未完成: {current_id} status={item.get('status')}")
        slice_path = slice_dir / f"{current_id}.md"
        review_path = review_dir / f"{current_id}.md"
        errors.extend(require_markdown(slice_path))
        errors.extend(require_markdown(review_path))
        if review_path.is_file() and review_result(review_path) != "通过":
            errors.append(f"{current_id} 切片评审未通过")


def check_review(path: Path, errors: list[str]) -> None:
    errors.extend(require_markdown(path))
    if path.is_file() and review_result(path) != "通过":
        errors.append(f"评审结论未通过: {path}")


def check_fact_trace(run_dir: Path, scope: str, errors: list[str]) -> None:
    facts_path = run_dir / "process/input-fact-model.md"
    coverage_path = run_dir / "process" / f"{scope}-fact-coverage-map.md"
    report_path = run_dir / "reports" / f"{scope}-final-report.md"
    errors.extend(require_markdown(coverage_path))
    errors.extend(require_markdown(report_path))
    if not facts_path.is_file() or not coverage_path.is_file() or not report_path.is_file():
        return
    facts = set(ids_in_markdown(facts_path, "FACT"))
    coverage = set(ids_in_markdown(coverage_path, "FACT"))
    report = set(ids_in_markdown(report_path, "FACT"))
    missing_coverage = sorted(facts - coverage)
    missing_report = sorted(facts - report)
    if missing_coverage:
        errors.append(f"{scope} 覆盖证据缺少 FACT: {', '.join(missing_coverage)}")
    if missing_report:
        errors.append(f"{scope} 最终报告缺少 FACT: {', '.join(missing_report)}")


def design_analysis_source(run_dir: Path) -> Path:
    root = Path(__file__).resolve().parents[1]
    work_items_path = run_dir / "process/test-case-work-items.json"
    if work_items_path.is_file():
        source = str(load_json(work_items_path).get("analysisSource") or "").strip()
        if source:
            path = Path(source)
            return path if path.is_absolute() else root / path
    return run_dir / "deliverables/test-analysis-solution.json"


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="检查 Markdown 过程件与结果 JSON 一致性")
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    run_dir = args.run_dir
    if not run_dir.is_dir():
        print(f"失败: 运行目录不存在: {run_dir}")
        return 1
    errors: list[str] = []
    analysis_path = run_dir / "deliverables/test-analysis-solution.json"
    design_path = run_dir / "deliverables/test-design-solution.json"

    if analysis_path.is_file():
        for rel in ("process/rules-pack.md", "process/context-pack.md", "process/input-fact-model.md", "process/scenario-tree.md"):
            errors.extend(require_markdown(run_dir / rel))
        check_render(run_dir, analysis_path, errors)
        check_work_items(run_dir, "analysis", errors)
        check_review(run_dir / "process/reviews/test-analysis-solution-review.md", errors)
        check_review(run_dir / "process/reviews/analysis-coverage-review.md", errors)
        check_fact_trace(run_dir, "analysis", errors)
        scenario_path = run_dir / "process/scenario-tree.md"
        if scenario_path.is_file():
            process_ids = [item.scenario_id for item in parse_scenario_headings(read_markdown(scenario_path))]
            solution_ids = [str(item.get("id") or "") for item in flatten_scenarios(load_json(analysis_path).get("scenarios", []))]
            if process_ids != solution_ids:
                errors.append("测试分析结果中的 SC 树与 process/scenario-tree.md 不一致")

    if design_path.is_file():
        upstream_analysis = design_analysis_source(run_dir)
        if not upstream_analysis.is_file():
            errors.append(f"测试设计结果缺少上游分析结果: {upstream_analysis}")
        check_render(run_dir, design_path, errors)
        check_work_items(run_dir, "design", errors)
        check_review(run_dir / "process/reviews/test-design-solution-review.md", errors)
        check_review(run_dir / "process/reviews/design-coverage-review.md", errors)
        check_fact_trace(run_dir, "design", errors)
        if upstream_analysis.is_file():
            analysis_nodes = flatten_scenarios(load_json(upstream_analysis).get("scenarios", []))
            design_nodes = flatten_scenarios(load_json(design_path).get("scenarios", []))
            if len(analysis_nodes) != len(design_nodes):
                errors.append("测试设计结果未完整继承分析方案的 SC 树")
            else:
                for analysis_node, design_node in zip(analysis_nodes, design_nodes):
                    for key in ("id", "title", "fields"):
                        if analysis_node.get(key) != design_node.get(key):
                            errors.append(f"设计方案 SC {design_node.get('id')} 未继承分析字段 {key}")
                    if not analysis_node.get("children"):
                        analysis_points = [base_point(item) for item in analysis_node.get("testPoints", []) if isinstance(item, dict)]
                        design_points = [base_point(item) for item in design_node.get("testPoints", []) if isinstance(item, dict)]
                        if analysis_points != design_points:
                            errors.append(f"设计方案 {design_node.get('id')} 未完整继承分析 TP")

    for path in run_dir.glob("process/**/*.json"):
        if path.name in {
            "id-registry.json",
            "test-point-work-items.json",
            "test-case-work-items.json",
        }:
            continue
        errors.append(f"发现不允许的语义过程 JSON: {path.relative_to(run_dir).as_posix()}")

    for error in errors:
        print(f"失败: {error}")
    if errors:
        return 1
    print(f"通过: {run_dir} 过程与结果一致性检查通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
