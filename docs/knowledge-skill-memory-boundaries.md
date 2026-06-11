# Knowledge / Skills / Memory 边界说明

## 一句话边界

```text
Knowledge = 稳定测试知识和标准
Skills = 使用知识完成分析动作的流程
Memory = 经确认的项目上下文、项目历史经验和个人本地偏好
Rules = 优先于输入文档的强制规则
```

配置来源按 `core / project / personal` 三层组织，personal 本地路径使用 `user` 目录。

| 层级 | 路径 | 默认提交 Git | 作用 |
|---|---|---|---|
| core | `rules/*.md`、`knowledge/*.md`、`memory/*.md`、`templates/*.md`、`quality-gates/*.md` | 是 | Agent 包随附的强制规则、稳定标准、模板和基础规则 |
| project | `rules/projects/<project-key>/**/*.md`、`knowledge/projects/<project-key>/**/*.md`、`memory/projects/<project-key>/**/*.md`、`quality-gates/projects/<project-key>/**/*.md` | 否 | 当前项目的强制规则、事实、经验、策略和附加门禁 |
| personal | `rules/user/**/*.md`、`knowledge/user/**/*.md`、`memory/user/**/*.md`、`quality-gates/user/**/*.md` | 否 | 当前使用者的个人强制规则、偏好、本地检查清单和补充启发 |

project 和 personal 是当前 run 的一等输入源：必须由 `memory-context-builder` 统一发现、裁剪和记录到 `process/context-pack.md`，后续 skill 只能消费 context pack 或按其来源记录受控补读。project knowledge 文件名没有硬性要求，但 context pack 必须记录其自理解类型和项目知识阶段绑定。

Rules 是高优先级约束源：优先级低于当前用户明确指令，高于当前输入文档、memory 和 knowledge。rules 与输入文档冲突时，默认遵守 rules，并在过程产物记录覆盖原因。rules 内部按 `core > project > personal` 处理，低层只能细化高层规则，不能放宽或违反高层强制约束。

## 归属规则

