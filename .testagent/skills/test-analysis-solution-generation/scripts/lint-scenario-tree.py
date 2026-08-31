#!/usr/bin/env python3
"""Lint a Markdown-first frozen scenario tree."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

BIN_DIR = Path(__file__).resolve().parents[3] / "bin"
if str(BIN_DIR) not in sys.path:
    sys.path.insert(0, str(BIN_DIR))

from encoding_utils import configure_stdio
from markdown_process import validate_scenario_tree


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="校验 Markdown SC 场景树")
    parser.add_argument("scenario_tree", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    path = args.scenario_tree if args.scenario_tree.is_absolute() else root / args.scenario_tree
    if not path.is_file():
        print(f"失败: 场景树不存在: {path}", file=sys.stderr)
        return 1
    errors, warnings = validate_scenario_tree(path)
    for warning in warnings:
        print(f"警告: {warning}")
    for error in errors:
        print(f"失败: {error}", file=sys.stderr)
    if errors:
        return 1
    print(f"通过: {path} Markdown 场景树校验通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
