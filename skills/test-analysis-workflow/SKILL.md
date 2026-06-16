---
name: test-analysis-workflow
description: 当用户提供需求文档和可选设计方案文档，并要求生成“测试场景 -> 测试点 -> 测试点明细”的测试分析方案时使用；非成功测试点明细需要继续拆分失败类型明细。该 skill 是主入口，负责编排上下文、需求与设计方案分析、测试技术路由、测试分析方案 JSON 生成、独立评审和 Markdown 渲染；入参来自 $ARGUMENTS。
---

# 需求到测试分析方案主入口

本 skill 是 `test-analysis-agent` 的完整链路入口。目标是从 `$ARGUMENTS` 指定的需求文档和可选设计方案文档中，生成 `测试分析方案`。

`测试分析方案` 回答 what to test：输出测试场景、测试点和测试点明细；当 `TP-*-*` 是非成功测试点明细时，继续输出失败类型明细，并给出需求或设计方案可支撑的简短预期结果。它不输出 `TDI-*` 测试设计项，不选择具体代表性条件/数据/状态/组合，不写完整测试用例、前置步骤、测试步骤、自动化脚本或执行数据清单。

推荐术语：

- 主交付件名称：`测试分析方案`。
- 单条明细名称：`测试点明细`。
- 固定缩写：测试场景 `SC-*`、测试点 `TP-*`、测试点明细 `TP-*-*`、失败类型明细 `TP-*-*-*`；主交付件不展开英文全名。
- 测试点明细 ID：继承测试点 ID，例如 `TP-001-001`。
- 失败类型明细 ID：继承测试点明细 ID，例如 `TP-001-002-001`，仅非成功测试点明细需要。
- 预期结果：只能写需求或设计方案明确支持的结果；依据不足时写 `待人工分析确认`。
- `TDI-*` 和 `测试设计项` 留给 `test-design-agent`，当前主交付件禁止输出。

## 必需输入

- `$ARGUMENTS`：至少包含一份 `.md` 或 `.markdown` 需求文档路径。
- `$ARGUMENTS` 可额外包含一份或多份 `.md` 或 `.markdown` 设计方案文档路径，或使用 `--design <path>`、`design=<path>`、`设计方案：<path>` 指定。
- 如果输入包含 `.docx` 或 `.xlsx`，不得在本 workflow 中转换；必须先由 `@file-normalization-agent` 归一化为 Markdown，再把归一化 Markdown 路径作为本 workflow 输入。
- 可选项目绑定参数：`--project <project-key>`、`project=<project-key>` 或 `项目：<project-key>`。如果出现该参数，必须原样传递给 `memory-context-builder`，并要求 `process/context-pack.json` 记录 project-key、已扫描 project 来源、未采用 project 来源和项目知识阶段绑定。
- 可选个人绑定参数：`--personal <personal-key>`、`personal=<personal-key>` 或 `个人：<personal-key>`。如果出现该参数，必须原样传递给 `memory-context-builder`，并要求 `process/context-pack.json` 记录 personal-key、使用路径和 personal 来源使用摘要。

如果只有需求文档，继续生成测试分析方案；不得编造设计方案中没有的接口、状态、字段、错误提示、错误码或处理规则。缺少判定依据时，在相关测试点明细的 `预期结果` 写 `待人工分析确认`。

## 职责边界

