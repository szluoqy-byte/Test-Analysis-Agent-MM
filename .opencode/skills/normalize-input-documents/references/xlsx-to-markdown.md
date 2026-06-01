# XLSX 转 Markdown 参考

本文件是 `normalize-input-documents` 的内置参考，用于说明 `.xlsx` 输入如何稳定转换为可被测试分析和测试设计流程读取的 Markdown。主流程默认使用 `python bin/normalize-office-input.py`，复杂 Excel 可按本参考做人工增强或脚本扩展。

## 转换目标

转换后的 Markdown 应满足：

- 一个 Excel 行对应一个 Markdown 表格行。
- 多行单元格使用 `<br>`，不能把一个 Excel 行拆成多行 Markdown。
- 单元格中的 `|` 转义为 `\|`。
- 每个 sheet 输出为独立章节。
- 空行跳过，空列按需过滤。
- 公式单元格读取计算结果，使用 `openpyxl.load_workbook(..., data_only=True)`。

## 基础转换规则

```python
def cell_to_md(value):
    if value is None:
        return ""
    text = str(value)
    text = text.replace("|", r"\|")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.replace("\n", "<br>").strip()
```

## 多 sheet 输出

每个 sheet 生成一个二级标题，便于后续按业务域或规则域定位。

```markdown
# <工作簿名>

## <SheetName>

| 字段 | 规则 |
| --- | --- |
| orderId | 长度 13 位 |
```

## 多级表头处理

有些 Excel 前两行或前三行共同构成表头，例如英文名 + 中文名，或一级分类 + 二级字段。转换前应合并为单行表头。

```python
def merge_headers(header_rows, max_cols):
    merged = [""] * max_cols
    for row in reversed(header_rows):
        for index in range(min(len(row), max_cols)):
            value = cell_to_md(row[index])
            if not value:
                continue
            merged[index] = f"{value}<br>{merged[index]}" if merged[index] else value
    return merged
```

使用建议：

- 普通需求/设计表：通常使用 1 行表头。
- 中英双语表头：通常合并 2 行。
- 分类 + 字段 + 子字段：先抽样查看前 5 行，再决定合并 2 行或 3 行。
- 不确定时不要自动猜测；保留原始表头并在过程产物记录“表头结构待确认”。

## 空列和空行

大表或测试因子库经常有占位列。过滤前先诊断，再决定是否删除。

空列诊断：

```python
for column_index in range(ws.max_column):
    values = [
        ws.cell(row=row_index + 1, column=column_index + 1).value
        for row_index in range(header_rows, ws.max_row)
    ]
    non_empty = sum(1 for value in values if value is not None and str(value).strip())
    name = ws.cell(row=1, column=column_index + 1).value or f"col_{column_index + 1}"
    print(column_index + 1, name, non_empty)
```

空行处理：

- 表尾全空行直接跳过。
- 只有分类列有值的数据行不能机械删除，它可能是后续数据的层级标题。
- 测试因子库中的空壳行应过滤：如果前置、操作、预期、自动化前置、自动化操作、自动化预期等执行列全空，则该行没有测试知识价值。

## 快速诊断

转换前建议抽样查看 sheet 尺寸和前几行非空单元格。

```python
import openpyxl

workbook = openpyxl.load_workbook(r"<input.xlsx>", data_only=True)
for sheet in workbook.worksheets:
    print(f"Sheet={sheet.title}, rows={sheet.max_row}, cols={sheet.max_column}")
    for row in range(1, min(6, sheet.max_row + 1)):
        values = []
        for col in range(1, min(28, sheet.max_column + 1)):
            value = sheet.cell(row=row, column=col).value
            if value is not None and str(value).strip():
                values.append(f"C{col}={str(value)[:50]!r}")
        print(f"Row {row}: {', '.join(values) if values else '(empty)'}")
```

## 校验要求

转换完成后检查：

- sheet 数量是否覆盖原文件。
- Markdown 表格行数是否与有效 Excel 行数一致。
- 多行单元格是否保持在同一个表格单元格内。
- `|` 是否已转义。
- 公式是否读取为计算值而不是公式文本。
- 表头是否能被下游理解；如果不能，记录表头待确认。
- 不出现模板占位符或转换脚本调试文本。
