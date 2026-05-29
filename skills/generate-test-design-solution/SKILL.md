---
name: generate-test-design-solution
description: 当用户提供已评审测试分析方案，或要求从需求先生成分析方案再扩展设计项时使用。该 skill 是 test-design-agent 主入口，负责编排测试分析方案校验、需求/设计依据补读、测试设计项生成、独立评审和 Markdown 产物输出；入参来自 $ARGUMENTS。
---

# 测试分析方案到测试设计方案主入口

本 skill 是 `test-design-agent` 的完整链路入口。目标是从 `$ARGUMENTS` 指定的已评审 `测试分析方案` 出发，生成 `测试设计方案`。

`测试设计方案` 回答 how to test：在既有 `测试场景 -> 测试点 -> 测试点明细` 层级下，为普通测试点明细补充 `TDI-*` 测试设计项；如果分析方案中存在非成功测试点明细的 `TP-*-*-*` 第四层，则在失败类型明细下补充 `TDI-*`。测试设计项只表达代表性条件、数据、状态或组合，并给出需求或设计方案可支撑的简短预期结果。

推荐术语：

- 主交付件名称：`测试设计方案`。
- 单条设计项名称：`测试设计项`。
- 固定缩写：测试场景 `SC-*`、测试点 `TP-*`、测试点明细 `TP-*-*`、失败类型明细 `TP-*-*-*`、测试设计项 `TDI-*`；主交付件不展开英文全名。
- 设计项 ID：`TDI-001` 起全局连续编号。
- 设计项内容：代表性条件、数据、状态或组合。
- 预期结果：只能写需求或设计方案明确支持的结果；依据不足时写 `待人工分析确认`。

## 必需输入

优先输入：

- `$ARGUMENTS`：一份 `test-analysis-solution.md` 或其他已评审测试分析方案 Markdown 路径。
- 可选：原始需求文档路径、设计方案文档路径、`--requirement <path>`、`--design <path>`、`requirement=<path>`、`design=<path>`、`project=<project-key>` 或 `personal=<personal-key>`。

兼容输入：

- 如果用户只提供需求文档和可选设计方案文档，并明确要求生成测试设计方案，本 skill 必须先使用 `analyze-requirement-test-analysis-solution` 生成 `deliverables/test-analysis-solution.md`，再以该分析方案作为设计输入继续执行。
- 如果用户提供的分析方案未通过 `bin/lint-test-analysis-solution.py`，不得静默设计；先记录为输入质量问题，按需回到分析流程修正。

## 职责边界

- 本 skill 只负责编排设计链路和写出测试设计方案。
- 测试分析层事实来自已评审测试分析方案；不得把设计阶段发现的新范围直接写成新的 `SC-*`、`TP-*`、`TP-*-*` 或 `TP-*-*-*`。
- 需求与设计方案只用于校验和补强测试设计项依据；不得覆盖分析方案中的已评审层级。
- 适用 rules 的优先级低于当前用户明确指令，但高于测试分析方案、需求文档、设计方案、memory 和 knowledge；与输入冲突时遵守 rules 并记录覆盖原因。
- 通用测试分析/设计边界、测试设计方案标准和测试技术来自 `knowledge/`。
- `test-design-solution-generation` 负责把普通测试点明细或失败类型明细扩展为测试设计项和预期结果。
- `test-design-solution-review` 负责独立评审设计项粒度、预期结果依据和非完整用例化。
- 主交付件是 `outputs/runs/<run-id>/deliverables/test-design-solution.md`。

## 项目根目录与输出路径

在生成任何运行产物前，必须先固定 `PROJECT_ROOT`：

1. `PROJECT_ROOT` 等于用户启动 Claude Code、OpenCode 或当前 agent 会话所在的工作目录。
2. `$ARGUMENTS` 只用于定位输入文档；不得从输入文档路径向上反推 `PROJECT_ROOT`。
3. 如果 `$ARGUMENTS` 是相对路径，只按 `PROJECT_ROOT` 解析为绝对路径。
4. 禁止把 skill 文件所在目录、插件缓存目录、`.claude-plugin/`、`.opencode/` 或宿主内部 skill 工作目录当作 `PROJECT_ROOT`。
5. 如果当前工作目录明显是上述禁止目录，必须先向用户确认正确工作目录，不得继续生成报告。

如果输入分析方案位于 `${PROJECT_ROOT}/outputs/runs/<run-id>/deliverables/test-analysis-solution.md`，优先复用该 `<run-id>`，把设计交付件写入同一个 run 目录。否则使用 `python bin/generate-run-id.py` 生成新的 `<run-id>`，格式为 `<YYYYMMDD-HHMMSS>`，并在 `process/task-list.md` 中记录外部分析方案来源。

## Project/Personal 上下文发现

如果当前 run 已存在 `process/context-pack.md`，优先复用并检查其中的适用强制规则、Rules 与输入冲突记录和项目知识阶段绑定。若不存在，则使用 `memory-context-builder` 生成 context pack。

`rules/` 是强制规则源：core rules 为 `rules/*.md`，project rules 为 `rules/projects/<project-key>/**/*.md`，personal rules 为 `rules/user/**/*.md`。rules 必须进入 `process/context-pack.md` 的“适用强制规则”表，并在设计生成、评审或覆盖审查阶段应用或解释不适用。

project knowledge 文件名没有硬性要求；如果 `knowledge/projects/<project-key>/` 下存在自由格式 Markdown，`memory-context-builder` 必须基于文件名、frontmatter、标题、章节和摘要自理解识别文件用途，并在 `context-pack.md` 生成“项目知识阶段绑定”。被绑定到 `test-design-solution-generation`、`test-design-solution-review` 或 `coverage-review` 的文件必须在对应阶段读取并输出应用状态。