- 本 skill 只负责编排完整分析链路和写出本次运行产物。
- 强制规则、业务术语、项目事实和历史经验来自 `memory-context-builder` 生成的上下文包，不在本 skill 内重复维护。
- 适用 rules 的优先级低于当前用户明确指令，但高于需求文档、设计方案、memory 和 knowledge；与输入冲突时遵守 rules 并记录覆盖原因。
- 通用测试分析理论、测试类型、测试点标准、测试分析方案标准和测试技术来自 `knowledge/`。
- 需求与设计方案的结构化结果用于支撑测试场景、测试点和测试点明细，不直接作为主交付件输出。
- `input-fact-modeling` 负责建立统一输入事实模型，覆盖需求事实、可选设计事实、需求-设计映射、缺口冲突和待确认事项。
- `clarification-gate` 负责过程级缺口治理；它不向主交付件写待确认章节。
- `test-analysis-solution-generation` 负责生成测试场景、测试点、测试点明细、失败类型明细和预期结果。
- `test-analysis-solution-review` 负责在确定性 lint 通过后检查主交付件语义质量，不重复结构、编号、字段和 Markdown 语法检查。
- `coverage-review` 负责覆盖、追踪、方法应用、rules/project knowledge 应用和过程一致性收口，不重复 lint 已覆盖的确定性规则。
- 主交付件事实源是 `outputs/runs/<run-id>/deliverables/test-analysis-solution.json`；人读版 `test-analysis-solution.md` 必须由 `bin/render-run-markdown.py` 生成。
- 本流程中 process、deliverables、review 和 coverage 的可编辑事实源均为 JSON；Markdown 只作为派生阅读版。

## 项目根目录与输出路径

在生成任何运行产物前，必须先固定 `PROJECT_ROOT`：

1. `PROJECT_ROOT` 等于用户启动 Claude Code、OpenCode 或当前 agent 会话所在的工作目录。
2. `$ARGUMENTS` 只用于定位输入文档；不得从输入文档路径向上反推 `PROJECT_ROOT`。
3. 如果 `$ARGUMENTS` 是相对路径，只按 `PROJECT_ROOT` 解析为绝对路径。
4. 禁止把 skill 文件所在目录、插件缓存目录、`.claude-plugin/`、`.opencode/` 或宿主内部 skill 工作目录当作 `PROJECT_ROOT`。
5. 如果当前工作目录明显是上述禁止目录，必须先向用户确认正确工作目录，不得继续生成报告。

所有运行产物必须写入 `${PROJECT_ROOT}/outputs/runs/<run-id>/` 下的固定类别目录，具体契约见 `docs/output-artifact-contract.md`。报告中可以展示相对路径 `outputs/runs/<run-id>/...`，但实际写文件时必须使用基于 `PROJECT_ROOT` 的绝对路径。

`run-id` 只在一次新的完整分析开始时生成一次，固定使用 `python bin/generate-run-id.py` 生成。格式为 `<YYYYMMDD-HHMMSS>`。同一轮分析内的后续修正、质量门禁重跑和报告刷新，必须复用已经创建的运行目录。

## Project/Personal 上下文发现

本流程按 `core / project / personal` 三层读取配置。core 层是随 Agent 包发布的根目录文件；project 层是 `*/projects/<project-key>/**/*.md`；personal 层是 `*/user/**/*.md`，后续可扩展为 `*/user/<personal-key>/**/*.md`。

`rules/` 是强制规则源：core rules 为 `rules/*.md`，project rules 为 `rules/projects/<project-key>/**/*.md`，personal rules 为 `rules/user/**/*.md`。rules 进入 `process/context-pack.json` 的“适用强制规则”结构，并渲染到 `process/context-pack.md`，在后续阶段强制应用或解释不适用。

project 和 personal 是当前 run 的一等输入源，不是后续阶段随意搜索的资料目录。主入口必须让 `memory-context-builder` 统一发现、裁剪并写入 `process/context-pack.json`；后续 skill 只能消费 context pack，或按 context pack 的来源记录进行受控补读。

project/personal 层只能补充项目风险画像、覆盖策略、术语映射、测试 oracle、个人关注点或附加门禁，不得覆盖 core 层中的核心标准、字段、输出契约和质量门禁。personal 层也不得覆盖需求文档、设计方案文档或 project memory，不得作为项目事实或团队共识。

