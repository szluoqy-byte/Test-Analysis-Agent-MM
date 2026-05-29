# 记忆上下文包模板

构建当前运行目录下的 `process/context-pack.md` 时使用以下结构。

```markdown
# 记忆上下文包

## 来源需求

- 文档：
- 生成时间：
- 关键词：

## 项目标识

- project-key：
- 确定依据：
- 未确定原因：

## 个人配置标识

- personal-key：
- 确定依据：
- 使用路径：
- 默认 personal 说明：

## 已扫描来源

- core：
- project：
- personal：

## 命中摘要

| 来源 | 片段 | 命中原因 | 使用方式 |
|---|---|---|---|

## Project/Personal 使用摘要

| 层级 | 绑定结果 | 命中来源 | 未采用来源 | 冲突处理 | 后续补读建议 |
|---|---|---|---|---|---|
| project |  |  |  |  |  |
| personal |  |  |  |  |  |

## 项目知识阶段绑定

| 来源文件 | 自理解类型 | 判断依据 | 强制应用环节 | 读取策略 | 应用留痕要求 |
|---|---|---|---|---|---|
|  | 测试设计因子库/测试设计模式库/测试设计Checklist/风险画像/Oracle/路由说明/术语表/unclassified | 文件名、frontmatter、标题或摘要 | testing-method-router / testpoint-generation / test-analysis-solution-generation / test-analysis-solution-review / test-design-solution-generation / test-design-solution-review / coverage-review 等 | 阶段开始前按相关章节或关键词读取，不全量复制大文件 | 输出 applied / not_applicable / insufficient_evidence / conflict_with_requirement / deferred_to_review |

## 相关项目事实

## 相关领域术语

## 相关项目知识补充

## 相关个人补充

## 相关历史缺陷和风险模式

## 相关项目测试经验

## 输出偏好

## 约束和非范围

## 已检索但未注入的 Memory

## 已检索但未注入的 Project/Personal 补充

## 大文件来源与后续补读建议

| 来源文件 | 命中原因 | 建议章节/关键词 | 未注入原因 |
|---|---|---|---|
```

## 选择策略

- 只注入能改善本次分析的 memory。
- project/personal 补充只注入与当前需求直接相关的风险画像、覆盖策略、术语映射、路由说明、模板偏好、附加门禁、个人检查偏好或测试 oracle 补充。
- project knowledge 文件名没有硬性要求；构建 context pack 时必须基于文件名、frontmatter、标题、章节和少量摘要自理解识别用途，并在“项目知识阶段绑定”中登记强制应用环节。
- context pack 不提前判断测试设计模式或 checklist 的具体命中项，只登记文件类型、适用环节和后续读取策略。
- 优先匹配模块、角色、对象、状态、接口或项目历史缺陷。
- 每条内容保持简洁，并标记来源 memory 文件或来源章节。
- 不注入通用测试理论；通用测试理论从 `knowledge/` 获取，`skills/` 只定义分析动作。
- 不用 project/personal 补充覆盖 core 层中的核心类型、字段、级别、交付件契约和质量门禁。
- 不把 personal 层内容当作项目事实或团队共识。
- 事实/契约冲突以当前需求和 project memory 为准；输出偏好冲突以当前用户指令和 personal 偏好优先，但不得违反事实和质量门禁。
- 大文件只记录来源、命中原因和建议补读范围，不整文件注入；后续 skill 可按来源文件和相关章节受控补读。
- 被绑定到某个阶段的 project knowledge，后续阶段必须读取、应用或解释不适用，并在方法证据、过程报告或覆盖审查中留痕。
- 构建 context pack 时不修改长期 memory 源文件。
