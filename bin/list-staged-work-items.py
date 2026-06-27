#!/usr/bin/env python3
"""List staged analysis/design work items and suggested deterministic commands."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from encoding_utils import configure_stdio
from staged_workflow import (
    item_id,
    iter_selected_items,
    load_work_items,
    rel_path,
    repo_root,
    resolve_path,
    review_path_for,
    scope_config,
    slice_path_for,
)


STATUS_CHOICES = ("all", "pending", "in_progress", "done", "blocked", "skipped")


def next_command(run_dir: Path, scope_name: str, current_id: str, status: str, slice_exists: bool, review_exists: bool) -> str:
    run_arg = rel_path(run_dir, repo_root())
    if not slice_exists:
        return f"python bin/init-staged-slices.py {run_arg} --scope {scope_name} --ids {current_id}"
    if status != "done":
        return f"填写 slice 后运行: python bin/init-report-artifact.py {run_arg} --kind review --review-type {'test-point-review' if scope_name == 'analysis' else 'test-case-review'} --target-id {current_id} --force"
    if not review_exists:
        return f"python bin/init-report-artifact.py {run_arg} --kind review --review-type {'test-point-review' if scope_name == 'analysis' else 'test-case-review'} --target-id {current_id} --force"
    return "已完成；如需重跑可使用 merge/check 固定脚本"


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="列出 analysis/design 分段工作项状态")
    parser.add_argument("run_dir", type=Path, help="outputs/runs/<run-id>")
    parser.add_argument("--scope", required=True, choices=["analysis", "design"])
    parser.add_argument("--status", default="all", choices=STATUS_CHOICES)
    parser.add_argument("--ids", nargs="*", default=[], help="只列出指定 SC/TP ID")
    args = parser.parse_args()

    root = repo_root()
    run_dir = resolve_path(args.run_dir, root)
    scope = scope_config(args.scope)
    try:
        work_items = load_work_items(run_dir, scope)
    except ValueError as exc:
        print(f"失败: {exc}", file=sys.stderr)
        return 1

    items = iter_selected_items(work_items, scope, status=args.status, ids=args.ids)
    print(f"{scope.label}工作项: {len(items)} 个")
    for item in items:
        current_id = item_id(item, scope)
        status = str(item.get("status") or "pending")
        slice_path = slice_path_for(run_dir, scope, current_id)
        review_path = review_path_for(run_dir, scope, current_id)
        slice_exists = slice_path.exists()
        review_exists = review_path.exists()
        print(
            " | ".join(
                [
                    current_id,
                    f"status={status}",
                    f"slice={rel_path(slice_path, root) if slice_exists else 'missing'}",
                    f"review={rel_path(review_path, root) if review_exists else 'missing'}",
                    f"mergedAt={item.get('mergedAt') or ''}",
                ]
            )
        )
        print("  next: " + next_command(run_dir, args.scope, current_id, status, slice_exists, review_exists))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
