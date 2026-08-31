#!/usr/bin/env python3
"""Manage persistent requirement runs, dependency fingerprints, revisions, and locks."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

from encoding_utils import configure_stdio


RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}
FILE_SUFFIXES = {".md", ".markdown", ".json", ".py"}
CONTEXT_ROOTS = ("rules", "knowledge")
FRAMEWORK_ROOTS = ("agents", "skills", "templates", "bin")
LOCK_TIMEOUT_HOURS = 12


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def now_text() -> str:
    return datetime.now().isoformat(timespec="seconds")


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"JSON 顶层必须是对象: {path}")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def rel_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def resolve_source(value: str, root: Path) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def validate_run_id(value: str) -> str:
    run_id = value.strip()
    if not RUN_ID_RE.fullmatch(run_id) or ".." in run_id or run_id.upper() in WINDOWS_RESERVED_NAMES:
        raise ValueError(
            "runid 必须为 1-64 位，以字母或数字开头，只包含字母、数字、点、下划线或连字符，"
            "且不能包含 '..' 或 Windows 保留名称"
        )
    return run_id


def generate_run_id(root: Path) -> str:
    result = subprocess.run(
        [sys.executable, str(root / "bin" / "generate-run-id.py")],
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise ValueError(f"generate-run-id.py 执行失败: {(result.stderr or result.stdout).strip()}")
    return result.stdout.strip()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def aggregate_hash(files: dict[str, str]) -> str:
    digest = hashlib.sha256()
    for path, value in sorted(files.items()):
        digest.update(path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(value.encode("ascii", errors="replace"))
        digest.update(b"\n")
    return digest.hexdigest()


def project_file_visible(relative: Path, project_key: str) -> bool:
    parts = relative.parts
    if "projects" not in parts:
        return True
    index = parts.index("projects")
    if len(parts) == index + 1:
        return True
    candidate = parts[index + 1]
    if candidate.lower() == "readme.md":
        return True
    return bool(project_key) and candidate.casefold() == project_key.casefold()


def iter_dependency_files(root: Path, roots: Iterable[str], project_key: str) -> Iterable[Path]:
    for relative_root in roots:
        directory = root / relative_root
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in FILE_SUFFIXES:
                continue
            if "__pycache__" in path.parts or path.name.endswith((".pyc", ".pyo")):
                continue
            relative = path.relative_to(root)
            if not project_file_visible(relative, project_key):
                continue
            yield path


def framework_file_visible(relative: str, flow: str) -> bool:
    normalized = relative.replace("\\", "/").lower()
    if flow == "analysis":
        return not any(
            marker in normalized
            for marker in (
                "test-design-agent",
                "test-design-workflow",
                "test-design-solution",
                "test-case-writing",
                "test-case-style",
            )
        )
    if flow == "design":
        return not any(
            marker in normalized
            for marker in (
                "test-analysis-agent",
                "test-analysis-workflow",
                "test-analysis-solution",
            )
        )
    return True


def dependency_group(root: Path, paths: Iterable[Path], flow: str | None = None) -> dict[str, Any]:
    files: dict[str, str] = {}
    for path in paths:
        relative = rel_path(path, root)
        if flow and not framework_file_visible(relative, flow):
            continue
        files[relative] = file_sha256(path)
    return {"hash": aggregate_hash(files), "files": files}


def normalize_existing_inputs(manifest: dict[str, Any], root: Path) -> dict[str, dict[str, Any]]:
    normalized: dict[str, dict[str, Any]] = {}
    for item in manifest.get("inputs", []):
        if not isinstance(item, dict) or not item.get("path"):
            continue
        path = resolve_source(str(item["path"]), root)
        key = os.path.normcase(str(path))
        normalized[key] = {"role": str(item.get("role") or "supplement"), "path": rel_path(path, root)}
    return normalized


def merge_inputs(args: argparse.Namespace, manifest: dict[str, Any], root: Path) -> tuple[list[dict[str, Any]], list[str]]:
    entries = normalize_existing_inputs(manifest, root)
    warnings: list[str] = []
    for role, values in (("requirement", args.requirement), ("design", args.design)):
        for value in values:
            path = resolve_source(value, root)
            if not path.is_file():
                raise ValueError(f"显式输入文件不存在: {path}")
            entries[os.path.normcase(str(path))] = {"role": role, "path": rel_path(path, root)}
    for value in args.remove_source:
        path = resolve_source(value, root)
        key = os.path.normcase(str(path))
        if key not in entries:
            warnings.append(f"待删除输入不在 manifest 中: {rel_path(path, root)}")
        entries.pop(key, None)

    result: list[dict[str, Any]] = []
    for item in sorted(entries.values(), key=lambda row: (row["role"], row["path"])):
        path = resolve_source(item["path"], root)
        result.append(
            {
                "role": item["role"],
                "path": item["path"],
                "sha256": file_sha256(path) if path.is_file() else "missing",
                "status": "available" if path.is_file() else "missing",
            }
        )
        if not path.is_file():
            warnings.append(f"历史输入文件已不存在: {item['path']}")
    return result, warnings


def compute_fingerprint(
    root: Path, flow: str, project_key: str, inputs: list[dict[str, Any]], run_dir: Path
) -> dict[str, Any]:
    input_files = {str(item["path"]): str(item.get("sha256") or "missing") for item in inputs}
    context_paths = iter_dependency_files(root, CONTEXT_ROOTS, project_key)
    framework_paths = list(iter_dependency_files(root, FRAMEWORK_ROOTS, project_key))
    agents_file = root / "AGENTS.md"
    if agents_file.is_file():
        framework_paths.append(agents_file)
    fingerprint = {
        "inputs": {"hash": aggregate_hash(input_files), "files": input_files},
        "context": dependency_group(root, context_paths, flow=flow),
        "framework": dependency_group(root, framework_paths, flow=flow),
    }
    if flow == "design":
        analysis_path = run_dir / "deliverables" / "test-analysis-solution.json"
        upstream_files = {
            rel_path(analysis_path, root): file_sha256(analysis_path) if analysis_path.is_file() else "missing"
        }
        fingerprint["upstream"] = {"hash": aggregate_hash(upstream_files), "files": upstream_files}
    return fingerprint


def compare_group(previous: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    old_files = previous.get("files", {}) if isinstance(previous, dict) else {}
    new_files = current.get("files", {}) if isinstance(current, dict) else {}
    paths = sorted(set(old_files) | set(new_files))
    changed = [path for path in paths if old_files.get(path) != new_files.get(path)]
    return {
        "changed": previous.get("hash") != current.get("hash") if previous else True,
        "files": changed,
    }


def compare_fingerprints(previous: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    return {name: compare_group(previous.get(name, {}), current[name]) for name in current}


def task_complete(run_dir: Path, flow: str) -> bool:
    deliverable = run_dir / "deliverables" / f"test-{flow}-solution.json"
    task_list = run_dir / "process" / f"{flow}-task-list.json"
    if not deliverable.is_file():
        return False
    if not task_list.is_file():
        return False
    try:
        data = read_json(task_list)
    except Exception:
        return False
    stages = data.get("stages", [])
    return bool(stages) and all(
        isinstance(stage, dict) and stage.get("status") == "done" for stage in stages
    )


def snapshot_artifact_tree(source: Path, destination: Path, exclude: set[str] | None = None) -> None:
    if not source.is_dir():
        return
    excluded = exclude or set()
    for path in source.rglob("*"):
        if not path.is_file() or path.name in excluded:
            continue
        if source.name != "inputs" and path.suffix.lower() not in {".json", ".md"}:
            continue
        target = destination / path.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)


def create_revision(
    root: Path, run_dir: Path, manifest: dict[str, Any], changes: dict[str, Any], action: str
) -> int:
    current_revision = int(manifest.get("revision") or 1)
    revision_dir = run_dir / "revisions" / f"r{current_revision:04d}"
    if revision_dir.exists():
        raise ValueError(f"revision 快照已存在，拒绝覆盖: {revision_dir}")
    revision_dir.mkdir(parents=True)
    snapshot_artifact_tree(run_dir / "deliverables", revision_dir / "deliverables")
    snapshot_artifact_tree(
        run_dir / "process",
        revision_dir / "process",
        exclude={"run.lock", "run-plan.json"},
    )
    snapshot_artifact_tree(run_dir / "reports", revision_dir / "reports")
    snapshot_artifact_tree(run_dir / "inputs", revision_dir / "inputs")
    for item in manifest.get("inputs", []):
        if not isinstance(item, dict) or item.get("status") != "available" or not item.get("path"):
            continue
        source = resolve_source(str(item["path"]), root)
        if not source.is_file():
            continue
        role = re.sub(r"[^A-Za-z0-9._-]+", "_", str(item.get("role") or "supplement"))
        digest = str(item.get("sha256") or file_sha256(source))[:12]
        target = revision_dir / "source-inputs" / role / f"{digest}-{source.name}"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    write_json(
        revision_dir / "revision-manifest.json",
        {
            "artifactType": "run-revision",
            "schemaVersion": "1.0",
            "runId": manifest.get("runId", run_dir.name),
            "revision": current_revision,
            "snapshotAt": now_text(),
            "nextAction": action,
            "changes": changes,
        },
    )
    manifest["revision"] = current_revision + 1
    return current_revision


def reset_scope(run_dir: Path, flow: str) -> None:
    paths: list[Path] = []
    if flow == "analysis":
        paths.extend(
            [
                run_dir / "deliverables" / "test-analysis-solution.json",
                run_dir / "deliverables" / "test-analysis-solution.md",
                run_dir / "process" / "scenario-tree.md",
                run_dir / "process" / "input-fact-model.md",
                run_dir / "process" / "testing-method-routing.md",
                run_dir / "process" / "test-point-work-items.json",
                run_dir / "process" / "test-point-slices",
                run_dir / "process" / "analysis-fact-coverage-map.md",
                run_dir / "process" / "reviews" / "scenario-tree-review.md",
                run_dir / "process" / "reviews" / "test-point-reviews",
                run_dir / "process" / "reviews" / "test-analysis-solution-review.md",
                run_dir / "process" / "reviews" / "analysis-coverage-review.md",
                run_dir / "reports" / "analysis-final-report.md",
            ]
        )
        reset_scope(run_dir, "design")
    else:
        paths.extend(
            [
                run_dir / "deliverables" / "test-design-solution.json",
                run_dir / "deliverables" / "test-design-solution.md",
                run_dir / "process" / "test-case-work-items.json",
                run_dir / "process" / "test-case-slices",
                run_dir / "process" / "design-fact-coverage-map.md",
                run_dir / "process" / "reviews" / "test-case-reviews",
                run_dir / "process" / "reviews" / "test-design-solution-review.md",
                run_dir / "process" / "reviews" / "design-coverage-review.md",
                run_dir / "reports" / "design-final-report.md",
            ]
        )
    for path in paths:
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()


def acquire_lock(run_dir: Path, flow: str, action: str) -> dict[str, Any]:
    lock_path = run_dir / "process" / "run.lock"
    if lock_path.exists():
        try:
            existing = read_json(lock_path)
            created_at = datetime.fromisoformat(str(existing.get("createdAt")))
        except Exception:
            created_at = datetime.now()
            existing = {"owner": "unknown"}
        if datetime.now() - created_at < timedelta(hours=LOCK_TIMEOUT_HOURS):
            raise ValueError(
                f"run 正被其他任务占用: owner={existing.get('owner')}, flow={existing.get('flow')}, "
                f"createdAt={existing.get('createdAt')}"
            )
        lock_path.unlink()
    lock = {
        "artifactType": "run-lock",
        "schemaVersion": "1.0",
        "owner": str(uuid.uuid4()),
        "pid": os.getpid(),
        "flow": flow,
        "action": action,
        "createdAt": now_text(),
    }
    write_json(lock_path, lock)
    return lock


def release_lock(run_dir: Path) -> None:
    lock_path = run_dir / "process" / "run.lock"
    if lock_path.exists():
        lock_path.unlink()


def default_manifest(run_id: str, project_key: str) -> dict[str, Any]:
    timestamp = now_text()
    return {
        "artifactType": "run-manifest",
        "schemaVersion": "1.0",
        "runId": run_id,
        "projectKey": project_key,
        "revision": 1,
        "createdAt": timestamp,
        "updatedAt": timestamp,
        "inputs": [],
        "fingerprints": {},
        "lifecycle": {"analysis": "not_started", "design": "not_started"},
        "deliverableHashes": {},
    }


def prepare(args: argparse.Namespace) -> int:
    root = repo_root()
    run_id = validate_run_id(args.runid) if args.runid else generate_run_id(root)
    run_dir = root / "outputs" / "runs" / run_id
    existed = run_dir.exists()
    manifest_path = run_dir / "process" / "run-manifest.json"
    had_manifest = manifest_path.is_file()
    manifest = read_json(manifest_path) if had_manifest else default_manifest(run_id, args.project or "")

    existing_project = str(manifest.get("projectKey") or "")
    requested_project = (args.project or "").strip()
    if existing_project and requested_project and existing_project.casefold() != requested_project.casefold():
        if not args.rebind_project:
            raise ValueError(
                f"run 已绑定 project={existing_project}，拒绝改为 project={requested_project}；"
                "如确需变更请使用 --rebind-project"
            )
    project_key = requested_project or existing_project
    manifest["projectKey"] = project_key
    inputs, warnings = merge_inputs(args, manifest, root)
    current = compute_fingerprint(root, args.flow, project_key, inputs, run_dir)
    previous = manifest.get("fingerprints", {}).get(args.flow, {})
    changes = compare_fingerprints(previous, current)
    changed = any(group["changed"] for group in changes.values())
    complete = task_complete(run_dir, args.flow)
    flow_state = str(manifest.get("lifecycle", {}).get(args.flow) or "not_started")
    flow_deliverable = run_dir / "deliverables" / f"test-{args.flow}-solution.json"

    if not existed:
        action = "create"
    elif args.mode == "rebuild":
        action = "rebuild"
    elif args.mode == "extend":
        action = "extend"
    elif args.mode == "resume":
        if complete:
            raise ValueError("mode=resume 只用于未完成 run；已完成 run 请使用 mode=auto 或 mode=extend")
        action = "resume"
    elif had_manifest and flow_state == "not_started" and not flow_deliverable.exists():
        action = "create"
    elif not had_manifest:
        action = "extend"
    elif not complete:
        action = "extend" if changed and (run_dir / "deliverables").exists() else "resume"
    elif changed:
        action = "extend"
    else:
        action = "reuse"

    run_dir.mkdir(parents=True, exist_ok=True)
    for name in ("deliverables", "process", "reports", "inputs", "revisions"):
        (run_dir / name).mkdir(parents=True, exist_ok=True)

    lock: dict[str, Any] | None = None
    snapshot_revision: int | None = None
    if action != "reuse":
        lock = acquire_lock(run_dir, args.flow, action)
        if action in {"extend", "rebuild"} and existed:
            snapshot_revision = create_revision(root, run_dir, manifest, changes, action)
        if action == "rebuild":
            reset_scope(run_dir, args.flow)
        manifest.setdefault("lifecycle", {})[args.flow] = "in_progress"

    manifest["inputs"] = inputs
    manifest["updatedAt"] = now_text()
    manifest.setdefault("pendingFingerprints", {})[args.flow] = current
    write_json(manifest_path, manifest)

    plan = {
        "artifactType": "run-plan",
        "schemaVersion": "1.0",
        "runId": run_id,
        "runDir": rel_path(run_dir, root),
        "flow": args.flow,
        "mode": args.mode,
        "action": action,
        "existingRun": existed,
        "previouslyComplete": complete,
        "revision": manifest.get("revision", 1),
        "snapshotRevision": snapshot_revision,
        "changes": changes,
        "requiresImpactAnalysis": action == "extend" and any(
            changes[name]["changed"] for name in ("inputs", "context", "upstream") if name in changes
        ),
        "defaultReopen": "all" if action == "rebuild" or changes["framework"]["changed"] else "semantic",
        "warnings": warnings,
        "lockOwner": lock.get("owner") if lock else "",
        "preparedAt": now_text(),
    }
    write_json(run_dir / "process" / "run-plan.json", plan)
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    return 0


def finalize(args: argparse.Namespace) -> int:
    root = repo_root()
    run_dir = resolve_source(str(args.run_dir), root)
    manifest_path = run_dir / "process" / "run-manifest.json"
    if not manifest_path.is_file():
        raise ValueError(f"run manifest 不存在: {manifest_path}")
    manifest = read_json(manifest_path)
    deliverable = run_dir / "deliverables" / f"test-{args.flow}-solution.json"
    if not deliverable.is_file():
        raise ValueError(f"无法完成 run，主交付 JSON 不存在: {deliverable}")
    inputs = manifest.get("inputs", [])
    current = compute_fingerprint(root, args.flow, str(manifest.get("projectKey") or ""), inputs, run_dir)
    manifest.setdefault("fingerprints", {})[args.flow] = current
    manifest.setdefault("pendingFingerprints", {}).pop(args.flow, None)
    manifest.setdefault("lifecycle", {})[args.flow] = "complete"
    digest = file_sha256(deliverable)
    manifest.setdefault("deliverableHashes", {})[args.flow] = digest
    if args.flow == "analysis":
        previous_source = str(manifest.get("designSourceAnalysisHash") or "")
        if previous_source and previous_source != digest:
            manifest["lifecycle"]["design"] = "stale"
    else:
        analysis = run_dir / "deliverables" / "test-analysis-solution.json"
        manifest["designSourceAnalysisHash"] = file_sha256(analysis) if analysis.is_file() else ""
    manifest["updatedAt"] = now_text()
    write_json(manifest_path, manifest)
    plan_path = run_dir / "process" / "run-plan.json"
    if plan_path.is_file():
        plan = read_json(plan_path)
        plan["status"] = "finalized"
        plan["finalizedAt"] = now_text()
        write_json(plan_path, plan)
    release_lock(run_dir)
    print(f"通过: 已完成 {args.flow} run {rel_path(run_dir, root)}")
    return 0


def abort(args: argparse.Namespace) -> int:
    root = repo_root()
    run_dir = resolve_source(str(args.run_dir), root)
    release_lock(run_dir)
    manifest_path = run_dir / "process" / "run-manifest.json"
    if manifest_path.is_file():
        manifest = read_json(manifest_path)
        manifest.setdefault("lifecycle", {})[args.flow] = "interrupted"
        manifest["updatedAt"] = now_text()
        write_json(manifest_path, manifest)
    plan_path = run_dir / "process" / "run-plan.json"
    if plan_path.is_file():
        plan = read_json(plan_path)
        plan["status"] = "aborted"
        plan["abortedAt"] = now_text()
        write_json(plan_path, plan)
    print(f"通过: 已释放 run lock {rel_path(run_dir, root)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare_parser = subparsers.add_parser("prepare", help="解析或创建持久 run 并生成增量计划")
    prepare_parser.add_argument("--flow", required=True, choices=["analysis", "design"])
    prepare_parser.add_argument("--runid", default="", help="可选稳定需求 run ID，例如 IR-2026-001")
    prepare_parser.add_argument("--mode", default="auto", choices=["auto", "resume", "extend", "rebuild"])
    prepare_parser.add_argument("--project", default="")
    prepare_parser.add_argument("--rebind-project", action="store_true")
    prepare_parser.add_argument("--requirement", action="append", default=[])
    prepare_parser.add_argument("--design", action="append", default=[])
    prepare_parser.add_argument("--remove-source", action="append", default=[])
    prepare_parser.set_defaults(handler=prepare)

    for name, handler in (("finalize", finalize), ("abort", abort)):
        command_parser = subparsers.add_parser(name)
        command_parser.add_argument("run_dir", type=Path)
        command_parser.add_argument("--flow", choices=["analysis", "design"], default="analysis")
        command_parser.set_defaults(handler=handler)
    return parser


def main() -> int:
    configure_stdio()
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.handler(args))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"失败: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
