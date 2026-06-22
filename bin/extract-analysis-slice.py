#!/usr/bin/env python3
"""Extract a small analysis JSON slice for one design batch."""

from __future__ import annotations

import argparse
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


def resolve_path(path: Path, root: Path) -> Path:
    return path if path.is_absolute() else root / path


def rel_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def collect_tp_ids_from_batch(work_items: dict[str, Any], batch_id: str) -> list[str]:
    for batch in work_items.get("batches", []):
        if isinstance(batch, dict) and batch.get("id") == batch_id:
            return [str(item) for item in batch.get("testPointIds", []) if item]
    return []


def first_pending_batch(work_items: dict[str, Any]) -> str:
    for batch in work_items.get("batches", []):
        if isinstance(batch, dict) and batch.get("status") != "done":
            return str(batch.get("id", ""))
    return ""


def prune_scenarios(scenarios: list[Any], selected_tp_ids: set[str]) -> list[dict[str, Any]]:
    pruned: list[dict[str, Any]] = []
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            continue
        children = scenario.get("children")
        copied = {
            key: value
            for key, value in scenario.items()
            if key in {"id", "title", "fields", "children", "testPoints"}
        }
        if isinstance(children, list) and children:
            child_nodes = prune_scenarios(children, selected_tp_ids)
            if child_nodes:
                copied["children"] = child_nodes
                copied.pop("testPoints", None)
                pruned.append(copied)
            continue
        points = [
            point
            for point in scenario.get("testPoints", [])
            if isinstance(point, dict) and str(point.get("id")) in selected_tp_ids
        ]
        if points:
            copied["children"] = []
            copied["testPoints"] = points
            pruned.append(copied)
    return pruned


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="抽取测试分析方案切片供测试设计分批生成")
    parser.add_argument("run_dir", type=Path, help="outputs/runs/<run-id>")
    parser.add_argument("--analysis", type=Path, help="分析方案 JSON，默认读取 run deliverables")
    parser.add_argument("--work-items", type=Path, help="工作项索引，默认 process/design-work-items.json")
    parser.add_argument("--batch", default="", help="批次 ID，例如 batch-001；未提供时使用第一个未完成批次")
    parser.add_argument("--tp", action="append", default=[], help="指定 TP，可重复；优先于 --batch")
    parser.add_argument("--output", type=Path, help="输出切片路径，默认 process/design-slices/<batch>.json")
    parser.add_argument("--stdout", action="store_true", help="打印 JSON 到 stdout，不写文件")
    args = parser.parse_args()

    root = repo_root()
    run_dir = resolve_path(args.run_dir, root)
    analysis_path = resolve_path(args.analysis, root) if args.analysis else run_dir / "deliverables" / "test-analysis-solution.json"
    work_items_path = resolve_path(args.work_items, root) if args.work_items else run_dir / "process" / "design-work-items.json"

    if not analysis_path.exists():
        print(f"失败: 分析方案不存在: {analysis_path}", file=sys.stderr)
        return 1
    if not work_items_path.exists():
        print(
            "失败: 工作项索引不存在，请先运行 "
            f"python bin/extract-design-work-items.py {rel_path(run_dir, root)}",
            file=sys.stderr,
        )
        return 1

    analysis = load_json(analysis_path)
    work_items = load_json(work_items_path)
    batch_id = args.batch
    selected_tp_ids: list[str] = []
    for value in args.tp:
        for raw_tp_id in value.split(","):
            tp_id = raw_tp_id.strip()
            if tp_id:
                selected_tp_ids.append(tp_id)
    if not selected_tp_ids:
        if not batch_id:
            batch_id = first_pending_batch(work_items)
        selected_tp_ids = collect_tp_ids_from_batch(work_items, batch_id)
    if not selected_tp_ids:
        print("失败: 未找到可抽取的 TP", file=sys.stderr)
        return 1

    selected_set = set(selected_tp_ids)
    scenarios = prune_scenarios(analysis.get("scenarios", []), selected_set)
    if not scenarios:
        print("失败: 指定 TP 在分析方案中不存在: " + "、".join(selected_tp_ids), file=sys.stderr)
        return 1

    slice_id = batch_id or "custom-" + "-".join(selected_tp_ids)
    data = {
        "artifactType": "test-design-analysis-slice",
        "schemaVersion": "1.0",
        "title": f"测试设计分析切片 {slice_id}",
        "runDir": rel_path(run_dir, root),
        "analysisSource": rel_path(analysis_path, root),
        "workItemsSource": rel_path(work_items_path, root),
        "batchId": batch_id,
        "testPointIds": selected_tp_ids,
        "analysisTitle": analysis.get("title", ""),
        "scope": analysis.get("scope", []),
        "scenarios": scenarios,
        "instructions": [
            "仅为本切片中的 TP 生成 testCases[]。",
            "输出可交给 bin/merge-design-slice.py 的 test-design-solution-slice JSON。",
        ],
    }

    if args.stdout:
        import json

        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    output_path = args.output
    if output_path is None:
        safe_name = slice_id or "slice"
        output_path = run_dir / "process" / "design-slices" / f"{safe_name}.json"
    output_path = resolve_path(output_path, root)
    dump_json(output_path, data)
    print(f"通过: 已生成 {rel_path(output_path, root)}，包含 TP: {', '.join(selected_tp_ids)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
