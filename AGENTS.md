# Testcase Title Outline Agent 项目规则

本仓库是一个独立维护的测试用例标题大纲 Agent 包。它面向需求文档和可选设计方案文档生成 `测试用例标题大纲`，不依赖其他 Agent 项目、旧插件链路或外部仓库结构。

主输出粒度为：

```text
测试场景 -> 测试点 -> 测试用例标题项
```

本 Agent 不生成完整测试用例，不输出前置步骤、测试步骤、完整预期结果或自动化脚本。

## 运行入口

- Claude Code 使用 `.claude-plugin/plugin.json` 和根目录 `skills/`。
- OpenCode 使用 `opencode.json`、`AGENTS.md`、`.opencode/commands/` 和 `.opencode/skills/`。
- 主流程入口是 `skills/analyze-requirement-testcase-outline/SKILL.md`。
- 不要重新引入插件级 `agents/`；角色化行为应放在 skills、knowledge 文件、templates 或 quality gates 中。

## Skill 事实源

- `skills/` 是唯一手工维护的 skill 源。
- `.opencode/skills/` 是供 OpenCode 发现 skill 的生成镜像。
- 修改任何 `skills/*/SKILL.md` 后，运行 `python bin/sync-opencode-skills.py`。
- 修改运行时 wiring 后，运行 `python bin/validate-agent-runtime.py`。

## 路径规则

- 所有 `skills/...`、`knowledge/...`、`templates/...`、`quality-gates/...`、`memory/...`、`bin/...` 和 `outputs/...` 路径都从仓库根目录解析。
- 不要基于 skill 目录、`.claude-plugin/`、`.opencode/` 或输入文件目录解析路径。
- 运行产物写入 `outputs/runs/<run-id>/`。
- 主交付件固定为 `outputs/runs/<run-id>/deliverables/testcase-title-outline.md`。
- 创建 run 目录后必须维护 `process/task-list.md`；它是阶段顺序和状态的流程事实源。

## Project/Personal 上下文

- 支持可选 `project-key`：确定后可扫描 `*/projects/<project-key>/**/*.md`；未唯一确定时不得读取所有项目目录正文。
- `project` 和 `personal` 是当前 run 的一等输入源：必须在 `process/context-pack.md` 中记录绑定结果、命中来源、未采用来源和补读建议。
- `knowledge/projects/<project-key>/` 和 `knowledge/user/` 只能作为测试知识补充，不得覆盖根目录 `knowledge/` 的核心标准、字段、类型、级别和质量门禁。
- personal 层只能补充个人偏好和本地检查关注点，不得作为项目事实或团队共识。

## 主流程

- 当用户要求基于需求和设计方案生成测试场景、测试点、测试用例标题粒度的大纲时，使用 `analyze-requirement-testcase-outline`。
- 阶段性动作依次使用 `memory-context-builder`、`requirement-testability`、`clarification-gate`、`testing-method-router`、路由选中的专项分析 skills、`testpoint-generation`、`testcase-title-outline-generation` 和 `coverage-review`。
- 设计方案输入用于补充接口、字段、状态、权限、数据依赖、配置开关、异常处理和非功能指标；没有设计方案时继续生成，并把设计缺口写入待确认信息。
- 不编造业务事实、状态、角色、接口契约、阈值、错误码或测试数据。
- 在认为报告完成前，运行 `bin/` 下的确定性检查。

## 校验命令

- Runtime wiring：`python bin/validate-agent-runtime.py`
- OpenCode skill 镜像：`python bin/sync-opencode-skills.py --check`
- 标题大纲结构：`python bin/lint-testcase-title-outline.py <outline.md>`
- 示例输出 smoke 检查：`python bin/smoke-test-analysis.py`
