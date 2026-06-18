# Knowledge 模块说明

Knowledge 保存本 Agent 稳定、可复用的测试分析与测试设计知识。主流程默认只读取 core、project 和 user 三层知识。Knowledge 是方法、标准和启发来源，不是强制规则源；必须优先于输入文档执行的约束应放在 `rules/`。

## 分层结构

| 层级 | 路径 | 默认提交 Git | 主流程默认读取 | 说明 |
|---|---|---|---|---|
| core | `knowledge/*.md`、`knowledge/test-techniques/**/*.md` | 是 | 是 | 测试分析方案和测试设计方案生成所需的跨 skill 稳定标准、方法论和公共测试技术 |
| project | `knowledge/projects/<project-key>/**/*.md` | 否 | 按需 | 项目级风险画像、覆盖策略、术语映射、测试设计因子/模式、checklist 和测试启发 |
| user | `knowledge/user/**/*.md` | 否 | 按需 | 个人测试启发、检查清单和本地关注点 |

## Core 知识归类

| 分类 | 文件或目录 | 用途 |
|---|---|---|
| 工作流边界层 | `test-workflow-boundaries.md` | 定义稳定术语、测试分析、测试设计和测试技术边界 |
| 标准层 | `testpoint-standard.md`、`test-analysis-solution-standard.md`、`test-design-solution-standard.md` | 定义 SC/TP/TC 字段、粒度、编号、追踪和保守预期标准 |
| 测试技术层 | `test-techniques/` | 同时支持测试分析和测试设计：分析层识别测试条件、覆盖项和风险；设计层把测试点扩展成测试用例 |

覆盖检查、专家评分和追踪检查不作为 `knowledge/` 根节点知识维护。覆盖检查、rubric 和深度检查标准统一归档到 `skills/coverage-review/references/`；确定性结构、编号、JSON/Markdown 一致性检查由 `bin/` 脚本负责。

只被单个 skill 使用的参考材料归档到对应 skill：

| 所属 skill | 文件或目录 | 用途 |
|---|---|---|
| `testing-method-router` | `skills/testing-method-router/references/test-method-routing-matrix.md` | 测试技术路由矩阵 |
| `testing-method-router` | `skills/testing-method-router/references/method-evidence-standard.md` | 方法参考记录字段和质量要求 |
| `coverage-review` | `skills/coverage-review/references/basic-test-types.md` | 覆盖审查使用的测试类型分类速查 |
| `coverage-review` | `skills/coverage-review/references/coverage-check.md` | 覆盖审查使用的覆盖门禁检查 |

## Project / User 边界

项目化 knowledge 可以补充当前项目的测试分析策略，但不得覆盖根目录中的核心标准：

- 不覆盖测试点字段、类型、方法和交付件契约。
- 不覆盖质量门禁、输出结构和固定运行目录规则。
- 不保存未确认业务事实、临时用户偏好或单次运行结果。
- 不保存必须优先于输入文档执行的强制规则；这类内容应放在 `rules/`。
- 不替代 `memory/projects/<project-key>/` 中的项目事实和历史经验。

## 发现规则

`context-source-indexing` 确定 `project-key` 后，只索引 `knowledge/projects/<project-key>/**/*.md` 的 frontmatter；同时索引 `knowledge/user/**/*.md`。未确定 `project-key` 时，不读取所有项目目录正文。

Project/User knowledge 文件名没有硬性要求，但动态来源文件必须声明 frontmatter：`name`、`description`，可选 `stages`。`stages` 未配置时默认所有阶段可用；配置后仅对应阶段读取正文并记录应用状态。
