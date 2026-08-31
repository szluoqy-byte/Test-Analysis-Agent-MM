---
name: test-analysis-design-workflow
description: 编排从 Markdown 需求到测试分析 JSON、再到测试设计 JSON 的全流程；优先隔离执行两个阶段，并只通过分析结果 JSON 交接业务事实。
---

# 测试分析与测试设计全流程

## 何时使用

用户明确要求从需求和可选设计方案一次性完成测试分析与测试设计时使用。Office 输入先归一化。

## 执行阶段

- [ ] Step 1: 准备输入与统一 run
- [ ] Step 2: 完成测试分析阶段
- [ ] Step 3: 通过分析 JSON 交接设计阶段
- [ ] Step 4: 核对完整结果

> 实时状态分别写入 `process/analysis-task-list.json` 与 `process/design-task-list.json`。

## 各阶段执行要求

### Step 1: 准备输入与统一 run

确定 Markdown 需求、可选设计、runid、mode 和 project-key。两个阶段必须使用同一 run；本层不复制 analysis/design 内部生成、评审或覆盖逻辑。

### Step 2: 完成测试分析阶段

优先由独立 analysis subagent 执行 `test-analysis-workflow`；环境不支持时在同会话完整执行。阶段完成标志是 `deliverables/test-analysis-solution.json/.md` 和 `reports/analysis-final-report.md` 均存在且固定检查通过。

### Step 3: 通过分析 JSON 交接设计阶段

把完整 `deliverables/test-analysis-solution.json`、同一 run、manifest 输入和 project-key 显式交给 design 阶段。聊天总结、分析 Markdown 或隐式记忆都不能替代该 JSON。

### Step 4: 核对完整结果

确认分析与设计结果 JSON/Markdown、两个最终报告 Markdown 均存在，设计 JSON 完整继承分析 SC/TP，并确认两个阶段分别完成自己的 review、coverage 和一致性检查。

## 输出

- `deliverables/test-analysis-solution.json/.md`。
- `deliverables/test-design-solution.json/.md`。
- `reports/analysis-final-report.md`。
- `reports/design-final-report.md`。

## 约束

- 语义过程件全部是 Markdown；只有结果方案 JSON 跨阶段传递。
- 本层不直接编辑切片、review 或 coverage 文件。
- fallback 为同会话串联时必须在最终回复说明。
