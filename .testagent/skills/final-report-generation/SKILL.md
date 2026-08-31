---
name: final-report-generation
description: 在 Markdown coverage-review 已通过后，将已审查的 FACT 覆盖证据整理为最终 Markdown 人审报告，不生成 JSON，也不触发返工。
---

# 最终报告生成 Skill

## 报告生成阶段

- [ ] Step 1: 确认覆盖审查已收口
- [ ] Step 2: 生成最终 Markdown 报告
- [ ] Step 3: 核对 FACT 与覆盖链

## 各阶段执行要求

### Step 1: 确认覆盖审查已收口

确认 `process/reviews/<scope>-coverage-review.md` 的结论为通过，并读取对应 fact coverage map。存在未处理 blocking 缺口时停止并返回 coverage-review。

### Step 2: 生成最终 Markdown 报告

按 `templates/final-report-template.md` 直接编写 `reports/analysis-final-report.md` 或 `reports/design-final-report.md`。不生成 final-report JSON，不从结果 JSON 再渲染报告。

### Step 3: 核对 FACT 与覆盖链

确认输入事实模型中的每个 FACT 都出现在最终报告，状态和 SC/TP/TC 链路与已审查 coverage map 一致。报告不得新增 missing 判断。

## 输出

- 分析：`reports/analysis-final-report.md`。
- 设计：`reports/design-final-report.md`。

## 约束

- final report 只供人工审阅。
- 不触发工作项重开，不修改切片或结果交付件。
