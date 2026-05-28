---
name: risk-based-test-analysis
description: 当需要按产品、业务、数据、权限、集成、运维和历史缺陷风险来识别重点覆盖区域和测试点级别时使用。
---

# 风险驱动测试分析 Skill

本 skill 用来判断“哪里失败代价最高，哪里应该优先测”。

## 职责边界

- 本 skill 只产出风险方法证据、风险登记和级别建议，供 `testpoint-generation` 给测试点定级和补充风险备注。
- 风险评分、失败模式和历史缺陷信号是优先级依据，不直接变成测试设计项展开规则、用例数量或执行步骤。
- 测试设计方案生成阶段会基于风险测试点决定测试设计项展开方式；本 skill 不写完整测试用例。

## 输入

- 结构化需求模型。
- 记忆上下文包。
- 记忆上下文包中命中的 project/personal 风险画像、个人关注点和 oracle 补充。
- `process/context-pack.md` 中绑定到 `risk-based-test-analysis` 的 project knowledge 文件，例如风险画像、历史高风险策略或风险类 checklist。
- `knowledge/testpoint-standard.md`。
- `knowledge/test-techniques/README.md`。
- `knowledge/test-techniques/risk-based/risk-based-testing.md`。
- `knowledge/test-techniques/experience-based/error-guessing-checklist.md`。

## 风险识别方式

- 使用 `knowledge/test-techniques/README.md` 中的专家审视顺序和 Oracle 规则判断风险覆盖方向。
- 使用 `knowledge/test-techniques/experience-based/error-guessing-checklist.md` 匹配通用缺陷模式。
- 使用 `${PROJECT_ROOT}/outputs/runs/<run-id>/process/context-pack.md` 中的项目历史缺陷和项目风险模式修正关注点。
- 使用 context pack 中的 project/personal knowledge 补充识别项目级风险画像、个人关注点、覆盖策略和判定依据启发；补充不得写成已确认业务事实。
- 如果 context pack 的“项目知识阶段绑定”存在绑定到 `risk-based-test-analysis` 的 project knowledge，必须读取相关章节并输出应用状态。
- 使用 `knowledge/test-techniques/risk-based/risk-based-testing.md` 判断建议级别，级别定义仍以 `knowledge/testpoint-standard.md` 为准。

风险识别必须区分三类来源：

| 来源 | 处理方式 |
|---|---|
| 需求明确说明 | 可直接作为测试点依据 |
| memory 或历史缺陷提示 | 可作为风险加权依据，但需保留来源 |
| 通用缺陷模式推断 | 只能作为风险确认点或待确认问题 |

## 级别规则

级别定义以 `knowledge/testpoint-standard.md` 为准；本 skill 只负责根据风险原因建议级别。

## 输出

先输出方法分析证据：

| 证据ID | 方法 | 风险点/失败模式 | 分析结论 | 关联测试点/待确认 |
|---|---|---|---|---|

再输出风险登记表：

| 模块 | 风险点 | 风险原因 | 建议级别 | 关联需求依据 |
|---|---|---|---|---|

如存在高风险但依据不足的问题，追加待确认候选或风险确认点：

| 问题ID | checkpoint | sourceStage | header | question | why | impact | options | blockingLevel | priority | askPolicy | mustAsk | relatedRequirement | memoryConflict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

如本阶段绑定了 project knowledge，追加应用记录：

| 来源文件 | 当前阶段 | 应用状态 | 应用位置 | 说明 |
|---|---|---|---|---|

## 约束

- 风险可以将测试点调整为更高重要级别，但不能创造需求中没有的业务规则。
- 合理但未明确的风险，标记为“待确认”或“风险确认点”。
- 不直接向用户提问。
- 不把风险等级当作测试点数量的唯一依据；高风险需要更强证据或更明确覆盖对象。
- 最终主交付件中只保留可追踪到需求、memory 或风险确认点的风险备注；不把通用风险推断写成已确认业务规则。
- 如果 context pack 中的 project/personal 风险画像不足，只能按 context pack 记录的来源或当前需求明确指向的文件补读相关章节，并在方法证据中记录来源；不得全目录搜索或全量复制大文件。
- 绑定到本阶段的 project knowledge 必须读取并留痕；如果未应用，必须使用 `not_applicable`、`insufficient_evidence` 或 `conflict_with_requirement` 解释。
