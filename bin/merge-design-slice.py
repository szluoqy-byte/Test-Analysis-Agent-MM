#!/usr/bin/env python3
"""Merge a batched test-design slice into deliverables/test-design-solution.json."""

from __future__ import annotations

import argparse
from datetime import datetime
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


def clone_analysis_point(point: dict[str, Any]) -> dict[str, Any]:
    cloned = {
        key: point.get(key)
        for key in ("id", "title", "objective", "basisRefs", "note")
        if key in point
    }
    cloned["testCases"] = []
    return cloned


def design_skeleton_from_analysis(analysis: dict[str, Any], analysis_path: Path, root: Path) -> dict[str, Any]:
    def clone_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
        cloned = {
            key: scenario.get(key)
            for key in ("id", "title", "fields")
            if key in scenario
        }
        children = scenario.get("children")
        if isinstance(children, list) and children:
            cloned["children"] = [clone_scenario(child) for child in children if isinstance(child, dict)]
        else:
            cloned["children"] = []
            cloned["testPoints"] = [
                clone_analysis_point(point)
                for point in scenario.get("testPoints", [])
                if isinstance(point, dict)
            ]
        return cloned

    title = str(analysis.get("title") or "测试设计方案")
    title = title.replace("测试分析方案", "测试设计方案")
    if "测试设计方案" not in title:
        title += " 测试设计方案"
    return {
        "artifactType": "test-design-solution",
        "schemaVersion": "2.0",
        "title": title,
        "inputs": [
            {"field": "测试分析方案来源", "content": rel_path(analysis_path, root)},
            {"field": "需求来源", "content": ""},
            {"field": "设计方案来源", "content": ""},
            {"field": "设计范围", "content": "按测试分析方案中的 TP 分批生成测试用例。"},
            {"field": "不覆盖内容", "content": ""},
        ],
        "scenarios": [
            clone_scenario(scenario)
            for scenario in analysis.get("scenarios", [])
            if isinstance(scenario, dict)
        ],
    }


def iter_points(scenarios: list[Any]) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            continue
        children = scenario.get("children")
        if isinstance(children, list) and children:
            points.extend(iter_points(children))
        else:
            points.extend(point for point in scenario.get("testPoints", []) if isinstance(point, dict))
    return points


def point_map(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(point.get("id")): point for point in iter_points(data.get("scenarios", []))}


def merge_cases(target: dict[str, Any], slice_data: dict[str, Any]) -> list[str]:
    target_points = point_map(target)
    merged: list[str] = []
    for source_point in iter_points(slice_data.get("scenarios", [])):
        point_id = str(source_point.get("id", ""))
        if not point_id:
            continue
        if point_id not in target_points:
            raise ValueError(f"切片包含目标设计方案不存在的测试点: {point_id}")
        cases = source_point.get("testCases")
        if not isinstance(cases, list) or not cases:
            raise ValueError(f"{point_id} 切片缺少非空 testCases[]")
        target_points[point_id]["testCases"] = cases
        merged.append(point_id)
    return merged


def renumber_test_cases(data: dict[str, Any]) -> None:
    index = 1
    for point in iter_points(data.get("scenarios", [])):
        cases = point.get("testCases")
        if not isinstance(cases, list):
            continue
        for case in cases:
            if isinstance(case, dict):
                case["id"] = f"TC-{index:03d}"
                index += 1


def update_work_items(run_dir: Path, merged_tp_ids: list[str], root: Path) -> None:
    work_items_path = run_dir / "process" / "design-work-items.json"
    if not work_items_path.exists():
        return
    data = load_json(work_items_path)
    merged_set = set(merged_tp_ids)
    now = datetime.now().isoformat(timespec="seconds")
    status_by_tp: dict[str, str] = {}
    for item in data.get("workItems", []):
        if not isinstance(item, dict):
            continue
        tp_id = str(item.get("testPointId", ""))
        if tp_id in merged_set:
            item["status"] = "done"
            item["mergedAt"] = now
        status_by_tp[tp_id] = str(item.get("status") or "pending")
    for batch in data.get("batches", []):
        if not isinstance(batch, dict):
            continue
        statuses = {status_by_tp.get(str(tp_id), "pending") for tp_id in batch.get("testPointIds", [])}
        if statuses == {"done"}:
            batch["status"] = "done"
        elif "done" in statuses:
            batch["status"] = "in_progress"
    dump_json(work_items_path, data)
    print(f"通过: 已更新 {rel_path(work_items_path, root)}")


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="合并测试设计分批切片")
    parser.add_argument("run_dir", type=Path, help="outputs/runs/<run-id>")
    parser.add_argument("--slice", required=True, type=Path, help="包含 testCases[] 的设计切片 JSON")
    parser.add_argument("--analysis", type=Path, help="分析方案 JSON，默认读取 run deliverables")
    parser.add_argument("--target", type=Path, help="目标设计方案 JSON，默认 deliverables/test-design-solution.json")
    parser.add_argument("--no-renumber", action="store_true", help="不重新全局编号 TC")
    args = parser.parse_args()

    root = repo_root()
    run_dir = resolve_path(args.run_dir, root)
    slice_path = resolve_path(args.slice, root)
    analysis_path = resolve_path(args.analysis, root) if args.analysis else run_dir / "deliverables" / "test-analysis-solution.json"
    target_path = resolve_path(args.target, root) if args.target else run_dir / "deliverables" / "test-design-solution.json"

    if not slice_path.exists():
        print(f"失败: 切片不存在: {slice_path}", file=sys.stderr)
        return 1
    if target_path.exists():
        target = load_json(target_path)
    else:
        if not analysis_path.exists():
            print(f"失败: 目标不存在且无法初始化，分析方案不存在: {analysis_path}", file=sys.stderr)
            return 1
        target = design_skeleton_from_analysis(load_json(analysis_path), analysis_path, root)

    slice_data = load_json(slice_path)
    try:
        merged_tp_ids = merge_cases(target, slice_data)
    except ValueError as exc:
        print(f"失败: {exc}", file=sys.stderr)
        return 1
    if not args.no_renumber:
        renumber_test_cases(target)
    dump_json(target_path, target)
    print(f"通过: 已合并 {len(merged_tp_ids)} 个 TP 到 {rel_path(target_path, root)}")
    update_work_items(run_dir, merged_tp_ids, root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
