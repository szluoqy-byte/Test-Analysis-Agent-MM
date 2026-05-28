---
name: analyze-requirement-test-design-solution
description: 当用户提供需求文档和可选设计方案文档，并要求生成“测试场景 -> 测试点 -> 测试设计项”的测试设计方案时使用。该 skill 是主入口，负责串联上下文、需求与设计方案分析、测试技术路由、测试点生成、测试设计方案生成、独立评审和 Markdown 产物输出；入参来自 $ARGUMENTS。
---

# 需求到测试设计方案主入口

本 skill 是本独立 Agent 的完整链路入口。目标是从 `$ARGUMENTS` 指定的需求文档和可选设计方案文档中，生成 `测试设计方案`。

`测试设计方案` 是介于测试点和完整测试用例之间的设计产物：它回答“这个测试点应该用哪些代表性条件、数据、状态或组合去覆盖”。主交付件不写完整测试用例，不写前置步骤、测试步骤、自动化脚本或执行数据清单。

推荐术语：

- 主交付件名称：`测试设计方案`。
- 单条明细名称：`测试设计项`。
- 设计项 ID：`TD-001` 起全局连续编号。
- 设计项内容：代表性条件、数据、状态或组合。
- 预期结果：只能写需求或设计方案明确支持的结果；依据不足时写 `待人工分析确认`。

## 必需输入

- `$ARGUMENTS`：至少包含一份 `.md` 需求文档路径。
- `$ARGUMENTS` 可额外包含一份或多份 `.md` 设计方案文档路径，或使用 `--design <path>`、`design=<path>`、`设计方案：<path>` 指定。

如果只有需求文档，继续生成测试设计方案；不得编造设计方案中没有的接口、状态、字段、错误提示、错误码或处理规则。缺少判定依据时，在相关测试设计项的 `预期结果` 写 `待人工分析确认`。

## 职责边界

- 本 skill 只负责编排完整分析链路和写出本次运行产物。
- 业务术语、项目事实和历史经验来自 `memory-context-builder` 生成的上下文包，不在本 skill 内重复维护。
- 通用测试分析理论、测试类型、测试点标准、测试设计方案标准和测试技术来自 `knowledge/`。
- 需求与设计方案的结构化结果用于支撑测试点和测试设计项，不直接作为主交付件输出。
- `requirement-testability` 负责需求模型和可测性判断。
- `design-solution-extraction` 负责设计方案事实摘要和设计缺口候选。
- `clarification-gate` 负责过程级缺口治理；它不向主交付件写待确认章节。
- `testpoint-generation` 负责生成场景化测试点。
- `test-design-solution-generation` 负责把测试点扩展为测试设计项和预期结果。
- `test-design-solution-review` 负责作为独立评审 Agent 检查主交付件质量。
- 主交付件是 `outputs/runs/<run-id>/deliverables/test-design-solution.md`。

## 项目根目录与输出路径

在生成任何运行产物前，必须先固定 `PROJECT_ROOT`：

1. `PROJECT_ROOT` 等于用户启动 Claude Code、OpenCode 或当前 agent 会话所在的工作目录。
2. `$ARGUMENTS` 只用于定位输入文档；不得从输入文档路径向上反推 `PROJECT_ROOT`。
3. 如果 `$ARGUMENTS` 是相对路径，只按 `PROJECT_ROOT` 解析为绝对路径。
4. 禁止把 skill 文件所在目录、插件缓存目录、`.claude-plugin/`、`.opencode/` 或宿主内部 skill 工作目录当作 `PROJECT_ROOT`。
5. 如果当前工作目录明显是上述禁止目录，必须先向用户确认正确工作目录，不得继续生成报告。

所有运行产物必须写入 `${PROJECT_ROOT}/outputs/runs/<run-id>/` 下的固定类别目录，具体契约见 `docs/output-artifact-contract.md`。报告中可以展示相对路径 `outputs/runs/<run-id>/...`，但实际写文件时必须使用基于 `PROJECT_ROOT` 的绝对路径。

