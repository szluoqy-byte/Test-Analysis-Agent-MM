"""Helpers for Markdown-first semantic process artifacts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


SC_HEADING_RE = re.compile(r"^(#{3,5})\s+(SC-\d{3}(?:-\d{3}){0,2})\s+(.+?)\s*$")
FACT_ID_RE = re.compile(r"\bFACT-\d{3}\b")
TP_ID_RE = re.compile(r"\bTP-\d{3}\b")
TC_ID_RE = re.compile(r"\bTC-\d{3}\b")
REVIEW_RESULT_RE = re.compile(r"^-\s*结论[：:]\s*(通过|需修正|失败|警告|不适用)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class ScenarioHeading:
    scenario_id: str
    title: str
    depth: int
    line_no: int
    body: str


def read_markdown(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_markdown(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def parse_scenario_headings(text: str) -> list[ScenarioHeading]:
    lines = text.splitlines()
    raw: list[tuple[str, str, int, int]] = []
    for line_no, line in enumerate(lines, start=1):
        match = SC_HEADING_RE.match(line)
        if match:
            raw.append((match.group(2), match.group(3).strip(), len(match.group(1)) - 2, line_no))
    result: list[ScenarioHeading] = []
    for index, (scenario_id, title, depth, line_no) in enumerate(raw):
        end = raw[index + 1][3] - 1 if index + 1 < len(raw) else len(lines)
        body = "\n".join(lines[line_no:end]).strip()
        result.append(ScenarioHeading(scenario_id, title, depth, line_no, body))
    return result


def validate_scenario_tree(path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    text = read_markdown(path)
    headings = parse_scenario_headings(text)
    if not headings:
        return ["场景树没有 `### SC-*` 场景标题"], warnings

    seen: set[str] = set()
    sibling_counts: dict[str, int] = {}
    known: set[str] = set()
    for heading in headings:
        scenario_id = heading.scenario_id
        if scenario_id in seen:
            errors.append(f"第 {heading.line_no} 行场景编号重复: {scenario_id}")
            continue
        seen.add(scenario_id)
        segments = scenario_id.split("-")[1:]
        expected_depth = len(segments)
        if heading.depth != expected_depth:
            errors.append(
                f"第 {heading.line_no} 行 {scenario_id} 标题层级应为 {'#' * (expected_depth + 2)}，实际深度为 {heading.depth}"
            )
        parent = "SC" if expected_depth == 1 else "SC-" + "-".join(segments[:-1])
        if expected_depth > 1 and parent not in known:
            errors.append(f"第 {heading.line_no} 行 {scenario_id} 的父场景 {parent} 尚未定义")
        sibling_counts[parent] = sibling_counts.get(parent, 0) + 1
        expected_id = f"{parent}-{sibling_counts[parent]:03d}"
        if scenario_id != expected_id:
            errors.append(f"第 {heading.line_no} 行场景序号应为 {expected_id}，实际为 {scenario_id}")
        known.add(scenario_id)

    prefixes = {"-".join(item.scenario_id.split("-")[:-1]) for item in headings if item.depth > 1}
    leaf_ids = [item.scenario_id for item in headings if item.scenario_id not in prefixes]
    if not leaf_ids:
        warnings.append("场景树没有可识别的叶子场景")
    return errors, warnings


def leaf_scenarios(path: Path) -> list[ScenarioHeading]:
    headings = parse_scenario_headings(read_markdown(path))
    parents = {"-".join(item.scenario_id.split("-")[:-1]) for item in headings if item.depth > 1}
    return [item for item in headings if item.scenario_id not in parents]


def review_result(path: Path) -> str:
    match = REVIEW_RESULT_RE.search(read_markdown(path))
    return match.group(1) if match else ""


def require_markdown(path: Path, *, minimum_chars: int = 20) -> list[str]:
    if not path.is_file():
        return [f"缺少 Markdown 过程件: {path}"]
    text = read_markdown(path).strip()
    if len(text) < minimum_chars:
        return [f"Markdown 过程件内容过少: {path}"]
    return []


def ids_in_markdown(path: Path, kind: str) -> list[str]:
    pattern = {"FACT": FACT_ID_RE, "TP": TP_ID_RE, "TC": TC_ID_RE}[kind]
    return list(dict.fromkeys(pattern.findall(read_markdown(path))))
