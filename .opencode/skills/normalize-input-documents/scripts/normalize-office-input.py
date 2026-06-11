#!/usr/bin/env python3
"""将 Office 输入文档归一化为缓存 Markdown 文件。"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SUPPORTED_SUFFIXES = {".md", ".markdown", ".docx", ".xlsx"}
INVALID_PATH_CHARS_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]+')


class ChineseArgumentParser(argparse.ArgumentParser):
    def format_usage(self) -> str:
        return super().format_usage().replace("usage:", "用法:")

    def format_help(self) -> str:
        return super().format_help().replace("usage:", "用法:")

    def error(self, message: str) -> None:
        translations = {
            "the following arguments are required: inputs": "缺少必需输入文件",
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


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_stem(path: Path) -> str:
    stem = INVALID_PATH_CHARS_RE.sub("_", path.stem).strip(" .")
    return stem or "document"


def escape_table_cell(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r\n", "\n").replace("\r", "\n").strip()
    text = text.replace("|", r"\|")
    return text.replace("\n", "<br>")


def trim_trailing_empty(cells: list[str]) -> list[str]:
    while cells and not cells[-1]:
        cells.pop()
    return cells


def markdown_table(rows: list[list[str]]) -> list[str]:
    if not rows:
        return []
    trimmed_rows = [trim_trailing_empty(row[:]) for row in rows]
    width = max(len(row) for row in trimmed_rows)
    padded = [row + [""] * (width - len(row)) for row in trimmed_rows]
    header = [cell if cell else f"列{index + 1}" for index, cell in enumerate(padded[0])]
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    for row in padded[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return lines


def docx_image_count(doc: Any) -> int:
    try:
        inline_count = len(doc.inline_shapes)
    except Exception:
        inline_count = 0
    rel_count = 0
    try:
        rel_count = sum(1 for rel in doc.part.rels.values() if "image" in rel.reltype)
    except Exception:
        rel_count = 0
    return max(inline_count, rel_count)


def docx_image_map(doc: Any) -> dict[str, str]:
    image_map: dict[str, str] = {}
    try:
        for rel_id, rel in doc.part.rels.items():
            if "image" in rel.reltype:
                image_map[rel_id] = Path(rel.target_ref).name
    except Exception:
        return {}
    return image_map


def image_refs_from_element(element: Any, image_map: dict[str, str]) -> list[str]:
    rel_attrs = (
        "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed",
        "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}link",
    )
    refs: list[str] = []
    try:
        blips = element.xpath(".//*[local-name()='blip']")
    except Exception:
        blips = []
    for blip in blips:
        rel_id = ""
        for attr in rel_attrs:
            rel_id = blip.get(attr) or rel_id
        refs.append(image_map.get(rel_id, rel_id or "unknown-image"))
    return refs


def image_placeholder_lines(source: Path, image_name: str, occurrence: int, location: str) -> list[str]:
    image_id = f"{image_name}#{occurrence}"
    return [
        f"<!-- DOCX_IMAGE_START: {image_id} -->",
        f"图片占位：{image_id}",
        "",
        f"- 来源：{source.name} / {image_name}",
        f"- 原文位置：{location}",
        "- 补充状态：待处理",
        "- 位置要求：解析后的 Mermaid 或结构化图片事实必须替换此占位块，不得移动到文末或单独文件。",
        f"<!-- DOCX_IMAGE_END: {image_id} -->",
    ]


def append_image_placeholders(
    lines: list[str],
    source: Path,
    refs: list[str],
    location: str,
    image_occurrences: dict[str, int],
    image_placeholders: list[dict[str, Any]],
) -> None:
    for image_name in refs:
        image_occurrences[image_name] = image_occurrences.get(image_name, 0) + 1
        occurrence = image_occurrences[image_name]
        image_id = f"{image_name}#{occurrence}"
        lines.extend(image_placeholder_lines(source, image_name, occurrence, location))
        lines.append("")
        image_placeholders.append(
            {
                "image": image_name,
                "image_id": image_id,
                "location": location,
                "status": "pending",
            }
        )


def build_image_processing_plan(image_placeholders: list[dict[str, Any]], total_images: int) -> dict[str, Any]:
    queue = [
        {
            "image_id": item["image_id"],
            "image": item["image"],
            "location": item["location"],
            "status": item.get("status", "pending"),
        }
        for item in image_placeholders
    ]
    batches: list[dict[str, Any]] = []
    for index in range(0, len(queue), 5):
        batch_items = queue[index : index + 5]
        batches.append(
            {
                "batch_id": f"IMG-BATCH-{len(batches) + 1:03d}",
                "recommended_size": len(batch_items),
                "image_ids": [item["image_id"] for item in batch_items],
                "status": "pending",
            }
        )
    return {
        "strategy": "按原文顺序分批处理图片；普通图片每批最多 5 张，复杂流程图/架构图每批 1-2 张；每批完成后立即回写 Markdown 占位块。",
        "total_images": total_images,
        "located_images": len(image_placeholders),
        "unlocated_images": max(0, total_images - len(image_placeholders)),
        "queue": queue,
        "recommended_batches": batches,
    }


def iter_docx_blocks(parent: Any):
    from docx.document import Document as DocxDocument
    from docx.oxml.table import CT_Tbl
    from docx.oxml.text.paragraph import CT_P
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    parent_element = parent.element.body if isinstance(parent, DocxDocument) else parent._tc
    for child in parent_element.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)


def paragraph_to_markdown(paragraph: Any) -> list[str]:
    text = paragraph.text.strip()
    if not text:
        return []

    style_name = ""
    try:
        style_name = (paragraph.style.name or "").strip()
    except Exception:
        style_name = ""
    style_lower = style_name.lower()

    if style_lower.startswith("toc") or "table of contents" in style_lower:
        return []

    heading_match = re.search(r"heading\s*(\d+)", style_lower)
    if not heading_match:
        heading_match = re.search(r"标题\s*(\d+)", style_lower)
    if heading_match:
        level = min(max(int(heading_match.group(1)), 1), 6)
        return [f"{'#' * level} {text}"]

    if "list" in style_lower or "列表" in style_lower:
        return [f"- {text}"]

    return [text]


def table_to_markdown(table: Any) -> list[str]:
    rows: list[list[str]] = []
    for row in table.rows:
        cells = [escape_table_cell(cell.text) for cell in row.cells]
        if any(cells):
            rows.append(cells)
    return markdown_table(rows)


def collect_table_image_refs(table: Any, image_map: dict[str, str]) -> list[tuple[str, list[str]]]:
    refs: list[tuple[str, list[str]]] = []
    for row_index, row in enumerate(table.rows, start=1):
        for column_index, cell in enumerate(row.cells, start=1):
            cell_refs = image_refs_from_element(cell._tc, image_map)
            if cell_refs:
                refs.append((f"表格第 {row_index} 行第 {column_index} 列之后", cell_refs))
    return refs


def convert_docx(source: Path, output: Path) -> dict[str, Any]:
    try:
        from docx import Document
    except ImportError as exc:
        raise RuntimeError("转换 .docx 需要安装 python-docx") from exc

    doc = Document(str(source))
    image_count = docx_image_count(doc)
    image_map = docx_image_map(doc)
    image_occurrences: dict[str, int] = {}
    image_placeholders: list[dict[str, Any]] = []
    lines: list[str] = [f"# {source.stem}", ""]

    for block in iter_docx_blocks(doc):
        if block.__class__.__name__ == "Paragraph":
            converted = paragraph_to_markdown(block)
            image_refs = image_refs_from_element(block._element, image_map)
        else:
            converted = table_to_markdown(block)
            table_image_refs = collect_table_image_refs(block, image_map)
            image_refs = []
        if converted:
            lines.extend(converted)
            lines.append("")
        if block.__class__.__name__ == "Paragraph" and image_refs:
            append_image_placeholders(
                lines,
                source,
                image_refs,
                "原 DOCX 图片所在段落之后",
                image_occurrences,
                image_placeholders,
            )
        elif block.__class__.__name__ != "Paragraph":
            for location, refs in table_image_refs:
                append_image_placeholders(lines, source, refs, location, image_occurrences, image_placeholders)

    output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    warnings: list[str] = []
    if image_count:
        warnings.append(
            f"检测到 {image_count} 个图片对象，已在 Markdown 中插入 {len(image_placeholders)} 个原文位置占位块。"
            "架构图、流程图或截图需要按 DOCX 图片与图形补充流程在占位块原位置替换为 Mermaid 或结构化描述。"
        )
        if len(image_placeholders) < image_count:
            warnings.append(
                f"有 {image_count - len(image_placeholders)} 个图片对象未能可靠定位到正文位置，"
                "可能位于页眉页脚、文本框、浮动图形或不支持的位置；完成归一化前必须人工定位并合并回正确上下文。"
            )
    return {
        "kind": "docx",
        "image_count": image_count,
        "image_placeholder_count": len(image_placeholders),
        "image_placeholders": image_placeholders,
        "image_processing": build_image_processing_plan(image_placeholders, image_count),
        "warnings": warnings,
    }


def convert_xlsx(source: Path, output: Path) -> dict[str, Any]:
    try:
        import openpyxl
    except ImportError as exc:
        raise RuntimeError("转换 .xlsx 需要安装 openpyxl") from exc

    workbook = openpyxl.load_workbook(source, data_only=True)
    lines: list[str] = [f"# {source.stem}", ""]
    sheet_count = 0
    warnings: list[str] = []
    sheet_summaries: list[dict[str, Any]] = []
    for sheet in workbook.worksheets:
        rows: list[list[str]] = []
        skipped_empty_rows = 0
        for row in sheet.iter_rows(values_only=True):
            cells = trim_trailing_empty([escape_table_cell(value) for value in row])
            if any(cells):
                rows.append(cells)
            else:
                skipped_empty_rows += 1
        if not rows:
            sheet_summaries.append(
                {
                    "sheet": sheet.title,
                    "rows": 0,
                    "skipped_empty_rows": skipped_empty_rows,
                    "merged_ranges": len(sheet.merged_cells.ranges),
                }
            )
            continue
        sheet_count += 1
        merged_ranges = len(sheet.merged_cells.ranges)
        if merged_ranges:
            warnings.append(
                f"工作表 `{sheet.title}` 检测到 {merged_ranges} 个合并单元格；"
                "已保留左上角单元格内容，复杂多级表头建议人工确认。"
            )
        sheet_summaries.append(
            {
                "sheet": sheet.title,
                "rows": len(rows),
                "skipped_empty_rows": skipped_empty_rows,
                "merged_ranges": merged_ranges,
            }
        )
        lines.extend([f"## {sheet.title}", ""])
        lines.extend(markdown_table(rows))
        lines.append("")

    output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    if sheet_count == 0:
        warnings.append("未发现包含内容的工作表，已生成仅含标题的 Markdown。")
    return {"kind": "xlsx", "sheet_count": sheet_count, "sheet_summaries": sheet_summaries, "warnings": warnings}


def normalize_one(source: Path, cache_dir: Path, force: bool) -> dict[str, Any]:
    source = source.expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"输入文件不存在: {source}")
    if not source.is_file():
        raise ValueError(f"输入路径不是文件: {source}")

    suffix = source.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise ValueError(f"不支持的输入类型 {suffix}: {source}")

    if suffix in {".md", ".markdown"}:
        sha = file_sha256(source)
        stat = source.stat()
        return {
            "source": str(source),
            "markdown": str(source),
            "metadata": "",
            "cached": False,
            "kind": "markdown",
            "source_name": source.name,
            "source_size": stat.st_size,
            "source_mtime": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
            "sha256": sha,
            "warnings": [],
        }

    sha = file_sha256(source)
    out_dir = cache_dir / sha[:12]
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = safe_stem(source)
    markdown_path = out_dir / f"{stem}.md"
    metadata_path = out_dir / f"{stem}.conversion.json"

    cached = markdown_path.exists() and metadata_path.exists() and not force
    conversion_extra: dict[str, Any] = {"kind": suffix.lstrip("."), "warnings": []}
    if not cached:
        if suffix == ".docx":
            conversion_extra = convert_docx(source, markdown_path)
        elif suffix == ".xlsx":
            conversion_extra = convert_xlsx(source, markdown_path)

        stat = source.stat()
        metadata = {
            "source": str(source),
            "source_name": source.name,
            "source_size": stat.st_size,
            "source_mtime": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
            "sha256": sha,
            "markdown": str(markdown_path.resolve()),
            "converted_at": utc_now_iso(),
            **conversion_extra,
        }
        metadata_path.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    else:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        conversion_extra = {
            "kind": metadata.get("kind", suffix.lstrip(".")),
            "warnings": metadata.get("warnings", []),
        }

    return {
        "source": str(source),
        "markdown": str(markdown_path.resolve()),
        "metadata": str(metadata_path.resolve()),
        "cached": cached,
        "sha256": sha,
        **conversion_extra,
    }


def run_input_basename(result: dict[str, Any]) -> str:
    source = Path(result["source"])
    sha = result.get("sha256") or file_sha256(source)
    return f"{sha[:12]}-{safe_stem(source)}"


def load_or_create_metadata(result: dict[str, Any]) -> dict[str, Any]:
    metadata_path = result.get("metadata")
    if metadata_path:
        path = Path(metadata_path)
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))

    source = Path(result["source"])
    stat = source.stat()
    return {
        "source": str(source),
        "source_name": source.name,
        "source_size": stat.st_size,
        "source_mtime": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
        "sha256": result.get("sha256") or file_sha256(source),
        "markdown": str(Path(result["markdown"]).resolve()),
        "converted_at": None,
        "kind": result.get("kind", source.suffix.lower().lstrip(".")),
        "warnings": result.get("warnings", []),
    }


def bind_results_to_run_inputs(results: list[dict[str, Any]], run_input_dir: Path) -> Path:
    run_input_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = run_input_dir / "input-normalization-manifest.json"
    existing_entries: list[dict[str, Any]] = []
    if manifest_path.exists():
        try:
            existing_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            existing_entries = list(existing_manifest.get("inputs", []))
        except Exception:
            existing_entries = []
    manifest_entries_by_target: dict[str, dict[str, Any]] = {
        str(entry.get("run_markdown", "")): entry for entry in existing_entries if entry.get("run_markdown")
    }

    for result in results:
        basename = run_input_basename(result)
        run_markdown = (run_input_dir / f"{basename}.md").resolve()
        run_metadata = (run_input_dir / f"{basename}.conversion.json").resolve()
        markdown_path = Path(result["markdown"]).resolve()
        if markdown_path != run_markdown:
            shutil.copy2(markdown_path, run_markdown)

        metadata = load_or_create_metadata(result)
        metadata.update(
            {
                "run_markdown": str(run_markdown),
                "run_metadata": str(run_metadata),
                "global_cache_markdown": str(Path(result["markdown"]).resolve()),
                "global_cache_metadata": result.get("metadata", ""),
                "bound_at": utc_now_iso(),
            }
        )
        run_metadata.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        result["run_markdown"] = str(run_markdown)
        result["run_metadata"] = str(run_metadata)
        manifest_entries_by_target[str(run_markdown)] = {
            "source": result["source"],
            "kind": result.get("kind", ""),
            "sha256": result.get("sha256", ""),
            "cached": result.get("cached", False),
            "global_cache_markdown": str(Path(result["markdown"]).resolve()),
            "global_cache_metadata": result.get("metadata", ""),
            "run_markdown": str(run_markdown),
            "run_metadata": str(run_metadata),
            "warnings": result.get("warnings", []),
        }

    manifest = {
        "generated_at": utc_now_iso(),
        "run_input_dir": str(run_input_dir.resolve()),
        "inputs": list(manifest_entries_by_target.values()),
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path.resolve()


def main() -> int:
    configure_stdio()
    parser = ChineseArgumentParser(
        description="将 .docx/.xlsx 输入文档归一化为缓存 Markdown",
        add_help=False,
        usage="python skills/normalize-input-documents/scripts/normalize-office-input.py [选项] <输入文件...>",
    )
    parser._positionals.title = "位置参数"
    parser._optionals.title = "可选参数"
    parser.add_argument("-h", "--help", action="help", help="显示帮助信息并退出")
    parser.add_argument("inputs", nargs="+", type=Path, help="输入 .md、.docx 或 .xlsx 文件")
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=repo_root() / "outputs" / "input-cache",
        help="缓存目录，默认 outputs/input-cache",
    )
    parser.add_argument("--force", action="store_true", help="强制重新生成缓存 Markdown")
    parser.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    parser.add_argument(
        "--run-dir",
        type=Path,
        help="可选 run 目录；归一化输入会复制到 <run-dir>/inputs",
    )
    parser.add_argument(
        "--run-input-dir",
        type=Path,
        help="可选 run-local inputs 目录；优先级高于 --run-dir/inputs",
    )
    args = parser.parse_args()
    if args.run_dir and args.run_input_dir:
        print("失败: --run-dir 和 --run-input-dir 不能同时使用", file=sys.stderr)
        return 2

    cache_dir = args.cache_dir
    if not cache_dir.is_absolute():
        cache_dir = repo_root() / cache_dir
    cache_dir.mkdir(parents=True, exist_ok=True)

    run_input_dir: Path | None = None
    if args.run_input_dir:
        run_input_dir = args.run_input_dir
    elif args.run_dir:
        run_input_dir = args.run_dir / "inputs"
    if run_input_dir is not None and not run_input_dir.is_absolute():
        run_input_dir = repo_root() / run_input_dir

    results = []
    try:
        for source in args.inputs:
            results.append(normalize_one(source, cache_dir, args.force))
        manifest_path = bind_results_to_run_inputs(results, run_input_dir) if run_input_dir else None
    except Exception as exc:
        print(f"失败: {exc}", file=sys.stderr)
        return 1

    if args.json:
        if manifest_path:
            payload: dict[str, Any] = {"results": results}
            payload["run_input_manifest"] = str(manifest_path)
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        warning_count = 0
        for result in results:
            if result["kind"] == "markdown":
                print(f"无需转换: {result['source']}")
            else:
                state = "复用缓存" if result["cached"] else "已转换"
                print(f"{state}: {result['source']} -> {result['markdown']}")
            if result.get("run_markdown"):
                print(f"绑定到 run inputs: {result['run_markdown']}")
            for warning in result.get("warnings", []):
                warning_count += 1
                print(f"警告: {warning}")
        if manifest_path:
            print(f"run 输入 manifest: {manifest_path}")
        if warning_count:
            print(
                f"脚本阶段完成，但存在 {warning_count} 条转换警告；"
                "调用 normalize-input-documents skill 时必须继续处理或记录这些警告后才能结束。"
            )
        else:
            print("脚本阶段完成：未发现转换警告。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
