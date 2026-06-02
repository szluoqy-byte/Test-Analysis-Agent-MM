---
name: normalize-input-documents
description: 当需求文档、设计方案文档或已评审分析方案输入包含 .docx 或 .xlsx Office 文件时使用；先统一转换到全局 cache，并在完整 run 中绑定为 run-local Markdown，再交给测试分析或测试设计主流程。
---

# 输入文档归一化

本 skill 负责在测试分析或测试设计正式开始前，把 Office 输入文档归一化为 Markdown。它解决三个问题：

- 主流程只消费 Markdown，避免 `requirement-testability`、`design-solution-extraction` 和设计依据补读重复处理 Office 文件。
- 转换结果按源文件内容哈希归档，源文件未变化时复用缓存，避免重复解析。
- 完整 run 在 `outputs/runs/<run-id>/inputs/` 下保存本次实际使用的归一化输入副本和 manifest，保证单次交付自包含可追踪。

## 触发条件

当 `$ARGUMENTS`、用户消息或过程输入中出现以下文件时，先执行本 skill：

- 需求文档：`.docx`、`.xlsx`。
- 系统设计方案文档：`.docx`、`.xlsx`。
- 外部已评审测试分析方案：优先要求 `.md`；如果用户只给 Office 文件，也先归一化。

`.md` 文件不需要转换，直接作为下游输入。

## 归档路径

转换结果采用两层路径。

全局复用缓存固定写入仓库根目录下：

```text
outputs/input-cache/<sha256-12>/<source-stem>.md
outputs/input-cache/<sha256-12>/<source-stem>.conversion.json
```

- `<sha256-12>` 是源文件内容 SHA-256 的前 12 位。
- `<source-stem>` 来自源文件名，脚本会替换 Windows 非法路径字符。
- 源文件内容不变时，输出路径稳定，可直接复用。
- 源文件内容变化时，哈希变化，生成新的缓存目录，不覆盖旧转换结果。

完整测试分析或测试设计 run 创建后，还必须把本次使用的归一化输入绑定到 run 目录：

```text
outputs/runs/<run-id>/inputs/<sha256-12>-<source-stem>.md
outputs/runs/<run-id>/inputs/<sha256-12>-<source-stem>.conversion.json
outputs/runs/<run-id>/inputs/input-normalization-manifest.json
```

- run-local Markdown 是后续主流程读取的输入事实源。
- `input-normalization-manifest.json` 记录源文件、全局缓存、run-local 输入、metadata 和转换警告之间的映射。
- 独立 `/normalize-input-documents` 命令不创建 run 时，可以只写全局缓存。

## 执行命令

从仓库根目录执行：

```bash
python bin/normalize-office-input.py <input1.docx> <input2.xlsx>
```

输出会列出每个输入的归一化结果。

完整测试分析或测试设计主流程必须在创建 run 目录后执行：

```bash
python bin/normalize-office-input.py --run-dir outputs/runs/<run-id> <input1.docx> <input2.xlsx>
```

下游主流程必须使用 `outputs/runs/<run-id>/inputs/*.md` 路径作为需求文档、设计方案文档或外部分析方案路径。

如果需要机器可读结果：

```bash
python bin/normalize-office-input.py --json --run-dir outputs/runs/<run-id> <input1.docx> <input2.xlsx>
```

## 复用规则

1. 对每个输入计算内容哈希。
2. 如果 `outputs/input-cache/<sha256-12>/<source-stem>.md` 和 `.conversion.json` 已存在，且未指定 `--force`，直接复用。
3. 如果不存在缓存，执行转换。
4. 如果传入 `--run-dir` 或 `--run-input-dir`，把归一化 Markdown 和 metadata 复制到 run-local inputs，并刷新 `input-normalization-manifest.json`。
5. 转换后必须记录源路径、源大小、源 mtime、SHA-256、转换时间、输出 Markdown 路径和转换警告。

## DOCX 转换边界

本仓库脚本提供稳定的文本与表格转换能力：

- 段落按原顺序输出。
- Word heading 样式映射为 Markdown 标题。
- 表格转换为 Markdown 表格。
- 多行单元格转换为 `<br>`。
- 表格中的 `|` 会转义。

如果 DOCX 中包含架构图、流程图、截图、EMF、Visio 或其他图片内容，脚本会在 metadata 中记录图片数量和转换警告。此时应按本 skill 内置参考 `references/docx-image-and-diagram-workflow.md` 补充图片描述或 Mermaid，再进入分析/设计主流程；不得静默忽略设计图中承载的接口、流程、状态或依赖信息。

## XLSX 转换边界

本仓库脚本提供基础表格转换能力：

- 每个 sheet 输出为独立章节。
- 第一行非空行作为表头。
- 多行单元格转换为 `<br>`。
- 空行会跳过。

大型测试因子库、复杂多级表头或需要按维度拆分的 Excel，使用本 skill 内置参考 `references/xlsx-to-markdown.md` 和 `references/xlsx-to-ai-knowledge-base.md` 做增强处理。

## 内置参考资料

本 skill 已内置 Office 转 Markdown 所需参考，不依赖任何外部仓库或本机固定路径。

- `references/docx-image-and-diagram-workflow.md`：DOCX 图片、架构图、流程图、EMF、Visio 和截图的补充分析流程。
- `references/xlsx-to-markdown.md`：XLSX 多 sheet、多行单元格、管道符、多级表头、空行空列的 Markdown 转换规则。
- `references/xlsx-to-ai-knowledge-base.md`：测试设计因子库、checklist 或项目知识类 Excel 的结构化归档规则。

## 主流程集成

- `analyze-requirement-test-analysis-solution` 和 `generate-test-design-solution` 必须先固定 `<run-id>` 并创建 run 目录，再执行本 skill。
- 若存在 Office 输入，主流程使用 `python bin/normalize-office-input.py --run-dir outputs/runs/<run-id> ...`；无 Office 输入时该阶段置为 `skipped`。
- `process/task-list.md` 中的“输入文档归一化”阶段在触发时置为 `done`，证据路径写 `outputs/runs/<run-id>/inputs/input-normalization-manifest.json`；无 Office 输入时置为 `skipped`。
- `process/context-pack.md` 应记录源文件、全局缓存路径、run-local Markdown 和 metadata 的映射，便于后续追踪源文件。

## 约束

- 不从输入文件路径反推 `PROJECT_ROOT`；所有缓存路径从仓库根目录解析。
- 不把缓存 Markdown 写到输入文件所在目录。
- 完整 run 的后续流程不得直接读取全局 `outputs/input-cache/`；必须读取 `outputs/runs/<run-id>/inputs/` 下的 run-local 输入。
- 不把 Office 原文全量写入 memory、knowledge 或 rules。
- 不把转换警告写入主交付件；需要留痕时写入 process 或 reports。
- 转换后的 Markdown 是下游分析/设计的输入事实源；如果转换存在图片缺失或表格异常风险，必须在过程产物中记录。
