# Knowledge 模块说明

Knowledge 保存稳定测试知识、分析标准、测试设计模式、覆盖分类、测试类型、风险规则和专家审查规则。根目录下的 `*.md` 和 `testcase-design-patterns/` 是 core 层事实源，所有项目默认适用。

## 三层范围

| 层级 | 路径 | 是否默认提交 Git | 说明 |
|---|---|---|---|
| core | `knowledge/*.md` | 是 | Agent 包内置的稳定测试知识和标准 |
| project | `knowledge/projects/<project-key>/**/*.md` | 否 | 当前项目的风险画像、覆盖策略、术语映射、路由说明和 oracle 补充 |
| user | `knowledge/user/**/*.md` | 否 | 当前使用者的个人测试启发、检查清单和本地关注点 |

## 文件类型

- `*.md`：core 测试知识和标准，例如测试类型、测试点标准、测试用例标题大纲标准、方法路由矩阵、缺陷模式和专家规则。
- `testcase-design-patterns/`：本 Agent 内置的标题项设计模式库，用于把测试点扩展成测试用例标题项，不直接生成完整测试用例。
- `projects/<project-key>/**/*.md`：project 知识补充，例如项目风险画像、覆盖策略、术语映射、方法路由补充和测试 oracle 补充。
- `user/**/*.md`：user 知识补充，例如个人测试启发、检查清单和本地关注点。

## 项目化 Knowledge 边界

项目化 knowledge 可以补充当前项目的测试分析策略，但不得覆盖根目录中的核心标准：

- 不覆盖测试点字段、类型、方法、级别和交付件契约。
- 不覆盖质量门禁、输出结构和固定运行目录规则。
- 不保存未确认业务事实、临时用户偏好或单次运行结果。
- 不替代 `memory/projects/<project-key>/` 中的项目事实和历史经验。

## 发现规则

`memory-context-builder` 确定 `project-key` 后，会按需扫描 `knowledge/projects/<project-key>/**/*.md`；同时会扫描 `knowledge/user/**/*.md`。只有与当前需求直接相关的片段会写入 `process/context-pack.md`。未确定 `project-key` 时，不读取所有项目目录正文。