`run-id` 只在一次新的完整分析开始时生成一次。格式为 `<YYYYMMDD-HHMMSS>-<需求文件名安全短名>-<短哈希>`。同一轮分析内的后续修正、质量门禁重跑和报告刷新，必须复用已经创建的运行目录。

## Project/Personal 上下文发现

本流程按 `core / project / personal` 三层读取配置。core 层是随 Agent 包发布的根目录文件；project 层是 `*/projects/<project-key>/**/*.md`；personal 层是 `*/user/**/*.md`，后续可扩展为 `*/user/<personal-key>/**/*.md`。

project 和 personal 是当前 run 的一等输入源，不是后续阶段随意搜索的资料目录。主入口必须让 `memory-context-builder` 统一发现、裁剪并写入 `process/context-pack.md`；后续 skill 只能消费 context pack，或按 context pack 的来源记录进行受控补读。

project/personal 层只能补充项目风险画像、覆盖策略、术语映射、测试 oracle、模板偏好、个人关注点或附加门禁，不得覆盖 core 层中的核心标准、字段、输出契约和质量门禁。personal 层也不得覆盖需求文档、设计方案文档或 project memory，不得作为项目事实或团队共识。

## 执行流程

1. 校验输入至少包含一份 Markdown 需求文档；识别可选设计方案文档。
2. 将当前 agent 会话工作目录固定为 `PROJECT_ROOT`，生成本次运行 ID，并创建 `${PROJECT_ROOT}/outputs/runs/<run-id>/deliverables/`、`process/` 和 `reports/`。
3. 使用 `templates/task-list-template.md` 创建 `${PROJECT_ROOT}/outputs/runs/<run-id>/process/task-list.md`，并按阶段维护状态。
4. 解析可选 `project-key` 和 `personal-key`，使用 `memory-context-builder` 扫描 core、project 和 personal 三层配置，生成 `process/context-pack.md`。
5. 使用 `requirement-testability` 分析需求文档，生成结构化需求模型，并登记需求待确认候选。
6. 如果提供设计方案文档，使用 `design-solution-extraction` 提取架构决策、流程、接口、字段、状态机、权限、数据依赖、异常处理、配置开关、非功能指标和设计缺口；如果未提供设计方案，登记 `Q-DESIGN-*` 过程候选。
7. 使用 `clarification-gate` 执行 `CP-INPUT`，合并 memory、需求与设计方案之间的冲突、缺失和歧义，不向用户提问。
8. 使用 `testing-method-router` 对需求片段和设计方案片段进行测试技术路由，选择适用测试技术和专项分析 skill。
9. 使用路由选中的专项分析 skill 产出 `ME-*` 方法证据、测试点候选、技术缺口候选和按源补读记录。
10. 使用 `clarification-gate` 执行 `CP-ANALYSIS`，收口会导致测试点、方法覆盖或预期结果失真的信息缺口。
11. 使用 `testpoint-generation` 生成场景化测试点、接口测试点和场景测试条件。
12. 使用 `test-design-solution-generation` 基于场景、测试点、测试技术库和需求/设计方案上下文生成测试设计方案。
13. 使用 `test-design-solution-review` 独立评审测试设计方案，重点检查设计项粒度、预期结果依据和非完整用例化。
14. 使用 `coverage-review` 执行覆盖审查、质量门禁和确定性校验。
15. 将主输出写入 `${PROJECT_ROOT}/outputs/runs/<run-id>/deliverables/test-design-solution.md`，使用 `templates/test-design-solution-template.md`。
16. 如需保留过程审查信息，将分析报告写入 `${PROJECT_ROOT}/outputs/runs/<run-id>/reports/test-analysis-report.md`。
17. 最终输出前刷新 `process/task-list.md`：所有必选阶段必须为 `done`，未触发的可选阶段为 `skipped` 并说明原因；如果存在 `blocked`，必须在过程报告中说明。