project knowledge 文件名没有硬性要求；如果 `knowledge/projects/<project-key>/` 下存在自由格式 Markdown，`memory-context-builder` 必须基于文件名、frontmatter、标题、章节和摘要自理解识别文件用途，并在 `context-pack.json` 生成“项目知识阶段绑定”。主流程后续阶段必须遵守该绑定：被绑定到某个阶段的文件，在该阶段开始前必须读取相关章节，并输出应用状态。context-pack 阶段不提前判断具体测试点或测试点明细命中。

## 执行流程

1. 校验输入至少包含一份 Markdown 需求文档；识别可选 Markdown 设计方案文档。若发现 `.docx` 或 `.xlsx` 输入，输出需先使用 `@file-normalization-agent` 的阻断说明，不创建测试分析 run。
2. 将当前 agent 会话工作目录固定为 `PROJECT_ROOT`，运行 `python bin/generate-run-id.py` 生成本次运行 ID，并创建 `${PROJECT_ROOT}/outputs/runs/<run-id>/deliverables/`、`process/`、`reports/` 和 `inputs/`。
3. 使用 `templates/process-artifacts-json-template.json` 创建 `${PROJECT_ROOT}/outputs/runs/<run-id>/process/task-list.json`，并按阶段维护状态；需要人读版时由渲染脚本生成 `process/task-list.md`。
4. 解析可选 `project-key` 和 `personal-key`，使用 `memory-context-builder` 扫描 core、project 和 personal 三层配置，生成 `process/context-pack.json`，登记适用 rules、Rules 与输入冲突记录和 project knowledge 阶段绑定。
5. 使用 `input-fact-modeling` 读取需求文档和可选设计方案文档，生成 `${PROJECT_ROOT}/outputs/runs/<run-id>/process/input-fact-model.json`，其中包含事实清单、需求-设计映射、待确认事项和来源应用说明；如果未提供设计方案，在事实模型中记录未提供设计依据，而不是单独跳过设计提取阶段。
6. 使用 `clarification-gate` 执行 `CP-INPUT`，合并 memory、需求与设计方案之间的冲突、缺失和歧义，不向用户提问。
7. 使用 `testing-method-router` 对输入事实模型中的需求事实、设计事实和待确认事项进行测试技术路由，选择适用测试技术和专项方法参考；如果 context pack 绑定了本阶段 project knowledge，必须先读取并记录应用状态。
8. 使用路由选中的专项方法参考产出 `ME-*` 方法证据、测试点候选、技术缺口候选和按源补读记录。
9. 使用 `clarification-gate` 执行 `CP-ANALYSIS`，收口会导致测试点、方法覆盖或预期结果失真的信息缺口；如果没有任何候选，也必须刷新 `process/clarification-session.json` 并声明 `无待确认候选`。
10. 使用 `test-analysis-solution-generation` 基于输入事实模型、测试技术路由、专项方法参考、方法证据和项目知识生成并写入 `${PROJECT_ROOT}/outputs/runs/<run-id>/deliverables/test-analysis-solution.json`；如果 context pack 绑定了本阶段 project knowledge，必须先读取并记录应用状态。
11. 执行确定性 JSON 校验：运行 `bin/lint-run-json.py ${PROJECT_ROOT}/outputs/runs/<run-id>`。如果失败，先按脚本失败项修正 JSON，不进入独立评审和覆盖审查。
12. 执行 Markdown 渲染和派生 Markdown 校验：运行 `bin/render-run-markdown.py ${PROJECT_ROOT}/outputs/runs/<run-id>`，再运行 `bin/lint-test-analysis-solution.py ${PROJECT_ROOT}/outputs/runs/<run-id>/deliverables/test-analysis-solution.md`。如果失败，修正 JSON 后重新渲染，不手工改 Markdown。
13. 使用 `test-analysis-solution-review` 独立语义评审测试分析方案 JSON，重点检查测试点明细粒度、失败类型拆分充分性、预期结果依据、事实溯源、非用例化语义和本阶段绑定的 project review knowledge；不得重复执行 lint 已覆盖的结构、编号、字段和 Markdown 语法检查。评审结果写入 `reports/test-analysis-solution-review.json`。
14. 使用 `coverage-review` 执行覆盖、追踪、方法应用、rules 应用、project knowledge 应用和过程门禁收口；如果 context pack 绑定了本阶段 project knowledge，必须读取并检查前序阶段应用状态。专家评分和深度语义检查仅在用户明确要求或高风险场景下执行。覆盖结果写入 `reports/coverage-review.json`。
15. 不再新建自由格式过程分析 Markdown 作为机器证据；测试技术路由、专项分析、review 和 coverage 的机器可读结论应沉淀到 `process/*.json`、`deliverables/test-analysis-solution.json`、`reports/test-analysis-solution-review.json` 或 `reports/coverage-review.json`。迁移旧 run 时才允许保留 `reports/test-analysis-report.md` 作为兼容性人读证据。
16. 最终输出前刷新 `process/task-list.json`：所有必选阶段必须为 `done`，未触发的可选阶段为 `skipped` 并说明原因；运行 `bin/render-run-markdown.py ${PROJECT_ROOT}/outputs/runs/<run-id>` 生成派生 Markdown；运行 `bin/check-artifact-consistency.py ${PROJECT_ROOT}/outputs/runs/<run-id>` 做最终一致性检查；如果存在 `blocked`，必须在 `process/task-list.json`、`process/clarification-session.json` 或 review/coverage JSON 中说明。

