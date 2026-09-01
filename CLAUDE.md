# Claude Code 项目规则

本仓库同时是 Claude Code plugin 和 OpenCode 项目 Agent 包，作为独立的测试分析与测试设计 Agent 维护。请遵循 `AGENTS.md` 中的同一套项目规则。

简版规则：

- Claude Code 加载 `.claude-plugin/plugin.json`、根目录 `agents/` 和根目录 `skills/`。
- 用户主入口 Agent 包括 `@file-normalization-agent`、`@test-analysis-agent`、`@test-design-agent` 和 `@test-e2e-analysis-design-agent`。
- 文件归一化入口是 `@file-normalization-agent`，用于把 `.docx` / `.xlsx` / `.md` 输入整理为后续分析或设计可读取的 Markdown 输入事实源。
- 测试分析主流程 skill 入口是 `skills/test-analysis-workflow/SKILL.md`。
- 测试设计主流程 skill 入口是 `skills/test-design-workflow/SKILL.md`。
- 全流程编排 skill 入口是 `skills/test-analysis-design-workflow/SKILL.md`，优先用独立 subagent 隔离执行 analysis/design；不支持真实 subagent 时才 fallback 为同会话 workflow 串联，不复制两边内部校验逻辑。
- 测试用例写作 skill 入口是 `skills/test-case-writing/SKILL.md`。
- 最终人审报告 skill 入口是 `skills/final-report-generation/SKILL.md`。
- `agents/` 是唯一手工维护的 Agent 门面源；`skills/` 是唯一手工维护的 skill 源。
- `.opencode/agents/` 和 `.opencode/skills/` 由根目录源生成，不要直接编辑。
- 只有当前任务实际修改了 agents 或 skills，才运行 `python bin/sync-opencode-skills.py`。
- 正常执行文件归一化、测试分析、测试设计或 analysis-design 业务 run 时，不运行 `bin/sync-opencode-skills.py`，只执行对应 workflow 规定的当前 run 校验。
- `SKILL.md` 必须保持 Agent Skills 兼容：frontmatter 的 `name` 匹配目录名，`description` 说明做什么和何时用；正文保留核心流程，并包含何时使用、输入、执行步骤、输出、验证闭环和约束/易错点。
- 多步骤 workflow、生成、coverage、final-report 和写作类 skill 必须使用阶段索引与同编号的 `各阶段执行要求`；阶段索引是静态执行契约，不维护阶段级状态 JSON、`Progress:` 或独立的“计划-校验-执行模式”状态副本。
- 从仓库根目录解析路径，不要从 `.claude-plugin/`、`.opencode/`、skill 目录或输入文件目录解析。
- `test-analysis-workflow` 和 `test-design-workflow` 不直接处理 `.docx` / `.xlsx`；它们只消费已归一化 Markdown 或 JSON canonical 输入。
- 每次 run 只维护必要的脚本控制 `id-registry/work-items` JSON，以及 `process/rules-pack.md`、`process/context-pack.md`、`process/input-fact-model.md` 等语义 Markdown。
- `runid` 只确定 `outputs/runs/<runid>/` 输出目录；未提供时直接使用当前会话时间戳。workflow 的 Step 1 不为此探测 Python、Bash 或调用 shell。
- 只有结果方案使用 JSON 作为阶段边界；过程、review、coverage 和 final-report 直接使用 Markdown。
- 测试分析主交付件固定为 `deliverables/test-analysis-solution.json/.md`，输出粒度是 `SC 场景树 -> TP 测试点`。
- 测试设计主交付件固定为 `deliverables/test-design-solution.json/.md`，输出粒度是 `SC 场景树 -> TP 测试点 -> TC 测试用例`。
- 测试分析先冻结 `process/scenario-tree.md`，再按叶子 SC 编写 `process/test-point-slices/<SC-ID>.md`；测试设计按 TP 编写 `process/test-case-slices/<TP-ID>.md`。
- 过程件不持久化 `generationContext`，不建立同名 JSON schema；结果草稿只在阶段边界生成一次。
- coverage 和 final-report 均使用 Markdown；缺口通过 `reopen-run-items.py` 重开对应切片工作项。
- e2e 全流程阶段只通过 canonical JSON 和固定报告文件交接；不得依赖 analysis/design subagent 的聊天上下文或自然语言总结传递业务事实。
- `SC-*` 最多 3 层，只有叶子 SC 挂 `TP-*`；`TP-*` 全局连续；`TC-*` 全局连续。
- 测试分析方案不输出测试用例、步骤、测试数据或预期结果。
- 测试设计方案输出完整步骤级测试用例，包含前置条件、测试数据、步骤、步骤预期和最终预期。
- 新 run 只使用 schemaVersion 2.0 定义的字段、编号和层级。
- 每个叶子测试场景必须包含 `E2E场景测试` 测试点。
- 测试分析阶段不要把单个输入变体、边界点、角色样本、状态样本、错误类型、配置取值、依赖返回、消息顺序或接口参数缺失项拆成独立 TP；这些属于设计阶段 TC 因子。
- 如果错误提示、状态变化、错误码或其他判定依据未被需求/设计方案明确说明，测试用例最终预期只写输入可支撑的保守判定，不补写未说明具体值。
- 主交付件不得使用 Markdown 加粗语法，例如 `**文本**` 或 `__文本__`。
