#!/usr/bin/env python3
"""Build process/context-pack.json from project/personal source metadata."""

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
    "test-design-solution-review",
    "coverage-review",
}
PROJECT_ROOT_PATTERNS = (
    "rules/projects/{project_key}",
    "knowledge/projects/{project_key}",
    "memory/projects/{project_key}",
)
PROJECT_UNSCANNED_ROOTS = (
    "rules/projects/",
    "knowledge/projects/",
    "memory/projects/",
)
PERSONAL_ROOTS = (
    "rules/user",
    "knowledge/user",
    "memory/user",
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
    return Path(__file__).resolve().parents[3]


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
    for pattern in PROJECT_ROOT_PATTERNS:
        projects_root = root / pattern.split("/{project_key}", 1)[0]
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
        if not normalized_key:
            continue
        if normalized_key in evidence_text:
            candidates.append(project_key)

    if len(candidates) == 1:
        return candidates[0], f"根据需求标题/路径/keywords 唯一匹配 project-key: {candidates[0]}", []
    if len(candidates) > 1:
        return "", "需求标题/路径/keywords 命中多个 project-key，未唯一绑定", candidates
    return "", "未提供 project-key，且无法从需求标题/路径/keywords 唯一识别", []


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


def read_frontmatter(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return None, f"不是有效 UTF-8: {exc}"

    lines = text.splitlines()
    if not lines or lines[0].strip().lstrip("\ufeff") != "---":
        return None, "缺少 frontmatter"

    frontmatter: list[str] = []
    for line in lines[1:]:
        if line.strip() == "---":
            return parse_frontmatter_lines(frontmatter), None
        frontmatter.append(line)
    return None, "frontmatter 未闭合"


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


def collect_source(path: Path, root: Path, warnings: list[str]) -> dict[str, Any] | None:
    meta, error = read_frontmatter(path)
    relative = rel_path(path, root)
    if error:
        warnings.append(f"{relative}: {error}")
        return None
    if meta is None:
        warnings.append(f"{relative}: frontmatter 解析失败")
        return None

    name = str(meta.get("name", "")).strip()
    description = str(meta.get("description", "")).strip()
    if not name:
        warnings.append(f"{relative}: frontmatter 缺少 name")
        return None
    if not description:
        warnings.append(f"{relative}: frontmatter 缺少 description")
        return None

    stages, availability = normalize_stages(meta.get("stages"))
    invalid_stages = [stage for stage in stages if stage not in ALLOWED_STAGES]
    if invalid_stages:
        warnings.append(f"{relative}: stages 包含不支持的阶段: {', '.join(invalid_stages)}")
        return None

    return {
        "path": relative,
        "name": name,
        "description": description,
        "availableStages": stages,
        "availability": availability,
    }


def iter_markdown_sources(source_root: Path) -> list[Path]:
    if not source_root.is_dir():
        return []
    return sorted(
        path
        for path in source_root.rglob("*.md")
        if path.is_file() and path.name != "README.md"
    )


def build_index(args: argparse.Namespace, root: Path) -> dict[str, Any]:
    warnings: list[str] = []
    sources: list[dict[str, Any]] = []
    unscanned_project_sources: list[dict[str, str]] = []

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
        for pattern in PROJECT_ROOT_PATTERNS:
            for path in iter_markdown_sources(root / pattern.format(project_key=project_key)):
                source = collect_source(path, root, warnings)
                if source:
                    sources.append(source)
    else:
        reason = args.project_reason or inferred_reason or "未提供 project-key，且无法从输入唯一识别"
        project_binding = {
            "status": "unresolved",
            "projectKey": project_key if project_key and not PROJECT_KEY_RE.fullmatch(project_key) else "",
            "reason": reason,
        }
        if explicit_project_key and not PROJECT_KEY_RE.fullmatch(explicit_project_key):
            warnings.append(f"project-key `{project_key}` 格式非法，未扫描 project 目录")
        if ambiguous_candidates:
            warnings.append("project-key 候选不唯一，未扫描 project 目录: " + "、".join(ambiguous_candidates))
        unscanned_project_sources = [
            {"path": path, "reason": "project-key 未唯一确定"}
            for path in PROJECT_UNSCANNED_ROOTS
        ]

    personal_key = (args.personal or "default").strip() or "default"
    personal_binding = {
        "status": "default" if personal_key == "default" else "resolved",
        "personalKey": personal_key,
        "reason": args.personal_reason or ("使用默认 personal 扩展路径" if personal_key == "default" else "用户显式提供 personal-key"),
    }
    for relative_root in PERSONAL_ROOTS:
        for path in iter_markdown_sources(root / relative_root):
            source = collect_source(path, root, warnings)
            if source:
                sources.append(source)

    requirement_path = ""
    if args.requirement:
        requirement_path = rel_path(Path(args.requirement), root)

    return {
        "artifactType": "context-pack",
        "schemaVersion": "1.0",
        "title": args.title or "上下文来源索引",
        "requirement": {
            "path": requirement_path,
            "title": args.requirement_title or "",
            "keywords": split_keywords(args.keyword),
        },
        "projectBinding": project_binding,
        "personalBinding": personal_binding,
        "sources": sources,
        "unscannedProjectSources": unscanned_project_sources,
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
    parser = ChineseArgumentParser(description="生成 process/context-pack.json 动态来源索引")
    parser.add_argument("--run-dir", required=True, type=Path, help="outputs/runs/<run-id>")
    parser.add_argument("--requirement", type=Path, help="需求 Markdown 路径")
    parser.add_argument("--requirement-title", default="", help="需求标题")
    parser.add_argument("--keyword", action="append", default=[], help="需求关键词，可重复或用逗号分隔")
    parser.add_argument("--project", default="", help="已唯一确定的 project-key")
    parser.add_argument("--project-reason", default="", help="project 绑定或未绑定原因")
    parser.add_argument("--personal", default="default", help="personal-key，默认 default")
    parser.add_argument("--personal-reason", default="", help="personal 绑定原因")
    parser.add_argument("--title", default="", help="context-pack 标题")
    parser.add_argument("--no-render", action="store_true", help="只写 JSON，不渲染 Markdown")
    args = parser.parse_args()

    root = repo_root()
    run_dir = args.run_dir
    if not run_dir.is_absolute():
        run_dir = root / run_dir
    run_dir.mkdir(parents=True, exist_ok=True)

    data = build_index(args, root)
    output_path = run_dir / "process" / "context-pack.json"
    write_json(output_path, data)
    print(f"通过: 已生成 {rel_path(output_path, root)}，动态来源 {len(data['sources'])} 个，告警 {len(data['warnings'])} 个")

    if args.no_render:
        return 0
    return render_markdown(run_dir, root)


if __name__ == "__main__":
    raise SystemExit(main())
