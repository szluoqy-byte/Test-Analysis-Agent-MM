#!/usr/bin/env python3
"""Initialize process/scenario-tree.json, optionally from an existing analysis solution."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from generation_context import attach_generation_context, build_generation_context
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


def strip_points(nodes: list[Any]) -> list[dict[str, Any]]:
    stripped: list[dict[str, Any]] = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        copied = {key: node.get(key) for key in ("id", "title", "fields") if key in node}
        children = node.get("children")
        if isinstance(children, list) and children:
            copied["children"] = strip_points(children)
        else:
            copied["children"] = []
        stripped.append(copied)
    return stripped


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="初始化冻结 SC 场景树")
    parser.add_argument("run_dir", type=Path, help="outputs/runs/<run-id>")
    parser.add_argument("--analysis", type=Path, help="可选：从 test-analysis-solution.json 抽取 SC 树")
    parser.add_argument("--output", type=Path, help="输出路径，默认 process/scenario-tree.json")
    parser.add_argument("--force", action="store_true", help="覆盖已存在文件")
    parser.add_argument("--no-generation-context", action="store_true", help="调试用：不写入 generationContext")
    args = parser.parse_args()

    root = repo_root()
    run_dir = resolve_path(args.run_dir, root)
    analysis_path = resolve_path(args.analysis, root) if args.analysis else None
    output_path = resolve_path(args.output, root) if args.output else run_dir / "process" / "scenario-tree.json"
    if output_path.exists() and not args.force:
        print(f"失败: 场景树已存在，使用 --force 覆盖: {output_path}", file=sys.stderr)
        return 1

    scope: list[Any] = []
    scenarios: list[dict[str, Any]] = []
    title = "冻结 SC 场景树"
    source = ""
    if analysis_path:
        if not analysis_path.exists():
            print(f"失败: 分析方案不存在: {analysis_path}", file=sys.stderr)
            return 1
        analysis = load_json(analysis_path)
        if analysis.get("artifactType") != "test-analysis-solution":
            print("失败: --analysis 必须是 test-analysis-solution JSON", file=sys.stderr)
            return 1
        title = str(analysis.get("title") or title).replace("测试分析方案", "冻结 SC 场景树")
        scope = analysis.get("scope", [])
        scenarios = strip_points(analysis.get("scenarios", []))
        source = rel_path(analysis_path, root)

    data = {
        "artifactType": "scenario-tree",
        "schemaVersion": "1.0",
        "title": title,
        "runDir": rel_path(run_dir, root),
        "analysisSource": source,
        "scope": scope,
        "scenarios": scenarios,
        "rulesApplications": [],
        "dynamicSourceApplications": [],
    }
    dump_json(output_path, data)
    if not args.no_generation_context:
        context = build_generation_context(run_dir, "scenario-tree", output_path, target_id="scenario-tree")
        attach_generation_context(output_path, context)
    print(f"通过: 已生成 {rel_path(output_path, root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
