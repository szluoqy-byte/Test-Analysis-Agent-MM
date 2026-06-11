---
name: test-design-workflow
description: 当用户提供已评审测试分析方案，或要求从需求先生成分析方案再扩展设计项时使用。该 skill 是 test-design-agent 主入口，负责编排测试分析方案校验、需求/设计依据补读、测试设计项生成、独立评审和 Markdown 产物输出；入参来自 $ARGUMENTS。
---

# 测试分析方案到测试设计方案主入口

本 skill 是 `test-design-agent` 的完整链路入口。目标是从 `$ARGUMENTS` 指定的已评审 `测试分析方案` 出发，生成 `测试设计方案`。

`测试设计方案` 回答 how to test：在既有 `测试场景 -> 测试点 -> 测试点明细` 层级下，为普通测试点明细补充 `TDI-*` 测试设计项；如果分析方案中存在非成功测试点明细的 `TP-*-*-*` 第四层，则在失败类型明细下补充 `TDI-*`。测试设计项只表达代表性条件、具体数据值、数据槽位、状态、接口返回或组合；简短预期结果保留在普通测试点明细或失败类型明细层，不在 TDI 下一层重复输出。

推荐术语：

- 主交付件名称：`测试设计方案`。
- 单条设计项名称：`测试设计项`。
- 固定缩写：测试场景 `SC-*`、测试点 `TP-*`、测试点明细 `TP-*-*`、失败类型明细 `TP-*-*-*`、测试设计项 `TDI-*`；主交付件不展开英文全名。
- 设计项 ID：`TDI-001` 起全局连续编号。
- 设计项内容：代表性条件、具体数据值、数据槽位、状态、接口返回或组合。
- 预期结果：普通测试点明细或失败类型明细层的判定结果；只能写需求或设计方案明确支持的结果，依据不足时写 `待人工分析确认`。

## 必需输入

优先输入：

- `$ARGUMENTS`：一份 `test-analysis-solution.md` 或其他已评审测试分析方案 Markdown 路径。
- 可选：原始需求文档路径、设计方案文档路径、`--requirement <path>`、`--design <path>`、`requirement=<path>`、`design=<path>`、`project=<project-key>` 或 `personal=<personal-key>`。原始需求、设计依据或外部分析方案可以是 `.md`、`.docx` 或 `.xlsx`；Office 输入必须先绑定为 run-local Markdown。

兼容输入：

- 如果用户只提供需求文档和可选设计方案文档，并明确要求生成测试设计方案，本 skill 必须先使用 `test-analysis-workflow` 生成 `deliverables/test-analysis-solution.md`，再以该分析方案作为设计输入继续执行。
- 如果输入包含 `.docx` 或 `.xlsx`，必须先固定或创建 `<run-id>`，再使用 `normalize-input-documents` 转换到全局 cache 并绑定到 `outputs/runs/<run-id>/inputs/`；后续分析方案校验、需求/设计依据补读或上游分析流程只读取 run-local Markdown 路径。
- 如果用户提供的分析方案未通过 `bin/lint-test-analysis-solution.py`，不得静默设计；先记录为输入质量问题，按需回到分析流程修正。

## 职责边界

- 本 skill 只负责编排设计链路和写出测试设计方案。
- 测试分析层事实来自已评审测试分析方案；不得把设计阶段发现的新范围直接写成新的 `SC-*`、`TP-*`、`TP-*-*` 或 `TP-*-*-*`。
- 需求与设计方案只用于校验和补强测试设计项依据；不得覆盖分析方案中的已评审层级。
- 适用 rules 的优先级低于当前用户明确指令，但高于测试分析方案、需求文档、设计方案、memory 和 knowledge；与输入冲突时遵守 rules 并记录覆盖原因。
- 通用测试分析/设计边界、测试设计方案标准和测试技术来自 `knowledge/`。
- `test-design-solution-generation` 负责把普通测试点明细或失败类型明细扩展为数据化测试设计项，并保留叶子节点预期结果。
- `test-design-solution-review` 负责在确定性 lint 通过后独立评审设计项数据化粒度、叶子节点预期结果依据和非完整用例化语义，不重复结构、编号、字段和 Markdown 语法检查。
- 设计阶段只承接分析层级，不重新判定或修复 `SC-*`、`TP-*`、`TP-*-*` 或 `TP-*-*-*` 的归属；分析层缺口记录为输入质量问题，必要时回到分析流程修正。
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

