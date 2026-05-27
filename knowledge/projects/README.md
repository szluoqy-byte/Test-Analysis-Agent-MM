# 项目化 Knowledge 目录说明

本目录按 `project-key` 保存项目级测试知识补充。它用于让分析过程理解某个项目特有的测试策略，而不是保存业务事实本身。

本目录属于 `project` 层，默认不提交 Git；`.gitignore` 只保留本 README。团队如果确实希望共享某个项目配置，可以显式强制添加对应文件。project 层是当前 run 的一等输入源，命中和未采用情况必须记录到 `outputs/runs/<run-id>/process/context-pack.md`。

## 建议结构

```text
knowledge/projects/<project-key>/
  glossary.md
  risk-profile.md
  coverage-profile.md
  routing-notes.md
  oracle-heuristics.md
```

## 适合放入的内容

- 项目级术语映射和测试解释口径。
- 项目风险画像、重点质量属性和缺陷高发区。
- 项目覆盖策略、兼容矩阵选择原则和回归优先级补充。
- 方法路由补充，例如某类需求在当前项目中通常需要额外关注接口契约或数据一致性。
- 项目级测试 oracle 补充，例如账务、库存、权限或审计类结果判定启发。

## 不应放入的内容

- 未确认业务规则、一次性需求结论或临时假设。
- 项目真实缺陷和团队反馈，这些应进入 `memory/projects/<project-key>/`。
- 测试点字段、类型、方法、级别、输出结构和质量门禁覆盖规则。
- 运行产物、context pack 或过程报告。

## 发现规则

`memory-context-builder` 只有在唯一确定 `project-key` 后才扫描对应项目目录。每个文件应包含清晰标题、适用范围和关键词，便于按当前需求裁剪相关片段。
