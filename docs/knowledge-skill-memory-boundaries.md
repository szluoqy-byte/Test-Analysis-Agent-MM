# Knowledge / Skills / Memory 边界说明

## 一句话边界

```text
Knowledge = 稳定测试知识和标准
Skills = 使用知识完成分析动作的流程
Memory = 经确认的项目上下文、项目历史经验和个人本地偏好
```

配置来源按 `core / project / personal` 三层组织，personal 本地路径使用 `user` 目录。

| 层级 | 路径 | 默认提交 Git | 作用 |
|---|---|---|---|
| core | `knowledge/*.md`、`memory/*.md`、`templates/*.md`、`quality-gates/*.md` | 是 | Agent 包随附的稳定标准、模板和基础规则 |
| project | `knowledge/projects/<project-key>/**/*.md`、`memory/projects/<project-key>/**/*.md`、`templates/projects/<project-key>/**/*.md`、`quality-gates/projects/<project-key>/**/*.md` | 否 | 当前项目的事实、经验、策略、模板补充和附加门禁 |
| personal | `knowledge/user/**/*.md`、`memory/user/**/*.md`、`templates/user/**/*.md`、`quality-gates/user/**/*.md` | 否 | 当前使用者的个人偏好、本地检查清单和补充启发 |

project 和 personal 是当前 run 的一等输入源：必须由 `memory-context-builder` 统一发现、裁剪和记录到 `process/context-pack.md`，后续 skill 只能消费 context pack 或按其来源记录受控补读。project knowledge 文件名没有硬性要求，但 context pack 必须记录其自理解类型和项目知识阶段绑定。

## 归属规则

| 内容类型 | 放置位置 | 原因 |
|---|---|---|
| 用户入口、意图识别、`@test-analysis-agent` 路由 | `agents/test-analysis-agent.md` | Agent 门面，只做入口和路由，不沉淀方法论正文 |
| 测试点定义、字段、类型、方法 | `knowledge/testpoint-standard.md` | 稳定标准，所有 skill 共用 |
| 测试分析、测试设计边界、分析维度和交付件落点 | `knowledge/test-analysis-methodology.md` | 本项目的上位方法论 |
| 测试场景、测试点、测试设计项和完整测试用例边界 | `knowledge/test-analysis-methodology.md` | 主输出层级边界标准 |
| 测试设计项字段、粒度和预期结果兜底规则 | `knowledge/test-design-solution-standard.md` | 主交付件标准 |
| 测试类型大类和子类 | `knowledge/basic-test-types.md` | 本项目内置测试类型体系 |
| 风险优先、异常优先、状态优先等专家原则 | `knowledge/test-techniques/README.md`、`knowledge/test-techniques/risk-based/risk-based-testing.md` | 测试技术的通用审视规则，分析层识别风险，设计层控制设计项深度 |
| 空值、重复提交、越权、幂等等通用缺陷模式 | `knowledge/test-techniques/experience-based/error-guessing-checklist.md` | 经验型测试技术补充，分析层识别缺陷风险，设计层补充高价值设计项 |
| 需求文档、需求依据、方法证据、记忆上下文包等框架术语 | `knowledge/test-analysis-methodology.md` | 稳定分析术语，所有 skill 共用 |
| 分析维度、需求信号到测试技术的映射 | `knowledge/test-method-routing-matrix.md` | 稳定路由知识 |
| 方法分析证据字段和质量要求 | `knowledge/method-evidence-standard.md` | 证明测试理论被实际应用的统一标准 |
| 设计方案事实摘要字段 | `templates/design-facts-template.md` | 设计事实是运行期结构化产物，模板定义形状，具体事实由 `design-solution-extraction` 提取 |
| 项目风险画像、覆盖策略、术语映射、路由说明、测试 oracle、测试设计因子、测试设计模式和 checklist 补充 | `knowledge/projects/<project-key>/**/*.md` | 项目级测试知识补充，确定 `project-key` 后按需扫描并登记阶段绑定 |
| 个人测试启发、检查清单和本地关注点 | `knowledge/user/**/*.md` | personal 层知识补充，按需扫描 |
| 记住、记录、归档类请求的写入分类流程 | `skills/context-capture/SKILL.md` | 判断写入 memory/knowledge 与 personal/project 层级 |
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
| 报告、中间产物和运行产物的 Markdown 结构 | `templates/*.md` | 模板层只定义形状和占位，不维护另一套标准 |
| 输出是否通过的检查项、失败条件和字段校验 | `quality-gates/*.md` | 质量门禁层负责判定，不产生新知识 |
| 可机械执行的结构、语义和回归检查 | `bin/*.py` | 脚本层只做确定性校验 |

