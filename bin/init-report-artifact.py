#!/usr/bin/env python3
"""Initialize review or coverage report JSON skeletons."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from generation_context import (
    REVIEW_TYPES,
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


def default_review_target(run_dir: Path, review_type: str) -> Path:
    if review_type == "scenario-tree-review":
        return run_dir / "process" / "scenario-tree.json"
    if review_type == "test-point-review":
        return run_dir / "deliverables" / "test-analysis-solution.json"
    if review_type == "test-case-review":
        return run_dir / "deliverables" / "test-design-solution.json"
    if review_type == "test-analysis-solution-review":
        return run_dir / "deliverables" / "test-analysis-solution.json"
    if review_type == "test-design-solution-review":
        return run_dir / "deliverables" / "test-design-solution.json"
    raise ValueError(f"不支持的 review-type: {review_type}")


def review_target_from_id(run_dir: Path, review_type: str, target_id: str) -> Path:
    if not target_id:
        return default_review_target(run_dir, review_type)
    if review_type == "test-point-review":
        return run_dir / "process" / "test-point-slices" / f"{target_id}.json"
    if review_type == "test-case-review":
        return run_dir / "process" / "test-case-slices" / f"{target_id}.json"
    raise ValueError(f"{review_type} 不支持 --target-id")


def default_coverage_target(run_dir: Path, scope: str) -> Path:
    if scope == "analysis":
        return run_dir / "deliverables" / "test-analysis-solution.json"
    if scope == "design":
        return run_dir / "deliverables" / "test-design-solution.json"
    raise ValueError("--scope 必须为 analysis 或 design")


def default_output(run_dir: Path, kind: str, review_type: str, scope: str) -> Path:
    if kind == "review":
        return run_dir / "process" / "reviews" / f"{review_type}.json"
    return run_dir / "process" / "reviews" / f"{scope}-coverage-review.json"


def review_output_from_id(run_dir: Path, review_type: str, target_id: str) -> Path:
    if not target_id:
        return default_output(run_dir, "review", review_type, "")
    if review_type == "test-point-review":
        return run_dir / "process" / "reviews" / "test-point-reviews" / f"{target_id}.json"
    if review_type == "test-case-review":
        return run_dir / "process" / "reviews" / "test-case-reviews" / f"{target_id}.json"
    raise ValueError(f"{review_type} 不支持 --target-id")


def review_title(review_type: str) -> str:
    titles = {
        "scenario-tree-review": "SC 场景树评审结果",
        "test-point-review": "测试点评审结果",
        "test-case-review": "测试用例评审结果",
        "test-analysis-solution-review": "测试分析方案语义评审结果",
        "test-design-solution-review": "测试设计方案语义评审结果",
    }
    return titles.get(review_type, "测试方案语义评审结果")


def init_review(run_dir: Path, root: Path, review_type: str, target: Path) -> dict:
    context = build_generation_context(
        run_dir,
        "review",
        target,
        target_id=target.stem,
        review_type=review_type,
    )
    return {
        "artifactType": review_type,
        "schemaVersion": "1.0",
        "title": review_title(review_type),
        "result": "需修正",
        "summary": "待语义评审填写。",
        "targetArtifact": rel_path(target, root),
        "findings": [],
        "blockingIssues": [],
        "recommendations": [],
        "evidenceRefs": [
            {
                "source": "targetArtifact",
                "location": rel_path(target, root),
                "description": "本次评审目标 canonical JSON。",
            }
        ],
        "knowledgeApplications": [],
        "generationContext": context,
    }


def init_coverage(run_dir: Path, root: Path, scope: str, target: Path) -> dict:
    context = build_generation_context(
        run_dir,
        "coverage",
        target,
        target_id=target.stem,
        coverage_scope=scope,
    )
    return {
        "artifactType": "coverage-review",
        "schemaVersion": "1.0",
        "title": "测试分析覆盖审查结果" if scope == "analysis" else "测试设计覆盖审查结果",
        "result": "需修正",
        "summary": "待覆盖审查填写。",
        "coverageScope": scope,
        "targetArtifact": rel_path(target, root),
        "targetArtifacts": {
            "targetArtifact": rel_path(target, root),
            "factCoverageMap": rel_path(run_dir / "process" / f"{scope}-fact-coverage-map.json", root),
        },
        "findings": [],
        "blockingIssues": [],
        "recommendations": [],
        "evidenceRefs": [
            {
                "source": "targetArtifact",
                "location": rel_path(target, root),
                "description": "本次覆盖审查目标 canonical JSON。",
            }
        ],
        "qualityGates": [
            {
                "gate": "确定性校验",
                "result": "不适用",
                "description": "由 workflow 在 coverage 前执行 lint/render/consistency。",
                "recommendation": "coverage 只记录语义覆盖收口结论，不重复 deterministic lint。",
            }
        ],
        "rulesApplications": [],
        "projectKnowledgeApplications": [],
        "coverageGaps": [],
        "generationContext": context,
    }


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="初始化 review/coverage 报告 JSON 骨架")
    parser.add_argument("run_dir", type=Path, help="outputs/runs/<run-id>")
    parser.add_argument("--kind", required=True, choices=["review", "coverage"])
    parser.add_argument("--review-type", default="", choices=sorted(REVIEW_TYPES))
    parser.add_argument("--scope", default="", choices=["", "analysis", "design"])
    parser.add_argument("--target-id", default="", help="切片评审目标 ID，例如 SC-001-001 或 TP-001")
    parser.add_argument("--target", type=Path, help="被评审/覆盖的 canonical JSON")
    parser.add_argument("--output", type=Path, help="输出报告 JSON")
    parser.add_argument("--force", action="store_true", help="覆盖已存在报告")
    args = parser.parse_args()

    root = repo_root()
    run_dir = resolve_path(args.run_dir, root)
    try:
        if args.kind == "review":
            if not args.review_type:
                raise ValueError("--kind review 必须提供 --review-type")
            target = (
                resolve_path(args.target, root)
                if args.target
                else review_target_from_id(run_dir, args.review_type, args.target_id)
            )
            output = (
                resolve_path(args.output, root)
                if args.output
                else review_output_from_id(run_dir, args.review_type, args.target_id)
            )
            data = init_review(run_dir, root, args.review_type, target)
        else:
            if not args.scope:
                raise ValueError("--kind coverage 必须提供 --scope")
            target = resolve_path(args.target, root) if args.target else default_coverage_target(run_dir, args.scope)
            output = resolve_path(args.output, root) if args.output else default_output(run_dir, "coverage", "", args.scope)
            data = init_coverage(run_dir, root, args.scope, target)
    except ValueError as exc:
        print(f"失败: {exc}", file=sys.stderr)
        return 1
    if not target.exists():
        print(f"失败: 目标 canonical JSON 不存在: {target}", file=sys.stderr)
        return 1
    if output.exists() and not args.force:
        print(f"失败: 报告已存在，使用 --force 覆盖: {output}", file=sys.stderr)
        return 1
    output.parent.mkdir(parents=True, exist_ok=True)
    dump_json(output, data)
    render_markdown_for_json(output)
    print(f"通过: 已生成 {rel_path(output, root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
