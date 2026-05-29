---
name: memory-context-builder
description: 每次需求分析开始前使用，用于从精简 memory 中选择相关项目上下文和测试经验，生成紧凑的本次上下文包，避免长期 memory 全量注入。
---

# 记忆上下文构建 Skill

本 skill 在每次分析开始时使用，目标是为当前需求挑选最相关的项目语境、项目测试经验、个人偏好和本地检查关注点。project 与 personal 不是可有可无的“附加资料”，而是当前 run 的一等输入源；即使没有命中正文，也必须记录绑定、扫描、未采用原因和项目知识阶段绑定。

## 输入

- 需求文档路径、需求标题和主入口解析出的 `PROJECT_ROOT`。
- 可选 `project-key`：来自用户显式参数、需求文档 frontmatter 或唯一匹配的项目目录名。
- `memory/project-memory.md`，包括全局项目事实、全局约束和输出偏好。
- 自动扫描得到的、与当前需求匹配的 `memory/domains/*.md` 业务域分片。
- `memory/testing-experience-memory.md`。
- 自动扫描得到的、与 `project-key` 匹配且与当前需求相关的 `memory/projects/<project-key>/**/*.md` 项目化 memory。
- 自动扫描得到的、与 `project-key` 匹配的 `knowledge/projects/<project-key>/**/*.md` 项目化知识补充；先做阶段绑定，再按当前需求相关性摘录片段。
- 可选 `personal-key`：来自用户显式参数、当前运行者配置或默认个人配置；personal 目录为 `*/user/`，后续可扩展为 `*/user/<personal-key>/`。
- 自动扫描得到的、与当前需求相关的 `memory/user/**/*.md` 和 `knowledge/user/**/*.md` personal 补充。
- 自动扫描得到的、与当前需求相关的 `templates/projects/<project-key>/**/*.md`、`templates/user/**/*.md`、`quality-gates/projects/<project-key>/**/*.md` 和 `quality-gates/user/**/*.md` 本地附加配置。
- `templates/context-pack-template.md`。

## 三层配置模型

配置按 `core / project / personal` 三层处理：

| 层级 | 路径 | 是否默认提交 Git | 作用 |
|---|---|---|---|
| core | `knowledge/*.md`、`memory/*.md`、`templates/*.md`、`quality-gates/*.md` | 是 | Agent 包随附的稳定标准、模板和基础规则 |
| project | `*/projects/<project-key>/**/*.md` | 否 | 当前项目的事实、经验、风险画像、覆盖策略和附加门禁 |
| personal | `*/user/**/*.md`，后续可扩展为 `*/user/<personal-key>/**/*.md` | 否 | 当前使用者的个人偏好、检查清单和本地补充 |

`project` 和 `personal` 层默认由 `.gitignore` 忽略，只保留各目录 README。团队确实需要共享某个项目配置时，可以显式强制添加，但本流程不要求提交。

## 渐进式披露协议

本 skill 是 project/personal 配置的唯一常规发现入口，必须按渐进式披露使用长期资料：

| 层级 | 读取内容 | 使用场景 |
|---|---|---|
| L0 来源发现 | 目录名、文件名、README、frontmatter、标题和 Markdown 标题结构 | 判断 `project-key`、候选领域和可能相关文件 |
| L1 摘要命中 | 标题、适用范围、关键词、章节名和短摘要 | 判断是否需要摘录正文；对 project knowledge 文件判断强制应用环节 |
| L2 片段摘录 | 与当前需求直接相关的段落、表格行或章节摘要 | 写入 `context-pack.md`，供后续 skill 默认使用 |
| L3 按源补读 | 后续 skill 根据 context pack 中的来源文件或明确需求缺口读取对应文件的相关章节 | 补足专项分析，不刷新 context pack |

超过 50KB 的 project/personal Markdown 视为大文件，不得在 context pack 中全量注入。大文件不强制维护索引文件；需要先看文件名、frontmatter、目录、标题结构或章节标题，再按当前需求命中的标题、关键词或表格片段读取必要内容。

`context-pack.md` 必须记录已检索来源、已注入片段、未注入但可能相关的来源和建议补读范围。后续 skill 如发现上下文不足，可以按这些来源进行受控补读；补读结果直接进入该 skill 的方法证据、风险备注或过程报告，不要求刷新 context pack。

context pack 对 project/personal 的记录必须满足四个要求：

