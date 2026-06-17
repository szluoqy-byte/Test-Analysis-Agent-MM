---
name: test-workflow-boundaries
description: 定义测试分析与测试设计工作流边界。
---

# 测试工作流边界

## 分析阶段

`test-analysis-agent` 负责回答 what to test。

输出：

```text
SC 场景树 -> TP 测试点
```

分析阶段不输出：

- 测试用例
- 测试数据
- 操作步骤
- 步骤预期
- 最终预期

## 设计阶段

`test-design-agent` 负责回答 how to test。

输出：

```text
SC 场景树 -> TP 测试点 -> TC 测试用例
```

设计阶段继承分析方案中的场景树和测试点，不改写分析层级。设计阶段可以补读需求和设计依据，用于生成 TC 的前置条件、测试数据、步骤和最终预期。

## 触发关系

- 用户要求“测试分析方案”：进入 `test-analysis-workflow`。
- 用户要求“测试设计方案”“测试用例”“用例步骤”：进入 `test-design-workflow`。
- 用户只提供 Office 输入：先进入 `file-normalization-agent`。
- 用户只有需求/设计方案但要求测试设计：先生成测试分析方案，再生成测试设计方案。

## 自动闭环

全流程不创建澄清队列，不中途向用户提问。依据不足时，分析阶段只生成可支持的测试点；设计阶段生成保守预期，不编造具体值。
