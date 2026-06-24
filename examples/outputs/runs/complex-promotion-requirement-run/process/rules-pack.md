# 强制规则索引

## 优先级策略

| 策略项 | 说明 |
|---|---|
| currentUserInstruction | 当前用户明确指令最高；只有当前用户明确指令可以覆盖 rules。 |
| runtimeContract | AGENTS、workflow、skill、schema 和固定脚本定义执行契约；rules 不能要求违反运行时契约，除非用户明确要求修改框架。 |
| rules | rules 是强制约束，按 core > project > user 处理，优先于输入文档、memory 和 knowledge。 |
| inputDocuments | 需求、设计方案和已评审测试分析方案是业务事实来源；与 rules 冲突时默认遵守 rules 并记录覆盖原因。 |
| memoryKnowledge | memory 和 knowledge 只能补充风险、偏好、方法或经验；与输入文档或 rules 冲突时不得覆盖。 |

## 加载策略

| 策略项 | 说明 |
|---|---|
| indexOnly | rules-pack 只索引规则元数据，不内联规则正文。 |
| stageRequired | 后续阶段必须筛选 availableStages 包含当前阶段或 `*` 的 ruleSources，并读取对应 Markdown 正文后再执行。 |
| applicationRecord | 读取、应用、未应用或被当前用户指令覆盖的 rules，必须在阶段产物、review 或 coverage 中留痕。 |

## 规则来源索引

无。

## 未扫描项目规则

| 路径 | 原因 |
|---|---|
| rules/projects/ | project-key 未唯一确定 |

## 告警

无告警。
