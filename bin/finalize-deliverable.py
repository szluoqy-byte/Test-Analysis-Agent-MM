#!/usr/bin/env python3
"""Finalize one model-authored result JSON and assign stable TP/TC identifiers."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from encoding_utils import configure_stdio
from markdown_process import parse_scenario_headings, read_markdown
from run_artifacts import dump_json, load_json, render_json_artifact, validate_artifact
from stable_ids import assign_stable_ids


def flatten_scenarios(nodes: list[Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for node in nodes:
        if not isinstance(node, dict):
            continue
        node_id = str(node.get("id") or "")
        if node_id:
            result[node_id] = node
        children = node.get("children")
        if isinstance(children, list):
            result.update(flatten_scenarios(children))
    return result


def all_points(nodes: list[Any]) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        children = node.get("children")
        if isinstance(children, list) and children:
            points.extend(all_points(children))
        else:
            points.extend(item for item in node.get("testPoints", []) if isinstance(item, dict))
    return points


def all_cases(nodes: list[Any]) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for point in all_points(nodes):
        cases.extend(item for item in point.get("testCases", []) if isinstance(item, dict))
    return cases


def base_point(point: dict[str, Any]) -> dict[str, Any]:
    return {key: point.get(key) for key in ("id", "title", "objective", "basisRefs", "note") if key in point}


def work_item_errors(run_dir: Path, scope: str) -> list[str]:
    name = "test-point-work-items.json" if scope == "analysis" else "test-case-work-items.json"
    id_key = "leafScenarioId" if scope == "analysis" else "testPointId"
    path = run_dir / "process" / name
    if not path.is_file():
        return [f"缺少工作项控制文件: process/{name}"]
    items = load_json(path).get("workItems")
    if not isinstance(items, list) or not items:
        return [f"process/{name} 没有工作项"]
    errors: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            errors.append("工作项包含非对象节点")
        elif item.get("status") != "done":
            errors.append(f"工作项尚未通过评审: {item.get(id_key)} status={item.get('status')}")
    return errors


def analysis_tree_errors(run_dir: Path, draft: dict[str, Any]) -> list[str]:
    path = run_dir / "process" / "scenario-tree.md"
    if not path.is_file():
        return ["缺少 process/scenario-tree.md"]
    process_nodes = [(item.scenario_id, item.title) for item in parse_scenario_headings(read_markdown(path))]
    result_nodes = [
        (str(item.get("id") or ""), str(item.get("title") or ""))
        for item in flatten_scenarios(draft.get("scenarios", [])).values()
    ]
    return [] if process_nodes == result_nodes else ["结果草稿中的 SC 编号/标题与 process/scenario-tree.md 不一致"]


def design_analysis_source(run_dir: Path) -> Path:
    root = Path(__file__).resolve().parents[1]
    work_items_path = run_dir / "process" / "test-case-work-items.json"
    if work_items_path.is_file():
        source = str(load_json(work_items_path).get("analysisSource") or "").strip()
        if source:
            path = Path(source)
            return path if path.is_absolute() else root / path
    return run_dir / "deliverables" / "test-analysis-solution.json"


def design_inheritance_errors(run_dir: Path, draft: dict[str, Any]) -> list[str]:
    path = design_analysis_source(run_dir)
    if not path.is_file():
        return [f"设计固化缺少上游分析结果: {path}"]
    analysis_nodes = list(flatten_scenarios(load_json(path).get("scenarios", [])).values())
    design_nodes = list(flatten_scenarios(draft.get("scenarios", [])).values())
    if len(analysis_nodes) != len(design_nodes):
        return ["设计结果未完整继承分析方案的 SC 树"]
    errors: list[str] = []
    for analysis_node, design_node in zip(analysis_nodes, design_nodes):
        for key in ("id", "title", "fields"):
            if analysis_node.get(key) != design_node.get(key):
                errors.append(f"设计结果 SC {design_node.get('id')} 未继承分析字段 {key}")
        if not analysis_node.get("children"):
            expected = [base_point(item) for item in analysis_node.get("testPoints", []) if isinstance(item, dict)]
            actual = [base_point(item) for item in design_node.get("testPoints", []) if isinstance(item, dict)]
            if expected != actual:
                errors.append(f"设计结果 {design_node.get('id')} 未完整继承分析 TP")
    return errors


def restore_registry(path: Path, original: bytes | None) -> None:
    if original is None:
        if path.exists():
            path.unlink()
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(original)


def assign_analysis_ids(run_dir: Path, draft: dict[str, Any], previous: dict[str, Any]) -> None:
    previous_by_sc = flatten_scenarios(previous.get("scenarios", []))
    existing = all_points(previous.get("scenarios", []))
    for scenario_id, node in flatten_scenarios(draft.get("scenarios", [])).items():
        children = node.get("children")
        if isinstance(children, list) and children:
            continue
        incoming = [item for item in node.get("testPoints", []) if isinstance(item, dict)]
        previous_points = previous_by_sc.get(scenario_id, {}).get("testPoints", [])
        node["testPoints"] = assign_stable_ids(run_dir, "TP", incoming, previous_points, existing)


def assign_design_ids(run_dir: Path, draft: dict[str, Any], previous: dict[str, Any]) -> None:
    previous_points = {str(item.get("id")): item for item in all_points(previous.get("scenarios", []))}
    existing_cases = all_cases(previous.get("scenarios", []))
    for point in all_points(draft.get("scenarios", [])):
        tp_id = str(point.get("id") or "")
        incoming = [item for item in point.get("testCases", []) if isinstance(item, dict)]
        old_cases = previous_points.get(tp_id, {}).get("testCases", [])
        point["testCases"] = assign_stable_ids(run_dir, "TC", incoming, old_cases, existing_cases)


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="固化阶段结果 JSON 并分配稳定编号")
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--scope", required=True, choices=["analysis", "design"])
    parser.add_argument("--draft", required=True, type=Path, help="模型一次性生成的结果草稿 JSON")
    parser.add_argument("--replace", action="store_true", help="明确替换当前 run 已存在的同阶段结果")
    parser.add_argument("--keep-draft", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    run_dir = args.run_dir if args.run_dir.is_absolute() else root / args.run_dir
    draft_path = args.draft if args.draft.is_absolute() else root / args.draft
    target_name = "test-analysis-solution.json" if args.scope == "analysis" else "test-design-solution.json"
    target = run_dir / "deliverables" / target_name
    if target.is_file() and not args.replace:
        print(
            f"失败: 当前 run 已存在 {target_name}；请使用新 runid，或在明确返工覆盖时添加 --replace",
            file=sys.stderr,
        )
        return 1
    if not draft_path.is_file():
        print(f"失败: 草稿不存在: {draft_path}", file=sys.stderr)
        return 1
    try:
        draft = load_json(draft_path)
    except Exception as exc:
        print(f"失败: 草稿不是合法 JSON: {exc}", file=sys.stderr)
        return 1
    gate_errors = work_item_errors(run_dir, args.scope)
    gate_errors.extend(
        analysis_tree_errors(run_dir, draft)
        if args.scope == "analysis"
        else design_inheritance_errors(run_dir, draft)
    )
    if gate_errors:
        for error in gate_errors:
            print(f"失败: {error}", file=sys.stderr)
        return 1

    previous = load_json(target) if target.is_file() else {}
    registry_path = run_dir / "process" / "id-registry.json"
    original_registry = registry_path.read_bytes() if registry_path.is_file() else None
    try:
        if args.scope == "analysis":
            assign_analysis_ids(run_dir, draft, previous)
        else:
            assign_design_ids(run_dir, draft, previous)
    except Exception as exc:
        restore_registry(registry_path, original_registry)
        print(f"失败: 稳定编号分配失败: {exc}", file=sys.stderr)
        return 1
    errors, warnings = validate_artifact(draft)
    for warning in warnings:
        print(f"警告: {warning}")
    if errors:
        restore_registry(registry_path, original_registry)
        for error in errors:
            print(f"失败: {error}", file=sys.stderr)
        return 1
    dump_json(target, draft)
    target.with_suffix(".md").write_text(render_json_artifact(draft, target), encoding="utf-8")
    if not args.keep_draft and draft_path.resolve() != target.resolve():
        draft_path.unlink()
    print(f"通过: 已固化 {target.relative_to(root).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
