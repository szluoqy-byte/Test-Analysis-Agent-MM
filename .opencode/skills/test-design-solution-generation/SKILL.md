---
name: test-design-solution-generation
description: 基于已评审测试分析 JSON，按 TP 编写 Markdown 测试用例切片并在阶段边界一次性固化 schema 2.0 测试设计结果 JSON。
---

# 测试设计方案生成 Skill

## 何时使用

仅在完整 schema 2.0 `test-analysis-solution.json` 已存在时使用，不自动运行分析。

## 输入

- `deliverables/test-analysis-solution.json`。
- 需求、可选设计方案、rules/context Markdown。
- `knowledge/test-case-writing-standard.md` 和对应 GUI/API/CLI 风格。

## 生成阶段

- [ ] Step 1: 建立 TP 工作项
- [ ] Step 2: 识别测试设计因子
- [ ] Step 3: 编写并评审 TC Markdown 切片
- [ ] Step 4: 一次性固化设计结果 JSON

## 各阶段执行要求

### Step 1: 建立 TP 工作项

运行固定脚本从分析 JSON 生成 `process/test-case-work-items.json`，每个 TP 一个工作项；内容 hash 变化时重开对应 TP。

### Step 2: 识别测试设计因子

对每个 TP 识别必选因子、候选因子和基于目标补充推导的必要因子，形成最小充分 TC 集，不机械限制一个 TP 一个 TC。

### Step 3: 编写并评审 TC Markdown 切片

按 `templates/test-case-slice-template.md` 编写 `process/test-case-slices/<TP-ID>.md`，测试数据必须具体，步骤 action 与 expected 配对。过程切片不分配 TC 编号；评审通过后由脚本完成工作项。

### Step 4: 一次性固化设计结果 JSON

所有工作项完成后一次性编写 `deliverables/test-design-solution.draft.json`，完整继承分析 SC/TP，再运行 `finalize-deliverable.py --scope design` 复用或追加 TC 编号并写入最终交付；固化成功后删除草稿。

## 输出

- Markdown：`test-case-slices/*.md`。
- 控制 JSON：`test-case-work-items.json`。
- 结果 JSON：`deliverables/test-design-solution.json`。

## 约束

- `level` 为 Level 0 到 Level 4。
- `testData[]`、`steps[]` 只在最终结果 JSON 使用；过程 Markdown 采用自然段和列表表达。
- 不持久化 generationContext，不生成过程 JSON 镜像。
