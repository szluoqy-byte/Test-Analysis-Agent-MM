---
name: coverage-review
description: 在测试分析方案或测试设计方案 JSON 生成后使用，作为覆盖与过程门禁收口环节；先消费确定性 JSON/Markdown lint 和独立语义评审 JSON，再检查需求覆盖、追踪关系、测试技术应用、core rules 应用、动态来源应用和必要的过程一致性；不重复执行脚本已覆盖的结构、编号、字段和 Markdown 语法检查。
---

# 覆盖审查 Skill

本 skill 是生成链路的覆盖与过程门禁收口。它不再承担主交付件结构 lint 的模型复查职责；确定性规则由 `bin/lint-run-json.py`、`bin/render-run-markdown.py --check`、`bin/lint-test-analysis-solution.py`、`bin/lint-test-design-solution.py` 和 `bin/check-artifact-consistency.py` 执行并作为事实源。

如果确定性 lint 失败，本 skill 直接输出阻断结论和脚本失败项，不继续执行耗时的覆盖语义审查、项目 checklist 深查或专家评分。

## 输入

- 已生成的测试分析方案 JSON，或已生成的测试设计方案 JSON 及其上游测试分析方案 JSON。
- 对应 `lint-run-json.py`、`render-run-markdown.py --check` 和主交付件 Markdown lint 结果。
- 独立评审 JSON：`reports/test-analysis-solution-review.json` 或 `reports/test-design-solution-review.json`。
- 如有结构化过程 JSON 或 review/coverage JSON，读取其中的测试点映射、测试技术路由和方法证据。
- `${PROJECT_ROOT}/outputs/runs/<run-id>/process/task-list.json`。
- `${PROJECT_ROOT}/outputs/runs/<run-id>/process/context-pack.json`。
- `${PROJECT_ROOT}/outputs/runs/<run-id>/process/clarification-session.json`。
- core rules、core knowledge 和固定质量门禁。
- `process/context-pack.json` 中 `sources[]` 对 `coverage-review` 可见的 project/personal checklist、覆盖策略、风险画像、Oracle 或附加门禁。
- `knowledge/test-workflow-boundaries.md`。
- `skills/coverage-review/references/basic-test-types.md`。
- `knowledge/test-analysis-solution-standard.md`。
- 审查测试设计方案时读取 `knowledge/test-design-solution-standard.md`。
- 测试分析维度与测试技术路由表。
- 方法分析证据摘要。
- 输入事实模型。
- `skills/coverage-review/references/coverage-check.md`。
- `skills/coverage-review/references/review-gates.md`。
- `skills/coverage-review/references/context-application-gates.md`。
- 可选深度评估时读取 `skills/coverage-review/references/deep-review-rubric.md`。
- `templates/coverage-review-json-template.json` 和 `templates/coverage-review-template.md`。前者定义 JSON 事实源形态，后者仅作为渲染后 Markdown 样式参考。

## 审查步骤

1. 读取 `process/context-pack.json`，筛选 `availableStages` 包含 `coverage-review` 或 `"*"` 的动态来源；如需使用，按来源文件、相关章节、关键词或标题读取正文，不全量复制大文件。
2. 检查主交付件 lint 结果；先确认 `bin/lint-run-json.py` 和 `bin/render-run-markdown.py --check` 通过，再按方案类型消费 `bin/lint-test-analysis-solution.py` 或 `bin/lint-test-design-solution.py`。如果 lint 失败，输出 `失败`，不继续做模型型覆盖审查。
3. 消费独立评审结果。如果独立评审结论为 `需修正`，输出 `失败` 或 `警告`，并只补充覆盖层面的影响，不重复评审结构和粒度细节。
4. 执行 `coverage-check.md`，检查需求模块、主流程、失败路径、权限、状态、接口、数据一致性、高风险区域和场景级 E2E 是否被覆盖；已由 lint 确认的 E2E 存在性不再重复判断，只判断语义覆盖是否合理。
5. 执行 `skills/coverage-review/references/review-gates.md`，检查测试点、测试点明细或测试设计项是否能追踪到需求、设计方案、rules、方法证据或明确风险确认点，并检查必选测试技术是否落到主交付件、方法证据或过程缺口，不只停留在路由表。
6. 执行 `skills/coverage-review/references/context-application-gates.md`，检查 core rules 是否被应用、解释不适用，或由当前用户明确指令覆盖；同时检查动态来源读取和应用状态。默认 checklist 类动态来源在本阶段统一查漏，避免独立评审和覆盖审查重复读取。
7. 检查前序阶段和当前覆盖审查中的 core rules/project/personal 使用情况是否在结构化过程记录或审查 JSON 中可见。
8. 按本阶段可见的 project checklist、覆盖策略、风险画像、Oracle 或附加门禁检查项目级漏覆盖，并验证前序阶段是否有应用状态记录。
9. 新 run 不要求生成自由格式过程分析 Markdown。只有迁移旧 run、且用户明确要求校验遗留 `reports/test-analysis-report.md` 时，才运行 `skills/coverage-review/scripts/lint-testpoint-report.py ...` 和 `skills/coverage-review/scripts/semantic-testpoint-check.py ...`；否则不因未生成遗留过程分析 Markdown 额外触发语义脚本。
10. 检查 `process/task-list.json` 当前阶段状态和证据路径是否具备收口条件；`bin/check-artifact-consistency.py ${PROJECT_ROOT}/outputs/runs/<run-id>` 必须在输出收口阶段刷新最终 task-list 后运行，本阶段如已有结果则消费并记录，否则标记为 `pending_to_output_close`。
11. 如果使用了 core rules 或 project/personal 动态来源，检查相关强制规则、覆盖策略、判定依据、个人偏好或附加门禁是否已正确处理，且没有违反 core rules、核心字段、输出契约和质量门禁。
12. 仅在用户明确要求深度评估、任务参数声明 deep review、或覆盖审查发现高风险但无法定性时，使用 `skills/coverage-review/references/deep-review-rubric.md` 进行专家评分；默认单次报告不执行专家评分。
13. 列出通过、警告和失败项。
14. 对阻断报告发布且无法通过修正测试点、测试点明细或测试设计项解决的问题，登记 `CP-REVIEW` 过程候选。
15. 给出针对性修正建议。

