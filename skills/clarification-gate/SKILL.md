---
name: clarification-gate
description: 在多个测试分析检查点使用。用于收集、去重、分级和排序待确认候选问题；不在分析过程中打断用户，也不向测试分析方案主交付件写待确认章节。
---

# 待确认问题治理 Skill

本 skill 用于治理分析过程中的信息缺口。各阶段可以产出待确认候选问题，主流程统一去重、分级、排序和降级后，不触发中途交互。

在本 Agent 中，缺口治理的原则是：过程缺口进入 `process/clarification-session.md`；主交付件 `deliverables/test-analysis-solution.md` 不设置待确认信息章节。如果缺口影响单条测试点明细的判定结果，生成阶段在该测试点明细的 `预期结果` 写 `待人工分析确认`。

## 输入

- 当前检查点名称。
- 当前阶段产物，例如记忆上下文包、结构化需求模型、测试技术路由表、方法证据、测试分析方案草稿或覆盖审查结果。
- 已累计的待确认候选问题。
- `${PROJECT_ROOT}/outputs/runs/<run-id>/process/context-pack.md`。
- `templates/clarification-template.md`。

## 检查点

主流程只在以下三个固定检查点调用本 skill。所有检查点都只做候选治理，不向用户提问。

| 检查点 | 位置 | 典型候选问题 | 默认处理 |
|---|---|---|---|
| `CP-INPUT` | `memory-context-builder`、`requirement-testability` 和 `design-solution-extraction` 后 | 业务域命中冲突、memory 与需求冲突、需求与设计冲突、业务规则/状态/权限/边界/接口契约/字段/数据依赖缺失 | 进入过程候选队列；影响预期结果时标记为预期兜底依据 |
| `CP-ANALYSIS` | `testing-method-router` 和专项技术分析后 | 技术必要性范围、性能/安全/兼容是否展开、决策表条件、状态终态、幂等补偿、权限矩阵缺口 | 进入过程候选队列；影响测试点或测试点明细时写明影响范围 |
| `CP-REVIEW` | `test-analysis-solution-review` 和 `coverage-review` 后 | 核心需求缺失、覆盖无法关闭、主交付件可用性风险 | 作为过程审查问题收口；不得新增主交付件待确认章节 |

## 候选问题来源

各阶段只产出待确认候选，不直接调用用户交互能力：

| 来源阶段 | 允许产出候选 | 不允许做什么 |
|---|---|---|
| `memory-context-builder` | memory 冲突、业务域归属不清 | 不要求用户选择所有可能业务域 |
| `requirement-testability` | 影响需求模型的关键缺口 | 不为每个模糊词都生成问题 |
| `design-solution-extraction` | 影响设计事实、接口契约、状态或数据依赖的缺口 | 不补造设计方案没有给出的规则 |
| `testing-method-router` | 影响方法必要性的范围问题 | 不为了可选方法制造待确认项 |
| 专项分析 skill | 影响决策表、状态图、权限矩阵、接口契约的关键缺口 | 不追问可作为过程风险处理的细枝末节 |
| `testpoint-generation` | 影响测试点粒度或是否保留风险确认点的问题 | 不打断生成流程 |
| `test-analysis-solution-generation` | 影响测试点明细或预期结果的问题 | 不打断生成流程；缺口落到 `预期结果 = 待人工分析确认` |
| `coverage-review` | 阻断质量门禁关闭的需求缺失 | 不因普通覆盖建议制造阻断项 |

## 候选问题字段

每个候选问题应包含：

