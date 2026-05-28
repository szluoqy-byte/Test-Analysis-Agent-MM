# Skills 架构优化分析

## 1. 分析范围

本文分析 `skills/` 的职责分层、调用链、输入输出契约、质量门禁闭环和后续优化方向。分析基于当前仓库文件，不依赖历史项目假设。

核心目标是判断当前 skill 架构是否能稳定支撑：

```text
需求文档 + 可选设计方案 -> 测试场景 -> 测试点 -> 测试设计项
```

## 2. 当前 Skills 拓扑

| 层级 | Skill | 当前职责 | 主要输出 |
|---|---|---|---|
| 编排入口 | `analyze-requirement-test-design-solution` | 固定项目根目录、创建 run、编排全链路、写出主交付件 | `deliverables/test-design-solution.md` |
| 上下文层 | `memory-context-builder` | 发现并裁剪 core/project/personal 上下文 | `process/context-pack.md` |
| 需求分析层 | `requirement-testability` | 提取可验证对象、角色、规则、流程、状态、接口和缺口 | 结构化需求模型、需求待确认候选 |
| 设计分析层 | `design-solution-extraction` | 提取接口、字段、状态、权限、数据依赖、配置、异常处理、非功能约束和设计缺口 | 设计方案事实摘要、设计缺口候选 |
| 待确认治理层 | `clarification-gate` | 在 `CP-INPUT`、`CP-ANALYSIS`、`CP-REVIEW` 三个检查点治理候选缺口 | `process/clarification-session.md`、预期结果兜底清单 |
| 路由层 | `testing-method-router` | 根据分析维度和触发信号选择测试技术和专项分析 skill | 测试技术路由表、技术范围缺口候选 |
| 专项分析层 | 专项 skill | 产出 `ME-*` 方法证据和测试点候选 | 方法证据、测试点候选、技术缺口候选 |
| 测试点聚合层 | `testpoint-generation` | 把方法证据和候选归并为场景和测试点 | `SC-*`、`TP-*` |
| 测试设计层 | `test-design-solution-generation` | 把测试点展开为测试设计项和预期结果 | `TD-*` 测试设计项 |
| 独立评审层 | `test-design-solution-review` | 评审设计项粒度、预期结果依据和旧字段泄漏 | 独立评审结论 |
| 审查层 | `coverage-review` | 执行质量门禁、专家评分和确定性脚本校验 | 覆盖审查结果、修正建议、阻断项 |

当前架构是清晰的流水线：入口编排，context/requirement/router/specialist/generator/reviewer 各层职责基本成立。

## 3. 主要优化点

### F1. 产物契约已迁移为测试设计方案

主输出现在只包含 `测试设计项 ID | 测试设计项 | 预期结果` 三列。旧字段 `覆盖意图`、`级别`、`输入条件与数据依赖`、`判定关注` 和 `待确认信息` 不再进入主交付件。

影响：

- 输出更接近用户当前目标：测试点 + 对应输入测试数据场景/状态/组合 + 预期结果。
- 完整用例写作仍留给下游，不提前生成步骤和执行数据。
- 预期结果从“禁止字段”变成“必填字段”，但必须受需求/设计方案依据约束。

### F2. 缺口治理从主交付件章节转为预期结果兜底

`clarification-gate` 仍负责过程级待确认治理，但不再向主交付件写独立待确认章节。需求或设计方案未说明错误提示、状态变化、错误码、接口返回或数据记录变化时，生成阶段将相关设计项的 `预期结果` 写成 `待人工分析确认`。

影响：

- 主交付件更精简。
- 缺口直接贴近受影响的测试设计项。
- 不再需要 `## 3. 未明确规则` 或待确认信息清单。

### F3. 独立评审 Agent 以 skill 实现

根据项目规则，不新增插件级 `agents/`。独立评审能力由 `test-design-solution-review` skill、`quality-gates/test-design-solution-check.md` 和 `bin/lint-test-design-solution.py` 共同承担。

影响：

- 保持 Claude Code/OpenCode 双入口兼容。
- 评审规则可被运行时校验和 smoke 检查覆盖。
- 角色化行为不依赖外部 Agent 注册机制。

## 4. 推荐目标架构

| 层级 | 建议状态 | 调整方向 |
|---|---|---|
| 编排入口 | 保持单入口 | 只负责调度、run 目录、任务清单和最终落盘 |
| 上下文层 | 保持独立 | 将 project/personal 发现策略继续沉淀在 context pack，不下放给后续 skill 自行搜索 |
| 需求与设计层 | 保持双输入契约 | `requirement-testability` 负责需求模型，`design-solution-extraction` 负责设计事实摘要 |
| 路由层 | 保持独立 | 明确输出只到测试技术路由，不提前选择测试设计项 |
| 专项分析层 | 统一输出骨架 | 所有专项 skill 使用同一方法证据表、候选测试点表和缺口候选表 |
| 测试点生成层 | 强化 handoff | `testpoint-generation` 输出稳定的场景/测试点中间契约 |
| 测试设计层 | 保持独立 | 专注 `TD-*`、代表性条件/数据/状态/组合和预期结果 |
| 独立评审层 | 保持独立 | 先审设计项粒度和预期结果依据，再进入覆盖审查 |
| 覆盖审查层 | 拆分判断类型 | 机械脚本、质量门禁、专家评分和过程缺口治理分别列明结果 |

## 5. 后续优化路线

1. 统一专项 skill 输出骨架：所有专项分析都引用 `knowledge/method-evidence-standard.md` 和 `templates/method-analysis-template.md`。
2. 强化设计事实使用：让 `design-solution-extraction` 的结构化结果稳定进入测试技术路由、测试点生成和测试设计项生成。
3. 深化 test-techniques：补充更多测试设计项展开示例，并补齐预期结果兜底样例。
4. 扩展评审样例：增加包含错误码缺失、状态变化缺失和提示文案缺失的样例，验证 `待人工分析确认` 规则。

## 6. 当前结论

当前 skills 架构已经具备独立 Agent 的基本闭环：入口清楚、专项测试技术齐全、生成链路完整、独立评审和质量门禁可运行。

最关键的架构原则是：测试分析层输出测试点，测试设计层输出测试设计项，测试技术库同时支持两层，但不直接决定主交付件字段。
