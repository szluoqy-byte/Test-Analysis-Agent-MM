---
name: test-analysis-solution-generation
description: 基于输入事实和方法分析，使用 Markdown 冻结 SC 树并按叶子 SC 编写 TP 切片，最后一次性固化 schema 2.0 测试分析结果 JSON。
---

# 测试分析方案生成 Skill

## 何时使用

在 `input-fact-model.md` 和方法分析完成后使用。本 skill 不生成 TC。

## 输入

- `process/input-fact-model.md`、`process/testing-method-routing.md`。
- `process/rules-pack.md`、`process/context-pack.md` 及适用正文。
- 当前 run 输入、既有分析结果和 `process/run-plan.json`。

## 生成阶段

- [ ] Step 1: 冻结 SC 场景树
- [ ] Step 2: 生成叶子 SC 工作项
- [ ] Step 3: 编写 TP Markdown 切片
- [ ] Step 4: 一次性固化分析结果 JSON

## 各阶段执行要求

### Step 1: 冻结 SC 场景树

初始化并填写 `process/scenario-tree.md`。场景标题使用 `###/####/##### SC-*`，最多三层；只有场景事实，不写 TP。

### Step 2: 生成叶子 SC 工作项

场景树评审通过后运行固定脚本生成 `process/test-point-work-items.json`。该 JSON 只记录 ID、hash 和状态，由脚本维护。

### Step 3: 编写 TP Markdown 切片

按 `templates/test-point-slice-template.md` 逐叶子 SC 编写切片。每个叶子场景必须包含 E2E 场景测试。过程切片使用标题和验证目标，不分配 TP 编号。

### Step 4: 一次性固化分析结果 JSON

全部切片评审通过后，一次性编写 `deliverables/test-analysis-solution.draft.json`，并通过 `finalize-deliverable.py --scope analysis` 复用或追加 TP 编号。最终 JSON 只使用 schema 2.0 字段，固化成功后删除草稿。

## 输出

- Markdown：`scenario-tree.md`、`test-point-slices/*.md`。
- 控制 JSON：`test-point-work-items.json`。
- 结果 JSON：`deliverables/test-analysis-solution.json`。

## 约束

- TP 是验证目标簇，不按单个输入变体、角色样本、错误类型或配置取值拆分。
- 接口类非 E2E TP 按接口、端点、消息、回调或集成点组织。
- 不持久化 generationContext；生成时按需读取规则、上下文和事实 Markdown。
