# Claude Code 项目规则

本仓库同时是 Claude Code plugin 和 OpenCode 项目 Agent 包，作为独立的测试分析与测试设计 Agent 维护。

请遵循 `AGENTS.md` 中的同一套项目规则。简版如下：

- Claude Code 加载 `.claude-plugin/plugin.json`、根目录 `agents/` 和根目录 `skills/`。
- 用户主入口 Agent 包括 `@test-analysis-agent` 和 `@test-design-agent`。
- 测试分析主流程 skill 入口是 `skills/analyze-requirement-test-analysis-solution/SKILL.md`。
- 测试设计主流程 skill 入口是 `skills/generate-test-design-solution/SKILL.md`。
- OpenCode 独立文档归一化命令入口是 `.opencode/commands/normalize-input-documents.md`，用于单独执行 `.docx` / `.xlsx` 转 Markdown 与可选图片/图形补充，不进入测试分析或测试设计主流程。
- 需求由 `requirement-testability` 结构化；设计方案由 `design-solution-extraction` 提取为设计事实摘要。
- `agents/` 是唯一手工维护的 Agent 门面源；`skills/` 是唯一手工维护的 skill 源。
- `.opencode/agents/` 和 `.opencode/skills/` 由根目录源生成，不要直接编辑。
- 修改 agents 或 skills 后，运行 `python bin/sync-opencode-skills.py`。
- 修改运行时 wiring 后，运行 `python bin/validate-agent-runtime.py`。
- 从仓库根目录解析路径，不要从 `.claude-plugin/`、`.opencode/`、skill 目录或输入文件目录解析。
- 如果需求文档、系统设计方案或外部分析方案输入是 `.docx` 或 `.xlsx`，先固定 `<run-id>` 并创建 run 目录，再使用 `normalize-input-documents` 归一化为 Markdown；全局缓存路径为 `outputs/input-cache/<sha256-12>/`，本次 run 输入绑定路径为 `outputs/runs/<run-id>/inputs/`。
- `normalize-input-documents` 必须处理或记录 DOCX 图片/图形、复杂 Excel 和 metadata warnings 的收口状态，不能只因脚本执行成功就结束。
- 新建完整 run 时，`run-id` 固定使用 `python bin/generate-run-id.py` 生成，格式为 `<YYYYMMDD-HHMMSS>`。
- `rules/` 是强制规则源，按 `core / project / personal` 三层加载，优先级低于当前用户明确指令但高于输入文档、memory 和 knowledge。
- 已确定 `project-key` 时可扫描 `*/projects/<project-key>/**/*.md`；未唯一确定时不要读取所有项目目录正文。
- 配置按 `core / project / personal` 三层处理；personal 本地目录是 `*/user/`，project 和 personal 层默认本地化，不提交 Git。
- project 和 personal 是当前 run 的一等输入源，命中、未采用和补读建议必须记录到 `process/context-pack.md`。
- `knowledge/projects/<project-key>/` 下的文件名没有硬性要求；context pack 必须记录项目知识阶段绑定，被绑定阶段必须读取并留痕。
- 每次 run 必须维护 `process/task-list.md`、`process/context-pack.md` 和 `process/clarification-session.md` 三个固定 process 产物。
- `process/task-list.md` 用于约束阶段顺序和状态；`process/context-pack.md` 记录本次上下文绑定；`process/clarification-session.md` 记录待确认治理结果，无候选时也必须声明 `无待确认候选`。
- 测试分析主交付件固定为 `outputs/runs/<run-id>/deliverables/test-analysis-solution.md`，输出粒度是“测试场景 -> 测试点 -> 测试点明细”；非成功测试点明细继续到失败类型明细。
- 测试设计主交付件固定为 `outputs/runs/<run-id>/deliverables/test-design-solution.md`，输出粒度是“测试场景 -> 测试点 -> 测试点明细 -> 测试设计项”；非成功测试点明细继承失败类型明细后再生成测试设计项。
- 主交付件术语与缩写固定为测试场景 `SC-*`、测试点 `TP-*`、测试点明细 `TP-*-*`、失败类型明细 `TP-*-*-*`、测试设计项 `TDI-*`，不展开英文全名。
- 测试点明细只表达分析层规则分支、路径分支、状态分支、权限分支、接口契约分支或风险分支，以及基于需求/设计方案可确认的预期结果。
- 每个测试场景必须包含 `E2E场景测试` 测试点；是否新增第四层由 `TP-*-*` 测试点明细决定，只有非成功测试点明细新增 `TP-*-*-*` 失败类型明细。
- 测试分析方案不输出 `TDI-*` 或测试设计项；它们由 `@test-design-agent` 承接。
- 测试设计方案只输出 `TDI-*` 代表性条件、具体数据值、数据槽位、状态、接口返回或组合，不输出完整测试用例。
- 测试设计方案中的 `预期结果` 保留在普通测试点明细或失败类型明细层；`TDI-*` 下一层不重复写预期结果。
- 接口类 `TDI-*` 不输出完整裸 URL；拆成 `接口=METHOD /path`、`参数名=参数值`、`响应状态=HTTP 500` 等同一行字段片段，避免 Markdown 转脑图时被链接解析或换行破坏层级。
- `TDI-*` 不写结果或动作表达，例如“发送通知”“显示提示”“自动填充”“接口调用正确”“处理成功”“删除成功”；同类条件复用时必须补充场景、渠道、操作、接口或数据依赖等差异维度。
- 接口契约叶子节点应基于已明确字段约束覆盖代表性有效、无效、边界、枚举、必填、鉴权、幂等、超时或异常返回组合；超时、回滚、补偿或外部依赖恢复类叶子节点应写成可观察条件组合。
- 如果错误提示、状态变化、错误码或其他判定依据未被需求/设计方案明确说明，普通测试点明细或失败类型明细的 `预期结果` 写 `待人工分析确认`。
- 主交付件不设置 `未明确规则` 章节，不输出独立待确认信息清单。
- 主交付件不得使用 Markdown 加粗语法，例如 `**文本**` 或 `__文本__`。
- 不生成完整测试用例、前置步骤、测试步骤、自动化脚本或执行数据清单。
- Agent 门面只负责用户意图识别和路由；具体流程动作仍放在 skills、knowledge 文件、templates 或 quality gates 中。
