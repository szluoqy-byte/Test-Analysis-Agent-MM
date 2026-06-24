# Knowledge / Skill / Memory 边界

## 分工

| 类型 | 内容 | 示例 |
|---|---|---|
| `skills/` | 流程动作、生成步骤、评审步骤和脚本调用约束 | workflow、generation、review |
| `knowledge/` | 稳定测试知识、输出标准、测试技术和方法参考 | SC/TP/TC 标准、测试技术 |
| `rules/` | 必须遵守的强制规则 | 禁止编造、输出约束 |
| `memory/` | 项目或个人会变化的事实、偏好、经验 | 项目风险、历史缺陷、个人关注点 |
| `templates/` | JSON skeleton 和 Markdown 渲染样式参考 | 主交付件模板 |

## 优先级

`skills/`、schema 和固定脚本定义运行时执行契约，不作为业务事实来源。业务和输出约束按以下顺序处理：

```text
当前用户明确指令
  > process/rules-pack.json 中的适用 rules
  > 当前输入文档（需求 / 设计方案 / 已评审测试分析方案）
  > memory
  > knowledge
```

rules 内部按 `core > project > personal` 处理；project/personal rules 可以细化更高层规则，但不得放宽或违反更高层强制约束。

## 当前主标准

- 测试分析方案标准：`knowledge/test-analysis-solution-standard.md`
- 测试设计方案标准：`knowledge/test-design-solution-standard.md`
- 测试点标准：`knowledge/testpoint-standard.md`
- 工作流边界：`knowledge/test-workflow-boundaries.md`

## 动态来源

project/personal knowledge 和 memory 动态来源必须声明 `name`、`description`，可选 `stages`。`context-source-indexing` 只索引元数据；后续阶段按 `context-pack.json` 中的 `sources[]` 读取正文并记录应用状态。rules 不进入 `context-pack.json`，由 `process/rules-pack.json` 独立承载强制语义。
