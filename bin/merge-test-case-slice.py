#!/usr/bin/env python3
"""Merge one TC slice into deliverables/test-design-solution.json."""

from __future__ import annotations

import argparse
from datetime import datetime
import re
import sys
from pathlib import Path
from typing import Any

from run_artifacts import dump_json, load_json
from staged_workflow import render_markdown_for_json


CASE_KEYS = {"id", "title", "level", "preconditions", "testData", "steps", "expectedResult", "sourceRefs"}
LEVEL_VALUES = {"Level 0", "Level 1", "Level 2", "Level 3", "Level 4"}


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


def clone_point(point: dict[str, Any]) -> dict[str, Any]:
    cloned = {key: point.get(key) for key in ("id", "title", "objective", "basisRefs", "note") if key in point}
    cloned["testCases"] = []
    return cloned


def design_skeleton_from_analysis(analysis: dict[str, Any], analysis_path: Path, root: Path) -> dict[str, Any]:
    def clone_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
        cloned = {key: scenario.get(key) for key in ("id", "title", "fields") if key in scenario}
        children = scenario.get("children")
        if isinstance(children, list) and children:
            cloned["children"] = [clone_scenario(child) for child in children if isinstance(child, dict)]
        else:
            cloned["children"] = []
            cloned["testPoints"] = [
                clone_point(point)
                for point in scenario.get("testPoints", [])
                if isinstance(point, dict)
            ]
        return cloned

    return {
        "artifactType": "test-design-solution",
        "schemaVersion": "2.0",
        "title": str(analysis.get("title") or "测试设计方案").replace("测试分析方案", "测试设计方案"),
        "inputs": [
            {"field": "测试分析方案来源", "content": rel_path(analysis_path, root)},
            {"field": "设计范围", "content": "按已冻结 TP 逐项生成测试用例。"},
        ],
        "scenarios": [
            clone_scenario(scenario)
            for scenario in analysis.get("scenarios", [])
            if isinstance(scenario, dict)
        ],
    }


def iter_points(nodes: list[Any]) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        children = node.get("children")
        if isinstance(children, list) and children:
            points.extend(iter_points(children))
        else:
            points.extend(point for point in node.get("testPoints", []) if isinstance(point, dict))
    return points


def point_map(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(point.get("id")): point for point in iter_points(data.get("scenarios", []))}


def validate_case(tp_id: str, case: Any, index: int) -> dict[str, Any]:
    if not isinstance(case, dict):
        raise ValueError(f"{tp_id} testCases[{index}] 不是对象")
    extra = sorted(set(case) - CASE_KEYS)
    if extra:
        raise ValueError(f"{tp_id} testCases[{index}] 包含未定义字段: {', '.join(extra)}")
    if "id" in case and case.get("id") and not re.fullmatch(r"TC-\d{3}", str(case.get("id"))):
        raise ValueError(f"{tp_id} testCases[{index}].id 不是合法 TC 编号")
    for key in ("title", "level", "preconditions", "testData", "steps", "expectedResult", "sourceRefs"):
        if key not in case:
            raise ValueError(f"{tp_id} testCases[{index}] 缺少 {key}")
    if case.get("level") not in LEVEL_VALUES:
        raise ValueError(f"{tp_id} testCases[{index}].level 必须为 Level 0 到 Level 4")
    if not isinstance(case.get("preconditions"), list):
        raise ValueError(f"{tp_id} testCases[{index}].preconditions 必须是数组")
    test_data = case.get("testData")
    if not isinstance(test_data, list) or not test_data:
        raise ValueError(f"{tp_id} testCases[{index}].testData 必须是非空数组")
    for data_index, item in enumerate(test_data, start=1):
        if not isinstance(item, dict) or any(not item.get(field) for field in ("name", "value", "description")):
            raise ValueError(f"{tp_id} testCases[{index}].testData[{data_index}] 必须包含 name/value/description")
    steps = case.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError(f"{tp_id} testCases[{index}].steps 必须是非空数组")
    for step_index, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            raise ValueError(f"{tp_id} testCases[{index}].steps[{step_index}] 不是对象")
        if step.get("stepNo") != step_index:
            raise ValueError(f"{tp_id} testCases[{index}].steps[{step_index}].stepNo 应为 {step_index}")
        if not step.get("action") or not step.get("expected"):
            raise ValueError(f"{tp_id} testCases[{index}].steps[{step_index}] 缺少 action 或 expected")
    if not isinstance(case.get("sourceRefs"), list):
        raise ValueError(f"{tp_id} testCases[{index}].sourceRefs 必须是数组")
    return dict(case)


def validate_slice(slice_data: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    if slice_data.get("artifactType") != "test-case-slice":
        raise ValueError("切片 artifactType 必须为 test-case-slice")
    point = slice_data.get("testPoint")
    if not isinstance(point, dict):
        raise ValueError("切片缺少 testPoint 对象")
    tp_id = str(point.get("id") or "")
    cases = point.get("testCases")
    if not isinstance(cases, list) or not cases:
        raise ValueError(f"{tp_id} 缺少非空 testCases[]")
    return tp_id, [validate_case(tp_id, case, index) for index, case in enumerate(cases, start=1)]


def renumber_cases(data: dict[str, Any]) -> None:
    index = 1
    for point in iter_points(data.get("scenarios", [])):
        cases = point.get("testCases")
        if not isinstance(cases, list):
            continue
        for case in cases:
            if isinstance(case, dict):
                case["id"] = f"TC-{index:03d}"
                index += 1


def update_work_items(run_dir: Path, tp_id: str, slice_path: Path, root: Path) -> None:
    path = run_dir / "process" / "test-case-work-items.json"
    if not path.exists():
        return
    data = load_json(path)
    now = datetime.now().isoformat(timespec="seconds")
    for item in data.get("workItems", []):
        if isinstance(item, dict) and item.get("testPointId") == tp_id:
            item["status"] = "done"
            item["slicePath"] = rel_path(slice_path, root)
            item["mergedAt"] = now
    dump_json(path, data)
    render_markdown_for_json(path)
    print(f"通过: 已更新 {rel_path(path, root)}")


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="合并 TP 测试用例切片")
    parser.add_argument("run_dir", type=Path, help="outputs/runs/<run-id>")
    parser.add_argument("--slice", required=True, type=Path, help="test-case-slice JSON")
    parser.add_argument("--analysis", type=Path, help="分析方案 JSON，默认 deliverables/test-analysis-solution.json")
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

    try:
        tp_id, cases = validate_slice(load_json(slice_path))
        points = point_map(target)
        if tp_id not in points:
            raise ValueError(f"目标设计方案不存在 TP: {tp_id}")
        points[tp_id]["testCases"] = cases
        if not args.no_renumber:
            renumber_cases(target)
    except ValueError as exc:
        print(f"失败: {exc}", file=sys.stderr)
        return 1

    dump_json(target_path, target)
    render_markdown_for_json(target_path)
    print(f"通过: 已合并 {tp_id} 到 {rel_path(target_path, root)}")
    update_work_items(run_dir, tp_id, slice_path, root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