## 阶段产物契约

| 阶段 | 必须产出 | 交给下一阶段 |
|---|---|---|
| `task-list` | `process/task-list.json`、派生 `process/task-list.md` | 全流程阶段顺序与状态追踪 |
| `memory-context-builder` | `process/context-pack.json`、适用强制规则、Rules 与输入冲突记录、project/personal 来源使用摘要、项目知识阶段绑定 | 需求与设计方案分析 |
| `input-fact-modeling` | `process/input-fact-model.json`、事实清单、需求-设计映射、待确认事项、来源应用说明 | 待确认治理、测试技术路由、测试分析方案生成 |
| `clarification-gate` | `process/clarification-session.json` | 固定 process 产物；记录过程缺口治理、预期结果兜底依据；无候选时声明 `无待确认候选` |
| `testing-method-router` | 分析维度覆盖表、测试技术路由表 | 专项方法参考、测试分析方案生成 |
| 专项方法参考 | `ME-*` 方法证据、测试点候选、技术缺口候选 | 测试分析方案生成 |
| `test-analysis-solution-generation` | `deliverables/test-analysis-solution.json`、测试场景、测试点、测试点明细、失败类型明细、预期结果 | JSON 校验 |
| 确定性校验 | `lint-run-json.py`、`render-run-markdown.py --check`、`lint-test-analysis-solution.py` 结果 | 独立语义评审；失败时回到 JSON 修正 |
| `test-analysis-solution-review` | `reports/test-analysis-solution-review.json` | 覆盖审查与输出收口 |
| `coverage-review` | `reports/coverage-review.json` | 主交付件、结构化过程记录和覆盖结论收口 |

## Project Knowledge 应用留痕

如果 `process/context-pack.json` 的“项目知识阶段绑定”中存在绑定到当前阶段的 project knowledge，当前阶段必须输出应用记录：

| 来源文件 | 当前阶段 | 应用状态 | 应用位置 | 说明 |
|---|---|---|---|---|

应用状态只能使用 `applied`、`not_applicable`、`insufficient_evidence`、`conflict_with_requirement` 或 `deferred_to_review`。覆盖审查必须检查所有已绑定文件是否被对应阶段读取并留痕；未读取或无状态说明时，按质量问题处理。

## 输出要求

