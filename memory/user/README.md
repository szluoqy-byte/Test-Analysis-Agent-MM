# Personal Memory 目录说明

本目录保存当前使用者的本地 memory 和输出偏好。它在架构语义上属于 `personal` 层，默认不提交 Git，只影响本地运行。

## 建议结构

```text
memory/user/
  preferences.md
  terminology.md
  testing-habits.md
```

## 使用边界

- 适合保存个人常用措辞、输出偏好、评审关注点和本地使用习惯。
- 不保存项目事实、团队共识、真实缺陷复盘或未确认业务规则。
- 不覆盖当前用户明确指令、需求文档、project memory、核心输出契约和质量门禁。
- `context-source-indexing` 只把本目录动态来源的 frontmatter 写入 `outputs/runs/<run-id>/process/context-pack.json`；同名 Markdown 只是派生阅读版。
- 即使没有动态来源，也需要记录空 `sources[]`；personal 来源不需要 binding 或 key。