| 字段 | 说明 |
|---|---|
| 问题ID | 使用 `CQ-001` 递增 |
| checkpoint | 检查点，例如 `CP-INPUT` |
| sourceStage | 来源阶段或 skill |
| header | 12 个字以内，用于归类问题 |
| question | 面向后续设计人员的清晰问题 |
| why | 为什么必须确认 |
| impact | 不确认会影响什么 |
| options | 2 到 4 个可能处理方向，可为空但不得编造成已确认规则 |
| blockingLevel | `Blocking`、`Important` 或 `Optional` |
| priority | `P0`、`P1`、`P2` 或 `P3` |
| askPolicy | 统一写为 `DoNotAsk` |
| mustAsk | 统一写为 `否` |
| relatedRequirement | 关联需求依据 |
| expectedResultFallback | 是否需要把相关测试点明细预期结果写成 `待人工分析确认` |
| memoryConflict | 如有冲突，说明冲突的 memory 来源 |

统一候选表头如下，所有阶段必须按此 schema 输出 `CQ-*` 候选：

| 问题ID | checkpoint | sourceStage | header | question | why | impact | options | blockingLevel | priority | askPolicy | mustAsk | relatedRequirement | expectedResultFallback | memoryConflict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## 优先级规则

| 优先级 | 说明 | 默认处理 |
|---|---|---|
| `P0` | 不确认会导致核心业务规则、状态、权限、接口契约或高风险测试点错误 | 过程记录标为阻断风险；相关预期结果写 `待人工分析确认` |
| `P1` | 不确认会明显影响覆盖范围、方法选择或报告可用性 | 过程记录标为重要风险；相关预期结果写 `待人工分析确认` |
| `P2` | 不确认仍可继续，但会留下普通设计风险 | 过程记录；必要时相关预期结果写 `待人工分析确认` |
| `P3` | 只影响措辞、偏好或低风险补充 | 通常只保留在过程记录 |

## 去重、排序和收口

每次调用本 skill 时必须先处理候选队列：

1. 合并同一业务对象、同一规则或同一状态缺口的问题。
2. 删除已被当前需求、设计方案、memory、上下文包或已有场景条件明确覆盖的问题。
3. 按 `priority`、`blockingLevel`、影响范围和需求依据清晰度排序。
4. 将仍未解决且会影响预期结果的问题标记 `expectedResultFallback = 是`。
5. 将只影响过程说明或后续人工补充的问题保留在 `process/clarification-session.md`，不得写入主交付件章节。
6. 全流程不调用用户交互能力，不暂停主流程，不向用户发起中途确认。

## 预期结果兜底规则

当以下信息在需求和设计方案中没有明确依据时，相关测试点明细的 `预期结果` 必须写 `待人工分析确认`：

- 错误提示。
- 错误码。
- 失败后的状态变化。
- 接口返回内容。
- 消息发送结果。
- 数据库、缓存、日志或审计记录变化。
- 多规则冲突时的优先级。

不得为上述缺口单独创建 `未明确规则` 章节，也不得在主交付件创建待确认信息清单。

## 过程记录

如存在候选问题，创建或更新 `${PROJECT_ROOT}/outputs/runs/<run-id>/process/clarification-session.md`，记录：

- 当前检查点。
- 候选问题队列。
- 去重和排序结果。
- 未进入主交付件的原因。
- 需要触发 `预期结果 = 待人工分析确认` 的测试点明细范围。
- 是否建议沉淀到长期 memory。

该文件是运行产物，不是长期 memory，也不是后续测试分析方案评审、细化或落地的必读文件。

## 输出

每次调用本 skill 必须输出：

- 候选问题去重结果。
- 需要过程保留的问题列表。
- 需要让测试点明细预期结果写 `待人工分析确认` 的问题列表。
- 被移除的问题和移除原因。
- 是否需要刷新 `process/clarification-session.md`。

## 约束

- 不生成测试点。
- 不生成测试设计项或 TDI。
- 不生成测试用例或操作步骤。
- 不调用用户交互能力。
- 不在分析过程中向用户提问或暂停主流程。
- 不把任何候选问题伪装成用户已确认事实。
- 不向 `deliverables/test-analysis-solution.md` 写待确认信息章节。
- 不把用户本次后续反馈自动写入 `memory/project-memory.md`、`memory/domains/*.md` 或 `memory/testing-experience-memory.md`。
