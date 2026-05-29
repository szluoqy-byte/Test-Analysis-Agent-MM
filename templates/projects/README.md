# Project Templates 目录说明

本目录保存按项目隔离的模板补充，属于 `project` 层，默认不提交 Git。project 模板补充是当前 run 的一等输入源，命中和未采用情况必须记录到 `outputs/runs/<run-id>/process/context-pack.md`。

## 建议结构

```text
templates/projects/<project-key>/
  test-analysis-solution-notes.md
  report-notes.md
```

项目模板只能补充说明、措辞和局部呈现偏好，不得改变 core 模板定义的固定章节、必填字段、表头和主交付件路径。
