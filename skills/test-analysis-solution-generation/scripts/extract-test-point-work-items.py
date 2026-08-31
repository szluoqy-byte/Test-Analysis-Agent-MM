#!/usr/bin/env python3
"""Create leaf-SC work items from the Markdown scenario tree."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys

BIN_DIR = Path(__file__).resolve().parents[3] / "bin"
if str(BIN_DIR) not in sys.path:
    sys.path.insert(0, str(BIN_DIR))

from encoding_utils import configure_stdio
from markdown_process import leaf_scenarios, parse_scenario_headings, read_markdown, validate_scenario_tree
from run_artifacts import dump_json, load_json


def existing_items(path: Path) -> dict[str, dict]:
    if not path.is_file():
        return {}
    try:
        data = load_json(path)
    except Exception:
        return {}
    return {
        str(item.get("leafScenarioId")): item
        for item in data.get("workItems", [])
        if isinstance(item, dict) and item.get("leafScenarioId")
    }


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="从 Markdown 场景树生成叶子 SC 工作项")
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--scenario-tree", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    run_dir = args.run_dir if args.run_dir.is_absolute() else root / args.run_dir
    scenario_path = args.scenario_tree or run_dir / "process" / "scenario-tree.md"
    scenario_path = scenario_path if scenario_path.is_absolute() else root / scenario_path
    output = args.output or run_dir / "process" / "test-point-work-items.json"
    output = output if output.is_absolute() else root / output
    if not scenario_path.is_file():
        print(f"失败: 场景树不存在: {scenario_path}", file=sys.stderr)
        return 1
    errors, _warnings = validate_scenario_tree(scenario_path)
    if errors:
        for error in errors:
            print(f"失败: {error}", file=sys.stderr)
        return 1

    all_headings = {item.scenario_id: item for item in parse_scenario_headings(read_markdown(scenario_path))}
    previous = existing_items(output)
    items: list[dict] = []
    for leaf in leaf_scenarios(scenario_path):
        segments = leaf.scenario_id.split("-")[1:]
        path_ids = ["SC-" + "-".join(segments[:index]) for index in range(1, len(segments) + 1)]
        scenario_path_rows = [{"id": value, "title": all_headings[value].title} for value in path_ids]
        digest = hashlib.sha256((leaf.title + "\n" + leaf.body).encode("utf-8")).hexdigest()
        old = previous.get(leaf.scenario_id, {})
        changed = bool(old.get("contentHash")) and old.get("contentHash") != digest
        items.append(
            {
                "scenarioPath": scenario_path_rows,
                "leafScenarioId": leaf.scenario_id,
                "leafScenarioTitle": leaf.title,
                "status": "pending" if changed else old.get("status", "pending"),
                "slicePath": old.get("slicePath", ""),
                "completedAt": "" if changed else old.get("completedAt", ""),
                "contentHash": digest,
                "contentChanged": changed or bool(old.get("contentChanged", False)),
                "reopenReason": old.get("reopenReason", ""),
            }
        )
    data = {
        "artifactType": "test-point-work-items",
        "schemaVersion": "1.0",
        "runDir": run_dir.relative_to(root).as_posix(),
        "scenarioTreeSource": scenario_path.relative_to(root).as_posix(),
        "workItems": items,
    }
    dump_json(output, data)
    print(f"通过: 已生成 {output.relative_to(root).as_posix()}，叶子 SC {len(items)} 个")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
