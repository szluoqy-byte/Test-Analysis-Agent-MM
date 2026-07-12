# Test Analysis Agent 项目规则

本仓库是独立维护的测试分析与测试设计 Agent 包。它面向需求文档、可选设计方案文档和已评审测试分析方案生成 `测试分析方案` 或 `测试设计方案`，不依赖其他 Agent 项目、旧插件链路或外部仓库结构。

主输出粒度固定为：

```text
测试分析 Agent：测试场景 SC -> 测试点 TP
测试设计 Agent：测试场景 SC -> 测试点 TP -> 测试用例 TC
```

`SC-*` 是业务场景树，最多 3 层，例如 `SC-001`、`SC-001-001`、`SC-001-001-001`。只有叶子场景挂载 `TP-*`。`TP-*` 是验证目标、规则点、路径点、状态点、权限点、接口契约点或风险点，编号在 run 内全局唯一且增量稳定。`TC-*` 是可执行测试用例，包含前置条件、具体测试数据、步骤、步骤预期和最终预期，编号在 run 内全局唯一且增量稳定；新增编号从历史最大值后追加，已退役编号不复用。

测试分析方案不输出测试用例、步骤、测试数据或预期结果。测试设计方案在每个测试点下输出完整步骤级测试用例。新 run 只允许 schemaVersion 2.0 定义的字段、编号和层级。

## 运行入口

- Claude Code 使用 `.claude-plugin/plugin.json`、根目录 `agents/` 和根目录 `skills/`。
- OpenCode 使用 `opencode.json`、`AGENTS.md`、`.opencode/agents/`、`.opencode/commands/` 和 `.opencode/skills/`。
- TestAgent/CodeArts 兼容入口使用 `codearts.json`、`.testagent/agents/`、`.testagent/commands/` 和 `.testagent/skills/`；`.testagent` 内容由同步脚本与 `.opencode` 保持一致。
- 用户主入口 Agent 包括 `@file-normalization-agent`、`@test-analysis-agent`、`@test-design-agent` 和 `@test-e2e-analysis-design-agent`。
- 文件归一化入口是 `agents/file-normalization-agent.md`，用于把 `.docx` / `.xlsx` / `.md` 输入整理为后续分析或设计可读取的 Markdown 输入事实源。
- 测试分析主流程 skill 入口是 `skills/test-analysis-workflow/SKILL.md`。
- 测试设计主流程 skill 入口是 `skills/test-design-workflow/SKILL.md`。
- 测试分析与测试设计全流程编排入口是 `skills/test-analysis-design-workflow/SKILL.md`，优先用独立 subagent 分别执行分析和设计阶段，再将完整分析 JSON 显式交给设计阶段。
- 测试用例写作 skill 入口是 `skills/test-case-writing/SKILL.md`，用于把 canonical 测试设计 JSON 写作为标准 Markdown 或后续扩展的不同交付风格。
- 最终人审报告 skill 入口是 `skills/final-report-generation/SKILL.md`，用于在 coverage-review 闭环后基于已审查的 FACT 覆盖证据图生成输入事实到 SC/TP/TC 的最终覆盖展示。
- OpenCode 独立文档归一化命令入口是 `.opencode/commands/normalize-input-documents.md`。
- Agent 门面负责用户意图识别和路由；具体流程动作仍放在 skills、knowledge、templates 或对应 skill 私有参考中。

## Agent 与 Skill 事实源

- `agents/` 是唯一手工维护的 Agent 门面源。
- `skills/` 是唯一手工维护的 skill 源。
- `.opencode/agents/`、`.opencode/skills/`、`.testagent/agents/` 和 `.testagent/skills/` 是生成镜像，不直接手工编辑。
- 修改任何 `agents/*.md`、`skills/*/SKILL.md` 或根目录 `codearts.json` 后，运行 `python bin/sync-opencode-skills.py`。
- 修改运行时 wiring 后，运行 `python bin/validate-agent-runtime.py`。
- 每个 `skills/<skill-name>/SKILL.md` 必须保持 Agent Skills 兼容 frontmatter：`name` 与目录名一致，`description` 说明做什么和何时使用，正文保持核心指令而不是长篇资料。
- 每个 skill 正文必须能快速定位：何时使用、输入、执行步骤、输出、验证闭环和约束/易错点；详细参考放入该 skill 的 `references/`，可执行 helper 放入该 skill 的 `scripts/`，并在正文说明何时读取或调用。
- 多步骤 workflow、生成、coverage 和 final-report 类 skill 必须包含 `Progress:` checklist，用 `- [ ] Step N: ...` 明确关键脚本、编辑对象和验证门禁。
- 本仓库命令仍从仓库根目录执行，因此命令示例使用仓库相对路径；skill 私有参考资料在说明中优先使用 `references/...`、`scripts/...` 的相对写法。

