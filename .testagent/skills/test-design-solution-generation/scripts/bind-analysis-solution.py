#!/usr/bin/env python3
"""Bind an explicit test-analysis-solution JSON into a design run."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BIN_DIR = Path(__file__).resolve().parents[3] / "bin"
if str(BIN_DIR) not in sys.path:
    sys.path.insert(0, str(BIN_DIR))

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


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="绑定显式测试分析方案到测试设计 run")
    parser.add_argument("run_dir", type=Path, help="outputs/runs/<run-id>")
    parser.add_argument("--analysis", required=True, type=Path, help="显式提供的 test-analysis-solution.json")
    parser.add_argument("--target", type=Path, help="目标路径，默认 deliverables/test-analysis-solution.json")
    args = parser.parse_args()

    root = repo_root()
    run_dir = resolve_path(args.run_dir, root)
    analysis_path = resolve_path(args.analysis, root)
    target_path = resolve_path(args.target, root) if args.target else run_dir / "deliverables" / "test-analysis-solution.json"

    if not analysis_path.exists():
        print(f"失败: 分析方案不存在: {analysis_path}", file=sys.stderr)
        return 1

    try:
        analysis = load_json(analysis_path)
    except Exception as exc:
        print(f"失败: 无法读取分析方案 JSON: {exc}", file=sys.stderr)
        return 1

    if analysis.get("artifactType") != "test-analysis-solution":
        print("失败: --analysis 必须是 test-analysis-solution JSON", file=sys.stderr)
        return 1
    if str(analysis.get("schemaVersion")) != "2.0":
        print("失败: --analysis 必须使用 schemaVersion 2.0", file=sys.stderr)
        return 1
    if not isinstance(analysis.get("scenarios"), list):
        print("失败: --analysis 缺少 scenarios[]", file=sys.stderr)
        return 1

    target_path.parent.mkdir(parents=True, exist_ok=True)
    dump_json(target_path, analysis)
    render_markdown_for_json(target_path)
    print(f"通过: 已绑定 {rel_path(analysis_path, root)} -> {rel_path(target_path, root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
