# Test Analysis Agent 项目规则

本仓库是一个独立维护的测试分析与测试设计 Agent 包。它面向需求文档、可选设计方案文档和已评审测试分析方案生成 `测试分析方案` 或 `测试设计方案`，不依赖其他 Agent 项目、旧插件链路或外部仓库结构。

测试分析 Agent 主输出粒度为：

```text
测试场景 -> 测试点 -> 测试点明细
非成功测试点明细 -> 失败类型明细
```

测试设计 Agent 主输出粒度为：

```text
测试场景 -> 测试点 -> 测试点明细 -> 测试设计项
非成功测试点明细 -> 失败类型明细 -> 测试设计项
```

测试分析方案不生成测试设计项。测试设计方案不生成完整测试用例、前置步骤、测试步骤、自动化脚本或可执行测试数据清单。`测试点明细` 的核心是说明测试点下需要评审的规则分支、路径分支、状态分支、权限分支、接口契约分支或风险分支；只有明确非成功聚合测试点明细强制新增 `TP-*-*-*` 失败类型明细继续拆分失败来源，单一弱结果分支可停留在 `TP-*-*`。`测试设计项` 的核心是说明用哪些代表性条件、具体数据值、数据槽位、状态、接口返回或组合覆盖测试点明细或失败类型明细。

主交付件术语与缩写固定为：测试场景 `SC-*`、测试点 `TP-*`、测试点明细 `TP-*-*`、失败类型明细 `TP-*-*-*`、测试设计项 `TDI-*`。分析方案不使用 `TDI-*`；设计方案不使用 `TD-*`、`TC-*`、`TCT-*`、`TI-*`、`ITP-*` 或 `ITDI-*`。主交付件不展开英文全名。

## 运行入口

- Claude Code 使用 `.claude-plugin/plugin.json`、根目录 `agents/` 和根目录 `skills/`。
- OpenCode 使用 `opencode.json`、`AGENTS.md`、`.opencode/agents/`、`.opencode/commands/` 和 `.opencode/skills/`。
- 用户主入口 Agent 包括 `@test-analysis-agent` 和 `@test-design-agent`，源文件分别是 `agents/test-analysis-agent.md` 和 `agents/test-design-agent.md`。
- 测试分析主流程 skill 入口是 `skills/analyze-requirement-test-analysis-solution/SKILL.md`。
- 测试设计主流程 skill 入口是 `skills/generate-test-design-solution/SKILL.md`。
- OpenCode 独立文档归一化命令入口是 `.opencode/commands/normalize-input-documents.md`，用于在切换到多模态模型后单独执行 `.docx` / `.xlsx` 转 Markdown 与可选图片/图形补充，不进入测试分析或测试设计主流程。
- Agent 门面负责用户意图识别和路由；具体流程动作仍放在 skills、knowledge 文件、templates 或 quality gates 中。

## Agent 与 Skill 事实源

- `agents/` 是唯一手工维护的 Agent 门面源。
- `skills/` 是唯一手工维护的 skill 源。
- `.opencode/agents/` 是供 OpenCode 发现 Agent 的生成镜像。
- `.opencode/skills/` 是供 OpenCode 发现 skill 的生成镜像。
- 修改任何 `agents/*.md` 或 `skills/*/SKILL.md` 后，运行 `python bin/sync-opencode-skills.py`。
- 修改运行时 wiring 后，运行 `python bin/validate-agent-runtime.py`。

## 路径规则

- 所有 `skills/...`、`rules/...`、`knowledge/...`、`templates/...`、`quality-gates/...`、`memory/...`、`bin/...` 和 `outputs/...` 路径都从仓库根目录解析。
- 不要基于 skill 目录、`.claude-plugin/`、`.opencode/` 或输入文件目录解析路径。
- 运行产物写入 `outputs/runs/<run-id>/`。
- Office 输入归一化采用两层路径：全局复用缓存写入 `outputs/input-cache/<sha256-12>/`；完整 run 的本次输入绑定写入 `outputs/runs/<run-id>/inputs/`。
- 新建完整 run 时，`run-id` 固定使用 `python bin/generate-run-id.py` 生成，格式为 `<YYYYMMDD-HHMMSS>`。
- 测试分析主交付件固定为 `outputs/runs/<run-id>/deliverables/test-analysis-solution.md`。
- 测试设计主交付件固定为 `outputs/runs/<run-id>/deliverables/test-design-solution.md`，优先复用上游测试分析方案所在 run。
- 创建 run 目录后必须维护三个固定 process 产物：`process/task-list.md`、`process/context-pack.md` 和 `process/clarification-session.md`。
- `process/task-list.md` 是阶段顺序和状态的流程事实源；`process/context-pack.md` 是本次上下文绑定事实源；`process/clarification-session.md` 是待确认治理事实源。
- 即使没有 project/personal 命中或没有待确认候选，也必须生成对应 process 产物，并在文件内写明无命中或 `无待确认候选`。

