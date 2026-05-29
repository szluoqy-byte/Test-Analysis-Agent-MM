---
name: coverage-review
description: 在测试分析方案或测试设计方案生成后使用，用于执行覆盖审查、需求追踪检查、测试技术应用检查、输出结构检查、粒度检查、预期结果依据检查和非完整用例化检查。
---

# 覆盖审查 Skill

本 skill 在测试分析方案或测试设计方案输出前使用，是自我评审和迭代修正入口。

## 输入

- 已生成的测试分析方案，或已生成的测试设计方案及其上游测试分析方案。
- 如有过程报告，读取其中的测试点映射、测试技术路由和方法证据。
- `${PROJECT_ROOT}/outputs/runs/<run-id>/process/task-list.md`。
- `${PROJECT_ROOT}/outputs/runs/<run-id>/process/context-pack.md`。
- `${PROJECT_ROOT}/outputs/runs/<run-id>/process/clarification-session.md`。
- `process/context-pack.md` 中绑定到 `coverage-review` 的 project checklist、覆盖策略、风险画像、Oracle 或附加门禁。
- `knowledge/test-analysis-methodology.md`。
- `knowledge/basic-test-types.md`。
- `knowledge/test-analysis-solution-standard.md`。
- 如审查测试设计方案，读取 `knowledge/test-design-solution-standard.md`。
- 测试分析维度与测试技术路由表。
- 方法分析证据摘要。
- 结构化需求模型。
- `quality-gates/*.md`。
- `quality-gates/expert-review-rubric.md`。

## 审查步骤

1. 读取 context pack 的“项目知识阶段绑定”。如果存在绑定到 `coverage-review` 的 project knowledge，先按来源文件、相关章节、关键词或标题读取，不全量复制大文件。
2. 执行 `testpoint-not-testcase-check.md`。
3. 执行 `coverage-check.md`。
4. 执行 `traceability-check.md`。
5. 执行 `method-application-check.md`。
6. 执行 `output-schema-check.md`。
7. 如果审查测试分析方案，执行 `test-analysis-solution-check.md`，重点检查 `测试场景 -> 测试点 -> 测试点明细` 层级、预期结果兜底、TDI 泄漏和非完整用例化约束。
8. 如果审查测试设计方案，执行 `test-design-solution-check.md`，重点检查 `测试场景 -> 测试点 -> 测试点明细 -> 测试设计项` 层级、TDI 表头、预期结果兜底和非完整用例化约束。
9. 执行 `semantic-quality-check.md`。
10. 执行 `project-knowledge-application-check.md`，检查项目知识阶段绑定、绑定文件读取和应用状态。
11. 按绑定的 project checklist、覆盖策略、风险画像或 Oracle 检查项目级漏覆盖，并验证前序绑定阶段是否有应用状态记录。
12. 检查 `process/task-list.md` 是否包含固定阶段、顺序正确、最终必选阶段已完成。
13. 如果测试分析方案文件已生成，运行 `bin/lint-test-analysis-solution.py ${PROJECT_ROOT}/outputs/runs/<run-id>/deliverables/test-analysis-solution.md` 做确定性结构校验。
14. 如果测试设计方案文件已生成，运行 `bin/lint-test-design-solution.py ${PROJECT_ROOT}/outputs/runs/<run-id>/deliverables/test-design-solution.md` 做确定性结构校验。
15. 运行 `bin/check-artifact-consistency.py ${PROJECT_ROOT}/outputs/runs/<run-id>`，检查固定运行目录、任务清单、主交付件和过程报告之间的一致性。
16. 如果过程分析报告已生成，运行 `bin/lint-testpoint-report.py ${PROJECT_ROOT}/outputs/runs/<run-id>/reports/test-analysis-report.md` 和 `bin/semantic-testpoint-check.py ${PROJECT_ROOT}/outputs/runs/<run-id>/reports/test-analysis-report.md` 做过程报告校验。
17. 如果使用了 project/personal 补充，检查相关风险原因、覆盖策略、判定依据、个人偏好、模板偏好或附加门禁是否已正确处理，且没有覆盖核心字段、输出契约和质量门禁。
18. 检查 project/personal 使用情况是否在 context pack 和过程报告中可见，包括绑定结果、命中来源、未采用来源、冲突处理、项目知识阶段绑定、应用状态和后续补读建议；personal 内容不得被写成项目事实或团队共识。
19. 使用 `quality-gates/expert-review-rubric.md` 进行专家评分。
20. 列出通过、警告和失败项。
21. 对阻断报告发布且无法通过修正测试点、测试点明细或测试设计项解决的问题，登记 `CP-REVIEW` 过程候选。
22. 给出针对性修正建议。

