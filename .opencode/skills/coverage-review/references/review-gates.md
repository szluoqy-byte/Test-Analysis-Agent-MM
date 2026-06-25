# Review Gates

## 必选门禁

- deterministic lint 已通过。
- scenario-tree、TP/TC 切片和 review/coverage JSON 已包含固定脚本生成的 `generationContext`。
- `process/scenario-tree.json` 已通过 SC 树校验，且不包含 `testPoints[]`。
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
- coverage 发现缺口后未先运行 `bin/apply-coverage-gaps.py` 重开对应工作项，或直接编辑最终 Markdown / 绕过切片脚本手改主交付件。
