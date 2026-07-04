---
name: coverage-review
description: 对测试分析/测试设计运行结果执行覆盖审查，检查需求到 TP、TP 到 TC 的覆盖关系、rules-pack 和动态 project/personal 来源应用状态，并输出结构化 coverage-review JSON。
---

# 覆盖审查

本 skill 是测试分析与测试设计链路的覆盖收口环节。它读取 JSON canonical、确定性 lint 结果、独立评审结果、`process/rules-pack.json` 中当前阶段可见的规则索引及对应 Markdown 正文、动态来源应用状态和必要的私有参考。测试分析输出 `process/reviews/analysis-coverage-review.json`；测试设计输出 `process/reviews/design-coverage-review.json`，不作为新流程写入目标。

coverage-review 是过程门禁；发现缺口时通过 `coverageGaps[]` 触发切片返工。最终人审展示由 `final-report-generation` 负责，输出 `reports/analysis-final-report.json` 或 `reports/design-final-report.json`，不在本 skill 中生成。

coverage-review 必须基于对应范围的 FACT 覆盖证据图执行门禁：测试分析读取 `process/analysis-fact-coverage-map.json`，测试设计读取 `process/design-fact-coverage-map.json`。覆盖证据图是过程件，不是最终报告；它把每条 FACT 到叶子 SC、TP、TC 的候选覆盖链路列清楚，coverage-review 再判断这些链路是否充分。不得等到 final-report 阶段才新增 `missing` 判断。

## 必读输入

- `process/input-fact-model.json`
- `process/scenario-tree.json`
- `process/test-point-work-items.json`
- 可选 `process/test-case-work-items.json`
- `process/analysis-fact-coverage-map.json` 或 `process/design-fact-coverage-map.json`
- `process/rules-pack.json`
- `process/context-pack.json`
- `deliverables/test-analysis-solution.json`
- 可选 `deliverables/test-design-solution.json`
- `process/reviews/test-analysis-solution-review.json`
- 可选 `process/reviews/test-design-solution-review.json`
- 当前 coverage JSON 内的 `generationContext`；缺失时先运行 `bin/init-report-artifact.py`
- `skills/coverage-review/references/coverage-check.md`
- `skills/coverage-review/references/review-gates.md`
- `skills/coverage-review/references/context-application-gates.md`

## 审查步骤

1. 确认 coverage JSON 已由 `bin/init-report-artifact.py` 初始化 skeleton 和 `generationContext`；缺失时先初始化，不手工拼写。
2. 确认 deterministic lint 已通过；未通过时直接输出需修正。
3. 优先读取 `generationContext.applicableRules[]` 中已内联的 coverage-review 适用 rules 正文，并检查 rules 与动态来源应用状态。
4. 读取 `process/<scope>-fact-coverage-map.json`，逐条 FACT 审查 `coverageTree[]` 是否真实、充分、有依据。
5. 检查需求事实、设计事实和高风险点是否能追踪到已冻结 `SC-*`，以及叶子 SC 是否都有 TP 切片承接。
6. 检查每个叶子 SC 是否至少有一个 `E2E场景测试`，且非 E2E TP 没有重复泛化主流程闭环。
7. 如果存在测试设计方案，检查每个 `TP-*` 是否有 TC 工作项和 TC 切片承接；`至少一个 TC` 只是最低结构门槛，还必须检查该 TP 下是否形成覆盖适用测试设计因子的最小充分 TC 集合。
8. 检查 TC 的测试数据、步骤和最终预期是否有依据。
9. 输出结构化 findings、blockingIssues、recommendations、evidenceRefs、qualityGates 和 coverageGaps。
10. 对覆盖证据图中 `coverageStatus=gap` 的 FACT，必须输出对应 `coverageGaps[]`，除非能明确改为 `not_applicable` 并写明原因。对 `coverageStatus=partial` 的 FACT，必须判断是否需要返工；需要返工时输出 `coverageGaps[]`，不需要返工时在 findings/recommendations 中说明保留原因。
11. 对需要返工的 `coverageGaps[]`，`artifactLocation` 必须优先定位到可编辑 canonical slice：分析缺口写 `process/test-point-slices/<SC-ID>.json`，设计缺口写 `process/test-case-slices/<TP-ID>.json`；`suggestedFix` 必须说明回到对应 slice 修复、重新 slice review、脚本合并、最终 review、coverage 和一致性检查。

## 输出

输出按当前阶段写入 `process/reviews/analysis-coverage-review.json` 或 `process/reviews/design-coverage-review.json`，结构以 `templates/coverage-review-json-template.json` 为准；如需人读版，由 `bin/render-run-markdown.py` 渲染。

coverage-review 不重复执行 deterministic lint 已覆盖的编号、字段、Markdown 语法和 JSON 结构检查。

coverage-review 可以修改对应的 `process/<scope>-fact-coverage-map.json` 覆盖状态和原因，但不直接修改主交付件。发现覆盖缺口时，只输出结构化返工位置和建议；对应 workflow 必须先运行 `bin/apply-coverage-gaps.py` 重开工作项，再回到切片产物修复后合并。返工合并后，必须重新运行 `bin/build-fact-coverage-map.py` 刷新覆盖证据图，再重新执行 coverage-review。
