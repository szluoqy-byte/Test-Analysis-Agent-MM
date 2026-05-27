# 运行任务清单模板

构建当前运行目录下的 `process/task-list.md` 时使用以下结构。任务清单是本次运行的流程控制产物，用于约束阶段顺序和记录每个阶段的证据路径。

```markdown
# 测试用例标题大纲任务清单

## 运行标识

- 需求文档：
- 设计方案文档：
- run-id：
- PROJECT_ROOT：
- 生成时间：

## 任务列表

| 序号 | 阶段 | 负责 skill | 必须产物/检查点 | 状态 | 证据/路径 |
|---|---|---|---|---|---|
| 1 | 固定 PROJECT_ROOT 与运行目录 | analyze-requirement-testcase-outline | outputs/runs/<run-id>/ | pending |  |
| 2 | 构建上下文包 | memory-context-builder | process/context-pack.md | pending |  |
| 3 | 需求可测性分析 | requirement-testability | 结构化需求模型、需求待确认候选 | pending |  |
| 4 | 设计方案提取 | design-solution-extraction | 设计方案事实摘要、接口/状态/字段/数据依赖清单 | pending |  |
| 5 | 待确认治理 | clarification-gate | CP-INPUT、CP-ANALYSIS、CP-REVIEW | pending |  |
| 6 | 测试技术路由 | testing-method-router | 分析维度覆盖表、测试技术路由表 | pending |  |
| 7 | 专项分析 | selected method skills | ME-* 方法证据、测试点候选、技术缺口候选 | pending |  |
| 8 | 按源补读 | selected method skills | 按需补读记录、来源说明 | skipped |  |
| 9 | 场景化测试点生成 | testpoint-generation | 场景、测试点、接口测试点 | pending |  |
| 10 | 测试用例标题大纲生成 | testcase-title-outline-generation | deliverables/testcase-title-outline.md | pending |  |
| 11 | 覆盖审查 | coverage-review | 门禁结果、专家评分、阻断项 | pending |  |
| 12 | 确定性校验 | coverage-review / bin | lint、consistency、semantic 检查结果 | pending |  |
| 13 | 输出收口 | analyze-requirement-testcase-outline | 主交付件路径、过程报告路径、最终待确认信息 | pending |  |

## 状态说明

- `pending`：尚未开始。
- `in_progress`：当前正在执行。
- `done`：已完成且有证据路径或阶段输出。
- `blocked`：因输出质量或需求缺口阻断，必须在最终待确认信息或过程报告中说明。
- `skipped`：当前需求不适用或未触发，必须说明原因。
```

## 维护规则

- 创建 run 目录后立即创建 `process/task-list.md`。
- 每个阶段开始前，将对应阶段置为 `in_progress`；阶段完成后置为 `done` 或 `skipped`。
- 任意时刻最多一个阶段处于 `in_progress`。
- 不依赖 Claude Code 或 OpenCode 的内置 todo 工具；如果运行时支持任务列表，可以同步维护，但 `process/task-list.md` 是流程事实源。
- 最终输出前，所有必选阶段必须是 `done`；可选阶段可以是 `skipped`，但必须说明原因。
