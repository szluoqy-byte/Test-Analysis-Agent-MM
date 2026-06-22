#!/usr/bin/env python3
"""Initialize an editable test-design slice skeleton for one batch."""

from __future__ import annotations

import argparse
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


def clone_point(point: dict[str, Any]) -> dict[str, Any]:
    cloned = {
        key: point.get(key)
        for key in ("id", "title", "objective", "basisRefs", "note")
        if key in point
    }
    cloned["testCases"] = []
    return cloned


def clone_scenarios(nodes: list[Any]) -> list[dict[str, Any]]:
    cloned_nodes: list[dict[str, Any]] = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        cloned = {
            key: node.get(key)
            for key in ("id", "title", "fields")
            if key in node
        }
        children = node.get("children")
        if isinstance(children, list) and children:
            cloned["children"] = clone_scenarios(children)
        else:
            cloned["children"] = []
            cloned["testPoints"] = [
                clone_point(point)
                for point in node.get("testPoints", [])
                if isinstance(point, dict)
            ]
        cloned_nodes.append(cloned)
    return cloned_nodes


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="Initialize a test-design batch slice skeleton")
    parser.add_argument("run_dir", type=Path, help="outputs/runs/<run-id>")
    parser.add_argument("--batch", default="", help="batch id, for example batch-001")
    parser.add_argument("--analysis-slice", type=Path, help="analysis slice, defaults to process/design-slices/<batch>.json")
    parser.add_argument("--output", type=Path, help="design slice output, defaults to process/design-slices/<batch>-design.json")
    parser.add_argument("--force", action="store_true", help="overwrite an existing design slice")
    args = parser.parse_args()

    root = repo_root()
    run_dir = resolve_path(args.run_dir, root)
    if not run_dir.is_dir():
        print(f"failed: run directory does not exist: {run_dir}", file=sys.stderr)
        return 1

    batch_id = args.batch
    analysis_slice_path = resolve_path(args.analysis_slice, root) if args.analysis_slice else None
    if analysis_slice_path is None:
        if not batch_id:
            print("failed: provide --batch or --analysis-slice", file=sys.stderr)
            return 2
        analysis_slice_path = run_dir / "process" / "design-slices" / f"{batch_id}.json"
    if not analysis_slice_path.exists():
        print(f"failed: analysis slice does not exist: {analysis_slice_path}", file=sys.stderr)
        return 1

    analysis_slice = load_json(analysis_slice_path)
    if analysis_slice.get("artifactType") != "test-design-analysis-slice":
        print("failed: --analysis-slice must be a test-design-analysis-slice JSON", file=sys.stderr)
        return 1
    batch_id = batch_id or str(analysis_slice.get("batchId") or "")
    if not batch_id:
        print("failed: analysis slice has no batchId; pass --batch explicitly", file=sys.stderr)
        return 1

    output_path = resolve_path(args.output, root) if args.output else run_dir / "process" / "design-slices" / f"{batch_id}-design.json"
    if output_path.exists() and not args.force:
        print(f"failed: design slice already exists; use --force to overwrite: {output_path}", file=sys.stderr)
        return 1

    data = {
        "artifactType": "test-design-solution-slice",
        "schemaVersion": "1.0",
        "title": f"测试设计方案切片 {batch_id}",
        "runDir": rel_path(run_dir, root),
        "batchId": batch_id,
        "analysisSliceSource": rel_path(analysis_slice_path, root),
        "testPointIds": analysis_slice.get("testPointIds", []),
        "analysisTitle": analysis_slice.get("analysisTitle", ""),
        "scope": analysis_slice.get("scope", []),
        "instructions": [
            "只填写本文件现有 TP 的 testCases[]。",
            "不要新增、删除、合并或改写 SC/TP。",
            "不要创建临时 Python/JavaScript/PowerShell 脚本拼接 JSON。",
            "填写完成后使用 bin/merge-design-slice.py 合并到主交付件。",
        ],
        "scenarios": clone_scenarios(analysis_slice.get("scenarios", [])),
    }
    dump_json(output_path, data)
    print(f"passed: wrote {rel_path(output_path, root)}; pending TP: {', '.join(data['testPointIds'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
