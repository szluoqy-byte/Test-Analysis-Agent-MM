---
name: coverage-review
description: 基于 Markdown 输入事实和最终分析或设计 JSON，编写 Markdown FACT 覆盖证据图与覆盖审查，定位需返工的 SC/TP 切片。
---

# Coverage Review Skill

## 何时使用

仅在最终方案 JSON 已通过整体语义评审后使用。Coverage review 决定是否返工；final report 只展示结果。

## 审查阶段

- [ ] Step 1: 建立 FACT 覆盖证据 Markdown
- [ ] Step 2: 审查覆盖链路
- [ ] Step 3: 定位并执行返工
- [ ] Step 4: 收口覆盖结论

## 各阶段执行要求

### Step 1: 建立 FACT 覆盖证据 Markdown

读取 `process/input-fact-model.md` 和最终方案 JSON，按 `templates/fact-coverage-map-template.md` 编写 `process/analysis-fact-coverage-map.md` 或 `process/design-fact-coverage-map.md`。每个 FACT 恰好一行。

### Step 2: 审查覆盖链路

分析范围的 covered 链路必须包含真实叶子 SC 和 TP；设计范围还必须包含真实 TC。使用 covered、partial、gap、not_applicable，并给出可追溯原因。

### Step 3: 定位并执行返工

按 `templates/coverage-review-template.md` 编写对应 `process/reviews/<scope>-coverage-review.md`。缺口位置只能指向 TP 或 TC Markdown 切片。运行 `reopen-run-items.py --ids ...`，修复、重审、完成工作项并重新固化结果后，再更新覆盖文件。

### Step 4: 收口覆盖结论

所有 blocking 缺口完成后，将覆盖审查结论写为通过。允许保留的 gap 必须明确说明原因；最终报告不得改变该判断。

## 输出

- `process/<scope>-fact-coverage-map.md`。
- `process/reviews/<scope>-coverage-review.md`。

## 约束

- 不生成 coverage JSON。
- 不直接编辑结果 JSON 或结果 Markdown。
- 不重复确定性 lint 已覆盖的字段和编号检查。
