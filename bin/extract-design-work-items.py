#!/usr/bin/env python3
"""Create a lightweight TP work-item index for batched test design generation."""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Any

from run_artifacts import dump_json, load_json


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_run_dir(path: Path) -> Path:
    return path if path.is_absolute() else repo_root() / path


def rel_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def load_existing_statuses(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        data = load_json(path)
    except Exception:
        return {}
    statuses: dict[str, str] = {}
    for item in data.get("workItems", []):
        if isinstance(item, dict) and item.get("testPointId"):
            statuses[str(item["testPointId"])] = str(item.get("status") or "pending")
    return statuses


def iter_work_items(
    scenarios: list[Any],
    scenario_path: list[dict[str, str]] | None = None,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    current_path = scenario_path or []
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            continue
        next_path = current_path + [
            {
                "id": str(scenario.get("id", "")),
                "title": str(scenario.get("title", "")),
            }
        ]
        children = scenario.get("children")
        if isinstance(children, list) and children:
            items.extend(iter_work_items(children, next_path))
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


def build_batches(items: list[dict[str, Any]], batch_size: int) -> list[dict[str, Any]]:
    batches: list[dict[str, Any]] = []
    total_batches = math.ceil(len(items) / batch_size) if items else 0
    for index in range(total_batches):
        batch_items = items[index * batch_size : (index + 1) * batch_size]
        batches.append(
            {
                "id": f"batch-{index + 1:03d}",
                "status": "pending",
                "testPointIds": [item["testPointId"] for item in batch_items],
                "itemCount": len(batch_items),
            }
        )
    return batches


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="生成测试设计分批工作项索引")
    parser.add_argument("run_dir", type=Path, help="outputs/runs/<run-id>")
    parser.add_argument("--analysis", type=Path, help="分析方案 JSON，默认读取 run deliverables")
    parser.add_argument("--output", type=Path, help="输出路径，默认 process/design-work-items.json")
    parser.add_argument("--batch-size", type=int, default=8, help="每批测试点数量，默认 8")
    args = parser.parse_args()

    if args.batch_size <= 0:
        print("失败: --batch-size 必须大于 0", file=sys.stderr)
        return 2

    root = repo_root()
    run_dir = resolve_run_dir(args.run_dir)
    analysis_path = args.analysis or run_dir / "deliverables" / "test-analysis-solution.json"
    if not analysis_path.is_absolute():
        analysis_path = root / analysis_path
    output_path = args.output or run_dir / "process" / "design-work-items.json"
    if not output_path.is_absolute():
        output_path = root / output_path

    if not run_dir.is_dir():
        print(f"失败: 运行目录不存在: {run_dir}", file=sys.stderr)
        return 1
    if not analysis_path.exists():
        print(f"失败: 分析方案不存在: {analysis_path}", file=sys.stderr)
        return 1

    analysis = load_json(analysis_path)
    if analysis.get("artifactType") != "test-analysis-solution":
        print("失败: --analysis 必须是 test-analysis-solution JSON", file=sys.stderr)
        return 1

    existing_statuses = load_existing_statuses(output_path)
    items = iter_work_items(analysis.get("scenarios", []))
    for item in items:
        item["status"] = existing_statuses.get(item["testPointId"], item["status"])
    batches = build_batches(items, args.batch_size)
    status_by_tp = {item["testPointId"]: item["status"] for item in items}
    for batch in batches:
        statuses = {status_by_tp.get(tp_id, "pending") for tp_id in batch["testPointIds"]}
        batch["status"] = "done" if statuses == {"done"} else "in_progress" if "done" in statuses else "pending"

    data = {
        "artifactType": "design-work-items",
        "schemaVersion": "1.0",
        "title": "测试设计分批工作项索引",
        "runDir": rel_path(run_dir, root),
        "analysisSource": rel_path(analysis_path, root),
        "batchSize": args.batch_size,
        "totalTestPoints": len(items),
        "totalBatches": len(batches),
        "batches": batches,
        "workItems": items,
    }
    dump_json(output_path, data)
    print(
        "通过: 已生成 "
        f"{rel_path(output_path, root)}，测试点 {len(items)} 个，批次 {len(batches)} 个"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
