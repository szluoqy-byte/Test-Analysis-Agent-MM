# 项目化 Knowledge 目录说明

本目录按 `project-key` 保存项目级测试知识补充。它用于让分析过程理解某个项目特有的测试策略，而不是保存业务事实本身。

本目录属于 `project` 层，默认不提交 Git；`.gitignore` 只保留本 README。团队如果确实希望共享某个项目配置，可以显式强制添加对应文件。project 层是当前 run 的一等输入源，动态来源索引必须记录到 `outputs/runs/<run-id>/process/context-pack.json`；同名 Markdown 只是派生阅读版。

## 建议结构

```text
knowledge/projects/<project-key>/
  test-design-factors.md
  test-design-patterns.md
  test-design-checklist.md
  glossary.md
  risk-profile.md
  coverage-profile.md
  routing-notes.md
  oracle-heuristics.md
```

文件名不是硬性要求。每个动态来源文件必须声明 frontmatter：`name`、`description`，可选 `stages`。推荐命名只是为了降低误判概率。

```yaml
---
name: payment-risk-profile
description: 支付项目风险画像，补充支付状态、幂等、补偿和对账类覆盖关注点。
stages:
  - testing-method-router
  - coverage-review
---
```

## 适合放入的内容

- 项目级术语映射和测试解释口径。
- 项目风险画像、重点质量属性和缺陷高发区。
- 项目覆盖策略、兼容矩阵选择原则和回归优先级补充。
- 测试技术路由补充，例如某类需求在当前项目中通常需要额外关注接口契约或数据一致性。
- 项目级测试 oracle 补充，例如账务、库存、权限或审计类结果判定启发。
- 测试设计因子库或业务测试设计模式库，用于测试分析和测试设计阶段补充业务入口、数据因子、状态、组合和观察点。
- 测试设计 checklist 或评审清单，默认用于覆盖审查阶段统一查漏；只有文件或用户指令明确要求产物语义评审时，才额外绑定独立评审。

## 不应放入的内容

- 未确认业务规则、一次性需求结论或临时假设。
- 项目真实缺陷和团队反馈，这些应进入 `memory/projects/<project-key>/`。
- 测试点字段、类型、方法、级别、输出结构和质量门禁覆盖规则。
- 运行产物、context pack、结构化过程记录或派生报告。

## 发现规则

`context-source-indexing` 只有在唯一确定 `project-key` 后才索引对应项目目录。未确定 `project-key` 时，不读取所有项目目录正文。

context pack 阶段只读取 frontmatter，不摘录正文，也不判断具体测试点或测试设计项命中。后续阶段只读取 `sources[]` 中对本阶段可见的文件正文，并输出应用状态：

- `applied`
- `not_applicable`
- `insufficient_evidence`
- `conflict_with_requirement`
- `deferred_to_review`
