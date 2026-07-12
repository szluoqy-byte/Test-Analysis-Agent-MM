---
name: test-analysis-design-workflow
description: 编排测试分析与测试设计全流程；优先以独立 subagent 执行分析和设计阶段，通过 test-analysis-solution.json 显式交接，最终输出两套交付件和最终审阅报告。
---

# 测试分析与测试设计全流程入口

本 skill 是 `test-e2e-analysis-design-agent` 的完整链路编排契约。它面向用户“一次性完成测试分析和测试设计”的请求，优先使用独立 subagent 隔离执行分析和设计阶段；不支持真实 subagent 的运行环境才 fallback 为同会话 workflow 串联。本 skill 不重新实现 `test-analysis-workflow` 或 `test-design-workflow` 的内部生成、校验、评审、coverage 和 final-report 逻辑。

## 必需输入

- `$ARGUMENTS`：新 run 至少包含一份 `.md` 或 `.markdown` 需求文档路径；已有 `runid` 可继承 manifest 输入。
- 可额外包含一份或多份 `.md` 或 `.markdown` 设计方案文档路径。
- 可选 `--project <project-key>`，必须原样传递给测试分析和测试设计阶段。
- 可选 `runid=<requirement-id>`、`mode=auto|resume|extend|rebuild` 和 `remove-source=<path>`，必须原样传递给两个阶段。
- 如果输入包含 `.docx` 或 `.xlsx`，不得在本 workflow 中转换；必须先由 `@file-normalization-agent` 归一化为 Markdown。

## 执行检查清单

Progress:
- [ ] Step 1: 校验全流程输入都是 Markdown（block on Office input and route to `@file-normalization-agent`）
- [ ] Step 2: 启动 analysis subagent 执行 `test-analysis-workflow`
- [ ] Step 3: 校验分析交接文件（check `deliverables/test-analysis-solution.json` and `reports/analysis-final-report.json/.md`）
- [ ] Step 4: 启动 design subagent 执行 `test-design-workflow`，显式传入完整分析 JSON
- [ ] Step 5: 汇总分析/设计交付件和 final-report 路径
- [ ] Step 6: 若使用 fallback，同步说明未获得 subagent 会话隔离收益

## 职责边界

- 本 skill 负责全流程 subagent 编排和阶段交接。
- analysis subagent 使用 `test-analysis-agent` 职责边界，执行 `test-analysis-workflow`，负责生成并收口测试分析方案，包括 JSON lint、Markdown render、独立评审、analysis-fact-coverage-map、coverage-review、analysis-final-report 和一致性检查。
- design subagent 使用 `test-design-agent` 职责边界，执行 `test-design-workflow`，负责生成并收口测试设计方案，包括 JSON lint、Markdown render、独立评审、design-fact-coverage-map、coverage-review、design-final-report 和一致性检查。
- 本 skill 只做轻量交接检查：确认上一阶段成功完成，并确认下一阶段必需路径存在。
- 本 skill 不新增 SC/TP/TC，不直接编辑主交付件 JSON 或 Markdown，不重复执行 analysis/design 内部质量门禁。
- subagent 隔离的是会话上下文，不隔离文件系统；同一全流程优先复用同一个 `outputs/runs/<run-id>/`。
- subagent 之间不得通过聊天记录、自然语言总结或隐式上下文交接业务事实；阶段交接只依赖 canonical JSON 和固定报告文件。

## 易错点

- 不要把同一会话里提到 `@test-analysis-agent` / `@test-design-agent` 当成真实 subagent 隔离。
- 不要把 analysis subagent 的聊天总结传给 design subagent 作为业务事实；只传完整分析 JSON 和输入文件路径。
- 不要在 e2e 层重复实现 analysis/design 内部 lint、review、coverage 或 final-report 逻辑。

## 执行流程