- 绑定可见：记录 `project-key`、`personal-key` 或无法确定的原因。
- 来源可见：记录已扫描、命中、未采用和未扫描的 project/personal 来源。
- 证据可追溯：每个摘录片段必须保留来源文件、命中原因和使用方式。
- 后续可补读：大文件或未注入内容必须给出可控补读范围，而不是要求后续阶段重新全目录搜索。

## Project Knowledge 阶段绑定

`knowledge/projects/<project-key>/**/*.md` 中的文件不要求固定文件名，也不要求固定 Markdown 结构。推荐使用可读文件名，例如 `test-design-factors.md`、`test-design-patterns.md`、`test-design-checklist.md`、`risk-profile.md`、`oracle-heuristics.md` 或 `routing-notes.md`，但这些不是硬性要求。

本 skill 必须基于文件名、frontmatter、一级/二级标题、章节标题和少量开头摘要自理解识别文件用途，只做“应该强制进入哪些环节”的阶段绑定，不提前判断具体测试点或测试点明细是否命中。

常见自理解规则：

| 文件意图 | 识别信号 | 强制应用环节 | 使用目的 |
|---|---|---|---|
| 测试设计因子库/业务测试设计模式库 | 文件名或标题包含 `factor`、`pattern`、`测试设计因子`、`测试设计模式`、`覆盖因子`、`业务模式` | `testing-method-router`、`testpoint-generation`、`test-analysis-solution-generation`、`test-design-solution-generation` | 增强测试技术路由、补充测试点明细，并在设计阶段生成代表性条件、数据、状态或组合 |
| 测试设计 Checklist/检查清单 | 文件名或标题包含 `checklist`、`check-list`、`检查清单`、`评审清单`、`验收检查` | `test-analysis-solution-review`、`test-design-solution-review`、`coverage-review` | 独立评审和覆盖审查时强制查漏 |
| 风险画像/历史高风险策略 | 文件名或标题包含 `risk`、`风险`、`缺陷高发`、`风险画像` | `testing-method-router`、`risk-based-test-analysis`、`testpoint-generation`、`coverage-review` | 调整方法选择、风险测试点和覆盖深度 |
| Oracle/判定启发 | 文件名或标题包含 `oracle`、`判定`、`预期结果`、`结果依据` | `testpoint-generation`、`test-analysis-solution-generation`、`coverage-review` | 补充可观察结果和预期结果依据 |
| 路由说明/覆盖策略 | 文件名或标题包含 `routing`、`route`、`coverage`、`路由`、`覆盖策略` | `testing-method-router`、`testpoint-generation`、`coverage-review` | 约束测试技术选择和覆盖审查 |
| 术语表/领域词表 | 文件名或标题包含 `glossary`、`term`、`术语`、`词表` | `requirement-testability`、`design-solution-extraction`、`testpoint-generation` | 统一业务术语解释，不作为业务事实覆盖需求 |

无法自理解识别用途的 project knowledge 文件必须记录为 `unclassified`，写入后续补读建议；除非用户或文件 frontmatter 明确指定适用环节，否则不强制绑定到生成或审查环节，避免把未知资料硬套进流程。

context pack 必须输出“项目知识阶段绑定”表。后续被绑定的 skill 在开始本阶段活动前必须读取对应文件的相关章节，输出应用状态，并在方法证据、过程报告或覆盖审查中记录来源。应用状态只能是：

- `applied`：已应用到路由、测试点、测试点明细、预期结果依据或检查结论。
- `not_applicable`：已读取，但本需求/当前测试点不适用，并说明原因。
- `insufficient_evidence`：文件提供了启发，但需求或设计方案依据不足，只能生成过程缺口或 `待人工分析确认`。
- `conflict_with_requirement`：与需求或设计方案冲突，以当前需求/设计为准并记录冲突。
- `deferred_to_review`：生成阶段只登记，留给独立评审或覆盖审查处理。

## 项目标识发现

`project-key` 是可选项目标识，只用于发现项目化配置文件，不用于反推或修正 `PROJECT_ROOT`。

按以下顺序确定 `project-key`：

1. 用户在命令参数或当前请求中显式提供 `--project <project-key>`、`project=<project-key>` 或“项目：<project-key>”。
2. 需求 Markdown frontmatter 中存在 `project` 或 `project_key`。
3. `memory/projects/` 或 `knowledge/projects/` 下存在唯一目录名，且该目录名、目录 README、项目标题或关键词与需求标题、模块或正文显式匹配。

如果无法唯一确定项目，继续使用全局 `memory/` 和 `knowledge/`，不要扫描所有项目目录正文；只在 context pack 的“待确认候选”中记录项目归属不明确。

