# Personal Knowledge 目录说明

本目录保存当前使用者的本地测试知识补充。它在架构语义上属于 `personal` 层，默认不提交 Git，只影响本地运行。

## 适合放入的内容

- 个人常用的测试启发、检查清单和评审关注点。
- 不涉及项目事实的术语理解或判定依据补充。
- 本地使用者希望额外关注的质量属性。

## 不应放入的内容

- 项目事实、团队约定、真实缺陷复盘或未确认业务规则。
- 测试点字段、类型、方法、级别、输出结构和质量门禁覆盖规则。
- 会削弱 core 或 project 层约束的规则。
- 个人长期输出偏好、沟通偏好或必须遵守的本地要求；这些应放入 `rules/user/`。

`context-source-indexing` 会在运行时索引本目录的动态来源 frontmatter，并在 `process/context-pack.json` 中记录到 `sources[]`；同名 Markdown 只作为派生阅读版。personal 来源不需要 binding 或 key，只通过 `knowledge/user/**` 路径表达。每个动态来源文件必须声明 `name`、`description`，可选 `stages`；未配置 `stages` 时默认所有阶段可用。