## 判定规则

| 结果 | 含义 | 后续处理 |
|---|---|---|
| 通过 | 结构、追踪、测试技术应用、测试点明细粒度和语义质量满足要求 | 可以输出测试分析方案 |
| 警告 | 存在非阻断问题或需求待确认风险 | 记录原因，必要时把相关预期结果改为 `待人工分析确认` |
| 失败 | 输出结构错误、用例化、缺少必选方法证据、专家评分低于通过线或核心需求不可追踪 | 修正后重跑审查 |

失败项分两类处理：

- 输出质量失败：例如结构不合规、测试点/测试点明细/测试设计项完整用例化、重复严重、场景条件缺失、预期结果为空、旧字段泄漏、TDI 泄漏到分析方案，或设计方法泄漏到分析方案。必须修正输出后重新审查。
- 需求信息缺失：例如核心规则、终态、权限范围或接口契约无法确认。登记 `CP-REVIEW` 过程候选，并把相关测试点明细的 `预期结果` 写成 `待人工分析确认`。
- Project knowledge 应用失败：context pack 已绑定到某阶段的 project knowledge 未被对应阶段读取、没有应用状态、或 project checklist 明确指出核心漏覆盖且无合理解释。必须补读、补齐应用记录或修正输出后重新审查。

## 输出

使用 `templates/coverage-review-template.md`。

审查输出必须包含：

- 每个 quality gate 的结果和失败/警告项。
- task-list 中固定阶段的状态和异常项。
- 必选方法是否都有测试点或过程缺口承接。
- 适用分析维度是否都落到主交付件，且没有只停留在过程报告中。
- 测试分析方案中的测试点和测试点明细是否保持非用例化，且没有提前输出 TDI 或具体代表性数据组合。
- 测试设计方案中的测试设计项是否只表达代表性条件、数据、状态或组合，且没有进入完整用例步骤。
- 预期结果是否都有需求/设计依据，依据不足时是否写 `待人工分析确认`。
- 需求依据和方法证据是否可追踪。
- 专项分析方法是否只保留在过程报告中，主交付件是否没有边界值清单、等价类清单、判定表、组合矩阵或状态迁移矩阵。
- 专家评分和未达标维度。
- 需要回传给 `clarification-gate` 的 `CP-REVIEW` 过程候选。
- project knowledge 阶段绑定和应用状态，包括每个绑定文件是否已读取、应用、解释不适用或进入缺口兜底。

## 约束

- 不静默修复或隐藏失败项。
- 不通过不可追踪的测试点。
- 保留需求歧义，但必须用 `待人工分析确认` 承接缺少依据的预期结果。
- 不通过缺少方法分析证据且没有解释的必选方法。
- 如果专家评分低于通过线且原因是输出质量不足，必须修正后再终稿。
- 确定性 lint 失败视为阻断性输出质量问题。
- 本 skill 不直接向用户提问；覆盖建议默认不进入主交付件。
- 不把普通覆盖建议升级成阻断项，除非它会影响核心测试结论或报告可交付性。
- 如果需要核对 project/personal 附加门禁或模板偏好，只能按 context pack 记录的来源或当前需求明确指向的文件补读相关章节，并在审查输出中记录来源；不得全目录搜索或全量复制大文件。
- 绑定到本阶段的 project knowledge 必须读取并留痕；前序阶段缺少绑定文件应用记录时，不得静默通过。
