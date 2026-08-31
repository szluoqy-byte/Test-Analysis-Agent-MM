# Review Gates

## 必选门禁

- deterministic lint 已通过。
- scenario-tree、TP/TC 切片、review 和 coverage 均为可直接审阅的 Markdown，且没有同名过程 JSON。
- `process/scenario-tree.md` 已通过 SC 树校验，且只包含 SC 层级和依据，不包含 TP/TC。
- `process/test-point-work-items.json` 中每个叶子 SC 工作项已完成并有 TP 切片。
- 如存在测试设计方案，`process/test-case-work-items.json` 中每个 TP 工作项已完成并有 TC 切片。
- `test-analysis-solution.json` 使用 schema `2.0`，且只包含 SC/TP。
- `test-design-solution.json` 使用 schema `2.0`，且在 TP 下生成 TC。
- 选中测试技术只作为覆盖参考，不要求在主交付件中逐项体现。
- 每个适用分析维度应体现在有依据的场景、测试点、测试用例或不适用说明中。
- 动态来源被读取后必须记录应用状态。

## 失败门禁

- 分析方案提前输出测试用例、步骤、测试数据或预期。
- TP 切片阶段新增、删除、合并或改写了已冻结 SC。
- TC 切片阶段新增、删除、合并或改写了已冻结 SC/TP。
- 设计方案缺少 TC 或 TC 缺少步骤、测试数据、最终预期。
- 结构化过程记录中的方法参考结论与主交付件明显冲突。
- 设计方案改写了分析方案中的场景树或测试点。
- coverage 发现缺口后未使用 `bin/reopen-run-items.py` 重开对应工作项，或绕过过程切片直接手改结果 JSON。
