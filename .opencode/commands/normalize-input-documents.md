---
description: 将 Office 输入文档归一化为缓存 Markdown
agent: build
---

使用仓库内置 skill `normalize-input-documents`。

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
python bin/normalize-office-input.py <arguments>
```

固定使用 `outputs/input-cache/<sha256-12>/` 作为全局缓存位置。输出时说明归一化 Markdown 路径、转换 metadata 路径、缓存复用状态和转换警告。完整测试分析或测试设计 run 后续会用同一脚本追加 `--run-dir outputs/runs/<run-id>`，把缓存 Markdown 绑定到 `outputs/runs/<run-id>/inputs/`；本独立命令不得执行 run-local 绑定。

如果转换 metadata 报告图片或转换警告，读取 `skills/normalize-input-documents/references/docx-image-and-diagram-workflow.md`。当当前模型支持多模态图片理解时，在下游分析或设计使用归一化输入前，补充图片、图形、流程图、架构图、截图、EMF 或 Visio 中承载的事实。补充事实保存在同一缓存目录，或明确说明当前模型不支持多模态，因此未执行图片理解。

当输入是大型或复杂 Excel 知识源时，先读取 `skills/normalize-input-documents/references/xlsx-to-markdown.md` 和 `skills/normalize-input-documents/references/xlsx-to-ai-knowledge-base.md`，再判断基础表格转换是否足够。
