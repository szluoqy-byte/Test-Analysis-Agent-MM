#!/usr/bin/env python3
"""Utilities for generated deliverable Markdown files."""

from __future__ import annotations

import re
from pathlib import Path


PLACEHOLDER_RE = re.compile(r"<([^<>\n]{1,120})>")


def normalize_angle_brackets(path: Path) -> bool:
    """Replace placeholder angle brackets with braces in generated Markdown deliverables."""
    if path.suffix.lower() != ".md" or not path.exists():
        return False

    text = path.read_text(encoding="utf-8-sig")

    def replace_placeholder(match: re.Match[str]) -> str:
        content = match.group(1)
        if content.lower() in {"br", "br/"}:
            return match.group(0)
        return "{" + content + "}"

    normalized = PLACEHOLDER_RE.sub(replace_placeholder, text)
    if normalized == text:
        return False

    path.write_text(normalized, encoding="utf-8")
    return True


def normalize_deliverable_markdown_files(deliverables_dir: Path) -> list[Path]:
    """Normalize all Markdown files directly under a deliverables directory."""
    if not deliverables_dir.is_dir():
        return []

    normalized_paths: list[Path] = []
    for path in sorted(deliverables_dir.glob("*.md")):
        if normalize_angle_brackets(path):
            normalized_paths.append(path)
    return normalized_paths
