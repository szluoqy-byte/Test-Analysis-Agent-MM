# 测试用例标题项设计模式路由

本目录用于指导本 Agent 将测试点转换为测试用例标题项。每个模式文件都应回答四个问题：

1. 这个模式解决哪类测试点。
2. 如何从测试点中抽取建模元素。
3. 如何把模型派生为标题项。
4. 如何控制标题项数量并写出输入条件与数据依赖、判定关注。

本目录不维护完整测试用例写作规则，不输出前置步骤、测试步骤、完整预期结果或执行数据。完整测试用例写作知识不在本 Agent 内维护。

## 模式分类

| 分类 | 作用 | 使用方式 |
|---|---|---|
| 基于规格的测试 | 从需求规则、流程、状态、接口、数据范围等规格信息派生标题项 | 作为大多数测试点的主生成方法 |
| 基于经验的测试 | 根据历史缺陷、专家经验、易错点补充标题项 | 作为补强方法，不替代规格建模 |
| 基于风险的测试 | 根据业务影响和失败后果调整等级、覆盖深度和补充场景 | 作为上层策略叠加到主生成方法 |
| 基于质量属性的测试 | 生成性能效率、可靠性与恢复性相关的验证标题项 | 作为非功能关注点补充 |

## 路由矩阵

| 测试点信号 | 首选模式 | 辅助模式 |
|---|---|---|
| 范围、阈值、枚举、格式、数量、金额、时间窗口 | `specification-based/equivalence-boundary.md` | `risk-based/risk-based-test-design.md` |
| 多输入参数、多配置项、多维组合、渠道/版本/角色组合 | `specification-based/data-combination.md` | `specification-based/equivalence-boundary.md` |
| 多条件共同决定结果、业务规则矩阵 | `specification-based/decision-table.md` | `specification-based/cause-effect.md` |
| 单个判断节点、校验点、流程分支、开关点 | `specification-based/decision-point.md` | `specification-based/equivalence-boundary.md` |
| 账期、结算周期、批处理周期、重试周期、定时任务 | `specification-based/processing-cycle.md` | `specification-based/state-transition.md` |
| 状态、生命周期、审批、取消、重试、超时、回退 | `specification-based/state-transition.md` | `specification-based/decision-point.md` |
| 主流程、备选流程、用户故事、验收标准、端到端链路 | `specification-based/scenario-usecase-userstory.md` | `risk-based/risk-based-test-design.md` |
| 复杂布尔原因与结果关系 | `specification-based/cause-effect.md` | `specification-based/decision-table.md` |
| API、字段、错误码、回调、消息、第三方系统 | `specification-based/interface-contract.md` | `quality-attribute-based/reliability-recoverability.md` |
| 历史缺陷、易错规则、专家经验 | `experience-based/error-guessing-checklist.md` | 与缺陷相关的规格模式 |
| 资金、安全、合规、不可逆操作、高用户影响 | `risk-based/risk-based-test-design.md` | 与测试点结构匹配的规格模式 |
| 性能、容量、响应时间、吞吐量 | `quality-attribute-based/performance-efficiency.md` | `specification-based/data-combination.md` |
| 稳定性、容错、恢复、重试、降级 | `quality-attribute-based/reliability-recoverability.md` | `specification-based/processing-cycle.md` |

## 选择规则

1. 先选主模式。主模式必须能解释测试点的核心验证目标。
2. 再选辅助模式。辅助模式只用于补充边界、风险、历史缺陷或质量属性，不替代主模式。
3. 如果测试点同时命中多个基于规格的模式，按“状态/周期/判定/组合/范围/场景”的顺序优先选择更结构化的模式。
4. 如果测试点只有“验证功能正常”之类泛化描述，应登记待确认问题或降级为场景测试，不直接扩展大量标题项。
5. 如果缺少生成标题项所需的入口、账号、数据或状态，使用中性输入条件描述并登记待确认问题，不编造项目事实。

## 专家审视顺序

1. 先确认需求边界：模块、角色、业务对象、状态、接口、数据对象和非范围。
2. 再识别高风险：资金、权限、不可逆、批量、外部依赖、历史缺陷和恢复成本。
3. 再选择主模式和辅助模式，避免只凭经验直接生成标题项。
4. 再检查判定关注：每个标题项都应有可观察结果方向。
5. 最后控制数量：合并同路径、同风险、同判定方向的低价值标题项。

## 标题项数量控制

| 标题项等级 | 默认策略 |
|---|---|
| Level 0 | 核心标题项，覆盖每个转测试版本必须验证的核心功能，必要时补充关键异常、边界或防护场景 |
| Level 1 | 关键标题项，覆盖特性关键功能和关键可靠性，建议每个迭代验证 |
| Level 2 | 重要标题项，覆盖系统重要功能，适合 TR 点或对外发布版本进行完整验证 |
| Level 3 | 一般标题项，用于较完整的版本全量测试，按变更范围选择相关标题项回归 |
| Level 4 | 生僻标题项，覆盖低频应用场景和特殊预置条件，建议新特性首次验证后按需回归 |

## 判定关注与 Oracle 规则

判定关注只写观察方向，不展开完整预期结果。优先从需求、设计方案、context pack 或明确业务不变量中寻找依据。

| Oracle 类型 | 适用场景 | 判定关注表达方向 |
|---|---|---|
| 规则 Oracle | 业务规则、校验、限制、优先级 | 规则命中、拦截、默认处理、优先级结果 |
| 状态 Oracle | 生命周期、审批流、终态和非法迁移 | 源状态、目标状态、终态保护、非法迁移拒绝 |
| 数据 Oracle | 主数据、派生数据、缓存、统计和日志 | 主数据与派生数据一致、缓存刷新、审计可追踪 |
| 契约 Oracle | 接口字段、错误码、回调和幂等 | 响应结构、错误码、幂等响应、回调语义 |
| 权限 Oracle | 角色、资源、动作、数据范围 | 授权通过、越权拦截、数据隔离、权限变更生效 |
| 风险 Oracle | 历史缺陷、不变量和高损失失败模式 | 不重复、不泄露、不破坏、可恢复、可追踪 |

缺少判定依据时：

- 不创建假的预期结果。
- 生成待确认信息。
- 如有价值，可生成风险确认点，并明确标记需求未完全说明。

不应作为 Oracle 的内容：

- 纯实现猜测，例如需求未说明的数据表变化。
- 具体测试数据，除非需求或设计方案明确给出。
- UI 操作步骤，应改写为可观察业务结果。
- 通用最佳实践本身，例如“应该有日志”，除非需求、风险或 project memory 支撑。

## 输出给 `testcase-title-outline-generation` 的设计要素

每个模式最终都应形成如下设计要素，供标题项生成阶段使用：

| 测试点 ID | 主模式 | 辅助模式 | 覆盖意图 | 标题建议 | 等级 | 输入条件与数据依赖关注 | 判定关注 | 待确认信息 |
|---|---|---|---|---|---|---|---|---|