1. 校验输入至少包含一份 Markdown 需求文档；若发现 Office 输入，输出需先使用 `@file-normalization-agent` 的阻断说明，不创建全流程 run。
2. 固定 `PROJECT_ROOT`，整理传给分析阶段的参数：需求 Markdown、可选设计 Markdown、`runid`、`mode`、`remove-source` 和可选 `project=<project-key>`。
3. 优先启动 analysis subagent 完成测试分析阶段。显式传入同一组持久 run 参数；analysis subagent 内部执行 `test-analysis-workflow`，按 run plan 创建、复用、续作或增量补充 `outputs/runs/<run-id>/`，并负责 revision、锁、分析校验和返工闭环。
4. 分析阶段完成后，只做阶段交接检查：
   - 确认 `outputs/runs/<run-id>/deliverables/test-analysis-solution.json` 存在。
   - 确认 `outputs/runs/<run-id>/reports/analysis-final-report.json` 和同名 Markdown 已生成。
   - 不重新实现 `lint-run-json.py`、Markdown lint、review 或 coverage。
5. 优先启动 design subagent 完成测试设计阶段。传入内容只包含：阶段目标、上一步生成的 `deliverables/test-analysis-solution.json`、同一 `runid`、`mode`、同一 run 目录、manifest 输入、可选 `project=<project-key>`、仓库根路径和本 skill 的交接要求。design subagent 内部执行 `test-design-workflow`，必须基于最新 analysis hash 判断增量影响。
6. 设计阶段完成后，只做最终路径汇总：
   - `deliverables/test-analysis-solution.json/.md`
   - `deliverables/test-design-solution.json/.md`
   - `reports/analysis-final-report.json/.md`
   - `reports/design-final-report.json/.md`
7. 如果分析阶段失败，不进入设计阶段；如果设计阶段失败，保留并报告已完成的分析产物路径和设计失败位置。
8. 如果运行环境不支持真实独立 subagent，允许在同一会话内按上述顺序直接执行 `test-analysis-workflow` 和 `test-design-workflow`，但最终回复必须说明使用了 fallback，未获得 analysis/design 会话隔离收益。

## 计划-校验-执行模式

先计划并启动 analysis 阶段，校验分析交接文件存在后才启动 design 阶段；design 阶段完成后只校验最终路径汇总。任何阶段失败都停止后续阶段并报告已完成产物，不用自然语言补齐缺失交付件。

## 阶段交接规则

- 测试设计必须显式使用分析阶段生成的 `test-analysis-solution.json`，不得依赖碎片化 TP 输入。
- 不调用 `test-design-workflow` 的“缺失分析方案”失败分支；本 workflow 在进入设计前必须已经拿到完整分析 JSON。
- 不要求 `test-design-workflow` 自动运行 `test-analysis-workflow`；自动串联只存在于本全流程 workflow。
- 同一全流程优先复用分析阶段创建的 run 目录，让分析和设计产物落在同一个 `outputs/runs/<run-id>/` 下。
- analysis/design 各自通过 `manage-run.py` 获取和释放阶段锁；analysis finalize 后 design 才能 prepare。不得同时写同一持久 run。
- analysis subagent 不输出 TC、不关心测试步骤；design subagent 不重新分析或改写 SC/TP，只读取完整 `test-analysis-solution.json` 生成 TC。
- “调用 subagent”必须代表真实独立执行上下文；在同一会话里提到 `@test-analysis-agent` 或 `@test-design-agent` 不视为隔离执行。

## 输出要求

最终回复必须汇总：

- run 目录。
- 测试分析 JSON/Markdown 路径。
- 测试设计 JSON/Markdown 路径。
- 分析最终报告 JSON/Markdown 路径。
- 设计最终报告 JSON/Markdown 路径。
- 分析阶段和设计阶段各自的收口状态。
- 是否使用真实 subagent；如果使用 fallback，说明未获得会话隔离收益。

## 验证闭环

分析 subagent 完成后只检查交接文件是否存在，不重复实现分析内部 review、coverage 或 final-report。设计 subagent 完成后检查最终四类路径均存在，并确认 `test-design-solution.json` 使用的是同一 run 下的完整 `test-analysis-solution.json`。如果 fallback 为同会话串联，最终回复必须明确说明。

## 约束

- 不直接处理 `.docx` / `.xlsx`。
- 不复制 analysis/design workflow 内部校验逻辑。
- 不手工维护 Markdown；Markdown 仍由 `bin/render-run-markdown.py` 或对应 workflow 内部脚本从 JSON 渲染。
- 不临时创建脚本处理 JSON、循环切片、汇总状态或定位返工；如固定脚本能力不足，修改仓库固定脚本并运行校验。