## 不再重复检查

以下规则只读取脚本结果，不在模型审查中逐项复查：

- 主标题、必需章节、禁止章节和固定路径。
- `SC-*`、`TP-*`、`TP-*-*`、`TP-*-*-*`、`TDI-*` 的格式和连续编号。
- 禁用编号、旧字段、Markdown 加粗、完整用例字段和表格承载规则。
- 每个场景是否存在 `E2E场景测试`、每个测试点是否有明细、明确非成功聚合明细是否有第四层。

输出结构和交付件粒度说明以 `knowledge/test-analysis-solution-standard.md`、`knowledge/test-design-solution-standard.md` 和对应 lint 脚本为准；coverage-review 默认只消费这些确定性结果，不重复维护或执行旧版结构门禁。

## 判定规则

| 结果 | 含义 | 后续处理 |
|---|---|---|
| 通过 | lint、独立评审、覆盖、追踪、方法应用、core rules 和动态来源应用均满足要求 | 可以输出方案 |
| 警告 | 存在非阻断问题、依据不足或局部待人工分析确认风险 | 记录原因，必要时把相关预期结果改为 `待人工分析确认` |
| 失败 | 确定性 lint 失败、核心需求不可追踪、必选方法无承接、core rules/动态来源应用失败或独立评审阻断 | 修正后重跑对应检查 |

失败项分为四类处理：

- 确定性校验失败：结构、编号、字段、语法和固定路径问题。必须按脚本输出修正后重跑 lint；最终一致性问题必须在输出收口阶段修正后重跑 `check-artifact-consistency.py`。
- 输出质量失败：例如测试点/测试点明细完整用例化、核心粒度不合理、预期结果为空或事实编造。必须修正输出后重跑独立评审和覆盖审查。
- 需求信息缺失：例如核心规则、终态、权限范围或接口契约无法确认。登记 `CP-REVIEW` 过程候选，并把相关叶子节点的 `预期结果` 写成 `待人工分析确认`。
- Dynamic/core 应用失败：core rules 未被遵守，或 `sources[]` 可见动态来源未被对应阶段读取、应用或解释。必须补读、补齐应用记录或修正输出后重审。

## 输出

输出写入 `reports/coverage-review.json`，结构以 `templates/coverage-review-json-template.json` 为准；如需人读版，由 `bin/render-run-markdown.py` 渲染。`templates/coverage-review-template.md` 仅作为渲染后 Markdown 样式参考。

审查输出必须包含：

- `artifactType` 固定为 `coverage-review`，`schemaVersion` 固定为 `1.0`。
- `result` 使用 `通过`、`警告`、`失败`、`需修正` 或 `不适用`。
- `findings[]` 记录覆盖问题、质量门禁结果和需要返工的位置。
- `blockingIssues[]` 只记录阻断交付的问题。
- `recommendations[]` 记录非阻断修正建议。
- `evidenceRefs[]` 记录需求、设计方案、主交付件、过程产物、core rules、动态来源或 quality gate 的证据来源。
- `qualityGates[]` 记录覆盖类 gate 的结构化结果。
- `rulesApplications[]` 记录适用 rules 的应用、解释不适用、冲突或用户指令覆盖情况。
- `projectKnowledgeApplications[]` 记录动态来源和附加门禁的读取与应用状态。
- `coverageGaps[]` 记录可定位到需求或主交付件位置的覆盖缺口。
- 确定性校验结果：lint 脚本名称、通过/失败、关键失败项；最终一致性检查结果可在输出收口阶段补充。
- 独立评审结论：只引用结论和阻断项，不重复展开所有结构规则。
- 每个覆盖类 quality gate 的结果和失败/警告项。
- task-list 中固定阶段的状态和异常项。
- 必选方法是否都有主交付件承接、方法证据或过程缺口。
- 适用分析维度是否落到主交付件，而不是只停留在结构化过程记录。
- 需求依据和方法证据是否可追踪。
- core rules 应用状态，包括适用 rules 是否已遵守、解释不适用、被当前用户明确指令覆盖，或与输入冲突并完成覆盖留痕。
- 动态来源应用状态，包括每个已读取来源是否已应用、解释不适用或进入缺口兜底。
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
- 如需核对 project/personal 附加检查要求，只能按 `sources[]` 中对本阶段可见的来源或当前需求明确指向的文件补读相关章节，并在审查输出中记录来源；不得全目录搜索或全量复制大文件。
- 对本阶段可见且被读取的动态来源必须留痕；前序阶段缺少已读取来源应用记录时，不得静默通过。