## 阶段产物契约

| 阶段 | 必须产出 | 交给下一阶段 |
|---|---|---|
| `task-list` | `process/task-list.md` | 全流程阶段顺序与状态追踪 |
| `memory-context-builder` | `process/context-pack.md`、project/personal 来源使用摘要 | 需求与设计方案分析 |
| `requirement-testability` | 结构化需求模型、需求待确认候选 | 测试技术路由、测试点生成 |
| `design-solution-extraction` | 设计方案事实摘要、接口/状态/字段/数据依赖清单、设计缺口候选 | 测试技术路由、设计项输入 |
| `clarification-gate` | `process/clarification-session.md` | 过程缺口治理、预期结果兜底依据 |
| `testing-method-router` | 分析维度覆盖表、测试技术路由表 | 专项分析 skill、测试点生成 |
| 专项分析 skill | `ME-*` 方法证据、测试点候选、技术缺口候选 | 测试点生成、测试设计项生成 |
| `testpoint-generation` | 场景化测试点、接口测试点、场景测试条件 | 测试设计方案生成 |
| `test-design-solution-generation` | 测试设计项、预期结果 | 独立评审和覆盖审查 |
| `test-design-solution-review` | 独立评审结论、修正建议 | 覆盖审查与输出收口 |
| `coverage-review` | 门禁结果、专家评分、阻断项和修正建议 | 主交付件和过程报告刷新 |

## 输出要求

- 主输出使用 `templates/test-design-solution-template.md`。
- 主输出只包含测试设计方案所需内容，不设置 `未明确规则` 章节，不设置独立待确认信息清单。
- 主输出必须包含 `## 1. 需求范围` 和 `## 2. 测试场景与测试设计`。
- 主输出必须按 `测试场景 -> 测试点 -> 测试设计项` 组织；接口对象可作为测试场景或测试点呈现，不另建接口专用大纲。
- 每个测试点下至少有 1 个测试设计项；设计项表必须使用 `测试设计项 ID | 测试设计项 | 预期结果`。
- `测试设计项` 只写代表性条件、数据、状态或组合，例如“下发订单 ID 总长度为 13 位”“订单已支付状态下重复提交取消请求”。
- `预期结果` 只能来自需求、设计方案、context pack 中明确事实或可直接推出的业务不变量。
- 如果需求和设计方案没有明确错误提示、状态变化、错误码、返回内容、数据记录变化或其他判定依据，`预期结果` 写 `待人工分析确认`。
- 主输出不得包含 `覆盖意图`、`级别`、`待确认信息`、`判定关注`、`输入条件与数据依赖` 等旧字段。
- 主输出不得包含操作步骤、前置步骤、有序测试步骤、自动化脚本、接口调用代码或执行数据表。
- 如果保留过程分析报告，报告可以包含测试技术路由、方法证据、覆盖审查、质量门禁、独立评审和 memory 更新建议；这些过程字段不得进入主交付件。

## 硬性约束

- 不生成完整测试用例。
- 不生成操作步骤。
- 不生成自动化脚本。
- 不编造需求或设计方案中没有的业务规则、接口、字段、状态、角色、阈值、错误提示、错误码或测试数据。
- 不把“回读原始需求、设计方案、过程报告或 memory”作为后续理解测试设计方案的前提。
- 不直接覆盖历史运行产物；所有本次运行产物必须写入同一个 `${PROJECT_ROOT}/outputs/runs/<run-id>/` 目录，并使用固定文件名。
- 不允许在 `skills/`、`.claude-plugin/`、`.opencode/`、插件缓存目录或 skill 工作目录下创建 `outputs/runs/`。
- 全流程不调用用户交互能力；多个环节只登记过程候选，不直接向用户提问，不暂停主流程。
- 未经用户明确确认，不写入 memory 源文件。
