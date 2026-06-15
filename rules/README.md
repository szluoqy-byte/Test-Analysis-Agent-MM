# Rules 模块说明

Rules 保存本 Agent 的强制规则。它不是测试知识库，也不是长期事实库；它用于声明当前运行必须遵守的约束。

## 优先级

在本仓库的运行决策中，优先级为：

```text
当前用户明确指令
  > rules 强制规则
  > 当前输入文档（需求 / 设计方案 / 已评审测试分析方案）
  > memory
  > knowledge
  > skill 默认流程
```

如果 rules 与输入文档冲突，默认遵守 rules，并在 `process/context-pack.json` 或结构化 review/coverage JSON 中记录“规则覆盖输入”的原因。只有当前用户明确指令可以覆盖 rules；同名 Markdown 只作为脚本渲染的人读版。

Rules 内部冲突时，按 `core > project > personal` 处理；project/personal rules 可以细化更高层规则，但不得放宽或违反更高层强制约束。

## 分层结构

| 层级 | 路径 | 默认提交 Git | 说明 |
|---|---|---|---|
| core | `rules/*.md` | 是 | Agent 包内置的全局强制规则 |
| project | `rules/projects/<project-key>/**/*.md` | 否 | 指定项目的强制规则，确定 `project-key` 后读取 |
| personal | `rules/user/**/*.md` | 否 | 当前使用者的本地强制规则，不能覆盖 core/project rules |

`rules/projects/` 和 `rules/user/` 默认由 `.gitignore` 忽略，只保留 README。团队确实需要共享某个项目规则时，可以显式强制添加。

## 规则写法

每个规则文件建议使用 Markdown 标题和简短条目，推荐包含：

```markdown
# <规则集名称>

## 适用范围

- project-key：
- 适用模块：
- 适用阶段：input-fact-modeling / test-analysis-solution-generation / test-design-solution-generation / review / coverage-review

## 强制规则

| 规则 ID | 规则 | 冲突处理 |
|---|---|---|
| RULE-001 | <必须/禁止/优先采用的规则> | 与输入冲突时遵守本规则，并记录覆盖原因 |
```

## 使用边界

- Rules 可以强制输出结构、术语、字段、覆盖策略、判定优先级或项目约束。
- Rules 不用于沉淀通用测试方法；通用方法放在 `knowledge/`。
- Rules 不用于沉淀历史经验或事实记忆；事实和经验放在 `memory/`。
- Rules 应尽量明确适用范围，避免写成宽泛口号。
- Rules 不应要求违反系统级约束、仓库运行路径规则或当前用户明确指令。
