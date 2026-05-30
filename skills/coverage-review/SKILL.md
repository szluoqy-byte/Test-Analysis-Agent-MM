---
name: coverage-review
description: 在测试分析方案或测试设计方案生成后使用，作为覆盖与过程门禁收口环节；先消费确定性 lint 和独立语义评审结果，再检查需求覆盖、追踪关系、测试技术应用、rules 应用、project knowledge 应用和必要的过程一致性；不重复执行脚本已覆盖的结构、编号、字段和 Markdown 语法检查。
---

# 覆盖审查 Skill

本 skill 是生成链路的覆盖与过程门禁收口。它不再承担主交付件结构 lint 的模型复查职责；确定性规则由 `bin/lint-test-analysis-solution.py`、`bin/lint-test-design-solution.py` 和 `bin/check-artifact-consistency.py` 执行并作为事实源。

如果确定性 lint 失败，本 skill 直接输出阻断结论和脚本失败项，不继续执行耗时的覆盖语义审查、项目 checklist 深查或专家评分。

## 输入

- 已生成的测试分析方案，或已生成的测试设计方案及其上游测试分析方案。
- 对应主交付件 lint 结果。
- 独立评审结果：`test-analysis-solution-review` 或 `test-design-solution-review`。
- 如有过程报告，读取其中的测试点映射、测试技术路由和方法证据。
- `${PROJECT_ROOT}/outputs/runs/<run-id>/process/task-list.md`。
- `${PROJECT_ROOT}/outputs/runs/<run-id>/process/context-pack.md`。
- `${PROJECT_ROOT}/outputs/runs/<run-id>/process/clarification-session.md`。
- `process/context-pack.md` 中的适用强制规则和 Rules 与输入冲突记录。
- `process/context-pack.md` 中绑定到 `coverage-review` 的 project checklist、覆盖策略、风险画像、Oracle 或附加门禁。
- `knowledge/test-analysis-methodology.md`。
- `knowledge/basic-test-types.md`。
- `knowledge/test-analysis-solution-standard.md`。
- 审查测试设计方案时读取 `knowledge/test-design-solution-standard.md`。
- 测试分析维度与测试技术路由表。
- 方法分析证据摘要。
- 结构化需求模型。
- `quality-gates/coverage-check.md`。
- `quality-gates/traceability-check.md`。
- `quality-gates/method-application-check.md`。
- `quality-gates/rules-application-check.md`。
- `quality-gates/project-knowledge-application-check.md`。
- 可选深度评估时读取 `quality-gates/semantic-quality-check.md` 和 `quality-gates/expert-review-rubric.md`。

## 审查步骤

1. 读取 context pack 的“项目知识阶段绑定”。如果存在绑定到 `coverage-review` 的 project knowledge，先按来源文件、相关章节、关键词或标题读取，不全量复制大文件。
2. 检查主交付件 lint 结果；测试分析方案使用 `bin/lint-test-analysis-solution.py`，测试设计方案使用 `bin/lint-test-design-solution.py`。如果 lint 失败，输出 `失败`，不继续做模型型覆盖审查。
3. 消费独立评审结果。如果独立评审结论为 `需修正`，输出 `失败` 或 `警告`，并只补充覆盖层面的影响，不重复评审结构和粒度细节。
4. 执行 `coverage-check.md`，检查需求模块、主流程、失败路径、权限、状态、接口、数据一致性、高风险区域和场景级 E2E 是否被覆盖；已由 lint 确认的 E2E 存在性不再重复判断，只判断语义覆盖是否合理。
5. 执行 `traceability-check.md`，检查测试点、测试点明细或测试设计项是否能追踪到需求、设计方案、rules、方法证据或明确风险确认点。
6. 执行 `method-application-check.md`，检查必选测试技术是否落到主交付件、方法证据或过程缺口，不只停留在路由表。
7. 执行 `rules-application-check.md`，检查适用 rules 是否被应用、解释不适用，或由当前用户明确指令覆盖。
8. 执行 `project-knowledge-application-check.md`，检查项目知识阶段绑定、绑定文件读取和应用状态；默认 checklist 类项目知识在本阶段统一查漏，避免独立评审和覆盖审查重复读取。
9. 按绑定的 project checklist、覆盖策略、风险画像或 Oracle 检查项目级漏覆盖，并验证前序绑定阶段是否有应用状态记录。
10. 如果过程分析报告已生成且本次要求校验过程报告，运行 `bin/lint-testpoint-report.py ${PROJECT_ROOT}/outputs/runs/<run-id>/reports/test-analysis-report.md` 和 `bin/semantic-testpoint-check.py ${PROJECT_ROOT}/outputs/runs/<run-id>/reports/test-analysis-report.md`；否则不因未生成过程报告额外触发语义脚本。
11. 检查 `process/task-list.md` 当前阶段状态和证据路径是否具备收口条件；`bin/check-artifact-consistency.py ${PROJECT_ROOT}/outputs/runs/<run-id>` 必须在输出收口阶段刷新最终 task-list 后运行，本阶段如已有结果则消费并记录，否则标记为 `pending_to_output_close`。
12. 如果使用了 rules 或 project/personal 补充，检查相关强制规则、覆盖策略、判定依据、个人偏好、模板偏好或附加门禁是否已正确处理，且没有违反 rules、核心字段、输出契约和质量门禁。
13. 检查 rules/project/personal 使用情况是否在 context pack 和过程报告或审查记录中可见，包括绑定结果、命中来源、未采用来源、冲突处理、适用强制规则、项目知识阶段绑定、应用状态和后续补读建议；personal 内容不得被写成项目事实或团队共识。
14. 仅在用户明确要求深度评估、任务参数声明 deep review、或覆盖审查发现高风险但无法定性时，使用 `quality-gates/semantic-quality-check.md` 和 `quality-gates/expert-review-rubric.md` 进行专家评分；默认单次报告不执行专家评分。
15. 列出通过、警告和失败项。
16. 对阻断报告发布且无法通过修正测试点、测试点明细或测试设计项解决的问题，登记 `CP-REVIEW` 过程候选。
17. 给出针对性修正建议。

