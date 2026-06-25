---
name: test-analysis-solution-generation
description: 基于输入事实模型、测试技术路由参考、专项方法候选和可见动态来源，先生成冻结 SC 场景树，再按叶子 SC 生成 TP 切片并合并为 schema 2.0 测试分析方案。
---

# 测试分析方案生成

本 skill 负责分析生成阶段，但不再一次性生成完整 SC+TP。它先生成 `process/scenario-tree.json` 冻结 SC 树，再按每个叶子 SC 填写 `process/test-point-slices/<SC-ID>.json`，最后通过固定脚本合并为 `deliverables/test-analysis-solution.json`。它不输出测试用例、测试数据、步骤或预期结果。

## 必读上下文

- `process/input-fact-model.json`
- `process/rules-pack.json`
- `process/context-pack.json`
- 测试技术路由结果与专项方法候选
- `knowledge/test-analysis-solution-standard.md`
- `knowledge/testpoint-standard.md`
- `process/scenario-tree.json`
- `process/test-point-work-items.json`
- `process/test-point-slices/<SC-ID>.json`
- 当前 `process/scenario-tree.json` 或切片 JSON 内的 `generationContext`
- `templates/test-analysis-solution-json-template.json`
- 对本阶段可见的 project/personal 动态来源

## 生成原则

1. 每个内部阶段开始前，必须先确认目标 JSON 已由固定脚本写入 `generationContext`；若缺失，先运行 `bin/init-scenario-tree.py`、`bin/init-test-point-slice.py` 或 `bin/build-generation-context.py` 生成，不手工拼写。
2. 优先读取 `generationContext.applicableRules[]` 中已内联的本阶段 rules 正文；这些 rules 是强制约束。
3. 按 `generationContext.visibleSources[]` 判断本阶段可见动态来源；只读取与 SC 建模或 TP 生成有关的正文，并在过程产物或 review/coverage 中记录应用状态。
4. 使用 `generationContext.relevantFacts[]` 作为当前工作单元的优先事实候选；如候选不足，可回读 `process/input-fact-model.json` 和输入 Markdown，但不得跳出当前 SC/TP 工作边界。
5. SC 阶段只从需求目标、业务流程、角色、状态、接口、数据对象和风险中组织 `SC-*` 场景树，写入 `process/scenario-tree.json`。
6. `process/scenario-tree.json` 的场景最多 3 层，任何 SC 节点都不得包含 `testPoints[]`、测试用例、步骤、测试数据或预期结果。
7. SC review 通过后视为冻结；TP 阶段不得新增、删除、合并或改写 SC ID、标题、层级或字段。
8. 运行固定脚本生成 `process/test-point-work-items.json`，每个叶子 SC 对应一个 TP 切片。
9. 每个 `process/test-point-slices/<SC-ID>.json` 只填写当前叶子 SC 的 `scenario.testPoints[]`。
10. 每个叶子场景必须包含一个 `E2E场景测试` 测试点。
11. `TP-*` 最终由 `bin/merge-test-point-slice.py` 全局连续编号，不按场景重置；切片内不得依赖局部编号作为事实。
12. `TP-*` 是验证目标，不是具体测试用例标题；它表达规则、路径、状态、权限、接口契约或风险。
13. 接口类场景下的非 E2E `TP-*` 应先定位接口、端点、消息、回调或集成点，再表达契约关注点。
14. 不输出 `expectedResult`。具体预期属于设计阶段 TC。
15. 不输出具体数据值、操作步骤、测试脚本、自动化代码或真实生产数据。
16. 如果输入不足，只生成输入可支持的 SC/TP，不编造错误码、提示文案、状态值或阈值；rules 与输入文档冲突时，默认遵守 rules 并在 basisRefs 或 note 中记录覆盖原因。
17. 测试技术和专项方法只作为生成参考，用于启发覆盖维度和风险视角；最终 TP 不必逐项映射方法，也不得为了贴合某个方法而牺牲输入事实支持。

## JSON 结构

SC 阶段输出：

```text
outputs/runs/<run-id>/process/scenario-tree.json
```

TP 阶段输出：

```text
outputs/runs/<run-id>/process/test-point-slices/<SC-ID>.json
```

最终主输出由 `bin/merge-test-point-slice.py` 合并写入：

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

- 不在 `process/scenario-tree.json` 中写 `testPoints[]`。
- 不删除或手工伪造 `generationContext`；上下文缺失或过期时运行固定脚本刷新。
- 不在 TP 切片阶段改写 SC。
- 不写 `TC-*`。
- 不写 schemaVersion 2.0 之外的字段或 `testCases`。
- 不写 `expectedResult`、`preconditions`、`testData`、`steps`。
- 不把测试技术名称直接塞进测试点标题。
- 不把“功能正常”“异常流程”这类空泛词作为测试点主体。
- 不手工写 Markdown；由 `bin/render-run-markdown.py` 渲染。
