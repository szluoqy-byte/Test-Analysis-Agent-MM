---
name: test-analysis-workflow
description: 当用户提供需求文档和可选设计方案文档，并要求生成“SC 场景树 -> TP 测试点”的测试分析方案时使用；该 skill 编排上下文、输入事实、测试技术路由、测试分析方案 JSON 生成、独立评审和 Markdown 渲染。
---

# 需求到测试分析方案主入口

本 skill 是 `test-analysis-agent` 的完整链路入口。目标是从 `$ARGUMENTS` 指定的需求文档和可选设计方案文档中，生成 `测试分析方案`。

测试分析方案回答 what to test：输出最多 3 层 `SC-*` 场景树和全局连续 `TP-*` 测试点。它不输出测试用例、测试数据、操作步骤或预期结果。

## 必需输入

- `$ARGUMENTS`：至少包含一份 `.md` 或 `.markdown` 需求文档路径。
- 可额外包含一份或多份 `.md` 或 `.markdown` 设计方案文档路径。
- 如果输入包含 `.docx` 或 `.xlsx`，不得在本 workflow 中转换；必须先由 `@file-normalization-agent` 归一化为 Markdown。
- 可选 `--project <project-key>`，必须传递给 `context-source-indexing`；personal 来源固定来自 `*/user/**/*.md`，无需额外参数。

## 职责边界

- 本 skill 只负责编排完整分析链路和写出本次运行产物。
- core 强制规则、通用知识和固定质量门禁由 workflow 或对应 skill 明确读取。
- project/personal 扩展来源来自 `context-source-indexing` 生成的 `sources[]` 索引。
- `input-fact-modeling` 负责建立统一输入事实模型。
- `test-analysis-solution-generation` 负责生成 `SC-*` 场景树和 `TP-*` 测试点。
- `test-analysis-solution-review` 负责语义评审，不重复结构、编号、字段和 Markdown 语法检查。
- `coverage-review` 负责覆盖、追踪、方法应用、core rules 和动态来源应用状态收口。
- 主交付件事实源是 `outputs/runs/<run-id>/deliverables/test-analysis-solution.json`；人读版由 `bin/render-run-markdown.py` 生成。

## 执行流程

1. 校验输入至少包含一份 Markdown 需求文档；若发现 Office 输入，输出需先使用 `@file-normalization-agent` 的阻断说明，不创建测试分析 run。
2. 固定 `PROJECT_ROOT`，运行 `python bin/generate-run-id.py` 生成本次运行 ID，并创建 `outputs/runs/<run-id>/deliverables/`、`process/`、`reports/` 和 `inputs/`。
3. 使用 `templates/process-artifacts-json-template.json` 创建 `process/task-list.json`，并按阶段维护状态。
4. 调用 `python skills/context-source-indexing/scripts/build-context-source-index.py ...` 生成 `process/context-pack.json`。
5. 使用 `input-fact-modeling` 读取需求文档和可选设计方案文档，生成 `process/input-fact-model.json`。
6. 使用 `testing-method-router` 对输入事实模型中的需求事实和设计事实进行测试技术路由。
7. 使用路由选中的专项方法参考产出 `ME-*` 方法证据、测试点候选和按源补读记录。
8. 使用 `test-analysis-solution-generation` 生成 `deliverables/test-analysis-solution.json`。主交付件使用 schema `2.0`，只包含 `SC-*` 和 `TP-*`。
9. 运行 `bin/lint-run-json.py outputs/runs/<run-id>`。失败时先修正 JSON，不进入评审。
10. 运行 `bin/render-run-markdown.py outputs/runs/<run-id>`，再运行 `bin/lint-test-analysis-solution.py outputs/runs/<run-id>/deliverables/test-analysis-solution.md`。
11. 使用 `test-analysis-solution-review` 独立语义评审测试分析方案 JSON，评审结果写入 `reports/test-analysis-solution-review.json`。
12. 使用 `coverage-review` 执行覆盖、追踪、方法应用和过程门禁收口，结果写入 `reports/coverage-review.json`。
13. 最终输出前刷新 `process/task-list.json`，运行 `bin/render-run-markdown.py` 和 `bin/check-artifact-consistency.py`。

## 阶段产物契约

| 阶段 | 必须产出 | 交给下一阶段 |
|---|---|---|
| `task-list` | `process/task-list.json`、派生 `process/task-list.md` | 全流程阶段顺序与状态追踪 |
| `context-source-indexing` | `process/context-pack.json` | 后续阶段按阶段可见性读取动态来源 |
| `input-fact-modeling` | `process/input-fact-model.json` | 测试技术路由、测试分析方案生成 |
| `testing-method-router` | 测试技术路由表 | 专项方法参考、测试分析方案生成 |
| 专项方法参考 | `ME-*` 方法证据、测试点候选 | 测试分析方案生成 |
| `test-analysis-solution-generation` | `deliverables/test-analysis-solution.json`、场景树、测试点 | JSON 校验 |
| 确定性校验 | JSON lint、Markdown render、Markdown lint | 独立语义评审 |
| `test-analysis-solution-review` | `reports/test-analysis-solution-review.json` | 覆盖审查 |
| `coverage-review` | `reports/coverage-review.json` | 输出收口 |

## 输出要求

- 主输出使用 `templates/test-analysis-solution-json-template.json` 生成 JSON。
- `scenarios[]` 是场景树，最多 3 层；非叶子场景只允许有 `children[]`，叶子场景必须有 `testPoints[]`。
- `TP-*` 全局连续编号，每个叶子场景必须包含 `E2E场景测试`。
- `TP-*` 必须包含 `id`、`title`、`objective`，建议包含 `basisRefs[]` 和 `methodRefs[]`。
- 分析方案不得包含测试用例、测试数据、步骤、预期结果或 schemaVersion 2.0 之外的字段。
- 主输出不得使用 Markdown 加粗语法。
- 全流程不调用用户交互能力，不创建问题队列，不直接向用户提问，不暂停主流程。
