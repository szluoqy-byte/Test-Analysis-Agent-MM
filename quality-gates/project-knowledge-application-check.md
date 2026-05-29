# 质量门禁：Project Knowledge 应用检查

## 目的

确保 `process/context-pack.md` 中登记的项目知识阶段绑定被对应流程环节实际读取、应用或解释跳过，避免 project knowledge 只被发现但未参与测试分析设计。

## 必需输入

- `process/context-pack.md` 中的“项目知识阶段绑定”表。
- 过程报告中的 Project Knowledge 应用记录。
- 测试技术路由、测试点明细、测试分析方案、测试设计方案、独立评审和覆盖审查结果。

## 失败条件

- context pack 绑定了 project knowledge 到某个阶段，但过程报告或对应阶段输出没有应用记录。
- 应用状态不是 `applied`、`not_applicable`、`insufficient_evidence`、`conflict_with_requirement` 或 `deferred_to_review`。
- 绑定到 `test-analysis-solution-review`、`test-design-solution-review` 或 `coverage-review` 的 checklist 未被读取。
- checklist 明确指出核心漏覆盖，但输出既未补充测试点/测试点明细/测试设计项，也未给出不适用或依据不足说明。
- project knowledge 被用于覆盖 core 输出契约、字段、类型、质量门禁或需求/设计方案中的明确事实。

## 警告条件

- project knowledge 被读取但应用位置描述过泛，无法追踪到路由、测试点、测试点明细、测试设计项或检查结论。
- 文件被识别为 `unclassified`，但没有后续补读建议。
- 同一 project knowledge 在多个阶段应用状态不一致且没有解释。

## 通过条件

- 每个绑定文件在对应阶段都有应用记录。
- 每条应用记录都有来源文件、当前阶段、应用状态、应用位置和说明。
- 未应用的文件都有明确的 `not_applicable`、`insufficient_evidence` 或 `conflict_with_requirement` 原因。
- checklist 类文件在独立评审或覆盖审查中有明确检查结论。
