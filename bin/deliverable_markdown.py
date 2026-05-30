#!/usr/bin/env python3
"""Utilities for generated deliverable Markdown files."""

from __future__ import annotations

from pathlib import Path


def normalize_angle_brackets(path: Path) -> bool:
    """Replace angle brackets with braces in generated Markdown deliverables."""
    if path.suffix.lower() != ".md" or not path.exists():
        return False

    text = path.read_text(encoding="utf-8-sig")
    normalized = text.replace("<", "{").replace(">", "}")
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
