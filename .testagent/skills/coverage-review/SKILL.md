---
name: coverage-review
description: 对测试分析/测试设计运行结果执行覆盖审查，检查需求到 TP、TP 到 TC 的覆盖关系、rules-pack 和动态 project/personal 来源应用状态，并输出结构化 coverage-review JSON。
---

# 覆盖审查

本 skill 是测试分析与测试设计链路的覆盖收口环节。它读取 JSON canonical、确定性 lint 结果、独立评审结果、`process/rules-pack.json` 中当前阶段可见的规则索引及对应 Markdown 正文、动态来源应用状态和必要的私有参考。测试分析输出 `process/reviews/analysis-coverage-review.json`；测试设计输出 `process/reviews/design-coverage-review.json`，不作为新流程写入目标。

coverage-review 是过程门禁；发现缺口时通过 `coverageGaps[]` 触发切片返工。最终人审展示由 `final-report-generation` 负责，输出 `reports/analysis-final-report.json` 或 `reports/design-final-report.json`，不在本 skill 中生成。

coverage-review 必须基于对应范围的 FACT 覆盖证据图执行门禁：测试分析读取 `process/analysis-fact-coverage-map.json`，测试设计读取 `process/design-fact-coverage-map.json`。覆盖证据图是过程件，不是最终报告；它把每条 FACT 到叶子 SC、TP、TC 的候选覆盖链路列清楚，coverage-review 再判断这些链路是否充分。不得等到 final-report 阶段才新增 `missing` 判断。

## 何时使用

在分析或设计主交付件已经完成确定性校验、Markdown 渲染和最终语义评审后使用。不要把本 skill 用作最终人审报告生成器；最终展示交给 `final-report-generation`。

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
- `references/coverage-check.md`
- `references/review-gates.md`
- `references/context-application-gates.md`

## 审查阶段

- [ ] Step 1: 初始化 coverage 审查工作包
- [ ] Step 2: 确认前置确定性校验和最终语义评审已完成
- [ ] Step 3: 读取并审查 FACT 覆盖证据图
- [ ] Step 4: 检查场景、测试点和测试用例覆盖充分性
- [ ] Step 5: 输出结构化审查结论
- [ ] Step 6: 为需要返工的缺口定位 canonical slice
- [ ] Step 7: 校验 coverage 审查产物并交回 workflow 收口

> 本节是本 skill 的静态执行契约，不记录 run 的真实状态；真实状态以 `process/*-task-list.json` 为准。

## 易错点

- 不要等 final-report 阶段才判断 missing；missing/gap 必须先在覆盖证据图和 coverage-review 中形成。
- 不要把 `coverageGaps[].artifactLocation` 指向最终 Markdown；必须指向可编辑 canonical slice。
- 不要重复 deterministic lint 的字段、编号和 Markdown 漂移检查。

## 各阶段执行要求

### Step 1: 初始化 coverage 审查工作包

- 确认 coverage JSON 已由 `bin/init-report-artifact.py` 初始化 skeleton 和 `generationContext`；缺失时先初始化，不手工拼写。

### Step 2: 确认前置确定性校验和最终语义评审已完成

- 确认 deterministic lint、Markdown render 和最终语义 review 已通过；未通过时停止 coverage 审查并返回需修正项。
- 优先读取 `generationContext.applicableRules[]` 中已内联的 coverage-review 适用 rules 正文，并检查 rules 与动态来源应用状态。

### Step 3: 读取并审查 FACT 覆盖证据图

- 读取 `process/<scope>-fact-coverage-map.json`，逐条 FACT 审查 `coverageTree[]` 是否真实、充分、有依据。
- 只编辑脚本已生成的 `factCoverage[]` 行中的 `coverageTree[]`、`coverageStatus` 和 `coverageReason`，不得新增、删除、合并或重编号 FACT。`coverageStatus` 只能为 `covered`、`partial`、`gap` 或 `not_applicable`，不要写 `missing`。
- `coverageTree[]` 固定为 `{leafScenarioId, testPoints:[{testPointId, testCases:[]}]}` 层级；analysis 覆盖图的 `testCases[]` 必须为空，design 覆盖图中 `coverageStatus=covered` 时必须至少关联一个 `TC-*`。`gap` 或 `not_applicable` 时 `coverageTree[]` 必须为空，并在 `coverageReason` 写明原因。

