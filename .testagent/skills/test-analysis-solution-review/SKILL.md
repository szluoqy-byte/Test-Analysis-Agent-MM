---
name: test-analysis-solution-review
description: 评审 Markdown SC 场景树、TP 切片或最终测试分析 JSON，并直接输出 Markdown 评审结论和返工位置。
---

# 测试分析方案评审 Skill

## 输入

- SC 阶段：`process/scenario-tree.md`。
- TP 阶段：`process/test-point-slices/<SC-ID>.md`。
- 最终阶段：`deliverables/test-analysis-solution.json`。
- 输入事实、rules/context Markdown 和适用正文。

## 评审要求

- 使用 `templates/review-report-template.md`，直接写 Markdown，不生成 review JSON。
- SC 评审写入 `process/reviews/scenario-tree-review.md`。
- TP 评审写入 `process/reviews/test-point-reviews/<SC-ID>.md`。
- 最终评审写入 `process/reviews/test-analysis-solution-review.md`。
- 第一段必须包含 `- 结论：通过/需修正/失败/警告/不适用`。

重点检查场景边界、SC 层级、TP 粒度、E2E 测试点、接口组织方式、来源依据以及是否错误用例化。结构和编号问题由固定 lint 负责，不在评审中重复展开。

## 返工

blocking 问题必须定位到 `process/test-point-slices/<SC-ID>.md`。重开工作项、修复切片、重新评审并重新固化分析结果；不得手改结果 Markdown。
