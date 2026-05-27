# Skills 架构优化分析

## 1. 分析范围

本文分析 `skills/` 下 17 个 skill 的职责分层、调用链、输入输出契约、质量门禁闭环和后续优化方向。分析基于当前仓库文件，不依赖历史项目假设。

核心目标是判断当前 skill 架构是否能稳定支撑：

```text
需求文档 + 可选设计方案 -> 测试场景 -> 测试点 -> 测试用例标题项
```

## 2. 当前 Skills 拓扑

| 层级 | Skill | 当前职责 | 主要输出 |
|---|---|---|---|
| 编排入口 | `analyze-requirement-testcase-outline` | 固定项目根目录、创建 run、编排全链路、写出主交付件 | `deliverables/testcase-title-outline.md` |
| 上下文层 | `memory-context-builder` | 发现并裁剪 core/project/personal 上下文 | `process/context-pack.md` |
| 需求分析层 | `requirement-testability` | 提取可验证对象、角色、规则、流程、状态、接口和缺口 | 结构化需求模型、需求待确认候选 |
| 待确认治理层 | `clarification-gate` | 在多个检查点收集、去重、分级、排序待确认候选 | `Q-*` 最终待确认信息、过程治理记录 |
| 路由层 | `testing-method-router` | 根据分析维度和触发信号选择专项方法 | 方法路由表、方法范围待确认候选 |
| 专项分析层 | 9 个专项 skill | 产出 `ME-*` 方法证据和测试点候选 | 方法证据、测试点候选、方法缺口候选 |
| 测试点聚合层 | `testpoint-generation` | 把方法证据和候选归并为场景、场景条件、测试点和接口测试点 | `SC-*`、`TP-*`、`ITP-*` |
| 标题大纲层 | `testcase-title-outline-generation` | 把测试点展开为标题项，补输入条件与数据依赖、判定关注 | `TCT-*` 标题项 |
| 审查层 | `coverage-review` | 执行质量门禁、专家评分和确定性脚本校验 | 覆盖审查结果、修正建议、阻断项 |

当前架构是清晰的流水线：入口编排，context/requirement/router/specialist/generator/reviewer 各层职责基本成立。

## 3. 已验证事实

| 证据 | 结论 |
|---|---|
| `skills/` 当前包含 17 个 skill | 主入口、上下文、需求、路由、专项分析、生成、审查层齐全 |
| 11 个 skill 显式包含 `## 职责边界` | 主入口、标题生成和 9 个专项分析 skill 的边界较清楚 |
| 所有 skill 均包含 `## 输入` 和 `## 输出` 或等价章节 | 输入输出契约在文档层基本完整 |
| `bin/` 中存在 `lint-testpoint-report.py`、`semantic-testpoint-check.py`、`check-artifact-consistency.py` | `coverage-review` 引用的过程报告校验脚本真实存在 |
| 两个示例报告均通过 `lint-testpoint-report.py` 和 `semantic-testpoint-check.py` | 过程报告校验链路可运行 |
| `python bin/smoke-test-analysis.py` 通过 | 主输出示例和基础 runtime wiring 当前可用 |
| Mermaid 主流程图通过 `bin/check-design-doc-mermaid.py`，且在线 SVG 渲染成功 | 设计文档主流程图已修复到可导出图片的 Mermaid 写法 |

## 4. 主要发现

### F1. 设计方案提取仍是入口内隐阶段

`analyze-requirement-testcase-outline` 把“设计方案提取”定义为阶段，但仓库没有独立的 `design-solution-extraction` skill。当前做法适合轻量设计文档；当设计方案复杂时，会让主入口承担结构化提取、缺口判断和字段归一化职责。

影响：

- 主入口职责偏重，后续维护容易膨胀。
- `testpoint-generation` 和 `testcase-title-outline-generation` 都依赖“设计方案事实摘要”，但该摘要的 schema 不如需求模型清晰。
- 设计缺口候选与需求缺口候选容易混在 `CP-REQUIREMENT-DESIGN` 中。

建议优先级：P1。

### F2. 专项分析 skill 输出模式相似，但缺少统一的机械契约

9 个专项 skill 都产出方法证据和候选测试点，但输出表头、字段命名和候选结构由各 skill 自己描述。`knowledge/method-evidence-standard.md` 已定义方法证据标准，`templates/method-analysis-template.md` 也存在，但专项 skill 没有统一引用模板作为硬性输出骨架。

影响：

- 专项方法输出在人工运行时容易漂移。
- `testpoint-generation` 需要容忍多种候选表结构。
- 方法证据与 `TP-*` / `ITP-*` 的可追踪性更多依赖 reviewer 事后检查。

建议优先级：P1。

### F3. 部分核心 skill 缺少统一的 `职责边界` 章节

`requirement-testability`、`testing-method-router`、`memory-context-builder`、`clarification-gate`、`testpoint-generation`、`coverage-review` 没有统一使用 `## 职责边界`。这些 skill 正好是跨层传递信息的关键节点，缺少统一章节会降低架构可读性。

影响：

- 新维护者更难判断“这一层不做什么”。
- 入口、生成、审查之间的边界虽然散落在约束中，但不如专项 skill 直观。

建议优先级：P2。

### F4. `coverage-review` 同时承担专家评审、门禁编排和脚本调度

`coverage-review` 当前负责 quality gates、task-list 检查、主输出 lint、跨产物一致性、过程报告校验、project/personal 复核和专家评分。它是必要的收口点，但职责密度高。

影响：

- 一旦门禁数量继续增加，审查 skill 会变成第二个编排入口。
- 机械校验、专家判断、待确认治理的失败处理策略可能混在一起。

