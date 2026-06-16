# 上下文应用门禁

本文件是 `coverage-review` 的私有参考，用于检查 core rules 和 `process/context-pack.json` 中动态 project/personal 来源是否被后续阶段正确读取、应用或解释跳过。

## 1. Core Rules 应用检查

### 目的

确保根目录 `rules/*.md` 中的 core rules 被后续流程实际遵守。Rules 的优先级低于当前用户明确指令，高于当前输入文档、memory 和 knowledge。

### 必需输入

- 根目录 `rules/*.md`。
- 结构化过程记录、review JSON 或 coverage JSON 中的 rules 应用记录。
- 测试分析方案或测试设计方案。
- 当前用户明确指令摘要。
- 当前输入文档摘要。

### 通过条件

- 适用 core rules 已有应用状态，或其不适用原因清晰。
- 与输入冲突的 rules 已记录覆盖原因。
- 用户明确指令覆盖 rules 时，有清晰留痕。

### 失败条件

- 输出与 core rules 冲突，且没有当前用户明确指令作为覆盖依据。
- rules 与输入文档冲突时，输出采用了输入文档而未说明原因。
- rules 被当作普通 knowledge 启发处理，没有强制执行或冲突留痕。
- project/personal 动态 rules 覆盖了 core rules。

### 警告条件

- rules 适用范围描述过泛，导致应用位置难以追踪。
- rules 文件被读取但未说明 `applied`、`not_applicable` 或 `conflict_with_requirement`。
- rules 与输入冲突较多，说明规则集需要拆分或缩小适用范围。

## 2. 动态来源应用检查

### 目的

确保 `process/context-pack.json` 中 `sources[]` 对各阶段可见的 project/personal 动态来源被对应流程环节实际读取、应用或解释跳过，避免动态来源只被索引但未参与测试分析设计。

### 必需输入

- `process/context-pack.json` 的 `sources[]`。
- 结构化过程记录、review JSON 或 coverage JSON 中的动态来源应用记录。
- 测试技术路由、测试点明细、测试分析方案、测试设计方案、独立评审和覆盖审查结果。

### 通过条件

- 对当前阶段可见且被读取的动态来源都有应用记录。
- 每条应用记录都有来源文件、当前阶段、应用状态、应用位置和说明。
- 未应用的文件都有明确的 `not_applicable`、`insufficient_evidence` 或 `conflict_with_requirement` 原因。
- checklist 类动态来源默认在覆盖审查中有明确检查结论；被额外用于独立评审时，独立评审也有明确应用记录。

### 失败条件

- `sources[]` 中对某阶段可见的动态来源被读取，但结构化过程记录或对应阶段输出没有应用记录。
- 应用状态不是 `applied`、`not_applicable`、`insufficient_evidence`、`conflict_with_requirement` 或 `deferred_to_review`。
- 对 `coverage-review` 可见的 checklist 未被读取，也未解释不适用。
- checklist 明确指出核心漏覆盖，但输出既未补充测试点、测试点明细或测试设计项，也未给出不适用或依据不足说明。
- 动态来源被用于覆盖 core 输出契约、字段、类型、质量门禁或需求/设计方案中的明确事实。

### 警告条件

- 动态来源被读取但应用位置描述过泛，无法追踪到路由、测试点、测试点明细、测试设计项或检查结论。
- 同一动态来源在多个阶段应用状态不一致且没有解释。
- `sources[]` 中存在对当前阶段可见的来源，但阶段输出没有说明是否读取；若该来源明显与当前需求无关，可补充 `not_applicable`。
