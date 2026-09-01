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
- 只有当前任务实际修改了 `agents/*.md`、`skills/*/SKILL.md` 或根目录 `codearts.json`，才运行 `python bin/sync-opencode-skills.py`。
- 正常执行文件归一化、测试分析、测试设计或 analysis-design 业务 run 时，不得运行 `bin/sync-opencode-skills.py`；该脚本不校验当前 run 的业务产物。
- 每个 `skills/<skill-name>/SKILL.md` 必须保持 Agent Skills 兼容 frontmatter：`name` 与目录名一致，`description` 说明做什么和何时使用，正文保持核心指令而不是长篇资料。
- 每个 skill 正文必须能快速定位：何时使用、输入、执行步骤、输出、验证闭环和约束/易错点；详细参考放入该 skill 的 `references/`，可执行 helper 放入该 skill 的 `scripts/`，并在正文说明何时读取或调用。
- 多步骤 workflow、生成、coverage、final-report 和写作类 skill 必须用 `## 执行阶段`、`## 生成阶段`、`## 审查阶段`、`## 报告生成阶段`、`## 归一化阶段` 或 `## 写作阶段` 之一列出连续的 `- [ ] Step N: ...` 阶段索引，并在 `## 各阶段执行要求` 中以同编号、同标题展开执行、原则、脚本门禁和必要的失败回退。`### Step N` 是唯一顶层 Step 编号；其下可使用连续的操作编号，但不得形成第二套阶段清单。阶段索引是静态执行契约；不得再维护阶段级状态 JSON、独立 `Progress:` 或“计划-校验-执行模式”等重复状态副本。
- 本仓库命令仍从仓库根目录执行，因此命令示例使用仓库相对路径；skill 私有参考资料在说明中优先使用 `references/...`、`scripts/...` 的相对写法。

## 路径规则

- 所有 `skills/...`、`rules/...`、`knowledge/...`、`templates/...`、`bin/...` 和 `outputs/...` 路径都从仓库根目录解析。
- 不要基于 skill 目录、`.claude-plugin/`、`.opencode/`、`.testagent/` 或输入文件目录解析路径。
- 运行产物写入 `outputs/runs/<run-id>/`。
- analysis/design/E2E 入口支持可选 `runid=<requirement-id>`，它只用于确定 `outputs/runs/<runid>/` 输出目录；未提供时由当前会话直接采用 `<YYYYMMDD-HHMMSS>`，发生碰撞时追加 `-01`、`-02`。
- `runid` 只允许 1-64 位字母、数字、点、下划线和连字符，并以字母或数字开头；不得包含路径分隔符、`..` 或 Windows 保留名称。
- analysis/design workflow 的 Step 1 不得为了确定 run 目录而探测 Python、Bash 或执行其他 shell 命令；后续首次写入产物时自然创建目录。
- 已存在同阶段正式结果时默认停止并要求使用新 `runid`，不得静默覆盖；只有当前 workflow 内 review/coverage 返工才允许显式替换并沿用 `id-registry.json` 保持编号稳定。
- Office 输入归一化复用缓存写入 `outputs/input-cache/<sha256-12>/`；绑定既有 run 时写入 `outputs/runs/<run-id>/inputs/`。
- DOCX 图片、流程图、架构图、状态图、截图或 EMF/Visio 图形解析后的 Mermaid/结构化事实必须合并回同一个归一化 Markdown 的原文占位位置。
- DOCX 图片理解和 Mermaid 转换必须按原文顺序分批处理：普通图片每批最多 3-5 张，复杂图每批 1-2 张。

## 产物契约

- 测试分析主交付件固定为 `outputs/runs/<run-id>/deliverables/test-analysis-solution.json`，由 `bin/render-run-markdown.py` 渲染同名 `.md` 人读版。
- 测试设计主交付件固定为 `outputs/runs/<run-id>/deliverables/test-design-solution.json`，由 `test-case-writing` 调用 `bin/render-run-markdown.py` 渲染同名 `.md` 人读版；优先复用上游测试分析方案所在 run。
- 模型编写的语义过程件以 Markdown 为唯一事实源；只有分析/设计结果方案使用 JSON 作为阶段边界和跨 Agent 传递格式。结果 Markdown 可由 JSON 渲染。
- 脚本控制 JSON 只保留 `process/id-registry.json`、`process/test-point-work-items.json` 和 `process/test-case-work-items.json`。模型不得手工编辑这些控制文件，也不为它们渲染 Markdown 副本。
- 共享语义过程件固定为 `process/rules-pack.md`、`process/context-pack.md`、`process/input-fact-model.md` 和按需生成的 `process/testing-method-routing.md`。
- 测试分析先生成并评审 `process/scenario-tree.md`，再按叶子 SC 编写 `process/test-point-slices/<SC-ID>.md`，全部通过后一次性固化 `deliverables/test-analysis-solution.json`。
- 测试设计按每个已冻结 TP 编写 `process/test-case-slices/<TP-ID>.md`，全部通过后一次性固化 `deliverables/test-design-solution.json`。
- 过程 Markdown 不持久化 `generationContext`，不建立同名 JSON schema；需要的规则、动态来源和 FACT 在生成当前工作单元时按需读取。
- 工作项使用 `contentHash` 判断其 SC/TP 上游内容变化；变化项自动重开。review/coverage 返工使用 `bin/reopen-run-items.py` 重开受影响工作项，不能判定影响范围时保守重开全部。
- 测试分析和测试设计流程不得临时生成 `.py`、`.js`、`.ps1`、`.bat` 或其他可执行脚本处理切片、状态或返工；固定脚本能力不足时修改仓库 `bin/` 脚本并运行校验。
- 只有主结果交付件使用 schema `2.0`；过程 Markdown 不使用 JSON schema。
- 新 run 只支持 schemaVersion 2.0；历史 run 需要按新模型重新生成。