## 路径规则

- 所有 `skills/...`、`rules/...`、`knowledge/...`、`templates/...`、`memory/...`、`bin/...` 和 `outputs/...` 路径都从仓库根目录解析。
- 不要基于 skill 目录、`.claude-plugin/`、`.opencode/`、`.testagent/` 或输入文件目录解析路径。
- 运行产物写入 `outputs/runs/<run-id>/`。
- analysis/design/E2E 入口支持可选 `runid=<requirement-id>`，用于把同一需求的多次分析和设计维护在 `outputs/runs/<runid>/`；未提供时由 `bin/manage-run.py prepare` 调用固定时间戳规则生成 `<YYYYMMDD-HHMMSS>`。
- `runid` 只允许 1-64 位字母、数字、点、下划线和连字符，并以字母或数字开头；不得包含路径分隔符、`..` 或 Windows 保留名称。
- 持久 run 固定先执行 `python bin/manage-run.py prepare --flow analysis|design ...`，读取 `process/run-plan.json` 的 `create/resume/reuse/extend/rebuild` 决策；结束时执行 `finalize`，失败退出前执行 `abort` 释放锁。
- Office 输入归一化复用缓存写入 `outputs/input-cache/<sha256-12>/`；绑定既有 run 时写入 `outputs/runs/<run-id>/inputs/`。
- DOCX 图片、流程图、架构图、状态图、截图或 EMF/Visio 图形解析后的 Mermaid/结构化事实必须合并回同一个归一化 Markdown 的原文占位位置。
- DOCX 图片理解和 Mermaid 转换必须按原文顺序分批处理：普通图片每批最多 3-5 张，复杂图每批 1-2 张。

## 产物契约

- 测试分析主交付件固定为 `outputs/runs/<run-id>/deliverables/test-analysis-solution.json`，由 `bin/render-run-markdown.py` 渲染同名 `.md` 人读版。
- 测试设计主交付件固定为 `outputs/runs/<run-id>/deliverables/test-design-solution.json`，由 `test-case-writing` 调用 `bin/render-run-markdown.py` 渲染同名 `.md` 人读版；优先复用上游测试分析方案所在 run。
- JSON 是 run 过程产物、主交付件、review 和 coverage 的事实源；Markdown 是脚本派生产物，不手工维护。
- 持久 run 的生命周期事实源是 `process/run-manifest.json`；每次 `extend/rebuild` 修改前必须在 `revisions/rNNNN/` 创建 JSON/input 快照，当前交付路径保持不变。
- `process/run-manifest.json` 记录输入、project 绑定、analysis/design 依赖指纹、交付件 hash 和 revision；输入默认追加，同路径视为版本更新，删除旧来源必须显式使用 `remove-source=<path>`。
- 创建 run 目录后必须维护阶段化任务清单和共享过程产物：测试分析使用 `process/analysis-task-list.json/.md`，测试设计使用 `process/design-task-list.json/.md`；共享过程产物包括 `process/rules-pack.json/.md`、`process/context-pack.json/.md` 和 `process/input-fact-model.json/.md`。历史 `process/task-list.json/.md` 只作为兼容读取路径，不作为新流程写入目标。
- 测试分析必须先生成并评审冻结 `process/scenario-tree.json`，再按叶子 SC 生成 `process/test-point-slices/<SC-ID>.json`，最后合并为 `deliverables/test-analysis-solution.json`。
- 测试设计必须按每个已冻结 TP 生成 `process/test-case-slices/<TP-ID>.json`，评审后合并为 `deliverables/test-design-solution.json`。
- `process/scenario-tree.json`、`process/test-point-slices/<SC-ID>.json`、`process/test-case-slices/<TP-ID>.json` 以及 review/coverage JSON 必须包含由固定脚本生成的 `generationContext`；它只用于生成前工作包、规则正文、动态来源索引和事实候选，不作为最终业务事实合并进 deliverables。
- 测试设计流程固定按 `process/test-case-work-items.json` 和 `process/test-case-slices/<TP-ID>.json` 逐 TP 生成并合并，最终事实源仍是 `deliverables/test-design-solution.json`。
- 增量 run 中工作项使用 `contentHash` 判断上游内容变化；变化项必须自动重开。输入/context 变化由 workflow 做语义影响分析并用 `bin/reopen-run-items.py` 重开受影响 SC/TP，不能判定影响范围时保守重开全部。
- 测试分析和测试设计流程不得临时生成 `.py`、`.js`、`.ps1`、`.bat` 或其他可执行脚本来处理 JSON、循环切片、汇总状态或定位返工；固定脚本能力不足时修改仓库 `bin/` 脚本并运行校验。
- 主交付件 schema 使用 `2.0`；process、review 和 coverage 产物继续使用各自当前 schema。
- 新 run 只支持 schemaVersion 2.0；历史 run 需要按新模型重新生成。

