# Test Eval Agent 设计草案

本文档保留为未来测试评估 Agent 的设计草案。当前主链路采用：

```text
分析：SC 场景树 -> TP 测试点
设计：SC 场景树 -> TP 测试点 -> TC 测试用例
```

## 评估对象

| 产物 | 评估重点 |
|---|---|
| `deliverables/test-analysis-solution.json` | 场景树是否合理、测试点是否覆盖需求事实和风险 |
| `deliverables/test-design-solution.json` | 每个测试点是否形成覆盖适用测试设计因子的最小充分 TC 集合，测试数据、步骤和预期是否可执行且有依据 |
| `reports/*review.json` | 语义评审问题是否可定位、建议是否可执行 |
| `reports/analysis-coverage-review.json` / `reports/design-coverage-review.json` | 需求到测试点、测试点到测试用例的覆盖关系是否闭环 |

## 典型问题

| 类型 | 示例 |
|---|---|
| 场景遗漏 | 需求存在客服审核流程，但分析方案未出现可对应场景或测试点 |
| 测试点弱覆盖 | 高风险规则只在 E2E 中泛化出现，没有独立测试点 |
| 用例弱覆盖 | 边界、等价类、状态组合或权限组合没有代表性 TC |
| 承接错误 | 设计方案改写了分析方案中的场景树或测试点 |
| 依据不足 | TC 写了输入未说明的错误码、提示文案、状态值或阈值 |

评估不替代 deterministic lint。
