#!/usr/bin/env python3
"""Update analysis/design task-list JSON status deterministically."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from run_artifacts import dump_json, load_json


STATUS_BY_ACTION = {
    "start": "in_progress",
    "done": "done",
    "blocked": "blocked",
    "skipped": "skipped",
}

FLOW_STAGES = {
    "analysis": [
        ("准备持久 run", "test-analysis-workflow", "process/run-plan.json"),
        ("建立 Markdown 输入上下文", "rules-pack/context-source-indexing", "process/rules-pack.md、process/context-pack.md"),
        ("完成事实建模与方法分析", "input-fact-modeling/testing-method-router", "process/input-fact-model.md、process/testing-method-routing.md"),
        ("冻结 Markdown 场景树", "test-analysis-solution-generation", "process/scenario-tree.md、process/reviews/scenario-tree-review.md"),
        ("生成并评审 TP 切片", "test-analysis-solution-generation/review", "process/test-point-slices/*.md、process/reviews/test-point-reviews/*.md"),
        ("固化分析结果 JSON", "bin/finalize-deliverable.py", "deliverables/test-analysis-solution.json/.md"),
        ("完成整体语义评审", "test-analysis-solution-review", "process/reviews/test-analysis-solution-review.md"),
        ("完成覆盖闭环", "coverage-review", "process/analysis-fact-coverage-map.md、process/reviews/analysis-coverage-review.md"),
        ("生成最终人审报告", "final-report-generation", "reports/analysis-final-report.md"),
        ("校验并结束 run", "test-analysis-workflow", "bin/check-staged-run.py --scope analysis"),
    ],
    "design": [
        ("准备 run 并绑定分析结果", "test-design-workflow", "process/run-plan.json、deliverables/test-analysis-solution.json"),
        ("加载 Markdown 上下文", "rules-pack/context-source-indexing", "process/rules-pack.md、process/context-pack.md"),
        ("建立 TC 工作项", "test-design-solution-generation", "process/test-case-work-items.json"),
        ("生成并评审 TC 切片", "test-design-solution-generation/review", "process/test-case-slices/*.md、process/reviews/test-case-reviews/*.md"),
        ("固化设计结果 JSON", "bin/finalize-deliverable.py", "deliverables/test-design-solution.json/.md"),
        ("完成整体语义评审", "test-design-solution-review", "process/reviews/test-design-solution-review.md"),
        ("完成覆盖闭环与最终报告", "coverage-review/final-report-generation", "process/design-fact-coverage-map.md、process/reviews/design-coverage-review.md、reports/design-final-report.md"),
        ("校验并结束 run", "test-design-workflow", "bin/check-staged-run.py --scope design"),
    ],
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


def default_task_list(run_dir: Path, root: Path, flow: str) -> dict:
    stages = []
    for index, (stage, owner, checkpoint) in enumerate(FLOW_STAGES[flow], start=1):
        stages.append(
            {
                "order": index,
                "stage": stage,
                "owner": owner,
                "checkpoint": checkpoint.replace("<run-id>", run_dir.name),
                "status": "pending",
                "evidence": "",
            }
        )
    return {
        "artifactType": "task-list",
        "schemaVersion": "1.0",
        "metadata": {
            "runId": run_dir.name,
            "projectRoot": root.as_posix(),
            "generatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "flow": flow,
        },
        "stages": stages,
    }


def ensure_default_stages(data: dict, run_dir: Path, flow: str) -> dict:
    required = FLOW_STAGES[flow]
    existing = {stage.get("stage"): stage for stage in data.get("stages", []) if isinstance(stage, dict)}
    if all(stage_name in existing for stage_name, _owner, _checkpoint in required):
        return data
    metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
    rebuilt = default_task_list(run_dir, repo_root(), flow)
    rebuilt["metadata"].update(metadata)
    rebuilt["metadata"]["flow"] = flow
    for stage in rebuilt["stages"]:
        previous = existing.get(stage["stage"])
        if not isinstance(previous, dict):
            continue
        if previous.get("status"):
            stage["status"] = previous["status"]
        if previous.get("evidence"):
            stage["evidence"] = previous["evidence"]
        if previous.get("checkpoint"):
            stage["checkpoint"] = previous["checkpoint"]
    return rebuilt


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
    args = parser.parse_args()

    root = repo_root()
    run_dir = resolve_path(args.run_dir, root)
    path = task_path(run_dir, args.flow)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = load_json(path) if path.exists() else default_task_list(run_dir, root, args.flow)
    data = ensure_default_stages(data, run_dir, args.flow)
    try:
        update_task(data, args.stage, args.action, args.evidence)
    except ValueError as exc:
        print(f"失败: {exc}", file=sys.stderr)
        return 1
    dump_json(path, data)
    print(f"通过: 已更新 {rel_path(path, root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
