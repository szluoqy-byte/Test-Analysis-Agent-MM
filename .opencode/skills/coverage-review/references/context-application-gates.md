# 上下文应用门禁

本文件是 `coverage-review` 的私有参考，用于检查 `process/context-pack.json` 中发现的 rules、project knowledge 和附加门禁是否被后续阶段正确读取、应用或解释跳过。

## 1. Rules 应用检查

### 目的

确保 `process/context-pack.json` 中登记的 applicable rules 被后续流程实际遵守。Rules 的优先级低于当前用户明确指令，高于当前输入文档、memory 和 knowledge。

### 必需输入

- `process/context-pack.json` 中的“适用强制规则”结构。
- 结构化过程记录、review JSON 或 coverage JSON 中的 Rules 应用记录。
- 测试分析方案或测试设计方案。
- 当前用户明确指令摘要。
- 当前输入文档摘要。

### 通过条件

- 每条适用 rules 都有应用状态。
- 与输入冲突的 rules 已记录覆盖原因。
- 未应用的 rules 有明确不适用原因。
- 用户明确指令覆盖 rules 时，有清晰留痕。

### 失败条件

- context pack 登记了适用 rules，但生成、评审或覆盖审查阶段没有应用记录。
- 输出与适用 rules 冲突，且没有当前用户明确指令作为覆盖依据。
- rules 与输入文档冲突时，输出采用了输入文档而未说明原因。
- rules 被当作普通 knowledge 启发处理，没有强制执行或冲突留痕。
- project/personal rules 覆盖了 core rules，且没有当前用户明确指令。

### 警告条件

- rules 适用范围描述过泛，导致应用位置难以追踪。
- rules 文件被读取但未说明 `applied`、`not_applicable`、`overridden_by_user` 或 `conflict_recorded`。
- rules 与输入冲突较多，说明规则集需要拆分或缩小适用范围。

## 2. Project Knowledge 应用检查

### 目的

确保 `process/context-pack.json` 中登记的项目知识阶段绑定被对应流程环节实际读取、应用或解释跳过，避免 project knowledge 只被发现但未参与测试分析设计。

### 必需输入

- `process/context-pack.json` 中的“项目知识阶段绑定”结构。
- 结构化过程记录、review JSON 或 coverage JSON 中的 Project Knowledge 与附加门禁应用记录。
- 测试技术路由、测试点明细、测试分析方案、测试设计方案、独立评审和覆盖审查结果。

### 通过条件

- 每个绑定文件在对应阶段都有应用记录。
- 每条应用记录都有来源文件、当前阶段、应用状态、应用位置和说明。
- 未应用的文件都有明确的 `not_applicable`、`insufficient_evidence` 或 `conflict_with_requirement` 原因。
- checklist 类文件默认在覆盖审查中有明确检查结论；被额外绑定到独立评审时，独立评审也有明确应用记录。

### 失败条件

- context pack 绑定了 project knowledge 到某个阶段，但结构化过程记录或对应阶段输出没有应用记录。
- 应用状态不是 `applied`、`not_applicable`、`insufficient_evidence`、`conflict_with_requirement` 或 `deferred_to_review`。
- 绑定到 `coverage-review` 的 checklist 未被读取；如果 context pack 明确把 checklist 额外绑定到 `test-analysis-solution-review` 或 `test-design-solution-review`，对应独立评审也必须读取并留痕。
- checklist 明确指出核心漏覆盖，但输出既未补充测试点、测试点明细或测试设计项，也未给出不适用或依据不足说明。
- project knowledge 被用于覆盖 core 输出契约、字段、类型、质量门禁或需求/设计方案中的明确事实。

### 警告条件

- project knowledge 被读取但应用位置描述过泛，无法追踪到路由、测试点、测试点明细、测试设计项或检查结论。
- 文件被识别为 `unclassified`，但没有后续补读建议。
- 同一 project knowledge 在多个阶段应用状态不一致且没有解释。
