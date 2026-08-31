---
name: test-design-solution-review
description: 评审 Markdown TC 切片或最终测试设计 JSON，并直接输出 Markdown 评审结论和 TP 级返工位置。
---

# 测试设计方案评审 Skill

## 输入

- 切片阶段：`process/test-case-slices/<TP-ID>.md`。
- 最终阶段：`deliverables/test-design-solution.json` 与上游分析 JSON。
- 输入文档、rules/context Markdown 和测试用例写作标准。

## 评审要求

- 使用 `templates/review-report-template.md`，不生成 review JSON。
- 切片评审写入 `process/reviews/test-case-reviews/<TP-ID>.md`。
- 最终评审写入 `process/reviews/test-design-solution-review.md`。
- 第一段必须包含标准结论行。

重点检查分析承接、测试因子充分性、TC 原子性、具体测试数据、可执行步骤、步骤预期、最终预期、来源依据和 GUI/API/CLI 风格。

## 返工

blocking 问题定位到 `process/test-case-slices/<TP-ID>.md`，通过 `reopen-run-items.py` 重开对应 TP。修复后重新评审、完成工作项并重新固化设计结果。