- 主输出使用 `templates/test-analysis-solution-json-template.json` 生成 JSON；`templates/test-analysis-solution-template.md` 仅作为渲染后 Markdown 样式参考。
- 主输出只包含测试分析方案所需内容，不设置 `未明确规则` 章节，不设置独立待确认信息清单。
- 渲染后的 Markdown 必须包含 `## 1. 需求范围` 和 `## 2. 测试场景与测试点`。
- 主输出必须按 `测试场景 -> 测试点 -> 测试点明细` 组织；非成功测试点明细按 `测试场景 -> 测试点 -> 测试点明细 -> 失败类型明细` 组织；接口契约不使用接口专用编号体系。若当前任务或输入明确要求接口测试/API 契约覆盖，接口测试或集成覆盖场景下必须先按接口、端点、消息、回调或集成点组织同级 `TP-*`，再拆契约维度。
- 主输出只使用中文术语和固定缩写 `SC`、`TP`、`TP-*-*`、`TP-*-*-*`，不得使用 `TDI-*`、`TD-*`、`TC-*`、`TCT-*`、`TI-*`、`ITP-*` 或 `ITDI-*`。
- 每个测试场景下必须包含一个 `E2E场景测试` 测试点。
- 每个测试点下至少有 1 个测试点明细。
- 普通测试点明细必须包含 `description` 和 `expectedResult`；明确非成功聚合测试点明细必须新增 `TP-*-*-*` 失败类型明细，并由第四层承载 `description` 和 `expectedResult`。
- 是否新增第四层由 `TP-*-*` 测试点明细决定，不由 `TP-*` 测试点主题决定；“未找到返回空结果”“列表为空”“count=0”等单一弱结果分支不强制新增第四层。
- `测试点明细` 只写规则分支、路径分支、状态分支、权限分支、接口契约分支或风险分支，例如“下发订单 ID 满足长度要求”“下发订单 ID 不满足长度要求”。
- 主输出不得把测试点明细拆成具体代表性条件、数据、状态或组合，例如不要输出“订单 ID 长度等于 13 位”“订单 ID 长度小于 13 位”；这些留给 `test-design-agent`。
- `预期结果` 只能来自当前用户明确指令、适用 rules、需求、设计方案、context pack 中明确事实或可直接推出的业务不变量。
- 如果需求和设计方案没有明确错误提示、状态变化、错误码、返回内容、数据记录变化或其他判定依据，`预期结果` 写 `待人工分析确认`。
- 主输出不得包含 `覆盖意图`、`级别`、`待确认信息`、`判定关注`、`输入条件与数据依赖` 等旧字段。
- 主输出不得使用 Markdown 加粗语法，例如 `**文本**` 或 `__文本__`。
- 主输出不得包含操作步骤、前置步骤、有序测试步骤、自动化脚本、接口调用代码或执行数据表。
- 测试技术路由、方法证据、覆盖审查、质量门禁、独立评审和 memory 更新建议优先写入结构化过程 JSON 或 review/coverage JSON；这些过程字段不得进入主交付件正文。

## 硬性约束

- 不生成完整测试用例。
- 不生成操作步骤。
- 不生成自动化脚本。
- 不生成 `TDI-*` 或测试设计项。
- 不编造当前用户明确指令、适用 rules、需求或设计方案中没有的业务规则、接口、字段、状态、角色、阈值、错误提示、错误码或测试数据。
- 不把“回读原始需求、设计方案、结构化过程记录或 memory”作为后续理解测试分析方案的前提。
- 不直接覆盖历史运行产物；所有本次运行产物必须写入同一个 `${PROJECT_ROOT}/outputs/runs/<run-id>/` 目录，并使用固定文件名。
- 不允许在 `skills/`、`.claude-plugin/`、`.opencode/`、插件缓存目录或 skill 工作目录下创建 `outputs/runs/`。
- 全流程不调用用户交互能力；多个环节只登记过程候选，不直接向用户提问，不暂停主流程。
- 未经用户明确确认，不写入 memory 源文件。
