# 上下文来源索引模板

构建当前运行目录下的 `process/context-pack.json` 时使用 `templates/context-pack-json-template.json`；本文件只作为 `process/context-pack.md` 派生阅读版样式参考。

```markdown
# 上下文来源索引

## 本次需求

| 字段 | 值 |
|---|---|
| path |  |
| title |  |
| keywords |  |

## 绑定结果

| 绑定 | 状态 | 标识 | 说明 |
|---|---|---|---|
| projectBinding | unresolved/resolved |  |  |

## 动态来源索引

| 路径 | 名称 | 描述 | 可用阶段 | 可见性 |
|---|---|---|---|---|
| knowledge/projects/<project-key>/risk-profile.md | payment-risk-profile | 支付项目风险画像，补充支付状态、幂等、补偿和对账类覆盖关注点。 | testing-method-router、coverage-review | restricted |

## 未扫描项目来源

| 路径 | 原因 |
|---|---|
| knowledge/projects/ | project-key 未唯一确定 |

## 告警

无告警。
```

## 生成原则

- `context-pack.json` 只记录动态 project/personal 来源索引，不摘录正文。
- rules 由 `process/rules-pack.json` 独立承载强制语义，不进入 `sources[]`。
- core 层 `knowledge/*.md`、templates 和 skill 私有参考由 workflow 或对应 skill 固定引用，不进入 `sources[]`。
- 只有唯一确定 `project-key` 时才扫描 `*/projects/<project-key>/**/*.md`；未确定时不得读取所有 project 目录正文。
- personal 层扫描 `*/user/**/*.md`，但跳过 `README.md` 正文。
- 动态来源文件必须声明 frontmatter：`name`、`description`，可选 `stages`。
- `stages` 未配置时，`availableStages` 写 `["*"]`，`availability` 写 `all`；配置后仅对对应阶段可见，`availability` 写 `restricted`。
- `sources[]` 不写 `sourceType`、`layer`、`projectKey` 或 personal 专属字段；这些信息由 `path` 推断，project 绑定只写在顶层 `projectBinding`，personal 来源只通过 `knowledge/user/**`、`memory/user/**` 路径表达。
- 后续 skill 只读取对当前阶段可见的 `sources[]` 文件正文，并在本阶段过程 JSON、review JSON 或 coverage JSON 中记录应用状态。
