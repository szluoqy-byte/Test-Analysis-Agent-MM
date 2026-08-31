#!/usr/bin/env python3
"""Initialize one Markdown test-case slice for a test point."""

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
    parser = argparse.ArgumentParser(description="初始化 TP 的 Markdown TC 切片")
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--tp", required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    run_dir = args.run_dir if args.run_dir.is_absolute() else root / args.run_dir
    work_items = load_json(run_dir / "process" / "test-case-work-items.json")
    item = next((row for row in work_items.get("workItems", []) if row.get("testPointId") == args.tp), None)
    if not item:
        print(f"失败: 未找到测试点工作项 {args.tp}", file=sys.stderr)
        return 1
    output = run_dir / "process" / "test-case-slices" / f"{args.tp}.md"
    if output.exists() and not args.force:
        print(f"跳过: 已存在 {output.relative_to(root).as_posix()}")
        return 0
    text = f"""# {args.tp} 测试用例切片

- 测试点：{item.get('testPointTitle', '')}
- 验证目标：{item.get('objective', '')}
- 叶子场景：{item.get('leafScenarioId', '')} {item.get('leafScenarioTitle', '')}

## 测试用例

<!-- 每个用例使用 `### 测试用例：标题`。过程件不分配 TC 编号，最终交付 JSON 统一分配稳定编号。 -->

### 测试用例：待填写

- 级别：Level 0/Level 1/Level 2/Level 3/Level 4
- 前置条件：待填写
- 测试数据：待填写具体名称、值和说明
- 步骤 1：待填写可执行动作
  - 预期：待填写对应结果
- 最终预期：待填写
- 来源引用：待填写
"""
    write_markdown(output, text)
    print(f"通过: 已初始化 {output.relative_to(root).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
