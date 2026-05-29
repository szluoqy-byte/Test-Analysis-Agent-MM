# 质量门禁：Rules 强制规则应用检查

## 目的

确保 `process/context-pack.md` 中登记的 applicable rules 被后续流程实际遵守。Rules 的优先级低于当前用户明确指令，高于当前输入文档、memory 和 knowledge。

## 必需输入

- `process/context-pack.md` 中的“适用强制规则”表。
- 过程报告中的 Rules 应用记录。
- 测试分析方案或测试设计方案。
- 当前用户明确指令摘要。
- 当前输入文档摘要。

## 失败条件

- context pack 登记了适用 rules，但生成、评审或覆盖审查阶段没有应用记录。
- 输出与适用 rules 冲突，且没有当前用户明确指令作为覆盖依据。
- rules 与输入文档冲突时，输出采用了输入文档而未说明原因。
- rules 被当作普通 knowledge 启发处理，没有强制执行或冲突留痕。
- project/personal rules 覆盖了 core rules，且没有当前用户明确指令。

## 警告条件

- rules 适用范围描述过泛，导致应用位置难以追踪。
- rules 文件被读取但未说明 `applied`、`not_applicable`、`overridden_by_user` 或 `conflict_recorded`。
- rules 与输入冲突较多，说明规则集需要拆分或缩小适用范围。

## 通过条件

- 每条适用 rules 都有应用状态。
- 与输入冲突的 rules 已记录覆盖原因。
- 未应用的 rules 有明确不适用原因。
- 用户明确指令覆盖 rules 时，有清晰留痕。
