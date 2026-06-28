#!/usr/bin/env python3
"""Lint a frozen scenario-tree process artifact."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

BIN_DIR = Path(__file__).resolve().parents[3] / "bin"
if str(BIN_DIR) not in sys.path:
    sys.path.insert(0, str(BIN_DIR))

from run_artifacts import load_json


SC_RE = re.compile(r"^SC-\d{3}(?:-\d{3}){0,2}$")


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def normalize_text(value: Any) -> str:
    return "" if value is None else str(value)


def validate_scenarios(nodes: list[Any], errors: list[str], parent_id: str = "", depth: int = 1) -> None:
    if depth > 3:
        errors.append(f"{parent_id or 'scenarios'} 超过 3 层 SC 深度")
        return
    for index, scenario in enumerate(nodes, start=1):
        if not isinstance(scenario, dict):
            errors.append(f"{parent_id or 'scenarios'}[{index}] 不是对象")
            continue
        expected_id = f"{parent_id}-{index:03d}" if parent_id else f"SC-{index:03d}"
        scenario_id = normalize_text(scenario.get("id"))
        if scenario_id != expected_id:
            errors.append(f"场景序号应为 {expected_id}，实际为 {scenario.get('id')}")
        if not SC_RE.fullmatch(scenario_id):
            errors.append(f"{scenario_id or expected_id} 不是合法 SC 编号")
        if not scenario.get("title"):
            errors.append(f"{scenario_id or expected_id} 缺少 title")
        extra_keys = sorted(set(scenario) - {"id", "title", "fields", "children"})
        if extra_keys:
            errors.append(f"{scenario_id or expected_id} 包含未定义字段: {', '.join(extra_keys)}")
        if "testPoints" in scenario:
            errors.append(f"{scenario_id or expected_id} 在 scenario-tree 阶段不得包含 testPoints")
        children = scenario.get("children", [])
        if children is None:
            children = []
        if not isinstance(children, list):
            errors.append(f"{scenario_id or expected_id} children 必须是数组")
            continue
        if children:
            validate_scenarios(children, errors, scenario_id, depth + 1)


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="校验冻结 SC 场景树 JSON")
    parser.add_argument("scenario_tree", type=Path, help="process/scenario-tree.json")
    args = parser.parse_args()

    if not args.scenario_tree.exists():
        print(f"失败: 场景树不存在: {args.scenario_tree}", file=sys.stderr)
        return 1
    try:
        data = load_json(args.scenario_tree)
    except Exception as exc:
        print(f"失败: 不是合法 JSON: {exc}", file=sys.stderr)
        return 1

    errors: list[str] = []
    if data.get("artifactType") != "scenario-tree":
        errors.append("artifactType 必须为 scenario-tree")
    if data.get("schemaVersion") != "1.0":
        errors.append("schemaVersion 必须为 1.0")
    if not isinstance(data.get("scope", []), list):
        errors.append("scope 必须是数组")
    scenarios = data.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        errors.append("scenarios 必须是非空数组")
    else:
        validate_scenarios(scenarios, errors)

    for error in errors:
        print(f"失败: {error}")
    if errors:
        return 1
    print(f"通过: {args.scenario_tree} SC 场景树校验通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
