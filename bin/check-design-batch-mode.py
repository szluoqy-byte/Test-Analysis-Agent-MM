#!/usr/bin/env python3
"""Decide whether test design generation must use batched mode."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from run_artifacts import dump_json, load_json


DEFAULT_ANALYSIS_SIZE_KB = 200
DEFAULT_DESIGN_SIZE_KB = 300
DEFAULT_TP_COUNT = 30


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


def count_test_points(nodes: list[Any]) -> int:
    total = 0
    for node in nodes:
        if not isinstance(node, dict):
            continue
        children = node.get("children")
        if isinstance(children, list) and children:
            total += count_test_points(children)
        else:
            points = node.get("testPoints")
            if isinstance(points, list):
                total += sum(1 for point in points if isinstance(point, dict))
    return total


def file_size_kb(path: Path) -> float:
    if not path.exists():
        return 0.0
    return path.stat().st_size / 1024


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="Decide whether test design must use batched mode")
    parser.add_argument("run_dir", type=Path, help="outputs/runs/<run-id>")
    parser.add_argument("--analysis", type=Path, help="analysis JSON, defaults to run deliverables")
    parser.add_argument("--design", type=Path, help="existing design JSON, defaults to run deliverables")
    parser.add_argument("--output", type=Path, help="output path, defaults to process/design-batch-decision.json")
    parser.add_argument("--analysis-size-kb", type=int, default=DEFAULT_ANALYSIS_SIZE_KB)
    parser.add_argument("--design-size-kb", type=int, default=DEFAULT_DESIGN_SIZE_KB)
    parser.add_argument("--tp-count", type=int, default=DEFAULT_TP_COUNT)
    args = parser.parse_args()

    root = repo_root()
    run_dir = resolve_path(args.run_dir, root)
    analysis_path = resolve_path(args.analysis, root) if args.analysis else run_dir / "deliverables" / "test-analysis-solution.json"
    design_path = resolve_path(args.design, root) if args.design else run_dir / "deliverables" / "test-design-solution.json"
    output_path = resolve_path(args.output, root) if args.output else run_dir / "process" / "design-batch-decision.json"

    if not run_dir.is_dir():
        print(f"failed: run directory does not exist: {run_dir}", file=sys.stderr)
        return 1
    if not analysis_path.exists():
        print(f"failed: analysis JSON does not exist: {analysis_path}", file=sys.stderr)
        return 1

    analysis = load_json(analysis_path)
    if analysis.get("artifactType") != "test-analysis-solution":
        print("failed: --analysis must be a test-analysis-solution JSON", file=sys.stderr)
        return 1

    analysis_size = round(file_size_kb(analysis_path), 2)
    design_size = round(file_size_kb(design_path), 2)
    tp_count = count_test_points(analysis.get("scenarios", []))
    reasons: list[str] = []
    if analysis_size > args.analysis_size_kb:
        reasons.append(f"analysis JSON {analysis_size}KB > {args.analysis_size_kb}KB")
    if tp_count > args.tp_count:
        reasons.append(f"TP count {tp_count} > {args.tp_count}")
    if design_path.exists() and design_size > args.design_size_kb:
        reasons.append(f"design JSON {design_size}KB > {args.design_size_kb}KB")

    data = {
        "artifactType": "design-batch-decision",
        "schemaVersion": "1.0",
        "title": "测试设计分批模式判定",
        "runDir": rel_path(run_dir, root),
        "analysisSource": rel_path(analysis_path, root),
        "designSource": rel_path(design_path, root) if design_path.exists() else "",
        "batchRequired": bool(reasons),
        "reasons": reasons,
        "metrics": {
            "analysisSizeKB": analysis_size,
            "designSizeKB": design_size,
            "testPointCount": tp_count,
        },
        "thresholds": {
            "analysisSizeKB": args.analysis_size_kb,
            "designSizeKB": args.design_size_kb,
            "testPointCount": args.tp_count,
        },
    }
    dump_json(output_path, data)
    mode = "batch required" if data["batchRequired"] else "whole-file allowed"
    reason_text = "; ".join(reasons) if reasons else "below thresholds"
    print(f"passed: {mode}: {reason_text}; wrote {rel_path(output_path, root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
