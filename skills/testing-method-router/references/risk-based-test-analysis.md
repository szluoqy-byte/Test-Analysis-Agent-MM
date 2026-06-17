# 风险驱动测试分析 方法参考

本方法参考 用来判断“哪里失败代价最高，哪里应该优先测”。

## 职责边界

- 本方法参考 只产出风险方法证据、风险登记和级别建议，供 `test-analysis-solution-generation` 给测试点定级和补充风险备注。
- 风险评分、失败模式和历史缺陷信号是优先级依据，不直接变成测试用例展开规则、用例数量或执行步骤。
- 测试分析方案生成阶段会基于风险测试点生成测试点；本方法参考不写测试用例。

## 输入

- 输入事实模型。
- 上下文来源索引。
- `process/context-pack.json` 中 `sources[]` 对 `testing-method-router` 可见的 project/personal 风险画像、个人关注点、oracle 补充和风险类 checklist。
- `knowledge/testpoint-standard.md`。
- `knowledge/test-techniques/README.md`。
- `knowledge/test-techniques/risk-based/risk-based-testing.md`。
- `knowledge/test-techniques/experience-based/error-guessing-checklist.md`。

## 风险识别方式

- 使用 `knowledge/test-techniques/README.md` 中的专家审视顺序和 Oracle 规则判断风险覆盖方向。
- 使用 `knowledge/test-techniques/experience-based/error-guessing-checklist.md` 匹配通用缺陷模式。
- 使用 `${PROJECT_ROOT}/outputs/runs/<run-id>/process/context-pack.json` 中对本阶段可见的动态来源修正风险关注点。
- 使用已读取的 project/personal 动态来源补充识别项目级风险画像、个人关注点、覆盖策略和判定依据启发；补充不得写成已确认业务事实。
- 对本阶段可见且被读取的风险类动态来源，必须输出应用状态。
- 使用 `knowledge/test-techniques/risk-based/risk-based-testing.md` 判断建议级别，级别定义仍以 `knowledge/testpoint-standard.md` 为准。

风险识别必须区分三类来源：

| 来源 | 处理方式 |
|---|---|
| 需求明确说明 | 可直接作为测试点依据 |
| memory 或历史缺陷提示 | 可作为风险加权依据，但需保留来源 |
| 通用缺陷模式推断 | 只能作为风险确认点或输入不足说明 |

## 级别规则

级别定义以 `knowledge/testpoint-standard.md` 为准；本方法参考 只负责根据风险原因建议级别。

## 输出

先输出方法分析证据：

| 证据ID | 方法 | 风险点/失败模式 | 分析结论 | 关联测试点/说明 |
|---|---|---|---|---|

再输出风险登记表：

| 模块 | 风险点 | 风险原因 | 建议级别 | 关联需求依据 |
|---|---|---|---|---|

如存在高风险但依据不足的问题，追加输入不足说明或风险确认点：

| 问题ID | checkpoint | sourceStage | header | question | why | impact | options | blockingLevel | priority | askPolicy | mustAsk | relatedRequirement | memoryConflict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

如本阶段读取了动态来源，追加应用记录：

| 来源文件 | 当前阶段 | 应用状态 | 应用位置 | 说明 |
|---|---|---|---|---|

## 约束

- 风险可以将测试点调整为更高重要级别，但不能创造需求中没有的业务规则。
- 合理但未明确的风险，标记为 `insufficient_evidence` 或风险确认点，不创建问题队列。
- 不直接向用户提问。
- 不把风险等级当作测试点数量的唯一依据；高风险需要更强证据或更明确覆盖对象。
- 最终主交付件中只保留可追踪到需求、memory 或风险确认点的风险备注；不把通用风险推断写成已确认业务规则。
- 如果可见动态来源中的 project/personal 风险画像不足，只能按 `sources[]` 记录的可见来源或当前需求明确指向的文件补读相关章节，并在方法证据中记录来源；不得全目录搜索或全量复制大文件。
- 对本阶段可见且被读取的动态来源必须留痕；如果未应用，必须使用 `not_applicable`、`insufficient_evidence` 或 `conflict_with_requirement` 解释。
