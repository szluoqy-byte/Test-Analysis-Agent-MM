#!/usr/bin/env python3
"""Create leaf-SC work items for staged TP generation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

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


def load_existing_statuses(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    try:
        data = load_json(path)
    except Exception:
        return {}
    statuses: dict[str, dict[str, str]] = {}
    for item in data.get("workItems", []):
        if isinstance(item, dict) and item.get("leafScenarioId"):
            statuses[str(item["leafScenarioId"])] = {
                "status": str(item.get("status") or "pending"),
                "slicePath": str(item.get("slicePath") or ""),
                "mergedAt": str(item.get("mergedAt") or ""),
            }
    return statuses


def collect_leaf_scenarios(nodes: list[Any], path: list[dict[str, str]] | None = None) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    current_path = path or []
    for scenario in nodes:
        if not isinstance(scenario, dict):
            continue
        next_path = current_path + [{"id": str(scenario.get("id", "")), "title": str(scenario.get("title", ""))}]
        children = scenario.get("children")
        if isinstance(children, list) and children:
            items.extend(collect_leaf_scenarios(children, next_path))
            continue
        items.append(
            {
                "scenarioPath": next_path,
                "leafScenarioId": next_path[-1]["id"] if next_path else "",
                "leafScenarioTitle": next_path[-1]["title"] if next_path else "",
                "status": "pending",
                "slicePath": "",
                "mergedAt": "",
            }
        )
    return items


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="生成叶子 SC 到 TP 的工作项索引")
    parser.add_argument("run_dir", type=Path, help="outputs/runs/<run-id>")
    parser.add_argument("--scenario-tree", type=Path, help="场景树 JSON，默认 process/scenario-tree.json")
    parser.add_argument("--output", type=Path, help="输出路径，默认 process/test-point-work-items.json")
    args = parser.parse_args()

    root = repo_root()
    run_dir = resolve_path(args.run_dir, root)
    scenario_tree_path = resolve_path(args.scenario_tree, root) if args.scenario_tree else run_dir / "process" / "scenario-tree.json"
    output_path = resolve_path(args.output, root) if args.output else run_dir / "process" / "test-point-work-items.json"

    if not scenario_tree_path.exists():
        print(f"失败: 场景树不存在: {scenario_tree_path}", file=sys.stderr)
        return 1
    scenario_tree = load_json(scenario_tree_path)
    if scenario_tree.get("artifactType") != "scenario-tree":
        print("失败: --scenario-tree 必须是 scenario-tree JSON", file=sys.stderr)
        return 1

    existing = load_existing_statuses(output_path)
    items = collect_leaf_scenarios(scenario_tree.get("scenarios", []))
    for item in items:
        previous = existing.get(item["leafScenarioId"], {})
        item["status"] = previous.get("status", item["status"])
        item["slicePath"] = previous.get("slicePath", item["slicePath"])
        item["mergedAt"] = previous.get("mergedAt", item["mergedAt"])

    data = {
        "artifactType": "test-point-work-items",
        "schemaVersion": "1.0",
        "title": "测试点生成工作项索引",
        "runDir": rel_path(run_dir, root),
        "scenarioTreeSource": rel_path(scenario_tree_path, root),
        "totalLeafScenarios": len(items),
        "workItems": items,
    }
    dump_json(output_path, data)
    render_markdown_for_json(output_path)
    print(f"通过: 已生成 {rel_path(output_path, root)}，叶子 SC {len(items)} 个")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
