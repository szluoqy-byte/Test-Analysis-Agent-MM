#!/usr/bin/env python3
"""Render human-readable Markdown from analysis/design result JSON only."""

from __future__ import annotations

import argparse
from pathlib import Path

from encoding_utils import configure_stdio
from run_artifacts import collect_renderable_json_files, load_json, render_json_artifact


def select_artifact_pairs(run_dir: Path, artifacts: list[str]) -> tuple[list[tuple[Path, Path]], list[str]]:
    pairs = collect_renderable_json_files(run_dir)
    if not artifacts:
        return pairs, []

    available = {json_path.resolve(): (json_path, markdown_path) for json_path, markdown_path in pairs}
    selected: list[tuple[Path, Path]] = []
    errors: list[str] = []
    root = run_dir.resolve()
    for artifact in artifacts:
        requested = Path(artifact)
        json_path = requested if requested.is_absolute() else run_dir / requested
        resolved = json_path.resolve()
        try:
            resolved.relative_to(root)
        except ValueError:
            errors.append(f"指定 JSON 不在运行目录内: {artifact}")
            continue
        pair = available.get(resolved)
        if pair is None:
            errors.append(f"指定 JSON 不是可渲染的运行产物或不存在: {artifact}")
            continue
        if pair not in selected:
            selected.append(pair)
    return selected, errors


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="从分析/设计结果 JSON 渲染人读 Markdown")
    parser.add_argument("run_dir", type=Path, help="outputs/runs/<run-id>")
    parser.add_argument("--check", action="store_true", help="只检查现有 Markdown 是否与 JSON 渲染结果一致")
    parser.add_argument(
        "--artifact",
        action="append",
        default=[],
        metavar="RELATIVE_JSON",
        help="只渲染或检查指定 run 内的结果 JSON；可重复传入",
    )
    args = parser.parse_args()

    run_dir = args.run_dir
    if not run_dir.is_dir():
        print(f"失败: 运行目录不存在: {run_dir}")
        return 1

    pairs, errors = select_artifact_pairs(run_dir, args.artifact)
    if errors:
        for error in errors:
            print(f"失败: {error}")
        return 1
    if not pairs:
        print(f"失败: 未找到可渲染的分析/设计结果 JSON: {run_dir}")
        return 1

    errors = []
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
