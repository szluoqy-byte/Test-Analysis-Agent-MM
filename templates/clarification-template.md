# 待确认问题治理模板

本模板用于记录各阶段产生的待确认候选。候选问题只作为过程治理信息，不写入主交付件 `deliverables/test-design-solution.md` 的独立章节。

如果某个缺口影响测试设计项的判定依据，主交付件只在对应设计项的 `预期结果` 写 `待人工分析确认`。

## 候选问题队列

各阶段先产出候选问题，不直接触发交互，不在分析过程中打断用户。

```markdown
| 问题ID | checkpoint | sourceStage | header | question | why | impact | options | blockingLevel | priority | askPolicy | mustAsk | relatedRequirement | expectedResultFallback | memoryConflict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
```

`问题ID` 使用 `CQ-001` 递增；`askPolicy` 统一填写 `DoNotAsk`；`mustAsk` 统一填写 `否`。无 memory 冲突时 `memoryConflict` 填写 `无`。

## 治理规则

- `P0/P1` 且仍未解决的问题必须进入过程记录。
- 影响单条测试设计项预期结果的问题，`expectedResultFallback` 写 `是`。
- `P2` 问题按影响范围保留在过程记录，必要时触发相关设计项 `预期结果 = 待人工分析确认`。
- `P3` 问题默认只保留在过程记录。
- 已被需求原文、设计方案、上下文包、场景说明或测试点描述覆盖的问题应移除。
- 重复问题必须合并，同一业务对象、同一规则或同一状态缺口只保留一个最清晰的问题。
- 不把候选问题写成已确认业务规则；缺少依据时必须明确“待确认”。
- 不创建 `未明确规则` 主交付件章节。

## 过程记录产物

```markdown
# <需求名称> 待确认问题治理记录

## 基本信息

- 需求文档：
- 项目根目录：
- 运行 ID：
- 运行目录：
- 生成时间：
- 当前检查点：
- 当前状态：Collecting / Finalized

## 候选问题队列

| 问题ID | checkpoint | sourceStage | header | question | why | impact | options | blockingLevel | priority | askPolicy | mustAsk | relatedRequirement | expectedResultFallback | memoryConflict | 状态 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## 去重与降级记录

| 问题ID | 处理结果 | 原因 | 后续承接位置 |
|---|---|---|---|

处理结果可取：过程保留、触发预期兜底、合并到其他问题、已由需求覆盖、仅保留过程记录。

## 预期结果兜底清单

| 问题ID | 影响场景/测试点/测试设计项 | 兜底原因 | 主交付件处理 |
|---|---|---|---|
| CQ-001 | TP-001 / TDI-003 | 需求未说明错误提示、状态变化或错误码 | 预期结果写 `待人工分析确认` |

## 建议沉淀的 Memory 更新
```

## 问题设计要求

- 问题必须说明会影响哪些测试分析结论、场景、接口、测试点或测试设计项。
- 问题必须面向后续需求确认或用例设计人员可读，不依赖过程报告才能理解。
- 用户后续反馈不自动写入长期 memory；只有用户明确确认沉淀时，才更新 memory 源文件。
- 主交付件不展示“待确认信息”；缺少判定依据只通过 `预期结果 = 待人工分析确认` 表达。
