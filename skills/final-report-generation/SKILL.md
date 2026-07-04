---
name: final-report-generation
description: 在测试分析或测试设计 coverage-review 已闭环后，基于输入事实模型和最终 canonical 交付件填写最终人审报告，展示 FACT 到 SC/TP/TC 的覆盖关系；不触发返工。
---

# 最终报告生成 Skill

本 skill 在 `coverage-review` 通过且返工闭环完成后使用。它读取 `process/input-fact-model.json` 和最终 canonical 交付件，填写 `reports/analysis-final-report.json` 或 `reports/design-final-report.json` 中的覆盖关系，供人工最终审阅。

`final-report-generation` 不是质量门禁，不输出 `coverageGaps[]`，不调用 `bin/apply-coverage-gaps.py`，不直接修改 slice、主交付件 JSON 或派生 Markdown。即使最终报告存在 `partial`、`missing` 或 `not_applicable`，也只作为最终审阅信息，不触发自动返工链路。

## 输入

- `process/input-fact-model.json`。
- `reports/analysis-final-report.json` 或 `reports/design-final-report.json`，由 `python bin/build-final-report.py outputs/runs/<run-id> --scope analysis|design` 先生成骨架。
- 分析范围读取 `deliverables/test-analysis-solution.json`。
- 设计范围读取 `deliverables/test-analysis-solution.json` 和 `deliverables/test-design-solution.json`。
- 对应范围的 `process/reviews/analysis-coverage-review.json` 或 `process/reviews/design-coverage-review.json` 只作为最终状态参考，不作为返工指令。
- `process/rules-pack.json` 中对 `final-report-generation` 可见的 rules；rules 是强制约束。
- `process/context-pack.json` 中对 `final-report-generation` 可见的 project/personal 动态来源；如需使用，只读取相关正文，并在 `reviewNote` 中说明影响。
- `templates/final-report-json-template.json`。

## 生成步骤

1. 确认对应范围的 coverage-review 已完成且没有待处理 blocking 返工项。
2. 读取 `process/rules-pack.json` 和 `process/context-pack.json`，筛选对 `final-report-generation` 可见的 rules 和动态来源；rules 必须遵守，动态来源只用于补充审阅判断。
3. 读取 final report 骨架，保持每个 `factCoverage[]` 行的 `factId`、`inputSource`、`factSummary`、`condition` 和 `observableResult` 不变。
4. 逐条 FACT 对照最终交付件，填写：
   - `coveredScenarios[]`：覆盖该 FACT 的 `SC-*`，写 `SC-001 用户发起支付` 这类可读文本。
   - `coveredTestPoints[]`：覆盖该 FACT 的 `TP-*`，写 `TP-001 创建支付单接口契约` 这类可读文本。
   - `coveredTestCases[]`：仅设计范围填写覆盖该 FACT 的 `TC-*`；分析范围保持空数组。
   - `coverageStatus`：只能取 `covered`、`partial`、`missing`、`not_applicable`。
   - `reviewNote`：解释覆盖判断，尤其是 `partial`、`missing` 或 `not_applicable` 的原因。
5. 保存 JSON 后运行 `python bin/build-final-report.py outputs/runs/<run-id> --scope analysis|design` 重新计算 `summary` 并渲染 Markdown。
6. 不手写 `reports/*-final-report.md`，Markdown 只能由脚本从 JSON 渲染。

## 覆盖状态定义

- `covered`：FACT 的核心事实、约束和可观察结果已被最终 SC/TP 覆盖；设计范围还必须有对应 TC 覆盖。
- `partial`：只覆盖了事实的一部分，或缺少关键约束、结果、路径、角色、状态、数据组合或设计范围 TC。
- `missing`：最终交付件没有可追溯的 SC/TP/TC 覆盖。
- `not_applicable`：该 FACT 是输入背景、范围说明、非测试对象或只作为上下文，不需要由 SC/TP/TC 覆盖。

## 约束

- 不新增、删除、合并或改写 FACT。
- 不编造不存在的 SC、TP 或 TC 编号；引用必须来自最终 canonical JSON。
- 不把最终报告中的缺口转写为 `coverageGaps[]`，也不触发自动返工。
- 不重复 deterministic lint 已覆盖的 JSON 字段、编号、Markdown 漂移检查。
- 分析最终报告只展示 `FACT -> SC -> TP`；`coveredTestCases[]` 保持空数组。
- 设计最终报告展示 `FACT -> SC -> TP -> TC`，一个 FACT 可以对应多个 SC、TP 和 TC。