## Project/Personal 上下文

- 支持可选 `project-key`：确定后可扫描 `*/projects/<project-key>/**/*.md`；未唯一确定时不得读取所有项目目录正文。
- `rules/` 是强制规则源，按 `core / project / personal` 三层加载，由 `bin/build-rules-pack.py` 直接写入 `process/rules-pack.md`；后续阶段按其中的可用阶段读取对应规则正文。
- `project` 和 `personal` knowledge 是当前 run 的动态补充输入源，由 `context-source-indexing` 在 `process/context-pack.md` 中记录绑定结果和动态来源索引。
- 优先级分两层理解：workflow、skill、schema 和固定脚本定义运行时执行契约；业务与输出约束按 `当前用户明确指令 > rules > 当前输入文档 > project/personal knowledge > core knowledge` 处理。
- `knowledge/projects/<project-key>/` 和 `knowledge/user/` 只能作为测试知识补充，不得覆盖根目录 `knowledge/` 的核心标准、字段和质量门禁。
- 动态来源必须声明 `name`、`description`，可选 `stages`；未配置 `stages` 时默认全部阶段可用。
- `context-source-indexing` 只读取 project/personal knowledge 动态来源 frontmatter 生成 Markdown 索引，不扫描 rules，不扫描 core 层，不摘录正文，也不替后续阶段判断具体命中。
- 后续 skill 只读取 Markdown 索引中对本阶段可见的文件正文，并输出应用状态。

## 主流程

- 当用户要求把 `.docx` / `.xlsx` / `.md` 输入整理为可供下游读取的 Markdown 输入事实源时，使用 `@file-normalization-agent`。
- 当用户要求基于需求和设计方案生成测试场景、测试点粒度的方案时，使用 `test-analysis-workflow`。该 workflow 只接受 Markdown 输入；Office 输入必须先归一化。
- 当用户要求从需求和设计方案一次性完成测试分析与测试设计时，使用 `test-analysis-design-workflow`。该 workflow 优先用独立 subagent 隔离执行 analysis/design，只做全流程编排和阶段交接，不复制 analysis/design 内部校验、review、coverage 或 final-report 逻辑；若运行环境不支持真实 subagent，才 fallback 为同会话 workflow 串联并在最终回复说明。
- 测试分析阶段依次生成 rules/context/FACT/method Markdown、冻结 SC Markdown、逐叶子 SC 编写并评审 TP Markdown 切片，再一次性固化分析 JSON，完成整体评审、coverage Markdown、最终报告 Markdown 和固定检查。
- 分段工作项状态查看、切片初始化、完成、重开和固定检查分别使用 `bin/list-staged-work-items.py`、`bin/init-staged-slices.py`、`bin/complete-staged-items.py`、`bin/reopen-run-items.py` 和 `bin/check-staged-run.py`。
- 同一输出目录不得由多个执行者并发写入；目录选择和协作协调由当前 workflow 负责。
- 覆盖证据过程件分别为 `process/analysis-fact-coverage-map.md` 和 `process/design-fact-coverage-map.md`；覆盖审查分别为 `process/reviews/analysis-coverage-review.md` 和 `process/reviews/design-coverage-review.md`。
- coverage-review 发现缺口后，必须在 Markdown 表格中定位到 TP/TC 切片，并用 `reopen-run-items.py` 重开工作项；修复切片、重新评审和重新固化结果后再更新覆盖文件。
- 最终审阅报告分别为 `reports/analysis-final-report.md` 和 `reports/design-final-report.md`。final-report 只展示已审查覆盖关系，不生成 JSON、不新增缺口判断、不触发返工。
- 当用户要求基于已评审测试分析方案生成测试用例时，使用 `test-design-workflow`。该 workflow 优先使用用户显式指定的 `test-analysis-solution.json`，否则只读取当前 run 已存在的 `deliverables/test-analysis-solution.json`。
- 测试设计阶段使用 `test-design-solution-generation` 按 TP 编写 TC Markdown 切片，评审通过后由完成脚本更新 work-items；全部完成后通过 `finalize-deliverable.py` 一次性固化结果 JSON 和稳定 TC 编号。
- 测试设计 coverage-review 闭环后由 `final-report-generation` 直接生成 `reports/design-final-report.md`。
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

## 校验命令分层

### 单次业务 run 校验

- 单次 run JSON 结构：`python bin/lint-run-json.py outputs/runs/<run-id>`
- 单次 run Markdown 渲染一致性：`python bin/render-run-markdown.py outputs/runs/<run-id> --check`
- 测试分析方案结构：`python bin/lint-test-analysis-solution.py <solution.md>`
- 测试设计方案结构：`python bin/lint-test-design-solution.py <solution.md>`
- 单次 run 一致性：`python bin/check-artifact-consistency.py outputs/runs/<run-id>`

### 仓库开发校验

以下命令只在当前任务修改了 Agent 或 Skill 时按变更范围执行，不属于测试分析/设计业务 run：

- Skill 阶段契约：`python bin/lint-skill-step-contract.py`
- OpenCode/TestAgent skill 镜像：`python bin/sync-opencode-skills.py --check`