## 个人配置发现

personal 层用于表达当前使用者的输出偏好、个人检查清单和本地测试启发，不能作为项目事实或团队共识。

按以下顺序确定 `personal-key`：

1. 用户在命令参数或当前请求中显式提供 `--personal <personal-key>`、`personal=<personal-key>` 或“个人：<personal-key>”。
2. 当前运行环境或个人配置中存在稳定使用者标识。
3. 未提供时使用默认 personal 配置，扫描默认 personal 路径 `*/user/**/*.md`。

如果未来存在 `*/user/<personal-key>/` 子目录，优先扫描该子目录；否则继续使用 `*/user/**/*.md`。无法确定 `personal-key` 不阻断运行，但必须在 context pack 中记录为默认 personal。

## 选择规则

先读取 core 层的 `memory/project-memory.md`，再自动扫描 `memory/domains/*.md` 业务域分片并跳过 `README.md`。如果已确定 `project-key`，继续扫描 project 层的 `memory/projects/<project-key>/**/*.md`、`knowledge/projects/<project-key>/**/*.md`、`templates/projects/<project-key>/**/*.md` 和 `quality-gates/projects/<project-key>/**/*.md`。最后扫描 personal 层的 `memory/user/**/*.md`、`knowledge/user/**/*.md`、`templates/user/**/*.md` 和 `quality-gates/user/**/*.md`。所有扫描都跳过各级 `README.md` 正文，但可使用 README 的标题、目录结构和说明作为 L0 元信息。

全局分片和项目分片都不需要在 `project-memory.md` 中登记。根据文件名、标题、适用范围、关键词、领域术语、角色、接口、状态、数据对象和以下内容选择相关片段：

- 需求模块、产品区域、用户角色或业务对象。
- 需求中出现的领域术语。
- 需求中出现的接口、数据对象、状态、配置、规则或设计约束。
- 与相同流程、状态、权限、接口或数据对象相关的历史缺陷或反馈教训。
- 团队明确表达过的输出偏好。
- 关于测试点粒度或措辞的反馈教训。
- 项目化 knowledge 中声明的项目风险画像、覆盖策略、术语映射、路由补充、测试 oracle、测试设计因子、测试设计模式或测试设计 checklist 补充。
- personal 层中声明的个人输出偏好、本地检查清单或测试启发。

## 匹配与裁剪规则

- 优先纳入与当前需求标题、模块、角色、业务对象、接口、状态、数据对象直接命中的片段。
- 文件名或标题命中但正文无关时，只记录命中原因，不摘取无关正文。
- 大文件只通过文件名、frontmatter、标题结构、关键词或明确的补读需求定位片段；不得把整份大文件复制进 context pack。
- 同一事实在多个 memory 文件中重复出现时，只保留更具体、更新或适用范围更窄的一条。
- 项目化 memory 优先于全局 memory；当前需求文档中的明确规则优先于任何 memory。
- 项目化 knowledge 只能补充项目风险、术语、覆盖策略、测试 oracle、测试设计因子、测试设计模式和 checklist，不得覆盖 `knowledge/` 根目录中的核心类型、字段、级别、交付件契约和质量门禁。
- `memory/project-memory.md` 中的全局高优先级规则始终纳入，但不得把整份文件原样复制进 context pack。
- `memory/domains/*.md` 中的用户扩展内容按片段引用；每个片段必须保留来源文件名和命中原因。
- `memory/projects/<project-key>/**/*.md`、`knowledge/projects/<project-key>/**/*.md`、`templates/projects/<project-key>/**/*.md` 和 `quality-gates/projects/<project-key>/**/*.md` 中的内容按片段引用；每个片段必须保留项目标识、来源文件和命中原因。
- `memory/user/**/*.md`、`knowledge/user/**/*.md`、`templates/user/**/*.md` 和 `quality-gates/user/**/*.md` 中的内容按片段引用；每个片段必须保留 personal 层来源文件和命中原因。
- personal 层只能补充个人偏好和本地检查关注点，不得覆盖当前用户明确指令、需求文档、project memory、core 输出契约或 core/project 质量门禁。
- 冲突裁剪按信息类型处理：事实/契约以当前需求和 project memory 为准；测试策略以 project knowledge 优先于 personal knowledge；输出偏好以当前用户指令优先于 personal，再优先于 project，但不得违反事实、交付件契约或门禁。
- `memory/testing-experience-memory.md` 只摘取与当前需求的方法选择、风险模式、输出反馈直接相关的经验。
- 如果相关性无法判断，宁可少量摘要并登记待确认候选，也不要全量注入。

