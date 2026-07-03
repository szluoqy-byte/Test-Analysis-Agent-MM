---
name: test-analysis-design-workflow
description: 编排测试分析与测试设计全流程；先运行测试分析 workflow，再将生成的 test-analysis-solution.json 显式交给测试设计 workflow，最终输出两套交付件和最终审阅报告。
---

# 测试分析与测试设计全流程入口

本 skill 是 `test-e2e-analysis-design-agent` 的完整链路入口。它面向用户“一次性完成测试分析和测试设计”的请求，只做高层编排，不重新实现 `test-analysis-workflow` 或 `test-design-workflow` 的内部生成、校验、评审、coverage 和 final-report 逻辑。

## 必需输入

- `$ARGUMENTS`：至少包含一份 `.md` 或 `.markdown` 需求文档路径。
- 可额外包含一份或多份 `.md` 或 `.markdown` 设计方案文档路径。
- 可选 `--project <project-key>`，必须原样传递给测试分析和测试设计阶段。
- 如果输入包含 `.docx` 或 `.xlsx`，不得在本 workflow 中转换；必须先由 `@file-normalization-agent` 归一化为 Markdown。

## 职责边界

- 本 skill 负责全流程编排和阶段交接。
- `test-analysis-workflow` 负责生成并收口测试分析方案，包括 JSON lint、Markdown render、独立评审、coverage-review、analysis-final-report 和一致性检查。
- `test-design-workflow` 负责生成并收口测试设计方案，包括 JSON lint、Markdown render、独立评审、coverage-review、design-final-report 和一致性检查。
- 本 skill 只做轻量交接检查：确认上一阶段成功完成，并确认下一阶段必需路径存在。
- 本 skill 不新增 SC/TP/TC，不直接编辑主交付件 JSON 或 Markdown，不重复执行 analysis/design 内部质量门禁。

## 执行流程

1. 校验输入至少包含一份 Markdown 需求文档；若发现 Office 输入，输出需先使用 `@file-normalization-agent` 的阻断说明，不创建全流程 run。
2. 固定 `PROJECT_ROOT`，整理传给分析阶段的参数：需求 Markdown、可选设计 Markdown、可选 `project=<project-key>`。
3. 使用 `test-analysis-workflow` 完成测试分析阶段。该阶段自行创建或维护 `outputs/runs/<run-id>/`，并负责所有分析内部校验和返工闭环。
4. 分析阶段完成后，只做阶段交接检查：
   - 确认 `outputs/runs/<run-id>/deliverables/test-analysis-solution.json` 存在。
   - 确认 `outputs/runs/<run-id>/reports/analysis-final-report.json` 和同名 Markdown 已生成。
   - 不重新实现 `lint-run-json.py`、Markdown lint、review 或 coverage。
5. 使用 `test-design-workflow` 完成测试设计阶段，并显式传入上一步生成的 `deliverables/test-analysis-solution.json`。需求 Markdown、设计 Markdown 和 `project=<project-key>` 作为设计依据继续传入。
6. 设计阶段完成后，只做最终路径汇总：
   - `deliverables/test-analysis-solution.json/.md`
   - `deliverables/test-design-solution.json/.md`
   - `reports/analysis-final-report.json/.md`
   - `reports/design-final-report.json/.md`
7. 如果分析阶段失败，不进入设计阶段；如果设计阶段失败，保留并报告已完成的分析产物路径和设计失败位置。

## 阶段交接规则

- 测试设计必须显式使用分析阶段生成的 `test-analysis-solution.json`，不得依赖碎片化 TP 输入。
- 不调用 `test-design-workflow` 的“缺失分析方案”失败分支；本 workflow 在进入设计前必须已经拿到完整分析 JSON。
- 不要求 `test-design-workflow` 自动运行 `test-analysis-workflow`；自动串联只存在于本全流程 workflow。
- 同一全流程优先复用分析阶段创建的 run 目录，让分析和设计产物落在同一个 `outputs/runs/<run-id>/` 下。

## 输出要求

最终回复必须汇总：

- run 目录。
- 测试分析 JSON/Markdown 路径。
- 测试设计 JSON/Markdown 路径。
- 分析最终报告 JSON/Markdown 路径。
- 设计最终报告 JSON/Markdown 路径。
- 分析阶段和设计阶段各自的收口状态。

## 约束

- 不直接处理 `.docx` / `.xlsx`。
- 不复制 analysis/design workflow 内部校验逻辑。
- 不手工维护 Markdown；Markdown 仍由 `bin/render-run-markdown.py` 或对应 workflow 内部脚本从 JSON 渲染。
- 不临时创建脚本处理 JSON、循环切片、汇总状态或定位返工；如固定脚本能力不足，修改仓库固定脚本并运行校验。
