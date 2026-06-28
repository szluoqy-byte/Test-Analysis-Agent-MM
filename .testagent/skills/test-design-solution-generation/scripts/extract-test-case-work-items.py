#!/usr/bin/env python3
"""Create TP work items for staged TC generation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

BIN_DIR = Path(__file__).resolve().parents[3] / "bin"
if str(BIN_DIR) not in sys.path:
    sys.path.insert(0, str(BIN_DIR))

from run_artifacts import dump_json, load_json
from staged_workflow import render_markdown_for_json


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def resolve_path(path: Path, root: Path) -> Path:
    return path if path.is_absolute() else root / path


def rel_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def load_existing_statuses(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    try:
        data = load_json(path)
    except Exception:
        return {}
    statuses: dict[str, dict[str, str]] = {}
    for item in data.get("workItems", []):
        if isinstance(item, dict) and item.get("testPointId"):
            statuses[str(item["testPointId"])] = {
                "status": str(item.get("status") or "pending"),
                "slicePath": str(item.get("slicePath") or ""),
                "mergedAt": str(item.get("mergedAt") or ""),
            }
    return statuses


def iter_items(nodes: list[Any], scenario_path: list[dict[str, str]] | None = None) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    current_path = scenario_path or []
    for scenario in nodes:
        if not isinstance(scenario, dict):
            continue
        next_path = current_path + [{"id": str(scenario.get("id", "")), "title": str(scenario.get("title", ""))}]
        children = scenario.get("children")
        if isinstance(children, list) and children:
            items.extend(iter_items(children, next_path))
            continue
        for point in scenario.get("testPoints", []):
            if not isinstance(point, dict):
                continue
            items.append(
                {
                    "scenarioPath": next_path,
                    "leafScenarioId": next_path[-1]["id"] if next_path else "",
                    "leafScenarioTitle": next_path[-1]["title"] if next_path else "",
                    "testPointId": str(point.get("id", "")),
                    "testPointTitle": str(point.get("title", "")),
                    "objective": str(point.get("objective", "")),
                    "basisRefs": point.get("basisRefs", []),
                    "status": "pending",
                    "slicePath": "",
                    "mergedAt": "",
                }
            )
    return items


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="生成 TP 到 TC 的工作项索引")
    parser.add_argument("run_dir", type=Path, help="outputs/runs/<run-id>")
    parser.add_argument("--analysis", type=Path, help="分析方案 JSON，默认 deliverables/test-analysis-solution.json")
    parser.add_argument("--output", type=Path, help="输出路径，默认 process/test-case-work-items.json")
    args = parser.parse_args()

    root = repo_root()
    run_dir = resolve_path(args.run_dir, root)
    analysis_path = resolve_path(args.analysis, root) if args.analysis else run_dir / "deliverables" / "test-analysis-solution.json"
    output_path = resolve_path(args.output, root) if args.output else run_dir / "process" / "test-case-work-items.json"
    if not analysis_path.exists():
        print(f"失败: 分析方案不存在: {analysis_path}", file=sys.stderr)
        return 1
    analysis = load_json(analysis_path)
    if analysis.get("artifactType") != "test-analysis-solution":
        print("失败: --analysis 必须是 test-analysis-solution JSON", file=sys.stderr)
        return 1

    existing = load_existing_statuses(output_path)
    items = iter_items(analysis.get("scenarios", []))
    for item in items:
        previous = existing.get(item["testPointId"], {})
        item["status"] = previous.get("status", item["status"])
        item["slicePath"] = previous.get("slicePath", item["slicePath"])
        item["mergedAt"] = previous.get("mergedAt", item["mergedAt"])
    data = {
        "artifactType": "test-case-work-items",
        "schemaVersion": "1.0",
        "title": "测试用例生成工作项索引",
        "runDir": rel_path(run_dir, root),
        "analysisSource": rel_path(analysis_path, root),
        "totalTestPoints": len(items),
        "workItems": items,
    }
    dump_json(output_path, data)
    render_markdown_for_json(output_path)
    print(f"通过: 已生成 {rel_path(output_path, root)}，TP {len(items)} 个")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
