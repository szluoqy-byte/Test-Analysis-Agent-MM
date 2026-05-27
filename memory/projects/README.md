# 项目化 Memory 目录说明

本目录按 `project-key` 隔离不同项目的长期 memory。项目化 memory 只保存经确认、会影响后续测试分析的项目事实、业务域约定、历史缺陷、输出偏好和团队反馈。

本目录属于 `project` 层，默认不提交 Git；`.gitignore` 只保留本 README。团队如果确实希望共享某个项目配置，可以显式强制添加对应文件。project 层是当前 run 的一等输入源，命中和未采用情况必须记录到 `outputs/runs/<run-id>/process/context-pack.md`。

## 目录结构

```text
memory/projects/<project-key>/
  project-memory.md
  testing-experience-memory.md
  output-preferences.md
  domains/
    <业务域>.md
```

`project-key` 建议使用小写字母、数字、短横线或下划线，例如 `crm`, `mall-order`, `payment_core`。

## 发现规则

- `memory-context-builder` 先确定 `project-key`，再扫描 `memory/projects/<project-key>/**/*.md`。
- 未确定 `project-key` 时，不读取所有项目目录正文，避免跨项目 memory 污染。
- 项目化 memory 不需要登记到全局 `memory/project-memory.md`。
- 每个项目文件应包含清晰标题、适用范围、关键词、来源或确认记录，便于自动匹配和裁剪。

## 写入边界

- 只写入已确认的项目事实、项目经验和输出偏好。
- 未确认业务规则保留为待确认问题，不写入 memory。
- 通用测试理论、通用缺陷模式、框架术语和风险等级定义不写入本目录。
- 单次运行产物不写入本目录，应保存在 `outputs/runs/<run-id>/`。