## 不再重复检查

以下规则只读取脚本结果，不在模型审查中逐项复查：

- 主标题、必需章节、禁止章节和固定路径。
- `SC-*`、`TP-*`、`TP-*-*`、`TP-*-*-*`、`TDI-*` 的格式和连续编号。
- 禁用编号、旧字段、Markdown 加粗、完整用例字段和表格承载规则。
- 每个场景是否存在 `E2E场景测试`、每个测试点是否有明细、非成功明细是否有第四层。

`quality-gates/output-schema-check.md`、`quality-gates/test-analysis-solution-check.md` 和 `quality-gates/test-design-solution-check.md` 作为输出契约说明保留；默认审查以 lint 脚本结果为事实源，不再由模型重复执行。

## 判定规则

| 结果 | 含义 | 后续处理 |
|---|---|---|
| 通过 | lint、独立评审、覆盖、追踪、方法应用、rules 和 project knowledge 应用均满足要求 | 可以输出方案 |
| 警告 | 存在非阻断问题、依据不足或局部待人工分析确认风险 | 记录原因，必要时把相关预期结果改为 `待人工分析确认` |
| 失败 | 确定性 lint 失败、核心需求不可追踪、必选方法无承接、rules/project knowledge 应用失败或独立评审阻断 | 修正后重跑对应检查 |

失败项分为四类处理：

- 确定性校验失败：结构、编号、字段、语法和固定路径问题。必须按脚本输出修正后重跑 lint；最终一致性问题必须在输出收口阶段修正后重跑 `check-artifact-consistency.py`。
- 输出质量失败：例如测试点/测试点明细完整用例化、核心粒度不合理、预期结果为空或事实编造。必须修正输出后重跑独立评审和覆盖审查。
- 需求信息缺失：例如核心规则、终态、权限范围或接口契约无法确认。登记 `CP-REVIEW` 过程候选，并把相关叶子节点的 `预期结果` 写成 `待人工分析确认`。
- Project/rules 应用失败：context pack 已绑定或登记的来源未被对应阶段读取、应用或解释。必须补读、补齐应用记录或修正输出后重审。

## 输出

使用 `templates/coverage-review-template.md`。

审查输出必须包含：

- 确定性校验结果：lint 脚本名称、通过/失败、关键失败项；最终一致性检查结果可在输出收口阶段补充。
- 独立评审结论：只引用结论和阻断项，不重复展开所有结构规则。
- 每个覆盖类 quality gate 的结果和失败/警告项。
- task-list 中固定阶段的状态和异常项。
- 必选方法是否都有主交付件承接、方法证据或过程缺口。
- 适用分析维度是否落到主交付件，而不是只停留在过程报告。
- 需求依据和方法证据是否可追踪。
- rules 应用状态，包括适用 rules 是否已遵守、解释不适用、被当前用户明确指令覆盖，或与输入冲突并完成覆盖留痕。
- project knowledge 阶段绑定和应用状态，包括每个绑定文件是否已读取、应用、解释不适用或进入缺口兜底。
- 需要回传给 `clarification-gate` 的 `CP-REVIEW` 过程候选。
- 深度评估开启时，输出专家评分；默认不输出专家评分章节。

## 约束

- 不静默修复或隐藏失败项。
- 不通过不可追踪的测试点。
- 不重复执行确定性脚本已经覆盖的结构、编号、字段和 Markdown 语法检查。
- 保留需求歧义，但必须用 `待人工分析确认` 承接缺少依据的预期结果。
- 不通过缺少方法分析证据且没有解释的必选方法。
- 确定性 lint 失败视为阻断性输出质量问题。
- 本 skill 不直接向用户提问；覆盖建议默认不进入主交付件。
- 不把普通覆盖建议升级成阻断项，除非它会影响核心测试结论或报告可交付性。
- 如需核对 project/personal 附加门禁或模板偏好，只能按 context pack 记录的来源或当前需求明确指向的文件补读相关章节，并在审查输出中记录来源；不得全目录搜索或全量复制大文件。
- 绑定到本阶段的 project knowledge 必须读取并留痕；前序阶段缺少绑定文件应用记录时，不得静默通过。
