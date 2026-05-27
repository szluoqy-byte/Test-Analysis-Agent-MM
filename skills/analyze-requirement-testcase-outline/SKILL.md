---
name: analyze-requirement-testcase-outline
description: 当用户提供需求文档和可选设计方案文档，并要求生成“测试场景 -> 测试点 -> 测试用例标题大纲”时使用。该 skill 是主入口，负责串联上下文、需求与设计方案分析、方法路由、测试点生成、用例标题大纲生成、覆盖审查和 Markdown 产物输出；入参来自 $ARGUMENTS。
---

# 需求到测试用例标题大纲主入口

本 skill 是本独立 Agent 的完整链路入口。目标是从 `$ARGUMENTS` 指定的需求文档和可选设计方案文档中，生成 `测试用例标题大纲`。

`测试用例标题大纲` 是介于测试点和完整测试用例之间的设计产物：它给出每个测试点应派生哪些测试用例标题，并补充每个标题所需的输入条件与数据依赖、覆盖意图、判定关注和待确认信息，但不输出前置步骤、测试步骤、完整预期结果或自动化脚本。

推荐术语：

- 主交付件名称：`测试用例标题大纲`。
- 单条明细名称：`测试用例标题项`。
- 条件字段名称：`输入条件与数据依赖`，用于承载生成完整用例前必须知道的角色、状态、字段、枚举、边界、配置、依赖服务和数据准备约束。

## 必需输入

- `$ARGUMENTS`：至少包含一份 `.md` 需求文档路径。
- `$ARGUMENTS` 可额外包含一份或多份 `.md` 设计方案文档路径，或使用 `--design <path>`、`design=<path>`、`设计方案：<path>` 指定。

如果只有需求文档，继续生成大纲，并把缺失的设计方案上下文写入待确认信息或风险备注；不得编造设计方案中没有的接口、状态、字段或处理规则。

## 职责边界

- 本 skill 只负责编排完整分析链路和写出本次运行产物。
- 业务术语、项目事实和历史经验来自 `memory-context-builder` 生成的上下文包，不在本 skill 内重复维护。
- 通用测试分析理论、测试类型、测试点标准、标题大纲标准和测试设计模式来自 `knowledge/`。
- 需求与设计方案的结构化结果用于支撑测试点和标题项，不直接作为主交付件输出。
- `testpoint-generation` 负责生成场景化测试点。
- `testcase-title-outline-generation` 负责把测试点扩展为测试用例标题项。
- 主交付件是 `outputs/runs/<run-id>/deliverables/testcase-title-outline.md`；凡是后续完整用例编写必须知道的场景条件、输入条件、数据依赖、接口契约、状态、字段、边界、设计约束和未确认问题，都必须进入主交付件。

## 项目根目录与输出路径

在生成任何运行产物前，必须先固定 `PROJECT_ROOT`：

1. `PROJECT_ROOT` 等于用户启动 Claude Code、OpenCode 或当前 agent 会话所在的工作目录。
2. `$ARGUMENTS` 只用于定位输入文档；不得从输入文档路径向上反推 `PROJECT_ROOT`。
3. 如果 `$ARGUMENTS` 是相对路径，只按 `PROJECT_ROOT` 解析为绝对路径。
4. 禁止把 skill 文件所在目录、插件缓存目录、`.claude-plugin/`、`.opencode/` 或宿主内部 skill 工作目录当作 `PROJECT_ROOT`。
5. 如果当前工作目录明显是上述禁止目录，必须先向用户确认正确工作目录，不得继续生成报告。

所有运行产物必须写入 `${PROJECT_ROOT}/outputs/runs/<run-id>/` 下的固定类别目录，具体契约见 `docs/output-artifact-contract.md`。报告中可以展示相对路径 `outputs/runs/<run-id>/...`，但实际写文件时必须使用基于 `PROJECT_ROOT` 的绝对路径。

