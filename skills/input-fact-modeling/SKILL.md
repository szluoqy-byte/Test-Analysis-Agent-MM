---
name: input-fact-modeling
description: 在测试分析 workflow 中读取需求文档和可选设计方案文档，建立统一输入事实模型；记录事实、需求-设计映射、缺口冲突和待确认事项，为测试技术路由和测试分析方案生成提供事实输入。
---

# 输入事实建模 Skill

本 skill 在 `memory-context-builder` 之后、`clarification-gate` 和 `testing-method-router` 之前使用。它把需求文档、可选设计方案文档和当前 run 的上下文补充建模为统一的输入事实模型。

`input-fact-modeling` 只回答“输入材料说了什么、哪些事实可验证、哪些事实缺失或冲突、需求与设计如何对应”。它不判断应该使用哪种测试技术，不给出必选/可选路由，不生成测试点、测试点明细、TDI、测试步骤或完整预期结果。

## 输入

- run-local 需求 Markdown。
- 可选 run-local 设计方案 Markdown。
- `process/context-pack.json`。
- `process/context-pack.json` 中绑定到 `input-fact-modeling` 的 project knowledge，例如术语表、领域词表、接口/状态/设计约定或项目级输入建模约束。
- `knowledge/test-workflow-boundaries.md`。
- `templates/process-artifacts-json-template.json` 和 `templates/input-fact-model-template.md`。前者定义 JSON 事实源形态，后者仅作为渲染后 Markdown 样式参考。

## 建模步骤

1. 读取 context pack 的“项目知识阶段绑定”。如果存在绑定到 `input-fact-modeling` 的 project knowledge，按来源文件、相关章节、关键词或标题读取，不全量复制大文件。
2. 识别输入来源、需求范围、可选设计方案范围和明确非范围。
3. 从需求文档提取事实：模块、业务对象、角色、流程、规则、状态、输入输出、异常路径、外部依赖、可观察结果和可测性缺口。
4. 如果提供设计方案，从设计文档提取事实：接口、字段、状态、权限、数据依赖、配置、异常处理、非功能约束、架构决策和设计缺口。
5. 不给事实预先标注测试技术或分析维度；只记录事实内容、约束条件、可观察结果和缺口/冲突，让 `testing-method-router` 后续自行判断测试技术。
6. 建立需求事实和设计事实之间的映射关系：
   - `补充`：设计事实细化需求事实，例如接口字段、状态枚举或数据一致性时机。
   - `一致`：设计事实与需求事实语义一致。
   - `冲突`：需求和设计事实互相矛盾。
   - `无设计依据`：需求事实没有设计补充。
   - `设计新增`：设计事实无法追溯到需求，需要作为设计假设或待确认事项。
7. 将模糊、缺失、冲突和不可验证内容记录为人可读的待确认事项，只说明问题、影响和处理建议；不生成 `checkpoint`、`askPolicy`、`blockingLevel` 等 `clarification-gate` 内部字段。
8. 记录来源与应用说明，尤其是本阶段读取的 project knowledge、应用状态和影响范围。
9. 按通用 process JSON 结构输出 `process/input-fact-model.json`，交给 `clarification-gate`、`testing-method-router` 和测试分析方案生成阶段使用；不要手工维护 `process/input-fact-model.md`。

## 输出

输出 `process/input-fact-model.json`，并由 `bin/render-run-markdown.py` 渲染 `process/input-fact-model.md`。输出至少包含：

- 输入来源。
- 事实清单。
- 需求-设计映射。
- 待确认事项。
- 来源与应用说明。

事实清单使用统一字段：

| 事实ID | 来源 | 对象/范围 | 事实内容 | 约束/条件 | 可观察结果 | 缺口/冲突 |
|---|---|---|---|---|---|---|

待确认事项使用轻量字段：

| 编号 | 来源事实 | 问题 | 影响 | 处理建议 |
|---|---|---|---|---|

## 约束

- 不从常识、接口名、字段名或实现细节反推未说明的业务规则。
- 不编造接口路径、字段、状态、错误码、阈值、角色、错误提示、数据关系或非功能指标。
- 不把 project/personal knowledge 写成需求或设计事实；只能作为术语解释、关注点、约束来源或待确认依据。
- 需求明确、设计仅细化实现时，以需求作为业务事实，设计作为测试约束补充。
- 需求未说明但设计明确的接口、字段、状态或配置，可以作为设计事实进入模型，并保留来源。
- 需求与设计冲突时，记录待确认事项，不静默选择任意一边。
- 不输出测试技术、必选/可选路由、置信度、测试点、测试点明细、TDI、操作步骤、自动化脚本或完整测试用例。
- 本 skill 不直接向用户提问。
- 如果 context pack 中的项目补充不足，只能按 context pack 记录的来源或当前需求明确指向的文件补读相关章节，并在来源与应用说明中记录来源；不得全目录搜索或全量复制大文件。
- 绑定到本阶段的 project knowledge 必须读取并留痕；如果未应用，必须使用 `not_applicable`、`insufficient_evidence` 或 `conflict_with_requirement` 解释。
