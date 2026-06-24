# Test Analysis Agent 项目规则

本仓库是独立维护的测试分析与测试设计 Agent 包。它面向需求文档、可选设计方案文档和已评审测试分析方案生成 `测试分析方案` 或 `测试设计方案`，不依赖其他 Agent 项目、旧插件链路或外部仓库结构。

主输出粒度固定为：

```text
测试分析 Agent：测试场景 SC -> 测试点 TP
测试设计 Agent：测试场景 SC -> 测试点 TP -> 测试用例 TC
```

`SC-*` 是业务场景树，最多 3 层，例如 `SC-001`、`SC-001-001`、`SC-001-001-001`。只有叶子场景挂载 `TP-*`。`TP-*` 是验证目标、规则点、路径点、状态点、权限点、接口契约点或风险点，全局连续编号。`TC-*` 是可执行测试用例，包含前置条件、具体测试数据、步骤、步骤预期和最终预期，全局连续编号。

测试分析方案不输出测试用例、步骤、测试数据或预期结果。测试设计方案在每个测试点下输出完整步骤级测试用例。新 run 只允许 schemaVersion 2.0 定义的字段、编号和层级。

## 运行入口

- Claude Code 使用 `.claude-plugin/plugin.json`、根目录 `agents/` 和根目录 `skills/`。
- OpenCode 使用 `opencode.json`、`AGENTS.md`、`.opencode/agents/`、`.opencode/commands/` 和 `.opencode/skills/`。
- TestAgent/CodeArts 兼容入口使用 `codearts.json`、`.testagent/agents/`、`.testagent/commands/` 和 `.testagent/skills/`；`.testagent` 内容由同步脚本与 `.opencode` 保持一致。
- 用户主入口 Agent 包括 `@file-normalization-agent`、`@test-analysis-agent` 和 `@test-design-agent`。
- 文件归一化入口是 `agents/file-normalization-agent.md`，用于把 `.docx` / `.xlsx` / `.md` 输入整理为后续分析或设计可读取的 Markdown 输入事实源。
- 测试分析主流程 skill 入口是 `skills/test-analysis-workflow/SKILL.md`。
- 测试设计主流程 skill 入口是 `skills/test-design-workflow/SKILL.md`。
- 测试用例写作 skill 入口是 `skills/test-case-writing/SKILL.md`，用于把 canonical 测试设计 JSON 写作为标准 Markdown 或后续扩展的不同交付风格。
- OpenCode 独立文档归一化命令入口是 `.opencode/commands/normalize-input-documents.md`。
- Agent 门面负责用户意图识别和路由；具体流程动作仍放在 skills、knowledge、templates 或对应 skill 私有参考中。

## Agent 与 Skill 事实源

- `agents/` 是唯一手工维护的 Agent 门面源。
- `skills/` 是唯一手工维护的 skill 源。
- `.opencode/agents/`、`.opencode/skills/`、`.testagent/agents/` 和 `.testagent/skills/` 是生成镜像，不直接手工编辑。
- 修改任何 `agents/*.md`、`skills/*/SKILL.md` 或根目录 `codearts.json` 后，运行 `python bin/sync-opencode-skills.py`。
- 修改运行时 wiring 后，运行 `python bin/validate-agent-runtime.py`。

## 路径规则

- 所有 `skills/...`、`rules/...`、`knowledge/...`、`templates/...`、`memory/...`、`bin/...` 和 `outputs/...` 路径都从仓库根目录解析。
- 不要基于 skill 目录、`.claude-plugin/`、`.opencode/`、`.testagent/` 或输入文件目录解析路径。
- 运行产物写入 `outputs/runs/<run-id>/`。
- 新建完整 run 时，`run-id` 固定使用 `python bin/generate-run-id.py` 生成，格式为 `<YYYYMMDD-HHMMSS>`。
- Office 输入归一化复用缓存写入 `outputs/input-cache/<sha256-12>/`；绑定既有 run 时写入 `outputs/runs/<run-id>/inputs/`。
- DOCX 图片、流程图、架构图、状态图、截图或 EMF/Visio 图形解析后的 Mermaid/结构化事实必须合并回同一个归一化 Markdown 的原文占位位置。
- DOCX 图片理解和 Mermaid 转换必须按原文顺序分批处理：普通图片每批最多 3-5 张，复杂图每批 1-2 张。

## 产物契约