| 内容类型 | 放置位置 | 原因 |
|---|---|---|
| 用户入口、意图识别、`@test-analysis-agent` 路由 | `agents/test-analysis-agent.md` | 测试分析 Agent 门面，只做入口和路由，不沉淀方法论正文 |
| 用户入口、意图识别、`@test-design-agent` 路由 | `agents/test-design-agent.md` | 测试设计 Agent 门面，只做入口和路由，不沉淀方法论正文 |
| 全局强制规则 | `rules/*.md` | 优先级高于输入文档的全局约束 |
| 项目强制规则 | `rules/projects/<project-key>/**/*.md` | 项目级必须遵守的约束，确定 `project-key` 后扫描 |
| 个人强制规则 | `rules/user/**/*.md` | 使用者本地强制约束，不得覆盖 core/project rules |
| 测试点定义、字段、类型、方法 | `knowledge/testpoint-standard.md` | 稳定标准，所有 skill 共用 |
| 测试分析、测试设计、测试技术和执行级用例边界 | `knowledge/test-workflow-boundaries.md` | 本项目的公共工作流边界 |
| 测试分析维度和技术路由 | `skills/testing-method-router/references/test-method-routing-matrix.md` | testing-method-router 私有路由参考 |
| 测试场景、测试点、测试点明细和失败类型明细边界 | `knowledge/test-analysis-solution-standard.md` | 测试分析主输出层级边界标准 |
| 测试设计项和完整测试用例边界 | `knowledge/test-design-solution-standard.md` | 测试设计主输出层级边界标准 |
| 测试点明细字段、粒度和预期结果兜底规则 | `knowledge/test-analysis-solution-standard.md` | 主交付件标准 |
| 测试设计项字段、粒度和预期结果兜底规则 | `knowledge/test-design-solution-standard.md` | 测试设计主交付件标准 |
| 测试类型大类和子类 | `skills/coverage-review/references/basic-test-types.md` | 本项目内置测试类型体系 |
| 风险优先、异常优先、状态优先等专家原则 | `knowledge/test-techniques/README.md`、`knowledge/test-techniques/risk-based/risk-based-testing.md` | 测试技术的通用审视规则，分析层识别风险和测试点明细，设计层控制设计项深度 |
| 空值、重复提交、越权、幂等等通用缺陷模式 | `knowledge/test-techniques/experience-based/error-guessing-checklist.md` | 经验型测试技术补充，分析层识别缺陷风险，设计层补充高价值设计项 |
| 需求文档、需求依据、方法证据、记忆上下文包等框架术语 | `knowledge/test-workflow-boundaries.md` | 稳定分析术语，所有 skill 共用 |
| 分析维度、需求信号到测试技术的映射 | `skills/testing-method-router/references/test-method-routing-matrix.md` | 稳定路由知识 |
| 方法分析证据字段和质量要求 | `skills/testing-method-router/references/method-evidence-standard.md` | 证明测试理论被实际应用的统一标准 |
| 输入事实模型字段 | `templates/input-fact-model-template.md` | 输入事实模型是运行期结构化产物，模板定义事实清单、需求-设计映射、待确认事项和来源说明 |
| 项目风险画像、覆盖策略、术语映射、路由说明、测试 oracle、测试设计因子、测试设计模式和 checklist 补充 | `knowledge/projects/<project-key>/**/*.md` | 项目级测试知识补充，确定 `project-key` 后按需扫描并登记阶段绑定 |
| 个人测试启发、检查清单和本地关注点 | `knowledge/user/**/*.md` | personal 层知识补充，按需扫描 |
| 记住、记录、归档类请求的写入分类流程 | `skills/context-capture/SKILL.md` | 判断写入 memory/knowledge 与 personal/project 层级 |
| `.docx` / `.xlsx` 输入转 Markdown 与缓存复用流程 | `skills/normalize-input-documents/SKILL.md` | 输入归一化流程；转换结果写入全局 `outputs/input-cache/` 并在完整 run 中绑定到 `outputs/runs/<run-id>/inputs/`，不沉淀为 knowledge 或 memory |
| 某个测试技术的执行步骤 | `skills/*/SKILL.md` | 过程性动作，不是事实库 |
| 输入、输出、约束、质量门禁调用顺序 | `skills/*/SKILL.md` | 插件运行流程 |
| 项目全局事实、全局约束、输出偏好和项目专属术语覆盖 | `memory/project-memory.md` | 项目专属且经确认 |
| 项目真实历史缺陷、复盘教训、团队测试习惯 | `memory/testing-experience-memory.md` | 项目专属经验 |
| 指定项目的事实、业务域分片、历史经验和输出偏好 | `memory/projects/<project-key>/**/*.md` | 项目级长期 memory，确定 `project-key` 后自动扫描 |
| 个人输出偏好、检查习惯和本地记忆 | `memory/user/**/*.md` | personal 层 memory，按需扫描 |
| 本次运行筛选出的少量上下文 | `${PROJECT_ROOT}/outputs/runs/<run-id>/process/context-pack.md` | 运行产物，不是长期事实源 |
| 本次运行缺口治理结果 | `${PROJECT_ROOT}/outputs/runs/<run-id>/process/clarification-session.md` | 运行产物，用于解释 `待人工分析确认` 的来源 |
| 本次运行阶段顺序、状态和证据路径 | `${PROJECT_ROOT}/outputs/runs/<run-id>/process/task-list.md` | 运行产物，是流程事实源，不是长期配置 |
| 运行产物分类、固定文件名和下游消费约定 | `docs/output-artifact-contract.md` | 输出契约，防止 skill、模板和脚本各自发散 |
| 测试设计 Agent 架构、流程和边界 | `docs/test-design-agent-design.md` | 设计层架构文档，说明如何承接测试分析方案 |
| 报告、中间产物和运行产物的 Markdown 结构 | `templates/*.md` | 模板层只定义形状和占位，不维护另一套标准 |
| 公共覆盖门禁和 project/personal 附加门禁入口 | `quality-gates/*.md`、`quality-gates/projects/`、`quality-gates/user/` | 跨阶段或本地附加门禁，不产生新知识 |
| coverage-review 私有审查清单 | `skills/coverage-review/references/*.md` | 仅供覆盖审查执行，不放在公共 quality-gates 根目录 |
| 可机械执行的结构、一致性、启发式语义和回归检查 | `bin/*.py` | 脚本层只做可重复检查；模型 review 不重复脚本已覆盖的确定性项 |

