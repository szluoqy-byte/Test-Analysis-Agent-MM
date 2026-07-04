#!/usr/bin/env python3
"""Render Markdown artifacts from run JSON canonical files."""

from __future__ import annotations

import argparse
from pathlib import Path

from encoding_utils import configure_stdio
from run_artifacts import collect_renderable_json_files, load_json, render_json_artifact


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="从 run JSON canonical 渲染 Markdown")
    parser.add_argument("run_dir", type=Path, help="outputs/runs/<run-id>")
    parser.add_argument("--check", action="store_true", help="只检查现有 Markdown 是否与 JSON 渲染结果一致")
    args = parser.parse_args()

    run_dir = args.run_dir
    if not run_dir.is_dir():
        print(f"失败: 运行目录不存在: {run_dir}")
        return 1

    pairs = collect_renderable_json_files(run_dir)
    if not pairs:
        print(f"失败: 未找到可渲染 JSON 产物: {run_dir}")
        return 1

    errors: list[str] = []
    rendered_count = 0
    for json_path, markdown_path in pairs:
        try:
            rendered = render_json_artifact(load_json(json_path), json_path)
        except Exception as exc:
            errors.append(f"{json_path.relative_to(run_dir)} 渲染失败: {exc}")
            continue

        if args.check:
            if not markdown_path.exists():
                errors.append(f"缺少派生 Markdown: {markdown_path.relative_to(run_dir)}")
                continue
            current = markdown_path.read_text(encoding="utf-8", errors="replace")
            if current != rendered:
                errors.append(f"派生 Markdown 已漂移: {markdown_path.relative_to(run_dir)}")
            continue

        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        with markdown_path.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(rendered)
        rendered_count += 1

    for error in errors:
        print(f"失败: {error}")
    if errors:
        return 1
    if args.check:
        print(f"通过: {run_dir} Markdown 派生产物与 JSON 一致")
    else:
        print(f"通过: 已渲染 {rendered_count} 个 Markdown 派生产物")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