## 输出

创建或刷新 `${PROJECT_ROOT}/outputs/runs/<run-id>/process/context-pack.md`，包含：

- 与本次需求相关的项目背景。
- 本次使用的 `project-key`，或未确定项目时的原因。
- 本次使用的 `personal-key`，或默认 personal 配置说明。
- 已扫描来源和未采用来源。
- project/personal 来源使用摘要，包括命中来源、未采用来源、冲突处理和补读建议。
- 领域术语片段。
- 相关业务域分片和命中原因。
- 相关项目化 knowledge 补充、阶段绑定和命中原因。
- 相关 personal 偏好或本地检查补充和命中原因。
- 历史缺陷和风险模式。
- 已确认的项目测试经验。
- 输出偏好。
- 约束和非范围。
- memory 待确认候选问题，仅限业务域命中冲突或 memory 与当前需求明显冲突的情况。
- 可能需要后续按源补读的文件、章节或关键词。

建议使用以下结构：

| 章节 | 内容 |
|---|---|
| 本次需求标识 | 需求文件、标题、run-id |
| 项目标识 | project-key、确定依据、无法确定时的原因 |
| 个人配置标识 | personal-key、确定依据、默认 personal 说明 |
| 已扫描来源 | 全局 memory、项目 memory、项目 knowledge、personal 补充的文件清单 |
| 命中摘要 | 命中的 memory 文件、片段和原因 |
| Project/Personal 使用摘要 | project/personal 的命中、未采用、冲突处理和补读建议 |
| 项目知识阶段绑定 | project knowledge 文件的自理解类型、强制应用环节、读取策略和留痕要求 |
| 项目事实 | 影响测试分析的已确认事实 |
| 业务术语 | 当前需求会用到的项目特有术语 |
| 项目知识补充 | 当前项目适用的风险画像、覆盖策略、术语映射或 oracle 补充 |
| 个人补充 | 当前使用者适用的输出偏好、本地检查清单或测试启发 |
| 大文件来源 | 命中的大文件、标题结构、建议补读章节和未注入原因 |
| 后续补读建议 | 后续阶段如上下文不足时可读取的文件、章节、关键词和原因 |
| 设计约束 | 会影响测试点生成的项目约束 |
| 历史经验 | 相关缺陷、风险模式和输出反馈 |
| 非范围 | 本次不应套用的 memory |
| 待确认候选 | 仅记录 memory 冲突或业务域归属冲突 |

## 约束

- 不把所有业务域分片全量注入 context pack；可以扫描文件元信息和标题结构，但只摘取与本次需求相关的片段。
- 新增 `memory/domains/*.md` 分片无需登记索引；但分片内容必须自带清晰的标题、适用范围、关键词或术语，便于自动匹配。
- 新增 `*/projects/<project-key>/**/*.md` 和 `*/user/**/*.md` 文件无需登记索引；project 目录名必须是稳定的 `project-key`。project knowledge 文件名不作硬性要求，但文件名、标题、frontmatter 或开头摘要应能让 Agent 自理解识别用途和适用环节。
- 超过 50KB 的 project/personal Markdown 不要求提供索引文件，但 context pack 只能记录来源、命中原因、标题结构或少量摘录，不得整文件注入。
- 未确定 `project-key` 时，不得全量读取所有项目目录正文，避免跨项目污染。
- 不把 `knowledge/` 中已有的通用测试理论复制进 context pack。
- 不把项目化 knowledge 当作项目事实；事实性业务规则仍应来自需求或已确认 memory。
- 不把 personal 层内容当作项目事实或团队共识。
- context pack 保持简洁、相关、有依据。
- 不把 `context-pack.md` 作为“最新全局上下文”复用给后续任务；后续任务必须重新按需求筛选或显式复用当前 run。
- 未经用户明确确认，不更新 memory 源文件。
- 本 skill 不直接向用户提问；只向 `clarification-gate` 提供候选。
- 后续 skill 如果发现 context pack 不足，可以读取 context pack 中列出的对应来源文件或当前需求明确指向的 project/personal 文件；读取时必须限定到相关标题、章节、关键词或表格片段，并在方法证据或过程报告中记录来源，不得自行全目录搜索或全量复制大文件。
- `process/context-pack.md` 是当前 run 的运行产物，不写入 `memory/`，也不作为长期 memory 源文件。
- 不允许在 skill 文件目录、插件缓存目录或 `.claude-plugin/` 目录下创建 `outputs/runs/`。
