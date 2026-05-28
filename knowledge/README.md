# Knowledge 模块说明

Knowledge 保存本 Agent 稳定、可复用的测试分析与测试设计知识。主流程默认只读取 core、project 和 user 三层知识。

## 分层结构

| 层级 | 路径 | 默认提交 Git | 主流程默认读取 | 说明 |
|---|---|---|---|---|
| core | `knowledge/*.md`、`knowledge/test-techniques/**/*.md` | 是 | 是 | 测试设计方案生成所需的稳定标准、方法论和测试技术 |
| project | `knowledge/projects/<project-key>/**/*.md` | 否 | 按需 | 项目级风险画像、覆盖策略、术语映射和测试启发 |
| user | `knowledge/user/**/*.md` | 否 | 按需 | 个人测试启发、检查清单和本地关注点 |

## Core 知识归类

| 分类 | 文件或目录 | 用途 |
|---|---|---|
| 方法论层 | `test-analysis-methodology.md` | 定义稳定术语、测试分析、测试设计、测试技术和非完整用例输出边界 |
| 标准层 | `testpoint-standard.md`、`test-design-solution-standard.md`、`basic-test-types.md` | 定义测试点字段、测试设计项字段、预期结果兜底、类型和非用例化标准 |
| 路由与证据层 | `test-method-routing-matrix.md`、`method-evidence-standard.md` | 定义测试技术路由和方法证据要求 |
| 测试技术层 | `test-techniques/` | 同时支持测试分析和测试设计：分析层识别测试条件、覆盖项和风险；设计层把测试点扩展成代表性条件、数据、状态或组合 |

覆盖检查、专家评分和追踪检查属于 `quality-gates/`，不再作为 `knowledge/` 根节点知识维护。

## Project / User 边界

项目化 knowledge 可以补充当前项目的测试分析策略，但不得覆盖根目录中的核心标准：

- 不覆盖测试点字段、类型、方法和交付件契约。
- 不覆盖质量门禁、输出结构和固定运行目录规则。
- 不保存未确认业务事实、临时用户偏好或单次运行结果。
- 不替代 `memory/projects/<project-key>/` 中的项目事实和历史经验。

## 发现规则

`memory-context-builder` 确定 `project-key` 后，会按需扫描 `knowledge/projects/<project-key>/**/*.md`；同时会扫描 `knowledge/user/**/*.md`。只有与当前需求直接相关的片段会写入 `process/context-pack.md`。未确定 `project-key` 时，不读取所有项目目录正文。
