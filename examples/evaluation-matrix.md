# 示例评测矩阵

本文件用于规划 Testcase Title Outline Agent 的回归样例。每个样例都应包含输入需求，以及 `examples/outputs/runs/<stem>-run/` 下固定命名的测试用例标题大纲，并通过 `bin/smoke-test-analysis.py`。

## 已覆盖样例

| 样例 | 主要能力 | 状态 |
|---|---|---|
| `sample-requirement.md` | 状态迁移、权限矩阵、数据一致性、接口契约、待确认问题 | 已覆盖，固定 run：`examples/outputs/runs/sample-requirement-run/` |
| `complex-promotion-requirement.md` | 边界值、等价类、决策表、状态迁移、权限矩阵、接口契约、数据一致性、组合兼容、风险驱动 | 已覆盖，固定 run：`examples/outputs/runs/complex-promotion-requirement-run/` |

## 待补充样例

| 样例方向 | 必须覆盖的方法 | 目标风险 |
|---|---|---|
| 审批流和撤回 | 状态迁移、权限矩阵、场景流 | 非法迁移、越权审批、终态修改 |
| 批量导入和部分失败 | 边界值、等价类、数据一致性、错误推测 | 批量上限、重复数据、部分成功回滚 |
| 多租户数据隔离 | 权限矩阵、数据一致性、安全风控 | 跨租户访问、数据泄露、权限缓存 |
| 外部系统回调 | 接口契约、状态迁移、数据一致性 | 重复回调、乱序回调、超时补偿 |
| 配置开关灰度发布 | 组合兼容、场景流、风险驱动 | 新老版本差异、开关回滚、降级行为 |

## 样例验收

- 测试用例标题大纲通过 `bin/lint-testcase-title-outline.py`。
- 主输出按 `测试场景 -> 测试点 -> 测试用例标题项` 组织。
- 每个标题项包含输入条件与数据依赖、判定关注和待确认信息。
- 主输出不包含前置步骤、测试步骤、完整预期结果或自动化脚本。
- Runtime wiring 通过 `bin/validate-agent-runtime.py`。
