#!/usr/bin/env python3
"""Shared helpers for staged analysis/design workflow scripts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from run_artifacts import dump_json, load_json


@dataclass(frozen=True)
class StageScope:
    name: str
    label: str
    item_id_key: str
    work_items_relative: str
    slice_dir_relative: str
    review_dir_relative: str
    init_script: str
    init_id_arg: str
    markdown_lint_script: str
    markdown_relative: str


SCOPES = {
    "analysis": StageScope(
        name="analysis",
        label="测试分析",
        item_id_key="leafScenarioId",
        work_items_relative="process/test-point-work-items.json",
        slice_dir_relative="process/test-point-slices",
        review_dir_relative="process/reviews/test-point-reviews",
        init_script="skills/test-analysis-solution-generation/scripts/init-test-point-slice.py",
        init_id_arg="--leaf-sc",
        markdown_lint_script="bin/lint-test-analysis-solution.py",
        markdown_relative="deliverables/test-analysis-solution.md",
    ),
    "design": StageScope(
        name="design",
        label="测试设计",
        item_id_key="testPointId",
        work_items_relative="process/test-case-work-items.json",
        slice_dir_relative="process/test-case-slices",
        review_dir_relative="process/reviews/test-case-reviews",
        init_script="skills/test-design-solution-generation/scripts/init-test-case-slice.py",
        init_id_arg="--tp",
        markdown_lint_script="bin/lint-test-design-solution.py",
        markdown_relative="deliverables/test-design-solution.md",
    ),
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_path(path: Path, root: Path) -> Path:
    return path if path.is_absolute() else root / path


def rel_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def scope_config(scope: str) -> StageScope:
    try:
        return SCOPES[scope]
    except KeyError as exc:
        raise ValueError("scope 必须为 analysis 或 design") from exc


def work_items_path(run_dir: Path, scope: StageScope) -> Path:
    return run_dir / scope.work_items_relative


def slice_path_for(run_dir: Path, scope: StageScope, item_id: str) -> Path:
    return run_dir / scope.slice_dir_relative / f"{item_id}.md"


def review_path_for(run_dir: Path, scope: StageScope, item_id: str) -> Path:
    return run_dir / scope.review_dir_relative / f"{item_id}.md"


def load_work_items(run_dir: Path, scope: StageScope) -> dict[str, Any]:
    path = work_items_path(run_dir, scope)
    if not path.exists():
        raise ValueError(f"工作项索引不存在: {path}")
    data = load_json(path)
    if not isinstance(data.get("workItems"), list):
        raise ValueError(f"工作项索引缺少 workItems[]: {path}")
    return data


def dump_work_items(run_dir: Path, scope: StageScope, data: dict[str, Any]) -> None:
    dump_json(work_items_path(run_dir, scope), data)


def item_id(item: dict[str, Any], scope: StageScope) -> str:
    return str(item.get(scope.item_id_key) or "")


def iter_selected_items(
    work_items: dict[str, Any],
    scope: StageScope,
    *,
    status: str = "all",
    ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    selected_ids = set(ids or [])
    items: list[dict[str, Any]] = []
    for item in work_items.get("workItems", []):
        if not isinstance(item, dict):
            continue
        current_id = item_id(item, scope)
        if not current_id:
            continue
        if selected_ids and current_id not in selected_ids:
            continue
        current_status = str(item.get("status") or "pending")
        if status == "pending":
            if current_status == "done":
                continue
        elif status != "all" and current_status != status:
            continue
        items.append(item)
    return items


def normalized_location(location: str, run_dir: Path, root: Path) -> str:
    normalized = location.replace("\\", "/").strip()
    run_abs = str(run_dir.resolve()).replace("\\", "/").rstrip("/") + "/"
    if normalized.startswith(run_abs):
        normalized = normalized[len(run_abs) :]
    run_rel = rel_path(run_dir, root).rstrip("/") + "/"
    if normalized.startswith(run_rel):
        normalized = normalized[len(run_rel) :]
    return normalized
