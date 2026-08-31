#!/usr/bin/env python3
"""Mark Markdown-first analysis/design work items complete after review."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from encoding_utils import configure_stdio
from markdown_process import review_result
from staged_workflow import (
    dump_work_items,
    item_id,
    load_work_items,
    rel_path,
    repo_root,
    resolve_path,
    review_path_for,
    scope_config,
    slice_path_for,
)


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="完成已生成并评审的 Markdown 分段工作项")
    parser.add_argument("run_dir", type=Path, help="outputs/runs/<run-id>")
    parser.add_argument("--scope", required=True, choices=["analysis", "design"])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true")
    group.add_argument("--ids", nargs="+")
    args = parser.parse_args()

    root = repo_root()
    run_dir = resolve_path(args.run_dir, root)
    scope = scope_config(args.scope)
    try:
        data = load_work_items(run_dir, scope)
    except ValueError as exc:
        print(f"失败: {exc}", file=sys.stderr)
        return 1

    selected = set(args.ids or [])
    known: set[str] = set()
    completed: list[str] = []
    errors: list[str] = []
    for item in data.get("workItems", []):
        if not isinstance(item, dict):
            continue
        current_id = item_id(item, scope)
        known.add(current_id)
        if not args.all and current_id not in selected:
            continue
        slice_path = slice_path_for(run_dir, scope, current_id)
        review_path = review_path_for(run_dir, scope, current_id)
        if not slice_path.is_file():
            errors.append(f"{current_id} 缺少切片: {rel_path(slice_path, root)}")
            continue
        if not review_path.is_file():
            errors.append(f"{current_id} 缺少评审: {rel_path(review_path, root)}")
            continue
        result = review_result(review_path)
        if result != "通过":
            errors.append(f"{current_id} 评审结论不是通过: {result or '未填写'}")
            continue
        item["status"] = "done"
        item["slicePath"] = rel_path(slice_path, root)
        item["completedAt"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        item["contentChanged"] = False
        item["reopenReason"] = ""
        item.pop("mergedAt", None)
        completed.append(current_id)

    missing = sorted(selected - known)
    if missing:
        errors.append("未知工作项 ID: " + ", ".join(missing))
    if errors:
        for error in errors:
            print(f"失败: {error}", file=sys.stderr)
        return 1
    dump_work_items(run_dir, scope, data)
    print(f"通过: 已完成 {args.scope} 工作项 {', '.join(completed) if completed else '无'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
