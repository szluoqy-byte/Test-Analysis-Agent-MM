# Test Design Solution Agent 项目规则

本仓库是一个独立维护的测试设计方案 Agent 包。它面向需求文档和可选设计方案文档生成 `测试设计方案`，不依赖其他 Agent 项目、旧插件链路或外部仓库结构。

主输出粒度为：

```text
测试场景 -> 测试点 -> 测试设计项
```

本 Agent 不生成完整测试用例，不输出前置步骤、测试步骤、自动化脚本或可执行测试数据清单。`测试设计项` 的核心是说明用哪些代表性条件、数据、状态或组合覆盖测试点，并给出基于需求/设计方案可确认的 `预期结果`。

主交付件术语与缩写固定为：测试场景 `SC-*`、测试点 `TP-*`、测试设计项 `TDI-*`。主交付件不展开英文全名，不使用 `TD-*`、`TC-*`、`TCT-*`、`TI-*`、`ITP-*` 或 `ITDI-*`。

## 运行入口

- Claude Code 使用 `.claude-plugin/plugin.json`、根目录 `agents/` 和根目录 `skills/`。
- OpenCode 使用 `opencode.json`、`AGENTS.md`、`.opencode/agents/`、`.opencode/commands/` 和 `.opencode/skills/`。
- 用户主入口 Agent 是 `@test-analysis-agent`，源文件是 `agents/test-analysis-agent.md`。
- 主流程 skill 入口仍是 `skills/analyze-requirement-test-design-solution/SKILL.md`。
- Agent 门面负责用户意图识别和路由；具体流程动作仍放在 skills、knowledge 文件、templates 或 quality gates 中。

## Agent 与 Skill 事实源

- `agents/` 是唯一手工维护的 Agent 门面源。
- `skills/` 是唯一手工维护的 skill 源。
- `.opencode/agents/` 是供 OpenCode 发现 Agent 的生成镜像。
- `.opencode/skills/` 是供 OpenCode 发现 skill 的生成镜像。
- 修改任何 `agents/*.md` 或 `skills/*/SKILL.md` 后，运行 `python bin/sync-opencode-skills.py`。
- 修改运行时 wiring 后，运行 `python bin/validate-agent-runtime.py`。

## 路径规则

- 所有 `skills/...`、`knowledge/...`、`templates/...`、`quality-gates/...`、`memory/...`、`bin/...` 和 `outputs/...` 路径都从仓库根目录解析。
- 不要基于 skill 目录、`.claude-plugin/`、`.opencode/` 或输入文件目录解析路径。
- 运行产物写入 `outputs/runs/<run-id>/`。
- 主交付件固定为 `outputs/runs/<run-id>/deliverables/test-design-solution.md`。
- 创建 run 目录后必须维护 `process/task-list.md`；它是阶段顺序和状态的流程事实源。

## Project/Personal 上下文

- 支持可选 `project-key`：确定后可扫描 `*/projects/<project-key>/**/*.md`；未唯一确定时不得读取所有项目目录正文。
- `project` 和 `personal` 是当前 run 的一等输入源：必须在 `process/context-pack.md` 中记录绑定结果、命中来源、未采用来源和补读建议。
- `knowledge/projects/<project-key>/` 和 `knowledge/user/` 只能作为测试知识补充，不得覆盖根目录 `knowledge/` 的核心标准、字段、类型和质量门禁。
- `knowledge/projects/<project-key>/` 下的文件名没有硬性要求；`memory-context-builder` 必须自理解识别文件用途并在 `context-pack.md` 记录项目知识阶段绑定。被绑定到某阶段的文件，该阶段必须读取并输出应用状态。
- personal 层只能补充个人偏好和本地检查关注点，不得作为项目事实或团队共识。

## 主流程

- 当用户要求基于需求和设计方案生成测试场景、测试点、测试设计项粒度的方案时，使用 `analyze-requirement-test-design-solution`。
- 阶段性动作依次使用 `memory-context-builder`、`requirement-testability`、`design-solution-extraction`、`clarification-gate`、`testing-method-router`、路由选中的专项分析 skills、`testpoint-generation`、`test-design-solution-generation`、`test-design-solution-review` 和 `coverage-review`。
- 设计方案输入用于补充接口、字段、状态、权限、数据依赖、配置开关、异常处理和非功能指标；没有设计方案时继续生成，并把缺口沉淀到过程澄清记录或单条预期结果的 `待人工分析确认`。
- 不编造业务事实、状态、角色、接口契约、阈值、错误码、错误提示、状态变化或测试数据。
- 如果需求和设计方案没有说明错误提示、状态变化、错误码或其他判定依据，相关测试设计项的 `预期结果` 写 `待人工分析确认`。
- 主交付件不设置独立的 `未明确规则` 章节，也不输出待确认信息清单；澄清和缺口治理保留在过程产物中。
- 在认为报告完成前，运行 `bin/` 下的确定性检查。

## 校验命令

- Runtime wiring：`python bin/validate-agent-runtime.py`
- OpenCode skill 镜像：`python bin/sync-opencode-skills.py --check`
- 测试设计方案结构：`python bin/lint-test-design-solution.py <solution.md>`
- 示例输出 smoke 检查：`python bin/smoke-test-analysis.py`
