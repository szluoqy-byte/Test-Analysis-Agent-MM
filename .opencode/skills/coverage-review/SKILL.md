---
name: coverage-review
description: 在测试用例标题大纲生成后使用，用于执行覆盖审查、需求追踪检查、方法应用检查、风险级别检查、输出结构检查、标题粒度检查和非完整用例化检查。
---

# 覆盖审查 Skill

本 skill 在测试用例标题大纲输出前使用，是自我评审和迭代修正入口。

## 输入

- 已生成的测试用例标题大纲。
- 如有过程报告，读取其中的测试点映射、方法路由和方法证据。
- `${PROJECT_ROOT}/outputs/runs/<run-id>/process/task-list.md`。
- `knowledge/test-analysis-methodology.md`。
- `knowledge/test-scenario-point-case-boundary.md`。
- `knowledge/basic-test-types.md`。
- 测试分析维度与方法路由表。
- 方法分析证据摘要。
- 结构化需求模型。
- 待确认问题。
- 记忆上下文包中的 project/personal 补充、绑定结果和命中来源。
- `quality-gates/*.md`。
- `knowledge/expert-review-rubric.md`。

## 审查步骤

1. 执行 `testpoint-not-testcase-check.md`。
2. 执行 `coverage-check.md`。
3. 执行 `traceability-check.md`。
4. 执行 `method-application-check.md`。
5. 执行 `risk-priority-check.md`。
6. 执行 `output-schema-check.md`。
7. 执行 `testcase-title-outline-check.md`，重点检查 `测试场景 -> 测试点 -> 测试用例标题项` 层级、输入条件与数据依赖、判定关注和非完整用例化约束。
8. 执行 `semantic-quality-check.md`。
9. 检查 `process/task-list.md` 是否包含固定阶段、顺序正确、最终必选阶段已完成。
10. 如果测试用例标题大纲文件已生成，运行 `bin/lint-testcase-title-outline.py ${PROJECT_ROOT}/outputs/runs/<run-id>/deliverables/testcase-title-outline.md` 做确定性结构校验。
11. 运行 `bin/check-artifact-consistency.py ${PROJECT_ROOT}/outputs/runs/<run-id>`，检查固定运行目录、任务清单、主交付件和过程报告之间的一致性。
12. 如果过程分析报告已生成，运行 `bin/lint-testpoint-report.py ${PROJECT_ROOT}/outputs/runs/<run-id>/reports/test-analysis-report.md` 和 `bin/semantic-testpoint-check.py ${PROJECT_ROOT}/outputs/runs/<run-id>/reports/test-analysis-report.md` 做过程报告校验。
13. 如果使用了 project/personal 补充，检查相关风险原因、覆盖策略、判定依据、个人偏好、模板偏好或附加门禁是否已正确处理，且没有覆盖核心类型、字段、级别、输出契约和质量门禁。
14. 检查 project/personal 使用情况是否在 context pack 和过程报告中可见，包括绑定结果、命中来源、未采用来源、冲突处理和后续补读建议；personal 内容不得被写成项目事实或团队共识。
15. 使用 `knowledge/expert-review-rubric.md` 进行专家评分。
16. 列出通过、警告和失败项。
17. 对阻断报告发布且无法通过修正测试点或标题项解决的问题，登记 `CP-REVIEW` 待确认候选。
18. 给出针对性修正建议。

## 判定规则

| 结果 | 含义 | 后续处理 |
|---|---|---|
| 通过 | 结构、追踪、方法应用、标题粒度和语义质量满足要求 | 可以输出标题大纲 |
| 警告 | 存在非阻断问题或需求待确认风险 | 记录原因，必要时刷新待确认问题 |
| 失败 | 输出结构错误、用例化、缺少必选方法证据、专家评分低于通过线或核心需求不可追踪 | 修正后重跑审查 |

失败项分两类处理：

- 输出质量失败：例如表结构不合规、测试点或标题项完整用例化、重复严重、场景条件缺失、输入条件与数据依赖缺失、类型不在 `knowledge/basic-test-types.md` 定义内，或设计方法泄漏到主输出。必须修正输出后重新审查。
- 需求信息缺失：例如核心规则、终态、权限范围或接口契约无法确认。登记 `CP-REVIEW` 待确认候选，并保留为最终待确认问题。

## 输出

使用 `templates/coverage-review-template.md`。

审查输出必须包含：

- 每个 quality gate 的结果和失败/警告项。
- task-list 中固定阶段的状态和异常项。
- 必选方法是否都有测试点或待确认问题承接。
- 适用分析维度是否都落到主交付件，且没有只停留在过程报告中。
- 测试点是否保持非用例化，标题项是否保持标题大纲粒度。
- 标题项是否补充输入条件与数据依赖、判定关注和待确认信息。
- 需求依据和方法证据是否可追踪。
- 专项分析方法是否只保留在过程报告中，主交付件是否没有边界值清单、等价类清单、判定表、组合矩阵或状态迁移矩阵。
- 专家评分和未达标维度。
- 需要回传给 `clarification-gate` 的 `CP-REVIEW` 待确认候选。

## 约束

- 不静默修复或隐藏失败项。
- 不通过不可追踪的测试点。
- 保留需求歧义。
- 不通过缺少方法分析证据且没有解释的必选方法。
- 如果专家评分低于通过线且原因是输出质量不足，必须修正后再终稿。
- 确定性 lint 失败视为阻断性输出质量问题。
- 本 skill 不直接向用户提问；覆盖建议默认不进入最终待确认信息，除非影响核心测试结论或报告可交付性。
- 不把普通覆盖建议升级成阻断项，除非它会影响核心测试结论或报告可交付性。
- 如果需要核对 project/personal 附加门禁或模板偏好，只能按 context pack 记录的来源或当前需求明确指向的文件补读相关章节，并在审查输出中记录来源；不得全目录搜索或全量复制大文件。
