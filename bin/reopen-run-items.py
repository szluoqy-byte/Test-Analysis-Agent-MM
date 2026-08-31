#!/usr/bin/env python3
"""Reopen persistent analysis/design work items for incremental regeneration."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from encoding_utils import configure_stdio
from run_artifacts import dump_json, load_json
from staged_workflow import item_id, repo_root, resolve_path, scope_config


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--scope", required=True, choices=["analysis", "design"])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true")
    group.add_argument("--ids", nargs="+")
    parser.add_argument("--reason", default="持久 run 依赖变化")
    args = parser.parse_args()

    root = repo_root()
    run_dir = resolve_path(args.run_dir, root)
    scope = scope_config(args.scope)
    path = run_dir / scope.work_items_relative
    if not path.is_file():
        print(f"失败: 工作项不存在: {path}", file=sys.stderr)
        return 1
    data = load_json(path)
    selected = set(args.ids or [])
    reopened: list[str] = []
    known: set[str] = set()
    for item in data.get("workItems", []):
        if not isinstance(item, dict):
            continue
        current_id = item_id(item, scope)
        known.add(current_id)
        if not args.all and current_id not in selected:
            continue
        item["status"] = "pending"
        item.pop("completedAt", None)
        item.pop("mergedAt", None)
        item["contentChanged"] = True
        item["reopenReason"] = args.reason
        reopened.append(current_id)
    missing = sorted(selected - known)
    if missing:
        print(f"失败: 未知工作项 ID: {', '.join(missing)}", file=sys.stderr)
        return 1
    dump_json(path, data)
    print(f"通过: 已重开 {args.scope} 工作项 {', '.join(reopened) if reopened else '无'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
