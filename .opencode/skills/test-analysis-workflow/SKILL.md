---
name: test-analysis-workflow
description: 当用户提供需求文档和可选设计方案文档，并要求生成“SC 场景树 -> TP 测试点”的测试分析方案时使用；该 skill 编排上下文、输入事实、测试技术路由、测试分析方案 JSON 生成、独立评审和 Markdown 渲染。
---

# 需求到测试分析方案主入口

本 skill 是 `test-analysis-agent` 的完整链路入口。目标是从 `$ARGUMENTS` 指定的需求文档和可选设计方案文档中，生成 `测试分析方案`。

测试分析方案回答 what to test：输出最多 3 层 `SC-*` 场景树和全局连续 `TP-*` 测试点。它不输出测试用例、测试数据、操作步骤或预期结果。

## 必需输入

- `$ARGUMENTS`：至少包含一份 `.md` 或 `.markdown` 需求文档路径。
- 可额外包含一份或多份 `.md` 或 `.markdown` 设计方案文档路径。
- 如果输入包含 `.docx` 或 `.xlsx`，不得在本 workflow 中转换；必须先由 `@file-normalization-agent` 归一化为 Markdown。
- 可选 `--project <project-key>`，必须传递给 `bin/build-rules-pack.py` 和 `context-source-indexing`；personal rules 来自 `rules/user/**/*.md`，personal 动态补充来源来自 `knowledge/user/**/*.md` 和 `memory/user/**/*.md`。

## 职责边界

- 本 skill 只负责编排完整分析链路和写出本次运行产物。
- 强制规则由 `process/rules-pack.json` 独立索引，后续每个阶段必须筛选当前阶段可见的 `ruleSources[]`，读取对应 Markdown 正文并遵守适用 rules。
- project/personal knowledge 和 memory 扩展来源来自 `context-source-indexing` 生成的 `sources[]` 索引。
- `input-fact-modeling` 负责建立统一输入事实模型。
- `test-analysis-solution-generation` 负责先生成并冻结 `SC-*` 场景树，再按每个叶子 SC 生成 `TP-*` 切片并合并。
- `test-analysis-solution-review` 负责分段语义评审：先评审 SC 树，再评审 TP 覆盖和粒度，最后评审主交付件整体语义。
- `coverage-review` 负责覆盖、追踪、rules-pack 和动态来源应用状态收口。
- `final-report-generation` 负责在 coverage-review 闭环后填写最终人审报告，只展示 FACT 到 SC/TP 的最终覆盖关系，不触发返工。
- 主交付件事实源是 `outputs/runs/<run-id>/deliverables/test-analysis-solution.json`；人读版由 `bin/render-run-markdown.py` 生成。

## 执行流程

