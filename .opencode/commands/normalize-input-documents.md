---
description: 将 Office 输入文档归一化为缓存 Markdown
agent: build
---

使用仓库内置 skill `normalize-input-documents`。该命令是 `@file-normalization-agent` 的轻量命令入口，只做文件归一化，不进入测试分析或测试设计主流程。

将下面的命令参数视为该 skill 的 `$ARGUMENTS`：

```text
$ARGUMENTS
```

本命令只执行输入文档归一化。不得创建 `outputs/runs/<run-id>/`，不得生成 `test-analysis-solution.md`，也不得生成 `test-design-solution.md`。

支持的参数提示：

- Office 输入文档：`<input.docx>` 或 `<input.xlsx>`。
- Markdown 输入文档：`<input.md>` 或 `<input.markdown>`；只报告无需转换。
- 支持一次传入多个输入文件。路径包含空格或中文时必须使用引号包裹。
- 可选强制刷新：`--force`。
- 可选机器可读输出：`--json`。

从仓库根目录执行：

```text
python skills/normalize-input-documents/scripts/normalize-office-input.py <arguments>
```

固定使用 `outputs/input-cache/<sha256-12>/` 作为全局缓存位置。输出时说明归一化 Markdown 路径、转换 metadata 路径、缓存复用状态和转换警告。测试分析或测试设计 workflow 后续直接读取本命令输出的归一化 Markdown 路径；本独立命令不得创建或修改 run-local 绑定。

如果转换 metadata 报告图片或转换警告，读取 `skills/normalize-input-documents/references/docx-image-and-diagram-workflow.md`。当当前模型支持多模态图片理解时，在下游分析或设计使用归一化输入前，补充图片、图形、流程图、架构图、截图、EMF 或 Visio 中承载的事实。补充事实必须替换归一化 Markdown 中对应的 `DOCX_IMAGE_START` / `DOCX_IMAGE_END` 原位占位块，不能只保存在单独文件、文末章节、过程记录或最终回复中；如果当前模型不支持多模态，必须在对应占位块记录未执行原因。

当输入是大型或复杂 Excel 知识源时，先读取 `skills/normalize-input-documents/references/xlsx-to-markdown.md` 和 `skills/normalize-input-documents/references/xlsx-to-ai-knowledge-base.md`，再判断基础表格转换是否足够。

完成条件：

- 不能只运行 `python skills/normalize-input-documents/scripts/normalize-office-input.py ...` 后就结束。
- 必须逐个输入文件说明处理状态：无需转换、已转换或复用缓存。
- 必须说明每个输出 Markdown、metadata 和缓存目录路径。
- 必须处理或记录每条转换警告的收口状态：`已处理`、`无需处理` 或 `未执行原因`。
- DOCX 图片/图形 warning 必须按图片补充流程处理，并把 Mermaid 或结构化图片事实合并回归一化 Markdown 的原始占位位置；不能只单独维护补充文件。
- 如果 metadata 显示有图片未能生成正文位置占位块，必须先人工定位正确上下文；无法定位时结论必须写 `需补充处理`。
- 图片理解和 Mermaid 转换必须按原文顺序分批执行，不能一次性读取所有图片：普通图片每批最多 3-5 张，复杂流程图/架构图每批 1-2 张；每批完成后立即回写对应 Markdown 占位块。
- XLSX 合并单元格、多级表头、大型测试因子库或 checklist warning 必须说明基础转换是否足够；如果不足，给出增强归档建议。
- 最终回复必须包含“归一化完成摘要”。如果仍有 warning 未收口，结论必须写 `需补充处理`，不得写 `完成`。
