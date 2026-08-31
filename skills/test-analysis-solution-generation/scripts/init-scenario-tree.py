#!/usr/bin/env python3
"""Initialize the Markdown-first frozen scenario tree."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

BIN_DIR = Path(__file__).resolve().parents[3] / "bin"
if str(BIN_DIR) not in sys.path:
    sys.path.insert(0, str(BIN_DIR))

from encoding_utils import configure_stdio
from markdown_process import write_markdown


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="初始化 Markdown SC 场景树")
    parser.add_argument("run_dir", type=Path, help="outputs/runs/<run-id>")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    run_dir = args.run_dir if args.run_dir.is_absolute() else root / args.run_dir
    output = run_dir / "process" / "scenario-tree.md"
    if output.exists() and not args.force:
        print(f"跳过: 已存在 {output.relative_to(root).as_posix()}")
        return 0
    text = """# 冻结测试场景树

## 需求范围

| 字段 | 内容 |
|---|---|
| 测试目标 | 待填写 |
| 测试范围 | 待填写 |
| 非测试范围 | 待填写 |

## 场景树

<!-- SC 标题固定使用以下层级：一级 ###、二级 ####、三级 #####。最多三层。 -->

### SC-001 待填写场景

- 场景说明：待填写
- 来源引用：待填写
"""
    write_markdown(output, text)
    print(f"通过: 已初始化 {output.relative_to(root).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
