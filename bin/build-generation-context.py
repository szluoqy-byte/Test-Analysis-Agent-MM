#!/usr/bin/env python3
"""Attach deterministic generationContext to a staged run artifact."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from generation_context import (
    REVIEW_TYPES,
    attach_generation_context,
    build_generation_context,
    rel_path,
    repo_root,
    resolve_path,
)
from run_artifacts import dump_json
from staged_workflow import render_markdown_for_json


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def default_target(run_dir: Path, kind: str, target_id: str, review_type: str, coverage_scope: str) -> Path:
    if kind == "scenario-tree":
        return run_dir / "process" / "scenario-tree.json"
    if kind == "test-point":
        if not target_id:
            raise ValueError("--target-id 或 --leaf-sc 必填")
        return run_dir / "process" / "test-point-slices" / f"{target_id}.json"
    if kind == "test-case":
        if not target_id:
            raise ValueError("--target-id 或 --tp 必填")
        return run_dir / "process" / "test-case-slices" / f"{target_id}.json"
    if kind == "review":
        if not review_type:
            raise ValueError("--review-type 必填")
        return run_dir / "reports" / f"{review_type}.json"
    if kind == "coverage":
        name = f"{coverage_scope}-coverage-review" if coverage_scope in {"analysis", "design"} else "coverage-review"
        return run_dir / "reports" / f"{name}.json"
    raise ValueError(f"不支持的 kind: {kind}")


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="构建并写入 generationContext")
    parser.add_argument("run_dir", type=Path, help="outputs/runs/<run-id>")
    parser.add_argument(
        "--kind",
        required=True,
        choices=["scenario-tree", "test-point", "test-case", "review", "coverage"],
        help="生成上下文类型",
    )
    parser.add_argument("--target", type=Path, help="目标 JSON；未提供时按 kind 推断")
    parser.add_argument("--context-target", type=Path, help="构建 generationContext 时使用的被评审/覆盖对象；默认等于 --target")
    parser.add_argument("--target-id", default="", help="目标 ID，例如 SC-001-001 或 TP-001")
    parser.add_argument("--leaf-sc", default="", help="test-point 的目标叶子 SC ID")
    parser.add_argument("--tp", default="", help="test-case 的目标 TP ID")
    parser.add_argument("--review-type", default="", choices=sorted(REVIEW_TYPES), help="review artifactType")
    parser.add_argument("--coverage-scope", default="", choices=["", "analysis", "design"], help="coverage 范围")
    args = parser.parse_args()

    root = repo_root()
    run_dir = resolve_path(args.run_dir, root)
    target_id = args.target_id or args.leaf_sc or args.tp
    try:
        target_path = resolve_path(args.target, root) if args.target else default_target(
            run_dir,
            args.kind,
            target_id,
            args.review_type,
            args.coverage_scope,
        )
        if not target_path.exists():
            print(f"失败: 目标 JSON 不存在: {target_path}", file=sys.stderr)
            return 1
        context_target_path = resolve_path(args.context_target, root) if args.context_target else target_path
        if not context_target_path.exists():
            print(f"失败: context-target JSON 不存在: {context_target_path}", file=sys.stderr)
            return 1
        context = build_generation_context(
            run_dir,
            args.kind,
            context_target_path,
            target_id=target_id,
            review_type=args.review_type,
            coverage_scope=args.coverage_scope,
        )
        data = attach_generation_context(target_path, context)
        if args.kind in {"review", "coverage"}:
            data["targetArtifact"] = rel_path(context_target_path, root)
            if args.kind == "coverage" and args.coverage_scope:
                data["coverageScope"] = args.coverage_scope
            dump_json(target_path, data)
        render_markdown_for_json(target_path)
    except ValueError as exc:
        print(f"失败: {exc}", file=sys.stderr)
        return 1
    print(f"通过: 已写入 {rel_path(target_path, root)} 的 generationContext")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
