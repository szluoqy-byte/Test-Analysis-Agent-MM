# Project Quality Gates 目录说明

本目录保存按项目隔离的附加质量门禁，属于 `project` 层，默认不提交 Git。project 质量门禁是当前 run 的一等输入源，命中和未采用情况必须记录到 `outputs/runs/<run-id>/process/context-pack.md`。

项目质量门禁只能比 core 门禁更严格，例如要求某项目必须覆盖审计日志、账务一致性、租户隔离或特定兼容矩阵。不得放宽、覆盖或删除 core 门禁。
