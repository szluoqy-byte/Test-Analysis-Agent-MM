#!/usr/bin/env python3
"""Reopen staged work items from blocking review findings."""

from __future__ import annotations

import argparse
from datetime import datetime
import sys
from pathlib import Path
from typing import Any

from encoding_utils import configure_stdio
from run_artifacts import load_json
from staged_workflow import (
    dump_work_items,
    item_id,
    load_work_items,
    normalized_location,
    render_markdown_for_json,
    rel_path,
    repo_root,
    resolve_path,
    scope_config,
    work_items_path,
)


def default_review_paths(run_dir: Path, scope_name: str) -> list[Path]:
    if scope_name == "analysis":
        paths = sorted((run_dir / "reports" / "test-point-reviews").glob("*.json"))
        aggregate = run_dir / "reports" / "test-point-review.json"
        final = run_dir / "reports" / "test-analysis-solution-review.json"
    else:
        paths = sorted((run_dir / "reports" / "test-case-reviews").glob("*.json"))
        aggregate = run_dir / "reports" / "test-case-review.json"
        final = run_dir / "reports" / "test-design-solution-review.json"
    if aggregate.exists():
        paths.append(aggregate)
    if final.exists():
        paths.append(final)
    return paths


def blocking_items(review: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for key in ("blockingIssues", "findings"):
        values = review.get(key, [])
        if not isinstance(values, list):
            continue
        for value in values:
            if not isinstance(value, dict):
                continue
            if key == "blockingIssues" or value.get("severity") == "blocking":
                items.append(value)
    return items


def item_location(item: dict[str, Any]) -> str:
    for key in ("artifactLocation", "location", "targetArtifact"):
        value = str(item.get(key) or "").strip()
        if value:
            return value
    return ""


def apply_review(
    run_dir: Path,
    root: Path,
    scope_name: str,
    review_path: Path,
    work_items: dict[str, Any],
) -> tuple[list[str], list[str]]:
    scope = scope_config(scope_name)
    report = load_json(review_path)
    prefix = scope.slice_dir_relative + "/"
    by_id = {
        item_id(item, scope): item
        for item in work_items.get("workItems", [])
        if isinstance(item, dict) and item_id(item, scope)
    }
    errors: list[str] = []
    reopened: list[str] = []
    now = datetime.now().isoformat(timespec="seconds")
    for finding in blocking_items(report):
        raw_location = item_location(finding)
        location = normalized_location(raw_location, run_dir, root)
        if not location:
            errors.append(f"{review_path}: blocking finding 缺少 location")
            continue
        if not location.startswith(prefix) or not location.endswith(".json"):
            errors.append(f"{review_path}: blocking location 必须指向 {prefix}<ID>.json: {location}")
            continue
        slice_path = run_dir / location
        if not slice_path.exists():
            errors.append(f"{review_path}: blocking location 指向的切片不存在: {location}")
            continue
        current_id = Path(location).stem
        item = by_id.get(current_id)
        if not item:
            errors.append(f"{review_path}: 未找到对应工作项: {current_id}")
            continue
        item["status"] = "in_progress"
        item["slicePath"] = location
        item["mergedAt"] = ""
        item["repairSource"] = rel_path(review_path, root)
        item.setdefault("repairReasons", [])
        item["repairReasons"].append(
            {
                "reviewId": report.get("artifactType", ""),
                "findingId": finding.get("id", ""),
                "description": finding.get("description", ""),
                "recommendation": finding.get("recommendation", ""),
                "appliedAt": now,
            }
        )
        reopened.append(current_id)
    return errors, reopened


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="根据 review blocking findings 重开分段工作项")
    parser.add_argument("run_dir", type=Path, help="outputs/runs/<run-id>")
    parser.add_argument("--scope", required=True, choices=["analysis", "design"])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--review", type=Path, help="指定 review JSON")
    group.add_argument("--all", action="store_true", help="扫描默认切片 review 和最终 review")
    args = parser.parse_args()

    root = repo_root()
    run_dir = resolve_path(args.run_dir, root)
    scope = scope_config(args.scope)
    try:
        work_items = load_work_items(run_dir, scope)
    except ValueError as exc:
        print(f"失败: {exc}", file=sys.stderr)
        return 1
    review_paths = [resolve_path(args.review, root)] if args.review else default_review_paths(run_dir, args.scope)
    if not review_paths:
        print("通过: 未找到可应用的 review 报告")
        return 0

    all_errors: list[str] = []
    reopened: list[str] = []
    for review_path in review_paths:
        if not review_path.exists():
            all_errors.append(f"review 不存在: {review_path}")
            continue
        errors, updated = apply_review(run_dir, root, args.scope, review_path, work_items)
        all_errors.extend(errors)
        reopened.extend(updated)

    for error in all_errors:
        print(f"失败: {error}", file=sys.stderr)
    if all_errors:
        return 1
    if reopened:
        dump_work_items(run_dir, scope, work_items)
        render_markdown_for_json(work_items_path(run_dir, scope))
        print(f"通过: 已重开 {scope.label}工作项 " + "、".join(sorted(set(reopened))))
        print(f"通过: 已更新 {rel_path(work_items_path(run_dir, scope), root)}")
    else:
        print("通过: 未发现 blocking findings，无需重开工作项")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
