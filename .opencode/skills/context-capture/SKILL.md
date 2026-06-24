---
name: context-capture
description: 当用户要求记住、记录、收录、归档或沉淀个人偏好、项目知识、强制规则、测试设计 checklist、历史缺陷、测试经验或输出偏好时使用；负责判断内容应进入 rules、memory 还是 knowledge，以及 personal/project 层级。
---

# 上下文归档

本 skill 负责把用户明确要求长期保留的信息分类写入 `rules/`、`memory/` 或 `knowledge/`。它不是一次运行的 context pack 构建器，而是长期上下文维护入口。

## 触发信号

- “记住我的偏好”
- “以后输出都按这个风格”
- “把这个 checklist 收进项目知识”
- “把这个历史缺陷记下来”
- “这套测试设计模式后续都要用”
- “这条规则以后必须遵守”
- “这个约束优先于需求/设计输入”
- “归档到 personal / project / knowledge / memory”
- “归档到 rules”

## 分类规则

| 信息类型 | 默认归档位置 |
|---|---|
| Agent 包全局强制规则、跨项目必须遵守的输出/流程约束 | `rules/*.md`，仅在用户明确要求修改框架规则时写入 |
| 项目强制规则、项目级必须遵守且优先于输入文档的约束 | `rules/projects/<project-key>/` 下语义清晰的 Markdown 文件 |
| 个人本地强制规则、个人审核时必须遵守的约束 | `rules/user/` 下语义清晰的 Markdown 文件 |
| 个人输出偏好、沟通偏好、本地使用习惯 | `memory/user/preferences.md` |
| 个人测试启发、个人检查清单、个人常用测试设计方法 | `knowledge/user/test-design-notes.md` 或 `knowledge/user/test-design-checklist.md` |
| 项目事实、项目约束、团队输出偏好、项目术语事实 | `memory/projects/<project-key>/project-memory.md` |
| 项目历史缺陷、复盘经验、团队测试习惯 | `memory/projects/<project-key>/testing-experience.md` |
| 项目测试设计 checklist、测试设计模式、测试 Oracle、覆盖策略、路由补充 | `knowledge/projects/<project-key>/` 下语义清晰的 Markdown 文件 |
| Agent 框架方法论、通用测试技术、主流程规则 | 仅在用户明确要求修改框架时写入根目录 `knowledge/`、`skills/` 或 `docs/` |

## 写入流程

1. 判断用户是否明确要求长期记录。没有明确记录意图时，只给建议，不落盘。
2. 判断层级：personal、project 或 core。
3. 判断类型：带有“必须/禁止/优先于输入/强制执行”语义的约束归 `rules`；事实/偏好/历史经验归 `memory`；稳定测试知识、模式、checklist 和 Oracle 归 `knowledge`。
4. 如果需要 `project-key` 但无法唯一确定，先问一个简短问题；不要扫描所有项目目录正文，也不要跨项目写入。
5. 如果目标文件不存在，可以创建；如果存在，只追加条目，不覆盖已有内容。
6. 条目应包含：
   - 日期。
   - 来源：用户明确输入。
   - 适用范围。
   - 内容。
   - 使用方式或不应使用的边界。
7. 写入后简要告诉用户写入位置和归档理由。

## 冲突处理

- rules 优先级低于当前用户明确指令，但高于输入文档、memory 和 knowledge。
- rules 在 run 内由 `bin/build-rules-pack.py` 索引到 `process/rules-pack.json`，不通过 `process/context-pack.json` 承载强制语义；后续阶段按 `ruleSources[]` 读取适用规则正文。
- personal rules 不能覆盖 project rules 或 core rules。
- personal 不能覆盖 project 或 core。
- project/personal 动态来源不能覆盖根目录 `knowledge/` 的核心标准、字段、输出契约和质量门禁。
- memory 或 knowledge 与当前输入文档冲突时，当前输入文档优先；长期记录只能作为风险、偏好或风险来源。
- rules 与当前输入文档冲突时，默认遵守 rules 并记录覆盖原因；只有当前用户明确指令可以覆盖 rules。
- 未确认业务事实不得写成项目事实；应暂不归档，或仅作为风险/偏好记录且标明输入不足。

## 推荐条目格式

```markdown
## YYYY-MM-DD <简短标题>

- 来源：用户明确输入
- 层级：personal | project:<project-key>
- 类型：强制规则 | 偏好 | 项目事实 | 历史经验 | 测试设计 checklist | 测试设计模式 | Oracle | 覆盖策略
- 适用范围：<何时使用>
- 内容：<需要长期保留的信息>
- 使用边界：<不得如何使用，或与需求冲突时如何处理>
```

## 约束

- 不把一次性任务结论写进长期文件，除非用户明确要求沉淀。
- 不把用户个人偏好写成团队共识。
- 不把通用测试理论复制进 memory。
- 不直接编辑 `.opencode/skills/`、`.opencode/agents/`、`.testagent/skills/` 或 `.testagent/agents/`。