建议优先级：P2。

### F5. 主交付件与过程报告之间的关系已清晰，但示例 smoke 覆盖仍偏主输出

`coverage-review` 和 `semantic-quality-check` 已要求过程报告校验；实际脚本也可运行。但 `smoke-test-analysis.py` 主要检查关键文件、Mermaid、标题大纲 lint，没有把过程报告 lint 和语义检查纳入固定 smoke。

影响：

- 主交付件回归能较早发现问题。
- 过程报告 schema 或语义漂移可能要到人工执行审查时才暴露。

建议优先级：P2。

## 5. 推荐目标架构

目标不是增加 skill 数量，而是让每一层的产物更稳定、更好校验。

| 层级 | 建议状态 | 调整方向 |
|---|---|---|
| 编排入口 | 保持单入口 | 只负责调度、run 目录、任务清单和最终落盘 |
| 上下文层 | 保持独立 | 将 project/personal 发现策略继续沉淀在 context pack，不下放给后续 skill 自行搜索 |
| 需求与设计层 | 拆出设计提取契约 | 保留 `requirement-testability`，新增或规范化设计方案事实摘要 schema |
| 路由层 | 保持独立 | 明确输出只到方法路由，不提前选择标题项设计模式 |
| 专项分析层 | 统一输出骨架 | 所有专项 skill 使用同一方法证据表、候选测试点表和缺口候选表 |
| 聚合生成层 | 强化 handoff | `testpoint-generation` 输出稳定的场景/测试点中间契约，标题生成只消费该契约 |
| 标题生成层 | 保持独立 | 专注 `TCT-*`、输入条件与数据依赖、判定关注 |
| 审查层 | 拆分判断类型 | 机械脚本、质量门禁、专家评分和待确认治理分别列明结果，不互相吞并 |

## 6. 分阶段优化路线

### 阶段 1：文档与契约标准化

建议先做低风险、收益高的文档标准化：

1. 为 `requirement-testability`、`testing-method-router`、`memory-context-builder`、`clarification-gate`、`testpoint-generation`、`coverage-review` 补齐 `## 职责边界`。
2. 在每个专项 skill 中统一引用 `knowledge/method-evidence-standard.md` 和 `templates/method-analysis-template.md`。
3. 新增“专项分析输出契约”小节，统一 `ME-*`、测试点候选、缺口候选三类输出。
4. 在设计文档中补一张 skills 分层表，避免只看主流程图无法理解 skill 架构。

验收：

- 所有 skill 都包含 `职责边界 / 输入 / 输出 / 约束` 四类章节或等价章节。
- `python bin/validate-agent-runtime.py` 通过。
- `python bin/smoke-test-analysis.py` 通过。

### 阶段 2：设计方案事实摘要独立化

当设计方案文档成为常态输入时，建议新增 `design-solution-extraction` skill，或至少新增 `templates/design-facts-template.md`。

建议 schema：

| 字段 | 内容 |
|---|---|
| 架构决策 | 影响测试范围和风险判断的实现选择 |
| 接口契约 | 请求方式、路径、字段、错误码、幂等、回调 |
| 状态与生命周期 | 状态集合、合法迁移、终态、异常恢复 |
| 权限与数据范围 | 角色、资源、动作、租户、归属关系 |
| 数据依赖 | 主数据、派生数据、缓存、日志、外部系统 |
| 配置与非功能 | 开关、灰度、性能、安全、可靠性 |
| 设计缺口 | 会影响测试点或标题项生成的问题 |

验收：

- `testpoint-generation` 和 `testcase-title-outline-generation` 不再依赖自由文本的设计方案事实摘要。
- `CP-REQUIREMENT-DESIGN` 能区分需求缺口与设计缺口。

### 阶段 3：审查链路分层

建议将 `coverage-review` 的执行结果拆成四类：

| 类别 | 示例 | 处理方式 |
|---|---|---|
| 机械校验 | lint、artifact consistency、report lint | 失败即阻断 |
| 质量门禁 | 覆盖、追踪、方法应用、风险级别 | 失败则修正或登记待确认 |
| 专家评分 | rubric 评分 | 低于通过线时给出修正建议 |
| 待确认治理 | `CP-REVIEW` | 只保留影响后续完整用例编写的问题 |

验收：

- 审查输出不把脚本失败、专家建议和需求缺口混成同一种失败。
- `coverage-review-template.md` 能承载四类结果。

## 7. 不建议立即做的事

- 不建议把 9 个专项 skill 合并成一个“大分析 skill”。它们现在的触发条件和方法边界清楚，合并会降低可路由性。
- 不建议把 `memory-context-builder` 下放给每个 skill 自行搜索 project/personal 文件。当前集中构建 context pack 的设计是正确的。
- 不建议在主交付件加入方法证据列。方法证据应留在过程报告，主交付件保持标题大纲粒度。
- 不建议把 `coverage-review` 完全拆成多个用户可见入口。它仍应作为唯一审查入口，只是内部结果分类要更清楚。

## 8. 当前结论

当前 skills 架构已经具备独立 Agent 的基本闭环：入口清楚、专项方法齐全、生成链路完整、质量门禁和脚本可运行。

最值得优先优化的是两个方向：

1. 标准化契约：补齐核心 skill 的职责边界，并统一专项分析输出骨架。
2. 独立化设计事实：把“设计方案提取”从主入口的隐式阶段沉淀为明确 schema 或独立 skill。

这两项能降低后续维护成本，也能让 `测试场景 -> 测试点 -> 测试用例标题项` 的链路更可验证。
