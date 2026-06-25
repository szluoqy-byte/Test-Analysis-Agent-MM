#!/usr/bin/env python3
"""Apply coverage gaps by reopening the referenced staged work items."""

from __future__ import annotations

import argparse
from datetime import datetime
import sys
from pathlib import Path
from typing import Any

from run_artifacts import dump_json, load_json


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


def normalize_location(location: str, run_dir: Path, root: Path) -> str:
    normalized = location.replace("\\", "/").strip()
    run_rel_prefix = rel_path(run_dir, root).rstrip("/") + "/"
    if normalized.startswith(run_rel_prefix):
        normalized = normalized[len(run_rel_prefix) :]
    return normalized


def expected_prefix(scope: str) -> str:
    if scope == "analysis":
        return "process/test-point-slices/"
    if scope == "design":
        return "process/test-case-slices/"
    raise ValueError("scope 必须为 analysis 或 design")


def work_items_path(run_dir: Path, scope: str) -> Path:
    if scope == "analysis":
        return run_dir / "process" / "test-point-work-items.json"
    return run_dir / "process" / "test-case-work-items.json"


def id_key(scope: str) -> str:
    return "leafScenarioId" if scope == "analysis" else "testPointId"


def default_report(run_dir: Path, scope: str) -> Path:
    return run_dir / "reports" / f"{scope}-coverage-review.json"


def infer_scope(report: dict[str, Any], report_path: Path) -> str:
    scope = str(report.get("coverageScope") or "")
    if scope in {"analysis", "design"}:
        return scope
    name = report_path.name
    if name.startswith("analysis-"):
        return "analysis"
    if name.startswith("design-"):
        return "design"
    raise ValueError("无法判断 coverage scope，请传入 --scope")


def gap_location(gap: dict[str, Any]) -> str:
    location = gap.get("artifactLocation")
    return str(location or "").strip()


def apply_gaps(run_dir: Path, root: Path, report_path: Path, scope: str) -> tuple[list[str], list[str]]:
    report = load_json(report_path)
    gaps = [gap for gap in report.get("coverageGaps", []) if isinstance(gap, dict)]
    errors: list[str] = []
    updated: list[str] = []
    if not gaps:
        return errors, updated
    prefix = expected_prefix(scope)
    items_path = work_items_path(run_dir, scope)
    if not items_path.exists():
        return [f"工作项索引不存在: {rel_path(items_path, root)}"], updated
    items_data = load_json(items_path)
    by_id = {
        str(item.get(id_key(scope)) or ""): item
        for item in items_data.get("workItems", [])
        if isinstance(item, dict)
    }
    now = datetime.now().isoformat(timespec="seconds")
    for gap in gaps:
        location = normalize_location(gap_location(gap), run_dir, root)
        if not location.startswith(prefix) or not location.endswith(".json"):
            errors.append(f"{gap.get('id', 'GAP')} artifactLocation 必须指向 {prefix}<ID>.json: {location}")
            continue
        slice_path = run_dir / location
        if not slice_path.exists():
            errors.append(f"{gap.get('id', 'GAP')} 指向的切片不存在: {location}")
            continue
        item_id = Path(location).stem
        item = by_id.get(item_id)
        if not item:
            errors.append(f"{gap.get('id', 'GAP')} 未找到对应工作项: {item_id}")
            continue
        item["status"] = "in_progress"
        item["slicePath"] = location
        item["mergedAt"] = ""
        item["repairSource"] = rel_path(report_path, root)
        item.setdefault("repairReasons", [])
        item["repairReasons"].append(
            {
                "gapId": gap.get("id", ""),
                "description": gap.get("description", ""),
                "suggestedFix": gap.get("suggestedFix", ""),
                "appliedAt": now,
            }
        )
        updated.append(item_id)
    if not errors:
        dump_json(items_path, items_data)
    return errors, updated


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description="根据 coverageGaps[].artifactLocation 重开对应分片工作项")
    parser.add_argument("run_dir", type=Path, help="outputs/runs/<run-id>")
    parser.add_argument("--scope", choices=["analysis", "design"], help="coverage 范围")
    parser.add_argument("--report", type=Path, help="coverage review JSON；默认 reports/<scope>-coverage-review.json")
    args = parser.parse_args()

    root = repo_root()
    run_dir = resolve_path(args.run_dir, root)
    report_path = resolve_path(args.report, root) if args.report else None
    if report_path is None:
        if not args.scope:
            print("失败: 未传 --report 时必须传 --scope", file=sys.stderr)
            return 1
        report_path = default_report(run_dir, args.scope)
    if not report_path.exists():
        print(f"失败: coverage report 不存在: {report_path}", file=sys.stderr)
        return 1
    report = load_json(report_path)
    try:
        scope = args.scope or infer_scope(report, report_path)
        errors, updated = apply_gaps(run_dir, root, report_path, scope)
    except ValueError as exc:
        print(f"失败: {exc}", file=sys.stderr)
        return 1
    for error in errors:
        print(f"失败: {error}")
    if errors:
        return 1
    if updated:
        print("通过: 已重开工作项 " + "、".join(updated))
    else:
        print("通过: coverageGaps 为空，无需重开工作项")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
