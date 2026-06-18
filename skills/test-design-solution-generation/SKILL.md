---
name: test-design-solution-generation
description: 基于已评审测试分析方案、需求/设计依据和可见动态来源，生成 schema 2.0 的 SC/TP/TC 测试设计方案。
---

# 测试设计方案生成

本 skill 负责生成 `deliverables/test-design-solution.json`。它继承测试分析方案中的 `SC-*` 场景树和 `TP-*` 测试点，并在每个测试点下生成完整步骤级 `TC-*` 测试用例。

## 必读上下文

- `deliverables/test-analysis-solution.json`
- 归一化后的需求 Markdown 和可选设计方案 Markdown
- `process/context-pack.json`
- `knowledge/test-design-solution-standard.md`
- `templates/test-design-solution-json-template.json`
- 对本阶段可见的 project/personal 动态来源

## 生成原则

1. 完整继承分析方案的 `SC-*` 场景树和 `TP-*` 测试点，不新增、删除、合并或改写分析层级。
2. 每个 `TP-*` 至少生成 1 个 `TC-*`。
3. `TC-*` 全局连续编号，不按场景或测试点重置。
4. TC 必须具体到可执行实例：明确前置条件、测试数据、操作步骤、步骤预期和最终预期。
5. `testData[]` 使用 `{name, value, description}` 数组，必须给出具体值或稳定数据槽位。
6. `steps[]` 使用 `{stepNo, action, expected}` 数组，`stepNo` 从 1 连续。
7. `expectedResult` 只能来自当前用户明确指令、适用 rules、需求、设计方案、分析方案或可直接推出的业务不变量。
8. 依据不足时使用保守预期，例如“请求被拒绝，系统不产生成功态数据变更”，不补写未说明的错误码、提示文案或状态值。
9. 接口类用例不得写完整裸 URL；拆成 `接口=METHOD /path`、`参数名=参数值`、`响应状态=...` 等字段片段。

## JSON 结构

主输出必须写入：

```text
outputs/runs/<run-id>/deliverables/test-design-solution.json
```

结构要求：

- `artifactType`: `test-design-solution`
- `schemaVersion`: `2.0`
- `inputs[]`: 设计输入说明
- `scenarios[]`: 继承分析方案场景树
- 叶子场景的 `testPoints[]` 继承 `id`、`title`、`objective`、`basisRefs[]`
- 每个测试点下生成 `testCases[]`

每个 TC 必须包含：

- `id`
- `title`
- `preconditions[]`
- `testData[]`
- `steps[]`
- `expectedResult`
- `sourceRefs[]`

## 禁止项

- 不手工写 Markdown、CSV、平台导入文件或其他派生表达格式。
- 不写 schemaVersion 2.0 之外的字段。
- 不输出自动化脚本或真实生产数据。
- 派生表达由 `test-case-writing` 读取 canonical JSON 后生成。