## 禁止重复

- `agents/` 只维护用户入口和意图路由，不重复维护测试点类型、方法枚举和通用缺陷模式。
- `skills/` 不重复维护测试点类型、方法枚举和通用缺陷模式，只引用 `knowledge/`。
- `skills/` 不把方法证据写成自由发挥的叙述，统一引用 `skills/testing-method-router/references/method-evidence-standard.md`。
- `memory/` 不保存通用测试理论、通用缺陷模式、通用类型定义和方法步骤。
- `rules/` 不保存普通知识、历史经验或临时偏好；只有明确“必须/禁止/优先于输入”的约束才进入 rules。
- `memory/` 不重复维护框架术语定义；框架术语归属 `knowledge/test-workflow-boundaries.md`，memory 只记录项目专属术语或覆盖。
- `knowledge/` 不保存项目事实、用户临时偏好、单次运行结果和未确认假设。
- `knowledge/projects/<project-key>/` 只能保存项目级测试知识补充，不保存未确认业务事实、真实缺陷复盘或输出偏好。
- `knowledge/projects/<project-key>/` 不覆盖根目录 `knowledge/` 的测试点字段、类型、方法、输出契约和质量门禁。
- `knowledge/projects/<project-key>/` 下的文件名不作硬性要求；如果无法从文件名、标题、frontmatter 或摘要自理解识别用途，context pack 只能记录为 `unclassified` 和后续补读建议，不得强行套用。
- 未唯一确定 `project-key` 时，不读取所有项目目录正文，避免跨项目知识和 memory 污染。
- project 和 personal 层默认不提交 Git；仓库只保留对应 README 和发现规则。
- `rules/projects/<project-key>/` 和 `rules/user/` 默认不提交 Git；仓库只保留对应 README 和发现规则。
- `templates/` 只保留 core 模板，不提供 project/personal 分层模板补充；项目或个人输出偏好应归入 memory，强制格式要求应归入 rules。
- `context-pack.md` 只摘录与本次需求相关的 memory 和 project/personal 补充，不复制整份长期文件，也不放在 `memory/` 下。
- `context-pack.md` 的“项目知识阶段绑定”只判断文件应进入哪些环节；具体命中和应用由对应 skill 在阶段内读取后判断，并记录应用状态。
- `task-list.md`、`context-pack.md` 和 `clarification-session.md` 必须随 run 目录生成，分别记录固定阶段顺序、上下文绑定和待确认治理结果；即使无 project/personal 命中或无待确认候选，也必须生成并说明原因。
- `task-list.md` 不替代运行时 todo 工具，但比运行时 UI 更适合作为可校验事实源。
- `templates/` 只列出字段、占位和最小示例，不直接维护或长篇引用背景知识；字段含义、类型、方法等标准由调用模板的 `skills/` 和 `quality-gates/` 按需引用 `knowledge/`。
- `quality-gates/` 可以重复列出允许值用于校验，但必须以 `knowledge/` 的标准为来源，不维护独立定义。
- `bin/` 中的枚举和章节列表必须服务于机械校验；如果标准变化，应同步来自 `knowledge/`、`templates/` 或 `quality-gates/` 的权威来源。

## 冲突处理

当信息冲突时，按以下顺序处理：

1. 当前用户明确指令。
2. `rules/` 中适用于当前 run 的强制规则。
3. 当前输入文档中的明确规则，包括需求、设计方案和已评审测试分析方案。
4. 经确认的项目 memory。
5. `memory/user/` 中的 personal 偏好和本地记忆，但不得覆盖项目事实。
6. `knowledge/projects/<project-key>/` 中的项目化测试知识补充。
7. `knowledge/user/` 中的 personal 测试启发，但不得覆盖项目化知识和 core 标准。
8. `knowledge/` 中的通用测试知识。
9. skill 的流程性默认动作。

如果 rules 与输入文档冲突，默认遵守 rules，并记录“规则覆盖输入”。如果 memory 或 knowledge 与输入文档冲突，不直接覆盖输入；相关预期结果缺少依据时写 `待人工分析确认`，并在过程记录中说明。
