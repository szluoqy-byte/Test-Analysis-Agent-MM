# 动态来源应用门禁

动态 project/personal knowledge 来源由 `context-source-indexing` 写入 `process/context-pack.json`。强制规则由 `process/rules-pack.json` 独立索引，不作为普通动态来源处理。后续阶段只读取对本阶段可见的来源正文；适用 rules 还必须按 `ruleSources[]` 的 `path` 读取 Markdown 正文并遵守。

## 检查项

- 可见来源被读取后，必须记录应用状态。
- 应用状态只能使用 `applied`、`not_applicable`、`insufficient_evidence`、`conflict_with_requirement` 或 `deferred_to_review`。
- 来源应用位置应能追踪到路由、测试点、测试用例、review finding 或 coverage finding。
- 动态来源不得覆盖 `process/rules-pack.json` 中当前阶段可见且已读取正文的适用 rules、当前用户明确指令或输入文档事实。

## 问题示例

- checklist 明确指出核心漏覆盖，但输出既未补充测试点或测试用例，也未给出不适用说明。
- 来源被读取但应用位置过泛，无法定位到具体产物或检查结论。
