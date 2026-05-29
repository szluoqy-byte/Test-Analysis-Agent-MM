# 示例回归矩阵

本文件用于规划 Test Analysis Agent 的回归样例。每个样例都应包含输入需求，以及 `examples/outputs/runs/<stem>-run/` 下固定命名的测试分析方案，并通过 `bin/smoke-test-analysis.py`。

## 当前样例

| 样例 | 需求文件 | 固定 run 目录 | 覆盖重点 |
|---|---|---|---|
| 订单取消 | `examples/requirements/sample-requirement.md` | `examples/outputs/runs/sample-requirement-run/` | 状态、权限、幂等、数据一致性、预期结果兜底 |
| 限时优惠与订单支付 | `examples/requirements/complex-promotion-requirement.md` | `examples/outputs/runs/complex-promotion-requirement-run/` | 时间边界、库存、金额门槛、组合规则、支付幂等、接口契约 |

## 验收

- 测试分析方案通过 `bin/lint-test-analysis-solution.py`。
- 主输出按 `测试场景 -> 测试点 -> 测试点明细` 组织。
- 每个测试点明细包含预期结果。
- 需求或设计未说明错误提示、状态变化或错误码时，预期结果写 `待人工分析确认`。
- 不输出完整测试用例、测试步骤、执行数据清单或自动化脚本。
