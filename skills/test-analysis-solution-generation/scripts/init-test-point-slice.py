#!/usr/bin/env python3
"""Initialize an editable TP slice for one frozen leaf scenario."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

BIN_DIR = Path(__file__).resolve().parents[3] / "bin"
if str(BIN_DIR) not in sys.path:
    sys.path.insert(0, str(BIN_DIR))

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
    return Path(__file__).resolve().parents[3]


def resolve_path(path: Path, root: Path) -> Path:
    return path if path.is_absolute() else root / path


def rel_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def find_work_item(work_items: dict[str, Any], leaf_sc: str) -> dict[str, Any] | None:
    for item in work_items.get("workItems", []):
        if isinstance(item, dict) and item.get("leafScenarioId") == leaf_sc:
            return item
    return None


def find_first_pending(work_items: dict[str, Any]) -> dict[str, Any] | None:
    for item in work_items.get("workItems", []):
        if isinstance(item, dict) and item.get("status") != "done":
            return item
    return None


def clone_leaf_from_path(scenario_path: list[Any]) -> dict[str, Any]:
    leaf = scenario_path[-1] if scenario_path else {}
    return {
        "id": str(leaf.get("id", "")) if isinstance(leaf, dict) else "",
        "title": str(leaf.get("title", "")) if isinstance(leaf, dict) else "",
        "children": [],
        "testPoints": [],
    }


def find_leaf(nodes: list[Any], leaf_id: str) -> dict[str, Any] | None:
    for node in nodes:
        if not isinstance(node, dict):
            continue
        children = node.get("children")
        if isinstance(children, list) and children:
            found = find_leaf(children, leaf_id)
            if found:
                return found
        elif node.get("id") == leaf_id:
            return node
    return None


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="初始化叶子 SC 的测试点切片")
    parser.add_argument("run_dir", type=Path, help="outputs/runs/<run-id>")
    parser.add_argument("--leaf-sc", default="", help="叶子 SC ID，例如 SC-001-001；未提供时使用第一个未完成工作项")
    parser.add_argument("--work-items", type=Path, help="工作项索引，默认 process/test-point-work-items.json")
    parser.add_argument("--analysis", type=Path, help="可选：从现有 test-analysis-solution.json 预填 TP")
    parser.add_argument("--output", type=Path, help="输出路径，默认 process/test-point-slices/<SC-ID>.json")
    parser.add_argument("--force", action="store_true", help="覆盖已存在切片")
    parser.add_argument("--no-generation-context", action="store_true", help="调试用：不写入 generationContext")
    args = parser.parse_args()

    root = repo_root()
    run_dir = resolve_path(args.run_dir, root)
    work_items_path = resolve_path(args.work_items, root) if args.work_items else run_dir / "process" / "test-point-work-items.json"
    if not work_items_path.exists():
        print(
            "失败: 工作项索引不存在，请先运行 "
            "python skills/test-analysis-solution-generation/scripts/extract-test-point-work-items.py "
            f"{rel_path(run_dir, root)}",
            file=sys.stderr,
        )
        return 1
    work_items = load_json(work_items_path)
    item = find_work_item(work_items, args.leaf_sc) if args.leaf_sc else find_first_pending(work_items)
    if not item:
        print("失败: 未找到可初始化的叶子 SC 工作项", file=sys.stderr)
        return 1
    leaf_sc = str(item.get("leafScenarioId") or "")
    output_path = resolve_path(args.output, root) if args.output else run_dir / "process" / "test-point-slices" / f"{leaf_sc}.json"
    if output_path.exists() and not args.force:
        print(f"失败: 切片已存在，使用 --force 覆盖: {output_path}", file=sys.stderr)
        return 1

    scenario = clone_leaf_from_path(item.get("scenarioPath", []))
    analysis_path = resolve_path(args.analysis, root) if args.analysis else run_dir / "deliverables" / "test-analysis-solution.json"
    if analysis_path.exists():
        analysis = load_json(analysis_path)
        leaf = find_leaf(analysis.get("scenarios", []), leaf_sc)
        if leaf and isinstance(leaf.get("testPoints"), list):
            scenario["testPoints"] = leaf.get("testPoints", [])

    data = {
        "artifactType": "test-point-slice",
        "schemaVersion": "1.0",
        "title": f"测试点切片 {leaf_sc}",
        "runDir": rel_path(run_dir, root),
        "workItemsSource": rel_path(work_items_path, root),
        "leafScenarioId": leaf_sc,
        "scenarioPath": item.get("scenarioPath", []),
        "instructions": [
            "只在 scenario.testPoints[] 中填写本叶子 SC 的测试点。",
            "不要新增、删除、合并或改写 SC。",
            "保留已有 TP 的 id；新增测试点可以暂不填写 id，merge 脚本会追加稳定编号且不重排既有 TP。",
            "每个叶子 SC 必须包含一个标题为 E2E场景测试 的测试点。",
        ],
        "scenario": scenario,
        "rulesApplications": [],
        "dynamicSourceApplications": [],
    }
    dump_json(output_path, data)
    if not args.no_generation_context:
        context = build_generation_context(run_dir, "test-point", output_path, target_id=leaf_sc)
        attach_generation_context(output_path, context)
    render_markdown_for_json(output_path)
    print(f"通过: 已生成 {rel_path(output_path, root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
