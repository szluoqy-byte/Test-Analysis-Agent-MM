#!/usr/bin/env python3
"""Check fixed run artifact layout and basic solution consistency."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import os
from pathlib import Path


TASK_LIST_HEADER = "| 序号 | 阶段 | 负责 skill | 必须产物/检查点 | 状态 | 证据/路径 |"
TASK_STATUS_VALUES = {"pending", "in_progress", "done", "blocked", "skipped"}
ANALYSIS_REQUIRED_TASK_STAGES = [
    "固定 PROJECT_ROOT 与运行目录",
    "强制规则加载",
    "上下文来源索引",
    "输入事实建模",
    "测试技术路由",
    "专项分析",
    "按源补读",
    "测试分析方案生成",
    "确定性校验",
    "独立评审",
    "覆盖审查",
    "输出收口",
]
DESIGN_REQUIRED_TASK_STAGES = [
    "固定 PROJECT_ROOT 与运行目录",
    "测试分析方案校验",
    "强制规则加载",
    "上下文来源索引",
    "设计依据补读",
    "测试设计方案生成",
    "确定性校验",
    "独立评审",
    "覆盖审查",
    "输出收口",
]
OPTIONAL_TASK_STAGES = {"按源补读", "设计依据补读"}
TASK_STAGE_ALIASES = {
    "构建上下文包": "上下文来源索引",
    "记忆上下文构建": "上下文来源索引",
    "方法路由": "测试技术路由",
    "专项方法分析": "专项分析",
    "场景化测试点生成": "测试分析方案生成",
    "需求可测性分析": "输入事实建模",
    "设计方案提取": "输入事实建模",
}


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def collect_all_tables(lines: list[str], header: str) -> list[list[tuple[int, list[str]]]]:
    tables: list[list[tuple[int, list[str]]]] = []
    for start, line in enumerate(lines):
        if line != header:
            continue
        rows: list[tuple[int, list[str]]] = []
        for index in range(start + 2, len(lines)):
            row = lines[index]
            if not row.startswith("|"):
                break
            rows.append((index + 1, split_row(row)))
        tables.append(rows)
    return tables


def collect_first_table(lines: list[str], header: str) -> list[tuple[int, list[str]]]:
    tables = collect_all_tables(lines, header)
    return tables[0] if tables else []


def collect_solution_points(path: Path) -> set[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    points: set[str] = set()
    for line in lines:
        match = re.match(r"^#{3,6}\s+(TP-\d{3})\s+", line)
        if match:
            points.add(match.group(1))
    return points


def collect_test_cases(path: Path) -> set[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    cases: set[str] = set()
    for line in lines:
        heading_match = re.match(r"^#{4,5}\s+(TC-\d{3})\s+", line)
        bullet_match = re.match(r"^\s*-\s+(TC-\d{3})\s+", line)
        if heading_match:
            cases.add(heading_match.group(1))
        elif bullet_match:
            cases.add(bullet_match.group(1))
    return cases


def collect_task_rows(path: Path) -> list[tuple[int, list[str]]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return collect_first_table(lines, TASK_LIST_HEADER)


def has_any(paths: list[Path]) -> bool:
    return any(path.exists() for path in paths)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def existing_task_list_paths(run_dir: Path) -> list[Path]:
    preferred = [
        run_dir / "process" / "analysis-task-list.md",
        run_dir / "process" / "design-task-list.md",
    ]
    existing = [path for path in preferred if path.exists()]
    legacy = run_dir / "process" / "task-list.md"
    if not existing and legacy.exists():
        existing.append(legacy)
    return existing


def validate_task_list(path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    rows = collect_task_rows(path)
    if not rows:
        errors.append("任务清单缺少固定任务表")
        return errors, warnings

    stages: list[str] = []
    statuses: dict[str, str] = {}
    in_progress: list[str] = []

    for line_number, cells in rows:
        if len(cells) != 6:
            errors.append(f"任务清单第 {line_number} 行列数不正确")
            continue
        order, stage, _owner, _artifact, status, evidence = cells
        if not re.fullmatch(r"\d+", order):
            errors.append(f"任务清单第 {line_number} 行序号不是数字: {order}")
        if status not in TASK_STATUS_VALUES:
            errors.append(f"任务清单第 {line_number} 行状态非法: {status}")
        canonical_stage = TASK_STAGE_ALIASES.get(stage, stage)
        if status == "in_progress":
            in_progress.append(canonical_stage)
        if status in {"done", "blocked", "skipped"} and not evidence:
            errors.append(f"任务清单阶段 `{stage}` 状态为 {status} 但证据/路径为空")
        stages.append(canonical_stage)
        statuses[canonical_stage] = status

    if len(in_progress) > 1:
        errors.append("任务清单同时存在多个 in_progress 阶段: " + "、".join(in_progress))

    candidate_flows = [
        ("测试分析", ANALYSIS_REQUIRED_TASK_STAGES),
        ("测试设计", DESIGN_REQUIRED_TASK_STAGES),
    ]
    matched_flow = next(
        ((flow_name, required_stages) for flow_name, required_stages in candidate_flows if all(stage in statuses for stage in required_stages)),
        None,
    )
    if matched_flow is None:
        analysis_missing = [stage for stage in ANALYSIS_REQUIRED_TASK_STAGES if stage not in statuses]
        design_missing = [stage for stage in DESIGN_REQUIRED_TASK_STAGES if stage not in statuses]
        errors.append(
            "任务清单未匹配测试分析或测试设计固定阶段；"
            "分析缺少: "
            + "、".join(analysis_missing)
            + "；设计缺少: "
            + "、".join(design_missing)
        )
        return errors, warnings

    flow_name, required_stages = matched_flow
    positions = [stages.index(stage) for stage in required_stages if stage in stages]
    if positions != sorted(positions):
        errors.append(f"任务清单{flow_name}固定阶段顺序不正确")

    for stage in required_stages:
        status = statuses.get(stage)
        if stage in OPTIONAL_TASK_STAGES:
            if status not in {"done", "skipped"}:
                errors.append(f"任务清单可选阶段 `{stage}` 最终状态应为 done 或 skipped，当前为 {status}")
        elif status != "done":
            errors.append(f"任务清单必选阶段 `{stage}` 最终状态应为 done，当前为 {status}")

    return errors, warnings


def validate_context_pack(path: Path) -> tuple[list[str], list[str]]:
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    warnings: list[str] = []

    if not text.strip():
        errors.append("context-pack 为空")
        return errors, warnings
    for marker in ["上下文来源索引", "## 绑定结果", "projectBinding", "## 动态来源索引"]:
        if marker not in text:
            errors.append(f"context-pack 缺少固定渲染标记: {marker}")

    return errors, warnings


def validate_rules_pack(path: Path) -> tuple[list[str], list[str]]:
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    warnings: list[str] = []

    if not text.strip():
        errors.append("rules-pack 为空")
        return errors, warnings
    for marker in ["强制规则索引", "## 优先级策略", "## 加载策略", "## 规则来源索引"]:
        if marker not in text:
            errors.append(f"rules-pack 缺少固定渲染标记: {marker}")

    return errors, warnings


def normalize_scenario_tree(nodes: list[dict], include_points: bool = False) -> list[dict]:
    normalized: list[dict] = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        item = {
            "id": node.get("id"),
            "title": node.get("title"),
            "fields": node.get("fields", []),
        }
        children = node.get("children")
        if isinstance(children, list) and children:
            item["children"] = normalize_scenario_tree(children, include_points=include_points)
        else:
            item["children"] = []
            if include_points:
                item["testPoints"] = [
                    {
                        "id": point.get("id"),
                        "title": point.get("title"),
                        "objective": point.get("objective"),
                        "basisRefs": point.get("basisRefs", []),
                        "note": point.get("note", ""),
                    }
                    for point in node.get("testPoints", [])
                    if isinstance(point, dict)
                ]
        normalized.append(item)
    return normalized


def collect_leaf_ids(nodes: list[dict]) -> list[str]:
    leaf_ids: list[str] = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        children = node.get("children")
        if isinstance(children, list) and children:
            leaf_ids.extend(collect_leaf_ids(children))
        else:
            leaf_ids.append(str(node.get("id") or ""))
    return leaf_ids


def collect_test_point_ids(nodes: list[dict]) -> list[str]:
    point_ids: list[str] = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        children = node.get("children")
        if isinstance(children, list) and children:
            point_ids.extend(collect_test_point_ids(children))
        else:
            point_ids.extend(
                str(point.get("id") or "")
                for point in node.get("testPoints", [])
                if isinstance(point, dict)
            )
    return point_ids


def resolve_artifact_path(run_dir: Path, repo_root: Path, value: object) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    run_relative = run_dir / path
    if run_relative.exists():
        return run_relative
    return repo_root / path


def validate_done_work_items(
    data: dict,
    expected_ids: list[str],
    id_key: str,
    label: str,
    run_dir: Path,
    repo_root: Path,
) -> list[str]:
    errors: list[str] = []
    items = data.get("workItems", [])
    actual_ids = [str(item.get(id_key) or "") for item in items if isinstance(item, dict)]
    if actual_ids != expected_ids:
        errors.append(f"{label} workItems 与上游冻结 ID 不一致，期望 {expected_ids}，实际 {actual_ids}")
    for item in items:
        if not isinstance(item, dict):
            continue
        item_id = str(item.get(id_key) or "")
        if item.get("status") != "done":
            errors.append(f"{label} {item_id} 状态不是 done: {item.get('status')}")
        slice_path = resolve_artifact_path(run_dir, repo_root, item.get("slicePath"))
        if slice_path is None:
            errors.append(f"{label} {item_id} 缺少 slicePath")
        elif not slice_path.exists():
            errors.append(f"{label} {item_id} slicePath 不存在: {item.get('slicePath')}")
    return errors


def validate_slice_reviews(
    data: dict,
    id_key: str,
    label: str,
    review_dir: Path,
    run_dir: Path,
    repo_root: Path,
) -> list[str]:
    errors: list[str] = []
    for item in data.get("workItems", []):
        if not isinstance(item, dict):
            continue
        item_id = str(item.get(id_key) or "")
        if not item_id or item.get("status") != "done":
            continue
        review_path = review_dir / f"{item_id}.json"
        if not review_path.exists():
            errors.append(f"{label} {item_id} 缺少切片评审报告: {review_path.relative_to(run_dir)}")
            continue
        try:
            review = load_json(review_path)
        except Exception as exc:
            errors.append(f"{label} {item_id} 切片评审报告不是合法 JSON: {exc}")
            continue
        if "generationContext" not in review:
            errors.append(f"{label} {item_id} 切片评审报告缺少 generationContext")
        target = resolve_artifact_path(run_dir, repo_root, review.get("targetArtifact"))
        slice_path = resolve_artifact_path(run_dir, repo_root, item.get("slicePath"))
        if target is None:
            errors.append(f"{label} {item_id} 切片评审报告缺少 targetArtifact")
        elif slice_path is not None and target.resolve() != slice_path.resolve():
            errors.append(f"{label} {item_id} 切片评审 targetArtifact 未指向对应 slice")
    return errors


def validate_json_chain(run_dir: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []
    scenario_tree_path = run_dir / "process" / "scenario-tree.json"
    analysis_path = run_dir / "deliverables" / "test-analysis-solution.json"
    design_path = run_dir / "deliverables" / "test-design-solution.json"
    tp_work_items_path = run_dir / "process" / "test-point-work-items.json"
    tc_work_items_path = run_dir / "process" / "test-case-work-items.json"

    scenario_tree = load_json(scenario_tree_path) if scenario_tree_path.exists() else None
    analysis = load_json(analysis_path) if analysis_path.exists() else None
    design = load_json(design_path) if design_path.exists() else None

    if scenario_tree and analysis:
        frozen_tree = normalize_scenario_tree(scenario_tree.get("scenarios", []), include_points=False)
        analysis_tree = normalize_scenario_tree(analysis.get("scenarios", []), include_points=False)
        if frozen_tree != analysis_tree:
            errors.append("deliverables/test-analysis-solution.json 的 SC 树与 process/scenario-tree.json 不一致")

    if scenario_tree and tp_work_items_path.exists():
        work_items = load_json(tp_work_items_path)
        errors.extend(
            validate_done_work_items(
                work_items,
                collect_leaf_ids(scenario_tree.get("scenarios", [])),
                "leafScenarioId",
                "test-point-work-items",
                run_dir,
                repo_root,
            )
        )
        errors.extend(
            validate_slice_reviews(
                work_items,
                "leafScenarioId",
                "test-point-work-items",
                run_dir / "reports" / "test-point-reviews",
                run_dir,
                repo_root,
            )
        )

    if analysis and tc_work_items_path.exists():
        work_items = load_json(tc_work_items_path)
        errors.extend(
            validate_done_work_items(
                work_items,
                collect_test_point_ids(analysis.get("scenarios", [])),
                "testPointId",
                "test-case-work-items",
                run_dir,
                repo_root,
            )
        )
        errors.extend(
            validate_slice_reviews(
                work_items,
                "testPointId",
                "test-case-work-items",
                run_dir / "reports" / "test-case-reviews",
                run_dir,
                repo_root,
            )
        )

    if analysis and design:
        analysis_basis = normalize_scenario_tree(analysis.get("scenarios", []), include_points=True)
        design_basis = normalize_scenario_tree(design.get("scenarios", []), include_points=True)
        if analysis_basis != design_basis:
            errors.append("deliverables/test-design-solution.json 未完整继承 test-analysis-solution.json 的 SC/TP 基础字段")

    return errors


def main() -> int:
    configure_stdio()
    if len(sys.argv) != 2:
        print("用法: check-artifact-consistency.py <outputs/runs/<run-id>>", file=sys.stderr)
        return 2

    run_dir = Path(sys.argv[1])
    errors: list[str] = []
    warnings: list[str] = []

    if not run_dir.is_dir():
        print(f"失败: 运行目录不存在: {run_dir}")
        return 1

    repo_root = Path(__file__).resolve().parents[1]
    child_env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
    json_lint = subprocess.run(
        [sys.executable, str(repo_root / "bin" / "lint-run-json.py"), str(run_dir)],
        cwd=repo_root,
        env=child_env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    if json_lint.stdout:
        print(json_lint.stdout.rstrip())
    if json_lint.stderr:
        print(json_lint.stderr.rstrip(), file=sys.stderr)
    if json_lint.returncode != 0:
        return json_lint.returncode

    render_check = subprocess.run(
        [sys.executable, str(repo_root / "bin" / "render-run-markdown.py"), str(run_dir), "--check"],
        cwd=repo_root,
        env=child_env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    if render_check.stdout:
        print(render_check.stdout.rstrip())
    if render_check.stderr:
        print(render_check.stderr.rstrip(), file=sys.stderr)
    if render_check.returncode != 0:
        return render_check.returncode

    solution_path = run_dir / "deliverables" / "test-analysis-solution.md"
    design_solution_path = run_dir / "deliverables" / "test-design-solution.md"
    solution_json_path = run_dir / "deliverables" / "test-analysis-solution.json"
    design_solution_json_path = run_dir / "deliverables" / "test-design-solution.json"
    context_pack_path = run_dir / "process" / "context-pack.md"
    rules_pack_path = run_dir / "process" / "rules-pack.md"

    required_paths = [
        run_dir / "process" / "rules-pack.json",
        run_dir / "process" / "rules-pack.md",
        run_dir / "process" / "context-pack.json",
        run_dir / "process" / "context-pack.md",
    ]
    for required in required_paths:
        if not required.exists():
            errors.append(f"缺少固定运行产物: {required.relative_to(run_dir)}")

    if solution_json_path.exists() and not has_any(
        [
            run_dir / "process" / "analysis-task-list.json",
            run_dir / "process" / "task-list.json",
        ]
    ):
        errors.append("缺少测试分析任务清单: process/analysis-task-list.json")
    if solution_path.exists() and not has_any(
        [
            run_dir / "process" / "analysis-task-list.md",
            run_dir / "process" / "task-list.md",
        ]
    ):
        errors.append("缺少测试分析任务清单 Markdown: process/analysis-task-list.md")
    if design_solution_json_path.exists() and not has_any(
        [
            run_dir / "process" / "design-task-list.json",
            run_dir / "process" / "task-list.json",
        ]
    ):
        errors.append("缺少测试设计任务清单: process/design-task-list.json")
    if design_solution_path.exists() and not has_any(
        [
            run_dir / "process" / "design-task-list.md",
            run_dir / "process" / "task-list.md",
        ]
    ):
        errors.append("缺少测试设计任务清单 Markdown: process/design-task-list.md")
    if solution_json_path.exists():
        for relative in (
            "process/scenario-tree.json",
            "process/scenario-tree.md",
            "process/test-point-work-items.json",
            "process/test-point-work-items.md",
            "reports/analysis-coverage-review.json",
            "reports/analysis-coverage-review.md",
        ):
            if not (run_dir / relative).exists():
                errors.append(f"测试分析 run 缺少分层冻结产物: {relative}")
    if design_solution_json_path.exists():
        for relative in (
            "process/test-case-work-items.json",
            "process/test-case-work-items.md",
            "reports/design-coverage-review.json",
            "reports/design-coverage-review.md",
        ):
            if not (run_dir / relative).exists():
                errors.append(f"测试设计 run 缺少分层冻结产物: {relative}")

    if not solution_path.exists() and not design_solution_path.exists():
        errors.append("缺少主交付件: deliverables/test-analysis-solution.md 或 deliverables/test-design-solution.md")
    if not solution_json_path.exists() and not design_solution_json_path.exists():
        errors.append("缺少主交付件 JSON: deliverables/test-analysis-solution.json 或 deliverables/test-design-solution.json")

    for task_list_path in existing_task_list_paths(run_dir):
        task_errors, task_warnings = validate_task_list(task_list_path)
        errors.extend(f"{task_list_path.relative_to(run_dir)}: {error}" for error in task_errors)
        warnings.extend(f"{task_list_path.relative_to(run_dir)}: {warning}" for warning in task_warnings)
        rows = collect_task_rows(task_list_path)
        normalize_done = any(
            len(cells) == 6 and cells[1] == "输入文档归一化" and cells[4] == "done"
            for _line_number, cells in rows
        )
        if normalize_done:
            manifest_path = run_dir / "inputs" / "input-normalization-manifest.json"
            if not manifest_path.exists():
                errors.append("输入文档归一化已完成，但缺少 inputs/input-normalization-manifest.json")

    if context_pack_path.exists():
        context_errors, context_warnings = validate_context_pack(context_pack_path)
        errors.extend(context_errors)
        warnings.extend(context_warnings)
    if rules_pack_path.exists():
        rules_errors, rules_warnings = validate_rules_pack(rules_pack_path)
        errors.extend(rules_errors)
        warnings.extend(rules_warnings)

    try:
        errors.extend(validate_json_chain(run_dir, repo_root))
    except Exception as exc:
        errors.append(f"跨产物 JSON 链路校验失败: {exc}")

    if solution_path.exists():
        points = collect_solution_points(solution_path)
        if not points:
            errors.append("测试分析方案未找到 TP-* 测试点标题")

    if design_solution_path.exists():
        points = collect_solution_points(design_solution_path)
        cases = collect_test_cases(design_solution_path)
        if not points:
            errors.append("测试设计方案未找到 TP-* 测试点标题")
        if not cases:
            errors.append("测试设计方案未找到 TC-* 测试用例")

    for warning in warnings:
        print(f"警告: {warning}")
    for error in errors:
        print(f"失败: {error}")

    if errors:
        return 1
    print(f"通过: {run_dir} 运行产物路径和基础一致性校验通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
