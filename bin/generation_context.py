"""Build deterministic generation context for staged run artifacts."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from run_artifacts import dump_json, load_json


REVIEW_TYPES = {
    "scenario-tree-review",
    "test-point-review",
    "test-case-review",
    "test-analysis-solution-review",
    "test-design-solution-review",
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


def stage_for_kind(kind: str, review_type: str = "") -> str:
    if kind in {"scenario-tree", "test-point"}:
        return "test-analysis-solution-generation"
    if kind == "test-case":
        return "test-design-solution-generation"
    if kind == "review":
        return review_type
    if kind == "coverage":
        return "coverage-review"
    raise ValueError(f"不支持的 generation context kind: {kind}")


def target_type_for_kind(kind: str, review_type: str = "") -> str:
    if kind == "scenario-tree":
        return "scenario-tree"
    if kind == "test-point":
        return "test-point-slice"
    if kind == "test-case":
        return "test-case-slice"
    if kind == "review":
        return review_type
    if kind == "coverage":
        return "coverage-review"
    raise ValueError(f"不支持的 generation context kind: {kind}")


def is_stage_visible(stages: Any, stage: str) -> bool:
    return isinstance(stages, list) and ("*" in stages or stage in stages)


def read_text_file(root: Path, relative: str) -> str:
    path = root / relative
    if not path.exists() or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def applicable_rules(run_dir: Path, root: Path, stage: str) -> list[dict[str, Any]]:
    path = run_dir / "process" / "rules-pack.json"
    if not path.exists():
        return []
    data = load_json(path)
    rules: list[dict[str, Any]] = []
    for rule in data.get("ruleSources", []):
        if not isinstance(rule, dict) or not is_stage_visible(rule.get("availableStages"), stage):
            continue
        source = str(rule.get("path") or "")
        rules.append(
            {
                "path": source,
                "layer": rule.get("layer", ""),
                "name": rule.get("name", ""),
                "description": rule.get("description", ""),
                "mandatory": rule.get("mandatory", True),
                "content": read_text_file(root, source),
            }
        )
    return rules


def visible_sources(run_dir: Path, stage: str) -> list[dict[str, Any]]:
    path = run_dir / "process" / "context-pack.json"
    if not path.exists():
        return []
    data = load_json(path)
    sources: list[dict[str, Any]] = []
    for source in data.get("sources", []):
        if not isinstance(source, dict) or not is_stage_visible(source.get("availableStages"), stage):
            continue
        sources.append(
            {
                "path": source.get("path", ""),
                "name": source.get("name", ""),
                "description": source.get("description", ""),
                "availableStages": source.get("availableStages", []),
            }
        )
    return sources


def strings_from_value(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            result.extend(strings_from_value(item))
        return result
    if isinstance(value, dict):
        result = []
        for item in value.values():
            result.extend(strings_from_value(item))
        return result
    return [str(value)] if value not in (None, "") else []


def fact_rows(input_fact_model: dict[str, Any]) -> list[dict[str, Any]]:
    facts: list[dict[str, Any]] = []
    for section in input_fact_model.get("sections", []):
        if not isinstance(section, dict):
            continue
        for content in section.get("content", []):
            if not isinstance(content, dict) or content.get("type") != "table":
                continue
            columns = [str(column) for column in content.get("columns", [])]
            if "事实ID" not in columns:
                continue
            for row in content.get("rows", []):
                if not isinstance(row, list):
                    continue
                item = {columns[index]: row[index] for index in range(min(len(columns), len(row)))}
                if str(item.get("事实ID", "")).startswith("FACT-"):
                    facts.append(item)
    return facts


def target_terms(target: dict[str, Any]) -> list[str]:
    raw = " ".join(strings_from_value(target))
    terms = re.split(r"[\s,，。；;:：/|\\()（）\[\]【】{}<>《》、-]+", raw)
    return [term for term in terms if len(term) >= 2 and not re.fullmatch(r"(SC|TP|TC)?\d+", term)]


def relevant_facts(run_dir: Path, target: dict[str, Any], include_all: bool = False) -> list[dict[str, Any]]:
    path = run_dir / "process" / "input-fact-model.json"
    if not path.exists():
        return []
    facts = fact_rows(load_json(path))
    if include_all:
        return facts[:80]
    terms = target_terms(target)
    if not terms:
        return facts[:20]
    matched: list[dict[str, Any]] = []
    for fact in facts:
        text = " ".join(strings_from_value(fact))
        if any(term in text for term in terms):
            matched.append(fact)
    return (matched or facts)[:20]


def default_constraints(kind: str) -> list[str]:
    if kind == "scenario-tree":
        return [
            "只生成 scope[] 和 scenarios[]。",
            "SC 最多 3 层，任何 SC 节点不得包含 testPoints/testCases/steps/testData/expectedResult。",
            "场景树通过 review 后冻结，后续 TP 阶段不得改写 SC。",
        ]
    if kind == "test-point":
        return [
            "只填写当前叶子 SC 的 scenario.testPoints[]。",
            "不得新增、删除、合并或改写 SC。",
            "每个叶子 SC 必须包含一个标题为 E2E场景测试 的 TP。",
            "TP 是验证目标，不输出 TC、步骤、测试数据或预期结果。",
        ]
    if kind == "test-case":
        return [
            "只填写当前 TP 的 testPoint.testCases[]。",
            "不得新增、删除、合并或改写 SC/TP。",
            "填写 TC 前先识别当前 TP 的测试设计因子，并生成覆盖适用因子的最小充分 TC 集合。",
            "每个 TP 至少 1 个 TC 只是最低门槛；只有输入依据确实只支持一个独立测试实例时，才允许该 TP 下只有 1 个 TC。",
            "一个 TC 只覆盖一个可独立执行、独立判定的测试实例。",
            "steps[].action 只写可执行动作或取数动作，检查项写入同一步 expected。",
        ]
    if kind == "review":
        return [
            "只做语义评审，不重复 deterministic lint 已覆盖的结构校验。",
            "发现必须修复的问题时，location 指向 canonical JSON 或对应 slice。",
        ]
    if kind == "coverage":
        return [
            "coverageGaps[].artifactLocation 必须指向可编辑 slice，不得指向 Markdown 或最终 deliverable。",
            "coverage 只输出最终覆盖缺口和收口意见，不创建澄清流程。",
        ]
    return []


def default_read_plan(kind: str, stage: str) -> list[str]:
    common = [
        f"读取 generationContext.applicableRules[] 中已内联的 {stage} 适用 rules 正文并遵守。",
        "按需读取 generationContext.visibleSources[] 指向的 project/personal 动态来源正文，并记录应用状态。",
    ]
    if kind == "scenario-tree":
        return common + ["读取 process/input-fact-model.json 的事实清单，生成冻结 SC 树。"]
    if kind == "test-point":
        return common + ["读取当前 test-point-slice 的 scenarioPath 与 relevantFacts[]，只生成当前叶子 SC 的 TP。"]
    if kind == "test-case":
        return common + ["读取当前 test-case-slice 的 scenarioPath、testPoint 与 relevantFacts[]，只生成当前 TP 的 TC。"]
    if kind == "review":
        return common + ["读取 targetArtifact 指向的 canonical JSON，输出语义评审结论。"]
    if kind == "coverage":
        return common + ["读取主交付件、work items、slice 与 review 结果，输出覆盖收口结论。"]
    return common


def load_target(target_path: Path) -> dict[str, Any]:
    return load_json(target_path) if target_path.exists() else {}


def target_from_artifact(kind: str, data: dict[str, Any], target_id: str) -> dict[str, Any]:
    if kind == "scenario-tree":
        return {"id": target_id or "scenario-tree", "title": data.get("title", "冻结 SC 场景树")}
    if kind == "test-point":
        return {
            "id": target_id or data.get("leafScenarioId", ""),
            "scenarioPath": data.get("scenarioPath", []),
            "scenario": data.get("scenario", {}),
        }
    if kind == "test-case":
        point = data.get("testPoint", {})
        return {
            "id": target_id or point.get("id", ""),
            "scenarioPath": data.get("scenarioPath", []),
            "leafScenarioId": data.get("leafScenarioId", ""),
            "testPoint": point,
        }
    return {"id": target_id, "title": data.get("title", "")}


def build_generation_context(
    run_dir: Path,
    kind: str,
    target_path: Path,
    *,
    target_id: str = "",
    review_type: str = "",
    coverage_scope: str = "",
) -> dict[str, Any]:
    root = repo_root()
    stage = stage_for_kind(kind, review_type)
    target_type = target_type_for_kind(kind, review_type)
    target_data = load_target(target_path)
    target = target_from_artifact(kind, target_data, target_id)
    input_artifacts = [
        "process/rules-pack.json",
        "process/context-pack.json",
    ]
    if (run_dir / "process" / "input-fact-model.json").exists():
        input_artifacts.append("process/input-fact-model.json")
    if kind == "test-case":
        input_artifacts.append("deliverables/test-analysis-solution.json")
    if kind in {"review", "coverage"}:
        input_artifacts.append(rel_path(target_path, root))

    return {
        "stage": stage,
        "targetType": target_type,
        "targetId": target.get("id") or target_id or target_type,
        "coverageScope": coverage_scope,
        "inputArtifacts": input_artifacts,
        "applicableRules": applicable_rules(run_dir, root, stage),
        "visibleSources": visible_sources(run_dir, stage),
        "relevantFacts": relevant_facts(run_dir, target, include_all=(kind == "scenario-tree")),
        "constraints": default_constraints(kind),
        "readPlan": default_read_plan(kind, stage),
    }


def attach_generation_context(
    path: Path,
    context: dict[str, Any],
) -> dict[str, Any]:
    data = load_json(path) if path.exists() else {}
    data["generationContext"] = context
    dump_json(path, data)
    return data