1. 校验输入：识别测试分析方案、需求文档和可选设计方案文档；如果输入包含 `.docx` 或 `.xlsx`，此时只识别路径，不读取 Office 正文。
2. 如果没有测试分析方案，先调用 `test-analysis-workflow` 生成分析方案，并以其输出作为后续输入；该上游分析流程负责创建 run、归一化 Office 输入并绑定 run-local inputs。
3. 固定 `PROJECT_ROOT` 和 `<run-id>`；如果输入分析方案位于 `${PROJECT_ROOT}/outputs/runs/<run-id>/deliverables/test-analysis-solution.md`，优先复用该 run，否则运行 `python bin/generate-run-id.py` 新建 run。创建或复用 `${PROJECT_ROOT}/outputs/runs/<run-id>/deliverables/`、`process/`、`reports/` 和 `inputs/`。
4. 创建或刷新 `process/task-list.md`，记录当前进入测试设计阶段。
5. 若当前设计输入仍包含未在本 run manifest 中绑定的 `.docx` 或 `.xlsx`，调用 `normalize-input-documents`，使用 `python skills/normalize-input-documents/scripts/normalize-office-input.py --run-dir outputs/runs/<run-id> ...` 将 Office 输入转换到全局 cache，并绑定到 `${PROJECT_ROOT}/outputs/runs/<run-id>/inputs/`；必须按该 skill 的“完成判定”处理或记录所有图片、图形、复杂 Excel 和转换 warning 后，才能把“输入文档归一化”阶段标记为 `done`；后续步骤只使用 run-local Markdown 路径。若 Office 输入已由上游分析 run 绑定，该阶段置为 `done` 并以既有 `inputs/input-normalization-manifest.json` 及 warning 收口记录为证据；若无 Office 输入，该阶段置为 `skipped`。
6. 读取并校验 `deliverables/test-analysis-solution.md`；若文件存在，运行 `bin/lint-test-analysis-solution.py`。
7. 读取或生成 `process/context-pack.md`，确认适用 rules、Rules 与输入冲突记录、project/personal 来源和项目知识阶段绑定。
8. 创建或刷新 `process/clarification-session.md`；如果设计阶段没有新增待确认候选，声明 `无待确认候选`。
9. 受控补读 run-local 原始需求 Markdown、设计方案 Markdown、`design-facts` 或过程报告中与当前分析方案相关的依据；不得要求后续读者回看这些文件才能理解主交付件。
10. 使用 `test-design-solution-generation` 在普通 `TP-*-*` 或失败类型 `TP-*-*-*` 下生成 1-N 个 `TDI-*`，写入 `${PROJECT_ROOT}/outputs/runs/<run-id>/deliverables/test-design-solution.md`，并记录项目知识应用状态。
11. 运行 `bin/lint-test-design-solution.py ${PROJECT_ROOT}/outputs/runs/<run-id>/deliverables/test-design-solution.md` 做确定性结构校验；失败时先修正主交付件，不进入独立评审。
12. 使用 `test-design-solution-review` 独立评审测试设计方案，重点检查分析方案承接、失败类型明细继承、设计项数据化粒度、叶子节点预期结果依据和非完整用例化语义。
13. 使用 `coverage-review` 或设计级覆盖审查记录检查需求覆盖、分析方案承接关系、项目知识应用状态和过程门禁，不重复 lint 已覆盖的结构规则。
14. 如需保留过程审查信息，使用 `templates/test-design-report-template.md` 将设计报告写入 `${PROJECT_ROOT}/outputs/runs/<run-id>/reports/test-design-report.md`。
15. 最终输出前刷新 `process/task-list.md`：设计阶段必选项必须为 `done`，未触发的可选项为 `skipped` 并说明原因；`process/task-list.md`、`process/context-pack.md` 和 `process/clarification-session.md` 必须同时存在；运行 `bin/check-artifact-consistency.py ${PROJECT_ROOT}/outputs/runs/<run-id>` 做最终一致性检查；如果存在 `blocked`，必须在过程报告中说明。