## Project/Personal 上下文

- 支持可选 `project-key`：确定后可扫描 `*/projects/<project-key>/**/*.md`；未唯一确定时不得读取所有项目目录正文。
- `rules/` 是强制规则源，按 `core / project / personal` 三层加载，必须由 `bin/build-rules-pack.py` 写入 `process/rules-pack.json` 规则索引；后续每个阶段筛选 `ruleSources[]` 中对当前阶段可见的规则，读取对应 Markdown 正文并遵守。
- `project` 和 `personal` 的 knowledge/memory 是当前 run 的动态补充输入源：必须由 `context-source-indexing` 在 `process/context-pack.json` 中记录绑定结果和动态来源索引。
- 优先级分两层理解：workflow、skill、schema 和固定脚本定义运行时执行契约；业务与输出约束按 `当前用户明确指令 > rules > 当前输入文档 > memory > knowledge` 处理。
- `knowledge/projects/<project-key>/` 和 `knowledge/user/` 只能作为测试知识补充，不得覆盖根目录 `knowledge/` 的核心标准、字段和质量门禁。
- 动态来源必须声明 `name`、`description`，可选 `stages`；未配置 `stages` 时默认全部阶段可用。
- `context-source-indexing` 只读取 knowledge/memory 动态来源 frontmatter 生成 `sources[]`，不扫描 rules，不扫描 core 层，不摘录正文，也不替后续阶段判断具体命中。
- 后续 skill 只读取 `sources[]` 中对本阶段可见的文件正文，并输出应用状态。

## 主流程

