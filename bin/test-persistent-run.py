#!/usr/bin/env python3
"""Regression checks for persistent run lifecycle and stable IDs."""

from __future__ import annotations

import json
import copy
import shutil
import subprocess
import sys
import os
from pathlib import Path

from encoding_utils import configure_stdio, subprocess_text_kwargs, utf8_env
from run_artifacts import validate_artifact
from stable_ids import assign_stable_ids


def root_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def run(command: list[str], root: Path, expect: int = 0) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=root,
        env=utf8_env(),
        capture_output=True,
        **subprocess_text_kwargs(),
    )
    if result.returncode != expect:
        raise AssertionError(
            f"command returned {result.returncode}, expected {expect}: {' '.join(command)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def all_points(nodes: list[dict]) -> list[dict]:
    result: list[dict] = []
    for scenario in nodes:
        children = scenario.get("children")
        if isinstance(children, list) and children:
            result.extend(all_points(children))
        else:
            result.extend(point for point in scenario.get("testPoints", []) if isinstance(point, dict))
    return result


def all_cases(nodes: list[dict]) -> list[dict]:
    return [case for point in all_points(nodes) for case in point.get("testCases", []) if isinstance(case, dict)]


def main() -> int:
    configure_stdio()
    root = root_dir()
    run_id = f"IR-PERSISTENT-RUN-TEST-{os.getpid()}"
    run_dir = root / "outputs" / "runs" / run_id
    fixture = root / "examples" / "outputs" / "runs" / "sample-requirement-run"
    if run_dir.exists():
        shutil.rmtree(run_dir)
    shutil.copytree(fixture, run_dir)

    try:
        prepare = run(
            [
                sys.executable,
                "bin/manage-run.py",
                "prepare",
                "--flow",
                "analysis",
                "--runid",
                run_id,
                "--project",
                "MobileMoney",
                "--requirement",
                "examples/requirements/sample-requirement.md",
            ],
            root,
        )
        plan = json.loads(prepare.stdout)
        assert plan["action"] == "extend"
        assert plan["snapshotRevision"] == 1
        assert (run_dir / "revisions" / "r0001" / "revision-manifest.json").is_file()
        assert (run_dir / "process" / "run.lock").is_file()

        run([sys.executable, "bin/manage-run.py", "finalize", str(run_dir), "--flow", "analysis"], root)
        manifest = load(run_dir / "process" / "run-manifest.json")
        assert manifest["lifecycle"]["analysis"] == "complete"
        assert manifest["projectKey"] == "MobileMoney"

        reuse = run(
            [
                sys.executable,
                "bin/manage-run.py",
                "prepare",
                "--flow",
                "analysis",
                "--runid",
                run_id,
            ],
            root,
        )
        assert json.loads(reuse.stdout)["action"] == "reuse"
        assert not (run_dir / "process" / "run.lock").exists()

        extend = run(
            [
                sys.executable,
                "bin/manage-run.py",
                "prepare",
                "--flow",
                "analysis",
                "--runid",
                run_id,
                "--design",
                "examples/requirements/complex-promotion-requirement.md",
            ],
            root,
        )
        extend_plan = json.loads(extend.stdout)
        assert extend_plan["action"] == "extend"
        assert extend_plan["changes"]["inputs"]["changed"] is True
        assert (run_dir / "revisions" / "r0002" / "revision-manifest.json").is_file()

        run(
            [sys.executable, "bin/manage-run.py", "prepare", "--flow", "analysis", "--runid", run_id],
            root,
            expect=1,
        )
        run([sys.executable, "bin/manage-run.py", "abort", str(run_dir), "--flow", "analysis"], root)

        conflict = run(
            [
                sys.executable,
                "bin/manage-run.py",
                "prepare",
                "--flow",
                "analysis",
                "--runid",
                run_id,
                "--project",
                "OtherProject",
            ],
            root,
            expect=1,
        )
        assert "已绑定 project=MobileMoney" in conflict.stderr

        previous = [
            {"id": "TP-001", "title": "A", "objective": "A", "basisRefs": []},
            {"id": "TP-002", "title": "B", "objective": "B", "basisRefs": []},
        ]
        registry_test_dir = run_dir / "registry-test"
        assigned = assign_stable_ids(
            registry_test_dir,
            "TP",
            [
                {"id": "TP-001", "title": "A changed", "objective": "A", "basisRefs": []},
                {"title": "C", "objective": "C", "basisRefs": []},
            ],
            previous,
            previous,
        )
        assert [item["id"] for item in assigned] == ["TP-001", "TP-003"]
        registry = load(registry_test_dir / "process" / "id-registry.json")
        assert "TP-002" in registry["retiredIds"]["TP"]

        analysis_path = run_dir / "deliverables" / "test-analysis-solution.json"
        analysis_before = load(analysis_path)
        existing_tp_ids = [point["id"] for point in all_points(analysis_before["scenarios"])]
        tp_slice_path = run_dir / "process" / "test-point-slices" / "SC-001-001.json"
        tp_slice = load(tp_slice_path)
        tp_slice["scenario"]["testPoints"].append(
            {"title": "增量补充测试点", "objective": "验证新增需求事实。", "basisRefs": []}
        )
        tp_slice_path.write_text(json.dumps(tp_slice, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        run(
            [
                sys.executable,
                "skills/test-analysis-solution-generation/scripts/merge-test-point-slice.py",
                str(run_dir),
                "--slice",
                str(tp_slice_path),
            ],
            root,
        )
        analysis_after = load(analysis_path)
        merged_tp_ids = [point["id"] for point in all_points(analysis_after["scenarios"])]
        assert merged_tp_ids[: len(existing_tp_ids)] != []
        assert all(item_id in merged_tp_ids for item_id in existing_tp_ids), (existing_tp_ids, merged_tp_ids)
        new_tp_id = next(item_id for item_id in merged_tp_ids if item_id not in existing_tp_ids)
        assert int(new_tp_id.split("-")[1]) > max(int(value.split("-")[1]) for value in existing_tp_ids)

        design_path = run_dir / "deliverables" / "test-design-solution.json"
        design_before = load(design_path)
        existing_tc_ids = [case["id"] for case in all_cases(design_before["scenarios"])]
        tc_slice_path = run_dir / "process" / "test-case-slices" / "TP-001.json"
        tc_slice = load(tc_slice_path)
        new_case = copy.deepcopy(tc_slice["testPoint"]["testCases"][0])
        new_case.pop("id", None)
        new_case["title"] = "增量补充测试用例"
        tc_slice["testPoint"]["testCases"].append(new_case)
        tc_slice_path.write_text(json.dumps(tc_slice, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        run(
            [
                sys.executable,
                "skills/test-design-solution-generation/scripts/merge-test-case-slice.py",
                str(run_dir),
                "--slice",
                str(tc_slice_path),
            ],
            root,
        )
        design_after = load(design_path)
        merged_tc_ids = [case["id"] for case in all_cases(design_after["scenarios"])]
        assert all(item_id in merged_tc_ids for item_id in existing_tc_ids)
        new_tc_id = next(item_id for item_id in merged_tc_ids if item_id not in existing_tc_ids)
        assert int(new_tc_id.split("-")[1]) > max(int(value.split("-")[1]) for value in existing_tc_ids)

        stable_analysis = load(fixture / "deliverables" / "test-analysis-solution.json")
        stable_analysis["scenarios"][0]["children"][0]["testPoints"][0]["id"] = "TP-099"
        errors, _warnings = validate_artifact(stable_analysis)
        assert not errors, errors
        stable_design = load(fixture / "deliverables" / "test-design-solution.json")
        stable_design["scenarios"][0]["children"][0]["testPoints"][0]["testCases"][0]["id"] = "TC-099"
        errors, _warnings = validate_artifact(stable_design)
        assert not errors, errors

        run(
            [
                sys.executable,
                "skills/test-design-solution-generation/scripts/extract-test-case-work-items.py",
                str(run_dir),
            ],
            root,
        )
        work_items_path = run_dir / "process" / "test-case-work-items.json"
        initial_items = load(work_items_path)
        assert all(item.get("contentHash") for item in initial_items["workItems"])

        analysis = load(analysis_path)
        first_leaf = analysis["scenarios"][0]["children"][0]
        first_leaf["testPoints"][0]["objective"] += "（更新）"
        analysis_path.write_text(json.dumps(analysis, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        run(
            [
                sys.executable,
                "skills/test-design-solution-generation/scripts/extract-test-case-work-items.py",
                str(run_dir),
            ],
            root,
        )
        changed_items = load(work_items_path)
        changed = next(item for item in changed_items["workItems"] if item["testPointId"] == "TP-001")
        assert changed["status"] == "pending"
        assert changed["contentChanged"] is True

        invalid = run(
            [
                sys.executable,
                "bin/manage-run.py",
                "prepare",
                "--flow",
                "analysis",
                "--runid",
                "../bad",
            ],
            root,
            expect=1,
        )
        assert "runid 必须" in invalid.stderr
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)

    print("Persistent run regression passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