## Project/Personal 上下文

- 支持可选 `project-key`：确定后可扫描 `*/projects/<project-key>/**/*.md`；未唯一确定时不得读取所有项目目录正文。
- `project` 和 `personal` 是当前 run 的一等输入源：必须在 `process/context-pack.md` 中记录绑定结果、命中来源、未采用来源和补读建议。
- `rules/` 是强制规则源，按 `core / project / personal` 三层加载：`rules/*.md`、`rules/projects/<project-key>/**/*.md`、`rules/user/**/*.md`。
- rules 优先级低于当前用户明确指令，但高于当前输入文档、memory 和 knowledge；与输入冲突时默认遵守 rules，并在过程产物中记录覆盖原因。
- rules 内部按 `core > project > personal` 处理，低层只能细化高层规则，不能放宽或违反高层强制约束。
- `knowledge/projects/<project-key>/` 和 `knowledge/user/` 只能作为测试知识补充，不得覆盖根目录 `knowledge/` 的核心标准、字段、类型和质量门禁。
- `knowledge/projects/<project-key>/` 下的文件名没有硬性要求；`memory-context-builder` 必须自理解识别文件用途并在 `context-pack.md` 记录项目知识阶段绑定。被绑定到某阶段的文件，该阶段必须读取并输出应用状态。
- personal 层只能补充个人偏好和本地检查关注点，不得作为项目事实或团队共识。

## 主流程