1. 校验输入至少包含一份 Markdown 需求文档；若发现 Office 输入，输出需先使用 `@file-normalization-agent` 的阻断说明，不创建测试分析 run。
2. 固定 `PROJECT_ROOT`，运行 `python bin/generate-run-id.py` 生成本次运行 ID，并创建 `outputs/runs/<run-id>/deliverables/`、`process/`、`reports/` 和 `inputs/`。
3. 使用 `templates/process-artifacts-json-template.json` 创建 `process/analysis-task-list.json`，并通过 `python bin/update-run-task.py outputs/runs/<run-id> --flow analysis ...` 维护状态；不要覆盖历史 run 中可能由测试设计维护的 `process/design-task-list.json`。
4. 调用 `python bin/build-rules-pack.py ...` 生成 `process/rules-pack.json`，并把同一 `project-key` 传入脚本。
5. 调用 `python skills/context-source-indexing/scripts/build-context-source-index.py ...` 生成 `process/context-pack.json`。
6. 使用 `input-fact-modeling` 读取需求文档、可选设计方案文档、`process/rules-pack.json` 中当前阶段可见的规则正文，生成 `process/input-fact-model.json`。
7. 使用 `testing-method-router` 基于输入事实模型和 `process/rules-pack.json` 中当前阶段可见的规则正文，对需求事实和设计事实进行测试技术路由。
8. 使用路由选中的专项方法参考产出覆盖维度建议、候选 SC/TP 方向和按源补读记录；方法只作为生成参考，不要求最终 TP 完全来自或逐项绑定这些方法。
9. 运行 `python skills/test-analysis-solution-generation/scripts/init-scenario-tree.py outputs/runs/<run-id>` 初始化带 `generationContext` 的 `process/scenario-tree.json`，再使用 `test-analysis-solution-generation` 读取 `generationContext` 和当前阶段可见来源，填写 `scope[]` 与 `scenarios[]`。该文件只允许 SC 树，不得包含 `testPoints[]`。
10. 运行 `python skills/test-analysis-solution-generation/scripts/lint-scenario-tree.py outputs/runs/<run-id>/process/scenario-tree.json`，再运行 `python bin/init-report-artifact.py outputs/runs/<run-id> --kind review --review-type scenario-tree-review --force` 初始化评审骨架，并使用 `test-analysis-solution-review` 填写 `process/reviews/scenario-tree-review.json`。SC review 通过后，后续阶段不得新增、删除、合并或改写 SC。
11. 运行 `python skills/test-analysis-solution-generation/scripts/extract-test-point-work-items.py outputs/runs/<run-id>` 生成 `process/test-point-work-items.json`，再运行 `python bin/init-staged-slices.py outputs/runs/<run-id> --scope analysis --pending` 批量初始化 `process/test-point-slices/<SC-ID>.json`；需要查看状态时运行 `python bin/list-staged-work-items.py outputs/runs/<run-id> --scope analysis --status all`。
12. 使用 `test-analysis-solution-generation` 逐个填写 `process/test-point-slices/<SC-ID>.json` 的 `scenario.testPoints[]`；每个切片必须读取当前阶段适用 rules 和动态来源，不得改写 SC。
13. 对每个 TP 切片先运行 `python bin/init-report-artifact.py outputs/runs/<run-id> --kind review --review-type test-point-review --target-id <SC-ID> --force` 初始化评审骨架，再使用 `test-analysis-solution-review` 执行覆盖和粒度评审；切片通过后可运行 `python bin/merge-staged-slices.py outputs/runs/<run-id> --scope analysis --ids <SC-ID>`，所有切片完成后运行 `python bin/merge-staged-slices.py outputs/runs/<run-id> --scope analysis --all` 确保最终合并为 `deliverables/test-analysis-solution.json` 并统一全局 `TP-*` 编号。
14. 所有叶子 SC 合并后，运行 `bin/lint-run-json.py outputs/runs/<run-id>`。失败时先修正 JSON，不进入最终评审。
15. 运行 `bin/render-run-markdown.py outputs/runs/<run-id>`，再运行 `bin/lint-test-analysis-solution.py outputs/runs/<run-id>/deliverables/test-analysis-solution.md`。
16. 运行 `python bin/init-report-artifact.py outputs/runs/<run-id> --kind review --review-type test-analysis-solution-review --force` 初始化最终评审骨架，再使用 `test-analysis-solution-review` 独立语义评审最终测试分析方案 JSON，评审结果写入 `process/reviews/test-analysis-solution-review.json`。
17. 运行 `python bin/init-report-artifact.py outputs/runs/<run-id> --kind coverage --scope analysis --force` 初始化 coverage 骨架，再使用 `coverage-review` 执行覆盖、追踪、rules-pack 应用、动态来源应用和过程门禁收口，结果写入 `process/reviews/analysis-coverage-review.json`。
18. 如果切片 review 或最终 review 存在 blocking findings/issues，先运行 `python bin/apply-review-findings.py outputs/runs/<run-id> --scope analysis --all` 重开对应工作项；如果 `process/reviews/analysis-coverage-review.json` 中存在 `coverageGaps[]`，必须先运行 `python bin/apply-coverage-gaps.py outputs/runs/<run-id> --scope analysis`。之后按被重开的 `process/test-point-slices/<SC-ID>.json` 修复；不得直接编辑最终 Markdown，也不得跳过切片回写直接手改 `deliverables/test-analysis-solution.json`。修复后重新执行对应 TP 切片 review、`bin/merge-staged-slices.py`、确定性校验、最终分析 review、coverage-review 和一致性检查。
19. coverage-review 通过且返工闭环完成后，运行 `python bin/build-final-report.py outputs/runs/<run-id> --scope analysis` 生成 `reports/analysis-final-report.json` 骨架，再使用 `final-report-generation` 填写 `coverageTree[]`、`coverageStatus` 和 `coverageReason`；填写后再次运行同一脚本重新计算 `summary` 并渲染 `reports/analysis-final-report.md`。最终报告只供人工审阅，不输出 `coverageGaps[]`，不触发返工。
20. 最终输出前通过 `bin/update-run-task.py` 刷新 `process/analysis-task-list.json`，运行 `bin/check-staged-run.py outputs/runs/<run-id> --scope analysis`。