## 阶段产物契约

| 阶段 | 必须产出 | 交给下一阶段 |
|---|---|---|
| `normalize-input-documents` | Office 输入全局 cache、run-local Markdown、conversion metadata、`inputs/input-normalization-manifest.json`、warning 收口记录；无 Office 输入时记录 skipped | 分析方案校验和设计依据补读 |
| `analysis-solution-check` | 已校验测试分析方案、承接关系检查 | 测试设计项生成 |
| `memory-context-builder` | `process/context-pack.md` 或复用记录、适用强制规则、Rules 与输入冲突记录、项目知识阶段绑定 | 测试设计项生成和评审 |
| `clarification-session` | `process/clarification-session.md`，无候选时声明 `无待确认候选` | 测试设计项生成和评审 |
| `test-design-solution-generation` | `TDI-*` 测试设计项、叶子节点预期结果、项目知识应用状态 | 确定性校验 |
| 确定性校验 | `lint-test-design-solution.py` 结果 | 独立评审；失败时回到主交付件修正 |
| `test-design-solution-review` | 独立评审结论、修正建议 | 覆盖审查与输出收口 |
| `coverage-review` | 门禁结果、阻断项和修正建议 | 主交付件和过程报告刷新 |

## Project Knowledge 应用留痕

如果 `process/context-pack.md` 的“项目知识阶段绑定”表中存在绑定到当前阶段的 project knowledge，当前阶段必须输出应用记录：

| 来源文件 | 当前阶段 | 应用状态 | 应用位置 | 说明 |
|---|---|---|---|---|

应用状态只能使用 `applied`、`not_applicable`、`insufficient_evidence`、`conflict_with_requirement` 或 `deferred_to_review`。覆盖审查必须检查所有已绑定文件是否被对应阶段读取并留痕；未读取或无状态说明时，按质量问题处理。

## 输出要求