- 测试分析主交付件固定为 `outputs/runs/<run-id>/deliverables/test-analysis-solution.json`，由 `bin/render-run-markdown.py` 渲染同名 `.md` 人读版。
- 测试设计主交付件固定为 `outputs/runs/<run-id>/deliverables/test-design-solution.json`，由 `test-case-writing` 调用 `bin/render-run-markdown.py` 渲染同名 `.md` 人读版；优先复用上游测试分析方案所在 run。
- JSON 是 run 过程产物、主交付件、review 和 coverage 的事实源；Markdown 是脚本派生产物，不手工维护。
- 创建 run 目录后必须维护阶段化任务清单和共享过程产物：测试分析使用 `process/analysis-task-list.json/.md`，测试设计使用 `process/design-task-list.json/.md`；共享过程产物包括 `process/rules-pack.json/.md`、`process/context-pack.json/.md` 和 `process/input-fact-model.json/.md`。历史 `process/task-list.json/.md` 只作为兼容读取路径，不作为新流程写入目标。
- 当测试分析 JSON 大于 200KB、TP 数量大于 30 或已有测试设计 JSON 大于 300KB 时，必须使用固定分批脚本生成测试设计：`bin/check-design-batch-mode.py`、`bin/extract-design-work-items.py`、`bin/extract-analysis-slice.py`、`bin/init-design-slice.py` 和 `bin/merge-design-slice.py`；分批过程产物写入 `process/design-batch-decision.json`、`process/design-work-items.json` 和 `process/design-slices/`，最终事实源仍是 `deliverables/test-design-solution.json`。
- 测试设计流程不得临时生成 `.py`、`.js`、`.ps1`、`.bat` 或其他可执行脚本来处理 JSON；固定脚本能力不足时修改仓库 `bin/` 脚本并运行校验。
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
- 测试分析阶段依次使用 `rules-pack`、`context-source-indexing`、`input-fact-modeling`、`testing-method-router`、路由选中的专项方法参考、`test-analysis-solution-generation`、JSON lint、Markdown render、派生 Markdown lint、`test-analysis-solution-review` 和 `coverage-review`。
- 覆盖审查产物按阶段拆分：测试分析写入 `reports/analysis-coverage-review.json/.md`，测试设计写入 `reports/design-coverage-review.json/.md`；历史 `reports/coverage-review.json/.md` 只作为兼容读取路径，不作为新流程写入目标。
- 当用户要求基于已评审测试分析方案生成测试用例时，使用 `test-design-workflow`。该 workflow 优先读取上游 `test-analysis-solution.json`。
- 如果用户只提供需求/设计方案且要求测试设计，必须先生成或取得测试分析方案，再进入测试设计。
- 设计方案输入用于补充接口、字段、状态、权限、数据依赖、配置开关、异常处理和非功能指标；没有设计方案时继续生成，预期结果只写输入可支撑的保守判定。
- 不编造业务事实、状态、角色、接口契约、阈值、错误码、错误提示或状态变化。
- 每个叶子测试场景下必须包含一个 `E2E场景测试` 测试点，用于覆盖该场景端到端业务主流程是否按预期完整闭环。
- 接口测试或集成覆盖场景下的非 E2E `TP-*` 必须先按接口、端点、消息、回调或集成点组织；字段、状态码、错误码、鉴权、幂等、超时和重试作为该接口测试点的用例覆盖重点。
- 测试用例必须包含 `level`，取值为 `Level 0` 到 `Level 4`；`testData[]` 使用 `{name, value, description}` 数组；`steps[]` 使用 `{stepNo, action, expected}` 数组。
- 测试步骤的 `action` 只写可执行动作或取数动作；字段、状态、记录、事件、响应内容等检查要求写入对应 `expected`，不要把“检查响应体字段”这类检查项单独写成步骤。
- 接口类测试用例步骤或测试数据不得写完整裸 URL；必须拆成 `接口=METHOD /path`、`参数名=参数值`、`响应状态=...` 等字段片段。
- 确定性结构、编号、字段、JSON 结构、Markdown 语法和固定产物一致性问题以 Python 脚本为事实源；review 和 coverage 不重复执行脚本已覆盖的检查。

## 校验命令

- Runtime wiring：`python bin/validate-agent-runtime.py`
- OpenCode/TestAgent skill 镜像：`python bin/sync-opencode-skills.py --check`
- 单次 run JSON 结构：`python bin/lint-run-json.py outputs/runs/<run-id>`
- 单次 run Markdown 渲染一致性：`python bin/render-run-markdown.py outputs/runs/<run-id> --check`
- 测试分析方案结构：`python bin/lint-test-analysis-solution.py <solution.md>`
- 测试设计方案结构：`python bin/lint-test-design-solution.py <solution.md>`
- 单次 run 一致性：`python bin/check-artifact-consistency.py outputs/runs/<run-id>`
- 框架回归/示例 fixture smoke：`python bin/smoke-test-analysis.py`