## 执行流程

1. 校验输入：识别测试分析方案、需求文档和可选设计方案文档。
2. 如果没有测试分析方案，先调用 `analyze-requirement-test-analysis-solution` 生成分析方案，并以其输出作为后续输入。
3. 固定 `PROJECT_ROOT` 和 `<run-id>`；需要新建 run 时先运行 `python bin/generate-run-id.py`，再创建或复用 `${PROJECT_ROOT}/outputs/runs/<run-id>/deliverables/`、`process/` 和 `reports/`。
4. 创建或刷新 `process/task-list.md`，记录当前进入测试设计阶段。
5. 读取并校验 `deliverables/test-analysis-solution.md`；若文件存在，运行 `bin/lint-test-analysis-solution.py`。
6. 读取或生成 `process/context-pack.md`，确认适用 rules、Rules 与输入冲突记录、project/personal 来源和项目知识阶段绑定。
7. 受控补读原始需求文档、设计方案文档、`design-facts` 或过程报告中与当前分析方案相关的依据；不得要求后续读者回看这些文件才能理解主交付件。
8. 使用 `test-design-solution-generation` 在普通 `TP-*-*` 或失败类型 `TP-*-*-*` 下生成 1-N 个 `TDI-*`，并记录项目知识应用状态。
9. 使用 `test-design-solution-review` 独立评审测试设计方案，重点检查分析方案承接、失败类型明细继承、设计项粒度、预期结果依据、旧字段泄漏和非完整用例化。
10. 使用 `coverage-review` 或设计级覆盖审查记录检查需求覆盖、分析方案承接关系、项目知识应用状态和确定性校验。
11. 将主输出写入 `${PROJECT_ROOT}/outputs/runs/<run-id>/deliverables/test-design-solution.md`，使用 `templates/test-design-solution-template.md`。
12. 如需保留过程审查信息，使用 `templates/test-design-report-template.md` 将设计报告写入 `${PROJECT_ROOT}/outputs/runs/<run-id>/reports/test-design-report.md`。
13. 最终输出前刷新 `process/task-list.md`：设计阶段必选项必须为 `done`，未触发的可选项为 `skipped` 并说明原因。

## 阶段产物契约

| 阶段 | 必须产出 | 交给下一阶段 |
|---|---|---|
| `analysis-solution-check` | 已校验测试分析方案、承接关系检查 | 测试设计项生成 |
| `memory-context-builder` | `process/context-pack.md` 或复用记录、适用强制规则、Rules 与输入冲突记录、项目知识阶段绑定 | 测试设计项生成和评审 |
| `test-design-solution-generation` | `TDI-*` 测试设计项、设计级预期结果、项目知识应用状态 | 独立评审 |
| `test-design-solution-review` | 独立评审结论、修正建议 | 覆盖审查与输出收口 |
| `coverage-review` | 门禁结果、阻断项和修正建议 | 主交付件和过程报告刷新 |

## 输出要求

- 主输出使用 `templates/test-design-solution-template.md`。
- 主输出只包含测试设计方案所需内容，不设置 `未明确规则` 章节，不设置独立待确认信息清单。
- 主输出必须包含 `## 1. 设计输入` 和 `## 2. 测试场景与测试设计`。
- 主输出必须保留普通分支 `测试场景 -> 测试点 -> 测试点明细 -> 测试设计项` 层级；非成功分支必须保留 `测试场景 -> 测试点 -> 测试点明细 -> 失败类型明细 -> 测试设计项` 层级。
- 主输出只使用中文术语和固定缩写 `SC`、`TP`、`TP-*-*`、`TP-*-*-*`、`TDI`，不得使用 `TD-*`、`TC-*`、`TCT-*`、`TI-*`、`ITP-*` 或 `ITDI-*`。
- 每个普通测试点明细或失败类型明细下至少有 1 个测试设计项；设计项表必须使用 `测试设计项 ID | 条件/数据/状态/组合 | 预期结果`。
- `条件/数据/状态/组合` 只写代表性条件、数据、状态或组合，例如“订单 ID 总长度等于 13 位”“订单已支付状态下重复提交取消请求”。
- `预期结果` 只能来自当前用户明确指令、适用 rules、需求、设计方案、测试分析方案、context pack 中明确事实或可直接推出的业务不变量。
- 如果需求和设计方案没有明确错误提示、状态变化、错误码、返回内容、数据记录变化或其他判定依据，`预期结果` 写 `待人工分析确认`。
- 主输出不得包含 `覆盖意图`、`级别`、`待确认信息`、`判定关注`、`输入条件与数据依赖` 等旧字段。
- 主输出不得包含操作步骤、前置步骤、有序测试步骤、自动化脚本、接口调用代码或执行数据表。

## 硬性约束

- 不生成完整测试用例。
- 不生成操作步骤。
- 不生成自动化脚本。
- 不编造当前用户明确指令、适用 rules、需求、设计方案或分析方案中没有的业务规则、接口、字段、状态、角色、阈值、错误提示、错误码或测试数据。
- 不把“回读原始需求、设计方案、过程报告或 memory”作为后续理解测试设计方案的前提。
- 不直接覆盖历史运行产物；设计交付件必须写入固定 run 目录，并使用固定文件名。
- 不允许在 `skills/`、`.claude-plugin/`、`.opencode/`、插件缓存目录或 skill 工作目录下创建 `outputs/runs/`。
- 全流程不调用用户交互能力；多个环节只登记过程候选，不直接向用户提问，不暂停主流程。
- 未经用户明确确认，不写入 memory 源文件。
