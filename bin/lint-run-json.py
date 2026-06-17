#!/usr/bin/env python3
"""Lint JSON canonical artifacts in a run directory."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from run_artifacts import collect_renderable_json_files, load_json, validate_artifact


REQUIRED_PROCESS_JSON = [
    "process/task-list.json",
    "process/context-pack.json",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="校验 run 目录内 JSON canonical 产物")
    parser.add_argument("run_dir", type=Path, help="outputs/runs/<run-id>")
    args = parser.parse_args()

    run_dir = args.run_dir
    if not run_dir.is_dir():
        print(f"失败: 运行目录不存在: {run_dir}")
        return 1

    errors: list[str] = []
    warnings: list[str] = []
    for relative in REQUIRED_PROCESS_JSON:
        if not (run_dir / relative).exists():
            errors.append(f"缺少固定 JSON 运行产物: {relative}")

    analysis_json = run_dir / "deliverables" / "test-analysis-solution.json"
    design_json = run_dir / "deliverables" / "test-design-solution.json"
    if not analysis_json.exists() and not design_json.exists():
        errors.append("缺少主交付件 JSON: deliverables/test-analysis-solution.json 或 deliverables/test-design-solution.json")
    if analysis_json.exists() and not (run_dir / "process" / "input-fact-model.json").exists():
        errors.append("测试分析 run 缺少固定 JSON 运行产物: process/input-fact-model.json")

    json_files = [json_path for json_path, _markdown_path in collect_renderable_json_files(run_dir)]
    seen = set(json_files)
    for required in REQUIRED_PROCESS_JSON:
        path = run_dir / required
        if path.exists() and path not in seen:
            json_files.append(path)
            seen.add(path)
    for path in (analysis_json, design_json):
        if path.exists() and path not in seen:
            json_files.append(path)
            seen.add(path)

    for path in sorted(json_files):
        try:
            data = load_json(path)
        except Exception as exc:
            errors.append(f"{path.relative_to(run_dir)} 不是合法 JSON: {exc}")
            continue
        artifact_errors, artifact_warnings = validate_artifact(data)
        errors.extend(f"{path.relative_to(run_dir)}: {error}" for error in artifact_errors)
        warnings.extend(f"{path.relative_to(run_dir)}: {warning}" for warning in artifact_warnings)

    task_json = run_dir / "process" / "task-list.json"
    if task_json.exists():
        try:
            task_data = load_json(task_json)
        except Exception:
            task_data = {}
        normalize_done = any(
            stage.get("stage") == "输入文档归一化" and stage.get("status") == "done"
            for stage in task_data.get("stages", [])
            if isinstance(stage, dict)
        )
        if normalize_done and not (run_dir / "inputs" / "input-normalization-manifest.json").exists():
            errors.append("输入文档归一化已完成，但缺少 inputs/input-normalization-manifest.json")

    for warning in warnings:
        print(f"警告: {warning}")
    for error in errors:
        print(f"失败: {error}")
    if errors:
        return 1
    print(f"通过: {run_dir} JSON canonical 产物校验通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
