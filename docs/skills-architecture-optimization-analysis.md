# Skills 架构优化分析

## 1. 分析范围

本文分析 `skills/` 的职责分层、调用链、输入输出契约、质量门禁闭环和后续优化方向。分析基于当前仓库文件，不依赖历史项目假设。

核心目标是判断当前 skill 架构是否能稳定支撑两个子 Agent：

```text
需求文档 + 可选设计方案 -> 测试场景 -> 测试点 -> 测试点明细
非成功测试点明细 -> 失败类型明细
已评审测试分析方案 -> 测试设计项
```

## 2. 当前 Agent 与 Skills 拓扑

| 层级 | Skill | 当前职责 | 主要输出 |
|---|---|---|---|
| Agent 门面 | `agents/test-analysis-agent.md` | 支持 `@test-analysis-agent`，识别测试分析、上下文归档或框架维护意图 | 用户入口、路由决策 |
| Agent 门面 | `agents/test-design-agent.md` | 支持 `@test-design-agent`，识别测试设计、设计评审或框架维护意图 | 用户入口、路由决策 |
| 输入归一化层 | `normalize-input-documents` | 将 `.docx` / `.xlsx` 需求、设计依据或外部分析方案转换到全局 cache，并绑定为 run-local Markdown | `outputs/input-cache/<sha256-12>/`、`outputs/runs/<run-id>/inputs/` |
| 分析编排入口 | `test-analysis-workflow` | 固定项目根目录、创建 run、编排分析链路、写出测试分析方案 | `deliverables/test-analysis-solution.json` |
| 设计编排入口 | `test-design-workflow` | 复用或创建 run，承接已评审测试分析方案，写出测试设计方案 | `deliverables/test-design-solution.json` |
| 上下文归档 | `context-capture` | 处理“记住/记录/收录/归档”类请求，判断写入 memory 或 knowledge | 长期 personal/project 上下文 |
| 上下文层 | `memory-context-builder` | 发现并裁剪 core/project/personal 上下文，登记 project knowledge 阶段绑定 | `process/context-pack.json` |
| 输入事实建模层 | `input-fact-modeling` | 从需求文档和可选设计方案建立事实清单、需求-设计映射、待确认事项和来源应用说明 | `process/input-fact-model.json` |
| 待确认治理层 | `clarification-gate` | 在 `CP-INPUT`、`CP-ANALYSIS`、`CP-REVIEW` 三个检查点治理候选缺口 | `process/clarification-session.json`、预期结果兜底清单 |
| 路由层 | `testing-method-router` | 根据分析维度和触发信号选择测试技术和专项方法参考 | 测试技术路由表、技术范围缺口候选 |
| 专项方法参考层 | `skills/testing-method-router/references/*.md` | 为路由阶段提供专项分析步骤，产出 `ME-*` 方法证据和测试点候选 | 方法证据、测试点候选、技术缺口候选 |
| 测试分析方案生成层 | `test-analysis-solution-generation` | 把方法证据和候选归并为场景、测试点、测试点明细和预期结果；非成功测试点明细继续拆分失败类型明细 | `SC-*`、`TP-*`、`TP-*-*` 测试点明细、`TP-*-*-*` 失败类型明细 |
| 确定性校验层 | `bin/lint-test-analysis-solution.py` / `bin/lint-test-design-solution.py` | 检查结构、编号、字段、禁用术语、Markdown 语法和固定交付件格式 | lint 结果 |
| 独立评审层 | `test-analysis-solution-review` | 在 lint 通过后评审测试点明细粒度、失败类型拆分充分性、预期结果依据、事实溯源和非用例化语义 | 独立语义评审结论 |
| 测试设计方案生成层 | `test-design-solution-generation` | 把普通测试点明细或失败类型明细扩展为代表性条件、具体数据值、数据槽位、状态、接口返回或组合 | `TDI-*` 测试设计项 |
| 测试设计评审层 | `test-design-solution-review` | 在 lint 通过后评审设计项数据化粒度、叶子节点预期结果依据、分析方案承接和非用例化语义 | 独立语义评审结论 |
| 审查层 | `coverage-review` | 执行覆盖、追踪、方法应用、rules/project knowledge 应用和过程门禁；专家评分仅深度评估时执行 | 覆盖审查结果、修正建议、阻断项 |

当前架构是清晰的流水线：入口编排，context/requirement/router/specialist/generator/reviewer 各层职责基本成立。

## 3. 主要优化点

### F1. 产物契约已迁移为测试分析方案

主输出现在使用三级标题结构承载：

```text
SC-* 测试场景
  -> TP-* 测试点
      -> TP-*-* 测试点明细
          -> TP-*-*-* 失败类型明细（仅非成功测试点明细）
```