## 禁止重复

- `agents/` 只维护用户入口和意图路由，不重复维护测试点类型、方法枚举和通用缺陷模式。
- `skills/` 不重复维护测试点类型、方法枚举和通用缺陷模式，只引用 `knowledge/`。
- `skills/` 不把方法证据写成自由发挥的叙述，统一引用 `knowledge/method-evidence-standard.md` 和 `templates/method-analysis-template.md`。
- `memory/` 不保存通用测试理论、通用缺陷模式、通用类型定义和方法步骤。
- `memory/` 不重复维护框架术语定义；框架术语归属 `knowledge/test-analysis-methodology.md`，memory 只记录项目专属术语或覆盖。
- `knowledge/` 不保存项目事实、用户临时偏好、单次运行结果和未确认假设。
- `knowledge/projects/<project-key>/` 只能保存项目级测试知识补充，不保存未确认业务事实、真实缺陷复盘或输出偏好。
- `knowledge/projects/<project-key>/` 不覆盖根目录 `knowledge/` 的测试点字段、类型、方法、输出契约和质量门禁。
- `knowledge/projects/<project-key>/` 下的文件名不作硬性要求；如果无法从文件名、标题、frontmatter 或摘要自理解识别用途，context pack 只能记录为 `unclassified` 和后续补读建议，不得强行套用。
- 未唯一确定 `project-key` 时，不读取所有项目目录正文，避免跨项目知识和 memory 污染。
- project 和 personal 层默认不提交 Git；仓库只保留对应 README 和发现规则。
- `context-pack.md` 只摘录与本次需求相关的 memory 和 project/personal 补充，不复制整份长期文件，也不放在 `memory/` 下。
- `context-pack.md` 的“项目知识阶段绑定”只判断文件应进入哪些环节；具体命中和应用由对应 skill 在阶段内读取后判断，并记录应用状态。
- `task-list.md` 必须随 run 目录生成，记录固定阶段顺序、状态和证据路径；它不替代运行时 todo 工具，但比运行时 UI 更适合作为可校验事实源。
- `templates/` 只列出字段、占位和最小示例，不直接维护或长篇引用背景知识；字段含义、类型、方法等标准由调用模板的 `skills/` 和 `quality-gates/` 按需引用 `knowledge/`。
- `quality-gates/` 可以重复列出允许值用于校验，但必须以 `knowledge/` 的标准为来源，不维护独立定义。
- `bin/` 中的枚举和章节列表必须服务于机械校验；如果标准变化，应同步来自 `knowledge/`、`templates/` 或 `quality-gates/` 的权威来源。

## 冲突处理

当信息冲突时，按以下顺序处理：

1. 当前用户明确指令。
2. 当前需求文档中的明确规则。
3. 经确认的项目 memory。
4. `memory/user/` 中的 personal 偏好和本地记忆，但不得覆盖项目事实。
5. `knowledge/projects/<project-key>/` 中的项目化测试知识补充。
6. `knowledge/user/` 中的 personal 测试启发，但不得覆盖项目化知识和 core 标准。
7. `knowledge/` 中的通用测试知识。
8. skill 的流程性默认动作。

如果 memory 或 knowledge 与需求文档冲突，不直接覆盖需求；相关预期结果缺少依据时写 `待人工分析确认`，并在过程记录中说明。
