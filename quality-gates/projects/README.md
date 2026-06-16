# Project Quality Gates 目录说明

本目录保存按项目隔离的附加质量门禁，属于 `project` 层，默认不提交 Git。project 质量门禁是当前 run 的一等输入源，动态来源索引必须记录到 `outputs/runs/<run-id>/process/context-pack.json`；同名 Markdown 只是派生阅读版。

项目质量门禁只能比 core 门禁更严格，例如要求某项目必须覆盖审计日志、账务一致性、租户隔离或特定兼容矩阵。不得放宽、覆盖或删除 core 门禁。

动态来源文件必须声明 frontmatter：`name`、`description`，可选 `stages`。Checklist 或附加门禁通常配置 `stages: [coverage-review]`。