影响：

- 当前 Agent 专注 what to test，不再输出 `TDI-*` 测试设计项。
- 给 `test-design-agent` 留出清晰空间，由它基于评审后的测试分析方案补充代表性条件、具体数据值、数据槽位、状态、接口返回或组合。
- 预期结果保留在测试点明细层，但必须受需求/设计方案依据约束。
- 每个测试场景新增 `E2E场景测试` 测试点，用于确保端到端主流程闭环不被局部规则覆盖稀释。
- 非成功路径的第四层由 `TP-*-*` 测试点明细触发，不由 `TP-*` 测试点主题触发。

### F2. 缺口治理从主交付件章节转为预期结果兜底

`clarification-gate` 仍负责过程级待确认治理，但不再向主交付件写独立待确认章节。需求或设计方案未说明错误提示、状态变化、错误码、接口返回或数据记录变化时，生成阶段将相关测试点明细的 `预期结果` 写成 `待人工分析确认`。

影响：

- 主交付件更精简。
- 缺口直接贴近受影响的测试点明细。
- 不再需要 `## 3. 未明确规则` 或待确认信息清单。

### F3. Agent 门面与执行 skill 分离

当前架构使用 `test-analysis-agent` 作为用户可 `@` 调用的门面。它负责识别“生成测试分析方案、记录偏好/知识、维护框架、咨询方法”等用户意图；具体执行仍由 skills、knowledge、templates、quality gates 和 bin 脚本完成。

### F4. Project Knowledge 阶段绑定

project knowledge 文件不要求固定命名或固定结构。`memory-context-builder` 只在 context pack 中识别文件用途和强制应用环节，不提前判断具体测试点或测试点明细命中。

影响：

- 测试设计因子库、业务测试设计模式库可以绑定到测试技术路由和测试分析方案生成。
- 测试设计 checklist 默认绑定到覆盖审查统一查漏；只有明确声明产物语义评审用途时，才额外绑定到独立评审。
- 后续阶段必须读取绑定文件并输出应用状态，避免“读过但没有用”的假强应用。

## 4. 推荐目标架构

| 层级 | 建议状态 | 调整方向 |
|---|---|---|
| Agent 门面 | 保持轻量 | 只做意图识别、路由和用户体验收口，不沉淀测试理论或复杂流程 |
| 编排入口 | 保持单入口 | 只负责调度、run 目录、任务清单和最终落盘 |
| 上下文层 | 保持独立 | 将 project/personal 发现策略和 project knowledge 阶段绑定沉淀在 context pack，不下放给后续 skill 自行搜索 |
| 需求与设计层 | 统一输入事实模型 | `input-fact-modeling` 负责需求事实、设计事实、映射关系、缺口冲突和待确认事项 |
| 路由层 | 保持独立 | 明确输出只到测试技术路由，不提前选择测试点明细 |
| 专项方法参考层 | 统一输出骨架 | 所有专项方法参考使用同一方法证据表、候选测试点表和缺口候选表 |
| 测试分析方案生成层 | 保持独立 | 统一生成 `SC-*`、`TP-*`、`TP-*-*`、非成功 `TP-*-*-*` 失败类型明细和预期结果 |
| 确定性校验层 | 前置执行 | 先跑 lint，结构失败时不进入模型评审 |
| 独立评审层 | 保持独立但收窄职责 | 只审粒度、预期结果依据、事实溯源、失败类型充分性和非用例化语义 |
| 覆盖审查层 | 拆分判断类型 | 覆盖、追踪、方法应用、rules/project knowledge、过程一致性和可选专家评分分别列明结果 |

## 5. 后续优化路线

1. 统一专项方法参考输出骨架：所有专项分析都引用 `skills/testing-method-router/references/method-evidence-standard.md`。
2. 强化输入事实使用：让 `input-fact-modeling` 的结构化结果稳定进入测试技术路由和测试分析方案生成。
3. 梳理 test-techniques：明确哪些内容服务 `test-analysis-agent`，哪些示例服务 `test-design-agent`。
4. 扩展评审样例：增加包含错误码缺失、状态变化缺失和提示文案缺失的样例，验证 `待人工分析确认` 规则。

## 6. 当前结论

当前 skills 架构已经具备独立 Agent 的基本闭环：入口清楚、专项测试技术齐全、生成链路完整、独立评审和质量门禁可运行。

最关键的架构原则是：`test-analysis-agent` 输出测试场景、测试点和测试点明细；`test-design-agent` 再输出 `TDI-*` 测试设计项；测试技术库同时支持两层，但不直接决定分析主交付件字段。
