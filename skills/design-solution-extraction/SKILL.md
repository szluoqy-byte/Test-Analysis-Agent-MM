---
name: design-solution-extraction
description: 当用户提供设计方案文档时使用。负责从设计方案中提取接口、字段、状态、权限、数据依赖、配置、异常处理、非功能约束和设计缺口，形成可供测试技术路由、测试点生成和测试设计方案生成消费的设计事实摘要。
---

# 设计方案事实提取 Skill

本 skill 在 `requirement-testability` 之后、`testing-method-router` 之前使用。它把设计方案文档转换为结构化设计事实，补充需求模型没有展开的实现约束，但不覆盖需求中已经明确的业务规则。

## 职责边界

- 本 skill 只提取设计方案中已经明确说明的事实、约束和缺口。
- 需求业务目标、验收范围和可测性判断仍由 `requirement-testability` 负责。
- 设计事实可以补充接口、字段、状态、权限、数据依赖、配置、异常处理和非功能约束。
- 设计方案与需求不一致时，不选择任意一边作为事实；输出冲突候选交给 `clarification-gate`。
- 设计推导出的新业务规则不能直接写成需求事实；必须标记为设计假设或待确认候选。
- 本 skill 不生成测试点、测试设计项、测试步骤、完整预期结果或自动化脚本。

## 输入

- 一份或多份设计方案 Markdown 文档。
- `requirement-testability` 产出的结构化需求模型。
- `${PROJECT_ROOT}/outputs/runs/<run-id>/process/context-pack.md`。
- `process/context-pack.md` 中绑定到 `design-solution-extraction` 的 project knowledge 文件，例如术语表、接口/状态/设计约定或项目级设计约束说明。
- `knowledge/test-analysis-methodology.md`。
- `templates/design-facts-template.md`。

## 提取步骤

1. 读取 context pack 的“项目知识阶段绑定”。如果存在绑定到 `design-solution-extraction` 的 project knowledge，先按来源文件、相关章节、关键词或标题读取，不全量复制大文件。
2. 识别设计方案来源、适用模块、关联需求片段和非范围说明。
3. 提取架构决策和关键流程，只保留会影响测试范围、风险、观察点或数据依赖的内容。
4. 提取接口契约，包括接口/集成点、请求字段、响应字段、错误码、鉴权、幂等、超时、重试、回调和兼容约束。
5. 提取字段和数据约束，包括必填、可空、格式、长度、枚举、范围、唯一性、精度和默认值。
6. 提取状态与生命周期，包括状态集合、合法迁移、终态、非法迁移、超时、回退、补偿和重复触发处理。
7. 提取权限与数据范围，包括角色、资源、动作、租户、归属、审批权限和可见范围。
8. 提取数据依赖，包括主数据、派生数据、缓存、统计、搜索、日志、消息、外部系统和一致性时机。
9. 提取配置与非功能约束，包括开关、灰度、降级、性能指标、容量限制、安全、可靠性和可观测性。
10. 对需求与设计冲突、设计缺失、来源不明或无法判断测试影响的内容登记 `CQ-*` 待确认候选。
11. 记录本阶段 project knowledge 应用状态。
12. 按 `templates/design-facts-template.md` 输出设计事实摘要，交给测试技术路由、测试点生成和测试设计方案生成使用。

## 输出

使用 `templates/design-facts-template.md`。输出至少包含：

- 设计方案信息。
- 设计事实清单。
- 接口契约摘要。
- 状态与权限摘要。
- 数据依赖与配置摘要。
- 设计缺口和冲突候选。

设计事实清单使用统一字段：

| 事实ID | 设计维度 | 对象/范围 | 设计事实 | 来源依据 | 对测试影响 | 待确认候选 |
|---|---|---|---|---|---|---|

如存在设计缺口、需求冲突或设计假设，追加统一 `CQ-*` 候选表：

| 问题ID | checkpoint | sourceStage | header | question | why | impact | options | blockingLevel | priority | askPolicy | mustAsk | relatedRequirement | memoryConflict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## 约束

- 不从接口名、字段名或实现细节反推未说明的业务规则。
- 不编造接口路径、字段、状态、错误码、阈值、角色或数据关系。
- 不把内部实现细节写入主交付件，除非它会影响测试点、测试设计项或预期结果依据。
- 需求明确、设计仅细化实现时，以需求作为业务事实，设计作为测试约束补充。
- 需求未说明但设计明确的接口、字段、状态或配置，可以作为设计事实进入后续分析，并保留来源。
- 需求与设计冲突时，登记待确认候选，不静默修正。
- 本 skill 不直接向用户提问。
- 如果 context pack 中的项目设计约定不足，只能按 context pack 记录的来源或当前需求明确指向的文件补读相关章节，并在设计事实摘要中记录来源；不得全目录搜索或全量复制大文件。
- 绑定到本阶段的 project knowledge 必须读取并留痕；如果未应用，必须使用 `not_applicable`、`insufficient_evidence` 或 `conflict_with_requirement` 解释。
