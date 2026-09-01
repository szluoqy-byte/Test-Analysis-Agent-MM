#!/usr/bin/env python3
"""Validate result-deliverable JSON and script-owned run control JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from encoding_utils import configure_stdio
from run_artifacts import load_json, validate_artifact


CONTROL_JSON = {
    "process/id-registry.json",
    "process/test-point-work-items.json",
    "process/test-case-work-items.json",
}
RESULT_JSON = {
    "deliverables/test-analysis-solution.json",
    "deliverables/test-design-solution.json",
}
STATUS_VALUES = {"pending", "in_progress", "done", "blocked", "skipped"}


def relative(path: Path, run_dir: Path) -> str:
    return path.relative_to(run_dir).as_posix()


def validate_work_items(data: dict[str, Any], path: str) -> list[str]:
    errors: list[str] = []
    expected_type = "test-point-work-items" if "test-point" in path else "test-case-work-items"
    id_key = "leafScenarioId" if expected_type == "test-point-work-items" else "testPointId"
    if data.get("artifactType") != expected_type or data.get("schemaVersion") != "1.0":
        errors.append(f"{path}: artifactType/schemaVersion 非法")
    items = data.get("workItems")
    if not isinstance(items, list):
        return errors + [f"{path}: 缺少 workItems[]"]
    seen: set[str] = set()
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            errors.append(f"{path}: workItems[{index}] 不是对象")
            continue
        current_id = str(item.get(id_key) or "")
        if not current_id:
            errors.append(f"{path}: workItems[{index}] 缺少 {id_key}")
        elif current_id in seen:
            errors.append(f"{path}: 工作项 ID 重复: {current_id}")
        seen.add(current_id)
        if item.get("status") not in STATUS_VALUES:
            errors.append(f"{path}: {current_id} status 非法: {item.get('status')}")
        if not item.get("contentHash"):
            errors.append(f"{path}: {current_id} 缺少 contentHash")
    return errors


def validate_control(path: Path, run_dir: Path, data: dict[str, Any]) -> list[str]:
    rel = relative(path, run_dir)
    if rel.endswith("work-items.json"):
        return validate_work_items(data, rel)
    if not isinstance(data, dict):
        return [f"{rel}: 顶层必须是对象"]
    return []


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="校验结果交付 JSON 和脚本控制 JSON")
    parser.add_argument("run_dir", type=Path, help="outputs/runs/<run-id>")
    args = parser.parse_args()
    run_dir = args.run_dir
    if not run_dir.is_dir():
        print(f"失败: 运行目录不存在: {run_dir}")
        return 1

    errors: list[str] = []
    warnings: list[str] = []
    analysis = run_dir / "deliverables" / "test-analysis-solution.json"
    design = run_dir / "deliverables" / "test-design-solution.json"
    if not analysis.is_file() and not design.is_file():
        errors.append("缺少结果交付 JSON: test-analysis-solution.json 或 test-design-solution.json")

    for path in sorted(run_dir.rglob("*.json")):
        rel = relative(path, run_dir)
        if rel.startswith("inputs/"):
            continue
        if rel not in CONTROL_JSON and rel not in RESULT_JSON:
            errors.append(f"发现不允许的过程 JSON: {rel}；语义过程件必须使用 Markdown")
            continue
        try:
            data = load_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{rel} 不是合法 JSON: {exc}")
            continue
        if rel in RESULT_JSON:
            artifact_errors, artifact_warnings = validate_artifact(data)
            errors.extend(f"{rel}: {error}" for error in artifact_errors)
            warnings.extend(f"{rel}: {warning}" for warning in artifact_warnings)
        else:
            errors.extend(validate_control(path, run_dir, data))

    if analysis.is_file():
        for rel in (
            "process/rules-pack.md",
            "process/context-pack.md",
            "process/input-fact-model.md",
            "process/scenario-tree.md",
            "process/test-point-work-items.json",
        ):
            if not (run_dir / rel).is_file():
                errors.append(f"分析结果缺少必要上游产物: {rel}")
    if design.is_file() and not (run_dir / "process/test-case-work-items.json").is_file():
        errors.append("设计结果缺少必要控制产物: process/test-case-work-items.json")

    for warning in warnings:
        print(f"警告: {warning}")
    for error in errors:
        print(f"失败: {error}")
    if errors:
        return 1
    print(f"通过: {run_dir} JSON 边界校验通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
