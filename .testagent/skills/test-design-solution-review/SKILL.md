---
name: test-design-solution-review
description: 在确定性 lint 通过后，评审 schema 2.0 测试设计方案的 TC 粒度、步骤可执行性、测试数据明确性、预期依据和分析方案承接。
---

# 测试设计方案语义评审

本 skill 是 `test-design-agent` 的产物级语义评审环节。结构、编号、JSON canonical 结构和 Markdown 语法以确定性脚本为准；本 skill 只评审语义质量。

## 输入

- `outputs/runs/<run-id>/deliverables/test-design-solution.json`
- `outputs/runs/<run-id>/deliverables/test-analysis-solution.json`
- `bin/lint-run-json.py`、`bin/render-run-markdown.py --check` 和 `bin/lint-test-design-solution.py` 的执行结果
- 归一化后的需求 Markdown 和可选设计方案 Markdown
- `process/context-pack.json`
- `knowledge/test-design-solution-standard.md`

## 评审重点

| 维度 | 检查内容 |
|---|---|
| 分析承接 | 设计方案是否完整继承 SC/TP，不新增、删除、合并或改写分析层级 |
| 用例覆盖 | 每个 TP 是否至少有一个 TC，关键规则是否有代表性 TC |
| 用例粒度 | TC 是否具体到可执行实例，而不是抽象条件标签；是否把多个独立输入条件、数据组合、等价类、边界点、角色、权限、状态、配置、外部依赖返回、消息顺序或异常类型合并进一个 TC |
| 用例级别 | `level` 是否符合 `Level 0` 到 `Level 4` 定义，是否与失败后果、风险和覆盖优先级匹配 |
| 测试数据 | `testData[]` 是否给出具体值或稳定数据槽位，并说明含义 |
| 步骤可执行性 | `steps[]` 是否按顺序表达同一个测试实例内由用户、测试人员、外部调用方或测试工具执行的动作和步骤预期，而不是枚举多个互斥请求、多组替代数据、多种角色/状态/配置切换或多条独立路径；`action` 是否只写可执行动作或取数动作，没有把检查项、断言项、观察结论或系统内部行为单独写成步骤 |
| 最终预期 | `expectedResult` 是否有需求、设计、规则或分析方案依据 |
| 接口表达 | 接口类用例是否拆成字段片段，避免完整裸 URL |
| 动态来源 | 可见 project/personal 来源是否被读取、应用或解释不适用 |

## 输出

评审输出写入 `reports/test-design-solution-review.json`，结构以 `templates/review-report-json-template.json` 为准；如需人读版，由 `bin/render-run-markdown.py` 渲染。