- 当用户要求基于需求和设计方案生成测试场景、测试点、测试点明细粒度的方案时，使用 `analyze-requirement-test-analysis-solution`。
- 如果需求文档、系统设计方案或外部分析方案输入是 `.docx` 或 `.xlsx`，先固定 `<run-id>` 并创建 run 目录，再使用 `normalize-input-documents` 调用 `python bin/normalize-office-input.py --run-dir outputs/runs/<run-id> ...` 转换到全局 cache 并绑定为 run-local Markdown；后续流程只读取 `outputs/runs/<run-id>/inputs/` 下的归一化 Markdown 路径。
- 阶段性动作依次使用 `normalize-input-documents`（仅 Office 输入时触发）、`memory-context-builder`、`requirement-testability`、`design-solution-extraction`、`clarification-gate`、`testing-method-router`、路由选中的专项分析 skills、`testpoint-generation`、`test-analysis-solution-generation`、确定性 lint、`test-analysis-solution-review` 和 `coverage-review`。
- 设计方案输入用于补充接口、字段、状态、权限、数据依赖、配置开关、异常处理和非功能指标；没有设计方案时继续生成，并把缺口沉淀到过程澄清记录或单条预期结果的 `待人工分析确认`。
- 当用户要求基于已评审测试分析方案生成测试设计项时，使用 `generate-test-design-solution`。
- 测试设计阶段使用 `test-design-solution-generation`、确定性 lint 和 `test-design-solution-review`，在每个 `TP-*-*` 下生成 `TDI-*`；如果用户只提供需求/设计方案且要求测试设计，必须先生成或取得测试分析方案，再进入测试设计。
- 不编造业务事实、状态、角色、接口契约、阈值、错误码、错误提示或状态变化；测试设计阶段可使用由规则推导的代表值或稳定数据槽位，但不得伪造真实生产数据或需求未说明的业务事实。
- 如果需求和设计方案没有说明错误提示、状态变化、错误码或其他判定依据，相关测试点明细或失败类型明细的 `预期结果` 写 `待人工分析确认`。
- 每个测试场景下必须包含一个 `E2E场景测试` 测试点，用于覆盖该场景端到端业务主流程是否按预期完整闭环。
- `E2E场景测试` 是场景下独立同级 `TP-*`，只维护 1 个端到端主流程成功闭环测试点明细；其他业务规则、异常处理、接口契约、权限、状态、数据校验、回滚或补偿分支必须拆成同级 `TP-*`。
- 当需求、设计方案或用户任务明确要求接口测试/API 契约覆盖时，接口测试或集成覆盖场景下的非 E2E `TP-*` 必须先按接口、端点、消息、回调或集成点组织；字段、状态码、错误码、鉴权、幂等、超时和重试作为该接口 `TP-*` 下的明细或失败类型，不作为无法定位目标接口的泛化 `TP-*`。
- 是否新增第四层由 `TP-*-*` 测试点明细决定：只有明确非成功聚合明细强制新增 `TP-*-*-*` 失败类型明细；“未找到返回空结果”“列表为空”“count=0”等单一弱结果分支可停留在 `TP-*-*`。`TP-*` 本身仍表示测试点主题。
- 主交付件不设置独立的 `未明确规则` 章节，也不输出待确认信息清单；澄清和缺口治理保留在过程产物中。
- 主交付件不得使用 Markdown 加粗语法，例如 `**文本**` 或 `__文本__`。
- 测试设计方案中的普通测试点明细或失败类型明细层保留一条 `- 预期结果：...`；`TDI-*` 必须使用列表节点，格式为 `- TDI-001 <条件/数据/状态/组合>`，不得在 TDI 下一层重复写预期结果，不得使用测试设计项表格。
- `TDI-*` 应优先写具体数据值、数据槽位、状态值、接口返回或组合，例如 `amount=1000.00；category=PAY；customer_id=AGT_CUSTOMER_001`，不要只写“有效金额”“错误PIN”“接口超时”等抽象标签。
- 接口类 `TDI-*` 不得写完整裸 URL，例如 `GET https://host/path?query=...`；必须拆成 `接口=GET /path`、`参数名=参数值`、`响应状态=HTTP 500` 等同一行字段片段，避免 Markdown 转脑图时被链接解析或换行破坏层级。
- `TDI-*` 不得写结果或动作表达，例如“发送通知”“显示提示”“自动填充”“接口调用正确”“处理成功”“删除成功”；这些内容属于测试点详情或预期结果。
- 同类条件在不同场景、渠道、操作或接口下复用时，`TDI-*` 必须补充差异维度，例如 `场景=`、`渠道=`、`操作=`、`接口=` 或 `数据依赖=`；无差异重复项应合并。
- 接口契约叶子节点应基于输入已明确字段约束覆盖代表性有效、无效、边界、枚举、必填、鉴权、幂等、超时或异常返回组合，不只生成正向有效组合。
- 超时、回滚、补偿或外部依赖恢复类叶子节点应写成可观察条件组合，例如查询返回数量、状态值、依赖返回或超时状态，不只写“接口超时”或“补偿成功”。
- 确定性结构、编号、字段、Markdown 语法和固定产物一致性问题以 Python 脚本为事实源；`test-analysis-solution-review` 和 `coverage-review` 不重复执行脚本已覆盖的检查，只处理语义质量、覆盖、追踪、方法应用、rules/project knowledge 应用和过程门禁。
- 在认为单次报告完成前，只运行当前 run 相关的确定性检查，例如对应交付件 lint 和 `bin/check-artifact-consistency.py`；不要在 review 阶段运行示例 smoke。

## 校验命令

- Runtime wiring：`python bin/validate-agent-runtime.py`
- OpenCode skill 镜像：`python bin/sync-opencode-skills.py --check`
- 测试分析方案结构：`python bin/lint-test-analysis-solution.py <solution.md>`
- 测试设计方案结构：`python bin/lint-test-design-solution.py <solution.md>`
- 单次 run 一致性：`python bin/check-artifact-consistency.py outputs/runs/<run-id>`
- 框架回归/示例 fixture smoke：`python bin/smoke-test-analysis.py`，仅在修改 Agent、skill、knowledge、template、quality gate、bin 脚本或示例 fixture 时运行，不属于单次方案 review 阶段。
