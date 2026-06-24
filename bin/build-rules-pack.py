#!/usr/bin/env python3
"""Build process/rules-pack.json as the mandatory rules source index for a run."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


PROJECT_KEY_RE = re.compile(r"^(?=.{1,64}$)[A-Za-z0-9](?:[A-Za-z0-9 _-]*[A-Za-z0-9])?$")
ALLOWED_STAGES = {
    "*",
    "input-fact-modeling",
    "testing-method-router",
    "test-analysis-solution-generation",
    "test-analysis-solution-review",
    "test-design-solution-generation",
    "test-case-writing",
    "test-design-solution-review",
    "coverage-review",
}
PROJECT_RULES_ROOT = "rules/projects/{project_key}"
PERSONAL_RULES_ROOT = "rules/user"
PROJECT_INFERENCE_ROOTS = (
    "rules/projects",
    "knowledge/projects",
    "memory/projects",
)


class ChineseArgumentParser(argparse.ArgumentParser):
    def format_usage(self) -> str:
        return super().format_usage().replace("usage:", "用法:")

    def error(self, message: str) -> None:
        translations = {
            "the following arguments are required:": "缺少必需参数:",
            "unrecognized arguments:": "无法识别的参数:",
            "expected one argument": "缺少参数值",
        }
        for original, translated in translations.items():
            message = message.replace(original, translated)
        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog}: 参数错误: {message}\n")


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def rel_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def split_keywords(values: list[str]) -> list[str]:
    keywords: list[str] = []
    for value in values:
        for item in re.split(r"[,，]", value):
            item = item.strip()
            if item:
                keywords.append(item)
    return keywords


def normalize_match_text(value: str) -> str:
    return re.sub(r"[^0-9a-z]+", "", value.casefold())


def discover_project_keys(root: Path) -> list[str]:
    keys: set[str] = set()
    for relative_root in PROJECT_INFERENCE_ROOTS:
        projects_root = root / relative_root
        if not projects_root.is_dir():
            continue
        for path in projects_root.iterdir():
            if path.is_dir() and PROJECT_KEY_RE.fullmatch(path.name):
                keys.add(path.name)
    return sorted(keys, key=lambda value: value.casefold())


def infer_project_key(args: argparse.Namespace, root: Path) -> tuple[str, str, list[str]]:
    evidence_parts = [args.requirement_title or "", str(args.requirement or "")]
    evidence_parts.extend(split_keywords(args.keyword))
    evidence_text = normalize_match_text(" ".join(evidence_parts))
    if not evidence_text:
        return "", "未提供 project-key，且需求标题、路径和关键词不足以推断", []

    candidates: list[str] = []
    for project_key in discover_project_keys(root):
        normalized_key = normalize_match_text(project_key)
        if normalized_key and normalized_key in evidence_text:
            candidates.append(project_key)

    if len(candidates) == 1:
        return candidates[0], f"根据需求标题/路径/keywords 唯一匹配 project-key: {candidates[0]}", []
    if len(candidates) > 1:
        return "", "需求标题/路径/keywords 命中多个 project-key，未唯一绑定", candidates
    return "", "未提供 project-key，且无法从需求标题/路径/keywords 唯一识别", []


def strip_yaml_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"\"", "'", "“", "”", "‘", "’"}:
        return value[1:-1].strip()
    return value


def split_frontmatter_item(line: str) -> tuple[str, str] | None:
    half_index = line.find(":")
    full_index = line.find("：")
    indexes = [index for index in (half_index, full_index) if index >= 0]
    if not indexes:
        return None
    index = min(indexes)
    key = line[:index].strip().lstrip("\ufeff")
    value = line[index + 1 :].strip()
    if not key:
        return None
    return key, value


def parse_inline_list(value: str) -> list[str]:
    value = value.strip()
    if not (value.startswith("[") and value.endswith("]")):
        return []
    items = []
    for raw_item in value[1:-1].split(","):
        item = raw_item.strip().strip("\"'")
        if item:
            items.append(item)
    return items


def parse_frontmatter_lines(lines: list[str]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    current_key = ""
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if current_key and stripped.startswith("- "):
            values.setdefault(current_key, []).append(stripped[2:].strip().strip("\"'"))
            continue
        current_key = ""
        item = split_frontmatter_item(line)
        if item is None:
            continue
        key, value = item
        if key == "stages":
            current_key = key
            inline = parse_inline_list(value)
            values[key] = inline if inline else []
        else:
            values[key] = strip_yaml_scalar(value)
    return values


def read_markdown(path: Path) -> tuple[str, dict[str, Any], str | None]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return "", {}, f"不是有效 UTF-8: {exc}"

    lines = text.splitlines()
    if not lines or lines[0].strip().lstrip("\ufeff") != "---":
        return text, {}, None

    frontmatter: list[str] = []
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            content = "\n".join(lines[index + 1 :]).strip()
            return content, parse_frontmatter_lines(frontmatter), None
        frontmatter.append(line)
    return "", {}, "frontmatter 未闭合"


def normalize_stages(value: Any) -> tuple[list[str], str]:
    if value is None or value == "":
        return ["*"], "all"
    if isinstance(value, str):
        stages = parse_inline_list(value) or [value]
    elif isinstance(value, list):
        stages = [str(item).strip() for item in value if str(item).strip()]
    else:
        stages = []
    if not stages:
        return ["*"], "all"
    return stages, "restricted" if stages != ["*"] else "all"


def first_heading(text: str, fallback: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or fallback
    return fallback


def rule_priority(layer: str) -> int:
    return {"core": 300, "project": 200, "user": 100}.get(layer, 0)


def collect_rule(path: Path, root: Path, layer: str, warnings: list[str]) -> dict[str, Any] | None:
    relative = rel_path(path, root)
    content, meta, error = read_markdown(path)
    if error:
        warnings.append(f"{relative}: {error}")
        return None

    if layer in {"project", "user"}:
        if not meta:
            warnings.append(f"{relative}: 缺少 frontmatter，未加载为 rules-pack 规则")
            return None
        name = str(meta.get("name", "")).strip()
        description = str(meta.get("description", "")).strip()
        if not name:
            warnings.append(f"{relative}: frontmatter 缺少 name")
            return None
        if not description:
            warnings.append(f"{relative}: frontmatter 缺少 description")
            return None
    else:
        name = str(meta.get("name", "")).strip() or path.stem
        description = str(meta.get("description", "")).strip() or first_heading(content, path.stem)

    stages, availability = normalize_stages(meta.get("stages"))
    invalid_stages = [stage for stage in stages if stage not in ALLOWED_STAGES]
    if invalid_stages:
        warnings.append(f"{relative}: stages 包含不支持的阶段: {', '.join(invalid_stages)}")
        return None

    if not content.strip():
        warnings.append(f"{relative}: 规则正文为空，未加载")
        return None

    return {
        "path": relative,
        "layer": layer,
        "name": name,
        "description": description,
        "availableStages": stages,
        "availability": availability,
        "mandatory": True,
        "loadPolicy": "stage_required",
        "priority": rule_priority(layer),
        "conflictPolicy": "current_user_instruction_overrides_rules; rules_override_input_documents_memory_knowledge",
    }


def iter_markdown_sources(source_root: Path) -> list[Path]:
    if not source_root.is_dir():
        return []
    return sorted(
        path
        for path in source_root.rglob("*.md")
        if path.is_file() and path.name != "README.md"
    )


def build_rules_pack(args: argparse.Namespace, root: Path) -> dict[str, Any]:
    warnings: list[str] = []
    rule_sources: list[dict[str, Any]] = []
    unscanned_project_rules: list[dict[str, str]] = []

    for path in sorted((root / "rules").glob("*.md")):
        if path.name == "README.md":
            continue
        rule = collect_rule(path, root, "core", warnings)
        if rule:
            rule_sources.append(rule)

    explicit_project_key = (args.project or "").strip()
    project_key = explicit_project_key
    inferred_reason = ""
    ambiguous_candidates: list[str] = []
    if not project_key:
        project_key, inferred_reason, ambiguous_candidates = infer_project_key(args, root)

    if project_key and PROJECT_KEY_RE.fullmatch(project_key):
        project_binding = {
            "status": "resolved",
            "projectKey": project_key,
            "reason": args.project_reason or ("用户显式提供 project-key" if explicit_project_key else inferred_reason),
        }
        for path in iter_markdown_sources(root / PROJECT_RULES_ROOT.format(project_key=project_key)):
            rule = collect_rule(path, root, "project", warnings)
            if rule:
                rule_sources.append(rule)
    else:
        reason = args.project_reason or inferred_reason or "未提供 project-key，且无法从输入唯一识别"
        project_binding = {
            "status": "unresolved",
            "projectKey": project_key if project_key and not PROJECT_KEY_RE.fullmatch(project_key) else "",
            "reason": reason,
        }
        if explicit_project_key and not PROJECT_KEY_RE.fullmatch(explicit_project_key):
            warnings.append(f"project-key `{project_key}` 格式非法，未扫描 project rules")
        if ambiguous_candidates:
            warnings.append("project-key 候选不唯一，未扫描 project rules: " + "、".join(ambiguous_candidates))
        unscanned_project_rules.append({"path": "rules/projects/", "reason": "project-key 未唯一确定"})

    for path in iter_markdown_sources(root / PERSONAL_RULES_ROOT):
        rule = collect_rule(path, root, "user", warnings)
        if rule:
            rule_sources.append(rule)

    return {
        "artifactType": "rules-pack",
        "schemaVersion": "1.1",
        "title": args.title or "强制规则索引",
        "priorityPolicy": {
            "currentUserInstruction": "当前用户明确指令最高；只有当前用户明确指令可以覆盖 rules。",
            "runtimeContract": "AGENTS、workflow、skill、schema 和固定脚本定义执行契约；rules 不能要求违反运行时契约，除非用户明确要求修改框架。",
            "rules": "rules 是强制约束，按 core > project > user 处理，优先于输入文档、memory 和 knowledge。",
            "inputDocuments": "需求、设计方案和已评审测试分析方案是业务事实来源；与 rules 冲突时默认遵守 rules 并记录覆盖原因。",
            "memoryKnowledge": "memory 和 knowledge 只能补充风险、偏好、方法或经验；与输入文档或 rules 冲突时不得覆盖。",
        },
        "loadingPolicy": {
            "indexOnly": "rules-pack 只索引规则元数据，不内联规则正文。",
            "stageRequired": "后续阶段必须筛选 availableStages 包含当前阶段或 `*` 的 ruleSources，并读取对应 Markdown 正文后再执行。",
            "applicationRecord": "读取、应用、未应用或被当前用户指令覆盖的 rules，必须在阶段产物、review 或 coverage 中留痕。",
        },
        "projectBinding": project_binding,
        "ruleSources": rule_sources,
        "unscannedProjectRules": unscanned_project_rules,
        "warnings": warnings,
    }


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def render_markdown(run_dir: Path, root: Path) -> int:
    script = root / "bin" / "render-run-markdown.py"
    result = subprocess.run(
        [sys.executable, str(script), str(run_dir)],
        cwd=root,
        text=True,
        capture_output=True,
    )
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip(), file=sys.stderr)
    return result.returncode


def main() -> int:
    configure_stdio()
    parser = ChineseArgumentParser(description="生成 process/rules-pack.json 强制规则索引")
    parser.add_argument("--run-dir", required=True, type=Path, help="outputs/runs/<run-id>")
    parser.add_argument("--requirement", type=Path, help="需求 Markdown 路径")
    parser.add_argument("--requirement-title", default="", help="需求标题")
    parser.add_argument("--keyword", action="append", default=[], help="需求关键词，可重复或用逗号分隔")
    parser.add_argument("--project", default="", help="已唯一确定的 project-key")
    parser.add_argument("--project-reason", default="", help="project 绑定或未绑定原因")
    parser.add_argument("--title", default="", help="rules-pack 标题")
    parser.add_argument("--no-render", action="store_true", help="只写 JSON，不渲染 Markdown")
    args = parser.parse_args()

    root = repo_root()
    run_dir = args.run_dir
    if not run_dir.is_absolute():
        run_dir = root / run_dir
    run_dir.mkdir(parents=True, exist_ok=True)

    data = build_rules_pack(args, root)
    output_path = run_dir / "process" / "rules-pack.json"
    write_json(output_path, data)
    count = len(data["ruleSources"])
    print(f"通过: 已生成 {rel_path(output_path, root)}，规则索引 {count} 条，告警 {len(data['warnings'])} 个")

    if args.no_render:
        return 0
    return render_markdown(run_dir, root)


if __name__ == "__main__":
    raise SystemExit(main())
