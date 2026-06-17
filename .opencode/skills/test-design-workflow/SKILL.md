---
name: test-design-workflow
description: 当用户提供已评审测试分析方案，或要求从需求先生成分析方案再扩展 TC 测试用例时使用；该 skill 编排测试分析方案校验、依据补读、测试设计方案 JSON 生成、写作渲染和独立评审。
---

# 测试分析方案到测试设计方案主入口

本 skill 是 `test-design-agent` 的完整链路入口。目标是从 `$ARGUMENTS` 指定的已评审 `测试分析方案` 出发，生成 `测试设计方案`。

测试设计方案回答 how to test：继承 `SC-*` 场景树和 `TP-*` 测试点，并在每个测试点下生成完整步骤级 `TC-*` 测试用例。

## 必需输入

- `$ARGUMENTS`：优先是一份 `test-analysis-solution.json`。
- 可选：原始需求文档路径、设计方案文档路径或 `project=<project-key>`；personal 来源固定来自 `*/user/**/*.md`，无需额外参数。
- 如果用户只提供需求文档和可选设计方案文档，并明确要求生成测试设计方案，本 skill 必须先使用 `test-analysis-workflow` 生成分析方案。
- 如果输入包含 `.docx` 或 `.xlsx`，不得在本 workflow 中转换；必须先由 `@file-normalization-agent` 归一化为 Markdown。
- 新模型不支持旧格式自动迁移；输入分析方案必须符合 schema `2.0`。

## 职责边界

- 本 skill 只负责编排设计链路和写出测试设计方案。
- 测试分析层事实来自已评审测试分析方案；不得把设计阶段发现的新范围直接写成新的 `SC-*` 或 `TP-*`。
- 需求与设计方案只用于校验和补强测试用例依据；不得覆盖分析方案中的已评审层级。
- `test-design-solution-generation` 负责在每个 `TP-*` 下生成 `testCases[]`。
- `test-case-writing` 负责把 canonical JSON 写作为标准 Markdown 或后续扩展的不同交付风格，不改变测试用例事实。
- `test-design-solution-review` 负责独立评审测试用例步骤、测试数据、预期结果依据和分析方案承接。
- 主交付件事实源是 `outputs/runs/<run-id>/deliverables/test-design-solution.json`；人读版由 `test-case-writing` 调用 `bin/render-run-markdown.py` 生成。

## 执行流程

1. 校验输入：识别测试分析方案、Markdown 需求文档和可选 Markdown 设计方案文档。
2. 如果没有测试分析方案，先调用 `test-analysis-workflow` 生成分析方案。
3. 固定 `PROJECT_ROOT` 和 `<run-id>`；优先复用上游分析方案所在 run，否则新建 run。
4. 创建或刷新 `process/task-list.json`，记录当前进入测试设计阶段。
5. 读取并校验 `deliverables/test-analysis-solution.json`；未通过 schema `2.0` 时不进入测试设计生成。
6. 读取或生成 `process/context-pack.json`。
7. 受控补读归一化后的原始需求 Markdown、设计方案 Markdown 或结构化过程记录中与当前分析方案相关的依据。
8. 使用 `test-design-solution-generation` 在每个 `TP-*` 下生成 `testCases[]`，写入 `deliverables/test-design-solution.json`。
9. 运行 `bin/lint-run-json.py`。
10. 使用 `test-case-writing` 将 canonical JSON 写作为标准 Markdown，并运行 `bin/render-run-markdown.py --check` 和 `bin/lint-test-design-solution.py`。
11. 使用 `test-design-solution-review` 独立评审测试设计方案 JSON，结果写入 `reports/test-design-solution-review.json`。
12. 使用 `coverage-review` 检查需求到测试点、测试点到测试用例的覆盖关系。
13. 最终输出前刷新 `process/task-list.json`，运行 `test-case-writing` 的标准 Markdown 检查和 `bin/check-artifact-consistency.py`。

## 输出要求

- 主输出使用 `templates/test-design-solution-json-template.json` 生成 JSON。
- 主输出必须继承分析方案中的 `SC-*` 场景树和 `TP-*` 测试点，不新增、删除、合并或改写分析层级。
- 每个 `TP-*` 必须包含至少 1 个 `TC-*`。
- `TC-*` 全局连续编号。
- 每个 TC 必须包含：
  - `id`
  - `title`
  - `preconditions[]`
  - `testData[]`，每项包含 `name`、`value`、`description`
  - `steps[]`，每项包含 `stepNo`、`action`、`expected`
  - `expectedResult`
  - `sourceRefs[]`
- 接口类 TC 不得写完整裸 URL；必须拆成字段片段。
- 不编造当前用户明确指令、适用 rules、需求、设计方案或分析方案中没有的业务事实、接口、字段、状态、角色、阈值、错误提示或错误码。
- 主输出不得使用 Markdown 加粗语法。
- 全流程不调用用户交互能力，不创建问题队列，不直接向用户提问，不暂停主流程。
