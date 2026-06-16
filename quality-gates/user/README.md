# Personal Quality Gates 目录说明

本目录保存当前使用者的本地附加检查偏好，在架构语义上属于 `personal` 层，默认不提交 Git。

Personal 门禁只能作为附加检查或提醒，不能放宽 core/project 门禁，也不能改变主交付件结构和字段约束。

动态来源文件必须声明 frontmatter：`name`、`description`，可选 `stages`。`stages` 未配置时默认所有阶段可用。
