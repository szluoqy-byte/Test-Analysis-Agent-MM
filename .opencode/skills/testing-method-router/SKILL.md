---
name: testing-method-router
description: 在需求结构化之后使用，用于根据需求片段的分析维度和触发信号选择合适的测试技术和专项分析 skill，例如边界值、等价类、状态迁移、决策表、场景流、权限矩阵、接口契约、数据一致性和组合兼容。
---

# 测试分析维度与测试技术路由 Skill

本 skill 用来决定“该从哪些分析维度审视这段需求，以及该用什么测试技术分析”。它是防止 Agent 泛泛生成测试点的关键环节。

本 skill 路由的是本项目内部专项分析 skill 和其对应测试技术，不提前选择测试点明细展开结果，不建议明细数量，也不决定测试步骤或预期结果。

## 输入

- 结构化需求模型。
- 记忆上下文包。
- 记忆上下文包中命中的 project/personal 覆盖策略、风险画像、个人关注点和路由补充。
- `process/context-pack.md` 中绑定到 `testing-method-router` 的 project knowledge 文件，例如测试设计因子库、测试设计模式库、风险画像、覆盖策略或路由说明。
- `knowledge/test-analysis-methodology.md`。
- `knowledge/test-method-routing-matrix.md`。
- `quality-gates/coverage-check.md`。

## 分析步骤

1. 读取 context pack 的“项目知识阶段绑定”。如果存在绑定到 `testing-method-router` 的 project knowledge，先按来源文件、相关章节、关键词或标题读取，不全量复制大文件。
2. 逐条扫描需求片段，先识别分析维度：需求可测性、风险、业务场景、数据域、规则组合、状态、权限、接口、数据一致性、组合兼容、非功能质量属性和经验缺陷模式。
3. 识别每个分析维度下的触发信号。
4. 结合 context pack 中的 project/personal knowledge 和本阶段绑定文件，补充识别项目特有风险、覆盖要求或测试技术倾向；补充只能提高关注度，不能覆盖根目录 knowledge 的路由矩阵和核心标准。
5. 将触发信号映射到一个或多个测试技术和专项分析 skill。
6. 将方法标记为 `必选`、`可选` 或 `不适用`。
7. 根据需求明确程度标记置信度：`高`、`中`、`低`。
8. 说明选择或跳过某个维度/方法的原因。
9. 对影响方法必要性的范围不确定项登记待确认候选。
10. 记录本阶段 project knowledge 应用状态，并将分析维度和测试技术路由结果传递给测试点生成阶段。

## 路由判定细则

| 判定 | 使用条件 |
|---|---|
| `必选` | 需求中出现明确触发信号，跳过会造成覆盖缺口 |
| `可选` | 需求存在弱触发信号，适合补充风险覆盖但不影响主结论 |
| `不适用` | 当前需求没有相关对象、规则或风险信号 |

置信度判定：

- `高`：需求依据明确，方法和覆盖对象可以直接确定。
- `中`：触发信号明确，但范围、边界或异常处理仍有缺口。
- `低`：只有弱信号或来自 memory/历史经验，需要作为风险确认点或待确认候选。

## 输出

| 需求片段 | 分析维度 | 触发信号 | 适用测试技术 | 调用 skill | 必要性 | 置信度 | 说明 |
|---|---|---|---|---|---|---|---|

如存在方法范围待确认候选，追加输出统一 `CQ-*` 候选表：

| 问题ID | checkpoint | sourceStage | header | question | why | impact | options | blockingLevel | priority | askPolicy | mustAsk | relatedRequirement | memoryConflict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

如本阶段绑定了 project knowledge，追加应用记录：

| 来源文件 | 当前阶段 | 应用状态 | 应用位置 | 说明 |
|---|---|---|---|---|

## 路由规则

- 分析维度以 `knowledge/test-analysis-methodology.md` 为准。
- 路由矩阵以 `knowledge/test-method-routing-matrix.md` 为准。
- 覆盖要求以 `quality-gates/coverage-check.md` 为准。
- project/personal knowledge 补充以当前 run 的 `process/context-pack.md` 为准，只能补充关注点和原因；personal 层不能覆盖 project 层或 core 层约束。
- 绑定到本阶段的 project knowledge 必须读取并留痕；如果未应用，必须使用 `not_applicable`、`insufficient_evidence`、`conflict_with_requirement` 或 `deferred_to_review` 解释。
- 本 skill 只负责把当前需求片段映射到测试技术和专项分析 skill，并说明选择或跳过原因。
- 同一需求片段可路由到多个测试技术；后续由 `testpoint-generation` 合并重复测试点。
- 测试点明细阶段如何应用测试技术由 `test-analysis-solution-generation` 统一选择，本 skill 不提前映射或替代。

## 约束

- 跳过某个明显相关的测试技术时，必须给出原因。
- 被标记为 `必选` 的测试技术，最终必须生成测试点或待确认问题。
- 被标记为 `必选` 的测试技术可以由方法证据、场景测试点、接口契约分析候选或待确认问题承接；不得把覆盖缺口留给测试分析方案生成、评审或细化环节重新分析原始需求来补洞。
- 性能、安全、兼容等范围不确定时，默认登记为 `Important` 待确认候选。
- 本 skill 不直接向用户提问。
- 不直接生成最终测试点，只输出测试技术路由和待确认候选。
- 如果 context pack 中的 project/personal 覆盖策略不足，只能按 context pack 记录的来源或当前需求明确指向的文件补读相关章节，并在路由说明中记录来源；不得全目录搜索或全量复制大文件。
