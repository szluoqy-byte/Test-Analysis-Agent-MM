---
name: input-fact-modeling
description: 在测试分析前把需求、可选设计、规则和动态知识整理为 Markdown 输入事实模型，为方法路由和场景测试点分析提供可追溯 FACT。
---

# 输入事实建模 Skill

## 何时使用

在 `process/rules-pack.md` 和 `process/context-pack.md` 已生成后使用。只回答输入材料明确表达了什么，不选择测试技术，不生成 SC/TP/TC。

## 输入

- run manifest 中全部可用的需求和设计 Markdown。
- `process/rules-pack.md` 与适用规则正文。
- `process/context-pack.md` 中本阶段可见的动态来源正文。
- `templates/input-fact-model-template.md`。

## 执行要求

1. 直接编写 `process/input-fact-model.md`，不生成 JSON 草稿或同名 JSON。
2. FACT 从 `FACT-001` 开始全局连续编号。
3. 记录来源类型、文件、位置、对象、事实、约束和可观察结果。
4. 设计对需求的关系只使用补充、一致、冲突、无设计依据、设计新增。
5. rules 和动态来源记录应用状态；动态知识不得伪装成需求事实。

## 输出

唯一输出是 `process/input-fact-model.md`。后续阶段直接读取该 Markdown，不通过 JSON 中转。

## 验证闭环

确认所有 FACT 可追溯、编号连续、没有测试点或用例内容，并确认文件未包含 JSON 代码块或 schema 字段占位。

## 约束

- 不编造接口、字段、状态、错误码、角色、阈值或提示。
- 冲突事实并列保留，不静默选择。
- 不生成确认问题清单，不直接向用户提问。
