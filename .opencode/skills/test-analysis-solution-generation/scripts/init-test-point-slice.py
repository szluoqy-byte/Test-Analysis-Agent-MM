#!/usr/bin/env python3
"""Initialize one Markdown test-point slice for a leaf scenario."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

BIN_DIR = Path(__file__).resolve().parents[3] / "bin"
if str(BIN_DIR) not in sys.path:
    sys.path.insert(0, str(BIN_DIR))

from encoding_utils import configure_stdio
from markdown_process import write_markdown
from run_artifacts import load_json


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="初始化叶子 SC 的 Markdown TP 切片")
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--leaf-sc", required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    run_dir = args.run_dir if args.run_dir.is_absolute() else root / args.run_dir
    work_items = load_json(run_dir / "process" / "test-point-work-items.json")
    item = next((row for row in work_items.get("workItems", []) if row.get("leafScenarioId") == args.leaf_sc), None)
    if not item:
        print(f"失败: 未找到叶子场景工作项 {args.leaf_sc}", file=sys.stderr)
        return 1
    output = run_dir / "process" / "test-point-slices" / f"{args.leaf_sc}.md"
    if output.exists() and not args.force:
        print(f"跳过: 已存在 {output.relative_to(root).as_posix()}")
        return 0
    path_text = " > ".join(f"{row.get('id')} {row.get('title')}" for row in item.get("scenarioPath", []))
    text = f"""# {args.leaf_sc} 测试点切片

- 场景路径：{path_text}
- 叶子场景：{item.get('leafScenarioTitle', '')}

## 测试点

<!-- 每个测试点使用 `### 测试点：标题`。过程件不分配 TP 编号，最终交付 JSON 统一分配稳定编号。 -->

### 测试点：E2E场景测试

- 验证目标：待填写
- 依据引用：待填写
- 说明：待填写
"""
    write_markdown(output, text)
    print(f"通过: 已初始化 {output.relative_to(root).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