`run-id` 只在一次新的完整分析开始时生成一次。格式为 `<YYYYMMDD-HHMMSS>-<需求文件名安全短名>-<短哈希>`。同一轮分析内的后续修正、待确认问题刷新、质量门禁重跑和报告刷新，必须复用已经创建的运行目录。

## Project/Personal 上下文发现

本流程按 `core / project / personal` 三层读取配置。core 层是随 Agent 包发布的根目录文件；project 层是 `*/projects/<project-key>/**/*.md`；personal 层是 `*/user/**/*.md`，后续可扩展为 `*/user/<personal-key>/**/*.md`。

project 和 personal 是当前 run 的一等输入源，不是后续阶段随意搜索的资料目录。主入口必须让 `memory-context-builder` 统一发现、裁剪并写入 `process/context-pack.md`；后续 skill 只能消费 context pack，或按 context pack 的来源记录进行受控补读。

project/personal 层只能补充项目风险画像、覆盖策略、术语映射、测试 oracle、模板偏好、个人关注点或附加门禁，不得覆盖 core 层中的核心标准、字段、类型、级别、输出契约和质量门禁。personal 层也不得覆盖需求文档、设计方案文档或 project memory，不得作为项目事实或团队共识。

## 执行流程

1. 校验输入至少包含一份 Markdown 需求文档；识别可选设计方案文档。
2. 将当前 agent 会话工作目录固定为 `PROJECT_ROOT`，生成本次运行 ID，并创建 `${PROJECT_ROOT}/outputs/runs/<run-id>/deliverables/`、`process/` 和 `reports/`。
3. 使用 `templates/task-list-template.md` 创建 `${PROJECT_ROOT}/outputs/runs/<run-id>/process/task-list.md`，并按阶段维护状态。
4. 解析可选 `project-key` 和 `personal-key`，使用 `memory-context-builder` 扫描 core、project 和 personal 三层配置，生成 `process/context-pack.md`。
5. 使用 `clarification-gate` 执行 `CP-MEMORY`，记录 memory 冲突或项目归属缺口。
6. 使用 `requirement-testability` 分析需求文档，生成结构化需求模型，并登记需求待确认候选。
7. 如果提供设计方案文档，执行“设计方案提取”：提取架构决策、流程、接口、字段、状态机、权限、数据依赖、异常处理、配置开关、非功能指标和设计缺口；如果未提供设计方案，登记 `Q-DESIGN-*` 待确认候选。
8. 使用 `clarification-gate` 执行 `CP-REQUIREMENT-DESIGN`，合并需求与设计方案之间的冲突、缺失和歧义，不向用户提问。
9. 使用 `testing-method-router` 对需求片段和设计方案片段进行方法路由，选择适用测试方法。
10. 使用路由选中的专项分析 skill 产出 `ME-*` 方法证据、测试点候选、方法缺口候选和按源补读记录。
11. 使用 `clarification-gate` 执行 `CP-METHOD`，收口会导致测试点或标题项失真的信息缺口。
12. 使用 `testpoint-generation` 生成场景化测试点、接口测试点和场景测试条件。
13. 使用 `testcase-title-outline-generation` 基于场景、测试点、设计模式知识库和需求/设计方案上下文生成测试用例标题大纲。
14. 使用 `coverage-review` 执行覆盖审查、标题粒度检查、质量门禁和专家评分。
15. 使用 `clarification-gate` 执行 `CP-REVIEW`，刷新最终待确认信息；只保留后续完整用例编写必须知道的问题。
16. 将主输出写入 `${PROJECT_ROOT}/outputs/runs/<run-id>/deliverables/testcase-title-outline.md`，使用 `templates/testcase-title-outline-template.md`。
17. 如需保留过程审查信息，将分析报告写入 `${PROJECT_ROOT}/outputs/runs/<run-id>/reports/test-analysis-report.md`。
18. 最终输出前刷新 `process/task-list.md`：所有必选阶段必须为 `done`，未触发的可选阶段为 `skipped` 并说明原因；如果存在 `blocked`，必须在最终待确认信息或过程报告中说明。

