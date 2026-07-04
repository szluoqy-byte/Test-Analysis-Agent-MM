---
name: final-report-generation
description: 在测试分析或测试设计 coverage-review 已闭环后，基于已审查的 FACT 覆盖证据图生成最终人审报告，展示 FACT 到 SC/TP/TC 的覆盖关系；不触发返工。
---

# 最终报告生成 Skill

本 skill 在 `coverage-review` 通过且返工闭环完成后使用。它读取 `process/analysis-fact-coverage-map.json` 或 `process/design-fact-coverage-map.json` 中已经审查过的覆盖证据，生成 `reports/analysis-final-report.json` 或 `reports/design-final-report.json`，供人工最终审阅。

`final-report-generation` 不是质量门禁，不输出 `coverageGaps[]`，不调用 `bin/apply-coverage-gaps.py`，不直接修改 slice、主交付件 JSON、覆盖证据图或派生 Markdown。最终报告里的 `missing` 只能来自覆盖证据图中的 `gap`，不得在 final-report 阶段新增覆盖缺口判断。

## 何时使用

仅在对应范围的 coverage-review 已通过或已明确收口、且覆盖证据图已经完成审查后使用。不要在 coverage-review 之前使用，也不要用本 skill 判断是否需要返工。

## 输入

- `process/input-fact-model.json`。
- `process/analysis-fact-coverage-map.json` 或 `process/design-fact-coverage-map.json`，由 `coverage-review` 审查并填写覆盖状态。
- 分析范围读取 `deliverables/test-analysis-solution.json`。
- 设计范围读取 `deliverables/test-analysis-solution.json` 和 `deliverables/test-design-solution.json`。
- 对应范围的 `process/reviews/analysis-coverage-review.json` 或 `process/reviews/design-coverage-review.json` 用于确认 coverage-review 已通过且没有待处理 blocking 返工项。
- `process/rules-pack.json` 中对 `final-report-generation` 可见的 rules；rules 是强制约束。
- `process/context-pack.json` 中对 `final-report-generation` 可见的 project/personal 动态来源；如需使用，只读取相关正文，并在 `coverageReason` 中说明影响。
- `templates/final-report-json-template.json`。

## 生成检查清单

Progress:
- [ ] Step 1: 确认对应 coverage-review 已通过或明确收口
- [ ] Step 2: 确认 fact-coverage-map 已由 coverage-review 审查
- [ ] Step 3: 运行 `python bin/build-final-report.py outputs/runs/<run-id> --scope analysis|design`
- [ ] Step 4: 运行 `python bin/render-run-markdown.py outputs/runs/<run-id> --check`
- [ ] Step 5: 运行 `python bin/lint-run-json.py outputs/runs/<run-id>`
- [ ] Step 6: 确认 final-report 没有新增 coverage-review 未判断的 missing

## 默认路径

默认只从当前 run 的 `process/<scope>-fact-coverage-map.json` 生成对应 `reports/<scope>-final-report.json/.md`。不要读取其他 run 的报告，不要从 Markdown 反推覆盖关系。

## 计划-校验-执行模式

先确认 coverage-review 已完成并审查过 fact-coverage-map；再由 `bin/build-final-report.py` 从覆盖证据图生成 final-report；最后用 render check 和 `lint-run-json.py` 校验。若发现 final-report 需要新增缺口判断，停止并回到 coverage-review，不在 final-report 阶段自行判断。

## 易错点

- final-report 是最终人审件，不是过程门禁，不输出 `coverageGaps[]`。
- `missing` 只能来自 coverage-review 允许保留的 `gap`。
- Markdown 是派生阅读版，不能手写，也不能作为下一阶段事实源。

## 生成步骤

1. 确认对应范围的 coverage-review 已完成且没有待处理 blocking 返工项。
2. 读取 `process/rules-pack.json` 和 `process/context-pack.json`，筛选对 `final-report-generation` 可见的 rules 和动态来源；rules 必须遵守，动态来源只用于补充审阅判断。
3. 确认覆盖证据图中每个 `factCoverage[]` 行已经完成 coverage-review 判断；如仍有 `coverageStatus=gap`，必须确认对应 coverage-review 已明确允许保留为最终人审缺口，否则回到 coverage-review。
4. 运行 `python bin/build-final-report.py outputs/runs/<run-id> --scope analysis|design`，由脚本从覆盖证据图生成 `reports/*-final-report.json` 并渲染 Markdown。
5. 不手写 `reports/*-final-report.json` 或 `.md`；最终报告只能由脚本从覆盖证据图生成。

## 输出

- 分析范围输出 `reports/analysis-final-report.json` 和 `reports/analysis-final-report.md`。
- 设计范围输出 `reports/design-final-report.json` 和 `reports/design-final-report.md`。
- Markdown 只由脚本从 JSON 渲染，供人工审阅，不作为后续流程事实源。

## 验证闭环

运行 `python bin/build-final-report.py outputs/runs/<run-id> --scope analysis|design` 后，再运行 `python bin/render-run-markdown.py outputs/runs/<run-id> --check` 和 `python bin/lint-run-json.py outputs/runs/<run-id>`。若 final-report 出现新的 `missing` 判断，说明流程错误，应回到 coverage-review 和 fact-coverage-map。

## 覆盖状态定义

- `covered`：FACT 的核心事实、约束和可观察结果已被最终叶子 SC/TP 覆盖；设计范围还必须有对应 TC 覆盖。
- `partial`：只覆盖了事实的一部分，或缺少关键约束、结果、路径、角色、状态、数据组合或设计范围 TC。
- `missing`：coverage-review 允许保留的过程 `gap`，表示最终交付件没有可追溯的 SC/TP/TC 覆盖。
- `not_applicable`：该 FACT 是输入背景、范围说明、非测试对象或只作为上下文，不需要由 SC/TP/TC 覆盖。

## 约束

- 不新增、删除、合并或改写 FACT。
- 不编造不存在的 SC、TP 或 TC 编号；引用必须来自最终 canonical JSON。
- `coverageTree` 必须保持真实层级：TP 必须属于所填叶子 SC，TC 必须属于所填 TP。
- 不在 final-report 阶段新增覆盖缺口判断；需要返工的问题必须回到 coverage-review 和覆盖证据图。
- 不重复 deterministic lint 已覆盖的 JSON 字段、编号、Markdown 漂移检查。
- 分析最终报告只展示 `FACT -> leaf SC -> TP`；`testCases[]` 保持空数组。
- 设计最终报告展示 `FACT -> leaf SC -> TP -> TC`，一个 FACT 可以对应多个叶子 SC、TP 和 TC。
