#!/usr/bin/env python3
"""Initialize analysis/design staged slices in bulk."""

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
    parser = argparse.ArgumentParser(description="批量初始化 analysis/design 分段切片")
    parser.add_argument("run_dir", type=Path, help="outputs/runs/<run-id>")
    parser.add_argument("--scope", required=True, choices=["analysis", "design"])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="初始化全部工作项")
    group.add_argument("--pending", action="store_true", help="初始化未完成工作项")
    group.add_argument("--ids", nargs="+", help="初始化指定 SC/TP ID")
    parser.add_argument("--force", action="store_true", help="覆盖已存在切片")
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
        print("通过: 没有需要初始化的工作项")
        return 0

    errors = 0
    initialized = 0
    for item in items:
        current_id = item_id(item, scope)
        output_path = slice_path_for(run_dir, scope, current_id)
        effective_force = args.force or bool(item.get("contentChanged", False))
        if output_path.exists() and not effective_force:
            print(f"跳过: 切片已存在 {rel_path(output_path, root)}")
            continue
        command = [sys.executable, scope.init_script, rel_path(run_dir, root), scope.init_id_arg, current_id]
        if effective_force:
            command.append("--force")
        code = run_command(command, root)
        if code == 0:
            initialized += 1
        else:
            errors += 1

    if errors:
        print(f"失败: {errors} 个切片初始化失败", file=sys.stderr)
        return 1
    print(f"通过: 已初始化 {initialized} 个切片")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
