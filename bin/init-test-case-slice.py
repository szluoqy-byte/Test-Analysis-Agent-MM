#!/usr/bin/env python3
"""Initialize an editable TC slice for one frozen TP."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from generation_context import attach_generation_context, build_generation_context
from run_artifacts import dump_json, load_json
from staged_workflow import render_markdown_for_json


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


def find_work_item(work_items: dict[str, Any], tp_id: str) -> dict[str, Any] | None:
    for item in work_items.get("workItems", []):
        if isinstance(item, dict) and item.get("testPointId") == tp_id:
            return item
    return None


def first_pending(work_items: dict[str, Any]) -> dict[str, Any] | None:
    for item in work_items.get("workItems", []):
        if isinstance(item, dict) and item.get("status") != "done":
            return item
    return None


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


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="初始化 TP 的测试用例切片")
    parser.add_argument("run_dir", type=Path, help="outputs/runs/<run-id>")
    parser.add_argument("--tp", default="", help="TP ID，例如 TP-001；未提供时使用第一个未完成工作项")
    parser.add_argument("--work-items", type=Path, help="工作项索引，默认 process/test-case-work-items.json")
    parser.add_argument("--design", type=Path, help="可选：从现有 test-design-solution.json 预填 TC")
    parser.add_argument("--output", type=Path, help="输出路径，默认 process/test-case-slices/<TP-ID>.json")
    parser.add_argument("--force", action="store_true", help="覆盖已存在切片")
    parser.add_argument("--no-generation-context", action="store_true", help="调试用：不写入 generationContext")
    args = parser.parse_args()

    root = repo_root()
    run_dir = resolve_path(args.run_dir, root)
    work_items_path = resolve_path(args.work_items, root) if args.work_items else run_dir / "process" / "test-case-work-items.json"
    if not work_items_path.exists():
        print(
            "失败: 工作项索引不存在，请先运行 "
            f"python bin/extract-test-case-work-items.py {rel_path(run_dir, root)}",
            file=sys.stderr,
        )
        return 1
    work_items = load_json(work_items_path)
    item = find_work_item(work_items, args.tp) if args.tp else first_pending(work_items)
    if not item:
        print("失败: 未找到可初始化的 TP 工作项", file=sys.stderr)
        return 1
    tp_id = str(item.get("testPointId") or "")
    output_path = resolve_path(args.output, root) if args.output else run_dir / "process" / "test-case-slices" / f"{tp_id}.json"
    if output_path.exists() and not args.force:
        print(f"失败: 切片已存在，使用 --force 覆盖: {output_path}", file=sys.stderr)
        return 1

    test_point = {
        "id": tp_id,
        "title": item.get("testPointTitle", ""),
        "objective": item.get("objective", ""),
        "basisRefs": item.get("basisRefs", []),
        "testCases": [],
    }
    design_path = resolve_path(args.design, root) if args.design else run_dir / "deliverables" / "test-design-solution.json"
    if design_path.exists():
        design = load_json(design_path)
        for point in iter_points(design.get("scenarios", [])):
            if point.get("id") == tp_id and isinstance(point.get("testCases"), list):
                test_point["testCases"] = point.get("testCases", [])
                break

    data = {
        "artifactType": "test-case-slice",
        "schemaVersion": "1.0",
        "title": f"测试用例切片 {tp_id}",
        "runDir": rel_path(run_dir, root),
        "workItemsSource": rel_path(work_items_path, root),
        "scenarioPath": item.get("scenarioPath", []),
        "leafScenarioId": item.get("leafScenarioId", ""),
        "testPoint": test_point,
        "instructions": [
            "只填写 testPoint.testCases[]。",
            "不要新增、删除、合并或改写 SC/TP。",
            "testCases[] 可以暂不填写全局 TC 编号，merge 脚本会统一重排。",
            "一个 TC 只覆盖一个可独立执行、独立判定的测试实例。",
        ],
        "rulesApplications": [],
        "dynamicSourceApplications": [],
    }
    dump_json(output_path, data)
    if not args.no_generation_context:
        context = build_generation_context(run_dir, "test-case", output_path, target_id=tp_id)
        attach_generation_context(output_path, context)
    render_markdown_for_json(output_path)
    print(f"通过: 已生成 {rel_path(output_path, root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
