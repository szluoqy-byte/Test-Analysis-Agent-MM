# 项目化 Memory 目录说明

本目录按 `project-key` 隔离不同项目的长期 memory。项目化 memory 只保存经确认、会影响后续测试分析的项目事实、业务约定、历史缺陷、输出偏好和团队反馈。

本目录属于 `project` 层，默认不提交 Git；`.gitignore` 只保留本 README。团队如果确实希望共享某个项目配置，可以显式强制添加对应文件。project 层是当前 run 的一等输入源，动态来源索引必须记录到 `outputs/runs/<run-id>/process/context-pack.json`；同名 Markdown 只是派生阅读版。

## 目录结构

```text
memory/projects/<project-key>/
  project-memory.md
  testing-experience-memory.md
  output-preferences.md
```

`project-key` 可使用大小写字母、数字、空格、短横线或下划线，例如 `CRM`, `Mall Order`, `payment_core`。不要使用路径分隔符，且不要以空格、短横线或下划线开头或结尾。

## 发现规则

- `context-source-indexing` 先确定 `project-key`，再索引 `memory/projects/<project-key>/**/*.md` 的 frontmatter。
- 未确定 `project-key` 时，不读取所有项目目录正文，避免跨项目 memory 污染。
- 项目化 memory 不需要登记到全局 memory 文件。
- 每个项目文件必须包含 frontmatter：`name`、`description`，可选 `stages`；正文应包含清晰标题、适用范围、关键词、来源或确认记录，便于后续阶段按需读取。

## 写入边界

- 只写入已确认的项目事实、项目经验和输出偏好。
- 未确认业务规则保留为待确认问题，不写入 memory。
- 通用测试理论、通用缺陷模式、框架术语和风险等级定义不写入本目录。
- 单次运行产物不写入本目录，应保存在 `outputs/runs/<run-id>/`。