## 阶段产物契约

| 阶段 | 必须产出 | 交给下一阶段 |
|---|---|---|
| `task-list` | `process/analysis-task-list.json`、派生 `process/analysis-task-list.md` | 测试分析阶段顺序与状态追踪 |
| `rules-pack` | `process/rules-pack.json`、派生 `process/rules-pack.md` | 后续所有阶段筛选 `ruleSources[]`，读取规则正文并遵守适用 rules |
| `context-source-indexing` | `process/context-pack.json` | 后续阶段按阶段可见性读取 knowledge/memory 动态来源 |
| `input-fact-modeling` | `process/input-fact-model.json` | 测试技术路由、测试分析方案生成 |
| `testing-method-router` | 测试技术路由表 | 专项方法参考、测试分析方案生成 |
| 专项方法参考 | 覆盖维度建议、测试点候选 | 测试分析方案生成 |
| `SC 树生成与评审` | `process/scenario-tree.json`、`process/reviews/scenario-tree-review.json` | 叶子 SC 工作项生成 |
| `TP 切片生成与评审` | `process/test-point-work-items.json`、`process/test-point-slices/<SC-ID>.json`、`process/reviews/test-point-reviews/<SC-ID>.json`；可选汇总 `process/reviews/test-point-review.json` | 测试分析方案合并 |
| `test-analysis-solution-generation` | `deliverables/test-analysis-solution.json`、场景树、测试点 | JSON 校验 |
| 确定性校验 | JSON lint、Markdown render、Markdown lint | 独立语义评审 |
| `test-analysis-solution-review` | `process/reviews/test-analysis-solution-review.json` | 覆盖审查 |
| `coverage-review` | `process/reviews/analysis-coverage-review.json` | 输出收口 |
| `final-report-generation` | `reports/analysis-final-report.json`、派生 `reports/analysis-final-report.md` | 最终人审 |

## 脚本稳定性规则

- analysis 流程不得临时创建 `.py`、`.js`、`.ps1`、`.bat` 或其他可执行脚本来拼接、修复、循环处理或拆分 JSON。
- 只能调用仓库固定脚本：`bin/build-rules-pack.py`、`skills/test-analysis-solution-generation/scripts/init-scenario-tree.py`、`skills/test-analysis-solution-generation/scripts/lint-scenario-tree.py`、`skills/test-analysis-solution-generation/scripts/extract-test-point-work-items.py`、`skills/test-analysis-solution-generation/scripts/init-test-point-slice.py`、`bin/init-staged-slices.py`、`bin/list-staged-work-items.py`、`bin/build-generation-context.py`、`bin/init-report-artifact.py`、`bin/build-final-report.py`、`bin/apply-review-findings.py`、`bin/apply-coverage-gaps.py`、`bin/update-run-task.py`、`skills/test-analysis-solution-generation/scripts/merge-test-point-slice.py`、`bin/merge-staged-slices.py`、`bin/check-staged-run.py`、`bin/lint-run-json.py`、`bin/render-run-markdown.py`、`bin/lint-test-analysis-solution.py` 和 `bin/check-artifact-consistency.py`。
- 如果固定脚本能力不足，必须修改仓库 `bin/` 或对应 skill `scripts/` 下的固定脚本并运行校验；不得在 `outputs/`、`process/`、`reports/`、临时目录或当前工作目录写一次性脚本。

## 输出要求

- 主输出使用 `templates/test-analysis-solution-json-template.json` 生成 JSON。
- `process/scenario-tree.json` 是冻结 SC 树，最多 3 层，任何层级都不得包含 `testPoints[]`。
- `deliverables/test-analysis-solution.json` 的 `scenarios[]` 是场景树，最多 3 层；非叶子场景只允许有 `children[]`，叶子场景必须有 `testPoints[]`。
- `TP-*` 全局连续编号，每个叶子场景必须包含 `E2E场景测试`。
- `TP-*` 必须包含 `id`、`title`、`objective` 和 `basisRefs[]`。
- 测试技术和专项方法是生成参考，不是主交付字段；不得在 `TP-*` 中输出 `methodRefs[]` 或方法字段表格。
- 分析方案不得包含测试用例、测试数据、步骤、预期结果或 schemaVersion 2.0 之外的字段。
- 主输出不得使用 Markdown 加粗语法。
- 全流程不调用用户交互能力，不创建问题队列，不直接向用户提问，不暂停主流程。
