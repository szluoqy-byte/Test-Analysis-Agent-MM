# Memory 模块说明

Memory 是 Agent 在多次需求分析/测试设计之间保留的、经人工确认的项目上下文、测试经验和个人本地偏好。它的目标是让测试分析方案和测试设计方案更贴近当前项目和当前使用者，而不是替代当前用户明确指令、rules、需求文档、设计方案、测试理论或专家知识库。

强制执行、禁止覆盖输入、优先级高于输入文档的内容不写入 `memory/`，应写入 `rules/`。

## 两层范围

| 层级 | 路径 | 是否默认提交 Git | 说明 |
|---|---|---|---|
| project | `projects/<project-key>/**/*.md` | 否 | 指定项目的事实、历史经验、团队反馈和输出偏好 |
| personal | `user/**/*.md` | 否 | 当前使用者的个人输出偏好、检查习惯和本地补充 |

## 文件

| 文件 | 定义 | 使用方式 |
|---|---|---|
| `projects/<project-key>/**/*.md` | 按项目隔离的项目事实、历史经验、团队反馈和输出偏好 | 确定 `project-key` 后自动扫描，按需注入；默认不提交 Git |
| `user/**/*.md` | 当前使用者的 personal 偏好、检查清单和本地记忆 | 自动扫描，按需注入；默认不提交 Git |

运行时上下文包不保存在 `memory/` 下；每次分析先将当前 Claude Code 会话工作目录固定为 `PROJECT_ROOT`，再写入 `${PROJECT_ROOT}/outputs/runs/<run-id>/process/context-pack.json`。同名 Markdown 只由 `bin/render-run-markdown.py` 渲染，供人工阅读。

## 运行产物

| 文件 | 定义 | 使用方式 |
|---|---|---|
| `${PROJECT_ROOT}/outputs/runs/<run-id>/process/context-pack.json` | 本次运行筛选出的相关 memory 摘要、来源绑定和补读建议 | 当前 run 内机器交互、注入和追溯 |
| `${PROJECT_ROOT}/outputs/runs/<run-id>/process/context-pack.md` | 由 `context-pack.json` 渲染的人读版 | 只用于人工查看，不作为后续 skill 的事实源 |

## 使用流程

1. `memory-context-builder` 先根据用户参数、输入 frontmatter 和项目目录元信息确定 `project-key`。
2. 如果能唯一确定 `project-key`，扫描 `projects/<project-key>/**/*.md`，跳过 `README.md`，并按片段选择相关项目化 memory。
3. 扫描 `user/**/*.md`，只选择与当前需求直接相关的 personal 偏好或本地检查关注点。
4. 只选择与本次需求直接相关的条目，生成 `${PROJECT_ROOT}/outputs/runs/<run-id>/process/context-pack.json`，再按需渲染同名 Markdown。
5. 后续需求分析、测试技术路由、测试分析方案生成、测试设计方案生成和覆盖审查默认读取当前 run 的 `context-pack.json`；如果上下文不足，可以按 context pack 记录的来源文件或当前需求明确指向的 project/personal 文件受控补读相关章节。
6. review/coverage JSON 或结构化过程记录给出“建议沉淀的 Memory 更新”。
7. 用户确认后，才把建议追加到对应项目化 memory 文件或 personal 本地文件。

## 写入边界

- 写入 memory 的内容必须有证据，来源可以是需求文档、用户反馈、评审结论或真实缺陷复盘。
- 强制规则不写入 memory；带有“必须/禁止/优先于输入/强制执行”语义的约束应写入 `rules/`。
- 通用测试理论、通用缺陷模式和通用级别定义不写入 memory，应放在 `knowledge/`。
- 框架术语不写入 memory，应放在 `knowledge/test-workflow-boundaries.md`；memory 只记录项目专属术语或业务域术语覆盖。
- 未确认的业务规则不写入 memory，应放在待确认问题。
- 单次运行的完整中间产物不写入 memory，应保存在 `outputs/`。
- 项目化 memory 不需要登记到全局索引；新增 `projects/<project-key>/**/*.md` 后会在项目命中时自动扫描。
- personal memory 不需要登记索引；新增 `user/**/*.md` 后会按需扫描，但只能作为个人偏好或本地检查补充。
- 无法唯一确定 `project-key` 时，不得读取所有项目目录正文；项目归属问题应进入过程缺口记录。
- personal 层不保存项目事实、团队共识和真实缺陷复盘；这些内容应进入 project memory 或待确认问题。
- 大文件不需要维护 `index.md`；但 context pack JSON 只能记录来源、标题结构、命中原因和少量摘录，后续阶段按需补读相关章节。
- `context-pack.json` 是运行产物，不是全局 memory 文件；`context-pack.md` 是派生阅读版。
- 不允许把运行产物写到 skill 文件目录、插件缓存目录或 `.claude-plugin/` 目录。
