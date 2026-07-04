---
name: testing-method-router
description: 在需求结构化之后使用，用于根据需求片段的分析维度和触发信号选择合适的测试技术和专项方法参考，例如边界值、等价类、状态迁移、决策表、场景流、权限矩阵、接口契约、数据一致性和组合兼容。
---

# 测试分析维度与测试技术路由 Skill

本 skill 用来决定“该从哪些分析维度审视这段需求，以及该用什么测试技术分析”。它是防止 Agent 泛泛生成测试点的关键环节。

本 skill 路由的是本项目内部专项方法参考和其对应测试技术，不提前选择测试点展开结果，不建议明细数量，也不决定测试步骤或预期结果。

测试技术和专项方法是生成参考，不是最终交付件的固定来源清单。后续生成可以综合多个方法、跳出单一方法模板，或基于输入事实补充更合适的测试点；最终主交付件只要求业务依据可追溯，不输出 `methodRefs[]`。

## 何时使用

在 `input-fact-modeling` 完成后、`test-analysis-solution-generation` 之前使用。不要在 SC/TP/TC 已生成后倒推方法引用，也不要把本 skill 当作 coverage-review。

## 输入

- 输入事实模型。
- `process/rules-pack.json` 中对 `testing-method-router` 可见的 core/project/user rules 索引及对应 Markdown 正文。
- 上下文来源索引。
- `process/context-pack.json` 中 `sources[]` 对 `testing-method-router` 可见的 project/personal 覆盖策略、风险画像、个人关注点和路由补充。
- `knowledge/test-workflow-boundaries.md`。
- `references/test-method-routing-matrix.md`。
- `references/*.md` 中的专项方法参考。
- `skills/coverage-review/references/coverage-check.md`。

## 分析步骤

1. 读取 `process/rules-pack.json`，筛选 `ruleSources[]` 中 `availableStages` 包含 `testing-method-router` 或 `"*"` 的 rules，并读取对应 `path` 的 Markdown 正文；路由选择必须遵守适用 rules。
2. 读取 `process/context-pack.json`，筛选 `availableStages` 包含 `testing-method-router` 或 `"*"` 的动态来源；如需使用，按来源文件、相关章节、关键词或标题读取正文，不全量复制大文件。
3. 逐条扫描输入事实模型中的事实、约束/条件和可观察结果，先识别分析维度：需求可测性、风险、业务场景、数据域、规则组合、状态、权限、接口、数据一致性、组合兼容、非功能质量属性和经验缺陷模式。
4. 识别每个分析维度下的触发信号。
5. 结合本阶段可见的 project/personal 动态来源，补充识别项目特有风险、覆盖要求或测试技术倾向；补充只能提高关注度，不能覆盖 rules、根目录 knowledge 的路由矩阵和核心标准。
6. 将触发信号映射到一个或多个测试技术和专项方法参考。
7. 将方法标记为 `必选`、`可选` 或 `不适用`。
8. 根据需求明确程度标记置信度：`高`、`中`、`低`。
9. 说明选择或跳过某个维度/方法的原因。
10. 对范围不确定项只做自动适用性判断：明确触发信号标记 `必选`，弱触发信号标记 `可选`，完全无依据标记 `不适用`；不创建问题队列。
11. 记录本阶段 rules 与动态来源应用状态，并将分析维度和测试技术路由结果传递给测试分析方案生成阶段。

## 路由判定细则

| 判定 | 使用条件 |
|---|---|
| `必选` | 需求中出现明确触发信号，跳过会造成覆盖缺口 |
| `可选` | 需求存在弱触发信号，适合补充风险覆盖但不影响主结论 |
| `不适用` | 当前需求没有相关对象、规则或风险信号 |

置信度判定：

- `高`：需求依据明确，方法和覆盖对象可以直接确定。
- `中`：触发信号明确，但范围、边界或异常处理仍有缺口。
- `低`：只有弱信号或来自 memory/历史经验，只能作为可选风险关注，不创建问题队列。

## 输出

| 需求片段 | 分析维度 | 触发信号 | 适用测试技术 | 方法参考 | 必要性 | 置信度 | 说明 |
|---|---|---|---|---|---|---|---|

如本阶段读取了动态来源，追加应用记录：

| 来源文件 | 当前阶段 | 应用状态 | 应用位置 | 说明 |
|---|---|---|---|---|

## 路由规则

- 工作流术语和分析/设计边界以 `knowledge/test-workflow-boundaries.md` 为准。
- 强制规则以 `process/rules-pack.json` 为准；rules 与输入文档冲突时，默认遵守 rules 并记录覆盖原因。
- 分析维度和路由矩阵以 `references/test-method-routing-matrix.md` 为准。
- 覆盖要求以 `skills/coverage-review/references/coverage-check.md` 为准。
- project/personal 动态来源补充以当前 run 的 `process/context-pack.json` `sources[]` 为准，只能补充关注点和原因；personal 层不能覆盖 project 层或 core 层约束。
- 对本阶段可见且被读取的动态来源必须留痕；如果未应用，必须使用 `not_applicable`、`insufficient_evidence`、`conflict_with_requirement` 或 `deferred_to_review` 解释。
- 本 skill 只负责把当前需求片段映射到测试技术和专项方法参考，并说明选择或跳过原因。
- 同一需求片段可路由到多个测试技术；后续由 `test-analysis-solution-generation` 合并重复测试点。
- 测试点阶段如何应用测试技术由 `test-analysis-solution-generation` 统一选择，本 skill 不提前映射或替代。

## 约束

- 跳过某个明显相关的测试技术时，必须给出原因。
- 被标记为 `必选` 的测试技术表示该维度需要被重点参考；最终应通过有依据的场景或测试点体现其关注对象，但不要求输出独立方法记录或 `methodRefs[]`。
- 专项方法参考不得限制最终测试点的表达方式；如果输入事实支持更直接的业务测试点，优先输出业务可读的 TP。
- 性能、安全、兼容等范围不确定时，默认标记为 `可选` 或 `不适用`，不创建问题队列。

## 验证闭环

路由结果交给 `test-analysis-solution-generation` 前，检查每条被标记为 `必选` 的技术都有明确事实依据和说明；被跳过的明显相关技术必须有原因。若读取了 project/personal 动态来源，记录应用状态，避免后续阶段误以为所有来源都已被正文读取。
- 本 skill 不直接向用户提问。
- 不直接生成最终测试点，只输出测试技术路由和动态来源应用记录。
- 如果可见动态来源中的 project/personal 覆盖策略不足，只能按 `sources[]` 记录的可见来源或当前需求明确指向的文件补读相关章节，并在路由说明中记录来源；不得全目录搜索或全量复制大文件。
