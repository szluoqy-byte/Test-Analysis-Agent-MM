#!/usr/bin/env python3
"""Merge analysis/design staged slices in bulk."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from encoding_utils import configure_stdio, subprocess_text_kwargs, utf8_env
from staged_workflow import (
    item_id,
    iter_selected_items,
    load_work_items,
    rel_path,
    repo_root,
    resolve_path,
    scope_config,
    slice_path_for,
)


def run_command(command: list[str], root: Path) -> int:
    result = subprocess.run(
        command,
        cwd=root,
        env=utf8_env(),
        **subprocess_text_kwargs(),
        capture_output=True,
        check=False,
    )
    if result.stdout:
        print(result.stdout.rstrip())
    if result.stderr:
        print(result.stderr.rstrip(), file=sys.stderr)
    return result.returncode


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="批量合并 analysis/design 分段切片")
    parser.add_argument("run_dir", type=Path, help="outputs/runs/<run-id>")
    parser.add_argument("--scope", required=True, choices=["analysis", "design"])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="合并全部工作项")
    group.add_argument("--pending", action="store_true", help="合并未完成工作项")
    group.add_argument("--ids", nargs="+", help="合并指定 SC/TP ID")
    parser.add_argument("--no-renumber", action="store_true", help="透传给单切片 merge 脚本")
    args = parser.parse_args()

    root = repo_root()
    run_dir = resolve_path(args.run_dir, root)
    scope = scope_config(args.scope)
    try:
        work_items = load_work_items(run_dir, scope)
    except ValueError as exc:
        print(f"失败: {exc}", file=sys.stderr)
        return 1

    status = "all" if args.all or args.ids else "pending"
    items = iter_selected_items(work_items, scope, status=status, ids=args.ids or [])
    if not items:
        print("通过: 没有需要合并的工作项")
        return 0

    errors: list[str] = []
    merged = 0
    for item in items:
        current_id = item_id(item, scope)
        slice_path = slice_path_for(run_dir, scope, current_id)
        if not slice_path.exists():
            errors.append(f"{current_id} 切片不存在: {rel_path(slice_path, root)}")
            continue
        command = [sys.executable, scope.merge_script, rel_path(run_dir, root), "--slice", rel_path(slice_path, root)]
        if args.no_renumber:
            command.append("--no-renumber")
        code = run_command(command, root)
        if code == 0:
            merged += 1
        else:
            errors.append(f"{current_id} 合并失败")

    for error in errors:
        print(f"失败: {error}", file=sys.stderr)
    if errors:
        return 1
    print(f"通过: 已合并 {merged} 个切片")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
