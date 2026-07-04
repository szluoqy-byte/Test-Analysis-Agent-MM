#!/usr/bin/env python3
"""Update analysis/design task-list JSON status deterministically."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from run_artifacts import dump_json, load_json, render_json_artifact


STATUS_BY_ACTION = {
    "start": "in_progress",
    "done": "done",
    "blocked": "blocked",
    "skipped": "skipped",
}

FLOW_STAGES = {
    "analysis": [
        ("固定 PROJECT_ROOT 与运行目录", "test-analysis-workflow", "outputs/runs/<run-id>/"),
        ("强制规则加载", "bin/build-rules-pack.py", "process/rules-pack.json"),
        ("上下文来源索引", "context-source-indexing", "process/context-pack.json"),
        ("输入事实建模", "input-fact-modeling", "process/input-fact-model.json"),
        ("测试技术路由", "testing-method-router", "测试技术路由结果"),
        ("专项分析", "testing-method-router", "覆盖维度建议、测试点候选、补读记录"),
        ("按源补读", "testing-method-router", "按需补读记录、来源说明"),
        ("测试分析方案生成", "test-analysis-solution-generation", "process/scenario-tree.json、process/test-point-work-items.json、process/test-point-slices/<SC-ID>.json、deliverables/test-analysis-solution.json"),
        ("确定性校验", "bin", "lint-run-json.py、render-run-markdown.py、lint-test-analysis-solution.py"),
        ("独立评审", "test-analysis-solution-review", "process/reviews/test-analysis-solution-review.json"),
        ("覆盖审查", "coverage-review", "process/reviews/analysis-coverage-review.json"),
        ("最终报告生成", "final-report-generation", "reports/analysis-final-report.json、reports/analysis-final-report.md"),
        ("输出收口", "test-analysis-workflow", "bin/check-staged-run.py --scope analysis"),
    ],
    "design": [
        ("固定 PROJECT_ROOT 与运行目录", "test-design-workflow", "outputs/runs/<run-id>/"),
        ("测试分析方案校验", "test-design-workflow", "deliverables/test-analysis-solution.json"),
        ("强制规则加载", "bin/build-rules-pack.py", "process/rules-pack.json"),
        ("上下文来源索引", "context-source-indexing", "process/context-pack.json"),
        ("设计依据补读", "test-design-workflow", "归一化需求、可选设计方案、完整测试分析方案"),
        ("测试设计方案生成", "test-design-solution-generation", "process/test-case-work-items.json、process/test-case-slices/<TP-ID>.json、deliverables/test-design-solution.json"),
        ("确定性校验", "lint-run-json/render-run-markdown/lint-test-design-solution", "JSON 与 Markdown 校验"),
        ("独立评审", "test-design-solution-review", "process/reviews/test-design-solution-review.json"),
        ("覆盖审查", "coverage-review", "process/reviews/design-coverage-review.json"),
        ("最终报告生成", "final-report-generation", "reports/design-final-report.json、reports/design-final-report.md"),
        ("输出收口", "test-design-workflow", "bin/check-staged-run.py --scope design"),
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
    parser.add_argument("--no-render", action="store_true", help="只更新 JSON，不刷新 Markdown")
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
    if not args.no_render:
        path.with_suffix(".md").write_text(render_json_artifact(data), encoding="utf-8")
    print(f"通过: 已更新 {rel_path(path, root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