- 当用户要求把 `.docx` / `.xlsx` / `.md` 输入整理为可供下游读取的 Markdown 输入事实源时，使用 `@file-normalization-agent`。
- 当用户要求基于需求和设计方案生成测试场景、测试点粒度的方案时，使用 `test-analysis-workflow`。该 workflow 只接受 Markdown 输入；Office 输入必须先归一化。
- 当用户要求从需求和设计方案一次性完成测试分析与测试设计时，使用 `test-analysis-design-workflow`。该 workflow 优先用独立 subagent 隔离执行 analysis/design，只做全流程编排和阶段交接，不复制 analysis/design 内部校验、review、coverage 或 final-report 逻辑；若运行环境不支持真实 subagent，才 fallback 为同会话 workflow 串联并在最终回复说明。
- 测试分析阶段依次使用 `rules-pack`、`context-source-indexing`、`input-fact-modeling`、`testing-method-router`、路由选中的专项方法参考、`test-analysis-solution-generation` 生成冻结 SC 树、`test-analysis-solution-review` 评审 SC、按叶子 SC 生成并评审 TP 切片、合并分析方案、JSON lint、Markdown render、派生 Markdown lint、最终 `test-analysis-solution-review`、构建并审查 `analysis-fact-coverage-map`、`coverage-review` 和 `final-report-generation`。
- 分段工作项状态查看、批量切片初始化、批量合并、review blocking 返工重开和分段 run 固定检查分别使用 `bin/list-staged-work-items.py`、`bin/init-staged-slices.py`、`bin/merge-staged-slices.py`、`bin/apply-review-findings.py` 和 `bin/check-staged-run.py`。
- 持久 run 生命周期、revision、依赖变化和并发锁由 `bin/manage-run.py` 管理；不得绕过有效的 `process/run.lock` 并发写同一 run。
- 覆盖证据过程件按阶段拆分：测试分析写入 `process/analysis-fact-coverage-map.json/.md`，测试设计写入 `process/design-fact-coverage-map.json/.md`。它是 coverage-review 的工作底稿，不是最终人审报告。
- 覆盖审查产物按阶段拆分：测试分析写入 `process/reviews/analysis-coverage-review.json/.md`，测试设计写入 `process/reviews/design-coverage-review.json/.md`。coverage-review 必须基于对应 fact-coverage-map 做门禁，避免 final-report 阶段才新增 missing 判断。
- coverage-review 发现覆盖缺口后，不直接编辑最终 Markdown 或主交付件 JSON；必须通过 `coverageGaps[].artifactLocation` 定位到 `process/test-point-slices/<SC-ID>.json` 或 `process/test-case-slices/<TP-ID>.json`，先运行 `bin/apply-coverage-gaps.py` 重开对应工作项，再修复切片并重新执行切片 review、脚本合并、最终 review、coverage 和一致性检查。
- 最终审阅报告产物按阶段拆分：测试分析写入 `reports/analysis-final-report.json/.md`，测试设计写入 `reports/design-final-report.json/.md`。final-report 只消费已审查的 fact-coverage-map 并展示输入 FACT 最终被哪些 SC/TP/TC 覆盖，不输出 `coverageGaps[]`，不触发 `apply-coverage-gaps.py`，也不参与自动返工链路。
- 当用户要求基于已评审测试分析方案生成测试用例时，使用 `test-design-workflow`。该 workflow 优先使用用户显式指定的 `test-analysis-solution.json`，否则只读取当前 run 已存在的 `deliverables/test-analysis-solution.json`。
- 测试设计阶段使用 `test-design-solution-generation` 按 TP 生成 TC 切片，`test-design-solution-review` 按切片评审，切片通过后由固定脚本合并并统一 TC 编号。
- 测试设计 coverage-review 闭环后使用 `final-report-generation` 从 `process/design-fact-coverage-map.json` 生成 `reports/design-final-report.json`，最终 Markdown 仍由脚本从 JSON 渲染。
- 如果用户只提供需求/设计方案且要求测试设计，不得自动调用测试分析 workflow；必须先取得完整 `test-analysis-solution.json`，再进入测试设计。
- 只有 `test-analysis-design-workflow` 可以在同一全流程中先运行分析再运行设计；`test-design-workflow` 本身不得自动运行分析。全流程阶段之间只通过 canonical JSON 和固定报告文件交接，不通过聊天上下文、自然语言总结或隐式记忆交接业务事实。
- 设计方案输入用于补充接口、字段、状态、权限、数据依赖、配置开关、异常处理和非功能指标；没有设计方案时继续生成，预期结果只写输入可支撑的保守判定。
- 不编造业务事实、状态、角色、接口契约、阈值、错误码、错误提示或状态变化。
- 每个叶子测试场景下必须包含一个 `E2E场景测试` 测试点，用于覆盖该场景端到端业务主流程是否按预期完整闭环。
- 接口测试或集成覆盖场景下的非 E2E `TP-*` 必须先按接口、端点、消息、回调或集成点组织；字段、状态码、错误码、鉴权、幂等、超时和重试作为该接口测试点的用例覆盖重点。
- 分析阶段不得把单个输入变体、边界点、角色样本、状态样本、错误类型、配置取值、依赖返回、消息顺序或接口参数缺失项拆成独立 TP；这些属于 TC 设计因子。若多个候选 TP 只在这些因子上不同但验证同一目标，应合并为一个 TP。
- 测试用例必须包含 `level`，取值为 `Level 0` 到 `Level 4`；`testData[]` 使用 `{name, value, description}` 数组；`steps[]` 使用 `{stepNo, action, expected}` 数组。
- 设计阶段不得把“每个 TP 至少 1 个 TC”当作充分覆盖；每个 TP 是验证目标簇，必须先识别必选因子、候选因子和基于 TP 目标补充推导的必要因子，再生成最小充分 TC 集合。已加载来源中的既有测试设计因子是必选覆盖项或启发来源，不是封闭上限；除非更高优先级指令明确限定仅使用指定因子集合，否则不得因为因子库未列出某类情况，就忽略该 TP 下有判定意义的独立测试实例。
- 测试用例公共写作必须遵守 `knowledge/test-case-writing-standard.md`，包括标题、前置条件、测试数据、步骤动作、步骤预期、最终预期和来源引用的写法。
- 测试步骤的 `action` 只写可执行动作或取数动作；字段、状态、记录、事件、响应内容等检查要求写入对应 `expected`，不要把“检查响应体字段”这类检查项单独写成步骤。
- GUI、API、CLI 测试用例必须按 `knowledge/test-case-writing-styles/` 中对应执行形态风格生成和评审；混合场景按测试人员实际发起动作确定主风格。
- 接口类测试用例步骤或测试数据不得写完整裸 URL；必须拆成 `接口=METHOD /path`、`参数名=参数值`、`响应状态=...` 等字段片段。
- 确定性结构、编号、字段、JSON 结构、Markdown 语法和固定产物一致性问题以 Python 脚本为事实源；review 和 coverage 不重复执行脚本已覆盖的检查。

## 校验命令

- Runtime wiring：`python bin/validate-agent-runtime.py`
- OpenCode/TestAgent skill 镜像：`python bin/sync-opencode-skills.py --check`
- 持久 run 生命周期回归：`python bin/test-persistent-run.py`
- 单次 run JSON 结构：`python bin/lint-run-json.py outputs/runs/<run-id>`
- 单次 run Markdown 渲染一致性：`python bin/render-run-markdown.py outputs/runs/<run-id> --check`
- 测试分析方案结构：`python bin/lint-test-analysis-solution.py <solution.md>`
- 测试设计方案结构：`python bin/lint-test-design-solution.py <solution.md>`
- 单次 run 一致性：`python bin/check-artifact-consistency.py outputs/runs/<run-id>`
- 框架回归/示例 fixture smoke：`python bin/smoke-test-analysis.py`
