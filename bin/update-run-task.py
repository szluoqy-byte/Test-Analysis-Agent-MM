#!/usr/bin/env python3
"""Update analysis/design task-list JSON status deterministically."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from run_artifacts import dump_json, load_json, render_json_artifact


STATUS_BY_ACTION = {
    "start": "in_progress",
    "done": "done",
    "blocked": "blocked",
    "skipped": "skipped",
}


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_path(path: Path, root: Path) -> Path:
    return path if path.is_absolute() else root / path


def rel_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def task_path(run_dir: Path, flow: str) -> Path:
    return run_dir / "process" / f"{flow}-task-list.json"


def update_task(data: dict, stage_name: str, action: str, evidence: str) -> None:
    status = STATUS_BY_ACTION[action]
    found = False
    for stage in data.get("stages", []):
        if not isinstance(stage, dict):
            continue
        if action == "start" and stage.get("status") == "in_progress" and stage.get("stage") != stage_name:
            stage["status"] = "pending"
        if stage.get("stage") != stage_name:
            continue
        found = True
        stage["status"] = status
        if evidence:
            stage["evidence"] = evidence
        elif status in {"done", "blocked", "skipped"} and not stage.get("evidence"):
            stage["evidence"] = "由 bin/update-run-task.py 更新"
    if not found:
        raise ValueError(f"任务清单中不存在阶段: {stage_name}")


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="更新 run 任务清单状态")
    parser.add_argument("run_dir", type=Path, help="outputs/runs/<run-id>")
    parser.add_argument("--flow", required=True, choices=["analysis", "design"])
    parser.add_argument("--stage", required=True, help="阶段名称，必须与 task-list JSON 中的 stage 完全一致")
    parser.add_argument("--action", required=True, choices=sorted(STATUS_BY_ACTION))
    parser.add_argument("--evidence", default="", help="证据或路径")
    parser.add_argument("--no-render", action="store_true", help="只更新 JSON，不刷新 Markdown")
    args = parser.parse_args()

    root = repo_root()
    run_dir = resolve_path(args.run_dir, root)
    path = task_path(run_dir, args.flow)
    if not path.exists():
        print(f"失败: 任务清单不存在: {path}", file=sys.stderr)
        return 1
    data = load_json(path)
    try:
        update_task(data, args.stage, args.action, args.evidence)
    except ValueError as exc:
        print(f"失败: {exc}", file=sys.stderr)
        return 1
    dump_json(path, data)
    if not args.no_render:
        path.with_suffix(".md").write_text(render_json_artifact(data), encoding="utf-8")
    print(f"通过: 已更新 {rel_path(path, root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
