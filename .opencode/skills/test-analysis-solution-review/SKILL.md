---
name: test-analysis-solution-review
description: 在分析链路中分段评审冻结 SC 树、TP 切片和最终 schema 2.0 测试分析方案的语义质量。
---

# 测试分析方案语义评审

本 skill 是 `test-analysis-agent` 的语义评审环节。结构、编号、JSON canonical 结构和 Markdown 语法以确定性脚本为准；本 skill 只评审语义质量。它在同一个 skill 内承担三类评审：SC 树评审、TP 切片评审和最终分析方案评审。

## 输入

- `process/scenario-tree.json`，用于 SC 树评审。
- `process/test-point-slices/<SC-ID>.json`，用于单个叶子 SC 的 TP 切片评审。
- `outputs/runs/<run-id>/deliverables/test-analysis-solution.json`，用于最终整体评审。
- `bin/lint-run-json.py`、`bin/render-run-markdown.py --check` 和 `bin/lint-test-analysis-solution.py` 的执行结果
- `process/input-fact-model.json`
- `process/rules-pack.json`
- `process/context-pack.json`
- 目标评审 JSON 内的 `generationContext`；缺失时先运行 `bin/init-report-artifact.py`
- `knowledge/test-analysis-solution-standard.md`

## 评审重点

| 维度 | 检查内容 |
|---|---|
| SC 树冻结 | `process/scenario-tree.json` 是否覆盖输入范围、分层是否表达真实业务路径、叶子粒度是否合适、是否混入 TP/TC 粒度 |
| 场景树 | 最终分析方案中的 SC 是否与已评审 `process/scenario-tree.json` 保持一致，是否只有叶子场景挂测试点 |
| 测试点粒度 | TP 是否是验证目标，而不是具体用例、数据值或操作步骤 |
| E2E 覆盖 | 每个叶子场景是否有独立 E2E 测试点，且不把所有规则都塞进 E2E |
| 接口组织 | 接口/API 明确时，TP 是否定位到接口、端点、消息、回调或集成点 |
| 覆盖完整性 | 需求事实、设计事实和高风险点是否有测试点承接 |
| 依据质量 | basisRefs 是否能支撑测试点 |
| Rules 应用 | 是否从 `process/rules-pack.json` 的 `ruleSources[]` 筛选并读取了适用 rules 正文，是否已遵守，冲突时是否说明规则覆盖输入的原因 |
| 动态来源 | 可见 project/personal 来源是否被读取、应用或解释不适用 |
| 分析边界 | 是否提前生成 TC、步骤、测试数据或预期结果 |

## 输出

SC 树评审写入 `reports/scenario-tree-review.json`；TP 切片评审写入 `reports/test-point-reviews/<SC-ID>.json`，汇总可写入 `reports/test-point-review.json`；最终分析方案评审写入 `reports/test-analysis-solution-review.json`。报告必须先由 `bin/init-report-artifact.py` 生成 skeleton 和 `generationContext`，AI 只填写语义结论字段；如需人读版，由 `bin/render-run-markdown.py` 渲染。
