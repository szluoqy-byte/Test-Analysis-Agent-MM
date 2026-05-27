#!/usr/bin/env python3
"""Check design-document Mermaid blocks for image-export friendly syntax."""

from __future__ import annotations

import re
import sys
from pathlib import Path


DESIGN_DOC = Path("docs/testcase-title-outline-agent-design.md")
BANNED_IN_BLOCK = [
    "subgraph",
    "<br",
    "<br/>",
    "\\n",
    "classDef",
    "style ",
    "%%{",
    "click ",
    "::",
    ";",
]
BANNED_IN_DOC = [
    "![主运行流程]",
    "assets/main-run-flow",
]
NODE_RE = re.compile(r'^\s*[A-Za-z][A-Za-z0-9_]*\["[^"<>`\\]+"\]\s*$')
EDGE_RE = re.compile(r"^\s*[A-Za-z][A-Za-z0-9_]*\s*-->\s*[A-Za-z][A-Za-z0-9_]*\s*$")
SAFE_ID_RE = re.compile(r"n\d{2}$")


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def extract_mermaid_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    parts = text.split("```mermaid")
    for part in parts[1:]:
        body, sep, _rest = part.partition("```")
        if not sep:
            blocks.append(part)
        else:
            blocks.append(body.strip())
    return blocks


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) == 2 else DESIGN_DOC
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []

    if text.count("```") % 2 != 0:
        fail("Markdown fenced code block 数量不成对", errors)

    for marker in BANNED_IN_DOC:
        if marker in text:
            fail(f"设计文档仍包含图片化主流程引用: {marker}", errors)

    blocks = extract_mermaid_blocks(text)
    if not blocks:
        fail("设计文档缺少 Mermaid 代码块", errors)
    if len(blocks) != 1:
        fail(f"设计文档 Mermaid 代码块数量应为 1，实际为 {len(blocks)}", errors)

    for block_index, block in enumerate(blocks, start=1):
        lines = [line.rstrip() for line in block.splitlines() if line.strip()]
        if not lines:
            fail(f"第 {block_index} 个 Mermaid 代码块为空", errors)
            continue
        if lines[0].strip() != "flowchart TD":
            fail(
                f"第 {block_index} 个 Mermaid 代码块应使用官方 flowchart TD 语法，"
                f"实际首行是: {lines[0].strip()}",
                errors,
            )
        for banned in BANNED_IN_BLOCK:
            if banned in block:
                fail(f"第 {block_index} 个 Mermaid 代码块包含不利于图片导出的特性: {banned}", errors)
        for line_number, line in enumerate(lines[1:], start=2):
            if NODE_RE.fullmatch(line) or EDGE_RE.fullmatch(line):
                continue
            if "-->" in line:
                fail(
                    f"第 {block_index} 个 Mermaid 代码块第 {line_number} 行应只用节点 ID 连线，不要在连线上声明节点文本: {line}",
                    errors,
                )

        ids: set[str] = set()
        for line in lines[1:]:
            node_match = re.match(r'^\s*([A-Za-z][A-Za-z0-9_]*)\["', line)
            if node_match:
                node_id = node_match.group(1)
                ids.add(node_id)
                if not SAFE_ID_RE.fullmatch(node_id):
                    fail(f"节点 ID `{node_id}` 应使用 n01 这类安全编号，避免 Mermaid 保留字或渲染器差异", errors)

        for line_number, line in enumerate(lines[1:], start=2):
            edge_match = re.match(
                r"^\s*([A-Za-z][A-Za-z0-9_]*)\s*-->\s*([A-Za-z][A-Za-z0-9_]*)\s*$",
                line,
            )
            if not edge_match:
                continue
            source, target = edge_match.groups()
            for node_id in (source, target):
                if node_id not in ids:
                    fail(f"第 {block_index} 个 Mermaid 代码块第 {line_number} 行引用了未定义节点: {node_id}", errors)

    if errors:
        for error in errors:
            print(f"失败: {error}")
        return 1

    print(f"通过: {path} Mermaid 主流程图使用图片导出友好的基础语法")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
