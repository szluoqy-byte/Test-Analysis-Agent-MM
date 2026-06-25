#!/usr/bin/env python3
"""Merge one TP slice into deliverables/test-analysis-solution.json."""

from __future__ import annotations

import argparse
from datetime import datetime
import re
import sys
from pathlib import Path
from typing import Any

from run_artifacts import dump_json, load_json


POINT_KEYS = {"id", "title", "objective", "basisRefs", "note"}


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


def clone_scenario_tree_node(node: dict[str, Any]) -> dict[str, Any]:
    cloned = {key: node.get(key) for key in ("id", "title", "fields") if key in node}
    children = node.get("children")
    if isinstance(children, list) and children:
        cloned["children"] = [clone_scenario_tree_node(child) for child in children if isinstance(child, dict)]
    else:
        cloned["children"] = []
        cloned["testPoints"] = []
    return cloned


def analysis_skeleton_from_scenario_tree(tree: dict[str, Any], tree_path: Path, root: Path) -> dict[str, Any]:
    return {
        "artifactType": "test-analysis-solution",
        "schemaVersion": "2.0",
        "title": str(tree.get("title") or "测试分析方案").replace("场景树", "测试分析方案"),
        "scope": tree.get("scope", []),
        "inputs": [
            {"field": "场景树来源", "content": rel_path(tree_path, root)},
            {"field": "生成方式", "content": "SC 先冻结，再按叶子 SC 合并测试点。"},
        ],
        "scenarios": [
            clone_scenario_tree_node(node)
            for node in tree.get("scenarios", [])
            if isinstance(node, dict)
        ],
    }


def iter_leaf_scenarios(nodes: list[Any]) -> list[dict[str, Any]]:
    leaves: list[dict[str, Any]] = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        children = node.get("children")
        if isinstance(children, list) and children:
            leaves.extend(iter_leaf_scenarios(children))
        else:
            leaves.append(node)
    return leaves


def leaf_map(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(node.get("id")): node for node in iter_leaf_scenarios(data.get("scenarios", []))}


def normalize_point(point: dict[str, Any]) -> dict[str, Any]:
    normalized = {key: point.get(key) for key in POINT_KEYS if key in point}
    normalized.setdefault("basisRefs", [])
    return normalized


def validate_slice(slice_data: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    if slice_data.get("artifactType") != "test-point-slice":
        raise ValueError("切片 artifactType 必须为 test-point-slice")
    leaf_id = str(slice_data.get("leafScenarioId") or "")
    scenario = slice_data.get("scenario")
    if not isinstance(scenario, dict):
        raise ValueError("切片缺少 scenario 对象")
    if scenario.get("id") != leaf_id:
        raise ValueError(f"切片 scenario.id 必须等于 leafScenarioId: {leaf_id}")
    if scenario.get("children") not in ([], None):
        raise ValueError(f"{leaf_id} 是叶子 SC 切片，不得包含 children")
    points = scenario.get("testPoints")
    if not isinstance(points, list) or not points:
        raise ValueError(f"{leaf_id} 缺少非空 testPoints[]")
    if not any(isinstance(point, dict) and point.get("title") == "E2E场景测试" for point in points):
        raise ValueError(f"{leaf_id} 缺少 E2E场景测试")
    normalized_points: list[dict[str, Any]] = []
    for index, point in enumerate(points, start=1):
        if not isinstance(point, dict):
            raise ValueError(f"{leaf_id} testPoints[{index}] 不是对象")
        extra = sorted(set(point) - POINT_KEYS)
        if extra:
            raise ValueError(f"{leaf_id} testPoints[{index}] 包含未定义字段: {', '.join(extra)}")
        if not point.get("title") or not point.get("objective"):
            raise ValueError(f"{leaf_id} testPoints[{index}] 缺少 title 或 objective")
        if "id" in point and point.get("id") and not re.fullmatch(r"TP-\d{3}", str(point.get("id"))):
            raise ValueError(f"{leaf_id} testPoints[{index}].id 不是合法 TP 编号")
        if not isinstance(point.get("basisRefs", []), list):
            raise ValueError(f"{leaf_id} testPoints[{index}].basisRefs 必须是数组")
        normalized_points.append(normalize_point(point))
    return leaf_id, normalized_points


def renumber_points(data: dict[str, Any]) -> None:
    index = 1
    for leaf in iter_leaf_scenarios(data.get("scenarios", [])):
        points = leaf.get("testPoints")
        if not isinstance(points, list):
            continue
        for point in points:
            if isinstance(point, dict):
                point["id"] = f"TP-{index:03d}"
                index += 1


def update_work_items(run_dir: Path, leaf_id: str, slice_path: Path, root: Path) -> None:
    path = run_dir / "process" / "test-point-work-items.json"
    if not path.exists():
        return
    data = load_json(path)
    now = datetime.now().isoformat(timespec="seconds")
    for item in data.get("workItems", []):
        if isinstance(item, dict) and item.get("leafScenarioId") == leaf_id:
            item["status"] = "done"
            item["slicePath"] = rel_path(slice_path, root)
            item["mergedAt"] = now
    dump_json(path, data)
    print(f"通过: 已更新 {rel_path(path, root)}")


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="合并叶子 SC 测试点切片")
    parser.add_argument("run_dir", type=Path, help="outputs/runs/<run-id>")
    parser.add_argument("--slice", required=True, type=Path, help="test-point-slice JSON")
    parser.add_argument("--scenario-tree", type=Path, help="场景树 JSON，默认 process/scenario-tree.json")
    parser.add_argument("--target", type=Path, help="目标分析方案 JSON，默认 deliverables/test-analysis-solution.json")
    parser.add_argument("--no-renumber", action="store_true", help="不重新全局编号 TP")
    args = parser.parse_args()

    root = repo_root()
    run_dir = resolve_path(args.run_dir, root)
    slice_path = resolve_path(args.slice, root)
    tree_path = resolve_path(args.scenario_tree, root) if args.scenario_tree else run_dir / "process" / "scenario-tree.json"
    target_path = resolve_path(args.target, root) if args.target else run_dir / "deliverables" / "test-analysis-solution.json"

    if not slice_path.exists():
        print(f"失败: 切片不存在: {slice_path}", file=sys.stderr)
        return 1
    if not tree_path.exists():
        print(f"失败: 场景树不存在: {tree_path}", file=sys.stderr)
        return 1
    target = load_json(target_path) if target_path.exists() else analysis_skeleton_from_scenario_tree(load_json(tree_path), tree_path, root)
    try:
        leaf_id, points = validate_slice(load_json(slice_path))
        leaves = leaf_map(target)
        if leaf_id not in leaves:
            raise ValueError(f"目标分析方案不存在叶子 SC: {leaf_id}")
        leaves[leaf_id]["testPoints"] = points
        if not args.no_renumber:
            renumber_points(target)
    except ValueError as exc:
        print(f"失败: {exc}", file=sys.stderr)
        return 1

    dump_json(target_path, target)
    print(f"通过: 已合并 {leaf_id} 到 {rel_path(target_path, root)}")
    update_work_items(run_dir, leaf_id, slice_path, root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
