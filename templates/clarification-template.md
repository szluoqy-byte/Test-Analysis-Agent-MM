# 待确认治理记录模板

本模板用于记录各阶段产生的待确认候选。候选问题只作为过程治理信息，不写入主交付件 `deliverables/test-analysis-solution.md` 的独立章节。

`process/clarification-session.md` 是固定 process 产物。即使当前 run 没有待确认候选，也必须生成本文件，并在运行状态中声明 `无待确认候选`。

如果某个缺口影响测试点明细的判定依据，主交付件只在对应测试点明细的 `预期结果` 写 `待人工分析确认`。

## 0. 运行状态

- 治理结论：无待确认候选 / 存在待确认候选
- 说明：

## 1. 候选问题总表

| 问题ID | checkpoint | sourceStage | header | question | why | impact | options | blockingLevel | priority | askPolicy | mustAsk | relatedRequirement | memoryConflict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CQ-001 | CP-INPUT | requirement-testability |  |  |  |  |  | Important/Blocking | High/Medium/Low | defer/auto-resolve | false |  |  |

## 2. 去重与降级结果

| 原问题ID | 处理结果 | 合并到 | 降级原因 | 保留影响 |
|---|---|---|---|---|
|  | kept/merged/downgraded/dropped |  |  |  |

## 3. 预期结果兜底清单

| 问题ID | 影响场景/测试点/测试点明细 | 兜底原因 | 主交付件处理 |
|---|---|---|---|
| CQ-001 | TP-001 / TP-001-002 | 需求未说明错误提示、状态变化或错误码 | 预期结果写 `待人工分析确认` |

## 4. 治理规则

- 本 Agent 默认不向用户提问，不暂停主流程。
- 问题必须说明会影响哪些测试分析结论、场景、接口、测试点或测试点明细。
- 主交付件不输出独立待确认章节。
- 不把未确认信息写入 `knowledge/` 或 `memory/` 源文件。
- 无待确认候选时，保留固定章节和表头，可以不填写候选行。
