---
name: coverage-review
description: 对测试分析/测试设计运行结果执行覆盖审查，检查需求到 TP、TP 到 TC 的覆盖关系、rules-pack 和动态 project/personal 来源应用状态，并输出结构化 coverage-review JSON。
---

# 覆盖审查

本 skill 是测试分析与测试设计链路的覆盖收口环节。它读取 JSON canonical、确定性 lint 结果、独立评审结果、`process/rules-pack.json` 中当前阶段可见的规则索引及对应 Markdown 正文、动态来源应用状态和必要的私有参考。测试分析输出 `reports/analysis-coverage-review.json`；测试设计输出 `reports/design-coverage-review.json`。历史 `reports/coverage-review.json` 只作为兼容读取路径，不作为新流程写入目标。

coverage-review 是过程门禁；发现缺口时通过 `coverageGaps[]` 触发切片返工。最终人审展示由 `final-report-generation` 负责，输出 `reports/analysis-final-report.json` 或 `reports/design-final-report.json`，不在本 skill 中生成。

## 必读输入

- `process/input-fact-model.json`
- `process/scenario-tree.json`
- `process/test-point-work-items.json`
- 可选 `process/test-case-work-items.json`
- `process/rules-pack.json`
- `process/context-pack.json`
- `deliverables/test-analysis-solution.json`
- 可选 `deliverables/test-design-solution.json`
- `reports/test-analysis-solution-review.json`
- 可选 `reports/test-design-solution-review.json`
- 当前 coverage JSON 内的 `generationContext`；缺失时先运行 `bin/init-report-artifact.py`
- `skills/coverage-review/references/coverage-check.md`
- `skills/coverage-review/references/review-gates.md`
- `skills/coverage-review/references/context-application-gates.md`

## 审查步骤

1. 确认 coverage JSON 已由 `bin/init-report-artifact.py` 初始化 skeleton 和 `generationContext`；缺失时先初始化，不手工拼写。
2. 确认 deterministic lint 已通过；未通过时直接输出需修正。
3. 优先读取 `generationContext.applicableRules[]` 中已内联的 coverage-review 适用 rules 正文，并检查 rules 与动态来源应用状态。
4. 检查需求事实、设计事实和高风险点是否能追踪到已冻结 `SC-*`，以及叶子 SC 是否都有 TP 切片承接。
5. 检查每个叶子 SC 是否至少有一个 `E2E场景测试`，且非 E2E TP 没有重复泛化主流程闭环。
6. 如果存在测试设计方案，检查每个 `TP-*` 是否有 TC 工作项和 TC 切片承接；`至少一个 TC` 只是最低结构门槛，还必须检查该 TP 下是否形成覆盖适用测试设计因子的最小充分 TC 集合。
7. 检查 TC 的测试数据、步骤和最终预期是否有依据。
8. 输出结构化 findings、blockingIssues、recommendations、evidenceRefs、qualityGates 和 coverageGaps。
9. 对需要返工的 `coverageGaps[]`，`artifactLocation` 必须优先定位到可编辑 canonical slice：分析缺口写 `process/test-point-slices/<SC-ID>.json`，设计缺口写 `process/test-case-slices/<TP-ID>.json`；`suggestedFix` 必须说明回到对应 slice 修复、重新 slice review、脚本合并、最终 review、coverage 和一致性检查。

## 输出

输出按当前阶段写入 `reports/analysis-coverage-review.json` 或 `reports/design-coverage-review.json`，结构以 `templates/coverage-review-json-template.json` 为准；如需人读版，由 `bin/render-run-markdown.py` 渲染。

coverage-review 不重复执行 deterministic lint 已覆盖的编号、字段、Markdown 语法和 JSON 结构检查。

coverage-review 不直接修改主交付件。发现覆盖缺口时，只输出结构化返工位置和建议；对应 workflow 必须先运行 `bin/apply-coverage-gaps.py` 重开工作项，再回到切片产物修复后合并。
