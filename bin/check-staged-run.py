#!/usr/bin/env python3
"""Run deterministic checks for an analysis or design staged run."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from encoding_utils import configure_stdio, subprocess_text_kwargs, utf8_env
from staged_workflow import rel_path, repo_root, resolve_path, scope_config


def run_command(command: list[str], root: Path) -> bool:
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
    return result.returncode == 0


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="运行 analysis/design 分段 run 的固定检查")
    parser.add_argument("run_dir", type=Path, help="outputs/runs/<run-id>")
    parser.add_argument("--scope", required=True, choices=["analysis", "design"])
    args = parser.parse_args()

    root = repo_root()
    run_dir = resolve_path(args.run_dir, root)
    scope = scope_config(args.scope)
    run_arg = rel_path(run_dir, root)
    markdown_path = run_dir / scope.markdown_relative
    commands = [
        [sys.executable, "bin/lint-run-json.py", run_arg],
        [sys.executable, "bin/render-run-markdown.py", run_arg, "--check"],
        [sys.executable, scope.markdown_lint_script, rel_path(markdown_path, root)],
        [sys.executable, "bin/check-artifact-consistency.py", run_arg],
    ]
    ok = True
    for command in commands:
        print("== " + " ".join(command) + " ==")
        ok &= run_command(command, root)
    if not ok:
        print("失败: 分段 run 固定检查未通过", file=sys.stderr)
        return 1
    print(f"通过: {scope.label}分段 run 固定检查全部通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