## 阶段产物契约

| 阶段 | 必须产出 | 交给下一阶段 |
|---|---|---|
| `task-list` | `process/task-list.md` | 全流程阶段顺序与状态追踪 |
| `memory-context-builder` | `process/context-pack.md`、project/personal 来源使用摘要 | 需求与设计方案分析 |
| `requirement-testability` | 结构化需求模型、需求待确认候选 | 方法路由、测试点生成 |
| 设计方案提取 | 设计方案事实摘要、接口/状态/字段/数据依赖清单、设计缺口候选 | 方法路由、标题项输入条件 |
| `testing-method-router` | 分析维度覆盖表、方法路由表 | 专项方法 skill、测试点生成 |
| 专项方法 skill | `ME-*` 方法证据、测试点候选、方法缺口候选 | 测试点生成、标题项生成 |
| `testpoint-generation` | 场景化测试点、接口测试点、场景测试条件 | 测试用例标题大纲生成 |
| `testcase-title-outline-generation` | 测试用例标题项、输入条件与数据依赖、判定关注 | 覆盖审查 |
| `coverage-review` | 门禁结果、专家评分、阻断项和修正建议 | 主交付件和过程报告刷新 |

## 输出要求

- 主输出使用 `templates/testcase-title-outline-template.md`。
- 主输出必须包含：需求与设计方案信息、测试场景清单、测试场景详情、测试点与测试用例标题项、接口测试标题大纲、待确认信息和完整性自检。
- 主输出必须自包含：不能用“见原始需求”“见设计方案”“同上”“按需求实现”等占位替代业务规则、设计约束、接口契约、数据因子或范围边界。
- 主输出必须按 `测试场景 -> 测试点 -> 测试用例标题项` 组织；接口对象可独立按 `接口 -> 接口测试点 -> 测试用例标题项` 组织。
- 每个测试点下至少有 1 个标题项；如信息不足无法可靠生成，必须给出待确认项，并在该测试点下标记原因。
- 标题项表必须包含 `标题项 ID | 测试用例标题 | 覆盖意图 | 级别 | 输入条件与数据依赖 | 判定关注 | 待确认信息`。
- `测试用例标题` 应表达被测对象、条件/场景和验证目标，例如“验证下发订单 ID 总长度为 13 位时订单下发成功”。
- `输入条件与数据依赖` 应写清楚标题项派生完整用例时需要的条件与数据维度，例如角色、订单状态、字段长度、字段格式、依赖服务、配置开关、枚举值、边界范围或数据准备约束；不得展开成完整执行步骤。
- `判定关注` 只写观察方向或 oracle，例如接口响应、状态变化、错误码、数据记录、消息通知、日志或 UI 展示；不得写完整预期结果清单。
- 主输出不得包含操作步骤、前置步骤、有序测试步骤、完整预期结果、自动化脚本或执行数据表。
- 如果保留过程分析报告，报告可以包含方法路由、方法证据、覆盖审查、质量门禁、专家评分和 memory 更新建议；这些过程字段不得进入主交付件。

## 硬性约束

- 不生成完整测试用例。
- 不生成操作步骤。
- 不生成完整预期结果。
- 不生成自动化脚本。
- 不编造需求或设计方案中没有的业务规则、接口、字段、状态、角色、阈值或测试数据。
- 不把“回读原始需求、设计方案、过程报告或 memory”作为后续完整用例编写的前提。
- 不直接覆盖历史运行产物；所有本次运行产物必须写入同一个 `${PROJECT_ROOT}/outputs/runs/<run-id>/` 目录，并使用固定文件名。
- 不允许在 `skills/`、`.claude-plugin/`、`.opencode/`、插件缓存目录或 skill 工作目录下创建 `outputs/runs/`。
- 全流程不调用用户交互能力；多个环节只登记待确认候选，不直接向用户提问，不暂停主流程。
- 未经用户明确确认，不写入 memory 源文件。
