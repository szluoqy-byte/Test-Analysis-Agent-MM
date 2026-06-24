---
name: test-analysis-solution-generation
description: 基于输入事实模型、测试技术路由参考、专项方法候选和可见动态来源，生成 schema 2.0 的 SC 场景树与 TP 测试点测试分析方案。
---

# 测试分析方案生成

本 skill 负责生成 `deliverables/test-analysis-solution.json`。它只输出 `SC-*` 场景树和 `TP-*` 测试点，不输出测试用例、测试数据、步骤或预期结果。

## 必读上下文

- `process/input-fact-model.json`
- `process/rules-pack.json`
- `process/context-pack.json`
- 测试技术路由结果与专项方法候选
- `knowledge/test-analysis-solution-standard.md`
- `knowledge/testpoint-standard.md`
- `templates/test-analysis-solution-json-template.json`
- 对本阶段可见的 project/personal 动态来源

## 生成原则

1. 从需求目标、业务流程、角色、状态、接口、数据对象和风险中组织 `SC-*` 场景树。
2. 生成前先筛选 `process/rules-pack.json` 的 `ruleSources[]` 中 `availableStages` 包含 `test-analysis-solution-generation` 或 `"*"` 的 rules，并读取对应 `path` 的 Markdown 正文；SC/TP 组织、覆盖策略、禁止项和命名口径必须遵守适用 rules。
3. `SC-*` 最多 3 层。非叶子场景只做业务路径分组，不挂测试点；只有叶子场景挂 `testPoints[]`。
4. 每个叶子场景必须包含一个 `E2E场景测试` 测试点。
5. `TP-*` 全局连续编号，不按场景重置。
6. `TP-*` 是验证目标，不是具体测试用例标题；它表达规则、路径、状态、权限、接口契约或风险。
7. 接口类场景下的非 E2E `TP-*` 应先定位接口、端点、消息、回调或集成点，再表达契约关注点。
8. 不输出 `expectedResult`。具体预期属于设计阶段 TC。
9. 不输出具体数据值、操作步骤、测试脚本、自动化代码或真实生产数据。
10. 如果输入不足，只生成输入可支持的测试点，不编造错误码、提示文案、状态值或阈值；rules 与输入文档冲突时，默认遵守 rules 并在 basisRefs 或 note 中记录覆盖原因。
11. 测试技术和专项方法只作为生成参考，用于启发覆盖维度和风险视角；最终 TP 不必逐项映射方法，也不得为了贴合某个方法而牺牲输入事实支持。

## JSON 结构

主输出必须写入：

```text
outputs/runs/<run-id>/deliverables/test-analysis-solution.json
```

结构要求：

- `artifactType`: `test-analysis-solution`
- `schemaVersion`: `2.0`
- `scope[]`: 需求范围说明
- `scenarios[]`: 场景树
- 叶子场景的 `testPoints[]` 每项包含：
  - `id`
  - `title`
  - `objective`
  - `basisRefs[]`
  - 可选 `note`

## 禁止项

- 不写 `TC-*`。
- 不写 schemaVersion 2.0 之外的字段或 `testCases`。
- 不写 `expectedResult`、`preconditions`、`testData`、`steps`。
- 不把测试技术名称直接塞进测试点标题。
- 不把“功能正常”“异常流程”这类空泛词作为测试点主体。
- 不手工写 Markdown；由 `bin/render-run-markdown.py` 渲染。