- 主输出使用 `templates/test-design-solution-template.md`。
- 主输出只包含测试设计方案所需内容，不设置 `未明确规则` 章节，不设置独立待确认信息清单。
- 主输出必须包含 `## 1. 设计输入` 和 `## 2. 测试场景与测试设计`。
- 主输出必须保留普通分支 `测试场景 -> 测试点 -> 测试点明细 -> 测试设计项` 层级；非成功分支必须保留 `测试场景 -> 测试点 -> 测试点明细 -> 失败类型明细 -> 测试设计项` 层级。
- 主输出必须继承分析方案中的 `E2E场景测试` 独立同级结构；E2E 只生成端到端主流程成功闭环设计项，其他规则、异常、接口、权限、状态、回滚或补偿设计项保留在同级 `TP-*` 下。
- 如果分析方案包含接口测试或集成覆盖场景，主输出必须继承按接口、端点、消息、回调、集成点或通用接口范围组织的 `TP-*`；不得把多个接口的 `TDI-*` 混到无法定位目标接口的泛化测试点下。
- 如果分析方案已有 `TP-*-*-*` 失败类型明细，`TDI-*` 必须挂在第四层下；如果分析方案中的单一弱结果分支停留在 `TP-*-*`，`TDI-*` 直接挂在该明细下，不为了设计阶段机械新增第四层。
- 主输出只使用中文术语和固定缩写 `SC`、`TP`、`TP-*-*`、`TP-*-*-*`、`TDI`，不得使用 `TD-*`、`TC-*`、`TCT-*`、`TI-*`、`ITP-*` 或 `ITDI-*`。
- 每个普通测试点明细或失败类型明细下必须保留 1 条 `- 预期结果：<明确预期结果或待人工分析确认>`，并至少有 1 个测试设计项。
- 测试设计项必须使用列表节点：`- TDI-001 <条件/数据/状态/组合>`，不得在 TDI 下一层重复写 `预期结果`。
- 主输出不得使用测试设计项表格；`TDI-*` 以列表节点挂在对应普通测试点明细或失败类型明细下，便于 Markdown 转脑图时保持层级。
- `TDI-*` 后的正文只写代表性条件、具体数据值、数据槽位、状态、接口返回或组合，例如 `amount=1000.00；category=PAY；customer_id=AGT_CUSTOMER_001`。
- 接口类 `TDI-*` 不得写完整裸 URL，例如 `GET https://api.example.com/customers/?telephone_exact=...`；必须拆成同一行字段片段，例如 `接口=GET /customers/；telephone_exact=%2B225070000001；响应状态=HTTP 500`。
- `TDI-*` 不得写成结果或动作描述，例如“发送通知”“显示错误提示”“自动填充”“接口调用正确”“处理成功”“删除成功”；这些语义应保留在测试点详情或预期结果层，设计项只写可选择的条件、数据、状态、接口返回或组合。
- 多个场景、渠道、操作或接口复用同类条件时，`TDI-*` 必须补充差异维度，例如 `场景=Add Payment`、`渠道=APP`、`操作=Delete Favorite`、`接口=POST /payments/`、`数据依赖=预验证已失败`，不得输出无差异的重复设计项。
- 接口契约叶子节点必须结合输入已明确的字段约束生成代表性有效、无效、边界和异常返回组合；例如金额精度、枚举值、必填字段、鉴权、幂等、状态码、错误码、超时和重试。
- 超时、回滚、补偿或外部依赖恢复类叶子节点必须把分支写成可观察组合，例如 `查询返回count=1；payment_status=SUCCESS`、`查询返回count=0；payment_status=FAILED`、`查询超时；payment_status=TIMEOUT`，不得只写抽象“接口超时”或“补偿成功”。
- `预期结果` 只能来自当前用户明确指令、适用 rules、需求、设计方案、测试分析方案、context pack 中明确事实或可直接推出的业务不变量。
- 如果需求和设计方案没有明确错误提示、状态变化、错误码、返回内容、数据记录变化或其他判定依据，`预期结果` 写 `待人工分析确认`。
- 主输出不得包含 `覆盖意图`、`级别`、`待确认信息`、`判定关注`、`输入条件与数据依赖` 等旧字段。
- 主输出不得使用 Markdown 加粗语法，例如 `**文本**` 或 `__文本__`。
- 主输出不得包含操作步骤、前置步骤、有序测试步骤、自动化脚本、接口调用代码或执行数据表。

## 硬性约束

- 不生成完整测试用例。
- 不生成操作步骤。
- 不生成自动化脚本。
- 不编造当前用户明确指令、适用 rules、需求、设计方案或分析方案中没有的业务规则、接口、字段、状态、角色、阈值、错误提示或错误码；测试设计项可使用由规则推导的代表值或稳定数据槽位，但不得伪造真实生产数据或需求未说明的业务事实。
- 不把“回读原始需求、设计方案、过程报告或 memory”作为后续理解测试设计方案的前提。
- 不直接覆盖历史运行产物；设计交付件必须写入固定 run 目录，并使用固定文件名。
- 不允许在 `skills/`、`.claude-plugin/`、`.opencode/`、插件缓存目录或 skill 工作目录下创建 `outputs/runs/`。
- 全流程不调用用户交互能力；多个环节只登记过程候选，不直接向用户提问，不暂停主流程。
- 未经用户明确确认，不写入 memory 源文件。
