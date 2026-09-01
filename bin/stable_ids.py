"""Stable TP/TC identifier allocation within one run directory."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data if isinstance(data, dict) else {}


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def _id_number(value: Any, prefix: str) -> int | None:
    match = re.fullmatch(rf"{re.escape(prefix)}-(\d{{3}})", str(value or ""))
    return int(match.group(1)) if match else None


def _semantic_key(item: dict[str, Any]) -> str:
    payload = {key: value for key, value in item.items() if key != "id"}
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def assign_stable_ids(
    run_dir: Path,
    prefix: str,
    incoming: list[dict[str, Any]],
    previous: list[dict[str, Any]],
    all_existing: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Preserve existing IDs and append new IDs without reusing retired values."""

    registry_path = run_dir / "process" / "id-registry.json"
    registry = _read_json(registry_path) or {
        "artifactType": "id-registry",
        "schemaVersion": "1.0",
        "nextNumbers": {},
        "retiredIds": {},
    }
    next_numbers = registry.setdefault("nextNumbers", {})
    retired_map = registry.setdefault("retiredIds", {})
    retired = set(str(value) for value in retired_map.setdefault(prefix, []))

    previous_ids = {
        str(item.get("id")): item
        for item in previous
        if isinstance(item, dict) and _id_number(item.get("id"), prefix) is not None
    }
    current_group_ids = set(previous_ids)
    used_elsewhere = {
        str(item.get("id"))
        for item in all_existing
        if isinstance(item, dict)
        and _id_number(item.get("id"), prefix) is not None
        and str(item.get("id")) not in current_group_ids
    }
    known_numbers = [
        number
        for item in all_existing
        if isinstance(item, dict)
        for number in [_id_number(item.get("id"), prefix)]
        if number is not None
    ]
    known_numbers.extend(
        number for value in retired for number in [_id_number(value, prefix)] if number is not None
    )
    next_number = max(int(next_numbers.get(prefix, 1)), max(known_numbers, default=0) + 1)

    semantic_matches: dict[str, list[str]] = {}
    for item_id, item in previous_ids.items():
        semantic_matches.setdefault(_semantic_key(item), []).append(item_id)

    assigned: set[str] = set()
    result: list[dict[str, Any]] = []
    for raw_item in incoming:
        item = dict(raw_item)
        candidate = str(item.get("id") or "")
        # The model may copy an existing identifier for the same work item, but
        # it must never choose an identifier for a newly introduced item.
        if candidate not in previous_ids or candidate in used_elsewhere or candidate in assigned or candidate in retired:
            candidate = ""
        if not candidate:
            matches = semantic_matches.get(_semantic_key(item), [])
            candidate = next((value for value in matches if value not in assigned), "")
        while not candidate:
            if next_number > 999:
                raise ValueError(f"{prefix} 编号已超过三位上限")
            value = f"{prefix}-{next_number:03d}"
            next_number += 1
            if value not in used_elsewhere and value not in assigned and value not in retired:
                candidate = value
        item["id"] = candidate
        assigned.add(candidate)
        result.append(item)

    retired.update(current_group_ids - assigned)
    next_numbers[prefix] = next_number
    retired_map[prefix] = sorted(retired)
    _write_json(registry_path, registry)
    return result
