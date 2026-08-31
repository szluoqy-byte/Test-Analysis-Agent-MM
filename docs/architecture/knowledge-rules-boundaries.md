# Knowledge / Rules 边界

本文件说明信息源职责和优先级。docs 只解释边界，不作为运行时事实源。

## 分工

| 类型 | 内容 | 示例 |
|---|---|---|
| `skills/` | 流程动作、生成步骤、评审步骤和脚本调用约束 | workflow、generation、review |
| `knowledge/` | 测试标准、测试技术、写作规范，以及 project/user 的测试经验补充 | SC/TP/TC 标准、测试技术、项目历史缺陷、测试设计 checklist |
| `rules/` | 必须遵守的强制规则，包括用户明确要求长期遵守的个人偏好 | 禁止项、输出约束、项目强规则、个人审核要求 |
| `templates/` | JSON skeleton 和 Markdown 样式参考 | 主交付件模板、报告模板 |
| `docs/` | 面向人的架构说明 | Agent 设计、产物契约、边界说明 |

## 优先级

`skills/`、schema 和固定脚本定义运行时执行契约，不作为业务事实来源。业务和输出约束按以下顺序处理：

```text
当前用户明确指令
  > process/rules-pack.md 中当前阶段可见且已读取正文的适用 rules
  > 当前输入文档（需求 / 设计方案 / 已评审测试分析方案）
  > project/personal knowledge
  > core knowledge
```

rules 内部按 `core > project > user` 处理；project/personal rules 可以细化更高层规则，但不得放宽或违反更高层强制约束。个人偏好只有在用户明确要求长期遵守时才进入 `rules/user/`；一次性表达仍以当前用户指令处理，不沉淀为长期规则。

## Project / User Knowledge

`knowledge/projects/<project-key>/` 和 `knowledge/user/` 是动态补充来源，必须声明 `name`、`description`，可选 `stages`。`context-source-indexing` 只索引 frontmatter；后续阶段按 `context-pack.md` 中的来源表读取正文并记录应用状态。

- project knowledge 可以保存经确认的项目术语、历史缺陷、复盘经验、风险画像、测试策略和测试设计启发，但不能替代当前需求或设计方案的业务事实。
- user knowledge 可以保存个人测试方法、检查清单和测试关注点；用户明确要求长期遵守的输出偏好、审查要求或本地限制必须保存到 `rules/user/`。
- knowledge 只提供风险、方法和经验补充；与当前输入文档或 rules 冲突时不得覆盖。

rules 不进入 `context-pack.md`，由 `process/rules-pack.md` 独立索引强制规则；后续阶段按规则表读取当前阶段适用规则正文并记录应用状态。

## 当前主标准

- 工作流边界：`knowledge/test-workflow-boundaries.md`
- 测试点标准：`knowledge/testpoint-standard.md`
- 测试分析方案标准：`knowledge/test-analysis-solution-standard.md`
- 测试设计方案标准：`knowledge/test-design-solution-standard.md`
- 测试用例公共写作标准：`knowledge/test-case-writing-standard.md`
- GUI/API/CLI 用例写作风格：`knowledge/test-case-writing-styles/`
