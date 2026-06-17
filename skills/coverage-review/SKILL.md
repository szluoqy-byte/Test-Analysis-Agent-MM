---
name: coverage-review
description: 对测试分析/测试设计运行结果执行覆盖审查，检查需求到 TP、TP 到 TC 的覆盖关系、测试方法应用、core rules 和动态 project/personal 来源应用状态，并输出结构化 coverage-review JSON。
---

# 覆盖审查

本 skill 是测试分析与测试设计链路的覆盖收口环节。它读取 JSON canonical、确定性 lint 结果、独立评审结果、core rules、动态来源应用状态和必要的私有参考，输出 `reports/coverage-review.json`。

## 必读输入

- `process/input-fact-model.json`
- `process/context-pack.json`
- `deliverables/test-analysis-solution.json`
- 可选 `deliverables/test-design-solution.json`
- `reports/test-analysis-solution-review.json`
- 可选 `reports/test-design-solution-review.json`
- `skills/coverage-review/references/coverage-check.md`
- `skills/coverage-review/references/review-gates.md`
- `skills/coverage-review/references/context-application-gates.md`

## 审查步骤

1. 确认 deterministic lint 已通过；未通过时直接输出需修正。
2. 检查需求事实、设计事实、方法证据和高风险点是否能追踪到 `SC-*` 或 `TP-*`。
3. 如果存在测试设计方案，检查每个 `TP-*` 是否至少有一个 `TC-*` 承接。
4. 检查 TC 的测试数据、步骤和最终预期是否有依据。
5. 检查 core rules 与动态来源应用状态。
6. 输出结构化 findings、blockingIssues、recommendations、evidenceRefs、qualityGates 和 coverageGaps。

## 输出

输出写入 `reports/coverage-review.json`，结构以 `templates/coverage-review-json-template.json` 为准；如需人读版，由 `bin/render-run-markdown.py` 渲染。

coverage-review 不重复执行 deterministic lint 已覆盖的编号、字段、Markdown 语法和 JSON 结构检查。
