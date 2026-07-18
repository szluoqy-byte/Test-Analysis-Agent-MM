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
- 只有当前任务实际修改了 agents 或 skills，才运行 `python bin/sync-opencode-skills.py`；只有实际修改了运行时 wiring，才运行 `python bin/validate-agent-runtime.py`。
- 正常执行文件归一化、测试分析、测试设计或 analysis-design 业务 run 时，不运行 `bin/sync-opencode-skills.py`、`bin/validate-agent-runtime.py` 或 `bin/smoke-test-analysis.py`，只执行对应 workflow 规定的当前 run 校验。
- `SKILL.md` 必须保持 Agent Skills 兼容：frontmatter 的 `name` 匹配目录名，`description` 说明做什么和何时用；正文保留核心流程，并包含何时使用、输入、执行步骤、输出、验证闭环和约束/易错点。
- 多步骤 workflow、生成、coverage 和 final-report 类 skill 必须包含 `Progress:` checklist，防止跳过脚本初始化、review、coverage 或最终校验。
- 从仓库根目录解析路径，不要从 `.claude-plugin/`、`.opencode/`、skill 目录或输入文件目录解析。
- `test-analysis-workflow` 和 `test-design-workflow` 不直接处理 `.docx` / `.xlsx`；它们只消费已归一化 Markdown 或 JSON canonical 输入。
- 每次 run 必须维护任务清单，以及 `process/rules-pack.json/.md`、`process/context-pack.json/.md` 和 `process/input-fact-model.json/.md`。
- `process/rules-pack.json` 是强制规则索引；后续阶段必须筛选当前阶段可见的 `ruleSources[]` 并读取对应 Markdown 正文。`process/context-pack.json` 只索引 project/personal knowledge 动态来源。
- JSON 是 run 过程产物、主交付件、review、coverage 和 final-report 的事实源；Markdown 是 `bin/render-run-markdown.py` 派生的人读版，不手工维护。
- 测试分析主交付件固定为 `deliverables/test-analysis-solution.json/.md`，输出粒度是 `SC 场景树 -> TP 测试点`。
- 测试设计主交付件固定为 `deliverables/test-design-solution.json/.md`，输出粒度是 `SC 场景树 -> TP 测试点 -> TC 测试用例`。
- 测试分析生成必须先冻结 `process/scenario-tree.json`，再按叶子 SC 生成并合并 `process/test-point-slices/<SC-ID>.json`。
- 测试设计生成必须按 TP 生成并合并 `process/test-case-slices/<TP-ID>.json`。
- SC/TP/TC 过程 JSON 和 review/coverage JSON 必须包含固定脚本生成的 `generationContext`，用于生成前工作包、规则正文、动态来源索引和事实候选。
- 分段工作项状态、批量切片初始化、批量合并、review blocking 返工重开和分段 run 固定检查使用仓库固定 `bin/` 脚本；不得临时创建脚本处理 JSON。
- coverage-review 前必须生成并审查 `process/analysis-fact-coverage-map.json` 或 `process/design-fact-coverage-map.json`；coverage 缺口必须先通过 `bin/apply-coverage-gaps.py` 重开对应 slice 工作项，再修复切片、评审、合并和收口。
- final-report 只消费已审查的 fact-coverage-map，展示输入 FACT 最终被哪些 SC/TP/TC 覆盖，不输出 `coverageGaps[]`，不触发自动返工。
- e2e 全流程阶段只通过 canonical JSON 和固定报告文件交接；不得依赖 analysis/design subagent 的聊天上下文或自然语言总结传递业务事实。
- `SC-*` 最多 3 层，只有叶子 SC 挂 `TP-*`；`TP-*` 全局连续；`TC-*` 全局连续。
- 测试分析方案不输出测试用例、步骤、测试数据或预期结果。
- 测试设计方案输出完整步骤级测试用例，包含前置条件、测试数据、步骤、步骤预期和最终预期。
- 新 run 只使用 schemaVersion 2.0 定义的字段、编号和层级。
- 每个叶子测试场景必须包含 `E2E场景测试` 测试点。
- 测试分析阶段不要把单个输入变体、边界点、角色样本、状态样本、错误类型、配置取值、依赖返回、消息顺序或接口参数缺失项拆成独立 TP；这些属于设计阶段 TC 因子。
- 如果错误提示、状态变化、错误码或其他判定依据未被需求/设计方案明确说明，测试用例最终预期只写输入可支撑的保守判定，不补写未说明具体值。
- 主交付件不得使用 Markdown 加粗语法，例如 `**文本**` 或 `__文本__`。
