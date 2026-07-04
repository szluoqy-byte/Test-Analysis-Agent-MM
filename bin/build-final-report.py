#!/usr/bin/env python3
"""Build or refresh final human-review fact coverage reports."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from encoding_utils import configure_stdio
from run_artifacts import dump_json, load_json, normalize_text
from staged_workflow import render_markdown_for_json


STATUS_VALUES = {"covered", "partial", "missing", "not_applicable"}


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


def report_paths(run_dir: Path, scope: str) -> tuple[Path, Path]:
    return run_dir / "reports" / f"{scope}-final-report.json", run_dir / "reports" / f"{scope}-final-report.md"


def target_artifacts(run_dir: Path, scope: str) -> dict[str, str]:
    artifacts = {"inputFactModel": "process/input-fact-model.json"}
    analysis_path = run_dir / "deliverables" / "test-analysis-solution.json"
    design_path = run_dir / "deliverables" / "test-design-solution.json"
    coverage_relative = f"process/reviews/{scope}-coverage-review.json"
    coverage_path = run_dir / coverage_relative
    if analysis_path.exists():
        artifacts["analysisSolution"] = "deliverables/test-analysis-solution.json"
    if scope == "design" and design_path.exists():
        artifacts["designSolution"] = "deliverables/test-design-solution.json"
    if coverage_path.exists():
        artifacts["coverageReview"] = coverage_relative
    return artifacts


def existing_coverage(report_path: Path) -> dict[str, dict[str, Any]]:
    if not report_path.exists():
        return {}
    data = load_json(report_path)
    coverage = data.get("factCoverage", [])
    if not isinstance(coverage, list):
        return {}
    return {
        normalize_text(item.get("factId")): item
        for item in coverage
        if isinstance(item, dict) and item.get("factId")
    }


def coverage_row(fact: dict[str, Any], existing: dict[str, Any] | None, scope: str) -> dict[str, Any]:
    existing = existing or {}
    status = existing.get("coverageStatus", "missing")
    if status not in STATUS_VALUES:
        status = "missing"
    return {
        "factId": fact["factId"],
        "inputSource": fact["inputSource"],
        "factSummary": fact.get("factSummary", ""),
        "condition": fact.get("condition", ""),
        "observableResult": fact.get("observableResult", ""),
        "coveredScenarios": existing.get("coveredScenarios", []) if isinstance(existing.get("coveredScenarios", []), list) else [],
        "coveredTestPoints": existing.get("coveredTestPoints", []) if isinstance(existing.get("coveredTestPoints", []), list) else [],
        "coveredTestCases": existing.get("coveredTestCases", []) if isinstance(existing.get("coveredTestCases", []), list) else [],
        "coverageStatus": status,
        "reviewNote": existing.get("reviewNote", "待最终审阅填写覆盖结论"),
    }


def build_summary(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "totalFacts": len(rows),
        "coveredFacts": sum(1 for row in rows if row.get("coverageStatus") == "covered"),
        "partialFacts": sum(1 for row in rows if row.get("coverageStatus") == "partial"),
        "missingFacts": sum(1 for row in rows if row.get("coverageStatus") == "missing"),
        "notApplicableFacts": sum(1 for row in rows if row.get("coverageStatus") == "not_applicable"),
    }


def build_report(run_dir: Path, scope: str) -> Path:
    input_fact_path = run_dir / "process" / "input-fact-model.json"
    if not input_fact_path.exists():
        raise FileNotFoundError(f"缺少输入事实模型: {input_fact_path}")
    if scope == "analysis" and not (run_dir / "deliverables" / "test-analysis-solution.json").exists():
        raise FileNotFoundError("缺少分析方案: deliverables/test-analysis-solution.json")
    if scope == "design" and not (run_dir / "deliverables" / "test-design-solution.json").exists():
        raise FileNotFoundError("缺少设计方案: deliverables/test-design-solution.json")

    report_path, _ = report_paths(run_dir, scope)
    facts = collect_facts(load_json(input_fact_path))
    existing = existing_coverage(report_path)
    rows = [coverage_row(fact, existing.get(fact["factId"]), scope) for fact in facts]
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