### Step 4: 检查场景、测试点和测试用例覆盖充分性

- 检查需求事实、设计事实和高风险点是否能追踪到已冻结 `SC-*`，以及叶子 SC 是否都有 TP 切片承接。
- 检查每个叶子 SC 是否至少有一个 `E2E场景测试`，且非 E2E TP 没有重复泛化主流程闭环。
- 如果存在测试设计方案，检查每个 `TP-*` 是否有 TC 工作项和 TC 切片承接；`至少一个 TC` 只是最低结构门槛，还必须检查该 TP 下是否形成覆盖适用测试设计因子的最小充分 TC 集合。已加载来源中的既有测试设计因子不是封闭上限，coverage-review 应识别只覆盖因子库/checklist 条目但遗漏 TP 目标下必要测试实例的问题。
- 检查 TC 的测试数据、步骤和最终预期是否有依据。

### Step 5: 输出结构化审查结论

- 输出 findings、blockingIssues、recommendations、evidenceRefs、qualityGates 和 coverageGaps；`result` 只能为 `通过`、`需修正`、`失败`、`警告` 或 `不适用`，这些集合字段必须保留为数组。
- 对 `coverageStatus=gap` 的 FACT，必须输出对应 `coverageGaps[]`，除非能明确改为 `not_applicable` 并写明原因；对 `partial` 必须判断是否需要返工，并说明保留原因或输出 gap。

### Step 6: 为需要返工的缺口定位 canonical slice

- `coverageGaps[].artifactLocation` 必须定位到可编辑 canonical slice：分析缺口写 `process/test-point-slices/<SC-ID>.json`，设计缺口写 `process/test-case-slices/<TP-ID>.json`。
- `suggestedFix` 必须说明回到对应 slice 修复、重新 slice review、脚本合并、最终 review、coverage 和一致性检查。

### Step 7: 校验 coverage 审查产物并交回 workflow 收口

- 输出 coverage JSON 后运行 `python bin/lint-run-json.py outputs/runs/<run-id>`。
- coverage-review 只输出结构化返工位置和建议；workflow 负责 `bin/apply-coverage-gaps.py`、切片修复、合并和重新审查。

## 输出

输出按当前阶段写入 `process/reviews/analysis-coverage-review.json` 或 `process/reviews/design-coverage-review.json`，结构以 `templates/coverage-review-json-template.json` 为准；如需人读版，由 `bin/render-run-markdown.py` 渲染。

coverage-review 不重复执行 deterministic lint 已覆盖的编号、字段、Markdown 语法和 JSON 结构检查。

coverage-review 可以修改对应的 `process/<scope>-fact-coverage-map.json` 覆盖状态和原因，但不直接修改主交付件。发现覆盖缺口时，只输出结构化返工位置和建议；对应 workflow 必须先运行 `bin/apply-coverage-gaps.py` 重开工作项，再回到切片产物修复后合并。返工合并后，必须重新运行 `bin/build-fact-coverage-map.py` 刷新覆盖证据图，再重新执行 coverage-review。

## 验证闭环

输出 coverage JSON 后运行 `python bin/lint-run-json.py outputs/runs/<run-id>`。若有 `coverageGaps[]`，必须确认 `artifactLocation` 指向可编辑切片；若结果为 `通过`，后续 workflow 必须生成对应 final-report。不要用本 skill 修复 deterministic lint 已能发现的字段、编号或 Markdown 漂移问题。

## 约束

- 不直接编辑 `deliverables/*.json` 或 Markdown。
- 不把最终人审报告逻辑前移到本 skill；本 skill 只做过程门禁。
- 不在缺少 fact-coverage-map 时凭最终交付件直接生成 coverage 结论。
- 不重复 deterministic lint 已覆盖的字段、编号和 Markdown 检查。
